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
# Expected substrate formulas, option counts and reagent/acid masses do not
# come from the product editor. Actual public stoichiometry feeds the TS tool.
cases=[('C=C',2,4,0,1),('C=CC',3,6,0,2),('C/C=C/C',4,8,0,2),('C/C=C\\\\C',4,8,0,1),
 ('CC=CCCC',6,12,0,1),('C1=CCCCC1',6,10,0,1),('C=Cc1ccccc1',8,8,0,2),
 ('C=CC[C@H](C)CC',7,14,0,2),('C=CCCCCCCCO',9,18,1,2),
 ('C=CCCCCCCCOC',10,20,1,2),('C=CCCCCC=C',8,14,0,2),('C=CCCCCC=CC',9,16,0,3)]
reagents=[('CC(=O)OO',76.051,60.052,'C2H4O2'),('O=C(OO)c1cccc(Cl)c1',172.567,156.568,'C7H5ClO2')]
for substrate,c,h,o,count in cases:
 for reagent,reagent_mass,acid_mass,acid_formula in reagents:
  for reverse in [False,True]:
   a,b={'smiles':substrate},{'smiles':reagent}
   if reverse:a,b=b,a
   rs=[r for r in s.match_reactions(a,b,{'solvent':'dry'})['reactions'] if r['mechanism']=='Epoxidation']
   assert len(rs)==count,(substrate,reagent,len(rs))
   for r in rs:
    assert r['assessment']['canRun']
    assert [p['formula'] for p in r['byproducts']]==[acid_formula]
    rows.append(dict(substrate=substrate,reagent=reagent,reverse=reverse,id=r['id'],basis=r['stoichiometry'],
      substrateMass=c*12.011+h*1.008+o*15.999,reagentMass=reagent_mass,acidMass=acid_mass))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
assert.equal(fixtures.length, 84);
for (const f of fixtures) {
  test(`Peracid amounts: ${f.substrate}, ${f.reagent}, reversed=${f.reverse}, ${f.id}`, () => {
    const d = f.basis, substrate = f.reverse ? 1 : 0, oxidant = 1 - substrate;
    assert.equal(d.balanced, true); assert.deepEqual(d.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(d.product.coefficient, 1); assert.deepEqual(d.excludedInputs, []);
    close(d.product.molarMass, f.substrateMass + 15.999);
    close(d.reactants.find((r) => r.inputSlot === oxidant).molarMass, f.reagentMass);
    close(d.reactants.find((r) => r.inputSlot === substrate).molarMass, f.substrateMass);
    close(f.substrateMass + f.reagentMass, d.product.molarMass + f.acidMass);
    const result = calculateReaction(d, {
      [substrate]: { value: 20, unit: 'mmol' }, [oxidant]: { value: f.reagentMass * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005); close(result.product.grams, (f.substrateMass + 15.999) * 0.005);
    assert.deepEqual(result.limitingInputs, [oxidant]);
    close(result.reactants.find((r) => r.inputSlot === substrate).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(d, { value: (f.substrateMass + 15.999) * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002); close(r.grams, (r.inputSlot === oxidant ? f.reagentMass : f.substrateMass) * 0.002);
    }
    assert.ok(d.notes.some((n) => /actual carboxylic acid coproduct/.test(n)));
    assert.ok(d.notes.some((n) => /not an amount to sum or a stereoisomer ratio/.test(n)));
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
test('peracid capture-medium uncertainty disables 3D but retains conditional 2D', () => {
  const c = controls({ mechanism: 'Epoxidation', assessment: { canRun: false, status: 'unevaluated' } });
  assert.equal(c.view2D.disabled, false);
  for (const x of [c.view3D, c.viewCompare, c.runButton]) assert.equal(x.disabled, true);
});
test('supported dry peracid options retain existing controls', () => {
  for (const c of Object.values(controls({ mechanism: 'Epoxidation', assessment: { canRun: true } }))) assert.equal(c.disabled, false);
});
test('programmatic 3D cannot bypass peracid condition gates', async () => {
  const start = ui.indexOf('async function showProduct3D(');
  const prefix = transpile(ui.slice(start, ui.indexOf('  setPreview(mode);', start)) + '\n}\n');
  const calls = [];
  await new Function('selectedReaction', 'resolveReactant', 'setStatus', prefix + '\nreturn showProduct3D();')(
    { assessment: { canRun: false, note: 'Acid and water can open the epoxide.' } }, () => ({}), (text) => calls.push(text),
  );
  assert.deepEqual(calls, ['Acid and water can open the epoxide.']);
});
test('input/condition changes discard an obsolete epoxide and its mechanism', () => {
  assert.match(ui, /for \(const select of \[solventInput, temperatureInput, catalystInput[^]*?addEventListener\('change'[^]*?updateMatches\(\)/);
  const update = ui.slice(ui.indexOf('function updateMatches('), ui.indexOf('async function findReactions('));
  assert.match(update, /resetResult\(\)/);
  assert.match(ui, /function resetResult\([^]*?mechanismPanel\.reset\(\)/);
});
