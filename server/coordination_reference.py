"""Exact-record coordination references; never infer complexes from formula alone."""
import math
import ssl
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from rdkit import Chem

NIST_FE_CO5_URL = 'https://webbook.nist.gov/cgi/cbook.cgi?Str3File=C13463406'
PUBCHEM_FE_CO5 = '[C]=O.[C]=O.[C]=O.[C]=O.[C]=O.[Fe]'
MAX_BYTES = 100_000
CARBONYL_PROFILES = {
    26040: {'metal': 'Fe', 'count': 5, 'geometry': 'trigonal-bipyramidal', 'smiles': PUBCHEM_FE_CO5, 'url': NIST_FE_CO5_URL},
    26039: {'metal': 'Ni', 'count': 4, 'geometry': 'tetrahedral', 'smiles': '[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[Ni]', 'url': 'https://webbook.nist.gov/cgi/cbook.cgi?Str3File=C13463393'},
    25589: {'metal': 'Cr', 'count': 6, 'geometry': 'octahedral', 'smiles': '[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[Cr]', 'url': 'https://webbook.nist.gov/cgi/cbook.cgi?Str3File=C13007926'},
}


def matches_reviewed_fragments(cid, smiles):
    """Accept only the separately reviewed exact CID and its neutral fragment graph."""
    profile = CARBONYL_PROFILES.get(cid)
    if profile is None or not isinstance(smiles, str):
        return False
    mol = Chem.MolFromSmiles(smiles)
    expected = Chem.MolFromSmiles(profile['smiles'])
    if mol is None or expected is None:
        return False
    return Chem.MolToSmiles(mol, isomericSmiles=True) == Chem.MolToSmiles(expected, isomericSmiles=True)


def validate_carbonyl_sdf(text, cid):
    """Validate a reviewed neutral carbonyl and its expected coordination shape."""
    profile = CARBONYL_PROFILES.get(cid)
    if profile is None:
        return False
    count, metal = profile['count'], profile['metal']
    mol = Chem.MolFromMolBlock(text.split('$$$$', 1)[0], sanitize=False, removeHs=False)
    if mol is None or mol.GetNumAtoms() != 1 + 2 * count or mol.GetNumBonds() != 2 * count or mol.GetNumConformers() != 1:
        return False
    atoms = list(mol.GetAtoms())
    if sorted(a.GetSymbol() for a in atoms) != sorted([metal] + ['C'] * count + ['O'] * count):
        return False
    if any(a.GetIsotope() or a.GetFormalCharge() for a in atoms):
        return False
    iron = next(a for a in atoms if a.GetSymbol() == metal)
    if len(iron.GetNeighbors()) != count or any(a.GetSymbol() != 'C' for a in iron.GetNeighbors()):
        return False
    conf = mol.GetConformer()
    vectors = []
    for carbon in iron.GetNeighbors():
        neighbours = [n for n in carbon.GetNeighbors() if n.GetIdx() != iron.GetIdx()]
        if len(neighbours) != 1 or neighbours[0].GetSymbol() != 'O' or neighbours[0].GetDegree() != 1:
            return False
        if mol.GetBondBetweenAtoms(carbon.GetIdx(), neighbours[0].GetIdx()).GetBondTypeAsDouble() != 3:
            return False
        if mol.GetBondBetweenAtoms(carbon.GetIdx(), iron.GetIdx()).GetBondTypeAsDouble() != 1:
            return False
        vector = conf.GetAtomPosition(carbon.GetIdx()) - conf.GetAtomPosition(iron.GetIdx())
        oxygen_vector = conf.GetAtomPosition(neighbours[0].GetIdx()) - conf.GetAtomPosition(carbon.GetIdx())
        if not 1.5 < vector.Length() < 2.1 or not 0.9 < oxygen_vector.Length() < 1.4:
            return False
        if vector.DotProduct(oxygen_vector) / (vector.Length() * oxygen_vector.Length()) < 0.95:
            return False
        vectors.append(vector)
    if not all(math.isfinite(x) for i in range(mol.GetNumAtoms()) for x in tuple(conf.GetAtomPosition(i))):
        return False
    cosines = sorted(vectors[i].DotProduct(vectors[j]) / (vectors[i].Length() * vectors[j].Length()) for i in range(count) for j in range(i))
    if profile['geometry'] == 'tetrahedral':
        return all(abs(c + 1 / 3) < 0.08 for c in cosines)
    if profile['geometry'] == 'octahedral':
        return all(abs(c + 1) < 0.05 for c in cosines[:3]) and all(abs(c) < 0.08 for c in cosines[3:])
    return (abs(cosines[0] + 1) < 0.05 and all(abs(c + 0.5) < 0.08 for c in cosines[1:4])
            and all(abs(c) < 0.08 for c in cosines[4:]))


def validate_fe_carbonyl_sdf(text):
    return validate_carbonyl_sdf(text, 26040)


def fetch_nist_reference(cid=26040):
    profile = CARBONYL_PROFILES.get(cid)
    if profile is None:
        return None
    request = Request(profile['url'], headers={'User-Agent': 'MoleculePlayground/0.1 educational viewer'})
    try:
        system_bundle = Path('/etc/ssl/cert.pem')
        context = ssl.create_default_context(cafile=str(system_bundle) if not ssl.get_default_verify_paths().cafile and system_bundle.is_file() else None)
        with urlopen(request, timeout=10, context=context) as response:
            content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            return None
        text = content.decode('utf-8')
        return text if validate_carbonyl_sdf(text, cid) else None
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, ValueError):
        return None
