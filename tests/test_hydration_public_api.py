"""Real chemistry through authenticated HTTP handlers without listening sockets.

Only synthetic local credentials are used; no hosting/publication is involved.
"""
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
class HydrationPublicApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="hydration-http-tests-")
        self.addCleanup(self.directory.cleanup)
        self.origin = "https://hydration-fixture.example.test"
        password = "Synthetic-hydration-test-password"
        self.app = create_app({"TRIAL_PASSWORD": password,
                               "SESSION_SECRET": "5a793bc832adc647a5f382190dead01d19f58f6fa0c9246eb8b2b31f0f419b60",
                               "PUBLIC_ORIGIN": self.origin, "FRAME_ANCESTORS": "https://frame.example.test",
                               "DIST_DIR": Path(self.directory.name), "TESTING": True}, chemistry_backend=chemistry)
        self.client = self.app.test_client()
        self.assertEqual(self.post("/login", data={"password": password}).status_code, 303)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=self.origin, headers={"Origin": self.origin}, **kwargs)

    def body(self, conditions=None, substrate="CC=CCCC"):
        return {"reactantA": {"name": "Not a preset", "smiles": substrate}, "reactantB": "water",
                "conditions": {} if conditions is None else conditions}

    def test_public_match_returns_separate_internal_regio_options(self):
        response = self.post("/api/reactions/match", json=self.body({"catalyst": "acid"}))
        self.assertEqual(response.status_code, 200)
        options = response.json["reactions"]
        self.assertEqual(len(options), 2)
        self.assertEqual({o["productSmiles"] for o in options}, {"CCCCC(C)O", "CCCC(O)CC"})
        self.assertTrue(all(o["regioselectivity"]["ratios"] is None for o in options))
        self.assertTrue(all(o["assessment"]["canRun"] for o in options))

    def test_public_missing_acid_allows_conditional_2d_but_returns_422_on_run(self):
        body = self.body(substrate="C=CC")
        matched = self.post("/api/reactions/match", json=body)
        self.assertEqual(matched.status_code, 200)
        body["reactionId"] = matched.json["reactions"][0]["id"]
        diagram = self.post("/api/reactions/diagram", json=body)
        self.assertEqual(diagram.status_code, 200)
        self.assertFalse(diagram.json["assessment"]["canRun"])
        self.assertIn("Conditional net hydration", diagram.json["note"])
        run = self.post("/api/reactions/run", json=body)
        self.assertEqual(run.status_code, 422)
        self.assertIn("Acid activation is required", run.json["error"])
        self.assertNotIn("product", run.json)

    def test_public_acid_enabled_alternatives_link_exact_2d_3d_maps(self):
        body = self.body({"catalyst": "acid", "solvent": "aqueous-protic"})
        matched = self.post("/api/reactions/match", json=body)
        for option in matched.json["reactions"]:
            body["reactionId"] = option["id"]
            diagram = self.post("/api/reactions/diagram", json=body)
            run = self.post("/api/reactions/run", json=body)
            self.assertEqual(diagram.status_code, 200); self.assertEqual(run.status_code, 200)
            self.assertEqual(run.json["product"]["smiles"], option["productSmiles"])
            self.assertTrue(run.json["balanced"])
            after = [a for a in diagram.json["atoms"] if a["side"] == "products"]
            self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after],
                             [(a["index"], a["mapId"], a["element"]) for a in run.json["product"]["atomLinks"]])

    def test_public_rearrangement_rejection_and_forged_site_id(self):
        body = self.body({"catalyst": "acid"}, "C=CC(C)C")
        matched = self.post("/api/reactions/match", json=body)
        self.assertEqual(matched.status_code, 200)
        self.assertEqual(matched.json["reactions"], [])
        self.assertIn("shift", " ".join(matched.json["unsupportedReasons"]))
        body["reactionId"] = "hydration-drawn-1"
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
