import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
async function importSource(path) {
  return import(`data:text/javascript;base64,${Buffer.from(transpile(await readFile(new URL(`../${path}`, import.meta.url), 'utf8'))).toString('base64')}`);
}
const { conditionLabel } = await importSource('src/reaction-conditions.ts');
const { calculateReaction, calculateRequiredAmounts } = await importSource('src/reaction-calculator.ts');
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);

const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
# Independent product formulas/atomic-weight sums, not RDKit products.
cases=[('C=CC',3,8,1),('CC=CCCC',6,14,1),('C1=CCCCCC1',7,14,1),
 ('C=CCCCCCCCO',9,20,2),('C=CC[C@H](C)CC',7,16,1),('C=CCCCCCCCCC=C',12,24,1)]
for substrate,c,h,o in cases:
 for reverse in [False,True]:
  a,b={'smiles':substrate},'water'
  if reverse:a,b=b,a
  for r in s.match_reactions(a,b,{'catalyst':'acid','solvent':'aqueous-protic'})['reactions']:
   if r['mechanism']=='Hydration':
    rows.append(dict(substrate=substrate,reverse=reverse,site=r['id'],stoichiometry=r['stoichiometry'],
      productMass=c*12.011+h*1.008+o*15.999))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
assert.equal(fixtures.length, 16);
for (const f of fixtures) {
  test(`hydration amounts: ${f.substrate}, reverse=${f.reverse}, ${f.site}`, () => {
    const d = f.stoichiometry, substrateSlot = f.reverse ? 1 : 0, waterSlot = 1 - substrateSlot;
    assert.equal(d.balanced, true); assert.deepEqual(d.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(d.product.coefficient, 1); close(d.product.molarMass, f.productMass);
    close(d.reactants.find((r) => r.inputSlot === waterSlot).molarMass, 18.015);
    close(d.reactants.find((r) => r.inputSlot === substrateSlot).molarMass, f.productMass - 18.015);
    const result = calculateReaction(d, {
      [substrateSlot]: { value: 20, unit: 'mmol' }, [waterSlot]: { value: 18.015 * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005); close(result.product.grams, f.productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [waterSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(d, { value: f.productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002); close(r.grams, (r.inputSlot === waterSlot ? 18.015 : f.productMass - 18.015) * 0.002);
    }
    assert.ok(d.notes.some((n) => /Acid is regenerated and excluded/.test(n)));
    assert.ok(d.notes.some((n) => /not equilibrium yield, regioisomer ratios/.test(n)));
    assert.equal(d.reactants.length, 2); // Acid never appears as a consumed third reactant.
  });
}

test('missing acid label is activation, not reference mismatch or experimental disfavor', () => {
  assert.equal(conditionLabel({ status: 'activation-required', state: 'incomplete', note: '' }), 'Acid activation required · conditional 2D option only');
  assert.doesNotMatch(conditionLabel({ status: 'activation-required', state: 'alternative', note: '' }), /unfavorable|reference/i);
});

const ui = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
const actions = transpile(ui.slice(ui.indexOf('function updatePreviewActions()'), ui.indexOf('function setPreview(')));
function controlsFor(selectedReaction, runController = null) {
  const view2D = {}, view3D = {}, viewCompare = {}, runButton = {};
  new Function('selectedReaction', 'runController', 'view2D', 'view3D', 'viewCompare', 'runButton', actions + '\nupdatePreviewActions();')(
    selectedReaction, runController, view2D, view3D, viewCompare, runButton,
  );
  return { view2D, view3D, viewCompare, runButton };
}
test('conditional hydration leaves 2D available but disables 3D/run/compare', () => {
  const c = controlsFor({ assessment: { canRun: false } });
  assert.equal(c.view2D.disabled, false);
  for (const x of [c.view3D, c.viewCompare, c.runButton]) assert.equal(x.disabled, true);
});
test('supported activation and old pathways preserve their 3D controls', () => {
  for (const r of [{ assessment: { canRun: true } }, {}, { assessment: { status: 'disfavored' } }]) {
    const c = controlsFor(r);
    for (const x of [c.view2D, c.view3D, c.viewCompare, c.runButton]) assert.equal(x.disabled, false);
  }
});
test('no selection and an in-progress calculation keep existing control behavior', () => {
  const empty = controlsFor(null);
  for (const c of Object.values(empty)) assert.equal(c.disabled, true);
  const running = controlsFor({ assessment: { canRun: true } }, {});
  assert.equal(running.runButton.disabled, true); assert.equal(running.runButton.textContent, 'Calculating 3D…');
});
test('programmatic 3D request also respects activation gate before any preview/run', async () => {
  const start = ui.indexOf('async function showProduct3D(');
  const prefix = transpile(ui.slice(start, ui.indexOf('  setPreview(mode);', start)) + '\n}\n');
  const calls = [];
  const reaction = { assessment: { canRun: false, note: 'Acid activation required.' } };
  await new Function('selectedReaction', 'resolveReactant', 'setStatus', prefix + '\nreturn showProduct3D();')(
    reaction, () => ({}), (message) => calls.push(message),
  );
  assert.deepEqual(calls, ['Acid activation required.']);
});
test('changing existing condition controls clears obsolete selected products', () => {
  assert.match(ui, /for \(const select of \[solventInput, temperatureInput, catalystInput[^]*?addEventListener\('change'[^]*?updateMatches\(\)/);
  const update = ui.slice(ui.indexOf('function updateMatches('), ui.indexOf('async function findReactions('));
  assert.match(update, /resetResult\(\)/);
});
