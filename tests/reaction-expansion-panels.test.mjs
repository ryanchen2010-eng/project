import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const compile = (source) => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const dataUrl = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const atomsUrl = dataUrl(compile(await read('src/atom-inspector.ts')));
const source = compile(await read('src/functional-group-panel.ts')).replace(/import \{ indexModelAtoms, safeDiagramSvg \} from '.\/atom-inspector';/,
  `import { indexModelAtoms } from '${atomsUrl}'; const safeDiagramSvg = (source) => globalThis.testSvg(source);`);
const { FunctionalGroupPanel, GroupHighlighter, groupModelCorrespondence } = await import(dataUrl(source));
const { ReactionInformationPanel } = await import(dataUrl(compile(await read('src/reaction-information-panel.ts'))));

class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.listeners = {}; this.hidden = false; this.open = false; this.text = ''; this.className = ''; this.classes = new Set();
    this.classList = { toggle: (name, on) => on ? this.classes.add(name) : this.classes.delete(name) }; }
  set textContent(value) { this.children = []; this.text = String(value); }
  get textContent() { return this.text + this.children.map((child) => child.textContent).join(' '); }
  set innerHTML(value) { throw new Error(`Unsafe HTML: ${value}`); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = []; this.text = ''; this.append(...children); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, callback) { (this.listeners[name] ??= []).push(callback); }
  emit(name) { for (const callback of this.listeners[name] ?? []) callback({ target: this }); }
  querySelectorAll(selector) { return descendants(this).filter((node) => selector.startsWith('.') ? node.className.split(' ').includes(selector.slice(1)) : node.tagName === selector); }
}
const descendants = (root) => root.children.flatMap((child) => [child, ...descendants(child)]);
const target = (map, element) => { const node = new Element('g'); node.className = 'atom-target'; node.dataset = { atomMap: String(map), element }; return node; };
const scene = () => { const root = new Element('div'); root.append(target(1, 'C'), target(2, 'O')); return root; };
const atoms = [{ index: 3, elem: 'C', x: 1, y: 2, z: 3 }, { index: 5, elem: 'O', x: 4, y: 5, z: 6 }];
const links = [{ index: 5, mapId: 2, element: 'O' }, { index: 3, mapId: 1, element: 'C' }];
function viewer() { const shapes = new Set(), specs = []; let clearCount = 0;
  return { shapes, specs, get clearCount() { return clearCount; }, addSphere(spec) { const shape = {}; specs.push(spec); shapes.add(shape); return shape; },
    removeShape(shape) { shapes.delete(shape); }, render() {}, resize() {}, zoomTo() {}, setStyle() {},
    removeAllModels() { clearCount += 1; }, addModel() { return { selectedAtoms: () => atoms }; } };
}
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
const deferred = () => { let resolve; const promise = new Promise((r) => { resolve = r; }); return { promise, resolve }; };
const data = (name = 'Actual structure') => ({ name, formula: 'C2H6O', svg: 'safe fixture', note: 'Partner and conditions are required.', groups: [
  { id: 'alcohol-1-2', type: 'alcohol', label: 'Alcohol', atomMaps: [1, 2], reactions: [{ mechanism: 'Alcohol oxidation', classifications: ['Oxidation'] }] },
  { id: 'amide-2', type: 'amide', label: 'Amide', atomMaps: [2], reactions: [] },
] });
const modelData = () => ({ ...data(), model: { representation: '3d', molfile: 'mapped fixture', atomLinks: links, forceField: 'MMFF94', converged: true } });
const response = (payload) => ({ ok: true, json: async () => payload });
async function fixture(run, fetcher = async () => response(data())) {
  const previous = { document: globalThis.document, fetch: globalThis.fetch, svg: globalThis.testSvg, setTimeout: globalThis.setTimeout, clearTimeout: globalThis.clearTimeout };
  const timers = new Map(); let sequence = 0;
  globalThis.document = { createElement: (tag) => new Element(tag) }; globalThis.testSvg = scene; globalThis.fetch = fetcher;
  globalThis.setTimeout = (callback) => { const id = ++sequence; timers.set(id, callback); return id; };
  globalThis.clearTimeout = (id) => timers.delete(id);
  const tick = async () => { const callbacks = [...timers.values()]; timers.clear(); for (const callback of callbacks) callback(); await flush(); };
  try { return await run(tick); } finally {
    globalThis.document = previous.document; globalThis.fetch = previous.fetch; globalThis.testSvg = previous.svg;
    globalThis.setTimeout = previous.setTimeout; globalThis.clearTimeout = previous.clearTimeout;
  }
}
const info = { version: 1, name: 'Hydrogenation', primaryFamily: 'Addition', classifications: ['Addition', 'Reduction'],
  reactantGroups: ['alkene'], productGroups: ['alkane'], transformation: 'Adds H₂.', difficulty: 'Basic', requirements: { catalyst: 'metal' },
  capabilities: { mappedMechanism: 'unsupported', stereochemistry: 'unsupported' }, limitations: ['No rates'],
  references: [{ title: 'Primary source', url: 'https://example.test/primary' }, { title: 'Bad URL', url: 'javascript:alert(1)' }] };
