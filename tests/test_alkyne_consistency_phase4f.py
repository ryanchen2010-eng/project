"""Confidence-only fixes. Independent invariants; no frozen expectations edited."""
from copy import deepcopy
import hashlib
import json
import secrets
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from server import chemistry_server as service
from server.production_app import create_app
from scripts import reaction_conditions_companion as companion

MODELS = {
    "partial": ("Alkyne partial hydrogenation", "hydrogen", {"catalyst": "lindlar"}),
    "complete": ("Alkyne hydrogenation", "hydrogen", {"catalyst": "metal"}),
    "x2": ("Alkyne halogenation", "bromine", {"solvent": "dry", "additionStage": "one"}),
    "hx": ("Alkyne hydrohalogenation", "hydrogen-bromide", {"solvent": "dry", "temperature": "ambient", "additionStage": "one"}),
}


class AlkyneConfidencePublicTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="phase4f-api-"); self.addCleanup(folder.cleanup)
        self.origin = "https://phase4f.example.test"
        self.client = create_app({"TRIAL_PASSWORD": "Synthetic-phase4f-password", "SESSION_SECRET": secrets.token_hex(32),
                                  "PUBLIC_ORIGIN": self.origin, "FRAME_ANCESTORS": self.origin,
                                  "DIST_DIR": Path(folder.name), "TESTING": True}, chemistry_backend=service).test_client()
        self.assertEqual(self.post("/login", data={"password": "Synthetic-phase4f-password"}).status_code, 303)

    def post(self, route, **kwargs):
        return self.client.post(route, base_url=self.origin, headers={"Origin": self.origin}, **kwargs)

    def workflow(self, model, conditions, *, source="CCC#C", allowed=False):
        path, reagent, _ = MODELS[model]
        body = {"reactantA": {"smiles": source}, "reactantB": reagent, "conditions": conditions}
        match = self.post("/api/reactions/match", json=body)
        self.assertEqual(match.status_code, 200)
        option = next(o for o in match.json["reactionOptions"] if o["mechanism"] == path)
        assessment = option["assessment"]; evidence = assessment["evidence"]
        self.assertEqual(assessment["canRun"], allowed)
        self.assertEqual(evidence["canGenerate3D"], allowed)
        self.assertEqual(option["stoichiometry"]["context"]["canGenerate3D"], allowed)
        self.assertEqual(evidence["structuralEligibility"], "eligible")
        self.assertTrue(evidence["canPreview2D"])
        self.assertEqual(evidence["chemistryCorrectness"]["status"], "not-independently-certified-at-runtime")
        body["reactionId"] = option["id"]
        diagram = self.post("/api/reactions/diagram", json=body)
        self.assertEqual(diagram.status_code, 200)
        self.assertEqual(diagram.json["assessment"], assessment)
        self.assertIsNone(diagram.json["mechanism"])
        atoms = diagram.json["atoms"]
        before = {a["mapId"]: (a["element"], a["formalCharge"]) for a in atoms if a["side"] == "reactants"}
        after = {a["mapId"]: (a["element"], a["formalCharge"]) for a in atoms if a["side"] == "products"}
        self.assertEqual(before, after)
        self.assertEqual(len(atoms), 2 * len(before))
        result = self.post("/api/reactions/run", json=body)
        self.assertEqual(result.status_code, 200 if allowed else 422)
        if allowed:
            self.assertEqual(result.json["product"]["smiles"], option["productSmiles"])
        else:
            self.assertNotIn("product", result.json)
        return option, diagram.json

    def test_valid_existing_alternative_is_not_blanket_rejected(self):
        self.workflow("complete", {"catalyst": "metal", "solvent": "ethanolic-protic", "temperature": "ambient"}, allowed=True)

    def test_unvalidated_alternative_remains_conditional_not_chemically_impossible(self):
        r, _ = self.workflow("partial", {"catalyst": "lindlar", "solvent": "ethanolic-protic"})
        self.assertEqual(r["assessment"]["evidence"]["conditionCompleteness"], "not-evaluated")
        self.assertEqual(r["assessment"]["conditionIssues"][0]["kind"], "unvalidated-alternative")

    def test_known_wrong_value_identifies_field(self):
        body = {"reactantA": {"smiles": "CCC#C"}, "reactantB": "hydrogen", "conditions": {"catalyst": "sodium-ammonia"}}
        response = self.post("/api/reactions/match", json=body)
        self.assertEqual(response.status_code, 422)
        self.assertIn("catalyst", response.json["error"])

    def test_condition_schema_names_stay_synchronized(self):
        from server.reaction_conditions import CONDITION_FIELDS
        self.assertEqual(set(service.CONDITION_VALUES), CONDITION_FIELDS)

    def test_conflicting_activation_is_not_mistaken_for_missing_input(self):
        r, _ = self.workflow("partial", {"catalyst": "metal"})
        self.assertEqual(r["assessment"]["evidence"]["conditionCompleteness"], "conflicting-input")
        self.assertEqual(r["assessment"]["conditionIssues"][0]["field"], "catalyst")

    def test_explicit_other_pathway_settings_are_not_silently_applied(self):
        r, _ = self.workflow("x2", {**MODELS["x2"][2], "oxidationStage": "further"})
        self.assertIn("oxidationStage", r["assessment"]["note"])

    def test_persistent_ui_bookkeeping_selectors_are_acknowledged_not_activation(self):
        r, _ = self.workflow("partial", {"catalyst": "lindlar", "additionStage": "one", "polymerUnits": "4"}, allowed=True)
        self.assertEqual(r["assessment"]["evidence"]["notApplicableSettings"], ["polymerUnits", "additionStage"])

    def test_lindlar_equivalent_aliases_are_mapped_conditional_not_asserted(self):
        r, _ = self.workflow("partial", {"catalyst": "lindlar"}, source="C#CCCCCC#C")
        self.assertEqual(r["optionIdentity"]["siteCount"], 2)
        self.assertEqual(len(r["optionIdentity"]["sourceReactionIds"]), 2)
        self.assertIn("Competing alkyne sites", r["stoichiometry"]["context"]["warning"])
        source = {"smiles": "C#CCCCCC#C"}
        for identifier in r["optionIdentity"]["sourceReactionIds"]:
            d = service.reaction_diagram(identifier, source, "hydrogen", {"catalyst": "lindlar"})
            self.assertEqual(d["bondOrderChanges"][0]["atomMaps"], d["site"]["atomMaps"][:2])
            self.assertEqual([(c["before"], c["after"]) for c in d["bondOrderChanges"]], [(3, 2)])
            from rdkit import Chem
            self.assertEqual(sum(b.GetBondTypeAsDouble() == 3 for b in Chem.MolFromSmiles(d["products"][0]["smiles"]).GetBonds()), 1)
            with self.assertRaises(service.ChemistryError): service.run_curated_reaction(identifier, source, "hydrogen", {"catalyst": "lindlar"})

    def test_distinct_lindlar_products_and_distant_stereo_remain(self):
        response = service.match_reactions({"smiles": "C#CCCCCCC#CC"}, "hydrogen", {"catalyst": "lindlar"})
        opts = [r for r in response["reactionOptions"] if r["mechanism"] == MODELS["partial"][0]]
        self.assertEqual(len({r["productSmiles"] for r in opts}), 2)
        self.assertTrue(all(not r["assessment"]["canRun"] for r in opts))
        self.workflow("partial", {"catalyst": "lindlar"}, source="C#CC[C@H](C)CC", allowed=True)

    def test_stale_permission_cannot_survive_new_unknown_field(self):
        self.workflow("hx", MODELS["hx"][2], allowed=True)
        r, _ = self.workflow("hx", {**MODELS["hx"][2], "peroxide": True})
        self.assertIn("peroxide", r["stoichiometry"]["context"]["warning"])


