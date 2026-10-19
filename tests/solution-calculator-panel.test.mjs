import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const moduleUrl = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const calculatorSource = await readFile(new URL('../src/solution-calculator.ts', import.meta.url), 'utf8');
const calculatorUrl = moduleUrl(transpile(calculatorSource));
const panelSource = await readFile(new URL('../src/solution-calculator-panel.ts', import.meta.url), 'utf8');
const panelOutput = transpile(panelSource).replace(/from ['"]\.\/solution-calculator['"]/, `from '${calculatorUrl}'`);
const { SolutionCalculatorPanel } = await import(moduleUrl(panelOutput));

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
    this.disabled = false;
    this._textContent = '';
    this.classList = { add: (...names) => {
      this.className = [...new Set([...this.className.split(/\s+/).filter(Boolean), ...names])].join(' ');
    } };
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
function clickMode(host, label) {
  const button = find(host, (element) => element.tagName === 'BUTTON' && element.textContent === label);
  button.emit('click');
  return button;
}
function fixture(run) {
  const previous = { present: Object.hasOwn(globalThis, 'document'), value: globalThis.document };
  globalThis.document = { createElement: (tag) => new FakeElement(tag) };
  try {
    const host = new FakeElement('details');
    host.id = 'test-solution';
    const panel = new SolutionCalculatorPanel(host);
    return run({ host, panel });
  } finally {
    if (previous.present) globalThis.document = previous.value;
    else delete globalThis.document;
  }
}

const salt = () => ({ id: 'sodium-chloride', name: 'Sodium chloride', formula: 'NaCl', molarMass: 58.44 });

function field(host, key) { return byId(host, `${host.id}-${key}`); }
function rowFor(host, key) {
  const input = field(host, key);
  return find(host, (element) => element.className.split(/\s+/).includes('solution-field')
    && descendants(element).includes(input));
}
function unitFor(host, key) { return byTag(rowFor(host, key), 'select'); }
function setValue(host, key, value) {
  const input = field(host, key);
  input.value = String(value);
  input.emit('input');
}
function setUnit(host, key, unit) {
  const select = unitFor(host, key);
  select.value = unit;
  select.emit('change');
}
function submit(host) { return byTag(host, 'form').emit('submit'); }
function output(host) { return byClass(host, 'solution-output'); }
function error(host) { return byClass(host, 'solution-error'); }
function noResult(host) {
  assert.equal(output(host).hidden, true);
  assert.equal(output(host).children.length, 0);
}
function concentration(host, panel) {
  panel.setCompound(salt());
  setValue(host, 'amount', '5.844');
  setValue(host, 'volume', '100');
  submit(host);
  assert.equal(output(host).hidden, false);
}

test('a standalone calculator exposes three compact modes without needing a compound or 3D model', () => fixture(({ host }) => {
  assert.equal(host.hidden, false);
  assert.equal(byTag(host, 'summary').textContent, 'Solution calculator');
  assert.deepEqual(descendants(host).filter((element) => element.tagName === 'BUTTON' && element.getAttribute('aria-pressed') !== null)
    .map((element) => element.textContent), ['Find concentration', 'Find solute mass', 'Dilute a stock']);
  assert.equal(clickMode(host, 'Find concentration').getAttribute('aria-pressed'), 'true');
  assert.equal(field(host, 'amount').type, 'number');
  assert.equal(field(host, 'amount').step, 'any');
  assert.equal(field(host, 'volume').type, 'number');
  assert.equal(unitFor(host, 'amount').value, 'g');
  assert.equal(unitFor(host, 'volume').value, 'mL');
  assert.equal(field(host, 'molar-mass').value, '');
  assert.equal(byTag(host, 'form').noValidate, true);
  noResult(host);
}));

test('selected solute identity provides its molar mass and concentration uses final solution volume', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  assert.equal(field(host, 'molar-mass').value, '58.44');
  assert.match(byClass(host, 'solution-context').textContent, /Sodium chloride/);
  assert.match(byClass(host, 'solution-context').textContent, /NaCl/);
  assert.match(output(host).textContent, /1 mol\/L/);
  assert.equal(error(host).hidden, true);
  assert.ok(descendants(output(host)).some((element) => element.className === 'solution-fact'));
}));

test('numeric input and unit edits clear prior results immediately', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  setValue(host, 'amount', '11.688');
  noResult(host);
  submit(host);
  assert.match(output(host).textContent, /2 mol\/L/);
  setUnit(host, 'volume', 'L');
  noResult(host);
  submit(host);
  assert.match(output(host).textContent, /0\.002 mol\/L/);
  setUnit(host, 'amount', 'mg');
  noResult(host);
}));

