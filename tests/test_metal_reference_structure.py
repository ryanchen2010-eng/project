"""Validate the bounded, experimentally informed gas-phase reference."""
import math
import unittest
from pathlib import Path
from rdkit import Chem


class ZirconiumGasReferenceTest(unittest.TestCase):
    def test_tetrahedral_geometry_and_identity(self):
        path = Path(__file__).resolve().parents[1] / 'public/molecules/zirconium-tetrachloride-gas-reference.sdf'
        molecule = next(iter(Chem.SDMolSupplier(str(path), removeHs=False)))
        self.assertIsNotNone(molecule)
        self.assertEqual([a.GetSymbol() for a in molecule.GetAtoms()], ['Zr', 'Cl', 'Cl', 'Cl', 'Cl'])
        self.assertEqual(molecule.GetNumBonds(), 4)
        conf = molecule.GetConformer()
        vectors = [conf.GetAtomPosition(i) - conf.GetAtomPosition(0) for i in range(1, 5)]
        for v in vectors:
            self.assertAlmostEqual(v.Length(), 2.32, places=3)
        for i in range(4):
            for j in range(i + 1, 4):
                self.assertAlmostEqual(vectors[i].DotProduct(vectors[j]) / (vectors[i].Length() * vectors[j].Length()), -1 / 3, places=6)


if __name__ == '__main__':
    unittest.main()
