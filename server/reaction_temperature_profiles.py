"""Immutable registry for individually reviewed cooled net models.

This is condition/output policy, not a reaction rule or temperature simulator.
Br2, peroxyacid, explicit cyclohexene/Pd-silica and exact R3 free-product
profiles are registered. Unknown identifiers
and versions never authorize a conformer. The v1 response remains compatible.
"""
from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable
from rdkit import Chem
if __package__:
    from . import cooled_dihydroxylation_r3 as r3
    from .named_condition_profiles import SELECTION_FIELDS, descriptor, fact, describe, reference
else:
    import cooled_dihydroxylation_r3 as r3
    from named_condition_profiles import SELECTION_FIELDS, descriptor, fact, describe, reference

REGISTRY_VERSION = 1
CONDITION_FIELDS = frozenset({"solvent", "temperature", "catalyst", "oxidationStage", "additionStage", "polymerUnits", "workup"}) | SELECTION_FIELDS
LEGACY_COOLING_PATHWAYS = frozenset({
    "Hydrogenation", "Carbonyl hydrogenation", "Esterification",
    "Ester hydrolysis", "Ester saponification", "Polymerization model",
})

COOLING_NOTE = (
    "Cooled / low-temperature conditions are selected. This is a qualitative input, not an exact "
    "temperature. No low-temperature range or pathway outcome has been validated for this selection; "
    "cooling is not treated as room temperature "
    "or heating. This does not mean the reaction is impossible or chemically unfavorable. "
    "Inspect the conditional 2D net option; no cooled 3D product is asserted. "
    "Where this pathway provides a separately supported profile, review its temperature setting "
    "only if that is the model you intend."
)


COOLED_BROMINATION_MODEL = "cooled-alkene-bromination-v1"
COOLED_BROMINATION_SOURCES = (
    "https://www.orgsyn.org/demo.aspx?prep=CV2P0171",
    "https://doi.org/10.1016/j.orggeochem.2004.06.019",
)

COOLED_EPOXIDATION_MODEL = "cooled-peroxyacid-epoxidation-v1"
COOLED_EPOXIDATION_SOURCES = (
    "https://doi.org/10.1081/SCC-120004069",
    "https://patents.google.com/patent/US7612123B2/en",
)
MCPBA_IDENTITY = "O=C(OO)c1cccc(Cl)c1"
PERBENZOIC_IDENTITY = "O=C(OO)c1ccccc1"
COOLED_PERBENZOIC_MODEL = "cooled-perbenzoic-epoxidation-v1"
COOLED_PERBENZOIC_SOURCES = ("https://www.orgsyn.org/demo.aspx?prep=CV1P0494",)
PERBENZOIC_SCOPE = "terminal-vinylbenzene-hydrocarbons-v1"
COOLED_CYCLOHEXENE_MODEL = "cooled-cyclohexene-pd-silica-v1"
CYCLOHEXENE_SOURCE = "https://patents.google.com/patent/JP2004250387A/en"

