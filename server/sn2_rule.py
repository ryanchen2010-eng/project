"""Hydroxide-only SN2 site compatibility and independent mapped inversion.

Preserves existing methyl/primary/selected secondary/benzylic scope. Spectators
are screened specifically for base and neighboring-group chemistry, not copied
from reduction or oxidation whitelists. Net options never predict efficiency.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility
else:
    import molecular_graph as graph, reaction_compatibility as compatibility

SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction"
CYCLIZATION_SOURCE = "https://openstax.org/books/organic-chemistry/pages/18-4-cyclic-ethers-epoxides"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")
NONALKYL_HALIDE = Chem.MolFromSmarts("[#6;!X4]-[F,Cl,Br,I]")


def sites(molecule):
    return graph.find_alkyl_halides(molecule)


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def site_check(molecule, site):
    if tuple(site) not in sites(molecule):
        return "SN2 needs an actual single C(sp³)–Cl/Br/I bond; aryl/vinyl bonds, fluoride and other leaving-group families are not this site."
    carbon = molecule.GetAtomWithIdx(site[0])
    if carbon.IsInRing():
        return "Ring-bound SN2 electrophiles still need separate backside-access and conformational validation."
    if graph.is_allylic_or_benzylic(carbon) and not any(n.GetIsAromatic() for n in graph.carbon_neighbors(carbon)):
        return "Allylic SN2/SN2′ regioselectivity remains outside this increment; no automatic allylic expansion."
    if graph.substitution_degree(carbon) > 2:
        return "Ordinary tertiary alkyl halides do not match this SN2 pathway; backside access is not supported."
    if any(graph.substitution_degree(n) >= 4 for n in graph.carbon_neighbors(carbon)):
        return "Neopentyl-type neighboring quaternary-carbon hindrance remains excluded from this SN2 model."
    if any(n.GetIdx() != site[1] and n.GetAtomicNum() not in {1, 6} for n in carbon.GetNeighbors()):
        return "Geminal halides or heteroatoms directly on the electrophilic carbon need separate substitution/cleavage validation."
    return None


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "haloalkane":
        other = next((s for s in sites(molecule) if set(s) == set(indices)), None)
        if other is None:
            return "rejected", "unvalidated", "This alkyl-halide group has no actual validated C(sp³)–Cl/Br/I site."
        if set(other) == set(site):
            issue = site_check(molecule, site)
            if issue:
                return "rejected", "unvalidated", "Selected SN2 site: " + issue
            return "reactive", "validated", "The selected C–halogen bond breaks as the actual hydroxide oxygen forms C–O; a specified reacting center inverts physically."
        issue = site_check(molecule, other)
        if issue:
            chosen, remote = (molecule.GetAtomWithIdx(s[0]) for s in (site, other))
            # Narrow independent primary-site permission. Five C–C edges keep
            # product OH -> remote C–X closure beyond the screened 3–6 rings.
            screened = (graph.substitution_degree(chosen) <= 1
                        and graph.substitution_degree(remote) == 3
                        and distance(molecule, site[0], other[0]) >= 5
                        and not remote.IsInRing()
                        and all(n.GetAtomicNum() in {1, 6} for n in remote.GetNeighbors() if n.GetIdx() != other[1])
                        and all(n.GetHybridization() == Chem.HybridizationType.SP3 and not n.IsInRing()
                                for n in graph.carbon_neighbors(remote)))
            if screened:
                return "preserved", "bounded", "The screened distant ordinary tertiary C–X is NOT SN2-eligible and stays mapped/unchanged while this primary site substitutes. Hydroxide-driven elimination at that other site can compete when beta H exists; larger-ring/product-OH chemistry and selective mono-substitution are not predicted."
            return "rejected", "competition", "Additional C–X at substrate atoms " + ", ".join(str(i + 1) for i in other) + ": " + issue + " Independent-site competition/retention is not validated for this environment."
        return "alternative-site", "bounded", "Another eligible alkyl halide stays unchanged in this one-site net option. Further substitution, elimination and product-OH cyclization may compete; selective mono-substitution is not predicted."
    if kind == "alcohol":
        other = next((s for s in graph.find_alcohols(molecule) if set(s) == set(indices)), None)
        if other is None:
            return "rejected", "unvalidated", "This OH is not an ordinary neutral saturated alcohol."
        carbon, oxygen = other
        if sum(n.GetAtomicNum() == 8 for n in molecule.GetAtomWithIdx(carbon).GetNeighbors()) != 1:
            return "rejected", "unvalidated", "Hemiacetal/geminal-diol alcohol environments require their own base/substitution policy."
        for electrophile, _ in sites(molecule):
            issue = compatibility.oxygen_closure_issue(molecule, oxygen, electrophile, "SN2")
            if issue:
                return "rejected", *issue
        return "preserved", "bounded", "This screened remote saturated OH retains its C–O/O–H bonds in the net edit. Base–alcohol proton equilibria, intermolecular ether formation and larger-ring cyclization are not experimentally excluded or predicted."
    if kind == "ether":
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None or oxygen.GetDegree() != 2:
            return "rejected", "unvalidated", "This ether lacks an ordinary neutral two-carbon oxygen environment."
        if distance(molecule, oxygen.GetIdx(), site[0]) < 3:
            return "rejected", "unvalidated", "An ether oxygen near the electrophile needs neighboring-group/substitution validation; this increment screens remote ethers."
        if all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Diaryl ether spectator compatibility is not generalized in this increment."
        for carbon in oxygen.GetNeighbors():
            if (carbon.GetAtomicNum() != 6 or molecule.GetBondBetweenAtoms(carbon.GetIdx(), oxygen.GetIdx()).GetBondType() != Chem.BondType.SINGLE
                    or (not carbon.GetIsAromatic() and carbon.GetHybridization() != Chem.HybridizationType.SP3)):
                return "rejected", "unvalidated", "Unsaturated/enol or nonordinary ethers are not validated SN2 spectators."
            if sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1:
                return "rejected", "unvalidated", "Acetal/ketal and multiple-oxygen carbon environments need a separate compatibility policy."
        return "preserved", "bounded", "This screened remote dialkyl/carbocyclic aryl–alkyl ether keeps its bonds in the net substitution; neighboring-group participation and reagent-specific stability are not experimentally predicted."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic substrates require a separate SN2/base compatibility policy."
        return "preserved", "bounded", "The carbocyclic aromatic skeleton is retained. Existing benzylic net options remain bounded; no SN1/E2 competition or experimental preference is predicted."
    if kind in {"alkene", "alkyne"}:
        return "rejected", "unvalidated", f"Additional {kind} environments are not validated spectators in this SN2 increment; allylic/propargylic or other competing chemistry is not silently enabled."
    return "rejected", "unvalidated", f"The additional {kind} group has no validated hydroxide/SN2 compatibility policy; unsupported does not imply chemically incapable of substitution."


def additional_check(molecule, site):
    return ()


POLICY = compatibility.SitePolicy("hydroxide SN2 substitution", frozenset({"C", "H", "O", "Cl", "Br", "I"}),
                                  site_check, group_check, additional_check, added_atoms=1,
                                  extra_groups=(("ether", ETHER_QUERY), ("non-alkyl halide", NONALKYL_HALIDE)))


def assess(molecule, site):
    return compatibility.assess_site(molecule, site, POLICY)


def nucleophile(reagent):
    oxygens = [a for a in reagent.GetAtoms() if a.GetAtomicNum() == 8]
    if (len(oxygens) != 1 or reagent.GetNumAtoms() != 2 or reagent.GetNumBonds() != 1
            or oxygens[0].GetFormalCharge() != -1 or graph.attached_hydrogens(oxygens[0]) != 1
            or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetAtomicNum() not in {1, 8} or (a.GetAtomicNum() == 1 and a.GetFormalCharge())
                   or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in reagent.GetAtoms())):
        raise ValueError("This SN2 consumes one actual OH⁻ ion; other nucleophiles are not substituted by name or formula.")
    return oxygens[0]


def substitution(substrate, reagent, site):
    return {"center": substrate.GetAtomWithIdx(site[0]).GetAtomMapNum(),
            "leaving": substrate.GetAtomWithIdx(site[1]).GetAtomMapNum(), "incoming": nucleophile(reagent).GetAtomMapNum()}


def edit_contract(substrate, reagent, site):
    s = substitution(substrate, reagent, site)
    return [{"atomMaps": [s["center"], s["leaving"]], "before": 1.0, "after": None},
            {"atomMaps": [s["center"], s["incoming"]], "before": None, "after": 1.0}]


def charge_contract(substrate, reagent, site):
    s = substitution(substrate, reagent, site)
    return [{"atomMap": s["leaving"], "before": 0, "after": -1}, {"atomMap": s["incoming"], "before": -1, "after": 0}]


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    compatibility.validate_edit_contract(before, after, edit_contract(substrate, reagent, site),
                                        charge_changes=charge_contract(substrate, reagent, site),
                                        inverted_substitutions=[substitution(substrate, reagent, site)], expected_fragments=2)
