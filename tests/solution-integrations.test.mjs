import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const compile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const importSource = (source) => import(`data:text/javascript;base64,${Buffer.from(compile(source)).toString('base64')}`);
const { parseMolarMass, solutionCompoundFromMolecule, solutionCompoundForReactant } = await importSource(await read('src/solution-compound.ts'));
const shared = JSON.parse(await read('src/shared-molecules.json'));
const { molecules } = await importSource((await read('src/molecules.ts'))
  .replace("import sharedCatalog from './shared-molecules.json';", `const sharedCatalog = ${JSON.stringify(shared)};`));
const { findReactantCandidates } = await importSource(await read('src/reactant-entry.ts'));
const reactants = shared.map((record) => ({ ...record }));
const reactant = (id) => reactants.find((item) => item.id === id);

test('automatic molar mass accepts only complete positive finite g/mol values', () => {
  for (const [input, expected] of [['18.015 g/mol', 18.015], [' 58.443 g/mol ', 58.443], ['.5 g/mol', .5]]) {
    assert.equal(parseMolarMass(input), expected);
  }
  for (const input of ['N/A', 'Not reviewed', '18.015', '18.015 mg/mol', '18.015 g/mol at room temperature',
    '18.015 garbage', '0 g/mol', '-4 g/mol', 'Infinity g/mol', 'NaN g/mol', '1e2 g/mol', `${'9'.repeat(400)} g/mol`]) {
    assert.equal(parseMolarMass(input), undefined, input);
  }
});

test('Explorer exact records share neutral and full salt formula-unit masses', () => {
  for (const [id, mass] of [['water', 18.015], ['ethanol', 46.07], ['sodium-chloride', 58.443], ['sodium-hydroxide', 39.997]]) {
    const source = molecules.find((item) => item.id === id);
    const compound = solutionCompoundFromMolecule(source);
    assert.equal(compound.id, source.id);
    assert.equal(compound.name, source.name);
    assert.equal(compound.formula, source.formula);
    assert.equal(compound.molarMass, mass);
  }
  const source = { ...molecules[0], properties: { ...molecules[0].properties, mass: 'Not available' } };
  assert.equal(solutionCompoundFromMolecule(source).molarMass, undefined);
});

test('Reaction Lab only reuses mass for an exact id plus structure, never a shared formula or omitted counterion', () => {
  const salt = solutionCompoundForReactant(reactant('sodium-hydroxide'), molecules);
  assert.equal(salt.molarMass, 39.997);
  assert.equal(salt.formula, 'NaOH');
  const hydroxide = { id: 'hydroxide', name: 'Hydroxide ion', formula: 'OH⁻', smiles: '[OH-]', aliases: [] };
  assert.equal(solutionCompoundForReactant(hydroxide, molecules).molarMass, undefined);
  const changedStructure = { ...reactant('ethanol'), smiles: 'COC' };
  assert.equal(solutionCompoundForReactant(changedStructure, molecules).molarMass, undefined);
  const unreviewed = { ...reactant('ethanol'), id: 'pubchem-9999' };
  assert.equal(solutionCompoundForReactant(unreviewed, molecules).molarMass, undefined);
  const trustedIdentity = solutionCompoundForReactant({ ...reactant('water'), name: 'Different label', formula: 'Wrong formula' }, molecules);
  assert.equal(trustedIdentity.name, 'Water');
  assert.equal(trustedIdentity.formula, 'H₂O');
  assert.equal(solutionCompoundForReactant(undefined, molecules), undefined);
});

