"""Condition evidence for individually reviewed reaction models.

Eligibility stays in graph/reagent validators. Reference profiles are not
activation requirements, measured selectivity, or a solvent/pH/kinetic model.
Hydration separately requires independently validated acid activation.
"""
from copy import deepcopy

# Keep the original v1 imports available; the registry now owns these policies.
if __package__:
    from .reaction_temperature_profiles import (
        CONDITION_FIELDS, COOLING_NOTE, COOLING_LIMITATIONS, COOLED_BROMINATION_MODEL,
        COOLED_BROMINATION_SOURCES, COOLED_EPOXIDATION_MODEL, COOLED_EPOXIDATION_SOURCES,
        MCPBA_IDENTITY, assess_cooling_support, profile_for_review, current_cooling_overlay,
        reject_cooling_contract, normalize_legacy_cooling_assessment,
    )
else:
    from reaction_temperature_profiles import (
        CONDITION_FIELDS, COOLING_NOTE, COOLING_LIMITATIONS, COOLED_BROMINATION_MODEL,
        COOLED_BROMINATION_SOURCES, COOLED_EPOXIDATION_MODEL, COOLED_EPOXIDATION_SOURCES,
        MCPBA_IDENTITY, assess_cooling_support, profile_for_review, current_cooling_overlay,
        reject_cooling_contract, normalize_legacy_cooling_assessment,
    )

REVIEWED = frozenset({"SN1", "SN2", "E1", "E2", "Hydration", "Hydrohalogenation", "Bromination", "Chlorination", "Epoxidation", "Alcohol dehydration", "Alcohol substitution", "Aldehyde oxidation", "Alkene dihydroxylation", "Alkyne partial hydrogenation", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"})
LABELS = {"model-match": "Model conditions match", "reference-difference": "Reference differs",
          "missing": "Conditions incomplete", "disfavored": "Disfavored factors", "unevaluated": "Not evaluated",
          "activation-required": "Acid activation required", "unsupported-pathway": "Radical pathway unsupported"}


def assess_bromination_conditions(conditions):
    """Dibromide-only model, not halohydrin, solvent capture or radical chemistry."""
    medium, catalyst, temperature = (conditions.get(k, "") for k in ("solvent", "catalyst", "temperature"))
    radical = catalyst == "radical"
    extra = catalyst not in {"", "none", "radical"}
    capture = medium in {"aqueous-protic", "ethanolic-protic"}
    unknown = medium == "polar-aprotic"
    heated = temperature == "heated"
    status = "unsupported-pathway" if radical else "unevaluated" if extra or capture or unknown or heated else "missing" if not medium else "model-match"
    medium_note = ("Water can open a bromonium ion to a bromohydrin rather than the selected dibromide; no halohydrin product is invented here." if medium == "aqueous-protic" else
                   "Alcohol solvent can compete in bromonium opening to bromoethers; this is not identical to dibromide formation." if capture else
                   "Polar aprotic alone does not establish a non-nucleophilic solvent: nitrile/DMSO and other solvent-specific capture are not validated." if unknown else
                   "A defined non-nucleophilic medium is required for this dibromide-only model. Dryness alone or an unspecified medium is not proof of no solvent capture." if not medium else
                   "Dry/non-nucleophilic net model selected. Exact solvent compatibility and experimental dibromide selectivity are not established by this selector.")
    catalyst_note = ("Radical initiation can introduce allylic/substitution chemistry; a bromonium anti product is not inferred." if radical else
                     "Added activation is not validated for ordinary Br2 addition; aromatic substitution and other chemistry may differ." if extra else
                     "Actual Br2 supplies both incoming atoms. No additional acid, metal or radical catalyst is required by the neutral net model.")
    temperature_note = "Heated Br2 conditions are outside the bounded neutral addition model; rate, side reactions and stereo fidelity cannot be inferred." if heated else "No rate, energy, face ratio or experimental temperature dependence is predicted."
    return {"state": "aligned" if status == "model-match" else "incomplete", "status": status, "label": LABELS[status],
            "canRun": status == "model-match", "note": catalyst_note if radical or extra else temperature_note if heated else medium_note,
            "missingSettings": ["solvent"] if not medium else [], "referenceDifferences": [],
            "reagentRequirement": "actual neutral Br2", "reagentValidated": True,
            "activationRequirement": "none; neutral non-nucleophilic net model",
            "factors": {"solvent": {"status": "unevaluated" if capture or unknown else "missing" if not medium else "model-match", "effect": "unknown" if capture or unknown or not medium else "neutral", "explanation": medium_note},
                       "catalyst": {"status": "unsupported-pathway" if radical else "unevaluated" if extra else "model-match", "effect": "unknown" if radical or extra else "neutral", "explanation": catalyst_note},
                       "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": temperature_note}}}


def assess_epoxidation_conditions(conditions):
    """Isolated epoxide net model, not subsequent acid/solvent ring opening."""
    medium,catalyst,temperature = (conditions.get(k,"") for k in ("solvent","catalyst","temperature"))
    radical = catalyst == "radical"
    extra = catalyst not in {"","none","radical"}
    capture = medium in {"aqueous-protic","ethanolic-protic"}
    unknown = medium not in {"","dry","aqueous-protic","ethanolic-protic"}
    heated = temperature == "heated"
    status = "unsupported-pathway" if radical else "unevaluated" if extra or capture or unknown or heated else "missing" if not medium else "model-match"
    medium_note = ("Water plus the acid coproduct can open the epoxide; no diol or guaranteed isolated epoxide is predicted." if medium == "aqueous-protic" else
                   "Alcohol medium can participate in acid-promoted epoxide opening; this is not the isolated-epoxide model." if capture else
                   "A generic polar-aprotic setting does not validate peracid/solvent compatibility or epoxide stability." if unknown else
                   "A defined compatible non-capturing medium is missing; only a conditional net epoxide can be inspected." if not medium else
                   "Dry compatible-medium net model selected. Exact solvent, buffering and epoxide isolation are not established; the generated acid may enable later opening.")
    activation_note = ("Radical activation is a different unvalidated pathway, not concerted peroxyacid transfer." if radical else
                       "Added activation is unvalidated; acid/metal chemistry can alter oxidation and epoxide opening." if extra else
                       "The actual peroxyacid is consumed and supplies oxygen and its own proton; no external acid or metal activation is required.")
    temp_note = "Heated peracid/epoxide side chemistry is unvalidated; no isolated epoxide is inferred." if heated else "No temperature-dependent rate, selectivity, conversion or epoxide lifetime is calculated."
    return {"state":"aligned" if status == "model-match" else "incomplete", "status":status,"label":LABELS[status],
            "canRun":status == "model-match", "note":activation_note if radical or extra else temp_note if heated else medium_note,
            "missingSettings":["solvent"] if not medium else [], "referenceDifferences":[],
            "reagentRequirement":"actual neutral single peroxyacid", "reagentValidated":True,
            "activationRequirement":"peroxyacid itself; no added activation",
            "factors":{"solvent":{"status":"unevaluated" if capture or unknown else "missing" if not medium else "model-match",
                                  "effect":"unknown" if capture or unknown or not medium else "neutral","explanation":medium_note},
                       "catalyst":{"status":"unsupported-pathway" if radical else "unevaluated" if extra else "model-match",
                                   "effect":"unknown" if radical or extra else "neutral","explanation":activation_note},
                       "temperature":{"status":"unevaluated","effect":"unknown","explanation":temp_note}}}


def assess_chlorination_conditions(conditions):
    """Dichloride-only model, not halohydrin, solvent capture or radical chemistry."""
    medium, catalyst, temperature = (conditions.get(k, "") for k in ("solvent", "catalyst", "temperature"))
    radical = catalyst == "radical"
    extra = catalyst not in {"", "none", "radical"}
    capture = medium in {"aqueous-protic", "ethanolic-protic"}
    unknown = medium == "polar-aprotic"
    heated = temperature == "heated"
    status = "unsupported-pathway" if radical else "unevaluated" if extra or capture or unknown or heated else "missing" if not medium else "model-match"
    medium_note = ("Water can open a chloronium ion to a chlorohydrin rather than the selected dichloride; no halohydrin product is invented here." if medium == "aqueous-protic" else
                   "Alcohol solvent can compete in chloronium opening to chloroethers; this is not identical to dichloride formation." if capture else
                   "Polar aprotic alone does not establish a non-nucleophilic solvent: nitrile/DMSO and other solvent-specific capture are not validated." if unknown else
                   "A defined non-nucleophilic medium is required for this dichloride-only model. Dryness alone or an unspecified medium is not proof of no solvent capture." if not medium else
                   "Dry/non-nucleophilic net model selected. Exact solvent compatibility and experimental dichloride selectivity are not established by this selector.")
    catalyst_note = ("Radical initiation can introduce allylic/substitution chemistry; a chloronium anti product is not inferred." if radical else
                     "Added activation is not validated for ordinary Cl2 addition; aromatic substitution and other chemistry may differ." if extra else
                     "Actual Cl2 supplies both incoming atoms. No additional acid, metal or radical catalyst is required by the neutral net model.")
    temperature_note = "Heated Cl2 conditions are outside the bounded neutral addition model; rate, side reactions and stereo fidelity cannot be inferred." if heated else "No rate, energy, face ratio or experimental temperature dependence is predicted."
    return {"state": "aligned" if status == "model-match" else "incomplete", "status": status, "label": LABELS[status],
            "canRun": status == "model-match", "note": catalyst_note if radical or extra else temperature_note if heated else medium_note,
            "missingSettings": ["solvent"] if not medium else [], "referenceDifferences": [],
            "reagentRequirement": "actual neutral Cl2", "reagentValidated": True,
            "activationRequirement": "none; neutral non-nucleophilic net model",
            "factors": {"solvent": {"status": "unevaluated" if capture or unknown else "missing" if not medium else "model-match", "effect": "unknown" if capture or unknown or not medium else "neutral", "explanation": medium_note},
                       "catalyst": {"status": "unsupported-pathway" if radical else "unevaluated" if extra else "model-match", "effect": "unknown" if radical or extra else "neutral", "explanation": catalyst_note},
                       "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": temperature_note}}}


