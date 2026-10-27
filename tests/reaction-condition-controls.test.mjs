import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const compile = source => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const load = async path => import(`data:text/javascript;base64,${Buffer.from(compile(await read(path))).toString('base64')}`);
const source = await read('src/reaction-lab.ts');
const sourceFile = ts.createSourceFile('reaction-lab.ts', source, ts.ScriptTarget.Latest, true);

function findNode(root, predicate) {
  if (predicate(root)) return root;
  return ts.forEachChild(root, child => findNode(child, predicate));
}
function declaration(name) {
  const node = findNode(sourceFile, node => ts.isFunctionDeclaration(node) && node.name?.text === name);
  assert.ok(node, `Missing production function: ${name}`);
  return node;
}
function selectMarkup(id) {
  const match = source.match(new RegExp(`<select\\b([^>]*\\bid="${id}"[^>]*)>([\\s\\S]*?)</select>`));
  assert.ok(match, `Missing select: ${id}`);
  return {
    attributes: match[1],
    options: [...match[2].matchAll(/<option value="([^"]*)">([^<]*)<\/option>/g)]
      .map(([, value, label]) => ({ value, label })),
  };
}
function helpFor(id, kind = 'select') {
  const attributes = kind === 'select' ? selectMarkup(id).attributes
    : source.match(new RegExp(`<input\\b([^>]*\\bid="${id}"[^>]*)>`))?.[1];
  assert.ok(attributes, `Missing control: ${id}`);
  const ids = attributes.match(/aria-describedby="([^"]+)"/)?.[1].split(/\s+/);
  assert.ok(ids?.length, `${id} needs an accessible helper`);
  return ids.map(helperId => {
    const match = source.match(new RegExp(`<p\\b[^>]*\\bid="${helperId}"[^>]*>([^<]*)</p>`));
    assert.ok(match, `Broken description link: ${helperId}`);
    return match[1];
  }).join(' ');
}
const controls = () => ({
  solventInput: { value: 'dry' }, temperatureInput: { value: 'cooled' }, catalystInput: { value: 'none' },
  oxidationStageInput: { value: '' }, additionStageInput: { value: 'one' },
  polymerUnitsInput: { value: '4' }, workupInput: { value: '' },
});
function conditionsFrom(values) {
  return new Function(...Object.keys(values), `const namedProfileSelection = null; ${compile(declaration('currentConditions').getText(sourceFile))}; return currentConditions();`)(...Object.values(values));
}

test('temperature adds cooled without renaming or removing existing serialized choices', () => {
  assert.deepEqual(selectMarkup('reaction-temperature').options, [
    { value: '', label: 'Not specified' },
    { value: 'cooled', label: 'Cooled / Low Temperature' },
    { value: 'ambient', label: 'Room temperature' },
    { value: 'heated', label: 'Heated' },
  ]);
  const help = helpFor('reaction-temperature');
  assert.match(help, /qualitative/i);
  assert.match(help, /not exact temperatures/i);
  assert.match(help, /assessed by pathway/i);
  assert.match(help, /eligible alkene Br₂ addition can show a theoretical 3D product/i);
  assert.match(help, /all model requirements are met/i);
  assert.match(help, /unvalidated/i);
  assert.match(help, /Other cooled cases remain conditional 2D/i);
  assert.match(help, /3D does not simulate temperature/i);
  assert.doesNotMatch(help, /cooling does not qualify a 3D product/i);
  assert.doesNotMatch(help, /\d+\s*(?:°|degrees|kelvin)/i);
});

