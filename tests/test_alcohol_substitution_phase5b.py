"""Independent HX net structures/confidence; no engine-produced expectations."""
import hashlib
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from server import chemistry_server as service, reaction_engine as engine, alcohol_substitution_rule as rule
from server.reaction_diagrams import _species, _combine
from server.stereochemistry import inspect_stereochemistry
from server.production_app import create_app

FIXTURE = json.loads(Path('tests/fixtures/alcohol-substitution-phase5b.json').read_text())
canonical = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s))
PATHWAY = 'Alcohol substitution'


def options(source, reagent='hydrogen-bromide', conditions=None, reverse=False):
    a, b = {'smiles':source}, reagent
    if reverse: a,b=b,a
    response = service.match_reactions(a,b,conditions)
    return a,b,response,[o for o in response['reactionOptions'] if o['mechanism']==PATHWAY]


class SubstitutionTests(unittest.TestCase):
    def positive(self, case):
        for symbol,reagent in [('Br','hydrogen-bromide'),('I','hydrogen-iodide')]+([('Cl','hydrogen-chloride')] if case.get('chloride') else []):
            for reverse in [False,True]:
                with self.subTest(symbol=symbol,reverse=reverse):
                    conditions={'temperature':case['temperature'],'additionStage':'one','polymerUnits':'4'}
                    a,b,response,found=options(case['substrate'],reagent,conditions,reverse)
                    self.assertEqual({o['productSmiles'] for o in found},{canonical(s.replace('Br',symbol)) for s in case['products']})
                    self.assertTrue(found)
                    if case.get('legacySites'):
                        legacy=[o for o in response['reactions'] if o['mechanism']==PATHWAY]
                        self.assertEqual(len(legacy),case['legacySites'])
                        self.assertEqual(len(found),1)
                        self.assertEqual(len(found[0]['optionIdentity']['sourceReactionIds']),2)
                        self.assertEqual(len(found[0]['optionIdentity']['siteAliases']),2)
                        selected_oxygens=set()
                        for alias in legacy:
                            d=service.reaction_diagram(alias['id'],a,b,conditions)
                            model=d['alcoholSubstitutionModel'];selected_oxygens.add(model['oxygen'])
                            self.assertEqual({x['mapId'] for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==1},
                                             {model['oxygen'],model['reagentHydrogen'],model['originalOHHydrogen']})
                        self.assertEqual(len(selected_oxygens),2)
                    for r in found:
                        model=r['alcoholSubstitutionModel']; basis=r['stoichiometry']
                        self.assertTrue(model['hxConsumed']); self.assertIsNone(model['stereoisomerRatios'])
                        self.assertEqual(model['hydrogenHalide'],'H'+symbol)
                        self.assertEqual(model['mappedMechanism'],'unsupported')
                        self.assertEqual(r['information']['capabilities']['mappedMechanism'],'unsupported')
                        self.assertEqual(r['assessment']['canRun'],case['allow3D'])
                        self.assertEqual(r['assessment']['evidence']['canGenerate3D'],case['allow3D'])
                        self.assertTrue(r['assessment']['evidence']['canPreview2D'])
                        self.assertEqual(r['assessment']['evidence']['notApplicableSettings'],['additionStage','polymerUnits'])
                        self.assertTrue(basis['balanced']); self.assertEqual(len(basis['reactants']),2)
                        self.assertEqual(basis['excludedInputs'],[])
                        self.assertEqual([x['coefficient'] for x in basis['reactants']],[1,1])
                        self.assertEqual(basis['product']['coefficient'],1)
                        self.assertEqual(r['byproducts'],[{'name':'Water','formula':'H2O'}])
                        self.assertIn('HX is consumed',basis['context']['warning'])
                        self.assertEqual(basis['context']['canGenerate3D'],case['allow3D'])
                        d=service.reaction_diagram(r['id'],a,b,conditions)
                        self.assertIsNone(d['mechanism']); self.assertFalse(d['medium'])
                        self.assertEqual(d['assessment'],r['assessment'])
                        self.assertIn('not bare OH departure',d['note'])
                        identity=lambda side:{x['mapId']:(x['element'],x['formalCharge']) for x in d['atoms'] if x['side']==side}
                        self.assertEqual(identity('reactants'),identity('products')); self.assertEqual(len(d['atoms']),2*len(identity('reactants')))
                        water=[x for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==1]
                        self.assertEqual({x['mapId'] for x in water},{model['oxygen'],model['reagentHydrogen'],model['originalOHHydrogen']})
                        self.assertTrue(all(not x['linkedTo3D'] for x in water))
                        self.assertEqual(len(d['bondsBroken']),2);self.assertEqual(len(d['bondsFormed']),2);self.assertEqual(d['bondOrderChanges'],[])
                        x=next(x for x in d['atoms'] if x['side']=='products' and x['mapId']==model['incoming'])
                        self.assertEqual(x['element'],symbol);self.assertEqual(x['speciesIndex'],0)
                        if case['allow3D']:
                            p=service.run_curated_reaction(r['id'],a,b,conditions)['product']
                            self.assertEqual(p['representation'],'3d');self.assertEqual(p['smiles'],r['productSmiles'])
                            main=[x for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==0]
                            self.assertEqual([(x['atomIndex'],x['mapId']) for x in main],[(x['index'],x['mapId']) for x in p['atomLinks']])
                        else:
                            with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,conditions)

    def negative(self,case):
        _,_,response,found=options(case['substrate'],case.get('reagent','hydrogen-bromide'),{'temperature':'heated'})
        self.assertFalse(found)
        if case['reason']:self.assertIn(case['reason'].lower(),' '.join(response['unsupportedReasons']).lower())

    def test_local_mode_and_specified_configuration_are_not_guessed(self):
        for source in ['CC[C@H](O)CCC','CC[C@@H](O)CCC','CC[C@](O)(C)CCC','CC[C@@](O)(C)CCC']:
            _,_,_,found=options(source,conditions={'temperature':'ambient'})
            self.assertTrue(found)
            r=found[0]; self.assertNotIn('@',r['productSmiles']);self.assertTrue(r['alcoholSubstitutionModel']['stereochemistryUnresolved'])
            self.assertFalse(r['assessment']['canRun']);self.assertIsNone(r['alcoholSubstitutionModel']['stereoisomerRatios'])
            self.assertTrue(any(c['specified'] for c in r['stereochemistry']['reactant']['chiralCenters']))
            self.assertFalse(any(c['specified'] for c in r['stereochemistry']['product']['chiralCenters']))
        _,_,_,primary=options('CCO',conditions={'temperature':'heated'})
        self.assertIn('SN2 rationale',primary[0]['alcoholSubstitutionModel']['mode'])
        _,_,_,tertiary=options('CC(O)(C)C',conditions={'temperature':'ambient'})
        self.assertIn('SN1-type',tertiary[0]['alcoholSubstitutionModel']['mode'])

    def test_distant_physical_configuration_and_cip_are_independent(self):
        a,b,_,found=options('C[C@H](CCCCO)CCCCOC',conditions={'temperature':'heated'})
        r=found[0];before=r['stereochemistry']['reactant']['chiralCenters'];after=r['stereochemistry']['product']['chiralCenters']
        self.assertEqual([x['atomMap'] for x in before],[x['atomMap'] for x in after])
        self.assertEqual({before[0]['assignment'],after[0]['assignment']},{'R','S'})
        self.assertEqual(canonical(r['productSmiles']),canonical('C[C@H](CCCCBr)CCCCOC'))
        self.assertFalse(r['assessment']['canRun'])

    def test_3d_coordinates_retain_distant_enantiomer_identity(self):
        for source in ['CC[C@H](C)CCCCO','CC[C@@H](C)CCCCO']:
            conditions={'temperature':'heated'};a,b,_,found=options(source,conditions=conditions);r=found[0]
            target=next(c for c in r['stereochemistry']['product']['chiralCenters'] if c['specified'])
            product=service.run_curated_reaction(r['id'],a,b,conditions)['product']
            shape=Chem.MolFromMolBlock(product['molfile'],removeHs=False)
            indices={atom.GetAtomMapNum():atom.GetIdx() for atom in shape.GetAtoms()}
            for atom in shape.GetAtoms():atom.SetAtomMapNum(0);atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            Chem.AssignStereochemistryFrom3D(shape)
            self.assertEqual(dict(Chem.FindMolChiralCenters(shape,includeUnassigned=True,force=True))[indices[target['atomMap']]],target['assignment'])

    def test_source_maps_survive_and_name_formula_are_not_permissions(self):
        a={'name':'fake salt','smiles':'[CH3:71][CH2:9][OH:42]'};b={'name':'fake water','smiles':'[BrH:88]'}
        r=next(o for o in service.match_reactions(a,b,{'temperature':'heated'})['reactionOptions'] if o['mechanism']==PATHWAY)
        d=service.reaction_diagram(r['id'],a,b,{'temperature':'heated'})
        self.assertEqual(r['productSmiles'],'CCBr')
        self.assertEqual({x.get('originalAtomMap') for x in d['atomMap'] if x.get('originalAtomMap')},{71,9,42,88})

    def test_bad_activation_and_nucleophiles_never_displace_oh(self):
        for reagent in ['[Br-]','[Cl-]','[I-]','F','P(Br)(Br)Br','O=S(Cl)Cl','[Na+].[Br-]','hydroxide','water']:
            b=reagent if reagent in service.REACTANTS else {'smiles':reagent}
            try:_,_,_,found=options('CCCO',b,{'temperature':'heated'})
            except service.ChemistryError:continue
            self.assertFalse(found,reagent)

    def test_invalid_stereochemistry_fails_before_normalization(self):
        for source in ['C[C@H](O)C','CC[C@H](C)CCCCO |o1:2|','CC/C(O)C']:
            with self.subTest(source=source),self.assertRaises(service.ChemistryError):options(source,conditions={'temperature':'heated'})

    def test_size_and_invalid_site_limits_remain_explicit(self):
        self.assertTrue(options('C'*26+'O',conditions={'temperature':'heated'})[3])
        self.assertFalse(options('C'*27+'O',conditions={'temperature':'heated'})[3])
        mol=Chem.MolFromSmiles('CCO');reagent=Chem.MolFromSmiles('Br')
        for site in [(),(0,),(0,99),(0,0)]:self.assertFalse(rule.assess(mol,reagent,site)['eligible'])

    def test_edit_contract_rejects_atom_bond_charge_and_stereo_corruption(self):
        a,_=_species('a',{'name':'a','smiles':'CC[C@H](C)CCCCO'},1);b,_=_species('b',{'name':'b','smiles':'Br'},a['mol'].GetNumAtoms()+1)
        site=rule.sites(a['mol'])[0];before=_combine([a,b]);after=Chem.CombineMols(*engine.transform(PATHWAY,[a,b],site))
        rule.validate(before,after,a['mol'],b['mol'],site)
        p=rule.participants(a['mol'],b['mol'],site)
        for kind in ['stereo','local-stereo','charge','map','bond']:
            mutant=Chem.RWMol(after)
            atoms={x.GetAtomMapNum():x for x in mutant.GetAtoms()}
            if kind=='stereo':next(x for x in mutant.GetAtoms() if x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED).InvertChirality()
            elif kind=='local-stereo':atoms[p['center']].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            elif kind=='charge':atoms[p['incoming']].SetFormalCharge(-1)
            elif kind=='map':atoms[p['incoming']].SetAtomMapNum(999)
            else:mutant.RemoveBond(atoms[p['center']].GetIdx(),atoms[p['incoming']].GetIdx())
            with self.subTest(kind=kind),self.assertRaises((ValueError,RuntimeError,KeyError)):rule.validate(before,mutant.GetMol(),a['mol'],b['mol'],site)

    def test_unchanged_benchmark_and_phase5a_sources(self):
        self.assertEqual(hashlib.sha256(Path('scripts/audit_reaction_lab.py').read_bytes()).hexdigest(),'1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55')
        self.assertEqual(hashlib.sha256(Path('benchmarks/reaction-conditions/1.0.0.json').read_bytes()).hexdigest(),'35ce7ce6f3c3967a06fc354c8bc9fc8319a2247f3b3ac0c7cd246ec75ed8ca1e')
        self.assertEqual(hashlib.sha256(Path('server/alcohol_dehydration_rule.py').read_bytes()).hexdigest(),'173886554adbcb0ca76819b0a1f153fd8baad186cd57abc7ab99356327a87114')


