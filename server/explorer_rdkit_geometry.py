"""Bounded Explorer-only covalent conformer fallback; never changes Builder rules."""
import math
from rdkit import Chem
from rdkit.Chem import AllChem


def validate_geometry(original, candidate):
    """Check graph, finite coordinates and specified stereo, not experimental accuracy."""
    if candidate is None or candidate.GetNumConformers() != 1:
        return False
    expected = Chem.RemoveHs(Chem.Mol(original))
    observed = Chem.RemoveHs(Chem.Mol(candidate))
    if Chem.MolToSmiles(expected, isomericSmiles=False) != Chem.MolToSmiles(observed, isomericSmiles=False):
        return False
    if original.GetNumAtoms() > candidate.GetNumAtoms():
        return False
    for a, b in zip(original.GetAtoms(), candidate.GetAtoms()):
        if (a.GetAtomicNum(), a.GetIsotope(), a.GetFormalCharge()) != (b.GetAtomicNum(), b.GetIsotope(), b.GetFormalCharge()):
            return False
    original_bonds = {(min(b.GetBeginAtomIdx(), b.GetEndAtomIdx()), max(b.GetBeginAtomIdx(), b.GetEndAtomIdx()), b.GetBondType()) for b in original.GetBonds()}
    candidate_bonds = {(min(b.GetBeginAtomIdx(), b.GetEndAtomIdx()), max(b.GetBeginAtomIdx(), b.GetEndAtomIdx()), b.GetBondType()) for b in candidate.GetBonds() if b.GetBeginAtomIdx() < original.GetNumAtoms() and b.GetEndAtomIdx() < original.GetNumAtoms()}
    if original_bonds != candidate_bonds:
        return False
    conf = candidate.GetConformer()
    points = [conf.GetAtomPosition(i) for i in range(candidate.GetNumAtoms())]
    if not all(math.isfinite(v) and abs(v) < 10000 for p in points for v in (p.x, p.y, p.z)):
        return False
    if any((points[i] - points[j]).Length() < 0.35 for i in range(len(points)) for j in range(i)):
        return False
    for bond in candidate.GetBonds():
        distance = (points[bond.GetBeginAtomIdx()] - points[bond.GetEndAtomIdx()]).Length()
        if not 0.45 <= distance <= 3.1:
            return False
    reference = Chem.Mol(original)
    actual = Chem.Mol(candidate)
    Chem.AssignStereochemistry(reference, cleanIt=True, force=True)
    try:
        Chem.AssignStereochemistryFrom3D(actual, replaceExistingTags=True)
        Chem.AssignStereochemistry(actual, cleanIt=True, force=True)
    except Exception:
        return False
    for atom in reference.GetAtoms():
        if atom.HasProp('_CIPCode'):
            other = actual.GetAtomWithIdx(atom.GetIdx())
            if not other.HasProp('_CIPCode') or other.GetProp('_CIPCode') != atom.GetProp('_CIPCode'):
                return False
    for bond in reference.GetBonds():
        if bond.GetStereo() in (Chem.BondStereo.STEREOE, Chem.BondStereo.STEREOZ):
            other = actual.GetBondBetweenAtoms(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
            if other is None or other.GetStereo() != bond.GetStereo():
                return False
    return True


def generate_fallback(molecule, allowed_elements):
    """Three deterministic embedding attempts and bounded optimizations; fail closed."""
    if (len(Chem.GetMolFrags(molecule)) != 1 or molecule.GetNumAtoms() > 80
        or any(a.GetFormalCharge() or a.GetNumRadicalElectrons() or a.GetSymbol() not in allowed_elements for a in molecule.GetAtoms())):
        return None
    working = Chem.AddHs(Chem.Mol(molecule))
    try:
        if AllChem.MMFFHasAllMoleculeParams(working):
            method = 'MMFF94'
        elif AllChem.UFFHasAllMoleculeParams(working):
            method = 'UFF'
        else:
            return None
    except Exception:
        return None
    for seed, random_coords in ((42, False), (1729, False), (4099, True)):
        candidate = Chem.Mol(working)
        settings = AllChem.ETKDGv3()
        settings.randomSeed = seed
        settings.maxIterations = 200
        settings.useRandomCoords = random_coords
        try:
            if AllChem.EmbedMolecule(candidate, settings) != 0:
                continue
            status = (AllChem.MMFFOptimizeMolecule(candidate, maxIters=600) if method == 'MMFF94'
                      else AllChem.UFFOptimizeMolecule(candidate, maxIters=600))
            if status != 0 or not validate_geometry(molecule, candidate):
                continue
            return {'molfile': Chem.MolToMolBlock(candidate), 'forceField': method, 'converged': True}
        except Exception:
            continue
    return None
