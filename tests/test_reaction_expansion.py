"""Independent structural/product/map expectations for this incremental pass."""
import unittest
from rdkit import Chem
from server import chemistry_server as service
from server import epoxidation_rule
from server.functional_groups import inspect_structure
from server.reaction_information import DEFINITIONS, group_reactions


def canonical(smiles):
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class EpoxidationTests(unittest.TestCase):
    def options(self, substrate, reagent="CC(=O)OO", **conditions):
        return service.match_reactions({"name": "Arbitrary A", "smiles": substrate},
            {"name": "Arbitrary B", "smiles": reagent}, conditions)["reactions"]

    def test_chain_position_branching_size_and_ring_products(self):
        for substrate, expected in (("C=C", "C1CO1"), ("C=CC", "CC1CO1"), ("CC=CC", "CC1OC1C"),
                ("C=C(C)C", "CC1(C)CO1"), ("C=CCCCCCCC", "CCCCCCCC1CO1"),
                ("C1=CCCCC1", "C1CCC2OC2C1")):
            with self.subTest(substrate=substrate):
                options = self.options(substrate)
                self.assertEqual(len(options), 2 if substrate in {"C=CC", "C=CCCCCCCC"} else 1)
                for option in options:
                    self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(option["productSmiles"]),isomericSmiles=False),
                                     Chem.MolToSmiles(Chem.MolFromSmiles(expected),isomericSmiles=False))
                    self.assertTrue(option["stoichiometry"]["balanced"])

    def test_peroxyacid_variants_keep_their_actual_carboxylic_acid(self):
        for reagent, acid in (("O=COO", "O=CO"), ("CCC(=O)OO", "CCC(=O)O"),
                ("O=C(OO)c1cccc(Cl)c1", "O=C(O)c1cccc(Cl)c1")):
            with self.subTest(reagent=reagent):
                option = self.options("C=CC", reagent)[0]
                diagram = service.reaction_diagram(option["id"], {"smiles": "C=CC"}, {"smiles": reagent})
                self.assertEqual(diagram["products"][1]["smiles"], canonical(acid))
                self.assertIn("acid", diagram["products"][1]["name"].lower())

    def test_transfer_uses_terminal_oxygen_exact_maps_and_explicit_hydrogen(self):
        options = service._reactions_for_pair("ethene", "peracetic-acid", service.REACTANTS)[0]
        identifier, reaction = next(iter(options.items()))
        diagram = service.reaction_diagram(identifier, "ethene", "peracetic-acid")
        origins = {a["mapId"]: a for a in diagram["atomMap"]}
        product = Chem.MolFromSmiles(reaction["mappedProducts"][0], Chem.SmilesParserParams())
        # Reagent heavy-graph atom 4 is the terminal peracid oxygen, not 2 or 3.
        oxygen = next(a for a in product.GetAtoms() if a.GetSymbol() == "O")
        origin = origins[oxygen.GetAtomMapNum()]
        self.assertEqual((origin["reactantId"], origin["atomIndex"]), ("peracetic-acid", 4))
        before = {a["mapId"]: a["element"] for a in diagram["atoms"] if a["side"] == "reactants"}
        after = {a["mapId"]: a["element"] for a in diagram["atoms"] if a["side"] == "products"}
        self.assertEqual(before, after)
        self.assertEqual(len(diagram["bondsFormed"]), 3)
        self.assertEqual(len(diagram["bondsBroken"]), 2)
        # Concerted proton transfer reorganizes both actual acid C–O bonds too.
        self.assertEqual(len(diagram["bondOrderChanges"]), 3)
        self.assertTrue(diagram["highlightsAvailable"])
        self.assertEqual(len(diagram["mechanism"]["steps"]),1)
        self.assertTrue(diagram["mechanism"]["steps"][0]["concerted"])

    def test_name_and_input_order_never_decide_eligibility(self):
        a, b = {"name": "Sodium chloride", "smiles": "C=CC"}, {"name": "Not a peroxide", "smiles": "CC(=O)OO"}
        left, right = service.match_reactions(a, b)["reactions"], service.match_reactions(b, a)["reactions"]
        self.assertEqual([r["productSmiles"] for r in left], [r["productSmiles"] for r in right])
        self.assertTrue(left)

    def test_peroxide_acid_perester_and_ambiguous_reagent_do_not_match(self):
        for reagent in ("OO", "CC(=O)O", "CC(=O)OOC", "OOC(=O)CCC(=O)OO"):
            with self.subTest(reagent=reagent): self.assertFalse([r for r in self.options("C=CC", reagent) if r["mechanism"] == "Epoxidation"])

    def test_unsupported_selectivity_stereo_and_strained_substrates_are_not_guessed(self):
        self.assertEqual(len(self.options("C/C=C/C")),2)
        for substrate in ("C=C(O)C", "C=CC=C", "C1=CC1", "C=C[C@H](C)CC"):
            with self.subTest(substrate=substrate): self.assertFalse(self.options(substrate))

    def test_multiple_separated_alkenes_are_distinct_selectable_sites(self):
        options = self.options("C=CCCC=C")
        self.assertEqual(len(options), 2)
        self.assertEqual(len({o["id"] for o in options}), 2)
        # Equivalent substrate sites are grouped, but their exact map aliases remain.
        sites={tuple(v[:2]) for option in options for v in option["site"]["parameters"]["equivalentSiteFaces"]}
        self.assertEqual(len(sites),2)
        self.assertTrue(all("=" in o["productSmiles"] for o in options))

    def test_information_classification_condition_fit_and_calculator(self):
        option = self.options("C=C", solvent="dry", catalyst="none")[0]
        self.assertEqual(option["classifications"], ["Addition", "Oxidation"])
        self.assertEqual(option["information"]["capabilities"]["stereochemistry"], "validated same-face oxygen transfer and distant retention; unknown starting geometry stays unsigned")
        self.assertEqual(option["information"]["capabilities"]["mappedMechanism"], "supported")
        self.assertEqual(option["information"]["references"][0]["url"], epoxidation_rule.SOURCE)
        self.assertEqual(len(option["stoichiometry"]["reactants"]), 2)
        self.assertEqual(option["stoichiometry"]["product"]["formula"], "C2H4O")
        self.assertEqual(self.options("C=C", solvent="aqueous-protic")[0]["reasoning"]["label"], "Not evaluated")

    def test_actual_main_product_3d_retains_exact_mapping(self):
        option = self.options("C=CC")[0]
        result = service.run_curated_reaction(option["id"], {"smiles": "C=CC"}, {"smiles": "CC(=O)OO"}, {"solvent":"dry"})
        self.assertEqual(result["product"]["representation"], "3d")
        self.assertEqual(result["product"]["smiles"], option["productSmiles"])
        self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(result["product"]["smiles"]),isomericSmiles=False), canonical("CC1CO1"))
        self.assertEqual(len(result["product"]["atomLinks"]), result["product"]["atoms"])


