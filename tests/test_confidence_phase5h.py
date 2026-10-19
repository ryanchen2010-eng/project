"""Independent Phase 5H condition/reporting specifications; no new chemistry."""
import copy
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rdkit import Chem
from server import chemistry_server as service
from server import aldehyde_oxidation_conditions as confidence
from server.production_app import create_app

BASE = {'solvent': 'aqueous-protic', 'oxidationStage': 'further'}
SECONDARY = {'secondaryOxidationProfile': 'naocl-acetic-ketone-v1', 'solvent': 'aqueous-protic', 'temperature': 'ambient', 'catalyst': 'none', 'oxidationStage': 'first'}
canonical = lambda s: Chem.MolToSmiles(Chem.MolFromSmiles(s))


def matched(source='CCCCC=O', conditions=None, reagent='sodium-hypochlorite', reverse=False):
    a, b = {'smiles': source}, reagent
    if reverse: a, b = b, a
    c = dict(BASE if conditions is None else conditions)
    data = service.match_reactions(a, b, c)
    return a, b, c, data, [r for r in data['reactionOptions'] if r['mechanism'] == confidence.PATHWAY]


class ConfidenceTests(unittest.TestCase):
    def positive(self, source, expected, symbol, reverse):
        a, b, c, data, options = matched(source, reagent={'smiles': f'[{symbol}+].[O-]Cl'}, reverse=reverse)
        self.assertEqual(data['supportState'], 'Conditional')
        self.assertEqual({r['productSmiles'] for r in options}, {canonical(expected)})
        for r in options:
            ev = r['assessment']['evidence']; self.assertTrue(ev['canGenerate3D'])
            self.assertFalse(ev['conditionCompleteEligibility']); self.assertFalse(ev['acidEndpointValidated'])
            self.assertFalse(ev['solutionSpeciationEstablished']); self.assertNotIn('guidedConditions', r)
            self.assertEqual(ev['conditionCompleteness'], 'model-assumptions-only')
            d = service.reaction_diagram(r['id'], a, b, c); p = service.run_curated_reaction(r['id'], a, b, c)['product']
            self.assertEqual(d['assessment'], r['assessment']); self.assertIsNone(d['mechanism'])
            self.assertEqual(r['information']['capabilities']['mappedMechanism'], 'unsupported')
            before = {x['mapId']: x for x in d['atoms'] if x['side'] == 'reactants'}
            after = {x['mapId']: x for x in d['atoms'] if x['side'] == 'products'}
            self.assertEqual({k: v['element'] for k, v in before.items()}, {k: v['element'] for k, v in after.items()})
            self.assertEqual(sum(x['formalCharge'] for x in before.values()), sum(x['formalCharge'] for x in after.values()))
            self.assertEqual(len(d['atoms']), 2 * len(before))
            # Independent net provenance: the broken formyl C-H becomes O-H;
            # that incoming O is the O from the broken hypochlorite O-Cl.
            ch = next(e['atomMaps'] for e in d['bondsBroken'] if set(e['atoms']) == {'C', 'H'})
            ocl = next(e['atomMaps'] for e in d['bondsBroken'] if set(e['atoms']) == {'O', 'Cl'})
            h = next(m for m in ch if before[m]['element'] == 'H')
            c_map = next(m for m in ch if before[m]['element'] == 'C')
            o = next(m for m in ocl if before[m]['element'] == 'O')
            self.assertEqual({frozenset(e['atomMaps']) for e in d['bondsFormed']}, {frozenset((c_map, o)), frozenset((o, h))})
            self.assertEqual(after[o]['formalCharge'], 0); self.assertEqual(after[h]['speciesIndex'], 0)
            self.assertEqual(d['products'][0]['smiles'], canonical(expected))
            self.assertIn(canonical(f'[{symbol}+].[Cl-]'), [x['smiles'] for x in d['products']])
            self.assertEqual([(x['atomIndex'], x['mapId'], x['element']) for x in d['atoms'] if x['side'] == 'products' and x['speciesIndex'] == 0],
                             [(x['index'], x['mapId'], x['element']) for x in p['atomLinks']])
            self.assertTrue(r['stoichiometry']['balanced']); self.assertEqual([x['coefficient'] for x in r['stoichiometry']['reactants']], [1, 1])
            self.assertIn('not isolated acid yields', r['stoichiometry']['context']['warning'])
            self.assertIn('work-up are not established', d['note'])

    def blocked(self, extra):
        a, b, c, _, options = matched(conditions={**BASE, **extra}); self.assertTrue(options)
        for r in options:
            ev = r['assessment']['evidence']; self.assertFalse(ev['canGenerate3D'])
            self.assertTrue(r['assessment']['conditionIssues'])
            self.assertNotIn('Unfavorable', r['reasoning']['label'])
            self.assertTrue(service.reaction_diagram(r['id'], a, b, c)['svg'])
            self.assertFalse(r['stoichiometry']['context']['canGenerate3D'])
            self.assertIn('3D is blocked', r['stoichiometry']['context']['warning'])
            with patch.object(service, 'mapped_product_molecule', side_effect=AssertionError('Must reject before conformer generation')):
                with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, c)

    def test_missing_and_conflicting_settings_are_precise_without_new_matches(self):
        for c in [{}, {'oxidationStage': 'further'}, {'solvent': 'aqueous-protic'}, {'oxidationStage': 'first', 'solvent': 'aqueous-protic'}, {**BASE, 'solvent': 'dry'}]:
            assessment = confidence.assess_conditions({}, c)
            self.assertFalse(assessment['canRun']); self.assertNotIn('impossible', assessment['label'])
            _, _, _, data, found = matched(conditions=c)
            self.assertFalse(found); self.assertTrue(data['unsupportedReasons'])
            self.assertIn('reporting', ' '.join(data['unsupportedReasons']))
        self.assertEqual(confidence.assess_conditions({}, {})['missingSettings'], ['solvent', 'oxidationStage'])

    def test_background_equivalent_selectors_are_explicitly_not_applicable(self):
        r = matched(conditions={**BASE, 'additionStage': 'two', 'polymerUnits': '6'})[4][0]
        self.assertTrue(r['assessment']['canRun'])
        self.assertEqual(r['assessment']['notApplicableSettings'], ['additionStage', 'polymerUnits'])
        self.assertEqual([x['coefficient'] for x in r['stoichiometry']['reactants']], [1, 1])

    def test_scope_and_distant_stereo_permissions_are_not_expanded(self):
        for source in ['CC[C@H](C)CC=O', 'NCCCC=O', 'FCCCCC=O', 'C=CC=O', 'C#CC=O', 'CCC(=O)C']:
            self.assertFalse(matched(source)[4])
        with self.assertRaises(service.ChemistryError): matched('CC(=O)[O-]')

    def test_actual_oxidant_identity_required(self):
        for reagent in ['water', 'hydrogen', {'smiles': '[O-]Cl'}, {'smiles': 'OCl'}, {'smiles': '[Na+].[Cl-]'}, {'smiles': 'OO', 'name': 'NaOCl'}]:
            try: found = matched(reagent=reagent)[4]
            except service.ChemistryError: continue  # Explicit input-scope rejection is valid too.
            self.assertFalse(found)

    def test_invalid_enums_are_not_normalized_into_permission(self):
        for c in [{**BASE, 'catalyst': 'magic'}, {**BASE, 'temperature': None}, {**BASE, 'workup': 'acidification'}]:
            with self.assertRaises(service.ChemistryError): matched(conditions=c)

    def test_primary_and_secondary_confidence_matches_top_level(self):
        for source, c, allow in [('CCO', SECONDARY, False), ('CC(O)C', {}, False), ('CC(O)C', SECONDARY, True)]:
            data = service.match_reactions({'smiles': source}, 'sodium-hypochlorite', c)
            self.assertEqual(data['supportState'], 'Conditional')
            r = data['reactionOptions'][0]; self.assertEqual(r['assessment']['canRun'], allow)
            if source == 'CCO': self.assertEqual(r['guidedConditions']['state'], 'no-validated-profile')

    def test_water_replacement_summary_agrees_with_rows(self):
        c = {k: v for k, v in SECONDARY.items() if k != 'secondaryOxidationProfile'}
        r = service.match_reactions({'smiles': 'CC(O)C'}, 'sodium-hypochlorite', c)['reactionOptions'][0]
        g = r['guidedConditions']; self.assertEqual(g['state'], 'conflicting-conditions')
        self.assertEqual(next(x['state'] for x in g['requirements'] if x['field'] == 'solvent'), 'conflicting')
        self.assertEqual(g['targetConditions'], SECONDARY)

    def test_both_guides_revalidate_and_primary_never_inherits_permission(self):
        for source, reagent, c in [('CC(O)C', 'sodium-hypochlorite', {}), ('CC#CC', 'hydrogen', {'catalyst': 'metal'})]:
            data = service.match_reactions({'smiles': source}, reagent, c)
            r = next(r for r in data['reactionOptions'] if r.get('guidedConditions', {}).get('canApply'))
            proposal = copy.deepcopy(c); proposal.update(r['guidedConditions']['targetConditions'])
            current = next(o for o in service.match_reactions({'smiles': source}, reagent, proposal)['reactionOptions'] if o['id'] == r['id'])
            self.assertTrue(current['assessment']['canRun']); self.assertTrue(service.run_curated_reaction(r['id'], {'smiles': source}, reagent, proposal)['balanced'])
            with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], {'smiles': source}, reagent, c)
        multi = service.match_reactions({'smiles': 'C#CCCCCC#C'}, 'hydrogen', {'catalyst': 'lindlar'})
        self.assertTrue(all(not r['assessment']['canRun'] for r in multi['reactionOptions']))
        for c in [SECONDARY, {**SECONDARY, 'catalyst': 'lindlar'}, {**SECONDARY, 'profileId': 'approved'}]:
            r = service.match_reactions({'smiles': 'CCO'}, 'sodium-hypochlorite', c)['reactionOptions'][0]
            self.assertFalse(r['assessment']['canRun'])


