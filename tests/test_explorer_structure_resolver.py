import unittest
from unittest.mock import patch
from server import chemistry_server as service


class ExplorerResolverTests(unittest.TestCase):
    def test_pubchem_first_and_no_formula_substitution(self):
        with patch.object(service, 'get_pubchem_structure', return_value='source-sdf') as source, patch.object(service, 'get_pubchem_smiles') as smiles:
            structure, provenance = service.resolve_pubchem_structure(702)
        self.assertEqual(structure, 'source-sdf')
        self.assertEqual(provenance['kind'], 'calculated')
        self.assertEqual(provenance['source'], 'pubchem')
        source.assert_called_once_with(702)
        smiles.assert_not_called()

    def test_rdkit_converged_result_reports_method(self):
        with patch.object(service, 'get_pubchem_structure', return_value=None), patch.object(service, 'get_pubchem_smiles', return_value='CCO'):
            structure, provenance = service.resolve_pubchem_structure(702)
        self.assertTrue(structure)
        self.assertEqual(provenance['method'], 'MMFF94')
        self.assertEqual(provenance['convergence'], 'converged')

    def test_unsupported_is_not_promoted(self):
        with patch.object(service, 'get_pubchem_structure', return_value=None), patch.object(service, 'get_pubchem_smiles', return_value='Cl[Rh](Cl)Cl'):
            self.assertEqual(service.resolve_pubchem_structure(24872), (None, {}))


if __name__ == '__main__':
    unittest.main()
