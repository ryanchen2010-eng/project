import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const transpile = source => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = output => `data:text/javascript;base64,${Buffer.from(output).toString('base64')}`;
const eqUrl = url(transpile(await readFile(new URL('../src/equilibrium-calculator.ts', import.meta.url), 'utf8')));
const output = transpile(await readFile(new URL('../src/solubility-calculator.ts', import.meta.url), 'utf8')).replace(/from ['"]\.\/equilibrium-calculator['"]/, `from '${eqUrl}'`);
const { calculateSolubility, compareSaturation, validateSolubilityModel } = await import(url(output));
const ion = (name, charge, concentration = 0, overrides = {}) => ({ name, charge, concentration, coefficient: 1, ...overrides });
const model = (ions = [ion('M⁺', 1), ion('X⁻', -1)], overrides = {}) => ({ ions, constant: { notation: 'K', value: 1e-10 }, activityMode: 'ideal', temperatureC: 25, ...overrides });
const close = (actual, expected, tolerance = 2e-9) => assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) <= Math.max(Math.abs(expected), 1e-300) * tolerance, `Expected ${expected}, received ${actual}`);

test('OpenStax CuBr pure-water molar solubility agrees with sqrt(Ksp)', () => {
  // https://openstax.org/books/chemistry-2e/pages/15-1-precipitation-and-dissolution Example 15.3
  const answer = calculateSolubility(model([ion('Cu⁺', 1), ion('Br⁻', -1)], { constant: { notation: 'K', value: 6.3e-9 } }));
  close(answer.solubility, Math.sqrt(6.3e-9)); close(answer.concentrations[0], answer.concentrations[1]);
  assert.ok(Math.abs(answer.logResidual) <= 1e-10);
});

test('OpenStax calcium fluoride nonunit stoichiometry gives 4s³', () => {
  // Example 15.2: [Ca²⁺]=2.15e-4, [F⁻]=4.30e-4, Ksp=3.97535e-11 before rounding.
  const Ksp = 2.15e-4 * (4.3e-4) ** 2;
  const answer = calculateSolubility(model([ion('Ca²⁺', 2), ion('F⁻', -1, 0, { coefficient: 2 })], { constant: { notation: 'K', value: Ksp } }));
  close(answer.solubility, 2.15e-4); close(answer.concentrations[1], 4.3e-4);
});

test('OpenStax common-ion CdS case solves without a small-x substitution', () => {
  // Example 15.13: CdS Ksp=1e-28, initially .010 M Cd²⁺ from CdBr2; two Br⁻ per Cd²⁺.
  const answer = calculateSolubility(model([ion('Cd²⁺', 2, .01), ion('S²⁻', -2)], {
    constant: { notation: 'K', value: 1e-28 }, spectators: [{ name: 'Br⁻', charge: -1, concentration: .02 }],
  }));
  close(answer.solubility, 1e-26); close(answer.concentrations[0], .01);
});

test('common ions reduce solubility and the full quadratic is conserved', () => {
  const initial = model([ion('Ag⁺', 1), ion('Cl⁻', -1, .01)], {
    spectators: [{ name: 'Na⁺', charge: 1, concentration: .01 }],
  });
  const answer = calculateSolubility(initial);
  const exact = 2e-10 / (.01 + Math.sqrt(.01 ** 2 + 4e-10));
  close(answer.solubility, exact); close(answer.concentrations[1], .01 + exact);
  assert.ok(answer.solubility < calculateSolubility(model()).solubility);
  assert.equal(initial.ions[0].concentration, 0);
});

test('entered gamma values alter pure-water and common-ion saturation', () => {
  const input = model([ion('M⁺', 1, 0, { activityCoefficient: .5 }), ion('X⁻', -1, 0, { activityCoefficient: .8 })], { activityMode: 'entered' });
  close(calculateSolubility(input).solubility, Math.sqrt(1e-10 / .4));
  input.ions[0].concentration = 1e-5; input.ions[1].concentration = 1e-5;
  const q = compareSaturation(input); close(q.quotient, 4e-11); assert.equal(q.status, 'undersaturated');
});

