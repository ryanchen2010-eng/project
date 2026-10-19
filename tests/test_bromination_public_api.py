"""Authenticated Phase 3C public workflow, synthetic local credentials only."""
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
class BrominationPublicApiTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix="br2-http-tests-")
        self.addCleanup(directory.cleanup)
        self.origin="https://br2-fixture.example.test"
        password="Synthetic-Br2-test-password"
        app=create_app({"TRIAL_PASSWORD":password,"SESSION_SECRET":"e374571857d7a740b3447c16980a238c5c7b6c45d8416cc1a9b72f148b543a6a",
                        "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test",
                        "DIST_DIR":Path(directory.name),"TESTING":True},chemistry_backend=chemistry)
        self.client=app.test_client()
        self.assertEqual(self.post("/login",data={"password":password}).status_code,303)

    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)
    def body(self,source="C/C=C\\C",conditions=None):
        return {"reactantA":{"smiles":source},"reactantB":"bromine","conditions":{"solvent":"dry"} if conditions is None else conditions}
    def options(self,body):
        response=self.post("/api/reactions/match",json=body)
        self.assertEqual(response.status_code,200)
        return response.json

    def test_z_pair_and_e_meso_with_real_diagrams_and_models(self):
        for source,count in [("C/C=C\\C",2),("C/C=C/C",1),("C1=CCCCC1",2)]:
            body=self.body(source);options=self.options(body)["reactions"]
            self.assertEqual(len(options),count)
            for r in options:
                body["reactionId"]=r["id"]
                d=self.post("/api/reactions/diagram",json=body);p=self.post("/api/reactions/run",json=body)
                self.assertEqual(d.status_code,200);self.assertEqual(p.status_code,200)
                self.assertEqual(p.json["product"]["smiles"],r["productSmiles"])
                after=[a for a in d.json["atoms"] if a["side"]=="products"]
                self.assertEqual([(a["atomIndex"],a["mapId"],a["element"]) for a in after],
                                 [(a["index"],a["mapId"],a["element"]) for a in p.json["product"]["atomLinks"]])
                self.assertIn(" C",r["site"]["label"])
                self.assertIsNone(d.json["mechanism"])

    def test_missing_or_nucleophilic_medium_cannot_run_a_dibromide(self):
        for medium in ["","aqueous-protic","ethanolic-protic","polar-aprotic"]:
            body=self.body(conditions={"solvent":medium})
            r=self.options(body)["reactions"][0];body["reactionId"]=r["id"]
            self.assertFalse(r["assessment"]["canRun"])
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            p=self.post("/api/reactions/run",json=body)
            self.assertEqual(p.status_code,422);self.assertNotIn("product",p.json)
            self.assertNotEqual(r["assessment"]["status"],"disfavored")

    def test_radical_change_and_forged_ids_cannot_reuse_old_product(self):
        body=self.body();previous=self.options(body)["reactions"][0]
        body["conditions"]["catalyst"]="radical"
        response=self.options(body)
        self.assertEqual(response["reactions"],[])
        self.assertIn("Radical Br2"," ".join(response["unsupportedReasons"]))
        body["reactionId"]=previous["id"]
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_remote_oxygen_supported_but_local_capture_rejected(self):
        for source in ["C=CCCCCCCCO","C=CCCCCCCCOC"]:
            self.assertEqual(len(self.options(self.body(source))["reactions"]),2)
        response=self.options(self.body("C=CCCCO"))
        self.assertEqual(response["reactions"],[])
        self.assertIn("intramolecular oxygen capture"," ".join(response["unsupportedReasons"]))

    def test_reversed_br2_slot_and_independent_multisite_choices(self):
        body=self.body("C=CCCCCCCCCC=CC")
        body["reactantA"],body["reactantB"]=body["reactantB"],body["reactantA"]
        options=self.options(body)["reactions"]
        self.assertEqual(len(options),3)
        for r in options:
            self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"Br2")
            body["reactionId"]=r["id"]
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
