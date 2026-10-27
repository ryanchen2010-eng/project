"""Cooling Phase 4 v1: an evidence boundary, not a new cooled Cl2 profile.

Product oracles verify the existing conditional net model. They are not claims
that the reviewed cold experimental formulations give these exclusive outcomes.
"""
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
from server.reaction_temperature_profiles import reviewed_manifest, reviewed_profile


SUITE_VERSION = 1
PATHWAY = "Chlorination"
CANDIDATE = "cooled-alkene-chlorination-v1"
COLD = {"temperature": "cooled", "solvent": "dry", "catalyst": "none"}
CASES = (
    ("ethene", "C=C", ("ClCCCl",), 1),
    ("hexene_evidence_substrate", "C=CCCCC", ("ClCC(Cl)CCCC",), 2),
    ("branched", "C=CC(C)C", ("ClCC(Cl)C(C)C",), 2),
    ("e_butene", "C/C=C/C", ("CC(Cl)C(Cl)C",), 1),
    ("z_butene", "C/C=C\\C", ("CC(Cl)C(Cl)C",), 2),
    ("cyclic", "C1=CCCCC1", ("ClC1CCCCC1Cl",), 2),
    ("styrene", "C=Cc1ccccc1", ("ClCC(Cl)c1ccccc1",), 2),
    ("distant_stereo", "C=CCC[C@H](C)CCC(C)(C)C", ("ClCC(Cl)CC[C@H](C)CCC(C)(C)C",), 2),
    ("separated_sites", "C=CCCCCCCCCC=CC", ("ClCC(Cl)CCCCCCCCC=CC", "C=CCCCCCCCCC(Cl)C(Cl)C"), 3),
)


def canonical(smiles, stereo=False):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(molecule, isomericSmiles=stereo)


def match(source="C=CCCCC", conditions=None, reagent="chlorine", reverse=False):
    pair = ({"smiles": source}, reagent)
    if reverse:
        pair = pair[::-1]
    result = service.match_reactions(*pair, COLD if conditions is None else conditions)
    return pair, result, [r for r in result["reactionOptions"] if r["mechanism"] == PATHWAY]


