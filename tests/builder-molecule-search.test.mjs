import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const source = await readFile(new URL('../src/builder-molecule-search.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
});

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = '';
    this.id = '';
    this.value = '';
    this.disabled = false;
    this.hidden = false;
    this._textContent = '';
    this.htmlWrites = [];
    this.classList = {
      add: (...names) => { this.className = [...new Set([...this.classes(), ...names])].join(' '); },
      contains: (name) => this.classes().includes(name),
      toggle: (name, enabled) => {
        const chosen = enabled ?? !this.classes().includes(name);
        this.className = [...this.classes().filter((item) => item !== name), ...(chosen ? [name] : [])].join(' ');
        return chosen;
      },
    };
  }
  classes() { return this.className.split(/\s+/).filter(Boolean); }
  set textContent(value) { this._textContent = String(value); this.children = []; }
  get textContent() { return this._textContent + this.children.map((item) => item.textContent).join(''); }
  set innerHTML(value) {
    // Only the fixed constructor template is parsed. Result rendering must use
    // real element creation and textContent, never interpolate service data.
    assert.equal(this.tagName, 'SECTION');
    assert.equal(this.htmlWrites.length, 0, 'the search must not rewrite its DOM with result HTML');
    assert.match(value, /<form aria-label="Find a Molecule for Builder">/);
    this.htmlWrites.push(value);
    const form = new FakeElement('form');
    const input = new FakeElement('input');
    input.id = 'builder-molecule-name';
    input.disabled = true;
    const button = new FakeElement('button');
    button.disabled = true;
    const status = new FakeElement('p');
    status.id = 'builder-search-status';
    status.textContent = 'Available when the drawing editor is ready.';
    const results = new FakeElement('ul');
    results.className = 'builder-search-results';
    results.hidden = true;
    form.append(input, button);
    this.append(form, status, results);
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._textContent = ''; this.children = [...children]; }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  addEventListener(name, callback) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), callback]); }
  emit(name, extra = {}) {
    const event = { prevented: false, preventDefault() { this.prevented = true; }, target: this, ...extra };
    for (const callback of this.listeners.get(name) ?? []) callback(event);
    return event;
  }
  click() { if (!this.disabled) this.emit('click'); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  querySelectorAll(selector) {
    return descendants(this).filter((item) => selector.startsWith('#')
      ? item.id === selector.slice(1)
      : selector.startsWith('.') ? item.classes().includes(selector.slice(1)) : item.tagName === selector.toUpperCase());
  }
}
const descendants = (host) => host.children.flatMap((item) => [item, ...descendants(item)]);
const settle = async () => { await new Promise(setImmediate); await new Promise(setImmediate); };
const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const ethanol = Object.freeze({ cid: 702, name: 'Ethanol', formula: 'C2H6O', structure: 'CCO', iupacName: 'ethanol' });
const reply = (results, extra = {}) => ({ ok: true, json: async () => ({ results, ...extra }) });

function harness({ fetcher = async () => reply([ethanol]), blank = true, confirm = true, canImport = true, setMolecule } = {}) {
  const calls = { fetch: [], structures: [], imported: [], confirms: [], locks: 0, releases: 0 };
  const timers = new Map();
  let timerId = 0;
  const state = { blank, canImport, editorPresent: true, confirm };
  const editor = {
    editor: { struct: () => ({ isBlank: () => state.blank }) },
    setMolecule: async (structure) => { calls.structures.push(structure); return setMolecule?.(structure); },
  };
  const context = {
    exports: {}, AbortController, Error, TypeError, SyntaxError,
    document: { createElement: (tagName) => new FakeElement(tagName) },
    window: {
      setTimeout: (callback) => { const id = ++timerId; timers.set(id, callback); return id; },
      clearTimeout: (id) => timers.delete(id),
      confirm: (text) => { calls.confirms.push(text); return state.confirm; },
    },
    fetch: (url, options) => { calls.fetch.push({ url, options }); return fetcher(url, options); },
  };
  const Search = new vm.Script(`${outputText}\nexports.BuilderMoleculeSearch;`).runInNewContext(context);
  const host = new FakeElement('section');
  const search = new Search(host, {
    getEditor: () => state.editorPresent ? editor : null,
    canImport: () => state.canImport,
    lockEditor: () => { calls.locks += 1; return () => { calls.releases += 1; }; },
    onImported: (match) => { calls.imported.push(match); },
  });
  const input = host.querySelector('input');
  const form = host.querySelector('form');
  const submit = form.querySelector('button');
  const results = host.querySelector('ul');
  const status = host.querySelector('#builder-search-status');
  const enter = (value) => { input.value = value; input.emit('input'); };
  const query = async (value) => { enter(value); form.emit('submit'); await settle(); };
  const loads = () => results.querySelectorAll('button');
  return { search, host, form, input, submit, results, status, enter, query, loads, calls, state, timers };
}

