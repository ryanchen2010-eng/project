/** Cooling presentation contract v1; independent of the frozen chemistry audit. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const compile = source => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const conditionsSource = await readFile(new URL('../src/reaction-conditions.ts', import.meta.url), 'utf8');
const { conditionGuidance, conditionNextStep, conditionLabel } = await import(
  `data:text/javascript;base64,${Buffer.from(compile(conditionsSource)).toString('base64')}`,
);
const lab = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
const file = ts.createSourceFile('reaction-lab.ts', lab, ts.ScriptTarget.ES2022, true);
const functionText = name => {
  const node = file.statements.find(item => ts.isFunctionDeclaration(item) && item.name?.text === name);
  assert.ok(node, `Missing actual production function ${name}`);
  return node.getText(file);
};

function qualified(pathway = 'Epoxidation') {
  return {
    state: 'aligned', status: 'model-match', canRun: true, coolingUnvalidated: false,
    note: 'The selected screened substrate and reagent pass the bounded cooled model.',
    cooling: {
      version: 1, pathway,
      modelId: pathway === 'Bromination' ? 'cooled-alkene-bromination-v1' : 'cooled-peroxyacid-epoxidation-v1',
      status: 'supported-model', canGenerate3D: true,
      note: 'Mild cooled reference model only; exact temperature, conversion, lifetime and isolation are not established.',
      sourceUrls: ['https://www.orgsyn.org/'],
    },
    evidence: { label: 'Cooled theoretical net model', missingRequiredSettings: [], canGenerate3D: true },
  };
}

for (const [pathway, name] of [['Bromination', 'alkene bromination'], ['Epoxidation', 'mCPBA peroxyacid epoxidation']]) {
  test(`cooling profiles v1: exact ${pathway} profile gives its own qualified theoretical wording`, () => {
    const assessment = qualified(pathway);
    const before = structuredClone(assessment);
    const prompt = conditionNextStep(assessment);
    assert.ok(prompt.startsWith(`Supported cooled ${name} model.`));
    assert.match(prompt, /View the theoretical 3D product conformer/);
    assert.match(prompt, /not a temperature simulation or a prediction of rates, yields or selectivity/);
    assert.match(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
    assert.equal(conditionLabel(assessment), assessment.evidence.label);
    assert.deepEqual(assessment, before, 'Presentation cannot change backend permission or chemistry');
  });
}

for (const [label, mutate] of [
  ['run false', a => { a.canRun = false; }],
  ['run missing', a => { delete a.canRun; }],
  ['evidence false', a => { a.evidence.canGenerate3D = false; }],
  ['evidence absent', a => { delete a.evidence; }],
  ['cooling false', a => { a.cooling.canGenerate3D = false; }],
  ['cooling unresolved', a => { a.cooling.status = 'conditions-unresolved'; }],
  ['cooling unvalidated', a => { a.cooling.status = 'unvalidated-pathway'; }],
  ['unvalidated confidence marker', a => { a.coolingUnvalidated = true; }],
  ['contradictory assessment status', a => { a.status = 'unsupported-pathway'; }],
  ['condition issue remains', a => { a.evidence.conditionIssues = [{ field: 'solvent', kind: 'unvalidated-alternative', explanation: 'Medium not qualified.' }]; }],
  ['model missing', a => { delete a.cooling.modelId; }],
  ['model unknown', a => { a.cooling.modelId = 'cooled-unreviewed-v9'; }],
  ['model/pathway mismatch', a => { a.cooling.pathway = 'Bromination'; }],
  ['other pathway', a => { a.cooling.pathway = 'Chlorination'; }],
]) {
  test(`cooling profiles v1: positive epoxidation prompt fails closed when ${label}`, () => {
    const assessment = qualified();
    mutate(assessment);
    const before = structuredClone(assessment);
    assert.doesNotMatch(conditionNextStep(assessment), /Supported cooled|View the theoretical 3D product conformer/);
    assert.match(conditionNextStep(assessment), /3D stays unavailable/);
    assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
    assert.deepEqual(assessment, before);
  });
}

test('cooling profiles v1: missing model settings and unimplemented endpoints retain priority', () => {
  const assessment = qualified();
  assessment.evidence.missingRequiredSettings = ['solvent', 'catalyst', 'solvent'];
  assert.match(conditionNextStep(assessment), /^Complete: reaction medium, additional catalyst \/ activation\./);
  assert.doesNotMatch(conditionNextStep(assessment), /Supported cooled|View the theoretical 3D/);
  assert.match(conditionGuidance(assessment), /Missing: reaction medium/);
  assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
  assessment.evidence.aldehydeEndpointValidated = false;
  assert.match(conditionNextStep(assessment), /Changing dropdowns will not enable 3D/);
  assert.doesNotMatch(conditionNextStep(assessment), /^Complete:/);
});

test('cooling profiles v1: rejected peracid conditions retain the actual backend reason', () => {
  const assessment = qualified();
  assessment.canRun = false;
  assessment.evidence.canGenerate3D = false;
  assessment.cooling.canGenerate3D = false;
  assessment.cooling.status = 'conditions-unresolved';
  assessment.cooling.note = 'This cooled profile requires actual mCPBA and the reviewed non-capturing medium; another peroxyacid is not inferred to be equivalent.';
  const prompt = conditionNextStep(assessment);
  assert.ok(prompt.includes(assessment.cooling.note));
  assert.match(prompt, /Conditional 2D remains available; 3D stays unavailable/);
  assert.match(prompt, /do not substitute room temperature unless that is your intended setting/);
  assert.doesNotMatch(prompt, /reaction is impossible|cannot react/);
});

test('cooling profiles v1: accessible help distinguishes bounded mCPBA and Br2 from universal cooling', () => {
  const help = lab.match(/<p[^>]+id="reaction-temperature-help"[^>]*>([^<]*)<\/p>/)?.[1];
  assert.ok(help);
  assert.match(help, /eligible alkene Br₂ addition/);
  assert.match(help, /bounded mCPBA epoxidation profile/);
  assert.match(help, /does not approve every peroxyacid/);
  assert.match(help, /mild cooled reference models, not arbitrary cryogenic conditions/);
  assert.match(help, /3D does not simulate temperature/);
  assert.doesNotMatch(help, /\d+\s*(?:°|degrees|kelvin)/i);
  assert.match(lab, /id="reaction-temperature" aria-describedby="reaction-temperature-help"/);
  assert.match(lab, /else if \(reaction\.assessment\?\.cooling && !conditionAssessment\.textContent\.includes\(guidance\)\)/);
  assert.match(lab, /if \(payload\.assessment\.cooling\)/);
  assert.doesNotMatch(lab, /<input[^>]+temperatureCelsius|<select[^>]+cooling-profile/);
});

function element() {
  return { hidden: false, open: false, disabled: false, textContent: '',
    classList: { toggle() {} }, setAttribute(key, value) { this[key] = value; }, replaceChildren() {} };
}

/** Exercise actual page lifecycle functions, including a late cooled response. */
function lifecycle(fetcher) {
  const calls = [];
  const assessment = qualified();
  const state = {
    revision: 1, selectedReaction: { id: 'cooled-epoxide-fixture', mechanism: 'Epoxidation', assessment,
      productEquationFormula: 'C2H4O', explanation: 'Bounded epoxidation', conditions: 'Defined model' },
    productReady: false, previewMode: '2d', runController: null, diagramController: null,
    diagramData: { atoms: [], highlightsAvailable: true, note: null }, reactionSiteShapes: [],
    cameraControls: { setEnabled() {}, setVisible() {} },
    measurements: { available: false, reset() { calls.push('reset-measurements'); }, setAtoms() {} },
    atomInspector: { reset() { calls.push('reset-inspector'); }, clearHover() {}, setModel() {}, setDiagram() {} },
    informationPanel: { setReaction() { calls.push('clear-info'); } },
    reactionCalculator: { setReaction() { calls.push('clear-calculator'); } },
    mechanismPanel: { reset() { calls.push('reset-mechanism'); }, clearModel() {}, setModel() {} },
    viewer: { removeAllModels() { calls.push('remove-models'); }, removeShape() {},
      addModel() { calls.push('add-model'); return { selectedAtoms: () => [] }; },
      setStyle() {}, zoomTo() {}, resize() {}, render() {} },
    resolveReactant: index => ({ id: String(index) }), reactantReference: r => r,
    currentConditions: () => ({ temperature: 'cooled', solvent: 'dry', catalyst: 'none' }),
    conditionLabel, conditionGuidance, formatEquation: () => 'Net epoxidation',
    setStatus: text => calls.push(['status', text]), required: () => element(),
    requestAnimationFrame: callback => callback(), AbortController, Error,
    fetch: fetcher ?? (async () => ({ ok: true, json: async () => ({
      productName: 'Oxirane', balanced: true, assessment,
      product: { molfile: 'Synthetic conformer fixture', formula: 'C2H4O', smiles: 'C1CO1',
        representation: '3d', forceField: 'MMFF94', converged: true, atomLinks: [] },
    }) })),
  };
  for (const name of ['measurementsHost', 'diagramScroll', 'atomInspection', 'diagramPlaceholder', 'diagramHost',
    'bondSummary', 'bondLegend', 'diagramNote', 'viewerHost', 'placeholder', 'details', 'learning', 'equation',
    'conditionAssessment', 'formulaNote', 'view2D', 'view3D', 'viewCompare', 'runButton', 'viewerHint',
    'previewHost', 'workspace', 'previewLabel']) state[name] = element();
  const selected = ['resetResult', 'updatePreviewActions', 'setPreview', 'showProduct3D'].map(functionText).join('\n');
  const functions = new vm.Script(`${compile(selected)}\n({resetResult, showProduct3D});`).runInNewContext(state);
  return { state, calls, ...functions };
}

