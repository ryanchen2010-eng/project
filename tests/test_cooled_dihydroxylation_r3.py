"""R3 v1: source-specific endpoint contracts, independent net-graph oracles."""
import copy
import secrets
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as s, reaction_temperature_profiles as registry
from server import cooled_dihydroxylation_r3 as r3
from server.reaction_conditions import cooling_confidence
from server.production_app import create_app

CASES = ((r3.ISOBUTYLENE, 'C=C(C)C', 'CC(C)(O)CO', '', 90.122),
         (r3.CROTONIC, 'CC=CC(=O)O', 'CC(O)C(O)C(=O)O', 'aqueous-release', 120.104),
         (r3.CINNAMIC, 'O=C(O)C=Cc1ccccc1', 'O=C(O)C(O)C(O)c1ccccc1', 'aqueous-release', 182.175))


def settings(identifier, workup=''):
    return {'temperature':'cooled','solvent':'dry','catalyst':'osmium','workup':workup,
        'conditionProfileId':identifier,'conditionProfileVersion':'1'}


def matched(source, conditions, reverse=False):
    pair=({'smiles':source},'hydrogen-peroxide')
    if reverse: pair=pair[::-1]
    payload=s.match_reactions(*pair,conditions)
    return pair,payload,[o for o in payload['reactionOptions'] if o['mechanism']=='Alkene dihydroxylation']