test('name search waits for the editable drawing to be ready and preserves native form submission', async () => {
  const h = harness();
  assert.equal(h.input.disabled, true);
  assert.equal(h.submit.disabled, true);
  h.input.value = 'ethanol';
  assert.equal(h.form.emit('submit').prevented, true);
  await settle();
  assert.equal(h.calls.fetch.length, 0);
  h.search.setReady(true);
  assert.equal(h.input.disabled, false);
  assert.equal(h.submit.disabled, false);
  assert.match(h.status.textContent, /choose the exact compound/i);
  h.search.setReady(false);
  assert.equal(h.input.disabled, true);
});

test('typing never searches or imports; explicit submission trims and encodes the query', async () => {
  const h = harness();
  h.search.setReady(true);
  h.enter('  (R)-2-butanol + water  ');
  await settle();
  assert.equal(h.calls.fetch.length, 0);
  h.form.emit('submit');
  await settle();
  assert.equal(h.calls.fetch[0].url, '/api/pubchem/search?q=(R)-2-butanol%20%2B%20water');
  assert.ok(h.calls.fetch[0].options.signal instanceof AbortSignal);
  assert.equal(h.loads().length, 1);
  assert.equal(h.results.hidden, false);
  assert.equal(h.calls.structures.length, 0, 'a returned result is not an instruction to replace the drawing');
  assert.match(h.results.textContent, /Ethanol/);
  assert.match(h.results.textContent, /C2H6O · PubChem CID 702/);
  assert.equal(h.timers.size, 0);
});

test('blank and overlong queries fail locally without modifying the editor', async () => {
  const h = harness();
  h.search.setReady(true);
  for (const query of [' ', 'x'.repeat(101)]) {
    await h.query(query);
    assert.match(h.status.textContent, /1–100 characters/);
    assert.equal(h.status.classList.contains('is-error'), true);
  }
  assert.equal(h.calls.fetch.length, 0);
  assert.equal(h.calls.structures.length, 0);
});

test('selection imports the exact isomeric structure, name and CID, not a same-formula substitute', async () => {
  const matches = [
    { cid: 439258, name: '(R)-Butan-2-ol', formula: 'C4H10O', structure: 'CC[C@@H](C)O', iupacName: '(2R)-butan-2-ol' },
    { cid: 439259, name: '(S)-Butan-2-ol', formula: 'C4H10O', structure: 'CC[C@H](C)O', iupacName: '(2S)-butan-2-ol' },
  ];
  const h = harness({ fetcher: async () => reply(matches) });
  h.search.setReady(true);
  await h.query('butan-2-ol');
  assert.equal(h.loads().length, 2);
  assert.match(h.loads()[1].getAttribute('aria-label'), /\(S\)-Butan-2-ol, CID 439259/);
  h.loads()[1].click();
  await settle();
  assert.deepEqual(h.calls.structures, [matches[1].structure]);
  assert.equal(h.calls.imported[0], matches[1]);
  assert.match(h.status.textContent, /\(S\)-Butan-2-ol \(PubChem CID 439259\) loaded/);
  assert.equal(h.calls.confirms.length, 0, 'blank drawings need no replacement confirmation');
  assert.equal(h.calls.fetch.length, 1, 'import must not guess identity or ask for a 3D SDF');
  assert.equal(h.calls.locks, 1);
  assert.equal(h.calls.releases, 1);
});

