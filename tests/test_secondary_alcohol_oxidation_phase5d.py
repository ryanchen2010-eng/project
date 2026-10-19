"""Literal ketone oracles and independent mapped/stereo/condition checks."""
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, rdCIPLabeler
from server import chemistry_server as service, reaction_engine as engine, secondary_alcohol_oxidation_rule as rule
from server.reaction_diagrams import _species,_combine
from server.production_app import create_app

FIXTURE=json.loads(Path('tests/fixtures/secondary-alcohol-oxidation-phase5d.json').read_text())
PROFILE=FIXTURE['profile']
canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s))


def options(source,conditions=None,reagent='sodium-hypochlorite',reverse=False):
    a,b={'smiles':source},reagent
    if reverse:a,b=b,a
    response=service.match_reactions(a,b,PROFILE if conditions is None else conditions)
    return a,b,response,[r for r in response['reactionOptions'] if r.get('secondaryOxidationModel')]


class SecondaryOxidationTests(unittest.TestCase):
    def positive(self,case):
        for metal in ['Na','K']:
            for reverse in [False,True]:
                with self.subTest(metal=metal,reverse=reverse):
                    a,b,data,found=options(case['substrate'],reagent={'smiles':f'[{metal}+].[O-]Cl'},reverse=reverse)
                    self.assertEqual({r['productSmiles'] for r in found},{canonical(p) for p in case['products']})
                    if case.get('aliases'):
                        self.assertEqual(len(found),1);self.assertEqual(len(found[0]['optionIdentity']['sourceReactionIds']),case['aliases'])
                        self.assertEqual(sum(bool(r.get('secondaryOxidationModel')) for r in data['reactions']),case['aliases'])
                    for r in found:
                        allowed=case['qualified'] and metal=='Na';m=r['secondaryOxidationModel'];ev=r['assessment']['evidence']
                        self.assertEqual(r['assessment']['canRun'],allowed);self.assertEqual(ev['conditionCompleteEligibility'],allowed)
                        self.assertEqual(ev['canGenerate3D'],allowed);self.assertTrue(ev['canPreview2D']);self.assertEqual(m['profileId'],rule.PROFILE)
                        self.assertNotIn('primaryOxidationModel',r);self.assertEqual(r['productFormula'],rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(r['productSmiles'])))
                        self.assertTrue(r['stoichiometry']['balanced']);self.assertEqual([x['coefficient'] for x in r['stoichiometry']['reactants']],[1,1]);self.assertEqual(r['stoichiometry']['excludedInputs'],[])
                        self.assertEqual(r['stoichiometry']['context']['canGenerate3D'],allowed)
                        self.assertIn('not predicted',r['stoichiometry']['context']['warning']);self.assertIn('Full salt mass',r['stoichiometry']['context']['warning'])
                        self.assertEqual(r['information']['capabilities']['mappedMechanism'],'unsupported')
                        d=service.reaction_diagram(r['id'],a,b,PROFILE);self.assertIsNone(d['mechanism']);self.assertIn('net equation',d['note'])
                        before={x['mapId']:x for x in d['atoms'] if x['side']=='reactants'};after={x['mapId']:x for x in d['atoms'] if x['side']=='products'}
                        self.assertEqual({k:x['element'] for k,x in before.items()},{k:x['element'] for k,x in after.items()})
                        self.assertEqual(sum(x['formalCharge'] for x in before.values()),sum(x['formalCharge'] for x in after.values()))
                        self.assertEqual(len(d['atoms']),2*len(before));water=next(i for i,p in enumerate(d['products']) if p['smiles']=='O')
                        self.assertEqual({x['mapId'] for x in after.values() if x['speciesIndex']==water},{m['oxidantOxygen'],m['removedCarbonHydrogen'],m['removedOHHydrogen']})
                        self.assertEqual(after[m['oxygen']]['speciesIndex'],0)
                        self.assertEqual([(c['before'],c['after']) for c in d['bondOrderChanges']],[(1,2)])
                        self.assertEqual((len(d['bondsBroken']),len(d['bondsFormed'])),(3,2));self.assertFalse(any(p['formula']=='H2' for p in d['products']))
                        self.assertEqual({p['smiles'] for p in d['products'][1:]},{'O',canonical(f'[{metal}+].[Cl-]')})
                        if not allowed:
                            with patch.object(service,'mapped_product_molecule',side_effect=AssertionError('gate before 3D')):
                                with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,PROFILE)
                            continue
                        p=service.run_curated_reaction(r['id'],a,b,PROFILE)['product'];self.assertEqual(p['representation'],'3d')
                        main=[x for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==0]
                        self.assertEqual([(x['atomIndex'],x['mapId'],x['element']) for x in main],[(x['index'],x['mapId'],x['element']) for x in p['atomLinks']])
                        mol=Chem.MolFromMolBlock(p['molfile'],removeHs=False);link={x['mapId']:x['index'] for x in p['atomLinks']}
                        carbon=mol.GetAtomWithIdx(link[m['carbon']]);self.assertEqual(carbon.GetHybridization(),Chem.HybridizationType.SP2);self.assertEqual(carbon.GetChiralTag(),Chem.ChiralType.CHI_UNSPECIFIED)
                        self.assertEqual(mol.GetBondBetweenAtoms(link[m['carbon']],link[m['oxygen']]).GetBondTypeAsDouble(),2)
                        for atom in mol.GetAtoms():atom.SetAtomMapNum(0)
                        Chem.AssignStereochemistry(mol,cleanIt=True,force=True);rdCIPLabeler.AssignCIPLabels(mol)
                        for center in r['stereochemistry']['product']['chiralCenters']:
                            if center['specified']:self.assertEqual(mol.GetAtomWithIdx(link[center['atomMap']]).GetProp('_CIPCode'),center['assignment'])
                        # The formal source stereo, not an arbitrary conformer,
                        # determines every retained specified configuration.
                        self.assertIn(r['productSmiles'],{canonical(p) for p in case['products']})

    def negative(self,case):self.assertFalse(options(case['substrate'])[3])

    def test_primary_and_tertiary_cannot_enter_secondary_validator(self):
        from server import alcohol_oxidation_rule as base
        for source in ['CO','CCO','CC(O)(C)C']:
            mol=Chem.MolFromSmiles(source);site=base.sites(mol)[0]
            self.assertFalse(rule.is_secondary(mol,site));self.assertFalse(rule.assess(mol,site)['eligible'])
        for site in [(),(0,),(0,99),(0,0)]:self.assertFalse(rule.assess(Chem.MolFromSmiles('CC(O)C'),site)['eligible'])

    def test_mapped_validation_rejects_corruption_and_h2(self):
        a,n=_species('a',{'smiles':'CC(O)CC','name':'alcohol'},1);b,_=_species('b',{'smiles':'[Na+].[O-]Cl','name':'oxidant'},n)
        site=rule.sites(a['mol'])[0];m=rule.participants(a['mol'],b['mol'],site)
        before=_combine([a,b]);after=_combine([{'mol':p} for p in engine.transform('Alcohol oxidation',[a,b],site)])
        rule.validate(before,after,a['mol'],b['mol'],site)
        for kind in ['stereo','oxygen-swap','charge','map','H2']:
            bad=Chem.RWMol(after);atoms={x.GetAtomMapNum():x for x in bad.GetAtoms()}
            if kind=='stereo':atoms[m['carbon']].SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
            elif kind=='oxygen-swap':atoms[m['oxygen']].SetAtomMapNum(m['oxidantOxygen']);atoms[m['oxidantOxygen']].SetAtomMapNum(m['oxygen'])
            elif kind=='charge':atoms[m['chlorine']].SetFormalCharge(0)
            elif kind=='map':atoms[m['carbon']].SetAtomMapNum(999)
            else:
                for h in [m['removedCarbonHydrogen'],m['removedOHHydrogen']]:bad.RemoveBond(atoms[h].GetIdx(),atoms[m['oxidantOxygen']].GetIdx())
                bad.AddBond(atoms[m['removedCarbonHydrogen']].GetIdx(),atoms[m['removedOHHydrogen']].GetIdx(),Chem.BondType.SINGLE)
            with self.subTest(kind=kind),self.assertRaises((ValueError,RuntimeError,KeyError)):rule.validate(before,bad.GetMol(),a['mol'],b['mol'],site)

    def test_retained_physical_stereo_cannot_be_inverted_or_erased(self):
        a,n=_species('a',{'smiles':'CC[C@H](C)CCCC[C@@H](O)C','name':'a'},1);b,_=_species('b',{'smiles':'[Na+].[O-]Cl','name':'b'},n)
        site=rule.sites(a['mol'])[0];before=_combine([a,b]);after=_combine([{'mol':p} for p in engine.transform('Alcohol oxidation',[a,b],site)])
        self.assertEqual(sum(x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED for x in after.GetAtoms()),1)
        for mutation in ['invert','erase']:
            bad=Chem.Mol(after);c=next(x for x in bad.GetAtoms() if x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED)
            if mutation=='invert':c.InvertChirality()
            else:c.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
            with self.assertRaises(ValueError):rule.validate(before,bad,a['mol'],b['mol'],site)
        rule.validate(before,Chem.RenumberAtoms(after,list(reversed(range(after.GetNumAtoms())))),a['mol'],b['mol'],site)

    def test_source_maps_and_exact_alkali_salts(self):
        for metal in ['Li','Na','K','Rb','Cs']:
            a,b,data,found=options('[CH3:75][CH:2]([OH:96])CC',reagent={'smiles':f'[{metal}+].[O-]Cl'})
            r=found[0];d=service.reaction_diagram(r['id'],a,b,PROFILE)
            self.assertEqual({x.get('originalAtomMap') for x in d['atomMap'] if x.get('originalAtomMap')},{75,2,96})
            self.assertEqual(r['assessment']['canRun'],metal=='Na');self.assertIn(canonical(f'[{metal}+].[Cl-]'),[p['smiles'] for p in d['products']])

    def test_invalid_raw_stereo_and_missing_oxidants(self):
        for source in ['C[C@H](O)C','CC/CC(O)C','CC[C@H](C)CCCC(O)C |o1:2|']:
            with self.subTest(source=source),self.assertRaises(service.ChemistryError):options(source)
        with self.assertRaises(service.ChemistryError):service.match_reactions({'smiles':'CC(O)C'},None,PROFILE)
        for reagent in ['water','hydrogen','hydrogen-peroxide',{'smiles':'OO','name':'PCC or DMP'}]:self.assertFalse(options('CC(O)C',reagent=reagent)[3])
        for value in [False,None,0,[],{}]:
            r=options('CC(O)C',conditions={**PROFILE,'secondaryOxidationProfile':value})[3][0]
            self.assertFalse(r['assessment']['canRun']);self.assertEqual(r['assessment']['status'],'unsupported-pathway')

    def test_mixed_primary_behavior_is_not_qualified_by_secondary_profile(self):
        a,b,data,_=options('OCCCCCCCC(O)C')
        primary=next(r for r in data['reactionOptions'] if r.get('primaryOxidationModel'))
        self.assertFalse(primary['assessment']['canRun']);self.assertFalse(primary['primaryOxidationModel']['aldehydeEndpointValidated'])
        with self.assertRaises(service.ChemistryError):service.run_curated_reaction(primary['id'],a,b,PROFILE)

    def test_equivalent_source_site_aliases_remain_addressable(self):
        a,b,data,found=options('CC(O)CCCCCC(O)C');self.assertEqual(len(found),1)
        maps=set()
        for r in data['reactions']:
            if r.get('secondaryOxidationModel'):
                d=service.reaction_diagram(r['id'],a,b,PROFILE);maps.add(d['secondaryOxidationModel']['oxygen'])
        self.assertEqual(len(maps),2)