test('cooling profiles v1: an accepted epoxide response retains visible theoretical confidence', async () => {
  const { state, calls, showProduct3D } = lifecycle();
  await showProduct3D('compare');
  assert.equal(state.productReady, true);
  assert.ok(calls.includes('add-model'));
  assert.match(state.conditionAssessment.textContent, /Cooled 3D is a theoretical product conformer/);
  assert.match(state.conditionAssessment.textContent, /Mild cooled reference model only/);
  assert.match(state.conditionAssessment.title, /not a temperature simulation/);
});

test('cooling profiles v1: condition invalidation clears every old result before a late 3D response', async () => {
  let deliver;
  const response = new Promise(resolve => { deliver = resolve; });
  const { state, calls, resetResult, showProduct3D } = lifecycle(() => response);
  const assessment = state.selectedReaction.assessment;
  const pending = showProduct3D('compare');
  const oldRevision = state.revision;
  const controller = state.runController;
  resetResult();
  assert.equal(controller.signal.aborted, true);
  assert.equal(state.revision, oldRevision + 1);
  assert.equal(state.selectedReaction, null);
  assert.equal(state.productReady, false);
  assert.equal(state.previewMode, '2d');
  assert.equal(state.runButton.disabled, true);
  for (const expected of ['reset-measurements', 'reset-inspector', 'reset-mechanism', 'clear-calculator', 'clear-info', 'remove-models']) {
    assert.ok(calls.includes(expected), expected);
  }
  deliver({ ok: true, json: async () => ({ assessment, productName: 'Old oxirane',
    product: { representation: '3d', molfile: 'Late response' } }) });
  await pending;
  assert.equal(state.productReady, false);
  assert.ok(!calls.includes('add-model'), 'An old cooled product cannot reappear after a condition change');
});
