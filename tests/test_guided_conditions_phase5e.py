"""The pilot describes existing permissions; it must not create new chemistry."""
import copy
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from server import chemistry_server as service
from server import secondary_alcohol_oxidation_rule as secondary
from server.production_app import create_app
from server.reaction_condition_guidance import guidance

PROFILE = {'secondaryOxidationProfile': 'naocl-acetic-ketone-v1', 'solvent': 'aqueous-protic',
           'temperature': 'ambient', 'catalyst': 'none', 'oxidationStage': 'first'}


def match(source='CC(O)C', conditions=None, reagent='sodium-hypochlorite', reverse=False):
    a, b = {'smiles': source}, reagent
    if reverse:
        a, b = b, a
    data = service.match_reactions(a, b, {} if conditions is None else conditions)
    return a, b, data, [r for r in data['reactionOptions'] if r['mechanism'] == 'Alcohol oxidation']


class GuidedConditionTests(unittest.TestCase):
    def test_missing_settings_are_not_implicitly_applied(self):
        _, _, _, found = match()
        r = found[0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'missing-conditions'); self.assertTrue(g['canApply'])
        self.assertEqual(g['targetConditions'], PROFILE)
        self.assertTrue(all(row['state'] == 'missing' for row in g['requirements']))
        self.assertFalse(r['assessment']['canRun']); self.assertFalse(r['stoichiometry']['context']['canGenerate3D'])

    def test_generic_water_is_an_explicit_medium_replacement(self):
        g = match(conditions={'solvent': 'aqueous-protic'})[3][0]['guidedConditions']
        row = next(x for x in g['requirements'] if x['field'] == 'solvent')
        self.assertEqual(row['state'], 'conflicting'); self.assertIn('generic', row['selectedLabel'])
        self.assertEqual(row['requiredLabel'], 'Aqueous acetic acid · secondary NaOCl')

    def test_all_supported_settings_have_no_apply_action(self):
        r = match(conditions=PROFILE)[3][0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'qualified'); self.assertFalse(g['canApply'])
        self.assertNotIn('targetConditions', g); self.assertTrue(all(x['state'] == 'matches' for x in g['requirements']))
        self.assertTrue(r['assessment']['canRun']); self.assertIn('not predicted', g['message'])

    def test_correctable_conflicts_are_fully_listed(self):
        c = {'solvent': 'dry', 'temperature': 'heated', 'catalyst': 'acid', 'oxidationStage': 'further', 'workup': 'aqueous-release'}
        r = match(conditions=c)[3][0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'conflicting-conditions'); self.assertTrue(g['canApply'])
        self.assertTrue(all(x['state'] == 'conflicting' for x in g['requirements']))
        self.assertEqual(g['targetConditions'], {**PROFILE, 'workup': ''}); self.assertFalse(r['assessment']['canRun'])

    def test_unknown_condition_cannot_be_silently_cleared(self):
        g = match(conditions={**PROFILE, 'pressure': 'unsupported'})[3][0]['guidedConditions']
        self.assertEqual(g['state'], 'unsupported-conditions'); self.assertFalse(g['canApply']); self.assertNotIn('targetConditions', g)

    def test_shared_required_values_have_not_changed(self):
        self.assertEqual(secondary.PROFILE_SETTINGS, PROFILE)
        self.assertEqual(secondary.PROFILE, 'naocl-acetic-ketone-v1')

    def test_primary_aldehyde_has_no_secondary_preset(self):
        a, b, _, found = match('CCO', PROFILE); r = found[0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'no-validated-profile'); self.assertFalse(g['canApply']); self.assertFalse(g['requirements'])
        self.assertNotIn('profileId', g); self.assertNotIn('targetConditions', g)
        self.assertIn('PCC and Dess–Martin are not implemented', g['message'])
        self.assertTrue(service.reaction_diagram(r['id'], a, b, PROFILE)['svg'])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, PROFILE)

    def test_mixed_primary_secondary_options_have_independent_scope(self):
        _, _, _, found = match('OCCCCCCCC(O)C', PROFILE)
        self.assertEqual({r['guidedConditions']['state'] for r in found}, {'no-validated-profile', 'outside-profile-scope'})
        self.assertTrue(all(not r['guidedConditions']['canApply'] and not r['assessment']['canRun'] for r in found))

    def test_read_only_guidance_does_not_mutate_assessment_or_inputs(self):
        _, _, _, found = match(); r = found[0]
        candidate = {'secondaryOxidationModel': r['secondaryOxidationModel'], 'site': r['site']}
        assessment = copy.deepcopy(r['assessment']); c = service._conditions({'solvent': 'dry'})
        before = copy.deepcopy((candidate, assessment, c, vars(c)))
        guidance(r['id'], candidate, assessment, c)
        self.assertEqual((candidate, assessment, c, vars(c)), before)

    def test_unrelated_pathways_do_not_receive_pilot_metadata(self):
        for a, b in [('ethene', 'hydrogen'), ('bromoethane', 'hydroxide'), ('ethyl-ethanoate', 'water')]:
            data = service.match_reactions(a, b, {})
            self.assertTrue(data['reactionOptions']); self.assertTrue(all('guidedConditions' not in r for r in data['reactionOptions']))
        self.assertTrue(all('guidedConditions' not in r for r in service.reaction_catalog()['reactions']))

    def test_stale_reaction_id_is_not_a_profile_authorization(self):
        a, b, _, found = match(); old = found[0]
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(old['id'], {'smiles': 'CCCC(O)CCC'}, b, PROFILE)
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(old['id'], a, b, {'solvent': 'aqueous-protic'})

    def test_forged_guidance_cannot_authorize_generation(self):
        for source, reagent in [('CCO', 'sodium-hypochlorite'), ('COCCCC(O)C', 'sodium-hypochlorite'), ('CC(O)C', {'smiles': '[K+].[O-]Cl'})]:
            with patch.object(service, 'guided_condition_metadata', return_value={'version': 1, 'state': 'qualified', 'canApply': True}):
                a, b, _, found = match(source, PROFILE, reagent)
                self.assertTrue(found[0]['guidedConditions']['canApply'])
                with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Gate must run before 3D')):
                    with self.assertRaises(service.ChemistryError): service.run_curated_reaction(found[0]['id'], a, b, PROFILE)

    def test_condition_guidance_does_not_change_net_outputs(self):
        for source in ['CC(O)C', 'CCCC(O)CCC', 'OC1CCCCCC1']:
            a, b, _, found = match(source); r = found[0]; c = r['guidedConditions']['targetConditions']
            qualified = match(source, c)[3][0]
            self.assertEqual(r['id'], qualified['id']); self.assertEqual(r['productSmiles'], qualified['productSmiles'])
            self.assertEqual(r['stoichiometry']['reactants'], qualified['stoichiometry']['reactants'])
            d = service.reaction_diagram(r['id'], a, b, c); p = service.run_curated_reaction(r['id'], a, b, c)['product']
            self.assertIsNone(d['mechanism']); self.assertTrue(qualified['stoichiometry']['balanced'])
            self.assertEqual([(x['atomIndex'], x['mapId'], x['element']) for x in d['atoms'] if x['side'] == 'products' and x['speciesIndex'] == 0],
                             [(x['index'], x['mapId'], x['element']) for x in p['atomLinks']])


