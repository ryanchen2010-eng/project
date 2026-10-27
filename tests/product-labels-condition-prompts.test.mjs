import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
const read = p => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const load = async p => import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(await read(p), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText).toString('base64')}`);
const { conditionNextStep, conditionGuidance, productStructureLabel } = await load('src/reaction-conditions.ts');
const { GuidedConditionsPanel } = await load('src/guided-reaction-conditions.ts');

test('missing conditions get human labels, automatic refresh guidance and no invented settings', () => {
  const a = { state: 'incomplete', canRun: false, note: '', evidence: { missingRequiredSettings: ['oxidationStage', 'catalyst'], canGenerate3D: false } };
  assert.match(conditionNextStep(a), /oxidation stage, additional catalyst \/ activation/);
  assert.match(conditionGuidance(a), /options update automatically/);
  assert.match(conditionGuidance(a), /Review supported settings/);
  assert.doesNotMatch(conditionNextStep(a), /oxidationStage|NaBH4|Lindlar|guaranteed/);
  assert.equal(a.canRun, false);
});

test('unimplemented selective aldehyde conditions are not advertised as fillable', () => {
  const a = { canRun: false, evidence: { missingRequiredSettings: ['solvent'], aldehydeEndpointValidated: false } };
  assert.match(conditionNextStep(a), /not implemented/);
  assert.match(conditionNextStep(a), /will not enable 3D/);
  assert.doesNotMatch(conditionNextStep(a), /Complete:/);
});

test('missing comparison settings are not confused with required activation', () => {
  assert.match(conditionNextStep({ status: 'missing' }), /comparison settings/);
  assert.match(conditionNextStep({ status: 'missing' }), /does not mean the reaction is impossible/);
  assert.equal(conditionNextStep({ status: 'model-match', canRun: true }), '');
  assert.match(conditionNextStep({ canRun: false }), /may not resolve/);
});

test('fallback products include an exact structure identifier, not a guessed name', () => {
  assert.equal(productStructureLabel('Alcohol product', 'CC(C)CCO'), 'Structure identifier (SMILES): CC(C)CCO');
  assert.match(productStructureLabel('Partially hydrogenated product', 'C=CCCCC'), /C=CCCCC/);
  assert.equal(productStructureLabel('Pentan-1-ol', 'CCCCCO'), '');
  assert.equal(productStructureLabel('Methanol', 'CO'), '');
  assert.equal(productStructureLabel('Organic product'), '');
});

class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {}; this.attributes = {}; this._text = ''; this.disabled = false; this.checked = false; }
  set textContent(s) { this._text = String(s); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; this._text = ''; }
  setAttribute(k, v) { this.attributes[k] = v; }
  addEventListener(k, fn) { (this.listeners[k] ??= []).push(fn); }
  async emit(k) { await Promise.all((this.listeners[k] ?? []).map(fn => fn({ target: this }))); }
}
const all = host => host.children.flatMap(c => [c, ...all(c)]);
const guidance = {
  version: 1, reactionId: 'test', state: 'conflicting-conditions', title: 'Defined model', message: 'Review conflicting selections',
  canApply: true, requireConfirmation: false, limitations: ['Not a laboratory procedure.'],
  requirements: [
    { field: 'solvent', label: 'Solvent / medium', selectedLabel: 'Water (generic)', requiredLabel: 'Reviewed medium', state: 'conflicting' },
    { field: 'temperature', label: 'Temperature', selectedLabel: 'Not specified', requiredLabel: 'Room temperature', state: 'missing' },
  ],
};

test('actionable checklist is visible before opening details, without applying anything', () => {
  const previous = globalThis.document; globalThis.document = { createElement: tag => new Element(tag) };
  try {
    const host = new Element('section'); let calls = 0;
    const panel = new GuidedConditionsPanel(host, () => { calls += 1; }); panel.setGuidance(guidance, 'current');
    const list = host.children.find(c => c.tagName === 'UL');
    assert.equal(list.attributes['aria-label'], 'Settings to review');
    assert.match(list.textContent, /Choose Temperature: Room temperature/);
    assert.match(list.textContent, /Water \(generic\) → Reviewed medium \(confirmation required\)/);
    assert.match(host.textContent, /Nothing changes until you review and apply/);
    assert.equal(calls, 0);
    assert.equal(all(host).find(e => e.tagName === 'BUTTON').disabled, true);
  } finally { if (previous === undefined) delete globalThis.document; else globalThis.document = previous; }
});

test('non-applicable or qualified guides do not offer a misleading checklist', () => {
  const previous = globalThis.document; globalThis.document = { createElement: tag => new Element(tag) };
  try {
    const host = new Element('section'); const panel = new GuidedConditionsPanel(host, () => assert.fail());
    for (const state of ['qualified', 'outside-profile-scope', 'no-validated-profile', 'unsupported-conditions']) {
      panel.setGuidance({ ...guidance, state, canApply: false }, 'context');
      assert.equal(host.children.find(c => c.tagName === 'UL'), undefined);
      assert.equal(all(host).find(c => c.tagName === 'BUTTON'), undefined);
    }
  } finally { if (previous === undefined) delete globalThis.document; else globalThis.document = previous; }
});

test('option identifiers and condition prompts use text content, and do not change eligibility', async () => {
  const source = await read('src/reaction-lab.ts');
  assert.match(source, /structure\.textContent = structureLabel/);
  assert.match(source, /structure\.style\.overflowWrap = 'anywhere'/);
  assert.match(source, /prompt\.textContent = nextStep/);
  assert.doesNotMatch(source, /(?:prompt|structure)\.innerHTML/);
  assert.match(source, /conditionNextStep\(reaction\.assessment\)/);
});