test('only duplicate exact CIDs are deduplicated, while formula-isomers stay separately selectable', async () => {
  const ether = { cid: 8254, name: 'Dimethyl ether', formula: 'C2H6O', structure: 'COC', iupacName: 'methoxymethane' };
  const h = harness({ fetcher: async () => reply([ethanol, ethanol, ether]) });
  h.search.setReady(true);
  await h.query('C2H6O');
  assert.equal(h.loads().length, 2);
  h.loads()[1].click();
  await settle();
  assert.deepEqual(h.calls.structures, ['COC']);
  assert.equal(h.calls.imported[0].cid, 8254);
});

test('canceling replacement preserves the existing drawing and does not enter import state', async () => {
  const h = harness({ blank: false, confirm: false });
  h.search.setReady(true);
  await h.query('ethanol');
  h.loads()[0].click();
  await settle();
  assert.equal(h.calls.confirms.length, 1);
  assert.match(h.calls.confirms[0], /Replace the current drawing with Ethanol \(PubChem CID 702\)/);
  assert.deepEqual(h.calls.structures, []);
  assert.deepEqual(h.calls.imported, []);
  assert.equal(h.calls.locks, 0);
  assert.match(h.status.textContent, /cancelled.*unchanged/i);
  assert.equal(h.host.getAttribute('aria-busy'), 'false');
});

test('replacement checks the current drawing at selection time, not when search started', async () => {
  const pending = deferred();
  const h = harness({ fetcher: () => pending.promise, confirm: false });
  h.search.setReady(true);
  h.enter('ethanol');
  h.form.emit('submit');
  h.state.blank = false;
  pending.resolve(reply([ethanol]));
  await settle();
  h.loads()[0].click();
  await settle();
  assert.equal(h.calls.confirms.length, 1);
  assert.equal(h.calls.structures.length, 0);
});

test('a busy existing preview or example blocks import without changing the drawing', async () => {
  const h = harness({ canImport: false, blank: false });
  h.search.setReady(true);
  await h.query('ethanol');
  h.loads()[0].click();
  await settle();
  assert.match(h.status.textContent, /Wait for the current drawing or preview operation/);
  assert.equal(h.calls.confirms.length, 0);
  assert.equal(h.calls.locks, 0);
  assert.equal(h.calls.structures.length, 0);
});

test('missing or no-longer-ready editors cannot import a result', async () => {
  const h = harness();
  h.search.setReady(true);
  await h.query('ethanol');
  h.state.editorPresent = false;
  h.loads()[0].click();
  await settle();
  assert.equal(h.calls.structures.length, 0);
  h.state.editorPresent = true;
  h.search.setReady(false);
  assert.equal(h.loads()[0].disabled, true);
  h.loads()[0].emit('click');
  await settle();
  assert.equal(h.calls.structures.length, 0);
});

test('a pending import locks editor/search and rejects concurrent programmatic loads', async () => {
  const pending = deferred();
  const h = harness({ setMolecule: () => pending.promise, blank: false });
  h.search.setReady(true);
  await h.query('ethanol');
  const button = h.loads()[0];
  button.click();
  assert.equal(h.input.disabled, true);
  assert.equal(h.submit.disabled, true);
  assert.equal(button.disabled, true);
  assert.equal(h.host.getAttribute('aria-busy'), 'true');
  button.emit('click');
  h.form.emit('submit');
  await settle();
  assert.equal(h.calls.structures.length, 1);
  assert.equal(h.calls.fetch.length, 1);
  assert.equal(h.calls.imported.length, 0);
  assert.equal(h.calls.releases, 0);
  pending.resolve();
  await settle();
  assert.equal(h.calls.imported.length, 1);
  assert.equal(h.calls.releases, 1);
  assert.equal(h.input.disabled, false);
  assert.equal(h.submit.disabled, false);
  assert.equal(h.host.getAttribute('aria-busy'), 'false');
});

