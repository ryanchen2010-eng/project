"""Primary-only net-stage specifications; no aldehyde-isolation approval."""
import hashlib
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from server import chemistry_server as service, reaction_engine as engine, alcohol_oxidation_rule as base, primary_alcohol_oxidation_rule as rule
from server.reaction_diagrams import _species, _combine, _identity
from server.production_app import create_app

FIXTURE=json.loads(Path('tests/fixtures/primary-alcohol-oxidation-phase5c.json').read_text())
MODEL=FIXTURE['conditions']
canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s))


def options(source,conditions=None,reagent='sodium-hypochlorite',reverse=False):
    a,b={'smiles':source},reagent
    if reverse:a,b=b,a
    response=service.match_reactions(a,b,MODEL if conditions is None else conditions)
    return a,b,response,[r for r in response['reactionOptions'] if r.get('primaryOxidationModel')]


class PrimaryOxidationTests(unittest.TestCase):
    def positive(self,case):
        for symbol in ['Na','K']:
            reagent={'smiles':f'[{symbol}+].[O-]Cl'}
            for reverse in [False,True]:
                with self.subTest(symbol=symbol,reverse=reverse):
                    a,b,response,found=options(case['substrate'],reagent=reagent,reverse=reverse)
                    self.assertEqual({r['productSmiles'] for r in found},{canonical(p) for p in case['products']})
                    if case.get('aliases'):
                        self.assertEqual(len(found),1)
                        self.assertEqual(len(found[0]['optionIdentity']['sourceReactionIds']),case['aliases'])
                        legacy=[r for r in response['reactions'] if r.get('primaryOxidationModel')]
                        self.assertEqual(len(legacy),case['aliases'])
                        oxygens=set()
                        for alias in legacy:
                            d=service.reaction_diagram(alias['id'],a,b,MODEL);oxygens.add(d['primaryOxidationModel']['oxygen'])
                        self.assertEqual(len(oxygens),case['aliases'])
                    secondary=[r for r in response['reactionOptions'] if r['mechanism']=='Alcohol oxidation' and not r.get('primaryOxidationModel')]
                    if case.get('secondaryProducts'):
                        self.assertEqual({r['productSmiles'] for r in secondary},{canonical(p) for p in case['secondaryProducts']})
                        # Secondary selectivity is now explicitly gated by Phase
                        # 5D; this mixed diol must not assert selective oxidation.
                        for r in secondary:
                            self.assertFalse(r['assessment']['canRun'])
                            with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,MODEL)
                    for r in found:
                        m=r['primaryOxidationModel'];ev=r['assessment']['evidence'];stoich=r['stoichiometry']
                        self.assertFalse(m['aldehydeEndpointValidated']);self.assertFalse(m['selectiveOxidantProfileImplemented'])
                        self.assertFalse(ev['conditionCompleteEligibility']);self.assertFalse(ev['canGenerate3D']);self.assertTrue(ev['canPreview2D'])
                        self.assertEqual(ev['structuralScope'],'formal-first-stage-only')
                        self.assertEqual(ev['independentChemistryReview'],'not-approved')
                        self.assertEqual(r['assessment']['status'],'unevaluated');self.assertIn('No aldehyde-selective',r['assessment']['note'])
                        self.assertTrue(stoich['balanced']);self.assertEqual([x['coefficient'] for x in stoich['reactants']],[1,1]);self.assertEqual(stoich['excludedInputs'],[])
                        self.assertEqual(stoich['context']['canGenerate3D'],False);self.assertIn('not an isolated aldehyde yield',stoich['context']['warning'])
                        self.assertEqual(r['productFormula'],rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(r['productSmiles'])))
                        self.assertEqual(sorted(x['formula'] for x in r['byproducts']),sorted(['H2O',symbol+'Cl']))
                        d=service.reaction_diagram(r['id'],a,b,MODEL);self.assertIsNone(d['mechanism'])
                        self.assertEqual(r['information']['capabilities']['mappedMechanism'],'unsupported')
                        self.assertIn('not an asserted aldehyde endpoint',d['note']);self.assertIn('No complete',d['note'])
                        before={x['mapId']:x for x in d['atoms'] if x['side']=='reactants'};after={x['mapId']:x for x in d['atoms'] if x['side']=='products'}
                        self.assertEqual({k:x['element'] for k,x in before.items()},{k:x['element'] for k,x in after.items()})
                        self.assertEqual(sum(x['formalCharge'] for x in before.values()),sum(x['formalCharge'] for x in after.values()))
                        self.assertEqual(len(d['atoms']),2*len(before))
                        water=next(i for i,p in enumerate(d['products']) if p['smiles']=='O')
                        self.assertEqual({x['mapId'] for x in after.values() if x['speciesIndex']==water},{m['oxidantOxygen'],m['removedCarbonHydrogen'],m['removedOHHydrogen']})
                        self.assertEqual(after[m['oxygen']]['speciesIndex'],0);self.assertEqual(before[m['oxygen']]['element'],'O')
                        self.assertNotEqual(m['oxygen'],m['oxidantOxygen'])
                        self.assertEqual([(c['before'],c['after']) for c in d['bondOrderChanges']],[(1,2)])
                        self.assertEqual(len(d['bondsBroken']),3);self.assertEqual(len(d['bondsFormed']),2)
                        self.assertFalse(any(p['formula']=='H2' for p in d['products']))
                        # Gate must run before attempting conformer generation.
                        with patch.object(service,'mapped_product_molecule',side_effect=AssertionError('3D must not be reached')):
                            with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,MODEL)

    def negative(self,case):
        _,_,response,found=options(case['substrate']);self.assertFalse(found)
        if case['reason']:self.assertIn(case['reason'].lower(),' '.join(response['unsupportedReasons']).lower())

    def test_cip_reassignment_is_not_physical_inversion(self):
        for tag,before,after in [('@','S','R'),('@@','R','S')]:
            _,_,_,found=options(f'C[C{tag}H](CCOC)CCO');r=found[0]
            self.assertEqual(r['stereochemistry']['reactant']['chiralCenters'][0]['assignment'],before)
            self.assertEqual(r['stereochemistry']['product']['chiralCenters'][0]['assignment'],after)
            self.assertEqual(r['productSmiles'],canonical(f'C[C{tag}H](CCOC)CC=O'))

    def test_primary_validation_cannot_route_secondary_or_tertiary(self):
        for source in ['CC(O)C','CC(O)(C)C']:
            mol=Chem.MolFromSmiles(source);site=base.sites(mol)[0]
            self.assertFalse(rule.is_primary(mol,site));self.assertFalse(rule.assess(mol,site)['eligible'])
        for site in [(),(0,),(0,99),(0,0)]:self.assertFalse(rule.assess(Chem.MolFromSmiles('CCO'),site)['eligible'])

    def test_selected_carbon_is_planar_and_retains_the_alcohol_oxygen(self):
        a,n=_species('a',{'name':'a','smiles':'CCO'},1);b,_=_species('b',{'name':'b','smiles':'[Na+].[O-]Cl'},n)
        site=rule.sites(a['mol'])[0];p=rule.participants(a['mol'],b['mol'],site)
        before=_combine([a,b]);after=_combine([{'mol':m} for m in engine.transform('Alcohol oxidation',[a,b],site)])
        rule.validate(before,after,a['mol'],b['mol'],site)
        atoms={x.GetAtomMapNum():x for x in after.GetAtoms()};c,o=atoms[p['carbon']],atoms[p['oxygen']]
        self.assertEqual(c.GetHybridization(),Chem.HybridizationType.SP2);self.assertEqual(o.GetDegree(),1)
        self.assertEqual(after.GetBondBetweenAtoms(c.GetIdx(),o.GetIdx()).GetBondTypeAsDouble(),2)
        self.assertEqual(sum(n.GetAtomicNum()==1 for n in c.GetNeighbors()),1)
        for kind in ['carbonyl-tag','oxygen-swap','charge','map','acid','H2']:
            bad=Chem.RWMol(after);atoms={x.GetAtomMapNum():x for x in bad.GetAtoms()}
            if kind=='carbonyl-tag':atoms[p['carbon']].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            elif kind=='oxygen-swap':atoms[p['oxygen']].SetAtomMapNum(p['oxidantOxygen']);atoms[p['oxidantOxygen']].SetAtomMapNum(p['oxygen'])
            elif kind=='charge':atoms[p['chlorine']].SetFormalCharge(0)
            elif kind=='map':atoms[p['oxygen']].SetAtomMapNum(999)
            elif kind=='acid':bad.AddBond(atoms[p['carbon']].GetIdx(),atoms[p['oxidantOxygen']].GetIdx(),Chem.BondType.SINGLE)
            else:
                for h in [p['removedCarbonHydrogen'],p['removedOHHydrogen']]:bad.RemoveBond(atoms[h].GetIdx(),atoms[p['oxidantOxygen']].GetIdx())
                bad.AddBond(atoms[p['removedCarbonHydrogen']].GetIdx(),atoms[p['removedOHHydrogen']].GetIdx(),Chem.BondType.SINGLE)
            with self.subTest(kind=kind),self.assertRaises((ValueError,RuntimeError,KeyError)):rule.validate(before,bad.GetMol(),a['mol'],b['mol'],site)

    def test_remote_stereo_corruption_and_missing_h_cannot_pass(self):
        a,n=_species('a',{'name':'a','smiles':'CC[C@H](C)CCO'},1);b,_=_species('b',{'name':'b','smiles':'[Na+].[O-]Cl'},n)
        site=rule.sites(a['mol'])[0];before=_combine([a,b]);after=_combine([{'mol':m} for m in engine.transform('Alcohol oxidation',[a,b],site)])
        for mutation in ['invert','erase']:
            bad=Chem.Mol(after);center=next(x for x in bad.GetAtoms() if x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED)
            if mutation=='invert':center.InvertChirality()
            else:center.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            with self.assertRaises(ValueError):rule.validate(before,bad,a['mol'],b['mol'],site)
        renumbered=Chem.RenumberAtoms(after,list(reversed(range(after.GetNumAtoms()))));rule.validate(before,renumbered,a['mol'],b['mol'],site)

    def test_all_existing_alkali_counterions_and_original_maps_are_accounted(self):
        for symbol in ['Li','Na','K','Rb','Cs']:
            a={'smiles':'[CH3:75][CH2:2][OH:96]'};b={'smiles':f'[{symbol}+].[O-]Cl'}
            r=next(r for r in service.match_reactions(a,b,MODEL)['reactionOptions'] if r.get('primaryOxidationModel'))
            d=service.reaction_diagram(r['id'],a,b,MODEL)
            self.assertEqual({x.get('originalAtomMap') for x in d['atomMap'] if x.get('originalAtomMap')},{75,2,96})
            self.assertIn(canonical(f'[{symbol}+].[Cl-]'),[x['smiles'] for x in d['products']])
            self.assertFalse(r['assessment']['canRun'])

    def test_missing_or_unsupported_oxidants_do_not_borrow_a_model(self):
        for reagent in ['water','hydrogen','hydrogen-peroxide',{'smiles':'[O-]Cl'}, {'smiles':'OCl'}, {'smiles':'[Na+].[Cl-]'}, {'name':'PCC or Dess-Martin','smiles':'OO'}]:
            try:
                found=options('CCO',reagent=reagent)[3]
            except service.ChemistryError:
                continue  # Invalid/unsupported reagent input is also a rejection.
            self.assertFalse(found)
        with self.assertRaises(service.ChemistryError):service.match_reactions({'smiles':'CCO'},None,MODEL)

    def test_invalid_input_stereo_is_not_normalized_away(self):
        for source in ['C[C@H2]O','CC[C@H](C)CCO |o1:2|','CC/CO']:
            with self.subTest(source=source),self.assertRaises(service.ChemistryError):options(source)

    def test_further_oxidation_is_not_a_new_direct_alcohol_to_acid_path(self):
        self.assertFalse(options('CCCO',conditions={'solvent':'aqueous-protic','oxidationStage':'further'})[3])
        r=service.match_reactions({'smiles':'CCC=O'},'sodium-hypochlorite',{'solvent':'aqueous-protic','oxidationStage':'further'})
        self.assertTrue(any(o['mechanism']=='Aldehyde oxidation' for o in r['reactions']))