def assess_hydrohalogenation_conditions(reaction, conditions):
    """Actual HX is consumed acid/reagent; no separate acid activation required.

    Missing medium gives a conditional ionic net model, not evidence that
    water/oxygen/peroxides are absent. Oxygen spectator retention has a tighter
    explicitly ambient HCl scope. Added activation is not presumed compatible.
    """
    model = reaction["hxModel"]
    catalyst, medium, temperature = (conditions.get(k, "") for k in ("catalyst", "solvent", "temperature"))
    radical = catalyst == "radical"
    extra = catalyst not in {"", "none", "radical"}
    capture_medium = medium in {"aqueous-protic", "ethanolic-protic"}
    oxygen_gap = model["oxygenSpectators"] and temperature != "ambient"
    status = ("unsupported-pathway" if radical else "unevaluated" if extra or capture_medium or (oxygen_gap and temperature)
              else "missing" if not medium or oxygen_gap else "reference-difference" if medium == "polar-aprotic" else "model-match")
    can_run = not (radical or extra or capture_medium or oxygen_gap)
    activation_note = ("Radical initiation is not this ionic mechanism; no peroxide/anti-Markovnikov HBr products or corresponding HCl/HI radical predictions are supported." if radical else
                       "Additional activation/catalyst chemistry is unvalidated. The selected HX already supplies the acidic H; a different catalyst is neither required nor automatically compatible." if extra else
                       model["hydrogenHalide"] + " supplies the acidic hydrogen and attacking halogen and is consumed. No extra acid catalyst is required by this ionic net model.")
    medium_note = ("Water or alcohol can compete in carbocation capture; halide activity/acid concentration and solvent-capture selectivity are not validated for this medium." if capture_medium else
                   "Medium is unspecified. The displayed net option assumes ionic halide capture in a non-capturing medium; absence of water, alcohol or peroxide is not established." if not medium else
                   "This polar-aprotic setting differs from the non-capturing reference; it may be compatible, but solvent identity/acid compatibility and experimental selectivity are not calculated." if medium == "polar-aprotic" else
                   "Dry/non-capturing ionic net settings selected. They do not certify peroxide absence, solvent compatibility or actual experimental conversion.")
    temperature_note = ("Screened oxygen retention is supported only for explicitly ambient HCl without added activation. Unset/heated settings do not establish that additional C–O substitution/cleavage can be ignored." if oxygen_gap else
                        "Ambient HCl is the bounded oxygen-spectator reporting model, not proof of permanent inertness or selective isolated conversion." if model["oxygenSpectators"] else
                        "No temperature-specific rate, ratio or rearrangement suppression is established by this ionic net model.")
    return {"state": "aligned" if status == "model-match" else "alternative" if status == "reference-difference" else "incomplete",
            "status": status, "label": LABELS[status], "canRun": can_run,
            "note": activation_note if radical or extra else medium_note if capture_medium else temperature_note if oxygen_gap else medium_note,
            "missingSettings": (["solvent"] if not medium else []) + (["temperature"] if oxygen_gap and not temperature else []),
            "referenceDifferences": ["solvent"] if medium == "polar-aprotic" else [],
            "reagentRequirement": "actual neutral " + model["hydrogenHalide"], "reagentValidated": True,
            "activationRequirement": "HX itself; separate acid catalyst not required", "ionicAssumption": True,
            "factors": {"catalyst": {"status": "unsupported-pathway" if radical else "unevaluated" if extra else "model-match", "effect": "unknown" if radical or extra else "neutral", "explanation": activation_note},
                       "solvent": {"status": "unevaluated" if capture_medium else "missing" if not medium else "reference-difference" if medium == "polar-aprotic" else "model-match", "effect": "unknown" if capture_medium or not medium else "neutral", "explanation": medium_note},
                       "temperature": {"status": "missing" if oxygen_gap and not temperature else "unevaluated" if oxygen_gap else "model-match" if model["oxygenSpectators"] else "unevaluated", "effect": "unknown" if oxygen_gap or not model["oxygenSpectators"] else "neutral", "explanation": temperature_note}}}


