"""Shared, bounded SN1/E1 ionization assessment; not a cation predictor.

Resonance capture/elimination permissions remain in the individual policies.
The secondary scope is exactly the Me/Me or Me/Et topology already screened
for E1, not blanket secondary solvolysis or rearrangement permission.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph
else:
    import molecular_graph as graph


def small_secondary(molecule, site):
    alpha = molecule.GetAtomWithIdx(site[0])
    if graph.substitution_degree(alpha) != 2 or graph.attached_hydrogens(alpha) != 1:
        return False
    lengths = []
    for arm in graph.carbon_neighbors(alpha):
        if arm.IsInRing() or arm.GetHybridization() != Chem.HybridizationType.SP3 or any(n.GetAtomicNum() not in {1, 6} for n in arm.GetNeighbors()):
            return False
        tail = [n for n in graph.carbon_neighbors(arm) if n.GetIdx() != alpha.GetIdx()]
        if not tail and graph.attached_hydrogens(arm) == 3:
            lengths.append(1)
        elif (len(tail) == 1 and graph.attached_hydrogens(arm) == 2 and graph.attached_hydrogens(tail[0]) == 3
              and len(graph.carbon_neighbors(tail[0])) == 1 and not tail[0].IsInRing()
              and all(n.GetAtomicNum() in {1, 6} for n in tail[0].GetNeighbors())):
            lengths.append(2)
        else:
            return False
    return sorted(lengths) in ([1, 1], [1, 2])


def alkyl_basis(molecule, site):
    center = molecule.GetAtomWithIdx(site[0])
    if any(n.GetIsAromatic() for n in graph.carbon_neighbors(center)):
        return "benzylic resonance"
    if graph.substitution_degree(center) == 3:
        return "tertiary alkyl stabilization"
    if small_secondary(molecule, site):
        return "bounded secondary alkyl stabilization"
    return None


def halide_issue(molecule, site, mechanism):
    if tuple(site) not in graph.find_alkyl_halides(molecule):
        return f"{mechanism} requires an actual C(sp³)–Cl/Br/I bond; aryl/vinyl halides, fluoride and new leaving groups are not enabled."
    carbon, leaving = (molecule.GetAtomWithIdx(i) for i in site)
    if carbon.IsInRing():
        return f"Ring-bound/bridgehead {mechanism} carbocation planarity and rearrangement require separate validation."
    if any(n.GetAtomicNum() not in {1, 6} for n in carbon.GetNeighbors() if n.GetIdx() != leaving.GetIdx()):
        return f"Geminal halides or directly heteroatom-substituted {mechanism} centers need a separate ionization/oxocarbenium policy."
    return None


def rearrangement_issue(molecule, site, mechanism, *, resonance_neighbors=(), saturated_neighbors=False):
    center = molecule.GetAtomWithIdx(site[0])
    for neighbor in graph.carbon_neighbors(center):
        if neighbor.GetIsAromatic() or neighbor.GetIdx() in resonance_neighbors:
            continue
        if saturated_neighbors and neighbor.GetHybridization() != Chem.HybridizationType.SP3:
            return "This allylic/conjugated environment can have alternative resonance-site or cumulated-diene elimination; only terminal CH2=C(R) with a H-free central pi carbon is screened."
        if neighbor.IsInRing():
            return f"An adjacent cyclic carbon can introduce ring migration/expansion chemistry; unrearranged {mechanism} is not validated."
        if graph.substitution_degree(neighbor) >= 3:
            return f"An adjacent branched/quaternary carbon permits competing hydride/alkyl shifts; no rearranged {mechanism} products or cation preference are assigned."
        if any(n.GetIsAromatic() for n in graph.carbon_neighbors(neighbor)):
            return f"A neighboring carbon can become a resonance-stabilized benzylic cation after a shift; this competing {mechanism} rearrangement is unvalidated."
    return None
