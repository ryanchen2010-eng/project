import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { toMoles, calculateReaction, calculateRequiredAmounts } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);

const quantity = (value, unit = 'mol') => ({ value, unit });
const hydrogen = { inputSlot: 0, name: 'Hydrogen', formula: 'H2', molarMass: 2.016, coefficient: 2 };
const oxygen = { inputSlot: 1, name: 'Oxygen', formula: 'O2', molarMass: 31.998, coefficient: 1 };
const water = { name: 'Water', formula: 'H2O', molarMass: 18.015, coefficient: 2 };
const waterReaction = () => ({
  balanced: true,
  reactants: [{ ...hydrogen }, { ...oxygen }],
  product: { ...water },
  excludedInputs: [],
  notes: [],
});

function close(actual, expected, relativeTolerance = 1e-12) {
  assert.ok(Number.isFinite(actual), `Expected finite value, received ${actual}`);
  if (expected === 0) assert.equal(actual, 0);
  else assert.ok(Math.abs(actual - expected) <= Math.abs(expected) * relativeTolerance,
    `Expected ${expected}, received ${actual}`);
}

function reactantAt(result, inputSlot) {
  const reactant = result.reactants.find((item) => item.inputSlot === inputSlot);
  assert.ok(reactant, `Missing reactant for input ${inputSlot}`);
  return reactant;
}

test('quantity conversion supports grams, milligrams, moles, and millimoles', () => {
  close(toMoles(quantity(18.015, 'g'), 18.015), 1);
  close(toMoles(quantity(18015, 'mg'), 18.015), 1);
  close(toMoles(quantity(1, 'mol'), 18.015), 1);
  close(toMoles(quantity(1000, 'mmol'), 18.015), 1);
  close(toMoles(quantity(0, 'g'), 18.015), 0);
});

test('mixed mass units identify the limiting input and preserve excess reactant', () => {
  const result = calculateReaction(waterReaction(), {
    0: quantity(4.032, 'g'),
    1: quantity(15999, 'mg'),
  });
  close(result.extent, 0.5);
  close(result.product.moles, 1);
  close(result.product.grams, 18.015);
  assert.deepEqual(result.limitingInputs, [1]);
  const h2 = reactantAt(result, 0);
  assert.equal(h2.name, 'Hydrogen');
  close(h2.availableMoles, 2);
  close(h2.consumedMoles, 1);
  close(h2.remainingMoles, 1);
  close(h2.remainingGrams, 2.016);
  const o2 = reactantAt(result, 1);
  close(o2.availableMoles, 0.5);
  close(o2.consumedMoles, 0.5);
  close(o2.remainingMoles, 0);
  close(o2.remainingGrams, 0);
});

test('non-unit stoichiometric coefficients determine consumption and product amount', () => {
  const ammoniaReaction = {
    balanced: true,
    reactants: [
      { ...hydrogen, coefficient: 3 },
      { inputSlot: 1, name: 'Nitrogen', formula: 'N2', molarMass: 28.014, coefficient: 1 },
    ],
    product: { name: 'Ammonia', formula: 'NH3', molarMass: 17.031, coefficient: 2 },
    excludedInputs: [], notes: [],
  };
  const result = calculateReaction(ammoniaReaction, { 0: quantity(12, 'mmol'), 1: quantity(0.003) });
  close(result.extent, 0.003);
  close(result.product.moles, 0.006);
  close(result.product.grams, 0.102186);
  assert.deepEqual(result.limitingInputs, [1]);
  close(reactantAt(result, 0).consumedMoles, 0.009);
  close(reactantAt(result, 0).remainingMoles, 0.003);
  close(reactantAt(result, 0).remainingGrams, 0.006048);
});

test('input slots, rather than reactant array positions, select entered quantities', () => {
  const stoichiometry = waterReaction();
  stoichiometry.reactants = [
    { ...oxygen, inputSlot: 0 },
    { ...hydrogen, inputSlot: 1 },
  ];
  const result = calculateReaction(stoichiometry, { 0: quantity(0.5), 1: quantity(2) });
  close(result.product.moles, 1);
  close(result.product.grams, 18.015);
  assert.deepEqual(result.limitingInputs, [0]);
  assert.equal(reactantAt(result, 0).name, 'Oxygen');
  assert.equal(reactantAt(result, 1).name, 'Hydrogen');
  close(reactantAt(result, 1).remainingMoles, 1);
});

