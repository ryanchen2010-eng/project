"""Trusted stoichiometry metadata for the Reaction Lab calculator."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from rdkit import Chem
from rdkit.Chem import Descriptors

from server import chemistry_server as chemistry


class ReactionStoichiometryTests(unittest.TestCase):
    def matches(self, first, second):
        return {item["id"]: item["stoichiometry"]
                for item in chemistry.match_reactions(first, second)["reactions"]}

    def test_every_catalog_pathway_has_balanced_unit_coefficient_metadata(self):
        catalog = chemistry.reaction_catalog()
        self.assertEqual(len(catalog["reactions"]), len(chemistry._all_reactions()))
        for reaction in catalog["reactions"]:
            with self.subTest(pathway=reaction["id"]):
                metadata = reaction["stoichiometry"]
                self.assertTrue(metadata["balanced"])
                self.assertEqual(len(metadata["reactants"]), len(reaction["equationReactants"]))
                self.assertEqual(metadata["product"]["name"], reaction["productName"])
                self.assertEqual(metadata["product"]["formula"], reaction["productFormula"])
                self.assertEqual(metadata["product"]["coefficient"], 1)
                self.assertGreater(metadata["product"]["molarMass"], 0)
                for item in metadata["reactants"]:
                    self.assertEqual(item["coefficient"], 1)
                    self.assertIn(item["inputSlot"], (0, 1))
                    self.assertGreater(item["molarMass"], 0)
                    self.assertTrue(item["name"])
                    self.assertTrue(item["formula"])
                self.assertTrue(metadata["notes"])

    def test_forward_and_reverse_inputs_keep_the_actual_input_slot(self):
        forward = self.matches("ethene", "hydrogen")["hydrogenation"]
        reverse = self.matches("hydrogen", "ethene")["hydrogenation"]
        self.assertEqual([(item["inputSlot"], item["name"]) for item in forward["reactants"]],
                         [(0, "Ethene"), (1, "Hydrogen")])
        self.assertEqual([(item["inputSlot"], item["name"]) for item in reverse["reactants"]],
                         [(0, "Hydrogen"), (1, "Ethene")])
        self.assertEqual(forward["product"], reverse["product"])

    def test_masses_come_from_structures_not_displayed_formula_strings(self):
        modified = {**chemistry.REACTANTS["bromomethane"], "formula": "incorrect-display-formula"}
        with patch.dict(chemistry.REACTANTS, {"bromomethane": modified}):
            metadata = self.matches("bromomethane", "hydroxide")["sn2-bromomethane"]
        mass = metadata["reactants"][0]["molarMass"]
        self.assertAlmostEqual(mass, Descriptors.MolWt(Chem.MolFromSmiles("CBr")), places=6)
        self.assertAlmostEqual(metadata["product"]["molarMass"], 32.042, places=3)

    def test_listed_sodium_hydroxide_uses_salt_not_hydroxide_mass(self):
        forward = self.matches("bromomethane", "sodium-hydroxide")["sn2-bromomethane"]
        reverse = self.matches("sodium-hydroxide", "bromomethane")["sn2-bromomethane"]
        for metadata, slot in ((forward, 1), (reverse, 0)):
            with self.subTest(slot=slot):
                salt = next(item for item in metadata["reactants"] if item["inputSlot"] == slot)
                self.assertEqual(salt["name"], "Sodium hydroxide")
                self.assertEqual(salt["formula"], "NaOH")
                self.assertAlmostEqual(salt["molarMass"], 39.997, places=3)
                self.assertEqual(salt["coefficient"], 1)
                self.assertTrue(metadata["balanced"])
                self.assertTrue(any("spectator Na⁺" in note for note in metadata["notes"]))

    def test_searched_and_drawn_alkali_hydroxides_preserve_full_salt_mass(self):
        for symbol, name in (("Li", "Lithium"), ("Na", "Sodium"), ("K", "Potassium"),
                             ("Rb", "Rubidium"), ("Cs", "Caesium")):
            reference = {"smiles": f"[OH-].[{symbol}+]", "name": "A supplied salt name"}
            for first, second, salt_slot in (("bromomethane", reference, 1),
                                             (reference, "bromomethane", 0)):
                with self.subTest(counterion=symbol, slot=salt_slot):
                    metadata = self.matches(first, second)["sn2-bromomethane"]
                    salt = next(item for item in metadata["reactants"] if item["inputSlot"] == salt_slot)
                    self.assertEqual(salt["name"], f"{name} hydroxide")
                    self.assertEqual(salt["formula"], f"{symbol}OH")
                    self.assertAlmostEqual(salt["molarMass"], Descriptors.MolWt(Chem.MolFromSmiles(reference["smiles"])), places=6)
                    self.assertTrue(metadata["balanced"])
                    self.assertTrue(any("1 mol supplies 1 mol OH⁻" in note for note in metadata["notes"]))

    def test_bare_hydroxide_keeps_ionic_mass_without_salt_note(self):
        metadata = self.matches("bromomethane", "hydroxide")["sn2-bromomethane"]
        hydroxide = metadata["reactants"][1]
        self.assertEqual(hydroxide["name"], "Hydroxide ion")
        self.assertAlmostEqual(hydroxide["molarMass"], 17.007, places=3)
        self.assertFalse(any("spectator" in note for note in metadata["notes"]))

    def test_e1_excludes_water_but_sn1_consumes_it_in_either_order(self):
        for first, second, water_slot, substrate_slot in (
                ("tert-butyl-chloride", "water", 1, 0),
                ("water", "tert-butyl-chloride", 0, 1)):
            with self.subTest(water_slot=water_slot):
                pathways = self.matches(first, second)
                e1 = pathways["e1-tert-butyl-chloride"]
                sn1 = pathways["sn1-tert-butyl-chloride"]
                self.assertEqual([item["inputSlot"] for item in e1["reactants"]], [substrate_slot])
                self.assertEqual(e1["excludedInputs"], [{"inputSlot": water_slot, "name": "Water",
                                                       "reason": "Solvent / medium; not consumed in this net equation."}])
                self.assertEqual(len(sn1["reactants"]), 2)
                self.assertEqual(sn1["excludedInputs"], [])
                self.assertTrue(e1["balanced"])

    def test_dynamic_alkyl_halide_pathways_have_structure_masses(self):
        drawing = {"smiles": "BrCCC", "name": "1-Bromopropane"}
        for first, second, slot in ((drawing, "hydroxide", 0), ("hydroxide", drawing, 1)):
            with self.subTest(slot=slot):
                pathways = self.matches(first, second)
                self.assertEqual(len(pathways), 2)
                for metadata in pathways.values():
                    self.assertTrue(metadata["balanced"])
                    substrate = next(item for item in metadata["reactants"] if item["inputSlot"] == slot)
                    self.assertEqual(substrate["name"], "1-Bromopropane")
                    self.assertEqual(substrate["formula"], "C3H7Br")
                    self.assertAlmostEqual(substrate["molarMass"], 122.993, places=3)

    def test_dynamic_alkene_pathways_and_tertiary_e1_are_balanced(self):
        for drawing, partner in (({"smiles": "C=CCCC"}, "hydrogen"),
                                 ({"smiles": "C=CCCC"}, "bromine"),
                                 ({"smiles": "CC(Br)(C)C"}, "water")):
            with self.subTest(drawing=drawing, partner=partner):
                metadata = list(self.matches(drawing, partner).values())
                self.assertTrue(metadata)
                self.assertTrue(all(item["balanced"] for item in metadata))

    def test_salt_coproducts_are_accounted_for_in_balance(self):
        metadata = self.matches("2-propanol", "sodium-hypochlorite")["oxidation-2-propanol"]
        self.assertTrue(metadata["balanced"])
        self.assertAlmostEqual(metadata["reactants"][1]["molarMass"], 74.442, places=3)
        self.assertAlmostEqual(metadata["product"]["molarMass"], 58.08, places=3)

    def test_atom_or_charge_imbalance_disables_calculation(self):
        original = chemistry.REACTIONS["sn2-bromomethane"]
        for byproducts in ([], [{"name": "Bromine atom", "smiles": "[Br]"}]):
            with self.subTest(byproducts=byproducts), patch.object(chemistry, "_reactions_for_pair", return_value=({
                    "sn2-bromomethane": {**original, "byproducts": byproducts}}, [])):
                metadata = self.matches("bromomethane", "hydroxide")["sn2-bromomethane"]
                self.assertFalse(metadata["balanced"])
                self.assertTrue(any("Calculation unavailable" in note for note in metadata["notes"]))

    def test_missing_consumed_input_disables_calculation(self):
        original = chemistry.REACTIONS["hydrogenation"]
        modified = {**original, "equationReactants": ("ethene", "hydrogen", "missing")}
        with patch.object(chemistry, "_reactions_for_pair", return_value=({"hydrogenation": modified}, [])):
            metadata = self.matches("ethene", "hydrogen")["hydrogenation"]
        self.assertFalse(metadata["balanced"])

    def test_metadata_never_runs_atom_mapping_or_3d_embedding(self):
        with patch.object(chemistry, "mapped_product_molecule", side_effect=AssertionError("No atom mapping needed")), \
                patch.object(chemistry, "analyze_molfile", side_effect=AssertionError("No 3D needed")), \
                patch.object(chemistry.AllChem, "EmbedMolecule", side_effect=AssertionError("No embedding needed")):
            self.assertTrue(self.matches("ethene", "hydrogen")["hydrogenation"]["balanced"])
            self.assertTrue(all(item["stoichiometry"]["balanced"] for item in chemistry.reaction_catalog()["reactions"]))

    def test_catalysts_and_reversible_reactions_have_calculation_limits(self):
        hydrogenation = self.matches("ethene", "hydrogen")["hydrogenation"]
        ester = self.matches("ethanoic-acid", "ethanol")["esterification"]
        self.assertTrue(any("Catalyst amounts are excluded" in note for note in hydrogenation["notes"]))
        self.assertTrue(any("reversible" in note for note in ester["notes"]))
        self.assertTrue(any("not a predicted or actual yield" in note for note in ester["notes"]))


if __name__ == "__main__":
    unittest.main()