def assess_hydration_conditions(conditions):
    """Acid is required activation, not a preset preference.

    Structural net options remain inspectable. A 3D run requires the supported
    activation/medium; this does not claim every other medium is unfavorable.
    Actual neutral water is already validated by the reaction edit contract.
    """
    catalyst, solvent = conditions.get("catalyst", ""), conditions.get("solvent", "")
    missing_acid = catalyst in {"", "none"}
    unsupported_activation = catalyst not in {"", "none", "acid"}
    unknown_medium = solvent not in {"", "aqueous-protic"}
    status = "activation-required" if missing_acid else "unevaluated" if unsupported_activation or unknown_medium else "model-match"
    catalyst_note = ("Acid activation is required for this pathway. Water alone or None added does not activate the supported carbocation hydration model; this is not merely a reference-example mismatch." if missing_acid else
                     "The selected activation is not a validated acid hydration catalyst; acid cannot be inferred from a metal, radical or other catalyst setting." if unsupported_activation else
                     "Acid enables protonation and is regenerated after water capture/deprotonation; it is not consumed in the net equation.")
    solvent_note = ("Dry medium conflicts with selected water. Water activity and acid ionization are unknown; the supported water-capture medium is not established." if solvent == "dry" else
                    "Alcoholic medium may compete through solvent capture; water versus alcohol capture is not validated by this model." if solvent == "ethanolic-protic" else
                    "Water activity and acid compatibility in this selected medium are not evaluated; no chemical disfavor or inability to hydrate is inferred." if unknown_medium else
                    "Actual water is selected as the consumed reagent; the aqueous net model is used. Acid identity/strength, concentration and water activity are not quantitatively evaluated.")
    can_run = status == "model-match"
    return {"state": "aligned" if can_run else "incomplete", "status": status, "label": LABELS[status],
            "note": catalyst_note if catalyst != "acid" else solvent_note if unknown_medium else
                    "Supported acid/water net conditions selected; temperature-dependent rates, competing pathways, conversion and experimental outcomes are not predicted.",
            "canRun": can_run, "missingSettings": ["catalyst"] if missing_acid else [], "referenceDifferences": [],
            "reagentRequirement": "actual neutral water", "reagentValidated": True,
            "activationRequirement": "acid catalyst (regenerated)",
            "factors": {"catalyst": {"status": "activation-required" if missing_acid else "unevaluated" if unsupported_activation else "model-match", "effect": "unknown" if catalyst != "acid" else "favors", "explanation": catalyst_note},
                       "solvent": {"status": "unevaluated" if unknown_medium else "model-match", "effect": "unknown" if unknown_medium else "neutral", "explanation": solvent_note},
                       "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": "Temperature does not establish a universal hydration rate or selectivity. Equilibrium composition, dehydration, acid-specific kinetics and experimental conversion are not calculated."}}}


def assess_dihydroxylation_conditions(conditions, reaction=None):
    if __package__: from .cooled_dihydroxylation_r3 import endpoint_assessment
    else: from cooled_dihydroxylation_r3 import endpoint_assessment
    named = endpoint_assessment(reaction or {}, conditions)
    if named is not None: return named
    catalyst, workup, temperature = (conditions.get(k, "") for k in ("catalyst", "workup", "temperature"))
    missing = [k for k, value in (("catalyst", catalyst), ("workup", workup)) if not value or (k == "catalyst" and value == "none")]
    wrong = catalyst not in {"", "none", "osmium"} or workup not in {"", "aqueous-release"} or temperature == "heated"
    status = "unevaluated" if wrong else "missing" if missing else "model-match"
    catalyst_note = ("Actual H2O2 is a co-oxidant; Os-based activation is required for this syn net model. Peroxide alone, acid, metal hydrogenation and radical settings are not equivalent osmylation conditions." if catalyst != "osmium" else
                     "Catalytic Os/H2O2 net model selected, not a catalyst-specific protocol, asymmetric ligand model or prediction of overoxidation suppression.")
    workup_note = ("Aqueous diol release/work-up is not confirmed. Inspect the conditional 2D net option; a free diol is not inferred as a completed 3D reaction." if workup != "aqueous-release" else
                   "Aqueous diol release is explicitly assumed for net-product reporting. Osmate hydrolysis, catalyst regeneration, work-up species and proton exchange are not explicitly mapped; this does not certify complete experimental conditions.")
    note = catalyst_note if catalyst != "osmium" else "Heated oxidative conditions are unvalidated; cleavage and further oxidation are not predicted." if temperature == "heated" else workup_note
    return {"state": "aligned" if status == "model-match" else "incomplete", "status": status, "label": LABELS[status],
            "canRun": status == "model-match", "note": note, "missingSettings": missing, "referenceDifferences": [],
            "reagentRequirement": "actual neutral H2O2", "reagentValidated": True,
            "activationRequirement": "Os-based catalyst and confirmed aqueous net-product release",
            "workupRepresented": False, "workupAssumptionConfirmed": workup == "aqueous-release",
            "factors": {"solvent": {"status": "unevaluated", "effect": "unknown", "explanation": "Solvent-specific Os/H2O2 compatibility is not evaluated. Aqueous release is a separate reporting assumption, not proof that a dry, aqueous, alcoholic or aprotic reaction medium is validated."},
                       "catalyst": {"status": "model-match" if catalyst == "osmium" else "missing" if catalyst in {"", "none"} else "unevaluated", "effect": "unknown", "explanation": catalyst_note},
                       "workup": {"status": "model-match" if workup == "aqueous-release" else "missing", "effect": "unknown", "explanation": workup_note},
                       "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": "No actual rate, yield, overoxidation or cleavage prediction is made. Heated settings are outside the validated net model."}}}