test('editor load failures release the lock, do not publish an imported identity and allow retry', async () => {
  let fail = true;
  const h = harness({ setMolecule: async () => { if (fail) throw new Error('Ketcher rejected the structure'); } });
  h.search.setReady(true);
  await h.query('ethanol');
  h.loads()[0].click();
  await settle();
  assert.equal(h.calls.imported.length, 0);
  assert.equal(h.calls.releases, 1);
  assert.match(h.status.textContent, /editor could not load.*Check your drawing/i);
  assert.equal(h.status.classList.contains('is-error'), true);
  assert.equal(h.input.disabled, false);
  fail = false;
  h.loads()[0].click();
  await settle();
  assert.equal(h.calls.imported.length, 1);
  assert.equal(h.calls.releases, 2);
});

test('later drawing edits clear the loaded-record claim without silently renaming the modified structure', async () => {
  const h = harness();
  h.search.setReady(true);
  await h.query('ethanol');
  h.loads()[0].click();
  await settle();
  assert.match(h.status.textContent, /CID 702\) loaded/);
  h.search.drawingChanged();
  assert.match(h.status.textContent, /Drawing edited/);
  assert.match(h.status.textContent, /original PubChem records, not your modified structure/);
  assert.doesNotMatch(h.status.textContent, /CID 702\) loaded/);
  assert.equal(h.calls.structures.length, 1);
  assert.equal(h.calls.imported.length, 1);
});

test('editing a submitted query clears stale results and ignores its later response', async () => {
  const pending = deferred();
  const h = harness({ fetcher: () => pending.promise });
  h.search.setReady(true);
  h.enter('ethanol');
  h.form.emit('submit');
  const signal = h.calls.fetch[0].options.signal;
  assert.equal(h.submit.disabled, true);
  assert.equal(h.input.disabled, false, 'the user can correct a pending query');
  h.enter('methanol');
  assert.equal(signal.aborted, true);
  assert.equal(h.submit.disabled, false);
  pending.resolve(reply([ethanol]));
  await settle();
  assert.equal(h.results.hidden, true);
  assert.equal(h.loads().length, 0);
  assert.equal(h.status.textContent, '');
  assert.equal(h.calls.structures.length, 0);
});

test('a repeated identical query is protected by request identity, not just matching query text', async () => {
  const first = deferred();
  const second = deferred();
  let attempt = 0;
  const h = harness({ fetcher: () => (++attempt === 1 ? first.promise : second.promise) });
  h.search.setReady(true);
  h.enter('ethanol');
  h.form.emit('submit');
  h.form.emit('submit');
  assert.equal(h.calls.fetch.length, 2);
  assert.equal(h.calls.fetch[0].options.signal.aborted, true);
  second.resolve(reply([ethanol]));
  await settle();
  assert.equal(h.loads().length, 1);
  first.resolve(reply([{ ...ethanol, name: 'Outdated response', structure: 'wrong' }]));
  await settle();
  assert.match(h.results.textContent, /Ethanol/);
  assert.doesNotMatch(h.results.textContent, /Outdated/);
  h.loads()[0].click();
  await settle();
  assert.deepEqual(h.calls.structures, ['CCO']);
});

test('stale request failures cannot overwrite newer successful results', async () => {
  const pending = deferred();
  let attempt = 0;
  const h = harness({ fetcher: () => (++attempt === 1 ? pending.promise : Promise.resolve(reply([ethanol]))) });
  h.search.setReady(true);
  h.enter('old');
  h.form.emit('submit');
  await h.query('ethanol');
  pending.reject(new Error('Old request failed'));
  await settle();
  assert.match(h.status.textContent, /1 structure found/);
  assert.equal(h.status.classList.contains('is-error'), false);
  assert.equal(h.loads().length, 1);
});

