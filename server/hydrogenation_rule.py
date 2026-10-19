"""Initial site-compatibility consumer: isolated alkene + one H2.

Remote, ordinary saturated aliphatic alcohols are screened spectators. No
catalyst-specific aromatic/carbonyl/alkyne chemoselectivity or stereofacial
outcome is inferred; other pathways keep their existing policies.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/8-6-reduction-of-alkenes-hydrogenation"


def site_check(molecule, site):
    if tuple(site) not in graph.find_alkenes(molecule) and tuple(reversed(site)) not in graph.find_alkenes(molecule):
        return "The selected bond is not a non-aromatic carbon–carbon double bond."
    if not graph.isolated_alkene(molecule, site):
        return "The selected C=C is conjugated, cumulated, aromatic-adjacent or directly heteroatom-substituted; its local selectivity is not validated by this isolated-alkene rule."
    return None


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(site):
            return "reactive", "validated", "One H adds to each atom of this selected isolated C=C."
        if graph.isolated_alkene(molecule, indices):
            return "alternative-site", "bounded", "Another isolated C=C remains unchanged in this one-site net option; this does not predict selective partial hydrogenation or rule out further reduction/isomerization."
        return "rejected", "competition", "Another non-isolated C=C is present; competing conjugated/cumulated reduction or isomerization needs a separate selectivity model."
    if kind == "alcohol":
        carbon, oxygen = next(((c, o) for c, o in graph.find_alcohols(molecule) if {c, o} == set(indices)), (None, None))
        if carbon is None:
            return "rejected", "unvalidated", "The oxygen group is not a validated ordinary aliphatic alcohol."
        if graph.is_allylic_or_benzylic(molecule.GetAtomWithIdx(carbon)):
            return "rejected", "competition", f"Alcohol at substrate atom {carbon + 1} is allylic/benzylic; possible C–O cleavage or isomerization is not evaluated by this remote-alcohol model."
        if sum(a.GetAtomicNum() == 8 for a in molecule.GetAtomWithIdx(carbon).GetNeighbors()) != 1:
            return "rejected", "unvalidated", "Geminal-diol, hemiacetal or related multiple-oxygen carbon environments are not validated spectators."
        return "preserved", "validated", "This screened saturated aliphatic alcohol's C–O and O–H bonds and applicable specified configuration are preserved in the net edit; arbitrary catalyst/condition inertness is not assumed."
    if kind in {"alkyne", "aldehyde", "ketone", "carbonyl", "peroxide"}:
        return "rejected", "competition", f"Additional {kind} chemistry is potentially reducible or catalyst-dependent; hydrogenating only the selected C=C is not validated for this combination."
    if kind == "aromatic ring":
        return "rejected", "unvalidated", "Aromatic-containing hydrogenation needs catalyst-specific chemoselectivity validation; this increment does not assume an aromatic ring is either inert or necessarily reduced."
    return "rejected", "unvalidated", f"The additional {kind} group has no validated spectator policy for alkene hydrogenation in this increment. Distance alone does not make it inert."


def additional_check(molecule, site):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in site)
            if distance < 2:
                yield ("near-site-stereo", "unvalidated", f"Specified center at substrate atom {atom.GetIdx() + 1} is at/adjacent to the C=C; stereofacial compatibility is not validated by this remote-center retention increment.", [atom.GetIdx()])


POLICY = compatibility.SitePolicy("isolated-alkene hydrogenation", frozenset({"C", "H", "O"}),
                                  site_check, group_check, additional_check, added_atoms=2)


def assess(molecule, site):
    return compatibility.assess_site(molecule, site, POLICY)


def edit_contract(substrate, reagent, site):
    hydrogens = [a for a in reagent.GetAtoms() if a.GetAtomicNum() == 1]
    if (reagent.GetNumAtoms() != 2 or len(hydrogens) != 2 or reagent.GetNumBonds() != 1
            or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() for a in hydrogens)):
        raise ValueError("Alkene hydrogenation consumes an actual neutral H–H molecule, not an arbitrary hydrogen-containing reagent.")
    ends = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    hs = [a.GetAtomMapNum() for a in hydrogens]
    return [{"atomMaps": ends, "before": 2.0, "after": 1.0},
            {"atomMaps": hs, "before": 1.0, "after": None},
            *[{"atomMaps": [c, h], "before": None, "after": 1.0} for c, h in zip(ends, hs)]]


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagent, site)
    compatibility.validate_edit_contract(before, after, edits, consumed_double_bonds=[edits[0]["atomMaps"]], expected_fragments=1)
