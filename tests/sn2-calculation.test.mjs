import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { calculateReaction, calculateRequiredAmounts } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);
const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
for substrate in ['COCCCBr','CC[C@H](Br)CCC','CC[C@H](C)CCCBr','BrCCCCBr']:
 for reverse in [False,True]:
  a={'smiles':substrate}; b='hydroxide'
  if reverse: a,b=b,a
  for r in s.match_reactions(a,b,{'solvent':'polar-aprotic'})['reactions']:
   if r['mechanism']=='SN2':
    rows.append(dict(substrate=substrate,reagent='hydroxide',reverse=reverse,site=r['site']['siteId'],stoichiometry=r['stoichiometry']))
for reagent,name in [('sodium-hydroxide','NaOH'),({'smiles':'[K+].[OH-]'},'KOH')]:
 for reverse in [False,True]:
  a={'smiles':'COCCCBr'}; b=reagent
  if reverse: a,b=b,a
  for r in s.match_reactions(a,b,{'solvent':'polar-aprotic'})['reactions']:
   if r['mechanism']=='SN2':
    rows.append(dict(substrate='COCCCBr',reagent=name,reverse=reverse,site=r['site']['siteId'],stoichiometry=r['stoichiometry']))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
assert.equal(fixtures.length, 14, 'all expected public sites and full salts must feed the real calculator');
for (const f of fixtures) {
  test(`SN2 → calculator: ${f.substrate}, ${f.reagent}, reverse=${f.reverse}, ${f.site}`, () => {
    const data = f.stoichiometry;
    const substrateSlot = f.reverse ? 1 : 0;
    const hydroxideSlot = 1 - substrateSlot;
    // Independent products: C4H10O2, C6H14O, C7H16O, or one-site C4H9BrO.
    const productMass = f.substrate === 'COCCCBr' ? 4 * 12.011 + 10 * 1.008 + 2 * 15.999
      : f.substrate === 'CC[C@H](Br)CCC' ? 6 * 12.011 + 14 * 1.008 + 15.999
        : f.substrate === 'CC[C@H](C)CCCBr' ? 7 * 12.011 + 16 * 1.008 + 15.999
          : 4 * 12.011 + 9 * 1.008 + 79.904 + 15.999;
    const hydroxideMass = 15.999 + 1.008;
    const actualReagentMass = hydroxideMass + (f.reagent === 'NaOH' ? 22.990 : f.reagent === 'KOH' ? 39.098 : 0);
    assert.equal(data.balanced, true);
    close(data.product.molarMass, productMass);
    close(data.reactants.find((r) => r.inputSlot === substrateSlot).molarMass, productMass + 79.904 - hydroxideMass);
    close(data.reactants.find((r) => r.inputSlot === hydroxideSlot).molarMass, actualReagentMass);
    assert.deepEqual(data.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(data.product.coefficient, 1);
    const result = calculateReaction(data, {
      [substrateSlot]: { value: 20, unit: 'mmol' },
      [hydroxideSlot]: { value: actualReagentMass * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005);
    close(result.product.grams, productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [hydroxideSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(data, { value: productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002);
      close(r.grams, data.reactants.find((x) => x.inputSlot === r.inputSlot).molarMass * 0.002);
    }
    assert.ok(data.notes.some((s) => s.includes('not a predicted or actual yield')));
    if (f.reagent !== 'hydroxide') assert.ok(data.notes.some((s) => s.includes('full salt molar mass')));
  });
}
