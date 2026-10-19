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
# Independent product formulas and atomic-weight sums, not production edits.
# Each tuple supplies C/H/O counts AFTER one HX addition and expected options.
cases=[('C=CC',3,7,0,1),('CC=CCCC',6,13,0,2),('C1=CCCCCC1',7,13,0,1),
 ('C=CC[C@H](C)CC',7,15,0,1),('C=CCCCCCCCCC=C',12,23,0,1),
 ('C=CCCCCCCCCC=CC',13,25,0,3),('CC/C=C/CC',6,13,0,1),('CC/C=C\\\\CC',6,13,0,1)]
oxygen=[('C=CCCCCCCCO',9,19,1,1),('C=CCCCCCCCOC',10,21,1,1),
 ('C=CCCC[C@H](C)CCCCO',11,23,1,1)]
for reagent,x,weight in [('hydrogen-chloride','Cl',35.453),('hydrogen-bromide','Br',79.904),('hydrogen-iodide','I',126.904)]:
 for substrate,c,h,o,count in cases+(oxygen if x=='Cl' else []):
  for reverse in [False,True]:
   a,b={'smiles':substrate},reagent
   if reverse:a,b=b,a
   result=s.match_reactions(a,b,{'solvent':'dry','temperature':'ambient','catalyst':'none'})
   options=[r for r in result['reactions'] if r['mechanism']=='Hydrohalogenation']
   assert len(options)==count,(substrate,x,len(options),result['unsupportedReasons'])
   for r in options:
    assert r['assessment']['canRun']
    rows.append(dict(substrate=substrate,reverse=reverse,x=x,site=r['id'],stoichiometry=r['stoichiometry'],
      productMass=c*12.011+h*1.008+o*15.999+weight,hxMass=weight+1.008))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
assert.equal(fixtures.length, 72);
for (const f of fixtures) {
  test(`ionic HX amounts: ${f.substrate}, H${f.x}, reverse=${f.reverse}, ${f.site}`, () => {
    const d = f.stoichiometry, substrateSlot = f.reverse ? 1 : 0, hxSlot = 1 - substrateSlot;
    assert.equal(d.balanced, true); assert.deepEqual(d.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(d.product.coefficient, 1); assert.deepEqual(d.excludedInputs, []);
    close(d.product.molarMass, f.productMass);
    close(d.reactants.find((r) => r.inputSlot === hxSlot).molarMass, f.hxMass);
    close(d.reactants.find((r) => r.inputSlot === substrateSlot).molarMass, f.productMass - f.hxMass);
    const result = calculateReaction(d, {
      [substrateSlot]: { value: 20, unit: 'mmol' }, [hxSlot]: { value: f.hxMass * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005); close(result.product.grams, f.productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [hxSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(d, { value: f.productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002); close(r.grams, (r.inputSlot === hxSlot ? f.hxMass : f.productMass - f.hxMass) * 0.002);
    }
    assert.ok(d.notes.some((n) => /HX is not a regenerated acid catalyst/.test(n)));
    assert.ok(d.notes.some((n) => /not selective mono-addition, regio\/stereoisomer ratios/.test(n)));
    assert.equal(d.reactants.length, 2); // Unlike hydration, HX IS consumed.
  });
}

test('radical status is unsupported, not unfavorable or a supported ionic model', () => {
  assert.equal(conditionLabel({ status: 'unsupported-pathway', state: 'incomplete', note: '' }),
    'Requested pathway unsupported · no product prediction');
  assert.doesNotMatch(conditionLabel({ status: 'unsupported-pathway', state: 'incomplete', note: '' }), /unfavorable|match/i);
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
test('unevaluated HX solvent capture keeps 2D but disables 3D/run/compare', () => {
  const c = controlsFor({ mechanism: 'Hydrohalogenation', assessment: { status: 'unevaluated', canRun: false } });
  assert.equal(c.view2D.disabled, false);
  for (const x of [c.view3D, c.viewCompare, c.runButton]) assert.equal(x.disabled, true);
});
test('HCl oxygen spectators missing ambient setting cannot run a 3D product', () => {
  const c = controlsFor({ mechanism: 'Hydrohalogenation', assessment: { status: 'missing', canRun: false } });
  assert.equal(c.view2D.disabled, false); assert.equal(c.runButton.disabled, true);
});
test('supported ionic options and original pathways retain their existing controls', () => {
  for (const r of [{ mechanism: 'Hydrohalogenation', assessment: { canRun: true } }, {}, { assessment: { status: 'disfavored' } }]) {
    for (const x of Object.values(controlsFor(r))) assert.equal(x.disabled, false);
  }
});
test('no selection and active run preserve disabled/busy control behavior', () => {
  for (const c of Object.values(controlsFor(null))) assert.equal(c.disabled, true);
  const running = controlsFor({ assessment: { canRun: true } }, {});
  assert.equal(running.runButton.disabled, true); assert.equal(running.runButton.textContent, 'Calculating 3D…');
});
test('programmatic 3D requests cannot bypass HX condition gating', async () => {
  const start = ui.indexOf('async function showProduct3D(');
  const prefix = transpile(ui.slice(start, ui.indexOf('  setPreview(mode);', start)) + '\n}\n');
  const calls = [], reaction = { mechanism: 'Hydrohalogenation', assessment: { canRun: false, note: 'Halide versus water capture is unvalidated.' } };
  await new Function('selectedReaction', 'resolveReactant', 'setStatus', prefix + '\nreturn showProduct3D();')(
    reaction, () => ({}), (message) => calls.push(message),
  );
  assert.deepEqual(calls, ['Halide versus water capture is unvalidated.']);
});
test('existing HX condition controls invalidate obsolete selected results', () => {
  assert.match(ui, /for \(const select of \[solventInput, temperatureInput, catalystInput[^]*?addEventListener\('change'[^]*?updateMatches\(\)/);
  const update = ui.slice(ui.indexOf('function updateMatches('), ui.indexOf('async function findReactions('));
  assert.match(update, /resetResult\(\)/);
});