test('exact and relative near-ties mark both limiting reactants without changing yield', () => {
  const exact = calculateReaction(waterReaction(), { 0: quantity(2), 1: quantity(1) });
  assert.deepEqual(exact.limitingInputs, [0, 1]);
  close(exact.extent, 1);
  const near = calculateReaction(waterReaction(), { 0: quantity(2), 1: quantity(1 + 5e-10) });
  assert.deepEqual(near.limitingInputs, [0, 1]);
  close(near.extent, 1);
  close(near.product.moles, 2);
  const distinct = calculateReaction(waterReaction(), { 0: quantity(2), 1: quantity(1 + 5e-8) });
  assert.deepEqual(distinct.limitingInputs, [0]);
});

test('zero available reactant gives zero yield and does not consume the other input', () => {
  const result = calculateReaction(waterReaction(), { 0: quantity(0), 1: quantity(1) });
  close(result.extent, 0);
  close(result.product.moles, 0);
  close(result.product.grams, 0);
  assert.deepEqual(result.limitingInputs, [0]);
  close(reactantAt(result, 1).consumedMoles, 0);
  close(reactantAt(result, 1).remainingMoles, 1);
  const allZero = calculateReaction(waterReaction(), { 0: quantity(0), 1: quantity(0) });
  assert.deepEqual(allZero.limitingInputs, [0, 1]);
  close(allZero.product.grams, 0);
});

test('small quantities remain distinct and are not rounded or treated as an absolute tie', () => {
  const result = calculateReaction(waterReaction(), { 0: quantity(2e-15), 1: quantity(2e-15) });
  close(result.extent, 1e-15);
  close(result.product.moles, 2e-15);
  close(result.product.grams, 3.603e-14);
  assert.deepEqual(result.limitingInputs, [0]);
  close(reactantAt(result, 1).remainingMoles, 1e-15);
});

test('one-reactant elimination does not require an excluded solvent or catalyst quantity', () => {
  const elimination = {
    balanced: true,
    reactants: [{ inputSlot: 1, name: 'tert-Butyl bromide', formula: 'C4H9Br', molarMass: 137.018, coefficient: 1 }],
    product: { name: '2-Methylpropene', formula: 'C4H8', molarMass: 56.108, coefficient: 1 },
    excludedInputs: [{ inputSlot: 0, name: 'Water', reason: 'Solvent, not a stoichiometric reactant' }],
    notes: ['Idealized elimination only'],
  };
  const result = calculateReaction(elimination, { 1: quantity(13.7018, 'g') });
  close(result.extent, 0.1);
  close(result.product.moles, 0.1);
  close(result.product.grams, 5.6108);
  assert.deepEqual(result.limitingInputs, [1]);
  assert.equal(result.reactants.length, 1);
  assert.equal(result.reactants[0].inputSlot, 1);
  const required = calculateRequiredAmounts(elimination, quantity(5.6108, 'g'));
  assert.equal(required.reactants.length, 1);
  assert.equal(required.reactants[0].inputSlot, 1);
  close(required.reactants[0].grams, 13.7018);
});

test('a salt uses its supplied whole-compound molar mass, not the reactive ion or parsed formula', () => {
  const substitution = {
    balanced: true,
    reactants: [
      { inputSlot: 0, name: 'Bromomethane', formula: 'CH3Br', molarMass: 94.939, coefficient: 1 },
      { inputSlot: 1, name: 'Sodium hydroxide', formula: 'NaOH', molarMass: 39.997, coefficient: 1 },
    ],
    product: { name: 'Methanol', formula: 'CH4O', molarMass: 32.042, coefficient: 1 },
    excludedInputs: [], notes: [],
  };
  const result = calculateReaction(substitution, { 0: quantity(9.4939, 'g'), 1: quantity(4, 'g') });
  close(reactantAt(result, 1).availableMoles, 4 / 39.997);
  close(result.product.grams, 3.2042);
  assert.deepEqual(result.limitingInputs, [0]);
  close(reactantAt(result, 1).remainingGrams, 4 - 0.1 * 39.997, 1e-9);
  const opaqueFormula = structuredClone(substitution);
  opaqueFormula.reactants[1].formula = 'whole salt';
  close(calculateReaction(opaqueFormula, { 0: quantity(0.1), 1: quantity(3.9997, 'g') }).product.moles, 0.1);
});