test('switching compound clears stale inputs and results instead of reusing another molar mass', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  panel.setCompound({ id: 'glucose', name: 'Glucose', formula: 'C6H12O6', molarMass: 180.156 });
  noResult(host);
  assert.equal(field(host, 'amount').value, '');
  assert.equal(field(host, 'volume').value, '');
  assert.equal(field(host, 'molar-mass').value, '180.156');
  assert.match(byClass(host, 'solution-context').textContent, /Glucose/);
  assert.ok(!byClass(host, 'solution-context').textContent.includes('Sodium chloride'));
  panel.setCompound({ id: 'unknown', name: 'Unknown solute' });
  assert.equal(field(host, 'molar-mass').value, '');
}));

test('reselecting the identical compound preserves a valid calculation', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  const result = output(host).textContent;
  panel.setCompound(salt());
  assert.equal(output(host).hidden, false);
  assert.equal(output(host).textContent, result);
  assert.equal(field(host, 'amount').value, '5.844');
}));

test('mole or millimole inputs work without a molar mass; switching to mass units requires one', () => fixture(({ host, panel }) => {
  panel.setCompound({ id: 'unidentified', name: 'Unidentified solute' });
  setUnit(host, 'amount', 'mol');
  setValue(host, 'amount', '0.1');
  setValue(host, 'volume', '100');
  submit(host);
  assert.match(output(host).textContent, /1 mol\/L/);
  assert.equal(field(host, 'molar-mass').required, false);
  assert.equal(rowFor(host, 'molar-mass').hidden, true);
  setUnit(host, 'amount', 'mmol');
  setValue(host, 'amount', '100');
  submit(host);
  assert.match(output(host).textContent, /1 mol\/L/);
  setUnit(host, 'amount', 'g');
  noResult(host);
  assert.equal(rowFor(host, 'molar-mass').hidden, false);
  submit(host);
  noResult(host);
  assert.equal(error(host).hidden, false);
  assert.match(error(host).textContent, /molar mass/i);
  setValue(host, 'molar-mass', '58.44');
  assert.equal(error(host).hidden, true);
  submit(host);
  assert.equal(output(host).hidden, false);
}));

test('mass mode calculates the required pure solute using concentration and final volume', () => fixture(({ host, panel }) => {
  panel.setCompound(salt());
  const mode = clickMode(host, 'Find solute mass');
  assert.equal(mode.getAttribute('aria-pressed'), 'true');
  setValue(host, 'concentration', '0.1');
  setValue(host, 'volume', '250');
  assert.equal(unitFor(host, 'concentration').value, 'mol/L');
  assert.equal(unitFor(host, 'volume').value, 'mL');
  submit(host);
  assert.match(output(host).textContent, /1\.461 g/);
  assert.match(output(host).textContent, /0\.025 mol/);
}));

test('dilution is independent of compound identity and mass, with matching concentration units', () => fixture(({ host }) => {
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '1');
  setValue(host, 'target-concentration', '100');
  setUnit(host, 'target-concentration', 'mmol/L');
  setValue(host, 'final-volume', '250');
  submit(host);
  assert.equal(output(host).hidden, false);
  assert.match(output(host).textContent, /25 mL/);
  assert.equal(error(host).hidden, true);
  assert.equal(descendants(host).some((element) => element.id === `${host.id}-molar-mass`), false);
}));

test('dilution rejects a target more concentrated than the stock and recovers after an edit', () => fixture(({ host }) => {
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '0.1');
  setValue(host, 'target-concentration', '1');
  setValue(host, 'final-volume', '250');
  submit(host);
  noResult(host);
  assert.equal(error(host).hidden, false);
  assert.match(error(host).textContent, /stock|target|dilut/i);
  setValue(host, 'target-concentration', '0.01');
  assert.equal(error(host).hidden, true);
  submit(host);
  assert.match(output(host).textContent, /25 mL/);
}));

test('reset returns to anonymous manual mass, removing old identity, quantities, and output', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  panel.reset();
  noResult(host);
  assert.equal(host.hidden, false);
  assert.equal(field(host, 'molar-mass').value, '');
  assert.equal(field(host, 'amount').value, '');
  assert.equal(field(host, 'volume').value, '');
  assert.ok(!byClass(host, 'solution-context').textContent.includes('Sodium chloride'));
  assert.equal(error(host).hidden, true);
}));

test('compound text is literal, results are announced, and errors use an alert', () => fixture(({ host, panel }) => {
  panel.setCompound({ id: '<unsafe>', name: '<img src=x onerror=alert(1)>', formula: '<script>unsafe()</script>', molarMass: 58.44 });
  assert.match(byClass(host, 'solution-context').textContent, /<img src=x onerror=alert\(1\)>/);
  assert.match(byClass(host, 'solution-context').textContent, /<script>unsafe\(\)<\/script>/);
  assert.equal(descendants(host).some((element) => ['IMG', 'SCRIPT', 'SVG'].includes(element.tagName)), false);
  assert.equal(output(host).getAttribute('role'), 'status');
  assert.equal(output(host).getAttribute('aria-live'), 'polite');
  assert.equal(error(host).getAttribute('role'), 'alert');
  assert.equal(field(host, 'molar-mass').getAttribute('aria-describedby'), 'test-solution-mass-source');
  submit(host);
  assert.equal(error(host).hidden, false);
}));

