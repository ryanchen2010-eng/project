import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const read = (p) => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const compile = (s) => ts.transpileModule(s, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = (s) => `data:text/javascript;base64,${Buffer.from(s).toString('base64')}`;
const arithmetic = url(compile(await read('src/reaction-calculator.ts')));
const panel = url(compile(await read('src/reaction-calculator-panel.ts')).replace(/from ['"]\.\/reaction-calculator['"]/, `from '${arithmetic}'`));
const catalog = url(compile(await read('src/calculator-reactions.ts')).replace(/import ['"]\.\/reaction-calculator\.css['"];?/, '')
  .replace(/from ['"]\.\/reaction-calculator['"]/, `from '${arithmetic}'`).replace(/from ['"]\.\/reaction-calculator-panel['"]/, `from '${panel}'`));
const { calculateReaction, calculateRequiredAmounts, copyCalculationContext } = await import(arithmetic);
const { reviewedCalculatorReactions } = await import(catalog);
const { conditionLabel } = await import(url(compile(await read('src/reaction-conditions.ts'))));
const data = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/alkyne-halogenation.json').read_text())
rows=[]
for case in f['positive']:
 for halogen,reagent in [('Br','bromine'),('Cl','chlorine')]:
  for stage in ['one','two']:
   for reverse in [False,True]:
    a={'smiles':case['substrate']}; b=reagent
    if reverse:a,b=b,a
    for r in s.match_reactions(a,b,{'solvent':'dry','additionStage':stage})['reactionOptions']:
     if r['mechanism']=='Alkyne halogenation':rows.append(dict(case=case,halogen=halogen,stage=stage,reverse=reverse,reaction=r))
controls=[]
for c in [{},{'solvent':'dry'},{'additionStage':'one'},{'solvent':'aqueous-protic','additionStage':'one'},
          {'solvent':'ethanolic-protic','additionStage':'two'},{'solvent':'polar-aprotic','additionStage':'one'},
          {'solvent':'dry','additionStage':'one','catalyst':'radical'}, {'solvent':'dry','additionStage':'two','temperature':'heated'}]:
 r=next(r for r in s.match_reactions({'smiles':'CC#CC'},'bromine',c)['reactionOptions'] if r['mechanism']=='Alkyne halogenation')
 controls.append(dict(conditions=c,reaction=r))
print(json.dumps(dict(rows=rows,controls=controls)))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }));
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);
for (const { case: c, halogen, stage, reverse, reaction: r } of data.rows) {
  test(`alkyne X2 amounts: ${c.label}, ${halogen}, ${stage}, reversed=${reverse}, ${r.site.siteId}`, () => {
    const basis = r.stoichiometry, count = stage === 'one' ? 1 : 2;
    // Independent C/H/O acyclic graph inventory: X2 adds NO H.
    const carbon = (c.substrate.match(/C/g) ?? []).length;
    const oxygen = (c.substrate.match(/O/g) ?? []).length;
    const triples = (c.substrate.match(/#/g) ?? []).length;
    const mass = carbon * 12.011 + (2 * carbon + 2 - 4 * triples) * 1.008 + oxygen * 15.999 + count * 2 * (halogen === 'Br' ? 79.904 : 35.453);
    close(basis.product.molarMass, mass);
    const substrateSlot = reverse ? 1 : 0, xSlot = 1 - substrateSlot;
    assert.equal(basis.reactants.find((v) => v.inputSlot === xSlot).coefficient, count);
    const result = calculateReaction(basis, { [substrateSlot]: { value: 20, unit: 'mmol' }, [xSlot]: { value: 0.01 * 2 * (halogen === 'Br' ? 79.904 : 35.453), unit: 'g' } });
    close(result.product.moles, 0.01 / count); close(result.product.grams, mass * 0.01 / count);
    assert.deepEqual(result.limitingInputs, [xSlot]);
    close(result.reactants.find((v) => v.inputSlot === substrateSlot).remainingMoles, 0.02 - 0.01 / count);
    const required = calculateRequiredAmounts(basis, { value: mass * 0.003, unit: 'g' });
    close(required.reactants.find((v) => v.inputSlot === xSlot).moles, count * 0.003);
    assert.match(basis.context.warning, /actual supply, stopping/);
    assert.match(basis.context.warning, /not experimental yields/);
    assert.deepEqual(copyCalculationContext(basis.context), basis.context);
    assert.equal(reviewedCalculatorReactions({ reactions: [r] }).length, 1);
    const permitted = !c.bookkeepingOnly && (halogen === 'Br' || stage === 'two' && !c.oxygen);
    assert.equal(basis.context.canGenerate3D, Boolean(permitted));
    if (c.bookkeepingOnly) assert.match(basis.context.warning, /selective one-site conversion/);
    assert.doesNotMatch(conditionLabel(r.assessment), /Unfavorable|teaching example|Acid activation/);
  });
}
for (const { conditions, reaction: r } of data.controls) {
  test(`incomplete/capture X2 amounts remain explicitly hypothetical: ${JSON.stringify(conditions)}`, () => {
    assert.equal(r.assessment.canRun, false);
    assert.equal(r.stoichiometry.context.canGenerate3D, false);
    assert.notEqual(r.assessment.status, 'disfavored');
    assert.match(conditionLabel(r.assessment), /missing|unresolved/i);
    const count = conditions.additionStage === 'two' ? 2 : 1;
    close(calculateReaction(r.stoichiometry, { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } }).product.moles, 1 / count);
  });
}
test('existing selectors invalidate diagrams, amounts and 3D on stage/reagent/condition edits', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.match(source, /for \(const select of \[solventInput, temperatureInput, catalystInput, oxidationStageInput, additionStageInput/);
  assert.match(source, /canRun/);
  assert.match(source, /reset|clear|invalidate/i);
  assert.match(source, /alkyne-halogenation.*solvent: 'dry'.*additionStage: 'one'/);
});