# This is a software-scope review, not an assertion that cooling prevents the
# corresponding experimental chemistry. No entry grants output permission.
COOLING_LIMITATIONS = {
    "Hydrogenation": "No cooled H2/metal catalyst–substrate profile is qualified by generic controls alone. Cold alkene hydrogenation is documented, but the current Metal Catalyst (Pd/Pt) and generic medium choices do not identify the reviewed catalyst/support, solvent or H2 pressure. No current selector combination qualifies cooled alkene-hydrogenation 3D without an explicitly selected named profile. Only cyclohexene has a separately reviewed Pd/silica-A reference model. Cooling alone does not establish catalyst activity, completion or selective retention of other reducible groups; do not substitute ambient conditions unless that is the model you intend.",
    "Chlorination": "A cooled Cl2/dichloride profile needs independent validation of chlorine-specific medium capture and radical competition; the Br2 cooling profile does not qualify Cl2. Dry / no water and None Added do not specify the solvent, chloride additives, light or atmosphere of a reviewed cooled formulation. None Added means no selected extra activation, not proof that radical or substitution chemistry is absent. No current dropdown combination qualifies cooled Cl2 3D; do not substitute ambient conditions unless that is the model you intend.",
    "Hydration": "No cooled acid/water hydration profile is reviewed; required acid activation and existing rearrangement, water-capture and cyclization screens still apply.",
    "Hydrohalogenation": "No cooled ionic HX profile is reviewed; oxygen-spectator retention also has an explicitly ambient HCl boundary. Cooling cannot qualify radical HBr, rearrangement or solvent-capture chemistry.",
    "SN2": "No cooled hydroxide substitution profile is reviewed; solvent activity and substitution/elimination competition remain unevaluated. Validated backside inversion alone is not evidence of cooled compatibility. Reported base-hydrolysis measurements near 14 C use aqueous phosphate buffers; they do not validate a generic polar-aprotic cooled profile or substituted substrates. No current selector combination qualifies cooled SN2 3D; do not substitute ambient conditions unless that is the model you intend.",
    "SN1": "No cooled water-solvolysis profile is reviewed; ionization, water capture and competing E1 chemistry are not established by this temperature selector.",
    "E2": "No cooled hydroxide elimination profile is reviewed. Heated is a reference, not proof that cooled E2 is impossible; base activity, competition and existing geometry screens still need validation.",
    "E1": "No cooled water-based elimination profile is reviewed. Heated is a reference, not a universal requirement; carbocation formation and competing SN1 chemistry need a separately reviewed profile.",
    "Alcohol oxidation": "A cooled hypochlorite oxidation profile is not reviewed; temperature alone cannot establish the oxidation endpoint or formulation-specific compatibility.",
    "Aldehyde oxidation": "The current hypochlorite neutral-acid reporting profile accepts ambient/unset temperature, not cooled conditions; pH, carboxylate speciation and separate acid work-up remain unresolved.",
    "Carbonyl hydrogenation": "No cooled H2/metal carbonyl-reduction profile is reviewed; catalyst-specific C=O activity and competing reductions are not established by cooling.",
    "Esterification": "No cooled acid-catalyzed esterification profile is reviewed; reaction progress and equilibrium composition cannot be inferred from cooling.",
    "Ester hydrolysis": "No cooled acid/water hydrolysis profile is reviewed; lactone, aryl-ester, site and stereochemical restrictions remain, and conversion/equilibrium is not predicted.",
    "Alcohol dehydration": "The existing sulfuric-acid dehydration profile requires heated conditions. Cooling does not qualify that profile or resolve activation, ether formation or other competing chemistry.",
    "Alcohol substitution": "The existing HX alcohol-substitution profiles use heated methyl/primary or ambient secondary/tertiary settings; cooled activation, elimination competition and stereochemical scope are not reviewed.",
    "Ester saponification": "No cooled base-hydrolysis profile is reviewed. Its charged carboxylate product additionally meets the engine's ionic-geometry exclusion; a neutral acid is not substituted without an appropriate separate work-up.",
    "Alkyne hydrogenation": "No cooled two-H2 active-metal completion profile is reviewed; catalyst activity, incomplete reduction and competing sites remain unresolved.",
    "Alkyne partial hydrogenation": "No cooled Lindlar stopping profile is reviewed; catalyst identity, one H2 equivalent and a syn graph do not establish a stopped alkene endpoint.",
    "Alkyne halogenation": "No cooled one-/two-X2 profile is reviewed; reagent identity, equivalent count, medium capture, competing sites and first-stage chlorine stereochemistry remain independent limits.",
    "Alkyne hydrohalogenation": "The current qualified alkyne-HX conformer profile requires ambient conditions. Cooling does not resolve HCl activation, internal first-stage E/Z, two-HI or oxygen-spectator limitations.",
    "Alkene dihydroxylation": "No generic cooled Os/H2O2 profile is reviewed; only three exact source-parent named references can qualify independently. Generic Os activation or aqueous release cannot select the source formulation. Other substrates, specified stereochemical outcomes, further oxidation and solvent/work-up generalizations remain unqualified.",
    "Polymerization model": "The finite BPO-initiated oligomer connectivity demonstration has no cooled initiation, propagation or termination model; its heated reference is not a temperature simulation.",
}


def _cooled_epoxidation_support(reaction, conditions, assessment, review):
    """One mCPBA identity/profile; not blanket cold permission for peracids."""
    review.update(modelId=COOLED_EPOXIDATION_MODEL, status="conditions-unresolved",
                  sourceUrls=list(COOLED_EPOXIDATION_SOURCES), profileLabel="Cooled mCPBA epoxidation",
                  temperatureScope="Mild cooled reaction-control reference (documented near 0 C, addition kept at or below 10 C); no exact temperature is entered, measured or simulated. Not arbitrary cryogenic conditions.")
    issues = []
    if reaction.get("peroxyacidIdentity") != MCPBA_IDENTITY:
        issues.append({"field": "reagentIdentity", "kind": "unvalidated-alternative",
                       "explanation": "This cooled epoxidation profile requires actual neutral meta-chloroperbenzoic acid (mCPBA). Other peracids, ortho/para isomers, a matching formula or a molecule named mCPBA do not qualify; no reagent is substituted automatically."})
    if conditions.get("solvent") != "dry":
        issues.append({"field": "solvent", "kind": "unvalidated-alternative",
                       "explanation": "The cooled mCPBA net model requires the existing dry/compatible non-capturing medium assumption. Evidence is anchored to dichloromethane, not to every dry solvent; aqueous, alcohol and generic polar-aprotic media do not establish epoxide stability."})
    if conditions.get("catalyst", "") not in {"", "none"}:
        issues.append({"field": "catalyst", "kind": "unvalidated-alternative",
                       "explanation": "Added acid, metal, Os, Lindlar or radical activation is not the reviewed no-added-activation mCPBA oxygen-transfer profile; buffering or a new catalyst is not inferred."})
    unknown = sorted(set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - CONDITION_FIELDS))
    for field in unknown:
        issues.append({"field": field, "kind": "unsupported",
                       "explanation": f"Unvalidated condition field {field} was supplied; it is not interpreted as compatible cooled mCPBA conditions."})
    for field in ("oxidationStage", "workup"):
        if conditions.get(field):
            issues.append({"field": field, "kind": "unvalidated-alternative",
                           "explanation": f"{field} belongs to a different modeled stage and is not included in this cooled epoxide profile; no epoxide opening, diol release or additional work-up chemistry is inferred."})
    if (assessment.get("canRun") is not True or assessment.get("status") != "model-match"
            or not assessment.get("reagentValidated") or assessment.get("reagentRequirement") != "actual neutral single peroxyacid"
            or assessment.get("conditionIssues")):
        if not issues:
            issues = deepcopy(assessment.get("conditionIssues")) or [{"field": "conditions", "kind": "unvalidated-alternative",
                "explanation": "The existing peroxyacid reagent, medium and product checks must already permit this net transformation; cooling cannot override a failed assessment."}]
    if issues:
        review.update(conditionIssues=issues, note="Cooled mCPBA Epoxidation conditions are unresolved. " +
                      " ".join(issue["explanation"] for issue in issues) + " Conditional 2D remains available where structurally supported; no isolated epoxide or experimental outcome is asserted.")
        return review
    review.update(status="supported-model", canGenerate3D=True,
                  note="Cooled Epoxidation is supported only by the bounded actual-mCPBA/dry-compatible-medium/no-added-activation net model. "
                       "The documented mild cooled reference is near 0 C with addition controlled at or below 10 C, not an arbitrary cryogenic range; no exact temperature is entered or simulated. "
                       "The medium evidence is dichloromethane-specific; Dry / no water is only its existing non-capturing modeling assumption, not validation of every dry solvent. "
                       "3D is a theoretical product conformer, not a temperature simulation or a guarantee of conversion, epoxide stability, isolation, rate, yield or site/face selectivity. "
                       "Cooling is reaction control, not evidence of a new stereochemical outcome: the existing validated same-face oxygen transfer and mapped substituent relationship remain, with no invented enantiomeric ratios. "
                       "The actual carboxylic acid coproduct is retained; buffering, later ring opening and experimental work-up are not modeled.")
    return review