test('empty searches have an actionable non-error state and preserve the drawing', async () => {
  const h = harness({ fetcher: async () => reply([]) });
  h.search.setReady(true);
  await h.query('no such molecule');
  assert.match(h.status.textContent, /No matching molecule.*common or full chemical name.*drawing is unchanged/i);
  assert.equal(h.status.classList.contains('is-error'), false);
  assert.equal(h.results.hidden, true);
  assert.equal(h.calls.structures.length, 0);
});

for (const [name, fetcher] of [
  ['HTTP failure', async () => ({ ok: false, json: async () => ({ error: 'PubChem lookup failed' }) })],
  ['service error payload', async () => ({ ok: true, json: async () => ({ error: 'Rate limit reached' }) })],
  ['network failure', async () => { throw new TypeError('offline'); }],
  ['invalid JSON', async () => ({ ok: true, json: async () => { throw new SyntaxError('invalid json'); } })],
]) {
  test(`${name} does not load or identify a molecule and restores search controls`, async () => {
    const h = harness({ fetcher });
    h.search.setReady(true);
    await h.query('ethanol');
    assert.equal(h.calls.structures.length, 0);
    assert.equal(h.calls.imported.length, 0);
    assert.equal(h.loads().length, 0);
    assert.equal(h.results.hidden, true);
    assert.match(h.status.textContent, /drawing is unchanged/i);
    assert.equal(h.status.classList.contains('is-error'), true);
    assert.equal(h.input.disabled, false);
    assert.equal(h.submit.disabled, false);
    assert.equal(h.host.getAttribute('aria-busy'), 'false');
    assert.equal(h.timers.size, 0);
  });
}

test('timeout aborts the lookup, preserves the drawing and provides retry guidance', async () => {
  const h = harness({ fetcher: (_url, { signal }) => new Promise((_resolve, reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')));
  }) });
  h.search.setReady(true);
  h.enter('ethanol');
  h.form.emit('submit');
  assert.equal(h.timers.size, 1);
  [...h.timers.values()][0]();
  await settle();
  assert.equal(h.calls.fetch[0].options.signal.aborted, true);
  assert.match(h.status.textContent, /Search timed out.*Try again.*unchanged/i);
  assert.equal(h.calls.structures.length, 0);
  assert.equal(h.submit.disabled, false);
  assert.equal(h.timers.size, 0);
});

for (const [name, payload] of [
  ['missing results', {}],
  ['non-array results', { results: ethanol }],
  ['too many results', { results: Array(21).fill(ethanol) }],
  ['null record', { results: [null] }],
  ['invalid CID', { results: [{ ...ethanol, cid: '702' }] }],
  ['zero CID', { results: [{ ...ethanol, cid: 0 }] }],
  ['missing name', { results: [{ ...ethanol, name: '' }] }],
  ['invalid formula', { results: [{ ...ethanol, formula: null }] }],
  ['non-string IUPAC name', { results: [{ ...ethanol, iupacName: { name: 'ethanol' } }] }],
  ['missing editable structure', { results: [{ ...ethanol, structure: '' }] }],
  ['oversized structure', { results: [{ ...ethanol, structure: 'C'.repeat(200_001) }] }],
]) {
  test(`malformed search payload (${name}) is rejected atomically`, async () => {
    const h = harness({ fetcher: async () => ({ ok: true, json: async () => payload }) });
    h.search.setReady(true);
    await h.query('ethanol');
    assert.equal(h.loads().length, 0);
    assert.equal(h.results.hidden, true);
    assert.equal(h.calls.structures.length, 0);
    assert.match(h.status.textContent, /unreadable|incomplete/i);
    assert.equal(h.status.classList.contains('is-error'), true);
  });
}

