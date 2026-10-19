"""Scope and postconditions for the two existing ester-cleavage net pathways.

Only ordinary acyl–O cleavage is modeled. Ring opening is deliberately bounded
to isolated, saturated five/six-membered lactones, not arbitrary cyclic esters.
Stereo retention is a checked property of the mapped edit, not a prediction of
epimerization, competing mechanisms or the configuration isolated in a lab.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph
    from . import stereochemistry as stereo
else:
    import molecular_graph as graph
    import stereochemistry as stereo

PATHWAYS = {"Ester hydrolysis", "Ester saponification"}
TETRAHEDRAL = {Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW}
DOUBLE_STEREO = {Chem.BondStereo.STEREOE, Chem.BondStereo.STEREOZ,
                 Chem.BondStereo.STEREOCIS, Chem.BondStereo.STEREOTRANS}


def stereo_scope_issue(molecule):
    return stereo.stereo_scope_issue(molecule, "ester cleavage")

def site_issue(molecule, site):
    """Detector != permission: validate the selected ester topology separately."""
    if tuple(site) not in graph.find_esters(molecule):
        return "The selected site is not an ordinary carboxylic ester."
    issue = stereo_scope_issue(molecule)
    if issue:
        return issue
    carbon, _, oxygen, alkoxy = site
    bond = molecule.GetBondBetweenAtoms(carbon, oxygen)
    if bond.IsInRing():
        rings = molecule.GetRingInfo().AtomRings()
        selected = [r for r in rings if carbon in r and oxygen in r]
        if len(selected) != 1 or len(selected[0]) not in {5, 6}:
            return "Only isolated five- or six-membered lactone rings are supported in this phase."
        ring = selected[0]
        if any(sum(i in r for r in rings) != 1 for i in ring):
            return "Fused, bridged and spiro lactones need additional ring-opening validation."
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != (8 if i == oxygen else 6)
               or (i not in {carbon, oxygen} and molecule.GetAtomWithIdx(i).GetHybridization() != Chem.HybridizationType.SP3)
               for i in ring):
            return "Unsaturated or additional-heteroatom lactone rings are outside this ring-opening model."
        if any(molecule.GetBondBetweenAtoms(ring[i], ring[(i + 1) % len(ring)]).GetBondType() != Chem.BondType.SINGLE
               for i in range(len(ring))):
            return "Only saturated lactone ring paths are supported in this phase."
    elif molecule.GetAtomWithIdx(alkoxy).GetIsAromatic():
        # A carbon-only aromatic system gives a phenolic coproduct. Heteroaryl
        # and enol ester chemistry is not broadened by this phase.
        seen, pending = set(), [alkoxy]
        while pending:
            i = pending.pop()
            if i in seen:
                continue
            seen.add(i)
            atom = molecule.GetAtomWithIdx(i)
            if atom.GetAtomicNum() != 6:
                return "Heteroaryl esters need separate validation; this phase supports carbocyclic aryl esters."
            pending.extend(b.GetOtherAtomIdx(i) for b in atom.GetBonds() if b.GetIsAromatic())
    return None


def validate_retained_stereo(before, after):
    # Compatibility wrapper: Phase 1 permits no loss of specified stereo.
    return stereo.validate_retained_stereo(before, after, context="Ester cleavage")


def validate_cleavage(before, after, substrate, site, reagent, mechanism):
    """Check exact acyl cleavage, proton accounting, charge and fragment count."""
    c, oxo, old_o, alkoxy = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    incoming = next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetAtomicNum() == 8)
    by_map = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    def bond(a, b):
        return after.GetBondBetweenAtoms(by_map[a].GetIdx(), by_map[b].GetIdx())
    def order(a, b):
        found = bond(a, b)
        return found.GetBondType() if found is not None else None
    if (bond(c, old_o) is not None or bond(c, incoming) is None
            or order(c, incoming) != Chem.BondType.SINGLE
            or order(c, oxo) != Chem.BondType.DOUBLE
            or order(old_o, alkoxy) != Chem.BondType.SINGLE):
        raise ValueError("The ester acyl-cleavage connectivity failed validation.")
    basic = mechanism == "Ester saponification"
    if (by_map[incoming].GetFormalCharge() != (-1 if basic else 0)
            or graph.attached_hydrogens(by_map[incoming]) != (0 if basic else 1)
            or by_map[old_o].GetFormalCharge() != 0 or graph.attached_hydrogens(by_map[old_o]) != 1
            or any(a.GetFormalCharge() != (-1 if basic and a.GetAtomMapNum() == incoming else 0)
                   for a in after.GetAtoms())):
        raise ValueError("The ester acid/carboxylate or alcohol protonation failed validation.")
    proton = next(a.GetAtomMapNum() for a in by_map[old_o].GetNeighbors() if a.GetAtomicNum() == 1)
    def mapped_bonds(molecule):
        return {frozenset((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum())): b.GetBondType()
                for b in molecule.GetBonds()}
    expected = mapped_bonds(before)
    for pair in (frozenset((c, old_o)), frozenset((incoming, proton))):
        if expected.pop(pair, None) != Chem.BondType.SINGLE:
            raise ValueError("The transferred proton did not come from the supplied water/hydroxide.")
    expected.update({frozenset((c, incoming)): Chem.BondType.SINGLE,
                     frozenset((old_o, proton)): Chem.BondType.SINGLE})
    if mapped_bonds(after) != expected:
        raise ValueError("Ester cleavage changed an unselected bond or missed a required bond edit.")
    cyclic = substrate.GetBondBetweenAtoms(site[0], site[2]).IsInRing()
    if len(Chem.GetMolFrags(after)) != (1 if cyclic else 2):
        raise ValueError("Lactone opening must give one connected product; ordinary cleavage must give two.")
    validate_retained_stereo(before, after)
    # The stored mapped SMILES feed BOTH the diagrams and the 3D/calculation
    # workflow. Validate stereo through that serialization boundary too.
    params = Chem.SmilesParserParams()
    params.removeHs = False
    restored = Chem.MolFromSmiles(Chem.MolToSmiles(after), params)
    if restored is None:
        raise ValueError("Mapped ester products failed serialization.")
    validate_retained_stereo(before, restored)