const labSource = await read('src/reaction-lab.ts');
const parsed = ts.createSourceFile('reaction-lab.ts', labSource, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
const selected = new Set(['candidatesFor', 'resolveReactant', 'updateCalculatorLinks', 'updateMatches']);
const functions = parsed.statements.filter((node) => ts.isFunctionDeclaration(node) && selected.has(node.name?.text));
assert.equal(functions.length, selected.size);
const inputListeners = parsed.statements.find((node) => ts.isExpressionStatement(node)
  && node.getText(parsed).startsWith("inputs.forEach((input, index) => input.addEventListener('input'"));
assert.ok(inputListeners, 'tests use the real reactant edit handlers');
const harnessSource = compile([...functions, inputListeners].map((node) => node.getText(parsed)).join('\n'));

function harness() {
  const button = () => ({ hidden: true, disabled: true, attributes: {}, setAttribute(key, value) { this.attributes[key] = value; } });
  const input = (value) => ({ value, listeners: new Map(), addEventListener(type, callback) { this.listeners.set(type, callback); } });
  const inputA = input('Water');
  const inputB = input('');
  const state = {
    inputA, inputB, inputs: [inputA, inputB],
    calculatorButtons: [button(), button()], findReactantCandidates,
    catalog: { reactants }, selectedIds: [null, null], drawnInputs: [null, null], pubchemLookups: [null, null],
    lookupRevisions: [0, 0], searchButtons: [{ disabled: false }, { disabled: false }],
    lookupStatuses: [{ textContent: '' }, { textContent: '' }],
    interpretation: { hidden: true, textContent: '' }, runButton: { disabled: false },
    selectedReaction: null, revision: 1, resetResult() { state.revision += 1; state.selectedReaction = null; },
    renderChoices() {}, showEmpty() {}, setStatus() {}, saveDraft() {},
    comparisonHost: {}, renderComparison() {},
    updatePathwaySettings() {},
    groupPanel: { setReactants() {} },
    guidedConditions: { clear() {} }, // New read-only panel dependency; calculator assertions remain unchanged.
  };
  const api = new vm.Script(`${harnessSource}\n({updateMatches,updateCalculatorLinks});`).runInNewContext(state);
  return { state, ...api };
}

test('calculator shortcuts work for either exact input before any supported reaction', async () => {
  const { state, updateMatches, updateCalculatorLinks } = harness();
  await updateMatches();
  assert.equal(state.calculatorButtons[0].hidden, false);
  assert.match(state.calculatorButtons[0].attributes['aria-label'], /Water/);
  assert.equal(state.calculatorButtons[1].hidden, true);
  assert.equal(state.selectedReaction, null);
  state.inputB.value = 'Sodium hydroxide';
  updateCalculatorLinks();
  assert.equal(state.calculatorButtons[1].hidden, false);
  assert.match(state.calculatorButtons[1].attributes['aria-label'], /Sodium hydroxide/);
});

test('input edits and ambiguous formulas remove calculator shortcuts until an exact structure is selected', async () => {
  const { state, updateMatches, updateCalculatorLinks } = harness();
  await updateMatches();
  state.inputA.value = 'C2H6O';
  state.inputA.listeners.get('input')();
  assert.equal(state.calculatorButtons[0].hidden, true, 'ambiguous formula cannot inherit water or pick an isomer silently');
  assert.equal(state.calculatorButtons[0].disabled, true);
  state.selectedIds[0] = 'dimethyl-ether';
  updateCalculatorLinks();
  assert.equal(state.calculatorButtons[0].hidden, false);
  assert.match(state.calculatorButtons[0].attributes['aria-label'], /Dimethyl ether/);
  state.inputA.value = 'Unrecognized compound';
  state.inputA.listeners.get('input')();
  assert.equal(state.calculatorButtons[0].hidden, true, 'stale structure/mass cannot survive edited text');
  assert.equal(state.selectedIds[0], null);
});

test('calculator shortcuts also resolve PubChem and drawn contexts without requiring a reaction', () => {
  const { state, updateCalculatorLinks } = harness();
  const custom = { id: 'pubchem-333', name: 'Unreviewed structure', formula: 'C2H6O', smiles: 'COC', aliases: [] };
  state.inputA.value = custom.name;
  state.pubchemLookups[0] = { query: custom.name, items: [custom] };
  updateCalculatorLinks();
  assert.equal(state.calculatorButtons[0].hidden, false);
  assert.match(state.calculatorButtons[0].attributes['aria-label'], /Unreviewed structure/);
  state.drawnInputs[0] = { ...custom, id: 'drawn-1', name: 'Drawn structure · C2H6O' };
  state.inputA.value = state.drawnInputs[0].name;
  updateCalculatorLinks();
  assert.match(state.calculatorButtons[0].attributes['aria-label'], /Drawn structure/);
});

test('conditions preserve exact calculator links; only Explorer retains an embedded solution calculator', async () => {
  const { state, updateMatches } = harness();
  await updateMatches();
  const first = state.calculatorButtons[0].attributes['aria-label'];
  await updateMatches();
  assert.equal(state.calculatorButtons[0].attributes['aria-label'], first);
  const mainSource = await read('src/main.ts');
  assert.match(mainSource, /<details id="explorer-solution-calculator"><\/details>/);
  assert.ok(mainSource.indexOf('id="explorer-solution-calculator"') > mainSource.indexOf('id="molecule-information"'));
  assert.ok(mainSource.indexOf('id="explorer-solution-calculator"') < mainSource.indexOf('class="explorer-transfer"'));
  assert.doesNotMatch(labSource, /lab-solution-calculator|solution-compound-source|new SolutionCalculatorPanel|solution-calculator\.css/);
  assert.match(labSource, /window\.location\.assign\('\/calculators\.html#solutions'\)/);
  assert.match(await read('src/calculators.ts'), /new SolutionCalculatorPanel\(solutionHost\)/);
  assert.match(labSource, /new ReactionCalculatorPanel/, 'reaction-dependent amount calculations stay in Reaction Lab');
});
