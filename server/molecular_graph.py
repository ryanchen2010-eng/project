"""Reusable functional-group detection on RDKit graphs, never compound names.

Indices refer to the supplied graph. Detection is separate from reaction scope
and reagent/condition validation. These helpers work with implicit or explicit H.
"""
from rdkit import Chem


def attached_hydrogens(atom):
    return atom.GetTotalNumHs() + sum(n.GetAtomicNum() == 1 for n in atom.GetNeighbors())


def carbon_neighbors(atom):
    return [n for n in atom.GetNeighbors() if n.GetAtomicNum() == 6]


def substitution_degree(atom):
    return len(carbon_neighbors(atom))


def classify_carbon(atom):
    return {0: "methyl", 1: "primary", 2: "secondary", 3: "tertiary", 4: "quaternary"}[substitution_degree(atom)]


def beta_hydrogens(molecule, carbon_index):
    return [n.GetIdx() for n in carbon_neighbors(molecule.GetAtomWithIdx(carbon_index))
            if attached_hydrogens(n) and not n.GetIsAromatic()
            and molecule.GetBondBetweenAtoms(carbon_index, n.GetIdx()).GetBondType() == Chem.BondType.SINGLE]


def find_alkenes(molecule):
    return [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in molecule.GetBonds()
            if b.GetBondType() == Chem.BondType.DOUBLE
            and all(a.GetAtomicNum() == 6 and not a.GetIsAromatic()
                    for a in (b.GetBeginAtom(), b.GetEndAtom()))]


def find_alkynes(molecule):
    return [(b.GetBeginAtomIdx(), b.GetEndAtomIdx()) for b in molecule.GetBonds()
            if b.GetBondType() == Chem.BondType.TRIPLE
            and b.GetBeginAtom().GetAtomicNum() == b.GetEndAtom().GetAtomicNum() == 6]


def find_carbonyls(molecule):
    result = []
    for b in molecule.GetBonds():
        if b.GetBondType() != Chem.BondType.DOUBLE:
            continue
        atoms = sorted((b.GetBeginAtom(), b.GetEndAtom()), key=lambda a: a.GetAtomicNum())
        if [a.GetAtomicNum() for a in atoms] == [6, 8]:
            result.append((atoms[0].GetIdx(), atoms[1].GetIdx()))
    return result


def find_aldehydes(molecule):
    return [(c, o) for c, o in find_carbonyls(molecule)
            if attached_hydrogens(molecule.GetAtomWithIdx(c)) > 0
            and all(n.GetAtomicNum() in {1, 6, 8} for n in molecule.GetAtomWithIdx(c).GetNeighbors())
            and len([n for n in molecule.GetAtomWithIdx(c).GetNeighbors() if n.GetAtomicNum() == 8]) == 1]


def find_ketones(molecule):
    return [(c, o) for c, o in find_carbonyls(molecule)
            if substitution_degree(molecule.GetAtomWithIdx(c)) == 2]


def find_alcohols(molecule):
    result = []
    for oxygen in molecule.GetAtoms():
        if oxygen.GetAtomicNum() != 8 or oxygen.GetFormalCharge() or attached_hydrogens(oxygen) != 1:
            continue
        carbons = carbon_neighbors(oxygen)
        if len(carbons) == 1 and carbons[0].GetHybridization() == Chem.HybridizationType.SP3:
            result.append((carbons[0].GetIdx(), oxygen.GetIdx()))
    return result


def find_carboxylic_acids(molecule):
    return [(c, o, n.GetIdx()) for c, o in find_carbonyls(molecule)
            for n in molecule.GetAtomWithIdx(c).GetNeighbors()
            if n.GetAtomicNum() == 8 and n.GetIdx() != o and not n.GetFormalCharge()
            and attached_hydrogens(n) == 1
            and all(a.GetIdx() in {o, n.GetIdx()} or a.GetAtomicNum() in {1, 6}
                    for a in molecule.GetAtomWithIdx(c).GetNeighbors())
            and molecule.GetBondBetweenAtoms(c, n.GetIdx()).GetBondType() == Chem.BondType.SINGLE]


def find_esters(molecule):
    result = []
    for c, o in find_carbonyls(molecule):
        carbon = molecule.GetAtomWithIdx(c)
        if any(n.GetAtomicNum() not in {1, 6, 8} for n in carbon.GetNeighbors()):
            continue
        for n in carbon.GetNeighbors():
            if n.GetAtomicNum() != 8 or n.GetIdx() == o or n.GetFormalCharge() or attached_hydrogens(n):
                continue
            others = [a for a in carbon_neighbors(n) if a.GetIdx() != c]
            if (len(others) == 1 and (others[0].GetHybridization() == Chem.HybridizationType.SP3 or others[0].GetIsAromatic())
                    and len([a for a in n.GetNeighbors() if a.GetAtomicNum() != 1]) == 2
                    and molecule.GetBondBetweenAtoms(c, n.GetIdx()).GetBondType() == Chem.BondType.SINGLE
                    and molecule.GetBondBetweenAtoms(n.GetIdx(), others[0].GetIdx()).GetBondType() == Chem.BondType.SINGLE
                    and all(a.GetIdx() in {o, n.GetIdx()} or a.GetAtomicNum() in {1, 6} for a in carbon.GetNeighbors())):
                result.append((c, o, n.GetIdx(), others[0].GetIdx()))
    return result


def find_amines(molecule):
    return [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() == 7
            and not a.GetFormalCharge() and not a.GetIsAromatic()
            and a.GetHybridization() == Chem.HybridizationType.SP3
            and all(n.GetAtomicNum() in {1, 6} for n in a.GetNeighbors())]


def find_alkyl_halides(molecule):
    return [(n.GetIdx(), a.GetIdx()) for a in molecule.GetAtoms()
            if a.GetSymbol() in {"Cl", "Br", "I"} and not a.GetFormalCharge()
            for n in a.GetNeighbors() if n.GetAtomicNum() == 6
            and n.GetHybridization() == Chem.HybridizationType.SP3
            and molecule.GetBondBetweenAtoms(n.GetIdx(), a.GetIdx()).GetBondType() == Chem.BondType.SINGLE]


def is_allylic_or_benzylic(atom):
    return any(n.GetIsAromatic() or any(b.GetBondType() == Chem.BondType.DOUBLE
                                      and b.GetOtherAtom(n).GetAtomicNum() == 6 for b in n.GetBonds())
               for n in carbon_neighbors(atom))


def isolated_alkene(molecule, ends):
    # No adjacent multiple bonds/aromatic groups or heteroatom-substituted C=C:
    # these need resonance-specific selectivity rules rather than degree alone.
    return all(n.GetAtomicNum() in {1, 6} and (n.GetIdx() in ends or
               (not n.GetIsAromatic() and all(b.GetBondType() == Chem.BondType.SINGLE for b in n.GetBonds())))
               for i in ends for n in molecule.GetAtomWithIdx(i).GetNeighbors())


def markovnikov_targets(molecule, ends):
    degrees = [substitution_degree(molecule.GetAtomWithIdx(i)) for i in ends]
    if degrees[0] != degrees[1]:
        return [ends[degrees.index(max(degrees))]]
    # Equal degree only has one orientation if the full graph makes ends equivalent.
    ranks = list(Chem.CanonicalRankAtoms(molecule, breakTies=False))
    return [ends[0]] if ranks[ends[0]] == ranks[ends[1]] else []
