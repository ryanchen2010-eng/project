import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const moduleUrl = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const calculator = moduleUrl(transpile(await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8')));
const panel = moduleUrl(transpile(await readFile(new URL('../src/reaction-calculator-panel.ts', import.meta.url), 'utf8'))
  .replace(/from ['"]\.\/reaction-calculator['"]/, `from '${calculator}'`));
const source = await readFile(new URL('../src/calculator-reactions.ts', import.meta.url), 'utf8');
const module = transpile(source).replace(/import ['"]\.\/reaction-calculator\.css['"];?/, '')
  .replace(/from ['"]\.\/reaction-calculator-panel['"]/, `from '${panel}'`)
  .replace(/from ['"]\.\/reaction-calculator['"]/, `from '${calculator}'`);
const { mountReactionAmounts, reviewedCalculatorReactions } = await import(moduleUrl(module));

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = '';
    this.id = '';
    this.hidden = false;
    this.disabled = false;
    this.value = '';
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
  addEventListener(name, listener) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), listener]); }
  emit(name) {
    const event = { target: this, prevented: false, preventDefault() { this.prevented = true; } };
    for (const listener of this.listeners.get(name) ?? []) listener(event);
    return event;
  }
}
const descendants = (element) => element.children.flatMap((child) => [child, ...descendants(child)]);
function find(host, predicate) {
  const element = descendants(host).find(predicate);
  assert.ok(element, 'Expected element was not rendered');
  return element;
}
const byId = (host, id) => find(host, (element) => element.id === id);
const byClass = (host, name) => find(host, (element) => element.className.split(/\s+/).includes(name));
const byTag = (host, tag) => find(host, (element) => element.tagName === tag.toUpperCase());
const choose = (host, id) => { const select = byId(host, `${host.id}-reaction`); select.value = id; select.emit('change'); };
const settle = () => new Promise((resolve) => setImmediate(resolve));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const response = (payload, ok = true) => ({ ok, json: async () => payload });

const substitution = () => ({
  id: 'methanol-sn2', name: 'Bromomethane substitution', family: 'Substitution',
  stoichiometry: {
    balanced: true,
    reactants: [
      { inputSlot: 0, name: 'Bromomethane', formula: 'CH3Br', molarMass: 94.939, coefficient: 1 },
      { inputSlot: 1, name: 'Hydroxide', formula: 'HO−', molarMass: 17.007, coefficient: 1 },
    ],
    product: { name: 'Methanol', formula: 'CH4O', molarMass: 32.042, coefficient: 1 },
    excludedInputs: [], notes: ['Complete conversion is a theoretical assumption.'],
  },
});
const elimination = () => ({
  id: 'tert-butyl-e1', name: 'tert-Butyl bromide elimination', family: 'Elimination',
  stoichiometry: {
    balanced: true,
    reactants: [{ inputSlot: 1, name: 'tert-Butyl bromide', formula: 'C4H9Br', molarMass: 137.018, coefficient: 1 }],
    product: { name: '2-Methylpropene', formula: 'C4H8', molarMass: 56.108, coefficient: 1 },
    excludedInputs: [{ inputSlot: 0, name: 'Water', reason: 'Solvent; not consumed stoichiometrically' }], notes: [],
  },
});
const catalog = () => ({ reactions: [substitution(), elimination()], reactants: [] });

async function fixture(fetcher, run) {
  const previous = { document: globalThis.document, documentPresent: Object.hasOwn(globalThis, 'document'),
    fetch: globalThis.fetch, fetchPresent: Object.hasOwn(globalThis, 'fetch') };
  globalThis.document = { createElement: (tag) => new FakeElement(tag) };
  globalThis.fetch = fetcher;
  try {
    const host = new FakeElement('section');
    host.id = 'reaction-topic';
    const controller = mountReactionAmounts(host);
    return await run({ host, controller });
  } finally {
    if (previous.documentPresent) globalThis.document = previous.document; else delete globalThis.document;
    if (previous.fetchPresent) globalThis.fetch = previous.fetch; else delete globalThis.fetch;
  }
}

function calculateYield(host) {
  const first = byId(host, 'calculator-reactant-0');
  const second = byId(host, 'calculator-reactant-1');
  first.value = '9.4939'; first.emit('input');
  second.value = '1.7007'; second.emit('input');
  byTag(host, 'form').emit('submit');
  assert.equal(byClass(host, 'calculator-output').hidden, false);
  assert.match(byClass(host, 'calculator-output').textContent, /3\.2042 g/);
}

test('only complete validated balanced server stoichiometry is eligible for reaction amounts', () => {
  const valid = substitution();
  const bad = [];
  for (const mutate of [
    (item) => { delete item.stoichiometry; },
    (item) => { item.stoichiometry.balanced = false; },
    (item) => { item.stoichiometry.product.molarMass = NaN; },
    (item) => { item.stoichiometry.reactants[0].coefficient = 0; },
    (item) => { item.stoichiometry.reactants[1].inputSlot = 0; },
    (item) => { item.stoichiometry.notes = { bad: 'not an array' }; },
    (item) => { item.stoichiometry.excludedInputs = [{ inputSlot: 0, name: 'Water', reason: 'Solvent' }]; },
    (item) => { item.name = ''; },
    (item) => { item.stoichiometry.product.formula = ''; },
  ]) {
    const item = substitution();
    item.id = `bad-${bad.length}`;
    mutate(item);
    bad.push(item);
  }
  assert.deepEqual(reviewedCalculatorReactions({ reactions: [...bad, valid] }).map((item) => item.id), [valid.id]);
  assert.deepEqual(reviewedCalculatorReactions({ reactions: [valid, substitution(), elimination()] }).map((item) => item.id), [valid.id, 'tert-butyl-e1']);
});

test('catalog metadata is copied and malformed catalogs fail closed', () => {
  const payload = catalog();
  const reviewed = reviewedCalculatorReactions(payload);
  payload.reactions[0].stoichiometry.reactants[0].molarMass = 999;
  payload.reactions[0].stoichiometry.notes.push('Later mutation');
  assert.equal(reviewed[0].stoichiometry.reactants[0].molarMass, 94.939);
  assert.equal(reviewed[0].stoichiometry.notes.length, 1);
  for (const invalid of [undefined, null, [], {}, { reactions: {} }, { reactions: Array(1001).fill(substitution()) }]) {
    assert.throws(() => reviewedCalculatorReactions(invalid), /unavailable/);
  }
  assert.deepEqual(reviewedCalculatorReactions({ reactions: [] }), []);
});

test('loading is visible and a validated catalog still requires an explicit pathway choice', async () => {
  const pending = deferred();
  let requested;
  await fixture((url) => { requested = url; return pending.promise; }, async ({ host }) => {
    const select = byId(host, 'reaction-topic-reaction');
    assert.equal(requested, '/api/reactions/catalog');
    assert.equal(select.disabled, true);
    assert.match(byClass(host, 'reaction-amounts-status').textContent, /Loading/);
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
    pending.resolve(response(catalog()));
    await settle();
    assert.equal(select.disabled, false);
    assert.equal(select.value, '');
    assert.equal(select.children.length, 3);
    assert.match(select.children[1].textContent, /Bromomethane \+ Hydroxide → Methanol/);
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
    choose(host, 'methanol-sn2');
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, false);
    assert.equal(byId(host, 'reaction-topic-calculator').open, true);
    assert.match(byClass(host, 'reaction-amounts-context').textContent, /Bromomethane \+ Hydroxide → Methanol/);
    calculateYield(host);
  });
});

test('switching pathway removes stale results and omits an E1 solvent from quantity inputs', async () => {
  await fixture(async () => response(catalog()), async ({ host }) => {
    await settle();
    choose(host, 'methanol-sn2');
    calculateYield(host);
    choose(host, 'tert-butyl-e1');
    assert.equal(byClass(host, 'calculator-output').hidden, true);
    assert.equal(byClass(host, 'calculator-output').children.length, 0);
    const inputs = descendants(byClass(host, 'calculator-fields')).filter((element) => element.tagName === 'INPUT');
    assert.equal(inputs.length, 1);
    assert.equal(inputs[0].id, 'calculator-reactant-1');
    assert.equal(inputs[0].value, '');
    assert.match(byClass(host, 'calculator-notes').textContent, /Water: Solvent/);
    choose(host, 'unsupported');
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
    assert.equal(byClass(host, 'calculator-fields').children.length, 0);
  });
});

test('clear removes reaction amounts while keeping an already-loaded catalog available', async () => {
  await fixture(async () => response(catalog()), async ({ host, controller }) => {
    await settle();
    choose(host, 'methanol-sn2');
    calculateYield(host);
    find(host, (element) => element.tagName === 'BUTTON' && element.textContent === 'Clear').emit('click');
    assert.equal(byId(host, 'reaction-topic-reaction').value, '');
    assert.equal(byId(host, 'reaction-topic-reaction').disabled, false);
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
    assert.equal(byClass(host, 'calculator-fields').children.length, 0);
    assert.equal(byClass(host, 'calculator-output').children.length, 0);
    assert.equal(byClass(host, 'reaction-amounts-context').hidden, true);
    choose(host, 'methanol-sn2');
    assert.equal(byId(host, 'calculator-reactant-0').value, '');
  });
});

test('offline failure stays local to this topic and can recover through Retry', async () => {
  let count = 0;
  await fixture(async () => {
    if (++count === 1) throw new Error('Network offline');
    return response(catalog());
  }, async ({ host }) => {
    const unrelated = new FakeElement('div');
    unrelated.textContent = 'Existing independent arithmetic result: 1 mol/L';
    await settle();
    const status = byClass(host, 'reaction-amounts-status');
    assert.equal(status.getAttribute('role'), 'alert');
    assert.match(status.textContent, /Other calculators still work/);
    assert.equal(byId(host, 'reaction-topic-reaction').disabled, true);
    const retry = byClass(host, 'reaction-amounts-retry');
    assert.equal(retry.hidden, false);
    assert.equal(retry.disabled, false);
    retry.emit('click');
    assert.equal(retry.hidden, true);
    assert.match(status.textContent, /Loading/);
    await settle();
    assert.equal(count, 2);
    assert.equal(status.getAttribute('role'), 'status');
    assert.equal(byId(host, 'reaction-topic-reaction').disabled, false);
    assert.equal(unrelated.textContent, 'Existing independent arithmetic result: 1 mol/L');
    choose(host, 'methanol-sn2');
    calculateYield(host);
  });
});

test('HTTP errors, malformed JSON catalogs, and catalogs with no eligible reactions all show Retry', async () => {
  for (const payload of [response(catalog(), false), response({ reactions: 'bad' }), response({ reactions: [{ id: 'bad', name: 'Unbalanced' }] }),
    { ok: true, json: async () => { throw new Error('Invalid JSON'); } }]) {
    await fixture(async () => payload, async ({ host }) => {
      await settle();
      assert.equal(byClass(host, 'reaction-amounts-retry').hidden, false);
      assert.equal(byId(host, 'reaction-topic-reaction').disabled, true);
      assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
      assert.equal(byClass(host, 'reaction-amounts-status').getAttribute('role'), 'alert');
    });
  }
});

test('later retry wins and aborted stale responses cannot populate a replaced catalog', async () => {
  const pending = [deferred(), deferred()];
  const signals = [];
  let count = 0;
  await fixture((url, options) => { signals.push(options.signal); return pending[count++].promise; }, async ({ host }) => {
    byClass(host, 'reaction-amounts-retry').emit('click');
    assert.equal(signals[0].aborted, true);
    pending[1].resolve(response({ reactions: [elimination()] }));
    await settle();
    pending[0].resolve(response({ reactions: [substitution()] }));
    await settle();
    const options = byId(host, 'reaction-topic-reaction').children;
    assert.deepEqual(options.map((option) => option.value), ['', 'tert-butyl-e1']);
  });
});

test('clearing while the catalog is loading cannot select a pathway when the response arrives', async () => {
  const pending = deferred();
  await fixture(() => pending.promise, async ({ host, controller }) => {
    controller.clear();
    pending.resolve(response(catalog()));
    await settle();
    assert.equal(byId(host, 'reaction-topic-reaction').value, '');
    assert.equal(byId(host, 'reaction-topic-calculator').hidden, true);
    assert.equal(byClass(host, 'calculator-output').hidden, true);
  });
});

test('reaction names and property notes remain literal text, not HTML', async () => {
  const reaction = substitution();
  reaction.name = '<img src=x onerror=alert(1)>';
  reaction.stoichiometry.reactants[0].name = '<script>unsafe()</script>';
  reaction.stoichiometry.notes = ['<svg onload=alert(2)>'];
  await fixture(async () => response({ reactions: [reaction] }), async ({ host }) => {
    await settle();
    choose(host, reaction.id);
    assert.match(host.textContent, /<img src=x onerror=alert\(1\)>/);
    assert.match(host.textContent, /<script>unsafe\(\)<\/script>/);
    assert.match(host.textContent, /<svg onload=alert\(2\)>/);
    assert.equal(descendants(host).some((element) => ['IMG', 'SCRIPT', 'SVG'].includes(element.tagName)), false);
    assert.equal(byId(host, 'reaction-topic-reaction').getAttribute('aria-describedby'), 'reaction-topic-status');
    assert.equal(byClass(host, 'reaction-amounts-status').getAttribute('aria-live'), 'polite');
  });
});

test('standalone reaction arithmetic never imports or initializes the viewer or full Reaction Lab', () => {
  assert.match(source, /import '\.\/reaction-calculator\.css'/);
  assert.doesNotMatch(source, /import ['"]\.\/reaction-lab(?:\.css)?['"]/);
  assert.doesNotMatch(source, /createViewer|3Dmol|Ketcher|\/api\/reactions\/run/);
});
