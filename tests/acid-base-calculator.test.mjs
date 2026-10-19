import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/acid-base-calculator.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } });
const { calculateAcidBase, constantLog10 } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
const K = (value) => ({ value, notation: 'K' });
const pK = (value) => ({ value, notation: 'pK' });
const base = (model = 'strong-acid') => ({ model, temperatureC: 25, kw: K(1e-14), activities: { mode: 'ideal' }, concentration: 0.1 });
const weak = (model = 'weak-acid') => ({ ...base(model), constants: [K(1.8e-5)] });
const buffer = (kind = 'acid') => ({ ...base('buffer'), bufferKind: kind, acidConcentration: 0.1, baseConcentration: 0.1, constants: [K(1.8e-5)] });
const poly = () => ({ ...base('polyprotic'), concentration: 0.033, steps: 2, counterionConcentration: 0, constants: [K(4.3e-7), K(4.7e-11)] });
const species = (result, name) => result.species.find((item) => item.name === name);
function close(actual, expected, tolerance = 1e-9) {
  assert.ok(Number.isFinite(actual), `Nonfinite result ${actual}`);
  assert.ok(Math.abs(actual - expected) <= Math.max(Math.abs(expected) * tolerance, 1e-300), `Expected ${expected}, received ${actual}`);
}
function balanced(result, total) {
  assert.ok(result.chargeResidual < 1e-10);
  assert.ok(result.materialResidual < 1e-10);
  assert.ok(result.equilibriumResidual < 1e-8);
  const charge = result.species.reduce((sum, item) => sum + item.charge * item.concentration, 0);
  const chargeScale = result.species.reduce((sum, item) => sum + Math.abs(item.charge) * item.concentration, 0);
  assert.ok(Math.abs(charge) <= 1e-10 * chargeScale);
  if (total !== undefined) close(result.species.filter((item) => !['H+', 'OH−'].includes(item.name) && !item.name.includes('spectator'))
    .reduce((sum, item) => sum + item.concentration, 0), total);
  close(result.species[0].activity * result.species[1].activity, 1e-14);
}

test('strong monoprotic acids include water equilibrium and their spectator anion', () => {
  const result = calculateAcidBase(base());
  close(result.pH, 1);
  close(result.hydrogen, (0.1 + Math.sqrt(0.01 + 4e-14)) / 2);
  close(species(result, 'X− (spectator)').concentration, 0.1);
  balanced(result);
});

test('strong monoprotic bases include water and their spectator cation', () => {
  const result = calculateAcidBase(base('strong-base'));
  close(result.pH, 13);
  close(result.pOH, 1);
  balanced(result);
});

test('zero analytical concentration is pure water, without invented concentration floors', () => {
  for (const model of ['strong-acid', 'strong-base']) {
    const result = calculateAcidBase({ ...base(model), concentration: 0 });
    assert.equal(result.pH, 7);
    assert.equal(result.hydrogen, 1e-7);
    assert.equal(result.hydroxide, 1e-7);
    assert.equal(result.species[2].concentration, 0);
    balanced(result);
  }
});

test('extremely dilute strong acid/base does not incorrectly ignore water', () => {
  const concentration = 1e-9;
  const expected = (concentration + Math.sqrt(concentration ** 2 + 4e-14)) / 2;
  const acid = calculateAcidBase({ ...base(), concentration });
  const alkali = calculateAcidBase({ ...base('strong-base'), concentration });
  close(acid.hydrogen, expected);
  close(alkali.hydroxide, expected);
  assert.ok(acid.pH < 7 && acid.pH > 6.99);
  assert.ok(alkali.pH > 7 && alkali.pH < 7.01);
  balanced(acid);
  balanced(alkali);
});

test('weak acid solves full dissociation rather than assuming x is small', () => {
  const result = calculateAcidBase(weak());
  const exactWithoutWater = (-1.8e-5 + Math.sqrt((1.8e-5) ** 2 + 4 * 1.8e-5 * 0.1)) / 2;
  close(result.hydrogen, exactWithoutWater, 1e-7);
  close(result.hydrogen * species(result, 'A−').concentration / species(result, 'HA').concentration, 1.8e-5);
  balanced(result, 0.1);
});

test('weak neutral base includes BH+ and converts Ka from the entered Kb and Kw', () => {
  const result = calculateAcidBase(weak('weak-base'));
  const acid = calculateAcidBase(weak());
  close(result.hydroxide, acid.hydrogen);
  close(result.pH + acid.pH, 14);
  close(species(result, 'BH+').concentration * result.hydroxide / species(result, 'B').concentration, 1.8e-5);
  balanced(result, 0.1);
});