for i,case in enumerate(FIXTURE['positive']):setattr(PrimaryOxidationTests,f'test_positive_{i:02}',lambda self,case=case:self.positive(case))
for i,case in enumerate(FIXTURE['negative']):setattr(PrimaryOxidationTests,f'test_negative_{i:02}',lambda self,case=case:self.negative(case))

CONDITIONS=[{}, {'solvent':'aqueous-protic'}, {'oxidationStage':'first'}, MODEL,
            {**MODEL,'temperature':'heated'}, {**MODEL,'temperature':'ambient'}, {**MODEL,'catalyst':'none'},
            {**MODEL,'catalyst':'acid'}, {**MODEL,'catalyst':'metal'}, {**MODEL,'catalyst':'radical'},
            {**MODEL,'solvent':'dry'}, {**MODEL,'solvent':'polar-aprotic'}, {**MODEL,'solvent':'ethanolic-protic'},
            {**MODEL,'peroxide':True}, {**MODEL,'TEMPO':True}, {**MODEL,'workup':'aqueous-release'}, {**MODEL,'additionStage':'one','polymerUnits':'4'}]
def condition_case(self,c):
    a,b,_,found=options('CCO',conditions=c);r=found[0]
    self.assertFalse(r['assessment']['canRun']);self.assertFalse(r['assessment']['evidence']['conditionCompleteEligibility'])
    self.assertTrue(service.reaction_diagram(r['id'],a,b,c)['svg'])
    with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,c)
    self.assertIn('No aldehyde-selective',r['assessment']['note'])
    self.assertIn('conditional 2D only',r['reasoning']['label'])
    self.assertNotIn('Unfavorable',r['reasoning']['label'])
    self.assertTrue(any(f['factor']=='aldehyde-endpoint' and f['effect']=='unknown' for f in r['reasoning']['factors']))
    if c.get('TEMPO'):self.assertIn('TEMPO',r['assessment']['note'])