class CooledDihydroxylationR3Tests(unittest.TestCase):
    def test_fractionation_contract_is_explicit_not_a_silent_aqueous_bypass(self):
        c=settings(r3.ISOBUTYLENE);pair,_,options=matched('C=C(C)C',c);o=options[0]
        a=o['assessment'];self.assertTrue(a['canRun']);self.assertFalse(a['workupAssumptionConfirmed'])
        self.assertTrue(a['productReleaseAssumptionConfirmed']);self.assertFalse(a['productRelease']['aqueousReleaseAssumed'])
        self.assertIn('fractionation',a['productRelease']['observedRecovery'])
        self.assertNotIn('workup',a['evidence']['requiredSettings'])
        for extra in ({'workup':'aqueous-release'},{'temperature':'ambient'},{'conditionProfileVersion':'2'}):
            cc={**c,**extra};other=matched('C=C(C)C',cc)[2][0]
            self.assertFalse(other['assessment']['canRun'])
            with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,cc)
        generic={k:v for k,v in c.items() if not k.startswith('conditionProfile')}
        self.assertFalse(matched('C=C(C)C',generic)[2][0]['assessment']['canRun'])
        self.assertIn('workup',matched('C=C(C)C',{**generic,'temperature':'ambient'})[2][0]['assessment']['missingSettings'])
        self.assertTrue(matched('C=C(C)C',{**generic,'temperature':'ambient','workup':'aqueous-release'})[2][0]['assessment']['canRun'])

    def test_independent_products_atom_charge_and_3d_correspondence(self):
        for identifier,source,expected,workup,mass in CASES:
            for reverse in (False,True):
                c=settings(identifier,workup);pair,_,options=matched(source,c);self.assertEqual(len(options),1)
                o=options[0];self.assertEqual(o['productSmiles'],expected);self.assertEqual(o['byproducts'],[])
                self.assertTrue(o['assessment']['canRun']);self.assertTrue(o['assessment']['evidence']['canGenerate3D'])
                d=s.reaction_diagram(o['id'],*pair,c);self.assertEqual(d['assessment'],o['assessment']);self.assertIsNone(d['mechanism'])
                atoms=lambda side:{a['mapId']:(a['element'],a['formalCharge']) for a in d['atoms'] if a['side']==side}
                self.assertEqual(atoms('reactants'),atoms('products'));self.assertTrue(all(v[1]==0 for v in atoms('products').values()))
                self.assertEqual(len(d['bondsFormed']),2);self.assertEqual(len(d['bondsBroken']),1)
                self.assertEqual([(b['before'],b['after']) for b in d['bondOrderChanges']],[(2,1)])
                p=s.run_curated_reaction(o['id'],*pair,c)['product'];self.assertEqual(p['representation'],'3d');self.assertEqual(p['smiles'],expected)
                after=[a for a in d['atoms'] if a['side']=='products']
                self.assertEqual([(a['atomIndex'],a['mapId'],a['element']) for a in after],[(a['index'],a['mapId'],a['element']) for a in p['atomLinks']])
                self.assertEqual(set(o['compatibility']['validation'].values()),{'verified'})
                mol=Chem.MolFromMolBlock(p['molfile'],removeHs=False)
                for a in mol.GetAtoms():a.SetAtomMapNum(0)
                # A 3D file necessarily embodies one geometry and RDKit can
                # infer tags when re-reading it. It is not the assigned product.
                self.assertEqual(Chem.MolToSmiles(Chem.RemoveHs(mol),isomericSmiles=False),expected)
                declared=Chem.MolFromSmiles(o['productSmiles'])
                self.assertTrue(all(a.GetChiralTag()==Chem.ChiralType.CHI_UNSPECIFIED for a in declared.GetAtoms()))
                self.assertEqual(o['dihydroxylationStereo']['assignedAtomMaps'],[])
                self.assertAlmostEqual(o['stoichiometry']['product']['molarMass'],mass)

    def test_formal_peroxide_o_h_inventory_is_not_an_os_mechanism(self):
        for identifier,source,_,workup,_ in CASES:
            c=settings(identifier,workup);pair,_,options=matched(source,c);o=options[0]
            d=s.reaction_diagram(o['id'],*pair,c)
            perox=next(i for i,r in enumerate(d['reactants']) if r['formula']=='H2O2')
            donors={a['mapId'] for a in d['atoms'] if a['side']=='reactants' and a['speciesIndex']==perox}
            self.assertEqual(len(donors),4);self.assertTrue(donors <= {a['mapId'] for a in d['atoms'] if a['side']=='products'})
            self.assertEqual(set(d['bondsBroken'][0]['atomMaps']),{a['mapId'] for a in d['atoms'] if a['side']=='reactants' and a['speciesIndex']==perox and a['element']=='O'})
            self.assertEqual(o['information']['capabilities']['mappedMechanism'],'unsupported')
            self.assertIn('not elementary',o['assessment']['note'])

    def test_wrong_conditions_and_facts_fail_before_embedding(self):
        for extra in ({'solvent':''},{'solvent':'ethanolic-protic'},{'solvent':'aqueous-protic'},{'catalyst':'none'},
                {'catalyst':'metal'},{'catalyst':'acid'},{'oxidationStage':'further'},{'temperatureC':0},
                {'osmiumPercent':'0.5%'},{'release':'fractionation'},{'profileFacts':{'canRun':True}}):
            c={**settings(r3.ISOBUTYLENE),**extra};pair,_,options=matched('C=C(C)C',c)
            self.assertFalse(options[0]['assessment']['canRun'],extra)
            with patch.object(s,'mapped_product_molecule',side_effect=AssertionError('gate before geometry')):
                with self.assertRaises(s.ChemistryError):s.run_curated_reaction(options[0]['id'],*pair,c)

    def test_other_substrates_reagents_and_source_endpoints_are_not_borrowed(self):
        c=settings(r3.ISOBUTYLENE)
        for source in ('C=C','CC=C(C)C','C=C(C)CC','C1=CCCCC1','C=CCCCO','C=CCCCCC=C','C/C=C/C'):
            pair,_,options=matched(source,c)
            for o in options:
                self.assertFalse(o['assessment']['canRun'])
                with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)
        for reagent in ('water','sodium-hypochlorite',{'smiles':'COO','name':'H2O2'}):
            self.assertFalse([o for o in s.match_reactions({'smiles':'C=C(C)C'},reagent,c)['reactionOptions'] if o['mechanism']=='Alkene dihydroxylation'])

    def test_source_provenance_distinguishes_stock_percent_time_and_yield(self):
        m=registry.PROFILES_BY_ID[r3.ISOBUTYLENE];self.assertTrue(m.explicit_only)
        self.assertNotIn('Alkene dihydroxylation',registry.PROFILES_BY_PATHWAY)
        d=registry.describe(m);f={f['field']:f for f in d['facts']}
        self.assertEqual(f['reagents']['value']['reportedPeroxide'],'6.62%')
        self.assertEqual(f['thermalHistory']['value']['duration'],'overnight; following day')
        self.assertIsNone(f['thermalHistory']['value']['hours'])
        self.assertEqual(f['productRelease']['value']['reportedYieldPercent'],37.6)
        self.assertTrue(d['unknowns']);self.assertIn('1303',d['evidence'][0]['locator'])
        d['facts'].clear();self.assertTrue(registry.describe(m)['facts'])

    def test_calculator_context_and_cached_permission_are_profile_bound(self):
        c=settings(r3.ISOBUTYLENE);pair,_,options=matched('C=C(C)C',c);o=options[0];d=o['stoichiometry']
        self.assertEqual([r['coefficient'] for r in d['reactants']],[1,1]);self.assertEqual(d['product']['coefficient'],1)
        self.assertAlmostEqual(next(r['molarMass'] for r in d['reactants'] if r['formula']=='H2O2'),34.014)
        self.assertEqual(d['context']['namedConditionProfile']['reference']['id'],r3.ISOBUTYLENE)
        self.assertIn('not experimental yields',d['context']['warning'])
        ids,custom,_=s._resolve_reactants(*pair);reaction=s._reactions_for_pair(*ids,{**s.REACTANTS,**custom},s._conditions(c))[0][o['id']]
        bad=copy.deepcopy(reaction);bad['dihydroxylationSubstrateIdentity']='C=C'
        self.assertFalse(cooling_confidence(o['assessment'],s._conditions(c),bad)['canRun'])
        self.assertFalse(cooling_confidence(o['assessment'],s._conditions({**c,'workup':'aqueous-release'}),reaction)['canRun'])

    def test_confirmed_guide_changes_neither_temperature_nor_hidden_facts(self):
        generic={'temperature':'cooled','catalyst':'osmium','workup':'aqueous-release'}
        _,_,options=matched('C=C(C)C',generic);g=options[0]['guidedConditions']
        self.assertTrue(g['canApply']);self.assertTrue(g['requireConfirmation'])
        self.assertEqual(g['targetConditions']['workup'],'');self.assertNotIn('temperature',g['targetConditions'])
        self.assertEqual(g['profileId'],r3.ISOBUTYLENE)
        self.assertTrue(any(r['field']=='workup' and r['state']=='conflicting' for r in g['requirements']))

    def test_acid_recovery_contracts_and_percent_yield_bases_are_distinct(self):
        for identifier,_,_,_,_ in CASES[1:]:
            model=r3.MODELS[identifier];d=registry.describe(registry.PROFILES_BY_ID[identifier]);facts={f['field']:f for f in d['facts']}
            self.assertEqual(facts['reagents']['value']['reportedPeroxide'],'6.3%')
            self.assertIn('consumed',facts['productRelease']['value']['yieldBasis'])
            self.assertEqual(facts['catalyst']['provenance'],'model-assumption')
            self.assertIn('cross-reference',facts['catalyst']['relevance'])
            self.assertEqual(facts['productRelease']['value']['recovery'],model.recovery)
        self.assertIn('chloroform',r3.MODELS[r3.CROTONIC].recovery)
        self.assertNotIn('chloroform',r3.MODELS[r3.CINNAMIC].recovery)
        self.assertIn('noncrystallized',r3.MODELS[r3.CINNAMIC].recovery)
        self.assertNotEqual(r3.MODELS[r3.CROTONIC].catalyst_ml,r3.MODELS[r3.CINNAMIC].catalyst_ml)

    def test_acid_contract_requires_explicit_reference_and_reviewed_water_recovery(self):
        for identifier,source,_,workup,_ in CASES[1:]:
            c=settings(identifier,workup)
            for extra in ({'workup':''},{'catalyst':'none'},{'solvent':'ethanolic-protic'},{'temperature':'heated'}):
                cc={**c,**extra};pair,_,options=matched(source,cc)
                self.assertTrue(options)
                self.assertFalse(options[0]['assessment']['canRun'])
                with self.assertRaises(s.ChemistryError):s.run_curated_reaction(options[0]['id'],*pair,cc)
            generic={k:v for k,v in c.items() if not k.startswith('conditionProfile')}
            o=matched(source,generic)[2][0]
            self.assertFalse(o['assessment']['canRun']);self.assertTrue(o['guidedConditions']['canApply'])
            self.assertEqual(o['guidedConditions']['targetConditions']['workup'],'aqueous-release')

    def test_acid_carbonyl_and_acid_oh_bonds_are_independently_preserved(self):
        for identifier,source,expected,workup,_ in CASES[1:]:
            c=settings(identifier,workup);pair,_,options=matched(source,c);o=options[0]
            ids,custom,_=s._resolve_reactants(*pair);catalog={**s.REACTANTS,**custom}
            reaction=s._reactions_for_pair(*ids,catalog,s._conditions(c))[0][o['id']]
            from server.reaction_diagrams import _species
            before,_=_species(reaction['reactants'][0],catalog[reaction['reactants'][0]],1)
            original=before['mol'];product=Chem.MolFromSmiles(reaction['mappedProducts'][0])
            acid=Chem.MolFromSmarts('[C](=[O])-[O;H1]')
            match=original.GetSubstructMatch(acid);self.assertEqual(len(match),3)
            maps=[original.GetAtomWithIdx(i).GetAtomMapNum() for i in match]
            indexed={a.GetAtomMapNum():a.GetIdx() for a in product.GetAtoms()}
            self.assertEqual(product.GetBondBetweenAtoms(indexed[maps[0]],indexed[maps[1]]).GetBondType(),Chem.BondType.DOUBLE)
            self.assertEqual(product.GetBondBetweenAtoms(indexed[maps[0]],indexed[maps[2]]).GetBondType(),Chem.BondType.SINGLE)
            self.assertEqual(product.GetAtomWithIdx(indexed[maps[2]]).GetFormalCharge(),0)
            self.assertEqual(len(Chem.MolFromSmiles(expected).GetSubstructMatches(acid)),1)

    def test_unspecified_acid_geometry_is_not_replaced_by_invented_stereo(self):
        for identifier,source,_,workup,_ in CASES[1:]:
            _,_,options=matched(source,settings(identifier,workup));o=options[0]
            self.assertEqual(o['dihydroxylationStereo']['assignedAtomMaps'],[])
            self.assertIn('unassigned',o['dihydroxylationStereo']['outcome'])
            self.assertNotIn('@',o['productSmiles']);self.assertIsNone(o['dihydroxylationStereo']['ratios'])
        for source in ('C/C=C/C(=O)O','C/C=C\\C(=O)O','O=C(O)/C=C/c1ccccc1','O=C(O)/C=C\\c1ccccc1'):
            for identifier in (r3.CROTONIC,r3.CINNAMIC):
                _,payload,options=matched(source,settings(identifier,'aqueous-release'))
                self.assertFalse(options);self.assertIn('not discarded',' '.join(payload['unsupportedReasons']))

    def test_source_acid_policy_is_not_general_conjugated_acid_approval(self):
        for source in ('C=CC(=O)O','CCC=CC(=O)O','CC=C(C)C(=O)O','C=CC(=O)OC',
                       'O=C(O)C=Cc1ccc(O)cc1','O=C(O)C=Cc1ccc(Cl)cc1','C=CC=CC(=O)O'):
            for identifier in (r3.CROTONIC,r3.CINNAMIC):
                _,_,options=matched(source,settings(identifier,'aqueous-release'));self.assertFalse(options,source)
        with self.assertRaises(s.ChemistryError):matched('CC=CC(=O)[O-]',settings(r3.CROTONIC,'aqueous-release'))
        for _,source,_,_,_ in CASES[1:]:
            self.assertFalse(matched(source,{'temperature':'ambient','catalyst':'osmium','workup':'aqueous-release'})[2])

    def test_fumaric_further_oxidation_and_calcium_recovery_are_not_a_free_acid_profile(self):
        self.assertFalse(any('fumaric' in k for k in registry.PROFILES_BY_ID))
        for source in ('O=C(O)/C=C/C(=O)O','O=C(O)/C=C\\C(=O)O','O=C(O)C=CC(=O)O'):
            _,payload,options=matched(source,{'temperature':'cooled','catalyst':'osmium','workup':'aqueous-release'})
            self.assertFalse(options);text=' '.join(payload['unsupportedReasons'])
            self.assertIn('oxalic acid',text);self.assertIn('calcium salts',text);self.assertIn('not implemented',text)

    def test_profiles_are_not_interchangeable_and_unknowns_cannot_be_overwritten(self):
        for identifier,source,_,workup,_ in CASES:
            for other in r3.MODELS:
                if other==identifier:continue
                _,payload,options=matched(source,settings(other,workup))
                self.assertTrue(all(not o['assessment']['canRun'] for o in options))
                if workup:
                    self.assertIn('ID/version conflicts',' '.join(payload['unsupportedReasons']))
                    self.assertNotIn('specified E/Z',' '.join(payload['unsupportedReasons']))
            c={**settings(identifier,workup),'reactionHours':12}
            _,_,options=matched(source,c);self.assertFalse(options[0]['assessment']['canRun'])
            self.assertFalse(options[0]['guidedConditions']['canApply'])

    def test_authenticated_public_match_diagram_run_and_temperature_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            origin='https://r3-test.invalid';password='Synthetic-R3-password'
            app=create_app({'SESSION_SECRET':secrets.token_hex(32),'TRIAL_PASSWORD':password,'PUBLIC_ORIGIN':origin,
                'FRAME_ANCESTORS':origin,'DIST_DIR':Path(directory),'TESTING':True},chemistry_backend=s)
            client=app.test_client();post=lambda path,body:client.post(path,json=body,base_url=origin,headers={'Origin':origin})
            body={'reactantA':{'smiles':'C=C(C)C'},'reactantB':'hydrogen-peroxide','conditions':settings(r3.ISOBUTYLENE)}
            self.assertEqual(post('/api/reactions/match',body).status_code,401)
            self.assertEqual(client.post('/login',data={'password':password},base_url=origin,headers={'Origin':origin}).status_code,303)
            for identifier,source,expected,workup,_ in CASES:
                body={'reactantA':{'smiles':source},'reactantB':'hydrogen-peroxide','conditions':settings(identifier,workup)}
                matched_response=post('/api/reactions/match',body);self.assertEqual(matched_response.status_code,200)
                o=matched_response.json['reactionOptions'][0];body['reactionId']=o['id']
                d=post('/api/reactions/diagram',body);self.assertEqual(d.status_code,200);self.assertEqual(d.json['assessment'],o['assessment'])
                result=post('/api/reactions/run',body);self.assertEqual(result.status_code,200);self.assertEqual(result.json['product']['smiles'],expected)
                body['conditions']={**body['conditions'],'temperature':'ambient'}
                self.assertEqual(post('/api/reactions/run',body).status_code,422)


if __name__=='__main__':unittest.main()
