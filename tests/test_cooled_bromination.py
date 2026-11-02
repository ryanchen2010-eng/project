"""Independent cooled-Br2 public contracts; no new reaction structures/rules.

Expected connectivity and anti-addition stereochemistry below are fixed test
expectations, not outputs copied from an arbitrary generated conformer.
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
from server.reaction_conditions import assess_bromination_conditions, assess_cooling_support, cooling_confidence


COOLED = {"temperature": "cooled", "solvent": "dry", "catalyst": "none"}


def canonical(smiles, stereo=True):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(f"Invalid independent test fixture: {smiles}")
    return Chem.MolToSmiles(molecule, isomericSmiles=stereo)


def options(source, conditions=None, reagent="bromine", reverse=False):
    substrate = {"smiles": source, "name": "Independent cooling fixture"}
    pair = (reagent, substrate) if reverse else (substrate, reagent)
    response = service.match_reactions(*pair, COOLED if conditions is None else conditions)
    return pair, response, [r for r in response["reactionOptions"] if r["mechanism"] == "Bromination"]


# Source, independently expected connectivity, number of separately selectable
# stereochemical/site products. These are not curated website examples.
POSITIVE_CASES = [
    ("ethene", "C=C", ["BrCCBr"], 1),
    ("propene", "C=CC", ["BrCC(Br)C"], 2),
    ("longer_terminal", "C=CCCCC", ["BrCC(Br)CCCC"], 2),
    ("branched", "C=CC(C)(C)C", ["BrCC(Br)C(C)(C)C"], 2),
    ("internal_unsigned", "CCC=CCC", ["CCC(Br)C(Br)CC"], 1),
    ("e_butene", "C/C=C/C", ["CC(Br)C(Br)C"], 1),
    ("z_butene", "C/C=C\\C", ["CC(Br)C(Br)C"], 2),
    ("cyclic", "C1=CCCCC1", ["BrC1CCCCC1Br"], 2),
    ("styrene", "C=Cc1ccccc1", ["BrCC(Br)c1ccccc1"], 2),
    ("remote_alcohol", "C=CCCCCCCCO", ["BrCC(Br)CCCCCCCO"], 2),
    ("remote_ether", "C=CCCCCCCCOC", ["BrCC(Br)CCCCCCCOC"], 2),
    ("distant_chiral_center", "C=CC[C@H](C)CC", ["BrCC(Br)C[C@H](C)CC"], 2),
    ("separated_sites", "C=CCCCCCCCCC=CC", ["BrCC(Br)CCCCCCCCC=CC", "C=CCCCCCCCCC(Br)C(Br)C"], 3),
    ("equivalent_sites", "C=CCCCCCCCCC=C", ["BrCC(Br)CCCCCCCCC=C"], 2),
]


class CoolingAssessmentUnitTests(unittest.TestCase):
    def test_helper_is_non_mutating_and_overlay_is_idempotent_for_same_inputs(self):
        base = assess_bromination_conditions(COOLED)
        baseline = copy.deepcopy(base)
        reaction = {"mechanism": "Bromination"}
        settings = copy.deepcopy(COOLED)
        review = assess_cooling_support(reaction, settings, base)
        self.assertTrue(review["canGenerate3D"])
        self.assertEqual(base, baseline)
        self.assertEqual(settings, COOLED)
        self.assertEqual(reaction, {"mechanism": "Bromination"})
        result = cooling_confidence(base, settings, reaction)
        self.assertEqual(base, baseline)
        self.assertIs(cooling_confidence(result, settings, reaction), result)

    def test_reusable_helper_cannot_resurrect_failed_reagent_or_other_assessment(self):
        base = assess_bromination_conditions(COOLED)
        for change in [{"canRun": False}, {"status": "missing"}, {"reagentValidated": False},
                       {"reagentRequirement": "actual neutral Cl2"},
                       {"conditionIssues": [{"field": "catalyst", "kind": "unsupported"}]}]:
            with self.subTest(change=change):
                review = assess_cooling_support({"mechanism": "Bromination"}, COOLED, {**base, **change})
                self.assertFalse(review["canGenerate3D"])
                self.assertEqual(review["status"], "conditions-unresolved")
        review = assess_cooling_support({"mechanism": "Chlorination"}, COOLED, base)
        self.assertFalse(review["canGenerate3D"])
        self.assertEqual(review["status"], "unvalidated-pathway")

    def test_non_cooled_inputs_do_not_acquire_a_cooling_profile(self):
        base = assess_bromination_conditions(COOLED)
        for temperature in ["", "ambient", "heated"]:
            settings = {**COOLED, "temperature": temperature}
            self.assertIsNone(assess_cooling_support({"mechanism": "Bromination"}, settings, base))
            self.assertIs(cooling_confidence(base, settings, {"mechanism": "Bromination"}), base)


class CooledBrominationPublicTests(unittest.TestCase):
    def assert_supported(self, source, expected, count):
        pair, response, found = options(source)
        self.assertEqual(len(found), count, response["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"], False) for r in found},
                         {canonical(s, False) for s in expected})
        self.assertEqual(len({canonical(r["productSmiles"]) for r in found}), count)
        self.assertEqual(response["supportState"], "Conditional")
        for option in found:
            assessment = option["assessment"]
            self.assertTrue(assessment["canRun"])
            self.assertFalse(assessment["coolingUnvalidated"])
            self.assertEqual(assessment["status"], "model-match")
            cooling = assessment["cooling"]
            self.assertEqual(cooling["version"], 1)
            self.assertEqual(cooling["pathway"], "Bromination")
            self.assertEqual(cooling["modelId"], "cooled-alkene-bromination-v1")
            self.assertEqual(cooling["status"], "supported-model")
            self.assertTrue(cooling["canGenerate3D"])
            self.assertTrue(cooling["sourceUrls"])
            evidence = assessment["evidence"]
            self.assertTrue(evidence["canPreview2D"])
            self.assertTrue(evidence["canGenerate3D"])
            self.assertEqual(evidence["assertionLevel"], "conditional-net")
            self.assertEqual(evidence["experimentalOutcome"], "not-predicted")
            self.assertNotIn("temperature", evidence["unknownConditions"])
            self.assertEqual(assessment["factors"]["temperature"]["status"], "model-match")
            self.assertNotIn("no cooled 3D product is asserted", assessment["note"])

            stoich = option["stoichiometry"]
            self.assertTrue(stoich["balanced"])
            self.assertEqual([row["coefficient"] for row in stoich["reactants"]], [1, 1])
            self.assertEqual(stoich["product"]["coefficient"], 1)
            self.assertEqual(stoich["excludedInputs"], [])
            self.assertEqual(option["byproducts"], [])
            self.assertTrue(stoich["context"]["canGenerate3D"])
            self.assertEqual(stoich["context"]["conditions"]["temperature"], "cooled")
            self.assertIn("not experimental yields", stoich["context"]["warning"])

            diagram = service.reaction_diagram(option["id"], *pair, COOLED)
            self.assertEqual(diagram["assessment"], assessment)
            self.assertIsNone(diagram["mechanism"], "The net model must not imply a complete bromonium mechanism")
            self.assertIn("<svg", diagram["svg"])
            self.assertNotIn("no cooled 3D product is asserted", diagram["note"])
            self.assertEqual(diagram["products"][0]["smiles"], option["productSmiles"])
            before = [a for a in diagram["atoms"] if a["side"] == "reactants"]
            after = [a for a in diagram["atoms"] if a["side"] == "products"]
            identity = lambda rows: {a["mapId"]: (a["element"], a["formalCharge"]) for a in rows}
            self.assertEqual(identity(before), identity(after))
            self.assertEqual(len(before), len(identity(before)))
            parameters = option["site"]["parameters"]
            bromines = set(parameters["bromines"])
            self.assertEqual({a["mapId"] for a in before if a["speciesIndex"] == 1}, bromines)
            self.assertEqual({a["element"] for a in before if a["mapId"] in bromines}, {"Br"})
            self.assertEqual(len(diagram["bondsBroken"]), 1)
            self.assertEqual(set(diagram["bondsBroken"][0]["atomMaps"]), bromines)
            self.assertEqual({frozenset(b["atomMaps"]) for b in diagram["bondsFormed"]},
                             {frozenset(pair) for pair in zip(parameters["alkene"], parameters["bromines"])})
            self.assertEqual(len(diagram["bondOrderChanges"]), 1)
            change = diagram["bondOrderChanges"][0]
            self.assertEqual((change["before"], change["after"]), (2, 1))
            self.assertEqual(set(change["atomMaps"]), set(parameters["alkene"]))

            result = service.run_curated_reaction(option["id"], *pair, COOLED)
            self.assertTrue(result["balanced"])
            self.assertEqual(result["assessment"], assessment)
            product = result["product"]
            self.assertEqual(product["representation"], "3d")
            self.assertEqual(canonical(product["smiles"]), canonical(option["productSmiles"]))
            self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after],
                             [(a["index"], a["mapId"], a["element"]) for a in product["atomLinks"]])
            geometry = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
            self.assertTrue(geometry.GetConformer().Is3D())
            # Verify the returned coordinates respect already assigned graph
            # configurations; never use coordinates to choose the expectation.
            for atom in geometry.GetAtoms():
                atom.SetAtomMapNum(0)
            Chem.AssignStereochemistryFrom3D(geometry, replaceExistingTags=True)
            Chem.AssignStereochemistry(geometry, cleanIt=True, force=True)
            Chem.AssignCIPLabels(geometry)
            indices = {a["mapId"]: a["index"] for a in product["atomLinks"]}
            for center in option["stereochemistry"]["product"]["chiralCenters"]:
                if center["specified"]:
                    atom = geometry.GetAtomWithIdx(indices[center["atomMap"]])
                    self.assertEqual(atom.GetProp("_CIPCode"), center["assignment"])

    def test_anti_e_and_z_graph_expectations_are_independent_of_conformer(self):
        cases = [
            ("C/C=C/C", {"C[C@H](Br)[C@H](Br)C"}),
            ("C/C=C\\C", {"C[C@H](Br)[C@@H](Br)C", "C[C@@H](Br)[C@H](Br)C"}),
            ("C1=CCCCC1", {"Br[C@H]1CCCC[C@@H]1Br", "Br[C@@H]1CCCC[C@H]1Br"}),
            ("C=CC[C@H](C)CC", {"BrC[C@H](Br)C[C@H](C)CC", "BrC[C@@H](Br)C[C@H](C)CC"}),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, _, found = options(source)
                self.assertEqual({canonical(r["productSmiles"]) for r in found}, {canonical(s) for s in expected})

    def test_omitted_and_explicit_no_additional_activation_are_both_allowed(self):
        for catalyst in ["", "none"]:
            settings = {**COOLED, "catalyst": catalyst}
            pair, _, found = options("C=C", settings)
            self.assertTrue(found[0]["assessment"]["canRun"])
            self.assertEqual(service.run_curated_reaction(found[0]["id"], *pair, settings)["product"]["representation"], "3d")

    def test_reversed_inputs_preserve_bromine_provenance(self):
        pair, _, found = options("C/C=C\\C", reverse=True)
        self.assertEqual(len(found), 2)
        for option in found:
            self.assertEqual(option["stoichiometry"]["reactants"][0]["formula"], "Br2")
            diagram = service.reaction_diagram(option["id"], *pair, COOLED)
            reagent = [a for a in diagram["atoms"] if a["side"] == "reactants" and a["element"] == "Br"]
            self.assertEqual({a["mapId"] for a in reagent}, set(option["site"]["parameters"]["bromines"]))
            self.assertTrue(service.run_curated_reaction(option["id"], *pair, COOLED)["balanced"])

    def test_switching_temperatures_keeps_existing_unset_ambient_heated_behavior(self):
        snapshots = {}
        for temperature in ["", "ambient", "heated"]:
            settings = {**COOLED, "temperature": temperature}
            pair, _, found = options("C=C", settings)
            assessment = found[0]["assessment"]
            self.assertEqual(assessment["canRun"], temperature != "heated")
            if temperature == "heated":
                with self.assertRaises(service.ChemistryError):
                    service.run_curated_reaction(found[0]["id"], *pair, settings)
            else:
                self.assertEqual(service.run_curated_reaction(found[0]["id"], *pair, settings)["product"]["smiles"], "BrCCBr")
            snapshots[temperature] = copy.deepcopy(assessment)
        options("C=C")
        for temperature, expected in snapshots.items():
            self.assertEqual(options("C=C", {**COOLED, "temperature": temperature})[2][0]["assessment"], expected)

    def test_capturing_unknown_and_missing_media_do_not_gain_3d(self):
        for medium in ["aqueous-protic", "ethanolic-protic", "polar-aprotic", ""]:
            with self.subTest(medium=medium):
                settings = {**COOLED, "solvent": medium}
                pair, _, found = options("C=CC", settings)
                self.assertEqual(len(found), 2)
                for option in found:
                    assessment = option["assessment"]
                    self.assertFalse(assessment["canRun"])
                    self.assertFalse(assessment["evidence"]["canGenerate3D"])
                    self.assertTrue(assessment["evidence"]["canPreview2D"])
                    diagram = service.reaction_diagram(option["id"], *pair, settings)
                    self.assertEqual(diagram["assessment"], assessment)
                    with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before 3D")):
                        with self.assertRaises(service.ChemistryError):
                            service.run_curated_reaction(option["id"], *pair, settings)

    def test_rejected_cooled_bromination_names_actual_incomplete_field_not_temperature(self):
        cases = [
            ({"solvent": "aqueous-protic"}, "solvent"),
            ({"solvent": "ethanolic-protic"}, "solvent"),
            ({"solvent": "polar-aprotic"}, "solvent"),
            ({"solvent": ""}, "solvent"),
            ({"catalyst": "acid"}, "catalyst"),
            ({"catalyst": "metal"}, "catalyst"),
            ({"unvalidatedSolvent": "DCM"}, "unvalidatedSolvent"),
            ({"secondaryOxidationProfile": "naocl-acetic-ketone-v1"}, "secondaryOxidationProfile"),
            ({"oxidationStage": "first"}, "oxidationStage"),
            ({"workup": "aqueous-release"}, "workup"),
        ]
        for changed, field in cases:
            with self.subTest(changed=changed):
                settings = {**COOLED, **changed}
                pair, _, found = options("C=C", settings)
                self.assertEqual(len(found), 1)
                option = found[0]
                assessment = option["assessment"]
                cooling = assessment["cooling"]
                evidence = assessment["evidence"]
                self.assertFalse(assessment["canRun"])
                self.assertFalse(cooling["canGenerate3D"])
                self.assertEqual(cooling["status"], "conditions-unresolved")
                self.assertEqual({i["field"] for i in cooling["conditionIssues"]}, {field})
                self.assertEqual({i["field"] for i in assessment["conditionIssues"]}, {field})
                self.assertEqual({i["field"] for i in evidence["conditionIssues"]}, {field})
                self.assertEqual(evidence["cooling"], cooling)
                self.assertTrue(evidence["label"].endswith(": " + field), evidence["label"])
                self.assertIn(field, evidence["unknownConditions"])
                self.assertNotIn("temperature", evidence["unknownConditions"])
                temperature = assessment["factors"]["temperature"]
                self.assertEqual(temperature["status"], "model-match")
                self.assertEqual(temperature["effect"], "neutral")
                self.assertEqual(evidence["evaluatedFactors"]["temperature"], temperature)
                self.assertFalse(evidence["canGenerate3D"])
                diagram = service.reaction_diagram(option["id"], *pair, settings)
                self.assertEqual(diagram["assessment"], assessment)
                self.assertFalse(option["stoichiometry"]["context"]["canGenerate3D"])
                self.assertNotIn("temperature", option["stoichiometry"]["context"]["unknownConditions"])
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before 3D")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(option["id"], *pair, settings)

    def test_multiple_unresolved_bromination_inputs_all_survive_evidence_classification(self):
        settings = {**COOLED, "solvent": "aqueous-protic", "catalyst": "acid",
                    "oxidationStage": "further", "workup": "aqueous-release", "unvalidatedSolvent": "DCM"}
        _, _, found = options("C=C", settings)
        self.assertEqual(len(found), 1)
        assessment = found[0]["assessment"]
        expected = {"solvent", "catalyst", "oxidationStage", "workup", "unvalidatedSolvent"}
        for issue_list in [assessment["conditionIssues"], assessment["cooling"]["conditionIssues"],
                           assessment["evidence"]["conditionIssues"]]:
            self.assertEqual({i["field"] for i in issue_list}, expected)
        self.assertEqual(set(assessment["evidence"]["unknownConditions"]), expected)
        self.assertEqual(set(assessment["evidence"]["label"].split(": ", 1)[1].split(", ")), expected)
        self.assertEqual(assessment["factors"]["temperature"]["status"], "model-match")
        self.assertEqual(assessment["factors"]["temperature"]["effect"], "neutral")
        self.assertFalse(assessment["canRun"])
        self.assertFalse(assessment["cooling"]["canGenerate3D"])
        self.assertFalse(assessment["evidence"]["canGenerate3D"])

    def test_extra_activation_does_not_inherit_cooled_permission(self):
        for catalyst in ["acid", "metal", "lindlar", "osmium", "radical"]:
            with self.subTest(catalyst=catalyst):
                settings = {**COOLED, "catalyst": catalyst}
                pair, response, found = options("C=CC", settings)
                if catalyst == "radical":
                    self.assertEqual(found, [])
                    self.assertIn("Radical Br2", " ".join(response["unsupportedReasons"]))
                else:
                    self.assertEqual(len(found), 2)
                    self.assertTrue(all(not r["assessment"]["canRun"] for r in found))
                previous = options("C=CC")[2][0]
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before 3D")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(previous["id"], *pair, settings)

    def test_irrelevant_and_unknown_inputs_cannot_claim_validated_cooled_model(self):
        for extra in [{"oxidationStage": "first"}, {"oxidationStage": "further"}, {"workup": "aqueous-release"},
                      {"secondaryOxidationProfile": "naocl-acetic-ketone-v1"}, {"unvalidatedSolvent": "DCM"}]:
            with self.subTest(extra=extra):
                settings = {**COOLED, **extra}
                pair, _, found = options("C=C", settings)
                self.assertEqual(len(found), 1)
                self.assertFalse(found[0]["assessment"]["canRun"])
                self.assertFalse(found[0]["assessment"]["evidence"]["canGenerate3D"])
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before 3D")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(found[0]["id"], *pair, settings)

    def test_persistent_stage_and_chain_controls_are_explicitly_not_applicable(self):
        # Existing UI retains these controls across pathways. Neither means
        # two Br2 equivalents or a polymer transformation on a selected alkene.
        for extra in [{"additionStage": "one", "polymerUnits": "4"},
                      {"additionStage": "two", "polymerUnits": "6"},
                      {"additionStage": "", "polymerUnits": "2"}]:
            with self.subTest(extra=extra):
                settings = {**COOLED, **extra}
                pair, _, found = options("C=C", settings)
                self.assertEqual(len(found), 1)
                option = found[0]
                self.assertTrue(option["assessment"]["canRun"])
                if extra["additionStage"]:
                    self.assertIn("additionStage", option["assessment"]["notApplicableSettings"])
                self.assertIn("polymerUnits", option["assessment"]["notApplicableSettings"])
                self.assertEqual([r["coefficient"] for r in option["stoichiometry"]["reactants"]], [1, 1])
                self.assertEqual(service.run_curated_reaction(option["id"], *pair, settings)["product"]["smiles"], "BrCCBr")

    def test_structural_competition_is_not_overridden_by_cooled_settings(self):
        for source in ["C=CCO", "C=CCCCO", "C=CCCOC", "C=CC=C", "C=CCCCCC=C", "C=Cc1ccc(O)cc1", "C=CCN"]:
            with self.subTest(source=source):
                _, response, found = options(source)
                self.assertEqual(found, [])
                self.assertTrue(response["unsupportedReasons"])

    def test_wrong_reagent_never_borrows_bromination_cooling_model(self):
        for reagent in ["chlorine", "hydrogen-bromide", {"smiles": "BrI"}, {"smiles": "II"}]:
            with self.subTest(reagent=reagent):
                _, _, found = options("C=CC", reagent=reagent)
                self.assertEqual(found, [])
        with self.assertRaises(service.ChemistryError):
            options("C=CC", reagent={"smiles": "[Br-]", "name": "Bromine"})

    def test_other_cooled_pathways_stay_conditional_2d(self):
        cases = [
            ("C=C", "chlorine", "Chlorination", {"solvent": "dry", "catalyst": "none"}),
            ("C=C", {"smiles": "CC(=O)OO"}, "Epoxidation", {"solvent": "dry", "catalyst": "none"}),
            ("CC#CC", "bromine", "Alkyne halogenation", {"solvent": "dry", "additionStage": "one", "catalyst": "none"}),
            ("C=C", "water", "Hydration", {"solvent": "aqueous-protic", "catalyst": "acid"}),
            ("CBr", "hydroxide", "SN2", {"solvent": "polar-aprotic"}),
        ]
        for source, reagent, pathway, settings in cases:
            with self.subTest(pathway=pathway):
                settings = {**settings, "temperature": "cooled"}
                pair = ({"smiles": source}, reagent)
                response = service.match_reactions(*pair, settings)
                found = [r for r in response["reactionOptions"] if r["mechanism"] == pathway]
                self.assertTrue(found, response["unsupportedReasons"])
                for option in found:
                    self.assertFalse(option["assessment"]["canRun"])
                    self.assertTrue(option["assessment"]["coolingUnvalidated"])
                    if pathway == "Epoxidation":
                        # Peracetic acid remains unsupported under cooling;
                        # only actual mCPBA has a separately reviewed profile.
                        self.assertEqual(option["assessment"]["cooling"]["status"], "conditions-unresolved")
                        self.assertEqual(option["assessment"]["cooling"]["modelId"], "cooled-peroxyacid-epoxidation-v1")
                        self.assertIn("reagentIdentity", [i["field"] for i in option["assessment"]["evidence"]["conditionIssues"]])
                    else:
                        self.assertEqual(option["assessment"]["cooling"]["status"], "unvalidated-pathway")
                        self.assertIsNone(option["assessment"]["cooling"]["modelId"])
                    self.assertFalse(option["assessment"]["evidence"]["canGenerate3D"])
                    with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Gate before 3D")):
                        with self.assertRaises(service.ChemistryError):
                            service.run_curated_reaction(option["id"], *pair, settings)


for label, source, expected, count in POSITIVE_CASES:
    setattr(CooledBrominationPublicTests, f"test_cooled_product_{label}",
            lambda self, s=source, p=expected, n=count: self.assert_supported(s, p, n))


class CooledBrominationAuthenticatedTests(unittest.TestCase):
    def test_match_diagram_run_and_condition_change_in_authenticated_public_api(self):
        with tempfile.TemporaryDirectory(prefix="cooled-br2-api-") as folder:
            origin = "https://cooled-br2.example.test"
            password = "Synthetic-cooled-Br2-password"
            app = create_app({"TRIAL_PASSWORD": password, "SESSION_SECRET": secrets.token_hex(32),
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda url, **kw: client.post(url, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "C/C=C\\C"}, "reactantB": "bromine", "conditions": dict(COOLED)}
            self.assertEqual(post("/api/reactions/match", json=body).status_code, 401)
            self.assertEqual(post("/login", data={"password": password}).status_code, 303)
            response = post("/api/reactions/match", json=body)
            self.assertEqual(response.status_code, 200)
            found = response.get_json()["reactionOptions"]
            self.assertEqual(len(found), 2)
            for option in found:
                self.assertTrue(option["assessment"]["canRun"])
                body["reactionId"] = option["id"]
                diagram = post("/api/reactions/diagram", json=body)
                result = post("/api/reactions/run", json=body)
                self.assertEqual(diagram.status_code, 200)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json["assessment"], diagram.json["assessment"])
                self.assertEqual(result.json["product"]["representation"], "3d")
                self.assertEqual(result.json["product"]["smiles"], option["productSmiles"])
                after = [a for a in diagram.json["atoms"] if a["side"] == "products"]
                self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after],
                                 [(a["index"], a["mapId"], a["element"]) for a in result.json["product"]["atomLinks"]])
            # A previously accepted ID is not permission to reuse stale 3D
            # after medium or activation changes.
            for changed in [{"solvent": "aqueous-protic"}, {"catalyst": "metal"}, {"catalyst": "radical"}]:
                body["conditions"] = {**COOLED, **changed}
                response = post("/api/reactions/run", json=body)
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("product", response.json)


if __name__ == "__main__":
    unittest.main()
