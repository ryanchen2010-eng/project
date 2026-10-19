"""Behavior checks for net-reaction diagrams and verified bond changes."""

import re
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from math import hypot

from rdkit import Chem

from server.chemistry_server import REACTANTS, _all_reactions, _resolve_reactants
from server.reaction_diagrams import COLORS, _lone_pairs, build_reaction_diagram, mapped_product_molecule


def change_set(diagram):
    return Counter((change["kind"], tuple(sorted(change["atoms"])), change["before"], change["after"])
                   for change in diagram["changes"])


class ReactionDiagramTests(unittest.TestCase):
    def diagram(self, identifier):
        return build_reaction_diagram(_all_reactions()[identifier], REACTANTS)

    def test_every_supported_pathway_has_valid_highlights_and_all_net_species(self):
        for identifier, reaction in _all_reactions().items():
            with self.subTest(reaction=identifier):
                result = build_reaction_diagram(reaction, REACTANTS)
                self.assertTrue(result["highlightsAvailable"])
                self.assertTrue(result["changes"])
                self.assertEqual([item["name"] for item in result["products"]],
                                 [reaction["productName"], *[item["name"] for item in reaction["byproducts"]]])
                expected_inputs = reaction.get("equationReactants", reaction["reactants"])
                self.assertEqual([item["name"] for item in result["reactants"]],
                                 [REACTANTS[identifier]["name"] for identifier in expected_inputs])
                expected_smiles = [reaction["productSmiles"], *[item["smiles"] for item in reaction["byproducts"]]]
                self.assertEqual([item["smiles"] for item in result["products"]],
                                 [Chem.MolToSmiles(Chem.MolFromSmiles(smiles), canonical=True) for smiles in expected_smiles])
                for change in result["changes"]:
                    self.assertEqual(set(change), {"kind", "atomMaps", "atoms", "before", "after", "label"})
                    self.assertEqual(len(change["atomMaps"]), 2)
                    self.assertTrue(all(isinstance(value, int) and value > 0 for value in change["atomMaps"]))
                root = ET.fromstring(result["svg"])
                self.assertEqual(root.attrib["viewBox"], "0 0 800 660")
                self.assertNotIn("<script", result["svg"])
                for legend in result["legend"]:
                    self.assertEqual(set(legend), {"kind", "label", "color"})
                    self.assertIn(legend["color"].upper(), result["svg"].upper())
                self.assertEqual({legend["kind"] for legend in result["legend"]},
                                 {change["kind"] for change in result["changes"]})
                self.assertIn("Net bond changes", result["note"])

    def test_every_atom_including_hydrogen_has_an_explicit_unique_target(self):
        for identifier, reaction in _all_reactions().items():
            with self.subTest(reaction=identifier):
                result = build_reaction_diagram(reaction, REACTANTS)
                root = ET.fromstring(result["svg"])
                targets = [node for node in root.iter() if node.attrib.get("class") == "atom-target"]
                keys = lambda item: (item["side"], item["speciesIndex"], item["mapId"])
                metadata = {keys(item): item for item in result["atoms"]}
                self.assertEqual(len(metadata), len(result["atoms"]))
                self.assertEqual(len(targets), len(metadata))
                target_keys = set()
                for target in targets:
                    key = (target.attrib["data-side"], int(target.attrib["data-species-index"]),
                           int(target.attrib["data-atom-map"]))
                    target_keys.add(key)
                    atom = metadata[key]
                    self.assertEqual(target.attrib["data-element"], atom["element"])
                    self.assertEqual(target.attrib["role"], "button")
                    self.assertEqual(target.attrib["tabindex"], "0")
                    self.assertIn(atom["speciesName"], target.attrib["aria-label"])
                    circles = {child.attrib["class"]: child for child in target}
                    self.assertEqual(set(circles), {"atom-glow", "atom-hit"})
                    self.assertEqual(circles["atom-glow"].attrib["cx"], circles["atom-hit"].attrib["cx"])
                    self.assertEqual(circles["atom-glow"].attrib["cy"], circles["atom-hit"].attrib["cy"])
                    self.assertEqual(circles["atom-hit"].attrib["pointer-events"], "all")
                self.assertEqual(target_keys, set(metadata))
                before = {atom["mapId"]: atom["element"] for atom in result["atoms"] if atom["side"] == "reactants"}
                after = {atom["mapId"]: atom["element"] for atom in result["atoms"] if atom["side"] == "products"}
                self.assertEqual(before, after)
                self.assertIn("H", before.values())
                product = mapped_product_molecule(reaction, REACTANTS)
                product_maps = {atom.GetAtomMapNum() for atom in product.GetAtoms()}
                self.assertEqual({atom["mapId"] for atom in result["atoms"] if atom["linkedTo3D"]}, product_maps)
                self.assertTrue(all(atom["linkedTo3D"] == (atom["speciesIndex"] == 0)
                                    for atom in result["atoms"] if atom["side"] == "products"))

    def test_colored_bonds_stop_before_atom_labels(self):
        for identifier in _all_reactions():
            with self.subTest(reaction=identifier):
                result = self.diagram(identifier)
                metadata = {(atom["side"], atom["speciesIndex"], atom["mapId"]): atom["atomIndex"]
                            for atom in result["atoms"]}
                colored_strokes = 0
                for group in ET.fromstring(result["svg"]):
                    if not group.tag.endswith("g"):
                        continue
                    centers = {}
                    for target in group:
                        if target.attrib.get("class") != "atom-target":
                            continue
                        key = (target.attrib["data-side"], int(target.attrib["data-species-index"]),
                               int(target.attrib["data-atom-map"]))
                        hit = next(node for node in target if node.attrib.get("class") == "atom-hit")
                        centers[metadata[key]] = (float(hit.attrib["cx"]), float(hit.attrib["cy"]))
                    for path in group:
                        classes = path.attrib.get("class", "")
                        style = path.attrib.get("style", "").lower()
                        if "bond-" not in classes or not any(
                                f"stroke:{color.lower()}" in style for color in COLORS.values()):
                            continue
                        # A filled center-to-center polygon can remain visible
                        # through O/C glyphs even when it is drawn behind them.
                        self.assertIn("fill:none", style)
                        points = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", path.attrib["d"])))
                        atom_indexes = list(map(int, re.findall(r"atom-(\d+)", classes)))
                        self.assertEqual(len(atom_indexes), 2)
                        for x, y in ((points[0], points[1]), (points[-2], points[-1])):
                            for index in atom_indexes:
                                atom_x, atom_y = centers[index]
                                self.assertGreater(hypot(x - atom_x, y - atom_y), 5)
                        colored_strokes += 1
                self.assertGreater(colored_strokes, 0)

    def test_lone_pairs_and_charges_are_explicit_for_standard_closed_shell_species(self):
        hydroxide = [item for item in self.diagram("sn2-bromomethane")["atoms"]
                     if item["side"] == "reactants" and item["element"] == "O"][0]
        self.assertEqual((hydroxide["formalCharge"], hydroxide["lonePairs"]), (-1, 3))
        bromide = [item for item in self.diagram("sn2-bromomethane")["atoms"]
                   if item["side"] == "products" and item["element"] == "Br"][0]
        self.assertEqual((bromide["formalCharge"], bromide["lonePairs"]), (-1, 4))
        sodium = [item for item in self.diagram("oxidation-2-propanol")["atoms"]
                  if item["element"] == "Na"]
        self.assertTrue(all(item["formalCharge"] == 1 and item["lonePairs"] is None for item in sodium))
        for smiles in ("O", "[OH-]", "[Br-]", "C=O", "N"):
            molecule = Chem.AddHs(Chem.MolFromSmiles(smiles))
            for atom in molecule.GetAtoms():
                expected = {"O": 2, "[OH-]": 3, "[Br-]": 4, "C=O": 2, "N": 1}[smiles]
                self.assertEqual(_lone_pairs(atom), expected if atom.GetSymbol() in {"O", "Br", "N"} else 0)
        for smiles in ("[CH3]", "[Fe+2]", "c1ccncc1"):
            molecule = Chem.AddHs(Chem.MolFromSmiles(smiles))
            self.assertTrue(all(_lone_pairs(atom) is None for atom in molecule.GetAtoms() if atom.GetSymbol() != "H"))
        result = self.diagram("sn2-bromomethane")
        dots = [node for node in ET.fromstring(result["svg"]).iter()
                if node.attrib.get("class") == "lewis-electron"]
        self.assertEqual(len(dots), 2 * sum(atom["lonePairs"] or 0 for atom in result["atoms"]))

    def test_sn2_breaks_carbon_halogen_and_forms_carbon_oxygen(self):
        result = self.diagram("sn2-bromoethane")
        self.assertEqual(change_set(result), Counter({
            ("broken", ("Br", "C"), 1, None): 1,
            ("formed", ("C", "O"), None, 1): 1,
        }))
        self.assertEqual(result["products"][1]["smiles"], "[Br-]")

    def test_e2_includes_beta_hydrogen_transfer_to_base(self):
        result = self.diagram("e2-bromoethane")
        self.assertEqual(change_set(result), Counter({
            ("broken", ("Br", "C"), 1, None): 1,
            ("broken", ("C", "H"), 1, None): 1,
            ("order", ("C", "C"), 1, 2): 1,
            ("formed", ("H", "O"), None, 1): 1,
        }))
        self.assertEqual([item["smiles"] for item in result["products"]], ["C=C", "O", "[Br-]"])

    def test_hydrogenation_shows_hydrogen_bond_break_and_two_carbon_hydrogen_bonds(self):
        result = self.diagram("hydrogenation")
        self.assertEqual(change_set(result), Counter({
            ("broken", ("H", "H"), 1, None): 1,
            ("order", ("C", "C"), 2, 1): 1,
            ("formed", ("C", "H"), None, 1): 2,
        }))

    def test_bromination_shows_reagent_and_both_bromine_additions(self):
        result = self.diagram("bromination")
        self.assertEqual(change_set(result), Counter({
            ("broken", ("Br", "Br"), 1, None): 1,
            ("order", ("C", "C"), 2, 1): 1,
            ("formed", ("Br", "C"), None, 1): 2,
        }))

    def test_hydration_includes_water_hydrogen_transfer(self):
        result = self.diagram("hydration")
        self.assertEqual(change_set(result), Counter({
            ("broken", ("H", "O"), 1, None): 1,
            ("order", ("C", "C"), 2, 1): 1,
            ("formed", ("C", "H"), None, 1): 1,
            ("formed", ("C", "O"), None, 1): 1,
        }))

    def test_e1_does_not_consume_selected_water_solvent(self):
        result = self.diagram("e1-tert-butyl-chloride")
        self.assertEqual([item["name"] for item in result["reactants"]], ["2-Chloro-2-methylpropane"])
        self.assertEqual(result["medium"], [{"name": "Water", "role": "medium"}])
        self.assertEqual([item["smiles"] for item in result["products"]], ["C=C(C)C", "Cl"])

    def test_oxidation_keeps_salt_and_water_byproducts(self):
        result = self.diagram("oxidation-2-propanol")
        self.assertEqual([item["smiles"] for item in result["products"]],
                         ["CC(C)=O", "[Cl-].[Na+]", "O"])
        self.assertEqual(result["products"][1]["formula"], "ClNa")

    def test_rule_generated_drawings_have_highlights_in_either_entry_order(self):
        examples = [("CCCBr", "hydroxide", "SN2"), ("CCCBr", "hydroxide", "E2"),
                    ("C=CCC", "hydrogen", "Hydrogenation"), ("C=CCC", "bromine", "Bromination")]
        for smiles, reagent, mechanism in examples:
            for reverse in (False, True):
                with self.subTest(smiles=smiles, mechanism=mechanism, reverse=reverse):
                    refs = ({"smiles": smiles}, reagent)
                    if reverse:
                        refs = refs[::-1]
                    pair, custom, _ = _resolve_reactants(*refs)
                    reaction = next(reaction for reaction in _all_reactions(custom).values()
                                    if sorted(reaction["reactants"]) == sorted(pair)
                                    and reaction["mechanism"] == mechanism)
                    result = build_reaction_diagram(reaction, {**REACTANTS, **custom})
                    self.assertTrue(result["highlightsAvailable"])
                    self.assertTrue(result["changes"])

    def test_sodium_hydroxide_normalization_uses_ionic_equation(self):
        pair, custom, notes = _resolve_reactants("bromoethane", "sodium-hydroxide")
        reaction = _all_reactions(custom)["e2-bromoethane"]
        self.assertEqual(pair, ("bromoethane", "hydroxide"))
        self.assertTrue(notes)
        result = build_reaction_diagram(reaction, {**REACTANTS, **custom})
        self.assertEqual(result["reactants"][1]["smiles"], "[OH-]")
        self.assertNotIn("Na", result["svg"])

    def test_different_product_cannot_receive_guessed_bond_highlights(self):
        reaction = {**_all_reactions()["sn2-bromoethane"], "productSmiles": "CO"}
        with self.assertRaisesRegex(ValueError, "failed validation"):
            build_reaction_diagram(reaction, REACTANTS)

    def test_invalid_structures_and_missing_species_are_rejected(self):
        for reaction in ({}, {**_all_reactions()["hydrogenation"], "productSmiles": "bad"},
                         {**_all_reactions()["hydrogenation"], "equationReactants": ["missing"]}):
            with self.subTest(reaction=reaction):
                with self.assertRaises(ValueError):
                    build_reaction_diagram(reaction, REACTANTS)

    def test_species_names_are_escaped_in_svg(self):
        catalog = {**REACTANTS, "ethene": {**REACTANTS["ethene"], "name": "<script>alert(1)</script>"}}
        result = build_reaction_diagram(_all_reactions()["hydrogenation"], catalog)
        self.assertNotIn("<script", result["svg"])
        self.assertIn("&lt;script&gt;", result["svg"])


if __name__ == "__main__":
    unittest.main()