def perbenzoic_substrate_issue(reaction):
    """A narrow condition-profile scope, not a new epoxidation product rule.

    The checked cold precedent is styrene. Saturated acyclic alkyl substitution
    on its single phenyl ring is a bounded net-model generalization, not an
    individually documented cold experiment or a selectivity claim.
    """
    identity = reaction.get("epoxidationSubstrateIdentity")
    if not isinstance(identity, str) or not identity or len(identity) > 1024:
        return "Exact substrate identity metadata is missing; the cooled perbenzoic-acid substrate scope cannot be verified."
    molecule = Chem.MolFromSmiles(identity)
    if molecule is None:
        return "The substrate identity cannot be validated for the cooled perbenzoic-acid profile."
    limitation = ("The cooled perbenzoic-acid profile currently covers one terminal CH2=CH–phenyl site "
                  "with a single all-carbon aromatic ring and optional saturated acyclic alkyl substituents. "
                  "Other alkenes, extra reactive sites, heteroatom groups and additional rings need separate "
                  "cold-profile validation; this does not mean they cannot undergo epoxidation.")
    if any(a.GetAtomicNum() not in {1, 6} or a.GetFormalCharge() or a.GetIsotope()
           or a.GetNumRadicalElectrons() or a.HasQuery() for a in molecule.GetAtoms()):
        return limitation
    rings = molecule.GetRingInfo().AtomRings()
    aromatic = {a.GetIdx() for a in molecule.GetAtoms() if a.GetIsAromatic()}
    if len(Chem.GetMolFrags(molecule)) != 1 or len(rings) != 1 or len(rings[0]) != 6 or set(rings[0]) != aromatic:
        return limitation
    alkenes = [b for b in molecule.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE]
    if len(alkenes) != 1 or any(b.GetBondType() not in {Chem.BondType.SINGLE, Chem.BondType.DOUBLE, Chem.BondType.AROMATIC}
                                 for b in molecule.GetBonds()):
        return limitation
    ends = (alkenes[0].GetBeginAtom(), alkenes[0].GetEndAtom())
    terminal = next((a for a in ends if a.GetTotalNumHs() == 2
                     and len([n for n in a.GetNeighbors() if n.GetAtomicNum() != 1]) == 1), None)
    if terminal is None:
        return limitation
    attached = ends[1] if ends[0].GetIdx() == terminal.GetIdx() else ends[0]
    others = [n for n in attached.GetNeighbors() if n.GetAtomicNum() != 1 and n.GetIdx() != terminal.GetIdx()]
    if attached.GetTotalNumHs() != 1 or len(others) != 1 or others[0].GetIdx() not in aromatic:
        return limitation
    return None


