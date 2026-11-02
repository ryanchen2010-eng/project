import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const read = p => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const compile = s => ts.transpileModule(s, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const load = async p => import(`data:text/javascript;base64,${Buffer.from(compile(await read(p))).toString('base64')}`);
const { GuidedConditionsPanel, guidedControlValues } = await load('src/guided-reaction-conditions.ts');
const { calculateReaction, copyCalculationContext } = await load('src/reaction-calculator.ts');
const source = await read('src/reaction-lab.ts');
const cases = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
p={'secondaryOxidationProfile':'naocl-acetic-ketone-v1','solvent':'aqueous-protic','temperature':'ambient','catalyst':'none','oxidationStage':'first'}
cases=[('missing','CC(O)C',{},'sodium-hypochlorite'),('water','CC(O)C',{'solvent':'aqueous-protic'},'sodium-hypochlorite'),
 ('qualified','CC(O)C',p,'sodium-hypochlorite'),('conflict','CC(O)C',{'solvent':'dry','temperature':'heated','catalyst':'acid','oxidationStage':'further','workup':'aqueous-release'},'sodium-hypochlorite'),
 ('primary','CCO',p,'sodium-hypochlorite'),('ether','COCCCC(O)C',p,'sodium-hypochlorite'),('aromatic','CC(O)c1ccccc1',p,'sodium-hypochlorite'),
 ('potassium','CC(O)C',p,{'smiles':'[K+].[O-]Cl'}),('unknown','CC(O)C',{**p,'peroxide':True},'sodium-hypochlorite'),
 ('heptanol','CCCC(O)CCC',p,'sodium-hypochlorite'),('cyclic','OC1CCCCCC1',p,'sodium-hypochlorite')]
print(json.dumps({name:next(r for r in s.match_reactions({'smiles':substrate},reagent,conditions)['reactionOptions'] if r['mechanism']=='Alcohol oxidation') for name,substrate,conditions,reagent in cases}))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }));

class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {}; this.attributes = {}; this.disabled = false; this.checked = false; this.hidden = false; this._text = ''; }
  set textContent(s) { this._text = String(s); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  set innerHTML(_) { throw new Error('Do not render guidance with innerHTML'); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  setAttribute(k, v) { this.attributes[k] = v; }
  addEventListener(name, fn) { (this.listeners[name] ??= []).push(fn); }
  async emit(name) { await Promise.all((this.listeners[name] ?? []).map(fn => fn({ target: this }))); }
}
const all = host => host.children.flatMap(c => [c, ...all(c)]);
const byTag = (host, tag) => all(host).find(c => c.tagName === tag.toUpperCase());
const g = name => cases[name].guidedConditions;
async function fixture(fn, apply = async () => {}) {
  const previous = globalThis.document;
  globalThis.document = { createElement: tag => new Element(tag) };
  try {
    const host = new Element('section');
    await fn({ host, panel: new GuidedConditionsPanel(host, apply) });
  } finally {
    if (previous === undefined) delete globalThis.document; else globalThis.document = previous;
  }
}

test('guidance never automatically applies or generates anything', async () => {
  const calls = [];
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'initial');
    assert.equal(calls.length, 0); assert.equal(host.hidden, false);
    assert.equal(byTag(host, 'button').type, 'button');
    assert.equal(byTag(host, 'input'), undefined);
    assert.match(host.textContent, /Missing required settings/);
    assert.match(host.textContent, /Review supported settings/);
    assert.equal(all(host).filter(e => e.tagName === 'SELECT').length, 0);
  }, async (...args) => calls.push(args));
});

test('explicit apply passes the exact backend suggestion and context to revalidation', async () => {
  const calls = [];
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'structure-and-condition-signature');
    await byTag(host, 'button').emit('click');
    assert.equal(calls.length, 1); assert.equal(calls[0][0], g('missing'));
    assert.equal(calls[0][1], 'structure-and-condition-signature');
  }, async (...args) => calls.push(args));
});

for (const name of ['water', 'conflict']) test(`${name}: explicit selections require a separate replacement confirmation`, async () => {
  let calls = 0;
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g(name), 'context');
    const button = byTag(host, 'button'), check = byTag(host, 'input');
    assert.equal(button.disabled, true); assert.equal(check.checked, false);
    assert.match(host.textContent, /replace the selected settings/i);
    await button.emit('click'); assert.equal(calls, 0);
    check.checked = true; await check.emit('change'); assert.equal(button.disabled, false);
    check.checked = false; await check.emit('change'); assert.equal(button.disabled, true);
    check.checked = true; await check.emit('change'); await button.emit('click'); assert.equal(calls, 1);
  }, async () => { calls += 1; });
});

