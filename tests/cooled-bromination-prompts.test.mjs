import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/reaction-conditions.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const { conditionGuidance, conditionLabel, conditionNextStep } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

const complete = () => ({
  state: 'aligned', status: 'model-match', canRun: true, coolingUnvalidated: false,
  note: 'Selected site and medium satisfy the bounded cooled Br₂ addition model.',
  cooling: {
    version: 1, pathway: 'Bromination', modelId: 'cooled-alkene-bromination-v1',
    status: 'supported-model', canGenerate3D: true,
    note: 'Cooled alkene bromination supported within the reviewed model; no temperature range or experimental selectivity is predicted.',
    sourceUrls: ['https://www.orgsyn.org/demo.aspx?prep=CV2P0171'],
  },
  evidence: {
    label: 'Supported theoretical model', missingRequiredSettings: [], canGenerate3D: true,
  },
});

test('qualified cooled bromination offers a theoretical conformer without experimental claims', () => {
  const assessment = complete();
  const before = structuredClone(assessment);
  const prompt = conditionNextStep(assessment);
  assert.match(prompt, /Supported cooled alkene bromination model/);
  assert.match(prompt, /View the theoretical 3D product conformer/);
  assert.match(prompt, /not a temperature simulation or a prediction of rates, yields or selectivity/);
  assert.doesNotMatch(prompt, /3D stays unavailable|no low-temperature profile/);
  assert.equal(conditionLabel(assessment), 'Supported theoretical model');
  assert.deepEqual(assessment, before);
});

test('qualified cooling guidance keeps backend notes and explains what 3D represents', () => {
  const assessment = complete();
  const text = conditionGuidance(assessment);
  assert.match(text, /Structure\/site supported/);
  assert.ok(text.includes(assessment.note));
  assert.ok(text.includes(assessment.cooling.note));
  assert.match(text, /Cooled 3D is a theoretical product conformer/);
  assert.match(text, /not a temperature simulation/);
  assert.doesNotMatch(text, /3D is blocked/);
});

for (const [label, mutate] of [
  ['run permission false', a => { a.canRun = false; }],
  ['run permission absent', a => { delete a.canRun; }],
  ['evidence permission false', a => { a.evidence.canGenerate3D = false; }],
  ['evidence absent', a => { delete a.evidence; }],
  ['cooling permission false', a => { a.cooling.canGenerate3D = false; }],
  ['unresolved cooling status', a => { a.cooling.status = 'conditions-unresolved'; }],
]) {
  test(`cooled positive prompt requires consistent backend permissions: ${label}`, () => {
    const assessment = complete();
    mutate(assessment);
    const prompt = conditionNextStep(assessment);
    assert.doesNotMatch(prompt, /View the theoretical 3D product conformer|Supported cooled alkene bromination model/);
    assert.match(prompt, /3D stays unavailable/);
    if (assessment.evidence) assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
  });
}

test('blocked bromination uses the precise backend blocker instead of denying all cooled chemistry', () => {
  const assessment = complete();
  assessment.canRun = false;
  assessment.evidence.canGenerate3D = false;
  assessment.cooling.status = 'conditions-unresolved';
  assessment.cooling.canGenerate3D = false;
  assessment.cooling.note = 'The selected water medium permits competing bromohydrin formation; this dibromide model requires a supported non-nucleophilic medium.';
  const prompt = conditionNextStep(assessment);
  assert.ok(prompt.includes(assessment.cooling.note));
  assert.match(prompt, /Use Edit conditions/);
  assert.match(prompt, /do not substitute room temperature unless that is your intended setting/);
  assert.doesNotMatch(prompt, /no low-temperature profile is validated/);
});

test('other cooled pathways remain conditional without claiming their chemistry is impossible', () => {
  const assessment = complete();
  assessment.canRun = false;
  assessment.cooling = {
    version: 1, pathway: 'Chlorination', modelId: null, status: 'unvalidated-pathway',
    canGenerate3D: false, sourceUrls: [], note: 'No cooled model is validated for the selected chlorination pathway.',
  };
  assessment.evidence.canGenerate3D = false;
  const before = structuredClone(assessment);
  const prompt = conditionNextStep(assessment);
  assert.match(prompt, /selected chlorination pathway/);
  assert.match(prompt, /Conditional 2D remains available; 3D stays unavailable/);
  assert.doesNotMatch(prompt, /reaction is impossible|View the theoretical 3D/);
  assert.deepEqual(assessment, before);
});

test('missing requirements stay ahead of cooled-model status and identify existing fields', () => {
  const assessment = complete();
  assessment.evidence.missingRequiredSettings = ['solvent', 'catalyst', 'solvent'];
  assessment.cooling.note = 'Review the reaction medium and additional activation before cooled 3D can be qualified.';
  const prompt = conditionNextStep(assessment);
  assert.match(prompt, /^Complete: reaction medium, additional catalyst \/ activation\./);
  assert.ok(prompt.includes(assessment.cooling.note));
  assert.doesNotMatch(prompt, /View the theoretical 3D product conformer|no low-temperature profile is validated/);
  assert.match(conditionGuidance(assessment), /Missing: reaction medium, additional catalyst \/ activation/);
  assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
});

test('unimplemented selective aldehyde endpoint keeps its stronger priority', () => {
  const assessment = complete();
  assessment.evidence.aldehydeEndpointValidated = false;
  assessment.evidence.missingRequiredSettings = ['catalyst'];
  const prompt = conditionNextStep(assessment);
  assert.match(prompt, /validated selective-aldehyde model is not implemented/);
  assert.match(prompt, /Changing dropdowns will not enable 3D/);
  assert.doesNotMatch(prompt, /Complete:|View the theoretical 3D/);
  assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
});

test('legacy assessments without cooling metadata retain the existing wording and permissions', () => {
  assert.equal(conditionNextStep({ state: 'aligned', status: 'model-match', canRun: true }), '');
  assert.match(conditionNextStep({ canRun: false, coolingUnvalidated: true, evidence: {
    missingRequiredSettings: [], canGenerate3D: false,
  } }), /no low-temperature profile is validated/);
  const assessment = { state: 'aligned', canRun: true, note: 'Existing model.', evidence: {
    missingRequiredSettings: [], canGenerate3D: true,
  } };
  assert.match(conditionGuidance(assessment), /3D is a conditional net-model conformer, not a verified experimental outcome/);
});

test('cooling confidence remains visible before and after generation without a new layout or condition field', async () => {
  const lab = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
  assert.match(lab, /reaction\.mechanism === 'Bromination' && reaction\.assessment\?\.cooling/);
  assert.match(lab, /if \(payload\.assessment\.cooling\) \{\s+const coolingGuidance = conditionGuidance\(payload\.assessment\);\s+conditionAssessment\.textContent \+= ` — \$\{coolingGuidance\}`/);
  assert.match(lab, /const guidance = conditionGuidance\(reaction\.assessment\)/);
  assert.match(lab, /for \(const control of \[view3D, viewCompare, runButton\]\) control\.title = guidance/);
  assert.doesNotMatch(lab, /<input[^>]+temperatureCelsius|<select[^>]+cooling-profile/);
});