test('OpenStax 14.6 acetate buffer agrees with pH 4.74 while checking full charge balance', () => {
  // Primary reference Example 14.20: https://openstax.org/books/chemistry-2e/pages/14-6-buffers
  const result = calculateAcidBase(buffer());
  assert.ok(Math.abs(result.pH - 4.74) < 0.01);
  const ha = species(result, 'HA').concentration;
  const a = species(result, 'A−').concentration;
  close(result.hydrogen * a / ha, 1.8e-5);
  close(species(result, 'M+ (spectator)').concentration, 0.1);
  assert.ok(a > 0.1 && ha < 0.1); // Not simply a ratio of the initial components.
  balanced(result, 0.2);
});

test('base conjugate-pair buffer includes a spectator anion and Kb mass action', () => {
  const result = calculateAcidBase(buffer('base'));
  const acid = calculateAcidBase(buffer());
  close(result.pH + acid.pH, 14);
  close(result.hydroxide * species(result, 'BH+').concentration / species(result, 'B').concentration, 1.8e-5);
  close(species(result, 'X− (spectator)').concentration, 0.1);
  balanced(result, 0.2);
});

test('buffer permits a zero component and solves the weak-acid limiting case', () => {
  const result = calculateAcidBase({ ...buffer(), baseConcentration: 0 });
  close(result.pH, calculateAcidBase(weak()).pH);
  assert.equal(species(result, 'M+ (spectator)').concentration, 0);
  balanced(result, 0.1);
});

test('zero weak/polyprotic family concentrations are exactly zero while water stays finite', () => {
  for (const input of [{ ...weak(), concentration: 0 }, { ...poly(), concentration: 0 }]) {
    const result = calculateAcidBase(input);
    assert.equal(result.pH, 7);
    assert.ok(result.species.filter((item) => !['H+', 'OH−'].includes(item.name)).every((item) => item.concentration === 0));
    balanced(result, 0);
  }
});

test('OpenStax carbonic acid example checks both dissociations simultaneously', () => {
  // Primary reference Example 14.19: https://openstax.org/books/chemistry-2e/pages/14-5-polyprotic-acids
  const result = calculateAcidBase(poly());
  close(result.hydrogen, 1.2e-4, 0.01);
  close(species(result, 'HA−').concentration, 1.2e-4, 0.01);
  close(species(result, 'A²−').concentration, 4.7e-11, 2e-6);
  const family = ['H₂A', 'HA−', 'A²−'].map((name) => species(result, name).concentration);
  close(result.hydrogen * family[1] / family[0], 4.3e-7);
  close(result.hydrogen * family[2] / family[1], 4.7e-11);
  balanced(result, 0.033);
});

test('triprotic phosphate values satisfy three independent mass-action equations and total mass', () => {
  // Primary constants: https://openstax.org/books/chemistry-2e/pages/14-5-polyprotic-acids
  const constants = [7.5e-3, 6.2e-8, 4.2e-13];
  const result = calculateAcidBase({ ...poly(), steps: 3, concentration: 0.1, constants: constants.map(K) });
  const concentrations = ['H₃A', 'H₂A−', 'HA²−', 'A³−'].map((name) => species(result, name).concentration);
  for (let i = 0; i < 3; i++) close(result.hydrogen * concentrations[i + 1] / concentrations[i], constants[i]);
  assert.ok(result.pH > 1.5 && result.pH < 2);
  balanced(result, 0.1);
});

test('polyprotic salt equivalents describe an amphiprotic solution without unrelated mixtures', () => {
  const result = calculateAcidBase({ ...poly(), concentration: 0.1, counterionConcentration: 0.1 });
  const approximation = -(Math.log10(4.3e-7) + Math.log10(4.7e-11)) / 2;
  assert.ok(Math.abs(result.pH - approximation) < 0.02);
  balanced(result, 0.1);
});

test('one-step polyprotic model reduces exactly to the weak-acid model', () => {
  const result = calculateAcidBase({ ...poly(), steps: 1, concentration: 0.1, constants: [K(1.8e-5)] });
  close(result.pH, calculateAcidBase(weak()).pH);
  balanced(result, 0.1);
});

test('pK constants are equivalent to K notation, and zero or negative pK is valid', () => {
  const result = calculateAcidBase({ ...weak(), kw: pK(14), constants: [pK(-Math.log10(1.8e-5))] });
  close(result.pH, calculateAcidBase(weak()).pH);
  assert.equal(constantLog10(pK(0)), -0);
  assert.equal(constantLog10(pK(-2)), 2);
});

test('variable temperature uses only the matching user-entered Kw, not an assumed pKw of 14', () => {
  const result = calculateAcidBase({ ...base(), concentration: 0, temperatureC: 50, kw: K(5.5e-14) });
  close(result.pH, -Math.log10(5.5e-14) / 2);
  close(result.pH + result.pOH, -Math.log10(5.5e-14));
  assert.equal(result.temperatureC, 50);
});

