import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const transpile = source => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = output => `data:text/javascript;base64,${Buffer.from(output).toString('base64')}`;
const eqUrl = url(transpile(await readFile(new URL('../src/equilibrium-calculator.ts', import.meta.url), 'utf8')));
const solUrl = url(transpile(await readFile(new URL('../src/solubility-calculator.ts', import.meta.url), 'utf8')).replace(/from ['"]\.\/equilibrium-calculator['"]/, `from '${eqUrl}'`));
const eqPanelOutput = transpile(await readFile(new URL('../src/equilibrium-calculator-panel.ts', import.meta.url), 'utf8')).replace(/from ['"]\.\/equilibrium-calculator['"]/, `from '${eqUrl}'`);
const solPanelOutput = transpile(await readFile(new URL('../src/solubility-calculator-panel.ts', import.meta.url), 'utf8')).replace(/from ['"]\.\/solubility-calculator['"]/, `from '${solUrl}'`);
const { mountEquilibriumCalculator } = await import(url(eqPanelOutput));
const { mountSolubilityCalculator } = await import(url(solPanelOutput));

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase(); this.children = []; this.listeners = new Map(); this.attributes = new Map();
    this.className = ''; this.id = ''; this.hidden = false; this.value = ''; this.checked = false; this.disabled = false; this._textContent = ''; this.parent = undefined;
  }
  set textContent(value) { this.children = []; this._textContent = String(value); }
  get textContent() { return this._textContent + this.children.map(child => child.textContent).join(''); }
  get valueAsNumber() { return this.value.trim() ? Number(this.value) : NaN; }
  set innerHTML(value) { throw new Error(`Unsafe innerHTML: ${value}`); }
  append(...children) {
    for (const child of children) { this.children.push(child); child.parent = this; }
    if (this.tagName === 'SELECT' && !this.value) this.value = this.children.find(child => child.tagName === 'OPTION')?.value ?? '';
  }
  replaceChildren(...children) { this.children = []; this._textContent = ''; this.append(...children); }
  remove() { if (this.parent) this.parent.children.splice(this.parent.children.indexOf(this), 1); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  addEventListener(name, callback) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), callback]); }
  emit(name) { const event = { target: this, preventDefault() {} }; for (const handler of this.listeners.get(name) ?? []) handler(event); }
}
function descendants(element) { return element.children.flatMap(child => [child, ...descendants(child)]); }
function find(host, predicate) { const item = descendants(host).find(predicate); assert.ok(item, 'Expected rendered control'); return item; }
function key(host, suffix) { return find(host, item => item.id.endsWith(`-${suffix}`)); }
function output(host) { return find(host, item => item.className === 'calc-result'); }
function error(host) { return find(host, item => item.className === 'calc-error'); }
function submit(host) { find(host, item => item.tagName === 'FORM').emit('submit'); }
function button(host, label) { return find(host, item => item.tagName === 'BUTTON' && item.textContent === label); }
function set(host, suffix, value, event = 'input') { const item = key(host, suffix); item.value = String(value); item.emit(event); return item; }
function fixture(mount, run) {
  const previous = { present: Object.hasOwn(globalThis, 'document'), value: globalThis.document };
  globalThis.document = { createElement: tag => new FakeElement(tag) };
  try { const host = new FakeElement('section'); const panel = mount(host); return run({ host, panel }); }
  finally { if (previous.present) globalThis.document = previous.value; else delete globalThis.document; }
}
function validEquilibrium(host) {
  key(host, 'balanced').checked = true;
  set(host, 'row-1-concentration', '.1'); set(host, 'row-2-concentration', '.2'); submit(host);
  assert.equal(error(host).hidden, true); assert.equal(output(host).hidden, false);
  assert.match(output(host).textContent, /Q: 2/);
}
function validSolubility(host) { set(host, 'constant', '1e-10'); submit(host); assert.equal(error(host).hidden, true); assert.equal(output(host).hidden, false); }
function noResult(host) { assert.equal(output(host).hidden, true); assert.equal(output(host).children.length, 0); }

test('equilibrium exposes four modes, labelled native controls and a collapsed reference', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  assert.deepEqual(key(host, 'mode').children.map(item => item.value), ['q', 'k', 'compare', 'solve']);
  for (const input of descendants(host).filter(item => (item.tagName === 'INPUT' || item.tagName === 'SELECT') && item.type !== 'checkbox')) assert.ok(descendants(host).some(label => label.tagName === 'LABEL' && label.htmlFor === input.id));
  assert.equal(output(host).getAttribute('aria-live'), 'polite');
  assert.equal(error(host).getAttribute('role'), 'alert');
  assert.ok(descendants(host).some(item => item.tagName === 'DETAILS'));
  assert.equal(key(host, 'row-1-gamma').disabled, true);
}));

