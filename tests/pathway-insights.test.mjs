import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const compile = (source) => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const dataUrl = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const atomsUrl = dataUrl(compile(await readFile(new URL('../src/atom-inspector.ts', import.meta.url), 'utf8')));
const moduleSource = compile(await readFile(new URL('../src/pathway-insights.ts', import.meta.url), 'utf8'))
  .replace(/import \{ indexModelAtoms, safeDiagramSvg \} from '.\/atom-inspector';/,
    `import { indexModelAtoms } from '${atomsUrl}'; const safeDiagramSvg = (source) => globalThis.testSvg(source);`);
const { renderReasoning, renderComparison, MechanismHighlighter, MechanismPanel } = await import(dataUrl(moduleSource));

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
const target = (map) => { const node = new Element('g'); node.className = 'atom-target'; node.dataset.atomMap = String(map); return node; };
const move = (id, sources, destinations) => ({ id, source: { type: 'lone-pair', atomMaps: sources }, destination: { type: 'atom', atomMaps: destinations }, description: `Move ${id}` });
function fixture(run) {
  const oldDocument = globalThis.document, oldSvg = globalThis.testSvg;
  globalThis.document = { createElement: (tag) => new Element(tag) };
  globalThis.testSvg = () => { const svg = new Element('svg'); svg.append(...[1, 2, 7, 10].map(target)); return svg; };
  try { return run(); } finally { globalThis.document = oldDocument; globalThis.testSvg = oldSvg; }
}
const model = [{ index: 9, elem: 'C', x: 1, y: 2, z: 3 }, { index: 13, elem: 'O', x: 4, y: 5, z: 6 }];
const links = [{ index: 13, mapId: 7, element: 'O' }, { index: 9, mapId: 1, element: 'C' }];
function scene() {
  const root = new Element('section'); root.append(...[1, 2, 7].map(target)); const shapes = new Set(), specs = [];
  const viewer = { addSphere(spec) { specs.push(spec); const shape = {}; shapes.add(shape); return shape; }, removeShape(shape) { shapes.delete(shape); }, render() {} };
  return { root, viewer, shapes, specs };
}

test('reasoning is collapsed, accessible and renders external-looking text without HTML', () => fixture(() => {
  const panel = renderReasoning({ label: 'Possible', factors: [{ factor: 'substrate', value: '<script>secondary</script>', effect: 'disfavors', explanation: '<img onerror=bad>', atomMaps: [] }], note: 'Not a probability' });
  assert.equal(panel.tagName, 'details'); assert.equal(panel.open, false);
  assert.match(panel.textContent, /Why This Pathway/); assert.match(panel.textContent, /<script>secondary/);
}));

test('comparison copies backend cells, aligns by reaction id and clears when unavailable', () => fixture(() => {
  const host = new Element('div');
  renderComparison(host, { columns: [{ id: 'a', pathway: 'SN2', label: 'Possible', site: 'Site 1' }, { id: 'b', pathway: 'E2', label: 'Possible', site: 'Site 2' }],
    rows: [{ factor: 'substrate', cells: [{ reactionId: 'b', effect: 'favors', value: 'secondary', explanation: 'Engine fact B' }, { reactionId: 'a', effect: 'disfavors', value: 'secondary', explanation: 'Engine fact A' }] }], note: 'Same facts' });
  assert.equal(host.hidden, false);
  const cells = host.querySelectorAll('td'); assert.match(cells[0].textContent, /Engine fact A/); assert.match(cells[1].textContent, /Engine fact B/);
  assert.equal(host.querySelectorAll('.comparison-scroll')[0].tabIndex, 0);
  renderComparison(host); assert.equal(host.hidden, true); assert.equal(host.children.length, 0);
}));

test('comparison supports four supplied pathways without inventing columns', () => fixture(() => {
  const host = new Element('div'); const columns = ['SN1', 'SN2', 'E1', 'E2'].map((pathway) => ({ id: pathway, pathway, site: '', label: 'Possible' }));
  renderComparison(host, { columns, rows: [], note: '' });
  assert.equal(host.querySelectorAll('th').length, 5);
  renderComparison(host, { columns: [columns[0]], rows: [], note: '' }); assert.equal(host.hidden, true);
}));

test('electron overlays use exact maps and highlight only retained final-product atoms in 3D', () => fixture(() => {
  const { root, viewer, shapes, specs } = scene(); const highlighter = new MechanismHighlighter(root, viewer);
  highlighter.setModel([...model].reverse(), links); highlighter.setMoves([move('attack', [7], [1]), move('depart', [1, 2], [2])]);
  assert.equal(shapes.size, 2, 'no invented 3D leaving-group atom');
  assert.deepEqual(specs.slice(-2).map((spec) => spec.center), [{ x: 4, y: 5, z: 6 }, { x: 1, y: 2, z: 3 }]);
  assert.ok(root.children[0].classes.has('is-electron-source')); assert.ok(root.children[0].classes.has('is-electron-destination'));
  assert.ok(specs.every((spec) => !spec.clickable && !spec.hoverable));
}));

test('invalid model correspondence creates no approximate highlights', () => fixture(() => {
  const { root, viewer, shapes } = scene(); const highlighter = new MechanismHighlighter(root, viewer);
  highlighter.setModel(model, [links[0]]); highlighter.setMoves([move('attack', [7], [1])]); assert.equal(shapes.size, 0);
}));

