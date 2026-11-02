"""Public-workflow checks for the shared-carbocation teaching example."""
import unittest

from rdkit import Chem
from server import chemistry_server as service


class TertiaryBromideComparison(unittest.TestCase):
    def test_both_paths_share_mapped_carbocation_and_correct_products(self):
        for temperature in ('ambient', 'heated'):
            with self.subTest(temperature=temperature):
                conditions = {'solvent': 'aqueous-protic', 'temperature': temperature}
                match = service.match_reactions('tert-butyl-bromide', 'water', conditions)
                options = {r['mechanism']: r for r in match['reactions']}
                self.assertTrue({'SN1', 'E1'} <= set(options))
                self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(options['SN1']['productSmiles'])), 'CC(C)(C)O')
                self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(options['E1']['productSmiles'])), 'C=C(C)C')
                mechanisms = [service.reaction_diagram(options[path]['id'], 'tert-butyl-bromide', 'water', conditions)['mechanism'] for path in ('SN1', 'E1')]
                self.assertEqual([len(m['steps']) for m in mechanisms], [3, 2])
                states = [m['steps'][0]['state'] for m in mechanisms]
                for state in states:
                    self.assertEqual([(a['mapId'], a['element'], a['formalCharge']) for a in state['atoms'] if a['formalCharge']], [(2, 'C', 1), (5, 'Br', -1)])
                # SN1 represents an additional solvent water for deprotonation;
                # compare the mapped substrate fragment, not all solvent molecules.
                substrate_bonds = lambda state: [bond for bond in state['bonds'] if max(bond['atomMaps']) <= 14]
                self.assertEqual(substrate_bonds(states[0]), substrate_bonds(states[1]))
                self.assertTrue(mechanisms[0]['steps'][-1]['protonTransfers'])
                self.assertTrue(mechanisms[1]['steps'][-1]['protonTransfers'])
                for path in ('SN1', 'E1'):
                    result = service.run_curated_reaction(options[path]['id'], 'tert-butyl-bromide', 'water', conditions)
                    self.assertTrue(result['balanced'])


if __name__ == '__main__':
    unittest.main()
