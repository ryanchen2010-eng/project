"""Real authenticated Phase 4A match, selection, preview and 3D routes."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
from server.production_app import create_app


class AlkynePartialPublicApiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="lindlar-api-tests-")
        self.addCleanup(folder.cleanup)
        self.origin = "https://lindlar-fixture.example.test"
        password = "Synthetic-Lindlar-test-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "e374571857d7a740b3447c16980a238c5c7b6c45d8416cc1a9b72f148b543a6a",
                          "PUBLIC_ORIGIN": self.origin, "FRAME_ANCESTORS": "https://frame.example.test",
                          "DIST_DIR": Path(folder.name), "TESTING": True}, chemistry_backend=chemistry)
        self.client = app.test_client()
        self.assertEqual(self.post("/login", data={"password": password}).status_code, 303)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=self.origin, headers={"Origin": self.origin}, **kwargs)

    def body(self, source="CC#CC", conditions=None):
        return {"reactantA": {"smiles": source}, "reactantB": "hydrogen", "conditions": {"catalyst": "lindlar"} if conditions is None else conditions}

    def matching(self, body):
        r = self.post("/api/reactions/match", json=body)
        self.assertEqual(r.status_code, 200)
        return [x for x in r.json["reactionOptions"] if x["mechanism"] == "Alkyne partial hydrogenation"]

    def test_internal_z_public_workflow(self):
        body = self.body()
        r = self.matching(body)[0]
        self.assertEqual(r["productSmiles"], "C/C=C\\C")
        body["reactionId"] = r["id"]
        d = self.post("/api/reactions/diagram", json=body)
        p = self.post("/api/reactions/run", json=body)
        self.assertEqual(d.status_code, 200)
        self.assertEqual(p.status_code, 200)
        self.assertIsNone(d.json["mechanism"])
        self.assertEqual(p.json["product"]["smiles"], r["productSmiles"])
        self.assertEqual([(a["atomIndex"], a["mapId"]) for a in d.json["atoms"] if a["side"] == "products"],
                         [(a["index"], a["mapId"]) for a in p.json["product"]["atomLinks"]])

    def test_missing_activation_is_preview_only(self):
        body = self.body(conditions={})
        r = self.matching(body)[0]; body["reactionId"] = r["id"]
        self.assertEqual(r["assessment"]["evidence"]["missingRequiredSettings"], ["catalyst"])
        self.assertEqual(self.post("/api/reactions/diagram", json=body).status_code, 200)
        p = self.post("/api/reactions/run", json=body)
        self.assertEqual(p.status_code, 422); self.assertNotIn("product", p.json)

    def test_condition_changes_cannot_reuse_previous_3d_permission(self):
        body = self.body(); body["reactionId"] = self.matching(body)[0]["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)
        for conditions in [{"catalyst": "metal"}, {}, {"catalyst": "lindlar", "solvent": "ethanolic-protic"}]:
            body["conditions"] = conditions
            self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)

    def test_equivalent_ids_and_distinct_products(self):
        body = self.body("C#CCCCCC#C")
        r = self.matching(body)
        self.assertEqual(len(r), 1)
        self.assertEqual(len(r[0]["optionIdentity"]["sourceReactionIds"]), 2)
        for identifier in r[0]["optionIdentity"]["sourceReactionIds"]:
            body["reactionId"] = identifier
            self.assertEqual(self.post("/api/reactions/diagram", json=body).status_code, 200)
            self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        self.assertEqual(len(self.matching(self.body("C#CCCCCCC#CC"))), 2)

    def test_wrong_reagent_or_forged_id_cannot_reuse_a_product(self):
        body = self.body(); body["reactionId"] = self.matching(body)[0]["id"]
        body["reactantB"] = "water"
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        body = self.body(); body["reactionId"] = "unverified-lindlar-product"
        self.assertEqual(self.post("/api/reactions/diagram", json=body).status_code, 422)

    def test_reversed_hydrogen_slot_and_distant_configuration(self):
        body = self.body("C#CC[C@H](C)CC")
        body["reactantA"], body["reactantB"] = body["reactantB"], body["reactantA"]
        r = self.matching(body)[0]
        self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"], "H2")
        self.assertEqual(r["stereochemistry"]["reactant"]["chiralCenters"][0]["assignment"], r["stereochemistry"]["product"]["chiralCenters"][0]["assignment"])
        body["reactionId"] = r["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)
