"""R2 v1: exact parent/catalyst reference, not generalized cooled hydrogenation."""
from pathlib import Path
import copy
import secrets
import tempfile
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as s, reaction_temperature_profiles as profiles
from server.production_app import create_app
from server.reaction_conditions import cooling_confidence

MODEL = 'cooled-cyclohexene-pd-silica-v1'
COLD = {'temperature':'cooled','solvent':'dry','catalyst':'metal',
        'conditionProfileId':MODEL,'conditionProfileVersion':'1'}


def match(source='C1=CCCCC1', conditions=None, reverse=False, reagent='hydrogen'):
    pair=({'smiles':source},reagent)
    if reverse:pair=pair[::-1]
    c=COLD if conditions is None else conditions
    result=s.match_reactions(*pair,c)
    return pair,result,[o for o in result['reactionOptions'] if o['mechanism']=='Hydrogenation']


class CooledCyclohexeneR2Tests(unittest.TestCase):
    def test_profile_is_explicit_only_with_detached_source_provenance(self):
        p=profiles.reviewed_profile(MODEL,'Hydrogenation')
        self.assertTrue(p.explicit_only)
        self.assertNotIn('Hydrogenation',profiles.PROFILES_BY_PATHWAY)
        d=next(r for r in profiles.named_profile_manifest()['profiles'] if r['id']==MODEL)
        facts={f['field']:f for f in d['facts']}
        self.assertEqual(facts['catalyst']['value']['metal'],'Pd')
        self.assertEqual(facts['catalyst']['value']['loadingWtPercent'],5)
        self.assertEqual(facts['catalyst']['value']['support'],'dual-pore silica catalyst A')
        self.assertEqual(facts['catalyst']['value']['averageParticleMicrometres'],68)
        self.assertEqual(facts['catalyst']['value']['preparation']['identity'],'Synthesis Example 1 only')
        self.assertEqual(facts['medium']['value'],'hexane')
        self.assertEqual(facts['thermalHistory']['value']['temperatureC'],0)
        self.assertEqual(facts['thermalHistory']['value']['durationMinutes'],15)
        self.assertFalse(facts['thermalHistory']['value']['rangeValidated'])
        self.assertEqual(facts['thermalHistory']['value']['catalystPretreatment'],[
            {'stage':'H2 reduction','temperature':'room temperature','durationMinutes':60},
            {'stage':'drying','temperatureC':110,'durationMinutes':720}])
        self.assertEqual(facts['hydrogenPressure']['value'],{'value':1.1,'unit':'MPa','basis':'not stated'})
        self.assertTrue(d['unknowns']);self.assertTrue(d['evidence'])

    def test_graph_orderings_and_both_input_orders_conserve_exact_net_atoms(self):
        for source in ('C1=CCCCC1','C1CC=CCC1','C1CCC=CC1'):
            for reverse in (False,True):
                pair,_,options=match(source,reverse=reverse);self.assertEqual(len(options),1);o=options[0]
                self.assertEqual(o['productSmiles'],'C1CCCCC1');self.assertEqual(o['byproducts'],[])
                self.assertTrue(o['assessment']['canRun']);self.assertTrue(o['assessment']['evidence']['canGenerate3D'])
                self.assertEqual(o['assessment']['namedConditionProfile']['selection'],'explicit')
                d=s.reaction_diagram(o['id'],*pair,COLD)
                self.assertEqual(d['assessment'],o['assessment']);self.assertIn('<svg',d['svg']);self.assertIsNone(d['mechanism'])
                before=[r for r in d['atoms'] if r['side']=='reactants'];after=[r for r in d['atoms'] if r['side']=='products']
                inventory=lambda rows:{r['mapId']:(r['element'],r['formalCharge']) for r in rows}
                self.assertEqual(inventory(before),inventory(after));self.assertEqual(len(before),len(after));self.assertEqual(len(before),18)
                self.assertTrue(all(r['formalCharge']==0 for r in after))
                h_species=next(i for i,r in enumerate(d['reactants']) if r['formula']=='H2')
                hs={r['mapId'] for r in before if r['speciesIndex']==h_species};self.assertEqual(len(hs),2)
                self.assertEqual(set(d['bondsBroken'][0]['atomMaps']),hs)
                self.assertEqual(len(d['bondsFormed']),2)
                self.assertEqual({m for b in d['bondsFormed'] for m in b['atomMaps']},hs|set(o['site']['atomMaps']))
                self.assertTrue(all(len(set(b['atomMaps'])&hs)==1 for b in d['bondsFormed']))
                self.assertEqual([(r['before'],r['after']) for r in d['bondOrderChanges']],[(2,1)])
                self.assertEqual(set(o['compatibility']['validation'].values()),{'verified'})
                p=s.run_curated_reaction(o['id'],*pair,COLD)['product'];self.assertEqual(p['representation'],'3d')
                self.assertEqual(p['smiles'],'C1CCCCC1')
                self.assertEqual([(r['atomIndex'],r['mapId'],r['element']) for r in after],[(r['index'],r['mapId'],r['element']) for r in p['atomLinks']])
                mol=Chem.MolFromMolBlock(p['molfile'],removeHs=False)
                for atom in mol.GetAtoms(): atom.SetAtomMapNum(0)
                self.assertEqual(Chem.MolToSmiles(Chem.RemoveHs(mol)),'C1CCCCC1')
                self.assertFalse(Chem.FindPotentialStereo(mol))
                self.assertEqual(o['information']['stereochemistry']['product']['chiralCenters'],[])
                self.assertEqual(o['information']['stereochemistry']['product']['alkenes'],[])

    def test_generic_metal_alone_does_not_gain_new_cold_permission(self):
        c={k:v for k,v in COLD.items() if not k.startswith('conditionProfile')}
        pair,_,options=match(conditions=c);o=options[0]
        self.assertFalse(o['assessment']['canRun']);self.assertTrue(o['guidedConditions']['canApply'])
        self.assertEqual(o['guidedConditions']['targetConditions']['conditionProfileId'],MODEL)
        self.assertNotIn('temperature',o['guidedConditions']['targetConditions'])
        with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)

    def test_other_existing_eligible_alkenes_are_not_admitted(self):
        for source in ('C=C','C=CC','C1=CCCC1','C1=CCCCCC1','CC1=CCCCC1','C=CCCCO','C=CC[C@H](C)CC','C=CCCCCC=C'):
            pair,_,options=match(source);self.assertTrue(options,source)
            for o in options:
                self.assertFalse(o['assessment']['canRun'],source)
                self.assertIn('only unsubstituted cyclohexene',o['assessment']['note'])
                with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,COLD)

    def test_actual_h2_and_existing_structure_restrictions_remain_authoritative(self):
        for reagent in ('water','bromine',{'smiles':'O','name':'Hydrogen'}):self.assertEqual(match(reagent=reagent)[2],[])
        for source in ('C=CC=C','C=Cc1ccccc1','C=CCCC=O'):
            self.assertEqual(match(source)[2],[])
        with self.assertRaises(s.ChemistryError):match(reagent={'smiles':'[2H][2H]'})

    def test_wrong_catalysts_media_and_additional_stages_cannot_be_overridden(self):
        negatives=[{'catalyst':v} for v in ('','none','acid','lindlar','osmium','radical')]
        negatives += [{'solvent':v} for v in ('','aqueous-protic','ethanolic-protic','polar-aprotic')]
        negatives += [{'workup':'aqueous-release'},{'oxidationStage':'first'}]
        for extra in negatives:
            c={**COLD,**extra};pair,_,options=match(conditions=c)
            for o in options:
                self.assertFalse(o['assessment']['canRun'])
                with patch.object(s,'mapped_product_molecule',side_effect=AssertionError('gate before geometry')):
                    with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)

    def test_unknown_numeric_or_formulation_overrides_are_not_interpreted(self):
        for extra in ({'pressure':'1.1 MPa'},{'pressureMPa':1.1},{'solventIdentity':'hexane'},
                {'catalystSupport':'Pd/C'},{'temperatureC':0},{'profileFacts':{'canRun':True}}):
            c={**COLD,**extra};pair,_,options=match(conditions=c);o=options[0]
            self.assertFalse(o['assessment']['canRun']);self.assertFalse(o['guidedConditions']['canApply'])
            with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)

    def test_persistent_alkyne_and_chain_selectors_do_not_change_one_h2_accounting(self):
        _,_,options=match(conditions={**COLD,'additionStage':'two','polymerUnits':'6'})
        o=options[0];self.assertTrue(o['assessment']['canRun'])
        self.assertEqual(set(o['assessment']['notApplicableSettings']),{'additionStage','polymerUnits'})
        self.assertEqual([r['coefficient'] for r in o['stoichiometry']['reactants']],[1,1])

    def test_unknown_or_wrong_profile_version_cannot_fall_back(self):
        for extra in ({'conditionProfileId':'cooled-cyclohexene-pd-c-v1'}, {'conditionProfileVersion':'2'},
                {'conditionProfileId':'cooled-alkene-bromination-v1'}):
            c={**COLD,**extra};pair,_,options=match(conditions=c)
            self.assertFalse(options[0]['assessment']['canRun'])
            with self.assertRaises(s.ChemistryError):s.run_curated_reaction(options[0]['id'],*pair,c)

    def test_temperature_switch_is_a_conflict_until_selection_is_deliberately_cleared(self):
        for temperature in ('','ambient','heated'):
            c={**COLD,'temperature':temperature};pair,_,options=match(conditions=c)
            self.assertFalse(options[0]['assessment']['canRun'])
            with self.assertRaises(s.ChemistryError):s.run_curated_reaction(options[0]['id'],*pair,c)
        pair,_,options=match(conditions={'temperature':'ambient','catalyst':'metal'})
        self.assertEqual(s.run_curated_reaction(options[0]['id'],*pair,{'temperature':'ambient','catalyst':'metal'})['product']['representation'],'3d')

    def test_cached_positive_cannot_be_reused_with_another_graph(self):
        pair,_,options=match();cached=copy.deepcopy(options[0]['assessment'])
        ids,custom,_=s._resolve_reactants(*pair)
        reaction=s._reactions_for_pair(*ids,{**s.REACTANTS,**custom},s._conditions(COLD))[0][options[0]['id']]
        altered=copy.deepcopy(reaction);altered['hydrogenationSubstrateIdentity']='C1=CCCC1'
        self.assertFalse(cooling_confidence(cached,COLD,altered)['canRun'])
        for key in ('hydrogenationReagentIdentity','compatibility'):
            altered=copy.deepcopy(reaction);altered.pop(key)
            self.assertFalse(cooling_confidence(cached,COLD,altered)['canRun'])

    def test_calculator_context_is_theoretical_and_does_not_use_the_patent_endpoint(self):
        for reverse in (False,True):
            _,_,options=match(reverse=reverse);d=options[0]['stoichiometry']
            self.assertEqual([r['coefficient'] for r in d['reactants']],[1,1]);self.assertEqual(d['product']['coefficient'],1)
            self.assertAlmostEqual(d['product']['molarMass'],84.162)
            self.assertAlmostEqual(next(r['molarMass'] for r in d['reactants'] if r['formula']=='H2'),2.016)
            self.assertTrue(d['context']['canGenerate3D']);self.assertEqual(d['context']['namedConditionProfile']['reference']['id'],MODEL)
            self.assertIn('not a predicted or actual yield',' '.join(d['notes']))
            self.assertIn('not establish complete conversion',d['context']['assumptions'][0])

    def test_mechanism_remains_net_only_not_a_fabricated_surface_cycle(self):
        pair,_,options=match();o=options[0]
        self.assertIsNone(s.reaction_diagram(o['id'],*pair,COLD)['mechanism'])
        self.assertEqual(o['information']['capabilities']['mappedMechanism'],'unsupported')
        self.assertIn('no full catalytic surface mechanism',o['assessment']['note'])

    def test_authenticated_match_diagram_run_share_the_profile_and_revalidate(self):
        with tempfile.TemporaryDirectory() as directory:
            origin='https://batch1-test.invalid';password='Synthetic-batch1-test-fixture'
            app=create_app({'SESSION_SECRET':secrets.token_hex(32),'TRIAL_PASSWORD':password,'PUBLIC_ORIGIN':origin,
                'FRAME_ANCESTORS':origin,'DIST_DIR':Path(directory),'TESTING':True},chemistry_backend=s)
            client=app.test_client()
            post=lambda path,body:client.post(path,json=body,base_url=origin,headers={'Origin':origin})
            body={'reactantA':{'smiles':'C1=CCCCC1'},'reactantB':'hydrogen','conditions':COLD}
            self.assertEqual(post('/api/reactions/match',body).status_code,401)
            self.assertEqual(client.post('/login',data={'password':password},base_url=origin,headers={'Origin':origin}).status_code,303)
            matched=post('/api/reactions/match',body);self.assertEqual(matched.status_code,200)
            o=matched.json['reactionOptions'][0];body['reactionId']=o['id']
            diagram=post('/api/reactions/diagram',body);self.assertEqual(diagram.status_code,200)
            self.assertEqual(diagram.json['assessment'],o['assessment'])
            self.assertEqual(post('/api/reactions/run',body).json['product']['representation'],'3d')
            body['conditions']={**COLD,'temperature':'ambient'}
            rejected=post('/api/reactions/run',body);self.assertEqual(rejected.status_code,422);self.assertNotIn('product',rejected.json)
            body['conditions']={**COLD,'conditionProfileVersion':'2'}
            self.assertEqual(post('/api/reactions/run',body).status_code,422)


if __name__=='__main__':unittest.main()
