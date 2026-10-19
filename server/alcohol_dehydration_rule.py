"""Sulfuric-acid alcohol dehydration: bounded net edits, not a protocol.

Primary substrates do not acquire an invented free primary carbocation.
Secondary/tertiary E1-type rationale is distinguished from mapped elementary
steps, which remain unimplemented (acid/proton exchange is not in the net).
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alcohol dehydration"
SOURCE = "https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc01038h"
LIMITATION = ("Selected-site unrearranged net elimination only. Acid is catalytic, not consumed. "
              "Primary alcohol mechanisms may involve concerted elimination/ether-mediated routes; no primary carbocation is invented. "
              "Secondary/tertiary alcohols have an E1-type rationale, not a resolved mapped acid cycle. "
              "Isomerization, ether formation, proton exchange, experimental completion and product ratios are not predicted.")


def distance(mol, a, b):
    return len(Chem.GetShortestPath(mol, a, b)) - 1 if a != b else 0


def classification(mol, site):
    return {1: "primary", 2: "secondary", 3: "tertiary"}.get(graph.substitution_degree(mol.GetAtomWithIdx(site[0])), "unsupported")


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, PATHWAY)
    if issue: return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None: return "Alcohol dehydration cannot validate the supplied stereo annotations."
    original = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    cleaned = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(original) != len(cleaned) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and
            (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL) for a, b in zip(original, cleaned)):
        return "Invalid or unsupported specified dehydration stereochemistry cannot be silently removed during input normalization."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional annotations without a valid C=C are unsupported in alcohol dehydration."
    return None


def site_issue(mol, site):
    if tuple(site) not in graph.find_alcohols(mol):
        return "Dehydration needs an ordinary neutral saturated C–OH site, not an ether, phenol or acid."
    carbon, oxygen = (mol.GetAtomWithIdx(i) for i in site)
    if carbon.IsInRing() or mol.GetRingInfo().NumRings():
        return "Cyclic alcohols and ring-containing dehydration require independently validated ring/rearrangement geometry; this increment is acyclic."
    if (classification(mol, site) == "unsupported" or carbon.GetHybridization() != Chem.HybridizationType.SP3
            or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1
            or any(n.GetAtomicNum() not in {1, 6, 8} for n in carbon.GetNeighbors())
            or sum(n.GetAtomicNum() == 1 for n in oxygen.GetNeighbors()) + oxygen.GetNumImplicitHs() + oxygen.GetNumExplicitHs() != 1):
        return "Geminal-O, hemiacetal or nonordinary alcohol environments need separate dehydration validation."
    # No borrowed alkyl-halide ionization permissions. Primary cases are
    # screened separately; secondary cations also screen a two-step shift risk.
    for neighbor in graph.carbon_neighbors(carbon):
        if neighbor.GetIsAromatic() or neighbor.GetHybridization() != Chem.HybridizationType.SP3:
            return "Allylic/benzylic/conjugated dehydration and resonance-site outcomes are not validated."
        if graph.substitution_degree(neighbor) >= 3:
            return "Adjacent branched/quaternary carbon permits hydride/alkyl migration; an unrearranged dehydration outcome is not asserted."
        if classification(mol, site) == "secondary":
            for other in graph.carbon_neighbors(neighbor):
                if other.GetIdx() != site[0] and graph.substitution_degree(other) >= 3:
                    return "Nearby branching permits a sequence of carbocation shifts; this secondary dehydration lacks a validated rearrangement model."
    return None


def beta_issue(mol, site):
    alpha, _, beta = site
    atom = mol.GetAtomWithIdx(beta); bond = mol.GetBondBetweenAtoms(alpha, beta)
    if (not bond or bond.GetBondType() != Chem.BondType.SINGLE or atom.GetAtomicNum() != 6
            or atom.GetHybridization() != Chem.HybridizationType.SP3 or not graph.attached_hydrogens(atom)):
        return "The selected beta position needs an actual saturated C–H bonded to alpha; no hydrogen, cumulene or aromatic elimination is invented."
    if atom.IsInRing() or any(n.GetAtomicNum() not in {1, 6} for n in atom.GetNeighbors()):
        return "Ring-bound or heteroatom-substituted beta elimination needs separate geometry/enol validation."
    return None


def sites(mol):
    return [(c, o, b) for c, o in graph.find_alcohols(mol) for b in graph.beta_hydrogens(mol, c)]


def equivalent_sites(mol, left, right):
    work = Chem.Mol(mol)
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    return any(tuple(match[i] for i in left) == tuple(right) for match in work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=1024))


def group_check(mol, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alcohol" and set(indices) == set(site):
        return "reactive", "validated", f"Selected {classification(mol, site)} C–OH; net water loss, not bare hydroxide departure."
    if kind in {"alcohol", "ether"}:
        oxygen = next(mol.GetAtomWithIdx(i) for i in indices if mol.GetAtomWithIdx(i).GetAtomicNum() == 8)
        ring = distance(mol, oxygen.GetIdx(), site[0]) + 1
        if ring <= 6:
            return "rejected", "competition", f"Potential {ring}-membered intramolecular oxygen capture or coupled dehydration is unresolved; this group is not an inert spectator."
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        if (len(carbons) != (1 if kind == "alcohol" else 2) or oxygen.IsInRing()
                or any(c.GetIsAromatic() or c.GetHybridization() != Chem.HybridizationType.SP3
                       or graph.substitution_degree(c) >= 3 or sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) != 1 for c in carbons)):
            return "rejected", "competition", "Acid-sensitive tertiary/benzylic/allylic, acetal or cyclic oxygen environments need separate cleavage/rearrangement validation."
        return "alternative-site" if kind == "alcohol" else "preserved", "bounded", "Screened remote oxygen bonds are retained for conditional 2D bookkeeping only; acid cleavage, additional dehydration and experimental one-site selectivity remain unresolved."
    return "rejected", "competition", f"Additional {kind} has no validated sulfuric-acid dehydration compatibility; unsupported does not mean chemically impossible."


POLICY = compatibility.SitePolicy("sulfuric-acid alcohol dehydration", frozenset({"C", "H", "O"}),
                                  site_issue, group_check, lambda mol, site: (), added_atoms=-3)


def assess(mol, site):
    if len(site) != 3 or len(set(site)) != 3 or any(type(i) is not int or not 0 <= i < mol.GetNumAtoms() for i in site):
        return {"version": 1, "policy": POLICY.name, "siteAtoms": list(site), "groups": [], "eligible": False,
                "rejections": [{"code": "invalid-site", "category": "structural", "message": "Select distinct alcohol alpha, oxygen and beta atoms.", "atomIndices": list(site)}]}
    report = compatibility.assess_site(mol, site[:2], POLICY); report["siteAtoms"] = list(site)
    issue = beta_issue(mol, site)
    if issue:
        report["rejections"].append({"code": "beta-environment", "category": "unvalidated", "message": issue, "atomIndices": [site[2]]})
        report["eligible"] = False
    report["alcoholClass"] = classification(mol, site)
    report["oxygenCompetition"] = any(g["type"] in {"alcohol", "ether"} and g["disposition"] in {"preserved", "alternative-site"} for g in report["groups"])
    return report


def participants(substrate, site):
    alpha, oxygen, beta = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    hydrogens = lambda i: sorted(n.GetAtomMapNum() for n in substrate.GetAtomWithIdx(i).GetNeighbors() if n.GetAtomicNum() == 1)
    hs, oh = hydrogens(site[2]), hydrogens(site[1])
    if not hs or len(oh) != 1: raise ValueError("Dehydration needs actual mapped beta H and one alcohol O–H.")
    return {"alpha": alpha, "oxygen": oxygen, "beta": beta, "betaHydrogen": hs[0], "originalOHHydrogen": oh[0]}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, site)
    return [{"atomMaps": [p["alpha"], p["oxygen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["beta"], p["betaHydrogen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["alpha"], p["beta"]], "before": 1.0, "after": 2.0},
            {"atomMaps": [p["oxygen"], p["betaHydrogen"]], "before": None, "after": 1.0}]


def edit(editor, substrate, site):
    if __package__: from .reaction_diagrams import _remove, _add, _order
    else: from reaction_diagrams import _remove, _add, _order
    p = participants(substrate, site)
    for e in edit_contract(substrate, None, site):
        a, b = e["atomMaps"]
        if e["after"] is None: _remove(editor, a, b)
        elif e["before"] is None: _add(editor, a, b)
        else: _order(editor, a, b, e["after"])
    for atom in editor.GetAtoms():
        if atom.GetAtomMapNum() in {p["alpha"], p["beta"]}: atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    editor.GetBondBetweenAtoms(*site[::2]).SetStereo(Chem.BondStereo.STEREONONE)


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    p = participants(substrate, site)
    atoms = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    bond = after.GetBondBetweenAtoms(atoms[p["alpha"]].GetIdx(), atoms[p["beta"]].GetIdx())
    if not bond or bond.GetBondTypeAsDouble() != 2 or bond.GetStereo() != Chem.BondStereo.STEREONONE:
        raise ValueError("Dehydration must form the selected unsigned C=C, not invent E/Z.")
    checked = Chem.Mol(before); Chem.AssignStereochemistry(checked, cleanIt=True, force=True)
    normalized = {a.GetAtomMapNum(): a for a in checked.GetAtoms()}
    source = Chem.Mol(before)
    for atom in source.GetAtoms():
        if atom.GetAtomMapNum() not in {p["alpha"], p["beta"]}: continue
        target = atoms[atom.GetAtomMapNum()]
        if (atom.GetAtomicNum() != 6 or atom.GetHybridization() != Chem.HybridizationType.SP3
                or target.GetHybridization() != Chem.HybridizationType.SP2 or target.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                or atom.GetChiralTag() in stereo.TETRAHEDRAL and normalized[atom.GetAtomMapNum()].GetChiralTag() not in stereo.TETRAHEDRAL):
            raise ValueError("Only valid participating sp3 carbons becoming unsigned sp2 may lose configuration.")
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    # Scoped comparison source erases ONLY the two checked planarized atoms.
    # Existing shared SN/E/oxidation stereo permissions remain unchanged.
    compatibility.validate_edit_contract(source, after, edit_contract(substrate, reagent, site), expected_fragments=2)
    water = next((f for f in Chem.GetMolFrags(after, asMols=True) if f.GetNumAtoms() == 3 and
                  {a.GetAtomMapNum() for a in f.GetAtoms()} == {p["oxygen"], p["betaHydrogen"], p["originalOHHydrogen"]}), None)
    if water is None: raise ValueError("Water must retain the actual alcohol O/OH-H and selected beta H in formal net bookkeeping.")


def metadata(substrate, product, site, report):
    p = participants(substrate, site)
    maps = {a.GetAtomMapNum(): a.GetIdx() for a in product.GetAtoms()}
    bond = product.GetBondBetweenAtoms(maps[p["alpha"]], maps[p["beta"]])
    unresolved = any(str(s.type) == "Bond_Double" and s.centeredOn == bond.GetIdx() for s in Chem.FindPotentialStereo(product))
    return {**p, "alcoholClass": report["alcoholClass"], "oxygenCompetition": report["oxygenCompetition"],
            "ezUnresolved": unresolved, "stereoisomerRatios": None, "acidConsumed": False,
            "mechanism": "primary net dehydration; no free primary carbocation assigned" if report["alcoholClass"] == "primary" else "E1-type rationale; complete mapped acid cycle unimplemented",
            "provenance": "Formal net O/OH-H/beta-H bookkeeping; catalyst/solvent proton exchange is not elementary isotope provenance."}


def assess_conditions(reaction, conditions):
    model = reaction["dehydrationModel"]
    catalyst, temperature, medium = (conditions.get(k, "") for k in ("catalyst", "temperature", "solvent"))
    missing = [k for k, value in (("catalyst", catalyst), ("temperature", temperature)) if not value]
    fields = {"solvent", "temperature", "catalyst", "oxidationStage", "additionStage", "polymerUnits", "workup"}
    unknown = set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - fields)
    issues = [{"field": k, "kind": "unsupported", "explanation": f"Condition field '{k}' is not evaluated for alcohol dehydration; no additional chemistry is inferred."} for k in sorted(unknown)]
    if catalyst and catalyst != "acid":
        issues.append({"field": "catalyst", "kind": "conflicting" if catalyst == "none" else "unsupported", "explanation": "catalyst: confirm the existing actual sulfuric-acid catalytic model; no acid-free, metal or radical dehydration is implemented."})
    if temperature and temperature != "heated":
        issues.append({"field": "temperature", "kind": "unvalidated-alternative", "explanation": "temperature: ambient dehydration may be possible for some alcohols, but this bounded heated model does not validate it. Primary ether formation and different activation temperatures are not resolved."})
    if medium not in {"", "dry"}:
        issues.append({"field": "solvent", "kind": "unvalidated-alternative", "explanation": "solvent: aqueous, alcoholic or generic polar-aprotic settings need acid/substrate-specific validation; water affects reversibility and alcohol capture can form ethers. This is not proof that all such media prevent dehydration."})
    for key in ("oxidationStage", "workup"):
        if conditions.get(key): issues.append({"field": key, "kind": "conflicting", "explanation": f"{key} belongs to another reaction model; clear it rather than infer coupled chemistry."})
    limitations = []
    if model["oxygenCompetition"]:
        limitations.append("Remote oxygen/other alcohol sites can react under acid. This preserved-spectator single-site equation is conditional 2D bookkeeping only, not selective experimental dehydration.")
    if model["ezUnresolved"]:
        limitations.append("The new alkene admits unresolved E/Z alternatives. Geometry remains unassigned; no single 3D stereochemical product or ratio is asserted.")
    allowed = not missing and not issues and not limitations
    status = "unsupported-pathway" if any(i["kind"] == "unsupported" for i in issues) else "activation-required" if catalyst == "none" else "missing" if missing else "unevaluated" if issues or limitations else "model-match"
    guidance = ["Structurally supported dehydration site."]
    if missing: guidance.append("Missing required model settings: " + ", ".join(missing) + ".")
    guidance.extend(i["explanation"] for i in issues); guidance.extend(limitations)
    guidance.append("Sulfuric acid is regenerated, not consumed; heated/unspecified-or-dry medium is a bounded net assumption, not a complete experimental protocol. Ether formation, isomerization, exact temperature and conversion are not predicted.")
    return {"state": "aligned" if allowed else "incomplete", "status": status, "label": "Heated acid net model" if allowed else "Dehydration conditions or product confidence incomplete",
            "confidenceLabel": "Acid dehydration net model · outcome not predicted" if allowed else "Dehydration conditions/stereo unresolved · conditional 2D only",
            "canRun": allowed, "missingSettings": missing, "conditionIssues": issues, "referenceDifferences": [],
            "note": " ".join(guidance), "reagentValidated": True, "reagentRequirement": "actual sulfuric acid, catalytic and excluded from the net equation",
            "activationRequirement": "confirmed acid and heated model", "factors": {
                "catalyst": {"status": "model-match" if catalyst == "acid" else "missing" if not catalyst else "unevaluated", "effect": "neutral" if catalyst == "acid" else "unknown", "explanation": "Actual acid catalysis, not bare OH departure; acid is not a consumed amount."},
                "temperature": {"status": "model-match" if temperature == "heated" else "missing" if not temperature else "unevaluated", "effect": "neutral" if temperature == "heated" else "unknown", "explanation": "Heated net-model confirmation is required; no exact temperature or ether/alkene distribution is established."},
                "solvent": {"status": "unevaluated", "effect": "unknown", "explanation": "Exact medium, water activity and concentration are not established by these selectors."},
                "competing chemistry": {"status": "unevaluated", "effect": "unknown", "explanation": " ".join(limitations) or "Ether formation, sulfate ester intermediates, later isomerization and experimental product distributions are outside the net model."}}}
