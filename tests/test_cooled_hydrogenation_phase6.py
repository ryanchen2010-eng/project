"""Cooling Phase 6 v1: evidence boundary for the existing alkene/H2 model.

Net-product oracles below check existing chemistry, not cold experimental scope.
No new catalyst, cooled profile, reaction family or benchmark expectation is added.
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
PATHWAY = "Hydrogenation"
CANDIDATE = "cooled-alkene-hydrogenation-v1"
COLD = {"temperature": "cooled", "solvent": "dry", "catalyst": "metal"}
CASES = (
    ("ethene", "C=C", "CC"),
    ("long_chain", "C=CCCCC", "CCCCCC"),
    ("branched", "C=C(C)CC", "CCC(C)C"),
    ("cyclohexene_evidence_candidate", "C1=CCCCC1", "C1CCCCC1"),
    ("remote_alcohol", "C=CCCCO", "CCCCCO"),
    ("distant_center", "C=CC[C@H](C)CC", "CCC[C@H](C)CC"),
    ("specified_alkene", "CC/C=C/CC", "CCCCCC"),
    ("new_unassigned_center", "CC=C(C)CCC", "CCC(C)CCC"),
)


def canonical(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(mol)


def match(source="C=C", conditions=None, reagent="hydrogen", reverse=False):
    pair = ({"smiles": source}, reagent)
    if reverse:
        pair = pair[::-1]
    settings = COLD if conditions is None else conditions
    result = service.match_reactions(*pair, settings)
    return pair, result, [o for o in result["reactionOptions"] if o["mechanism"] == PATHWAY]


class CooledHydrogenationPhase6Tests(unittest.TestCase):
    def check_net(self, source, expected):
        for reverse in (False, True):
            pair, _, options = match(source, reverse=reverse)
            self.assertEqual(len(options), 1)
            o = options[0]
            self.assertEqual(canonical(o["productSmiles"]), canonical(expected))
            self.assertEqual(o["byproducts"], [])
            a = o["assessment"]
            self.assertFalse(a["canRun"])
            self.assertTrue(a["evidence"]["canPreview2D"])
            self.assertFalse(a["evidence"]["canGenerate3D"])
            self.assertEqual(a["cooling"]["reasonCodes"], ["unreviewed-cooled-pathway"])
            self.assertIsNone(a["cooling"]["modelId"])
            self.assertIn("No current selector combination qualifies cooled alkene-hydrogenation 3D", a["note"])
            self.assertIn("does not mean the reaction is impossible", a["note"])
            d = service.reaction_diagram(o["id"], *pair, COLD)
            self.assertEqual(d["assessment"], a)
            self.assertIn("<svg", d["svg"])
            self.assertIsNone(d["mechanism"])  # Net edits, not a resolved surface mechanism.
            before = [r for r in d["atoms"] if r["side"] == "reactants"]
            after = [r for r in d["atoms"] if r["side"] == "products"]
            inventory = lambda rows: {r["mapId"]: (r["element"], r["formalCharge"]) for r in rows}
            self.assertEqual(len(inventory(before)), len(before))
            self.assertEqual(inventory(before), inventory(after))
            self.assertEqual(sum(r["formalCharge"] for r in after), 0)
            h_slot = 0 if reverse else 1  # Calculator input slot; diagram species are reordered.
            h_species = next(i for i, r in enumerate(d["reactants"]) if r["formula"] == "H2")
            h_maps = {r["mapId"] for r in before if r["speciesIndex"] == h_species}
            self.assertEqual(len(h_maps), 2)
            self.assertTrue(all(inventory(before)[m] == ("H", 0) for m in h_maps))
            site = o["site"]["atomMaps"]
            edits = {(frozenset(r["atomMaps"]), r["before"], r["after"]) for r in d["changes"]}
            self.assertIn((frozenset(site), 2, 1), edits)
            self.assertIn((frozenset(h_maps), 1, None), edits)
            formed = [r for r in d["changes"] if r["before"] is None]
            self.assertEqual(len(formed), 2)
            self.assertEqual({m for r in formed for m in r["atomMaps"]}, set(site) | h_maps)
            self.assertTrue(all(len(set(r["atomMaps"]) & h_maps) == 1 for r in formed))
            self.assertEqual(len(edits), 4)
            self.assertEqual(set(o["compatibility"]["validation"].values()), {"verified"})
            amounts = o["stoichiometry"]
            self.assertTrue(amounts["balanced"])
            self.assertEqual([r["coefficient"] for r in amounts["reactants"]], [1, 1])
            self.assertEqual(amounts["product"]["coefficient"], 1)
            self.assertEqual(amounts["reactants"][h_slot]["molarMass"], 2.016)
            self.assertFalse(amounts["context"]["canGenerate3D"])
            with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before embedding")):
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(o["id"], *pair, COLD)
            ambient = {**COLD, "temperature": "ambient"}
            _, _, ordinary = match(source, ambient, reverse=reverse)
            self.assertEqual(o["id"], ordinary[0]["id"])
            for key in ("productSmiles", "compatibility", "site", "information"):
                self.assertEqual(o[key], ordinary[0][key])
            result = service.run_curated_reaction(o["id"], *pair, ambient)["product"]
            self.assertEqual(result["representation"], "3d")
            self.assertEqual(canonical(result["smiles"]), canonical(expected))
            self.assertEqual([(r["atomIndex"], r["mapId"], r["element"]) for r in after],
                             [(r["index"], r["mapId"], r["element"]) for r in result["atomLinks"]])

    def test_profile_registry_and_forged_client_metadata_fail_closed(self):
        self.assertEqual(SUITE_VERSION, 1)
        self.assertIsNone(reviewed_profile(CANDIDATE, PATHWAY))
        profiles = reviewed_manifest()["profiles"]
        self.assertEqual(len(profiles), 7)
        for p in profiles:
            if p['modelId'] == 'cooled-cyclohexene-pd-silica-v1':
                self.assertTrue(reviewed_profile(p['modelId'], PATHWAY).explicit_only)
            else:
                self.assertIsNone(reviewed_profile(p["modelId"], PATHWAY))
        pair, _, options = match()
        forged = copy.deepcopy(options[0]["assessment"])
        forged.update(canRun=True, coolingUnvalidated=False, coolingPolicy=CANDIDATE)
        forged["cooling"].update(modelId=CANDIDATE, status="supported-model", canGenerate3D=True, profileVersion=1)
        self.assertFalse(cooling_confidence(forged, COLD, {"mechanism": PATHWAY})["canRun"])
        for model in [CANDIDATE] + [p["modelId"] for p in profiles]:
            with self.assertRaises(service.ChemistryError):
                service.run_curated_reaction(options[0]["id"], *pair, {**COLD, "coolingProfile": model})

    def test_generic_metal_media_or_unrecognized_pressure_do_not_qualify(self):
        for medium in ("", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"):
            for catalyst in ("", "none", "metal", "lindlar", "acid", "radical"):
                settings = {**COLD, "solvent": medium, "catalyst": catalyst, "pressure": "1.1 MPa", "catalystSupport": "Pd/C"}
                pair, _, options = match(conditions=settings)
                self.assertTrue(options)
                for o in options:
                    self.assertFalse(o["assessment"]["canRun"])
                    self.assertIn("catalyst/support", o["assessment"]["note"])
                    self.assertIn("H2 pressure", o["assessment"]["note"])
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, settings)

    def test_competing_groups_and_unsupported_environments_remain_rejected(self):
        cases = (("C=CCO", "allylic/benzylic"), ("C=CC=C", "conjugated"), ("C=C=C", "cumulated"),
                 ("C=CCCC#C", "alkyne"), ("C=CCCC=O", "aldehyde"), ("C=CCC(=O)C", "ketone"),
                 ("C=CCCCOC", "ether"), ("C=Cc1ccccc1", "aromatic"), ("C=CCCCCl", "Cl at substrate atom"),
                 ("C1=CCC1", "4-membered"), ("C=C[C@H](C)CC", "at/adjacent"))
        for source, reason in cases:
            _, result, options = match(source)
            self.assertEqual(options, [], source)
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))

    def test_reagent_identity_cannot_be_replaced_by_name_or_isotope(self):
        for reagent in ("water", "hydroxide", "bromine", {"name": "Hydrogen", "smiles": "O"}):
            self.assertEqual(match(reagent=reagent)[2], [])
        with self.assertRaises(service.ChemistryError):
            match(reagent={"smiles": "[2H][2H]"})
        self.assertTrue(match(reagent={"name": "Untrusted display label", "smiles": "[H][H]"})[2])

    def test_distant_physical_stereo_retention_can_relabel_cip(self):
        o = match("C=CC[C@H](CC)CC(C)C")[2][0]
        self.assertEqual(canonical(o["productSmiles"]), canonical("CCC[C@H](CC)CC(C)C"))
        st = o["information"]["stereochemistry"]
        before, after = st["reactant"]["chiralCenters"][0], st["product"]["chiralCenters"][0]
        self.assertEqual(before["atomMap"], after["atomMap"])
        self.assertEqual((before["assignment"], after["assignment"]), ("R", "S"))
        self.assertFalse(o["assessment"]["canRun"])
        o = match("CC=C(C)CCC")[2][0]
        self.assertNotIn("@", o["productSmiles"])
        self.assertTrue(all(not c["specified"] for c in o["information"]["stereochemistry"]["product"]["chiralCenters"]))

    def test_independent_sites_and_unselected_ez_are_not_cold_selectivity(self):
        for source, products in (("C=CCCCCC=C", ("C=CCCCCCC", "C=CCCCCCC")),
                                 ("C/C=C/CC/C=C\\C", ("CCCCC/C=C\\C", "C/C=C/CCCCC"))):
            _, _, options = match(source)
            self.assertEqual(len(options), 2)
            self.assertEqual(len({o["id"] for o in options}), 2)
            self.assertEqual(sorted(o["productSmiles"] for o in options), sorted(canonical(p) for p in products))
            for o in options:
                self.assertFalse(o["assessment"]["canRun"])
                self.assertEqual(o["stoichiometry"]["reactants"][1]["coefficient"], 1)
                self.assertIn("not a prediction of selective partial conversion", o["conditions"])
                mol = Chem.MolFromSmiles(o["productSmiles"])
                self.assertEqual(sum(b.GetBondType() == Chem.BondType.DOUBLE for b in mol.GetBonds()), 1)
                if "/" in source:
                    self.assertEqual(len(o["information"]["stereochemistry"]["product"]["alkenes"]), 1)
                    self.assertTrue(o["information"]["stereochemistry"]["product"]["alkenes"][0]["specified"])

    def test_net_only_mechanism_does_not_claim_resolved_surface_chemistry(self):
        pair, _, options = match()
        o = options[0]
        self.assertEqual(o["information"]["capabilities"]["mappedMechanism"], "unsupported")
        self.assertIsNone(service.reaction_diagram(o["id"], *pair, COLD)["mechanism"])
        self.assertIn("syn face", " ".join(o["information"]["limitations"]))

    def test_authenticated_api_rechecks_cooling_after_an_ambient_run(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, password = "https://phase6-test.invalid", "Synthetic-phase6-test-fixture"
            app = create_app({"SESSION_SECRET": secrets.token_hex(32), "TRIAL_PASSWORD": password,
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda path, **kw: client.post(path, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": "ethene", "reactantB": "hydrogen", "conditions": {**COLD, "temperature": "ambient"}}
            self.assertEqual(post('/api/reactions/match', json=body).status_code, 401)
            self.assertEqual(post('/login', data={"password": password}).status_code, 303)
            o = post('/api/reactions/match', json=body).json['reactionOptions'][0]
            body['reactionId'] = o['id']
            self.assertEqual(post('/api/reactions/run', json=body).status_code, 200)
            body['conditions'] = {**COLD, "coolingProfile": CANDIDATE}
            matched = post('/api/reactions/match', json=body)
            self.assertEqual(matched.status_code, 200)
            self.assertFalse(matched.json['reactionOptions'][0]['assessment']['canRun'])
            d = post('/api/reactions/diagram', json=body)
            self.assertEqual(d.status_code, 200)
            self.assertIsNone(d.json['mechanism'])
            self.assertFalse(d.json['assessment']['evidence']['canGenerate3D'])
            with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Gate before embedding')):
                blocked = post('/api/reactions/run', json=body)
            self.assertEqual(blocked.status_code, 422)
            self.assertNotIn('product', blocked.json)


def add_case(source, expected):
    def test(self):
        self.check_net(source, expected)
    return test


for label, source, expected in CASES:
    setattr(CooledHydrogenationPhase6Tests, f"test_net_oracle_{label}", add_case(source, expected))


if __name__ == '__main__':
    unittest.main()
