"""Read-only Lindlar guidance on the existing independently checked net model."""
import copy
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

from rdkit import Chem
from server import chemistry_server as service
from server.production_app import create_app

PATHWAY = 'Alkyne partial hydrogenation'
FIXTURE = json.loads(Path('tests/fixtures/alkyne-partial-hydrogenation.json').read_text())
SECONDARY = json.loads(Path('tests/fixtures/secondary-alcohol-oxidation-phase5d.json').read_text())['profile']


def matched(source='CC#CC', conditions=None, reagent='hydrogen', reverse=False):
    a, b = {'smiles': source}, reagent
    if reverse: a, b = b, a
    c = {} if conditions is None else conditions
    payload = service.match_reactions(a, b, c)
    return a, b, c, payload, [r for r in payload['reactionOptions'] if r['mechanism'] == PATHWAY]


def without_guidance(value):
    if isinstance(value, dict): return {k: without_guidance(v) for k, v in value.items() if k != 'guidedConditions'}
    if isinstance(value, list): return [without_guidance(v) for v in value]
    return value


class LindlarGuidanceTests(unittest.TestCase):
    def test_missing_activation_only_is_suggested(self):
        a, b, c, _, found = matched(); r = found[0]; g = r['guidedConditions']
        self.assertEqual(g['profileId'], PATHWAY); self.assertEqual(g['state'], 'missing-conditions')
        self.assertTrue(g['canApply']); self.assertTrue(g['requireConfirmation'])
        self.assertEqual(g['targetConditions'], {'catalyst': 'lindlar'})
        self.assertFalse(r['assessment']['canRun']); self.assertTrue(service.reaction_diagram(r['id'], a, b, c)['svg'])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, c)

    def test_valid_explicit_settings_are_preserved_not_replaced_by_defaults(self):
        c = {'solvent': 'dry', 'temperature': 'ambient', 'additionStage': 'two', 'polymerUnits': '6'}
        g = matched(conditions=c)[4][0]['guidedConditions']; self.assertEqual(g['targetConditions'], {'catalyst': 'lindlar'})
        for row in g['requirements']:
            if row['field'] in {'solvent', 'temperature'}:
                self.assertEqual(row['state'], 'preserved'); self.assertEqual(row['selectedValue'], c[row['field']])
                self.assertEqual(row['selectedValue'], row['requiredValue']); self.assertIn('no protocol validation', row['requiredLabel'])
        self.assertTrue(matched(conditions={**c, **g['targetConditions']})[4][0]['assessment']['canRun'])

    def test_unrelated_stage_release_can_only_be_explicitly_cleared(self):
        c = {'catalyst': 'lindlar', 'oxidationStage': 'first', 'workup': 'aqueous-release'}
        r = matched(conditions=c)[4][0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'conflicting-conditions'); self.assertFalse(r['assessment']['canRun'])
        self.assertEqual(g['targetConditions'], {'catalyst': 'lindlar', 'oxidationStage': '', 'workup': ''})
        self.assertTrue(all(row['state'] == 'conflicting' for row in g['requirements'] if row['field'] in {'oxidationStage', 'workup'}))
        self.assertTrue(matched(conditions={**c, **g['targetConditions']})[4][0]['assessment']['canRun'])

    def test_qualified_is_a_net_model_not_a_certified_protocol(self):
        r = matched(conditions={'catalyst': 'lindlar'})[4][0]; g = r['guidedConditions']
        self.assertEqual(g['state'], 'qualified'); self.assertFalse(g['canApply']); self.assertNotIn('targetConditions', g)
        self.assertIn('solvent, pressure and stopping conditions are not validated', g['message'])
        self.assertEqual(r['assessment']['evidence']['chemistryCorrectness']['status'], 'not-independently-certified-at-runtime')
        self.assertIn('solvent/pressure/stopping not validated', r['assessment']['evidence']['label'])

    def test_metadata_never_mutates_matching_or_conditions(self):
        contexts = [{}, {'catalyst': 'metal'}, {'catalyst': 'lindlar'}, {'catalyst': 'lindlar', 'solvent': 'dry'}, {'catalyst': 'lindlar', 'peroxide': True}]
        for source in ['CC#CC', 'C#CCCCO', 'C#CCCCCC#C', 'C1#CCCCCCC1', 'CCO']:
            for c in contexts:
                before = copy.deepcopy(c); actual = matched(source, c)[3]
                with patch.object(service, 'guided_condition_metadata', return_value=None): baseline = matched(source, c)[3]
                self.assertEqual(without_guidance(actual), without_guidance(baseline)); self.assertEqual(c, before)

    def test_all_existing_positive_structures_keep_their_original_products_and_scope(self):
        canonical = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s))
        for case in FIXTURE['positive']:
            a, b, c, _, found = matched(case['substrate'], {'catalyst': 'lindlar'})
            self.assertEqual({r['productSmiles'] for r in found}, {canonical(p) for p in case['products']})
            for r in found:
                multi = r['alkynePartialStereo']['singleSiteBookkeepingOnly']; g = r['guidedConditions']
                self.assertEqual(g['state'], 'outside-profile-scope' if multi else 'qualified')
                self.assertEqual(r['assessment']['canRun'], not multi); self.assertFalse(g['canApply'])
                self.assertTrue(service.reaction_diagram(r['id'], a, b, c)['svg'])

    def test_all_existing_negative_structures_still_have_no_partial_guidance(self):
        for case in FIXTURE['negative']:
            if case['label'] == 'isotope':
                with self.assertRaises(service.ChemistryError): matched(case['substrate'], {'catalyst': 'lindlar'})
            else:
                self.assertFalse(matched(case['substrate'], {'catalyst': 'lindlar'})[4], case['label'])

    def test_other_pathways_and_secondary_pilot_are_not_repurposed(self):
        data = matched(conditions={'catalyst': 'metal'})[3]
        complete = next(r for r in data['reactionOptions'] if r['mechanism'] == 'Alkyne hydrogenation')
        self.assertNotIn('guidedConditions', complete); self.assertTrue(complete['assessment']['canRun'])
        for source, expected in [('CC(O)C', 'qualified'), ('CCO', 'no-validated-profile'), ('COCCCC(O)C', 'outside-profile-scope')]:
            r = next(r for r in service.match_reactions({'smiles': source}, 'sodium-hypochlorite', SECONDARY)['reactionOptions'] if r['mechanism'] == 'Alcohol oxidation')
            self.assertEqual(r['guidedConditions']['state'], expected)
            self.assertEqual(r['assessment']['canRun'], expected == 'qualified')
        self.assertTrue(all('guidedConditions' not in r for r in service.reaction_catalog()['reactions']))

    def test_forged_profile_and_actual_reagent_identity_still_fail(self):
        for reagent in ['water', 'hydrogen-peroxide', {'smiles': '[H][H]', 'name': 'Lindlar catalyst'}]:
            found = matched(reagent=reagent)[4]
            if reagent == {'smiles': '[H][H]', 'name': 'Lindlar catalyst'}:
                self.assertTrue(found); self.assertFalse(found[0]['assessment']['canRun'])
            else: self.assertFalse(found)
        a, b, c, _, found = matched(conditions={'profileId': PATHWAY, 'canRun': True})
        self.assertFalse(found[0]['guidedConditions']['canApply'])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(found[0]['id'], a, b, c)

    def test_distant_stereo_mapping_calculator_and_saturated_path_switch(self):
        for source in ['CC#CC', 'CCC#CCC', 'C#CC[C@H](C)CC']:
            a, b, c, _, found = matched(source); r = found[0]
            qualified = matched(source, {**c, **r['guidedConditions']['targetConditions']})[4][0]
            self.assertEqual(r['id'], qualified['id']); self.assertEqual(r['stereochemistry'], qualified['stereochemistry'])
            c = {'catalyst': 'lindlar'}; diagram = service.reaction_diagram(r['id'], a, b, c)
            p = service.run_curated_reaction(r['id'], a, b, c)['product']
            self.assertIsNone(diagram['mechanism'])
            self.assertEqual([(x['atomIndex'], x['mapId'], x['element']) for x in diagram['atoms'] if x['side'] == 'products' and x['speciesIndex'] == 0],
                             [(x['index'], x['mapId'], x['element']) for x in p['atomLinks']])
            self.assertTrue(qualified['stoichiometry']['balanced']); self.assertEqual([x['coefficient'] for x in qualified['stoichiometry']['reactants']], [1, 1])
            self.assertTrue(qualified['stoichiometry']['context']['canGenerate3D']); self.assertIn('not predicted', qualified['stoichiometry']['context']['warning'])
            metal = matched(source, {'catalyst': 'metal'})[3]['reactionOptions']
            self.assertFalse(next(x for x in metal if x['mechanism'] == PATHWAY)['assessment']['canRun'])
            self.assertTrue(next(x for x in metal if x['mechanism'] == 'Alkyne hydrogenation')['assessment']['canRun'])


