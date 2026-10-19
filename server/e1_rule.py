"""Water E1: screened ionization, saturated beta H, unsigned alkene options.

One-site unrearranged net pathways, not selective solvolysis or a kinetic model.
No E2 anti permission, blanket secondary acceptance or arbitrary allylic allene.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, sn1_rule, carbocation_compatibility as carbocation
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, sn1_rule, carbocation_compatibility as carbocation

SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions"
SECONDARY_SOURCE = "https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")
NONALKYL_HALIDE = Chem.MolFromSmarts("[#6;!X4]-[F,Cl,Br,I]")


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def restricted_allyl(molecule, halide):
    """CH2=C(R)–C(X)(R')R'' or –CH(X)R', with saturated alkyl groups.

The central pi carbon has no H: the other formal cation contributor cannot
lose a beta H at that sp2 carbon to form a cumulated diene. Only ordinary
saturated beta-H loss at the original secondary/tertiary carbon is represented.
No substitution/regioselectivity permission is passed to SN1/SN2/E2.
"""
    alpha = molecule.GetAtomWithIdx(halide[0])
    if graph.substitution_degree(alpha) not in {2, 3}:
        return None
    middles = [n for n in graph.carbon_neighbors(alpha) if not n.GetIsAromatic() and n.GetHybridization() == Chem.HybridizationType.SP2]
    if len(middles) != 1:
        return None
    middle = middles[0]
    double = [b for b in middle.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(middle).GetAtomicNum() == 6]
    if len(double) != 1 or graph.attached_hydrogens(middle):
        return None
    end = double[0].GetOtherAtom(middle)
    remaining = [n for n in graph.carbon_neighbors(middle) if n.GetIdx() not in {alpha.GetIdx(), end.GetIdx()}]
    if (graph.attached_hydrogens(end) != 2 or len(graph.carbon_neighbors(end)) != 1 or len(remaining) != 1
            or double[0].GetStereo() != Chem.BondStereo.STEREONONE or any(a.IsInRing() for a in (alpha, middle, end))
            or any(n.GetAtomicNum() not in {1, 6} for n in middle.GetNeighbors())
            or remaining[0].GetHybridization() != Chem.HybridizationType.SP3 or remaining[0].GetIsAromatic()
            or any(n.GetIdx() != middle.GetIdx() and (n.GetHybridization() != Chem.HybridizationType.SP3 or n.GetIsAromatic()) for n in graph.carbon_neighbors(alpha))):
        return None
    return middle.GetIdx(), end.GetIdx()


def small_secondary(molecule, halide):
    return carbocation.small_secondary(molecule, halide)

def classification(molecule, halide):
    alpha = molecule.GetAtomWithIdx(halide[0])
    if any(n.GetIsAromatic() for n in graph.carbon_neighbors(alpha)):
        return "benzylic resonance"
    if restricted_allyl(molecule, halide):
        return "bounded allylic resonance"
    return carbocation.alkyl_basis(molecule, halide) or "unsupported cation environment"

def halide_issue(molecule, halide):
    return carbocation.halide_issue(molecule, halide, "E1")

def cation_issue(molecule, halide):
    issue = halide_issue(molecule, halide)
    if issue:
        return issue
    allyl = restricted_allyl(molecule, halide)
    if classification(molecule, halide) == "unsupported cation environment":
        return "Ordinary primary/methyl E1 ionization is excluded; secondary aliphatic sites are assessed individually and only the screened Me/Me or Me/Et arm scope is enabled. Other secondary environments need rearrangement validation, not an impossibility claim."
    return carbocation.rearrangement_issue(molecule, halide, "E1", resonance_neighbors=(allyl[0],) if allyl else (), saturated_neighbors=True)

def beta_issue(molecule, halide, beta):
    alpha = halide[0]; atom = molecule.GetAtomWithIdx(beta)
    bond = molecule.GetBondBetweenAtoms(alpha, beta)
    if (bond is None or bond.GetBondType() != Chem.BondType.SINGLE or atom.GetAtomicNum() != 6
            or atom.GetHybridization() != Chem.HybridizationType.SP3 or not graph.attached_hydrogens(atom)):
        return "E1 needs an actual saturated beta C–H single-bonded to alpha; aromatic/sp2 beta removal, cumulenes and invented hydrogens are not enabled."
    if atom.IsInRing() or bond.IsInRing():
        return "Ring-bound beta elimination/exocyclic alkene geometry requires separate E1 validation."
    if any(n.GetAtomicNum() not in {1, 6} for n in atom.GetNeighbors()):
        return "A heteroatom or halide on beta creates unvalidated enol/vinyl or coupled elimination chemistry."
    return None


def sites(molecule):
    work = Chem.Mol(molecule)
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    ranks = list(Chem.CanonicalRankAtoms(work, breakTies=False))
    result = []
    for alpha, leaving in graph.find_alkyl_halides(molecule):
        seen = set()
        for beta in graph.beta_hydrogens(molecule, alpha):
            if ranks[beta] not in seen:
                result.append((alpha, leaving, beta)); seen.add(ranks[beta])
    return result


def group_check(molecule, halide, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "haloalkane":
        other = next((s for s in graph.find_alkyl_halides(molecule) if set(s) == set(indices)), None)
        issue = halide_issue(molecule, other) if other else "This halide lacks a supported E1 carbon environment."
        if issue: return "rejected", "unvalidated", issue
        if set(other) == set(halide):
            return "reactive", "validated", f"Selected {classification(molecule, halide)}: ionization precedes separate solvent beta-H removal, not concerted E2."
        if distance(molecule, halide[0], other[0]) < 3:
            return "rejected", "competition", "Nearby multiple halides can have coupled ionization/elimination; independent E1 sites require separation."
        issue = cation_issue(molecule, other)
        if issue is None:
            return "alternative-site", "bounded", "Another screened ionizable C–X remains unchanged in this one-site E1 option. Subsequent SN1/E1 and selective mono-conversion are not predicted."
        carbon = molecule.GetAtomWithIdx(other[0])
        if graph.substitution_degree(carbon) <= 1 and not graph.is_allylic_or_benzylic(carbon):
            return "preserved", "bounded", "This separated ordinary primary C–X is retained without granting primary E1 ionization; other later chemistry is not claimed absent."
        return "rejected", "competition", "An additional halide has unvalidated competing ionization: " + issue
    if kind in {"alcohol", "ether"}:
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None: return "rejected", "unvalidated", "No ordinary E1 oxygen spectator environment."
        for other in graph.find_alkyl_halides(molecule):
            if classification(molecule, other) != "unsupported cation environment":
                allyl = restricted_allyl(molecule, other)
                targets = [other[0], *([allyl[1]] if allyl else [])]
                for target in targets:
                    size = distance(molecule, oxygen.GetIdx(), target) + 1
                    if size <= 3:
                        return "rejected", "unvalidated", "Direct/vicinal oxygen needs separate oxocarbenium/neighboring-group E1 validation."
                    if size <= 6:
                        return "rejected", "competition", f"Potential {size}-membered intramolecular oxygen-to-carbocation capture competes with E1; cyclization is not resolved."
        if kind == "alcohol":
            other = next((s for s in graph.find_alcohols(molecule) if set(s) == set(indices)), None)
            if other is None: return "rejected", "unvalidated", "Only ordinary saturated primary/secondary distant OH is screened for E1."
            carbon = molecule.GetAtomWithIdx(other[0])
            if graph.substitution_degree(carbon) >= 3 or graph.is_allylic_or_benzylic(carbon) or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1:
                return "rejected", "competition", "Acid-sensitive tertiary/benzylic/allylic or geminal-O alcohols can ionize/dehydrate under heated solvolysis; distant alone is not inert."
            return "preserved", "bounded", "Screened distant ordinary OH retains its net bonds; proton equilibria, larger-ring/intermolecular capture, dehydration and acid accumulation are not generally predicted."
        if oxygen.GetDegree() != 2 or all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Only ordinary distant dialkyl/aryl–alkyl ethers are screened for water E1."
        for carbon in oxygen.GetNeighbors():
            if carbon.GetAtomicNum() != 6 or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1 or (not carbon.GetIsAromatic() and (carbon.GetHybridization() != Chem.HybridizationType.SP3 or graph.substitution_degree(carbon) >= 3 or graph.is_allylic_or_benzylic(carbon))):
                return "rejected", "competition", "Acid-sensitive tertiary/benzyl/allyl, enol or acetal/ketal ethers have unvalidated cleavage/capture under heated E1 conditions."
        return "preserved", "bounded", "Screened distant ordinary ether retains its C–O bonds; strong-acid cleavage, larger-ring capture and experimental stability are not inferred from the medium selector."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic protonation/resonance/capture is outside water E1 scope."
        return "preserved", "bounded", "Carbocyclic aromatic bonds remain unchanged; benzylic cations are shown as formal resonance contributors, not localized charge-density predictions."
    if kind == "alkene":
        allyl = restricted_allyl(molecule, halide)
        if allyl and set(indices) == set(allyl):
            return "preserved", "bounded", "This terminal CH2=C(R) pi bond is retained in the bounded allylic E1 contributor; the central pi carbon has no H. Other resonance-site/cumulene products and ratios are not generated."
        return "rejected", "competition", "Additional or unequal unsaturation can allow cationic cyclization/conjugated regioisomers; it is not an E1 spectator by default."
    return "rejected", "unvalidated", f"The additional {kind} lacks a validated water E1 compatibility policy; unsupported is not chemically impossible."


POLICY = compatibility.SitePolicy("water E1 elimination", frozenset({"C", "H", "O", "Cl", "Br", "I"}),
                                  cation_issue, group_check, lambda molecule, site: (), added_atoms=-2,
                                  extra_groups=(("ether", ETHER_QUERY), ("non-alkyl halide", NONALKYL_HALIDE)))


def assess(molecule, site):
    if len(site) != 3 or len(set(site)) != 3 or any(type(i) is not int or not 0 <= i < molecule.GetNumAtoms() for i in site):
        return {"version": 1, "policy": POLICY.name, "siteAtoms": list(site), "groups": [], "eligible": False,
                "rejections": [{"code": "invalid-site", "category": "structural", "message": "Select distinct E1 alpha, leaving atom and beta carbon.", "atomIndices": list(site)}]}
    report = compatibility.assess_site(molecule, site[:2], POLICY)
    report["siteAtoms"] = list(site)
    issue = beta_issue(molecule, site[:2], site[2])
    if issue:
        report["rejections"].append({"code": "beta-environment", "category": "unvalidated", "message": issue, "atomIndices": [site[2]]})
        report["eligible"] = False
    return report


def water_oxygen(molecule):
    try: return sn1_rule.water_oxygen(molecule)
    except ValueError as exc: raise ValueError("E1 uses actual neutral solvent water, not hydroxide, alcohol or an assumed base.") from exc


def participants(substrate, site, stage="net", solvent=None):
    alpha, leaving, beta = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    hs = sorted(n.GetAtomMapNum() for n in substrate.GetAtomWithIdx(site[2]).GetNeighbors() if n.GetAtomicNum() == 1)
    if not hs: raise ValueError("E1 needs an actual mapped beta hydrogen.")
    s = {"alpha": alpha, "leaving": leaving, "beta": beta, "hydrogen": hs[0], "stage": stage}
    if stage not in {"net", "ionization", "elimination"}: raise ValueError("Unknown E1 stage.")
    if stage != "net":
        if solvent is None: raise ValueError("E1 mechanism needs explicit solvent water.")
        s["base"] = water_oxygen(solvent).GetAtomMapNum()
    return s


def stage_edits(s):
    a, x, b, h = (s[k] for k in ("alpha", "leaving", "beta", "hydrogen"))
    definitions = {"net": [(a, x, 1, None), (b, h, 1, None), (a, b, 1, 2), (x, h, None, 1)],
                   "ionization": [(a, x, 1, None)],
                   "elimination": [(b, h, 1, None), (a, b, 1, 2), (s.get("base"), h, None, 1)]}
    if s["stage"] not in definitions: raise ValueError("Unknown E1 stage.")
    return [{"atomMaps": [a, b], "before": before, "after": after} for a, b, before, after in definitions[s["stage"]]]


def stage_charges(s):
    changes = {"net": [], "ionization": [(s["alpha"], 0, 1), (s["leaving"], 0, -1)],
               "elimination": [(s["alpha"], 1, 0), (s.get("base"), 0, 1)]}
    if s["stage"] not in changes: raise ValueError("Unknown E1 stage.")
    return [{"atomMap": m, "before": before, "after": after} for m, before, after in changes[s["stage"]]]


def edit_contract(substrate, reagent, site):
    # Net equation excludes solvent water and reports HX as released acid.
    return stage_edits(participants(substrate, site))


def apply_stereo(editor, s):
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    atoms[s["alpha"]].SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    if s["stage"] != "ionization":
        atoms[s["beta"]].SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        editor.GetBondBetweenAtoms(atoms[s["alpha"]].GetIdx(), atoms[s["beta"]].GetIdx()).SetStereo(Chem.BondStereo.STEREONONE)


def validate(before, after, substrate, site, stage="net", solvent=None):
    report = assess(substrate, site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    s = participants(substrate, site, stage, solvent)
    compatibility.validate_edit_contract(before, after, stage_edits(s), charge_changes=stage_charges(s),
                                        e1_eliminations=[s], expected_fragments={"net": 2, "ionization": 3, "elimination": 3}[stage])
