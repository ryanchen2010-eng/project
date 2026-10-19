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
const rows = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
cases=[('missing','CC#CC',{}),('qualified','CC#CC',{'catalyst':'lindlar'}),('metal','CC#CC',{'catalyst':'metal'}),
 ('radical','CC#CC',{'catalyst':'radical'}),('preserved','CC#CC',{'solvent':'dry','temperature':'ambient','additionStage':'two','polymerUnits':'6'}),
 ('clear','CC#CC',{'catalyst':'lindlar','oxidationStage':'first','workup':'aqueous-release'}),
 ('water','CC#CC',{'solvent':'aqueous-protic'}),('heat','CC#CC',{'temperature':'heated'}),
 ('unknown','CC#CC',{'catalyst':'lindlar','peroxide':True}),('multisite','C#CCCCCCC#CC',{'catalyst':'lindlar'})]
data={name:next(r for r in s.match_reactions({'smiles':smiles},'hydrogen',c)['reactionOptions'] if r['mechanism']=='Alkyne partial hydrogenation') for name,smiles,c in cases}
p={'secondaryOxidationProfile':'naocl-acetic-ketone-v1','solvent':'aqueous-protic','temperature':'ambient','catalyst':'none','oxidationStage':'first'}
for name,smiles in [('secondary','CC(O)C'),('primary','CCO')]:
 data[name]=next(r for r in s.match_reactions({'smiles':smiles},'sodium-hypochlorite',p)['reactionOptions'] if r['mechanism']=='Alcohol oxidation')
print(json.dumps(data))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }));
const g = name => rows[name].guidedConditions;

class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {}; this.attributes = {}; this.disabled = false; this.checked = false; this.hidden = false; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ''; this.children = children; }
  setAttribute(k, v) { this.attributes[k] = v; }
  addEventListener(name, fn) { (this.listeners[name] ??= []).push(fn); }
  async emit(name) { await Promise.all((this.listeners[name] ?? []).map(fn => fn({ target: this }))); }
}
const descendants = e => e.children.flatMap(c => [c, ...descendants(c)]);
const tag = (host, name) => descendants(host).find(c => c.tagName === name.toUpperCase());
async function fixture(fn, apply = async () => {}) {
  const old = globalThis.document; globalThis.document = { createElement: t => new Element(t) };
  try { const host = new Element('section'); await fn(host, new GuidedConditionsPanel(host, apply)); }
  finally { if (old === undefined) delete globalThis.document; else globalThis.document = old; }
}

for (const name of ['missing', 'metal', 'radical', 'preserved', 'clear']) {
  test(`${name}: Lindlar review always requires explicit confirmation and never auto-applies`, async () => {
    const calls = [];
    await fixture(async (host, panel) => {
      panel.setGuidance(g(name), 'exact-context'); const button = tag(host, 'button'), checkbox = tag(host, 'input');
      assert.equal(button.disabled, true); assert.equal(checkbox.checked, false); assert.equal(calls.length, 0);
      await button.emit('click'); assert.equal(calls.length, 0);
      checkbox.checked = true; await checkbox.emit('change'); assert.equal(button.disabled, false);
      checkbox.checked = false; await checkbox.emit('change'); await button.emit('click'); assert.equal(calls.length, 0);
      checkbox.checked = true; await checkbox.emit('change'); await button.emit('click');
      assert.equal(calls.length, 1); assert.equal(calls[0][0], g(name)); assert.equal(calls[0][1], 'exact-context');
      assert.match(host.textContent, /not a fully specified experimental condition profile/);
      assert.equal(descendants(host).filter(e => e.tagName === 'SELECT').length, 0);
    }, async (...args) => calls.push(args));
  });
}

for (const name of ['qualified', 'water', 'heat', 'unknown', 'multisite', 'primary']) {
  test(`${name}: no Lindlar apply action can bypass unresolved conditions or chemistry`, async () => fixture(async (host, panel) => {
    panel.setGuidance(g(name), 'context'); assert.equal(tag(host, 'button'), undefined); assert.equal(tag(host, 'input'), undefined);
    assert.ok(host.textContent.includes(g(name).message));
    if (name === 'qualified') assert.match(host.textContent, /solvent, pressure and stopping conditions are not validated/);
    if (name === 'multisite') assert.match(host.textContent, /selective one-site conversion/);
  }, async () => assert.fail('No action should run')));
}

test('valid medium and temperature are displayed as preserved, not experimentally validated', async () => fixture(async (host, panel) => {
  panel.setGuidance(g('preserved'), 'context');
  assert.match(host.textContent, /Medium \(preserved\)/); assert.match(host.textContent, /Temperature \(preserved\)/);
  assert.match(host.textContent, /no protocol validation inferred/); assert.match(host.textContent, /\(preserved\)/);
  assert.deepEqual(guidedControlValues(g('preserved')), { catalyst: 'lindlar' });
}));