for (const name of ['qualified', 'primary', 'ether', 'aromatic', 'potassium', 'unknown']) {
  test(`${name}: backend non-applicable states never render an apply button`, async () => fixture(async ({ host, panel }) => {
    panel.setGuidance(g(name), 'context');
    assert.equal(byTag(host, 'button'), undefined); assert.equal(byTag(host, 'input'), undefined);
    assert.equal(host.hidden, false); assert.ok(host.textContent.includes(g(name).message));
    if (name === 'primary') assert.match(host.textContent, /PCC and Dess–Martin are not implemented/);
  }, async () => assert.fail('No apply handler may run')));
}

test('clearing a reaction removes the pilot and invalidates detached actions', async () => {
  let calls = 0;
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'old'); const old = byTag(host, 'button');
    panel.clear(); assert.equal(host.hidden, true); assert.equal(host.children.length, 0);
    await old.emit('click'); assert.equal(calls, 0);
    panel.setGuidance(undefined, 'unrelated'); assert.equal(host.hidden, true);
  }, async () => { calls += 1; });
});

test('changing structure or conditions invalidates an old suggestion even if its button is retained', async () => {
  let calls = 0;
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'old'); const old = byTag(host, 'button');
    panel.setGuidance(g('primary'), 'new'); await old.emit('click');
    assert.equal(calls, 0); assert.match(host.textContent, /No validated profile implemented/);
  }, async () => { calls += 1; });
});

test('double submission cannot apply a preset twice while revalidation is pending', async () => {
  let release, calls = 0;
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'current'); const button = byTag(host, 'button');
    const first = button.emit('click'); await Promise.resolve(); await button.emit('click');
    assert.equal(calls, 1); assert.equal(button.disabled, true); release(); await first;
  }, async () => { calls += 1; await new Promise(resolve => { release = resolve; }); });
});

test('revalidation failure remains explicit and does not announce qualified chemistry', async () => fixture(async ({ host, panel }) => {
  panel.setGuidance(g('missing'), 'current'); await byTag(host, 'button').emit('click');
  assert.match(host.textContent, /Backend unavailable/); assert.equal(byTag(host, 'button').disabled, false);
  assert.doesNotMatch(host.textContent, /Model conditions match/);
}, async () => { throw new Error('Backend unavailable'); }));

test('a delayed old failure cannot replace newly rendered qualified guidance', async () => {
  let reject;
  await fixture(async ({ host, panel }) => {
    panel.setGuidance(g('missing'), 'old'); const pending = byTag(host, 'button').emit('click');
    panel.setGuidance(g('qualified'), 'new'); reject(new Error('old failure')); await pending;
    assert.match(host.textContent, /Model conditions match/); assert.doesNotMatch(host.textContent, /old failure/);
  }, async () => { await new Promise((_, no) => { reject = no; }); });
});

test('guidance text is inert text, and reference links use safe attributes', async () => fixture(async ({ host, panel }) => {
  panel.setGuidance({ ...g('missing'), title: '<img src=x onerror=alert(1)>', limitations: ['<script>wrong()</script>'] }, 'ctx');
  assert.ok(host.textContent.includes('<img')); assert.equal(byTag(host, 'img'), undefined);
  const link = byTag(host, 'a'); assert.equal(link.target, '_blank'); assert.equal(link.rel, 'noopener noreferrer');
  panel.setGuidance({ ...g('missing'), sourceUrl: 'javascript:alert(1)' }, 'ctx'); assert.equal(byTag(host, 'a'), undefined);
}));

test('canonical server settings map to the existing medium select without extra selectors', () => {
  const controls = guidedControlValues(g('missing'));
  assert.deepEqual(controls, { solvent: 'secondary-naocl-acetic', temperature: 'ambient', catalyst: 'none', oxidationStage: 'first' });
  assert.deepEqual(guidedControlValues(g('conflict')), { ...controls, workup: '' });
  assert.equal(Object.hasOwn(controls, 'secondaryOxidationProfile'), false);
});

test('transport parsing rejects non-applicable guidance or unknown UI fields', () => {
  for (const name of ['qualified', 'primary', 'ether', 'unknown']) assert.throws(() => guidedControlValues(g(name)));
  for (const targetConditions of [
    { ...g('missing').targetConditions, secondaryOxidationProfile: 'PCC' },
    { ...g('missing').targetConditions, pressure: 'unknown' },
    { ...g('missing').targetConditions, solvent: 'dry' },
  ]) assert.throws(() => guidedControlValues({ ...g('missing'), targetConditions }));
});

