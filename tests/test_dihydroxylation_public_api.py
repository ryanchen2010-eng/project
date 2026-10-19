"""Authenticated public match/diagram/run routes for the unchanged diol model."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
try:
    from server.production_app import create_app
except ModuleNotFoundError as exc:
    if exc.name != "flask": raise
    create_app = None


@unittest.skipIf(create_app is None, "Optional production Flask requirements not installed")
class DihydroxylationPublicApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="diol-http-tests-"); self.addCleanup(directory.cleanup)
        self.origin = "https://diol-fixture.example.test"; password = "Synthetic-Diol-test-password"
        app = create_app({"TRIAL_PASSWORD":password,"SESSION_SECRET":"18761b53ac06992ae0e8d6bdf0f6e33182d7e923438230abb9685c86790ed4bd",
                          "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test",
                          "DIST_DIR":Path(directory.name),"TESTING":True}, chemistry_backend=chemistry)
        self.client = app.test_client()
        self.assertEqual(self.post("/login",data={"password":password}).status_code,303)
    def post(self,path,**kwargs): return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)
    def body(self,source="C/C=C/C",conditions=None):
        return {"reactantA":{"smiles":source},"reactantB":"hydrogen-peroxide",
                "conditions":{"catalyst":"osmium","workup":"aqueous-release"} if conditions is None else conditions}
    def options(self,body):
        response = self.post("/api/reactions/match",json=body); self.assertEqual(response.status_code,200)
        return [r for r in response.json["reactions"] if r["mechanism"] == "Alkene dihydroxylation"]
    def test_e_z_and_cyclic_all_three_routes(self):
        for source,count in [("C/C=C/C",2),("C/C=C\\C",1),("C1=CCCCC1",1)]:
            body = self.body(source); rs = self.options(body); self.assertEqual(len(rs),count)
            for r in rs:
                body["reactionId"] = r["id"]
                d = self.post("/api/reactions/diagram",json=body); p = self.post("/api/reactions/run",json=body)
                self.assertEqual(d.status_code,200); self.assertEqual(p.status_code,200)
                self.assertIsNone(d.json["mechanism"]); self.assertEqual(p.json["product"]["smiles"],r["productSmiles"])
                self.assertEqual([(v["atomIndex"],v["mapId"],v["element"]) for v in d.json["atoms"] if v["side"] == "products"],
                                 [(v["index"],v["mapId"],v["element"]) for v in p.json["product"]["atomLinks"]])
    def test_missing_workup_blocks_run_not_net_preview(self):
        body = self.body(conditions={"catalyst":"osmium"}); rs = self.options(body)
        for r in rs:
            self.assertFalse(r["assessment"]["canRun"]); body["reactionId"] = r["id"]
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            p = self.post("/api/reactions/run",json=body); self.assertEqual(p.status_code,422); self.assertNotIn("product",p.json)
    def test_no_osmium_and_wrong_activation_block_run(self):
        for catalyst in ["", "none", "acid", "metal", "radical"]:
            body = self.body(conditions={"catalyst":catalyst,"workup":"aqueous-release"})
            r = self.options(body)[0]; body["reactionId"] = r["id"]
            self.assertFalse(r["assessment"]["canRun"]); self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
    def test_changing_workup_cannot_reuse_previous_run(self):
        body = self.body(); r = self.options(body)[0]; body["reactionId"] = r["id"]
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
        body["conditions"]["workup"] = ""
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
    def test_multisite_site_selection_and_full_reagent_mass(self):
        body = self.body("C=CCCCCC=CC"); rs = self.options(body)
        self.assertEqual(len(rs),3); self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}),2)
        for r in rs:
            self.assertEqual(r["stoichiometry"]["reactants"][1]["molarMass"],34.014)
            body["reactionId"] = r["id"]; self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
    def test_reversed_inputs_and_distant_stereo(self):
        body = self.body("C=CC[C@H](C)CC"); body["reactantA"],body["reactantB"] = body["reactantB"],body["reactantA"]
        for r in self.options(body):
            body["reactionId"] = r["id"]; d = self.post("/api/reactions/diagram",json=body)
            self.assertEqual(d.status_code,200); self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"H2O2")
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
    def test_unsupported_structures_explain_why(self):
        for source,reason in [("C=CC=C","Conjugated"),("C=CCO","Activated"),("C1=CCCCCCC1","5–7-membered")]:
            response = self.post("/api/reactions/match",json=self.body(source))
            self.assertEqual(response.status_code,200); self.assertFalse(response.json["reactions"])
            self.assertIn(reason," ".join(response.json["unsupportedReasons"]))
    def test_invalid_workup_and_reagents_cannot_create_product(self):
        body = self.body(conditions={"catalyst":"osmium","workup":"not-a-model"})
        self.assertEqual(self.post("/api/reactions/match",json=body).status_code,422)
        for reagent in [{"smiles":"COO"}, {"smiles":"CC(=O)OO"}, "water"]:
            body = self.body(); body["reactantB"] = reagent
            self.assertFalse(self.options(body))
