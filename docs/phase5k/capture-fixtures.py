"""Generate frozen display assets for design proposals, not production chemistry.

Uses the existing public service functions without changing any engine, test or
benchmark. The browser proposals only read the resulting static JSON.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server import chemistry_server as service


def capture(a, b, conditions, mechanism):
    matched = service.match_reactions(a, b, conditions)
    reaction = next(r for r in matched['reactions'] if r['mechanism'] == mechanism)
    diagram = service.reaction_diagram(reaction['id'], a, b, conditions)
    run = None
    if reaction['assessment'].get('canRun') is not False:
        run = service.run_curated_reaction(reaction['id'], a, b, conditions)
        assert run['balanced'] and run['product']['representation'] == '3d'
    return {'inputs': [a, b], 'conditions': conditions, 'reaction': reaction,
            'diagram': diagram, 'run': run}


sn2 = capture('bromomethane', 'hydroxide', {'solvent': 'polar-aprotic'}, 'SN2')
assert sn2['run']['product']['smiles'] == 'CO'
assert len(sn2['diagram']['mechanism']['steps']) == 1
missing = capture('2-propanol', 'sodium-hypochlorite', {'solvent': 'aqueous-protic'}, 'Alcohol oxidation')
assert missing['run'] is None
guidance = missing['reaction']['guidedConditions']
assert guidance['canApply']
qualified = capture('2-propanol', 'sodium-hypochlorite', guidance['targetConditions'], 'Alcohol oxidation')
assert qualified['run']['product']['smiles'] in ('CC(C)=O', 'CC(=O)C')

payload = {'schemaVersion': 1, 'purpose': 'Static design review only; no experimental outcomes asserted',
           'sn2': sn2, 'secondaryMissing': missing, 'secondaryQualified': qualified}
target = Path(__file__).with_name('fixtures.json')
if target.exists():
    raise SystemExit('Fixture already exists; preserve it rather than overwrite.')
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: {'reactionId': v['reaction']['id'],
                      'product': v['reaction']['productName'],
                      'canRun': v['reaction']['assessment'].get('canRun', True),
                      'diagramAtoms': len(v['diagram'].get('atoms', []))}
                  for k, v in payload.items() if isinstance(v, dict)}))
