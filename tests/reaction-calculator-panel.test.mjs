import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const moduleUrl = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const calculatorSource = await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8');
const calculatorUrl = moduleUrl(transpile(calculatorSource));
const panelSource = await readFile(new URL('../src/reaction-calculator-panel.ts', import.meta.url), 'utf8');
const panelOutput = transpile(panelSource).replace(/from ['"]\.\/reaction-calculator['"]/, `from '${calculatorUrl}'`);
const { ReactionCalculatorPanel } = await import(moduleUrl(panelOutput));

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = '';
    this.id = '';
    this.hidden = false;
    this.value = '';
    this._textContent = '';
    this.classList = { add: (...names) => { this.className = [...new Set([...this.className.split(/\s+/).filter(Boolean), ...names])].join(' '); } };
  }
  set textContent(value) { this.children = []; this._textContent = String(value); }
  get textContent() { return this._textContent + this.children.map((child) => child.textContent).join(''); }
  get valueAsNumber() { return this.value.trim() ? Number(this.value) : NaN; }
  set innerHTML(value) { throw new Error(`Unsafe innerHTML write: ${value}`); }
  append(...children) {
    this.children.push(...children);
    if (this.tagName === 'SELECT' && !this.value) this.value = this.children.find((child) => child.tagName === 'OPTION')?.value ?? '';
  }
  replaceChildren(...children) { this.children = []; this._textContent = ''; this.append(...children); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  addEventListener(name, handler) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), handler]); }
  emit(name) {
    const event = { target: this, prevented: false, preventDefault() { this.prevented = true; } };
    for (const listener of this.listeners.get(name) ?? []) listener(event);
    return event;
  }
}

function descendants(element) { return element.children.flatMap((child) => [child, ...descendants(child)]); }
function find(host, predicate) {
  const element = descendants(host).find(predicate);
  assert.ok(element, 'Expected element was not rendered');
  return element;
}
function byId(host, id) { return find(host, (element) => element.id === id); }
function byClass(host, name) { return find(host, (element) => element.className.split(/\s+/).includes(name)); }
function byTag(host, name) { return find(host, (element) => element.tagName === name.toUpperCase()); }
function fields(host) { return descendants(byClass(host, 'calculator-fields')).filter((element) => element.tagName === 'INPUT'); }
function unitFor(host, inputId) {
  const row = find(host, (element) => element.className === 'calculator-field' && descendants(element).some((child) => child.id === inputId));
  return byTag(row, 'select');
}
function setAmount(host, id, value, unit = 'g') {
  const input = byId(host, id);
  input.value = String(value);
  unitFor(host, id).value = unit;
  input.emit('input');
}
function clickMode(host, label) {
  const button = find(host, (element) => element.tagName === 'BUTTON' && element.textContent === label);
  button.emit('click');
  return button;
}
function facts(host) {
  return byClass(host, 'calculator-output').children
    .filter((element) => element.className === 'calculator-fact')
    .map((element) => element.children.map((child) => child.textContent));
}
function fixture(run) {
  const previous = { present: Object.hasOwn(globalThis, 'document'), value: globalThis.document };
  globalThis.document = { createElement: (tag) => new FakeElement(tag) };
  try {
    const host = new FakeElement('details');
    const panel = new ReactionCalculatorPanel(host);
    return run({ host, panel });
  } finally {
    if (previous.present) globalThis.document = previous.value;
    else delete globalThis.document;
  }
}

const substitution = () => ({
  balanced: true,
  reactants: [
    { inputSlot: 0, name: 'Bromomethane', formula: 'CH3Br', molarMass: 94.939, coefficient: 1 },
    { inputSlot: 1, name: 'Sodium hydroxide', formula: 'NaOH', molarMass: 39.997, coefficient: 1 },
  ],
  product: { name: 'Methanol', formula: 'CH4O', molarMass: 32.042, coefficient: 1 },
  excludedInputs: [],
  notes: ['The sodium spectator ion is omitted from the equation.'],
});
function fillYield(host) {
  setAmount(host, 'calculator-reactant-0', 9.4939);
  setAmount(host, 'calculator-reactant-1', 7.9994);
  return byTag(host, 'form').emit('submit');
}