def qualified_case(self, source):
    for reverse in [False, True]:
        a, b, _, found = match(source, reverse=reverse)
        r = found[0]; target = r['guidedConditions']['targetConditions']
        self.assertEqual(target, PROFILE)
        result = service.match_reactions(a, b, target)['reactionOptions'][0]
        self.assertEqual(result['guidedConditions']['state'], 'qualified'); self.assertTrue(result['assessment']['canRun'])
        self.assertTrue(result['stoichiometry']['context']['canGenerate3D'])
        self.assertIn('Theoretical', result['stoichiometry']['context']['warning'])
        # No client action can make water-only settings retain qualification.
        after = service.match_reactions(a, b, {'solvent': 'aqueous-protic'})['reactionOptions'][0]
        self.assertFalse(after['assessment']['canRun']); self.assertTrue(after['guidedConditions']['canApply'])


for i, source in enumerate(['CC(O)C', 'CCCC(O)CCC', 'OC1CCCCCC1', 'CC[C@H](C)CCCC[C@@H](O)C']):
    setattr(GuidedConditionTests, f'test_qualified_model_{i}', lambda self, s=source: qualified_case(self, s))


def conditional_case(self, source, reagent):
    a, b, _, found = match(source, PROFILE, reagent)
    for r in found:
        g = r['guidedConditions']; self.assertEqual(g['state'], 'outside-profile-scope')
        self.assertFalse(g['canApply']); self.assertNotIn('targetConditions', g); self.assertTrue(g['limitations'])
        self.assertFalse(r['assessment']['canRun']); self.assertTrue(service.reaction_diagram(r['id'], a, b, PROFILE)['svg'])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, PROFILE)


