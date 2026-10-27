"""Independent Phase 2 contracts; not frozen benchmark or curated examples."""
import copy
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from rdkit import Chem
from server import chemistry_server as service
from server.production_app import create_app
from server import reaction_temperature_profiles as profiles
from server.reaction_conditions import cooling_confidence


PBA = "O=C(OO)c1ccccc1"
ACID = "O=C(O)c1ccccc1"
MODEL = "cooled-perbenzoic-epoxidation-v1"
COOLED = {"temperature": "cooled", "solvent": "dry", "catalyst": "none"}
# Expected graphs are specified independently, not obtained from transform().
CASES = (
    ("checked_styrene", "C=Cc1ccccc1", "C1OC1c1ccccc1"),
    ("ortho_methyl", "C=Cc1ccccc1C", "C1OC1c1ccccc1C"),
    ("meta_methyl", "C=Cc1cccc(C)c1", "C1OC1c1cccc(C)c1"),
    ("para_methyl", "C=Cc1ccc(C)cc1", "C1OC1c1ccc(C)cc1"),
    ("para_ethyl", "C=Cc1ccc(CC)cc1", "C1OC1c1ccc(CC)cc1"),
    ("dimethyl", "C=Cc1c(C)ccc(C)c1", "C1OC1c1c(C)ccc(C)c1"),
    ("remote_specified_center", "C=Cc1ccc([C@H](C)CC)cc1", "C1OC1c1ccc([C@H](C)CC)cc1"),
)


def canonical(smiles, stereo=True):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(smiles)
    return Chem.MolToSmiles(molecule, isomericSmiles=stereo)


def match(source="C=Cc1ccccc1", settings=None, reagent=None, reverse=False):
    pair = ({"smiles": source}, {"smiles": PBA} if reagent is None else reagent)
    if reverse:
        pair = pair[::-1]
    conditions = COOLED if settings is None else settings
    result = service.match_reactions(*pair, conditions)
    return pair, result, [r for r in result["reactionOptions"] if r["mechanism"] == "Epoxidation"]


