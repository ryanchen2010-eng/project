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
for substrate in ['COCCCCCCC(Br)(C)C','CC[C@H](C)CCC(Br)(C)C','C[C@H](Br)c1ccccc1','C=C(C)C(Br)(C)C','CC(Br)(C)CCC(Br)(C)C','CCC(Br)C']:
 for reverse in [False,True]:
  a={'smiles':substrate}; b='water'
  if reverse: a,b=b,a
  for r in s.match_reactions(a,b,{'solvent':'aqueous-protic','temperature':'heated'})['reactions']:
   if r['mechanism']=='E1':
    rows.append(dict(substrate=substrate,reverse=reverse,site=r['site']['siteId'],stoichiometry=r['stoichiometry']))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
assert.equal(fixtures.length, 24, 'all independent beta positions and C–X sites must reach the actual arithmetic');
for (const f of fixtures) {
  test(`E1 → calculator: ${f.substrate}, reverse=${f.reverse}, ${f.site}`, () => {
    const data = f.stoichiometry;
    const substrateSlot = f.reverse ? 1 : 0;
    const waterSlot = 1 - substrateSlot;
    // Independent net identities, not masses copied from engine products:
    // C10H20O, C9H18, C8H8, C6H10, one-site C8H15Br, or C4H8.
    const productMass = f.substrate === 'COCCCCCCC(Br)(C)C' ? 10 * 12.011 + 20 * 1.008 + 15.999
      : f.substrate === 'CC[C@H](C)CCC(Br)(C)C' ? 9 * 12.011 + 18 * 1.008
        : f.substrate === 'C[C@H](Br)c1ccccc1' ? 8 * 12.011 + 8 * 1.008
          : f.substrate === 'C=C(C)C(Br)(C)C' ? 6 * 12.011 + 10 * 1.008
            : f.substrate === 'CC(Br)(C)CCC(Br)(C)C' ? 8 * 12.011 + 15 * 1.008 + 79.904
              : 4 * 12.011 + 8 * 1.008;
    assert.equal(data.balanced, true);
    assert.deepEqual(data.reactants.map((r) => [r.inputSlot, r.coefficient]), [[substrateSlot, 1]]);
    assert.equal(data.product.coefficient, 1);
    assert.deepEqual(data.excludedInputs, [{ inputSlot: waterSlot, name: 'Water', reason: 'Solvent / medium; not consumed in this net equation.' }]);
    close(data.product.molarMass, productMass);
    close(data.reactants[0].molarMass, productMass + 79.904 + 1.008);
    // Zero/absent solvent quantities cannot falsely make water limiting.
    for (const waterAmount of [undefined, { value: 0, unit: 'mol' }]) {
      const amounts = { [substrateSlot]: { value: 20, unit: 'mmol' } };
      if (waterAmount) amounts[waterSlot] = waterAmount;
      const result = calculateReaction(data, amounts);
      close(result.product.moles, 0.02);
      close(result.product.grams, productMass * 0.02);
      assert.deepEqual(result.limitingInputs, [substrateSlot]);
      close(result.reactants[0].remainingMoles, 0);
    }
    const required = calculateRequiredAmounts(data, { value: productMass * 0.002, unit: 'g' });
    assert.equal(required.reactants.length, 1);
    close(required.reactants[0].moles, 0.002);
    close(required.reactants[0].grams, data.reactants[0].molarMass * 0.002);
    assert.ok(data.notes.some((s) => s.includes('not a predicted or actual yield')));
    assert.ok(data.notes.some((s) => s.includes('Water is solvent/base')));
    assert.ok(data.notes.some((s) => s.includes('not solvent quantity')));
  });
}