test('additional activation retains every existing catalyst code and does not invent generic base catalysis', () => {
  assert.match(source, /<label for="reaction-catalyst">Additional Catalyst \/ Activation<\/label>/);
  const options = selectMarkup('reaction-catalyst').options;
  assert.deepEqual(options.map(option => option.value), ['', 'none', 'acid', 'metal', 'lindlar', 'osmium', 'radical']);
  assert.ok(options.every(option => option.label.trim()));
  assert.equal(options.find(option => option.value === 'none').label, 'None Added');
  assert.match(options.find(option => option.value === 'acid').label, /activation.*catalysis/i);
  assert.match(options.find(option => option.value === 'radical').label, /initiation.*supported model/i);
  assert.doesNotMatch(options.map(option => option.label).join(' '), /base catalyst/i);
  const help = helpFor('reaction-catalyst');
  assert.match(help, /not a replacement reagent/i);
  assert.match(help, /hydroxide.*chemical input/i);
  assert.match(help, /no general base-catalysis model/i);
  assert.match(help, /partner may already supply acid activation/i);
});

test('second chemical input describes pathway-dependent reagent, solvent and catalyst roles accessibly', () => {
  assert.match(source, /<label for="reactant-b">Molecule 2 · Reagent \/ Partner<\/label>/);
  const help = helpFor('reactant-b', 'input');
  assert.match(help, /actual chemical/i);
  assert.match(help, /consumed reactant, solvent or catalyst/i);
  assert.match(help, /depends on the pathway/i);
  assert.match(source, /id="reactant-b"[^>]*aria-describedby="[^"]*reactant-b-lookup-status/);
});

test('actual serialized conditions preserve cooled and the original API field names', () => {
  const result = conditionsFrom(controls());
  assert.deepEqual(result, {
    solvent: 'dry', temperature: 'cooled', catalyst: 'none', oxidationStage: '',
    additionStage: 'one', polymerUnits: '4', workup: '',
  });
  assert.deepEqual(JSON.parse(JSON.stringify(result)), result);
  assert.equal(Object.hasOwn(result, 'activation'), false);
  assert.equal(Object.hasOwn(result, 'temperatureCelsius'), false);
});

test('legacy temperature and activation values remain unmodified during serialization', () => {
  for (const temperature of ['', 'ambient', 'heated']) {
    for (const catalyst of ['', 'none', 'acid', 'metal', 'lindlar', 'osmium', 'radical']) {
      const values = controls();
      values.temperatureInput.value = temperature;
      values.catalystInput.value = catalyst;
      const result = conditionsFrom(values);
      assert.equal(result.temperature, temperature);
      assert.equal(result.catalyst, catalyst);
    }
  }
});

test('the reviewed secondary oxidation medium keeps its exact profile while cooled stays explicit', () => {
  const values = controls();
  values.solventInput.value = 'secondary-naocl-acetic';
  const result = conditionsFrom(values);
  assert.equal(result.solvent, 'aqueous-protic');
  assert.equal(result.secondaryOxidationProfile, 'naocl-acetic-ketone-v1');
  assert.equal(result.temperature, 'cooled');
  assert.equal(result.catalyst, 'none');
});

test('temperature and activation changes save and rematch rather than reusing prior product permission', () => {
  const listenerLoop = sourceFile.statements.find(node => ts.isForOfStatement(node)
    && node.getText(sourceFile).startsWith('for (const select of [solventInput, temperatureInput, catalystInput')
    && node.getText(sourceFile).includes("addEventListener('change'"));
  assert.ok(listenerLoop, 'Condition controls must retain change invalidation');
  const values = controls();
  for (const control of Object.values(values)) control.addEventListener = (name, callback) => {
    assert.equal(name, 'change');
    control.change = callback;
  };
  const calls = [];
  new Function(...Object.keys(values), 'selectedReaction', 'saveDraft', 'updateMatches', compile(listenerLoop.getText(sourceFile)))(
    ...Object.values(values), { id: 'selected-site' }, () => calls.push('saved'), id => calls.push(['rematch', id]),
  );
  values.temperatureInput.change();
  values.catalystInput.change();
  assert.deepEqual(calls, ['saved', ['rematch', 'selected-site'], 'saved', ['rematch', 'selected-site']]);
  const reset = declaration('updateMatches').getText(sourceFile);
  assert.ok(reset.indexOf('resetResult()') < reset.indexOf("fetch('/api/reactions/match'"));
  assert.ok(reset.indexOf('selectedReaction = null') < reset.indexOf("fetch('/api/reactions/match'"));
  assert.ok(reset.indexOf('runButton.disabled = true') < reset.indexOf("fetch('/api/reactions/match'"));
});