test('mechanism overlay resets dispose shapes but preserve independent hover and site states', () => fixture(() => {
  const { root, viewer, shapes } = scene(); root.children[0].classes.add('is-observed'); root.children[0].classes.add('reaction-site');
  const highlighter = new MechanismHighlighter(root, viewer); highlighter.setModel(model, links); highlighter.setMoves([move('a', [7], [1])]);
  highlighter.reset(); assert.equal(shapes.size, 0); assert.ok(root.children[0].classes.has('is-observed')); assert.ok(root.children[0].classes.has('reaction-site'));
  assert.ok(root.children.every((target) => !target.classes.has('is-electron-source') && !target.classes.has('is-electron-destination')));
}));

test('mechanism panel opens steps, labels intermediate and clears stale content/highlights', () => fixture(() => {
  const { root, viewer, shapes } = scene(); const host = new Element('details'); root.append(host);
  const panel = new MechanismPanel(host, root, viewer);
  const steps = [{ id: 'first', title: 'Ionization', description: 'Departure', concerted: false, electronMoves: [move('depart', [1, 2], [2])],
    intermediate: { kind: 'Intermediate', name: 'Carbocation', svg: '' }, state: { kind: 'Intermediate', name: 'Carbocation', svg: '' } },
    { id: 'second', title: 'Capture', description: 'Attack', concerted: false, electronMoves: [move('attack', [7], [1])], intermediate: null,
      state: { kind: 'Product state', name: 'Products', svg: '' } }];
  panel.setMechanism({ version: 1, type: 'SN1', siteId: 'test', roles: { nucleophile: 7 }, steps,
    energyProfile: { qualitative: true, stepCount: 2, rateDeterminingStep: 1, intermediates: 1, activationEnergies: null, note: 'No energies calculated' }, limitations: ['No rates'] });
  panel.setModel(model, links); assert.equal(host.hidden, false); assert.equal(shapes.size, 0);
  host.open = true; host.emit('toggle'); assert.equal(shapes.size, 1);
  assert.match(host.textContent, /Intermediate — Carbocation/); assert.match(host.textContent, /barrier \(not calculated\)/);
  host.querySelectorAll('.mechanism-step-buttons')[0].children[1].emit('click'); assert.match(host.textContent, /SN1 · Step 2/); assert.equal(shapes.size, 2);
  host.open = false; host.emit('toggle'); assert.equal(shapes.size, 0);
  panel.reset(); assert.equal(host.hidden, true); assert.equal(shapes.size, 0); assert.doesNotMatch(host.textContent, /Carbocation/);
}));

test('reaction page integrates condition invalidation, independent mechanism lifecycle and non-nested option controls', async () => {
  const source = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
  assert.match(source, /mechanismPanel\.reset\(\)/); assert.match(source, /mechanismPanel\.setModel\(productAtoms, payload.product.atomLinks/);
  assert.match(source, /mechanismPanel\.setMechanism\(payload.mechanism\)/);
  assert.match(source, /\[solventInput, temperatureInput, catalystInput, oxidationStageInput, additionStageInput, polymerUnitsInput, workupInput\]/);
  assert.match(source, /wrapper\.append\(button\)/); assert.match(source, /wrapper\.append\(renderReasoning/);
  const css = await readFile(new URL('../src/reaction-lab.css', import.meta.url), 'utf8');
  assert.match(css, /\.comparison-scroll \{ max-width: 100%; overflow: auto/);
});

test('mechanism displays both mapped states and explicit forming, breaking and proton changes', () => fixture(() => {
  const { root, viewer } = scene(); const host = new Element('details'); root.append(host);
  const panel = new MechanismPanel(host, root, viewer);
  const change = (maps, kind, before, after) => ({ atomMaps: maps, kind, before, after });
  panel.setMechanism({ version: 1, type: 'SN1', siteId: 'exact', roles: { nucleophile: 7 },
    steps: [{ id: 'transfer', title: 'Proton transfer', description: 'Solvent deprotonates oxonium', concerted: false,
      electronMoves: [move('proton', [10], [7])], intermediate: null,
      beforeState: { kind: 'Starting state', name: 'Before this step', svg: 'before' },
      state: { kind: 'Product state', name: 'Alcohol plus hydronium', svg: 'after' },
      bondsFormed: [change([10, 7], 'formed', null, 1)], bondsBroken: [change([1, 7], 'broken', 1, null)],
      bondOrderChanges: [], protonTransfers: [change([1, 7], 'broken', 1, null)] }],
    energyProfile: { qualitative: true, stepCount: 1, note: 'No rates' }, limitations: [] });
  assert.equal(host.querySelectorAll('.mechanism-state').length, 2);
  assert.match(host.textContent, /Starting state — Before this step/);
  assert.match(host.textContent, /Bond forming: atoms 10–7/); assert.match(host.textContent, /Bond breaking: atoms 1–7/);
  assert.match(host.textContent, /Proton movement is shown explicitly/);
  host.open = true; host.emit('toggle');
  const atoms = host.querySelectorAll('.atom-target').filter((a) => a.dataset.atomMap === '7');
  assert.equal(atoms.length, 2); assert.ok(atoms.every((a) => a.classes.has('is-electron-destination')));
}));