def assess_alkyne_partial_conditions(conditions, reaction=None):
    """Lindlar is actual activation, not merely a reference example profile.

    No pressure/time/endpoint model is present. A qualified representative
    conformer is allowed with selected Lindlar and unspecified/dry medium;
    that policy is explicitly not evidence of experimental stopping/selectivity.
    """
    catalyst, medium, temperature = (conditions.get(k, "") for k in ("catalyst", "solvent", "temperature"))
    selected = catalyst == "lindlar"
    medium_unknown = medium not in {"", "dry"}
    heated = temperature == "heated"
    competing = bool((reaction or {}).get("alkynePartialStereo", {}).get("singleSiteBookkeepingOnly"))
    status = ("missing" if not catalyst else "activation-required" if catalyst == "none" else
              "unsupported-pathway" if catalyst == "radical" else "unevaluated" if not selected or medium_unknown or heated or competing else "model-match")
    catalyst_note = ("Lindlar selective partial-hydrogenation activation is required; an unspecified catalyst does not establish stopping at C=C." if not catalyst or catalyst == "none" else
                     "Ordinary Pd/Pt-type metal catalysis may continue to the alkane; it is not the selective Lindlar model. One H2 equivalent alone does not guarantee an alkene endpoint." if catalyst == "metal" else
                     "The Lindlar poisoned-catalyst net model is selected. Exact catalyst state, hydrogen uptake and stopping conditions are not established." if selected else
                     "This activation is not a validated Lindlar partial-reduction system; radical/dissolving-metal/other reducing mechanisms are not inferred.")
    medium_note = ("Solvent is unspecified; only a qualified net product/conformer is available, not a validated solvent protocol." if not medium else
                   "Dry compatible-medium assumption selected; dryness alone does not validate a solvent, catalyst activity or experimental stopping." if medium == "dry" else
                   "Aqueous, alcoholic or generic polar-aprotic media require solvent-specific Lindlar validation; alcohol medium is not assumed equivalent to a screened substrate alcohol.")
    temperature_note = ("Heated partial-hydrogenation/isomerization behavior is not validated; no stopped alkene product is inferred in 3D." if heated else
                        "No temperature-dependent rate or product distribution is predicted; an ambient/unspecified setting is not a complete protocol.")
    note = catalyst_note if not selected else medium_note if medium_unknown else temperature_note if heated else catalyst_note + " " + medium_note
    competition_note = "More than one C≡C site may undergo Lindlar reduction. This theoretical single-site possibility preserves the other triple bond for 2D bookkeeping, not experimentally established selective conversion; single-site 3D is blocked."
    if competing and selected:
        note = competition_note
    return {"state": "aligned" if status == "model-match" else "incomplete", "status": status,
            "label": "Lindlar activation required" if status == "activation-required" else LABELS[status],
            "canRun": selected and not medium_unknown and not heated and not competing, "note": note,
            "singleSiteBookkeepingOnly": competing,
            "missingSettings": ["catalyst"] if not catalyst or catalyst == "none" else [], "referenceDifferences": [],
            "reagentRequirement": "one actual neutral H2", "reagentValidated": True,
            "activationRequirement": "selective Lindlar catalyst; ordinary metal does not guarantee partial reduction",
            "factors": {"competing sites": {"status": "unevaluated" if competing else "model-match", "effect": "unknown" if competing else "neutral", "explanation": competition_note if competing else "No additional alkyne site passes as an inert spectator."},
                        "catalyst": {"status": "model-match" if selected else "missing" if not catalyst or catalyst == "none" else "unsupported-pathway" if catalyst == "radical" else "unevaluated", "effect": "neutral" if selected else "unknown", "explanation": catalyst_note},
                        "solvent": {"status": "unevaluated", "effect": "unknown", "explanation": medium_note},
                        "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": temperature_note},
                        "pressure": {"status": "unevaluated", "effect": "unknown", "explanation": "Hydrogen pressure, uptake, catalyst loading, contact time, isomerization and over-reduction are not modeled. Selective one-site conversion and an experimental endpoint are not predicted."}}}


def assess_alkyne_complete_conditions(reaction, conditions):
    """Existing Pd/Pt metal selector, not Lindlar or an unspecified catalyst.

    Another alkyne is not an inert spectator under active metal/H2. Single-site
    equations stay inspectable, but no selective single-site 3D product is run.
    """
    catalyst, medium, temperature = (conditions.get(k, "") for k in ("catalyst", "solvent", "temperature"))
    selected = catalyst == "metal"
    competing = reaction["alkyneCompleteModel"]["singleSiteBookkeepingOnly"]
    medium_unknown = medium not in {"", "dry", "ethanolic-protic"}
    heated = temperature == "heated"
    missing_activation = catalyst in {"", "none"}
    status = "missing" if not catalyst else "activation-required" if catalyst == "none" else "unevaluated" if not selected or competing or medium_unknown or heated else "model-match"
    catalyst_note = ("Active-metal activation is required for the two-H2 complete-reduction model; missing or no catalyst does not establish an alkane outcome." if missing_activation else
                     "Lindlar is the separately supported selective partial-hydrogenation setting. It does not validate this two-H2 alkane endpoint." if catalyst == "lindlar" else
                     "The existing active-metal (Pd/Pt) net model is selected; exact catalyst support, activity and experimental completion are not established." if selected else
                     "This catalyst/activation is not validated for complete alkyne hydrogenation. No radical, dissolving-metal or new reducing system is inferred.")
    competition_note = ("Another C≡C can also hydrogenate under active-metal conditions. The selected single-site equation is conditional 2D bookkeeping only; selective retention of the other alkyne and an all-sites product are not predicted." if competing else
                        "No other unsaturated functional group survives this structural screen as an assumed inert spectator. Screened saturated OH/ethers are bounded net scope, not universal catalyst compatibility.")
    medium_note = ("Solvent is unspecified; a representative net conformer is conditional, not a validated experimental medium." if not medium else
                   "Dry or ethanolic medium is a bounded active-metal net assumption, not a solvent-specific validated protocol or Lindlar solvent permission." if not medium_unknown else
                   "Aqueous or generic polar-aprotic media need separately validated catalyst/substrate compatibility; this model does not assert the saturated 3D outcome.")
    temperature_note = ("Heated heterogeneous hydrogenation/cleavage conditions require separate validation; no forcing-condition selectivity is inferred." if heated else
                        "No temperature-dependent rate, yield or experimental completion is calculated.")
    note = catalyst_note if not selected else competition_note if competing else medium_note if medium_unknown else temperature_note if heated else catalyst_note + " " + medium_note
    allowed = selected and not competing and not medium_unknown and not heated
    confidence_label = ("Partial-hydrogenation setting · full reduction not asserted" if catalyst == "lindlar" else
                        "Competing reductions unresolved · conditional 2D only" if competing and selected else
                        "Active-metal net model · 2 H2 per site · outcome not predicted" if allowed else
                        "Full-reduction conditions not validated · conditional 2D only")
    return {"state": "aligned" if allowed else "incomplete", "status": status,
            "label": "Active-metal activation required" if status == "activation-required" else LABELS[status],
            "confidenceLabel": confidence_label, "canRun": allowed, "note": note,
            "missingSettings": ["catalyst"] if missing_activation else [], "referenceDifferences": [],
            "reagentRequirement": "two actual neutral H2 equivalents per selected C≡C", "reagentValidated": True,
            "activationRequirement": "existing active-metal Pd/Pt model, not selective Lindlar",
            "singleSiteBookkeepingOnly": competing,
            "factors": {"catalyst": {"status": "model-match" if selected else "missing" if missing_activation else "unevaluated", "effect": "neutral" if selected else "unknown", "explanation": catalyst_note},
                        "solvent": {"status": "unevaluated", "effect": "unknown", "explanation": medium_note},
                        "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": temperature_note},
                        "competing reductions": {"status": "unevaluated" if competing else "model-match", "effect": "unknown" if competing else "neutral", "explanation": competition_note},
                        "hydrogen supply": {"status": "unevaluated", "effect": "unknown", "explanation": "H2 identity is validated, but available amount, pressure, uptake, catalyst loading and contact time are not specified by this selector. Two H2 per selected site is theoretical stoichiometry, not evidence that sufficient hydrogen or conversion was achieved."}}}


