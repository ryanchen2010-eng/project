"""Presentation/evidence contract for existing addition models, not chemistry rules.

Legacy site-addressable reactions and canRun gates are preserved. The new
reactionOptions view groups only proven graph-equivalent hydration choices.
Rendering a conformer never asserts reaction completion or solvent validation.
"""
from copy import deepcopy
from rdkit import Chem
if __package__:
    from .hydrohalogenation_rule import equivalent_sites
else:
    from hydrohalogenation_rule import equivalent_sites

PATHWAYS = frozenset({"Hydration", "Hydrohalogenation", "Bromination", "Chlorination",
                      "Epoxidation", "Alkene dihydroxylation"})
NET_PATHWAYS = PATHWAYS | {"Alkyne partial hydrogenation", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation", "Alcohol dehydration", "Alcohol substitution", "Aldehyde oxidation"}


def evidence(reaction, assessment, conditions):
    """Separate model requirements, unassessed factors and output permissions.

    status/canRun on the parent assessment remain the legacy gate contract.
    This versioned evidence is the confidence contract for new consumers.
    """
    if reaction.get("secondaryOxidationModel"):
        if __package__: from .secondary_alcohol_oxidation_rule import evidence as secondary_evidence
        else: from secondary_alcohol_oxidation_rule import evidence as secondary_evidence
        return secondary_evidence(reaction,assessment,conditions)
    path = reaction["mechanism"]
    primary_oxidation = bool(reaction.get("primaryOxidationModel"))
    if path not in NET_PATHWAYS and not primary_oxidation:
        return None
    required = {"Aldehyde oxidation": ["solvent", "oxidationStage"], "Alcohol substitution": ["temperature"], "Alcohol dehydration": ["catalyst", "temperature"], "Hydration": ["catalyst"], "Alkene dihydroxylation": ["catalyst", "workup"],
                "Bromination": ["solvent"], "Chlorination": ["solvent"],
                "Epoxidation": ["solvent"], "Alkyne partial hydrogenation": ["catalyst"],
                "Alkyne hydrogenation": ["catalyst"], "Alkyne halogenation": ["solvent", "additionStage"],
                "Alkyne hydrohalogenation": ["solvent", "temperature", "additionStage"]}.get(path, [])
    if path == "Hydrohalogenation" and reaction.get("hxModel", {}).get("oxygenSpectators"):
        required = ["temperature"]
    if primary_oxidation:
        required = ["solvent", "oxidationStage"]
    missing = [key for key in assessment.get("missingSettings", []) if key in required]
    factors = deepcopy(assessment.get("factors", {}))
    unknown = [key for key, fact in factors.items() if fact["status"] in {"missing", "unevaluated", "reference-difference", "unsupported-pathway"}]
    can_render = assessment.get("canRun", True)
    issues = assessment.get("conditionIssues", [])
    if issues:
        label = assessment["confidenceLabel"] + ": " + ", ".join(dict.fromkeys(i["field"] for i in issues))
    elif missing:
        label = "Required model settings missing: " + ", ".join(missing)
    elif primary_oxidation or path in {"Aldehyde oxidation", "Alcohol substitution", "Alcohol dehydration", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"}:
        label = assessment["confidenceLabel"]
    elif not can_render:
        label = "Conditions not evaluated · conditional 2D only"
    elif path == "Alkyne partial hydrogenation":
        label = "Lindlar net model · solvent/pressure/stopping not validated"
    elif path == "Alkene dihydroxylation":
        label = "Release assumed · solvent not evaluated"
    elif assessment.get("status") == "missing":
        label = "Conditional net model · medium unspecified"
    elif assessment.get("status") == "reference-difference":
        label = "Conditional net model · reference differs"
    else:
        label = "Net model settings match · outcome not predicted"
    alkyne = path.startswith("Alkyne ")
    completeness = ("unsupported-input" if any(i["kind"] == "unsupported" for i in issues) else
                    "conflicting-input" if any(i["kind"] == "conflicting" for i in issues) else
                    "not-evaluated" if issues else "incomplete" if assessment.get("missingSettings") else "model-assumptions-only")
    return {"version": 1, "structuralEligibility": "eligible", "reagentIdentity": "validated",
            "assertionLevel": "conditional-net", "experimentalOutcome": "not-predicted", "label": label,
            "requiredSettings": required, "missingRequiredSettings": missing,
            "requirementsState": "missing" if missing else "not-evaluated" if not can_render else "assumptions-satisfied",
            "conditionCompleteness": completeness,
            **({"conditionIssues": deepcopy(issues), "notApplicableSettings": assessment.get("notApplicableSettings", []),
                "chemistryCorrectness": {"status": "not-independently-certified-at-runtime", "scope": "Mapped net graph validation is not independent experimental, selectivity or protocol verification."}}
               if alkyne or path in {"Aldehyde oxidation", "Alcohol substitution"} or primary_oxidation else {}),
            **({"conditionCompleteEligibility": False, "acidEndpointValidated": False,
                "reportingForm": "neutral-carboxylic-acid", "solutionSpeciationEstablished": False,
                "independentChemistryReview": "reporting-graph-only"} if path == "Aldehyde oxidation" else {}),
            **({"conditionCompleteEligibility": False, "aldehydeEndpointValidated": False,
                "independentChemistryReview": "not-approved", "structuralScope": "formal-first-stage-only"} if primary_oxidation else {}),
            "evaluatedFactors": factors, "unknownConditions": unknown,
            "canPreview2D": True, "canGenerate3D": can_render,
            "renderingPolicy": "qualified-net-conformer" if can_render else "required-settings-or-compatibility-gate",
            "renderingNote": "3D permission is an output policy, not evidence of conversion, isolation or complete experimental conditions. " + ("Pathway-specific confidence gates apply." if alkyne or path in {"Aldehyde oxidation", "Alcohol substitution"} else "Pathway-specific gates are unchanged."),
            "workupRepresented": assessment.get("workupRepresented"),
            "workupAssumptionConfirmed": assessment.get("workupAssumptionConfirmed")}


def calculation_context(reaction, assessment, conditions, notes):
    if reaction.get("secondaryOxidationModel"):
        if __package__: from .secondary_alcohol_oxidation_rule import calculation_context as secondary_context
        else: from secondary_alcohol_oxidation_rule import calculation_context as secondary_context
        return secondary_context(reaction,assessment,conditions,notes)
    fact = assessment["evidence"]
    warning = "Conditional net amounts: complete conversion is assumed, not predicted. Do not sum alternative products; these are not experimental yields or a laboratory protocol."
    if reaction["mechanism"] == "Alkene dihydroxylation":
        warning += " Os cycling/release species are omitted; H2O2 maps are formal net bookkeeping, not elementary provenance."
    if reaction["mechanism"] == "Alcohol dehydration":
        warning += " One alcohol gives one alkene plus one water; actual sulfuric acid is catalytic and excluded from consumed amounts. Alternatives are not additive yields. Net H maps do not model catalyst/solvent proton exchange. " + assessment["note"]
    if reaction["mechanism"] == "Alcohol substitution":
        warning += " One alcohol plus one actual HX gives one haloalkane plus one water. HX is consumed and can limit the theoretical amount; it is not excluded as a catalyst. Alternatives are not additive yields. Net H maps do not model proton exchange. Arithmetic does not establish activation, mechanism or selective product formation; see the condition/site limitations in the assumptions."
    if reaction.get("primaryOxidationModel"):
        warning += " Hypothetical first-stage amounts only: one alcohol and one actual alkali hypochlorite formula unit give aldehyde, water and the actual chloride salt in the formal balanced net stage. This is not an isolated aldehyde yield or the total oxidant demand for further oxidation. No H2 gas, selective stopping, protection of other OH sites or approved condition profile is inferred. 3D remains blocked; arithmetic does not establish chemical completion."
    if reaction["mechanism"] == "Aldehyde oxidation":
        warning += " One aldehyde and one actual alkali hypochlorite formula unit give the neutral acid reporting graph and actual chloride salt. Full salt masses count. pH, acid/carboxylate speciation and isolated acid work-up are not established; these amounts are not isolated acid yields. Formal proton/oxygen mapping is not experimental isotope history."
        if not fact["canGenerate3D"]:
            warning += " 3D is blocked for these condition/site inputs; arithmetic does not qualify them."
    if reaction["mechanism"] == "Alkyne partial hydrogenation":
        warning += " One H2 per selected site assumes a Lindlar alkene endpoint; over-reduction and selective mono-conversion are not predicted."
        if assessment.get("singleSiteBookkeepingOnly"):
            warning += " Competing alkyne sites are unresolved: conditional 2D bookkeeping only; selective single-site 3D is blocked."
    if reaction["mechanism"].startswith("Alkyne ") and not fact["canGenerate3D"]:
        warning += " 3D is unavailable for this condition/site context; arithmetic does not confirm product generation. " + assessment["note"]
    if reaction["mechanism"] == "Alkyne hydrogenation":
        warning += " Two H2 are required per selected triple bond. Available hydrogen and complete conversion are not established."
        if assessment["singleSiteBookkeepingOnly"]:
            warning += " Other alkynes also compete: this one-site equation does not predict selective mono-hydrogenation or an all-sites product."
    if reaction["mechanism"] == "Alkyne halogenation":
        model = reaction["alkyneHalogenModel"]
        warning += f" This selected-site equation assumes {model['equivalents']} {model['halogen']}2 equivalent(s); actual supply, stopping and complete conversion are not established."
        if model["singleSiteBookkeepingOnly"]:
            warning += " Other alkynes compete: selective one-site conversion and an all-sites product are not predicted."
    if reaction["mechanism"] == "Alkyne hydrohalogenation":
        model = reaction["alkyneHxModel"]
        warning += f" This endpoint assumes {model['equivalents']} H{model['halogen']} equivalent(s) per selected site, not actual supply or stopping."
        warning += " Regioisomers are alternatives, not additive yields or a predicted distribution."
        if model["singleSiteBookkeepingOnly"] or model["oxygenCompetition"]:
            warning += " Competing sites or oxygen chemistry are unresolved; this preserved-spectator equation is conditional bookkeeping only."
    return {"version": 1, "assertionLevel": "conditional-net", "pathway": reaction["mechanism"],
            "label": fact["label"], "conditionStatus": assessment["status"],
            "conditions": dict(conditions), "missingRequiredSettings": fact["missingRequiredSettings"],
            "unknownConditions": fact["unknownConditions"], "canGenerate3D": fact["canGenerate3D"],
            "assumptions": [assessment["note"], *notes],
            "warning": warning}


def _site_aliases(option):
    p = (option.get("site") or {}).get("parameters", {})
    aliases = p.get("equivalentSiteFaces") or p.get("equivalentSiteAtomMaps")
    if aliases:
        return [list(a) for a in aliases]
    return [list((option.get("site") or {}).get("atomMaps", [])[:3 if option["mechanism"] == "Alcohol dehydration" else 2])]


def grouped_options(reactions, catalog):
    """Canonical product options with complete mapped site/face aliases.

    The hydration equivalence helper checks full-graph chirality AND capture
    orientation. Reusing symmetry logic does not reuse HX chemistry permission.
    The legacy reactions list keeps every independently addressable site ID.
    """
    result = []
    for original in reactions:
        option = deepcopy(original)
        aliases = _site_aliases(option)
        if option.get("secondaryOxidationModel"):
            if __package__: from .secondary_alcohol_oxidation_rule import equivalent_sites as equivalent_secondary_sites
            else: from secondary_alcohol_oxidation_rule import equivalent_sites as equivalent_secondary_sites
            substrate=Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior=next((old for old in result if old.get("secondaryOxidationModel") and old["reactants"]==option["reactants"] and old["productSmiles"]==option["productSmiles"] and equivalent_secondary_sites(substrate,old["site"]["substrateAtoms"],option["site"]["substrateAtoms"])),None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option.get("primaryOxidationModel"):
            if __package__: from .primary_alcohol_oxidation_rule import equivalent_sites as equivalent_primary_sites
            else: from primary_alcohol_oxidation_rule import equivalent_sites as equivalent_primary_sites
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old.get("primaryOxidationModel") and old["reactants"] == option["reactants"]
                          and old["productSmiles"] == option["productSmiles"] and equivalent_primary_sites(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alcohol substitution":
            if __package__: from .alcohol_substitution_rule import equivalent_sites as equivalent_alcohol_hx
            else: from alcohol_substitution_rule import equivalent_sites as equivalent_alcohol_hx
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == option["mechanism"] and old["reactants"] == option["reactants"]
                          and old["productSmiles"] == option["productSmiles"] and equivalent_alcohol_hx(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alcohol dehydration":
            if __package__: from .alcohol_dehydration_rule import equivalent_sites as equivalent_dehydration
            else: from alcohol_dehydration_rule import equivalent_sites as equivalent_dehydration
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == option["mechanism"] and old["reactants"] == option["reactants"]
                          and old["productSmiles"] == option["productSmiles"] and equivalent_dehydration(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alkyne hydrohalogenation":
            if __package__:
                from .alkyne_hydrohalogenation_rule import equivalent_choices
            else:
                from alkyne_hydrohalogenation_rule import equivalent_choices
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"]==option["mechanism"]
                          and old["reactants"]==option["reactants"] and old["productSmiles"]==option["productSmiles"]
                          and equivalent_choices(substrate,old["site"]["substrateAtoms"],option["site"]["substrateAtoms"])),None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alkyne halogenation":
            if __package__:
                from .alkyne_halogenation_rule import equivalent_sites as equivalent_x2_sites
            else:
                from alkyne_halogenation_rule import equivalent_sites as equivalent_x2_sites
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == option["mechanism"]
                          and old["reactants"] == option["reactants"] and old["productSmiles"] == option["productSmiles"]
                          and equivalent_x2_sites(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alkyne hydrogenation":
            if __package__:
                from .alkyne_complete_hydrogenation_rule import equivalent_sites as equivalent_complete_sites
            else:
                from alkyne_complete_hydrogenation_rule import equivalent_sites as equivalent_complete_sites
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == option["mechanism"]
                          and old["reactants"] == option["reactants"] and old["productSmiles"] == option["productSmiles"]
                          and equivalent_complete_sites(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Alkyne partial hydrogenation":
            # Presentation grouping only; every original mapped site ID remains
            # addressable, including the fixed benchmark's legacy site contract.
            if __package__:
                from .alkyne_partial_hydrogenation_rule import equivalent_sites as equivalent_alkyne_sites
            else:
                from alkyne_partial_hydrogenation_rule import equivalent_sites as equivalent_alkyne_sites
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == option["mechanism"]
                          and old["reactants"] == option["reactants"] and old["productSmiles"] == option["productSmiles"]
                          and equivalent_alkyne_sites(substrate, old["site"]["substrateAtoms"], option["site"]["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                prior["optionIdentity"]["siteAliases"].extend(a for a in aliases if a not in prior["optionIdentity"]["siteAliases"])
                continue
        if option["mechanism"] == "Hydration":
            site = option["site"]
            aliases = [[*site["atomMaps"][:2], site["parameters"]["oxygenCarbon"]]]
            substrate = Chem.MolFromSmiles(catalog[option["reactants"][0]]["smiles"])
            prior = next((old for old in result if old["mechanism"] == "Hydration"
                          and old["reactants"] == option["reactants"]
                          and old["productSmiles"] == option["productSmiles"]
                          and equivalent_sites(substrate, old["site"]["substrateAtoms"], site["substrateAtoms"])), None)
            if prior:
                prior["optionIdentity"]["sourceReactionIds"].append(option["id"])
                recorded = prior["optionIdentity"]["siteAliases"]
                for alias in aliases:
                    if alias not in recorded:
                        recorded.append(alias)
                prior["site"]["parameters"]["equivalentSiteAtomMaps"] = deepcopy(recorded)
                continue
            option["site"]["parameters"]["equivalentSiteAtomMaps"] = aliases
        option["optionIdentity"] = {"kind": "net-product-alternative", "mechanism": option["mechanism"],
                                    "sourceReactionIds": [option["id"]], "siteAliases": aliases,
                                    "aliasKind": "site-and-capture-atom" if option["mechanism"] in {"Hydration", "Hydrohalogenation"} else
                                                 "site-and-face-index" if option["mechanism"] in PATHWAYS else "site"}
        result.append(option)
    for option in result:
        identity = option["optionIdentity"]
        sites = {tuple(sorted(a[:2])) for a in identity["siteAliases"] if len(a) >= 2}
        identity["siteCount"] = len(sites)
        if option["mechanism"] == "Hydration" and len(identity["siteAliases"]) > 1:
            option["site"]["label"] += f" · {len(sites)} graph-equivalent sites (one product option)"
    return result


def option_counts(options):
    # Maps are scoped to each substrate, not globally unique across reactants.
    sites = {(tuple(o["reactants"]), tuple(sorted(a[:2]))) for o in options
             for a in o["optionIdentity"]["siteAliases"] if len(a) >= 2}
    return {"version": 1, "optionCount": len(options), "mechanismCount": len({o["mechanism"] for o in options}),
            "productCount": len({(o["mechanism"], o["productSmiles"]) for o in options}), "siteCount": len(sites),
            "note": "Options may differ by site, orientation or face; they are not necessarily different mechanisms. No ratios or selective one-site conversion are predicted."}
