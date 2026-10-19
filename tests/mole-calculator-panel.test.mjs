import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const read = (file) => readFile(new URL(`../src/${file}`, import.meta.url), 'utf8');
const compile = (source) => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = (code) => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`;
const pureUrl = url(compile(await read('mole-calculator.ts')));
const { MoleCalculatorPanel } = await import(url(compile(await read('mole-calculator-panel.ts')).replace("from './mole-calculator'", `from '${pureUrl}'`)));
class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = new Map(); this.attributes = new Map(); this.value = ''; this.hidden = false; this.className = ''; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); }
  set innerHTML(_) { throw Error('Unsafe text rendering'); }
  append(...children) { this.children.push(...children); for (const child of children) child.parent = this; if (this.tagName === 'SELECT' && !this.value) this.value = this.children[0].value; }
  replaceChildren(...children) { this.children = []; this._text = ''; this.append(...children); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  addEventListener(name, listener) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), listener]); }
  emit(name, event = { preventDefault() {} }) { for (const fn of this.listeners.get(name) ?? []) fn(event); if (['input', 'change'].includes(name)) this.parent?.emit(name, event); }
}
const descendants = (host) => host.children.flatMap((c) => [c, ...descendants(c)]);
const find = (host, fn) => { const item = descendants(host).find(fn); assert.ok(item); return item; };
const field = (host, id) => find(host, (el) => el.id === id);
const result = (host) => find(host, (el) => el.className === 'calc-result');
const submit = (host) => find(host, (el) => el.tagName === 'FORM').emit('submit');
const salt = { id: 'NaCl-exact', name: 'Sodium chloride', formula: 'NaCl', molarMass: 58.443, entityKind: 'formula-units' };
function fixture(run) {
  const previous = globalThis.document;
  globalThis.document = { createElement: (tag) => new Element(tag) };
  try { const host = new Element('div'); const panel = new MoleCalculatorPanel(host); return run({ host, panel }); }
  finally { if (previous === undefined) delete globalThis.document; else globalThis.document = previous; }
}
test('mole panel uses full salt mass and labels formula units with accessible fields', () => fixture(({ host, panel }) => {
  panel.setCompound(salt); field(host, 'moles-amount').value = '58.443'; submit(host);
  assert.equal(result(host).hidden, false); assert.match(result(host).textContent, /Ionic formula units6.02214e\+23/);
  for (const input of descendants(host).filter((el) => el.tagName === 'INPUT')) assert.ok(descendants(host).some((el) => el.tagName === 'LABEL' && el.htmlFor === input.id));
  assert.equal(result(host).attributes.get('role'), 'status');
}));
test('every amount, mass, unit and entity edit clears old results', () => fixture(({ host, panel }) => {
  for (const selector of ['moles-amount', 'moles-mass', 'moles-entity', 'unit']) {
    panel.setCompound(salt); field(host, 'moles-amount').value = '58.443'; submit(host); assert.equal(result(host).hidden, false);
    const target = selector === 'unit' ? find(host, (el) => el.attributes.get('aria-label') === 'Amount unit') : field(host, selector);
    target.emit(target.tagName === 'SELECT' ? 'change' : 'input'); assert.equal(result(host).hidden, true); assert.equal(result(host).children.length, 0);
  }
}));
test('entity change cannot silently use a whole-compound molar mass as atomic mass', () => fixture(({ host, panel }) => {
  panel.setCompound(salt); const entity = field(host, 'moles-entity'); entity.value = 'atoms'; entity.emit('change');
  assert.equal(field(host, 'moles-mass').value, ''); assert.match(host.textContent, /Manual entry/);
  field(host, 'moles-amount').value = '1'; submit(host); assert.equal(result(host).hidden, true); assert.match(host.textContent, /needs the exact/);
  find(host, (el) => el.attributes.get('aria-label') === 'Amount unit').value = 'mol'; submit(host);
  assert.equal(result(host).hidden, false); assert.match(result(host).textContent, /Atoms/);
}));
test('compound changes and Clear remove old quantities/results; selected mass is restored', () => fixture(({ host, panel }) => {
  panel.setCompound(salt); field(host, 'moles-amount').value = '58.443'; submit(host);
  panel.setCompound({ id: 'water', name: '<img onerror=unsafe>', formula: 'H₂O', molarMass: 18.015, entityKind: 'molecules' });
  assert.equal(field(host, 'moles-amount').value, ''); assert.equal(field(host, 'moles-mass').value, '18.015'); assert.equal(result(host).hidden, true);
  assert.ok(host.textContent.includes('<img onerror=unsafe>'));
  field(host, 'moles-mass').value = '100'; panel.clear(); assert.equal(field(host, 'moles-mass').value, '18.015');
}));
test('missing amount errors do not look like a zero result; zero input calculates exactly', () => fixture(({ host }) => {
  submit(host); assert.equal(result(host).hidden, true); assert.match(host.textContent, /Enter an amount/);
  field(host, 'moles-amount').value = '0'; find(host, (el) => el.attributes.get('aria-label') === 'Amount unit').value = 'mol'; submit(host);
  assert.equal(result(host).hidden, false); assert.match(result(host).textContent, /Amount0 mol/);
}));