def assess_alkyne_halogen_conditions(reaction, conditions):
    """Independent X2/alkyne confidence: supply, capture and stereo are separate."""
    model = reaction["alkyneHalogenModel"]
    medium, catalyst, temperature, stage = (conditions.get(k, "") for k in ("solvent", "catalyst", "temperature", "additionStage"))
    radical = catalyst == "radical"
    extra = catalyst not in {"", "none", "radical"}
    missing = [k for k, v in (("solvent", medium), ("additionStage", stage)) if not v]
    capture = medium in {"aqueous-protic", "ethanolic-protic"}
    unknown_medium = medium not in {"", "dry", "aqueous-protic", "ethanolic-protic"}
    competing = model["singleSiteBookkeepingOnly"]
    uncertain_cl = model["halogen"] == "Cl" and (model["equivalents"] == 1 or model["oxygenCompatibilityUnresolvedForCl2"])
    status = "unsupported-pathway" if radical else "unevaluated" if extra or capture or unknown_medium or temperature == "heated" or competing or uncertain_cl else "missing" if missing else "model-match"
    medium_note = ("Water can capture electrophilically activated alkynes; aqueous oxygenated products are not this dihaloalkene/tetrahalide model." if medium == "aqueous-protic" else
                   "Alcohol solvent can compete as a nucleophile; haloether/capture chemistry is not the selected X2-only net equation." if medium == "ethanolic-protic" else
                   "Generic polar-aprotic medium does not establish solvent-specific compatibility or absence of capture." if unknown_medium else
                   "A compatible non-nucleophilic medium is unspecified; conditional 2D only." if not medium else
                   "Dry compatible non-nucleophilic medium is a net assumption, not proof that every dry solvent is inert.")
    catalyst_note = ("Photochemical/radical initiation is outside this electrophilic X2 model; propargylic substitution, isomerization and mixed products are not inferred." if radical else
                     "Added activation has not been validated for this X2/alkyne model." if extra else
                     "Actual neutral X2 is consumed; no acid, metal or radical activation is required by this net model. Light exposure is not specified or simulated.")
    equivalent_note = ("Equivalents are unspecified: the displayed one-X2 equation is a hypothetical first-stage preview, not an established reagent amount or endpoint." if not stage else
                       f"The selected stage assumes {model['equivalents']} actual {model['halogen']}2 equivalents per chosen C≡C. Available reagent, concentration, time and stopping/overaddition are not established by this selector.")
    competition_note = ("Other C≡C sites also consume X2. Selective one-site 3D is blocked; conditional 2D retains the other site only as bookkeeping, not predicted selectivity." if competing else
                        "No unresolved extra pi site passes as an inert spectator. Screened remote O groups remain conditional net scope.")
    stereo_note = ("Cl2 first-stage stereospecificity is not established by the generic selector; E/Z remains unassigned and no single 3D geometry is asserted." if model["halogen"] == "Cl" and model["equivalents"] == 1 else
                   "Cl2 with additional oxygen functionality needs independent capture/oxidation compatibility; only the conditional net graph is available." if model["oxygenCompatibilityUnresolvedForCl2"] else
                   "Br2 first-stage anti relationship is qualified and independently CIP-checked, not a guaranteed exclusive E product." if model["stereoAssignment"] == "E" else
                   "First-stage Br2 geometry is unsigned because the compatible-medium anti model is not established by these settings." if model["equivalents"] == 1 else
                   "Two-equivalent saturation has no selected-bond E/Z and no new local centers; experimental completion is not predicted.")
    temp_note = "Heated X2 side chemistry/stereo fidelity is unvalidated; no forcing-condition product is asserted." if temperature == "heated" else "Temperature-dependent rates, yields and stereoisomer ratios are not evaluated."
    note = catalyst_note if radical or extra else competition_note if competing else stereo_note if uncertain_cl else temp_note if temperature == "heated" else equivalent_note if not stage else medium_note
    allowed = status == "model-match"
    return {"state": "aligned" if allowed else "incomplete", "status": status, "label": LABELS[status], "canRun": allowed,
            "confidenceLabel": f"{model['equivalents']}-X2 conditional net model · outcome not predicted" if allowed else "Alkyne X2 conditions/selectivity unresolved · conditional 2D only",
            "note": note, "missingSettings": missing, "referenceDifferences": [],
            "singleSiteBookkeepingOnly": competing, "reagentValidated": True,
            "reagentRequirement": f"{model['equivalents']} actual neutral {model['halogen']}2 equivalent(s)",
            "activationRequirement": "none; electrophilic non-nucleophilic model only",
            "factors": {"solvent": {"status": "model-match" if medium == "dry" else "missing" if not medium else "unevaluated", "effect": "neutral" if medium == "dry" else "unknown", "explanation": medium_note},
                        "catalyst": {"status": "unsupported-pathway" if radical else "unevaluated" if extra else "model-match", "effect": "unknown" if radical or extra else "neutral", "explanation": catalyst_note},
                        "additionStage": {"status": "missing" if not stage else "model-match", "effect": "unknown" if not stage else "neutral", "explanation": equivalent_note},
                        "halogen supply": {"status": "unevaluated", "effect": "unknown", "explanation": equivalent_note},
                        "competing sites": {"status": "unevaluated" if competing else "model-match", "effect": "unknown" if competing else "neutral", "explanation": competition_note},
                        "stereochemistry": {"status": "unevaluated" if uncertain_cl else "model-match", "effect": "unknown" if uncertain_cl else "neutral", "explanation": stereo_note},
                        "temperature": {"status": "unevaluated", "effect": "unknown", "explanation": temp_note}}}