class CooledPerbenzoicProductTests(unittest.TestCase):
    def assert_case(self, source, expected):
        pair, result, options = match(source)
        self.assertEqual(len(options), 2, result["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"], False) for r in options}, {canonical(expected, False)})
        self.assertEqual(len({canonical(r["productSmiles"]) for r in options}), 2)
        for option in options:
            assessment = option["assessment"]
            self.assertTrue(assessment["canRun"])
            self.assertEqual(assessment["cooling"]["modelId"], MODEL)
            self.assertEqual(assessment["cooling"]["reasonCodes"], [])
            self.assertEqual(assessment["cooling"]["mediumAssumption"]["referenceSolvent"], "chloroform")
            self.assertFalse(assessment["cooling"]["mediumAssumption"]["experimentalSolventEntered"])
            self.assertIn("0 C", assessment["cooling"]["temperatureScope"])
            self.assertIn("not separately", option["guidedConditions"]["limitations"][0])
            self.assertEqual(assessment["evidence"]["experimentalOutcome"], "not-predicted")
            self.assertIsNone(option["epoxidationStereo"]["ratios"])
            self.assertEqual(option["guidedConditions"]["profileId"], MODEL)
            self.assertEqual(option["guidedConditions"]["state"], "qualified")
            self.assertFalse(option["guidedConditions"]["canApply"])

            basis = option["stoichiometry"]
            self.assertTrue(basis["balanced"])
            self.assertEqual([r["coefficient"] for r in basis["reactants"]], [1, 1])
            self.assertEqual(basis["product"]["coefficient"], 1)
            self.assertEqual(basis["excludedInputs"], [])
            self.assertAlmostEqual(basis["reactants"][1]["molarMass"], 138.122, places=3)
            self.assertEqual(basis["reactants"][1]["formula"], "C7H6O3")
            self.assertTrue(basis["context"]["canGenerate3D"])
            self.assertIn("not experimental yields", basis["context"]["warning"])

            diagram = service.reaction_diagram(option["id"], *pair, COOLED)
            self.assertEqual(diagram["assessment"], assessment)
            self.assertEqual(len(diagram["products"]), 2)
            self.assertEqual(canonical(diagram["products"][1]["smiles"]), canonical(ACID))
            self.assertEqual(diagram["products"][1]["formula"], "C7H6O2")
            atoms = diagram["atoms"]
            before = [a for a in atoms if a["side"] == "reactants"]
            after = [a for a in atoms if a["side"] == "products"]
            identities = lambda rows: {a["mapId"]: (a["element"], a["formalCharge"]) for a in rows}
            self.assertEqual(identities(before), identities(after))
            self.assertEqual(len(identities(before)), len(before))
            self.assertEqual(sum(a["formalCharge"] for a in before), sum(a["formalCharge"] for a in after))
            p = option["site"]["parameters"]
            reagent_maps = {a["mapId"] for a in before if a["speciesIndex"] == 1}
            epoxide_maps = {a["mapId"] for a in after if a["speciesIndex"] == 0}
            acid_maps = {a["mapId"] for a in after if a["speciesIndex"] == 1}
            self.assertIn(p["transferredOxygen"], reagent_maps & epoxide_maps)
            self.assertEqual(acid_maps, reagent_maps - {p["transferredOxygen"]})
            self.assertIn(p["peracidHydrogen"], acid_maps)
            self.assertNotIn(p["peracidHydrogen"], epoxide_maps)
            self.assert_mechanism(diagram, p)

            run = service.run_curated_reaction(option["id"], *pair, COOLED)
            self.assertTrue(run["balanced"])
            self.assertEqual(run["assessment"], assessment)
            product = run["product"]
            self.assertEqual(product["representation"], "3d")
            self.assertEqual(canonical(product["smiles"]), canonical(option["productSmiles"]))
            self.assertEqual({a["mapId"] for a in product["atomLinks"]}, epoxide_maps)
            molecule = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
            self.assertTrue(molecule.GetConformer().Is3D())
            Chem.AssignStereochemistryFrom3D(molecule, replaceExistingTags=True)
            Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
            Chem.AssignCIPLabels(molecule)
            indices = {a["mapId"]: a["index"] for a in product["atomLinks"]}
            for center in option["stereochemistry"]["product"]["chiralCenters"]:
                if center["specified"]:
                    self.assertEqual(molecule.GetAtomWithIdx(indices[center["atomMap"]]).GetProp("_CIPCode"), center["assignment"])

    def assert_mechanism(self, diagram, p):
        a, b = p["alkene"]
        t, h, q, c, o = (p[k] for k in ("transferredOxygen", "peracidHydrogen", "proximalOxygen", "acylCarbon", "carbonylOxygen"))
        expected = {(frozenset((a, b)), 2, 1), (frozenset((q, t)), 1, None), (frozenset((t, h)), 1, None),
                    (frozenset((a, t)), None, 1), (frozenset((b, t)), None, 1),
                    (frozenset((c, q)), 1, 2), (frozenset((c, o)), 2, 1), (frozenset((o, h)), None, 1)}
        edits = lambda rows: {(frozenset(r["atomMaps"]), r["before"], r["after"]) for r in rows}
        self.assertEqual(edits(diagram["changes"]), expected)
        mechanism = diagram["mechanism"]
        self.assertEqual(mechanism["type"], "Epoxidation")
        self.assertEqual(len(mechanism["steps"]), 1)
        step = mechanism["steps"][0]
        self.assertTrue(step["concerted"])
        self.assertIsNone(step["intermediate"])
        expected_moves = {((a, b), (a, t)), ((t, h), (t, b)), ((q, t), (c, q)), ((c, o), (o, h))}
        self.assertEqual({(tuple(m["source"]["atomMaps"]), tuple(m["destination"]["atomMaps"])) for m in step["electronMoves"]}, expected_moves)
        self.assertEqual(edits(step["bondsFormed"] + step["bondsBroken"] + step["bondOrderChanges"]), expected)
        self.assertIsNone(mechanism["energyProfile"]["activationEnergies"])

    def test_parent_styrene_has_independent_r_s_alternatives_not_a_population_claim(self):
        _, _, options = match()
        expected = {canonical("c1ccccc1[C@H]1CO1"), canonical("c1ccccc1[C@@H]1CO1")}
        self.assertEqual({canonical(r["productSmiles"]) for r in options}, expected)
        labels = {tuple(c["assignment"] for c in r["stereochemistry"]["product"]["chiralCenters"] if c["specified"]) for r in options}
        self.assertEqual(labels, {("R",), ("S",)})
        self.assertTrue(all(r["epoxidationStereo"]["ratios"] is None for r in options))

    def test_remote_physical_configuration_matches_independently_written_products(self):
        _, _, options = match("C=Cc1ccc([C@H](C)CC)cc1")
        expected = {canonical(f"C1O[C{tag}H]1c1ccc([C@H](C)CC)cc1") for tag in ("@", "@@")}
        self.assertEqual({canonical(r["productSmiles"]) for r in options}, expected)

    def test_reversed_inputs_and_serialization_keep_actual_identity_and_amount_slots(self):
        for reverse in (False, True):
            for reagent in ({"smiles": "OOC(=O)c1ccccc1", "name": "not an identity"},
                            {"smiles": "[O:9]=[C:10]([O:11][OH:12])[c:1]1[cH:2][cH:3][cH:4][cH:5][cH:6]1"}):
                pair, result, options = match(reagent=reagent, reverse=reverse)
                self.assertEqual(len(options), 2, result["unsupportedReasons"])
                for r in options:
                    self.assertTrue(r["assessment"]["canRun"])
                    oxidant = next(x for x in r["stoichiometry"]["reactants"] if x["formula"] == "C7H6O3")
                    self.assertEqual(oxidant["inputSlot"], 0 if reverse else 1)
                    self.assertTrue(service.run_curated_reaction(r["id"], *pair, COOLED)["balanced"])