for i, (source, reagent) in enumerate([('CC(O)c1ccccc1', 'sodium-hypochlorite'), ('COCCCC(O)C', 'sodium-hypochlorite'),
                                     ('CC(O)CCCCCC(O)C', 'sodium-hypochlorite'), ('CC(O)C', {'smiles': '[K+].[O-]Cl'})]):
    setattr(GuidedConditionTests, f'test_outside_profile_{i}', lambda self, s=source, r=reagent: conditional_case(self, s, r))


class GuidedConditionPublicTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='phase5e-api-'); self.addCleanup(folder.cleanup)
        self.origin = 'https://guided.example.test'
        self.client = create_app({'TRIAL_PASSWORD': 'Synthetic-guided-password', 'SESSION_SECRET': secrets.token_hex(32), 'PUBLIC_ORIGIN': self.origin,
                                  'FRAME_ANCESTORS': self.origin, 'DIST_DIR': Path(folder.name), 'TESTING': True}, chemistry_backend=service).test_client()
        self.assertEqual(self.post('/login', data={'password': 'Synthetic-guided-password'}).status_code, 303)

    def post(self, path, **kwargs):
        return self.client.post(path, base_url=self.origin, headers={'Origin': self.origin}, **kwargs)

    def body(self, source='CC(O)C', c=None, reagent='sodium-hypochlorite'):
        body = {'reactantA': {'smiles': source}, 'reactantB': reagent, 'conditions': {} if c is None else copy.deepcopy(c)}
        response = self.post('/api/reactions/match', json=body); self.assertEqual(response.status_code, 200)
        reaction = next(r for r in response.get_json()['reactionOptions'] if r['mechanism'] == 'Alcohol oxidation')
        body['reactionId'] = reaction['id']; return body, reaction

    def test_public_review_apply_and_withdraw(self):
        body, r = self.body(); self.assertTrue(r['guidedConditions']['canApply'])
        self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body['conditions'] = r['guidedConditions']['targetConditions']
        updated = self.post('/api/reactions/match', json=body).get_json()['reactionOptions'][0]
        self.assertEqual(updated['guidedConditions']['state'], 'qualified')
        self.assertEqual(updated['reasoning']['label'], updated['assessment']['confidenceLabel'])
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 200)
        body['conditions'] = {'solvent': 'aqueous-protic'}
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)

    def test_saved_profile_is_revalidated_for_changed_structure_and_reagent(self):
        saved = json.loads(json.dumps(PROFILE))
        for source, reagent in [('CCO', 'sodium-hypochlorite'), ('COCCCC(O)C', 'sodium-hypochlorite'), ('CC(O)C', {'smiles': '[K+].[O-]Cl'})]:
            body, r = self.body(source, saved, reagent)
            self.assertFalse(r['assessment']['canRun']); self.assertFalse(r['guidedConditions']['canApply'])
            self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
            self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)

    def test_client_permission_and_metadata_are_not_trusted(self):
        body, r = self.body(); body.update(canRun=True, guidedConditions={'canApply': True, 'state': 'qualified'})
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body['conditions'] = {**PROFILE, 'guidedConditions': {'approved': True}}
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)

    def test_forged_profile_is_explicit_not_a_default(self):
        body, r = self.body(c={**PROFILE, 'secondaryOxidationProfile': 'PCC'})
        self.assertEqual(r['guidedConditions']['state'], 'conflicting-conditions')
        self.assertIn('Unsupported', r['guidedConditions']['requirements'][0]['selectedLabel'])
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)

    def test_stale_site_id_authentication_and_invalid_values_remain_blocked(self):
        body, _ = self.body(c=PROFILE); body['reactantA'] = {'smiles': 'CCCC(O)CCC'}
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body['conditions']['temperature'] = 'made-up'
        self.assertEqual(self.post('/api/reactions/match', json=body).status_code, 422)
        # Use a fresh unauthenticated client rather than depending on cookie names.
        other = self.client.application.test_client()
        self.assertEqual(other.post('/api/reactions/match', base_url=self.origin, headers={'Origin': self.origin}, json=body).status_code, 401)