def assess_alkyne_hx_conditions(reaction, conditions):
    """Ionic selected-site assumptions, not copied alkene capture permission."""
    model = reaction["alkyneHxModel"]
    medium, catalyst, temperature, stage = (conditions.get(k, "") for k in ("solvent", "catalyst", "temperature", "additionStage"))
    missing = [k for k,v in (("solvent",medium),("temperature",temperature),("additionStage",stage)) if not v]
    radical = catalyst == "radical"
    activation = catalyst not in {"", "none", "radical"}
    capture = medium in {"aqueous-protic", "ethanolic-protic"}
    uncertain_medium = medium not in {"", "dry", "aqueous-protic", "ethanolic-protic"}
    heated = temperature == "heated"
    internal_geometry = model["equivalents"] == 1 and model["internal"]
    cl_unvalidated = model["halogen"] == "Cl"
    hi_second = model["halogen"] == "I" and model["equivalents"] == 2
    competing = model["singleSiteBookkeepingOnly"] or model["oxygenCompetition"]
    status = "unsupported-pathway" if radical else "unevaluated" if activation or capture or uncertain_medium or heated or competing or internal_geometry or cl_unvalidated or hi_second else "missing" if missing else "model-match"
    allowed = status == "model-match"
    reagent_note = ("HCl has a valid net atom inventory, but this generic selector does not define a validated alkyne hydrochlorination activation/reagent formulation. Specialized Au/HCl, directed or transfer systems are not inferred from the Pd/Pt/acid selector. This is not a claim that uncatalyzed HCl addition is always impossible." if cl_unvalidated else
                    "Two-HI geminal accounting is retained, but its reagent-specific stopping, substrate compatibility and product stability are unvalidated by these selectors; only conditional 2D is asserted." if hi_second else
                    "Actual HBr uses the bounded ionic vinyl/geminal net model, not radical anti-Markovnikov addition or a solvent-specific protocol." if model["halogen"] == "Br" else
                    "Actual one-equivalent HI uses a bounded terminal Markovnikov net model; in-situ, metal-directed and transfer hydroiodination are separate unimplemented chemistry.")
    medium_note = ("Water/alcohol can compete with halide capture and change acid/halide activities; oxygenated/capture products are not this HX-only model." if capture else
                   "A generic polar-aprotic setting does not validate the actual HX formulation or solvent nucleophilicity." if uncertain_medium else
                   "Compatible non-capturing medium is missing; dryness or peroxide absence is not inferred." if not medium else
                   "Dry compatible non-capturing medium is an explicit net assumption, not proof that every dry solvent tolerates HX.")
    activation_note = ("Radical/peroxide initiation is outside the ionic model. No anti-Markovnikov HBr or analogous HCl/HI radical product is predicted." if radical else
                       "Added activation is unvalidated for this selected HX/alkyne model; no catalyst-specific products are inferred." if activation else
                       "HX itself supplies the acidic H and the entering halogen and is consumed. No separate acid reagent is invented; absence of peroxide/light initiation is an assumption, not measured.")
    equivalent_note = ("Equivalents are unspecified; the first-stage 2D equation is hypothetical and cannot assert supplied amount or completion." if not stage else
                       f"The selected net endpoint consumes {model['equivalents']} actual H{model['halogen']} molecule(s). Actual acid activity, amount, stopping and later addition are not established.")
    stereo_note = ("Internal first-stage E/Z remains unassigned; generic ionic HX is not automatically anti/trans. No single 3D stereochemical outcome is asserted." if internal_geometry else
                   "Terminal CH2= products have no E/Z; geminal saturation removes C=C and creates no local center. Distant mapped configurations remain checked.")
    competition_note = ("Other alkynes can consume HX: this selected-site equation is 2D bookkeeping only, not experimental one-site selectivity or an all-sites product." if model["singleSiteBookkeepingOnly"] else
                        f"Remote oxygen is not proven inert to H{model['halogen']}: protonation, alcohol substitution and ether cleavage remain unresolved. The preserved-O equation is conditional 2D only." if model["oxygenCompetition"] else
                        "No unscreened extra reactive group is assumed inert. Other possible acid-specific chemistry and experimental selectivity remain outside this net model.")
    temperature_note = ("Explicit ambient conditions are required for the bounded conformer policy; heating/forcing conditions are separately unvalidated." if temperature != "ambient" else
                        "Ambient is a reporting assumption, not a measured rate, yield or proof of suppressed competing chemistry.")
    note = activation_note if radical or activation else competition_note if competing else reagent_note if cl_unvalidated or hi_second else stereo_note if internal_geometry else medium_note if capture or uncertain_medium else temperature_note if temperature != "ambient" else equivalent_note if not stage else medium_note
    return {"state":"aligned" if allowed else "incomplete","status":status,"label":LABELS[status],"canRun":allowed,
            "confidenceLabel":"Ionic alkyne HX net model · outcome not predicted" if allowed else "Alkyne HX conditions/stereo unresolved · conditional 2D only",
            "note":note,"missingSettings":missing,"referenceDifferences":[],"reagentValidated":True,
            "reagentRequirement":f"{model['equivalents']} actual neutral H{model['halogen']} equivalent(s)",
            "activationRequirement":"HX consumed; no generic separate activation permission",
            "factors":{
                "reagent profile":{"status":"unevaluated" if cl_unvalidated or hi_second else "model-match","effect":"unknown" if cl_unvalidated or hi_second else "neutral","explanation":reagent_note},
                "solvent":{"status":"model-match" if medium=="dry" else "missing" if not medium else "unevaluated","effect":"neutral" if medium=="dry" else "unknown","explanation":medium_note},
                "catalyst":{"status":"unsupported-pathway" if radical else "unevaluated" if activation else "model-match","effect":"unknown" if radical or activation else "neutral","explanation":activation_note},
                "additionStage":{"status":"model-match" if stage else "missing","effect":"neutral" if stage else "unknown","explanation":equivalent_note},
                "HX supply":{"status":"unevaluated","effect":"unknown","explanation":equivalent_note},
                "competing chemistry":{"status":"unevaluated" if competing else "model-match","effect":"unknown" if competing else "neutral","explanation":competition_note},
                "stereochemistry":{"status":"unevaluated" if internal_geometry else "model-match","effect":"unknown" if internal_geometry else "neutral","explanation":stereo_note},
                "temperature":{"status":"missing" if not temperature else "unevaluated" if heated else "model-match","effect":"neutral" if temperature=="ambient" else "unknown","explanation":temperature_note},
                "radical initiation absence":{"status":"unevaluated","effect":"unknown","explanation":"No peroxide concentration, inhibitor, light exposure or oxygen measurement is entered. The selected ionic net model is not evidence these are absent."}}}


