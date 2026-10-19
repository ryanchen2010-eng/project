"""Phase 2H independent public regressions; never added to curated examples."""
import unittest
from importlib import import_module
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service, carbocation_compatibility as cation
from server import sn1_rule, e1_rule, sn2_rule, reaction_compatibility as compatibility
from server.reaction_conditions import assess_conditions

PROFILES = {'SN1': ('water', {'solvent': 'aqueous-protic', 'temperature': 'ambient'}),
            'E1': ('water', {'solvent': 'aqueous-protic', 'temperature': 'heated'}),
            'SN2': ('hydroxide', {'solvent': 'polar-aprotic'}),
            'E2': ('hydroxide', {'solvent': 'ethanolic-protic', 'temperature': 'heated'})}


def canonical(smiles): return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


class ConsistencyPhase2HTests(unittest.TestCase):
    def options(self, substrate, path, conditions=None, reagent=None):
        default_reagent, default_conditions = PROFILES[path]
        ref = {'name': 'Independent Phase 2H structure', 'smiles': substrate}
        result = service.match_reactions(ref, reagent or default_reagent, default_conditions if conditions is None else conditions)
        return ref, [r for r in result['reactions'] if r['mechanism'] == path], result

    def verified(self, substrate, path, expected, reagent=None):
        ref, options, result = self.options(substrate, path, reagent=reagent)
        self.assertEqual({r['productSmiles'] for r in options}, {canonical(s) for s in expected}, result['unsupportedReasons'])
        # Reuse strict existing mapping/elementary-step/3D checkers, with
        # independently specified products. Imported locally to avoid duplicate
        # unittest discovery of the existing classes.
        name = path.lower()
        module = import_module(f'tests.test_{name}_compatibility')
        checker = getattr(module, path + 'CompatibilityTests')()
        for r in options:
            if path == 'SN2': checker.check_option(ref, r, r['productSmiles'], reagent=reagent or 'hydroxide')
            else: checker.check_option(ref, r, r['productSmiles'])
        return options

    def test_isopropyl_shared_ionization_water_capture_and_elimination(self):
        self.verified('CC(Br)C', 'SN1', ['CC(O)C'])
        self.verified('CC(Br)C', 'E1', ['C=CC'])

    def test_secbutyl_shared_ionization_has_capture_and_two_beta_positions(self):
        self.verified('CCC(Br)C', 'SN1', ['CCC(O)C'])
        self.verified('CCC(Br)C', 'E1', ['C=CCC', 'CC=CC'])

    def test_secondary_existing_cl_br_i_families_are_actual_graphs(self):
        for x in ['Cl', 'Br', 'I']:
            self.verified(f'CCC({x})C', 'SN1', ['CCC(O)C'])
            self.verified(f'CCC({x})C', 'E1', ['C=CCC', 'CC=CC'])

    def test_secondary_both_specified_centers_lose_local_configuration(self):
        for a in ['C[C@H](Br)CC', 'C[C@@H](Br)CC']:
            r = self.verified(a, 'SN1', ['CCC(O)C'])[0]
            center = r['site']['atomMaps'][0]
            output = next(c for c in r['information']['stereochemistry']['product']['chiralCenters'] if c['atomMap'] == center)
            self.assertFalse(output['specified']); self.assertIsNone(output['assignment'])
            self.assertIsNone(r['information']['carbocationModel']['racemizationRatio'])

    def test_secondary_cation_is_not_described_as_resonance_stabilized(self):
        _, options, _ = self.options('CCC(Br)C', 'SN1')
        info = options[0]['information']['carbocationModel']
        self.assertEqual(info['basis'], 'bounded secondary alkyl stabilization')
        self.assertEqual(info['resonanceDepiction'], 'screened alkyl cation')
        self.assertIn('narrow conditional', next(f['value'] for f in options[0]['reasoning']['factors'] if f['factor'] == 'secondary-ionization'))

    def test_both_policies_use_the_shared_secondary_predicate(self):
        with patch.object(cation, 'small_secondary', return_value=False):
            for path in ['SN1', 'E1']:
                self.assertFalse(self.options('CCC(Br)C', path)[1])
                self.assertTrue(self.options('CC(Br)(C)C', path)[1])

    def test_no_blanket_secondary_expansion(self):
        for a in ['CCCC(Br)C', 'CCC(Br)CC', 'CC[C@H](Br)CCC', 'CC(Br)C(C)C', 'BrC1CCCCC1']:
            for path in ['SN1', 'E1']:
                self.assertFalse(self.options(a, path)[1], (a, path))

    def test_primary_and_methyl_cation_controls_stay_excluded(self):
        for a in ['CBr', 'CCBr', 'CCCCCCCCBr']:
            for path in ['SN1', 'E1']: self.assertFalse(self.options(a, path)[1])

    def test_allylic_e1_permission_is_not_capture_regioselectivity(self):
        for a, p in [('C=C(C)C(Br)(C)C', 'C=C(C)C(=C)C'), ('C=C(C)C(Br)C', 'C=CC(=C)C')]:
            self.verified(a, 'E1', [p])
            _, options, result = self.options(a, 'SN1')
            self.assertFalse(options)
            self.assertRegex(' '.join(result['unsupportedReasons']), 'resonance|regioselectivity')

    def test_symmetric_allyl_capture_not_forced_to_have_ordinary_beta_loss(self):
        self.verified('C=CCBr', 'SN1', ['C=CCO'])
        self.assertFalse(self.options('C=CCBr', 'E1')[1])

    def test_benzyl_capture_without_beta_h_does_not_invent_elimination(self):
        self.verified('BrCc1ccccc1', 'SN1', ['OCc1ccccc1'])
        self.assertFalse(self.options('BrCc1ccccc1', 'E1')[1])

    def test_shared_shift_screens_preserve_conservative_rejections(self):
        for a in ['CC(C)C(Br)(C)C', 'CC(Br)(C)C1CCCCC1', 'CC(Br)(C)Cc1ccccc1']:
            for path in ['SN1', 'E1']:
                _, opts, result = self.options(a, path)
                self.assertFalse(opts)
                self.assertRegex(' '.join(result['unsupportedReasons']), 'shift|migration')

    def test_distant_tertiary_does_not_block_primary_sn2(self):
        for a, p in [('BrCCCCCCC(Cl)(C)C', 'OCCCCCCC(Cl)(C)C'),
                     ('ClCCCCCCC(Br)(C)C', 'OCCCCCCC(Br)(C)C'),
                     ('ICCCCCCC(Cl)(C)C', 'OCCCCCCC(Cl)(C)C')]:
            r = self.verified(a, 'SN2', [p])[0]
            group = next(g for g in r['compatibility']['groups'] if g['type'] == 'haloalkane' and g['disposition'] == 'preserved')
            self.assertIn('NOT SN2-eligible', group['explanation'])
            self.assertIn('elimination', group['explanation'])
            self.assertEqual(r['reasoning']['label'], 'Possible')

    def test_remote_specified_tertiary_configuration_is_retained(self):
        for tag in ['@', '@@']:
            self.verified(f'BrCCCCCC[C{tag}](Cl)(C)CC', 'SN2', [f'OCCCCCC[C{tag}](Cl)(C)CC'])

    def test_distant_nonreacting_cip_reassignment_is_not_tag_erasure(self):
        r = self.verified('BrCCCCCC[C@](Cl)(C)CC', 'SN2', ['OCCCCCC[C@](Cl)(C)CC'])[0]
        before = [c for c in r['information']['stereochemistry']['reactant']['chiralCenters'] if c['specified']]
        after = [c for c in r['information']['stereochemistry']['product']['chiralCenters'] if c['specified']]
        self.assertEqual([c['atomMap'] for c in before], [c['atomMap'] for c in after])

    def test_mixed_halide_sources_reordered_and_remapped_are_equivalent(self):
        source = Chem.MolFromSmiles('BrCCCCCCC(Cl)(C)C')
        for atom in source.GetAtoms(): atom.SetAtomMapNum(100 + atom.GetIdx())
        source = Chem.RenumberAtoms(source, list(reversed(range(source.GetNumAtoms()))))
        self.verified(Chem.MolToSmiles(source, canonical=False), 'SN2', ['OCCCCCCC(Cl)(C)C'])

    def test_nearby_tertiary_product_oh_closure_not_silently_enabled(self):
        for a in ['BrCCCC(Cl)(C)C', 'BrCCCCC(Cl)(C)C']:
            self.assertFalse(self.options(a, 'SN2')[1])
        self.verified('BrCCCCCC(Cl)(C)C', 'SN2', ['OCCCCCC(Cl)(C)C'])

    def test_nonprimary_selected_site_not_granted_new_spectator_permission(self):
        self.assertFalse(self.options('CC(Br)CCCCCCC(Cl)(C)C', 'SN2')[1])

    def test_ordinary_tertiary_sn2_remains_excluded(self):
        for a in ['CC(Br)(C)C', 'CCCCCC(Cl)(C)C']:
            self.assertFalse(self.options(a, 'SN2')[1])

    def test_remote_ring_allyl_heteroatom_competition_not_bypassed(self):
        for a in ['BrCCCCCCC1(Cl)CCCCC1', 'BrCCCCCCC(Cl)(C)C=C', 'BrCCCCCCC(Cl)(C)OC', 'NCCCCCCCC(Br)CCCCCC(Cl)(C)C']:
            self.assertFalse(self.options(a, 'SN2')[1])

    def test_other_halide_elimination_options_remain_independently_available(self):
        self.verified('BrCCCCCCC(Cl)(C)C', 'E2', ['C=C(C)CCCCCCBr', 'CC(C)=CCCCCCBr', 'C=CCCCCC(C)(C)Cl'])

    def test_full_salt_reagent_preserves_new_mapping_and_formula_unit_mass(self):
        a = 'BrCCCCCCC(Cl)(C)C'
        self.verified(a, 'SN2', ['OCCCCCCC(Cl)(C)C'], reagent='sodium-hydroxide')
        for reagent, mass in [('sodium-hydroxide', 39.997), ({'smiles': '[K+].[OH-]'}, 56.105)]:
            _, opts, _ = self.options(a, 'SN2', reagent=reagent)
            self.assertAlmostEqual(opts[0]['stoichiometry']['reactants'][1]['molarMass'], mass)

    def test_edit_validation_is_still_mandatory(self):
        with patch.object(compatibility, 'validate_edit_contract', side_effect=ValueError('Independent edit contract rejection')):
            for a, path in [('CCC(Br)C', 'SN1'), ('BrCCCCCCC(Cl)(C)C', 'SN2')]:
                _, opts, result = self.options(a, path)
                self.assertFalse(opts)
                self.assertIn('Independent edit contract rejection', ' '.join(result['unsupportedReasons']))

    def test_missing_actual_reagents_do_not_match_by_name(self):
        for a, path, wrong in [('CCC(Br)C', 'SN1', 'hydroxide'), ('BrCCCCCCC(Cl)(C)C', 'SN2', 'water')]:
            self.assertFalse(self.options(a, path, reagent=wrong)[1])

    def test_model_match_is_distinct_from_experimental_certainty(self):
        for path in PROFILES:
            a = 'CCC(Br)C' if path in {'SN1', 'E1', 'SN2'} else 'CC(Br)(C)C'
            r = self.options(a, path)[1][0]
            self.assertEqual(r['assessment']['status'], 'model-match')
            self.assertTrue(r['assessment']['reagentValidated'])
            self.assertNotIn(r['reasoning']['label'], ['Unfavorable', 'Disfavored factors'])

    def test_sn1_heating_is_reference_difference_not_chemical_disfavor(self):
        _, opts, _ = self.options('CCC(Br)C', 'SN1', {'solvent': 'aqueous-protic', 'temperature': 'heated'})
        self.assertEqual(opts[0]['assessment']['status'], 'reference-difference')
        self.assertEqual(opts[0]['reasoning']['label'], 'Reference differs')
        self.assertFalse(any(f['effect'] == 'disfavors' for f in opts[0]['reasoning']['factors'] if f['factor'] == 'temperature'))

    def test_e1_ambient_is_reference_difference_not_impossibility(self):
        _, opts, _ = self.options('CCC(Br)C', 'E1', {'solvent': 'aqueous-protic', 'temperature': 'ambient'})
        self.assertEqual({r['productSmiles'] for r in opts}, {'C=CCC', 'CC=CC'})
        self.assertEqual(opts[0]['assessment']['status'], 'reference-difference')

    def test_e2_polar_aprotic_not_automatically_unfavorable(self):
        _, opts, _ = self.options('CC(Br)(C)C', 'E2', {'solvent': 'polar-aprotic', 'temperature': 'ambient'})
        self.assertEqual(opts[0]['reasoning']['label'], 'Reference differs')

    def test_sn2_protic_solvation_is_an_evidenced_factor_not_prediction(self):
        _, opts, _ = self.options('CCBr', 'SN2', {'solvent': 'aqueous-protic'})
        self.assertEqual(opts[0]['assessment']['status'], 'disfavored')
        self.assertEqual(opts[0]['reasoning']['label'], 'Disfavored factors')
        fact = next(f for f in opts[0]['reasoning']['factors'] if f['factor'] == 'solvent')
        self.assertEqual(fact['effect'], 'disfavors'); self.assertIn('solvation', fact['explanation'])
        self.assertEqual(opts[0]['productSmiles'], 'CCO')

    def test_missing_comparison_settings_not_fictitious_activation(self):
        for path in PROFILES:
            _, opts, _ = self.options('CCC(Br)C', path, {})
            a = opts[0]['assessment']
            self.assertEqual(a['status'], 'missing'); self.assertTrue(a['missingSettings'])
            self.assertIn('none independently established', a['activationRequirement'])
            self.assertTrue(a['reagentValidated'])

    def test_added_catalyst_cannot_be_treated_as_validated_promotion(self):
        for path, (_, cond) in PROFILES.items():
            for catalyst in ['acid', 'metal', 'lindlar', 'osmium', 'radical']:
                _, opts, _ = self.options('CCC(Br)C', path, {**cond, 'catalyst': catalyst})
                self.assertEqual(opts[0]['assessment']['status'], 'unevaluated')
                self.assertEqual(opts[0]['reasoning']['label'], 'Not evaluated')

    def test_water_with_dry_medium_cannot_be_evaluated_reliably(self):
        for path in ['SN1', 'E1']:
            _, opts, _ = self.options('CCC(Br)C', path, {'solvent': 'dry', 'temperature': 'ambient'})
            self.assertEqual(opts[0]['assessment']['status'], 'unevaluated')
            self.assertEqual(opts[0]['assessment']['state'], 'alternative')

    def test_conditions_do_not_change_graph_products_or_run_eligibility(self):
        for path in PROFILES:
            ref, opts, _ = self.options('CCC(Br)C', path)
            for cond in [{}, {'solvent': 'dry', 'temperature': 'ambient'}, {**PROFILES[path][1], 'catalyst': 'acid'}]:
                _, changed, _ = self.options('CCC(Br)C', path, cond)
                self.assertEqual({r['productSmiles'] for r in opts}, {r['productSmiles'] for r in changed})
                p = service.run_curated_reaction(changed[0]['id'], ref, PROFILES[path][0], cond)
                self.assertTrue(p['balanced']); self.assertEqual(p['assessment'], changed[0]['assessment'])

    def test_unrelated_condition_assessment_not_adopted(self):
        with self.assertRaises(ValueError): assess_conditions({'mechanism': 'Hydrogenation', 'profile': {}}, {})
        r = service.match_reactions({'smiles': 'C=C'}, 'hydrogen', {'catalyst': 'metal'})['reactions'][0]
        self.assertNotIn('status', r['assessment']); self.assertEqual(r['assessment']['state'], 'aligned')

    def test_direct_oh_not_described_as_two_membered_epoxide(self):
        _, opts, result = self.options('OCBr', 'SN2')
        self.assertFalse(opts)
        reason = ' '.join(result['unsupportedReasons'])
        self.assertNotIn('2-membered', reason)
        self.assertIn('already bonded', reason); self.assertIn('O atom', reason); self.assertIn('C atom', reason)

    def test_exact_three_to_six_membered_closure_counts(self):
        for a, size in [('OCCBr', 3), ('OCCCBr', 4), ('OCCCCBr', 5), ('OCCCCCBr', 6)]:
            for path in ['SN2', 'E2']:
                _, opts, result = self.options(a, path)
                self.assertFalse(opts)
                self.assertIn(f'{size}-membered', ' '.join(result['unsupportedReasons']))

    def test_closure_wording_distinguishes_epoxide_and_larger_ether(self):
        self.assertIn('epoxide', ' '.join(self.options('OCCBr', 'SN2')[2]['unsupportedReasons']))
        larger = ' '.join(self.options('OCCCBr', 'SN2')[2]['unsupportedReasons'])
        self.assertIn('cyclic ether', larger); self.assertNotIn('epoxide', larger)

    def test_remote_oh_remains_bounded_not_a_cyclization_prediction(self):
        self.verified('OCCCCCCBr', 'SN2', ['OCCCCCCO'])
        self.verified('OCCCCCCBr', 'E2', ['C=CCCCCO'])


if __name__ == '__main__': unittest.main()