test('Qsp statuses distinguish undersaturation, saturation and supersaturation', () => {
  assert.equal(compareSaturation(model()).quotient, 0);
  assert.equal(compareSaturation(model()).status, 'undersaturated');
  assert.equal(compareSaturation(model([ion('Ag⁺', 1, 1e-5), ion('Cl⁻', -1, 1e-5)])).status, 'saturated');
  // OpenStax Example 15.8: equal diluted Ag⁺ and Cl⁻ of 1e-4 M, Ksp1.6e-10.
  const input = model([ion('Ag⁺', 1, 1e-4), ion('Cl⁻', -1, 1e-4)], { constant: { notation: 'K', value: 1.6e-10 } });
  const answer = compareSaturation(input); close(answer.quotient, 1e-8); assert.equal(answer.status, 'supersaturated');
  assert.throws(() => calculateSolubility(input), /already supersaturated/);
});

test('already saturated initial ions require exactly zero additional dissolution', () => {
  const answer = calculateSolubility(model([ion('M⁺', 1, 1e-5), ion('X⁻', -1, 1e-5)]));
  assert.equal(answer.solubility, 0); assert.equal(answer.iterations, 0);
});

test('pKsp notation gives the same result as Ksp', () => {
  const answer = calculateSolubility(model(undefined, { constant: { notation: 'pK', value: 10 } }));
  close(answer.solubility, 1e-5);
});

test('salt coefficients must be charge-neutral and every ion concentration nonnegative', () => {
  for (const rows of [[ion('A', 2), ion('B', -1)], [ion('A', 1), ion('B', 1)], [ion('A', 0), ion('B', 0)], [ion('A', 1, -1), ion('B', -1)], [ion('A', 1, 0, { coefficient: .5 }), ion('B', -1)]]) assert.throws(() => validateSolubilityModel(model(rows)));
  assert.throws(() => validateSolubilityModel(model([ion('M', 1, .01), ion('X', -1)])), /spectator counterion/);
});

test('entered mode needs positive coefficients for both ions and every included spectator', () => {
  const input = model([ion('M', 1, .01, { activityCoefficient: .8 }), ion('X', -1, 0, { activityCoefficient: .8 })], {
    activityMode: 'entered', spectators: [{ name: 'Y', charge: -1, concentration: .01 }],
  });
  assert.throws(() => calculateSolubility(input), /activity coefficient for Y/);
  input.spectators[0].activityCoefficient = .7; assert.ok(calculateSolubility(input).solubility > 0);
  for (const gamma of [undefined, 0, -1, Infinity, NaN]) {
    input.ions[0].activityCoefficient = gamma; assert.throws(() => calculateSolubility(input), /activity coefficient/);
  }
});

test('zero concentrations remain exact and extreme unrepresentable results fail closed', () => {
  const input = model(); assert.equal(compareSaturation(input).quotient, 0);
  close(calculateSolubility(model(undefined, { constant: { notation: 'K', value: 1e-300 } })).solubility, 1e-150);
  assert.throws(() => compareSaturation(model([ion('M', 1, 1e300), ion('X', -1, 1e300)])), /represented/);
  assert.throws(() => calculateSolubility(model(undefined, { constant: { notation: 'pK', value: 1000 } })), /numeric range/);
});

test('invalid temperatures and duplicate spectator identities fail before solving', () => {
  assert.throws(() => calculateSolubility(model(undefined, { temperatureC: -273.15 })), /absolute zero/);
  assert.throws(() => calculateSolubility(model(undefined, { spectators: [{ name: 'M⁺', charge: 1, concentration: 0 }] })), /distinct/);
});

test('a subnormal unbalanced common-ion concentration cannot pass electroneutrality', () => {
  const input = model([ion('Ag⁺', 1), ion('Cl⁻', -1, 1e-320)]);
  assert.throws(() => validateSolubilityModel(input), /spectator counterion/);
  input.spectators = [{ name: 'Na⁺', charge: 1, concentration: 1e-320 }];
  assert.equal(compareSaturation(input).quotient, 0);
});

test('overflowed final charge scale is rejected rather than treated as infinite tolerance', () => {
  const input = model([ion('M⁺', 1, 0, { activityCoefficient: 1.1e-308 }),
    ion('X⁻', -1, 0, { activityCoefficient: 1.1e-308 })], {
    activityMode: 'entered', constant: { notation: 'K', value: 1 },
  });
  assert.throws(() => calculateSolubility(input), /final charge-balance/);
});