test('equilibrium current inputs use chosen units and edits clear stale results', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  validEquilibrium(host); set(host, 'row-1-unit', 'mmol/L', 'change'); noResult(host);
  submit(host); assert.match(output(host).textContent, /Q: 2000/);
  set(host, 'row-1-name', 'Other identity'); noResult(host);
  submit(host); set(host, 'row-1-side', 'product', 'change'); noResult(host); submit(host); assert.match(error(host).textContent, /reactant/);
}));

test('equilibrium K mode rejects exact zero/undefined rather than displaying a fake constant', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'mode', 'k', 'change');
  set(host, 'row-1-concentration', '1'); set(host, 'row-2-concentration', '0'); submit(host);
  assert.match(error(host).textContent, /positive finite equilibrium constant/); noResult(host);
}));

test('equilibrium zero quotients retain honest explanations and compare direction', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'row-1-concentration', '0'); set(host, 'row-2-concentration', '0'); submit(host);
  assert.match(output(host).textContent, /Undefined.*0\/0/);
  set(host, 'mode', 'compare', 'change'); set(host, 'constant', '1'); submit(host);
  assert.match(error(host).textContent, /undefined quotient/); noResult(host);
  set(host, 'row-1-concentration', '1'); submit(host); assert.match(output(host).textContent, /Q: 0/); assert.match(output(host).textContent, /forward/);
}));

test('equilibrium ICE solves exact-zero initial products and labels assumptions', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'mode', 'solve', 'change');
  set(host, 'row-1-concentration', '1'); set(host, 'row-2-concentration', '0'); set(host, 'constant', '1'); submit(host);
  assert.match(output(host).textContent, /A: 0\.5 mol\/L/); assert.match(output(host).textContent, /B: 0\.5 mol\/L/);
  assert.match(output(host).textContent, /Ideal.*25 °C.*1 mol\/L/);
}));

test('equilibrium entered mode requires every dissolved gamma and excludes pure phases', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'activity', 'entered', 'change');
  set(host, 'row-1-concentration', '1'); set(host, 'row-2-concentration', '1'); submit(host);
  assert.match(error(host).textContent, /activity coefficient/); noResult(host);
  set(host, 'row-1-gamma', '.5'); set(host, 'row-2-gamma', '1'); submit(host); assert.match(output(host).textContent, /Q: 2/);
  set(host, 'row-1-phase', 'solid', 'change'); noResult(host);
  assert.equal(key(host, 'row-1-concentration').disabled, true); assert.equal(key(host, 'row-1-gamma').disabled, true);
  submit(host); assert.match(output(host).textContent, /Q: 1/);
}));

