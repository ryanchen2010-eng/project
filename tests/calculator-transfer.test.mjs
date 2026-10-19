import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';
const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const compile = (source) => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const moduleUrl = (source) => `data:text/javascript;base64,${Buffer.from(compile(source)).toString('base64')}`;
const compoundSource = (await read('src/calculator-compound.ts')).replace("from './solution-compound'", `from '${moduleUrl(await read('src/solution-compound.ts'))}'`);
const { CALCULATOR_TRANSFER_KEY, calculatorCompoundFromMolecule, calculatorCompoundFromReactant, encodeCalculatorTransfer, decodeCalculatorTransfer } = await import(moduleUrl(compoundSource));
const shared = JSON.parse(await read('src/shared-molecules.json'));
const { molecules, isIonicCompound } = await import(moduleUrl((await read('src/molecules.ts')).replace("import sharedCatalog from './shared-molecules.json';", `const sharedCatalog = ${JSON.stringify(shared)};`)));
test('Explorer transfer preserves exact identities, masses and formula-unit kind', () => {
  for (const [id, mass] of [['water', 18.015], ['ethanol', 46.07], ['sodium-chloride', 58.443], ['sodium-hydroxide', 39.997]]) {
    const molecule = molecules.find((m) => m.id === id);
    const original = calculatorCompoundFromMolecule(molecule, isIonicCompound(molecule));
    const result = decodeCalculatorTransfer(encodeCalculatorTransfer(original));
    assert.equal(result.id, id); assert.equal(result.molarMass, mass); assert.equal(result.cid, molecule.cid);
    assert.equal(result.structure, molecule.structureForm);
    assert.equal(result.entityKind, id.startsWith('sodium-') ? 'formula-units' : 'molecules');
  }
});
test('same-formula isomers remain distinct and missing masses stay missing', () => {
  const ethanol = calculatorCompoundFromMolecule(molecules.find((m) => m.id === 'ethanol'), false);
  const ether = calculatorCompoundFromMolecule(molecules.find((m) => m.id === 'dimethyl-ether'), false);
  assert.notEqual(ethanol.id, ether.id); assert.notEqual(ethanol.structure, ether.structure);
  const unreviewed = { ...molecules[0], id: 'pubchem-1234', name: 'Exact form', properties: { ...molecules[0].properties, mass: 'N/A' } };
  assert.equal(decodeCalculatorTransfer(encodeCalculatorTransfer(calculatorCompoundFromMolecule(unreviewed, false))).molarMass, undefined);
});
test('only an exact one-atom structure becomes an atomic entity; formulas do not guess it', () => {
  for (const structureForm of ['[He]', '[Ne]', '[13C]', '[Cl-]']) {
    const molecule = { ...molecules[0], structureForm };
    assert.equal(calculatorCompoundFromMolecule(molecule, false).entityKind, 'atoms');
  }
  for (const structureForm of ['[Na+].[Cl-]', 'O', '[NH4+]', undefined]) {
    const molecule = { ...molecules[0], formula: 'He', structureForm };
    assert.notEqual(calculatorCompoundFromMolecule(molecule, false).entityKind, 'atoms');
  }
});
test('untrusted transfer rejects bad versions, types, masses and oversize labels', () => {
  const c = calculatorCompoundFromMolecule(molecules[0], false);
  for (const raw of [null, '', '{', JSON.stringify(c), JSON.stringify({ version: 2, compound: c }), ' '.repeat(17000)]) assert.equal(decodeCalculatorTransfer(raw), undefined);
  for (const mutation of [{ id: '' }, { name: 'a'.repeat(201) }, { formula: 5 }, { structure: [] }, { cid: 0 }, { cid: 1.5 }, { molarMass: 0 }, { molarMass: '18' }, { entityKind: 'guess' }]) {
    assert.equal(decodeCalculatorTransfer(JSON.stringify({ version: 1, compound: { ...c, ...mutation } })), undefined);
  }
});
test('actual Explorer action writes selected ionic compound even without a structure/viewer', async () => {
  const source = await read('src/main.ts');
  const ast = ts.createSourceFile('main.ts', source, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
  const fn = ast.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === 'openInCalculators');
  assert.ok(fn);
  const status = { textContent: '' }; const saved = []; const routes = [];
  const state = { activeMolecule: molecules.find((m) => m.id === 'sodium-chloride'),
    mustElement: () => status, calculatorCompoundFromMolecule, isIonicCompound, encodeCalculatorTransfer, CALCULATOR_TRANSFER_KEY,
    sessionStorage: { setItem(key, value) { saved.push([key, value]); } }, window: { location: { assign(route) { routes.push(route); } } } };
  const action = new vm.Script(`${compile(fn.getText(ast))}; openInCalculators;`).runInNewContext(state);
  action(); assert.equal(decodeCalculatorTransfer(saved[0][1]).molarMass, 58.443); assert.deepEqual(routes, ['/calculators.html#moles']);
  state.activeMolecule = null; action(); assert.match(status.textContent, /Select a compound/); assert.equal(saved.length, 1);
  state.activeMolecule = molecules[0]; state.sessionStorage.setItem = () => { throw Error('blocked'); }; action();
  assert.match(status.textContent, /unavailable/); assert.equal(routes.length, 1);
});
test('hub reuses catalog identity only by id, CID and structure, not formula', async () => {
  const hub = await read('src/calculators.ts');
  assert.match(hub, /reviewed\.cid === transferred\.cid && reviewed\.structure === transferred\.structure/);
  assert.doesNotMatch(hub, /reviewed\.formula === transferred\.formula/);
  assert.match(hub, /sessionStorage\.removeItem\(CALCULATOR_TRANSFER_KEY\)/);
  assert.match(hub, /solutionPanel\.setCompound\(compound\)/);
});