for i, (source, product) in enumerate([('C=O', 'O=CO'), ('CCC=O', 'CCC(=O)O'), ('CC(C)C=O', 'CC(C)C(=O)O'),
                                       ('O=Cc1ccccc1', 'O=C(O)c1ccccc1'), ('COCCC=O', 'COCCC(=O)O'), ('O=CC1CCCCC1', 'O=C(O)C1CCCCC1')]):
    for symbol in ['Na', 'K']:
        for reverse in [False, True]:
            setattr(ConfidenceTests, f'test_reporting_product_{i}_{symbol}_{reverse}', lambda self, a=source, p=product, s=symbol, r=reverse: self.positive(a, p, s, r))

for i, extra in enumerate([{'catalyst': x} for x in ['radical', 'acid', 'metal', 'lindlar', 'osmium']] +
                          [{'workup': 'aqueous-release'}, {'pressure': 'unknown'}, {'pH': 14}, {'secondaryOxidationProfile': 'naocl-acetic-ketone-v1'}, {'temperature': 'heated'}]):
    setattr(ConfidenceTests, f'test_unsupported_condition_{i}', lambda self, c=extra: self.blocked(c))


def competing(self, source, products):
    a, b, c, _, options = matched(source); self.assertEqual({r['productSmiles'] for r in options}, {canonical(s) for s in products})
    for r in options:
        self.assertTrue(r['aldehydeOxidationModel']['competition']); self.assertFalse(r['assessment']['canRun'])
        self.assertTrue(service.reaction_diagram(r['id'], a, b, c)['svg'])
        with self.assertRaises(service.ChemistryError): service.run_curated_reaction(r['id'], a, b, c)


