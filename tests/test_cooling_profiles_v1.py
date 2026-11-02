"""Version 1 cooling contracts, independent of the frozen 347-case benchmark.

These are model-confidence and molecular-identity fixtures, not experimental
temperature/yield predictions, visible examples, or laboratory procedures.
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
from server.reaction_conditions import assess_cooling_support, assess_epoxidation_conditions, cooling_confidence
from server.reaction_information import DEFINITIONS


SUITE_VERSION = 1
COOLED = {"solvent": "dry", "temperature": "cooled", "catalyst": "none"}
MCPBA = "O=C(OO)c1cccc(Cl)c1"
MCBA = "O=C(O)c1cccc(Cl)c1"
SUPPORTED_MODELS = {"Bromination": "cooled-alkene-bromination-v1",
                    "Epoxidation": "cooled-peroxyacid-epoxidation-v1"}

# Versioned diagnostic inputs are deliberately local to this suite. They do not
# import, rewrite, or replace frozen benchmark rows or curated website examples.
PATHWAY_CASES = (
    ("SN2", "CBr", "hydroxide", {"solvent": "polar-aprotic"}),
    ("SN1", "CC(C)(C)Br", "water", {"solvent": "aqueous-protic"}),
    ("E1", "CC(C)(C)Br", "water", {"solvent": "aqueous-protic"}),
    ("E2", "CCBr", "hydroxide", {"solvent": "ethanolic-protic"}),
    ("Hydrogenation", "C=C", "hydrogen", {"catalyst": "metal"}),
    ("Carbonyl hydrogenation", "CCC=O", "hydrogen", {"catalyst": "metal"}),
    ("Ester hydrolysis", "CC(=O)OCC", "water", {"solvent": "aqueous-protic", "catalyst": "acid"}),
    ("Ester saponification", "CC(=O)OCC", "hydroxide", {"solvent": "aqueous-protic"}),
    ("Hydration", "C=C", "water", {"solvent": "aqueous-protic", "catalyst": "acid"}),
    ("Hydrohalogenation", "C=C", {"smiles": "Cl"}, {"solvent": "dry"}),
    ("Bromination", "C=C", "bromine", {"solvent": "dry", "catalyst": "none"}),
    ("Chlorination", "C=C", "chlorine", {"solvent": "dry", "catalyst": "none"}),
    ("Epoxidation", "C=C", {"smiles": MCPBA}, {"solvent": "dry", "catalyst": "none"}),
    ("Alkene dihydroxylation", "C=C", "hydrogen-peroxide", {"catalyst": "osmium", "workup": "aqueous-release"}),
    ("Alkyne partial hydrogenation", "CC#CC", "hydrogen", {"catalyst": "lindlar"}),
    ("Alkyne hydrogenation", "CC#CC", "hydrogen", {"catalyst": "metal"}),
    ("Alkyne halogenation", "CC#CC", "bromine", {"solvent": "dry", "additionStage": "one", "catalyst": "none"}),
    ("Alkyne hydrohalogenation", "C#CC", {"smiles": "Br"}, {"solvent": "dry", "additionStage": "one", "catalyst": "none"}),
    ("Alcohol dehydration", "CCO", {"smiles": "OS(=O)(=O)O"}, {"solvent": "dry", "catalyst": "acid"}),
    ("Alcohol substitution", "CCO", {"smiles": "Br"}, {"solvent": "dry"}),
    ("Alcohol oxidation", "CC(O)C", "sodium-hypochlorite", {
        "secondaryOxidationProfile": "naocl-acetic-ketone-v1", "solvent": "aqueous-protic",
        "catalyst": "none", "oxidationStage": "first"}),
    ("Esterification", "CC(=O)O", {"smiles": "CCO"}, {"catalyst": "acid"}),
    ("Polymerization model", "C=C", {"smiles": "O=C(OOC(=O)c1ccccc1)c1ccccc1"}, {
        "catalyst": "radical", "polymerUnits": "2"}),
    ("Aldehyde oxidation", "CCC=O", "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "further"}),
    # Primary and secondary oxidation share a rule name but differ in endpoint
    # confidence. Both profiles are included rather than hiding this difference.
    ("Alcohol oxidation", "CCO", "sodium-hypochlorite", {"solvent": "aqueous-protic", "oxidationStage": "first"}),
)


def canonical(smiles, stereo=True):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError(f"Invalid versioned cooling fixture: {smiles}")
    return Chem.MolToSmiles(molecule, isomericSmiles=stereo)


def matches(pathway, source, reagent, settings):
    inputs = ({"smiles": source, "name": "Versioned cooling diagnostic"}, reagent)
    response = service.match_reactions(*inputs, settings)
    found = [r for r in response["reactionOptions"] if r["mechanism"] == pathway]
    if not found:
        raise AssertionError(f"Missing {pathway} diagnostic: {response['unsupportedReasons']}")
    return inputs, response, found


class CoolingMatrixV1Tests(unittest.TestCase):
    def test_versioned_fixture_covers_every_existing_rule_type(self):
        self.assertEqual(SUITE_VERSION, 1)
        self.assertEqual(len(DEFINITIONS), 24)
        self.assertEqual({case[0] for case in PATHWAY_CASES}, set(DEFINITIONS))
        self.assertEqual(len(PATHWAY_CASES), 25)

    def check_pathway(self, pathway, source, reagent, original):
        settings = {**original, "temperature": "cooled"}
        before = copy.deepcopy(settings)
        inputs, response, options = matches(pathway, source, reagent, settings)
        self.assertEqual(settings, before)
        self.assertEqual(response["supportState"], "Conditional")
        supported = pathway in SUPPORTED_MODELS
        for option in options:
            assessment = option["assessment"]
            review = assessment["cooling"]
            evidence = assessment["evidence"]
            context = option["stoichiometry"]["context"]
            self.assertEqual(review["version"], SUITE_VERSION)
            self.assertEqual(review["pathway"], pathway)
            self.assertEqual(review["canGenerate3D"], supported)
            self.assertEqual(assessment["canRun"], supported)
            self.assertEqual(evidence["canGenerate3D"], supported)
            self.assertEqual(context["canGenerate3D"], supported)
            self.assertEqual(context["conditions"]["temperature"], "cooled")
            self.assertTrue(evidence["canPreview2D"])
            self.assertTrue(option["stoichiometry"]["balanced"])
            diagram = service.reaction_diagram(option["id"], *inputs, settings)
            self.assertEqual(diagram["assessment"], assessment)
            self.assertIn("<svg", diagram["svg"])
            if supported:
                self.assertEqual(review["status"], "supported-model")
                self.assertEqual(review["modelId"], SUPPORTED_MODELS[pathway])
                self.assertIn("theoretical product conformer", diagram["note"])
                self.assertTrue(review["sourceUrls"])
            else:
                self.assertEqual(review["status"], "unvalidated-pathway")
                self.assertIsNone(review["modelId"])
                # The cooling registry must explain this exact pathway rather
                # than giving every reaction the same blanket rejection.
                self.assertIn(pathway, review["note"])
                self.assertIn(review["note"], assessment["note"])
                self.assertIn("no cooled 3D product is asserted", diagram["note"])
                with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Unreviewed cooling must gate before embedding")):
                    with self.assertRaises(service.ChemistryError):
                        service.run_curated_reaction(option["id"], *inputs, settings)

    def test_unsupported_rule_notes_are_distinct_and_specific(self):
        notes = {}
        for pathway, source, reagent, original in PATHWAY_CASES:
            if pathway in SUPPORTED_MODELS or pathway in notes:
                continue
            _, _, options = matches(pathway, source, reagent, {**original, "temperature": "cooled"})
            note = options[0]["assessment"]["cooling"]["note"]
            self.assertIn(pathway, note)
            notes[pathway] = note
        self.assertEqual(len(set(notes.values())), len(DEFINITIONS) - len(SUPPORTED_MODELS))

    def test_existing_cooled_bromination_still_generates_mapped_anti_3d(self):
        inputs, _, options = matches("Bromination", "C/C=C/C", "bromine", COOLED)
        self.assertEqual(len(options), 1)
        option = options[0]
        self.assertEqual(canonical(option["productSmiles"]), canonical("C[C@H](Br)[C@H](Br)C"))
        diagram = service.reaction_diagram(option["id"], *inputs, COOLED)
        self.assertIsNone(diagram["mechanism"])
        result = service.run_curated_reaction(option["id"], *inputs, COOLED)
        self.assertEqual(result["product"]["representation"], "3d")
        self.assertEqual(result["assessment"], diagram["assessment"])
        self.assertEqual(result["assessment"]["cooling"]["modelId"], SUPPORTED_MODELS["Bromination"])
        self.assertEqual({atom["mapId"] for atom in result["product"]["atomLinks"]},
                         {atom["mapId"] for atom in diagram["atoms"] if atom["side"] == "products"})
        self.assertFalse(option["stoichiometry"]["context"]["warning"].startswith("Actual yield"))


for index, values in enumerate(PATHWAY_CASES):
    setattr(CoolingMatrixV1Tests, f"test_rule_type_{index:02d}",
            lambda self, case=values: self.check_pathway(*case))


EPOXIDE_CASES = (
    ("ethene", "C=C", ("C1CO1",), 1),
    ("propene", "C=CC", ("CC1CO1",), 2),
    ("longer_chain", "C=CCCC", ("CCCC1CO1",), 2),
    ("branched", "C=C(C)CCC", ("CCCC1(C)CO1",), 2),
    ("e_butene", "C/C=C/C", ("CC1OC1C",), 2),
    ("z_butene", "C/C=C\\C", ("CC1OC1C",), 1),
    ("unsigned_internal", "CC=CCCC", ("CCCC1OC1C",), 1),
    ("cyclic", "C1=CCCCC1", ("C1CCC2OC2C1",), 1),
    ("styrene", "C=Cc1ccccc1", ("c1ccccc1C1CO1",), 2),
    ("remote_alcohol", "C=CCCCCCCCO", ("OCCCCCCCC1CO1",), 2),
    ("remote_ether", "C=CCCCCCCCOC", ("COCCCCCCCC1CO1",), 2),
    ("distant_chiral_center", "C=CC[C@H](C)CC", ("CCC(C)CC1CO1",), 2),
    ("distinct_multiple_sites", "C=CCCCCC=CC", ("C=CCCCCC1OC1C", "CC=CCCCCC1CO1"), 3),
    ("equivalent_multiple_sites", "C=CCCCCC=C", ("C=CCCCCC1CO1",), 2),
)


class CooledEpoxidationV1Tests(unittest.TestCase):
    def options(self, source, conditions=None, reagent=None, reverse=False):
        pair = ({"smiles": source, "name": "Versioned cooled epoxidation"},
                {"smiles": MCPBA} if reagent is None else reagent)
        if reverse:
            pair = pair[::-1]
        settings = COOLED if conditions is None else conditions
        response = service.match_reactions(*pair, settings)
        return pair, response, [r for r in response["reactionOptions"] if r["mechanism"] == "Epoxidation"]

    def assert_epoxide(self, source, products, count):
        pair, response, options = self.options(source)
        self.assertEqual(len(options), count, response["unsupportedReasons"])
        self.assertEqual({canonical(r["productSmiles"], False) for r in options},
                         {canonical(s, False) for s in products})
        self.assertEqual(len({canonical(r["productSmiles"]) for r in options}), count)
        for option in options:
            assessment = option["assessment"]
            review = assessment["cooling"]
            self.assertTrue(assessment["canRun"])
            self.assertFalse(assessment["coolingUnvalidated"])
            self.assertEqual(review["modelId"], SUPPORTED_MODELS["Epoxidation"])
            self.assertEqual(review["status"], "supported-model")
            self.assertTrue(review["canGenerate3D"])
            self.assertEqual(assessment["factors"]["temperature"]["effect"], "neutral")
            evidence = assessment["evidence"]
            self.assertTrue(evidence["canGenerate3D"])
            self.assertEqual(evidence["assertionLevel"], "conditional-net")
            self.assertEqual(evidence["experimentalOutcome"], "not-predicted")
            self.assertNotIn("temperature", evidence["unknownConditions"])
            self.assertIsNone(option["epoxidationStereo"]["ratios"])
            self.assertIn("theoretical product conformer", assessment["note"])
            self.assertIn("not a", assessment["note"])

            stoichiometry = option["stoichiometry"]
            self.assertTrue(stoichiometry["balanced"])
            self.assertEqual([r["coefficient"] for r in stoichiometry["reactants"]], [1, 1])
            self.assertEqual(stoichiometry["product"]["coefficient"], 1)
            self.assertEqual(stoichiometry["excludedInputs"], [])
            oxidant = stoichiometry["reactants"][1]
            self.assertEqual(oxidant["formula"], "C7H5ClO3")
            self.assertAlmostEqual(oxidant["molarMass"], 172.567, places=3)
            context = stoichiometry["context"]
            self.assertTrue(context["canGenerate3D"])
            self.assertEqual(context["conditions"]["temperature"], "cooled")
            self.assertEqual(context["assertionLevel"], "conditional-net")
            self.assertIn("not experimental yields", context["warning"])
            self.assertTrue(any("theoretical product conformer" in note for note in context["assumptions"]))

            diagram = service.reaction_diagram(option["id"], *pair, COOLED)
            self.assertEqual(diagram["assessment"], assessment)
            self.assertEqual(len(diagram["products"]), 2)
            self.assertEqual(canonical(diagram["products"][1]["smiles"]), canonical(MCBA))
            self.assertEqual(diagram["products"][1]["formula"], "C7H5ClO2")
            self.assertIn("<svg", diagram["svg"])
            self.assertIn("theoretical product conformer", diagram["note"])
            before = [a for a in diagram["atoms"] if a["side"] == "reactants"]
            after = [a for a in diagram["atoms"] if a["side"] == "products"]
            identities = lambda rows: {a["mapId"]: (a["element"], a["formalCharge"]) for a in rows}
            self.assertEqual(identities(before), identities(after))
            self.assertEqual(len(identities(before)), len(before))
            self.assertEqual(sum(a["formalCharge"] for a in before), 0)
            self.assertEqual(sum(a["formalCharge"] for a in after), 0)
            participants = option["site"]["parameters"]
            transferred = participants["transferredOxygen"]
            reagent_maps = {a["mapId"] for a in before if a["speciesIndex"] == 1}
            epoxide_maps = {a["mapId"] for a in after if a["speciesIndex"] == 0}
            acid_maps = {a["mapId"] for a in after if a["speciesIndex"] == 1}
            self.assertIn(transferred, reagent_maps & epoxide_maps)
            self.assertEqual(acid_maps, reagent_maps - {transferred})
            self.assertNotIn(participants["peracidHydrogen"], epoxide_maps)
            self.assertTrue({participants[key] for key in (
                "peracidHydrogen", "acylCarbon", "carbonylOxygen", "proximalOxygen")} <= acid_maps)
            expected_edits = self.edit_contract(participants)
            self.assertEqual(self.edits(diagram["changes"]), expected_edits)
            self.assert_mechanism(diagram["mechanism"], participants, expected_edits)

            result = service.run_curated_reaction(option["id"], *pair, COOLED)
            self.assertTrue(result["balanced"])
            self.assertEqual(result["assessment"], assessment)
            product = result["product"]
            self.assertEqual(product["representation"], "3d")
            self.assertEqual(canonical(product["smiles"]), canonical(option["productSmiles"]))
            self.assertEqual([(a["atomIndex"], a["mapId"], a["element"]) for a in after if a["speciesIndex"] == 0],
                             [(a["index"], a["mapId"], a["element"]) for a in product["atomLinks"]])
            self.assert_geometry_respects_graph(product, option)

    @staticmethod
    def edits(changes):
        return {(frozenset(c["atomMaps"]), c["before"], c["after"]) for c in changes}

    @staticmethod
    def edit_contract(p):
        a, b = p["alkene"]
        t, h, q, c, o = (p[key] for key in (
            "transferredOxygen", "peracidHydrogen", "proximalOxygen", "acylCarbon", "carbonylOxygen"))
        return {(frozenset((a, b)), 2, 1), (frozenset((q, t)), 1, None),
                (frozenset((t, h)), 1, None), (frozenset((a, t)), None, 1),
                (frozenset((b, t)), None, 1), (frozenset((c, q)), 1, 2),
                (frozenset((c, o)), 2, 1), (frozenset((o, h)), None, 1)}

    def assert_mechanism(self, mechanism, p, expected_edits):
        self.assertEqual(mechanism["type"], "Epoxidation")
        self.assertEqual(len(mechanism["steps"]), 1)
        step = mechanism["steps"][0]
        self.assertTrue(step["concerted"])
        self.assertIsNone(step["intermediate"])
        a, b = p["alkene"]
        t, h, q, c, o = (p[key] for key in (
            "transferredOxygen", "peracidHydrogen", "proximalOxygen", "acylCarbon", "carbonylOxygen"))
        expected_moves = {((a, b), (a, t)), ((t, h), (t, b)), ((q, t), (c, q)), ((c, o), (o, h))}
        self.assertEqual({(tuple(m["source"]["atomMaps"]), tuple(m["destination"]["atomMaps"]))
                          for m in step["electronMoves"]}, expected_moves)
        self.assertTrue(all(m["source"]["type"] == m["destination"]["type"] == "bond" for m in step["electronMoves"]))
        self.assertEqual(self.edits(step["bondsFormed"] + step["bondsBroken"] + step["bondOrderChanges"]), expected_edits)
        state = {frozenset(bond["atomMaps"]): bond["order"] for bond in step["state"]["bonds"]}
        self.assertEqual(state[frozenset((o, h))], 1)
        self.assertEqual(state[frozenset((c, q))], 2)
        self.assertEqual(state[frozenset((c, o))], 1)
        self.assertEqual(mechanism["energyProfile"]["intermediates"], 0)
        self.assertIsNone(mechanism["energyProfile"]["activationEnergies"])

    def assert_geometry_respects_graph(self, product, option):
        molecule = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
        self.assertTrue(molecule.GetConformer().Is3D())
        for atom in molecule.GetAtoms():
            atom.SetAtomMapNum(0)
        # Coordinates verify already declared graph assignments; they never
        # provide the expected reaction stereochemistry in these tests.
        Chem.AssignStereochemistryFrom3D(molecule, replaceExistingTags=True)
        Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
        Chem.AssignCIPLabels(molecule)
        indices = {a["mapId"]: a["index"] for a in product["atomLinks"]}
        for center in option["stereochemistry"]["product"]["chiralCenters"]:
            if center["specified"]:
                atom = molecule.GetAtomWithIdx(indices[center["atomMap"]])
                self.assertTrue(atom.HasProp("_CIPCode"))
                self.assertEqual(atom.GetProp("_CIPCode"), center["assignment"])

    def test_missing_or_mismatched_internal_identity_fails_closed_without_mutation(self):
        base = assess_epoxidation_conditions(COOLED)
        before = copy.deepcopy(base)
        for identity in [None, "", "CC(=O)OO", "O=C(OO)c1ccc(Cl)cc1"]:
            with self.subTest(identity=identity):
                reaction = {"mechanism": "Epoxidation"}
                if identity is not None:
                    reaction["peroxyacidIdentity"] = identity
                original = copy.deepcopy(reaction)
                review = assess_cooling_support(reaction, COOLED, base)
                self.assertFalse(review["canGenerate3D"])
                self.assertEqual(review["status"], "conditions-unresolved")
                self.assertIn("reagentIdentity", {i["field"] for i in review["conditionIssues"]})
                self.assertEqual(reaction, original)
                self.assertEqual(base, before)

    def test_supported_identity_cannot_override_failed_base_assessment(self):
        reaction = {"mechanism": "Epoxidation", "peroxyacidIdentity": MCPBA}
        base = assess_epoxidation_conditions(COOLED)
        for changed in [{"canRun": False}, {"status": "missing"}, {"reagentValidated": False},
                        {"reagentRequirement": "actual neutral Br2"},
                        {"conditionIssues": [{"field": "solvent", "kind": "unsupported",
                                              "explanation": "Synthetic validated solvent rejection."}]}]:
            with self.subTest(changed=changed):
                assessment = {**base, **changed}
                original = copy.deepcopy(assessment)
                review = assess_cooling_support(reaction, COOLED, assessment)
                self.assertFalse(review["canGenerate3D"])
                self.assertEqual(review["status"], "conditions-unresolved")
                self.assertFalse(cooling_confidence(assessment, COOLED, reaction)["canRun"])
                self.assertEqual(assessment, original)

    def test_e_z_cyclic_and_terminal_stereochemistry_has_independent_expectations(self):
        for source, expected in [("C/C=C/C", {("R", "R"), ("S", "S")}),
                                 ("C/C=C\\C", {("R", "S")}),
                                 ("C1=CCCCC1", {("R", "S")}),
                                 ("C=CC", {("R",), ("S",)})]:
            with self.subTest(source=source):
                _, _, options = self.options(source)
                actual = set()
                for option in options:
                    centers = option["stereochemistry"]["product"]["chiralCenters"]
                    assigned = tuple(c["assignment"] for c in sorted(centers, key=lambda c: c["atomMap"])
                                     if c["specified"] and c["atomMap"] in option["site"]["atomMaps"])
                    # Symmetric cis structures may reverse map enumeration.
                    actual.add(tuple(sorted(assigned)) if source in {"C/C=C\\C", "C1=CCCCC1"} else assigned)
                self.assertEqual(actual, expected)

    def test_unsigned_geometry_does_not_gain_a_cooling_selected_configuration(self):
        for source in ["CC=CCCC", "CCC(C)=C(C)CCC"]:
            _, _, options = self.options(source)
            self.assertEqual(len(options), 1)
            option = options[0]
            self.assertIn("unknown", option["epoxidationStereo"]["outcome"])
            self.assertTrue(all(not c["specified"] for c in option["stereochemistry"]["product"]["chiralCenters"]))
        _, _, ethene = self.options("C=C")
        self.assertEqual(ethene[0]["epoxidationStereo"]["assignedAtomMaps"], [])

    def test_distant_physical_configuration_retains_independently_changed_cip_label(self):
        pair, _, options = self.options("C=CCC[C@H](C)CCC(C)(C)C")
        self.assertEqual(len(options), 2)
        for option in options:
            old = option["stereochemistry"]["reactant"]["chiralCenters"][0]
            new = next(c for c in option["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"] == old["atomMap"])
            self.assertEqual((old["assignment"], new["assignment"]), ("S", "R"))
            product = service.run_curated_reaction(option["id"], *pair, COOLED)["product"]
            self.assert_geometry_respects_graph(product, option)

    def test_cooling_changes_confidence_not_existing_product_mechanism_or_atom_identity(self):
        pair, _, cooled = self.options("C/C=C/C")
        _, _, ambient = self.options("C/C=C/C", {**COOLED, "temperature": "ambient"})
        self.assertEqual({r["id"]: r["productSmiles"] for r in cooled}, {r["id"]: r["productSmiles"] for r in ambient})
        for option in cooled:
            cold = service.reaction_diagram(option["id"], *pair, COOLED)
            warm = service.reaction_diagram(option["id"], *pair, {**COOLED, "temperature": "ambient"})
            for key in ["atoms", "reactants", "products", "changes", "mechanism"]:
                self.assertEqual(cold[key], warm[key])
            self.assertEqual(option["assessment"]["cooling"]["status"], "supported-model")
            self.assertNotIn("cooling", warm["assessment"])

    def test_reverse_input_order_retains_actual_oxygen_and_acid_identity(self):
        for reverse in [False, True]:
            pair, _, options = self.options("C=CC", reverse=reverse)
            self.assertEqual(len(options), 2)
            for option in options:
                diagram = service.reaction_diagram(option["id"], *pair, COOLED)
                self.assertEqual(canonical(diagram["products"][1]["smiles"]), canonical(MCBA))
                oxygen = option["site"]["parameters"]["transferredOxygen"]
                origins = [a for a in diagram["atoms"] if a["side"] == "reactants" and a["mapId"] == oxygen]
                self.assertEqual(len(origins), 1)
                # Diagrams canonicalize species to substrate then peracid;
                # calculator inputSlot separately retains the user's order.
                self.assertEqual(diagram["reactants"][origins[0]["speciesIndex"]]["formula"], "C7H5ClO3")
                self.assertEqual(origins[0]["element"], "O")
                reagent_row = next(r for r in option["stoichiometry"]["reactants"] if r["formula"] == "C7H5ClO3")
                self.assertEqual(reagent_row["inputSlot"], 0 if reverse else 1)
                self.assertTrue(service.run_curated_reaction(option["id"], *pair, COOLED)["balanced"])

    def test_actual_mcpba_identity_not_formula_or_name_is_required(self):
        unsupported = ["CC(=O)OO", "O=COO", "CCC(=O)OO", "O=C(OO)c1ccccc1",
                       "O=C(OO)c1ccccc1Cl", "O=C(OO)c1ccc(Cl)cc1"]
        for reagent in unsupported:
            with self.subTest(reagent=reagent):
                pair, response, options = self.options("C=CC", reagent={"smiles": reagent, "name": "mCPBA"})
                self.assertEqual(len(options), 2, response["unsupportedReasons"])
                for option in options:
                    assessment = option["assessment"]
                    self.assertFalse(assessment["canRun"])
                    review = assessment["cooling"]
                    self.assertEqual(review["status"], "conditions-unresolved")
                    perbenzoic = reagent == "O=C(OO)c1ccccc1"
                    self.assertEqual(review["modelId"], "cooled-perbenzoic-epoxidation-v1" if perbenzoic else SUPPORTED_MODELS["Epoxidation"])
                    self.assertFalse(review["canGenerate3D"])
                    self.assertIn("substrateProfile" if perbenzoic else "reagentIdentity", {i["field"] for i in review["conditionIssues"]})
                    self.assertNotIn("temperature", assessment["evidence"]["unknownConditions"])
                    self.assertIn("perbenzoic-acid" if perbenzoic else "mCPBA", review["note"])
                    with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Unreviewed peracid must gate before embedding")):
                        with self.assertRaises(service.ChemistryError):
                            service.run_curated_reaction(option["id"], *pair, COOLED)

    def test_smiles_serialization_and_user_map_numbers_do_not_change_mcpba_identity(self):
        for reagent in [{"smiles": "Clc1cccc(C(=O)OO)c1", "name": "Not trusted as identity"},
                        {"smiles": "[O:91]=[C:51]([O:7][OH:31])[c:62]1[cH:2][cH:9][cH:3][c:8]([Cl:4])[cH:5]1"}]:
            pair, response, options = self.options("C=C", reagent=reagent)
            self.assertEqual(len(options), 1, response["unsupportedReasons"])
            self.assertTrue(options[0]["assessment"]["canRun"])
            self.assertTrue(service.run_curated_reaction(options[0]["id"], *pair, COOLED)["balanced"])

    def test_failed_media_activation_and_unrelated_settings_cannot_borrow_profile(self):
        changes = [{"solvent": medium} for medium in ["", "aqueous-protic", "ethanolic-protic", "polar-aprotic"]]
        changes += [{"catalyst": catalyst} for catalyst in ["acid", "metal", "lindlar", "osmium"]]
        changes += [{"oxidationStage": "first"}, {"workup": "aqueous-release"},
                    {"peroxyacidIdentity": MCPBA}, {"temperatureCelsius": "5"},
                    {"secondaryOxidationProfile": "naocl-acetic-ketone-v1"}]
        for changed in changes:
            with self.subTest(changed=changed):
                conditions = {**COOLED, **changed}
                pair, response, options = self.options("C=CC", conditions)
                self.assertEqual(len(options), 2, response["unsupportedReasons"])
                for option in options:
                    assessment = option["assessment"]
                    self.assertFalse(assessment["canRun"])
                    self.assertFalse(assessment["evidence"]["canGenerate3D"])
                    self.assertEqual(assessment["cooling"]["status"], "conditions-unresolved")
                    self.assertTrue(set(changed) <= {i["field"] for i in assessment["cooling"]["conditionIssues"]})
                    self.assertNotIn("temperature", assessment["evidence"]["unknownConditions"])
                    self.assertFalse(option["stoichiometry"]["context"]["canGenerate3D"])
                    self.assertTrue(service.reaction_diagram(option["id"], *pair, conditions)["assessment"]["evidence"]["canPreview2D"])
                    with patch.object(service, "mapped_product_molecule", side_effect=AssertionError("Must fail before embedding")):
                        with self.assertRaises(service.ChemistryError):
                            service.run_curated_reaction(option["id"], *pair, conditions)

    def test_unset_activation_and_persistent_stage_controls_are_not_extra_chemistry(self):
        for conditions in [{**COOLED, "catalyst": ""},
                           {**COOLED, "additionStage": "one", "polymerUnits": "4"},
                           {**COOLED, "additionStage": "two", "polymerUnits": "6"}]:
            pair, _, options = self.options("C=C", conditions)
            self.assertTrue(options[0]["assessment"]["canRun"])
            self.assertEqual([r["coefficient"] for r in options[0]["stoichiometry"]["reactants"]], [1, 1])
            self.assertEqual(service.run_curated_reaction(options[0]["id"], *pair, conditions)["product"]["smiles"], "C1CO1")
            for key in ["additionStage", "polymerUnits"]:
                if conditions.get(key):
                    self.assertIn(key, options[0]["assessment"]["notApplicableSettings"])

    def test_cooling_does_not_relax_structural_stereo_or_competing_reaction_rules(self):
        for source in ["C=CCO", "C=CCCCO", "C=CCCOC", "C=CCCCCCCCOC(C)(C)C",
                       "C=CCCCCCCC=O", "C=CCN", "C=CC=C", "C=C=C",
                       "C1=CCC1", "C1=CCCCCCC1", "C=C1CCCCC1", "C=C[C@H](C)CC"]:
            with self.subTest(source=source):
                _, response, options = self.options(source)
                self.assertFalse(options)
                self.assertTrue(response["unsupportedReasons"])

    def test_wrong_oxidant_or_radical_activation_never_selects_concerted_epoxidation(self):
        for reagent in ["hydrogen-peroxide", {"smiles": "OO", "name": "mCPBA"},
                        {"smiles": "CC(=O)OOC"}, {"smiles": MCBA}]:
            with self.subTest(reagent=reagent):
                self.assertFalse(self.options("C=CC", reagent=reagent)[2])
        _, response, options = self.options("C=CC", {**COOLED, "catalyst": "radical"})
        self.assertFalse(options)
        self.assertIn("Radical activation", " ".join(response["unsupportedReasons"]))


for label, source, products, count in EPOXIDE_CASES:
    setattr(CooledEpoxidationV1Tests, f"test_cooled_epoxide_{label}",
            lambda self, s=source, p=products, n=count: self.assert_epoxide(s, p, n))


class CoolingAuthenticatedV1Tests(unittest.TestCase):
    def test_cooling_permissions_recomputed_for_stale_ids_and_every_condition_change(self):
        with tempfile.TemporaryDirectory(prefix="cooling-profiles-v1-api-") as folder:
            origin = "https://cooling-v1.example.test"
            password = "Synthetic-cooling-v1-password"
            app = create_app({"TRIAL_PASSWORD": password, "SESSION_SECRET": secrets.token_hex(32),
                              "PUBLIC_ORIGIN": origin, "FRAME_ANCESTORS": origin,
                              "DIST_DIR": Path(folder), "TESTING": True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda url, **kw: client.post(url, base_url=origin, headers={"Origin": origin}, **kw)
            body = {"reactantA": {"smiles": "C/C=C\\C"}, "reactantB": {"smiles": MCPBA}, "conditions": dict(COOLED)}
            self.assertEqual(post("/api/reactions/match", json=body).status_code, 401)
            self.assertEqual(post("/login", data={"password": password}).status_code, 303)
            matched = post("/api/reactions/match", json=body)
            self.assertEqual(matched.status_code, 200)
            options = [r for r in matched.json["reactionOptions"] if r["mechanism"] == "Epoxidation"]
            self.assertEqual(len(options), 1)
            body["reactionId"] = options[0]["id"]
            first = post("/api/reactions/run", json=body)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json["product"]["representation"], "3d")
            expected = canonical(first.json["product"]["smiles"])
            for changed in [{"solvent": "aqueous-protic"}, {"solvent": ""},
                            {"catalyst": "acid"}, {"catalyst": "radical"},
                            {"temperature": "heated"}, {"workup": "aqueous-release"},
                            {"temperatureCelsius": "5"}]:
                with self.subTest(changed=changed):
                    body["conditions"] = {**COOLED, **changed}
                    stale = post("/api/reactions/run", json=body)
                    self.assertEqual(stale.status_code, 422)
                    self.assertNotIn("product", stale.json)
                    body["conditions"] = dict(COOLED)
                    restored = post("/api/reactions/run", json=body)
                    self.assertEqual(restored.status_code, 200)
                    self.assertEqual(canonical(restored.json["product"]["smiles"]), expected)
                    self.assertTrue(restored.json["assessment"]["evidence"]["canGenerate3D"])
            # An accepted model ID or a cached reaction selection is not a
            # license to replace the actual meta-peroxyacid by another acid.
            body["reactantB"] = {"smiles": "O=C(OO)c1ccc(Cl)cc1", "name": "mCPBA"}
            response = post("/api/reactions/match", json=body)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(any(r["assessment"]["canRun"] for r in response.json["reactionOptions"]))
            rejected = post("/api/reactions/run", json=body)
            self.assertEqual(rejected.status_code, 422)
            self.assertNotIn("product", rejected.json)


if __name__ == "__main__":
    unittest.main()
