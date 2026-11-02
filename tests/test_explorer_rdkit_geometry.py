import math
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service
from server import explorer_rdkit_geometry as geometry


class ExplorerGeometryTests(unittest.TestCase):
    def test_supported_graphs_and_stereo(self):
        for smiles in ('CCO', 'C[C@H](O)CC', 'C/C=C/C', 'C/C=C\\C', 'C1CCCCC1', 'O=C=O'):
            with self.subTest(smiles=smiles):
                mol = Chem.MolFromSmiles(smiles)
                output = geometry.generate_fallback(mol, service.BUILDER_3D_ELEMENTS)
                self.assertIsNotNone(output)
                candidate = Chem.MolFromMolBlock(output['molfile'], removeHs=False)
                self.assertTrue(geometry.validate_geometry(mol, candidate))
                self.assertTrue(output['converged'])

    def test_bounded_retry_after_embedding_failure(self):
        original = geometry.AllChem.EmbedMolecule
        attempts = []
        def fail_first(mol, settings):
            attempts.append(settings.randomSeed)
            return -1 if len(attempts) == 1 else original(mol, settings)
        with patch.object(geometry.AllChem, 'EmbedMolecule', side_effect=fail_first):
            output = geometry.generate_fallback(Chem.MolFromSmiles('CCO'), service.BUILDER_3D_ELEMENTS)
        self.assertIsNotNone(output)
        self.assertEqual(attempts, [42, 1729])

    def test_all_unconverged_or_failed_models_rejected(self):
        for status in (1, -1):
            with self.subTest(status=status), patch.object(geometry.AllChem, 'MMFFOptimizeMolecule', return_value=status) as optimize:
                self.assertIsNone(geometry.generate_fallback(Chem.MolFromSmiles('CCO'), service.BUILDER_3D_ELEMENTS))
                self.assertEqual(optimize.call_count, 3)

    def test_invalid_coordinate_and_connectivity_rejected(self):
        mol = Chem.MolFromSmiles('CCO')
        output = geometry.generate_fallback(mol, service.BUILDER_3D_ELEMENTS)
        candidate = Chem.MolFromMolBlock(output['molfile'], removeHs=False)
        candidate.GetConformer().SetAtomPosition(0, (math.nan, 0, 0))
        self.assertFalse(geometry.validate_geometry(mol, candidate))
        self.assertFalse(geometry.validate_geometry(Chem.MolFromSmiles('CCC'), Chem.MolFromMolBlock(output['molfile'], removeHs=False)))

    def test_inverted_specified_stereo_is_rejected(self):
        mol = Chem.MolFromSmiles('C[C@H](O)CC')
        output = geometry.generate_fallback(mol, service.BUILDER_3D_ELEMENTS)
        candidate = Chem.MolFromMolBlock(output['molfile'], removeHs=False)
        conf = candidate.GetConformer()
        for index in range(candidate.GetNumAtoms()):
            point = conf.GetAtomPosition(index)
            conf.SetAtomPosition(index, (-point.x, point.y, point.z))
        self.assertFalse(geometry.validate_geometry(mol, candidate))

    def test_unsupported_policy_is_unchanged(self):
        for smiles in ('[Na+].[Cl-]', '[NH4+]', '[CH3]', 'Cl[Rh](Cl)Cl', 'Cl[Zr](Cl)(Cl)Cl'):
            with self.subTest(smiles=smiles):
                self.assertIsNone(geometry.generate_fallback(Chem.MolFromSmiles(smiles), service.BUILDER_3D_ELEMENTS))
