import unittest
from pathlib import Path
from rdkit import Chem


class AluminumReferenceGeometryTests(unittest.TestCase):
    def test_nist_monomer_graph_charge_and_bond_lengths(self):
        path = Path(__file__).resolve().parents[1] / 'public/molecules/aluminum-trichloride-nist-reference.sdf'
        molecule = next(iter(Chem.SDMolSupplier(str(path), removeHs=False)))
        self.assertIsNotNone(molecule)
        self.assertEqual(Chem.MolToSmiles(molecule, isomericSmiles=False), '[Cl][Al]([Cl])[Cl]')
        self.assertEqual(sum(a.GetFormalCharge() for a in molecule.GetAtoms()), 0)
        self.assertEqual(molecule.GetNumBonds(), 3)
        conf = molecule.GetConformer()
        for i in range(1, 4):
            self.assertAlmostEqual((conf.GetAtomPosition(i) - conf.GetAtomPosition(0)).Length(), 2.06, places=3)


if __name__ == '__main__':
    unittest.main()