for i,case in enumerate(FIXTURE['positive']):
    setattr(SubstitutionTests,f'test_positive_{i:02}',lambda self,case=case:self.positive(case))
for i,case in enumerate(FIXTURE['negative']):
    setattr(SubstitutionTests,f'test_negative_{i:02}',lambda self,case=case:self.negative(case))

CONDITIONS=[{}, {'temperature':'ambient'}, {'temperature':'heated','catalyst':'acid'}, {'temperature':'heated','catalyst':'radical'},
            {'temperature':'heated','solvent':'dry'}, {'temperature':'heated','solvent':'ethanolic-protic'}, {'temperature':'heated','solvent':'polar-aprotic'},
            {'temperature':'heated','peroxide':True}, {'temperature':'heated','workup':'aqueous-release'}, {'temperature':'heated','catalyst':'metal'},
            {'temperature':'heated','oxidationStage':'first'}, {'temperature':'heated','catalyst':'lindlar'}]
def condition_test(self,c):
    a,b,_,found=options('CCO',conditions=c);self.assertTrue(found)
    r=found[0];self.assertFalse(r['assessment']['canRun']);self.assertTrue(r['assessment']['evidence']['canPreview2D'])
    self.assertTrue(service.reaction_diagram(r['id'],a,b,c)['svg'])
    with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,c)
    self.assertIn('HX is consumed',r['stoichiometry']['context']['warning'])
