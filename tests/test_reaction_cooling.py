"""Qualitative cooling input and the narrowly reviewed Br2 cooling exception."""
import copy
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from server import chemistry_server as service
from server.production_app import create_app
from server.reaction_conditions import COOLING_NOTE, cooling_confidence
from server.reaction_condition_guidance import LABELS
from server.reaction_information import DEFINITIONS


SECONDARY = {'secondaryOxidationProfile': 'naocl-acetic-ketone-v1',
             'solvent': 'aqueous-protic', 'temperature': 'ambient',
             'catalyst': 'none', 'oxidationStage': 'first'}


def matched(source, reagent, pathway, conditions):
    first = {'smiles': source}
    result = service.match_reactions(first, reagent, conditions)
    options = [r for r in result['reactionOptions'] if r['mechanism'] == pathway]
    if not options:
        raise AssertionError(f'No {pathway} option for {source}: {result["unsupportedReasons"]}')
    return first, result, options


class CoolingInputTests(unittest.TestCase):
    def test_distinct_temperature_is_accepted_without_normalization(self):
        source = {'temperature': 'cooled', 'catalyst': 'none'}
        before = copy.deepcopy(source)
        result = service._conditions(source)
        self.assertEqual(result['temperature'], 'cooled')
        self.assertEqual(source, before)
        self.assertEqual(service.CONDITION_VALUES['temperature'], {'', 'cooled', 'ambient', 'heated'})
        for value in ['cold', 'ambient cooled', 5, None]:
            with self.subTest(value=value), self.assertRaises(service.ChemistryError):
                service._conditions({'temperature': value})

    def test_other_condition_values_are_not_expanded_to_generic_base(self):
        with self.assertRaises(service.ChemistryError):
            service._conditions({'temperature': 'cooled', 'catalyst': 'base'})
        self.assertEqual(LABELS['temperature'][1]['cooled'], 'Cooled / Low Temperature')
        self.assertNotIn('base', LABELS['catalyst'][1])
        self.assertEqual(LABELS['catalyst'][0], 'Additional Catalyst / Activation')

    def test_overlay_is_non_mutating_and_idempotent(self):
        assessment = {'state': 'aligned', 'status': 'model-match', 'canRun': True,
                      'label': 'Model conditions match', 'note': 'Existing bounded model.',
                      'factors': {'catalyst': {'status': 'model-match', 'effect': 'neutral'}}}
        before = copy.deepcopy(assessment)
        result = cooling_confidence(assessment, {'temperature': 'cooled'})
        self.assertEqual(assessment, before)
        self.assertFalse(result['canRun']); self.assertTrue(result['coolingUnvalidated'])
        self.assertEqual(result['factors']['temperature']['effect'], 'unknown')
        self.assertIn('qualitative input, not an exact temperature', result['note'])
        self.assertIn('does not mean the reaction is impossible', result['note'])
        self.assertIs(cooling_confidence(result, {'temperature': 'cooled'}), result)

    def test_existing_temperature_assessments_are_not_modified(self):
        assessment = {'status': 'model-match', 'canRun': True, 'note': 'unchanged'}
        for temperature in ['', 'ambient', 'heated']:
            self.assertIs(cooling_confidence(assessment, {'temperature': temperature}), assessment)
        for reaction in service._all_reactions().values():
            for temperature in ['', 'ambient', 'heated']:
                conditions = service._conditions({**reaction['profile'], 'temperature': temperature})
                with self.subTest(pathway=reaction['mechanism'], temperature=temperature):
                    self.assertEqual(service._assessment(reaction, conditions), service._base_assessment(reaction, conditions))

    def test_stronger_missing_activation_and_unsupported_reasons_survive(self):
        for status in ['missing', 'activation-required', 'unsupported-pathway']:
            source = {'status': status, 'label': 'Original stronger reason', 'canRun': False,
                      'note': 'Original requirement.', 'missingSettings': ['catalyst']}
            result = cooling_confidence(source, {'temperature': 'cooled'})
            self.assertEqual(result['status'], status)
            self.assertEqual(result['label'], source['label'])
            self.assertEqual(result['missingSettings'], ['catalyst'])
            self.assertIn('Original requirement.', result['note'])

    def test_old_heated_rejection_text_is_not_repeated_for_cooling(self):
        a, _, options = matched('CCCCC=O', 'sodium-hypochlorite', 'Aldehyde oxidation',
                                {'solvent': 'aqueous-protic', 'oxidationStage': 'further', 'temperature': 'cooled'})
        for option in options:
            assessment = option['assessment']
            self.assertNotIn('Heated aldehyde oxidation', assessment['note'])
            self.assertEqual(next(i['explanation'] for i in assessment['conditionIssues'] if i['field'] == 'temperature'), COOLING_NOTE)

    def test_reference_match_note_is_scoped_to_other_settings_not_cooling(self):
        _, _, options = matched('CBr', 'hydroxide', 'SN2', {'solvent': 'polar-aprotic', 'temperature': 'cooled'})
        note = options[0]['assessment']['note']
        self.assertTrue(note.startswith(COOLING_NOTE))
        scoped_claim = ('Other model settings (excluding the unvalidated cooled temperature): '
                        'Selected conditions match the supported reference model')
        self.assertIn(scoped_claim, note)
        self.assertNotIn(COOLING_NOTE + ' Selected conditions match', note)
        self.assertFalse(options[0]['assessment']['canRun'])


