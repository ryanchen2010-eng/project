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

const rows = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/alkyne-partial-hydrogenation.json').read_text())
rows=[]
for case in f['positive']:
 for reverse in [False,True]:
  a={'smiles':case['substrate']};b='hydrogen'
  if reverse:a,b=b,a
  for r in s.match_reactions(a,b,{'catalyst':'lindlar'})['reactionOptions']:
   if r['mechanism']=='Alkyne partial hydrogenation': rows.append(dict(case=case,reverse=reverse,reaction=r))
for c in [{},{'catalyst':'none'},{'catalyst':'metal'},{'catalyst':'radical'},{'catalyst':'lindlar','temperature':'heated'}]:
 r=next(r for r in s.match_reactions({'smiles':'CC#CC'},'hydrogen',c)['reactionOptions'] if r['mechanism']=='Alkyne partial hydrogenation')
 rows.append(dict(condition=c,reaction=r))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);
for (const row of rows.filter((r) => r.case)) {
  const { reaction, case: c, reverse } = row;
  test(`Lindlar amounts/context: ${c.label}, reverse=${reverse}, ${reaction.site.siteId}`, () => {
    const basis = reaction.stoichiometry;
    // Independent element inventory for these acyclic C/H/O fixtures:
    // one alkyne loses one unsaturation unit; all other triple bonds stay.
    const carbon = (c.substrate.match(/C/g) ?? []).length;
    const oxygen = (c.substrate.match(/O/g) ?? []).length;
    const triples = (c.substrate.match(/#/g) ?? []).length;
    const hydrogen = 2 * carbon - 4 * (triples - 1);
    const mass = carbon * 12.011 + hydrogen * 1.008 + oxygen * 15.999;
    const substrateSlot = reverse ? 1 : 0, hydrogenSlot = 1 - substrateSlot;
    close(basis.product.molarMass, mass);
    close(basis.reactants.find((r) => r.inputSlot === hydrogenSlot).molarMass, 2.016);
    assert.deepEqual(basis.reactants.map((r) => r.coefficient), [1, 1]);
    const result = calculateReaction(basis, { [substrateSlot]: { value: 20, unit: 'mmol' }, [hydrogenSlot]: { value: 0.01008, unit: 'g' } });
    close(result.product.moles, 0.005); close(result.product.grams, mass * 0.005);
    assert.deepEqual(result.limitingInputs, [hydrogenSlot]);
    const required = calculateRequiredAmounts(basis, { value: mass * 0.002, unit: 'g' });
    for (const r of required.reactants) close(r.moles, 0.002);
    assert.match(basis.context.warning, /not experimental yields/);
    assert.match(basis.context.warning, /over-reduction/);
    assert.equal(basis.context.conditions.catalyst, 'lindlar');
    if (reaction.alkynePartialStereo.singleSiteBookkeepingOnly) {
      assert.equal(basis.context.canGenerate3D, false);
      assert.match(basis.context.warning, /Competing alkyne sites/);
      assert.match(conditionLabel(reaction.assessment), /conditional 2D only/);
    } else {
      assert.match(conditionLabel(reaction.assessment), /Lindlar net model/);
      assert.match(conditionLabel(reaction.assessment), /not validated/);
    }
    const accepted = reviewedCalculatorReactions({ reactions: [reaction] });
    assert.equal(accepted.length, 1);
    assert.deepEqual(accepted[0].stoichiometry.context, basis.context);
    const copied = copyCalculationContext(basis.context); copied.conditions.catalyst = 'metal';
    assert.equal(basis.context.conditions.catalyst, 'lindlar');
  });
}
for (const row of rows.filter((r) => r.condition)) {
  test(`blocked Lindlar conditions retain hypothetical arithmetic: ${JSON.stringify(row.condition)}`, () => {
    const r = row.reaction, context = r.stoichiometry.context;
    assert.equal(context.canGenerate3D, false);
    assert.equal(r.assessment.evidence.canPreview2D, true);
    assert.notEqual(r.assessment.status, 'disfavored');
    assert.doesNotMatch(conditionLabel(r.assessment), /Acid activation|fit the example/);
    const copied = reviewedCalculatorReactions({ reactions: [r] })[0].stoichiometry;
    assert.deepEqual(copied.context, context);
    const result = calculateReaction(copied, { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } });
    close(result.product.moles, 1);
  });
}
test('existing guide no longer claims Lindlar is terminal-only', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.doesNotMatch(source, /Lindlar is supported for terminal alkynes/);
  assert.match(source, /validated internal cis\/Z alkene/);
});
