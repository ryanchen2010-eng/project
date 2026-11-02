"""Versioned audit fixtures: eight references, independent of frozen benchmark."""
import unittest
from server import chemistry_server as s, reaction_temperature_profiles as p

PROFILES = (
 ('cooled-alkene-bromination-v1','Bromination','C=C','bromine',{'solvent':'dry','catalyst':'none'}),
 ('cooled-peroxyacid-epoxidation-v1','Epoxidation','C=C',{'smiles':'O=C(OO)c1cccc(Cl)c1'},{'solvent':'dry','catalyst':'none'}),
 ('cooled-perbenzoic-epoxidation-v1','Epoxidation','C=Cc1ccccc1',{'smiles':'O=C(OO)c1ccccc1'},{'solvent':'dry','catalyst':'none'}),
 ('cooled-cyclohexene-pd-silica-v1','Hydrogenation','C1=CCCCC1','hydrogen',{'solvent':'dry','catalyst':'metal'}),
 ('cooled-isobutylene-hcl-v1','Hydrohalogenation','C=C(C)C','hydrogen-chloride',{'solvent':'dry','catalyst':'none'}),
 ('cooled-isobutylene-os-peroxide-v1','Alkene dihydroxylation','C=C(C)C','hydrogen-peroxide',{'solvent':'dry','catalyst':'osmium','workup':''}),
 ('cooled-crotonic-os-peroxide-v1','Alkene dihydroxylation','CC=CC(=O)O','hydrogen-peroxide',{'solvent':'dry','catalyst':'osmium','workup':'aqueous-release'}),
 ('cooled-cinnamic-os-peroxide-v1','Alkene dihydroxylation','O=C(O)C=Cc1ccccc1','hydrogen-peroxide',{'solvent':'dry','catalyst':'osmium','workup':'aqueous-release'}),
)

def match(path,source,reagent,c):
 pair=({'smiles':source},reagent)
 return pair,[x for x in s.match_reactions(*pair,c)['reactionOptions'] if x['mechanism']==path]

class CoolingBatch4Audit(unittest.TestCase):
 def test_eight_models_source_graphs_and_endpoint_consistency(self):
  self.assertEqual({x[0] for x in PROFILES},set(p.PROFILES_BY_ID))
  for ident,path,source,reagent,setting in PROFILES:
   with self.subTest(profile=ident):
    c={**setting,'temperature':'cooled','conditionProfileId':ident,'conditionProfileVersion':'1'}
    pair,opts=match(path,source,reagent,c);self.assertTrue(opts)
    option=opts[0];assessment=option['assessment'];self.assertTrue(assessment['canRun'])
    self.assertEqual(assessment['cooling']['modelId'],ident)
    self.assertTrue(assessment['evidence']['canGenerate3D']);self.assertTrue(option['stoichiometry']['balanced'])
    descriptor=assessment['namedConditionProfile']['descriptor'];self.assertTrue(descriptor['evidence']);self.assertTrue(descriptor['unknowns'])
    diagram=s.reaction_diagram(option['id'],*pair,c);self.assertEqual(diagram['assessment'],assessment)
    before=[x for x in diagram['atoms'] if x['side']=='reactants'];after=[x for x in diagram['atoms'] if x['side']=='products']
    atoms=lambda rows:{x['mapId']:(x['element'],x['formalCharge']) for x in rows}
    self.assertEqual(atoms(before),atoms(after))
    product=s.run_curated_reaction(option['id'],*pair,c)['product'];self.assertEqual(product['representation'],'3d')
    self.assertEqual(option['stoichiometry']['context']['namedConditionProfile']['reference']['id'],ident)
    self.assertIn('not experimental yields',option['stoichiometry']['context']['warning'])

 def test_all_named_models_fail_closed_for_version_conditions_and_cross_path(self):
  for ident,path,source,reagent,setting in PROFILES:
   c={**setting,'temperature':'cooled','conditionProfileId':ident,'conditionProfileVersion':'1'}
   for extra in ({'conditionProfileVersion':'2'},{'temperature':'ambient'},{'solvent':'aqueous-protic'},{'catalyst':'radical'}, {'unknownOverride':'yes'}):
    with self.subTest(profile=ident,change=extra):
     cc={**c,**extra};pair,opts=match(path,source,reagent,cc)
     for option in opts:
      self.assertFalse(option['assessment']['canRun'])
      with self.assertRaises(s.ChemistryError):s.run_curated_reaction(option['id'],*pair,cc)
   self.assertIsNone(p.reviewed_profile(ident,'SN1'))

if __name__ == '__main__':unittest.main()