CASES = [
    ('CBr', 'hydroxide', 'SN2', {'solvent': 'polar-aprotic'}),
    ('CC(C)(C)Br', 'water', 'SN1', {'solvent': 'aqueous-protic'}),
    ('CC(C)(C)Br', 'water', 'E1', {'solvent': 'aqueous-protic'}),
    ('CCBr', 'hydroxide', 'E2', {'solvent': 'ethanolic-protic'}),
    ('C=C', 'hydrogen', 'Hydrogenation', {'catalyst': 'metal'}),
    ('CCC=O', 'hydrogen', 'Carbonyl hydrogenation', {'catalyst': 'metal'}),
    ('CC(=O)OCC', 'water', 'Ester hydrolysis', {'solvent': 'aqueous-protic', 'catalyst': 'acid'}),
    ('CC(=O)OCC', 'hydroxide', 'Ester saponification', {'solvent': 'aqueous-protic'}),
    ('C=C', 'water', 'Hydration', {'solvent': 'aqueous-protic', 'catalyst': 'acid'}),
    ('C=C', {'smiles': 'Cl'}, 'Hydrohalogenation', {'solvent': 'dry'}),
    ('C=C', {'smiles': 'BrBr'}, 'Bromination', {'solvent': 'dry', 'catalyst': 'none'}),
    ('C=C', {'smiles': 'ClCl'}, 'Chlorination', {'solvent': 'dry', 'catalyst': 'none'}),
    ('C=C', {'smiles': 'CC(=O)OO'}, 'Epoxidation', {'solvent': 'dry', 'catalyst': 'none'}),
    ('C=C', 'hydrogen-peroxide', 'Alkene dihydroxylation', {'catalyst': 'osmium', 'workup': 'aqueous-release'}),
    ('CC#CC', 'hydrogen', 'Alkyne partial hydrogenation', {'catalyst': 'lindlar'}),
    ('CC#CC', 'hydrogen', 'Alkyne hydrogenation', {'catalyst': 'metal'}),
    ('CC#CC', {'smiles': 'BrBr'}, 'Alkyne halogenation', {'solvent': 'dry', 'additionStage': 'one', 'catalyst': 'none'}),
    ('C#CC', {'smiles': 'Br'}, 'Alkyne hydrohalogenation', {'solvent': 'dry', 'additionStage': 'one', 'catalyst': 'none'}),
    ('CCO', {'smiles': 'OS(=O)(=O)O'}, 'Alcohol dehydration', {'solvent': 'dry', 'catalyst': 'acid'}),
    ('CCO', {'smiles': 'Br'}, 'Alcohol substitution', {'solvent': 'dry'}),
    ('CC(O)C', 'sodium-hypochlorite', 'Alcohol oxidation', SECONDARY),
    ('CC(=O)O', {'smiles': 'CCO'}, 'Esterification', {'catalyst': 'acid'}),
    ('C=C', {'smiles': 'O=C(OOC(=O)c1ccccc1)c1ccccc1'}, 'Polymerization model', {'catalyst': 'radical', 'polymerUnits': '2'}),
    ('CCC=O', 'sodium-hypochlorite', 'Aldehyde oxidation', {'solvent': 'aqueous-protic', 'oxidationStage': 'further'}),
    ('CCO', 'sodium-hypochlorite', 'Alcohol oxidation', {'solvent': 'aqueous-protic', 'oxidationStage': 'first'}),
]


