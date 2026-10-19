import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const source = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
const ast = ts.createSourceFile('reaction-lab.ts', source, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
const fn = ast.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === 'updatePathwaySettings');
assert.ok(fn);
const compiled = ts.transpileModule(fn.getText(ast), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
function harness() {
  const state = { extensionConditions: { hidden: true, open: true }, extensionTitle: { textContent: '' }, additionSettings: { hidden: true }, chainSettings: { hidden: true }, diolSettings: { hidden: true } };
  const update = new vm.Script(`${compiled}; updatePathwaySettings;`).runInNewContext(state);
  return { state, update: (mechanisms) => update(mechanisms.map((mechanism) => ({ mechanism }))) };
}

test('unrelated reactions and unresolved/unsupported inputs have no alkyne or chain settings', () => {
  const { state, update } = harness();
  for (const paths of [[], ['SN2', 'E2'], ['SN1', 'E1'], ['Esterification'], ['Hydrogenation'], ['Alkyne hydrogenation'], ['Ester saponification']]) {
    update(paths); assert.equal(state.extensionConditions.hidden, true);
    assert.equal(state.additionSettings.hidden, true); assert.equal(state.chainSettings.hidden, true);
  }
});

test('alkyne addition shows equivalents only; polymerization shows chain length only', () => {
  const { state, update } = harness();
  for (const path of ['Alkyne halogenation', 'Alkyne hydrohalogenation']) {
    update([path]); assert.equal(state.extensionConditions.hidden, false);
    assert.equal(state.additionSettings.hidden, false); assert.equal(state.chainSettings.hidden, true);
    assert.equal(state.extensionTitle.textContent, 'Alkyne addition settings');
  }
  update(['Polymerization model']); assert.equal(state.extensionConditions.hidden, false);
  assert.equal(state.additionSettings.hidden, true); assert.equal(state.chainSettings.hidden, false);
  assert.equal(state.extensionTitle.textContent, 'Finite chain settings');
});

test('changing input immediately hides old settings and preserves the user disclosure preference', () => {
  const { state, update } = harness();
  update(['Polymerization model']); state.extensionConditions.open = false;
  update([]); assert.equal(state.extensionConditions.hidden, true);
  update(['Alkyne halogenation']); assert.equal(state.chainSettings.hidden, true);
  assert.equal(state.extensionConditions.open, false);
  const body = ast.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === 'updateMatches').getText(ast);
  assert.ok(body.indexOf('updatePathwaySettings([])') < body.indexOf("fetch('/api/reactions/match'"));
  assert.ok(body.indexOf('updatePathwaySettings(matches)') > body.indexOf('if (!matches.length)'));
});

test('contextual controls live beside pathway options, not in the general reaction-conditions area', () => {
  assert.ok(source.indexOf('id="reaction-pathway-settings"') > source.indexOf('02 · Matching options'));
  assert.ok(source.indexOf('id="reaction-pathway-settings"') < source.indexOf('id="reaction-options"'));
  assert.match(source, /id="reaction-pathway-settings"[^>]*hidden/);
  assert.doesNotMatch(source, /Alkyne \/ chain model settings/);
  assert.match(source, /new FunctionalGroupPanel/, 'reactant inspection remains available');
  assert.match(source, /\[solventInput, temperatureInput, catalystInput, oxidationStageInput, additionStageInput, polymerUnitsInput, workupInput\]/, 'all settings still invalidate results and recalculate matches');
});
