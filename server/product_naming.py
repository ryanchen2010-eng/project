"""Local, display-only naming of a deliberately small structural vocabulary.

Not an unrestricted IUPAC namer. Never changes a molecule, matches a reaction,
looks up a formula, or makes a network request. Unsupported structures return
None so callers retain their honest class label and show isomeric SMILES.
Rules: IUPAC Blue Book P-14/P-15 and P-9 (iupac.qmul.ac.uk/BlueBook/).
"""
from collections import defaultdict
from rdkit import Chem
from rdkit.Chem import rdCIPLabeler

ROOTS = ('', 'meth', 'eth', 'prop', 'but', 'pent', 'hex', 'hept', 'oct', 'non', 'dec')
HALOGENS = {9: 'fluoro', 17: 'chloro', 35: 'bromo', 53: 'iodo'}
MULTIPLIERS = {1: '', 2: 'di', 3: 'tri', 4: 'tetra'}


def simple_product_name(smiles):
    """Name unbranched C1–C10 chains with bounded O/halogen/unsaturation.

    No rings, branching, isotopes, ions, aromaticity, enhanced stereo or exotic
    stereo. R/S and E/Z qualify only stereo already specified in the graph,
    using map-free CIP reassignment, never a generated conformer's geometry.
    """
    if not isinstance(smiles, str) or not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None or len(Chem.GetMolFrags(mol)) != 1 or mol.GetStereoGroups():
            return None
        if any(a.GetAtomicNum() not in {1, 6, 8, *HALOGENS} or a.GetFormalCharge()
               or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery()
               or a.GetIsAromatic() for a in mol.GetAtoms()) or mol.GetRingInfo().NumRings():
            return None
        if any(a.GetChiralTag() not in {Chem.ChiralType.CHI_UNSPECIFIED,
                Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW}
                for a in mol.GetAtoms()):
            return None
        for atom in mol.GetAtoms():
            atom.SetAtomMapNum(0)
        mol = Chem.RemoveHs(mol)
        Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
        rdCIPLabeler.AssignCIPLabels(mol, maxRecursiveIterations=100000)
        carbons = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 6]
        if not 1 <= len(carbons) <= 10:
            return None
        adjacent = {i: [a.GetIdx() for a in mol.GetAtomWithIdx(i).GetNeighbors()
                        if a.GetAtomicNum() == 6] for i in carbons}
        if any(len(ns) > 2 for ns in adjacent.values()):
            return None
        ends = [i for i in carbons if len(adjacent[i]) <= 1]
        if len(ends) != (1 if len(carbons) == 1 else 2):
            return None
        chain, previous, current = [], None, ends[0]
        while current is not None:
            chain.append(current)
            next_atoms = [i for i in adjacent[current] if i != previous]
            previous, current = current, next_atoms[0] if next_atoms else None
        if len(chain) != len(carbons):
            return None
        choices = [_numbered_name(mol, order) for order in (chain, list(reversed(chain)))]
        choices = [item for item in choices if item is not None]
        return min(choices)[-1] if choices else None
    except (ValueError, RuntimeError, IndexError):
        # A failed display name must never reject an otherwise valid reaction.
        return None