test('restoring drafts accepts the new option only through the existing allowed-value check', () => {
  const restoreLoop = findNode(sourceFile, node => ts.isForOfStatement(node)
    && node.getText(sourceFile).startsWith('for (const [key, select] of')
    && node.getText(sourceFile).includes('draft.conditions?.[key]'));
  assert.ok(restoreLoop);
  const values = controls();
  const ids = ['reaction-solvent', 'reaction-temperature', 'reaction-catalyst', 'reaction-oxidation-stage',
    'reaction-addition-stage', 'reaction-polymer-units', 'reaction-diol-workup'];
  Object.values(values).forEach((control, index) => {
    control.options = selectMarkup(ids[index]).options;
    control.value = '';
  });
  const restore = draft => new Function(...Object.keys(values), 'draft', compile(restoreLoop.getText(sourceFile)))(...Object.values(values), draft);
  restore({ conditions: { temperature: 'cooled', catalyst: 'acid' } });
  assert.equal(values.temperatureInput.value, 'cooled');
  assert.equal(values.catalystInput.value, 'acid');
  restore({ conditions: { temperature: 'invented-degrees', catalyst: 'base' } });
  assert.equal(values.temperatureInput.value, 'cooled');
  assert.equal(values.catalystInput.value, 'acid');
});

test('workspace condition summary renders current visible labels, including cooled, not enum keys', async () => {
  const workspaceSource = await read('src/reaction-workspace.ts');
  const file = ts.createSourceFile('reaction-workspace.ts', workspaceSource, ts.ScriptTarget.Latest, true);
  const refresh = findNode(file, node => ts.isVariableDeclaration(node) && node.name.getText(file) === 'refresh');
  assert.ok(refresh && ts.isArrowFunction(refresh.initializer) && ts.isBlock(refresh.initializer.body));
  const firstStatements = refresh.initializer.body.statements.slice(0, 3).map(node => node.getText(file)).join('\n');
  const selected = {
    '#reaction-solvent': { value: '' },
    '#reaction-temperature': { value: 'cooled', selectedOptions: [{ textContent: 'Cooled / Low Temperature' }] },
    '#reaction-catalyst': { value: 'acid', selectedOptions: [{ textContent: 'Acid Activation / Catalysis' }] },
  };
  const contextText = {};
  new Function('get', 'contextText', compile(firstStatements))(selector => selected[selector], contextText);
  assert.equal(contextText.textContent, 'Cooled / Low Temperature · Acid Activation / Catalysis');
});

test('missing-condition prompts use the same additional-activation label without changing permissions', async () => {
  const { conditionGuidance, conditionNextStep } = await load('src/reaction-conditions.ts');
  const assessment = { state: 'incomplete', canRun: false, note: 'Cooling has not been validated.', evidence: {
    missingRequiredSettings: ['temperature', 'catalyst', 'catalyst'], canGenerate3D: false,
  } };
  const before = structuredClone(assessment);
  assert.match(conditionNextStep(assessment), /Complete: temperature, additional catalyst \/ activation\./);
  assert.match(conditionGuidance(assessment), /Missing: temperature, additional catalyst \/ activation\./);
  assert.match(conditionGuidance(assessment), /Conditional 2D remains available/);
  assert.deepEqual(assessment, before);
});

