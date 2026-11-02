import unittest
from pathlib import Path
from rdkit import Chem
from tests.explorer_xtb_independent_pilot import starts

ROOT = Path(__file__).resolve().parents[1]

class IndependentStartsTests(unittest.TestCase):
    def test_random_starts_are_seeded_and_not_reference_coordinates(self):
        mol = Chem.SDMolSupplier(str(ROOT / 'public/molecules/zirconium-tetrachloride-gas-reference.sdf'), removeHs=False)[0]
        samples = [starts(mol, 0, [1, 2, 3, 4], seed) for seed in range(1, 9)]
        self.assertEqual(len(set(samples)), 8)
        self.assertEqual(samples[0], starts(mol, 0, [1, 2, 3, 4], 1))
        self.assertNotEqual(samples[0], Chem.MolToXYZBlock(mol))

    def test_unmapped_atoms_rejected(self):
        mol = Chem.MolFromSmiles('O.C')
        with self.assertRaises(ValueError): starts(mol, 0, [], 1)
