"""Cooling Phase 5 v1: SN2 evidence boundary, not a new cold profile.

These independent net products test preservation of existing chemistry, not
experimental product isolation or selective conversion at low temperature.
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
PATHWAY = "SN2"
CANDIDATE = "cooled-hydroxide-sn2-v1"
COLD = {"temperature": "cooled", "solvent": "polar-aprotic", "catalyst": "none"}
CASES = (
    ("methyl_bromide", "CBr", ("CO",)),
    ("methyl_iodide", "CI", ("CO",)),
    ("methyl_chloride", "CCl", ("CO",)),
    ("long_primary", "CCCCCCCCCl", ("CCCCCCCCO",)),
    ("benzylic", "BrCc1ccccc1", ("OCc1ccccc1",)),
    ("reacting_center", "C[C@H](Br)CC", ("C[C@@H](O)CC",)),
    ("distant_cip_relabel", "C[C@H](CCOC)CCBr", ("C[C@H](CCOC)CCO",)),
    ("remote_ether", "BrCCCCOC", ("OCCCCOC",)),
    ("remote_alcohol", "BrCCCCCCCCO", ("OCCCCCCCCO",)),
    ("multiple_sites", "ClCCCBr", ("OCCCBr", "ClCCCO")),
)


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(molecule)


def match(source="CBr", conditions=None, reagent="hydroxide", reverse=False):
    pair = ({"smiles": source}, reagent)
    if reverse:
        pair = pair[::-1]
    result = service.match_reactions(*pair, COLD if conditions is None else conditions)
    return pair, result, [o for o in result["reactionOptions"] if o["mechanism"] == PATHWAY]


class CooledSN2Phase5Tests(unittest.TestCase):
    def check_case(self, source, expected):
        for reverse in (False, True):
            pair, _, options = match(source, reverse=reverse)
            self.assertEqual(len(options), len(expected))
            self.assertEqual({canonical(o["productSmiles"]) for o in options}, {canonical(s) for s in expected})
            ambient = {**COLD, "temperature": "ambient"}
            _, _, ordinary = match(source, ambient, reverse=reverse)
            self.assertEqual({o["id"]: (o["productSmiles"], o["compatibility"], o["information"]["stereochemistry"]) for o in options},
                             {o["id"]: (o["productSmiles"], o["compatibility"], o["information"]["stereochemistry"]) for o in ordinary})
            for o in options:
                a = o["assessment"]
                self.assertFalse(a["canRun"])
                self.assertFalse(a["evidence"]["canGenerate3D"])
                self.assertTrue(a["evidence"]["canPreview2D"])
                self.assertEqual(a["cooling"]["reasonCodes"], ["unreviewed-cooled-pathway"])
                self.assertIsNone(a["cooling"]["modelId"])
                self.assertIn("No current selector combination qualifies cooled SN2 3D", a["note"])
                self.assertIn("does not mean the reaction is impossible", a["note"])
                d = service.reaction_diagram(o["id"], *pair, COLD)
                self.assertEqual(d["assessment"], a)
                self.assertIn("<svg", d["svg"])
                before = [r for r in d["atoms"] if r["side"] == "reactants"]
                after = [r for r in d["atoms"] if r["side"] == "products"]
                inventory = lambda rows: {r["mapId"]: (r["element"], r["formalCharge"]) for r in rows}
                b, p = inventory(before), inventory(after)
                self.assertEqual(len(b), len(before))
                self.assertEqual({k: v[0] for k, v in b.items()}, {k: v[0] for k, v in p.items()})
                self.assertEqual(sum(v[1] for v in b.values()), -1)
                self.assertEqual(sum(v[1] for v in p.values()), -1)
                roles = d["mechanism"]["roles"]
                center, leaving, incoming = (roles[k] for k in ("electrophilic-carbon", "leaving-group", "nucleophile"))
                self.assertEqual((b[incoming], p[incoming]), (("O", -1), ("O", 0)))
                self.assertEqual((b[leaving][1], p[leaving][1]), (0, -1))
                self.assertEqual(d["products"][1]["smiles"], f"[{b[leaving][0]}-]")
                edits = {(frozenset(r["atomMaps"]), r["before"], r["after"]) for r in d["changes"]}
                self.assertEqual(edits, {(frozenset((center, leaving)), 1, None), (frozenset((center, incoming)), None, 1)})
                m = d["mechanism"]
                self.assertEqual(m["type"], "SN2")
                self.assertEqual(len(m["steps"]), 1)
                step = m["steps"][0]
                self.assertTrue(step["concerted"])
                self.assertIsNone(step["intermediate"])
                self.assertEqual(step["protonTransfers"], [])
                attack, departure = step["electronMoves"]
                self.assertEqual((attack["source"], attack["destination"]),
                                 ({"type": "lone-pair", "atomMaps": [incoming]}, {"type": "atom", "atomMaps": [center]}))
                self.assertEqual((departure["source"], departure["destination"]),
                                 ({"type": "bond", "atomMaps": [center, leaving]}, {"type": "atom", "atomMaps": [leaving]}))
                self.assertIsNone(m["energyProfile"]["activationEnergies"])
                ordinary_diagram = service.reaction_diagram(o["id"], *pair, ambient)
                self.assertEqual(d["mechanism"], ordinary_diagram["mechanism"])
                self.assertTrue(o["stoichiometry"]["balanced"])
                self.assertEqual([r["coefficient"] for r in o["stoichiometry"]["reactants"]], [1, 1])
                self.assertFalse(o["stoichiometry"]["context"]["canGenerate3D"])
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before embedding")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, COLD)
                product = service.run_curated_reaction(o["id"], *pair, ambient)["product"]
                self.assertEqual(product["representation"], "3d")
                self.assertEqual(canonical(product["smiles"]), canonical(o["productSmiles"]))
                self.assertEqual([(r["atomIndex"], r["mapId"], r["element"]) for r in after if r["speciesIndex"] == 0],
                                 [(r["index"], r["mapId"], r["element"]) for r in product["atomLinks"]])
                self.assertNotIn(leaving, {r["mapId"] for r in product["atomLinks"]})

    def test_no_registry_entry_or_borrowed_cooling_permission(self):
        self.assertEqual(SUITE_VERSION, 1)
        self.assertIsNone(reviewed_profile(CANDIDATE, PATHWAY))
        profiles = reviewed_manifest()["profiles"]
        self.assertEqual(len(profiles), 7)
        for p in profiles:
            self.assertIsNone(reviewed_profile(p["modelId"], PATHWAY))
        pair, _, options = match()
        forged = copy.deepcopy(options[0]["assessment"])
        forged.update(canRun=True, coolingUnvalidated=False, coolingPolicy=CANDIDATE)
        forged["cooling"].update(modelId=CANDIDATE, status="supported-model", canGenerate3D=True, profileVersion=1)
        self.assertFalse(cooling_confidence(forged, COLD, {"mechanism": PATHWAY})["canRun"])
        with self.assertRaises(service.ChemistryError):
            service.run_curated_reaction(options[0]["id"], *pair, {**COLD, "coolingProfile": CANDIDATE})

    def test_generic_media_and_extra_activation_do_not_establish_cooled_profile(self):
        for medium in ("", "dry", "aqueous-protic", "ethanolic-protic", "polar-aprotic"):
            for catalyst in ("", "none", "acid", "metal", "radical"):
                settings = {**COLD, "solvent": medium, "catalyst": catalyst}
                pair, _, options = match(conditions=settings)
                self.assertTrue(options)
                for o in options:
                    self.assertFalse(o["assessment"]["canRun"])
                    self.assertIn("No current selector combination", o["assessment"]["note"])
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(o["id"], *pair, settings)
                    if not medium:
                        self.assertIn("solvent", o["assessment"]["missingSettings"])
                    if catalyst not in {"", "none"}:
                        self.assertEqual(o["assessment"]["factors"]["catalyst"]["status"], "unevaluated")

    def test_structural_and_competing_chemistry_negatives_remain_specific(self):
        for source, reason in (("CC(C)(C)Br", "tertiary"), ("BrCC(C)(C)C", "Neopentyl"),
                               ("BrC1CCCCC1", "Ring-bound"), ("C=CCBr", "Allylic"),
                               ("BrCCO", "3-membered"), ("CC(=O)OCCBr", "ester")):
            _, result, options = match(source)
            self.assertEqual(options, [], source)
            self.assertIn(reason, " ".join(result["unsupportedReasons"]))
        for source in ("CF", "C=CBr", "Brc1ccccc1"):
            self.assertEqual(match(source)[2], [])
        for reagent in ("water", {"name": "Hydroxide ion", "smiles": "O"}):
            self.assertEqual(match(reagent=reagent)[2], [])

    def test_inversion_and_distant_relabeling_do_not_grant_cold_stereo_confidence(self):
        r = match("C[C@H](Br)CC")[2][0]["information"]["stereochemistry"]
        self.assertEqual((r["reactant"]["chiralCenters"][0]["assignment"], r["product"]["chiralCenters"][0]["assignment"]), ("S", "R"))
        r = match("C[C@H](CCOC)CCBr")[2][0]["information"]["stereochemistry"]
        self.assertEqual((r["reactant"]["chiralCenters"][0]["assignment"], r["product"]["chiralCenters"][0]["assignment"]), ("R", "S"))
        for o in match("CCC(Br)C")[2]:
            self.assertNotIn("@", o["productSmiles"])
            self.assertTrue(all(not c["specified"] for c in o["information"]["stereochemistry"]["product"]["chiralCenters"]))

    def test_methyl_has_no_e2_and_nonmethyl_competition_is_not_cold_approved(self):
        for source in ("CCl", "CBr", "CI"):
            _, result, _ = match(source)
            self.assertFalse(any(o["mechanism"] in {"SN1", "E1", "E2"} for o in result["reactionOptions"]))
        _, result, _ = match("CCC(Br)C")
        self.assertTrue(any(o["mechanism"] == "E2" for o in result["reactionOptions"]))
        self.assertTrue(all(not o["assessment"]["canRun"] for o in result["reactionOptions"]))

    def test_authenticated_conditional_mechanism_and_stale_ambient_run(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, password = "https://phase5-test.invalid", "Synthetic-phase5-test-fixture"
            app = create_app({"SESSION_SECRET": secrets.token_hex(32), "TRIAL_PASSWORD": password,
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda path, **kw: client.post(path, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "CBr"}, "reactantB": "hydroxide", "conditions": {**COLD, "temperature": "ambient"}}
            self.assertEqual(post('/api/reactions/match', json=body).status_code, 401)
            self.assertEqual(post('/login', data={"password": password}).status_code, 303)
            o = post('/api/reactions/match', json=body).json['reactionOptions'][0]
            body['reactionId'] = o['id']
            self.assertEqual(post('/api/reactions/run', json=body).status_code, 200)
            body['conditions'] = COLD
            matched = post('/api/reactions/match', json=body)
            self.assertEqual(matched.status_code, 200)
            self.assertFalse(matched.json['reactionOptions'][0]['assessment']['canRun'])
            d = post('/api/reactions/diagram', json=body)
            self.assertEqual(d.status_code, 200)
            self.assertEqual(d.json['mechanism']['type'], 'SN2')
            self.assertFalse(d.json['assessment']['evidence']['canGenerate3D'])
            with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Gate before embedding')):
                blocked = post('/api/reactions/run', json=body)
            self.assertEqual(blocked.status_code, 422)
            self.assertNotIn('product', blocked.json)


def add_case(source, expected):
    def test(self):
        self.check_case(source, expected)
    return test


for label, source, expected in CASES:
    setattr(CooledSN2Phase5Tests, f"test_net_oracle_{label}", add_case(source, expected))


if __name__ == '__main__':
    unittest.main()
