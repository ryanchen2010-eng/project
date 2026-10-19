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
// Real public structure-based match responses, not manufactured metadata.
const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
for substrate in ['C=CCCCO','C=CC[C@H](C)CC','C=CCCCCC=C']:
 for reverse in [False,True]:
  a={'smiles':substrate}; b='hydrogen'
  if reverse: a,b=b,a
  for r in s.match_reactions(a,b,{'catalyst':'metal'})['reactions']:
   if r['mechanism']=='Hydrogenation':
    rows.append(dict(substrate=substrate,reverse=reverse,site=r['site']['siteId'],stoichiometry=r['stoichiometry']))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
for (const f of fixtures) {
  test(`hydrogenation public metadata → calculator: ${f.substrate}, reverse=${f.reverse}, ${f.site}`, () => {
    const data = f.stoichiometry;
    const substrateSlot = f.reverse ? 1 : 0;
    const hydrogenSlot = 1 - substrateSlot;
    // Independent atomic-weight sums: C5H12O / C7H16 / C8H16.
    const productMass = f.substrate === 'C=CCCCO' ? 5 * 12.011 + 12 * 1.008 + 15.999
      : f.substrate === 'C=CC[C@H](C)CC' ? 7 * 12.011 + 16 * 1.008 : 8 * 12.011 + 16 * 1.008;
    assert.equal(data.balanced, true);
    close(data.product.molarMass, productMass);
    close(data.reactants.find((r) => r.inputSlot === hydrogenSlot).molarMass, 2 * 1.008);
    assert.equal(data.product.coefficient, 1);
    assert.deepEqual(data.reactants.map((r) => r.coefficient), [1, 1]);
    const result = calculateReaction(data, {
      [substrateSlot]: { value: 20, unit: 'mmol' },
      [hydrogenSlot]: { value: 2 * 1.008 * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005);
    close(result.product.grams, productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [hydrogenSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(data, { value: productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002);
      close(r.grams, data.reactants.find((a) => a.inputSlot === r.inputSlot).molarMass * 0.002);
    }
    assert.ok(data.notes.some((s) => s.includes('not a predicted or actual yield')));
  });
}
