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
// Feed the real public match response into the actual browser calculator.
// Expected masses below are independent atomic-weight sums, not mock API data.
const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
for substrate in ['O=C1OCCC1','CC(=O)Oc1ccccc1']:
 for reagent in ['water','hydroxide','sodium-hydroxide',{'smiles':'[K+].[OH-]'}]:
  for reverse in [False,True]:
   a={'smiles':substrate}; b=reagent
   if reverse: a,b=b,a
   basic=reagent!='water'
   cond={'solvent':'aqueous-protic','catalyst':'none' if basic else 'acid'}
   mechanism='Ester saponification' if basic else 'Ester hydrolysis'
   option=next(r for r in s.match_reactions(a,b,cond)['reactions'] if r['mechanism']==mechanism)
   rows.append(dict(substrate=substrate,reagent=reagent,reverse=reverse,basic=basic,stoichiometry=option['stoichiometry']))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);
for (const f of fixtures) {
  test(`ester public metadata → calculator: ${f.substrate}, ${JSON.stringify(f.reagent)}, reverse=${f.reverse}`, () => {
    const data = f.stoichiometry;
    assert.equal(data.balanced, true);
    const substrateSlot = f.reverse ? 1 : 0;
    const reagentSlot = 1 - substrateSlot;
    const acidMass = f.substrate === 'O=C1OCCC1' ? 104.105 : 60.052;
    const expectedMass = acidMass - (f.basic ? 1.008 : 0);
    close(data.product.molarMass, expectedMass);
    const reagentMass = f.reagent === 'water' ? 18.015 : f.reagent === 'hydroxide' ? 17.007
      : f.reagent === 'sodium-hydroxide' ? 39.997 : 56.105;
    const reagent = data.reactants.find((r) => r.inputSlot === reagentSlot);
    close(reagent.molarMass, reagentMass);
    const amounts = {
      [substrateSlot]: { value: 20, unit: 'mmol' },
      [reagentSlot]: { value: reagentMass * 0.005, unit: 'g' },
    };
    const result = calculateReaction(data, amounts);
    close(result.product.moles, 0.005);
    close(result.product.grams, expectedMass * 0.005);
    assert.deepEqual(result.limitingInputs, [reagentSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const required = calculateRequiredAmounts(data, { value: expectedMass * 0.002, unit: 'g' });
    close(required.product.moles, 0.002);
    for (const r of required.reactants) {
      close(r.moles, 0.002);
      close(r.grams, data.reactants.find((a) => a.inputSlot === r.inputSlot).molarMass * 0.002);
    }
  });
}