test('equilibrium fixed spectators are explicit and their gamma cannot be omitted', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'activity', 'entered', 'change');
  set(host, 'row-1-name', 'A+'); set(host, 'row-2-name', 'B+'); set(host, 'row-1-charge', '1'); set(host, 'row-2-charge', '1');
  set(host, 'row-1-concentration', '.1'); set(host, 'row-2-concentration', '.1'); set(host, 'row-1-gamma', '1'); set(host, 'row-2-gamma', '1');
  button(host, 'Add fixed spectator / counterion').emit('click'); set(host, 'spectator-1-name', 'X-'); set(host, 'spectator-1-charge', '-1'); set(host, 'spectator-1-concentration', '.2'); submit(host);
  assert.match(error(host).textContent, /activity coefficient/);
  set(host, 'spectator-1-gamma', '.8'); submit(host); assert.match(output(host).textContent, /Q: 1/);
}));

test('temperature changes clear equilibrium constant and every reacting/spectator gamma', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  validEquilibrium(host); set(host, 'mode', 'compare', 'change'); set(host, 'constant', '1');
  set(host, 'row-1-gamma', '.8'); set(host, 'row-2-gamma', '.7'); button(host, 'Add fixed spectator / counterion').emit('click'); set(host, 'spectator-1-gamma', '.9');
  set(host, 'temperature', '30'); noResult(host);
  for (const suffix of ['constant', 'row-1-gamma', 'row-2-gamma', 'spectator-1-gamma']) assert.equal(key(host, suffix).value, '');
  assert.match(host.textContent, /Temperature changed/);
}));

test('equilibrium add/remove/clear clears stale structures and resets confirmation', () => fixture(mountEquilibriumCalculator, ({ host, panel }) => {
  validEquilibrium(host); button(host, 'Add species').emit('click'); noResult(host);
  assert.ok(key(host, 'row-3-name')); button(host, 'Remove species').emit('click'); noResult(host);
  panel.clear(); assert.equal(key(host, 'balanced').checked, false); assert.equal(key(host, 'row-1-concentration').value, '');
  assert.equal(descendants(host).filter(item => item.tagName === 'FIELDSET').length, 2);
}));

test('equilibrium unit underflow and unsupported unit values fail closed', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  key(host, 'balanced').checked = true; set(host, 'row-1-concentration', '5e-324'); set(host, 'row-1-unit', 'µmol/L', 'change'); set(host, 'row-2-concentration', '1'); submit(host);
  assert.match(error(host).textContent, /conversion.*numeric range/); noResult(host);
  set(host, 'row-1-concentration', '1'); set(host, 'row-1-unit', 'unknown', 'change'); submit(host); assert.match(error(host).textContent, /supported concentration unit/);
}));

test('solubility exposes two modes with explicit formula-unit output', () => fixture(mountSolubilityCalculator, ({ host }) => {
  validSolubility(host); assert.match(output(host).textContent, /0\.00001 mol\/L \(formula units\)/);
  assert.deepEqual(key(host, 'mode').children.map(item => item.value), ['solubility', 'compare']);
  for (const input of descendants(host).filter(item => item.tagName === 'INPUT' || item.tagName === 'SELECT')) assert.ok(descendants(host).some(label => label.tagName === 'LABEL' && label.htmlFor === input.id));
}));

test('solubility changes to inputs, units, model and constants invalidate results', () => fixture(mountSolubilityCalculator, ({ host }) => {
  validSolubility(host); set(host, 'ion-1-unit', 'mmol/L', 'change'); noResult(host); submit(host);
  set(host, 'activity', 'entered', 'change'); noResult(host); submit(host); assert.match(error(host).textContent, /activity coefficient/);
  set(host, 'ion-1-gamma', '.5'); set(host, 'ion-2-gamma', '.8'); submit(host); assert.equal(output(host).hidden, false);
  set(host, 'constant-type', 'pK', 'change'); noResult(host); assert.equal(key(host, 'constant').value, '');
}));