ALKYNE_PATHWAYS = frozenset({"Alkyne partial hydrogenation", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"})


def alkyne_input_evidence(assessment, conditions, path):
    """Fail closed on explicit unsupported input, without discarding net 2D.

    This is a confidence guard, not a reagent/solvent expansion. Unrelated
    pathways (including dihydroxylation) retain their existing assessments.
    """
    unknown = sorted(set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - CONDITION_FIELDS))
    issues = [{"field": k, "kind": "unsupported", "explanation": f"Condition field '{k}' is not supported by this model; its value was not interpreted. Conditional 2D remains available, but 3D is blocked."} for k in unknown]
    partial, complete = path == "Alkyne partial hydrogenation", path == "Alkyne hydrogenation"
    allowed = {"solvent": {"", "dry", *(["ethanolic-protic"] if complete else [])},
               "temperature": {"", "ambient"},
               "catalyst": {"lindlar"} if partial else {"metal"} if complete else {"", "none"}}
    for field, supported in allowed.items():
        selected = conditions.get(field, "")
        if not selected or selected in supported:
            continue
        kind = ("unsupported" if field == "catalyst" and selected == "radical" else
                "conflicting" if field == "catalyst" and (selected == "none" or partial and selected == "metal" or complete and selected == "lindlar")
                or field == "solvent" and selected in {"aqueous-protic", "ethanolic-protic"} and not (partial or complete) else "unvalidated-alternative")
        explanation = assessment["factors"][field]["explanation"]
        issues.append({"field": field, "kind": kind, "explanation": f"{field}: {explanation}"})
    for field in ("oxidationStage", "workup"):
        if conditions.get(field):
            issues.append({"field": field, "kind": "conflicting", "explanation": f"{field} belongs to a different pathway; no oxidation or diol-release chemistry is included in this alkyne model. Clear this setting."})
    assessment["conditionIssues"] = issues
    # These persistent UI selectors are bookkeeping, not activation evidence.
    assessment["notApplicableSettings"] = [k for k in ("polymerUnits", *(["additionStage"] if partial or complete else [])) if conditions.get(k)]
    if issues:
        assessment.update(canRun=False, state="incomplete")
        if any(i["kind"] == "unsupported" for i in issues):
            assessment.update(status="unsupported-pathway", label="Unsupported condition input")
        elif assessment["status"] not in {"activation-required", "missing"}:
            assessment.update(status="unevaluated", label="Conflicting or unvalidated conditions")
        assessment["note"] = " ".join(i["explanation"] for i in issues) + " " + assessment["note"]
        assessment["confidenceLabel"] = "Condition inputs unresolved · conditional 2D only"
        for issue in issues:
            assessment["factors"][issue["field"]] = {"status": "unsupported-pathway" if issue["kind"] == "unsupported" else "unevaluated", "effect": "unknown", "explanation": issue["explanation"]}
    return assessment


def cooling_confidence(assessment, conditions, reaction=None):
    """Shared cooling assessment, retaining unreviewed pathways' prior gate.

    This does not alter graph matching or invent a low-temperature protocol.
    Existing ambient/heated/unset behavior is unchanged, and stronger activation,
    missing-input or unsupported-pathway explanations are retained.
    """
    if __package__:
        from . import named_condition_profiles as named, reaction_temperature_profiles as profiles
    else:
        import named_condition_profiles as named, reaction_temperature_profiles as profiles
    issue = named.selection_issue(profiles.selected_profile(conditions), reaction or {}, conditions)
    if issue:
        return named.reject_selection(assessment, conditions, issue)
    if conditions.get("temperature") != "cooled":
        return assessment
    if "coolingPolicy" in assessment:
        return assessment if current_cooling_overlay(assessment, reaction, conditions) else reject_cooling_contract(assessment, reaction)
    assessment = normalize_legacy_cooling_assessment(assessment, conditions, reaction)
    review = assess_cooling_support(reaction, conditions, assessment)
    result = deepcopy(assessment)
    result["cooling"] = review
    if review["canGenerate3D"]:
        result.update(canRun=True, state="aligned", status="model-match", coolingPolicy=review["modelId"], coolingUnvalidated=False,
                      confidenceLabel=profile_for_review(review).confidence_label)
        if profile_for_review(review).explicit_only:
            result["label"] = "Named condition profile matches"
        result["factors"]["temperature"] = {
            "status": "model-match", "effect": "neutral", "explanation": review["note"]}
        # Persistent UI selectors are not equivalents or activation evidence.
        result["notApplicableSettings"] = list(dict.fromkeys([
            *result.get("notApplicableSettings", []),
            *(key for key in ("additionStage", "polymerUnits") if conditions.get(key))]))
        result["note"] = review["note"] + " " + result.get("note", "")
        return result
    if review["status"] == "conditions-unresolved":
        # A recognized cooling model can fail on reagent/medium/activation.
        # Do not misattribute these failures to an unreviewed temperature.
        model_name = profile_for_review(review).model_name
        result.update(canRun=False, state="incomplete", coolingPolicy=review["modelId"],
                      coolingUnvalidated=True, confidenceLabel=f"Cooled {model_name} conditions unresolved · conditional 2D only")
        if result.get("status") not in {"missing", "activation-required", "unsupported-pathway"}:
            result.update(status="unevaluated", label=f"Cooled {model_name} conditions unresolved")
        issues = result.setdefault("conditionIssues", [])
        for issue in review["conditionIssues"]:
            if not any(existing.get("field") == issue["field"] for existing in issues):
                issues.append(deepcopy(issue))
            result.setdefault("factors", {})[issue["field"]] = {
                "status": "unsupported-pathway" if issue["kind"] == "unsupported" else "unevaluated",
                "effect": "unknown", "explanation": issue["explanation"]}
        result["factors"]["temperature"] = {"status": "model-match", "effect": "neutral",
            "explanation": f"Cooling is compatible with the bounded {model_name} net model, but does not override unresolved reagent, medium, activation or condition-input requirements."}
        result["note"] = review["note"] + " " + result.get("note", "")
        return result
    result.update(canRun=False, state="incomplete", coolingPolicy="unvalidated-low-temperature-v1", coolingUnvalidated=True)
    if result.get("status") not in {"missing", "activation-required", "unsupported-pathway"}:
        result.update(status="unevaluated", label="Cooled conditions not evaluated")
    result["confidenceLabel"] = "Cooled conditions unvalidated · conditional 2D only"
    previous_note = result.get("note", "")
    result.setdefault("missingSettings", [])
    result.setdefault("referenceDifferences", [])
    result.setdefault("factors", {})["temperature"] = {
        "status": "unevaluated", "effect": "unknown", "explanation": COOLING_NOTE}
    issues = result.setdefault("conditionIssues", [])
    # A few older assessors describe every non-ambient input as "heated".
    # Keep their gates, but do not repeat that misleading explanation for a
    # newly distinct cooled selection.
    for issue in issues:
        if issue.get("field") == "temperature":
            previous_note = previous_note.replace(issue["explanation"], "").strip()
            issue["explanation"] = COOLING_NOTE
    if not any(i.get("field") == "temperature" for i in issues):
        issues.append({"field": "temperature", "kind": "unvalidated-alternative", "explanation": COOLING_NOTE})
    result["note"] = (review["note"] + " Other model settings (excluding the unvalidated cooled temperature): "
                      + previous_note)
    if "conditionCompleteEligibility" in result:
        result["conditionCompleteEligibility"] = False
    return result


def assess_conditions(reaction, conditions):
    return cooling_confidence(_assess_conditions(reaction, conditions), conditions, reaction)


def _assess_conditions(reaction, conditions):
    path, profile = reaction["mechanism"], reaction["profile"]
    if path == "Aldehyde oxidation":
        if __package__: from .aldehyde_oxidation_conditions import assess_conditions as assess_aldehyde
        else: from aldehyde_oxidation_conditions import assess_conditions as assess_aldehyde
        return assess_aldehyde(reaction, conditions)
    if path == "Alcohol substitution":
        if __package__: from .alcohol_substitution_rule import assess_conditions as assess_alcohol_substitution
        else: from alcohol_substitution_rule import assess_conditions as assess_alcohol_substitution
        return assess_alcohol_substitution(reaction, conditions)
    if path == "Alcohol dehydration":
        if __package__: from .alcohol_dehydration_rule import assess_conditions as assess_dehydration
        else: from alcohol_dehydration_rule import assess_conditions as assess_dehydration
        return assess_dehydration(reaction, conditions)
    if path in ALKYNE_PATHWAYS:
        assessor = {"Alkyne hydrohalogenation": assess_alkyne_hx_conditions,
                    "Alkyne halogenation": assess_alkyne_halogen_conditions,
                    "Alkyne hydrogenation": assess_alkyne_complete_conditions}
        assessment = (assess_alkyne_partial_conditions(conditions, reaction) if path == "Alkyne partial hydrogenation"
                      else assessor[path](reaction, conditions))
        return alkyne_input_evidence(assessment, conditions, path)
    if path == "Alkene dihydroxylation":
        return assess_dihydroxylation_conditions(conditions, reaction)
    if path == "Epoxidation":
        return assess_epoxidation_conditions(conditions)
    if path == "Chlorination":
        return assess_chlorination_conditions(conditions)
    if path == "Bromination":
        return assess_bromination_conditions(conditions)
    if path == "Hydration":
        return assess_hydration_conditions(conditions)
    if path == "Hydrohalogenation":
        return assess_hydrohalogenation_conditions(reaction, conditions)
    if path not in REVIEWED:
        raise ValueError("This condition assessment is limited to the individually reviewed pathways.")
    missing = [k for k in profile if not conditions.get(k)]
    different = [k for k, v in profile.items() if conditions.get(k) and conditions[k] != v]
    factors = {}
    for key in ("solvent", "temperature"):
        selected, reference = conditions.get(key, ""), profile.get(key)
        if reference and not selected:
            item = {"status": "missing", "effect": "unknown", "explanation": f"The reference {key} is not specified. This is an incomplete comparison setting, not proof of missing chemical activation or inability to react."}
        elif reference and selected != reference:
            item = {"status": "reference-difference", "effect": "neutral", "explanation": f"The selected {key} differs from the {reference} reference. A preset mismatch alone does not establish chemical disfavor or exclude the pathway."}
        else:
            item = {"status": "model-match" if reference else "unevaluated", "effect": "neutral" if selected else "unknown",
                    "explanation": f"The reference {key} matches; no rate or product preference is established." if reference else "No temperature requirement is validated for this SN2 net model; heating may change competition, not prove substitution unfavorable."}
        if key == "solvent" and path == "SN2" and selected in {"aqueous-protic", "ethanolic-protic"}:
            item = {"status": "disfavored", "effect": "disfavors", "explanation": "Protic solvation of OH⁻ can reduce its nucleophilic activity relative to a comparable polar-aprotic medium. This is one disfavoring factor, not proof that SN2 cannot occur or that elimination wins."}
        elif key == "solvent" and selected == "dry" and path in {"SN1", "E1"}:
            item = {"status": "unevaluated", "effect": "unknown", "explanation": "Actual water is selected as reagent/solvent but the medium is marked dry. Water activity and ionizing ability cannot be inferred from these conflicting settings."}
        factors[key] = item
    catalyst = conditions.get("catalyst", "")
    extra = catalyst not in {"", "none"}
    factors["catalyst"] = {"status": "unevaluated" if extra else "model-match", "effect": "unknown" if extra else "neutral",
                          "explanation": "This added catalyst is not evaluated for this pathway. Acid–base neutralization, reagent availability and catalyst-specific chemistry are not modeled." if extra else
                                         "No added catalyst/activation requirement is established for this supported net model; the actual hydroxide/water reagent graph is validated separately."}
    uncertain = extra or any(v["status"] == "unevaluated" for k, v in factors.items() if k != "temperature")
    disfavored = any(v["status"] == "disfavored" for v in factors.values())
    status = "unevaluated" if uncertain else "missing" if missing else "disfavored" if disfavored else "reference-difference" if different else "model-match"
    state = "alternative" if different else "incomplete" if missing or uncertain else "aligned"
    notes = {"model-match": "Selected conditions match the supported reference model; no experimental outcome or selectivity is guaranteed.",
             "reference-difference": "Conditions differ from the reference; this alone is not evidence that the pathway is chemically unfavorable.",
             "missing": "Set the missing comparison conditions. Actual reagent eligibility is checked separately; no missing activation requirement is inferred.",
             "disfavored": "A supported disfavoring factor is present; this does not predict inability to react, a competing winner or a product ratio.",
             "unevaluated": "Some conditions cannot be evaluated reliably in this model; products are bounded net options, not an approved protocol."}
    return {"state": state, "status": status, "label": LABELS[status], "note": notes[status],
            "missingSettings": missing, "referenceDifferences": different, "factors": factors,
            "reagentRequirement": "actual hydroxide" if path in {"SN2", "E2"} else "actual water",
            "reagentValidated": True, "activationRequirement": "none independently established by this model"}
