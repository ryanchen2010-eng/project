"""Carbonyl-specific compatibility for the existing one-H2 net pathway.

Only aldehyde/ketone C=O sites are edited. Screened alcohols/ethers and
carbocyclic aromatic skeletons can be retained in this bounded net option,
not a catalyst-specific chemoselectivity or stereofacial prediction.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/17-4-alcohols-from-carbonyl-compounds-reduction"
CATALYSIS_SOURCE = "https://doi.org/10.1002/cssc.200700086"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")


def sites(molecule):
    return [*graph.find_aldehydes(molecule), *graph.find_ketones(molecule)]


def site_check(molecule, site):
    if tuple(site) not in sites(molecule):
        return "The selected C=O is not an ordinary aldehyde or ketone; acid, ester, amide and other carbonyls are not this reaction site."
    carbon, oxygen = (molecule.GetAtomWithIdx(i) for i in site)
    if (carbon.GetIsAromatic() or carbon.GetHybridization() != Chem.HybridizationType.SP2
            or oxygen.GetDegree() != 1 or molecule.GetBondBetweenAtoms(*site).GetBondType() != Chem.BondType.DOUBLE):
        return "The selected aldehyde/ketone needs an ordinary C=O with a terminal oxygen."
    if any(not n.GetIsAromatic() and n.GetHybridization() != Chem.HybridizationType.SP3 for n in graph.carbon_neighbors(carbon)):
        return "The C=O has an adjacent unsaturated/carbonyl carbon; conjugated, cumulated and adjacent dicarbonyl environments need separate selectivity validation."
    return None


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind in {"aldehyde", "ketone"}:
        other = next((s for s in sites(molecule) if set(s) == set(indices)), None)
        if other is None or site_check(molecule, other):
            return "rejected", "unvalidated", "An additional carbonyl does not pass the ordinary aldehyde/ketone site policy."
        if set(indices) == set(site):
            return "reactive", "validated", "The selected C=O becomes C–OH: one reagent H bonds to carbon and the other to its original oxygen."
        if distance(molecule, site[0], other[0]) <= 2:
            return "rejected", "competition", "Adjacent or 1,3-dicarbonyl groups can involve enol/chelation chemistry; selective one-site reduction is not validated for this arrangement."
        return "alternative-site", "bounded", "Another separated aldehyde/ketone remains unchanged in this one-site net option. Further reduction can compete; no selective partial conversion or product ratio is predicted."
    if kind == "alcohol":
        alcohol = next(((c, o) for c, o in graph.find_alcohols(molecule) if {c, o} == set(indices)), None)
        if alcohol is None:
            return "rejected", "unvalidated", "This OH is not an ordinary saturated aliphatic alcohol."
        c, o = alcohol
        atom = molecule.GetAtomWithIdx(c)
        if graph.is_allylic_or_benzylic(atom):
            return "rejected", "competition", "An additional allylic/benzylic alcohol can undergo catalyst-dependent C–O cleavage; its retention is not validated."
        if sum(n.GetAtomicNum() == 8 for n in atom.GetNeighbors()) != 1:
            return "rejected", "unvalidated", "Geminal-diol/hemiacetal alcohol environments are not validated unchanged groups."
        for carbonyl, _ in sites(molecule):
            if distance(molecule, c, carbonyl) <= 1:
                return "rejected", "unvalidated", "An alpha-hydroxy carbonyl needs separate chelation/side-reaction validation; this increment screens remote alcohols."
            ring_size = distance(molecule, o, carbonyl) + 1
            if ring_size in {5, 6}:
                return "rejected", "competition", f"This OH and a carbonyl can close a {ring_size}-membered hemiacetal/hemiketal ring; open-chain reduction versus cyclization is not evaluated."
        return "preserved", "validated", "This screened remote saturated alcohol retains its C–O/O–H bonds and applicable specified configuration in the net edit; catalyst-dependent side reactions are not predicted."
    if kind == "ether":
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None or oxygen.GetDegree() != 2:
            return "rejected", "unvalidated", "The ether does not have a validated neutral two-carbon oxygen environment."
        if all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Diaryl ether retention needs separate validation; this increment screens dialkyl and aryl–alkyl ethers."
        for carbon in oxygen.GetNeighbors():
            if (carbon.GetAtomicNum() != 6 or molecule.GetBondBetweenAtoms(carbon.GetIdx(), oxygen.GetIdx()).GetBondType() != Chem.BondType.SINGLE
                    or (not carbon.GetIsAromatic() and carbon.GetHybridization() != Chem.HybridizationType.SP3)):
                return "rejected", "unvalidated", "Unsaturated/enol and nonordinary ethers are outside this spectator policy."
            if not carbon.GetIsAromatic() and graph.is_allylic_or_benzylic(carbon):
                return "rejected", "competition", "Benzyl/allyl ether cleavage can compete under hydrogenation; unchanged ether protection is not assumed."
            if sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1:
                return "rejected", "unvalidated", "Acetal/ketal and multiple-oxygen carbon environments need separate validation."
        return "preserved", "validated", "This screened saturated dialkyl or carbocyclic aryl–alkyl ether retains its C–O bonds in the selected net reduction. No acid cleavage or general catalyst inertness is inferred."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic rings have no validated compatibility policy in this increment."
        return "preserved", "bounded", "The carbocyclic aromatic skeleton is retained in this C=O-to-alcohol net option. Ring hydrogenation and benzylic deoxygenation depend on catalyst/conditions and are not excluded experimentally."
    if kind in {"alkene", "alkyne"}:
        return "rejected", "competition", f"An additional {kind} can compete for hydrogenation; selective C=O reduction with its geometry retained is not validated."
    if kind in {"peroxide", "peroxyacid", "carbonyl"}:
        return "rejected", "competition", f"Additional {kind} reduction/cleavage is not covered by this aldehyde/ketone compatibility policy."
    return "rejected", "unvalidated", f"The additional {kind} group has no validated spectator policy for carbonyl hydrogenation. Distance alone does not make it inert."


def additional_check(molecule, site):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL and distance(molecule, atom.GetIdx(), site[0]) < 2:
            yield ("near-site-stereo", "unvalidated", f"Specified center at substrate atom {atom.GetIdx() + 1} is at/adjacent to the C=O; epimerization/chelation and facial selectivity are not evaluated by distant-center retention.", [atom.GetIdx()])


POLICY = compatibility.SitePolicy("aldehyde/ketone carbonyl hydrogenation", frozenset({"C", "H", "O"}),
                                  site_check, group_check, additional_check, added_atoms=2,
                                  extra_groups=(("ether", ETHER_QUERY),))


def assess(molecule, site):
    return compatibility.assess_site(molecule, site, POLICY)


def edit_contract(substrate, reagent, site):
    hydrogens = list(reagent.GetAtoms())
    if (len(hydrogens) != 2 or reagent.GetNumBonds() != 1 or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetAtomicNum() != 1 or a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in hydrogens)):
        raise ValueError("Carbonyl hydrogenation consumes one actual neutral H–H molecule, not an arbitrary hydrogen-containing reagent.")
    ends = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    hs = [a.GetAtomMapNum() for a in hydrogens]
    return [{"atomMaps": ends, "before": 2.0, "after": 1.0},
            {"atomMaps": hs, "before": 1.0, "after": None},
            *[{"atomMaps": [end, h], "before": None, "after": 1.0} for end, h in zip(ends, hs)]]


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    # No unselected double-bond geometry may be consumed by this C=O edit.
    compatibility.validate_edit_contract(before, after, edit_contract(substrate, reagent, site), expected_fragments=1)