for model, (_, _, settings) in MODELS.items():
    for field, value in [("peroxide", True), ("light", "UV"), ("pressure", 2), ("solventName", "hexane")]:
        def unsupported(self, model=model, settings=settings, field=field, value=value):
            r, _ = self.workflow(model, {**settings, field: value})
            e = r["assessment"]["evidence"]
            self.assertEqual(e["conditionCompleteness"], "unsupported-input")
            self.assertIn(field, [i["field"] for i in e["conditionIssues"]])
            self.assertIn(field, r["assessment"]["note"])
        setattr(AlkyneConfidencePublicTests, f"test_unsupported_{model}_{field}", unsupported)
    def missing(self, model=model):
        r, _ = self.workflow(model, {})
        self.assertTrue(r["assessment"]["evidence"]["missingRequiredSettings"])
        self.assertEqual(r["assessment"]["evidence"]["conditionCompleteness"], "incomplete")
    setattr(AlkyneConfidencePublicTests, f"test_missing_{model}", missing)
    def valid(self, model=model, settings=settings): self.workflow(model, settings, allowed=True)
    setattr(AlkyneConfidencePublicTests, f"test_valid_{model}", valid)
    def radical(self, model=model, settings=settings):
        r, _ = self.workflow(model, {**settings, "catalyst": "radical"})
        self.assertEqual(r["assessment"]["conditionIssues"][0]["kind"], "unsupported")
    setattr(AlkyneConfidencePublicTests, f"test_radical_{model}", radical)
    def workup(self, model=model, settings=settings):
        r, _ = self.workflow(model, {**settings, "workup": "aqueous-release"})
        self.assertEqual(r["assessment"]["evidence"]["conditionCompleteness"], "conflicting-input")
    setattr(AlkyneConfidencePublicTests, f"test_conflicting_workup_{model}", workup)


