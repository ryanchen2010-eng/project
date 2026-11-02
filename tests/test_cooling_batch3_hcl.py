"""Exact source-reference cooling profile; not general HX selectivity."""
import copy
import unittest
from rdkit import Chem
from server import chemistry_server as s, reaction_temperature_profiles as profiles
from server.reaction_conditions import cooling_confidence

MODEL = 'cooled-isobutylene-hcl-v1'
COLD = {'temperature':'cooled','solvent':'dry','catalyst':'none',
        'conditionProfileId':MODEL,'conditionProfileVersion':'1'}


def options(smiles='C=C(C)C', reagent='hydrogen-chloride', conditions=None):
    pair = ({'smiles':smiles}, reagent)
    c = COLD if conditions is None else conditions
    result = s.match_reactions(*pair,c)
    return pair, [o for o in result['reactionOptions'] if o['mechanism'] == 'Hydrohalogenation']


class Batch3HclReference(unittest.TestCase):
    def test_descriptor_and_explicit_reference(self):
        p = profiles.reviewed_profile(MODEL, 'Hydrohalogenation')
        self.assertTrue(p.explicit_only)
        d = next(x for x in profiles.named_profile_manifest()['profiles'] if x['id'] == MODEL)
        self.assertEqual(next(x['value'] for x in d['facts'] if x['field'] == 'medium'), 'recycled tert-butyl chloride')
        self.assertTrue(d['unknowns']); self.assertTrue(d['evidence'])

    def test_correct_net_graph_map_conservation_and_3d(self):
        for smiles in ('C=C(C)C','CC(=C)C'):
            pair, opts = options(smiles); self.assertEqual(len(opts),1); o=opts[0]
            self.assertEqual(o['productSmiles'],'CC(C)(C)Cl'); self.assertTrue(o['assessment']['canRun'])
            self.assertEqual(o['assessment']['namedConditionProfile']['selection'],'explicit')
            diagram=s.reaction_diagram(o['id'],*pair,COLD)
            before=[x for x in diagram['atoms'] if x['side']=='reactants']; after=[x for x in diagram['atoms'] if x['side']=='products']
            inventory=lambda rows:{x['mapId']:(x['element'],x['formalCharge']) for x in rows}
            self.assertEqual(inventory(before),inventory(after))
            self.assertEqual([(x['before'],x['after']) for x in diagram['bondOrderChanges']],[(2,1)])
            reagent_maps={x['mapId'] for x in before if x['speciesIndex']==1}
            self.assertEqual(len(reagent_maps),2)
            self.assertEqual(set(diagram['bondsBroken'][0]['atomMaps']),reagent_maps)
            self.assertEqual(len(diagram['bondsFormed']),2)
            self.assertEqual({m for bond in diagram['bondsFormed'] for m in bond['atomMaps']},reagent_maps|set(o['site']['atomMaps']))
            self.assertTrue(o['stoichiometry']['balanced'])
            self.assertEqual([x['coefficient'] for x in o['stoichiometry']['reactants']],[1,1])
            self.assertIsNone(diagram['mechanism'])
            result=s.run_curated_reaction(o['id'],*pair,COLD)['product']; self.assertEqual(result['representation'],'3d')
            mol=Chem.MolFromMolBlock(result['molfile'],removeHs=False)
            for atom in mol.GetAtoms(): atom.SetAtomMapNum(0)
            self.assertEqual(Chem.MolToSmiles(Chem.RemoveHs(mol)),'CC(C)(C)Cl')
            self.assertEqual({(x['atomIndex'],x['mapId'],x['element']) for x in after},
                             {(x['index'],x['mapId'],x['element']) for x in result['atomLinks']})

    def test_missing_profile_is_conditional_and_guide_requires_confirmation(self):
        c={'temperature':'cooled','solvent':'dry','catalyst':'none'}
        pair,opts=options(conditions=c); o=opts[0]
        self.assertFalse(o['assessment']['canRun']); self.assertTrue(o['guidedConditions']['requireConfirmation'])
        self.assertTrue(o['guidedConditions']['canApply'])
        self.assertNotIn('temperature',o['guidedConditions']['targetConditions'])
        with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o['id'],*pair,c)

    def test_wrong_structures_and_conditions_do_not_qualify(self):
        for smiles in ('C=C','C=CC','CC=CC','C=C(C)CC'):
            pair,opts=options(smiles)
            for o in opts:
                self.assertFalse(o['assessment']['canRun'])
                with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o['id'],*pair,COLD)
        for change in ({'solvent':'aqueous-protic'},{'solvent':'polar-aprotic'},{'catalyst':'radical'},
                       {'temperature':'ambient'},{'conditionProfileVersion':'2'},{'pressure':'1 atm'}, {'workup':'aqueous-release'}):
            c={**COLD,**change}; pair,opts=options(conditions=c)
            for o in opts:
                self.assertFalse(o['assessment']['canRun'])
                with self.assertRaises(s.ChemistryError): s.run_curated_reaction(o['id'],*pair,c)
        for reagent in ('hydrogen-bromide','hydrogen-iodide'):
            _,opts=options(reagent=reagent)
            for o in opts: self.assertFalse(o['assessment']['canRun'])

    def test_cached_permission_is_bound_to_identity(self):
        pair,opts=options(); cached=copy.deepcopy(opts[0]['assessment'])
        ids,custom,_=s._resolve_reactants(*pair)
        reaction=s._reactions_for_pair(*ids,{**s.REACTANTS,**custom},s._conditions(COLD))[0][opts[0]['id']]
        for field in ('hydrohalogenationSubstrateIdentity','hydrohalogenationReagentIdentity','compatibility'):
            altered=copy.deepcopy(reaction); altered.pop(field)
            self.assertFalse(cooling_confidence(cached,COLD,altered)['canRun'])


if __name__ == '__main__': unittest.main()
