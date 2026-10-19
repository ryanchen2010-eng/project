"""Deterministic graph/condition explanations. No LLM or probability scoring."""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph
    from .reaction_engine import reagent_role
    from .reaction_conditions import assess_conditions, REVIEWED
    from . import primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule
else:
    import molecular_graph as graph
    from reaction_engine import reagent_role
    from reaction_conditions import assess_conditions, REVIEWED
    import primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule


CONDITION_NAMES = {"polar-aprotic": "polar aprotic", "aqueous-protic": "aqueous protic",
                   "ethanolic-protic": "ethanolic protic", "dry": "dry", "ambient": "room temperature",
                   "heated": "heated", "acid": "acid catalyst", "metal": "metal catalyst",
                   "none": "none added", "first": "first oxidation stage", "further": "further oxidation"}
CONDITION_NAMES.update({"lindlar": "Lindlar catalyst", "osmium": "Os-based dihydroxylation system", "radical": "radical initiation model",
                        "one": "one equivalent", "two": "two equivalents", "2": "2 monomer units", "4": "4 monomer units", "6": "6 monomer units"})
GROUPS = {"SN1": "alkyl halide", "SN2": "alkyl halide", "E1": "alkyl halide", "E2": "alkyl halide",
          "Hydrogenation": "isolated alkene", "Bromination": "isolated alkene", "Chlorination": "isolated alkene",
          "Hydration": "isolated alkene", "Hydrohalogenation": "isolated alkene", "Alcohol oxidation": "alcohol",
          "Aldehyde oxidation": "aldehyde", "Carbonyl hydrogenation": "aldehyde or ketone",
          "Esterification": "carboxylic acid + alcohol", "Ester hydrolysis": "ester", "Epoxidation": "isolated alkene"}
GROUPS.update({"Alcohol dehydration": "alcohol with beta H", "Alcohol substitution": "alcohol", "Ester saponification": "ester",
               "Alkyne hydrogenation": "alkyne", "Alkyne partial hydrogenation": "isolated acyclic alkyne", "Alkyne halogenation": "alkyne",
               "Alkyne hydrohalogenation": "alkyne", "Alkene dihydroxylation": "isolated alkene", "Polymerization model": "terminal vinyl monomer"})


