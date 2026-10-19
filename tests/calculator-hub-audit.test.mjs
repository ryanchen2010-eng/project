import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const compile = (source) => ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText;
const url = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const read = (name) => readFile(new URL(`../src/${name}`, import.meta.url), 'utf8');
const equilibriumUrl = url(compile(await read('equilibrium-calculator.ts')));
const { solveEquilibrium } = await import(equilibriumUrl);
const { calculateSolubility, compareSaturation } = await import(url(compile(await read('solubility-calculator.ts'))
  .replace(/from ['"]\.\/equilibrium-calculator['"]/, `from '${equilibriumUrl}'`)));
const { calculateAcidBase } = await import(url(compile(await read('acid-base-calculator.ts'))));
const { convertMoles, AVOGADRO_CONSTANT } = await import(url(compile(await read('mole-calculator.ts'))));
const massUrl = url(compile(await read('solution-compound.ts')));
const { calculatorCompoundFromMolecule, decodeCalculatorTransfer } = await import(url(compile(await read('calculator-compound.ts'))
  .replace(/from ['"]\.\/solution-compound['"]/, `from '${massUrl}'`)));

function relative(actual, expected, tolerance = 2e-9) {
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(Math.abs(actual), Math.abs(expected), 1e-300),
    `${actual} should equal ${expected} within relative tolerance ${tolerance}`);
}
const water = { notation: 'K', value: 1e-14 };

test('independent closed-form A⇌B equilibria agree with all entered activity factors', () => {
  for (const initialA of [0.01, 0.1, 1]) for (const initialB of [0, 0.03]) for (const k of [0.001, 1, 1000]) {
    const gammaA = 0.4;
    const gammaB = 0.7;
    const total = initialA + initialB;
    const ratio = k * gammaA / gammaB;
    const expectedB = total * ratio / (1 + ratio);
    const expectedA = total / (1 + ratio);
    const answer = solveEquilibrium({ temperatureC: 25, activityMode: 'entered', balancedConfirmed: true,
      species: [
        { name: 'A', side: 'reactant', coefficient: 1, phase: 'aq', charge: 0, concentration: initialA, activityCoefficient: gammaA },
        { name: 'B', side: 'product', coefficient: 1, phase: 'aq', charge: 0, concentration: initialB, activityCoefficient: gammaB },
      ] }, { notation: 'K', value: k });
    relative(answer.concentrations[0].concentration, expectedA);
    relative(answer.concentrations[1].concentration, expectedB);
    relative(answer.concentrations[0].concentration + answer.concentrations[1].concentration, total);
  }
});

test('independent pure-phase dissociation matches the two-ion solubility calculator in nonideal mode', () => {
  const ksp = 1.8e-10;
  const gammas = [0.4, 0.7];
  const expected = Math.sqrt(ksp / (gammas[0] * gammas[1]));
  const salt = { temperatureC: 25, activityMode: 'entered', constant: { notation: 'K', value: ksp }, ions: [
    { name: 'Ag+', coefficient: 1, charge: 1, concentration: 0, activityCoefficient: gammas[0] },
    { name: 'Cl−', coefficient: 1, charge: -1, concentration: 0, activityCoefficient: gammas[1] },
  ] };
  const solubility = calculateSolubility(salt);
  relative(solubility.solubility, expected);
  const equilibrium = solveEquilibrium({ temperatureC: 25, activityMode: 'entered', balancedConfirmed: true, species: [
    { name: 'AgCl(s)', side: 'reactant', coefficient: 1, phase: 'solid', concentration: 0, charge: 0 },
    ...salt.ions.map((ion) => ({ ...ion, side: 'product', phase: 'aq' })),
  ] }, salt.constant);
  relative(equilibrium.extent, expected);
  relative(equilibrium.extent, solubility.solubility);
});

test('2:1 salt with a common ion satisfies independent polynomial, salt and charge balances', () => {
  const commonFluoride = 0.001;
  const ksp = 3.9e-11;
  const model = { temperatureC: 25, activityMode: 'ideal', constant: { notation: 'K', value: ksp }, ions: [
    { name: 'Ca2+', coefficient: 1, charge: 2, concentration: 0 },
    { name: 'F−', coefficient: 2, charge: -1, concentration: commonFluoride },
  ], spectators: [{ name: 'Na+', charge: 1, concentration: commonFluoride }] };
  const answer = calculateSolubility(model);
  const [calcium, fluoride] = answer.concentrations;
  relative(calcium * fluoride ** 2, ksp);
  relative(calcium, answer.solubility);
  relative(fluoride, commonFluoride + 2 * answer.solubility);
  assert.ok(Math.abs(2 * calcium + commonFluoride - fluoride) < 1e-12);
  const status = compareSaturation({ ...model, ions: model.ions.map((ion, index) => ({ ...ion, concentration: answer.concentrations[index] })) });
  assert.equal(status.status, 'saturated');
});

test('nonideal pure water pH uses hydrogen activity rather than concentration and supplied-temperature Kw', () => {
  const gammaH = 0.6;
  const gammaOH = 0.8;
  const pKw = 13;
  const answer = calculateAcidBase({ model: 'strong-acid', temperatureC: 50, concentration: 0,
    kw: { notation: 'pK', value: pKw }, activities: { mode: 'entered', hydrogen: gammaH, hydroxide: gammaOH,
      family: [], counterions: [0.7] } });
  const expectedConcentration = Math.sqrt(10 ** -pKw / (gammaH * gammaOH));
  relative(answer.hydrogen, expectedConcentration);
  relative(answer.hydroxide, expectedConcentration);
  relative(answer.pH, -Math.log10(gammaH * expectedConcentration));
  relative(answer.pH + answer.pOH, pKw);
  assert.notEqual(answer.pH, -Math.log10(answer.hydrogen));
});

test('weak acid and base mirror models obey supplied activities and complete water balance', () => {
  const common = { temperatureC: 25, concentration: 0.1, kw: water,
    constants: [{ notation: 'K', value: 1e-5 }] };
  const acid = calculateAcidBase({ ...common, model: 'weak-acid', activities: { mode: 'entered', hydrogen: 0.7,
    hydroxide: 0.7, family: [1, 0.7], counterions: [] } });
  const base = calculateAcidBase({ ...common, model: 'weak-base', activities: { mode: 'entered', hydrogen: 0.7,
    hydroxide: 0.7, family: [0.7, 1], counterions: [] } });
  relative(acid.pH + base.pH, 14);
  const species = Object.fromEntries(acid.species.map((item) => [item.name, item]));
  relative(species['H+'].activity * species['A−'].activity / species.HA.activity, 1e-5);
  relative(species['H+'].activity * species['OH−'].activity, 1e-14);
  relative(species.HA.concentration + species['A−'].concentration, 0.1);
  relative(species['H+'].concentration, species['OH−'].concentration + species['A−'].concentration);
});

test('polyprotic salt model satisfies independently recomputed family and every dissociation balance', () => {
  const constants = [1e-3, 1e-7, 1e-11];
  const answer = calculateAcidBase({ model: 'polyprotic', steps: 3, concentration: 0.01,
    counterionConcentration: 0.02, temperatureC: 25, kw: water,
    constants: constants.map((value) => ({ notation: 'K', value })), activities: { mode: 'entered',
      hydrogen: 0.8, hydroxide: 0.9, family: [1, 0.8, 0.7, 0.6], counterions: [0.8] } });
  const species = Object.fromEntries(answer.species.map((item) => [item.name, item]));
  const names = ['H₃A', 'H₂A−', 'HA²−', 'A³−'];
  relative(names.reduce((sum, name) => sum + species[name].concentration, 0), 0.01);
  for (let i = 0; i < constants.length; i++) {
    relative(species['H+'].activity * species[names[i + 1]].activity / species[names[i]].activity, constants[i]);
  }
  relative(species['H+'].concentration + species['M+ (spectator)'].concentration,
    species['OH−'].concentration + species['H₂A−'].concentration + 2 * species['HA²−'].concentration + 3 * species['A³−'].concentration);
});

test('nonideal models cannot silently fill missing dissolved or spectator activity coefficients', () => {
  assert.throws(() => solveEquilibrium({ temperatureC: 25, activityMode: 'entered', balancedConfirmed: true,
    species: [
      { name: 'A', side: 'reactant', coefficient: 1, phase: 'aq', charge: 0, concentration: 0.1, activityCoefficient: 0.7 },
      { name: 'B', side: 'product', coefficient: 1, phase: 'aq', charge: 0, concentration: 0 },
    ] }, { notation: 'K', value: 1 }), /coefficient for B/);
  assert.throws(() => calculateSolubility({ temperatureC: 25, activityMode: 'entered',
    constant: { notation: 'K', value: 1e-10 }, ions: [
      { name: 'Ag+', coefficient: 1, charge: 1, concentration: 0, activityCoefficient: 0.7 },
      { name: 'Cl−', coefficient: 1, charge: -1, concentration: 0.001, activityCoefficient: 0.7 },
    ], spectators: [{ name: 'Na+', charge: 1, concentration: 0.001 }] }), /coefficient for Na/);
});

test('even representable subnormal concentrations must preserve relative electroneutrality', () => {
  const ions = [
    { name: 'Ag+', coefficient: 1, charge: 1, concentration: 0 },
    { name: 'Cl−', coefficient: 1, charge: -1, concentration: 1e-320 },
  ];
  const salt = { temperatureC: 25, activityMode: 'ideal', constant: { notation: 'K', value: 1.8e-10 }, ions };
  assert.throws(() => calculateSolubility(salt), /counterion|balance/i);
  assert.throws(() => compareSaturation(salt), /counterion|balance/i);
  assert.throws(() => solveEquilibrium({ temperatureC: 25, activityMode: 'ideal', balancedConfirmed: true, species: [
    { name: 'AgCl(s)', side: 'reactant', coefficient: 1, phase: 'solid', concentration: 0, charge: 0 },
    ...ions.map((ion) => ({ ...ion, side: 'product', phase: 'aq' })),
  ] }, salt.constant), /electroneutral|counterion/i);
});

test('full salt or hydrate molar mass converts formula units, not the sum of constituent ions', () => {
  const mass = 249.68;
  const result = convertMoles({ value: mass, unit: 'g', molarMass: mass, entityKind: 'formula-units' });
  assert.equal(result.moles, 1);
  assert.equal(result.particles, AVOGADRO_CONSTANT);
  assert.equal(result.entityKind, 'formula-units');
});

test('exact atomic records are counted as atoms, while covalent diatomic records remain molecules', () => {
  const record = (name, formula, structureForm) => ({ id: name, name, formula, structureForm, cid: 1, properties: { mass: '4.0026 g/mol' } });
  assert.equal(calculatorCompoundFromMolecule(record('Helium', 'He', '[He]'), false).entityKind, 'atoms');
  assert.equal(calculatorCompoundFromMolecule(record('Oxygen', 'O2', 'O=O'), false).entityKind, 'molecules');
});

test('untrusted transfers reject invalid exact mass/entity data rather than borrowing by formula', () => {
  for (const compound of [
    { id: 'water', name: 'Water', formula: 'H2O', entityKind: 'electrons', molarMass: 18.015 },
    { id: 'water', name: 'Water', formula: 'H2O', entityKind: 'molecules', molarMass: -18.015 },
    { id: 'water', name: 'Water', formula: 'H2O', entityKind: 'molecules', cid: 0 },
  ]) assert.equal(decodeCalculatorTransfer(JSON.stringify({ version: 1, compound })), undefined);
});
