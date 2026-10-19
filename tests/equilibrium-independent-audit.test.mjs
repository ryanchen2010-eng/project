import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const transpile = (source) => ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const url = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const eqUrl = url(transpile(await readFile(new URL('../src/equilibrium-calculator.ts', import.meta.url), 'utf8')));
const { calculateQuotient, compareQuotient, solveEquilibrium } = await import(eqUrl);
const solSource = transpile(await readFile(new URL('../src/solubility-calculator.ts', import.meta.url), 'utf8')).replace(/from ['"]\.\/equilibrium-calculator['"]/, `from '${eqUrl}'`);
const { calculateSolubility, compareSaturation } = await import(url(solSource));
const K = (value) => ({ notation: 'K', value });
const row = (name, side, concentration, options = {}) => ({ name, side, coefficient: 1, phase: 'aq', concentration, charge: 0, ...options });
const model = (species, options = {}) => ({ species, temperatureC: 25, activityMode: 'ideal', balancedConfirmed: true, ...options });
function close(actual, expected, tolerance = 1e-9) {
  assert.ok(Number.isFinite(actual));
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(Math.abs(expected), 1e-300), `Expected ${expected}, received ${actual}`);
}

test('independent audit: true zero, zero denominator and 0/0 are distinct quotient states', () => {
  const zero = calculateQuotient(model([row('A', 'reactant', 1), row('B', 'product', 0)]));
  assert.equal(zero.kind, 'zero');
  assert.equal(zero.value, 0);
  assert.equal(compareQuotient(zero, K(1)), 'forward');
  const infinite = calculateQuotient(model([row('A', 'reactant', 0), row('B', 'product', 1)]));
  assert.equal(infinite.kind, 'infinite');
  assert.equal(compareQuotient(infinite, K(1)), 'reverse');
  const undefinedQ = calculateQuotient(model([row('A', 'reactant', 0), row('B', 'product', 0)]));
  assert.equal(undefinedQ.kind, 'undefined');
  assert.throws(() => compareQuotient(undefinedQ, K(1)), /undefined/);
  assert.throws(() => solveEquilibrium(model([row('A', 'reactant', 0), row('B', 'product', 0)]), K(1)), /extent/);
});

test('independent audit: single-reactant zero initial product gives exact positive extent', () => {
  const result = solveEquilibrium(model([row('A', 'reactant', 1), row('B', 'product', 0)]), K(3));
  close(result.extent, 0.75);
  close(result.concentrations[0].concentration, 0.25);
  close(result.concentrations[1].concentration, 0.75);
  assert.ok(Math.abs(result.residual) <= 1e-10);
});

test('independent audit: nonunit coefficient obeys the 2A to B material balance', () => {
  const result = solveEquilibrium(model([row('A', 'reactant', 1, { coefficient: 2 }), row('B', 'product', 0)]), K(1));
  const expected = (5 - Math.sqrt(9)) / 8; // x = (1 − 2x)².
  close(result.extent, expected);
  close(result.concentrations[0].concentration + 2 * result.concentrations[1].concentration, 1);
});

test('independent audit: pure phases allow finite roots at either one-sided unbounded extent', () => {
  const dissolve = solveEquilibrium(model([row('A solid', 'reactant', NaN, { phase: 'solid' }), row('A dissolved', 'product', 0)]), K(2));
  close(dissolve.extent, 2);
  close(dissolve.concentrations[1].concentration, 2);
  assert.equal(Object.hasOwn(dissolve.concentrations[0], 'concentration'), false);
  const reverse = solveEquilibrium(model([row('A dissolved', 'reactant', 0), row('A liquid', 'product', NaN, { phase: 'liquid' })]), K(2));
  close(reverse.extent, -0.5);
  close(reverse.concentrations[0].concentration, 0.5);
});

test('independent audit: charged reaction requires true counterion rows, not arbitrary net charge metadata', () => {
  const acid = model([row('HA', 'reactant', 0.1), row('H+', 'product', 0.01, { charge: 1 }), row('A−', 'product', 0, { charge: -1 })]);
  assert.throws(() => calculateQuotient(acid), /electroneutral/);
  const withCounterion = { ...acid, spectators: [{ name: 'Cl−', charge: -1, concentration: 0.01 }] };
  const result = solveEquilibrium(withCounterion, K(1e-5));
  const concentrations = result.concentrations.map((item) => item.concentration);
  close(concentrations[0] + concentrations[2], 0.1);
  close(concentrations[1] - concentrations[2], 0.01);
});

test('independent audit: nonideal mode requires every reaction and spectator gamma even at zero concentration', () => {
  const input = model([row('HA', 'reactant', 0.1, { activityCoefficient: 1 }), row('H+', 'product', 0, { charge: 1, activityCoefficient: 0.7 }), row('A−', 'product', 0, { charge: -1, activityCoefficient: 0.7 })], {
    activityMode: 'entered', spectators: [{ name: 'Na+', charge: 1, concentration: 0, activityCoefficient: 0.8 }],
  });
  const result = solveEquilibrium(input, K(1e-5));
  close(result.quotient.value, 1e-5);
  for (const species of input.species) assert.throws(() => calculateQuotient({ ...input, species: input.species.map((item) => item === species ? { ...item, activityCoefficient: undefined } : item) }), /activity coefficient/);
  assert.throws(() => calculateQuotient({ ...input, spectators: [{ ...input.spectators[0], activityCoefficient: undefined }] }), /activity coefficient/);
});

const salt = (options = {}) => ({ ions: [{ name: 'Ca²+', charge: 2, coefficient: 1, concentration: 0 }, { name: 'F−', charge: -1, coefficient: 2, concentration: 0 }],
  constant: K(4e-12), temperatureC: 25, activityMode: 'ideal', ...options });

test('independent audit: two-ion salt solubility preserves full formula stoichiometry', () => {
  const result = calculateSolubility(salt());
  close(result.solubility, 1e-4); // Ksp = s(2s)² = 4s³.
  close(result.concentrations[0], 1e-4);
  close(result.concentrations[1], 2e-4);
  close(2 * result.concentrations[0] - result.concentrations[1], 0, 1e-7);
  const zeroQ = compareSaturation(salt());
  assert.equal(zeroQ.quotient, 0);
  assert.equal(zeroQ.status, 'undersaturated');
});

test('independent audit: common-ion charge balance and its corrected mass action are explicit', () => {
  const input = salt({ activityMode: 'entered', ions: [{ name: 'Ca²+', charge: 2, coefficient: 1, concentration: 0, activityCoefficient: 0.3 },
    { name: 'F−', charge: -1, coefficient: 2, concentration: 0.1, activityCoefficient: 0.7 }], spectators: [{ name: 'Na+', charge: 1, concentration: 0.1, activityCoefficient: 0.8 }] });
  const result = calculateSolubility(input);
  close(0.3 * result.concentrations[0] * (0.7 * result.concentrations[1]) ** 2, 4e-12);
  close(result.concentrations[1], 0.1 + 2 * result.solubility);
  assert.ok(result.solubility < 1e-8);
  assert.throws(() => calculateSolubility({ ...input, spectators: [] }), /counterion/);
  assert.throws(() => calculateSolubility({ ...input, spectators: [{ ...input.spectators[0], activityCoefficient: undefined }] }), /activity coefficient/);
});

test('independent audit: supersaturation is identified but not silently treated as dissolution', () => {
  const input = salt({ ions: [{ name: 'Ca²+', charge: 2, coefficient: 1, concentration: 1 }, { name: 'F−', charge: -1, coefficient: 2, concentration: 2 }] });
  assert.equal(compareSaturation(input).status, 'supersaturated');
  assert.throws(() => calculateSolubility(input), /supersaturated/);
});

test('independent audit: representability failures fail closed rather than displaying quotient zero or Infinity', () => {
  assert.throws(() => calculateQuotient(model([row('A', 'reactant', 1e300), row('B', 'product', 1e-300)])), /represented/);
  assert.throws(() => compareSaturation(salt({ ions: [{ name: 'Ca²+', charge: 2, coefficient: 1, concentration: 1e200 }, { name: 'F−', charge: -1, coefficient: 2, concentration: 2e200 }] })), /represented/);
});
