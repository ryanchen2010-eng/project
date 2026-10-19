import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/equilibrium-calculator.ts', import.meta.url), 'utf8');
const output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { calculateQuotient, compareQuotient, solveEquilibrium, constantLog, validateEquilibriumModel } = await import(`data:text/javascript;base64,${Buffer.from(output).toString('base64')}`);
const species = (name, side, concentration, overrides = {}) => ({ name, side, concentration, coefficient: 1, phase: 'aq', charge: 0, ...overrides });
const model = (rows, overrides = {}) => ({ species: rows, activityMode: 'ideal', balancedConfirmed: true, temperatureC: 25, ...overrides });
const K = value => ({ notation: 'K', value });
const close = (actual, expected, tolerance = 2e-9) => assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= Math.max(Math.abs(expected), 1e-300) * tolerance, `Expected ${expected}, received ${actual}`);

test('OpenStax 13.2 arithmetic: .042/.016² gives 164.0625 without implementing a gas model', () => {
  // OpenStax Example 13.2 is gaseous NO2/N2O4. Only its coefficient/concentration arithmetic is used here.
  // https://openstax.org/books/chemistry-2e/pages/13-2-equilibrium-constants
  const q = calculateQuotient(model([species('A', 'reactant', .016, { coefficient: 2 }), species('B', 'product', .042)]));
  assert.equal(q.kind, 'finite'); close(q.value, 164.0625, 1e-14);
  assert.equal(compareQuotient(q, K(164.0625)), 'equilibrium');
});

test('zero products produce an exact zero quotient and forward tendency', () => {
  const q = calculateQuotient(model([species('A', 'reactant', .1), species('B', 'product', 0)]));
  assert.equal(q.kind, 'zero'); assert.equal(q.value, 0);
  assert.equal(compareQuotient(q, K(1)), 'forward');
});

test('zero denominator is explicitly infinite, while 0/0 is undefined', () => {
  const q = calculateQuotient(model([species('A', 'reactant', 0), species('B', 'product', .1)]));
  assert.equal(q.kind, 'infinite'); assert.match(q.reason, /zero denominator/);
  assert.equal(compareQuotient(q, K(1)), 'reverse');
  const undefinedQ = calculateQuotient(model([species('A', 'reactant', 0), species('B', 'product', 0)]));
  assert.equal(undefinedQ.kind, 'undefined'); assert.match(undefinedQ.reason, /0\/0/);
  assert.throws(() => compareQuotient(undefinedQ, K(1)), /undefined/);
});

test('pure solids/liquids are excluded from Q and do not need coefficients', () => {
  const input = model([species('Solid', 'reactant', NaN, { phase: 'solid' }), species('Solvent', 'reactant', NaN, { phase: 'liquid' }), species('B', 'product', .2)]);
  close(calculateQuotient(input).value, .2);
});

test('constant notation supports negative pK and rejects invalid or unrepresentable constants', () => {
  close(constantLog({ notation: 'pK', value: 3 }), Math.log(.001));
  close(constantLog({ notation: 'pK', value: -2 }), Math.log(100));
  for (const constant of [K(0), K(-1), K(NaN), K(Infinity), { notation: 'pK', value: 1000 }, { notation: 'x', value: 1 }]) assert.throws(() => constantLog(constant));
});

test('single reaction ICE solving conserves a nonunit-coefficient material balance', () => {
  const initial = model([species('A', 'reactant', .1, { coefficient: 2 }), species('B', 'product', 0)]);
  const answer = solveEquilibrium(initial, K(164.0625));
  close(answer.extent, .042); close(answer.concentrations[0].concentration, .016);
  close(answer.concentrations[1].concentration, .042); close(answer.quotient.value, 164.0625);
  close(answer.concentrations[0].concentration + 2 * answer.concentrations[1].concentration, .1);
  assert.ok(Math.abs(answer.residual) <= 1e-10);
  assert.equal(initial.species[1].concentration, 0);
});

test('product-only initial state solves a reverse extent without inventing initial reactants', () => {
  const answer = solveEquilibrium(model([species('A', 'reactant', 0), species('B', 'product', 1)]), K(1));
  close(answer.extent, -.5); close(answer.concentrations[0].concentration, .5); close(answer.concentrations[1].concentration, .5);
});

test('zero amount everywhere fails clearly instead of creating artificial concentrations', () => {
  assert.throws(() => solveEquilibrium(model([species('A', 'reactant', 0), species('B', 'product', 0)]), K(1)), /No nonzero reaction extent/);
});

test('pure-phase models can form finite brackets on either unbounded extent side', () => {
  const dissolve = solveEquilibrium(model([species('S', 'reactant', 0, { phase: 'solid' }), species('A', 'product', 0)]), K(.2));
  close(dissolve.extent, .2); close(dissolve.concentrations[1].concentration, .2);
  assert.equal(Object.hasOwn(dissolve.concentrations[0], 'concentration'), false);
  const reverse = solveEquilibrium(model([species('A', 'reactant', .1), species('L', 'product', 0, { phase: 'liquid' })]), K(1));
  close(reverse.extent, -.9); close(reverse.concentrations[0].concentration, 1);
});

