"""Names are presentation only: identity, maps and condition gates stay intact."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service
from server.product_naming import simple_product_name
from server.reaction_engine import generate_pair


class ProductNamingTests(unittest.TestCase):
    def test_independent_simple_chain_names(self):
        cases = {
            'CCCCCO': 'Pentan-1-ol', 'CCCC(O)CC': 'Hexan-3-ol',
            'CCCCCC': 'Hexane', 'C=CCCC': 'Pent-1-ene', 'CCC#CC': 'Pent-2-yne',
            'CCCCC=O': 'Pentanal', 'CCCC(=O)C': 'Pentan-2-one',
            'CCCCC(=O)O': 'Pentanoic acid', 'OCCCO': 'Propane-1,3-diol',
            'BrCCCC': '1-bromobutane', 'BrCC(Br)C': '1,2-dibromopropane',
            'ClCC(Cl)C': '1,2-dichloropropane', 'CC(Br)(Br)CC': '2,2-dibromobutane',
            'FCCCCCO': '5-fluoropentan-1-ol',
        }
        for smiles, expected in cases.items():
            with self.subTest(smiles=smiles):
                self.assertEqual(simple_product_name(smiles), expected)

    def test_specified_stereo_is_named_without_assigning_unspecified_stereo(self):
        self.assertEqual(simple_product_name('BrC[C@H](Br)C'), '(2R)-1,2-dibromopropane')
        self.assertEqual(simple_product_name('BrC[C@@H](Br)C'), '(2S)-1,2-dibromopropane')
        self.assertEqual(simple_product_name('BrCC(Br)C'), '1,2-dibromopropane')
        self.assertEqual(simple_product_name('C/C=C/C'), '(2E)-but-2-ene')
        self.assertEqual(simple_product_name('C/C=C\\C'), '(2Z)-but-2-ene')
        self.assertEqual(simple_product_name('CC=CC'), 'But-2-ene')

    def test_numbering_and_names_are_independent_of_atom_order(self):
        for smiles in ['CCCCCO', 'CCC(O)CCC', 'BrC[C@H](Br)C', 'C/C=C/C', 'CC(Cl)CCBr']:
            mol = Chem.MolFromSmiles(smiles)
            reversed_mol = Chem.RenumberAtoms(mol, list(reversed(range(mol.GetNumAtoms()))))
            other = Chem.MolToSmiles(reversed_mol, canonical=False)
            with self.subTest(smiles=smiles):
                self.assertEqual(simple_product_name(smiles), simple_product_name(other))

    def test_maps_and_explicit_hydrogen_do_not_change_cip_or_names(self):
        mol = Chem.AddHs(Chem.MolFromSmiles('BrC[C@H](Br)C'))
        for i, atom in enumerate(mol.GetAtoms()): atom.SetAtomMapNum(99 - i)
        self.assertEqual(simple_product_name(Chem.MolToSmiles(mol)), '(2R)-1,2-dibromopropane')

    def test_unsupported_structures_do_not_receive_guessed_names(self):
        for smiles in ['CC(C)CCO', 'OC1CCCCC1', 'c1ccccc1O', 'COC', 'CC(=O)OCC',
                       'CC(=O)Cl', 'O=C(Cl)Cl', '[13CH3]CO', '[Na+].[O-]C=O',
                       'C[O-]', 'CN', 'C=CCO', 'C=CC=C', 'C' * 11, 'not-smiles']:
            with self.subTest(smiles=smiles):
                self.assertIsNone(simple_product_name(smiles))

    def test_display_namer_never_mutates_an_input_graph(self):
        mol = Chem.MolFromSmiles('BrC[C@H](Br)C')
        before = Chem.MolToSmiles(mol)
        simple_product_name(before)
        self.assertEqual(Chem.MolToSmiles(mol), before)

    def test_public_match_run_diagram_and_calculation_use_same_name(self):
        first, second, conditions = {'smiles': 'CCCCCBr'}, 'hydroxide', {'solvent': 'polar-aprotic'}
        option = next(r for r in service.match_reactions(first, second, conditions)['reactions'] if r['mechanism'] == 'SN2')
        self.assertEqual(option['productName'], 'Pentan-1-ol')
        self.assertEqual(option['stoichiometry']['product']['name'], 'Pentan-1-ol')
        self.assertEqual(option['productSmiles'], 'CCCCCO')
        diagram = service.reaction_diagram(option['id'], first, second, conditions)
        self.assertIn('Pentan-1-ol', diagram['svg'])
        result = service.run_curated_reaction(option['id'], first, second, conditions)
        self.assertEqual(result['productName'], 'Pentan-1-ol')
        self.assertTrue(result['balanced'])

    def test_bromination_enantiomers_have_distinct_graph_derived_names(self):
        options = service.match_reactions('propene', 'bromine', {'solvent': 'dry'})['reactions']
        names = {r['productName'] for r in options if r['mechanism'] == 'Bromination'}
        self.assertEqual(names, {'(2R)-1,2-dibromopropane', '(2S)-1,2-dibromopropane'})

    def test_naming_failure_does_not_change_structural_results_or_permissions(self):
        first, second, conditions = {'smiles': 'CCCCCBr'}, 'hydroxide', {'solvent': 'polar-aprotic'}
        normal = service.match_reactions(first, second, conditions)['reactionOptions']
        with patch('server.reaction_engine.simple_product_name', return_value=None):
            legacy = service.match_reactions(first, second, conditions)['reactionOptions']
        for before, after in zip(legacy, normal):
            for field in ['id', 'productSmiles', 'assessment', 'site', 'regioselectivity']:
                self.assertEqual(before.get(field), after.get(field))
            self.assertEqual(before['stoichiometry']['product']['molarMass'], after['stoichiometry']['product']['molarMass'])

    def test_exact_reviewed_names_keep_precedence(self):
        result = service.match_reactions('bromomethane', 'hydroxide', {'solvent': 'polar-aprotic'})['reactions']
        self.assertEqual(result[0]['productName'], 'Methanol')
        catalog = {'a': {'smiles': 'CCCCCBr', 'name': 'input'}, 'b': service.REACTANTS['hydroxide']}
        reactions, _ = generate_pair('a', 'b', catalog, {'CCCCCO': 'Exact identity label'})
        self.assertEqual(next(r for r in reactions.values() if r['mechanism'] == 'SN2')['productName'], 'Exact identity label')


if __name__ == '__main__': unittest.main()
