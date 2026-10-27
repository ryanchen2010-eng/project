"""Registry/contract consolidation only; no new cooled chemistry or benchmark rows."""
import copy
from dataclasses import FrozenInstanceError
import itertools
import unittest

from server import chemistry_server as service
from server import reaction_conditions as conditions
from server import reaction_temperature_profiles as registry
from server.reaction_information import DEFINITIONS


COOLED = {"temperature": "cooled", "solvent": "dry", "catalyst": "none"}
EXPECTED = {
    "cooled-alkene-bromination-v1": ("Bromination", "alkene bromination"),
    "cooled-peroxyacid-epoxidation-v1": ("Epoxidation", "mCPBA peroxyacid epoxidation"),
    "cooled-perbenzoic-epoxidation-v1": ("Epoxidation", "perbenzoic-acid epoxidation"),
    "cooled-cyclohexene-pd-silica-v1": ("Hydrogenation", "cyclohexene Pd/silica-A hydrogenation"),
    "cooled-isobutylene-os-peroxide-v1": ("Alkene dihydroxylation", "Isobutylene · OsO4/H2O2 · tert-butanol reference"),
    "cooled-crotonic-os-peroxide-v1": ("Alkene dihydroxylation", "Crotonic acid · OsO4/H2O2 · tert-butanol reference"),
    "cooled-cinnamic-os-peroxide-v1": ("Alkene dihydroxylation", "Cinnamic acid · OsO4/H2O2 · tert-butanol reference"),
}


def base(pathway="Bromination", settings=None):
    return (conditions.assess_epoxidation_conditions(settings or COOLED) if pathway == "Epoxidation"
            else conditions.assess_bromination_conditions(settings or COOLED))


def reaction(pathway="Bromination"):
    return {"mechanism": pathway, **({"peroxyacidIdentity": "O=C(OO)c1cccc(Cl)c1"}
                                    if pathway == "Epoxidation" else {})}


def overlaid(pathway="Bromination"):
    return conditions.cooling_confidence(base(pathway), COOLED, reaction(pathway))


