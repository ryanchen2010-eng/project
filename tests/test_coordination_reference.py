import math
import unittest
from unittest.mock import patch
from rdkit import Chem
from rdkit.Geometry import Point3D
from server import coordination_reference as reference
from server import chemistry_server as service


def synthetic_structure():
    mol = Chem.RWMol()
    fe = mol.AddAtom(Chem.Atom('Fe'))
    axes = [(0, 0, 1), (0, 0, -1), (1, 0, 0), (-0.5, math.sqrt(3)/2, 0), (-0.5, -math.sqrt(3)/2, 0)]
    for _ in axes:
        c, o = mol.AddAtom(Chem.Atom('C')), mol.AddAtom(Chem.Atom('O'))
        mol.AddBond(fe, c, Chem.BondType.SINGLE)
        mol.AddBond(c, o, Chem.BondType.TRIPLE)
    conf = Chem.Conformer(11)
    conf.SetAtomPosition(0, Point3D(0, 0, 0))
    for i, (x, y, z) in enumerate(axes):
        conf.SetAtomPosition(1 + 2*i, Point3D(x*1.8, y*1.8, z*1.8))
        conf.SetAtomPosition(2 + 2*i, Point3D(x*2.95, y*2.95, z*2.95))
    mol.AddConformer(conf)
    return Chem.MolToMolBlock(mol)


def synthetic_carbonyl(metal, axes):
    mol = Chem.RWMol()
    center = mol.AddAtom(Chem.Atom(metal))
    conf = Chem.Conformer(1 + 2 * len(axes))
    conf.SetAtomPosition(0, Point3D(0, 0, 0))
    for i, (x, y, z) in enumerate(axes):
        c, o = mol.AddAtom(Chem.Atom('C')), mol.AddAtom(Chem.Atom('O'))
        mol.AddBond(center, c, Chem.BondType.SINGLE)
        mol.AddBond(c, o, Chem.BondType.TRIPLE)
        conf.SetAtomPosition(c, Point3D(x * 1.8, y * 1.8, z * 1.8))
        conf.SetAtomPosition(o, Point3D(x * 2.95, y * 2.95, z * 2.95))
    mol.AddConformer(conf)
    return Chem.MolToMolBlock(mol)


class CoordinationReferenceTests(unittest.TestCase):
    def test_reviewed_class_accepts_only_exact_nickel_and_chromium_records(self):
        for cid in (26039, 25589):
            profile = reference.CARBONYL_PROFILES[cid]
            with self.subTest(cid=cid):
                self.assertTrue(reference.matches_reviewed_fragments(cid, profile['smiles']))
                self.assertFalse(reference.matches_reviewed_fragments(cid, reference.PUBCHEM_FE_CO5))
                self.assertFalse(reference.matches_reviewed_fragments(cid, profile['smiles'] + '.O'))
                self.assertFalse(reference.validate_carbonyl_sdf(synthetic_structure(), cid))

    def test_tetrahedral_and_octahedral_models_validate(self):
        unit = 1 / math.sqrt(3)
        tetra = [(unit, unit, unit), (unit, -unit, -unit), (-unit, unit, -unit), (-unit, -unit, unit)]
        octa = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        self.assertTrue(reference.validate_carbonyl_sdf(synthetic_carbonyl('Ni', tetra), 26039))
        self.assertTrue(reference.validate_carbonyl_sdf(synthetic_carbonyl('Cr', octa), 25589))
        self.assertFalse(reference.validate_carbonyl_sdf(synthetic_carbonyl('Ni', [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]), 26039))

    def test_strict_identity_no_general_mixture_or_ion_substitution(self):
        self.assertTrue(reference.matches_reviewed_fragments(26040, reference.PUBCHEM_FE_CO5))
        for cid, smiles in [(518773, reference.PUBCHEM_FE_CO5), (26040, '[Fe].[C]=O'), (26040, '[Fe+2].[C]=O.[C]=O.[C]=O.[C]=O.[C]=O'), (26040, '[Ni].[C]=O.[C]=O.[C]=O.[C]=O.[C]=O'), (26040, '[13C]=O.[C]=O.[C]=O.[C]=O.[C]=O.[Fe]')]:
            with self.subTest(cid=cid, smiles=smiles):
                self.assertFalse(reference.matches_reviewed_fragments(cid, smiles))

    def test_geometry_graph_and_trigonal_bipyramid_checked(self):
        model = synthetic_structure()
        self.assertTrue(reference.validate_fe_carbonyl_sdf(model))
        self.assertFalse(reference.validate_fe_carbonyl_sdf(model.replace('Fe', 'Ni', 1)))
        self.assertFalse(reference.validate_fe_carbonyl_sdf(model.replace('  1  2  1', '  1  2  2', 1)))
        self.assertFalse(reference.validate_fe_carbonyl_sdf(model.replace('    0.0000    0.0000   -1.8000', '    0.0000    0.0000    1.8000')))

    def test_source_failure_or_changed_selected_identity_never_returns_reference(self):
        with patch.object(service, 'get_pubchem_smiles', return_value=reference.PUBCHEM_FE_CO5), patch.object(reference, 'fetch_nist_reference', return_value=synthetic_structure()):
            self.assertTrue(service.resolve_coordination_reference(26040))
            self.assertIsNone(service.resolve_coordination_reference(518773))
        with patch.object(service, 'get_pubchem_smiles', return_value='[Fe].[C]=O'), patch.object(reference, 'fetch_nist_reference') as fetch:
            self.assertIsNone(service.resolve_coordination_reference(26040))
            fetch.assert_not_called()