test('activity coefficients change Q and the equilibrium solution using all aqueous rows', () => {
  const entered = model([species('A', 'reactant', 1, { activityCoefficient: 1.5 }), species('B', 'product', 0, { activityCoefficient: .5 })], { activityMode: 'entered' });
  const answer = solveEquilibrium(entered, K(1));
  close(answer.extent, .75); close(answer.concentrations[0].concentration, .25);
  const current = model([species('A', 'reactant', .25, { activityCoefficient: 1.5 }), species('B', 'product', .75, { activityCoefficient: .5 })], { activityMode: 'entered' });
  close(calculateQuotient(current).value, 1);
});

test('entered mode never defaults a missing, zero, negative or infinite gamma', () => {
  for (const gamma of [undefined, 0, -1, NaN, Infinity]) assert.throws(() => calculateQuotient(model([
    species('A', 'reactant', 1, { activityCoefficient: gamma }), species('B', 'product', 1, { activityCoefficient: 1 }),
  ], { activityMode: 'entered' })), /activity coefficient/);
});

test('charge conservation and electroneutrality include explicit fixed spectator rows', () => {
  const input = model([species('A⁺', 'reactant', .1, { charge: 1 }), species('B⁺', 'product', 0, { charge: 1 })], {
    spectators: [{ name: 'X⁻', charge: -1, concentration: .1 }],
  });
  const answer = solveEquilibrium(input, K(1)); close(answer.extent, .05);
  assert.throws(() => calculateQuotient({ ...input, spectators: [] }), /electroneutral/);
  assert.throws(() => calculateQuotient(model([species('A', 'reactant', .1), species('B⁺', 'product', 0, { charge: 1 })])), /conserve charge/);
});

test('every fixed spectator requires gamma in entered mode, although excluded from Q', () => {
  const input = model([species('A⁺', 'reactant', .1, { charge: 1, activityCoefficient: 1 }), species('B⁺', 'product', .1, { charge: 1, activityCoefficient: 1 })], {
    activityMode: 'entered', spectators: [{ name: 'X⁻', charge: -1, concentration: .2 }],
  });
  assert.throws(() => calculateQuotient(input), /activity coefficient for X/);
  input.spectators[0].activityCoefficient = .75; close(calculateQuotient(input).value, 1);
});

test('rejects unsupported phases, unbalanced confirmation, invalid charges/coefficients and duplicates', () => {
  const input = model([species('A', 'reactant', 1), species('B', 'product', 1)]);
  for (const modification of [
    { balancedConfirmed: false }, { temperatureC: -273.15 }, { activityMode: 'automatic' },
    { species: [species('A', 'reactant', 1, { phase: 'gas' }), species('B', 'product', 1)] },
    { species: [species('A', 'reactant', -1), species('B', 'product', 1)] },
    { species: [species('A', 'reactant', 1, { coefficient: 1.5 }), species('B', 'product', 1)] },
    { species: [species('A', 'reactant', 1, { charge: .5 }), species('B', 'product', 1)] },
    { species: [species('A', 'reactant', 1), species('a', 'product', 1)] },
    { spectators: [{ name: 'A', concentration: 1, charge: 0 }] },
  ]) assert.throws(() => validateEquilibriumModel({ ...input, ...modification }));
});

test('log arithmetic fails explicitly on unrepresentable quotients and nonconvergent roots', () => {
  assert.throws(() => calculateQuotient(model([species('A', 'reactant', 1e-300), species('B', 'product', 1e300)])), /represented/);
  assert.throws(() => solveEquilibrium(model([species('A', 'reactant', 1), species('B', 'product', 0)]), K(1e300)), /converge/);
  const tiny = solveEquilibrium(model([species('A', 'reactant', 1), species('B', 'product', 0)]), K(1e-300));
  close(tiny.concentrations[1].concentration, 1e-300);
});

test('all positive phase endpoint concentrations are handled exactly for coefficient three', () => {
  const answer = solveEquilibrium(model([species('A', 'reactant', .1, { coefficient: 3 }), species('B', 'product', 0)]), K(1));
  assert.ok(answer.concentrations.every(row => row.concentration >= 0));
  close(answer.quotient.value, 1);
});

test('subnormal concentrations cannot bypass relative electroneutrality checks', () => {
  const input = model([species('Ag⁺', 'reactant', 0, { charge: 1 }), species('B⁺', 'product', 1e-320, { charge: 1 })]);
  assert.throws(() => calculateQuotient(input), /electroneutral/);
  input.spectators = [{ name: 'Cl⁻', charge: -1, concentration: 1e-320 }];
  assert.equal(calculateQuotient(input).kind, 'infinite');
});

test('overflowed final charge scale fails closed even when net charge cancels to zero', () => {
  const input = model([species('Solid', 'reactant', 0, { phase: 'solid' }),
    species('A⁺', 'product', 0, { charge: 1, activityCoefficient: 1.1e-308 }),
    species('B⁻', 'product', 0, { charge: -1, activityCoefficient: 1.1e-308 })], { activityMode: 'entered' });
  assert.throws(() => solveEquilibrium(input, K(1)), /final charge-balance/);
});