test('remote names, formulas, IUPAC text and errors are rendered as text, never injected HTML', async () => {
  const hostile = { ...ethanol, name: '<img src=x onerror=alert(1)>', formula: '<svg/onload=alert(2)>', iupacName: '<script>alert(3)</script>' };
  const h = harness({ fetcher: async () => reply([hostile]) });
  h.search.setReady(true);
  await h.query('ethanol');
  assert.match(h.results.textContent, /<img src=x onerror=alert\(1\)>/);
  assert.match(h.results.textContent, /<script>alert\(3\)<\/script>/);
  assert.equal(h.host.htmlWrites.length, 1);
  assert.equal(descendants(h.results).some(({ tagName }) => ['IMG', 'SVG', 'SCRIPT'].includes(tagName)), false);
  assert.equal(h.loads()[0].getAttribute('aria-label'), `Load ${hostile.name}, CID 702, into Builder`);
});

test('remote error messages cannot inject markup into the search status', async () => {
  const h = harness({ fetcher: async () => ({ ok: false, json: async () => ({ error: '<img src=x onerror=alert(1)>' }) }) });
  h.search.setReady(true);
  await h.query('ethanol');
  assert.match(h.status.textContent, /<img src=x onerror=alert\(1\)>/);
  assert.equal(h.status.children.length, 0);
  assert.equal(h.host.htmlWrites.length, 1);
});

test('search control semantics and mobile wrapping are explicit, without altering chemical formulas', async () => {
  assert.match(source, /<label for="builder-molecule-name">Load a Molecule by Name<\/label>/);
  assert.match(source, /id="builder-molecule-name" type="search" maxlength="100"/);
  assert.match(source, /aria-describedby="builder-search-help builder-search-status"/);
  assert.match(source, /role="status" aria-live="polite"/);
  assert.match(source, /3D preview is a separate check/);
  const css = await readFile(new URL('../src/builder.css', import.meta.url), 'utf8');
  assert.match(css, /\.builder-search-controls\s*\{[^}]*flex-wrap:\s*wrap/);
  assert.match(css, /\.builder-search-controls input\s*\{[^}]*min-width:\s*0[^}]*min-height:\s*44px/);
  assert.match(css, /\.builder-search-results li\s*\{[^}]*flex-wrap:\s*wrap/);
  assert.match(css, /\.builder-search-results li > div\s*\{[^}]*min-width:\s*0/);
  assert.match(css, /\.builder-search-results :is\(strong, span, small\)\s*\{[^}]*overflow-wrap:\s*anywhere/);
});

test('Builder integrates search with readiness, import locks, draft saves and invalidation, not automatic 3D generation', async () => {
  const builder = await readFile(new URL('../src/builder.ts', import.meta.url), 'utf8');
  assert.match(builder, /import \{ BuilderMoleculeSearch \} from '\.\/builder-molecule-search'/);
  assert.ok(builder.indexOf('<div id="builder-molecule-search">') < builder.indexOf('<div id="ketcher-editor"'));
  assert.match(builder, /getEditor:\s*\(\) => ketcher/);
  assert.match(builder, /canImport:\s*\(\) => !generating && !loadingExample && !importingMolecule/);
  assert.match(builder, /editorHost\.inert = true/);
  assert.match(builder, /editorHost\.inert = wasInert/);
  const imported = builder.slice(builder.indexOf('onImported: (match) => {'), builder.indexOf('async function saveDrawing'));
  assert.match(imported, /resetResult\(\)/);
  assert.match(imported, /saveDrawing\(\+\+saveRevision\)/);
  assert.doesNotMatch(imported, /generate3D\(/);
  assert.match(builder, /requestAnimationFrame\(\(\) => requestAnimationFrame\(\(\) => moleculeSearch\.setReady\(ketcher !== null\)\)\)/);
  assert.match(builder, /const releaseEditorStartup = \(\) => \{\s*releaseStartupGuard\(\)/);
  assert.match(builder, /instance\.setMolecule\(saved\)[\s\S]*?\.finally\(releaseEditorStartup\)/);
  assert.match(builder, /instance\.editor\.subscribe\('change', \(\) => \{\s*moleculeSearch\.drawingChanged\(\)/);
  assert.match(builder, /if \(!ketcher \|\| generating \|\| importingMolecule\) return/);
});
