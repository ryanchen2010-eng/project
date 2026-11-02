import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const labSource = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
const sourceFile = ts.createSourceFile('reaction-lab.ts', labSource, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
const names = new Set(['resetResult', 'updatePreviewActions', 'setPreview', 'showProduct3D']);
const selectedFunctions = sourceFile.statements.filter((statement) => ts.isFunctionDeclaration(statement) && names.has(statement.name?.text));
assert.equal(selectedFunctions.length, names.size, 'Lifecycle tests exercise the actual Reaction Lab functions');
const { outputText } = ts.transpileModule(selectedFunctions.map((statement) => statement.getText(sourceFile)).join('\n'), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});

function element() {
  return { hidden: false, open: false, disabled: false, textContent: '',
    classList: { toggle() {} }, setAttribute(name, value) { this[name] = value; }, replaceChildren() {} };
}

const productAtoms = [
  { index: 0, elem: 'C', x: 0, y: 0, z: 0, bonds: [1] },
  { index: 1, elem: 'O', x: 1.4, y: 0, z: 0, bonds: [0] },
];
const productLinks = [{ index: 0, mapId: 3, element: 'C' }, { index: 1, mapId: 4, element: 'O' }];
const payload = {
  productName: 'Methanol', balanced: true, assessment: { state: 'aligned' },
  product: { molfile: 'test product', formula: 'CH4O', smiles: 'CO', forceField: 'MMFF94', converged: true, atomLinks: productLinks },
};

function harness({ fetcher, failModel = false } = {}) {
  const calls = [];
  let available = false;
  const state = {
    cameraControls: { setEnabled() {}, setVisible() {} },
    reactionSiteShapes: [],
    revision: 1, selectedReaction: { id: 'sn2', productEquationFormula: 'CH3OH', explanation: 'Substitution', conditions: 'Example', sourceUrl: 'https://example.com' },
    productReady: false, previewMode: '2d', runController: null, diagramController: null,
    diagramData: { atoms: [{ mapId: 3 }], highlightsAvailable: true, note: null },
    measurements: {
      get available() { return available; },
      reset() { available = false; calls.push('reset-measurements'); state.measurementsHost.hidden = true; },
      setAtoms(atoms) { available = atoms.length >= 2; calls.push(['measure-atoms', atoms]); state.measurementsHost.hidden = !available; },
    },
    atomInspector: {
      reset() { calls.push('reset-inspector'); }, clearHover() {},
      setDiagram(atoms) { calls.push(['diagram-atoms', atoms]); },
      setModel(atoms, links) { calls.push(['inspect-atoms', atoms, links]); },
    },
    viewer: {
      removeShape(shape) { calls.push(['remove-site-shape', shape]); },
      addSphere(spec) { const shape = { spec }; calls.push(['site-sphere', shape]); return shape; },
      removeAllModels() { calls.push('remove-models'); },
      addModel() { calls.push('add-model'); if (failModel) throw new Error('Preview failed'); return { selectedAtoms: () => productAtoms }; },
      setStyle() {}, zoomTo() {}, resize() {}, render() { calls.push('render'); },
    },
    reactionCalculator: { setReaction() {} },
    informationPanel: { setReaction() {} },
    mechanismPanel: { reset() { calls.push('reset-mechanism'); }, clearModel() { calls.push('clear-mechanism-model'); }, setModel(atoms, links) { calls.push(['mechanism-atoms', atoms, links]); } },
    resolveReactant: (index) => ({ id: String(index) }), reactantReference: (reactant) => reactant,
    currentConditions: () => ({}), formatEquation: () => 'CH3Br + OH− → CH3OH + Br−',
    conditionLabel: () => 'Example conditions',
    setStatus: (text, error) => calls.push(['status', text, error]),
    required: () => element(),
    requestAnimationFrame: (callback) => callback(),
    AbortController, Error,
    fetch: fetcher ?? (async () => ({ ok: true, json: async () => payload })),
  };
  for (const name of ['measurementsHost', 'diagramScroll', 'atomInspection', 'diagramPlaceholder', 'diagramHost',
    'bondSummary', 'bondLegend', 'diagramNote', 'viewerHost', 'placeholder', 'details', 'learning', 'equation',
    'conditionAssessment', 'formulaNote', 'view2D', 'view3D', 'viewCompare', 'runButton', 'viewerHint',
    'previewHost', 'workspace', 'previewLabel', 'source']) state[name] = element();
  const lifecycle = new vm.Script(`${outputText}\n({ resetResult, setPreview, showProduct3D });`).runInNewContext(state);
  return { state, calls, ...lifecycle };
}

test('Reaction Lab uses a shared click hook rather than overwriting the atom inspector callback', () => {
  assert.match(labSource, /new BondMeasurements\(measurementsHost, viewer, \{ bindClicks: false \}\)/);
  assert.match(labSource, /\(atom\) => measurements\.pickAtom\(atom\)/);
  assert.ok(labSource.indexOf('id="product-measurements"') > labSource.indexOf('id="viewer-hint"'), 'measurement controls stay outside the 3D canvas');
});