def _cooled_perbenzoic_support(reaction, conditions, assessment, review):
    """Actual perbenzoic acid plus a named chloroform-reference net assumption."""
    review.update(modelId=COOLED_PERBENZOIC_MODEL, status="conditions-unresolved",
                  sourceUrls=list(COOLED_PERBENZOIC_SOURCES), profileLabel="Cooled perbenzoic acid · chloroform-reference net model",
                  temperatureScope="Documented 0 C reaction-stage reference; no exact temperature is entered, measured or simulated. No continuous range or arbitrary cryogenic conditions are validated.",
                  substrateScope={"policyId": PERBENZOIC_SCOPE,
                                  "basis": "Checked styrene precedent; screened ring-alkyl hydrocarbon variants are a bounded modeling inference, not separately proven cold experiments."},
                  mediumAssumption={"referenceSolvent": "chloroform", "experimentalSolventEntered": False,
                                    "scope": "Dry / no water selects the named chloroform-reference theoretical net assumption; it does not validate every dry solvent."})
    issues = []
    if reaction.get("peroxyacidIdentity") != PERBENZOIC_IDENTITY:
        issues.append({"field": "reagentIdentity", "kind": "unvalidated-alternative",
                       "explanation": "This profile requires actual neutral perbenzoic acid; names, formulas, substituted peracids and other oxidants cannot select it."})
    substrate_issue = perbenzoic_substrate_issue(reaction)
    if substrate_issue:
        issues.append({"field": "substrateProfile", "kind": "unvalidated-alternative", "explanation": substrate_issue})
    if conditions.get("solvent") != "dry":
        issues.append({"field": "solvent", "kind": "unvalidated-alternative",
                       "explanation": "Select Dry / no water only to use the named chloroform-reference net assumption. Unspecified, aqueous, alcohol or generic aprotic media do not establish this epoxide model; later acid-promoted opening is not modeled."})
    if conditions.get("catalyst", "") not in {"", "none"}:
        issues.append({"field": "catalyst", "kind": "unvalidated-alternative",
                       "explanation": "Added acid, metal, Os, Lindlar or radical activation is not the reviewed perbenzoic-acid oxygen-transfer model. No buffering or new catalyst is inferred."})
    unknown = sorted(set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - CONDITION_FIELDS))
    issues.extend({"field": field, "kind": "unsupported",
                   "explanation": f"Unvalidated condition field {field} was supplied; this profile does not interpret it as supported experimental information."}
                  for field in unknown)
    for field in ("oxidationStage", "workup"):
        if conditions.get(field):
            issues.append({"field": field, "kind": "unvalidated-alternative",
                           "explanation": f"{field} is not included in this cooled epoxide net model. Post-reaction acid removal, epoxide opening and work-up chemistry are not inferred."})
    if (assessment.get("canRun") is not True or assessment.get("status") != "model-match"
            or not assessment.get("reagentValidated") or assessment.get("reagentRequirement") != "actual neutral single peroxyacid"
            or assessment.get("conditionIssues")) and not issues:
        issues = deepcopy(assessment.get("conditionIssues")) or [{"field": "conditions", "kind": "unvalidated-alternative",
            "explanation": "The existing peroxyacid reagent, substrate, medium and product assessment must already permit this transformation; cooling cannot override it."}]
    if issues:
        review.update(conditionIssues=issues, note="Cooled perbenzoic-acid epoxidation conditions are unresolved. " +
                      " ".join(i["explanation"] for i in issues) + " Conditional 2D remains available where structurally supported; no experimental epoxide outcome is asserted.")
        return review
    review.update(status="supported-model", canGenerate3D=True,
                  note="Cooled perbenzoic-acid epoxidation is supported only within the screened terminal styrene-type hydrocarbon scope and named chloroform-reference net assumption. "
                       "Dry / no water does not establish an actual experimental solvent or compatibility of all dry solvents. "
                       "The source's 0 C observation is a reference point, not an entered temperature, validated continuous range or arbitrary cryogenic permission. "
                       "3D is a theoretical product conformer, not a temperature simulation or a guarantee of conversion, epoxide lifetime, isolation, rate, yield or stereoisomer ratios. "
                       "Existing same-face oxygen transfer, mapped atom provenance and unaffected stereochemistry checks remain. Both represented faces are alternatives, not predicted populations. "
                       "The actual benzoic-acid coproduct remains in the net equation; post-reaction acid removal and experimental work-up are not modeled.")
    return review


def _cooled_bromination_support(reaction, conditions, assessment, review):
    review.update(modelId=COOLED_BROMINATION_MODEL, status="conditions-unresolved",
                  sourceUrls=list(COOLED_BROMINATION_SOURCES))
    reasons, issues = [], []
    def unresolved(field, explanation, kind="unvalidated-alternative"):
        reasons.append(explanation)
        issues.append({"field": field, "kind": kind, "explanation": explanation})
    if conditions.get("solvent") != "dry":
        unresolved("solvent", "Select the existing dry/non-capturing medium model; unspecified, aqueous, alcohol and generic polar-aprotic media do not establish dibromide-only conditions.")
    if conditions.get("catalyst", "") not in {"", "none"}:
        unresolved("catalyst", "Added acid, metal, radical or other activation is not this neutral Br2 addition model.")
    unknown = sorted(set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - CONDITION_FIELDS))
    if unknown:
        for field in unknown:
            unresolved(field, f"Unvalidated condition field {field} was supplied; it is not interpreted as compatible cooling conditions.", "unsupported")
    for field in ("oxidationStage", "workup"):
        if conditions.get(field):
            unresolved(field, f"{field} belongs to another pathway and is not included in cooled dibromination; review and clear this unrelated setting.")
    if (assessment.get("canRun") is not True or assessment.get("status") != "model-match"
            or not assessment.get("reagentValidated") or assessment.get("reagentRequirement") != "actual neutral Br2"
            or assessment.get("conditionIssues")):
        note = "The existing Br2 reagent/medium assessment must already permit the net transformation. Cooling does not override any structural, stereochemical or competing-chemistry restriction."
        reasons.append(note)
        if not issues:
            issues = deepcopy(assessment.get("conditionIssues")) or [{"field": "conditions", "kind": "unvalidated-alternative", "explanation": note}]
    if reasons:
        review["conditionIssues"] = issues
        review["note"] = ("Cooled Br2 3D conditions are unresolved. " + " ".join(reasons)
                          + " Conditional 2D remains available where the structure is supported; no product ratio or experimental outcome is inferred.")
        return review
    review.update(status="supported-model", canGenerate3D=True,
                  note=("Cooled conditions are compatible with the bounded alkene Br2 dibromination net model, "
                        "using its existing dry/non-capturing medium assumption and no additional activation. "
                        "3D is a theoretical product conformer, not a low-temperature simulation or a complete experimental protocol. "
                        "No exact temperature range, arbitrary cryogenic conditions, conversion, isolation, rate, yield, "
                        "site selectivity or stereoisomer ratio is established. Existing atom-mapping, anti-addition "
                        "and spectator-stereochemistry safeguards remain in force."))
    return review

