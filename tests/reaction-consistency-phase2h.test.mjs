import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

async function importSource(path) {
  const source = await readFile(new URL(`../${path}`, import.meta.url), 'utf8');
  const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } });
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
}
const { conditionLabel, unsupportedInputMessage } = await importSource('src/reaction-conditions.ts');
const { calculateReaction, calculateRequiredAmounts } = await importSource('src/reaction-calculator.ts');

for (const [status, expected] of [
  ['model-match', /Model conditions match.*not guaranteed/],
  ['reference-difference', /Reference conditions differ.*not proof/],
  ['missing', /Comparison conditions incomplete/],
  ['disfavored', /Disfavoring factor.*may still occur/],
  ['unevaluated', /not reliably evaluated/],
]) {
  test(`condition badge distinguishes ${status} without an unsupported winner`, () => {
    const text = conditionLabel({ status, state: 'alternative', note: '' });
    assert.match(text, expected); assert.doesNotMatch(text, /guaranteed major|cannot react|\d+%/);
  });
}
test('other reaction families retain legacy condition badges', () => {
  assert.equal(conditionLabel({ state: 'aligned', note: '' }), 'Conditions fit the example · outcome not guaranteed');
  assert.equal(conditionLabel({ state: 'alternative', note: '' }), 'Conditions differ from the example');
  assert.match(conditionLabel(), /Check the conditions/);
});
test('422 explanations preserve API reasons as text and retain the model-scope caveat', () => {
  const value = unsupportedInputMessage('<img onerror=bad> Unsupported relative stereochemistry.');
  assert.match(value, /Unsupported relative stereochemistry/);
  assert.match(value, /not proof/); assert.ok(value.startsWith('<img onerror=bad>'));
  assert.match(unsupportedInputMessage('  '), /outside the supported reaction model/);
});
test('existing reaction controls consume new labels and render rejection text safely', async () => {
  const source = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
  assert.match(source, /import \{ conditionLabel, unsupportedInputMessage/);
  assert.match(source, /showEmpty\(unsupportedInputMessage\('error' in payload/);
  const empty = source.slice(source.indexOf('function showEmpty('), source.indexOf('async function findReactions('));
  assert.match(empty, /textContent\s*=\s*message/);
  assert.doesNotMatch(empty, /innerHTML\s*=\s*message/);
});

const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
cases=[('SN1','CC(Br)C','water',3*12.011+8*1.008+15.999,79.904,18.015),
 ('SN1','CCC(Br)C','water',4*12.011+10*1.008+15.999,79.904,18.015),
 ('SN1','C[C@H](Br)CC','water',4*12.011+10*1.008+15.999,79.904,18.015),
 ('SN1','C[C@@H](Br)CC','water',4*12.011+10*1.008+15.999,79.904,18.015),
 ('SN2','BrCCCCCCC(Cl)(C)C','hydroxide',9*12.011+19*1.008+35.453+15.999,79.904,17.007),
 ('SN2','ClCCCCCCC(Br)(C)C','hydroxide',9*12.011+19*1.008+79.904+15.999,35.453,17.007),
 ('SN2','BrCCCCCCC(Cl)(C)C','sodium-hydroxide',9*12.011+19*1.008+35.453+15.999,79.904,39.997),
 ('SN2','BrCCCCCCC(Cl)(C)C',{'smiles':'[K+].[OH-]'},9*12.011+19*1.008+35.453+15.999,79.904,56.105)]
for path,substrate,reagent,mass,leavingMass,reagentMass in cases:
 for reverse in [False,True]:
  a,b={'smiles':substrate},reagent
  if reverse:a,b=b,a
  options=[r for r in s.match_reactions(a,b,{'solvent':'aqueous-protic','temperature':'ambient'})['reactions'] if r['mechanism']==path]
  assert len(options)==1
  rows.append(dict(path=path,substrate=substrate,reagent=reagent,reverse=reverse,stoichiometry=options[0]['stoichiometry'],
                   mass=mass,substrateMass=mass+leavingMass-15.999-1.008,reagentMass=reagentMass))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);
assert.equal(fixtures.length, 16);
for (const f of fixtures) {
  test(`Phase 2H calculator: ${f.path} ${f.substrate}, ${JSON.stringify(f.reagent)}, reverse=${f.reverse}`, () => {
    const d = f.stoichiometry, substrateSlot = f.reverse ? 1 : 0, reagentSlot = 1 - substrateSlot;
    assert.equal(d.balanced, true); assert.deepEqual(d.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(d.product.coefficient, 1); close(d.product.molarMass, f.mass);
    close(d.reactants.find((r) => r.inputSlot === substrateSlot).molarMass, f.substrateMass);
    close(d.reactants.find((r) => r.inputSlot === reagentSlot).molarMass, f.reagentMass);
    const result = calculateReaction(d, { [substrateSlot]: { value: 20, unit: 'mmol' }, [reagentSlot]: { value: f.reagentMass * 0.005, unit: 'g' } });
    close(result.product.moles, 0.005); close(result.product.grams, f.mass * 0.005);
    assert.deepEqual(result.limitingInputs, [reagentSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(d, { value: f.mass * 0.002, unit: 'g' });
    for (const r of required.reactants) { close(r.moles, 0.002); close(r.grams, (r.inputSlot === substrateSlot ? f.substrateMass : f.reagentMass) * 0.002); }
    assert.ok(d.notes.some((note) => note.includes('not a predicted or actual yield')));
  });
}