test('product measurements use the actual model atoms and appear only after a 3D product is ready', async () => {
  const { state, calls, setPreview, showProduct3D } = harness();
  setPreview('compare');
  assert.equal(state.measurementsHost.hidden, true, 'no controls appear while product generation is pending');
  await showProduct3D('compare');
  assert.equal(state.productReady, true);
  assert.equal(state.measurementsHost.hidden, false);
  assert.deepEqual(calls.find((call) => Array.isArray(call) && call[0] === 'measure-atoms'), ['measure-atoms', productAtoms]);
  assert.ok(calls.indexOf('reset-measurements') < calls.indexOf('remove-models'), 'old shapes are removed before their model');
  assert.ok(calls.indexOf('reset-inspector') < calls.indexOf('remove-models'), 'old linked-atom shapes are removed before their model');
  assert.deepEqual(calls.find((call) => Array.isArray(call) && call[0] === 'inspect-atoms'), ['inspect-atoms', productAtoms, productLinks]);
  setPreview('2d');
  assert.equal(state.measurementsHost.hidden, true);
  setPreview('3d');
  assert.equal(state.measurementsHost.hidden, false);
});

test('changing reactants clears measurement state before clearing the old model', async () => {
  const { state, calls, showProduct3D, resetResult } = harness();
  await showProduct3D('3d');
  calls.length = 0;
  resetResult();
  assert.equal(state.productReady, false);
  assert.equal(state.measurementsHost.hidden, true);
  assert.ok(calls.indexOf('reset-measurements') < calls.indexOf('remove-models'));
  assert.ok(calls.indexOf('reset-inspector') < calls.indexOf('remove-models'));
  assert.equal(state.previewMode, '2d');
});

test('selected-site halos use exact mapped product atoms and are disposed on input changes', async () => {
  const { state, calls, showProduct3D, resetResult } = harness();
  state.selectedReaction.site = { atomMaps: [4, 99] };
  await showProduct3D('compare');
  const spheres = calls.filter((call) => Array.isArray(call) && call[0] === 'site-sphere');
  assert.equal(spheres.length, 1, 'byproduct/unmatched maps do not create invented 3D positions');
  assert.ok(spheres[0][1].spec.radius > 1.7 * 0.28, 'the site halo must extend beyond the displayed carbon sphere');
  assert.equal(spheres[0][1].spec.hoverable, false, 'site overlays must not intercept linked atom inspection');
  assert.deepEqual(JSON.parse(JSON.stringify(spheres[0][1].spec.center)), { x: 1.4, y: 0, z: 0 });
  resetResult();
  assert.equal(state.reactionSiteShapes.length, 0);
  assert.deepEqual(calls.find((call) => Array.isArray(call) && call[0] === 'remove-site-shape'), ['remove-site-shape', spheres[0][1]]);
});

test('view switching cannot reveal unavailable measurements for an unmeasurable product', () => {
  const { state, setPreview } = harness();
  state.productReady = true;
  for (const mode of ['2d', '3d', 'compare']) {
    setPreview(mode);
    assert.equal(state.measurementsHost.hidden, true, `${mode} respects the measurement controller’s availability`);
  }
});

test('failed product rendering clears partial measurement and inspection state before removing its model', async () => {
  const { state, calls, showProduct3D } = harness({ failModel: true });
  await showProduct3D('compare');
  assert.equal(state.productReady, false);
  assert.equal(state.measurementsHost.hidden, true);
  assert.equal(state.placeholder.hidden, false);
  assert.match(state.placeholder.textContent, /Preview failed/);
  assert.ok(calls.lastIndexOf('reset-measurements') < calls.lastIndexOf('remove-models'));
  assert.ok(calls.lastIndexOf('reset-inspector') < calls.lastIndexOf('remove-models'));
});

test('a stale product response cannot restore measurements after reactants change', async () => {
  let deliver;
  const response = new Promise((resolve) => { deliver = resolve; });
  const { state, calls, showProduct3D, resetResult } = harness({ fetcher: () => response });
  const pending = showProduct3D('compare');
  resetResult();
  deliver({ ok: true, json: async () => payload });
  await pending;
  assert.equal(state.productReady, false);
  assert.equal(state.measurementsHost.hidden, true);
  assert.equal(calls.includes('add-model'), false);
  assert.equal(calls.some((call) => Array.isArray(call) && call[0] === 'measure-atoms'), false);
});

test('a charged net product keeps its valid 2D result without inventing a neutral 3D model', async () => {
  const ionic = { ...payload, productName: 'Ethanoate ion', product: { representation: '2d-only', formula: 'C2H3O2-', smiles: 'CC(=O)[O-]', reason: 'This drawing contains charged atoms. Ionic structures remain 2D-only in this Builder.' } };
  const { state, calls, showProduct3D } = harness({ fetcher: async () => ({ ok: true, json: async () => ionic }) });
  await showProduct3D('compare');
  assert.equal(state.previewMode, '2d'); assert.equal(state.productReady, false);
  assert.equal(state.measurementsHost.hidden, true);
  assert.equal(calls.includes('add-model'), false); assert.equal(state.details.hidden, false);
  assert.ok(calls.some((call) => Array.isArray(call) && call[0] === 'status' && call[1].includes('Ethanoate ion')));
  assert.ok(calls.some((call) => Array.isArray(call) && call[0] === 'status' && call[1].includes('no neutral 3D molecule assumed')));
  assert.equal(state.placeholder.textContent.includes('Builder'), false);
});