class CoolingPublicContractTests(unittest.TestCase):
    def test_all_24_existing_pathway_definitions_have_public_cases(self):
        self.assertEqual({case[2] for case in CASES}, set(DEFINITIONS))

    def check_pathway(self, source, reagent, pathway, settings):
        ordinary = {**settings, 'temperature': 'ambient'}
        cooled = {**settings, 'temperature': 'cooled'}
        first, result, found = matched(source, reagent, pathway, cooled)
        _, _, before = matched(source, reagent, pathway, ordinary)
        self.assertEqual(result['supportState'], 'Conditional')
        self.assertEqual({r['id']: r['productSmiles'] for r in found}, {r['id']: r['productSmiles'] for r in before})
        for option in found:
            assessment = option['assessment']; evidence = assessment['evidence']
            reviewed_bromination = pathway == 'Bromination'
            # This old fixture uses peracetic acid, not the newly reviewed
            # actual-mCPBA cooling profile. Reagent identity is its blocker.
            unreviewed_peracid = pathway == 'Epoxidation'
            self.assertEqual(assessment['coolingUnvalidated'], not reviewed_bromination)
            self.assertEqual(assessment['canRun'], reviewed_bromination)
            self.assertTrue(evidence['canPreview2D'])
            self.assertEqual(evidence['canGenerate3D'], reviewed_bromination)
            self.assertEqual('temperature' in evidence['unknownConditions'], not (reviewed_bromination or unreviewed_peracid))
            self.assertNotIn('Unfavorable', option['reasoning']['label'])
            temp = next(f for f in option['reasoning']['factors'] if f['factor'] == 'temperature')
            self.assertEqual(temp['value'], 'Cooled / Low Temperature')
            self.assertEqual(temp['effect'], 'neutral' if reviewed_bromination or unreviewed_peracid else 'unknown')
            context = option['stoichiometry']['context']
            self.assertEqual(context['canGenerate3D'], reviewed_bromination)
            self.assertEqual(context['conditions']['temperature'], 'cooled')
            self.assertTrue(option['stoichiometry']['balanced'])
            diagram = service.reaction_diagram(option['id'], first, reagent, cooled)
            self.assertTrue(diagram['svg']); self.assertEqual(diagram['assessment'], assessment)
            self.assertEqual(diagram['products'][0]['smiles'], option['productSmiles'])
            if reviewed_bromination:
                self.assertEqual(assessment['cooling']['status'], 'supported-model')
                self.assertEqual(assessment['cooling']['modelId'], 'cooled-alkene-bromination-v1')
                self.assertIn('theoretical product conformer', diagram['note'])
                self.assertTrue(any('theoretical product conformer' in a for a in context['assumptions']))
                product = service.run_curated_reaction(option['id'], first, reagent, cooled)
                self.assertEqual(product['product']['representation'], '3d')
            else:
                if unreviewed_peracid:
                    self.assertEqual(assessment['cooling']['status'], 'conditions-unresolved')
                    self.assertIn('reagentIdentity', [issue['field'] for issue in evidence['conditionIssues']])
                    self.assertIn('requires actual neutral meta-chloroperbenzoic acid', diagram['note'])
                else:
                    self.assertTrue(any('qualitative input' in a for a in context['assumptions']))
                    self.assertIn('no cooled 3D product is asserted', diagram['note'])
                with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Must gate before 3D')):
                    with self.assertRaisesRegex(service.ChemistryError, 'meta-chloroperbenzoic acid' if unreviewed_peracid else 'low-temperature'):
                        service.run_curated_reaction(option['id'], first, reagent, cooled)

    def test_lindlar_guide_cannot_erase_cooling_or_make_it_ambient(self):
        first, _, options = matched('CC#CC', 'hydrogen', 'Alkyne partial hydrogenation', {'temperature': 'cooled'})
        guide = options[0]['guidedConditions']
        self.assertFalse(guide['canApply']); self.assertEqual(guide['state'], 'unsupported-conditions')
        self.assertNotIn('targetConditions', guide)
        temp = next(r for r in guide['requirements'] if r['field'] == 'temperature')
        self.assertEqual(temp['selectedValue'], 'cooled'); self.assertEqual(temp['state'], 'preserved')
        self.assertEqual(temp['selectedLabel'], 'Cooled / Low Temperature')

    def test_secondary_guide_explicitly_reviews_existing_ambient_profile(self):
        first, _, options = matched('CC(O)C', 'sodium-hypochlorite', 'Alcohol oxidation', {**SECONDARY, 'temperature': 'cooled'})
        guide = options[0]['guidedConditions']
        self.assertTrue(guide['canApply']); self.assertEqual(guide['state'], 'conflicting-conditions')
        self.assertEqual(guide['targetConditions'], SECONDARY)
        temp = next(r for r in guide['requirements'] if r['field'] == 'temperature')
        self.assertEqual(temp['selectedValue'], 'cooled'); self.assertEqual(temp['requiredValue'], 'ambient')
        self.assertEqual(temp['state'], 'conflicting')

    def test_primary_endpoint_is_not_qualified_by_cooling_or_by_removing_it(self):
        for conditions in [{'temperature': 'cooled'}, {'temperature': 'cooled', 'solvent': 'aqueous-protic', 'oxidationStage': 'first'}]:
            first, _, options = matched('CCO', 'sodium-hypochlorite', 'Alcohol oxidation', conditions)
            for option in options:
                assessment = option['assessment']
                self.assertFalse(assessment['canRun'])
                self.assertFalse(assessment['conditionCompleteEligibility'])
                self.assertEqual(assessment['label'], 'Aldehyde endpoint not established')
                self.assertIn('Hypothetical aldehyde stage', assessment['confidenceLabel'])
                self.assertIn('cooled conditions unvalidated', assessment['confidenceLabel'])
                self.assertIn('No aldehyde-selective hypochlorite condition profile is implemented', assessment['note'])
                self.assertIn('aldehyde selectivity', assessment['factors'])
                guide = option['guidedConditions']
                self.assertEqual(guide['state'], 'no-validated-profile')
                self.assertFalse(guide['canApply']); self.assertNotIn('targetConditions', guide)
                if 'solvent' not in conditions:
                    self.assertEqual(assessment['status'], 'missing')
                    self.assertEqual(assessment['missingSettings'], ['solvent', 'oxidationStage'])
                    self.assertEqual(assessment['label'], 'Aldehyde endpoint not established')
                    self.assertIn('Missing existing model settings', assessment['note'])
                for temperature in ['', 'ambient']:
                    _, _, ordinary = matched('CCO', 'sodium-hypochlorite', 'Alcohol oxidation', {**conditions, 'temperature': temperature})
                    self.assertTrue(all(not r['assessment']['canRun'] for r in ordinary))

    def test_mapping_and_changed_bonds_are_not_changed_by_cooling(self):
        for source, reagent, pathway, settings in CASES[:2] + CASES[10:12]:
            first, _, options = matched(source, reagent, pathway, {**settings, 'temperature': 'cooled'})
            for option in options:
                cooled = service.reaction_diagram(option['id'], first, reagent, {**settings, 'temperature': 'cooled'})
                ambient = service.reaction_diagram(option['id'], first, reagent, {**settings, 'temperature': 'ambient'})
                for key in ['atoms', 'bondsBroken', 'bondsFormed', 'products', 'reactants']:
                    self.assertEqual(cooled[key], ambient[key])