for i,c in enumerate(CONDITIONS):setattr(PrimaryOxidationTests,f'test_conditions_{i:02}',lambda self,c=c:condition_case(self,c))


class PrimaryOxidationApiTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory(prefix='phase5c-api-');self.addCleanup(folder.cleanup);self.origin='https://oxidation.example.test'
        self.client=create_app({'TRIAL_PASSWORD':'Synthetic-oxidation-password','SESSION_SECRET':secrets.token_hex(32),'PUBLIC_ORIGIN':self.origin,
                               'FRAME_ANCESTORS':self.origin,'DIST_DIR':Path(folder.name),'TESTING':True},chemistry_backend=service).test_client()
        self.assertEqual(self.post('/login',data={'password':'Synthetic-oxidation-password'}).status_code,303)
    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={'Origin':self.origin},**kwargs)
    def matching(self,source='CCO',conditions=None):
        body={'reactantA':{'smiles':source},'reactantB':'sodium-hypochlorite','conditions':MODEL if conditions is None else conditions}
        response=self.post('/api/reactions/match',json=body);self.assertEqual(response.status_code,200)
        return body,response.get_json()
    def test_first_stage_2d_and_calculations_remain_not_final_3d(self):
        body,data=self.matching();r=data['reactionOptions'][0];body['reactionId']=r['id']
        self.assertTrue(r['stoichiometry']['balanced']);self.assertFalse(r['stoichiometry']['context']['canGenerate3D'])
        d=self.post('/api/reactions/diagram',json=body);self.assertEqual(d.status_code,200);self.assertIsNone(d.get_json()['mechanism'])
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_missing_or_strong_aqueous_conditions_cannot_unlock_an_endpoint(self):
        for c in [{},{**MODEL,'temperature':'heated','catalyst':'acid'},{**MODEL,'catalyst':'none','additionStage':'one','polymerUnits':'4'}]:
            body,data=self.matching(conditions=c);body['reactionId']=data['reactionOptions'][0]['id']
            self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200);self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_every_equivalent_source_site_stays_addressable(self):
        body,data=self.matching('OCCCO');self.assertEqual(len(data['reactionOptions']),1);self.assertEqual(len(data['reactions']),2)
        oxygens=set()
        for r in data['reactions']:
            body['reactionId']=r['id'];d=self.post('/api/reactions/diagram',json=body);self.assertEqual(d.status_code,200);oxygens.add(d.get_json()['primaryOxidationModel']['oxygen'])
        self.assertEqual(len(oxygens),2)
    def test_secondary_behavior_in_a_mixed_substrate_is_preserved(self):
        body,data=self.matching('OCCC(O)C');primary=next(r for r in data['reactionOptions'] if r.get('primaryOxidationModel'))
        secondary=next(r for r in data['reactionOptions'] if not r.get('primaryOxidationModel'))
        self.assertFalse(secondary['assessment']['evidence']['canGenerate3D']);self.assertFalse(secondary['stoichiometry']['context']['canGenerate3D'])
        body['reactionId']=secondary['id'];self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
        body['reactionId']=primary['id'];self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_stale_and_forged_permissions_fail_closed(self):
        body,data=self.matching();body['reactionId']=data['reactionOptions'][0]['id'];body['conditions']={**MODEL,'selective':True,'oxidant':'PCC'}
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
        body['reactionId']='forged-primary';self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,422)


if __name__=='__main__':unittest.main()
