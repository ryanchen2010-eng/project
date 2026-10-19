"""Phase 3H confidence/grouping fixes; original tests and benchmark unchanged."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from server import chemistry_server as service, addition_contract
from scripts import audit_addition_consistency as audit
from server.production_app import create_app


class AdditionContractTests(unittest.TestCase):
    def matches(self, path, source="C=CC", conditions=None):
        reagent, model = audit.MODELS[path]
        response = service.match_reactions({"smiles": source}, reagent, model if conditions is None else conditions)
        return [o for o in response["reactionOptions"] if o["mechanism"] == path], response

    def test_fixed_benchmark_bytes_unchanged(self):
        self.assertEqual(hashlib.sha256(Path("scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
                         "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55")

    def test_diol_solvent_is_explicitly_unknown_not_newly_validated(self):
        for medium in ["", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"]:
            options, _ = self.matches("Alkene dihydroxylation", conditions={"catalyst": "osmium", "workup": "aqueous-release", "solvent": medium})
            for o in options:
                fact = o["assessment"]["evidence"]
                self.assertTrue(fact["canGenerate3D"])
                self.assertIn("solvent", fact["unknownConditions"])
                self.assertEqual(fact["evaluatedFactors"]["solvent"]["status"], "unevaluated")
                self.assertIn("solvent not evaluated", fact["label"])
                self.assertFalse(fact["workupRepresented"])
                self.assertTrue(fact["workupAssumptionConfirmed"])

    def test_hx_missing_medium_qualified_render_not_condition_completeness(self):
        o = self.matches("Hydrohalogenation", conditions={})[0][0]
        e = o["assessment"]["evidence"]
        self.assertTrue(e["canGenerate3D"])
        self.assertEqual(e["conditionCompleteness"], "incomplete")
        self.assertIn("medium unspecified", e["label"])
        self.assertEqual(e["experimentalOutcome"], "not-predicted")

    def test_required_activation_and_workup_separated_from_reference_comparison(self):
        for path, required in [("Hydration", {"catalyst"}), ("Alkene dihydroxylation", {"catalyst", "workup"})]:
            e = self.matches(path, conditions={})[0][0]["assessment"]["evidence"]
            self.assertEqual(set(e["missingRequiredSettings"]), required)
            self.assertEqual(e["requirementsState"], "missing")
            self.assertFalse(e["canGenerate3D"])
            self.assertTrue(e["canPreview2D"])

    def test_hcl_oxygen_requires_explicit_temperature(self):
        response = service.match_reactions({"smiles": "C=CCCCCCCCO"}, "hydrogen-chloride", {"solvent": "dry"})
        e = response["reactionOptions"][0]["assessment"]["evidence"]
        self.assertEqual(e["missingRequiredSettings"], ["temperature"])
        self.assertFalse(e["canGenerate3D"])

    def test_hydration_groups_symmetry_but_keeps_every_addressable_id(self):
        options, response = self.matches("Hydration", "C=CCCCCCCCCC=C")
        self.assertEqual(len(options), 1)
        self.assertEqual(len(response["reactions"]), 2)  # existing site-addressable contract
        o = options[0]
        self.assertEqual(set(o["optionIdentity"]["sourceReactionIds"]), {r["id"] for r in response["reactions"]})
        self.assertEqual(o["optionIdentity"]["siteCount"], 2)
        self.assertEqual(o["optionIdentity"]["aliasKind"], "site-and-capture-atom")
        self.assertEqual(response["contractVersion"], 2)
        self.assertEqual(len(o["site"]["parameters"]["equivalentSiteAtomMaps"]), 2)
        self.assertEqual(response["optionCounts"]["mechanismCount"], 1)
        self.assertEqual(response["optionCounts"]["productCount"], 1)
        self.assertEqual(response["optionCounts"]["siteCount"], 2)
        for r in response["reactions"]:
            d = service.reaction_diagram(r["id"], {"smiles": "C=CCCCCCCCCC=C"}, "water", {"catalyst": "acid"})
            self.assertEqual(d["site"]["atomMaps"], r["site"]["atomMaps"])

    def test_unequal_capture_orientations_not_merged_by_formula(self):
        options, response = self.matches("Hydration", "CC=CCC")
        self.assertEqual(len(options), 2)
        self.assertEqual(len({r["productSmiles"] for r in options}), 2)
        self.assertEqual(response["optionCounts"]["siteCount"], 1)
        self.assertEqual(len({r["productFormula"] for r in options}), 1)

    def test_grouping_does_not_mutate_legacy_response(self):
        options, response = self.matches("Hydration", "C=CCCCCCCCCC=C")
        options[0]["optionIdentity"]["sourceReactionIds"].clear()
        options[0]["site"]["atomMaps"].clear()
        self.assertEqual(len(response["reactions"][0]["site"]["atomMaps"]), 2)

    def test_diol_face_options_are_not_two_sites(self):
        options, response = self.matches("Alkene dihydroxylation")
        self.assertEqual(len(options), 2)
        self.assertEqual(response["optionCounts"]["siteCount"], 1)
        self.assertEqual(response["optionCounts"]["mechanismCount"], 1)

    def test_net_only_diagram_does_not_claim_missing_mechanism_exists(self):
        for path in ["Hydration", "Hydrohalogenation"]:
            reagent, conditions = audit.MODELS[path]
            options, _ = self.matches(path)
            d = service.reaction_diagram(options[0]["id"], {"smiles": "C=CC"}, reagent, conditions)
            self.assertIsNone(d["mechanism"])
            self.assertIn("distant configurations are retained", d["note"])
            self.assertNotIn("steps appear separately", d["note"])
            self.assertNotIn("omits intermediate steps and stereochemistry", d["note"])

    def test_calculation_context_carries_exact_selected_conditions(self):
        c = {"catalyst": "osmium", "workup": "aqueous-release", "solvent": "dry"}
        o = self.matches("Alkene dihydroxylation", conditions=c)[0][0]
        context = o["stoichiometry"]["context"]
        self.assertEqual(context["conditions"], service._conditions(c))
        self.assertIn("formal net bookkeeping", context["warning"])
        self.assertIn("solvent", context["unknownConditions"])
        self.assertFalse(self.matches("Alkene dihydroxylation", conditions={"catalyst": "osmium"})[0][0]["stoichiometry"]["context"]["canGenerate3D"])

    def test_standalone_catalog_keeps_unknown_conditions_unknown(self):
        for r in service.reaction_catalog()["reactions"]:
            if r["mechanism"] in addition_contract.PATHWAYS or r.get("secondaryOxidationModel"):
                c = r["stoichiometry"]["context"]
                self.assertEqual(c["assertionLevel"], "conditional-net")
                self.assertFalse(any(c["conditions"].values()))
                self.assertIn("assumed, not predicted", c["warning"])
            else:
                self.assertNotIn("context", r["stoichiometry"])

    def test_diagnostic_preserves_2d_success_when_run_is_blocked(self):
        options, _ = self.matches("Alkene dihydroxylation", conditions={"catalyst": "osmium"})
        row = audit.inspect_option(options[0], {"smiles": "C=CC"}, "hydrogen-peroxide", {"catalyst": "osmium"})
        self.assertEqual(row["diagram"]["status"], "verified")
        self.assertEqual(row["run"]["status"], "blocked")
        self.assertFalse(row["failures"])

    def test_diagnostic_distinguishes_real_diagram_failure(self):
        o = self.matches("Hydration")[0][0]
        with patch.object(service, "reaction_diagram", side_effect=service.ChemistryError("Diagnostic-only diagram fault")):
            row = audit.inspect_option(o, {"smiles": "C=CC"}, "water", audit.MODELS["Hydration"][1])
        self.assertEqual(row["diagram"]["status"], "failed")
        self.assertEqual(row["run"]["status"], "verified")
        self.assertIn("Unexpected diagram failure", row["failures"])


def contract_test(path):
    def check(self):
        options, response = self.matches(path)
        self.assertTrue(options)
        self.assertEqual(response["supportState"], "Conditional")
        self.assertEqual(response["structuralEligibility"], "eligible")
        for o in options:
            e = o["assessment"]["evidence"]
            self.assertEqual(e["assertionLevel"], "conditional-net")
            self.assertEqual(e["reagentIdentity"], "validated")
            self.assertEqual(e["canGenerate3D"], o["assessment"]["canRun"])
            self.assertEqual(o["stoichiometry"]["context"]["label"], e["label"])
    return check


for path in audit.MODELS:
    setattr(AdditionContractTests, "test_confidence_contract_" + path.lower().replace(" ", "_"), contract_test(path))


class AdditionIndependentDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.result = audit.run_audit()


def independent_case(index):
    def check(self):
        row = self.result["results"][index]
        self.assertEqual(row["failures"], [], str(row))
    return check


for i, c in enumerate(audit.build_cases()):
    setattr(AdditionIndependentDiagnostics, f"test_{i:02d}_" + c["path"].replace(" ", "_") + "_" + c["label"].replace(" ", "_"), independent_case(i))


class AdditionPublicContract(unittest.TestCase):
    def test_authenticated_workflow_exposes_grouping_context_and_unchanged_workup_gate(self):
        with tempfile.TemporaryDirectory(prefix="addition-contract-") as directory:
            origin = "https://addition.example.test"
            app = create_app({"TRIAL_PASSWORD": "Synthetic-addition-test-password", "SESSION_SECRET": "18761b53ac06992ae0e8d6bdf0f6e33182d7e923438230abb9685c86790ed4bd",
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": "https://frame.example.test",
                              "DIST_DIR": Path(directory), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            def post(url, **kwargs): return client.post(url, base_url=origin, headers={"Origin": origin}, **kwargs)
            self.assertEqual(post("/login", data={"password": "Synthetic-addition-test-password"}).status_code, 303)
            body = {"reactantA": {"smiles": "C=CCCCCCCCCC=C"}, "reactantB": "water", "conditions": {"catalyst": "acid"}}
            r = post("/api/reactions/match", json=body)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.json["reactionOptions"]), 1)
            self.assertEqual(r.json["optionCounts"]["siteCount"], 2)
            body["reactionId"] = r.json["reactionOptions"][0]["id"]
            self.assertEqual(post("/api/reactions/diagram", json=body).status_code, 200)
            self.assertEqual(post("/api/reactions/run", json=body).status_code, 200)
            body = {"reactantA": "propene", "reactantB": "hydrogen-peroxide", "conditions": {"catalyst": "osmium"}}
            r = post("/api/reactions/match", json=body)
            self.assertEqual(r.json["supportState"], "Conditional")
            o = r.json["reactionOptions"][0]
            self.assertIn("workup", o["stoichiometry"]["context"]["missingRequiredSettings"])
            body["reactionId"] = o["id"]
            self.assertEqual(post("/api/reactions/diagram", json=body).status_code, 200)
            self.assertEqual(post("/api/reactions/run", json=body).status_code, 422)