for index, case in enumerate(CASES):
    setattr(CoolingPublicContractTests, f'test_cooling_contract_{index:02d}',
            lambda self, values=case: self.check_pathway(*values))


class CoolingAuthenticatedApiTests(unittest.TestCase):
    def test_http_match_diagram_and_run_have_consistent_cooling_gate(self):
        with tempfile.TemporaryDirectory(prefix='reaction-cooling-api-') as folder:
            origin = 'https://cooling.example.test'
            app = create_app({'TRIAL_PASSWORD': 'Synthetic-cooling-password', 'SESSION_SECRET': secrets.token_hex(32),
                              'PUBLIC_ORIGIN': origin, 'FRAME_ANCESTORS': origin, 'DIST_DIR': Path(folder), 'TESTING': True}, chemistry_backend=service)
            client = app.test_client()
            post = lambda url, **kw: client.post(url, base_url=origin, headers={'Origin': origin}, **kw)
            self.assertEqual(post('/login', data={'password': 'Synthetic-cooling-password'}).status_code, 303)
            body = {'reactantA': {'smiles': 'CBr'}, 'reactantB': 'hydroxide',
                    'conditions': {'temperature': 'cooled', 'solvent': 'polar-aprotic'}}
            response = post('/api/reactions/match', json=body)
            self.assertEqual(response.status_code, 200)
            option = response.get_json()['reactionOptions'][0]
            self.assertTrue(option['assessment']['coolingUnvalidated'])
            body['reactionId'] = option['id']
            diagram = post('/api/reactions/diagram', json=body)
            self.assertEqual(diagram.status_code, 200)
            self.assertEqual(diagram.get_json()['assessment'], option['assessment'])
            result = post('/api/reactions/run', json=body)
            self.assertEqual(result.status_code, 422)
            self.assertIn('qualitative input', result.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