test('Reaction Lab transfer preserves exact neutral and full salt identities and masses', () => {
  for (const id of ['ethanol', 'sodium-hydroxide', 'sodium-chloride']) {
    const record = shared.find((r) => r.id === id);
    const compound = calculatorCompoundFromReactant(record, molecules);
    const expected = calculatorCompoundFromMolecule(molecules.find((m) => m.id === id), id.startsWith('sodium-'));
    assert.deepEqual(compound, expected);
    assert.deepEqual(decodeCalculatorTransfer(encodeCalculatorTransfer(compound)), expected);
  }
});

test('unreviewed or changed Reaction Lab structures never borrow a same-formula mass or counterion', () => {
  for (const reactant of [
    { id: 'ethanol', name: 'Ether', formula: 'C2H6O', smiles: 'COC' },
    { id: 'pubchem-999', name: 'Unreviewed ethanol', formula: 'C2H6O', smiles: 'CCO' },
    { id: 'hydroxide', name: 'Hydroxide ion', formula: 'OH-', smiles: '[OH-]' },
    { id: 'drawn-1', name: 'Drawn structure', formula: 'C3H8O', smiles: 'CCCO' },
  ]) {
    const result = decodeCalculatorTransfer(encodeCalculatorTransfer(calculatorCompoundFromReactant(reactant, molecules)));
    assert.equal(result.molarMass, undefined); assert.equal(result.structure, reactant.smiles);
    assert.equal(result.id, reactant.id); assert.equal(result.name, reactant.name);
  }
});

test('actual Reaction Lab shortcut transfers the chosen input into Solutions and handles missing identity/storage', async () => {
  const source = await read('src/reaction-lab.ts');
  const ast = ts.createSourceFile('reaction-lab.ts', source, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS);
  const fn = ast.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === 'openSolutionCalculator');
  assert.ok(fn);
  const salt = shared.find((r) => r.id === 'sodium-hydroxide');
  const saved = []; const routes = []; const statuses = []; const drafts = [];
  const state = { resolveReactant: (slot) => slot === 1 ? salt : undefined, molecules,
    calculatorCompoundFromReactant, encodeCalculatorTransfer, CALCULATOR_TRANSFER_KEY,
    sessionStorage: { setItem(key, raw) { saved.push([key, raw]); } }, saveDraft() { drafts.push(true); },
    setStatus(text) { statuses.push(text); }, window: { location: { assign(route) { routes.push(route); } } } };
  const action = new vm.Script(`${compile(fn.getText(ast))}; openSolutionCalculator;`).runInNewContext(state);
  action(1);
  assert.equal(saved[0][0], CALCULATOR_TRANSFER_KEY);
  assert.equal(decodeCalculatorTransfer(saved[0][1]).molarMass, 39.997);
  assert.deepEqual(routes, ['/calculators.html#solutions']); assert.equal(drafts.length, 1);
  action(0); assert.match(statuses.at(-1), /Select an exact compound/); assert.equal(saved.length, 1);
  state.sessionStorage.setItem = () => { throw Error('blocked'); };
  action(1); assert.match(statuses.at(-1), /unavailable/); assert.equal(routes.length, 1);
});