def _numbered_name(mol, chain):
    positions = {i: n + 1 for n, i in enumerate(chain)}
    n = len(chain)
    root = ROOTS[n]
    hydroxyl, carbonyl, multiple = [], [], []
    halo = defaultdict(list)
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 6:
            continue
        if atom.GetDegree() != 1:
            return None  # Ether/ester/peroxide oxygen is not an alcohol.
        neighbor = atom.GetNeighbors()[0]
        if neighbor.GetIdx() not in positions:
            return None
        position = positions[neighbor.GetIdx()]
        order = mol.GetBondBetweenAtoms(atom.GetIdx(), neighbor.GetIdx()).GetBondTypeAsDouble()
        if atom.GetAtomicNum() in HALOGENS and order == 1:
            halo[HALOGENS[atom.GetAtomicNum()]].append(position)
        elif atom.GetAtomicNum() == 8 and order == 1 and atom.GetTotalNumHs() == 1:
            hydroxyl.append(position)
        elif atom.GetAtomicNum() == 8 and order == 2:
            carbonyl.append(position)
        else:
            return None
    for a, b in zip(chain, chain[1:]):
        bond = mol.GetBondBetweenAtoms(a, b)
        order = bond.GetBondTypeAsDouble()
        if order not in {1, 2, 3}:
            return None
        if order > 1:
            multiple.append((positions[a], order, bond))
    # Deliberately avoid combined senior groups / unsaturated oxygen naming.
    if len(multiple) > 1 or (multiple and (hydroxyl or carbonyl)):
        return None
    if any(len(values) > 4 for values in halo.values()):
        return None
    senior = []
    if carbonyl and hydroxyl:
        if len(carbonyl) != 1 or hydroxyl != carbonyl or carbonyl[0] not in {1, n}:
            return None
        if carbonyl[0] != 1:
            return None
        parent, senior = root + 'anoic acid', [1]
    elif carbonyl:
        if len(carbonyl) != 1:
            return None
        locant = carbonyl[0]
        if locant in {1, n}:
            if locant != 1:
                return None
            # Acyl halides are not aldehydes merely because C=O is terminal.
            carbon = mol.GetAtomWithIdx(chain[locant - 1])
            if carbon.GetTotalNumHs() != (2 if n == 1 else 1):
                return None
            parent = root + 'anal'
        else:
            parent = f'{root}an-{locant}-one'
        senior = [locant]
    elif hydroxyl:
        senior = sorted(hydroxyl)
        if len(hydroxyl) == 1:
            parent = root + 'anol' if n <= 2 else f'{root}an-{senior[0]}-ol'
        elif len(hydroxyl) == 2 and len(set(hydroxyl)) == 2:
            parent = f'{root}ane-{",".join(map(str, senior))}-diol'
        else:
            return None
    elif multiple:
        locant, order, _ = multiple[0]
        ending = 'ene' if order == 2 else 'yne'
        parent = root + ending if n == 2 else f'{root}-{locant}-{ending}'
    else:
        parent = root + 'ane'
    prefixes = []
    for label, locants in sorted(halo.items()):
        prefixes.append(f'{",".join(map(str, sorted(locants)))}-{MULTIPLIERS[len(locants)]}{label}')
    name = '-'.join(prefixes) + parent
    # Naming priorities: senior suffix, unsaturation, then substituent locants.
    priority = (tuple(senior), tuple(p for p, _, _ in multiple),
                tuple(sorted(p for values in halo.values() for p in values)),
                tuple((label, tuple(sorted(values))) for label, values in sorted(halo.items())))
    stereo = []
    for atom in mol.GetAtoms():
        if atom.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
            if atom.GetIdx() not in positions or not atom.HasProp('_CIPCode'):
                return None
            code = atom.GetProp('_CIPCode')
            if code not in {'R', 'S'}:
                return None
            stereo.append((positions[atom.GetIdx()], code))
    for locant, order, bond in multiple:
        if order == 2 and bond.GetStereo() != Chem.BondStereo.STEREONONE:
            if not bond.HasProp('_CIPCode') or bond.GetProp('_CIPCode') not in {'E', 'Z'}:
                return None
            stereo.append((locant, bond.GetProp('_CIPCode')))
    stereo.sort()
    # Resolve remaining symmetric numbering ties without inventing a center.
    tie = tuple((p, {'R': 0, 'S': 1, 'Z': 0, 'E': 1}[code]) for p, code in stereo)
    if stereo:
        name = '(' + ','.join(f'{p}{code}' for p, code in stereo) + ')-' + name
    else:
        name = name[0].upper() + name[1:]
    return priority, tie, name
