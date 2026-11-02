import math
import unittest
from pathlib import Path
from rdkit import Chem


class NistSulfurHexafluorideTest(unittest.TestCase):
    def test_exact_graph_charge_and_nist_coordinates(self):
        path = Path(__file__).resolve().parents[1] / 'public/molecules/sulfur-hexafluoride-nist-reference.sdf'
        mol = next(iter(Chem.SDMolSupplier(str(path), removeHs=False)))
        self.assertIsNotNone(mol)
        # The 3D parser may assign an octahedral ordering tag even though all
        # six ligands are identical; compare the chemical graph without it.
        self.assertEqual(Chem.MolToSmiles(mol, isomericSmiles=False), 'FS(F)(F)(F)(F)F')
        self.assertEqual(sum(a.GetFormalCharge() for a in mol.GetAtoms()), 0)
        self.assertEqual(mol.GetNumAtoms(), 7)
        self.assertEqual(mol.GetNumBonds(), 6)
        conf = mol.GetConformer()
        for i in range(1, 7):
            self.assertAlmostEqual((conf.GetAtomPosition(i) - conf.GetAtomPosition(0)).Length(), 1.5607, places=4)
        self.assertAlmostEqual((conf.GetAtomPosition(1) - conf.GetAtomPosition(2)).Length(), math.sqrt(2) * 1.5607, places=4)


if __name__ == '__main__':
    unittest.main()
