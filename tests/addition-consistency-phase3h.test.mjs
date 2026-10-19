import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const read = (p) => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const compile = (s) => ts.transpileModule(s, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = (s) => `data:text/javascript;base64,${Buffer.from(s).toString('base64')}`;
const arithmeticUrl = url(compile(await read('src/reaction-calculator.ts')));
const panelUrl = url(compile(await read('src/reaction-calculator-panel.ts')).replace(/from ['"]\.\/reaction-calculator['"]/, `from '${arithmeticUrl}'`));
const catalogUrl = url(compile(await read('src/calculator-reactions.ts')).replace(/import ['"]\.\/reaction-calculator\.css['"];?/, '')
  .replace(/from ['"]\.\/reaction-calculator['"]/, `from '${arithmeticUrl}'`)
  .replace(/from ['"]\.\/reaction-calculator-panel['"]/, `from '${panelUrl}'`));
const { copyCalculationContext, calculateReaction } = await import(arithmeticUrl);
const { ReactionCalculatorPanel } = await import(panelUrl);
const { reviewedCalculatorReactions, mountReactionAmounts } = await import(catalogUrl);
const { conditionLabel, reactionOptionSummary } = await import(url(compile(await read('src/reaction-conditions.ts'))));

const context = () => ({ version: 1, assertionLevel: 'conditional-net', pathway: 'Alkene dihydroxylation',
  label: 'Required model settings missing: workup', conditionStatus: 'missing', conditions: { catalyst: 'osmium', workup: '' },
  missingRequiredSettings: ['workup'], unknownConditions: ['solvent', 'temperature'], canGenerate3D: false,
  assumptions: ['Os cycling and release species are omitted.'], warning: 'Conditional net-equation amounts only; complete conversion is assumed, not predicted.' });
const basis = () => ({ balanced: true, reactants: [{ inputSlot: 0, name: 'Ethene', formula: 'C2H4', molarMass: 28.054, coefficient: 1 },
  { inputSlot: 1, name: 'Hydrogen peroxide', formula: 'H2O2', molarMass: 34.014, coefficient: 1 }],
  product: { name: 'Ethane-1,2-diol', formula: 'C2H6O2', molarMass: 62.068, coefficient: 1 }, excludedInputs: [], notes: [], context: context() });

class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.children = []; this.attributes = new Map(); this.listeners = new Map();
    this.className = ''; this.id = ''; this.hidden = false; this.open = false; this.value = ''; this.text = '';
    this.classList = { add: (...names) => { this.className += ` ${names.join(' ')}`; } };
  }
  set textContent(v) { this.text = String(v); this.children = []; }
  get textContent() { return this.text + this.children.map((c) => c.textContent).join(' '); }
  get valueAsNumber() { return Number(this.value); }
  set innerHTML(v) { throw new Error(`Unsafe HTML ${v}`); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = []; this.text = ''; this.append(...nodes); }
  setAttribute(k, v) { this.attributes.set(k, String(v)); }
  getAttribute(k) { return this.attributes.get(k); }
  addEventListener(k, f) { this.listeners.set(k, [...(this.listeners.get(k) ?? []), f]); }
  emit(k) { for (const f of this.listeners.get(k) ?? []) f({ target: this, preventDefault() {} }); }
}
const descendants = (e) => e.children.flatMap((c) => [c, ...descendants(c)]);
const find = (e, f) => { const result = descendants(e).find(f); assert.ok(result); return result; };
const byClass = (e, name) => find(e, (n) => n.className.split(/\s+/).includes(name));
const byId = (e, id) => find(e, (n) => n.id === id);
async function dom(run) {
  const old = globalThis.document;
  globalThis.document = { createElement: (tag) => new Element(tag) };
  try { return await run(); } finally { globalThis.document = old; }
}

test('new condition evidence overrides ambiguous legacy labels', () => {
  const a = { state: 'aligned', status: 'model-match', note: '', evidence: { label: 'Release assumed · solvent not evaluated' } };
  assert.equal(conditionLabel(a), a.evidence.label);
});
test('missing required workup is not called a comparison mismatch', () => {
  assert.match(conditionLabel({ status: 'missing', evidence: { label: context().label } }), /Required model settings missing: workup/);
});
test('option count does not call two stereoisomers two mechanisms', () => {
  const summary = reactionOptionSummary([{ mechanism: 'Bromination' }, { mechanism: 'Bromination' }]);
  assert.match(summary, /2 net product options across 1 mechanism/);
  assert.doesNotMatch(summary, /two pathways|may compete|50:50/);
});
test('different mechanisms remain distinguishable from options', () => {
  assert.match(reactionOptionSummary([{ mechanism: 'SN1' }, { mechanism: 'E1' }]), /2 mechanisms/);
});
test('context is copied without aliasing selected conditions or assumptions', () => {
  const source = context(), copy = copyCalculationContext(source);
  source.conditions.workup = 'aqueous-release'; source.assumptions.push('changed'); source.missingRequiredSettings.pop();
  assert.equal(copy.conditions.workup, ''); assert.equal(copy.assumptions.length, 1); assert.deepEqual(copy.missingRequiredSettings, ['workup']);
});
for (const [label, mutate] of [
  ['unknown version', (c) => { c.version = 2; }], ['asserted outcome', (c) => { c.assertionLevel = 'guaranteed-product'; }],
  ['missing warning', (c) => { delete c.warning; }], ['nonboolean permission', (c) => { c.canGenerate3D = 'true'; }],
  ['malformed assumptions', (c) => { c.assumptions = {}; }], ['malformed conditions', (c) => { c.conditions = []; }],
  ['malformed missing requirements', (c) => { c.missingRequiredSettings = [null]; }],
  ['oversized field', (c) => { c.label = 'x'.repeat(1001); }],
]) {
  test(`malformed context fails closed: ${label}`, () => {
    const c = context(); mutate(c); assert.throws(() => copyCalculationContext(c), /context is invalid/);
    const b = basis(); b.context = c;
    assert.equal(reviewedCalculatorReactions({ reactions: [{ id: 'test', name: 'Diol', stoichiometry: b }] }).length, 0);
  });
}
test('balanced catalog preserves condition context instead of stripping it', () => {
  const b = basis(); const reactions = reviewedCalculatorReactions({ reactions: [{ id: 'diol', name: 'Diol', stoichiometry: b }] });
  assert.deepEqual(reactions[0].stoichiometry.context, b.context);
  b.context.label = 'Later mutation'; assert.notEqual(reactions[0].stoichiometry.context.label, 'Later mutation');
});
test('conditional metadata does not change theoretical arithmetic or peroxide mass', () => {
  const b = basis(); const amounts = { 0: { value: 10, unit: 'mmol' }, 1: { value: 34.014 * 0.005, unit: 'g' } };
  const withContext = calculateReaction(b, amounts); delete b.context;
  assert.deepEqual(withContext, calculateReaction(b, amounts));
  assert.ok(Math.abs(withContext.product.grams - 62.068 * 0.005) < 1e-12);
});
test('calculator warning remains visible outside collapsed assumptions', async () => dom(() => {
  const host = new Element('details'), panel = new ReactionCalculatorPanel(host);
  panel.setReaction(basis());
  const notes = byClass(host, 'calculator-notes');
  assert.match(notes.textContent, /Required model settings missing: workup/);
  assert.match(notes.textContent, /assumed, not predicted/);
  assert.match(notes.textContent, /solvent, temperature/);
  assert.equal(byClass(host, 'calculator-assumptions').open, false);
  assert.ok(!descendants(byClass(host, 'calculator-assumptions')).includes(notes));
}));
test('calculator clears old conditional context with selection and clear', async () => dom(() => {
  const host = new Element('details'), panel = new ReactionCalculatorPanel(host);
  panel.setReaction(basis());
  const b = basis(); b.context.conditions.workup = 'aqueous-release'; b.context.missingRequiredSettings = [];
  b.context.label = 'Release assumed · solvent not evaluated'; b.context.canGenerate3D = true;
  panel.setReaction(b);
  assert.match(byClass(host, 'calculator-notes').textContent, /Release assumed/);
  assert.doesNotMatch(byClass(host, 'calculator-notes').textContent, /Required model settings missing/);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  panel.setReaction();
  assert.equal(host.hidden, true); assert.equal(byClass(host, 'calculator-notes').textContent, '');
}));
test('external-looking confidence text remains literal, never HTML', async () => dom(() => {
  const host = new Element('details'), panel = new ReactionCalculatorPanel(host), b = basis();
  b.context.label = '<img onerror=bad>'; panel.setReaction(b);
  assert.match(byClass(host, 'calculator-notes').textContent, /<img onerror=bad>/);
}));
test('standalone reaction calculator displays the carried warning', async () => dom(async () => {
  const old = globalThis.fetch;
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ reactions: [{ id: 'diol', name: 'Diol', stoichiometry: basis() }] }) });
  try {
    const host = new Element('section'); host.id = 'test'; mountReactionAmounts(host);
    await new Promise((resolve) => setImmediate(resolve));
    const select = byId(host, 'test-reaction'); select.value = 'diol'; select.emit('change');
    assert.match(byClass(host, 'calculator-notes').textContent, /Required model settings missing: workup/);
    assert.match(byClass(host, 'calculator-notes').textContent, /assumed, not predicted/);
  } finally { globalThis.fetch = old; }
}));
test('frontend uses canonical options and qualified confidence, preserving existing controls', async () => {
  const s = await read('src/reaction-lab.ts');
  assert.match(s, /matches = payload\.reactionOptions \?\? payload\.reactions/);
  assert.match(s, /assessment\?\.evidence/);
  assert.match(s, /setStatus\(reactionOptionSummary\(matches\)\)/);
  assert.match(s, /conditional net-model structure, not a predicted reaction outcome/);
  assert.match(s, /reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
});
test('reasoning type includes the actual server label and comparisons count options', async () => {
  const s = await read('src/pathway-insights.ts');
  assert.match(s, /label: 'Model conditions match'/);
  assert.match(s, /net product options/);
  assert.match(s, /Why This Option/);
});

const real = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
from scripts.audit_addition_consistency import MODELS
print(json.dumps([dict(id=p,name=p,stoichiometry=s.match_reactions({'smiles':'C=CC'},r,c)['reactionOptions'][0]['stoichiometry']) for p,(r,c) in MODELS.items()]))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
for (const r of real) {
  test(`actual ${r.id} context survives catalog parsing`, () => {
    const parsed = reviewedCalculatorReactions({ reactions: [r] });
    assert.equal(parsed.length, 1);
    assert.deepEqual(parsed[0].stoichiometry.context, r.stoichiometry.context);
    assert.equal(parsed[0].stoichiometry.context.assertionLevel, 'conditional-net');
  });
}
