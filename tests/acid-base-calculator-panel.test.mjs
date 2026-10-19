import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const url = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const math = url(transpile(await readFile(new URL('../src/acid-base-calculator.ts', import.meta.url), 'utf8')));
const source = await readFile(new URL('../src/acid-base-calculator-panel.ts', import.meta.url), 'utf8');
const { mountAcidBaseCalculator } = await import(url(transpile(source).replace(/from ['"]\.\/acid-base-calculator['"]/, `from '${math}'`)));

class FakeElement {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = '';
    this.id = '';
    this.hidden = false;
    this.value = '';
    this._textContent = '';
  }
  set textContent(value) { this.children = []; this._textContent = String(value); }
  get textContent() { return this._textContent + this.children.map((child) => child.textContent).join(''); }
  set innerHTML(value) { throw new Error(`Unsafe HTML: ${value}`); }
  append(...children) {
    this.children.push(...children);
    if (this.tagName === 'SELECT' && !this.value) this.value = this.children.find((child) => child.tagName === 'OPTION')?.value ?? '';
  }
  replaceChildren(...children) { this.children = []; this._textContent = ''; this.append(...children); }
  setAttribute(key, value) { this.attributes.set(key, String(value)); }
  getAttribute(key) { return this.attributes.get(key) ?? null; }
  addEventListener(type, listener) { this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]); }
  emit(type) {
    const event = { target: this, preventDefault() {} };
    for (const listener of this.listeners.get(type) ?? []) listener(event);
    return event;
  }
}
const descendants = (host) => host.children.flatMap((child) => [child, ...descendants(child)]);
function find(host, condition) {
  const result = descendants(host).find(condition);
  assert.ok(result, 'Expected element missing');
  return result;
}
const field = (host, key) => find(host, (item) => item.id.endsWith(`-${key}`));
const byClass = (host, name) => find(host, (item) => item.className === name);
const byTag = (host, tag) => find(host, (item) => item.tagName === tag.toUpperCase());
function fixture(run) {
  const original = globalThis.document;
  globalThis.document = { createElement: (tag) => new FakeElement(tag) };
  try {
    const host = new FakeElement('section');
    host.id = 'test-acid-base';
    const panel = mountAcidBaseCalculator(host);
    return run(host, panel);
  } finally {
    if (original === undefined) delete globalThis.document;
    else globalThis.document = original;
  }
}
function set(host, key, value, event = 'input') { const input = field(host, key); input.value = String(value); input.emit(event); }
function unit(host, key, value) {
  const input = field(host, key);
  const row = find(host, (item) => item.className === 'calc-field' && descendants(item).includes(input));
  const select = byTag(row, 'select');
  select.value = value;
  select.emit('change');
}
function submit(host) { byTag(host, 'form').emit('submit'); }
function noResult(host) { assert.equal(byClass(host, 'calc-result').hidden, true); assert.equal(byClass(host, 'calc-result').children.length, 0); }
function strong(host) { set(host, 'kw', 1e-14); set(host, 'concentration', 0.1); submit(host); assert.equal(byClass(host, 'calc-result').hidden, false); }
function choose(host, model) { set(host, 'model', model, 'change'); }
function acidBuffer(host) {
  choose(host, 'buffer');
  set(host, 'kw', 1e-14);
  set(host, 'acid-concentration', 0.1);
  set(host, 'base-concentration', 0.1);
  set(host, 'constant-0', 1.8e-5);
  submit(host);
  assert.equal(byClass(host, 'calc-result').hidden, false);
}

test('all six models are keyboard-native and constants have no silent default', () => fixture((host) => {
  assert.deepEqual(field(host, 'model').children.map((item) => item.value), ['strong-acid', 'strong-base', 'weak-acid', 'weak-base', 'buffer', 'polyprotic']);
  assert.equal(field(host, 'temperature').value, '25');
  assert.equal(field(host, 'kw').value, '');
  assert.equal(field(host, 'concentration').value, '');
  assert.equal(byClass(host, 'calc-error').getAttribute('role'), 'alert');
  assert.equal(byClass(host, 'calc-result').getAttribute('role'), 'status');
  const controls = descendants(host).filter((item) => item.tagName === 'INPUT' || (item.tagName === 'SELECT' && item.id));
  for (const input of controls) assert.ok(descendants(host).some((item) => item.tagName === 'LABEL' && item.htmlFor === input.id));
  assert.equal(byTag(host, 'details').open, undefined);
  noResult(host);
}));

test('strong-acid result is concise and labels its fixed conditions', () => fixture((host) => {
  strong(host);
  assert.match(byClass(host, 'calc-result').textContent, /pH1/);
  assert.match(byClass(host, 'calc-result').textContent, /Ideal model · 25 °C/);
  assert.match(byClass(host, 'calc-result').textContent, /X− \(spectator\)/);
  assert.equal(byClass(host, 'calc-error').hidden, true);
}));

test('input and unit changes clear results immediately', () => fixture((host) => {
  strong(host);
  set(host, 'concentration', 0.2);
  noResult(host);
  submit(host);
  assert.equal(byClass(host, 'calc-result').hidden, false);
  unit(host, 'concentration', 'mmol/L');
  noResult(host);
  submit(host);
  assert.match(byClass(host, 'calc-result').textContent, /pH3\.69897/);
  unit(host, 'kw', 'pK');
  noResult(host);
}));

test('missing constants or numbers show short errors and no result', () => fixture((host) => {
  set(host, 'concentration', 0.1);
  submit(host);
  assert.match(byClass(host, 'calc-error').textContent, /Enter Kw/);
  noResult(host);
  set(host, 'kw', 0);
  submit(host);
  assert.match(byClass(host, 'calc-error').textContent, /must be positive/);
  noResult(host);
  set(host, 'kw', 1e-14);
  set(host, 'concentration', -1);
  submit(host);
  assert.match(byClass(host, 'calc-error').textContent, /between 0/);
  noResult(host);
}));

test('K and pK controls both work, including pKw at other temperatures', () => fixture((host) => {
  set(host, 'temperature', 50);
  set(host, 'concentration', 0);
  unit(host, 'kw', 'pK');
  set(host, 'kw', 13);
  submit(host);
  assert.match(byClass(host, 'calc-result').textContent, /pH6\.5/);
  assert.match(byClass(host, 'calc-result').textContent, /50 °C/);
}));

test('K/pK notation switches clear the old constant instead of reinterpreting its number', () => fixture((host) => {
  acidBuffer(host);
  unit(host, 'kw', 'pK');
  assert.equal(field(host, 'kw').value, '');
  noResult(host);
  set(host, 'kw', 14);
  unit(host, 'constant-0', 'pK');
  assert.equal(field(host, 'constant-0').value, '');
  submit(host);
  assert.match(byClass(host, 'calc-error').textContent, /Enter dissociation constant/);
  noResult(host);
  set(host, 'constant-0', -Math.log10(1.8e-5));
  submit(host);
  assert.equal(byClass(host, 'calc-result').hidden, false);
  unit(host, 'constant-0', 'K');
  assert.equal(field(host, 'constant-0').value, '');
  assert.equal(field(host, 'kw').value, '14');
  noResult(host);
}));

test('changing temperature clears every dissociation/water constant and all entered coefficients', () => fixture((host) => {
  choose(host, 'polyprotic');
  set(host, 'activity', 'entered', 'change');
  set(host, 'kw', 1e-14);
  set(host, 'constant-0', 4.3e-7);
  set(host, 'constant-1', 4.7e-11);
  for (const key of ['gamma-hydrogen', 'gamma-hydroxide', 'gamma-family-0', 'gamma-family-1', 'gamma-family-2', 'gamma-counter-0']) set(host, key, 0.8);
  set(host, 'concentration', 0.033);
  submit(host);
  assert.equal(byClass(host, 'calc-result').hidden, false);
  set(host, 'temperature', 35);
  noResult(host);
  for (const key of ['kw', 'constant-0', 'constant-1', 'gamma-hydrogen', 'gamma-hydroxide', 'gamma-family-0', 'gamma-family-1', 'gamma-family-2', 'gamma-counter-0']) assert.equal(field(host, key).value, '');
  assert.equal(field(host, 'concentration').value, '0.033');
  submit(host);
  assert.match(byClass(host, 'calc-error').textContent, /Enter Kw/);
}));

test('temperature change events also clear constants when no input event occurs', () => fixture((host) => {
  strong(host);
  set(host, 'temperature', 30, 'change');
  assert.equal(field(host, 'kw').value, '');
  noResult(host);
}));

test('changing family/model drops all outdated parameters and constants', () => fixture((host) => {
  acidBuffer(host);
  choose(host, 'weak-base');
  noResult(host);
  assert.equal(field(host, 'kw').value, '');
  assert.equal(field(host, 'constant-0').value, '');
  assert.equal(field(host, 'concentration').value, '');
  assert.equal(descendants(host).some((item) => item.id.endsWith('-acid-concentration')), false);
}));

test('acid/base buffer pair switch changes species/constant labels and clears results', () => fixture((host) => {
  acidBuffer(host);
  set(host, 'buffer-kind', 'base', 'change');
  noResult(host);
  assert.match(host.textContent, /Initial BH\+ concentration/);
  assert.match(host.textContent, /Kb/);
  assert.equal(field(host, 'constant-0').value, '');
  assert.equal(field(host, 'acid-concentration').value, '');
}));

test('triprotic selection adds exactly three constants and four family coefficients', () => fixture((host) => {
  choose(host, 'polyprotic');
  set(host, 'steps', 3, 'change');
  set(host, 'activity', 'entered', 'change');
  assert.ok(field(host, 'constant-2'));
  assert.equal(descendants(host).filter((item) => item.tagName === 'INPUT' && /-gamma-family-\d$/.test(item.id)).length, 4);
  assert.ok(field(host, 'gamma-counter-0'));
  assert.equal(field(host, 'counter-concentration').value, '0');
}));

test('entered activity mode requires even neutral family and zero-concentration spectators', () => fixture((host) => {
  choose(host, 'weak-acid');
  set(host, 'activity', 'entered', 'change');
  set(host, 'kw', 1e-14);
  set(host, 'constant-0', 1.8e-5);
  set(host, 'concentration', 0.1);
  set(host, 'gamma-hydrogen', 0.7);
  set(host, 'gamma-hydroxide', 0.8);
  set(host, 'gamma-family-1', 0.7);
  submit(host);
  noResult(host);
  assert.match(byClass(host, 'calc-error').textContent, /family γ1/);
  set(host, 'gamma-family-0', 1);
  submit(host);
  assert.equal(byClass(host, 'calc-result').hidden, false);
  assert.match(byClass(host, 'calc-result').textContent, /Fixed entered γ model/);
}));

test('Clear removes constants, results and parameters but retains the selected model', () => fixture((host, panel) => {
  acidBuffer(host);
  panel.clear();
  noResult(host);
  assert.equal(field(host, 'model').value, 'buffer');
  assert.equal(field(host, 'kw').value, '');
  assert.equal(field(host, 'acid-concentration').value, '');
  assert.equal(field(host, 'base-concentration').value, '');
  assert.equal(field(host, 'constant-0').value, '');
}));

test('independent panels have unique labelled input ids', () => fixture((host) => {
  const other = new FakeElement('section');
  other.id = host.id;
  mountAcidBaseCalculator(other);
  const ids = descendants(host).concat(descendants(other)).map((item) => item.id).filter(Boolean);
  assert.equal(new Set(ids).size, ids.length);
}));
