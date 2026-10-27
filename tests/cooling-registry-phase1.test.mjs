/** V1 registry consolidation contracts; no new chemistry or visible fixtures. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = await readFile(new URL('../src/reaction-conditions.ts', import.meta.url), 'utf8');
const compile = value => ts.transpileModule(value, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const { REVIEWED_COOLING_MODELS, conditionNextStep, conditionGuidance } = await import(
  `data:text/javascript;base64,${Buffer.from(compile(source)).toString('base64')}`);
const python = code => JSON.parse(execFileSync(`${root}.venv/bin/python`, ['-c', code], { cwd: root, encoding: 'utf8' }));

function qualified() {
  return {
    state: 'aligned', status: 'model-match', canRun: true, coolingUnvalidated: false,
    note: 'Existing bounded cooled net model, not an experimental result.',
    cooling: {
      version: 1, registryVersion: 1, profileVersion: 1, reasonCodes: [], pathway: 'Bromination',
      modelId: 'cooled-alkene-bromination-v1', status: 'supported-model', canGenerate3D: true,
      note: 'Existing reviewed Br2 condition model.', sourceUrls: [],
    },
    evidence: { canGenerate3D: true, missingRequiredSettings: [], label: 'Bounded theoretical model' },
  };
}

test('phase1: frontend presentation manifest exactly matches the backend registry', () => {
  const backend = python('import json; from server.reaction_temperature_profiles import reviewed_manifest; print(json.dumps(reviewed_manifest()))');
  assert.equal(backend.version, 1);
  const local = Object.entries(REVIEWED_COOLING_MODELS).map(([modelId, item]) => ({ modelId, ...item }));
  assert.deepEqual(local, backend.profiles, 'An independent frontend registry edit must fail parity checks');
  assert.equal(local.length, 7); // Four preserved profiles plus three explicit-only R3 references.
  assert.ok(Object.isFrozen(REVIEWED_COOLING_MODELS));
  assert.ok(Object.values(REVIEWED_COOLING_MODELS).every(Object.isFrozen));
});

test('phase1: actual backend assessments produce the same two theoretical prompts', () => {
  const assessments = python(`import json
from server import chemistry_server as s
cases = [('Bromination', 'bromine'), ('Epoxidation', {'smiles': 'O=C(OO)c1cccc(Cl)c1'})]
conditions = {'temperature': 'cooled', 'solvent': 'dry', 'catalyst': 'none'}
print(json.dumps([next(r['assessment'] for r in s.match_reactions({'smiles':'C=C'}, reagent, conditions)['reactionOptions'] if r['mechanism']==path) for path,reagent in cases]))`);
  for (const assessment of assessments) {
    assert.match(conditionNextStep(assessment), /^Supported cooled/);
    assert.match(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
    assert.match(conditionGuidance(assessment), /not a temperature simulation/);
    assert.deepEqual(assessment.cooling.reasonCodes, []);
  }
});

test('phase1: original v1 payloads without additive registry fields keep working', () => {
  const assessment = qualified();
  delete assessment.cooling.registryVersion;
  delete assessment.cooling.profileVersion;
  delete assessment.cooling.reasonCodes;
  assert.match(conditionNextStep(assessment), /^Supported cooled alkene bromination model/);
});

for (const field of ['version', 'registryVersion', 'profileVersion']) {
  for (const value of [null, true, false, '1', 0, 2, [], {}]) {
    test(`phase1: ${field}=${JSON.stringify(value)} cannot authorize positive cooled wording`, () => {
      const assessment = qualified();
      assessment.cooling[field] = value;
      const before = structuredClone(assessment);
      assert.doesNotMatch(conditionNextStep(assessment), /^Supported cooled|View the theoretical 3D/);
      assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
      assert.deepEqual(assessment, before);
    });
  }
}

for (const modelId of ['unknown-v2', '__proto__', 'constructor', 'toString', null]) {
  test(`phase1: unknown or inherited model ${modelId} fails closed`, () => {
    const assessment = qualified();
    assessment.cooling.modelId = modelId;
    assert.doesNotMatch(conditionNextStep(assessment), /^Supported cooled/);
    assert.match(conditionNextStep(assessment), /3D stays unavailable/);
  });
}

for (const [label, change] of [
  ['parent conditions unresolved', a => { a.conditionIssues = [{ field: 'solvent', explanation: 'Not reviewed.' }]; }],
  ['parent settings missing', a => { a.missingSettings = ['solvent']; }],
  ['profile conditions unresolved', a => { a.cooling.conditionIssues = [{ field: 'catalyst', explanation: 'Not reviewed.' }]; }],
  ['profile reason code unresolved', a => { a.cooling.reasonCodes = ['underlying-assessment-blocked']; }],
]) {
  test(`phase1: contradictory ${label} cannot override a supported-model flag`, () => {
    const assessment = qualified();
    change(assessment);
    assert.doesNotMatch(conditionNextStep(assessment), /^Supported cooled/);
    assert.doesNotMatch(conditionGuidance(assessment), /Cooled 3D is a theoretical product conformer/);
  });
}

test('phase1: actual unsupported cooled backend context retains its precise reason', () => {
  const assessment = python(`import json
from server import chemistry_server as s
c = {'temperature':'cooled','solvent':'aqueous-protic','catalyst':'none'}
print(json.dumps(s.match_reactions({'smiles':'C=C'}, 'bromine', c)['reactionOptions'][0]['assessment']))`);
  assert.ok(assessment.cooling.reasonCodes.includes('medium-unresolved'));
  const prompt = conditionNextStep(assessment);
  assert.ok(prompt.includes('Review cooled conditions:'));
  assert.match(prompt, /Conditional 2D remains available; 3D stays unavailable/);
  assert.doesNotMatch(prompt, /reaction is impossible|Supported cooled/);
});