const snapshot = { information: info, explanation: '<img> structural explanation', conditions: 'Suitable catalyst, not a guarantee.', sourceUrl: 'https://example.test' };

test('potential and assigned stereo are separate, concise and clear on input changes', async () => fixture(async (tick) => {
  const host = new Element('details'); const panel = new FunctionalGroupPanel(host);
  panel.setReactants([{ name: 'Stereo molecule', smiles: 'CC(O)CC' }, null]); await tick();
  assert.match(host.textContent, /Atom 2: potential center · unassigned/);
  assert.match(host.textContent, /C=C 3–4: E · trans/);
  panel.setReactants([null, null]); assert.doesNotMatch(host.textContent, /Atom 2/);
}, async () => response({ ...data(), stereochemistry: { chiralCenters: [{ atomMap: 2, assignment: null }],
  alkenes: [{ atomMaps: [3, 4], assignment: 'E', cisTrans: 'trans' }], note: 'Specified configurations only.' } })));

test('reactant torsion results are one-conformer-only and reset with its model', async () => fixture(async (tick) => {
  const host = new Element('details'); const v = viewer(); const panel = new FunctionalGroupPanel(host, () => v);
  panel.setReactants([{ name: 'A', smiles: 'CCBr' }, null]); await tick();
  host.querySelectorAll('.group-choices')[0].children[0].emit('click');
  host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0].emit('click'); await flush();
  assert.match(host.textContent, /E2 torsions · this conformer only/); assert.match(host.textContent, /170° · anti-periplanar/);
  panel.setReactants([null, null]); assert.doesNotMatch(host.textContent, /170°/);
}, async (_, options) => response(JSON.parse(options.body).include3D ? { ...modelData(),
  e2Geometry: [{ atomMaps: [9, 1, 2, 3], dihedralDegrees: 170, antiPeriplanar: true }] } : data())));

test('advanced result shows backend CIP values without assuming an R/S letter swap', async () => fixture(() => {
  const host = new Element('details'); const panel = new ReactionInformationPanel(host, () => {});
  panel.setReaction({ ...snapshot, information: { ...info, stereochemistry: {
    reactant: { chiralCenters: [{ atomMap: 2, assignment: 'S' }], alkenes: [] },
    product: { chiralCenters: [{ atomMap: 2, assignment: 'S' }], alkenes: [] },
    effect: 'Backside inversion; priorities recomputed', geometryRequirement: null } } });
  host.querySelectorAll('.information-depth')[0].children[3].emit('click');
  assert.match(host.textContent, /Reactant atom 2: S/); assert.match(host.textContent, /Product atom 2: S/);
  assert.match(host.textContent, /Backside inversion/);
}));

