"""Small geometry checks; agreement is not a general accuracy guarantee."""
import unittest
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolTransforms
from server.chemistry_server import BUILDER_3D_ELEMENTS
from server.explorer_rdkit_geometry import generate_fallback

ROOT = Path(__file__).resolve().parents[1]

class GeometryReferencePilot(unittest.TestCase):
    def test_rdkit_water_against_water_reference(self):
        result = generate_fallback(Chem.MolFromSmiles('O'), BUILDER_3D_ELEMENTS)
        self.assertIsNotNone(result)
        mol = Chem.MolFromMolBlock(result['molfile'], removeHs=False)
        conf = mol.GetConformer()
        hydrogens = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'H']
        oxygen = next(a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'O')
        distances = [rdMolTransforms.GetBondLength(conf, oxygen, h) for h in hydrogens]
        angle = rdMolTransforms.GetAngleDeg(conf, hydrogens[0], oxygen, hydrogens[1])
        # Broad exploratory bounds, not a general scientific acceptance threshold.
        print(f'RDKit water: O-H {distances}, H-O-H {angle:.3f}°; reference approximately 0.958 Å, 104.5°')
        self.assertTrue(all(abs(d - 0.958) < 0.15 for d in distances))
        self.assertLess(abs(angle - 104.5), 10)

    def test_bundled_aluminum_reference_retains_nist_geometry(self):
        mol = Chem.SDMolSupplier(str(ROOT / 'public/molecules/aluminum-trichloride-nist-reference.sdf'), removeHs=False)[0]
        al = next(a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'Al')
        cl = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'Cl']
        conf = mol.GetConformer()
        distances = [rdMolTransforms.GetBondLength(conf, al, i) for i in cl]
        angle = rdMolTransforms.GetAngleDeg(conf, cl[0], al, cl[1])
        print(f'AlCl3 reference transcription: Al-Cl {distances}, Cl-Al-Cl {angle:.3f}°; NIST 2.060 Å, D3h')
        self.assertTrue(all(abs(d - 2.060) < 0.001 for d in distances))
        self.assertLess(abs(angle - 120), 0.1)
