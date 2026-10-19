"""Authenticated Phase 4B matching, conditions, diagrams and product generation."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
from server.production_app import create_app


class AlkyneCompletePublicApiTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="alkyne-full-api-")
        self.addCleanup(folder.cleanup)
        self.origin = "https://alkyne-full-fixture.example.test"
        password = "Synthetic-full-hydrogenation-password"
        app = create_app({"TRIAL_PASSWORD": password,
                          "SESSION_SECRET": "e374571857d7a740b3447c16980a238c5c7b6c45d8416cc1a9b72f148b543a6a",
                          "PUBLIC_ORIGIN": self.origin, "FRAME_ANCESTORS": "https://frame.example.test",
                          "DIST_DIR": Path(folder.name), "TESTING": True}, chemistry_backend=chemistry)
        self.client = app.test_client()
        self.assertEqual(self.post("/login", data={"password": password}).status_code, 303)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=self.origin, headers={"Origin": self.origin}, **kwargs)

    def body(self, source="CC#CC", conditions=None):
        return {"reactantA": {"smiles": source}, "reactantB": "hydrogen", "conditions": {"catalyst": "metal"} if conditions is None else conditions}

    def matching(self, body):
        r = self.post("/api/reactions/match", json=body)
        self.assertEqual(r.status_code, 200)
        return [x for x in r.json["reactionOptions"] if x["mechanism"] == "Alkyne hydrogenation"]

    def test_saturated_product_and_exact_atom_links(self):
        body = self.body("C#CCCCO"); r = self.matching(body)[0]; body["reactionId"] = r["id"]
        self.assertEqual(r["productSmiles"], "CCCCCO")
        d = self.post("/api/reactions/diagram", json=body)
        p = self.post("/api/reactions/run", json=body)
        self.assertEqual(d.status_code, 200); self.assertEqual(p.status_code, 200)
        self.assertIsNone(d.json["mechanism"])
        self.assertEqual(len(d.json["bondsFormed"]), 4)
        self.assertEqual(len(d.json["bondsBroken"]), 2)
        self.assertEqual(p.json["product"]["smiles"], r["productSmiles"])
        self.assertEqual([(a["atomIndex"], a["mapId"]) for a in d.json["atoms"] if a["side"] == "products"],
                         [(a["index"], a["mapId"]) for a in p.json["product"]["atomLinks"]])

    def test_partial_and_full_switch_without_reusing_old_permission(self):
        body = self.body(); r = self.matching(body)[0]; body["reactionId"] = r["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)
        body["conditions"] = {"catalyst": "lindlar"}
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        response = self.post("/api/reactions/match", json=body)
        partial = next(r for r in response.json["reactionOptions"] if r["mechanism"] == "Alkyne partial hydrogenation")
        body["reactionId"] = partial["id"]
        p = self.post("/api/reactions/run", json=body)
        self.assertEqual(p.status_code, 200)
        self.assertEqual(p.json["product"]["smiles"], "C/C=C\\C")

    def test_missing_catalyst_keeps_conditional_2d_only(self):
        body = self.body(conditions={}); r = self.matching(body)[0]; body["reactionId"] = r["id"]
        self.assertFalse(r["assessment"]["canRun"])
        self.assertEqual(r["assessment"]["evidence"]["missingRequiredSettings"], ["catalyst"])
        self.assertEqual(self.post("/api/reactions/diagram", json=body).status_code, 200)
        p = self.post("/api/reactions/run", json=body)
        self.assertEqual(p.status_code, 422); self.assertNotIn("product", p.json)

    def test_multiple_site_equations_are_not_selective_3d_outcomes(self):
        body = self.body("C#CCCCCC#C"); found = self.matching(body)
        self.assertEqual(len(found), 1)
        identity = found[0]["optionIdentity"]
        self.assertEqual(identity["siteCount"], 2)
        for identifier in identity["sourceReactionIds"]:
            body["reactionId"] = identifier
            d = self.post("/api/reactions/diagram", json=body)
            self.assertEqual(d.status_code, 200)
            self.assertIn("bookkeeping", d.json["note"])
            self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        self.assertEqual(len(self.matching(self.body("C#CCCCCCC#CC"))), 2)

    def test_wrong_reagent_and_forged_id_cannot_reuse_a_full_product(self):
        body = self.body(); body["reactionId"] = self.matching(body)[0]["id"]
        body["reactantB"] = "water"
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 422)
        body = self.body(); body["reactionId"] = "unverified-complete-product"
        self.assertEqual(self.post("/api/reactions/diagram", json=body).status_code, 422)

    def test_reverse_slots_stereo_and_theoretical_two_h2(self):
        body = self.body("C#CCC[C@H](C)CCC(C)(C)C")
        body["reactantA"], body["reactantB"] = body["reactantB"], body["reactantA"]
        r = self.matching(body)[0]
        self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"], "H2")
        self.assertEqual(r["stoichiometry"]["reactants"][0]["coefficient"], 2)
        self.assertEqual(r["stereochemistry"]["reactant"]["chiralCenters"][0]["assignment"], "R")
        self.assertEqual(r["stereochemistry"]["product"]["chiralCenters"][0]["assignment"], "S")
        body["reactionId"] = r["id"]
        self.assertEqual(self.post("/api/reactions/run", json=body).status_code, 200)