def explain_pathway(reaction, catalog, conditions=None):
    conditions = conditions or {}
    mechanism = reaction["mechanism"]
    condition_assessment = assess_conditions(reaction, conditions) if mechanism in REVIEWED else None
    if reaction.get("primaryOxidationModel"):
        condition_assessment = primary_alcohol_oxidation_rule.assess_conditions(reaction, conditions)
    if reaction.get("secondaryOxidationModel"):
        condition_assessment=secondary_alcohol_oxidation_rule.assess_conditions(reaction,conditions)
    if not reaction.get("site", {}).get("substrateAtoms"):
        return {"label": "Unsupported", "factors": [],
                "note": "No validated structural site is available; pathway reasoning is unavailable."}
    substrate = Chem.MolFromSmiles(catalog[reaction["reactants"][0]]["smiles"])
    reagent = Chem.MolFromSmiles(catalog[reaction["reactants"][1]]["smiles"])
    indices = reaction["site"]["substrateAtoms"]
    center = substrate.GetAtomWithIdx(indices[0])
    role = reagent_role(reagent)
    factors = []
    def add(factor, value, effect, explanation, atom_maps=None):
        factors.append({"factor": factor, "value": value, "effect": effect, "pathway": mechanism,
                        "explanation": explanation, "atomMaps": atom_maps or []})
    add("functional-group", GROUPS.get(mechanism, reaction["family"]), "favors",
        f"The selected graph contains the {GROUPS.get(mechanism, 'supported group')} required by this rule.", reaction["site"]["atomMaps"])
    add("reaction-site", reaction["site"]["label"], "favors", "This exact site passed the structural rule and product validation; other sites are separate options.", reaction["site"]["atomMaps"])
    if mechanism in {"Hydrogenation", "Carbonyl hydrogenation", "Alcohol oxidation", "SN2", "E2", "SN1", "E1", "Hydration", "Hydrohalogenation", "Bromination", "Chlorination", "Epoxidation", "Alkene dihydroxylation", "Alkyne partial hydrogenation", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"} and reaction.get("compatibility"):
        for index, group in enumerate(reaction["compatibility"]["groups"]):
            if group["disposition"] in {"preserved", "alternative-site"}:
                add(f"site-compatibility-{index}", f"{group['relation']} {group['type']}", "neutral",
                    group["explanation"], group["atomMaps"])
        add("stereo-retention", "validated net edit", "neutral", reaction["stereochemistry"]["effect"])
    if mechanism in {"SN1", "SN2", "E1", "E2"}:
        degree = graph.substitution_degree(center)
        classification = graph.classify_carbon(center)
        benzylic = any(n.GetIsAromatic() for n in graph.carbon_neighbors(center))
        add("substrate", classification + ("; benzylic" if benzylic else ""),
            "neutral" if mechanism == "SN2" and degree == 2 else "favors",
            "Secondary carbon permits this bounded SN2 model, but attack is more hindered and E2 can compete." if mechanism == "SN2" and degree == 2 else
            f"The leaving group is attached to a {classification} sp³ carbon accepted by this pathway's structural scope.")
        leaving = substrate.GetAtomWithIdx(indices[1]).GetSymbol()
        add("leaving-group", leaving, "favors", "A carbon–halogen leaving-group bond is present; this model supports Cl, Br and I, not ordinary alkyl fluoride.")
        if mechanism == "SN2":
            add("steric-hindrance", "moderate" if degree == 2 else "low / supported",
                "disfavors" if degree == 2 else "favors",
                "Secondary substitution is hindered; no reaction rate is estimated." if degree == 2 else "The center is not tertiary and does not have the rejected neopentyl-type severe hindrance.")
        if mechanism in {"SN1", "E1"}:
            add("carbocation-stability", reaction.get("carbocationModel", {}).get("basis", "benzylic resonance" if benzylic else "tertiary stabilization"), "favors",
                "This structure supports the restricted carbocation pathway. Rearrangements and measured ionization energies are not modeled.")
            if mechanism == "SN1" and reaction.get("compatibility"):
                add("competing-chemistry", "screened, not predicted", "unknown",
                    "Hydride/alkyl shifts, oxygen capture and acid-sensitive groups were screened. E1/SN2, ion pairs, facial preference and product ratios are not calculated; the absence of an E1 option is not proof that elimination cannot occur.")
                add("reacting-center-stereo", "unassigned after ionization", "neutral",
                    "A positive planar intermediate loses the original reacting configuration. Water capture is not assigned R/S or a perfect racemization ratio; distant mapped configurations must remain.")
            elif mechanism == "E1" and reaction.get("compatibility"):
                add("competing-chemistry", "screened, not predicted", "unknown",
                    "SN1 water capture, ion pairs, shifts, cyclization and subsequent conversion can compete. This one-site E1 option does not estimate product ratios or a guaranteed major product; absent SN1 options are not proof of no substitution.")
                add("reacting-center-stereo", "planar cation then unsigned alkene", "neutral",
                    "Alpha configuration is lost on ionization; beta becomes planar only on beta-H loss. Distant configurations and recomputed CIP are checked; E2 anti geometry cannot assign E1 E/Z.")
            if reaction.get("carbocationModel", {}).get("basis") == "bounded secondary alkyl stabilization":
                add("secondary-ionization", "narrow conditional possibility", "unknown",
                    "SN1/E1 share only the screened Me/Me or Me/Et saturated secondary ionization scope. Ionizing-solvent dependence, slow/negligible conversion and competition are not measured; this is not a dominant-product claim or blanket secondary permission.")
        if mechanism in {"E1", "E2"}:
            beta = substrate.GetAtomWithIdx(indices[2])
            add("beta-hydrogen", str(graph.attached_hydrogens(beta)) + " at selected beta carbon", "favors",
                "An actual beta C–H bond exists at this selected elimination position. Its electrons can form the displayed C=C.")
            geometry = reaction.get("stereochemistry", {}).get("geometry", {})
            add("geometry", geometry.get("status", "not evaluated") if mechanism == "E2" else "not evaluated", "unknown",
                geometry.get("note", "Anti-periplanar geometry and E/Z selectivity are not evaluated; a structural match is not proof of accessible conformation.") if mechanism == "E2" else
                "Carbocation conformations and E/Z selectivity are not evaluated; E1 does not require the E2 anti-periplanar concerted arrangement.")
        if mechanism in {"SN1", "SN2"}:
            add("nucleophile", "strong: hydroxide" if role == "hydroxide" else "weak: water",
                "favors" if mechanism == "SN2" and role == "hydroxide" else "neutral",
                "Hydroxide supplies the attacking oxygen and is also a strong base, so E2 can compete." if role == "hydroxide" else
                "Water can capture the supported carbocation; weak nucleophilicity does not prohibit this SN1 capture step.")
        add("base-strength", "strong: hydroxide" if role == "hydroxide" else "weak: water",
            "favors" if mechanism == "E2" and role == "hydroxide" else "neutral",
            "Hydroxide can remove beta H in E2 and can also substitute; conditions influence competition." if role == "hydroxide" else
            "Solvent water removes an O–H proton from the oxonium intermediate in a separate SN1 step; competing E1 beta-H removal is not quantified." if mechanism == "SN1" else
            "Water can remove beta H after carbocation formation; this is not a strong-base E2 model.")
    elif mechanism == "Epoxidation":
        add("reagent-group", "one peroxyacid group", "favors",
            "The O farther from the acyl carbon is transferred; the rest of the peroxyacid becomes a carboxylic acid. Hydrogen peroxide alone does not match this rule.")
        model = reaction["epoxidationStereo"]
        add("stereochemistry", model["outcome"], "neutral", model["basis"] + ". " + model["note"])
        add("mechanism", "one concerted oxygen transfer", "neutral", "The terminal O forms both C–O bonds; the actual peracid H moves to its original carbonyl O while the proximal O becomes acid C=O. No stable intermediate is invented.")
        add("competing-chemistry", "screened, not predicted", "unknown", "Peracid oxidation of other groups, directed/capture environments and later acid-promoted opening are screened or explicitly unpredicted; no isolated product or site/facial ratio is guaranteed.")
    elif mechanism == "Alcohol oxidation":
        degree = graph.substitution_degree(center)
        add("substrate", "primary / methyl alcohol" if degree <= 1 else "secondary alcohol", "favors",
            "The OH-bearing carbon has an attached H available for carbonyl formation; tertiary alcohols are excluded.")
        add("oxidation-stage", "aldehyde stage" if degree <= 1 else "ketone stage", "neutral",
            "Selecting the first stage describes aldehyde connectivity, not guaranteed controlled isolation with aqueous hypochlorite; further oxidation can occur." if degree <= 1 else
            "The secondary alcohol becomes a ketone; it is not matched by the ordinary aldehyde-to-acid rule.")
        add("oxidant-conditions", "net stage only", "unknown",
            "The hypochlorite graph supplies the balanced net oxidation. pH, reagent-specific catalysis, overoxidation, chlorination and selective mono-oxidation are not established by the medium selector.")
    elif mechanism == "Aldehyde oxidation":
        add("substrate", "aldehyde with formyl H", "favors", "A carbonyl carbon bonded to H is detected; an ordinary ketone lacks this formyl H.")
        add("oxidation-stage", "further oxidation", "favors", "The selected aqueous further-oxidation model adds oxygen to the aldehyde stage. The acid is shown in its neutral reporting form; solution protonation and isolated product are not predicted.")
        add("oxidant-conditions", "protocol not evaluated", "unknown",
            "Hypochlorite oxidation is reagent-, pH- and catalyst-dependent. This balanced net stage does not validate an uncatalyzed experimental protocol or exclude halogenation and other side reactions.")
    elif mechanism == "Carbonyl hydrogenation":
        add("substrate", "aldehyde" if graph.attached_hydrogens(center) else "ketone", "favors",
            "This is an aldehyde/ketone C=O, not an acid, ester or amide carbonyl.")
    elif mechanism == "Alkyne hydrohalogenation":
        model = reaction["alkyneHxModel"]
        add("actual-HX","H"+model["halogen"],"neutral","The actual reagent contributes every incoming H/X pair and is consumed; X2 and metal/transfer donors are not interchangeable.")
        add("alkyne-orientation",model["orientationBasis"],"unknown" if model["alternativeOrientations"]>1 else "neutral","Halogen attaches at mapped carbon "+str(model["halogenCarbon"])+". Both inequivalent internal constitutional possibilities remain separate without major/minor claims or bond migration.")
        add("HX-equivalents",str(model["equivalents"]),"neutral",condition_assessment["factors"]["additionStage"]["explanation"])
        add("alkyne-stereo",model["stereoOutcome"],"unknown" if model["internal"] and model["equivalents"]==1 else "neutral",model["note"])
        add("reagent-profile","independently bounded","unknown",condition_assessment["factors"]["reagent profile"]["explanation"])
        add("competing-HX-chemistry","conditional" if model["singleSiteBookkeepingOnly"] or model["oxygenCompetition"] else "screened","unknown",condition_assessment["factors"]["competing chemistry"]["explanation"])
        add("vinyl-mechanism","net only","unknown","No ordinary alkene carbocation mechanism, validated vinyl cation, transition state or radical electron movements are invented.")
    elif mechanism == "Alkyne halogenation":
        model = reaction["alkyneHalogenModel"]
        add("actual-halogen", model["halogen"] + "2", "neutral", "The actual selected homogeneous halogen molecule supplies every entering X atom; HX, alternative donors and mixed equivalents are not substituted.")
        add("equivalent-stage", str(model["equivalents"]), "neutral", condition_assessment["factors"]["additionStage"]["explanation"])
        add("alkyne-stereo", model["geometryBasis"], "unknown" if model["halogen"] == "Cl" and model["equivalents"] == 1 else "neutral", model["note"])
        add("competing-sites", "unresolved" if model["singleSiteBookkeepingOnly"] else "screened", "unknown" if model["singleSiteBookkeepingOnly"] else "neutral", condition_assessment["factors"]["competing sites"]["explanation"])
        add("halonium-mechanism", "net only", "unknown", "No complete mapped halonium intermediate or discrete stable vinyl carbocation is implemented; electron flow is not fabricated from the net bond edits.")
        add("halogen-supply", "not established", "unknown", condition_assessment["factors"]["halogen supply"]["explanation"])
    elif mechanism == "Alkyne partial hydrogenation":
        model = reaction["alkynePartialStereo"]
        add("lindlar-stereo", model["outcome"], "neutral", model["note"])
        add("hydrogen-provenance", "one actual H2 consumed", "neutral", "The two mapped reagent hydrogens attach one to each selected carbon. These are net identities, not a mapped surface-exchange mechanism.")
        add("surface-mechanism", "not implemented", "unknown", "Net syn addition is validated; no discrete ionic/radical intermediates or catalytic surface states are invented.")
        add("experimental-endpoint", "not predicted", "unknown", condition_assessment["factors"]["pressure"]["explanation"])
    elif mechanism == "Alkyne hydrogenation":
        add("hydrogen-stoichiometry", "two H2 per selected C≡C", "neutral", "Four actual mapped reagent hydrogens form four C–H bonds. The selected C≡C becomes C–C, not an alkene; this equation does not establish available H2 or experimental conversion.")
        add("saturated-site-stereo", "no E/Z or new local centers", "neutral", reaction["alkyneCompleteModel"]["note"])
        fact = condition_assessment["factors"]["competing reductions"]
        add("competing-reductions", "single-site bookkeeping only" if reaction["alkyneCompleteModel"]["singleSiteBookkeepingOnly"] else "screened", fact["effect"], fact["explanation"])
        add("surface-mechanism", "not implemented", "unknown", "No catalytic surface cycle, adsorbed intermediate, discrete carbocation/radical or experimental atom-exchange history is inferred from the net edit.")
        add("hydrogen-supply", "not established", "unknown", condition_assessment["factors"]["hydrogen supply"]["explanation"])
    elif mechanism == "Esterification":
        add("reagent-group", "alcohol OH", "favors", "The selected alcohol oxygen, not a compound-name lookup, becomes bonded to the acid's acyl carbon.")
    elif mechanism == "Ester hydrolysis":
        add("reagent-group", "water", "favors", "Water supplies the OH/H fragments that split this actual ester acyl–O bond.")
    if mechanism == "Hydration":
        regio = reaction["regioselectivity"]
        add("regioselectivity", regio["basis"], "unknown" if regio["alternativeOrientations"] > 1 else "neutral",
            "OH attaches at mapped carbon " + str(regio["oxygenCarbonMap"]) + ". Equal inequivalent ends have separate capture alternatives without major/minor ratios. This bounded initial capture does not predict rearranged or guaranteed experimental products.")
        add("competing-chemistry", "screened, not predicted", "unknown",
            "Adjacent shifts, short intramolecular capture and acid-sensitive groups are screened. Longer-range migration, polymerization, further hydration and equilibrium conversion are not predicted.")
    elif mechanism == "Hydrohalogenation":
        regio = reaction["regioselectivity"]
        add("regioselectivity", regio["basis"], "unknown" if regio["alternativeOrientations"] > 1 else "neutral",
            "Halogen capture is at mapped carbon " + str(regio["halogenCarbonMap"]) + ". Equal inequivalent ends have separately validated constitutional options with no major/minor ratio. Adjacent shifts and short intramolecular capture are screened, not predicted.")
        add("hx-provenance", reaction["hxModel"]["hydrogenHalide"] + " consumed", "neutral",
            "Both entering atoms come from the actual mapped H–X graph. HX supplies activation and is consumed; this is not an additional regenerated acid catalyst or an X2 halogenation.")
        equivalent = reaction["site"]["parameters"]["equivalentSiteAtomMaps"]
        if len(equivalent) > 1:
            add("equivalent-sites", str(len(equivalent)) + " graph-equivalent positions", "neutral",
                "A chirality-aware full-graph automorphism relates these sites and their capture orientation. One mapped representative is shown, not duplicate identical options or selective mono-addition.")
        add("competing-chemistry", "HX-specific screening", "unknown",
            "HBr/HI oxygen cleavage/substitution is not treated as inert. Only qualified ambient HCl oxygen spectators are enabled; solvent capture, polymerization, longer-range rearrangements and further HX addition are not experimentally predicted.")
    if mechanism == "Bromination":
        model = reaction["brominationStereo"]
        add("bromination-stereo", model["outcome"], "neutral", model["basis"] + ". " + model["note"])
        add("bromine-provenance", "actual Br2 consumed", "neutral", "Each entering Br has its own exact reagent map. One equivalent enters the selected net product; no byproduct or HBr catalyst is fabricated.")
        add("competing-chemistry", "screened, not predicted", "unknown", "Nearby oxygen/pi capture, activated groups and unvalidated environments fail closed. Water/alcohol capture, radical substitution and actual mono-bromination selectivity require other validated models.")
    if mechanism == "Chlorination":
        model = reaction["chlorinationStereo"]
        add("chlorination-stereo", model["outcome"], "neutral", model["basis"] + ". " + model["note"])
        add("chlorine-provenance", "actual Cl2 consumed", "neutral", "Each entering Cl has its own exact reagent map. One equivalent enters the selected net product; no byproduct or HCl catalyst is fabricated.")
        add("competing-chemistry", "screened, not predicted", "unknown", "Nearby oxygen/pi capture, activated groups and unvalidated environments fail closed. Water/alcohol capture, radical substitution and actual mono-chlorination selectivity require other validated models.")
    if role in {"hydrogen", "halogen", "hydrogen-halide", "hypochlorite"}:
        add("reagent", role, "favors", "The selected reagent's element/connectivity/charge graph matches this transformation, independent of its name or CID.")
    if mechanism == "Alkene dihydroxylation":
        add("dihydroxylation-stereo", reaction["dihydroxylationStereo"]["outcome"], "neutral", reaction["dihydroxylationStereo"]["note"])
        fact = condition_assessment["factors"]["workup"]
        add("workup", "aqueous release assumed" if conditions.get("workup") == "aqueous-release" else "not confirmed", fact["effect"], fact["explanation"])
    for key in ("solvent", "temperature", "catalyst", "oxidationStage", "additionStage", "polymerUnits"):
        selected = conditions.get(key, "")
        required = reaction["profile"].get(key)
        if condition_assessment and key in condition_assessment["factors"]:
            fact = condition_assessment["factors"][key]
            effect, explanation = fact["effect"], fact["explanation"]
        elif required:
            effect = "unknown" if not selected else "favors" if selected == required else "disfavors"
            explanation = f"This bounded pathway calls for {CONDITION_NAMES.get(required, required)}. "
            explanation += "Not specified; the condition fit remains uncertain." if not selected else "The selected condition matches." if selected == required else "The selected condition differs; this does not prove the pathway impossible."
        elif key == "temperature" and selected == "heated" and mechanism == "SN2":
            effect = "disfavors"; explanation = "Heating can increase elimination competition; it does not by itself prohibit substitution."
        elif key == "solvent" and mechanism == "SN2" and selected in {"aqueous-protic", "ethanolic-protic"}:
            effect = "disfavors"; explanation = "Protic solvation can reduce anionic nucleophile activity and favor competing pathways."
        elif key == "catalyst" and selected in {"acid", "metal"}:
            effect = "unknown"; explanation = "This additional catalyst is not evaluated by this pathway; it is not a validated promotion."
        else:
            effect = "neutral" if selected else "unknown"
            explanation = "No additional selectivity claim is made for this setting." if selected else "Not specified."
        add(key, CONDITION_NAMES.get(selected, selected) if selected else "not specified", effect, explanation)
    # Qualitative labels, not scores/probabilities. The engine already validated
    # availability. Missing inputs, secondary SN2 and geometry caveats prevent
    # a strong label; mismatch of required conditions is unfavorable, not impossible.
    mismatch = any(conditions.get(k) and conditions[k] != v for k, v in reaction["profile"].items())
    uncertain = any(not conditions.get(k) for k in reaction["profile"])
    caution = mechanism in {"E2", "Aldehyde oxidation"} or (mechanism == "SN2" and graph.substitution_degree(center) == 2)
    if mechanism == "Carbonyl hydrogenation" and reaction.get("compatibility"):
        caution = caution or any(g["type"] == "aromatic ring" or g["disposition"] == "alternative-site" for g in reaction["compatibility"]["groups"])
    if mechanism == "Alcohol oxidation" and reaction.get("compatibility"):
        caution = True  # A net stage is not a validated selective oxidant protocol.
    if mechanism == "SN2" and reaction.get("compatibility"):
        caution = caution or any(g["type"] in {"alcohol", "ether", "aromatic ring"} or g["disposition"] == "alternative-site" or (g["type"] == "haloalkane" and g["disposition"] == "preserved") for g in reaction["compatibility"]["groups"])
    if mechanism == "SN1" and reaction.get("compatibility"):
        caution = True  # Qualitative net scope is not selective solvolysis or a facial ratio.
    if mechanism == "E1" and reaction.get("compatibility"):
        caution = True  # A possible alkene option is not E1/SN1 selectivity.
    if mechanism == "Hydration":
        caution = True  # A conditional water-capture option, not assured regio/stereoselectivity.
    if mechanism == "Hydrohalogenation":
        caution = True  # Ionic net capture is not an experimental selectivity claim.
    if mechanism in {"Bromination", "Chlorination", "Epoxidation"}:
        caution = True  # Anti alternatives are not measured face populations.
    unknown_catalyst = "catalyst" not in reaction["profile"] and conditions.get("catalyst") in {"acid", "metal"}
    label = "Unfavorable" if mismatch else "Possible" if uncertain or caution or unknown_catalyst or (
        mechanism == "SN2" and conditions.get("temperature") == "heated") else "Strong match"
    if condition_assessment and condition_assessment["status"] != "model-match":
        label = condition_assessment["label"]
    if mechanism in {"Alkene dihydroxylation", "Alkyne halogenation", "Alkyne hydrohalogenation"}:
        label = condition_assessment["label"]  # Net assumptions, not a strong experimental match.
    if reaction.get("primaryOxidationModel"):
        label = condition_assessment["confidenceLabel"]
        add("aldehyde-endpoint", "unresolved", "unknown", condition_assessment["note"])
    if reaction.get("secondaryOxidationModel"):
        label=condition_assessment["confidenceLabel"]
        add("secondary-ketone-profile","qualified net" if condition_assessment['canRun'] else "unresolved","neutral" if condition_assessment['canRun'] else "unknown",condition_assessment['note'])
    return {"label": label, "factors": factors,
            "note": "Qualitative fit within the supported model; not a probability, rate, yield or experimental prediction."}


def compare_pathways(reactions):
    if len(reactions) < 2:
        return None
    keys = list(dict.fromkeys(f["factor"] for r in reactions for f in r["reasoning"]["factors"]))
    columns = [{"id": r["id"], "pathway": r["mechanism"], "site": r.get("site", {}).get("label", ""),
                "label": r["reasoning"]["label"]} for r in reactions]
    rows = []
    for key in keys:
        cells = []
        for r in reactions:
            factor = next((f for f in r["reasoning"]["factors"] if f["factor"] == key), None)
            cells.append({"reactionId": r["id"], "effect": factor["effect"] if factor else "neutral",
                          "value": factor["value"] if factor else "not applicable",
                          "explanation": factor["explanation"] if factor else "This factor is not part of this pathway's rule."})
        rows.append({"factor": key, "cells": cells})
    return {"columns": columns, "rows": rows, "note": "The same factors as Why This Pathway; only engine-available pathways are compared. No percentages or predicted winner."}