test('required amounts scale every coefficient from target product mass or molar amount', () => {
  for (const target of [quantity(36.03, 'g'), quantity(36030, 'mg'), quantity(2), quantity(2000, 'mmol')]) {
    const result = calculateRequiredAmounts(waterReaction(), target);
    close(result.product.moles, 2);
    close(result.product.grams, 36.03);
    close(reactantAt(result, 0).moles, 2);
    close(reactantAt(result, 0).grams, 4.032);
    close(reactantAt(result, 1).moles, 1);
    close(reactantAt(result, 1).grams, 31.998);
  }
});

test('unit conversion rejects invalid quantities, unknown units, and invalid molar masses', () => {
  for (const invalid of [quantity(-1), quantity(NaN), quantity(Infinity), quantity(-Infinity),
    quantity(1, 'kg'), quantity(1, ''), { value: '1', unit: 'mol' }, {}, null, undefined]) {
    assert.throws(() => toMoles(invalid, 18.015), Error);
  }
  for (const invalidMass of [0, -1, NaN, Infinity, '18.015', undefined]) {
    assert.throws(() => toMoles(quantity(1), invalidMass), Error);
  }
  assert.throws(() => toMoles(quantity(Number.MAX_VALUE, 'g'), Number.MIN_VALUE), Error);
});

test('calculations reject unbalanced, missing, negative, or nonfinite input amounts', () => {
  const complete = { 0: quantity(2), 1: quantity(1) };
  const unbalanced = { ...waterReaction(), balanced: false };
  assert.throws(() => calculateReaction(unbalanced, complete), Error);
  assert.throws(() => calculateRequiredAmounts(unbalanced, quantity(1)), Error);
  for (const amounts of [{}, { 0: quantity(2) }, { 1: quantity(1) },
    { ...complete, 0: quantity(-1) }, { ...complete, 1: quantity(NaN) },
    { ...complete, 0: quantity(Infinity) }, { ...complete, 1: quantity(1, 'litres') }]) {
    assert.throws(() => calculateReaction(waterReaction(), amounts), Error);
  }
});

test('both calculation modes reject invalid species coefficients and molar masses', () => {
  for (const field of ['coefficient', 'molarMass']) {
    for (const value of [0, -1, NaN, Infinity]) {
      for (const location of ['reactant', 'product']) {
        const stoichiometry = waterReaction();
        if (location === 'reactant') stoichiometry.reactants[0][field] = value;
        else stoichiometry.product[field] = value;
        assert.throws(() => calculateReaction(stoichiometry, { 0: quantity(2), 1: quantity(1) }), Error);
        assert.throws(() => calculateRequiredAmounts(stoichiometry, quantity(1)), Error);
      }
    }
  }
  const noReactants = { ...waterReaction(), reactants: [] };
  assert.throws(() => calculateReaction(noReactants, {}), Error);
  assert.throws(() => calculateRequiredAmounts(noReactants, quantity(1)), Error);
});

test('a requested product amount must be positive and finite', () => {
  for (const invalid of [quantity(0), quantity(-1), quantity(NaN), quantity(Infinity), quantity(1, 'kg')]) {
    assert.throws(() => calculateRequiredAmounts(waterReaction(), invalid), Error);
  }
});

test('overflowing yields or required masses fail instead of returning Infinity or NaN', () => {
  assert.throws(() => calculateReaction(waterReaction(), {
    0: quantity(Number.MAX_VALUE), 1: quantity(Number.MAX_VALUE),
  }), Error);
  assert.throws(() => calculateRequiredAmounts(waterReaction(), quantity(Number.MAX_VALUE)), Error);
});
