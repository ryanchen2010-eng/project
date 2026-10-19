"""Integration checks for the selected-pathway 2D preview API."""

import unittest
from unittest.mock import patch

from rdkit import Chem

from server.chemistry_server import ChemistryError, REACTANTS, _all_reactions, match_reactions, reaction_diagram, run_curated_reaction
from server.reaction_diagrams import mapped_product_molecule


class ReactionPreviewAPITests(unittest.TestCase):
    def assert_exact_atom_links(self, preview, product, expected_molecule):
        molecule = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
        self.assertIsNotNone(molecule)
        actual_links = [{"index": atom.GetIdx(), "mapId": atom.GetAtomMapNum(), "element": atom.GetSymbol()}
                        for atom in molecule.GetAtoms()]
        self.assertEqual(product["atomLinks"], actual_links)
        self.assertEqual(len(actual_links), product["atoms"])
        self.assertTrue(all(link["mapId"] > 0 for link in actual_links))
        self.assertEqual(len({link["mapId"] for link in actual_links}), len(actual_links))
        diagram_atoms = [atom for atom in preview["atoms"] if atom["side"] == "products" and atom["speciesIndex"] == 0]
        self.assertEqual([(atom["atomIndex"], atom["mapId"], atom["element"]) for atom in diagram_atoms],
                         [(link["index"], link["mapId"], link["element"]) for link in actual_links])
        self.assertTrue(all(atom["linkedTo3D"] for atom in diagram_atoms))
        def bonds(mol):
            return {(tuple(sorted((bond.GetBeginAtom().GetAtomMapNum(), bond.GetEndAtom().GetAtomMapNum()))),
                     bond.GetBondTypeAsDouble()) for bond in mol.GetBonds()}
        self.assertEqual(bonds(molecule), bonds(expected_molecule))
        self.assertEqual([atom.GetAtomMapNum() for atom in molecule.GetAtoms()],
                         [atom.GetAtomMapNum() for atom in expected_molecule.GetAtoms()])
        self.assertNotIn(":", product["smiles"])
        self.assertIn("H", [link["element"] for link in actual_links])

    def test_all_pathways_link_the_exact_explicit_h_molfile_atoms(self):
        for identifier, reaction in _all_reactions().items():
            with self.subTest(reaction=identifier):
                preview = reaction_diagram(identifier, *reaction["reactants"])
                conditions = {"catalyst": "acid"} if reaction["mechanism"] == "Hydration" else {"solvent": "dry"} if reaction["mechanism"] in {"Bromination", "Epoxidation"} else None
                if reaction.get("secondaryOxidationModel"):
                    with self.assertRaises(ChemistryError):run_curated_reaction(identifier,*reaction["reactants"],conditions)
                    conditions={"solvent":"aqueous-protic","temperature":"ambient","catalyst":"none","oxidationStage":"first","secondaryOxidationProfile":"naocl-acetic-ketone-v1"}
                result = run_curated_reaction(identifier, *reaction["reactants"], conditions)
                self.assert_exact_atom_links(preview, result["product"], mapped_product_molecule(reaction, REACTANTS))

    def test_preview_does_not_require_a_3d_calculation(self):
        with patch("server.chemistry_server.analyze_molfile", side_effect=AssertionError("3D must be separate")):
            result = reaction_diagram("sn2-bromomethane", "bromomethane", "hydroxide")
        self.assertTrue(result["highlightsAvailable"])
        self.assertEqual([item["name"] for item in result["products"]], ["Methanol", "Bromide ion"])

    def test_reverse_input_order_preserves_the_diagram(self):
        forward = reaction_diagram("e2-bromoethane", "bromoethane", "hydroxide")
        reverse = reaction_diagram("e2-bromoethane", "hydroxide", "bromoethane")
        self.assertEqual(forward, reverse)
        product_forward = run_curated_reaction("e2-bromoethane", "bromoethane", "hydroxide")["product"]
        product_reverse = run_curated_reaction("e2-bromoethane", "hydroxide", "bromoethane")["product"]
        self.assertEqual(product_forward["molfile"], product_reverse["molfile"])
        self.assertEqual(product_forward["atomLinks"], product_reverse["atomLinks"])

    def test_sodium_hydroxide_uses_the_same_ionic_equation(self):
        result = reaction_diagram("sn2-bromomethane", "bromomethane", "sodium-hydroxide")
        ionic = reaction_diagram("sn2-bromomethane", "bromomethane", "hydroxide")
        self.assertEqual(result["svg"], ionic["svg"])
        self.assertIn("Na⁺ is omitted", result["interpretationNotes"][0])

    def test_unlisted_drawn_structure_keeps_its_generated_pathway(self):
        substrate = {"smiles": "CCCBr"}
        matches = match_reactions(substrate, "hydroxide")["reactions"]
        for reaction in matches:
            with self.subTest(mechanism=reaction["mechanism"]):
                result = reaction_diagram(reaction["id"], substrate, "hydroxide")
                self.assertTrue(result["highlightsAvailable"])
                self.assertIn(result["products"][0]["smiles"], {"CCCO", "C=CC"})
                product = run_curated_reaction(reaction["id"], substrate, "hydroxide")["product"]
                molecule = Chem.MolFromMolBlock(product["molfile"], removeHs=False)
                self.assertEqual([atom["mapId"] for atom in result["atoms"]
                                  if atom["side"] == "products" and atom["speciesIndex"] == 0],
                                 [atom.GetAtomMapNum() for atom in molecule.GetAtoms()])

    def test_unrelated_pathway_and_invalid_conditions_are_rejected(self):
        with self.assertRaises(ChemistryError):
            reaction_diagram("bromination", "bromomethane", "hydroxide")
        with self.assertRaises(ChemistryError):
            reaction_diagram("sn2-bromomethane", "bromomethane", "hydroxide", {"catalyst": "invented"})


if __name__ == "__main__":
    unittest.main()