def cyclohexene_scope_issue(reaction):
    """Exact parent graph, not a molecule name or broader ring-size rule."""
    if reaction.get("mechanism") != "Hydrogenation":
        return "This reference is only alkene hydrogenation, not carbonyl or alkyne reduction."
    identity = reaction.get("hydrogenationSubstrateIdentity")
    mol = Chem.MolFromSmiles(identity) if isinstance(identity, str) and len(identity) <= 1024 else None
    if (mol is None or Chem.MolToSmiles(mol) != "C1=CCCCC1"
            or reaction.get("hydrogenationReagentIdentity") != "[H][H]"
            or reaction.get("productSmiles") != "C1CCCCC1" or reaction.get("byproducts")):
        return "The cooled Pd/silica-A reference covers only unsubstituted cyclohexene + actual H2 giving cyclohexane; other rings, substituents, spectators or reducible groups are not approved."
    report = reaction.get("compatibility", {})
    if (not report.get("eligible") or not report.get("validation")
            or set(report["validation"].values()) != {"verified"}
            or report.get("substrateSiteMaps") != (reaction.get("site") or {}).get("atomMaps")):
        return "The existing mapped reaction-site, atom, charge, bond and stereo validation must already pass."
    return None


def _cooled_cyclohexene_support(reaction, conditions, assessment, review):
    review.update(modelId=COOLED_CYCLOHEXENE_MODEL, status="conditions-unresolved",
                  sourceUrls=[CYCLOHEXENE_SOURCE], profileLabel="Cyclohexene · Pd/silica A · hexane reference",
                  temperatureScope="Documented 0 C reaction point, not a continuous range or temperature simulation.")
    issues = []
    scope = cyclohexene_scope_issue(reaction)
    if scope:
        issues.append({"field": "substrateProfile", "kind": "unvalidated-alternative", "explanation": scope})
    for field, expected in (("temperature", "cooled"), ("solvent", "dry"), ("catalyst", "metal")):
        if conditions.get(field) != expected:
            issues.append({"field": field, "kind": "conflicting", "explanation": f"The named Pd/silica-A reference requires {field}={expected}; current selections are not replaced automatically."})
    if reference(conditions) != {"id": COOLED_CYCLOHEXENE_MODEL, "version": "1"}:
        issues.append({"field": "conditionProfileId", "kind": "unsupported", "explanation": "Explicit selection of this exact versioned catalyst/hexane/pressure reference is required; generic Pd/Pt is insufficient."})
    unknown = sorted(set(getattr(conditions, "unsupported_fields", ())) | (set(conditions) - CONDITION_FIELDS))
    for field in unknown:
        issues.append({"field": field, "kind": "unsupported", "explanation": f"Unmodeled field {field} conflicts with fixed source-reference assumptions. No arbitrary catalyst, solvent, pressure or temperature was accepted."})
    for field in ("workup", "oxidationStage"):
        if conditions.get(field):
            issues.append({"field": field, "kind": "conflicting", "explanation": f"{field} is not part of this single-H2 reference; no release or multi-equivalent pathway is inferred."})
    if assessment.get("conditionIssues") or assessment.get("status") in {"missing", "activation-required", "unsupported-pathway"}:
        issues.extend(deepcopy(assessment.get("conditionIssues")) or [{"field": "conditions", "kind": "unsupported", "explanation": "An underlying condition validation remains unresolved."}])
    if issues:
        review.update(conditionIssues=issues, note="Named cooled hydrogenation unresolved. " + " ".join(i["explanation"] for i in issues))
        return review
    review.update(status="supported-model", canGenerate3D=True,
                  note="The explicitly selected cyclohexene/Pd-silica-A/hexane reference supports only the existing cyclohexane net graph. "
                       "0 C and 1.1 MPa H2 are fixed documented reference observations, not entered measurements, a validated range or a pressure/temperature simulation; pressure basis is not stated. "
                       "The source's 15-minute analytical endpoint does not establish complete conversion or isolated yield. "
                       "This is a theoretical product conformer, not a protocol or prediction of rates, yields or selectivity. "
                       "No other Pd/Pt catalyst, Pd/C, substituted substrate, alkyne or carbonyl reduction is qualified; no full catalytic surface mechanism is implemented.")
    return review


