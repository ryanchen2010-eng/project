import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const projectFile = (path) => new URL(`../${path}`, import.meta.url);
const sharedCatalog = JSON.parse(await readFile(projectFile('src/shared-molecules.json'), 'utf8'));
const source = (await readFile(projectFile('src/molecules.ts'), 'utf8'))
  .replace("import sharedCatalog from './shared-molecules.json';", `const sharedCatalog = ${JSON.stringify(sharedCatalog)};`);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { molecules, explorerSamples, findMolecules, moleculeFromPubChem, isIonicCompound } =
  await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const { outputText: compoundSource } = ts.transpileModule(await readFile(projectFile('src/solution-compound.ts'), 'utf8'), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { solutionCompoundFromMolecule } = await import(`data:text/javascript;base64,${Buffer.from(compoundSource).toString('base64')}`);

const saltIds = ['sodium-chloride', 'sodium-hydroxide'];
const ids = (items) => items.map(({ id }) => id);

test('Explorer samples omit ionic compounds without removing their shared identities or information', () => {
  assert.equal(sharedCatalog.length, 20, 'Reaction Lab retains the complete shared collection');
  assert.equal(molecules.length, sharedCatalog.length);
  assert.equal(explorerSamples.length, 18);
  assert.deepEqual(ids(explorerSamples), ids(molecules.filter((molecule) => !isIonicCompound(molecule))));
  assert.deepEqual(ids(molecules.filter(isIonicCompound)).sort(), [...saltIds].sort());
  for (const id of saltIds) {
    assert.ok(!explorerSamples.some((molecule) => molecule.id === id), `${id} is not a sample card`);
    const molecule = molecules.find((item) => item.id === id);
    assert.ok(molecule, `${id} remains searchable`);
    const identity = sharedCatalog.find((item) => item.id === id);
    assert.equal(molecule.cid, identity.cid);
    assert.equal(molecule.structureForm, identity.smiles, 'Reaction Lab handoff is preserved');
    assert.equal(molecule.properties.geometry, 'Ionic lattice');
    assert.equal(molecule.properties.polarity, 'Ionic');
    assert.equal(molecule.properties.bonds, 'Ionic');
    assert.ok(molecule.properties.mass.trim(), 'information is retained without a diagram');
  }
});

test('nonionic examples and ambiguous-formula searches remain available', () => {
  for (const molecule of molecules.filter((item) => !saltIds.includes(item.id))) {
    assert.equal(isIonicCompound(molecule), false, `${molecule.name} is not mislabeled as ionic`);
    assert.ok(explorerSamples.some((item) => item.cid === molecule.cid));
  }
  assert.deepEqual(ids(findMolecules('C2H6O')), ['ethanol', 'dimethyl-ether']);
  assert.deepEqual(ids(findMolecules('CH3Br')), ['bromomethane']);
  assert.ok(explorerSamples.some((molecule) => molecule.id === 'oxygen'));
  assert.ok(explorerSamples.some((molecule) => molecule.id === 'ammonia'));
});

test('explicit ionic names, aliases, and case-sensitive formulas still return the correct records', () => {
  for (const id of saltIds) {
    const molecule = molecules.find((item) => item.id === id);
    for (const query of [molecule.name, molecule.formula, ...molecule.aliases]) {
      assert.ok(findMolecules(query).some((item) => item.cid === molecule.cid), `${query} finds ${molecule.name}`);
    }
  }
  assert.deepEqual(ids(findMolecules('  SODIUM CHLORIDE  ')), ['sodium-chloride']);
  assert.deepEqual(ids(findMolecules('NaCl')), ['sodium-chloride']);
  assert.deepEqual(ids(findMolecules('NaOH')), ['sodium-hydroxide']);
  assert.deepEqual(findMolecules('naoh'), [], 'formula capitalization remains meaningful');
});

test('known ionic PubChem hits keep their reviewed catalog information', () => {
  for (const id of saltIds) {
    const original = molecules.find((item) => item.id === id);
    const molecule = moleculeFromPubChem({
      cid: original.cid,
      name: 'Alternative PubChem display name',
      iupacName: '',
      formula: 'Alternative formula order',
      molecularWeight: '',
      structure: original.structureForm,
      multiPart: true,
      hasFormalCharge: true,
      ionicAssembly: true,
    });
    assert.equal(molecule.id, id);
    assert.equal(molecule.name, original.name);
    assert.equal(molecule.formula, original.formula);
    assert.deepEqual(molecule.properties, original.properties);
    assert.equal(isIonicCompound(molecule), true);
  }
});

test('unlisted ionic PubChem assemblies receive the information-only classification', () => {
  const molecule = moleculeFromPubChem({
    cid: 25517,
    name: 'Ammonium chloride',
    iupacName: 'azanium;chloride',
    formula: 'ClH4N',
    molecularWeight: '53.49',
    structure: '[NH4+].[Cl-]',
    multiPart: true,
    hasFormalCharge: true,
    ionicAssembly: true,
  });
  assert.equal(molecule.id, 'pubchem-25517');
  assert.equal(molecule.cid, 25517);
  assert.equal(molecule.category, 'Ionic compound');
  assert.equal(isIonicCompound(molecule), true);
  assert.equal(molecule.structureForm, '[NH4+].[Cl-]');
  assert.equal(molecule.properties.mass, '53.49 g/mol');
  assert.equal(molecule.properties.geometry, 'Ionic lattice');
  assert.equal(molecule.properties.polarity, 'Ionic');
  assert.equal(molecule.properties.bonds, 'Ionic');
});

test('formal charge or multiple fragments alone do not incorrectly imply an ionic compound', () => {
  const zwitterion = moleculeFromPubChem({
    cid: 999991,
    name: 'Connected zwitterion test record',
    iupacName: '',
    formula: 'C2H5NO2',
    molecularWeight: '75.07',
    structure: '[NH3+]CC(=O)[O-]',
    hasFormalCharge: true,
    ionicAssembly: false,
  });
  const neutralMetalAssembly = moleculeFromPubChem({
    cid: 999992,
    name: 'Neutral metal multipart test record',
    iupacName: '',
    formula: 'Cl2H6N2Pt',
    molecularWeight: '300.05',
    structure: 'N.N.Cl[Pt]Cl',
    multiPart: true,
    hasFormalCharge: false,
    ionicAssembly: false,
  });
  const chargedMolecule = moleculeFromPubChem({
    cid: 999993,
    name: 'Connected charged test record',
    iupacName: '',
    formula: 'H3O',
    molecularWeight: '19.02',
    structure: '[OH3+]',
    hasFormalCharge: true,
  });
  assert.equal(isIonicCompound(zwitterion), false);
  assert.equal(zwitterion.category, 'Charged PubChem structure');
  assert.equal(isIonicCompound(neutralMetalAssembly), false);
  assert.equal(neutralMetalAssembly.category, 'Multi-part PubChem record');
  assert.equal(isIonicCompound(chargedMolecule), false);
  assert.equal(chargedMolecule.category, 'Charged PubChem structure');
});

test('ionic display classification accepts explicit assembly metadata without guessing from a name', () => {
  assert.equal(isIonicCompound({ category: 'Ionic compound' }), true);
  assert.equal(isIonicCompound({ category: 'PubChem structure', ionicAssembly: true }), true);
  assert.equal(isIonicCompound({ category: 'PubChem structure', name: 'Sodium-like teaching label' }), false);
  assert.equal(isIonicCompound({ category: 'Multi-part PubChem record', ionicAssembly: false }), false);
});

// Exercise the actual loading function with deterministic viewer/network doubles.
// No browser application or network requests are loaded by these lifecycle checks.
const mainSource = await readFile(projectFile('src/main.ts'), 'utf8');
const showStart = mainSource.indexOf('async function showMolecule(');
const showEnd = mainSource.indexOf('transferButtons.forEach(', showStart);
assert.ok(showStart >= 0 && showEnd > showStart, 'Explorer retains its molecule loading function');
const { outputText: showMoleculeSource } = ts.transpileModule(mainSource.slice(showStart, showEnd), {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});

function deferred() {
  let resolve;
  const promise = new Promise((fulfill) => { resolve = fulfill; });
  return { promise, resolve };
}

function element(initial = {}) {
  const classes = new Set();
  return {
    textContent: '', hidden: false, disabled: false,
    classList: {
      add: (...names) => names.forEach((name) => classes.add(name)),
      remove: (...names) => names.forEach((name) => classes.delete(name)),
      toggle(name, force) { if (force) classes.add(name); else classes.delete(name); },
      contains: (name) => classes.has(name),
    },
    setAttribute(name, value) { this[name] = value; },
    removeAttribute(name) { delete this[name]; },
    ...initial,
  };
}

function explorerHarness({ fetcher, viewerPresent = true, cleanupError = false } = {}) {
  const calls = { fetch: [], models: [], information: [], solutionCompounds: [], revokedUrls: [], createdUrls: [], errors: [], timers: [], measurementResets: 0, measuredAtoms: [], lifecycle: [] };
  const atoms = [
    { index: 0, elem: 'O', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { index: 1, elem: 'H', x: 0.96, y: 0, z: 0, bonds: [0] },
    { index: 2, elem: 'H', x: -0.24, y: 0.93, z: 0, bonds: [0] },
  ];
  const viewer = {
    removeAllModels() { calls.lifecycle.push('remove-models'); if (cleanupError) throw new Error('WebGL cleanup failed'); },
    removeAllSurfaces() {}, removeAllLabels() {}, removeAllShapes() {},
    addModel(data, format) {
      calls.models.push({ data, format });
      calls.lifecycle.push('add-model');
      return { selectedAtoms: () => atoms };
    },
    setStyle() {}, zoomTo() {}, render() { calls.lifecycle.push('render'); },
  };
  const state = {
    activeMolecule: null, activeMoleculeId: '', modelReady: false, loadSequence: 0,
    depictionUrl: 'blob:previous-compound',
    buttons: new Map(explorerSamples.map((molecule) => [molecule.id, element()])),
    category: element(), moleculeTitle: element(), formula: element(), moleculeInformation: element(),
    viewerStage: element(), ionicNotice: element({ hidden: true }),
    viewerStatus: element(), fallbackView: element(), fallbackImage: element({ src: 'blob:previous-compound' }),
    viewerHint: element(), viewer: viewerPresent ? viewer : undefined,
    measurements: {
      reset() { calls.measurementResets += 1; calls.lifecycle.push('reset-measurements'); },
      setAtoms(loadedAtoms) { calls.measuredAtoms.push(loadedAtoms); calls.lifecycle.push('set-measured-atoms'); },
    },
    solutionCalculator: { setCompound(compound) { calls.solutionCompounds.push(compound); } },
    solutionCompoundFromMolecule,
    isIonicCompound,
    renderMoleculeInformation: (_, molecule) => calls.information.push(molecule),
    fetch: (url) => {
      calls.fetch.push(url);
      return fetcher ? fetcher(url) : Promise.reject(new Error('Unexpected structure request'));
    },
    URL: {
      revokeObjectURL: (url) => calls.revokedUrls.push(url),
      createObjectURL: (blob) => { calls.createdUrls.push(blob); return 'blob:new-compound'; },
    },
    console: { error: (error) => calls.errors.push(error) },
    window: { setTimeout: (callback) => calls.timers.push(callback) },
  };
  const show = new vm.Script(`${showMoleculeSource}\nshowMolecule;`).runInNewContext(state);
  return { show, state, calls, atoms };
}

test('selecting an ionic record hides diagrams, retains information, and makes no structure or depiction request', async () => {
  for (const viewerPresent of [true, false]) {
    const { show, state, calls } = explorerHarness({ viewerPresent });
    const molecule = molecules.find(({ id }) => id === 'sodium-chloride');
    await show(molecule);
    assert.equal(state.viewerStage.hidden, true);
    assert.equal(state.ionicNotice.hidden, false);
    assert.match(state.ionicNotice.textContent, /ionic compound.*no 3D diagram/i);
    assert.equal(state.moleculeTitle.textContent, molecule.name);
    assert.equal(state.formula.textContent, molecule.formula);
    assert.deepEqual(calls.information, [molecule]);
    assert.deepEqual(calls.solutionCompounds, [solutionCompoundFromMolecule(molecule)], 'solution amounts use the salt’s formula-unit mass even without WebGL');
    assert.deepEqual(calls.fetch, []);
    assert.deepEqual(calls.models, []);
    assert.equal(calls.measurementResets, 1, 'old measurements are cleared before the ionic view');
    assert.deepEqual(calls.measuredAtoms, [], 'no measurements are invented for information-only records');
    assert.deepEqual(calls.createdUrls, []);
    assert.deepEqual(calls.revokedUrls, ['blob:previous-compound']);
    assert.equal(state.fallbackView.hidden, true);
    assert.ok(!('src' in state.fallbackImage));
    assert.equal(state.modelReady, true);
    assert.ok([...state.buttons.values()].every((button) => !button.disabled));
  }
});

test('ionic information remains usable without fetching a diagram when old WebGL cleanup fails', async () => {
  const { show, state, calls } = explorerHarness({ cleanupError: true });
  const molecule = molecules.find(({ id }) => id === 'sodium-hydroxide');
  await show(molecule);
  assert.equal(state.viewerStage.hidden, true);
  assert.equal(state.ionicNotice.hidden, false);
  assert.equal(state.moleculeTitle.textContent, molecule.name);
  assert.deepEqual(calls.information, [molecule]);
  assert.deepEqual(calls.fetch, []);
  assert.deepEqual(calls.createdUrls, []);
  assert.equal(calls.measurementResets, 1, 'measurement UI is reset even if old model cleanup fails');
  assert.deepEqual(calls.measuredAtoms, []);
  assert.equal(state.fallbackView.hidden, true);
  assert.equal(state.modelReady, true);
  assert.ok([...state.buttons.values()].every((button) => !button.disabled));
});

test('returning from an ionic compound to a molecular sample restores the viewer and clears the notice', async () => {
  const { show, state, calls, atoms } = explorerHarness({
    fetcher: async () => ({ ok: true, text: async () => 'water SDF test payload' }),
  });
  await show(molecules.find(({ id }) => id === 'sodium-hydroxide'));
  const water = molecules.find(({ id }) => id === 'water');
  await show(water);
  assert.equal(state.viewerStage.hidden, false);
  assert.equal(state.ionicNotice.hidden, true);
  assert.equal(state.ionicNotice.textContent, '');
  assert.equal(state.fallbackView.hidden, true);
  assert.deepEqual(calls.fetch, [water.structureFile]);
  assert.deepEqual(calls.models, [{ data: 'water SDF test payload', format: 'sdf' }]);
  assert.deepEqual(calls.measuredAtoms, [atoms], 'measurements use the loaded model’s actual coordinates');
  assert.equal(calls.measurementResets, 2);
  assert.ok(calls.lifecycle.lastIndexOf('set-measured-atoms') < calls.lifecycle.lastIndexOf('render'), 'atom targets are attached before the final render');
  assert.equal(state.moleculeTitle.textContent, 'Water');
  assert.match(state.viewerHint.textContent, /drag to rotate/i);
  assert.equal(state.modelReady, true);
  assert.ok([...state.buttons.values()].every((button) => !button.disabled));
});

test('a pending older 3D response cannot replace an ionic information-only selection', async () => {
  const pending = deferred();
  const { show, state, calls } = explorerHarness({ fetcher: () => pending.promise });
  const waterLoad = show(molecules.find(({ id }) => id === 'water'));
  const salt = molecules.find(({ id }) => id === 'sodium-chloride');
  await show(salt);
  pending.resolve({ ok: true, text: async () => 'stale water SDF' });
  await waterLoad;
  assert.equal(state.moleculeTitle.textContent, salt.name);
  assert.equal(state.viewerStage.hidden, true);
  assert.equal(state.ionicNotice.hidden, false);
  assert.equal(state.modelReady, true);
  assert.deepEqual(calls.models, []);
  assert.equal(calls.solutionCompounds.at(-1).id, salt.id, 'stale 3D responses cannot replace the current solution compound');
  assert.deepEqual(calls.measuredAtoms, [], 'stale models cannot revive the measurement panel');
  assert.deepEqual(calls.fetch, ['/molecules/water.sdf']);
  assert.ok([...state.buttons.values()].every((button) => !button.disabled));
});

test('a pending older 2D fallback cannot show a diagram after selecting an ionic compound', async () => {
  const pending = deferred();
  const { show, state, calls } = explorerHarness({
    fetcher: (url) => url.includes('/depiction?')
      ? pending.promise : Promise.resolve({ ok: false }),
  });
  const nonionic = molecules.find(({ id }) => id === 'oxygen');
  const olderLoad = show(nonionic);
  for (let turn = 0; turn < 10 && calls.fetch.length < 2; turn += 1) await Promise.resolve();
  assert.equal(calls.fetch.length, 2, 'older nonionic record reached its depiction fallback');
  const salt = molecules.find(({ id }) => id === 'sodium-hydroxide');
  await show(salt);
  pending.resolve({ ok: true, blob: async () => 'stale depiction bytes' });
  await olderLoad;
  assert.equal(state.moleculeTitle.textContent, salt.name);
  assert.equal(state.viewerStage.hidden, true);
  assert.equal(state.fallbackView.hidden, true);
  assert.ok(!('src' in state.fallbackImage));
  assert.deepEqual(calls.createdUrls, []);
  assert.deepEqual(calls.measuredAtoms, [], 'a stale 2D depiction cannot enable measurements');
  assert.ok([...state.buttons.values()].every((button) => !button.disabled));
});

test('Explorer clears old measurements while a new model is loading and keeps them hidden for 2D fallback', async () => {
  const pending = deferred();
  const { show, calls, state } = explorerHarness({
    fetcher: (url) => url.includes('/depiction?')
      ? Promise.resolve({ ok: true, blob: async () => '2D depiction bytes' }) : pending.promise,
  });
  const loading = show(molecules.find(({ id }) => id === 'oxygen'));
  assert.equal(calls.lifecycle[0], 'reset-measurements', 'measurement selection is cleared before model removal');
  assert.equal(calls.measurementResets, 1);
  assert.deepEqual(calls.measuredAtoms, [], 'pending requests have no measurable coordinates');
  pending.resolve({ ok: false });
  await loading;
  assert.equal(state.fallbackView.hidden, false);
  assert.equal(calls.measurementResets, 2, 'the failed 3D path clears measurement state before a 2D fallback');
  assert.deepEqual(calls.measuredAtoms, []);
});

test('Explorer failed model loading cannot retain a previous measurement selection', async () => {
  const { show, calls, state } = explorerHarness({ fetcher: async () => ({ ok: false }) });
  await show(molecules.find(({ id }) => id === 'water'));
  assert.equal(state.modelReady, false);
  assert.equal(calls.measurementResets, 2);
  assert.deepEqual(calls.measuredAtoms, []);
  assert.equal(state.viewerStatus.classList.contains('is-error'), true);
});
