"""Authenticated public routes exercise the real Phase 4C workflow."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
from server.production_app import create_app


class AlkyneHalogenationPublicApiTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory(prefix="alkyne-x2-api-"); self.addCleanup(folder.cleanup)
        self.origin="https://alkyne-x2.example.test"
        app=create_app({"TRIAL_PASSWORD":"Synthetic-X2-test-password", "SESSION_SECRET":"b41d0e76f1b249cd9e4e18c8c832fca57669cb64e3329bec634fbb5d58a21b47",
                        "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test", "DIST_DIR":Path(folder.name),"TESTING":True}, chemistry_backend=chemistry)
        self.client=app.test_client()
        self.assertEqual(self.post("/login",data={"password":"Synthetic-X2-test-password"}).status_code,303)

    def post(self,path,**kwargs):
        return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)

    def body(self, source="CCC#C", reagent="bromine", stage="one"):
        return {"reactantA":{"smiles":source},"reactantB":reagent,"conditions":{"solvent":"dry","additionStage":stage}}

    def match(self,body):
        result=self.post("/api/reactions/match",json=body)
        self.assertEqual(result.status_code,200)
        return [r for r in result.json["reactionOptions"] if r["mechanism"]=="Alkyne halogenation"]

    def test_br_first_stage_e_product_diagram_and_exact_3d_links(self):
        body=self.body(); r=self.match(body)[0]; body["reactionId"]=r["id"]
        self.assertEqual(r["productSmiles"],"CC/C(Br)=C\\Br")
        d=self.post("/api/reactions/diagram",json=body); p=self.post("/api/reactions/run",json=body)
        self.assertEqual(d.status_code,200); self.assertEqual(p.status_code,200)
        self.assertIsNone(d.json["mechanism"])
        self.assertEqual(p.json["product"]["smiles"],r["productSmiles"])
        self.assertEqual([(a["atomIndex"],a["mapId"]) for a in d.json["atoms"] if a["side"]=="products"],
                         [(a["index"],a["mapId"]) for a in p.json["product"]["atomLinks"]])

    def test_two_equivalents_have_four_incoming_atoms_and_no_local_ez(self):
        for reagent, symbol in (("bromine","Br"),("chlorine","Cl")):
            body=self.body(reagent=reagent,stage="two"); r=self.match(body)[0]; body["reactionId"]=r["id"]
            self.assertEqual(r["stoichiometry"]["reactants"][1]["coefficient"],2)
            d=self.post("/api/reactions/diagram",json=body)
            self.assertEqual(d.status_code,200)
            self.assertEqual(len(d.json["bondsFormed"]),4); self.assertEqual(len(d.json["bondsBroken"]),2)
            self.assertEqual(r["alkyneHalogenModel"]["halogen"],symbol)
            self.assertIsNone(r["alkyneHalogenModel"]["stereoAssignment"])
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_chlorine_first_stage_is_not_bromine_stereochemistry(self):
        body=self.body(reagent="chlorine"); r=self.match(body)[0]; body["reactionId"]=r["id"]
        self.assertFalse(r["assessment"]["canRun"]); self.assertNotIn("Br",r["productSmiles"])
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
        blocked=self.post("/api/reactions/run",json=body)
        self.assertEqual(blocked.status_code,422); self.assertNotIn("product",blocked.json)

    def test_conditions_and_stage_changes_cannot_reuse_old_permission(self):
        body=self.body(); body["reactionId"]=self.match(body)[0]["id"]
        for conditions in ({},{"additionStage":"one"},{"solvent":"dry"},
                           {"solvent":"aqueous-protic","additionStage":"one"},
                           {"solvent":"dry","additionStage":"one","catalyst":"radical"}):
            body["conditions"]=conditions
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body["conditions"]={"solvent":"dry","additionStage":"two"}
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,422)

    def test_symmetric_sites_keep_each_original_mapped_alias(self):
        body=self.body("C#CCCCCC#C"); found=self.match(body)
        self.assertEqual(len(found),1); self.assertEqual(found[0]["optionIdentity"]["siteCount"],2)
        for identifier in found[0]["optionIdentity"]["sourceReactionIds"]:
            body["reactionId"]=identifier
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_new_remote_oxygen_and_distant_stereo_use_public_routes(self):
        for source in ("C#CCCCCCO","C#CCCCCCOC","C#CC[C@H](C)CC"):
            body=self.body(source); body["reactantA"],body["reactantB"]=body["reactantB"],body["reactantA"]
            found=self.match(body); self.assertEqual(len(found),1)
            body["reactionId"]=found[0]["id"]
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)
        self.assertFalse(self.match(self.body("C#CCCCO")))

    def test_wrong_reagent_and_invalid_conditions_are_not_accepted(self):
        body=self.body(); body["reactionId"]=self.match(body)[0]["id"]
        body["reactantB"]="hydrogen-bromide"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body=self.body(); body["conditions"]["additionStage"]="three"
        self.assertEqual(self.post("/api/reactions/match",json=body).status_code,422)