class CoolingRegistryTests(unittest.TestCase):
    def test_two_types_with_the_three_individually_reviewed_ids_are_registered(self):
        self.assertEqual(registry.REGISTRY_VERSION, 1)
        self.assertEqual(set(registry.PROFILES_BY_ID), set(EXPECTED))
        self.assertEqual(set(registry.PROFILES_BY_PATHWAY), {"Bromination", "Epoxidation"})
        for model_id, (pathway, ui_name) in EXPECTED.items():
            profile = registry.reviewed_profile(model_id, pathway)
            if profile.explicit_only:
                self.assertNotIn(pathway, registry.PROFILES_BY_PATHWAY)
            elif model_id == registry.COOLED_PERBENZOIC_MODEL:
                self.assertIsNot(profile, registry.PROFILES_BY_PATHWAY[pathway])
                self.assertTrue(profile.selector({"peroxyacidIdentity": registry.PERBENZOIC_IDENTITY}))
            else:
                self.assertIs(profile, registry.PROFILES_BY_PATHWAY[pathway])
            self.assertEqual(profile.version, 1)
            self.assertEqual(profile.ui_name, ui_name)
            self.assertTrue(profile.source_urls)

    def test_registry_entries_and_mappings_are_immutable(self):
        with self.assertRaises(TypeError):
            registry.PROFILES_BY_ID["new"] = registry.PROFILES_BY_PATHWAY["Bromination"]
        with self.assertRaises(TypeError):
            registry.PROFILES_BY_PATHWAY["Chlorination"] = registry.PROFILES_BY_PATHWAY["Bromination"]
        with self.assertRaises(FrozenInstanceError):
            registry.PROFILES_BY_PATHWAY["Bromination"].version = 2

    def test_manifest_is_detached_and_contains_presentation_not_permission(self):
        expected = {"version": 1, "profiles": [
            {"modelId": key, "pathway": values[0], "version": 1, "uiName": values[1]}
            for key, values in EXPECTED.items()]}
        self.assertEqual(registry.reviewed_manifest(), expected)
        detached = registry.reviewed_manifest()
        detached["profiles"][0]["pathway"] = "Chlorination"
        detached["profiles"].clear()
        self.assertEqual(registry.reviewed_manifest(), expected)

    def test_unknown_mismatched_and_non_integer_versions_fail_closed(self):
        for version in (None, True, False, "1", 1.0, 0, 2, [], {}):
            with self.subTest(version=version):
                self.assertIsNone(registry.reviewed_profile("cooled-alkene-bromination-v1", "Bromination", version))
                self.assertIsNone(registry.reviewed_profile("cooled-alkene-bromination-v1", "Bromination", registry_version=version))
        for identifier, pathway in (("unknown-v1", "Bromination"), ("cooled-alkene-bromination-v1", "Chlorination"),
                                    (None, "Bromination"), ([], "Bromination"), ("cooled-alkene-bromination-v1", [])):
            self.assertIsNone(registry.reviewed_profile(identifier, pathway))

    def test_original_import_names_and_condition_fields_remain_compatible(self):
        for name in ("COOLING_NOTE", "COOLING_LIMITATIONS", "COOLED_BROMINATION_MODEL", "COOLED_BROMINATION_SOURCES",
                     "COOLED_EPOXIDATION_MODEL", "COOLED_EPOXIDATION_SOURCES", "MCPBA_IDENTITY", "CONDITION_FIELDS"):
            self.assertEqual(getattr(conditions, name), getattr(registry, name))
        self.assertEqual(registry.CONDITION_FIELDS, set(service.CONDITION_VALUES) | {"conditionProfileId", "conditionProfileVersion"})

    def test_non_cooled_lookup_and_overlay_are_identity_preserving(self):
        for temperature in ("", "ambient", "heated"):
            settings = {**COOLED, "temperature": temperature}
            value = {"note": "Legacy result", "state": "aligned"}
            self.assertIsNone(registry.assess_cooling_support(reaction(), settings, value))
            self.assertIs(conditions.cooling_confidence(value, settings, reaction()), value)
            self.assertIs(registry.normalize_legacy_cooling_assessment(value, settings, {"mechanism": "Hydrogenation"}), value)

    def test_new_metadata_is_additive_and_positive_codes_are_empty(self):
        for pathway in ("Bromination", "Epoxidation"):
            original = base(pathway)
            before = copy.deepcopy(original)
            result = registry.assess_cooling_support(reaction(pathway), COOLED, original)
            self.assertEqual(original, before)
            self.assertEqual(result["version"], 1)
            self.assertEqual(result["registryVersion"], 1)
            self.assertEqual(result["profileVersion"], 1)
            self.assertEqual(result["reasonCodes"], [])
            self.assertEqual(result["status"], "supported-model")
            self.assertTrue(result["canGenerate3D"])

    def test_all_other_rule_types_remain_unreviewed_even_with_optimistic_base_flags(self):
        for pathway in set(DEFINITIONS) - {"Bromination", "Epoxidation"}:
            with self.subTest(pathway=pathway):
                result = registry.assess_cooling_support({"mechanism": pathway}, COOLED, base())
                self.assertFalse(result["canGenerate3D"])
                self.assertEqual(result["status"], "unvalidated-pathway")
                self.assertIsNone(result["modelId"])
                self.assertIsNone(result["profileVersion"])
                self.assertEqual(result["reasonCodes"], ["unreviewed-cooled-pathway"])

    def test_condition_grid_keeps_only_the_existing_dry_neutral_profiles(self):
        for pathway, medium, catalyst in itertools.product(
                ("Bromination", "Epoxidation"), ("", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"),
                ("", "none", "acid", "metal", "osmium", "lindlar", "radical")):
            settings = {**COOLED, "solvent": medium, "catalyst": catalyst}
            with self.subTest(pathway=pathway, medium=medium, catalyst=catalyst):
                result = registry.assess_cooling_support(reaction(pathway), settings, base(pathway, settings))
                self.assertEqual(result["canGenerate3D"], medium == "dry" and catalyst in {"", "none"})

    def test_exact_mcpba_identity_not_other_peracids_names_or_formula(self):
        for identity in (None, "", "CC(=O)OO", "O=C(OO)c1ccccc1", "O=C(OO)c1ccc(Cl)cc1", "mCPBA", "C7H5ClO3"):
            value = {**reaction("Epoxidation"), "peroxyacidIdentity": identity}
            result = registry.assess_cooling_support(value, COOLED, base("Epoxidation"))
            self.assertFalse(result["canGenerate3D"])
            # Actual perbenzoic acid now selects its own profile, but this raw
            # fixture has no validated substrate metadata and cannot borrow 3D.
            self.assertIn("substrate-profile-unresolved" if identity == registry.PERBENZOIC_IDENTITY else "reagent-profile-mismatch", result["reasonCodes"])

    def test_stage_unknown_fields_and_underlying_blockers_have_specific_codes(self):
        for pathway in ("Bromination", "Epoxidation"):
            for extra, code in (({"solvent": "aqueous-protic"}, "medium-unresolved"),
                                ({"catalyst": "acid"}, "activation-unresolved"),
                                ({"workup": "aqueous-release"}, "unrelated-stage"),
                                ({"oxidationStage": "first"}, "unrelated-stage"),
                                ({"futureProfile": "v99"}, "unsupported-condition-field")):
                settings = {**COOLED, **extra}
                result = registry.assess_cooling_support(reaction(pathway), settings, base(pathway, settings))
                self.assertFalse(result["canGenerate3D"])
                self.assertIn(code, result["reasonCodes"])
            for field, value in (("canRun", False), ("status", "unevaluated"), ("reagentValidated", False),
                                 ("reagentRequirement", "different reagent")):
                blocked = {**base(pathway), field: value}
                result = registry.assess_cooling_support(reaction(pathway), COOLED, blocked)
                self.assertFalse(result["canGenerate3D"])
                self.assertIn("underlying-assessment-blocked", result["reasonCodes"])

    def test_known_persistent_ui_selectors_remain_not_applicable(self):
        for pathway in ("Bromination", "Epoxidation"):
            value = conditions.cooling_confidence(base(pathway), {**COOLED, "additionStage": "two", "polymerUnits": "6"}, reaction(pathway))
            self.assertTrue(value["canRun"])
            self.assertEqual(value["notApplicableSettings"], ["additionStage", "polymerUnits"])

    def test_legacy_adapter_cannot_turn_reference_differences_into_activation_requirements(self):
        self.assertEqual(registry.LEGACY_COOLING_PATHWAYS, {
            "Hydrogenation", "Carbonyl hydrogenation", "Esterification", "Ester hydrolysis",
            "Ester saponification", "Polymerization model"})
        for pathway, state in itertools.product(registry.LEGACY_COOLING_PATHWAYS, ("aligned", "alternative", "incomplete")):
            value = {"state": state, "note": "Original reference comparison."}
            before = copy.deepcopy(value)
            result = registry.normalize_legacy_cooling_assessment(value, COOLED, {"mechanism": pathway})
            self.assertEqual(value, before)
            self.assertEqual(result["state"], state)
            self.assertEqual(result["note"], value["note"])
            self.assertFalse(result["canRun"])
            self.assertEqual(result["status"], "unevaluated")
            self.assertEqual(result["missingSettings"], [])
            final = conditions.cooling_confidence(value, COOLED, {"mechanism": pathway})
            self.assertFalse(final["canRun"])
            self.assertNotEqual(final["status"], "activation-required")

    def test_primary_secondary_endpoint_reasons_remain_distinct(self):
        for marker, reason in (("primaryOxidationModel", "unsupported-endpoint"),
                               ("secondaryOxidationModel", "unreviewed-formulation")):
            review = registry.assess_cooling_support({"mechanism": "Alcohol oxidation", marker: True}, COOLED, base())
            self.assertEqual(review["reasonCodes"], [reason])
            self.assertFalse(review["canGenerate3D"])

    def test_existing_alkyne_temperature_guard_still_blocks_cooling(self):
        assessment = {"canRun": True, "status": "model-match", "note": "Existing model", "factors": {
            key: {"status": "model-match", "explanation": "Original guard"} for key in ("temperature", "solvent", "catalyst")}}
        result = conditions.alkyne_input_evidence(assessment, COOLED, "Alkyne halogenation")
        self.assertFalse(result["canRun"])
        self.assertIn("temperature", [issue["field"] for issue in result["conditionIssues"]])


class CoolingOverlayContractTests(unittest.TestCase):
    def test_consistent_positive_and_negative_overlays_are_idempotent_nonmutating(self):
        for pathway, settings in itertools.product(("Bromination", "Epoxidation", "Hydrogenation"),
                                                   (COOLED, {**COOLED, "solvent": "aqueous-protic"})):
            original = base("Epoxidation" if pathway == "Epoxidation" else "Bromination", settings)
            before = copy.deepcopy(original)
            first = conditions.cooling_confidence(original, settings, reaction(pathway))
            self.assertEqual(original, before)
            self.assertIs(conditions.cooling_confidence(first, settings, reaction(pathway)), first)

    def test_original_v1_metadata_remains_recognized(self):
        value = overlaid()
        for key in ("registryVersion", "profileVersion", "reasonCodes"):
            value["cooling"].pop(key)
        self.assertIs(conditions.cooling_confidence(value, COOLED, reaction()), value)

    def test_unknown_contract_markers_and_versions_cannot_bypass_overlay(self):
        for key, values in (("version", (None, True, "1", 2)), ("registryVersion", (None, True, "1", 2)),
                            ("profileVersion", (None, True, "1", 2)), ("modelId", (None, "unknown-v2")),
                            ("pathway", ("Chlorination", "Epoxidation"))):
            for replacement in values:
                with self.subTest(key=key, replacement=replacement):
                    value = overlaid()
                    value["cooling"][key] = replacement
                    before = copy.deepcopy(value)
                    result = conditions.cooling_confidence(value, COOLED, reaction())
                    self.assertEqual(value, before)
                    self.assertFalse(result["canRun"])
                    self.assertFalse(result["cooling"]["canGenerate3D"])
                    self.assertEqual(result["cooling"]["reasonCodes"], ["invalid-profile-contract"])
        for marker in ("unreviewed-v99", [], {}, True, False, None, ""):
            value = {**base(), "coolingPolicy": marker, "cooling": {"version": 99}}
            self.assertFalse(conditions.cooling_confidence(value, COOLED, reaction())["canRun"])

    def test_contradictory_supported_overlay_and_stale_evidence_are_rejected(self):
        mutations = [lambda a: a.update(canRun=False), lambda a: a.update(status="unsupported-pathway"),
                     lambda a: a["cooling"].update(canGenerate3D=False),
                     lambda a: a["cooling"].update(reasonCodes=["unresolved"]),
                     lambda a: a.update(missingSettings=["solvent"]),
                     lambda a: a.update(conditionIssues=[{"field": "solvent"}]),
                     lambda a: a["evidence"].update(canGenerate3D=False),
                     lambda a: a["evidence"].update(missingRequiredSettings=["solvent"]),
                     lambda a: a["evidence"].update(conditionIssues=[{"field": "solvent"}])]
        for mutate in mutations:
            value = overlaid()
            value["evidence"] = {"canGenerate3D": True}
            mutate(value)
            result = conditions.cooling_confidence(value, COOLED, reaction())
            self.assertFalse(result["canRun"])
            self.assertFalse(result["evidence"]["canGenerate3D"])

    def test_stale_positive_overlay_is_not_reused_under_changed_conditions_or_peracid(self):
        for pathway in ("Bromination", "Epoxidation"):
            value = overlaid(pathway)
            for extra in ({"solvent": "aqueous-protic"}, {"catalyst": "radical"}, {"workup": "aqueous-release"}):
                result = conditions.cooling_confidence(value, {**COOLED, **extra}, reaction(pathway))
                self.assertFalse(result["canRun"])
        stale = overlaid("Epoxidation")
        self.assertFalse(conditions.cooling_confidence(stale, COOLED, {
            **reaction("Epoxidation"), "peroxyacidIdentity": "CC(=O)OO"})["canRun"])

    def test_stronger_missing_and_activation_messages_are_not_replaced(self):
        for status in ("missing", "activation-required", "unsupported-pathway"):
            value = {"state": "incomplete", "status": status, "label": "Original stronger reason",
                     "canRun": False, "note": "Original requirement.", "missingSettings": ["catalyst"]}
            result = conditions.cooling_confidence(value, COOLED, {"mechanism": "Hydrogenation"})
            self.assertEqual(result["status"], status)
            self.assertEqual(result["label"], value["label"])
            self.assertIn(value["note"], result["note"])
            self.assertEqual(result["missingSettings"], ["catalyst"])

    def test_public_unrecognized_profile_inputs_are_blocked_not_registered(self):
        for pathway, reagent in (("Bromination", "bromine"), ("Epoxidation", {"smiles": registry.MCPBA_IDENTITY})):
            for unknown in ("coolingProfile", "registryVersion", "profileVersion", "temperatureCelsius"):
                settings = {**COOLED, unknown: "unreviewed"}
                source = {"smiles": "C=C"}
                result = service.match_reactions(source, reagent, settings)
                options = [r for r in result["reactionOptions"] if r["mechanism"] == pathway]
                self.assertTrue(options)
                assessment = options[0]["assessment"]
                self.assertFalse(assessment["canRun"])
                self.assertIn("unsupported-condition-field", assessment["cooling"]["reasonCodes"])
                self.assertFalse(assessment["evidence"]["canGenerate3D"])
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(options[0]["id"], source, reagent, settings)


if __name__ == "__main__":
    unittest.main()
