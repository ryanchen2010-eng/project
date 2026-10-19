"""Authenticated public Phase 4D match, diagram and run route tests."""
import tempfile
import unittest
from pathlib import Path
from server import chemistry_server as chemistry
from server.production_app import create_app


class AlkyneHxPublicApiTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory(prefix="alkyne-hx-api-");self.addCleanup(folder.cleanup)
        self.origin="https://alkyne-hx.example.test"
        app=create_app({"TRIAL_PASSWORD":"Synthetic-HX-fixture-password", "SESSION_SECRET":"ef51105fa915b7a1fb533ab70fcba3bd4f11002d411fd7d18661b0f5f75497f8",
                        "PUBLIC_ORIGIN":self.origin,"FRAME_ANCESTORS":"https://frame.example.test","DIST_DIR":Path(folder.name),"TESTING":True},chemistry_backend=chemistry)
        self.client=app.test_client()
        self.assertEqual(self.post("/login",data={"password":"Synthetic-HX-fixture-password"}).status_code,303)

    def post(self,path,**kwargs):
        return self.client.post(path,base_url=self.origin,headers={"Origin":self.origin},**kwargs)

    def body(self,source="CCC#C",reagent="hydrogen-bromide",stage="one"):
        return {"reactantA":{"smiles":source},"reactantB":reagent,"conditions":{"solvent":"dry","temperature":"ambient","additionStage":stage}}

    def match(self,body):
        response=self.post("/api/reactions/match",json=body);self.assertEqual(response.status_code,200)
        return [r for r in response.json["reactionOptions"] if r["mechanism"]=="Alkyne hydrohalogenation"]

    def test_terminal_markovnikov_public_diagram_and_3d_identity(self):
        body=self.body();r=self.match(body)[0];body["reactionId"]=r["id"]
        self.assertEqual(r["productSmiles"],"C=C(Br)CC")
        diagram=self.post("/api/reactions/diagram",json=body);product=self.post("/api/reactions/run",json=body)
        self.assertEqual(diagram.status_code,200);self.assertEqual(product.status_code,200)
        self.assertIsNone(diagram.json["mechanism"])
        self.assertEqual([(a["atomIndex"],a["mapId"]) for a in diagram.json["atoms"] if a["side"]=="products"],
                         [(a["index"],a["mapId"]) for a in product.json["product"]["atomLinks"]])
        self.assertEqual(product.json["product"]["smiles"],r["productSmiles"])

    def test_internal_regioisomers_are_separate_and_first_stage_stays_unsigned(self):
        body=self.body("CC#CCC");found=self.match(body)
        self.assertEqual(len(found),2)
        self.assertEqual({r["productSmiles"] for r in found},{"CCC=C(C)Br","CC=C(Br)CC"})
        for r in found:
            body["reactionId"]=r["id"]
            self.assertIsNone(r["regioselectivity"]["ratios"])
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body["conditions"]["additionStage"]="two"
        found=self.match(body);self.assertEqual(len(found),2)
        for r in found:
            body["reactionId"]=r["id"]
            self.assertEqual(r["stoichiometry"]["reactants"][1]["coefficient"],2)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200)

    def test_hcl_and_hi_do_not_reuse_hbr_permissions(self):
        for reagent,stage,allowed in (("hydrogen-chloride","one",False),("hydrogen-chloride","two",False),
                                      ("hydrogen-iodide","one",True),("hydrogen-iodide","two",False)):
            body=self.body(reagent=reagent,stage=stage);r=self.match(body)[0];body["reactionId"]=r["id"]
            self.assertEqual(r["assessment"]["canRun"],allowed)
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200 if allowed else 422)

    def test_new_distant_stereo_and_conditional_oxygen_are_publicly_accessible(self):
        for source,allowed in (("C#CC[C@H](C)CC",True),("C#CCCCCCO",False),("C#CCCCCCOC",False)):
            body=self.body(source);body["reactantA"],body["reactantB"]=body["reactantB"],body["reactantA"]
            r=self.match(body)[0];body["reactionId"]=r["id"]
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,200 if allowed else 422)
        self.assertFalse(self.match(self.body("C#CCCCO")))

    def test_multiple_site_aliases_do_not_claim_selective_single_site_3d(self):
        body=self.body("C#CCCCCC#C");found=self.match(body)
        self.assertEqual(len(found),1);self.assertEqual(found[0]["optionIdentity"]["siteCount"],2)
        for identifier in found[0]["optionIdentity"]["sourceReactionIds"]:
            body["reactionId"]=identifier
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)

    def test_incomplete_or_changed_conditions_never_reuse_a_previous_3d_gate(self):
        body=self.body();body["reactionId"]=self.match(body)[0]["id"]
        for conditions in ({},{"additionStage":"one"},{"solvent":"dry","additionStage":"one"},
                           {"solvent":"dry","temperature":"ambient","additionStage":"one","catalyst":"radical"},
                           {"solvent":"aqueous-protic","temperature":"ambient","additionStage":"one"}):
            body["conditions"]=conditions
            self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,200)
            blocked=self.post("/api/reactions/run",json=body)
            self.assertEqual(blocked.status_code,422);self.assertNotIn("product",blocked.json)

    def test_wrong_stage_reagent_and_forged_ids_fail_closed(self):
        body=self.body();body["reactionId"]=self.match(body)[0]["id"]
        body["conditions"]["additionStage"]="two"
        self.assertEqual(self.post("/api/reactions/diagram",json=body).status_code,422)
        body=self.body();body["reactionId"]=self.match(body)[0]["id"];body["reactantB"]="bromine"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
        body=self.body();body["reactionId"]="not-a-reviewed-HX-site"
        self.assertEqual(self.post("/api/reactions/run",json=body).status_code,422)