class CooledChlorinationPhase4Tests(unittest.TestCase):
    def check_net_case(self, source, expected, count):
        for reverse in (False, True):
            pair, result, options = match(source, reverse=reverse)
            self.assertEqual(result["supportState"], "Conditional")
            self.assertEqual(len(options), count)
            self.assertEqual({canonical(o["productSmiles"]) for o in options}, {canonical(s) for s in expected})
            ambient = {**COLD, "temperature": "ambient"}
            _, _, ordinary = match(source, ambient, reverse=reverse)
            self.assertEqual({o["id"]: (o["productSmiles"], o["stereochemistry"], o["chlorinationStereo"]) for o in options},
                             {o["id"]: (o["productSmiles"], o["stereochemistry"], o["chlorinationStereo"]) for o in ordinary})
            for o in options:
                a = o["assessment"]
                self.assertFalse(a["canRun"])
                self.assertFalse(a["evidence"]["canGenerate3D"])
                self.assertTrue(a["evidence"]["canPreview2D"])
                self.assertEqual(a["cooling"]["reasonCodes"], ["unreviewed-cooled-pathway"])
                self.assertIsNone(a["cooling"]["modelId"])
                self.assertIn("No current dropdown combination qualifies cooled Cl2 3D", a["note"])
                self.assertIn("does not mean the reaction is impossible", a["note"])
                self.assertIn("light or atmosphere", a["note"])
                self.assertEqual(o["byproducts"], [])
                self.assertIsNone(o["chlorinationStereo"]["ratios"])
                self.assertNotIn("guidedConditions", o)
                d = service.reaction_diagram(o["id"], *pair, COLD)
                self.assertEqual(d["assessment"], a)
                self.assertIsNone(d["mechanism"], "Net bond edits are not a resolved chloronium mechanism")
                self.assertIn("<svg", d["svg"])
                before = [r for r in d["atoms"] if r["side"] == "reactants"]
                after = [r for r in d["atoms"] if r["side"] == "products"]
                inventory = lambda rows: {r["mapId"]: (r["element"], r["formalCharge"]) for r in rows}
                self.assertEqual(inventory(before), inventory(after))
                self.assertEqual(len(inventory(before)), len(before))
                p = o["site"]["parameters"]
                # Diagram species order is substrate/reagent, not UI input order.
                chlorine_species = next(i for i, r in enumerate(d["reactants"]) if r["formula"] == "Cl2")
                chlorine_slot = 0 if reverse else 1
                self.assertEqual({r["mapId"] for r in before if r["speciesIndex"] == chlorine_species}, set(p["chlorines"]))
                self.assertEqual({r["element"] for r in before if r["speciesIndex"] == chlorine_species}, {"Cl"})
                x, y = p["alkene"]
                u, v = p["chlorines"]
                edits = {(frozenset(r["atomMaps"]), r["before"], r["after"]) for r in d["changes"]}
                self.assertEqual(edits, {(frozenset((x, y)), 2, 1), (frozenset((u, v)), 1, None),
                                         (frozenset((x, u)), None, 1), (frozenset((y, v)), None, 1)})
                amounts = o["stoichiometry"]
                self.assertTrue(amounts["balanced"])
                self.assertEqual([r["coefficient"] for r in amounts["reactants"]], [1, 1])
                self.assertEqual(amounts["product"]["coefficient"], 1)
                self.assertFalse(amounts["context"]["canGenerate3D"])
                self.assertAlmostEqual(amounts["reactants"][chlorine_slot]["molarMass"], 70.906, places=3)
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before embedding")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, COLD)
                product = service.run_curated_reaction(o["id"], *pair, ambient)["product"]
                self.assertEqual(product["representation"], "3d")
                self.assertEqual(product["smiles"], o["productSmiles"])
                self.assertEqual([(r["atomIndex"], r["mapId"], r["element"]) for r in after],
                                 [(r["index"], r["mapId"], r["element"]) for r in product["atomLinks"]])

    def test_no_cl2_profile_or_borrowed_bromine_permission(self):
        self.assertEqual(SUITE_VERSION, 1)
        self.assertIsNone(reviewed_profile(CANDIDATE, PATHWAY))
        profiles = reviewed_manifest()["profiles"]
        self.assertEqual(len(profiles), 7)
        self.assertEqual({p["pathway"] for p in profiles}, {"Bromination", "Epoxidation", "Hydrogenation", "Alkene dihydroxylation"})
        for p in profiles:
            self.assertIsNone(reviewed_profile(p["modelId"], PATHWAY))
        pair, _, options = match()
        forged = copy.deepcopy(options[0]["assessment"])
        forged.update(canRun=True, coolingPolicy=CANDIDATE, coolingUnvalidated=False)
        forged["cooling"].update(modelId=CANDIDATE, status="supported-model", canGenerate3D=True, profileVersion=1)
        self.assertFalse(cooling_confidence(forged, COLD, {"mechanism": PATHWAY})["canRun"])
        with self.assertRaises(service.ChemistryError):
            service.run_curated_reaction(options[0]["id"], *pair, {**COLD, "coolingProfile": CANDIDATE})

    def test_no_generic_medium_or_added_activation_qualifies_cooled_cl2(self):
        for medium in ("", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"):
            for catalyst in ("", "none", "acid", "metal"):
                settings = {**COLD, "solvent": medium, "catalyst": catalyst}
                pair, _, options = match(conditions=settings)
                self.assertTrue(options)
                for o in options:
                    self.assertFalse(o["assessment"]["canRun"])
                    self.assertIn("No current dropdown combination", o["assessment"]["note"])
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, settings)

    def test_cold_does_not_approve_radical_or_oxygen_and_diene_capture_cases(self):
        _, result, options = match(conditions={**COLD, "catalyst": "radical"})
        self.assertEqual(options, [])
        self.assertIn("Radical Cl2", " ".join(result["unsupportedReasons"]))
        for source in ("C=CCO", "C=CCCCCCCCO", "C=CCCCCCCCOC", "C=CCCCCC=C", "C/C=C/c1ccccc1", "C=CC=C"):
            _, result, options = match(source)
            self.assertEqual(options, [], source)
            self.assertTrue(result["unsupportedReasons"], source)

    def test_named_wrong_reagents_cannot_borrow_actual_cl2_identity(self):
        for reagent in ("hydrogen-chloride", {"name": "Chlorine", "smiles": "OCl"}, {"name": "Chlorine", "smiles": "BrCl"}):
            self.assertEqual(match(reagent=reagent)[2], [])

    def test_existing_relative_and_distant_stereo_are_conditional_not_cold_predictions(self):
        def local(o):
            return tuple(c["assignment"] for c in sorted(o["stereochemistry"]["product"]["chiralCenters"], key=lambda c: c["atomMap"])
                         if c["atomMap"] in o["site"]["atomMaps"])
        self.assertEqual({frozenset(local(o)) for o in match("C/C=C/C")[2]}, {frozenset(("R", "S"))})
        self.assertEqual({local(o) for o in match("C/C=C\\C")[2]}, {("R", "R"), ("S", "S")})
        self.assertTrue(all(o["chlorinationStereo"]["productRingRelationship"] == "trans Cl/Cl" for o in match("C1=CCCCC1")[2]))
        for o in match("C=CCC[C@H](C)CCC(C)(C)C")[2]:
            old = o["stereochemistry"]["reactant"]["chiralCenters"][0]
            new = next(c for c in o["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"] == old["atomMap"])
            self.assertEqual((old["assignment"], new["assignment"]), ("S", "R"))
            self.assertFalse(o["assessment"]["canRun"], "CIP relabeling must not grant cold confidence")

    def test_authenticated_match_diagram_and_stale_ambient_run_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            origin = "https://phase4-test.invalid"
            password = "Synthetic-phase4-test-fixture"
            app = create_app({"SESSION_SECRET": secrets.token_hex(32), "TRIAL_PASSWORD": password,
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda path, **kw: client.post(path, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "C=CCCCC"}, "reactantB": "chlorine", "conditions": {**COLD, "temperature": "ambient"}}
            self.assertEqual(post('/api/reactions/match', json=body).status_code, 401)
            self.assertEqual(post('/login', data={"password": password}).status_code, 303)
            o = post('/api/reactions/match', json=body).json['reactionOptions'][0]
            self.assertTrue(o['assessment']['canRun'])
            body.update(reactionId=o['id'], conditions=COLD)
            cold = post('/api/reactions/match', json=body)
            self.assertEqual(cold.status_code, 200)
            self.assertFalse(cold.json['reactionOptions'][0]['assessment']['canRun'])
            preview = post('/api/reactions/diagram', json=body)
            self.assertEqual(preview.status_code, 200)
            self.assertIsNone(preview.json['mechanism'])
            self.assertIn('conditional', preview.json['assessment']['evidence']['assertionLevel'])
            with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Gate before embedding')):
                blocked = post('/api/reactions/run', json=body)
            self.assertEqual(blocked.status_code, 422)
            self.assertNotIn('product', blocked.json)


def add_case(source, expected, count):
    def test(self):
        self.check_net_case(source, expected, count)
    return test


for label, source, expected, count in CASES:
    setattr(CooledChlorinationPhase4Tests, f"test_net_oracle_{label}", add_case(source, expected, count))


if __name__ == '__main__':
    unittest.main()
