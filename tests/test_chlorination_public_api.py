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
class ChlorinationPublicApiTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory(prefix="cl2-http-tests-")
        self.addCleanup(directory.cleanup)
        self.origin="https://cl2-fixture.example.test"
        password="Synthetic-Cl2-test-password"
        app=create_app({"TRIAL_PASSWORD":password,"SESSION_SECRET":"e374571857d7a740b3447c16980a238c5c7b6c45d8416cc1a9b72f148b543a6a",
                        "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test",
                        "DIST_DIR":Path(directory.name),"TESTING":True},chemistry_backend=chemistry)
        self.client=app.test_client()
        self.assertEqual(self.post("/login",data={"password":password}).status_code,303)

    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)
    def body(self,source="C/C=C\\C",conditions=None):
        return {"reactantA":{"smiles":source},"reactantB":"chlorine","conditions":{"solvent":"dry"} if conditions is None else conditions}
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

    def test_missing_or_nucleophilic_medium_cannot_run_a_dichloride(self):
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
        self.assertIn("Radical Cl2"," ".join(response["unsupportedReasons"]))
        body["reactionId"]=previous["id"]
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_oxygen_cases_fail_closed_without_changing_bromine(self):
        for source in ["C=CCCCCCCCO","C=CCCCCCCCOC","C=CCCCO"]:
            body=self.body(source)
            response=self.options(body)
            self.assertEqual(response["reactions"],[])
            self.assertTrue(response["unsupportedReasons"])
            body["reactantB"]="bromine"
            if source!="C=CCCCO":
                self.assertEqual(len(self.options(body)["reactions"]),2)

    def test_reversed_cl2_slot_and_independent_multisite_choices(self):
        body=self.body("C=CCCCCCCCCC=CC")
        body["reactantA"],body["reactantB"]=body["reactantB"],body["reactantA"]
        options=self.options(body)["reactions"]
        self.assertEqual(len(options),3)
        for r in options:
            self.assertEqual(r["stoichiometry"]["reactants"][0]["formula"],"Cl2")
            body["reactionId"]=r["id"]
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_distant_stereo_cip_flip_retains_exact_mapped_configuration(self):
        body=self.body("C=CCC[C@H](C)CCC(C)(C)C")
        for r in self.options(body)["reactions"]:
            before=r["stereochemistry"]["reactant"]["chiralCenters"][0]
            after=next(c for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"]==before["atomMap"])
            self.assertEqual((before["assignment"],after["assignment"]),("S","R"))
            body["reactionId"]=r["id"]
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_17_octadiene_and_internal_aryl_remain_outside_model(self):
        for source in ["C=CCCCCC=C","C/C=C/c1ccccc1"]:
            response=self.options(self.body(source))
            self.assertEqual(response["reactions"],[])
            self.assertTrue(response["unsupportedReasons"])

    def test_conditions_and_inputs_do_not_reuse_another_run(self):
        body=self.body("C=CC")
        r=self.options(body)["reactions"][0]
        body["reactionId"]=r["id"]
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
        body["conditions"]={"solvent":"aqueous-protic"}
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body["conditions"]={"solvent":"dry"}
        body["reactantB"]="hydrogen-chloride"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

