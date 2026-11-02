"""Batch 2 v1: independent negative contracts, not cold product evidence."""
import copy
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from rdkit import Chem

from server import chemistry_server as service
from server.production_app import create_app
from server.reaction_conditions import cooling_confidence
from server.reaction_temperature_profiles import reviewed_manifest


VERSION = 1
CASES = (
    # mechanism, substrate, reagent, model settings, expected connectivity,
    # reagent stoichiometry, existing mechanism display
    ("Chlorination", "C=CCCCC", "chlorine", {"solvent": "dry"}, "ClCC(Cl)CCCC", 1, None),
    ("Alkyne halogenation", "CCC#C", "bromine", {"solvent": "dry", "additionStage": "one"}, "CCC(Br)=CBr", 1, None),
    ("Alkyne halogenation", "CCC#C", "bromine", {"solvent": "dry", "additionStage": "two"}, "CCC(Br)(Br)C(Br)Br", 2, None),
    ("Alkyne halogenation", "CCC#C", "chlorine", {"solvent": "dry", "additionStage": "two"}, "CCC(Cl)(Cl)C(Cl)Cl", 2, None),
    ("SN2", "CBr", "hydroxide", {"solvent": "aqueous-protic"}, "CO", 1, "SN2"),
    ("SN1", "CC(C)(C)Cl", "water", {"solvent": "aqueous-protic"}, "CC(C)(C)O", 1, "SN1"),
    ("E1", "CC(C)(C)Cl", "water", {"solvent": "aqueous-protic"}, "C=C(C)C", None, "E1"),
    ("E2", "CCC(Br)C", "hydroxide", {"solvent": "aqueous-protic"}, "CC=CC", 1, "E2"),
)


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(molecule, isomericSmiles=False)


def matching(case, reverse=False):
    mechanism, source, reagent, settings, *_ = case
    pair = ({"smiles": source}, reagent)
    if reverse:
        pair = pair[::-1]
    conditions = {"temperature": "cooled", "catalyst": "none", **settings}
    result = service.match_reactions(*pair, conditions)
    options = [option for option in result["reactionOptions"] if option["mechanism"] == mechanism]
    return pair, conditions, options