test('separate calculator instances use unique input IDs and remain independent', () => fixture(({ host, panel }) => {
  const secondHost = new FakeElement('details');
  secondHost.id = 'other-solution';
  const secondPanel = new SolutionCalculatorPanel(secondHost);
  concentration(host, panel);
  secondPanel.setCompound({ id: 'ethanol', name: 'Ethanol', formula: 'C2H6O', molarMass: 46.07 });
  const firstIds = descendants(host).map((element) => element.id).filter(Boolean);
  const secondIds = descendants(secondHost).map((element) => element.id).filter(Boolean);
  assert.equal(new Set(firstIds).size, firstIds.length);
  assert.equal(new Set(secondIds).size, secondIds.length);
  assert.ok(firstIds.every((id) => id.startsWith(`${host.id}-`)));
  assert.ok(secondIds.every((id) => id.startsWith(`${secondHost.id}-`)));
  assert.ok(!firstIds.some((id) => secondIds.includes(id)));
  secondPanel.reset();
  assert.equal(output(host).hidden, false);
  assert.equal(field(host, 'molar-mass').value, '58.44');
}));

test('manual mass overrides are explicit, used for calculations, and never mistaken for an automatic property', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  setValue(host, 'molar-mass', '116.88');
  noResult(host);
  assert.match(byId(host, `${host.id}-mass-source`).textContent, /manual|entered|overrid/i);
  submit(host);
  assert.match(output(host).textContent, /0\.5 mol\/L/);
  panel.setCompound(salt());
  assert.equal(field(host, 'molar-mass').value, '116.88');
  assert.match(output(host).textContent, /0\.5 mol\/L/);
}));

test('blank, zero, negative, and non-finite quantities are rejected even without native form validation', () => fixture(({ host, panel }) => {
  panel.setCompound(salt());
  setValue(host, 'volume', '100');
  for (const invalid of ['', '0', '-1', 'NaN', 'Infinity']) {
    setValue(host, 'amount', invalid);
    assert.equal(submit(host).prevented, true);
    noResult(host);
    assert.equal(error(host).hidden, false);
    assert.ok(error(host).textContent.length > 0);
  }
  setValue(host, 'amount', '5.844');
  assert.equal(error(host).hidden, true);
  submit(host);
  assert.match(output(host).textContent, /1 mol\/L/);
}));

test('invalid or missing selected mass cannot be borrowed from the previously selected solute', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  for (const molarMass of [NaN, Infinity, -1, 0, undefined]) {
    panel.setCompound({ id: `bad-${String(molarMass)}`, name: 'Unverified solute', molarMass });
    assert.equal(field(host, 'molar-mass').value, '');
    setValue(host, 'amount', '5.844');
    setValue(host, 'volume', '100');
    submit(host);
    noResult(host);
    assert.equal(error(host).hidden, false);
  }
}));

test('switching modes removes previous quantities and results but retains the selected solute mass', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  clickMode(host, 'Find solute mass');
  noResult(host);
  assert.equal(field(host, 'concentration').value, '');
  assert.equal(field(host, 'volume').value, '');
  assert.equal(field(host, 'molar-mass').value, '58.44');
  setValue(host, 'concentration', '0.1');
  setValue(host, 'volume', '100');
  submit(host);
  assert.equal(output(host).hidden, false);
  clickMode(host, 'Dilute a stock');
  noResult(host);
  assert.equal(field(host, 'stock-concentration').value, '');
  assert.equal(field(host, 'target-concentration').value, '');
  assert.equal(field(host, 'final-volume').value, '');
  clickMode(host, 'Find concentration');
  assert.equal(field(host, 'amount').value, '');
  assert.equal(field(host, 'volume').value, '');
  assert.equal(field(host, 'molar-mass').value, '58.44');
}));

test('missing or invalid hidden mass does not block a mole-based result or dilution', () => fixture(({ host }) => {
  setValue(host, 'molar-mass', '-1');
  setUnit(host, 'amount', 'mol');
  setValue(host, 'amount', '0.1');
  setValue(host, 'volume', '100');
  submit(host);
  assert.equal(error(host).hidden, true);
  assert.match(output(host).textContent, /1 mol\/L/);
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '1');
  setValue(host, 'target-concentration', '0.1');
  setValue(host, 'final-volume', '100');
  submit(host);
  assert.equal(error(host).hidden, true);
  assert.match(output(host).textContent, /10 mL/);
}));