def _cyclohexene_descriptor():
    return descriptor([
        fact("reagents", ["cyclohexene", "actual neutral H2"], "model-assumption", "actual structures checked independently"),
        fact("catalyst", {"metal": "Pd", "loadingWtPercent": 5, "support": "dual-pore silica catalyst A", "macroporeMicrometres": 1, "mesoporeNanometres": 6, "averageParticleMicrometres": 68,
             "preparation": {"identity": "Synthesis Example 1 only", "precursor": "palladium acetate on source-defined silica", "postImpregnationCalcinationC": 500, "postImpregnationCalcinationMinutes": 120}},
             "source-observation", "exact source formulation and pretreatment, not generic Pd/Pt or Pd/C; manufacturing is not simulated", "[0081]–[0082], [0087]"),
        fact("medium", "hexane", "source-observation", "named reference assumption, not entered experimental solvent", "[0087]"),
        fact("thermalHistory", {"stage": "reaction", "temperatureC": 0, "durationMinutes": 15, "rangeValidated": False,
             "catalystPretreatment": [{"stage": "H2 reduction", "temperature": "room temperature", "durationMinutes": 60}, {"stage": "drying", "temperatureC": 110, "durationMinutes": 720}]},
             "source-observation", "catalyst pretreatment is distinct from the 0 C substrate reaction; not conversion kinetics", "[0087]"),
        fact("hydrogenPressure", {"value": 1.1, "unit": "MPa", "basis": "not stated"}, "source-observation", "reference observation, no gauge/absolute conversion or numeric override", "[0087]"),
        fact("additives", "No additional additive chemistry included in the modeled reaction", "model-assumption", "no hidden consumed participants"),
        fact("productRelease", "Source filtration and GC identify cyclohexane; isolation and catalyst separation are not modeled", "source-observation", "net molecular endpoint, not isolated recovery", "[0087]")],
        [{"url": CYCLOHEXENE_SOURCE, "locator": "Original pp. 14–15; [0082], Example 1 [0087]; Table 1. Reference [0090] is DIFFERENT Pd/C, not this profile."}],
        ["Explicitly selecting this named profile accepts the fixed source-defined catalyst/hexane/H2 reference, not actual measured conditions.",
         "Only unsubstituted cyclohexene is within the present scope; no broader substrate inference.",
         "Theoretical complete-conversion arithmetic remains independent of the source's partial analytical endpoint."],
        ["Pressure gauge/absolute basis is not stated.", "Catalyst activity, transfer kinetics, complete conversion, isolated recovery and experimental selectivity are not predicted."])


@dataclass(frozen=True)
class CoolingProfile:
    model_id: str
    pathway: str
    model_name: str
    ui_name: str
    confidence_label: str
    source_urls: tuple[str, ...]
    assessor: Callable
    version: int = 1
    selector: Callable | None = None
    descriptor_json: str = "{}"
    explicit_only: bool = False


def _existing_descriptor(reagent, medium, thermal, sources):
    return descriptor([
        fact("reagents", [reagent], "model-assumption", "identity; actual molecular graph is independently validated"),
        fact("catalyst", "No additional activation", "model-assumption", "competing chemistry"),
        fact("medium", medium, "model-assumption", "capture/stability; not an experimentally entered solvent"),
        fact("thermalHistory", thermal, "source-observation", "reference only; not an interpolated range", sources[0]),
        fact("hydrogenPressure", None, "not-applicable", "No H2 consumed"),
        fact("additives", "No additional additive chemistry modeled", "model-assumption", "No hidden participant or buffering"),
        fact("productRelease", "Net product reporting only; isolation/work-up not represented", "model-assumption", "endpoint")],
        [{"url": url, "locator": "Existing reviewed cooling report; source scope is narrower than general graph scope"} for url in sources],
        ["Existing bounded net-model assumptions retained; no experimental solvent or temperature measurement is entered.",
         "A theoretical conformer does not predict conversion, isolation, rate, yield or selectivity."],
        ["Full experimental formulation, unmodeled side chemistry, isolated recovery and mixture composition."])


_PROFILES = (
    CoolingProfile(COOLED_BROMINATION_MODEL, "Bromination", "Br2", "alkene bromination",
                   "Cooled Br2 net model · outcome not predicted", COOLED_BROMINATION_SOURCES,
                   _cooled_bromination_support, descriptor_json=_existing_descriptor("actual neutral Br2", "Existing dry/non-capturing net assumption; not all dry solvents", "Documented cooled precedents; no numerical range admitted", COOLED_BROMINATION_SOURCES)),
    CoolingProfile(COOLED_EPOXIDATION_MODEL, "Epoxidation", "mCPBA epoxidation", "mCPBA peroxyacid epoxidation",
                   "Cooled mCPBA epoxidation net model · outcome not predicted", COOLED_EPOXIDATION_SOURCES,
                   _cooled_epoxidation_support, descriptor_json=_existing_descriptor("actual neutral mCPBA", "Dichloromethane-reference compatible dry assumption", "Near-zero reference; addition upper bound 10 C is not a validated continuous interval", COOLED_EPOXIDATION_SOURCES)),
    CoolingProfile(COOLED_PERBENZOIC_MODEL, "Epoxidation", "perbenzoic-acid epoxidation", "perbenzoic-acid epoxidation",
                   "Cooled perbenzoic-acid epoxidation net model · outcome not predicted", COOLED_PERBENZOIC_SOURCES,
                   _cooled_perbenzoic_support, selector=lambda reaction: reaction.get("peroxyacidIdentity") == PERBENZOIC_IDENTITY,
                   descriptor_json=_existing_descriptor("actual neutral perbenzoic acid", "Named chloroform-reference net assumption; experimental solvent not entered", "0 C reaction-stage observation, not a continuous range or cryogenic permission", COOLED_PERBENZOIC_SOURCES)),
    CoolingProfile(COOLED_CYCLOHEXENE_MODEL, "Hydrogenation", "cyclohexene Pd/silica-A hydrogenation", "cyclohexene Pd/silica-A hydrogenation",
                   "Named cooled cyclohexene reference · theoretical product only", (CYCLOHEXENE_SOURCE,),
                   _cooled_cyclohexene_support, descriptor_json=_cyclohexene_descriptor(), explicit_only=True),
    *(CoolingProfile(m.identifier, "Alkene dihydroxylation", m.title, m.title,
        "Named cooled free-product reference · theoretical conformer only", (r3.SOURCE,),
        r3.cooling_support, descriptor_json=r3.description(m), explicit_only=True) for m in r3.MODELS.values()),
)
PROFILES_BY_ID = MappingProxyType({profile.model_id: profile for profile in _PROFILES})
# The first registered model remains the fallback for unreviewed reagent IDs;
# exact-identity selectors can choose another model of the same reaction type.
PROFILES_BY_PATHWAY = MappingProxyType({profile.pathway: profile for profile in reversed(_PROFILES) if not profile.explicit_only})