test('information starts collapsed and shows multiple classifications without creating multiple reactions', async () => fixture(() => {
  const host = new Element('details'); const panel = new ReactionInformationPanel(host, () => {}); panel.setReaction(snapshot);
  assert.equal(host.open, false); assert.match(host.textContent, /Addition \+ Reduction/); assert.equal(host.querySelectorAll('.information-depth')[0].children.length, 4);
  assert.match(host.textContent, /Mechanism · unavailable/); assert.equal(host.querySelectorAll('a').length, 1);
}));
test('depth switches keep advanced information optional and do not invent mechanisms or stereo', async () => fixture(() => {
  const host = new Element('details'); const panel = new ReactionInformationPanel(host, () => { throw new Error('No unsupported action'); }); panel.setReaction(snapshot);
  host.querySelectorAll('.information-depth')[0].children[1].emit('click'); assert.match(host.textContent, /<img> structural/);
  host.querySelectorAll('.information-depth')[0].children[2].emit('click'); assert.match(host.textContent, /net equation is not a mechanism/);
  host.querySelectorAll('.information-depth')[0].children[3].emit('click'); assert.match(host.textContent, /Stereochemistry: unsupported/); assert.match(host.textContent, /No rates/);
  panel.setReaction(); assert.equal(host.hidden, true); assert.doesNotMatch(host.textContent, /No rates/);
}));
test('validated mapped mechanism action opens existing panel instead of rebuilding another engine', async () => fixture(() => {
  const host = new Element('details'); let opened = 0; const panel = new ReactionInformationPanel(host, () => { opened++; });
  panel.setReaction({ ...snapshot, information: { ...info, capabilities: { mappedMechanism: 'supported' } } });
  host.querySelectorAll('.information-depth')[0].children[2].emit('click'); host.querySelectorAll('.information-content')[0].querySelectorAll('button')[0].emit('click'); assert.equal(opened, 1);
}));
test('functional group highlights use exact maps in both views and noninteractive halos', async () => fixture(() => {
  const root = scene(), v = viewer(), highlighter = new GroupHighlighter(root, v);
  highlighter.setModel([...atoms].reverse(), links); highlighter.setGroup([2]);
  assert.equal(v.shapes.size, 1); assert.deepEqual(v.specs.at(-1).center, { x: 4, y: 5, z: 6 });
  assert.equal(root.children[0].classes.has('is-functional-group'), false); assert.equal(root.children[1].classes.has('is-functional-group'), true);
  assert.equal(v.specs.at(-1).clickable, false); assert.equal(v.specs.at(-1).hoverable, false);
  highlighter.setGroup([1]); assert.equal(v.shapes.size, 1); assert.equal(root.children[1].classes.has('is-functional-group'), false);
  highlighter.reset(); assert.equal(v.shapes.size, 0); assert.ok(root.children.every((atom) => !atom.classes.has('is-functional-group')));
}));
test('partial, duplicated, wrong-element or mismatched 2D maps never receive approximate model highlights', async () => fixture(() => {
  const root = scene();
  for (const bad of ([links[0]], [links[0], links[0]], [{ ...links[0], element: 'C' }, links[1]], [{ ...links[0], mapId: 99 }, links[1]])) assert.equal(groupModelCorrespondence(root, atoms, bad).size, 0);
  const v = viewer(), highlighter = new GroupHighlighter(root, v); highlighter.setModel(atoms, [links[0]]); highlighter.setGroup([2]); assert.equal(v.shapes.size, 0);
}));
test('resolved inputs detect automatically while collapsed; 3D waits for explicit request', async () => {
  const requests = []; await fixture(async (tick) => {
    const host = new Element('details'); let contexts = 0; const panel = new FunctionalGroupPanel(host, () => { contexts++; return viewer(); });
    const refs = [{ name: 'A', smiles: 'CCO' }, { name: 'B', smiles: 'CC(=O)N' }]; panel.setReactants(refs); await tick();
    assert.equal(requests.length, 2); assert.ok(requests.every((request) => request.include3D === false)); assert.equal(contexts, 0);
    assert.match(host.textContent, /Molecule 1 · A/); assert.match(host.textContent, /Molecule 2 · B/);
    assert.equal(host.open, false); panel.setReactants(refs); await tick(); assert.equal(requests.length, 2, 'same identities retain selection across condition edits');
  }, async (_, options) => { requests.push(JSON.parse(options.body)); return response(data()); });
});
test('group selection lists only supplied rules, supports unimplemented groups and safe text', async () => fixture(async (tick) => {
  const host = new Element('details'); const panel = new FunctionalGroupPanel(host); panel.setReactants([{ name: '<img> exact identity', smiles: 'CCO' }, null]); await tick();
  host.querySelectorAll('.group-choices')[0].children[0].emit('click'); assert.match(host.textContent, /Alcohol oxidation/); assert.match(host.textContent, /Partner and conditions/);
  assert.equal(host.querySelectorAll('.group-drawing')[0].querySelectorAll('.atom-target')[0].attributes.role, 'presentation');
  host.querySelectorAll('.group-choices')[0].children[1].emit('click'); assert.match(host.textContent, /no reaction rule for this group is implemented/);
  assert.match(host.textContent, /<img> exact identity/); assert.equal(host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0].disabled, true);
}));
test('new input rejects a late old inspection even if transport ignores abort', async () => {
  const old = deferred(); let count = 0; await fixture(async (tick) => {
    const host = new Element('details'); const panel = new FunctionalGroupPanel(host); panel.setReactants([{ name: 'Old', smiles: 'CCO' }, null]); await tick();
    panel.setReactants([{ name: 'New', smiles: 'CCN' }, null]); await tick(); old.resolve(response(data('Old response'))); await flush();
    assert.match(host.textContent, /Molecule 1 · New/); assert.doesNotMatch(host.textContent, /Old/);
  }, async () => ++count === 1 ? old.promise : response(data('New response')));
});
test('reactant 3D and group overlay load together; changing input clears stale models immediately', async () => fixture(async (tick) => {
  const host = new Element('details'); host.open = true; const v = viewer(); const panel = new FunctionalGroupPanel(host, () => v);
  panel.setReactants([{ name: 'A', smiles: 'CCO' }, null]); await tick(); host.querySelectorAll('.group-choices')[0].children[0].emit('click');
  host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0].emit('click'); await flush();
  assert.equal(v.shapes.size, 2); assert.equal(host.querySelectorAll('.group-model')[0].hidden, false); assert.match(host.textContent, /same group in both views/);
  const clears = v.clearCount;
  host.querySelectorAll('.group-choices')[0].children[1].emit('click');
  assert.equal(v.shapes.size, 1); assert.equal(host.querySelectorAll('.group-model')[0].hidden, false); assert.equal(v.clearCount, clears, 'group switch reuses the actual conformer');
  panel.setReactants([null, null]); assert.equal(v.shapes.size, 0); assert.equal(host.querySelectorAll('.group-scene')[0].hidden, true); assert.ok(v.clearCount > 0);
}, async (_, options) => response(JSON.parse(options.body).include3D ? modelData() : data())));
test('changing selected group aborts stale 3D and cannot show the old conformer', async () => {
  const pending = deferred(); await fixture(async (tick) => {
    const host = new Element('details'), v = viewer(); const panel = new FunctionalGroupPanel(host, () => v);
    panel.setReactants([{ name: 'A', smiles: 'CCO' }, null]); await tick(); host.querySelectorAll('.group-choices')[0].children[0].emit('click');
    host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0].emit('click'); await flush();
    host.querySelectorAll('.group-choices')[0].children[1].emit('click'); pending.resolve(response(modelData())); await flush();
    assert.equal(host.querySelectorAll('.group-model')[0].hidden, true); assert.equal(v.shapes.size, 0); assert.match(host.textContent, /no reaction rule/);
  }, async (_, options) => JSON.parse(options.body).include3D ? pending.promise : response(data()));
});
test('ionic and unavailable models preserve 2D with a short reason and recoverable controls', async () => fixture(async (tick) => {
  const host = new Element('details'); const panel = new FunctionalGroupPanel(host, () => { throw new Error('No ionic WebGL'); });
  panel.setReactants([{ name: 'Salt', smiles: '[Na+].[OH-]' }, null]); await tick(); host.querySelectorAll('.group-choices')[0].children[0].emit('click');
  const button = host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0]; button.emit('click'); await flush();
  assert.match(host.textContent, /separate components/); assert.equal(button.disabled, false); assert.equal(host.querySelectorAll('.group-model')[0].hidden, true);
}, async (_, options) => response(JSON.parse(options.body).include3D ? { ...data(), model: { representation: '2d-only', reason: 'separate components; 2D retained' } } : data())));
test('a malformed conformer correspondence is removed, never shown as a valid mapped model', async () => fixture(async (tick) => {
  const host = new Element('details'), v = viewer(); const panel = new FunctionalGroupPanel(host, () => v);
  panel.setReactants([{ name: 'A', smiles: 'CCO' }, null]); await tick(); host.querySelectorAll('.group-choices')[0].children[0].emit('click');
  host.querySelectorAll('.group-scene')[0].querySelectorAll('button')[0].emit('click'); await flush();
  assert.match(host.textContent, /correspondence is unavailable/); assert.equal(host.querySelectorAll('.group-model')[0].hidden, true); assert.equal(v.shapes.size, 0);
}, async (_, options) => response(JSON.parse(options.body).include3D ? { ...modelData(), model: { ...modelData().model, atomLinks: [links[0]] } } : data())));