test('calculator stays hidden until verified reaction metadata is selected', () => fixture(({ host, panel }) => {
  assert.equal(host.hidden, true);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(fields(host).length, 0);
  panel.setReaction(substitution());
  assert.equal(host.hidden, false);
  assert.equal(byTag(host, 'form').hidden, false);
  assert.equal(fields(host).length, 2);
}));

test('fields show selected compound names, all supported units, and the full sodium hydroxide mass', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  const labels = descendants(byClass(host, 'calculator-fields')).filter((element) => element.tagName === 'LABEL');
  assert.deepEqual(labels.map((element) => element.textContent), ['Bromomethane (CH3Br)', 'Sodium hydroxide (NaOH)']);
  for (const input of fields(host)) {
    const unit = unitFor(host, input.id);
    assert.deepEqual(unit.children.map((element) => element.value), ['g', 'mg', 'mol', 'mmol']);
    assert.equal(unit.value, 'g');
    assert.equal(input.type, 'number');
    assert.equal(input.required, true);
    assert.equal(input.getAttribute('aria-describedby'), `${input.id}-conversion`);
  }
  assert.equal(byId(host, 'calculator-reactant-1-conversion').textContent, '39.997 g/mol');
  assert.match(byClass(host, 'calculator-notes').textContent, /full selected salt/);
}));

test('submitting both reactant amounts renders limiting input, product yield, and leftover quantities', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  assert.equal(fillYield(host).prevented, true);
  assert.equal(byClass(host, 'calculator-output').hidden, false);
  assert.equal(byId(host, 'calculator-error').hidden, true);
  assert.deepEqual(facts(host), [
    ['Limiting reactant', 'Bromomethane'],
    ['Theoretical yield · Methanol', '3.2042 g · 0.1 mol'],
    ['Remaining · Bromomethane', '0 g · 0 mol'],
    ['Remaining · Sodium hydroxide', '3.9997 g · 0.1 mol'],
  ]);
}));

test('editing an amount or its unit immediately clears stale results and refreshes mole conversion', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  fillYield(host);
  setAmount(host, 'calculator-reactant-0', 18.9878);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(byClass(host, 'calculator-output').children.length, 0);
  assert.equal(byId(host, 'calculator-reactant-0-conversion').textContent, '94.939 g/mol · 0.2 mol');
  byTag(host, 'form').emit('submit');
  assert.equal(byClass(host, 'calculator-output').hidden, false);
  const unit = unitFor(host, 'calculator-reactant-0');
  unit.value = 'mmol';
  unit.emit('change');
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(byClass(host, 'calculator-output').children.length, 0);
  assert.equal(byId(host, 'calculator-reactant-0-conversion').textContent, '94.939 g/mol · 0.018988 mol');
}));

test('switching mode discards the yield result and calculates target-based reactant requirements', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  fillYield(host);
  const targetButton = clickMode(host, 'Target → amounts');
  assert.equal(targetButton.getAttribute('aria-pressed'), 'true');
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(fields(host).length, 1);
  assert.equal(byId(host, 'calculator-target').value, '');
  setAmount(host, 'calculator-target', 3.2042);
  byTag(host, 'form').emit('submit');
  assert.deepEqual(facts(host), [
    ['Target · Methanol', '3.2042 g · 0.1 mol'],
    ['Required · Bromomethane', '9.4939 g · 0.1 mol'],
    ['Required · Sodium hydroxide', '3.9997 g · 0.1 mol'],
  ]);
  assert.match(byClass(host, 'calculator-output').textContent, /100% conversion/);
  clickMode(host, 'Amounts → yield');
  assert.equal(targetButton.getAttribute('aria-pressed'), 'false');
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(fields(host).length, 2);
  assert.ok(fields(host).every((input) => input.value === ''));
}));

test('selecting another reaction clears prior inputs, conversions, errors, and results', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  fillYield(host);
  const changed = substitution();
  changed.reactants[0] = { inputSlot: 0, name: 'Bromoethane', formula: 'C2H5Br', molarMass: 108.97, coefficient: 1 };
  changed.product = { name: 'Ethanol', formula: 'C2H6O', molarMass: 46.069, coefficient: 1 };
  panel.setReaction(changed);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(byClass(host, 'calculator-output').children.length, 0);
  assert.equal(byId(host, 'calculator-error').hidden, true);
  assert.ok(fields(host).every((input) => input.value === ''));
  assert.equal(byId(host, 'calculator-reactant-0-conversion').textContent, '108.97 g/mol');
  assert.ok(!host.textContent.includes('Bromomethane'));
  setAmount(host, 'calculator-reactant-0', 10.897);
  setAmount(host, 'calculator-reactant-1', 3.9997);
  byTag(host, 'form').emit('submit');
  assert.deepEqual(facts(host)[1], ['Theoretical yield · Ethanol', '4.6069 g · 0.1 mol']);
}));