for i,c in enumerate(FIXTURE['positive']):setattr(SecondaryOxidationTests,f'test_positive_{i:02}',lambda self,c=c:self.positive(c))
for i,c in enumerate(FIXTURE['negative']):setattr(SecondaryOxidationTests,f'test_negative_{i:02}',lambda self,c=c:self.negative(c))

UNQUALIFIED=[{}, {'solvent':'aqueous-protic'}, {k:v for k,v in PROFILE.items() if k!='secondaryOxidationProfile'},
            *[{k:v for k,v in PROFILE.items() if k!=field} for field in ['solvent','temperature','catalyst','oxidationStage']],
            *[{**PROFILE,field:value} for field,value in [('temperature','heated'),('catalyst','acid'),('catalyst','metal'),('catalyst','radical'),('solvent','dry'),('solvent','polar-aprotic'),('oxidationStage','further'),('workup','aqueous-release'),('secondaryOxidationProfile','PCC'),('secondaryOxidationProfile',True),('peroxide',True),('TEMPO',True),('pH','12')]]]
def condition_test(self,c):
    a,b,_,found=options('CC(O)C',conditions=c);r=found[0]
    self.assertFalse(r['assessment']['canRun']);self.assertFalse(r['assessment']['evidence']['conditionCompleteEligibility'])
    self.assertTrue(service.reaction_diagram(r['id'],a,b,c)['svg']);self.assertIn('conditional 2D only',r['reasoning']['label'])
    with patch.object(service,'mapped_product_molecule',side_effect=AssertionError('gate before conformer')):
        with self.assertRaises(service.ChemistryError):service.run_curated_reaction(r['id'],a,b,c)