def conflict(self, catalyst):
    c = {'catalyst': catalyst}; r = matched(conditions=c)[4][0]; g = r['guidedConditions']
    self.assertTrue(g['canApply']); self.assertEqual(g['state'], 'conflicting-conditions'); self.assertTrue(g['requireConfirmation'])
    self.assertEqual(g['requirements'][0]['selectedValue'], catalyst); self.assertEqual(g['requirements'][0]['state'], 'conflicting')
    self.assertFalse(r['assessment']['canRun'])
    self.assertTrue(matched(conditions={**c, **g['targetConditions']})[4][0]['assessment']['canRun'])


for i, catalyst in enumerate(['none', 'metal', 'acid', 'radical']):
    setattr(LindlarGuidanceTests, f'test_explicit_activation_replacement_{i}', lambda self, c=catalyst: conflict(self, c))


def blocked(self, c):
    a, b, _, _, found = matched(conditions=c); r = found[0]; g = r['guidedConditions']
    self.assertEqual(g['state'], 'unsupported-conditions'); self.assertFalse(g['canApply']); self.assertNotIn('targetConditions', g)
    self.assertFalse(r['assessment']['canRun']); self.assertTrue(service.reaction_diagram(r['id'], a, b, c)['svg'])
    with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, c)


for i, c in enumerate([{'catalyst': 'lindlar', 'solvent': s} for s in ['aqueous-protic', 'ethanolic-protic', 'polar-aprotic']] +
                      [{'catalyst': 'lindlar', 'temperature': 'heated'}, {'catalyst': 'lindlar', 'peroxide': True},
                       {'catalyst': 'lindlar', 'light': 'UV'}, {**SECONDARY, 'catalyst': 'lindlar'}]):
    setattr(LindlarGuidanceTests, f'test_no_automatic_condition_repair_{i}', lambda self, c=c: blocked(self, c))


class LindlarGuidancePublicTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='phase5f-api-'); self.addCleanup(folder.cleanup); self.origin = 'https://lindlar-guided.example.test'
        self.app = create_app({'TRIAL_PASSWORD': 'Synthetic-Lindlar-password', 'SESSION_SECRET': secrets.token_hex(32), 'PUBLIC_ORIGIN': self.origin,
                               'FRAME_ANCESTORS': self.origin, 'DIST_DIR': Path(folder.name), 'TESTING': True}, chemistry_backend=service)
        self.client = self.app.test_client(); self.assertEqual(self.post('/login', data={'password': 'Synthetic-Lindlar-password'}).status_code, 303)
    def post(self, route, **kwargs): return self.client.post(route, base_url=self.origin, headers={'Origin': self.origin}, **kwargs)
    def body(self, source='CC#CC', c=None):
        body = {'reactantA': {'smiles': source}, 'reactantB': 'hydrogen', 'conditions': copy.deepcopy(c or {})}
        result = self.post('/api/reactions/match', json=body); self.assertEqual(result.status_code, 200)
        r = next(r for r in result.get_json()['reactionOptions'] if r['mechanism'] == PATHWAY); body['reactionId'] = r['id']; return body, r
    def test_explicit_apply_and_withdraw_via_public_apis(self):
        body, r = self.body(); self.assertTrue(r['guidedConditions']['canApply'])
        self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body['conditions'].update(r['guidedConditions']['targetConditions'])
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 200)
        body['conditions']['catalyst'] = ''
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
    def test_saved_lindlar_revalidates_current_structure_and_never_authorizes_multisite(self):
        body, _ = self.body(c={'catalyst': 'lindlar'}); body['reactantA'] = {'smiles': 'CCC#CCC'}
        # IDs are request-local site addresses, not content-bound authorizations.
        # A reused valid address is reconstructed against the current molecule:
        # never return the old C4 product or treat the old choice as permission.
        current = self.post('/api/reactions/run', json=body)
        self.assertEqual(current.status_code, 200)
        self.assertEqual(Chem.MolToSmiles(Chem.MolFromSmiles(current.get_json()['product']['smiles'])), 'CC/C=C\\CC')
        self.assertEqual(current.get_json()['product']['formula'], 'C6H12')
        body, r = self.body('C#CCCCCC#C', {'catalyst': 'lindlar'})
        self.assertEqual(r['guidedConditions']['state'], 'outside-profile-scope')
        self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
    def test_fake_guidance_does_not_grant_output_or_ignore_input(self):
        body, _ = self.body(); body.update(canRun=True, guidedConditions={'canApply': True, 'state': 'qualified'})
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body['conditions'] = {'catalyst': 'lindlar', 'profileId': 'approved-lindlar'}
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
    def test_two_distinct_sites_and_equivalent_aliases_remain_conditional(self):
        for source in ['C#CCCCCCC#CC', 'C#CCCCCC#C']:
            body, _ = self.body(source, {'catalyst': 'lindlar'})
            matches = self.post('/api/reactions/match', json=body).get_json()
            options = [r for r in matches['reactionOptions'] if r['mechanism'] == PATHWAY]
            self.assertEqual(len(options), 2 if source == 'C#CCCCCCC#CC' else 1)
            for r in options:
                self.assertFalse(r['guidedConditions']['canApply']); body['reactionId'] = r['id']
                self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
                self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
    def test_wrong_enum_and_authentication_are_unchanged(self):
        body, _ = self.body(); body['conditions'] = {'catalyst': 'invented-lindlar'}
        self.assertEqual(self.post('/api/reactions/match', json=body).status_code, 422)
        self.assertEqual(self.app.test_client().post('/api/reactions/match', base_url=self.origin, headers={'Origin': self.origin}, json=body).status_code, 401)
