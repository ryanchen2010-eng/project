"""Authenticated Phase 3E public workflow, synthetic local credentials only."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
try:
    from server.production_app import create_app
except ModuleNotFoundError as exc:
    if exc.name != "flask":raise
    create_app=None


@unittest.skipIf(create_app is None,"Optional production Flask requirements not installed")
class EpoxidationPublicApiTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix="epoxide-http-tests-")
        self.addCleanup(directory.cleanup)
        self.origin="https://epoxide-fixture.example.test"
        password="Synthetic-Epoxide-test-password"
        app=create_app({"TRIAL_PASSWORD":password,"SESSION_SECRET":"e374571857d7a740b3447c16980a238c5c7b6c45d8416cc1a9b72f148b543a6a",
                        "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test",
                        "DIST_DIR":Path(directory.name),"TESTING":True},chemistry_backend=chemistry)
        self.client=app.test_client()
        self.assertEqual(self.post("/login",data={"password":password}).status_code,303)

    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)
    def body(self,source="C/C=C\\C",conditions=None):
        return {"reactantA":{"smiles":source},"reactantB":"peracetic-acid","conditions":{"solvent":"dry"} if conditions is None else conditions}
    def options(self,body):
        response=self.post("/api/reactions/match",json=body)
        self.assertEqual(response.status_code,200)
        return response.json


    def test_e_z_and_cyclic_structures_through_all_three_apis(self):
        for source,count in [("C/C=C/C",2),("C/C=C\\\\C",1),("C1=CCCCC1",1)]:
            body=self.body(source);rs=self.options(body)["reactions"]
            self.assertEqual(len(rs),count)
            for r in rs:
                body["reactionId"]=r["id"]
                d=self.post("/api/reactions/diagram",json=body);p=self.post("/api/reactions/run",json=body)
                self.assertEqual(d.status_code,200);self.assertEqual(p.status_code,200)
                self.assertEqual(p.json["product"]["smiles"],r["productSmiles"])
                main=[a for a in d.json["atoms"] if a["side"]=="products" and a["speciesIndex"]==0]
                self.assertEqual([(a["atomIndex"],a["mapId"],a["element"]) for a in main],
                                 [(a["index"],a["mapId"],a["element"]) for a in p.json["product"]["atomLinks"]])
                self.assertEqual(len(d.json["mechanism"]["steps"]),1)
                self.assertTrue(d.json["mechanism"]["steps"][0]["concerted"])

    def test_actual_mcpba_acid_and_transferred_oxygen_in_both_input_orders(self):
        for reverse in [False,True]:
            body=self.body("C=CC");body["reactantB"]={"smiles":"O=C(OO)c1cccc(Cl)c1"}
            if reverse:body["reactantA"],body["reactantB"]=body["reactantB"],body["reactantA"]
            for r in self.options(body)["reactions"]:
                body["reactionId"]=r["id"];d=self.post("/api/reactions/diagram",json=body)
                self.assertEqual(d.status_code,200)
                self.assertEqual(d.json["products"][1]["formula"],"C7H5ClO2")
                transferred=r["site"]["parameters"]["transferredOxygen"]
                after=[a for a in d.json["atoms"] if a["side"]=="products"]
                self.assertEqual(next(a["speciesIndex"] for a in after if a["mapId"]==transferred),0)
                self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_missing_capturing_and_unknown_medium_cannot_run_epoxide(self):
        for medium in ["","aqueous-protic","ethanolic-protic","polar-aprotic"]:
            body=self.body("C=CC",{"solvent":medium})
            r=self.options(body)["reactions"][0];body["reactionId"]=r["id"]
            self.assertFalse(r["assessment"]["canRun"])
            self.assertNotEqual(r["assessment"]["status"],"disfavored")
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            p=self.post("/api/reactions/run",json=body)
            self.assertEqual(p.status_code,422);self.assertNotIn("product",p.json)

    def test_radical_change_rejects_old_ionic_selection(self):
        body=self.body("C=CC");r=self.options(body)["reactions"][0]
        body["conditions"]["catalyst"]="radical";body["reactionId"]=r["id"]
        response=self.options(body)
        self.assertEqual(response["reactions"],[])
        self.assertIn("Radical activation"," ".join(response["unsupportedReasons"]))
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_multiple_sites_and_face_choices_are_independent(self):
        body=self.body("C=CCCCCC=CC")
        rs=self.options(body)["reactions"]
        self.assertEqual(len(rs),3);self.assertEqual(len({tuple(r["site"]["atomMaps"]) for r in rs}),2)
        for r in rs:
            body["reactionId"]=r["id"]
            p=self.post("/api/reactions/run",json=body)
            self.assertEqual(p.status_code,200)
            self.assertEqual(p.json["product"]["smiles"],r["productSmiles"])

    def test_screened_remote_oxygen_and_near_capture_fail_closed(self):
        for source in ["C=CCCCCCCCO","C=CCCCCCCCOC"]:
            self.assertEqual(len(self.options(self.body(source))["reactions"]),2)
        for source in ["C=CCCCO","C=CCCCCCCCOC(C)(C)C","C=CCCCCCCC=O"]:
            response=self.options(self.body(source))
            self.assertEqual(response["reactions"],[]);self.assertTrue(response["unsupportedReasons"])

    def test_distant_cip_change_does_not_erase_configuration(self):
        body=self.body("C=CCC[C@H](C)CCC(C)(C)C")
        for r in self.options(body)["reactions"]:
            old=r["stereochemistry"]["reactant"]["chiralCenters"][0]
            new=next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"]==old["atomMap"])
            self.assertEqual((old["assignment"],new["assignment"]),("S","R"))
            body["reactionId"]=r["id"]
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_wrong_oxidant_and_forged_reaction_id_cannot_reuse_product(self):
        body=self.body("C=CC");r=self.options(body)["reactions"][0];body["reactionId"]=r["id"]
        body["reactantB"]="hydrogen-peroxide"
        self.assertFalse(any(o["mechanism"]=="Epoxidation" for o in self.options(body)["reactions"]))
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body["reactantB"]="peracetic-acid";body["reactionId"]+="-fabricated"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        for invalid in ["C/C(=O)OO","O=[C@](C)OO"]:
            body["reactantB"]={"smiles":invalid}
            self.assertEqual(self.post("/api/reactions/match",json=body).status_code,422)

    def test_concerted_proton_and_acid_carbonyl_roles_are_public(self):
        body=self.body("C=C");r=self.options(body)["reactions"][0];body["reactionId"]=r["id"]
        d=self.post("/api/reactions/diagram",json=body).json;p=r["site"]["parameters"]
        step=d["mechanism"]["steps"][0]
        state={frozenset(b["atomMaps"]):b["order"] for b in step["state"]["bonds"]}
        self.assertEqual(state[frozenset((p["carbonylOxygen"],p["peracidHydrogen"]))],1)
        self.assertEqual(state[frozenset((p["acylCarbon"],p["proximalOxygen"]))],2)
        self.assertEqual(state[frozenset((p["acylCarbon"],p["carbonylOxygen"]))],1)
        self.assertIsNone(step["intermediate"]);self.assertEqual(len(step["electronMoves"]),4)