for i,c in enumerate(UNQUALIFIED):setattr(SecondaryOxidationTests,f'test_conditions_{i:02}',lambda self,c=c:condition_test(self,c))


class SecondaryOxidationApiTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory(prefix='phase5d-api-');self.addCleanup(folder.cleanup);self.origin='https://secondary.example.test'
        self.client=create_app({'TRIAL_PASSWORD':'Synthetic-secondary-password','SESSION_SECRET':secrets.token_hex(32),'PUBLIC_ORIGIN':self.origin,'FRAME_ANCESTORS':self.origin,'DIST_DIR':Path(folder.name),'TESTING':True},chemistry_backend=service).test_client()
        self.assertEqual(self.post('/login',data={'password':'Synthetic-secondary-password'}).status_code,303)
    def post(self,path,**kwargs):return self.client.post(path,base_url=self.origin,headers={'Origin':self.origin},**kwargs)
    def match(self,source='CC(O)C',conditions=None):
        body={'reactantA':{'smiles':source},'reactantB':'sodium-hypochlorite','conditions':PROFILE if conditions is None else conditions}
        data=self.post('/api/reactions/match',json=body);self.assertEqual(data.status_code,200)
        r=next(r for r in data.get_json()['reactionOptions'] if r.get('secondaryOxidationModel'));body['reactionId']=r['id'];return body,r
    def test_explicit_profile_runs_and_matches_2d_atoms(self):
        body,r=self.match('C[C@H](O)CC');self.assertTrue(r['assessment']['evidence']['canGenerate3D'])
        d=self.post('/api/reactions/diagram',json=body);p=self.post('/api/reactions/run',json=body);self.assertEqual((d.status_code,p.status_code),(200,200))
        self.assertEqual(d.get_json()['products'][0]['smiles'],canonical('CC(=O)CC'));self.assertIsNone(d.get_json()['mechanism'])
        self.assertEqual([(x['atomIndex'],x['mapId']) for x in d.get_json()['atoms'] if x['side']=='products' and x['speciesIndex']==0],[(x['index'],x['mapId']) for x in p.get_json()['product']['atomLinks']])
    def test_generic_aqueous_conditions_do_not_mean_acetic_acid(self):
        body,r=self.match(conditions={'solvent':'aqueous-protic','oxidationStage':'first'})
        self.assertIn('secondaryOxidationProfile',r['assessment']['missingSettings']);self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200);self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_competition_stays_conditional_despite_declared_profile(self):
        for source in ['COCCCC(O)C','CC(O)CCCCCC(O)C','OCCCCCCCC(O)C']:
            body,r=self.match(source);self.assertFalse(r['assessment']['canRun']);self.assertEqual(self.post('/api/reactions/diagram',json=body).status_code,200);self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_stale_conditions_and_forged_permission_fail_closed(self):
        body,r=self.match();body['conditions']={};body['canRun']=True
        self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
        body['conditions']={**PROFILE,'selective':True};self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
    def test_wrong_conditions_enum_and_authentication_are_enforced(self):
        body,r=self.match();body['conditions']={**PROFILE,'temperature':'25C'};self.assertEqual(self.post('/api/reactions/run',json=body).status_code,422)
        self.assertNotEqual(self.client.application.test_client().post('/api/reactions/run',base_url=self.origin,headers={'Origin':self.origin},json=body).status_code,200)


if __name__=='__main__':unittest.main()