for i,c in enumerate(CONDITIONS):setattr(SubstitutionTests,f'test_conditions_{i:02}',lambda self,c=c:condition_test(self,c))


class PublicSubstitutionTests(unittest.TestCase):
    def setUp(self):
        self.origin='https://substitution.example.test'
        folder=tempfile.TemporaryDirectory(prefix='phase5b-api-');self.addCleanup(folder.cleanup)
        self.client=create_app({'TRIAL_PASSWORD':'Synthetic-substitution-password','SESSION_SECRET':secrets.token_hex(32),'PUBLIC_ORIGIN':self.origin,
                               'FRAME_ANCESTORS':self.origin,'DIST_DIR':Path(folder.name),'TESTING':True},chemistry_backend=service).test_client()
        self.assertEqual(self.post('/login',data={'password':'Synthetic-substitution-password'}).status_code,303)
    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={'Origin':self.origin},**kwargs)
    def matching(self,source='CCO',conditions=None):
        body={'reactantA':{'smiles':source},'reactantB':'hydrogen-bromide','conditions':{'temperature':'heated'} if conditions is None else conditions}
        response=self.post('/api/reactions/match',json=body);self.assertEqual(response.status_code,200)
        return body,[r for r in response.get_json()['reactionOptions'] if r['mechanism']==PATHWAY]
    def test_match_diagram_run_and_required_amount_basis(self):
        body,found=self.matching();r=found[0];body['reactionId']=r['id']
        self.assertEqual(len(r['stoichiometry']['reactants']),2)
        self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200)
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,200)
    def test_stale_permissions_cannot_ignore_unknown_conditions(self):
        body,found=self.matching();body['reactionId']=found[0]['id'];body['conditions']['peroxide']=True
        self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200)
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_missing_temperature_keeps_2d_not_3d(self):
        body,found=self.matching(conditions={});body['reactionId']=found[0]['id']
        self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200)
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_secondary_and_other_oxygen_products_are_not_asserted(self):
        for source in ['CC[C@H](O)CCC','COCCCCCCCCO','OCc1ccccc1']:
            body,found=self.matching(source);self.assertTrue(found);body['reactionId']=found[0]['id']
            self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200)
            self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_actual_hx_not_additional_catalyst(self):
        body,found=self.matching(conditions={'temperature':'heated','catalyst':'none','solvent':'aqueous-protic','additionStage':'one','polymerUnits':'4'})
        self.assertTrue(found[0]['assessment']['canRun']);body['reactionId']=found[0]['id']
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,200)
    def test_unsupported_activation_and_forged_reaction_id(self):
        body,found=self.matching();body['reactionId']='forged-hx';self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
        body['reactantB']={'smiles':'[Br-]'};self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)


if __name__=='__main__':unittest.main()