test('the calculator notes scope, final volume, and does not claim to determine solubility or solvent added', () => fixture(({ host }) => {
  assert.match(host.textContent, /final (?:total )?(?:solution )?volume/i);
  assert.match(host.textContent, /solubility|soluble/i);
  assert.match(host.textContent, /solubility[\s\S]*not checked/i);
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '1');
  setValue(host, 'target-concentration', '0.1');
  setValue(host, 'final-volume', '100');
  submit(host);
  assert.ok(!output(host).textContent.includes('90 mL'));
  assert.match(output(host).textContent, /final|total/i);
}));

test('microlitre dilution preserves chosen display units and equal concentrations need no dilution', () => fixture(({ host }) => {
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '50');
  setUnit(host, 'stock-concentration', 'µmol/L');
  setValue(host, 'target-concentration', '50');
  setUnit(host, 'target-concentration', 'µmol/L');
  setValue(host, 'final-volume', '100');
  setUnit(host, 'final-volume', 'µL');
  submit(host);
  assert.equal(output(host).hidden, false);
  assert.match(output(host).textContent, /Stock aliquot100 µL/);
  assert.match(output(host).textContent, /Final total volume100 µL/);
  assert.match(output(host).textContent, /no dilution required/i);
  setValue(host, 'target-concentration', '5');
  noResult(host);
  submit(host);
  assert.match(output(host).textContent, /Stock aliquot10 µL/);
}));

test('tampered units fail closed rather than being silently interpreted as supported units', () => fixture(({ host, panel }) => {
  panel.setCompound(salt());
  setValue(host, 'amount', '5.844');
  setValue(host, 'volume', '100');
  setUnit(host, 'amount', 'kg');
  submit(host);
  noResult(host);
  assert.equal(error(host).hidden, false);
  setUnit(host, 'amount', 'g');
  setUnit(host, 'volume', 'gallons');
  submit(host);
  noResult(host);
  assert.equal(error(host).hidden, false);
  clickMode(host, 'Dilute a stock');
  setValue(host, 'stock-concentration', '1');
  setValue(host, 'target-concentration', '0.1');
  setValue(host, 'final-volume', '100');
  setUnit(host, 'target-concentration', 'percent');
  submit(host);
  noResult(host);
  assert.equal(error(host).hidden, false);
}));

test('anonymous instances still get unique IDs and labels are associated with every numeric input', () => fixture(() => {
  const hosts = [new FakeElement('details'), new FakeElement('details')];
  hosts.forEach((host) => new SolutionCalculatorPanel(host));
  const ids = hosts.flatMap((host) => descendants(host).map((element) => element.id).filter(Boolean));
  assert.equal(new Set(ids).size, ids.length);
  for (const host of hosts) {
    const labels = descendants(host).filter((element) => element.tagName === 'LABEL');
    for (const input of descendants(host).filter((element) => element.tagName === 'INPUT')) {
      assert.ok(input.id);
      assert.equal(labels.filter((label) => label.htmlFor === input.id).length, 1);
    }
    for (const select of descendants(host).filter((element) => element.tagName === 'SELECT')) {
      assert.match(select.getAttribute('aria-label'), /^Unit for /);
    }
  }
}));

test('valid finite values cannot become Infinity or zero merely from five-significant-digit display rounding', () => fixture(({ host }) => {
  setUnit(host, 'amount', 'mol');
  setValue(host, 'volume', '1');
  setUnit(host, 'volume', 'L');
  for (const value of [Number.MAX_VALUE, Number.MIN_VALUE]) {
    setValue(host, 'amount', String(value));
    submit(host);
    assert.equal(error(host).hidden, true);
    assert.equal(output(host).hidden, false);
    assert.ok(!/Infinity|NaN/.test(output(host).textContent));
    const facts = output(host).children.filter((element) => element.className === 'solution-fact');
    for (const fact of facts) {
      const displayed = Number.parseFloat(fact.children[1].textContent);
      assert.ok(Number.isFinite(displayed) && displayed > 0);
    }
  }
}));

test('clear amounts discards inputs, errors, and outputs without changing the selected mode', () => fixture(({ host, panel }) => {
  concentration(host, panel);
  clickMode(host, 'Find solute mass');
  setValue(host, 'concentration', '0.1');
  setValue(host, 'volume', '250');
  submit(host);
  assert.equal(output(host).hidden, false);
  clickMode(host, 'Clear amounts');
  noResult(host);
  assert.equal(clickMode(host, 'Find solute mass').getAttribute('aria-pressed'), 'true');
  assert.equal(field(host, 'concentration').value, '');
  assert.equal(field(host, 'volume').value, '');
  assert.equal(field(host, 'molar-mass').value, '58.44');
  assert.match(byClass(host, 'solution-context').textContent, /Sodium chloride/);
  assert.equal(error(host).hidden, true);
}));