test('E1 solvent is noted but never shown as a stoichiometric quantity input', () => fixture(({ host, panel }) => {
  panel.setReaction({
    balanced: true,
    reactants: [{ inputSlot: 1, name: 'tert-Butyl bromide', formula: 'C4H9Br', molarMass: 137.018, coefficient: 1 }],
    product: { name: '2-Methylpropene', formula: 'C4H8', molarMass: 56.108, coefficient: 1 },
    excludedInputs: [{ inputSlot: 0, name: 'Water', reason: 'Solvent; not consumed stoichiometrically' }], notes: [],
  });
  assert.equal(fields(host).length, 1);
  assert.equal(fields(host)[0].id, 'calculator-reactant-1');
  assert.match(byClass(host, 'calculator-notes').textContent, /Water: Solvent/);
  setAmount(host, 'calculator-reactant-1', 100, 'mmol');
  byTag(host, 'form').emit('submit');
  assert.deepEqual(facts(host)[1], ['Theoretical yield · 2-Methylpropene', '5.6108 g · 0.1 mol']);
  assert.ok(!facts(host).some(([label]) => label.includes('Water')));
}));

test('unbalanced metadata hides the form, removes stale results, and can recover on valid selection', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  fillYield(host);
  panel.setReaction({ ...substitution(), balanced: false });
  assert.equal(host.hidden, false);
  assert.equal(byTag(host, 'form').hidden, true);
  assert.equal(fields(host).length, 0);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.match(byClass(host, 'calculator-notes').textContent, /not been verified as balanced/);
  byTag(host, 'form').emit('submit');
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  panel.setReaction(substitution());
  assert.equal(byTag(host, 'form').hidden, false);
  assert.equal(fields(host).length, 2);
}));

test('compound names and notes are literal text and cannot create injected markup', () => fixture(({ host, panel }) => {
  const data = substitution();
  data.reactants[0].name = '<img src=x onerror=alert(1)>';
  data.product.name = '<script>unsafe()</script>';
  data.notes = ['<svg onload=alert(2)>'];
  panel.setReaction(data);
  fillYield(host);
  assert.match(host.textContent, /<img src=x onerror=alert\(1\)>/);
  assert.match(host.textContent, /<script>unsafe\(\)<\/script>/);
  assert.match(host.textContent, /<svg onload=alert\(2\)>/);
  assert.equal(descendants(host).some((element) => ['IMG', 'SCRIPT', 'SVG'].includes(element.tagName)), false);
}));

test('absent metadata hides the panel and removes previous amounts, messages, and outputs', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  fillYield(host);
  panel.setReaction();
  assert.equal(host.hidden, true);
  assert.equal(fields(host).length, 0);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  assert.equal(byClass(host, 'calculator-output').children.length, 0);
  assert.equal(byClass(host, 'calculator-notes').children.length, 0);
  assert.equal(byId(host, 'calculator-error').hidden, true);
  byTag(host, 'form').emit('submit');
  assert.equal(byClass(host, 'calculator-output').hidden, true);
}));

test('invalid or missing amounts show a plain error that disappears on edit', () => fixture(({ host, panel }) => {
  panel.setReaction(substitution());
  byTag(host, 'form').emit('submit');
  assert.equal(byId(host, 'calculator-error').hidden, false);
  assert.match(byId(host, 'calculator-error').textContent, /Enter an amount/);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
  setAmount(host, 'calculator-reactant-0', 1);
  assert.equal(byId(host, 'calculator-error').hidden, true);
  clickMode(host, 'Target → amounts');
  setAmount(host, 'calculator-target', 0);
  byTag(host, 'form').emit('submit');
  assert.equal(byId(host, 'calculator-error').hidden, false);
  assert.match(byId(host, 'calculator-error').textContent, /positive/);
  assert.equal(byClass(host, 'calculator-output').hidden, true);
}));
