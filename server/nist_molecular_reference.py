"""Exact-graph NIST molecular references; fail closed on ambiguous metal identities."""
import html
import math
import re
import ssl
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from rdkit import Chem

_BASE = 'https://webbook.nist.gov/cgi/cbook.cgi?'
_KEY = re.compile(r'^[A-Z]{14}-[A-Z]{10}-[A-Z]$')
_MAX_BYTES = 1_000_000
_NONMETALS = {'H', 'B', 'C', 'N', 'O', 'F', 'Si', 'P', 'S', 'Cl', 'Ge', 'As', 'Se', 'Br', 'Sb', 'Te', 'I'}


def _read(query):
    bundle = Path('/etc/ssl/cert.pem')
    context = ssl.create_default_context(cafile=str(bundle) if not ssl.get_default_verify_paths().cafile and bundle.is_file() else None)
    with urlopen(Request(_BASE + urlencode(query), headers={'User-Agent': 'MoleculePlayground/0.1 educational viewer'}), timeout=10, context=context) as response:
        data = response.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        raise ValueError('Reference response exceeds limit')
    return data.decode('utf-8')


def _canonical(mol):
    copy = Chem.Mol(mol)
    for atom in copy.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.RemoveHs(copy), canonical=True, isomericSmiles=True)


def validate_exact_graph(smiles, sdf):
    """Only neutral, connected, unambiguous, exact isomeric graph matches."""
    original = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    candidate = Chem.MolFromMolBlock(sdf.split('$$$$', 1)[0], removeHs=False)
    if original is None or candidate is None or candidate.GetNumConformers() != 1:
        return False
    if (len(Chem.GetMolFrags(original)) != 1 or len(Chem.GetMolFrags(candidate)) != 1 or original.GetNumAtoms() > 80 or candidate.GetNumAtoms() > 160
        or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in original.GetAtoms())
        or not any(a.GetSymbol() not in _NONMETALS for a in original.GetAtoms())):
        return False
    if _canonical(original) != _canonical(candidate):
        return False
    conf = candidate.GetConformer()
    if not conf.Is3D():
        return False
    points = [conf.GetAtomPosition(i) for i in range(candidate.GetNumAtoms())]
    if not all(math.isfinite(value) and abs(value) < 10000 for p in points for value in (p.x, p.y, p.z)):
        return False
    if any((points[i] - points[j]).Length() < 0.35 for i in range(len(points)) for j in range(i)):
        return False
    if any(not 0.45 <= (points[b.GetBeginAtomIdx()] - points[b.GetEndAtomIdx()]).Length() <= 3.2 for b in candidate.GetBonds()):
        return False
    return True


def lookup(smiles, inchi, key):
    """Bounded exact identifier search, fixed NIST host and full graph comparison."""
    if not isinstance(inchi, str) or not inchi.startswith('InChI=1S/') or not isinstance(key, str) or not _KEY.fullmatch(key):
        return None
    try:
        page = _read({'InChI': key})
        unescaped = html.unescape(page)
        inchi_matches = re.findall(r'<span class="inchi-text">([^<]+)</span>', unescaped)
        identifiers = re.findall(r'Str3File=(C\d{4,14})', unescaped)
        if inchi not in inchi_matches or key not in inchi_matches or len(set(identifiers)) != 1:
            return None
        sdf = _read({'Str3File': identifiers[0]})
        method = re.search(r'>\s*<METHOD>\s*\r?\n([^\r\n]+)', sdf)
        # Some WebBook records explicitly describe the 3D file as computed
        # but do not identify its computational method. Never infer a method.
        computed = re.search(r'<a\b[^>]*>\s*computed\s*</a>\s*<a\b[^>]*Str3File=' + re.escape(identifiers[0]) + r'[^>]*>\s*3d\s+SD\s+file\s*</a>', unescaped, re.I)
        if (not method and not computed) or not validate_exact_graph(smiles, sdf):
            return None
        return {'structure': sdf, 'method': method.group(1).strip()[:100] if method else 'Not reported by NIST', 'sourceUrl': _BASE + urlencode({'ID': identifiers[0]})}
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, ValueError, RuntimeError):
        return None
