"""Phase 3 evidence-gate contracts, not approval of a cooled Os/H2O2 profile.

The source/formulation/release review is unresolved. Independent net-product
oracles below verify existing 2D chemistry, not experimental cold outcomes.
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
PATHWAY = "Alkene dihydroxylation"
CANDIDATE = "cooled-osmium-peroxide-diol-v1"
COOLED = {"temperature": "cooled", "solvent": "dry", "catalyst": "osmium", "workup": "aqueous-release"}
CASES = (
    ("ethene", "C=C", "OCCO"),
    ("isobutylene_lead", "C=C(C)C", "OCC(O)(C)C"),
    ("identical_ethyl_substituents", "C=C(CC)CC", "OCC(O)(CC)CC"),
    ("tetramethylethylene", "CC(C)=C(C)C", "CC(O)(C)C(O)(C)C"),
)


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(molecule)


def match(source="C=C(C)C", conditions=None, reagent="hydrogen-peroxide", reverse=False):
    pair = ({"smiles": source}, reagent)
    if reverse:
        pair = pair[::-1]
    settings = COOLED if conditions is None else conditions
    result = service.match_reactions(*pair, settings)
    return pair, result, [r for r in result["reactionOptions"] if r["mechanism"] == PATHWAY]


class CooledDihydroxylationEvidenceGateTests(unittest.TestCase):
    def check_net_case(self, source, expected):
        for reverse in (False, True):
            pair, result, options = match(source, reverse=reverse)
            self.assertEqual(result["supportState"], "Conditional")
            self.assertEqual(len(options), 1)
            option = options[0]
            self.assertEqual(canonical(option["productSmiles"]), canonical(expected))
            self.assertEqual(option["byproducts"], [])
            self.assertEqual(option["dihydroxylationStereo"]["assignedAtomMaps"], [])
            self.assertEqual(option["dihydroxylationStereo"]["outcome"], "no local stereocenters")
            self.assertIsNone(option["dihydroxylationStereo"]["ratios"])
            a = option["assessment"]
            self.assertFalse(a["canRun"])
            self.assertFalse(a["evidence"]["canGenerate3D"])
            self.assertTrue(a["evidence"]["canPreview2D"])
            self.assertEqual(a["cooling"]["reasonCodes"], ["unreviewed-cooled-pathway"])
            self.assertIsNone(a["cooling"]["modelId"])
            self.assertIn("Solvent-specific", a["factors"]["solvent"]["explanation"])
            self.assertIn("does not mean the reaction is impossible", a["note"])
            self.assertFalse(a["workupRepresented"])
            self.assertTrue(a["workupAssumptionConfirmed"])
            if canonical(source) == 'C=C(C)C':
                self.assertEqual(option['guidedConditions']['profileId'],'cooled-isobutylene-os-peroxide-v1')
                self.assertTrue(option['guidedConditions']['requireConfirmation'])
            else:
                self.assertNotIn("guidedConditions", option)

            d = service.reaction_diagram(option["id"], *pair, COOLED)
            self.assertEqual(d["assessment"], a)
            self.assertIsNone(d["mechanism"], "Formal atom bookkeeping is not a resolved Os catalytic mechanism")
            self.assertEqual(len(d["products"]), 1)
            self.assertEqual(canonical(d["products"][0]["smiles"]), canonical(expected))
            before = [r for r in d["atoms"] if r["side"] == "reactants"]
            after = [r for r in d["atoms"] if r["side"] == "products"]
            inventory = lambda rows: {r["mapId"]: (r["element"], r["formalCharge"]) for r in rows}
            self.assertEqual(inventory(before), inventory(after))
            self.assertEqual(len(inventory(before)), len(before))
            p = d["site"]["parameters"]
            x, y = p["alkene"]
            u, v = p["oxygens"]
            edits = {(frozenset(r["atomMaps"]), r["before"], r["after"]) for r in d["changes"]}
            self.assertEqual(edits, {(frozenset((x, y)), 2, 1), (frozenset((u, v)), 1, None),
                                     (frozenset((x, u)), None, 1), (frozenset((y, v)), None, 1)})
            self.assertIn("formal net bookkeeping", p["provenanceModel"])
            donor_maps = {r["mapId"] for r in before if r["speciesIndex"] == 1}
            self.assertTrue(set(p["oxygens"] + p["hydroxylHydrogens"]) <= donor_maps)

            amounts = option["stoichiometry"]
            self.assertTrue(amounts["balanced"])
            self.assertEqual([r["coefficient"] for r in amounts["reactants"]], [1, 1])
            self.assertEqual(amounts["product"]["coefficient"], 1)
            oxidant = next(r for r in amounts["reactants"] if r["formula"] == "H2O2")
            self.assertAlmostEqual(oxidant["molarMass"], 34.014, places=3)
            self.assertFalse(amounts["context"]["canGenerate3D"])
            with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Must gate before embedding")):
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(option["id"], *pair, COOLED)

            ambient = {**COOLED, "temperature": "ambient"}
            _, _, ordinary = match(source, ambient, reverse=reverse)
            self.assertEqual({r["productSmiles"] for r in ordinary}, {r["productSmiles"] for r in options})
            product = service.run_curated_reaction(ordinary[0]["id"], *pair, ambient)["product"]
            self.assertEqual(product["representation"], "3d")
            self.assertEqual({r["mapId"] for r in product["atomLinks"]}, set(inventory(after)))

    def test_candidate_is_not_registered_or_borrowed_from_epoxidation(self):
        self.assertEqual(SUITE_VERSION, 1)
        self.assertIsNone(reviewed_profile(CANDIDATE, PATHWAY))
        manifest = reviewed_manifest()["profiles"]
        self.assertEqual(len(manifest), 7)
        self.assertEqual({p["pathway"] for p in manifest}, {"Bromination", "Epoxidation", "Hydrogenation", "Alkene dihydroxylation"})
        for p in manifest:
            if p['pathway'] == PATHWAY:
                self.assertTrue(reviewed_profile(p['modelId'], PATHWAY).explicit_only)
            else:
                self.assertIsNone(reviewed_profile(p["modelId"], PATHWAY))

    def test_no_generic_medium_or_missing_activation_can_qualify_cooling(self):
        for medium in ("", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"):
            for extra in ({}, {"catalyst": "none"}, {"workup": ""}, {"catalyst": "acid"}, {"futureProfile": CANDIDATE}):
                conditions = {**COOLED, "solvent": medium, **extra}
                pair, _, options = match(conditions=conditions)
                self.assertTrue(options)
                for o in options:
                    self.assertFalse(o["assessment"]["canRun"])
                    self.assertFalse(o["stoichiometry"]["context"]["canGenerate3D"])
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, conditions)
                    if extra.get("catalyst") == "none":
                        self.assertIn("catalyst", o["assessment"]["missingSettings"])
                    if extra.get("workup") == "":
                        self.assertIn("workup", o["assessment"]["missingSettings"])

    def test_internal_geometry_and_remote_stereo_are_not_rewritten_by_cooling(self):
        for source in ("C/C=C/C", "C/C=C\\C", "C=Cc1ccccc1", "C=CCCC[C@H](C)CC", "C=CCCCCC=C"):
            _, _, cooled = match(source)
            _, _, ambient = match(source, {**COOLED, "temperature": "ambient"})
            self.assertTrue(cooled)
            self.assertEqual({r["id"]: (r["productSmiles"], r["stereochemistry"], r["dihydroxylationStereo"]) for r in cooled},
                             {r["id"]: (r["productSmiles"], r["stereochemistry"], r["dihydroxylationStereo"]) for r in ambient})
            self.assertTrue(all(not r["assessment"]["canRun"] for r in cooled))

    def test_other_oxidants_and_reactive_environments_remain_excluded(self):
        for reagent in ({"smiles": "COO"}, {"smiles": "O", "name": "hydrogen peroxide"}):
            self.assertFalse(match(reagent=reagent)[2])
        with self.assertRaisesRegex(service.ChemistryError, "neutral"):
            match(reagent={"smiles": "C[N+]1([O-])CCOCC1"})
        for source in ("C=CO", "C=CCO", "C=CC=C", "C=C(C=O)C", "C=CN", "C1=CC1"):
            self.assertFalse(match(source)[2], source)

    def test_stale_ambient_option_and_forged_candidate_metadata_do_not_grant_permission(self):
        ambient = {**COOLED, "temperature": "ambient"}
        pair, _, options = match(conditions=ambient)
        self.assertTrue(options[0]["assessment"]["canRun"])
        with self.assertRaises(service.ChemistryError):
            service.run_curated_reaction(options[0]["id"], *pair, COOLED)
        forged = copy.deepcopy(options[0]["assessment"])
        forged.update(coolingPolicy=CANDIDATE, coolingUnvalidated=False)
        forged["cooling"] = {"version": 1, "registryVersion": 1, "profileVersion": 1, "modelId": CANDIDATE,
                             "pathway": PATHWAY, "status": "supported-model", "canGenerate3D": True, "reasonCodes": []}
        result = cooling_confidence(forged, COOLED, {"mechanism": PATHWAY})
        self.assertFalse(result["canRun"])
        self.assertFalse(result["evidence"]["canGenerate3D"])

    def test_authenticated_public_api_keeps_conditional_preview_and_rejects_run(self):
        with tempfile.TemporaryDirectory() as folder:
            origin = "https://phase3-test.invalid"
            app = create_app({"SESSION_SECRET": secrets.token_hex(32), "TRIAL_PASSWORD": "Synthetic-phase3-fixture",
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda path, **kw: client.post(path, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "C=C(C)C"}, "reactantB": {"smiles": "OO"}, "conditions": COOLED}
            self.assertEqual(post('/api/reactions/match', json=body).status_code, 401)
            self.assertEqual(post('/login', data={"password": "Synthetic-phase3-fixture"}).status_code, 303)
            matched = post('/api/reactions/match', json=body)
            self.assertEqual(matched.status_code, 200)
            o = next(r for r in matched.json['reactionOptions'] if r['mechanism'] == PATHWAY)
            self.assertFalse(o['assessment']['canRun'])
            body['reactionId'] = o['id']
            preview = post('/api/reactions/diagram', json=body)
            self.assertEqual(preview.status_code, 200)
            self.assertIsNone(preview.json['mechanism'])
            blocked = post('/api/reactions/run', json=body)
            self.assertEqual(blocked.status_code, 422)
            self.assertNotIn('product', blocked.json)


def add_case(source, expected):
    def test(self):
        self.check_net_case(source, expected)
    return test


for label, source, expected in CASES:
    setattr(CooledDihydroxylationEvidenceGateTests, f"test_net_oracle_{label}", add_case(source, expected))


if __name__ == '__main__':
    unittest.main()