class CompanionFrameworkTests(unittest.TestCase):
    def setUp(self): self.manifest = companion.load()

    def test_parent_all_347_identities_and_fixed_hash(self):
        self.assertEqual(len(self.manifest["parentCaseDigests"]), 347)
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(), companion.PARENT_SHA)
        self.assertEqual(len(companion.validate(self.manifest)), 347)
        self.assertEqual(len(companion.engine_fingerprint()), 64)

    def test_scope_denominators_and_controls(self):
        p = companion.parents()
        self.assertEqual(len(self.manifest["cases"]), 58)
        self.assertEqual(sum(p[b["id"]]["expected"] is not None for b in self.manifest["cases"]), 53)
        self.assertEqual(347 - len(self.manifest["cases"]), 289)

    def test_no_approved_profile_manufactured_from_diagnostics(self):
        self.assertTrue(all(not companion.reviewed(p) for p in self.manifest["profiles"].values()))
        self.assertEqual(sum(b["status"] == "reviewed-applicable" for b in self.manifest["cases"]), 0)

    def test_unreviewed_profile_cannot_be_promoted(self):
        self.manifest["cases"][0]["status"] = "reviewed-applicable"
        with self.assertRaisesRegex(ValueError, "independently reviewed"): companion.validate(self.manifest)

    def test_engine_pass_and_citation_without_independent_approval_are_insufficient(self):
        p = self.manifest["profiles"]["hx-draft"]
        p.update(status="reviewed-applicable", enginePassed=True, testsPassed=True,
                 evidence=[{"kind": "primary", "url": "https://example.test/synthetic", "location": "fixture", "rationale": "fixture"}])
        self.assertFalse(companion.reviewed(p))

    def test_unknown_dimensions_cannot_count_as_condition_complete(self):
        p = self.manifest["profiles"]["hx-draft"]
        p.update(status="reviewed-applicable", approval={"reviewer": "Synthetic framework fixture", "reviewedAt": "2026-10-16", "scope": "schema test only", "independentOfEngine": True},
                 evidence=[{"kind": "primary", "url": "https://example.test/synthetic", "location": "fixture", "rationale": "fixture only"}])
        self.assertFalse(companion.reviewed(p))
        p["dimensions"] = {k: {"state": "not-applicable", "rationale": "Synthetic schema fixture, not an admitted chemical profile"} for k in companion.DIMENSIONS}
        self.assertTrue(companion.reviewed(p))

    def test_reagent_and_identity_substitution_rejected(self):
        self.manifest["parentCaseDigests"]["A255"] = "altered-to-peroxide"
        with self.assertRaisesRegex(ValueError, "identities"): companion.validate(self.manifest)

    def test_explicit_frozen_conditions_cannot_be_overwritten(self):
        self.manifest["profiles"]["hx-draft"]["conditions"]["additionStage"] = "two"
        with self.assertRaisesRegex(ValueError, "replace an explicit"): companion.validate(self.manifest)

    def test_unknown_overlay_not_accepted_as_new_chemistry(self):
        self.manifest["profiles"]["hx-draft"]["conditions"]["peroxide"] = True
        with self.assertRaisesRegex(ValueError, "Unsupported condition overlay"): companion.validate(self.manifest)

    def test_a304_is_annotation_not_silent_expectation_replacement(self):
        defect = self.manifest["defects"]["A304"]
        self.assertFalse(defect["appliedToFrozen"])
        self.assertEqual(companion.parents()["A304"]["expected"], defect["originalExpected"])
        binding = next(b for b in self.manifest["cases"] if b["id"] == "A304")
        self.assertNotIn("products", binding["oracle"])
        binding["oracle"]["products"] = defect["proposedConnectivityOnly"]
        with self.assertRaisesRegex(ValueError, "erratum version"): companion.validate(self.manifest)

    def test_version_digest_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory(prefix="companion-version-test-") as folder:
            root = Path(folder)
            (root / "index.json").write_text((companion.DIRECTORY / "index.json").read_text())
            (root / "1.0.0.json").write_text(json.dumps(self.manifest) + " ")
            with patch.object(companion, "DIRECTORY", root), self.assertRaisesRegex(ValueError, "digest mismatch"):
                companion.load()

    def test_same_version_cannot_be_replaced_but_new_versions_can_compare(self):
        changed = deepcopy(self.manifest)
        changed["profiles"]["hx-draft"]["rationale"] += " Test-only revision."
        with self.assertRaisesRegex(ValueError, "overwritten"): companion.compare(self.manifest, changed)
        changed["version"] = "1.0.1-test-only"
        result = companion.compare(self.manifest, changed)
        self.assertEqual(result["changedProfiles"], ["hx-draft"])
        self.assertTrue(result["parentUnchanged"])

    def test_historical_diagnostic_denominators_remain_distinct(self):
        h = self.manifest["historicalDiagnostics"]
        self.assertEqual([(v["frozenStrictFull"], v["diagnosticGeneration"], v["oldScorerDiagnosticFull"], v["positiveDenominator"]) for v in h.values()], [(0, 12, 6, 21), (0, 11, 11, 21), (0, 10, 9, 11)])

    def test_future_version_cannot_rewrite_history(self):
        changed = deepcopy(self.manifest); changed["version"] = "1.0.1-test-only"
        changed["historicalDiagnostics"]["Alkyne halogenation"]["frozenStrictFull"] = 12
        with self.assertRaisesRegex(ValueError, "Historical diagnostics"): companion.compare(self.manifest, changed)

    def test_engine_success_never_admits_draft_case_metrics(self):
        observation = {"matched": True, "errors": [], "options": [{"product": "CC", "byproducts": [], "diagram": True, "mapping": True, "balanced": True, "run": "3d-passed"}]}
        with patch.object(companion, "observe", return_value=observation):
            report = companion.run(self.manifest, diagnostic=True)
        self.assertEqual(report["metrics"]["structuralMatching"], 53)
        self.assertEqual(report["metrics"]["diagnosticModelGenerationOnly"], 53)
        for key in ("conditionCompleteEligibility", "fullySupportedProductGeneration", "independentlyVerifiedChemistry"):
            self.assertEqual(report["metrics"][key], 0)
        self.assertTrue(any(r["transformations"] for r in report["results"]))
        self.assertEqual(next(r for r in report["results"] if r["id"] == "A278")["chemistryState"], "unreviewed")
        self.assertEqual(next(r for r in report["results"] if r["id"] == "A304")["chemistryState"], "frozen-oracle-defect")
        # Synthetic schema-only approval: a wrong independent oracle must be
        # reported as wrong, never as another unreviewed condition profile.
        profile = self.manifest["profiles"]["x2-draft"]
        profile.update(status="reviewed-applicable", approval={"reviewer": "Synthetic fixture only", "reviewedAt": "2026-10-16", "scope": "schema-only test", "independentOfEngine": True},
                       evidence=[{"kind": "primary", "url": "https://example.test/schema-fixture", "location": "synthetic test", "rationale": "not real chemical evidence"}],
                       dimensions={k: {"state": "not-applicable", "rationale": "synthetic test only"} for k in companion.DIMENSIONS})
        binding = next(b for b in self.manifest["cases"] if b["id"] == "A278")
        binding.update(status="reviewed-applicable", applicability={**deepcopy(profile), "caseId": "A278", "profileId": "x2-draft", "profileVersion": self.manifest["version"]})
        binding["oracle"] = {**deepcopy(profile), "products": ["CCC"], "byproducts": [], "connectivityRationale": "Deliberate mismatch fixture", "stereochemistryScope": "schema test", "mappingContract": "schema test", "origin": "independent-specification"}
        with patch.object(companion, "observe", return_value=observation):
            report = companion.run(self.manifest)
        row = next(r for r in report["results"] if r["id"] == "A278")
        self.assertEqual(row["chemistryState"], "failed-independent-oracle")
        self.assertFalse(row["fullySupportedGeneration"])
        self.assertIn({"id": "A278", "reason": "Independent product oracle mismatch"}, report["failures"])
        binding["oracle"]["products"] = ["CC"]
        with patch.object(companion, "observe", return_value=observation):
            report = companion.run(self.manifest)
        row = next(r for r in report["results"] if r["id"] == "A278")
        self.assertEqual(row["chemistryState"], "passed-independent-oracle")
        self.assertTrue(row["fullySupportedGeneration"])


if __name__ == "__main__": unittest.main()
