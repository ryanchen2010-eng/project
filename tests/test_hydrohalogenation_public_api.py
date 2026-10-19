"""Phase 3B authenticated HTTP checks, using synthetic local credentials only."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
try:
    from server.production_app import create_app
except ModuleNotFoundError as exc:
    if exc.name != "flask":
        raise
    create_app = None


@unittest.skipIf(create_app is None, "Install optional production requirements for authenticated HTTP checks")
class HydrohalogenationPublicApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="hx-http-tests-")
        self.addCleanup(directory.cleanup)
        self.origin = "https://hx-fixture.example.test"
        password = "Synthetic-HX-test-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "f1953e0b1eab9a1d0215c8b286d51b7aee40fc3342578c486cfd47214e6a4ed6",
                          "PUBLIC_ORIGIN": self.origin, "FRAME_ANCESTORS": "https://frame.example.test",
                          "DIST_DIR": Path(directory.name), "TESTING": True}, chemistry_backend=chemistry)
        self.client = app.test_client()
        self.assertEqual(self.post("/login", data={"password": password}).status_code, 303)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=self.origin, headers={"Origin": self.origin}, **kwargs)

    def body(self, substrate="CC=CCCC", reagent="hydrogen-bromide", conditions=None):
        return {"reactantA": {"name": "Not a preset", "smiles": substrate}, "reactantB": reagent,
                "conditions": {"solvent": "dry", "catalyst": "none"} if conditions is None else conditions}

    def options(self, body):
        response = self.post("/api/reactions/match", json=body)
        self.assertEqual(response.status_code, 200)
        return [r for r in response.json["reactions"] if r["mechanism"] == "Hydrohalogenation"], response.json

    def test_public_internal_alternatives_products_amounts_and_exact_maps(self):
        body = self.body()
        options, _ = self.options(body)
        self.assertEqual({r["productSmiles"] for r in options}, {"CCCCC(C)Br", "CCCC(Br)CC"})
        self.assertEqual(len(options), 2)
        for option in options:
            self.assertIsNone(option["regioselectivity"]["ratios"])
            self.assertTrue(option["assessment"]["canRun"])
            self.assertEqual([r["coefficient"] for r in option["stoichiometry"]["reactants"]], [1, 1])
            body["reactionId"] = option["id"]
            diagram = self.post("/api/reactions/diagram", json=body)
            run = self.post("/api/reactions/run", json=body)
            self.assertEqual(diagram.status_code, 200); self.assertEqual(run.status_code, 200)
            self.assertTrue(run.json["balanced"])
            self.assertEqual(run.json["product"]["smiles"], option["productSmiles"])
            after = [a for a in diagram.json["atoms"] if a["side"] == "products"]
            self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after],
                             [(a["index"], a["mapId"], a["element"]) for a in run.json["product"]["atomLinks"]])
            self.assertEqual(len(diagram.json["bondsBroken"]), 1)
            self.assertEqual(len(diagram.json["bondsFormed"]), 2)
            self.assertEqual(len(diagram.json["bondOrderChanges"]), 1)

    def test_all_actual_hx_reagents_keep_identity_with_reversed_inputs(self):
        for reagent, x in [("hydrogen-chloride", "Cl"), ("hydrogen-bromide", "Br"), ("hydrogen-iodide", "I")]:
            for reverse in [False, True]:
                body = self.body("C=CC", reagent)
                if reverse: body["reactantA"], body["reactantB"] = body["reactantB"], body["reactantA"]
                options, _ = self.options(body)
                self.assertEqual(len(options), 1)
                self.assertEqual(options[0]["productSmiles"], f"CC(C){x}")
                self.assertEqual(options[0]["hxModel"]["hydrogenHalide"], "H" + x)
                body["reactionId"] = options[0]["id"]
                self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)

    def test_radical_conditions_remove_ionic_options_and_forged_run_fails(self):
        body = self.body("C=CC")
        previous, _ = self.options(body)
        body["conditions"]["catalyst"] = "radical"
        options, result = self.options(body)
        self.assertEqual(options, [])
        self.assertIn("separate validated radical", " ".join(result["unsupportedReasons"]))
        body["reactionId"] = previous[0]["id"]
        for endpoint in ["diagram", "run"]:
            response = self.post("/api/reactions/" + endpoint, json=body)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn("product", response.json)

    def test_capturing_media_allow_conditional_2d_only(self):
        for medium in ["aqueous-protic", "ethanolic-protic"]:
            body = self.body("C=CC", conditions={"solvent": medium})
            options, _ = self.options(body)
            self.assertEqual(len(options), 1)
            self.assertFalse(options[0]["assessment"]["canRun"])
            self.assertEqual(options[0]["assessment"]["status"], "unevaluated")
            body["reactionId"] = options[0]["id"]
            diagram = self.post("/api/reactions/diagram", json=body)
            self.assertEqual(diagram.status_code, 200)
            self.assertIn("Conditional ionic HX", diagram.json["note"])
            self.assertFalse(diagram.json["assessment"]["canRun"])
            run = self.post("/api/reactions/run", json=body)
            self.assertEqual(run.status_code, 422)
            self.assertIn("can compete", run.json["error"])

    def test_hcl_oxygen_scope_requires_ambient_conditions_but_hbr_remains_excluded(self):
        body = self.body("C=CCCCCCCCO", "hydrogen-chloride")
        options, _ = self.options(body)
        self.assertEqual(len(options), 1)
        self.assertFalse(options[0]["assessment"]["canRun"])
        body["reactionId"] = options[0]["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        body["conditions"]["temperature"] = "ambient"
        options, _ = self.options(body)
        self.assertTrue(options[0]["assessment"]["canRun"])
        body["reactionId"] = options[0]["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)
        body["reactantB"] = "hydrogen-bromide"
        self.assertFalse(self.options(body)[0])
        body["reactantB"] = "hydrogen-chloride"
        body["conditions"]["temperature"] = "heated"
        options, result = self.options(body)
        self.assertFalse(options)
        self.assertIn("bounded ambient", " ".join(result["unsupportedReasons"]))

    def test_public_independent_sites_and_proven_equivalent_site_grouping(self):
        for substrate, expected_count, alias_count in [("C=CCCCCCCCCC=CC", 3, 1), ("C=CCCCCCCCCC=C", 1, 2)]:
            body = self.body(substrate)
            options, _ = self.options(body)
            self.assertEqual(len(options), expected_count)
            for option in options:
                self.assertEqual(len(option["site"]["parameters"]["equivalentSiteAtomMaps"]), alias_count)
                body["reactionId"] = option["id"]
                diagram = self.post("/api/reactions/diagram", json=body)
                self.assertEqual(diagram.status_code, 200)
                changes = diagram.json["bondOrderChanges"]
                self.assertEqual(len(changes), 1)
                self.assertEqual(set(changes[0]["atomMaps"]), set(option["site"]["atomMaps"]))