test('entered activities change pH and maintain water balance with fixed coefficients', () => {
  const result = calculateAcidBase({ ...base(), activities: { mode: 'entered', hydrogen: 0.5, hydroxide: 0.8, family: [], counterions: [0.6] } });
  close(result.pH, -Math.log10(0.05), 1e-9);
  assert.ok(Math.abs(result.pH + result.pOH - 14) < 1e-10);
  close(species(result, 'X− (spectator)').activity, 0.06);
  balanced(result);
});

test('nonideal buffer uses γ for H+, OH−, neutral acid, conjugate base and spectator separately', () => {
  const activities = { mode: 'entered', hydrogen: 0.7, hydroxide: 0.6, family: [1.1, 0.5], counterions: [0.4] };
  const result = calculateAcidBase({ ...buffer(), activities });
  const ha = species(result, 'HA');
  const a = species(result, 'A−');
  close(result.species[0].activity * a.activity / ha.activity, 1.8e-5);
  close(result.pH, -Math.log10(1.8e-5 * ha.activity / a.activity));
  assert.ok(Math.abs(result.pH - calculateAcidBase(buffer()).pH) > 0.3);
  balanced(result, 0.2);
});

test('every polyprotic species coefficient is included in the corrected distributions', () => {
  const input = { ...poly(), activities: { mode: 'entered', hydrogen: 0.7, hydroxide: 0.8, family: [1, 0.6, 0.3], counterions: [0.9] } };
  const result = calculateAcidBase(input);
  const family = ['H₂A', 'HA−', 'A²−'].map((name) => species(result, name));
  close(result.species[0].activity * family[1].activity / family[0].activity, 4.3e-7);
  close(result.species[0].activity * family[2].activity / family[1].activity, 4.7e-11);
  balanced(result, 0.033);
});

test('missing Kw/constants/activity corrections fail closed without reusing defaults', () => {
  for (const kw of [undefined, null, {}, K(0), K(-1), K(NaN), K(Infinity), { value: 1e-14, notation: 'unknown' }]) {
    assert.throws(() => calculateAcidBase({ ...weak(), kw }));
  }
  for (const constants of [undefined, [], [K(1e-5), K(1e-6)], [K(0)]]) assert.throws(() => calculateAcidBase({ ...weak(), constants }));
  for (const activities of [undefined, {}, { mode: 'unknown' }, { mode: 'entered' },
    { mode: 'entered', hydrogen: 1, hydroxide: 1, family: [1], counterions: [1] },
    { mode: 'entered', hydrogen: 1, hydroxide: 1, family: [1, 1], counterions: [] }]) {
    assert.throws(() => calculateAcidBase({ ...buffer(), activities }));
  }
});

test('invalid coefficients, negative concentrations and unsupported models never produce a plausible answer', () => {
  for (const invalid of [undefined, null, '', -1, Infinity, NaN, '1', true]) assert.throws(() => calculateAcidBase({ ...base(), concentration: invalid }));
  for (const invalid of [0, -1, Infinity, NaN, undefined, '1', 1e101, 1e-101]) {
    assert.throws(() => calculateAcidBase({ ...base(), activities: { mode: 'entered', hydrogen: invalid, hydroxide: 1, family: [], counterions: [1] } }));
  }
  for (const model of ['', 'mixture', undefined, '__proto__']) assert.throws(() => calculateAcidBase({ ...base(), model }));
  for (const temperatureC of [-273.15, -300, Infinity, NaN, undefined, '25']) assert.throws(() => calculateAcidBase({ ...base(), temperatureC }));
});

test('polyprotic families reject missing steps, excess salts and unsupported extra dissociations', () => {
  for (const steps of [undefined, 0, 4, -1, 2.5, '2']) assert.throws(() => calculateAcidBase({ ...poly(), steps }));
  assert.throws(() => calculateAcidBase({ ...poly(), constants: [K(1e-5)] }), /all 2/);
  assert.throws(() => calculateAcidBase({ ...poly(), counterionConcentration: 0.1 }), /fully neutralized/);
  assert.throws(() => calculateAcidBase({ ...buffer(), bufferKind: 'unrestricted' }), /conjugate pair/);
});

test('numeric underflow or out-of-range conditions report failure rather than substituting concentrations', () => {
  assert.throws(() => calculateAcidBase({ ...weak(), concentration: 1e-300, constants: [K(1e-300)] }), /numeric range/);
  assert.throws(() => calculateAcidBase({ ...base(), kw: K(1e-301) }), /between/);
  assert.throws(() => constantLog10(pK(301)), /between/);
  assert.throws(() => calculateAcidBase({ ...base(), concentration: 1e7 }), /between/);
});
