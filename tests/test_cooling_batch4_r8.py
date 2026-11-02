"""R8 boundaries: modeled net graphs do not imply a validated cooled endpoint."""
import unittest
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as s

CASES=(
 ('esterification','Esterification','CC(=O)O',{'smiles':'CCO'},{'catalyst':'acid'},'CCOC(C)=O',0),
 ('acid hydrolysis','Ester hydrolysis','CC(=O)OCC','water',{'solvent':'aqueous-protic','catalyst':'acid'},'CC(=O)O',0),
 ('saponification','Ester saponification','CC(=O)OCC','hydroxide',{'solvent':'aqueous-protic'},'CC(=O)[O-]',-1),
 ('secondary oxidation','Alcohol oxidation','CC(O)C','sodium-hypochlorite',{'secondaryOxidationProfile':'naocl-acetic-ketone-v1','solvent':'aqueous-protic','catalyst':'none','oxidationStage':'first'},'CC(C)=O',0),
 ('primary oxidation','Alcohol oxidation','CCO','sodium-hypochlorite',{'solvent':'aqueous-protic','oxidationStage':'first'},'CC=O',0),
 ('aldehyde oxidation','Aldehyde oxidation','CCC=O','sodium-hypochlorite',{'solvent':'aqueous-protic','oxidationStage':'further'},'CCC(=O)O',0),
)

class CoolingR8Boundaries(unittest.TestCase):
 def test_all_six_are_conditional_and_do_not_invent_release_or_3d(self):
  for label,path,source,reagent,settings,product,charge in CASES:
   with self.subTest(case=label):
    pair=({'smiles':source},reagent);c={**settings,'temperature':'cooled'}
    options=[o for o in s.match_reactions(*pair,c)['reactionOptions'] if o['mechanism']==path]
    self.assertTrue(options);o=options[0]
    self.assertEqual(o['productSmiles'],product)
    self.assertEqual(Chem.GetFormalCharge(Chem.MolFromSmiles(product)),charge)
    self.assertFalse(o['assessment']['canRun']);self.assertTrue(o['assessment']['evidence']['canPreview2D'])
    self.assertTrue(o['stoichiometry']['balanced']);self.assertIn('not predicted',o['stoichiometry']['context']['warning'])
    d=s.reaction_diagram(o['id'],*pair,c);self.assertIn('<svg',d['svg'])
    atoms=lambda side:{a['mapId']:(a['element'],a['formalCharge']) for a in d['atoms'] if a['side']==side}
    self.assertEqual({k:v[0] for k,v in atoms('reactants').items()},{k:v[0] for k,v in atoms('products').items()})
    self.assertEqual(sum(v[1] for v in atoms('reactants').values()),sum(v[1] for v in atoms('products').values()))
    with patch.object(s,'mapped_product_molecule',side_effect=AssertionError('must gate before geometry')):
     with self.assertRaises(s.ChemistryError):s.run_curated_reaction(o['id'],*pair,c)

 def test_source_temperature_does_not_override_other_temperature_profiles(self):
  for label,path,source,reagent,settings,_,_ in CASES:
   pair=({'smiles':source},reagent);c={**settings,'temperature':'cooled'}
   o=next(x for x in s.match_reactions(*pair,c)['reactionOptions'] if x['mechanism']==path)
   self.assertFalse(o['assessment']['canRun'],label)
   self.assertIn('cool',o['assessment']['note'].lower())

if __name__=='__main__':unittest.main()