def reviewed_profile(model_id, pathway, version=1, registry_version=1):
    """Exact versioned lookup; bool/string/future versions are not v1."""
    if (type(version) is not int or version != 1
            or type(registry_version) is not int or registry_version != REGISTRY_VERSION
            or not isinstance(model_id, str) or not isinstance(pathway, str)):
        return None
    profile = PROFILES_BY_ID.get(model_id)
    return profile if profile and profile.pathway == pathway and profile.version == version else None


def profile_for_review(review):
    if not isinstance(review, dict) or type(review.get("version")) is not int or review["version"] != 1:
        return None
    return reviewed_profile(review.get("modelId"), review.get("pathway"),
                            review.get("profileVersion", 1), review.get("registryVersion", 1))


def reviewed_manifest():
    """Detached presentation records; never a writable registration endpoint.

    The small frontend v1 mirror is checked against this manifest by regression
    tests. It cannot independently register new chemistry or grant permission.
    """
    return {"version": REGISTRY_VERSION, "profiles": [
        {"modelId": p.model_id, "pathway": p.pathway, "version": p.version, "uiName": p.ui_name}
        for p in _PROFILES]}


def named_profile_manifest():
    """Extended detached descriptors from the SAME immutable registry."""
    return {"version": 1, "profiles": [describe(p) for p in _PROFILES]}


def selected_profile(conditions):
    ref = reference(conditions)
    return PROFILES_BY_ID.get(ref["id"]) if ref and isinstance(ref.get("id"), str) else None


def attach_named_profile(assessment, conditions):
    review = assessment.get("cooling", {})
    profile = profile_for_review(review)
    if profile:
        assessment["namedConditionProfile"] = {
            "version": 1, "selection": "explicit" if reference(conditions) else "legacy-inferred",
            "status": "qualified" if review["canGenerate3D"] else "unresolved",
            "reference": {"id": profile.model_id, "version": str(profile.version)},
            "descriptor": describe(profile)}
    return assessment


def normalize_legacy_cooling_assessment(assessment, conditions, reaction=None):
    """Cooled-only adapter, not a modernization of legacy non-cooled rules.

    Reference differences are not missing chemical activation. These six
    pathways do not gain permission from this adapter. A separately selected,
    independently validated named profile may qualify one exact net reaction.
    """
    if conditions.get("temperature") != "cooled" or (reaction or {}).get("mechanism") not in LEGACY_COOLING_PATHWAYS:
        return assessment
    result = deepcopy(assessment)
    result.setdefault("status", "unevaluated")
    result.setdefault("label", "Conditions not reliably evaluated")
    result["canRun"] = False
    result.setdefault("missingSettings", [])
    result.setdefault("referenceDifferences", [])
    result.setdefault("factors", {})
    return result


def _reason_codes(review, reaction):
    if review["status"] == "supported-model":
        return []
    if review["status"] == "unvalidated-pathway":
        return ["unsupported-endpoint" if (reaction or {}).get("primaryOxidationModel") else
                "unreviewed-formulation" if (reaction or {}).get("secondaryOxidationModel") else
                "unreviewed-cooled-pathway"]
    fields = {"reagentIdentity": "reagent-profile-mismatch", "substrateProfile": "substrate-profile-unresolved", "solvent": "medium-unresolved",
              "catalyst": "activation-unresolved", "oxidationStage": "unrelated-stage",
              "workup": "unrelated-stage", "conditions": "underlying-assessment-blocked"}
    return list(dict.fromkeys("unsupported-condition-field" if issue["kind"] == "unsupported"
                              else fields.get(issue["field"], "conditions-unresolved")
                              for issue in review.get("conditionIssues", [])))


