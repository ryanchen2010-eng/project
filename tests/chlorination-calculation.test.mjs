import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const transpile = (text) => ts.transpileModule(text, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const source = await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8');
const { calculateReaction, calculateRequiredAmounts } = await import(`data:text/javascript;base64,${Buffer.from(transpile(source)).toString('base64')}`);
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);
const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
# Independent final formulas, atomic weights and expected numbers of choices.
cases=[('C=CC',3,6,0,2),('C/C=C/C',4,8,0,1),('C/C=C\\\\C',4,8,0,2),
 ('CC=CCCC',6,12,0,1),('C1=CCCCC1',6,10,0,2),('C=Cc1ccccc1',8,8,0,2),
 ('C=CC[C@H](C)CC',7,14,0,2),('C=CCCCCCCCCC=C',12,22,0,2),('C=CCCCCCCCCC=CC',13,24,0,3)]
for substrate,c,h,o,count in cases:
 for reverse in [False,True]:
  a,b={'smiles':substrate},'chlorine'
  if reverse:a,b=b,a
  options=[r for r in s.match_reactions(a,b,{'solvent':'dry'})['reactions'] if r['mechanism']=='Chlorination']
  assert len(options)==count,(substrate,len(options))
  for r in options:
   assert r['assessment']['canRun']
   rows.append(dict(substrate=substrate,reverse=reverse,id=r['id'],basis=r['stoichiometry'],
      productMass=c*12.011+h*1.008+o*15.999+2*35.453))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
assert.equal(fixtures.length, 34);
for (const f of fixtures) {
  test(`Cl2 amounts: ${f.substrate}, reversed=${f.reverse}, ${f.id}`, () => {
    const d = f.basis, substrate = f.reverse ? 1 : 0, chlorine = 1 - substrate;
    assert.equal(d.balanced, true); assert.deepEqual(d.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(d.product.coefficient, 1); assert.deepEqual(d.excludedInputs, []);
    close(d.product.molarMass, f.productMass);
    close(d.reactants.find((r) => r.inputSlot === chlorine).molarMass, 70.906);
    close(d.reactants.find((r) => r.inputSlot === substrate).molarMass, f.productMass - 70.906);
    const result = calculateReaction(d, {
      [substrate]: { value: 20, unit: 'mmol' }, [chlorine]: { value: 70.906 * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005); close(result.product.grams, f.productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [chlorine]);
    close(result.reactants.find((r) => r.inputSlot === substrate).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(d, { value: f.productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002); close(r.grams, (r.inputSlot === chlorine ? 70.906 : f.productMass - 70.906) * 0.002);
    }
    assert.ok(d.notes.some((n) => /no net byproduct/.test(n)));
    assert.ok(d.notes.some((n) => /not an amount to add across alternatives or a stereoisomer ratio/.test(n)));
  });
}

const ui = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
const actions = transpile(ui.slice(ui.indexOf('function updatePreviewActions()'), ui.indexOf('function setPreview(')));
function controls(reaction) {
  const view2D = {}, view3D = {}, viewCompare = {}, runButton = {};
  new Function('selectedReaction', 'runController', 'view2D', 'view3D', 'viewCompare', 'runButton', actions + '\nupdatePreviewActions();')(
    reaction, null, view2D, view3D, viewCompare, runButton,
  );
  return { view2D, view3D, viewCompare, runButton };
}
test('Cl2 capture-medium uncertainty disables 3D but keeps conditional 2D', () => {
  const c = controls({ mechanism: 'Chlorination', assessment: { canRun: false, status: 'unevaluated' } });
  assert.equal(c.view2D.disabled, false);
  for (const x of [c.view3D, c.viewCompare, c.runButton]) assert.equal(x.disabled, true);
});
test('neutral non-nucleophilic Cl2 options retain existing controls', () => {
  for (const c of Object.values(controls({ mechanism: 'Chlorination', assessment: { canRun: true } }))) assert.equal(c.disabled, false);
});
test('programmatic 3D cannot bypass chlorination condition gates', async () => {
  const start = ui.indexOf('async function showProduct3D(');
  const prefix = transpile(ui.slice(start, ui.indexOf('  setPreview(mode);', start)) + '\n}\n');
  const calls = [];
  await new Function('selectedReaction', 'resolveReactant', 'setStatus', prefix + '\nreturn showProduct3D();')(
    { assessment: { canRun: false, note: 'Water capture is a different pathway.' } }, () => ({}), (text) => calls.push(text),
  );
  assert.deepEqual(calls, ['Water capture is a different pathway.']);
});
test('condition changes clear obsolete dichloride selection and 3D result', () => {
  assert.match(ui, /for \(const select of \[solventInput, temperatureInput, catalystInput[^]*?addEventListener\('change'[^]*?updateMatches\(\)/);
  const update = ui.slice(ui.indexOf('function updateMatches('), ui.indexOf('async function findReactions('));
  assert.match(update, /resetResult\(\)/);
});