class GroupInspectionTests(unittest.TestCase):
    def inspect(self, smiles, **options):
        return service.inspect_reactant({"smiles": smiles, "name": "Test structure"}, **options)

    def types(self, smiles):
        return {g["type"] for g in self.inspect(smiles)["groups"]}

    def test_eleven_requested_groups_plus_peroxyacid(self):
        cases = {"C=C": "alkene", "C#C": "alkyne", "CCO": "alcohol", "C=O": "aldehyde",
                 "CC(=O)C": "ketone", "CC(=O)O": "carboxylic acid", "CC(=O)OC": "ester",
                 "CN": "amine", "CC(=O)N": "amide", "CF": "haloalkane",
                 "c1ccccc1": "aromatic ring", "CC(=O)OO": "peroxyacid"}
        for smiles, group in cases.items():
            with self.subTest(smiles=smiles): self.assertIn(group, self.types(smiles))

    def test_groups_do_not_confuse_acids_esters_amides_or_peroxides(self):
        self.assertEqual(self.types("CC(=O)N"), {"amide"})
        self.assertEqual(self.types("CC(=O)OC"), {"ester"})
        self.assertEqual(self.types("CC(=O)O"), {"carboxylic acid"})
        self.assertEqual(self.types("CC(=O)OO"), {"peroxyacid"})
        self.assertFalse(self.types("N"))
        self.assertFalse(self.types("ON"))
        self.assertNotIn("carboxylic acid", self.types("OC(=O)O"))

    def test_inspection_scope_broader_than_reaction_eligibility(self):
        for smiles, group in (("Nc1ccccc1", "amine"), ("CC(=O)Oc1ccccc1", "ester"), ("CF", "haloalkane")):
            self.assertIn(group, self.types(smiles))
        self.assertFalse(service.match_reactions({"smiles": "CF"}, "hydroxide")["reactions"])

    def test_multiple_groups_and_repeated_sites_keep_distinct_map_ids(self):
        data = self.inspect("OCCC(O)C")
        groups = data["groups"]
        self.assertEqual(len(groups), 2)
        self.assertEqual(len({g["id"] for g in groups}), 2)
        self.assertTrue(all(all(f'data-atom-map="{m}"' in data["svg"] for m in g["atomMaps"]) for g in groups))

    def test_suggestions_are_only_implemented_and_do_not_promise_a_match(self):
        alkene = self.inspect("C=CC=O")["groups"][0]
        self.assertIn("Epoxidation", [r["mechanism"] for r in alkene["reactions"]])
        self.assertFalse(service.match_reactions({"smiles": "C=CC=O"}, "peracetic-acid")["reactions"])
        for group in self.inspect("CC(=O)N")["groups"]: self.assertFalse(group["reactions"])
        self.assertIn("partner", self.inspect("C=C")["note"])
        self.assertTrue(all(r["mechanism"] in DEFINITIONS for r in group_reactions("alkene")))

    def test_no_conformer_unless_explicitly_requested_and_exact_maps_when_requested(self):
        self.assertNotIn("model", self.inspect("CCO"))
        data = self.inspect("CCO", include_3d=True)
        self.assertEqual(data["model"]["representation"], "3d")
        maps = {link["mapId"] for link in data["model"]["atomLinks"]}
        self.assertTrue(set(data["groups"][0]["atomMaps"]) <= maps)
        self.assertTrue(all(f'data-atom-map="{m}"' in data["svg"] for m in maps))

    def test_salt_identity_is_retained_and_ionic_3d_not_invented(self):
        data = service.inspect_reactant("sodium-hydroxide", True)
        self.assertEqual(data["formula"], "HNaO")
        self.assertEqual(data["model"]["representation"], "2d-only")
        self.assertIn("separate components", data["model"]["reason"])

    def test_validation_rejects_bad_requests_and_atom_bounds(self):
        for reference in (None, {}, "nonexistent", {"smiles": ""}, {"smiles": "not a smiles"}, {"smiles": "C" * 81}):
            with self.subTest(reference=reference):
                with self.assertRaises(ValueError): service.inspect_reactant(reference)
        with self.assertRaises(ValueError): self.inspect("CCO", include_3d="true")

    def test_every_catalog_pathway_has_consistent_information(self):
        for option in service.reaction_catalog()["reactions"]:
            info = option["information"]
            self.assertEqual(info["primaryFamily"], option["family"])
            self.assertEqual(info["classifications"], option["classifications"])
            self.assertEqual(info["capabilities"]["mappedMechanism"] == "supported", option["mechanism"] in {"SN1", "SN2", "E1", "E2", "Epoxidation"})
            self.assertEqual(info["capabilities"]["stereochemistry"], "validated distant retention; reacting center unassigned" if option["mechanism"] == "SN1" else "validated distant retention; new alkene unassigned" if option["mechanism"] == "E1" else "specified-center inversion" if option["mechanism"] == "SN2" else
                             "validated retention of specified configurations in the net edit" if option["mechanism"] in {"Ester hydrolysis", "Ester saponification"} else
                     "validated spectator retention; reactive alcohol center becomes planar" if option["mechanism"] == "Alcohol oxidation" else
                             "validated spectator retention; new centers unassigned" if option["mechanism"] in {"Hydrogenation", "Carbonyl hydrogenation", "Hydration"} else
                    "validated distant retention; bounded local anti E/Z" if option["mechanism"] == "E2" else
                    "validated local anti alternatives and distant retention; unknown starting geometry stays unsigned" if option["mechanism"] == "Bromination" else
                    "validated same-face oxygen transfer and distant retention; unknown starting geometry stays unsigned" if option["mechanism"] == "Epoxidation" else "unsupported")
        hydrogenation = next(r for r in service.reaction_catalog()["reactions"] if r["mechanism"] == "Hydrogenation")
        self.assertEqual(hydrogenation["classifications"], ["Addition", "Reduction"])