function extracted(name) {
  const start = source.indexOf(`async function ${name}(`);
  assert.ok(start >= 0); return compile(source.slice(start, source.indexOf('\n}', start) + 2));
}
function application(currentSignature = 'current') {
  const values = { solvent: 'dry', temperature: 'heated', catalyst: 'acid', oxidationStage: 'further', workup: 'aqueous-release' };
  const choices = { solvent: ['', 'dry', 'aqueous-protic', 'secondary-naocl-acetic'], temperature: ['', 'ambient', 'heated'], catalyst: ['', 'none', 'acid'], oxidationStage: ['', 'first', 'further'], workup: ['', 'aqueous-release'] };
  const controls = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, { value, options: choices[key].map(value => ({ value })) }]));
  const calls = [];
  const run = new Function('guidanceSignature', 'guidedControlValues', 'solventInput', 'temperatureInput', 'catalystInput', 'oxidationStageInput', 'workupInput', 'saveDraft', 'updateMatches', `let namedProfileSelection = null; const clearNamedProfile = {hidden:true}; ${extracted('applyGuidedConditions')};return applyGuidedConditions;`)(
    () => currentSignature, guidedControlValues, ...Object.values(controls), () => calls.push('saved'), async id => calls.push(['revalidate', id]));
  return { controls, calls, run };
}

test('Reaction Lab applies all reviewed settings then refreshes and reselects the same backend site', async () => {
  const { controls, calls, run } = application(); await run(g('conflict'), 'current');
  assert.deepEqual(Object.fromEntries(Object.entries(controls).map(([key, select]) => [key, select.value])), guidedControlValues(g('conflict')));
  assert.deepEqual(calls, ['saved', ['revalidate', g('conflict').reactionId]]);
});

test('Reaction Lab refuses stale structure/condition suggestions without changing any field', async () => {
  const { controls, calls, run } = application('changed'); const before = JSON.stringify(controls);
  await assert.rejects(run(g('missing'), 'old'), /changed/);
  assert.equal(JSON.stringify(controls), before); assert.deepEqual(calls, []);
});

test('suggestion signatures bind exact structures and conditions, not only labels or formulas', () => {
  const start = source.indexOf('function guidanceSignature(');
  const fn = compile(source.slice(start, source.indexOf('\n}', start) + 2));
  const inputs = [{ value: 'Same formula' }, { value: 'Sodium hypochlorite' }];
  const reactants = [{ smiles: 'CC(O)C' }, { smiles: '[Na+].[O-]Cl' }];
  let conditions = { solvent: 'aqueous-protic' };
  const signature = new Function('inputs', 'resolveReactant', 'reactantReference', 'currentConditions', `${fn};return guidanceSignature;`)(inputs, i => reactants[i], r => r, () => conditions);
  const initial = signature();
  reactants[0] = { smiles: 'CCCO' }; assert.notEqual(signature(), initial);
  reactants[0] = { smiles: 'CC(O)C' }; assert.equal(signature(), initial);
  conditions = { solvent: 'dry' }; assert.notEqual(signature(), initial);
});

test('unsupported control values cannot partially overwrite explicit selections', async () => {
  const { controls, calls, run } = application(); const before = JSON.stringify(controls);
  await assert.rejects(run({ ...g('missing'), targetConditions: { ...g('missing').targetConditions, catalyst: 'not-an-option' } }, 'current'), /available controls/);
  assert.equal(JSON.stringify(controls), before); assert.deepEqual(calls, []);
});

test('matching invalidates guidance and old results immediately and retains backend run authority', () => {
  assert.match(source, /async function updateMatches\(preferredReactionId\?: string\) \{\s*guidedConditions.clear\(\);\s*resetResult\(\);/);
  assert.match(source, /if \(requestRevision !== revision\) return/);
  assert.match(source, /guidedConditions.setGuidance\(reaction.guidedConditions, requestSignature\)/);
  assert.match(source, /if \(preferredButton\) preferredButton.click\(\)/);
  assert.match(source, /assessment\?\.canRun !== false/);
  assert.match(source, /draft\.conditions\?\.secondaryOxidationProfile === 'naocl-acetic-ketone-v1'/);
  assert.equal((source.match(/applyGuidedConditions\(/g) ?? []).length, 1, 'Only the handler definition; no automatic direct preset application');
});

for (const name of Object.keys(cases)) test(`${name}: calculator confidence stays identical to backend assessment`, () => {
  const r = cases[name], context = copyCalculationContext(r.stoichiometry.context);
  assert.equal(context.canGenerate3D, r.assessment.canRun);
  assert.match(context.warning, name === 'primary' ? /Hypothetical first-stage amounts only/ : /[Tt]heoretical/);
  assert.match(context.warning, /not predicted/);
  if (name === 'qualified') {
    const result = calculateReaction(r.stoichiometry, { 0: { value: 1, unit: 'mmol' }, 1: { value: 1, unit: 'mmol' } });
    assert.ok(Math.abs(result.product.grams - 0.05808) < 1e-8);
  }
});
