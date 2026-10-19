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
for substrate in ['COCCCCCCC(Br)(C)C','C[C@H](Br)c1ccccc1','C=CCBr','CC(Br)(C)CCCC(Cl)(C)CC']:
 for reverse in [False,True]:
  a={'smiles':substrate}; b='water'
  if reverse: a,b=b,a
  for r in s.match_reactions(a,b,{'solvent':'aqueous-protic','temperature':'ambient'})['reactions']:
   if r['mechanism']=='SN1':
    rows.append(dict(substrate=substrate,reverse=reverse,site=r['site']['siteId'],byproduct=r['byproducts'][0]['formula'],stoichiometry=r['stoichiometry']))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
assert.equal(fixtures.length, 10, 'all public sites, including both halides, must reach real calculator arithmetic');
for (const f of fixtures) {
  test(`SN1 → calculator: ${f.substrate}, reverse=${f.reverse}, ${f.site}`, () => {
    const data = f.stoichiometry;
    const substrateSlot = f.reverse ? 1 : 0;
    const waterSlot = 1 - substrateSlot;
    const leavingMass = f.byproduct === 'HBr' ? 79.904 : 35.453;
    // Independent net products, not masses copied from engine outputs:
    // C10H22O2, C8H10O, C3H6O, or C10H21(remaining halide)O.
    const productMass = f.substrate === 'COCCCCCCC(Br)(C)C' ? 10 * 12.011 + 22 * 1.008 + 2 * 15.999
      : f.substrate === 'C[C@H](Br)c1ccccc1' ? 8 * 12.011 + 10 * 1.008 + 15.999
        : f.substrate === 'C=CCBr' ? 3 * 12.011 + 6 * 1.008 + 15.999
          : 10 * 12.011 + 21 * 1.008 + (f.byproduct === 'HBr' ? 35.453 : 79.904) + 15.999;
    const waterMass = 15.999 + 2 * 1.008;
    assert.equal(data.balanced, true);
    assert.deepEqual(data.reactants.map((r) => r.coefficient), [1, 1]);
    assert.equal(data.product.coefficient, 1);
    close(data.product.molarMass, productMass);
    close(data.reactants.find((r) => r.inputSlot === waterSlot).molarMass, waterMass);
    close(data.reactants.find((r) => r.inputSlot === substrateSlot).molarMass, productMass + leavingMass - 15.999 - 1.008);
    const result = calculateReaction(data, {
      [substrateSlot]: { value: 20, unit: 'mmol' },
      [waterSlot]: { value: waterMass * 0.005, unit: 'g' },
    });
    close(result.product.moles, 0.005);
    close(result.product.grams, productMass * 0.005);
    assert.deepEqual(result.limitingInputs, [waterSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(data, { value: productMass * 0.002, unit: 'g' });
    for (const r of required.reactants) {
      close(r.moles, 0.002);
      close(r.grams, data.reactants.find((x) => x.inputSlot === r.inputSlot).molarMass * 0.002);
    }
    assert.ok(data.notes.some((s) => s.includes('not a predicted or actual yield')));
    assert.ok(data.notes.some((s) => s.includes('solvent/proton-transfer medium')));
    assert.ok(data.notes.some((s) => s.includes('not a prescription for solvent quantity')));
  });
}