test('Lindlar transport permits only activation and explicit unrelated-field clearing', () => {
  assert.deepEqual(guidedControlValues(g('missing')), { catalyst: 'lindlar' });
  assert.deepEqual(guidedControlValues(g('clear')), { catalyst: 'lindlar', oxidationStage: '', workup: '' });
  for (const targetConditions of [
    { catalyst: 'metal' }, { catalyst: 'lindlar', solvent: 'dry' }, { catalyst: 'lindlar', temperature: 'ambient' },
    { catalyst: 'lindlar', pressure: '1' }, { catalyst: 'lindlar', oxidationStage: 'first' },
    { catalyst: 'lindlar', secondaryOxidationProfile: 'naocl-acetic-ketone-v1' },
  ]) assert.throws(() => guidedControlValues({ ...g('missing'), targetConditions }));
});

test('switching pathway or site invalidates a previously confirmed Lindlar action', async () => {
  let calls = 0;
  await fixture(async (host, panel) => {
    panel.setGuidance(g('missing'), 'same-reactants'); const old = tag(host, 'button'), check = tag(host, 'input');
    check.checked = true; await check.emit('change');
    panel.setGuidance(g('multisite'), 'same-reactants'); await old.emit('click'); assert.equal(calls, 0);
    panel.setGuidance(undefined, 'full-hydrogenation'); assert.equal(host.hidden, true);
  }, async () => { calls += 1; });
});

test('Lindlar guidance waits for partial-pathway selection rather than contradicting a complete-reduction example', () => {
  assert.equal(g('missing').showOnInitialMatch, false);
  assert.equal(g('secondary').showOnInitialMatch, undefined);
  assert.match(source, /matches.filter\(reaction => reaction.guidedConditions\?\.showOnInitialMatch !== false\)/);
  assert.match(source, /guidedConditions.setGuidance\(reaction.guidedConditions, requestSignature\)/);
});

function application(signature = 'current') {
  const start = source.indexOf('async function applyGuidedConditions(');
  const fn = compile(source.slice(start, source.indexOf('\n}', start) + 2));
  const original = { solvent: 'dry', temperature: 'ambient', catalyst: 'metal', oxidationStage: '', workup: '' };
  const values = { solvent: ['', 'dry', 'secondary-naocl-acetic'], temperature: ['', 'ambient'], catalyst: ['', 'metal', 'lindlar', 'none'], oxidationStage: ['', 'first'], workup: ['', 'aqueous-release'] };
  const controls = Object.fromEntries(Object.entries(original).map(([key, value]) => [key, { value, options: values[key].map(value => ({ value })) }]));
  const calls = [];
  const run = new Function('guidanceSignature', 'guidedControlValues', 'solventInput', 'temperatureInput', 'catalystInput', 'oxidationStageInput', 'workupInput', 'saveDraft', 'updateMatches', `${fn};return applyGuidedConditions;`)(
    () => signature, guidedControlValues, ...Object.values(controls), () => calls.push('saved'), async id => calls.push(['revalidated', id]));
  return { controls, calls, run, original };
}

test('existing application handler preserves selections and reselects the exact partial-reduction site', async () => {
  const { controls, calls, run, original } = application(); await run(g('preserved'), 'current');
  assert.deepEqual(Object.fromEntries(Object.entries(controls).map(([key, control]) => [key, control.value])), { ...original, catalyst: 'lindlar' });
  assert.deepEqual(calls, ['saved', ['revalidated', g('preserved').reactionId]]);
});

test('a stale Lindlar request changes neither controls nor stored settings', async () => {
  const { controls, calls, run } = application('changed'); const before = JSON.stringify(controls);
  await assert.rejects(run(g('missing'), 'old'), /changed/); assert.equal(JSON.stringify(controls), before); assert.deepEqual(calls, []);
});

test('the original secondary-oxidation guidance remains distinct and functional', () => {
  assert.equal(g('secondary').profileId, 'naocl-acetic-ketone-v1'); assert.equal(g('secondary').state, 'qualified');
  assert.equal(rows.secondary.assessment.canRun, true); assert.equal(g('primary').state, 'no-validated-profile');
  assert.equal(rows.primary.assessment.canRun, false);
});

for (const name of ['missing', 'qualified', 'metal', 'radical', 'preserved', 'clear', 'water', 'heat', 'unknown', 'multisite']) {
  test(`${name}: reaction quantities cannot certify Lindlar conditions or selective conversion`, () => {
    const r = rows[name], context = copyCalculationContext(r.stoichiometry.context);
    assert.equal(context.canGenerate3D, r.assessment.canRun);
    assert.match(context.warning, /over-reduction and selective mono-conversion are not predicted/);
    assert.match(context.warning, /not experimental yields/); assert.equal(r.stoichiometry.reactants[1].coefficient, 1);
    if (name === 'qualified') {
      const result = calculateReaction(r.stoichiometry, { 0: { value: 1, unit: 'mmol' }, 1: { value: 1, unit: 'mmol' } });
      assert.ok(Math.abs(result.product.grams - 0.056108) < 1e-8); // Independently specified C4H8 formula mass.
    }
  });
}