def assess_cooling_support(reaction, conditions, assessment):
    """Run only an existing registered validator; preserve the original gates."""
    if conditions.get("temperature") != "cooled":
        return None
    path = (reaction or {}).get("mechanism", "Unspecified pathway")
    review = {"version": 1, "pathway": path, "modelId": None,
              "status": "unvalidated-pathway", "canGenerate3D": False,
              "note": COOLING_NOTE, "sourceUrls": []}
    profile = selected_profile(conditions) if reference(conditions) else next((p for p in _PROFILES if not p.explicit_only and p.pathway == path and p.selector and p.selector(reaction)),
                   PROFILES_BY_PATHWAY.get(path))
    if profile is None:
        limitation = COOLING_LIMITATIONS.get(path, "This pathway has no reviewed cooled product-generation model in the present engine.")
        if (reaction or {}).get("primaryOxidationModel"):
            limitation = "The primary-alcohol hypochlorite aldehyde endpoint has no validated selective-stopping profile at any selected temperature; cooling cannot establish stopping before further oxidation."
        elif (reaction or {}).get("secondaryOxidationModel"):
            limitation = "The qualified secondary-alcohol NaOCl/acetic-acid ketone profile explicitly requires ambient conditions; cooled reagent/formulation compatibility needs separate validation."
        review["note"] += f" {path}: {limitation}"
    else:
        review = profile.assessor(reaction, conditions, assessment, review)
    # Additive metadata: old v1 keys, labels and explanations are unchanged.
    review.update(registryVersion=REGISTRY_VERSION, profileVersion=profile.version if profile else None,
                  reasonCodes=_reason_codes(review, reaction))
    return review


def current_cooling_overlay(assessment, reaction=None, conditions=None):
    """Recognize a consistent existing overlay, not an arbitrary policy marker."""
    review = assessment.get("cooling")
    if (not isinstance(review, dict) or type(review.get("version")) is not int or review["version"] != 1
            or type(review.get("registryVersion", 1)) is not int or review.get("registryVersion", 1) != REGISTRY_VERSION
            or reaction is not None and review.get("pathway") != reaction.get("mechanism", "Unspecified pathway")):
        return False
    policy = assessment.get("coolingPolicy")
    if not isinstance(policy, str):
        return False
    if policy in {"unvalidated-low-temperature-v1", "invalid-cooling-contract-v1"}:
        return (review.get("modelId") is None and review.get("status") == "unvalidated-pathway"
                and review.get("canGenerate3D") is False and assessment.get("canRun") is False
                and assessment.get("coolingUnvalidated") is True
                and (review.get("profileVersion") is None))
    profile = profile_for_review(review)
    if profile is None or policy != profile.model_id:
        return False
    if review.get("status") == "conditions-unresolved":
        return (review.get("canGenerate3D") is False and assessment.get("canRun") is False
                and assessment.get("coolingUnvalidated") is True)
    consistent = (review.get("status") == "supported-model" and review.get("canGenerate3D") is True
            and assessment.get("canRun") is True and assessment.get("status") == "model-match"
            and assessment.get("coolingUnvalidated") is False and not assessment.get("conditionIssues")
            and not assessment.get("missingSettings") and not review.get("conditionIssues")
            and not review.get("reasonCodes"))
    evidence = assessment.get("evidence")
    if isinstance(evidence, dict) and (evidence.get("canGenerate3D") is not True
            or evidence.get("conditionIssues") or evidence.get("missingRequiredSettings")
            or evidence.get("aldehydeEndpointValidated") is False):
        return False
    # Idempotence applies to this request's inputs, not to stale permissions
    # reused after a condition/reagent change. Public endpoints also re-resolve
    # the graph and site independently before reaching this layer.
    if consistent and reaction is not None and conditions is not None:
        return assess_cooling_support(reaction, conditions, assessment)["canGenerate3D"] is True
    return consistent


def reject_cooling_contract(assessment, reaction=None):
    """Fail closed on forged/unknown cached metadata without creating a model."""
    result = deepcopy(assessment)
    note = ("Cooling profile metadata is unknown or inconsistent. No reviewed cooled 3D permission "
            "can be inferred; reassess the current reactants and conditions. Conditional 2D remains "
            "available only where the existing structure model permits it.")
    result.update(canRun=False, state="incomplete", coolingPolicy="invalid-cooling-contract-v1",
                  coolingUnvalidated=True, confidenceLabel="Cooling contract unresolved · conditional 2D only")
    if result.get("status") not in {"missing", "activation-required", "unsupported-pathway"}:
        result.update(status="unsupported-pathway", label="Cooling profile metadata unsupported")
    result["cooling"] = {"version": 1, "registryVersion": REGISTRY_VERSION, "profileVersion": None,
                         "pathway": (reaction or {}).get("mechanism", "Unspecified pathway"),
                         "modelId": None, "status": "unvalidated-pathway", "canGenerate3D": False,
                         "sourceUrls": [], "reasonCodes": ["invalid-profile-contract"], "note": note}
    result.setdefault("factors", {})["temperature"] = {"status": "unevaluated", "effect": "unknown", "explanation": note}
    result["note"] = note + " " + result.get("note", "")
    if "conditionCompleteEligibility" in result:
        result["conditionCompleteEligibility"] = False
    if isinstance(result.get("evidence"), dict):
        result["evidence"].update(canGenerate3D=False, label=result["confidenceLabel"],
                                  renderingPolicy="invalid-cooling-contract-gate", renderingNote=note)
    return result
