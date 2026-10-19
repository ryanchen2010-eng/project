import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const read = (p) => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const load = async (p) => import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(await read(p), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText).toString('base64')}`);
const { conditionLabel, conditionGuidance } = await load('src/reaction-conditions.ts');
const { calculateReaction, copyCalculationContext } = await load('src/reaction-calculator.ts');
const rows = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
models=[('Alkyne partial hydrogenation','hydrogen',{'catalyst':'lindlar'}),('Alkyne hydrogenation','hydrogen',{'catalyst':'metal'}),('Alkyne halogenation','bromine',{'solvent':'dry','additionStage':'one'}),('Alkyne hydrohalogenation','hydrogen-bromide',{'solvent':'dry','temperature':'ambient','additionStage':'one'})]
rows=[]
for path,reagent,conditions in models:
 for mode in ['unsupported','missing','valid']:
  c={} if mode=='missing' else dict(conditions,**({'peroxide':True} if mode=='unsupported' else {}))
  r=next(o for o in s.match_reactions({'smiles':'CCC#C'},reagent,c)['reactionOptions'] if o['mechanism']==path)
  rows.append(dict(path=path,mode=mode,reaction=r))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));

for (const row of rows) {
  test(`Phase 4F guidance/calculator confidence: ${row.path} ${row.mode}`, () => {
    const r = row.reaction, e = r.assessment.evidence, context = copyCalculationContext(r.stoichiometry.context);
    assert.equal(e.canPreview2D, true);
    assert.equal(context.canGenerate3D, row.mode === 'valid');
    assert.equal(context.canGenerate3D, e.canGenerate3D);
    assert.match(conditionGuidance(r.assessment), /Structure\/site supported/);
    assert.match(conditionGuidance(r.assessment), row.mode === 'valid' ? /not a verified experimental outcome/ : /Conditional 2D remains available/);
    if (row.mode === 'missing') assert.match(conditionGuidance(r.assessment), /Missing:.*Complete the existing condition fields/);
    if (row.mode === 'unsupported') {
      assert.match(conditionLabel(r.assessment), /peroxide/);
      assert.match(context.warning, /3D is unavailable.*peroxide/);
      assert.doesNotMatch(conditionLabel(r.assessment), /Model conditions match/);
    }
    const result = calculateReaction(r.stoichiometry, { 0: { value: 1, unit: 'mol' }, 1: { value: 1, unit: 'mol' } });
    assert.ok(result.product.moles > 0);
    assert.match(context.warning, /not experimental yields/);
  });
}
test('guidance stays in existing text controls and never creates a competing 3D gate', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.match(source, /conditionAssessment\.textContent \+=.*conditionGuidance/);
  assert.match(source, /control\.title = guidance/);
  const controls = source.slice(source.indexOf('function updatePreviewActions()'), source.indexOf('function setPreview('));
  assert.match(controls, /assessment\?\.canRun !== false/);
  assert.doesNotMatch(controls, /conditionCompleteness.*===/);
});
test('unknown field messages are inserted as text, not executable HTML', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.match(source, /conditionAssessment\.textContent/);
  assert.doesNotMatch(source, /conditionAssessment\.innerHTML/);
  const text = conditionGuidance({ state: 'incomplete', note: '<img onerror=bad>', evidence: { missingRequiredSettings: [], canGenerate3D: false } });
  assert.ok(text.includes('<img onerror=bad>'));
});