for i, (source, products) in enumerate([('O=CCCC=O', ['O=CCCC(=O)O']), ('OCCCC=O', ['OCCCC(=O)O']), ('CC(=O)CCC=O', ['CC(=O)CCC(=O)O'])]):
    setattr(ConfidenceTests, f'test_competing_site_{i}', lambda self, s=source, p=products: competing(self, s, p))


class PublicConfidenceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='phase5h-api-'); self.addCleanup(folder.cleanup)
        self.origin = 'https://phase5h.example.test'
        self.client = create_app({'TRIAL_PASSWORD': 'Phase5H-synthetic-password', 'SESSION_SECRET': secrets.token_hex(32), 'PUBLIC_ORIGIN': self.origin,
                                  'FRAME_ANCESTORS': self.origin, 'DIST_DIR': Path(folder.name), 'TESTING': True, 'API_REQUESTS_PER_MINUTE': 200, 'API_GLOBAL_REQUESTS_PER_MINUTE': 500}, chemistry_backend=service).test_client()
        self.assertEqual(self.post('/login', data={'password': 'Phase5H-synthetic-password'}).status_code, 303)

    def post(self, path, **kw): return self.client.post(path, base_url=self.origin, headers={'Origin': self.origin}, **kw)

    def body(self):
        body = {'reactantA': {'smiles': 'CCCCC=O'}, 'reactantB': 'sodium-hypochlorite', 'conditions': dict(BASE)}
        response = self.post('/api/reactions/match', json=body); self.assertEqual(response.status_code, 200)
        r = response.get_json()['reactionOptions'][0]; body['reactionId'] = r['id']; return body, r

    def test_each_phase5g_ignored_input_is_blocked_at_public_run(self):
        for extra in [{'catalyst': 'radical'}, {'workup': 'aqueous-release'}, {'pressure': 'unknown'}, {'catalyst': 'acid'}, {'secondaryOxidationProfile': 'naocl-acetic-ketone-v1'}]:
            body, _ = self.body(); body['conditions'].update(extra)
            current = self.post('/api/reactions/match', json=body).get_json()['reactionOptions'][0]
            self.assertFalse(current['assessment']['canRun'])
            self.assertEqual(self.post('/api/reactions/diagram', json=body).status_code, 200)
            self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)

    def test_saved_valid_settings_are_revalidated_not_cached_permission(self):
        body, _ = self.body(); self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 200)
        for key in ['solvent', 'oxidationStage']:
            altered = copy.deepcopy(body); altered['conditions'][key] = ''
            self.assertEqual(self.post('/api/reactions/run', json=altered).status_code, 422)
        altered = copy.deepcopy(body); altered['reactantA'] = {'smiles': 'O=CCCC=O'}
        self.assertEqual(self.post('/api/reactions/run', json=altered).status_code, 422)

    def test_forged_flags_wrong_reagent_and_stale_id_do_not_authorize(self):
        body, _ = self.body(); body.update(canRun=True, guidedConditions={'state': 'qualified'})
        body['conditions']['pressure'] = 'unknown'
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body, _ = self.body(); body['reactantB'] = 'hydrogen'
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)
        body, _ = self.body(); body['reactionId'] = 'invented-profile'
        self.assertEqual(self.post('/api/reactions/run', json=body).status_code, 422)


if __name__ == '__main__': unittest.main()
