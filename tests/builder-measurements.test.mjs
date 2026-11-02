import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

// Run Builder's real result/loading lifecycle without importing Ketcher or a browser.
const source = await readFile(new URL('../src/builder.ts', import.meta.url), 'utf8');
const start = source.indexOf('function resetResult()');
const end = source.indexOf("generateButton.addEventListener('click'", start);
assert.ok(start >= 0 && end > start);
const { outputText } = ts.transpileModule(source.slice(start, end), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});

function element() {
  const classes = new Set();
  return {
    hidden: false, disabled: false, textContent: '',
    classList: {
      add: (...names) => names.forEach((name) => classes.add(name)),
      remove: (...names) => names.forEach((name) => classes.delete(name)),
      contains: (name) => classes.has(name),
    },
  };
}

function harness({ fetcher } = {}) {
  const calls = { lifecycle: [], resets: 0, atoms: [], models: [], status: [] };
  const modelAtoms = [
    { index: 0, elem: 'C', x: -0.8, y: 0.2, z: 0.3, bonds: [1] },
    { index: 1, elem: 'O', x: 0.6, y: -0.2, z: -0.1, bonds: [0] },
  ];
  const state = {
    cameraControls: { setEnabled() {}, setVisible() {} },
    editRevision: 0, lastResult: null, generating: false, importingMolecule: false,
    transferButtons: [element(), element()],
    placeholder: element(), formula: element(), mass: element(), atomCount: element(), bondCount: element(),
    ruleCheck: element(), energyMethod: element(), atomLabel: element(), bondLabel: element(), previewBadge: element(),
    generateButton: element(),
    measurements: {
      reset() { calls.resets += 1; calls.lifecycle.push('reset-measurements'); },
      setAtoms(atoms) { calls.atoms.push(atoms); calls.lifecycle.push('set-atoms'); },
    },
    viewer: {
      removeAllModels() { calls.lifecycle.push('remove-models'); },
      addModel(data, format) {
        calls.models.push({ data, format });
        return { selectedAtoms: () => modelAtoms };
      },
      setStyle() {}, zoomTo() {}, resize() {},
      render() { calls.lifecycle.push('render'); },
    },
    setStatus: (...args) => calls.status.push(args),
    ketcher: { getMolfile: async () => 'drawn molfile' },
    fetch: fetcher ?? (async () => { throw new TypeError('Service unavailable'); }),
  };
  const api = new vm.Script(`${outputText}\n({ resetResult, displayResult, generate3D });`).runInNewContext(state);
  return { ...api, state, calls, modelAtoms };
}

const result3d = {
  representation: '3d', molfile: 'calculated 3D molfile', formula: 'CH4O', smiles: 'CO', molarMass: 32.042,
  atoms: 6, bonds: 5, forceField: 'MMFF94', converged: true,
};

test('Builder exposes measurements from the returned 3D model, not the drawing’s 2D coordinates', () => {
  const { displayResult, state, calls, modelAtoms } = harness();
  displayResult(result3d);
  assert.equal(calls.lifecycle[0], 'reset-measurements');
  assert.deepEqual(calls.models, [{ data: result3d.molfile, format: 'mol' }]);
  assert.deepEqual(calls.atoms, [modelAtoms]);
  assert.ok(calls.lifecycle.indexOf('set-atoms') < calls.lifecycle.lastIndexOf('render'));
  assert.equal(state.placeholder.hidden, true);
  assert.equal(state.ruleCheck.textContent, 'Passed');
});

test('Builder clears measurements before clearing a result after drawing edits', () => {
  const { resetResult, state, calls } = harness();
  state.lastResult = result3d;
  resetResult();
  assert.deepEqual(calls.lifecycle, ['reset-measurements', 'remove-models', 'render']);
  assert.equal(state.lastResult, null);
  assert.equal(state.editRevision, 1);
  assert.equal(state.placeholder.hidden, false);
  assert.ok(state.transferButtons.every(({ disabled }) => disabled));
});

test('Builder 2D-only validation results do not enable model measurements', () => {
  const { displayResult, calls, state } = harness();
  displayResult({ ...result3d, representation: '2d-only', reason: 'No reliable 3D geometry for this structure.' });
  assert.equal(calls.resets, 1);
  assert.deepEqual(calls.atoms, []);
  assert.deepEqual(calls.models, []);
  assert.equal(state.previewBadge.textContent, '2D only');
  assert.equal(state.placeholder.hidden, false);
});

test('Builder clears measurement selection during new calculations and service failures', async () => {
  const { generate3D, calls, state } = harness();
  const pending = generate3D();
  assert.equal(calls.resets, 1, 'measurements are hidden immediately when calculation starts');
  await pending;
  assert.equal(calls.resets, 2, 'failed preview stays unmeasurable');
  assert.deepEqual(calls.atoms, []);
  assert.equal(state.ruleCheck.textContent, 'Needs changes');
  assert.equal(state.generating, false);
  assert.equal(state.generateButton.disabled, false);
});

test('Builder ignores an old preview result when drawing changes while it is loading', async () => {
  let finish;
  const response = new Promise((resolve) => { finish = resolve; });
  const { generate3D, resetResult, calls, state } = harness({ fetcher: () => response });
  const pending = generate3D();
  await Promise.resolve();
  resetResult();
  finish({ ok: true, json: async () => result3d });
  await pending;
  assert.deepEqual(calls.models, []);
  assert.deepEqual(calls.atoms, []);
  assert.equal(state.lastResult, null);
});

test('Builder does not calculate a preview while a name-search import is replacing the drawing', async () => {
  const { generate3D, calls, state } = harness();
  state.importingMolecule = true;
  await generate3D();
  assert.equal(calls.resets, 0);
  assert.equal(calls.status.length, 0);
});
