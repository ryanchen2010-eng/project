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
f=json.loads(Path('tests/fixtures/alkyne-complete-hydrogenation.json').read_text())
rows=[]
for case in f['positive']:
 for reverse in [False,True]:
  a={'smiles':case['substrate']}; b='hydrogen'
  if reverse:a,b=b,a
  for r in s.match_reactions(a,b,{'catalyst':'metal'})['reactionOptions']:
   if r['mechanism']=='Alkyne hydrogenation':rows.append(dict(case=case,reverse=reverse,reaction=r))
controls=[]
for c in [{},{'catalyst':'none'},{'catalyst':'lindlar'},{'catalyst':'acid'},{'catalyst':'radical'},
          {'catalyst':'metal','temperature':'heated'},{'catalyst':'metal','solvent':'aqueous-protic'},
          {'catalyst':'metal','solvent':'polar-aprotic'}]:
 r=next(r for r in s.match_reactions({'smiles':'CC#CC'},'hydrogen',c)['reactionOptions'] if r['mechanism']=='Alkyne hydrogenation')
 controls.append(dict(conditions=c,reaction=r))
pair=s.match_reactions({'smiles':'CC#CC'},'hydrogen',{'catalyst':'lindlar'})['reactionOptions']
print(json.dumps(dict(rows=rows,controls=controls,pair=pair)))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);
for (const { case: c, reverse, reaction } of data.rows) {
  test(`complete alkyne arithmetic and caveats: ${c.label}, reverse=${reverse}, ${reaction.site.siteId}`, () => {
    const basis = reaction.stoichiometry;
    const carbon = (c.substrate.match(/C/g) ?? []).length;
    const oxygen = (c.substrate.match(/O/g) ?? []).length;
    const triples = (c.substrate.match(/#/g) ?? []).length;
    // Independent acyclic inventory after fully reducing exactly ONE site.
    const hydrogen = 2 * carbon + 2 - 4 * (triples - 1);
    const mass = carbon * 12.011 + hydrogen * 1.008 + oxygen * 15.999;
    close(basis.product.molarMass, mass);
    const substrateSlot = reverse ? 1 : 0, hydrogenSlot = 1 - substrateSlot;
    assert.equal(basis.reactants.find((r) => r.inputSlot === hydrogenSlot).coefficient, 2);
    const result = calculateReaction(basis, { [substrateSlot]: { value: 20, unit: 'mmol' }, [hydrogenSlot]: { value: 0.02016, unit: 'g' } });
    close(result.product.moles, 0.005); close(result.product.grams, mass * 0.005);
    assert.deepEqual(result.limitingInputs, [hydrogenSlot]);
    close(result.reactants.find((r) => r.inputSlot === substrateSlot).remainingMoles, 0.015);
    const target = calculateRequiredAmounts(basis, { value: mass * 0.003, unit: 'g' });
    close(target.reactants.find((r) => r.inputSlot === substrateSlot).moles, 0.003);
    close(target.reactants.find((r) => r.inputSlot === hydrogenSlot).moles, 0.006);
    assert.match(basis.context.warning, /Two H2/);
    assert.match(basis.context.warning, /not experimental yields/);
    assert.equal(basis.context.canGenerate3D, !c.bookkeepingOnly);
    assert.equal(reaction.assessment.evidence.canPreview2D, true);
    const accepted = reviewedCalculatorReactions({ reactions: [reaction] });
    assert.equal(accepted.length, 1);
    assert.deepEqual(accepted[0].stoichiometry.context, basis.context);
    const copy = copyCalculationContext(basis.context); copy.conditions.catalyst = 'lindlar';
    assert.equal(basis.context.conditions.catalyst, 'metal');
    if (c.bookkeepingOnly) {
      assert.match(conditionLabel(reaction.assessment), /Competing reductions unresolved/);
      assert.match(basis.context.warning, /one-site equation does not predict/);
    } else assert.match(conditionLabel(reaction.assessment), /Active-metal net model/);
  });
}
for (const row of data.controls) {
  test(`full-reduction conditional amounts stay usable but not certified: ${JSON.stringify(row.conditions)}`, () => {
    const r = row.reaction;
    assert.equal(r.assessment.canRun, false);
    assert.equal(r.stoichiometry.context.canGenerate3D, false);
    assert.notEqual(r.assessment.status, 'disfavored');
    assert.doesNotMatch(conditionLabel(r.assessment), /Acid activation|Unfavorable|teaching example/);
    const accepted = reviewedCalculatorReactions({ reactions: [r] });
    assert.equal(accepted.length, 1);
    const result = calculateReaction(accepted[0].stoichiometry, { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } });
    close(result.product.moles, 0.5);
  });
}
test('same H2 supply gives distinct partial and full theoretical amounts', () => {
  const full = data.pair.find((r) => r.mechanism === 'Alkyne hydrogenation');
  const partial = data.pair.find((r) => r.mechanism === 'Alkyne partial hydrogenation');
  assert.equal(full.productSmiles, 'CCCC'); assert.equal(partial.productSmiles, 'C/C=C\\C');
  const amounts = { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } };
  close(calculateReaction(full.stoichiometry, amounts).product.moles, 0.5);
  close(calculateReaction(partial.stoichiometry, amounts).product.moles, 1);
  assert.equal(full.assessment.canRun, false); assert.equal(partial.assessment.canRun, true);
});
