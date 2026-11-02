"""The base selector describes an existing reagent; it never supplies one."""
import unittest
from rdkit import Chem
from server import chemistry_server as s
from server.reaction_information import DEFINITIONS
from tests.test_cooling_profiles_v1 import PATHWAY_CASES


def options(a,b,conditions):
    return s.match_reactions(a,b,conditions)['reactionOptions']


class BasicConditionsTests(unittest.TestCase):
    def test_every_existing_reaction_type_is_considered(self):
        self.assertEqual({case[0] for case in PATHWAY_CASES},set(DEFINITIONS))
        self.assertEqual(len(DEFINITIONS),24)
        for path,smiles,reagent,settings in PATHWAY_CASES:
            with self.subTest(path=path,smiles=smiles):
                c={**settings,'temperature':'ambient','catalyst':'base'}
                pair=({'smiles':smiles},reagent)
                matched=[o for o in options(*pair,c) if o['mechanism']==path]
                self.assertTrue(matched, path)
                for o in matched:
                    diagram=s.reaction_diagram(o['id'],*pair,c)
                    self.assertEqual(diagram['assessment'],o['assessment'])
                    if path in {'SN2','E2','Ester saponification'}:
                        self.assertIsNot(o['assessment'].get('canRun'),False)
                        self.assertIn('actual hydroxide',o['assessment']['note'])
                    else:
                        self.assertFalse(o['assessment']['canRun'])
                        self.assertIn('not validated',o['assessment']['note'])
                        with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)

    def test_actual_hydroxide_is_still_required(self):
        c={'catalyst':'base','temperature':'ambient','solvent':'aqueous-protic'}
        for pair in (({'smiles':'CBr'},'water'),({'smiles':'CC(=O)OCC'},'water')):
            found=options(*pair,c)
            self.assertFalse(any(o['mechanism'] in {'SN2','E2','Ester saponification'} for o in found))

    def test_substitution_elimination_and_saponification_preserve_products_and_stoichiometry(self):
        fixtures=(('SN2',{'smiles':'CBr'},'hydroxide','CO'),
                  ('E2',{'smiles':'CCBr'},'hydroxide','C=C'),
                  ('Ester saponification',{'smiles':'CC(=O)OCC'},'hydroxide','CC(=O)[O-]'))
        c={'catalyst':'base','temperature':'ambient','solvent':'aqueous-protic'}
        for path,a,b,product in fixtures:
            with self.subTest(path=path):
                o=next(o for o in options(a,b,c) if o['mechanism']==path)
                self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(o['productSmiles'])),Chem.MolToSmiles(Chem.MolFromSmiles(product)))
                self.assertTrue(o['stoichiometry']['balanced'])
                self.assertEqual([r['coefficient'] for r in o['stoichiometry']['reactants']],[1,1])
                d=s.reaction_diagram(o['id'],a,b,c);self.assertIn('actual hydroxide',d['assessment']['note'])
                before=[x for x in d['atoms'] if x['side']=='reactants'];after=[x for x in d['atoms'] if x['side']=='products']
                inventory=lambda rows:{x['mapId']:x['element'] for x in rows}
                self.assertEqual(inventory(before),inventory(after))
                result=s.run_curated_reaction(o['id'],a,b,c)['product']
                self.assertEqual(result['representation'],'2d-only' if path=='Ester saponification' else '3d')
                if path=='Ester saponification':self.assertEqual(Chem.GetFormalCharge(Chem.MolFromSmiles(o['productSmiles'])),-1)

    def test_base_does_not_override_cooling_or_named_profile(self):
        c={'catalyst':'base','temperature':'cooled','solvent':'aqueous-protic'}
        o=next(o for o in options({'smiles':'CBr'},'hydroxide',c) if o['mechanism']=='SN2')
        self.assertFalse(o['assessment']['canRun'])
        with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],{'smiles':'CBr'},'hydroxide',c)
        c={'catalyst':'base','temperature':'cooled','solvent':'dry','conditionProfileId':'cooled-isobutylene-hcl-v1','conditionProfileVersion':'1'}
        for o in options({'smiles':'C=C(C)C'},'hydrogen-chloride',c):self.assertFalse(o['assessment']['canRun'])

    def test_sodium_hydroxide_calculator_keeps_full_salt_identity(self):
        c={'catalyst':'base','temperature':'ambient','solvent':'aqueous-protic'}
        o=next(o for o in options({'smiles':'CC(=O)OCC'},'sodium-hydroxide',c) if o['mechanism']=='Ester saponification')
        hydroxide=next(r for r in o['stoichiometry']['reactants'] if r['inputSlot']==1)
        self.assertEqual(hydroxide['formula'],'NaOH');self.assertAlmostEqual(hydroxide['molarMass'],39.997)
        self.assertEqual(Chem.GetFormalCharge(Chem.MolFromSmiles(o['productSmiles'])),-1)

if __name__=='__main__':unittest.main()
