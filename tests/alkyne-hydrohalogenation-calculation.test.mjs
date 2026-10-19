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
f=json.loads(Path('tests/fixtures/alkyne-hydrohalogenation.json').read_text());rows=[]
for case in f['positive']:
 for symbol,reagent in [('Cl','hydrogen-chloride'),('Br','hydrogen-bromide'),('I','hydrogen-iodide')]:
  for stage in ['one','two']:
   for reverse in [False,True]:
    a={'smiles':case['substrate']};b=reagent
    if reverse:a,b=b,a
    for r in s.match_reactions(a,b,{'solvent':'dry','temperature':'ambient','additionStage':stage})['reactionOptions']:
     if r['mechanism']=='Alkyne hydrohalogenation':rows.append(dict(case=case,symbol=symbol,stage=stage,reverse=reverse,reaction=r))
controls=[]
for c in [{},{'additionStage':'one'},{'solvent':'dry','additionStage':'one'},{'solvent':'dry','temperature':'ambient'},
          {'solvent':'aqueous-protic','temperature':'ambient','additionStage':'one'},
          {'solvent':'ethanolic-protic','temperature':'ambient','additionStage':'two'},
          {'solvent':'polar-aprotic','temperature':'ambient','additionStage':'one'},
          {'solvent':'dry','temperature':'ambient','additionStage':'one','catalyst':'radical'},
          {'solvent':'dry','temperature':'heated','additionStage':'two'}]:
 r=next(r for r in s.match_reactions({'smiles':'CCC#C'},'hydrogen-bromide',c)['reactionOptions'] if r['mechanism']=='Alkyne hydrohalogenation')
 controls.append(dict(conditions=c,reaction=r))
print(json.dumps(dict(rows=rows,controls=controls)))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }));
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);
const atomic = { Cl: 35.453, Br: 79.904, I: 126.904 };
for (const { case: c, symbol, stage, reverse, reaction: r } of data.rows) {
  test(`alkyne HX amounts: ${c.label}, H${symbol}, ${stage}, reversed=${reverse}, ${r.site.siteId}`, () => {
    const n = stage === 'one' ? 1 : 2, basis = r.stoichiometry;
    const carbon = (c.substrate.match(/C/g) ?? []).length;
    const oxygen = (c.substrate.match(/O/g) ?? []).length;
    const triples = (c.substrate.match(/#/g) ?? []).length;
    // Independent acyclic graph inventory: HX adds exactly ONE H and ONE X per equivalent.
    const mass = carbon * 12.011 + (2 * carbon + 2 - 4 * triples + n) * 1.008 + oxygen * 15.999 + n * atomic[symbol];
    close(basis.product.molarMass, mass);
    const substrateSlot = reverse ? 1 : 0, hxSlot = 1 - substrateSlot;
    assert.equal(basis.reactants.find((v) => v.inputSlot === hxSlot).coefficient, n);
    close(basis.reactants.find((v) => v.inputSlot === hxSlot).molarMass, 1.008 + atomic[symbol]);
    const result = calculateReaction(basis, { [substrateSlot]: { value: 20, unit: 'mmol' }, [hxSlot]: { value: 0.01 * (1.008 + atomic[symbol]), unit: 'g' } });
    close(result.product.moles, 0.01 / n); close(result.product.grams, mass * 0.01 / n);
    assert.deepEqual(result.limitingInputs, [hxSlot]);
    close(result.reactants.find((v) => v.inputSlot === substrateSlot).remainingMoles, 0.02 - 0.01 / n);
    const required = calculateRequiredAmounts(basis, { value: mass * 0.003, unit: 'g' });
    close(required.reactants.find((v) => v.inputSlot === hxSlot).moles, n * 0.003);
    assert.match(basis.context.warning, /not actual supply or stopping/);
    assert.match(basis.context.warning, /Regioisomers are alternatives, not additive yields/);
    assert.match(basis.context.warning, /not experimental yields/);
    const allowed = !c.oxygen && !c.bookkeepingOnly && symbol !== 'Cl' && !(stage === 'one' && c.internal) && !(symbol === 'I' && stage === 'two');
    assert.equal(basis.context.canGenerate3D, Boolean(allowed));
    assert.deepEqual(copyCalculationContext(basis.context), basis.context);
    assert.equal(reviewedCalculatorReactions({ reactions: [r] }).length, 1);
    assert.doesNotMatch(conditionLabel(r.assessment), /Unfavorable|Strong match|teaching example/);
    if (c.oxygen || c.bookkeepingOnly) assert.match(basis.context.warning, /conditional bookkeeping only/);
    assert.ok(r.assessment.evidence.unknownConditions.includes('radical initiation absence'));
  });
}
for (const { conditions, reaction: r } of data.controls) {
  test(`incomplete HX conditions retain theoretical amounts with qualification: ${JSON.stringify(conditions)}`, () => {
    assert.equal(r.assessment.canRun, false); assert.equal(r.stoichiometry.context.canGenerate3D, false);
    assert.notEqual(r.assessment.status, 'disfavored');
    assert.match(conditionLabel(r.assessment), /missing|unresolved/i);
    const count = conditions.additionStage === 'two' ? 2 : 1;
    close(calculateReaction(r.stoichiometry, { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } }).product.moles, 1 / count);
  });
}
test('existing page clears stale reaction, diagram, model and amount state on inputs/conditions', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.match(source, /for \(const select of \[solventInput, temperatureInput, catalystInput, oxidationStageInput, additionStageInput/);
  assert.match(source, /canRun/); assert.match(source, /clear|reset|invalidate/i);
});