class CoolingBatch2Boundaries(unittest.TestCase):
    def test_profile_registry_and_phase_r3_are_preserved(self):
        self.assertEqual(VERSION, 1)
        profiles = reviewed_manifest()["profiles"]
        self.assertEqual(len(profiles), 8)
        self.assertEqual({p["pathway"] for p in profiles},
                         {"Bromination", "Epoxidation", "Hydrogenation", "Alkene dihydroxylation", "Hydrohalogenation"})
        self.assertEqual(sum(p["pathway"] == "Alkene dihydroxylation" for p in profiles), 3)

    def test_each_candidate_stays_conditional_and_conserves_mapped_atoms(self):
        for case in CASES:
            mechanism, _, _, _, expected, coefficient, mechanism_type = case
            for reverse in (False, True):
                with self.subTest(pathway=mechanism, settings=case[3], reverse=reverse):
                    pair, conditions, options = matching(case, reverse)
                    self.assertTrue(options)
                    self.assertIn(canonical(expected), {canonical(o["productSmiles"]) for o in options})
                    for option in options:
                        assessment = option["assessment"]
                        self.assertFalse(assessment["canRun"])
                        self.assertTrue(assessment["evidence"]["canPreview2D"])
                        self.assertFalse(assessment["evidence"]["canGenerate3D"])
                        self.assertEqual(assessment["cooling"]["reasonCodes"], ["unreviewed-cooled-pathway"])
                        self.assertIn("does not mean the reaction is impossible", assessment["note"])
                        diagram = service.reaction_diagram(option["id"], *pair, conditions)
                        self.assertEqual(diagram["assessment"], assessment)
                        self.assertIn("<svg", diagram["svg"])
                        self.assertEqual(diagram["mechanism"]["type"] if diagram["mechanism"] else None,
                                         mechanism_type)
                        sides = [[a for a in diagram["atoms"] if a["side"] == side]
                                 for side in ("reactants", "products")]
                        inventories = [{a["mapId"]: a["element"] for a in atoms} for atoms in sides]
                        self.assertEqual([len(m) for m in inventories], [len(a) for a in sides])
                        self.assertEqual(*inventories)
                        self.assertEqual(*(sum(a["formalCharge"] for a in atoms) for atoms in sides))
                        stoich = option["stoichiometry"]
                        self.assertTrue(stoich["balanced"])
                        self.assertIn("not experimental yields", stoich["context"]["warning"])
                        if coefficient is not None:
                            slot = 0 if reverse else 1
                            self.assertEqual(stoich["reactants"][slot]["coefficient"], coefficient)
                        with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("cold gate")):
                            with self.assertRaises(service.ChemistryError):
                                service.run_curated_reaction(option["id"], *pair, conditions)

    def test_alkyne_equivalents_and_stereo_are_separate_net_models(self):
        for case, expected_order, expected_stereo in ((CASES[1], 2, "E"), (CASES[2], 1, None), (CASES[3], 1, None)):
            pair, conditions, options = matching(case)
            model = options[0]["alkyneHalogenModel"]
            self.assertEqual(model["selectedBondProductOrder"], expected_order)
            self.assertEqual(model["stereoAssignment"], expected_stereo)
            self.assertIsNone(model["ratios"])
            self.assertIn("net only", model["mechanism"])
            other = {**conditions, "additionStage": "two" if conditions["additionStage"] == "one" else "one"}
            with self.assertRaises(service.ChemistryError):
                service.reaction_diagram(options[0]["id"], *pair, other)

    def test_other_profile_and_stale_permission_do_not_authorize_candidates(self):
        existing = reviewed_manifest()["profiles"][0]
        for case in CASES:
            with self.subTest(pathway=case[0], settings=case[3]):
                pair, conditions, options = matching(case)
                original = options[0]
                forged = {**conditions, "conditionProfileId": existing["modelId"],
                          "conditionProfileVersion": str(existing["version"])}
                matches = [o for o in service.match_reactions(*pair, forged)["reactionOptions"]
                           if o["mechanism"] == case[0]]
                self.assertTrue(matches)
                self.assertTrue(all(not o["assessment"]["canRun"] for o in matches))
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(original["id"], *pair, forged)
                fake = copy.deepcopy(original["assessment"])
                fake.update(canRun=True, coolingUnvalidated=False, coolingPolicy=existing["modelId"])
                fake["cooling"].update(modelId=existing["modelId"], status="supported-model", canGenerate3D=True)
                checked = cooling_confidence(fake, service._conditions(conditions), {"mechanism": case[0]})
                self.assertFalse(checked["canRun"])

    def test_ambient_option_cannot_reuse_its_permission_after_cooling(self):
        for case in CASES[:4]:
            with self.subTest(pathway=case[0], settings=case[3]):
                pair, conditions, _ = matching(case)
                ambient = {**conditions, "temperature": "ambient"}
                options = [o for o in service.match_reactions(*pair, ambient)["reactionOptions"]
                           if o["mechanism"] == case[0]]
                self.assertTrue(options[0]["assessment"]["canRun"])
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("cold gate")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(options[0]["id"], *pair, conditions)

    def test_authenticated_public_endpoints_remain_conditional(self):
        with tempfile.TemporaryDirectory() as directory:
            origin = "https://batch2-test.invalid"
            password = "Synthetic-batch2-fixture-password"
            app = create_app({"SESSION_SECRET": secrets.token_hex(32), "TRIAL_PASSWORD": password,
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(directory), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()

            def post(path, **kwargs):
                return client.post(path, base_url=origin, headers={"Origin": origin}, **kwargs)

            self.assertEqual(post("/login", data={"password": password}).status_code, 303)
            for case in CASES:
                with self.subTest(pathway=case[0], settings=case[3]):
                    pair, conditions, _ = matching(case)
                    body = {"reactantA": pair[0], "reactantB": pair[1], "conditions": conditions}
                    response = post("/api/reactions/match", json=body)
                    self.assertEqual(response.status_code, 200)
                    options = [o for o in response.json["reactionOptions"] if o["mechanism"] == case[0]]
                    self.assertTrue(options)
                    body["reactionId"] = options[0]["id"]
                    diagram = post("/api/reactions/diagram", json=body)
                    self.assertEqual(diagram.status_code, 200)
                    self.assertFalse(diagram.json["assessment"]["evidence"]["canGenerate3D"])
                    with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("cold gate")):
                        blocked = post("/api/reactions/run", json=body)
                    self.assertEqual(blocked.status_code, 422)
                    self.assertNotIn("product", blocked.json)


if __name__ == "__main__":
    unittest.main()