test('solubility common-ion spectator row balances charge and must have nonideal gamma', () => fixture(mountSolubilityCalculator, ({ host }) => {
  set(host, 'ion-1-name', 'Ag+'); set(host, 'ion-2-name', 'Cl-'); set(host, 'ion-2-concentration', '.01'); set(host, 'constant', '1e-10'); submit(host);
  assert.match(error(host).textContent, /spectator counterion/); noResult(host);
  button(host, 'Add fixed spectator / counterion').emit('click'); set(host, 'spectator-1-name', 'Na+'); set(host, 'spectator-1-charge', '1'); set(host, 'spectator-1-concentration', '10'); set(host, 'spectator-1-unit', 'mmol/L', 'change'); submit(host);
  assert.equal(error(host).hidden, true); assert.match(output(host).textContent, /Na\+: 0\.01 mol\/L · fixed spectator/);
  set(host, 'activity', 'entered', 'change'); set(host, 'ion-1-gamma', '.8'); set(host, 'ion-2-gamma', '.8'); submit(host);
  assert.match(error(host).textContent, /spectator activity coefficient/); noResult(host);
  set(host, 'spectator-1-gamma', '.8'); submit(host); assert.equal(output(host).hidden, false);
}));

test('solubility temperature edit cannot reuse any previous constant or gamma', () => fixture(mountSolubilityCalculator, ({ host }) => {
  validSolubility(host); set(host, 'ion-1-gamma', '.8'); set(host, 'ion-2-gamma', '.8'); button(host, 'Add fixed spectator / counterion').emit('click'); set(host, 'spectator-1-gamma', '.8');
  set(host, 'temperature', '40', 'change'); noResult(host);
  for (const suffix of ['constant', 'ion-1-gamma', 'ion-2-gamma', 'spectator-1-gamma']) assert.equal(key(host, suffix).value, '');
  submit(host); assert.match(error(host).textContent, /solubility constant/);
}));

test('supersaturation is reported by comparison and not a fake dissolution result', () => fixture(mountSolubilityCalculator, ({ host }) => {
  set(host, 'constant', '1e-10'); set(host, 'ion-1-concentration', '.001'); set(host, 'ion-2-concentration', '.001'); submit(host);
  assert.match(error(host).textContent, /already supersaturated/); noResult(host);
  set(host, 'mode', 'compare', 'change'); submit(host); assert.match(output(host).textContent, /supersaturated/);
  assert.match(output(host).textContent, /rate is not calculated/);
}));

test('solubility conversion underflow and unknown units do not silently turn into zero or molarity', () => fixture(mountSolubilityCalculator, ({ host }) => {
  set(host, 'constant', '1e-10'); set(host, 'ion-1-concentration', '5e-324'); set(host, 'ion-1-unit', 'µmol/L', 'change'); submit(host);
  assert.match(error(host).textContent, /conversion.*numeric range/); noResult(host);
  set(host, 'ion-1-concentration', '0'); set(host, 'ion-1-unit', 'unknown', 'change'); submit(host); assert.match(error(host).textContent, /supported concentration unit/);
}));

test('clear removes spectator rows and does not retain a hidden result or old constant', () => fixture(mountSolubilityCalculator, ({ host, panel }) => {
  validSolubility(host); button(host, 'Add fixed spectator / counterion').emit('click'); panel.clear(); noResult(host);
  assert.equal(key(host, 'constant').value, ''); assert.equal(key(host, 'ion-1-concentration').value, '0');
  assert.equal(descendants(host).filter(item => item.tagName === 'FIELDSET').length, 2);
}));

test('two panel instances never reuse control identifiers and names stay safe text', () => fixture(mountEquilibriumCalculator, ({ host }) => {
  validEquilibrium(host); set(host, 'row-1-name', '<img src=x>'); submit(host);
  assert.ok(!descendants(host).some(item => item.tagName === 'IMG'));
  const second = new FakeElement('section'); mountEquilibriumCalculator(second); const ids = new Set(descendants(host).map(item => item.id).filter(Boolean));
  assert.ok(descendants(second).filter(item => item.id).every(item => !ids.has(item.id)));
}));