for label, source, expected in CASES:
    setattr(CooledPerbenzoicProductTests, f"test_product_{label}",
            lambda self, s=source, e=expected: self.assert_case(s, e))


class PerbenzoicCoolingBoundaryTests(unittest.TestCase):
    def test_valid_graphs_outside_the_cold_profile_remain_conditional_not_impossible(self):
        for source in ("C=C", "C=CC", "C=C(C)c1ccccc1", "C/C=C/c1ccccc1", "C/C=C\\c1ccccc1",
                       "C1=CCCCC1", "C=Cc1ccc(C=C)cc1", "C=Cc1ccc(C2CCCCC2)cc1"):
            with self.subTest(source=source):
                pair, result, options = match(source)
                self.assertTrue(options, result["unsupportedReasons"])
                for option in options:
                    assessment = option["assessment"]
                    self.assertFalse(assessment["canRun"])
                    self.assertEqual(assessment["cooling"]["modelId"], MODEL)
                    self.assertIn("substrate-profile-unresolved", assessment["cooling"]["reasonCodes"])
                    self.assertTrue(assessment["evidence"]["canPreview2D"])
                    self.assertFalse(option["guidedConditions"]["canApply"])
                    self.assertEqual(option["guidedConditions"]["state"], "outside-profile-scope")
                    with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Must gate before geometry')):
                        with self.assertRaises(service.ChemistryError):
                            service.run_curated_reaction(option["id"], *pair, COOLED)
                _, _, ambient = match(source, {**COOLED, "temperature": "ambient"})
                self.assertEqual({r["id"]: r["productSmiles"] for r in options}, {r["id"]: r["productSmiles"] for r in ambient})
                self.assertTrue(all(r["assessment"]["canRun"] for r in ambient))

    def test_existing_heteroatom_strain_and_competing_chemistry_rejections_are_preserved(self):
        for source in ("C=Cc1ccc(O)cc1", "C=Cc1ccc(N)cc1", "C=Cc1ccc(OC)cc1", "C=CCO",
                       "C=CCN", "C1=CCC1", "C=C=C", "C=CC=C", "C=Cc1ccc(C=O)cc1"):
            with self.subTest(source=source):
                _, result, options = match(source)
                self.assertFalse(options)
                self.assertTrue(result["unsupportedReasons"])

    def test_wrong_peracid_cannot_borrow_perbenzoic_profile_from_a_name(self):
        for reagent in ("CC(=O)OO", "O=C(OO)c1cccc(Cl)c1", "O=C(OO)c1ccc(Cl)cc1"):
            _, _, options = match(reagent={"smiles": reagent, "name": "Perbenzoic acid", "formula": "C7H6O3"})
            self.assertTrue(options)
            self.assertTrue(all(r["assessment"]["cooling"]["modelId"] != MODEL for r in options))
        for reagent in (ACID, "OO", "O=C(OOC)c1ccccc1"):
            self.assertFalse(match(reagent={"smiles": reagent, "name": "perbenzoic acid"})[2])

    def test_conditions_fail_closed_and_keep_reaction_and_conditions_unmodified(self):
        variants = [{"solvent": v} for v in ("", "aqueous-protic", "ethanolic-protic", "polar-aprotic")]
        variants += [{"catalyst": v} for v in ("acid", "metal", "osmium", "lindlar", "radical")]
        variants += [{"oxidationStage": "first"}, {"workup": "aqueous-release"}, {"temperature": "heated"},
                     {"temperatureCelsius": "0"}, {"solventIdentity": "chloroform"}, {"coolingProfile": MODEL}]
        for extra in variants:
            settings = {**COOLED, **extra}
            original = copy.deepcopy(settings)
            pair, result, options = match(settings=settings)
            self.assertEqual(settings, original)
            for option in options:
                self.assertFalse(option["assessment"]["canRun"])
                self.assertFalse(option["assessment"]["evidence"]["canGenerate3D"])
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(option["id"], *pair, settings)
            if not options:
                self.assertTrue(result["unsupportedReasons"])

    def test_missing_identity_and_underlying_failed_assessment_cannot_be_overridden(self):
        for changes in ({"epoxidationSubstrateIdentity": None}, {"epoxidationSubstrateIdentity": "not-smiles"},
                        {"peroxyacidIdentity": "CC(=O)OO"}):
            reaction = {"mechanism": "Epoxidation", "peroxyacidIdentity": PBA, "epoxidationSubstrateIdentity": "C=Cc1ccccc1", **changes}
            review = {"version": 1, "pathway": "Epoxidation", "canGenerate3D": False}
            base = {"canRun": True, "status": "model-match", "reagentValidated": True, "reagentRequirement": "actual neutral single peroxyacid"}
            result = profiles.PROFILES_BY_ID[MODEL].assessor(reaction, COOLED, base, review)
            self.assertFalse(result["canGenerate3D"])
        from server.reaction_conditions import assess_epoxidation_conditions
        reaction = {"mechanism": "Epoxidation", "peroxyacidIdentity": PBA, "epoxidationSubstrateIdentity": "C=Cc1ccccc1"}
        for change in ({"canRun": False}, {"status": "missing"}, {"reagentValidated": False},
                       {"reagentRequirement": "wrong"}, {"conditionIssues": [{"field": "solvent", "kind": "unsupported", "explanation": "Independent rejection"}]}):
            base = {**assess_epoxidation_conditions(COOLED), **change}
            original = copy.deepcopy(base)
            self.assertFalse(profiles.assess_cooling_support(reaction, COOLED, base)["canGenerate3D"])
            self.assertEqual(base, original)

    def test_guidance_only_changes_confirmable_existing_fields_and_preserves_unknowns(self):
        for extra in ({"solvent": ""}, {"solvent": "aqueous-protic"}, {"catalyst": "acid"}):
            settings = {**COOLED, **extra}
            _, _, options = match(settings=settings)
            g = options[0]["guidedConditions"]
            self.assertTrue(g["canApply"])
            self.assertTrue(g["requireConfirmation"])
            self.assertEqual(g["targetConditions"], {"solvent": "dry", "catalyst": "none"})
            self.assertNotIn("temperature", g["targetConditions"])
            self.assertIn("chloroform-reference", " ".join(g["limitations"]))
        for extra in ({"future": "unknown"}, {"workup": "aqueous-release"}, {"oxidationStage": "first"}):
            _, _, options = match(settings={**COOLED, **extra})
            g = options[0]["guidedConditions"]
            self.assertFalse(g["canApply"])
            self.assertNotIn("targetConditions", g)
            self.assertEqual(g["state"], "unsupported-conditions")

    def test_stale_cooling_permission_is_not_reused_with_a_new_substrate(self):
        _, _, options = match()
        value = options[0]["assessment"]
        changed = {"mechanism": "Epoxidation", "peroxyacidIdentity": PBA, "epoxidationSubstrateIdentity": "C=CC"}
        self.assertFalse(cooling_confidence(value, COOLED, changed)["canRun"])

    def test_cooled_confidence_does_not_change_existing_graphs_or_mechanisms(self):
        pair, _, cooled = match()
        for temperature in ("", "ambient"):
            settings = {**COOLED, "temperature": temperature}
            _, _, original = match(settings=settings)
            self.assertEqual({r["id"]: r["productSmiles"] for r in cooled}, {r["id"]: r["productSmiles"] for r in original})
            self.assertTrue(all("cooling" not in r["assessment"] for r in original))
            self.assertTrue(all("guidedConditions" not in r for r in original))
            for option in cooled:
                cold = service.reaction_diagram(option["id"], *pair, COOLED)
                warm = service.reaction_diagram(option["id"], *pair, settings)
                for key in ("atoms", "changes", "products", "reactants", "svg", "mechanism"):
                    self.assertEqual(cold[key], warm[key])

    def test_unknown_future_versions_and_models_remain_unreviewed(self):
        self.assertEqual(len(profiles.PROFILES_BY_ID), 7)
        self.assertIsNone(profiles.reviewed_profile(MODEL, "Epoxidation", version=2))
        self.assertIsNone(profiles.reviewed_profile(MODEL, "Epoxidation", registry_version=2))
        self.assertIsNone(profiles.reviewed_profile(MODEL, "Bromination"))
        self.assertIsNone(profiles.reviewed_profile("cooled-dihydroxylation-v1", "Alkene dihydroxylation"))

    def test_authenticated_public_match_diagram_run_and_stale_id_revalidation(self):
        with tempfile.TemporaryDirectory(prefix="cooled-perbenzoic-api-") as folder:
            origin = "https://perbenzoic.example.test"
            app = create_app({"TRIAL_PASSWORD": "Synthetic-PBA-fixture", "SESSION_SECRET": secrets.token_hex(32),
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda path, **kw: client.post(path, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "C=Cc1ccccc1"}, "reactantB": {"smiles": PBA}, "conditions": dict(COOLED)}
            self.assertEqual(post('/api/reactions/match', json=body).status_code, 401)
            self.assertEqual(post('/login', data={"password": "Synthetic-PBA-fixture"}).status_code, 303)
            matched = post('/api/reactions/match', json=body)
            self.assertEqual(matched.status_code, 200)
            body['reactionId'] = matched.json['reactionOptions'][0]['id']
            diagram = post('/api/reactions/diagram', json=body)
            run = post('/api/reactions/run', json=body)
            self.assertEqual((diagram.status_code, run.status_code), (200, 200))
            self.assertEqual(diagram.json['assessment'], run.json['assessment'])
            self.assertEqual(run.json['product']['representation'], '3d')
            for changed in ({"solvent": "aqueous-protic"}, {"solvent": ""}, {"catalyst": "acid"},
                            {"temperature": "heated"}, {"workup": "aqueous-release"}, {"temperatureCelsius": "0"}):
                body['conditions'] = {**COOLED, **changed}
                response = post('/api/reactions/run', json=body)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('product', response.json)
            body['conditions'] = dict(COOLED)
            body['reactantA'] = {"smiles": "C=CC"}
            rejected = post('/api/reactions/run', json=body)
            self.assertEqual(rejected.status_code, 422)
            self.assertNotIn('product', rejected.json)


if __name__ == '__main__':
    unittest.main()
