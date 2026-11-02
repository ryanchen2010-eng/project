import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Geometry import Point3D
from server import nist_molecular_reference as ref
from server import chemistry_server as service


def aluminum_sdf():
    mol = Chem.MolFromSmiles('Cl[Al](Cl)Cl')
    conf = Chem.Conformer(mol.GetNumAtoms())
    positions = [(0, 2.06, 0), (0, 0, 0), (1.784, -1.03, 0), (-1.784, -1.03, 0)]
    for i, position in enumerate(positions):
        conf.SetAtomPosition(i, Point3D(*position))
    conf.Set3D(True)
    mol.AddConformer(conf)
    return Chem.MolToMolBlock(mol) + '\n> <METHOD>\nB3LYP/6-31G*\n\n$$$$\n'


class NistExactReferenceTests(unittest.TestCase):
    def test_validates_graph_and_rejects_other_species(self):
        sdf = aluminum_sdf()
        self.assertTrue(ref.validate_exact_graph('Cl[Al](Cl)Cl', sdf))
        for bad in ('Cl[Ga](Cl)Cl', '[Al+3].[Cl-].[Cl-].[Cl-]', '[37Cl][Al](Cl)Cl', 'Cl[Al](Cl)Cl.O', 'CCC'):
            with self.subTest(bad=bad):
                self.assertFalse(ref.validate_exact_graph(bad, sdf))

    def test_exact_identifier_and_safe_source_required(self):
        inchi = 'InChI=1S/Al.3ClH/h;3*1H/q+3;;;/p-3'
        key = 'VSCWAEJMTAWNJL-UHFFFAOYSA-K'
        page = f'<span class="inchi-text">{inchi}</span><span class="inchi-text">{key}</span><a href="/cgi/cbook.cgi?Str3File=C7446700">3d</a>'
        with patch.object(ref, '_read', side_effect=[page, aluminum_sdf()]):
            result = ref.lookup('Cl[Al](Cl)Cl', inchi, key)
        self.assertEqual(result['method'], 'B3LYP/6-31G*')
        with patch.object(ref, '_read', return_value=page.replace(inchi, 'InChI=1S/other')):
            self.assertIsNone(ref.lookup('Cl[Al](Cl)Cl', inchi, key))
        with patch.object(ref, '_read', return_value=page + '<a href="?Str3File=C9999999">another</a>'):
            self.assertIsNone(ref.lookup('Cl[Al](Cl)Cl', inchi, key))
        self.assertIsNone(ref.lookup('Cl[Al](Cl)Cl', inchi, 'https://evil.invalid'))

    def test_backend_requires_matching_cid(self):
        payload = {'PropertyTable': {'Properties': [{'CID': 12, 'SMILES': 'Cl[Al](Cl)Cl', 'InChI': 'fake', 'InChIKey': 'fake'}]}}
        with patch.object(service.pubchem_service, '_request_json', return_value=payload), patch.object(ref, 'lookup') as lookup:
            self.assertIsNone(service.resolve_nist_molecular_reference(13))
            lookup.assert_not_called()

    def test_computed_reference_without_method_is_explicitly_unknown(self):
        inchi = 'InChI=1S/Al.3ClH/h;3*1H/q+3;;;/p-3'
        key = 'VSCWAEJMTAWNJL-UHFFFAOYSA-K'
        page = (f'<span class="inchi-text">{inchi}</span><span class="inchi-text">{key}</span>'
                '<a href="/chemistry/3d-structs/">computed</a>\n'
                '<a href="/cgi/cbook.cgi?Str3File=C7446700">3d SD file</a>')
        sdf = aluminum_sdf().replace('> <METHOD>\nB3LYP/6-31G*\n\n', '')
        with patch.object(ref, '_read', side_effect=[page, sdf]):
            result = ref.lookup('Cl[Al](Cl)Cl', inchi, key)
        self.assertEqual(result['method'], 'Not reported by NIST')
        with patch.object(ref, '_read', side_effect=[page.replace('computed', 'experimental'), sdf]):
            self.assertIsNone(ref.lookup('Cl[Al](Cl)Cl', inchi, key))
        with patch.object(ref, '_read', side_effect=[page, sdf]):
            self.assertIsNone(ref.lookup('Cl[Ga](Cl)Cl', inchi, key))
