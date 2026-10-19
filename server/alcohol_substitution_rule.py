"""Actual HX/alcohol substitution: activated-water net edits, not a protocol.

No new reagents or alkyl-halide SN permissions. Secondary/benzylic mechanisms
and acid-sensitive spectators stay conditional; no universal inversion claim.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

PATHWAY = "Alcohol substitution"
SOURCE = "https://onlinelibrary.wiley.com/doi/abs/10.1002/jctb.5010050104"
ETHER_SOURCE = "https://pubs.rsc.org/en/content/articlelanding/2017/ob/c7ob01096f"


def distance(mol, a, b):
    return len(Chem.GetShortestPath(mol, a, b)) - 1 if a != b else 0


def sites(mol):
    return graph.find_alcohols(mol)


def classification(mol, site):
    carbon = mol.GetAtomWithIdx(site[0])
    aromatic = [n for n in graph.carbon_neighbors(carbon) if n.GetIsAromatic()]
    if aromatic: return "primary benzylic" if graph.substitution_degree(carbon) == 1 and len(aromatic) == 1 else "unsupported benzylic"
    return {0: "methyl", 1: "primary", 2: "secondary", 3: "tertiary"}.get(graph.substitution_degree(carbon), "unsupported")


def hydrogen_halide(reagent):
    atoms = list(reagent.GetAtoms())
    halogens = [a for a in atoms if a.GetSymbol() in {"Cl", "Br", "I"}]
    if (len(halogens) != 1 or len(atoms) not in {1, 2} or len(Chem.GetMolFrags(reagent)) != 1
            or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in atoms)
            or any(a.GetAtomicNum() != 1 and a.GetIdx() != halogens[0].GetIdx() for a in atoms)
            or graph.attached_hydrogens(halogens[0]) != 1
            or (len(atoms) == 2 and (reagent.GetNumBonds() != 1 or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE))):
        raise ValueError("Alcohol substitution consumes actual neutral HCl/HBr/HI with its H–X bond; bare halide, hydroxide, HF and alternative activators are not HX activation.")
    return halogens[0]


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, PATHWAY)
    if issue: return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None: return "Alcohol substitution cannot validate supplied stereochemistry."
    original = [a for a in raw.GetAtoms() if a.GetAtomicNum() != 1]
    cleaned = [a for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    if len(original) != len(cleaned) or any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and
            (a.GetChiralTag() not in stereo.TETRAHEDRAL or b.GetChiralTag() not in stereo.TETRAHEDRAL) for a, b in zip(original, cleaned)):
        return "Invalid/unsupported specified alcohol-substitution stereochemistry cannot be silently normalized away."
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return "Directional annotations without a valid C=C are unsupported in alcohol substitution."
    return None


def site_issue(mol, site):
    if tuple(site) not in sites(mol): return "Select an ordinary neutral saturated C–OH, not ether, phenol, acid or unactivated halide."
    carbon, oxygen = (mol.GetAtomWithIdx(i) for i in site)
    kind = classification(mol, site)
    if (carbon.IsInRing() or carbon.GetHybridization() != Chem.HybridizationType.SP3
            or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1
            or any(n.GetAtomicNum() not in {1, 6, 8} for n in carbon.GetNeighbors())
            or graph.attached_hydrogens(oxygen) != 1):
        return "Ring-bound, geminal-O/hemiacetal or directly heteroatom-substituted alcohols need independent activation/neighboring-group validation."
    if kind.startswith("unsupported"): return "Secondary/tertiary benzylic or other complex carbocation environments lack independently validated HX substitution outcomes."
    # A phenyl ring may be a spectator, not a general permission for cyclic
    # alcohols, fused systems or ring-bound displacement.
    if any(len(r) != 6 or not all(mol.GetAtomWithIdx(i).GetAtomicNum() == 6 and mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)
           for r in mol.GetRingInfo().AtomRings()):
        return "Only isolated carbocyclic phenyl spectators are screened; complex/cyclic alcohol substitution is not generalized."
    rings = mol.GetRingInfo().AtomRings()
    if any(set(a) & set(b) for i, a in enumerate(rings) for b in rings[i + 1:]):
        return "Fused aromatic/resonance systems need independent HX compatibility validation."
    for neighbor in graph.carbon_neighbors(carbon):
        if neighbor.GetIsAromatic() and kind == "primary benzylic": continue
        if neighbor.GetHybridization() != Chem.HybridizationType.SP3:
            return "Allylic/propargylic resonance, rearranged capture and multiple incoming positions are not validated."
        if graph.substitution_degree(neighbor) >= 3:
            return "Adjacent branching introduces hindrance and/or hydride/alkyl migration; no unrearranged HX product is asserted."
        if kind == "secondary" and any(other.GetIdx() != site[0] and graph.substitution_degree(other) >= 3 for other in graph.carbon_neighbors(neighbor)):
            return "Nearby branching can permit sequential carbocation shifts; secondary HX selectivity is unvalidated."
    return None


def group_check(mol, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alcohol" and set(indices) == set(site):
        return "reactive", "validated", "Actual HX activates OH to water and supplies the incoming halogen; bare hydroxide departure is not an elementary step."
    if kind in {"alcohol", "ether"}:
        oxygen = next(mol.GetAtomWithIdx(i) for i in indices if mol.GetAtomWithIdx(i).GetAtomicNum() == 8)
        ring = distance(mol, oxygen.GetIdx(), site[0]) + 1
        if ring <= 6:
            return "rejected", "competition", f"Potential {ring}-membered intramolecular oxygen capture/neighboring-group participation competes with HX substitution; this is not an inert spectator."
        carbons = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 6]
        if (len(carbons) != (1 if kind == "alcohol" else 2) or oxygen.IsInRing()
                or any(c.GetHybridization() != Chem.HybridizationType.SP3 or c.GetIsAromatic()
                       or graph.substitution_degree(c) >= 3 or sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) != 1 for c in carbons)):
            return "rejected", "competition", "Acid-sensitive tertiary, benzylic, allylic, cyclic or acetal oxygen environments require their own HX cleavage/capture policy."
        return "alternative-site" if kind == "alcohol" else "preserved", "bounded", "Screened remote oxygen is preserved only in conditional 2D bookkeeping. HX can substitute other OH or cleave ethers; no selective one-site experimental product is asserted."
    if kind == "aromatic ring":
        if any(mol.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic protonation/capture is outside this HX model."
        if any(n.GetAtomicNum() not in {1, 6} for i in indices for n in mol.GetAtomWithIdx(i).GetNeighbors() if n.GetIdx() not in indices):
            return "rejected", "competition", "Activated/heteroatom-substituted aromatic rings require separate HX compatibility checks."
        return "preserved", "bounded", "An isolated unactivated phenyl skeleton is retained in the net graph; no aromatic reaction or benzyl cation rate is predicted."
    return "rejected", "competition", f"Additional {kind} is not a validated HX substitution spectator; unsupported does not mean chemically impossible."


POLICY = compatibility.SitePolicy("activated HX alcohol substitution", frozenset({"C", "H", "O"}), site_issue, group_check, lambda mol, site: (), added_atoms=-1)


def assess(mol, reagent, site):
    report = compatibility.assess_site(mol, site, POLICY)
    if len(site) != 2 or any(type(i) is not int or not 0 <= i < mol.GetNumAtoms() for i in site): return report
    try:
        halogen = hydrogen_halide(reagent).GetSymbol()
        report["hydrogenHalide"] = "H" + halogen
        if halogen == "Cl" and classification(mol, site) != "tertiary":
            raise ValueError("Primary/secondary/benzylic alcohol chlorination needs independently validated activation outside this existing tertiary-HCl model; no ZnCl2, SOCl2 or PBr3 mode is added.")
    except ValueError as exc:
        report["rejections"].append({"code": "activation-reagent", "category": "unvalidated", "message": str(exc), "atomIndices": []})
        report["eligible"] = False
    report["alcoholClass"] = classification(mol, site)
    report["oxygenCompetition"] = any(g["type"] in {"alcohol", "ether"} and g["disposition"] in {"preserved", "alternative-site"} for g in report["groups"])
    return report


def participants(substrate, reagent, site):
    carbon, oxygen = (substrate.GetAtomWithIdx(i) for i in site)
    x = hydrogen_halide(reagent)
    hs = [n for n in x.GetNeighbors() if n.GetAtomicNum() == 1]
    oh = [n for n in oxygen.GetNeighbors() if n.GetAtomicNum() == 1]
    if len(hs) != 1 or len(oh) != 1: raise ValueError("HX substitution requires explicit mapped H–X and alcohol O–H.")
    return {"center": carbon.GetAtomMapNum(), "oxygen": oxygen.GetAtomMapNum(), "incoming": x.GetAtomMapNum(),
            "reagentHydrogen": hs[0].GetAtomMapNum(), "originalOHHydrogen": oh[0].GetAtomMapNum()}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": [p["center"], p["oxygen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["incoming"], p["reagentHydrogen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["center"], p["incoming"]], "before": None, "after": 1.0},
            {"atomMaps": [p["oxygen"], p["reagentHydrogen"]], "before": None, "after": 1.0}]


def edit(editor, substrate, reagent, site):
    if __package__: from .reaction_diagrams import _remove, _add
    else: from reaction_diagrams import _remove, _add
    for e in edit_contract(substrate, reagent, site):
        (_remove if e["after"] is None else _add)(editor, *e["atomMaps"])
    # Neither an unspecified HX medium nor a secondary substrate establishes
    # inversion/retention. This is explicit uncertainty, NOT SN1 proof.
    editor.GetAtomWithIdx(site[0]).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, reagent, site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    p = participants(substrate, reagent, site)
    source = Chem.Mol(before)
    original = {a.GetAtomMapNum(): a for a in source.GetAtoms()}; targets = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    old, new = original[p["center"]], targets[p["center"]]
    checked = Chem.Mol(before); Chem.AssignStereochemistry(checked, cleanIt=True, force=True)
    checked_center = next(a for a in checked.GetAtoms() if a.GetAtomMapNum() == p["center"])
    if old.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and (old.GetChiralTag() not in stereo.TETRAHEDRAL or checked_center.GetChiralTag() not in stereo.TETRAHEDRAL):
        raise ValueError("Invalid specified reacting-center stereo cannot be silently removed by HX substitution.")
    if (old.GetAtomicNum() != 6 or old.GetDegree() != 4 or new.GetDegree() != 4
            or new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
            or {n.GetAtomMapNum() for n in new.GetNeighbors()} != ({n.GetAtomMapNum() for n in old.GetNeighbors()} - {p["oxygen"]}) | {p["incoming"]}):
        raise ValueError("HX substitution must replace the selected alcohol oxygen at the same tetrahedral carbon without inventing configuration.")
    # Exact local replacement authorized here, not a new shared SN1/SN2 stereo
    # escape hatch. All distant physical stereo and serialization still checked.
    old.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    compatibility.validate_edit_contract(source, after, edit_contract(substrate, reagent, site), expected_fragments=2)
    water_maps = {p["oxygen"], p["originalOHHydrogen"], p["reagentHydrogen"]}
    if not any({a.GetAtomMapNum() for a in f.GetAtoms()} == water_maps for f in Chem.GetMolFrags(after, asMols=True)):
        raise ValueError("Net water must contain the alcohol O/OH-H and actual HX hydrogen; HX is consumed, not catalytic.")


def equivalent_sites(mol, left, right):
    work = Chem.Mol(mol)
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    return any(tuple(match[i] for i in left) == tuple(right) for match in work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=1024))


def metadata(substrate, reagent, product, site, report):
    p = participants(substrate, reagent, site); kind = report["alcoholClass"]
    center_index = next(a.GetIdx() for a in product.GetAtoms() if a.GetAtomMapNum() == p["center"])
    mode = "activated-water SN2 rationale; no free primary cation" if kind in {"methyl", "primary"} else "activated-water SN1-type rationale; planar capture, no exact racemization ratio" if kind == "tertiary" else "HX SN1/SN2 partition and stereochemical outcome unresolved"
    return {**p, "alcoholClass": kind, "hydrogenHalide": report["hydrogenHalide"], "hxConsumed": True,
            "oxygenCompetition": report["oxygenCompetition"], "mode": mode, "mappedMechanism": "unsupported",
            "stereochemistryUnresolved": any(s.type == Chem.StereoType.Atom_Tetrahedral and s.centeredOn == center_index for s in Chem.FindPotentialStereo(product)),
            "mechanismUnresolved": kind in {"secondary", "primary benzylic"}, "productConfiguration": "unassigned", "stereoisomerRatios": None,
            "provenance": "Formal net alcohol O/OH-H and HX-H bookkeeping; solution proton exchange is not an isotope history. HX halogen enters the selected product carbon."}


def assess_conditions(reaction, conditions):
    model = reaction["alcoholSubstitutionModel"]
    temperature, medium, catalyst = (conditions.get(k, "") for k in ("temperature", "solvent", "catalyst"))
    missing = [] if temperature else ["temperature"]
    known = {"temperature", "solvent", "catalyst", "oxidationStage", "additionStage", "polymerUnits", "workup"}
    unknown = set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - known)
    issues = [{"field": k, "kind": "unsupported", "explanation": f"Condition field '{k}' is not evaluated for HX alcohol substitution."} for k in sorted(unknown)]
    if catalyst not in {"", "none"}:
        issues.append({"field": "catalyst", "kind": "unsupported" if catalyst == "radical" else "unvalidated-alternative", "explanation": "Actual HX already supplies acid activation and halide and is consumed. Added acid, Lewis-acid, metal or radical settings are not interchangeable validated HX profiles; no additional reagent is inferred."})
    if medium not in {"", "aqueous-protic"}:
        issues.append({"field": "solvent", "kind": "unvalidated-alternative", "explanation": "Exact dry/aprotic or alcoholic HX formulations are unvalidated here; alcohol capture, ether formation and ionization may differ. This is not a claim that all alternative media prevent substitution."})
    reference = "heated" if model["alcoholClass"] in {"methyl", "primary"} else "ambient"
    if temperature and temperature != reference:
        issues.append({"field": "temperature", "kind": "unvalidated-alternative", "explanation": "Temperature differs from the bounded HX model. Heated secondary/tertiary substitution can compete with dehydration; ambient primary conversion/activation is not established. No winner or rate is predicted."})
    for k in ("oxidationStage", "workup"):
        if conditions.get(k): issues.append({"field": k, "kind": "conflicting", "explanation": f"{k} belongs to another reaction model; clear it rather than infer coupled HX chemistry."})
    not_applicable = [k for k in ("additionStage", "polymerUnits") if conditions.get(k)]
    limitations = []
    if model["mechanismUnresolved"]: limitations.append("Secondary/benzylic HX mechanism and selectivity need substrate/formulation-specific validation. Conditional 2D net connectivity only; no universal SN2 inversion or free-cation SN1 sequence is asserted.")
    if model["stereochemistryUnresolved"]: limitations.append("The reacting product center is stereogenic but unresolved. Its configuration stays unsigned; no exact racemization ratio or stereochemical 3D outcome is asserted.")
    if model["oxygenCompetition"]: limitations.append("Other oxygen sites may substitute, cleave or capture under HX. Preserved-spectator single-site products remain conditional 2D, not selective experimental conversion.")
    allowed = not missing and not issues and not limitations
    note = " ".join(["Selected alcohol site and actual activating " + model["hydrogenHalide"] + " validated for formal net bookkeeping.",
                     *( ["Missing required model settings: temperature."] if missing else []),
                     *(i["explanation"] for i in issues), *limitations,
                     *( ["Persistent alkyne-equivalent/chain-length selectors are not applicable to alcohol substitution; they do not change its 1:1 HX equation."] if not_applicable else []),
                     "HX is consumed 1:1, supplying H to net water and halogen to the haloalkane; it is not merely catalytic. OH must be protonated so water, not bare hydroxide, can leave. Temperature/medium selectors are bounded assumptions, not a complete experimental protocol. Dehydration, ether formation, exchange and actual yields are not predicted."])
    status = "unsupported-pathway" if any(i["kind"] == "unsupported" for i in issues) else "missing" if missing else "unevaluated" if issues or limitations else "model-match"
    return {"state": "aligned" if allowed else "incomplete", "status": status, "label": "Activated HX net model" if allowed else "HX conditions/mechanism unresolved",
            "confidenceLabel": "Activated HX substitution net model · outcome not predicted" if allowed else "HX substitution unresolved · conditional 2D only",
            "canRun": allowed, "missingSettings": missing, "conditionIssues": issues, "notApplicableSettings": not_applicable, "referenceDifferences": [],
            "note": note, "reagentValidated": True, "reagentRequirement": "actual " + model["hydrogenHalide"] + " consumed, not bare halide",
            "activationRequirement": "protonation by actual HX; no separate acid catalyst is required", "factors": {
                "temperature": {"status": "model-match" if temperature == reference else "missing" if not temperature else "unevaluated", "effect": "unknown", "explanation": "Reference " + reference + " is a bounded net convention, not a substrate-specific protocol."},
                "activation": {"status": "model-match", "effect": "neutral", "explanation": "Validated actual HX supplies both acid activation and incoming halide; None added means no EXTRA catalyst, not absence of acid."},
                "solvent": {"status": "unevaluated", "effect": "unknown", "explanation": "Concentration, water activity and solvent-specific mechanism are not established."},
                "competing chemistry": {"status": "unevaluated", "effect": "unknown", "explanation": " ".join(limitations) or "Substitution/dehydration/ether ratios and completion are not predicted."}}}