test('unvalidated cooling has an actionable conditional-only message and never changes the selected temperature', async () => {
  const { conditionNextStep } = await load('src/reaction-conditions.ts');
  const assessment = { canRun: false, coolingUnvalidated: true, evidence: {
    missingRequiredSettings: [], canGenerate3D: false,
  } };
  const before = structuredClone(assessment);
  const message = conditionNextStep(assessment);
  assert.match(message, /Cooled conditions are recorded/);
  assert.match(message, /no low-temperature profile is validated/);
  assert.match(message, /Conditional 2D remains available; 3D stays unavailable/);
  assert.match(message, /do not substitute room temperature unless that is your intended setting/);
  assert.deepEqual(assessment, before);
});

test('cooling warnings preserve missing-field and unimplemented aldehyde-endpoint guidance priorities', async () => {
  const { conditionNextStep } = await load('src/reaction-conditions.ts');
  const assessment = { canRun: false, coolingUnvalidated: true, evidence: {
    missingRequiredSettings: ['catalyst', 'secondaryOxidationProfile'], canGenerate3D: false,
  } };
  const missing = conditionNextStep(assessment);
  assert.match(missing, /Complete: additional catalyst \/ activation, secondary NaOCl\/acetic-acid medium profile\./);
  assert.match(missing, /Cooled conditions are also unvalidated and do not qualify 3D/);
  const aldehyde = conditionNextStep({ ...assessment, evidence: {
    ...assessment.evidence, aldehydeEndpointValidated: false,
  } });
  assert.match(aldehyde, /validated selective-aldehyde model is not implemented/);
  assert.match(aldehyde, /Changing dropdowns will not enable 3D/);
  assert.doesNotMatch(aldehyde, /Complete:/);
});

test('public match, diagram and run requests retain the same condition object and endpoint contract', () => {
  for (const endpoint of ['match', 'diagram', 'run']) {
    const position = source.indexOf(`fetch('/api/reactions/${endpoint}'`);
    assert.ok(position >= 0);
    const request = source.slice(position, source.indexOf('\n    });', position));
    assert.match(request, /method: 'POST'/);
    assert.match(request, /conditions: currentConditions\(\)/);
    assert.doesNotMatch(request, /temperatureCelsius|catalystLabel|baseCatalyst/);
  }
});

test('conditional cooling remains context only and does not change theoretical stoichiometry', async () => {
  const { calculateReaction, copyCalculationContext } = await load('src/reaction-calculator.ts');
  const data = {
    balanced: true,
    reactants: [
      { inputSlot: 0, name: 'Bromomethane', formula: 'CH3Br', molarMass: 94.939, coefficient: 1 },
      { inputSlot: 1, name: 'Hydroxide ion', formula: 'HO-', molarMass: 17.007, coefficient: 1 },
    ],
    product: { name: 'Methanol', formula: 'CH4O', molarMass: 32.042, coefficient: 1 },
    excludedInputs: [], notes: [],
  };
  const context = {
    version: 1, assertionLevel: 'conditional-net', pathway: 'SN2', label: 'Conditional theoretical amounts',
    conditionStatus: 'unevaluated', conditions: { temperature: 'cooled', catalyst: 'none' },
    missingRequiredSettings: [], unknownConditions: ['temperature', 'catalyst'], canGenerate3D: false,
    assumptions: ['100% stoichiometric conversion; no yield prediction.'], warning: 'Cooling is not a validated temperature profile.',
  };
  const amounts = { 0: { value: 0.1, unit: 'mol' }, 1: { value: 0.2, unit: 'mol' } };
  const plain = calculateReaction(data, amounts);
  assert.deepEqual(calculateReaction({ ...data, context }, amounts), plain);
  assert.equal(plain.product.moles, 0.1);
  assert.ok(Math.abs(plain.product.grams - 3.2042) < 1e-12);
  const copied = copyCalculationContext(context);
  assert.equal(copied.conditions.temperature, 'cooled');
  assert.equal(copied.canGenerate3D, false);
  const panel = await read('src/reaction-calculator-panel.ts');
  assert.match(panel, /catalyst: 'additional catalyst \/ activation'/);
});
