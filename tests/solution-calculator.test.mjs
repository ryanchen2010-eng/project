import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/solution-calculator.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { calculateMolarity, calculateSoluteMass, calculateDilution } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);

const amount = (value, unit = 'mol') => ({ value, unit });
const volume = (value, unit = 'L') => ({ value, unit });
const concentration = (value, unit = 'mol/L') => ({ value, unit });
const molarityInput = () => ({ amount: amount(0.133), volume: volume(355, 'mL') });
const massInput = () => ({ concentration: concentration(0.2), volume: volume(250, 'mL'), molarMass: 110.98 });
const dilutionInput = () => ({ stock: concentration(1), target: concentration(100, 'mmol/L'), finalVolume: volume(250, 'mL') });

function close(actual, expected, tolerance = 1e-12) {
  assert.ok(Number.isFinite(actual), `Expected a finite value, received ${actual}`);
  assert.ok(Math.abs(actual - expected) <= Math.abs(expected) * tolerance,
    `Expected ${expected}, received ${actual}`);
}

test('molarity reference uses final total solution volume and preserves full precision', () => {
  const result = calculateMolarity(molarityInput());
  close(result.moles, 0.133);
  close(result.litres, 0.355);
  close(result.molarity, 0.37464788732394366);
  assert.equal(Object.hasOwn(result, 'grams'), false);
});

test('mass-to-molarity reference uses the selected whole-compound molar mass', () => {
  const result = calculateMolarity({ amount: amount(25.2, 'g'), volume: volume(0.5), molarMass: 60.052 });
  close(result.moles, 25.2 / 60.052);
  close(result.molarity, 25.2 / 60.052 / 0.5);
  assert.equal(result.grams, 25.2);
});

test('all solute amount and volume units produce equivalent molarity', () => {
  const amounts = [amount(0.2), amount(200, 'mmol'), amount(20, 'g'), amount(20_000, 'mg')];
  const volumes = [volume(0.25), volume(250, 'mL'), volume(250_000, 'µL')];
  for (const solute of amounts) {
    for (const solutionVolume of volumes) {
      const result = calculateMolarity({ amount: solute, volume: solutionVolume, molarMass: 100 });
      close(result.moles, 0.2);
      close(result.litres, 0.25);
      close(result.molarity, 0.8);
      close(result.grams, 20);
    }
  }
});

test('molar amount works without molar mass and mass is returned only when supplied', () => {
  for (const solute of [amount(0.2), amount(200, 'mmol')]) {
    const noMass = calculateMolarity({ amount: solute, volume: volume(0.5) });
    close(noMass.molarity, 0.4);
    assert.equal(Object.hasOwn(noMass, 'grams'), false);
    const withMass = calculateMolarity({ amount: solute, volume: volume(0.5), molarMass: 58.44 });
    close(withMass.grams, 11.688);
  }
});

test('solute mass reference for 0.2 mol/L calcium chloride in 250 mL is 5.549 g', () => {
  const result = calculateSoluteMass(massInput());
  close(result.moles, 0.05);
  close(result.grams, 5.549);
  close(result.litres, 0.25);
  close(result.molarity, 0.2);
});

test('all concentration and volume unit combinations produce equivalent solute mass', () => {
  const concentrations = [concentration(0.2), concentration(200, 'mmol/L'), concentration(200_000, 'µmol/L')];
  const volumes = [volume(0.25), volume(250, 'mL'), volume(250_000, 'µL')];
  for (const target of concentrations) {
    for (const solutionVolume of volumes) {
      const result = calculateSoluteMass({ concentration: target, volume: solutionVolume, molarMass: 110.98 });
      close(result.moles, 0.05);
      close(result.grams, 5.549);
      close(result.litres, 0.25);
      close(result.molarity, 0.2);
    }
  }
});

test('dilution reference takes 25 mL of 1 mol/L stock to a total of 250 mL at 100 mmol/L', () => {
  const result = calculateDilution(dilutionInput());
  close(result.stockLitres, 0.025);
  close(result.finalLitres, 0.25);
  close(result.stockMolarity, 1);
  close(result.targetMolarity, 0.1);
  close(result.dilutionFactor, 10);
  assert.deepEqual(Object.keys(result).sort(), ['dilutionFactor', 'finalLitres', 'stockLitres', 'stockMolarity', 'targetMolarity']);
});

test('dilution conserves solute across every supported unit combination', () => {
  const stocks = [concentration(0.5), concentration(500, 'mmol/L'), concentration(500_000, 'µmol/L')];
  const targets = [concentration(0.002), concentration(2, 'mmol/L'), concentration(2000, 'µmol/L')];
  const volumes = [volume(0.1), volume(100, 'mL'), volume(100_000, 'µL')];
  for (const stock of stocks) {
    for (const target of targets) {
      for (const finalVolume of volumes) {
        const result = calculateDilution({ stock, target, finalVolume });
        close(result.stockLitres, 0.0004);
        close(result.dilutionFactor, 250);
        close(result.stockMolarity * result.stockLitres, result.targetMolarity * result.finalLitres);
      }
    }
  }
});

test('equal normalized stock and target concentrations mean no dilution', () => {
  const result = calculateDilution({ stock: concentration(0.1), target: concentration(100, 'mmol/L'), finalVolume: volume(500, 'mL') });
  assert.equal(result.dilutionFactor, 1);
  assert.equal(result.stockLitres, result.finalLitres);
});

test('dilution rejects concentrating the stock without silently rounding the target', () => {
  for (const target of [concentration(1001, 'mmol/L'), concentration(1 + Number.EPSILON)]) {
    assert.throws(() => calculateDilution({ ...dilutionInput(), target }), /cannot exceed/);
  }
});

test('small practical values retain precision rather than rounding to zero', () => {
  const molarity = calculateMolarity({ amount: amount(1e-9, 'mmol'), volume: volume(10, 'µL'), molarMass: 100 });
  close(molarity.moles, 1e-12);
  close(molarity.molarity, 1e-7);
  close(molarity.grams, 1e-10);
  const mass = calculateSoluteMass({ concentration: concentration(0.01, 'µmol/L'), volume: volume(1, 'µL'), molarMass: 100 });
  close(mass.moles, 1e-14);
  close(mass.grams, 1e-12);
  const dilute = calculateDilution({ stock: concentration(1, 'µmol/L'), target: concentration(0.01, 'µmol/L'), finalVolume: volume(1, 'µL') });
  close(dilute.stockLitres, 1e-8);
});

test('calculators reject missing inputs and do not coerce nonnumeric values', () => {
  for (const calculate of [calculateMolarity, calculateSoluteMass, calculateDilution]) {
    for (const input of [undefined, null, {}, '1', 1]) assert.throws(() => calculate(input), Error);
  }
  for (const invalid of [0, -1, NaN, Infinity, -Infinity, '1', null, undefined, true]) {
    assert.throws(() => calculateMolarity({ ...molarityInput(), amount: amount(invalid) }), Error);
    assert.throws(() => calculateMolarity({ ...molarityInput(), volume: volume(invalid) }), Error);
    assert.throws(() => calculateSoluteMass({ ...massInput(), concentration: concentration(invalid) }), Error);
    assert.throws(() => calculateSoluteMass({ ...massInput(), volume: volume(invalid) }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), stock: concentration(invalid) }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), target: concentration(invalid) }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), finalVolume: volume(invalid) }), Error);
  }
});

test('unknown units fail closed instead of being inferred or coerced', () => {
  for (const unit of ['', 'kg', 'moles', 'M', '__proto__', undefined, null, 1]) {
    assert.throws(() => calculateMolarity({ ...molarityInput(), amount: { value: 1, unit } }), Error);
  }
  for (const unit of ['', 'l', 'ml', 'uL', 'μL', '__proto__', undefined, null, 1]) {
    assert.throws(() => calculateMolarity({ ...molarityInput(), volume: { value: 1, unit } }), Error);
    assert.throws(() => calculateSoluteMass({ ...massInput(), volume: { value: 1, unit } }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), finalVolume: { value: 1, unit } }), Error);
  }
  for (const unit of ['', 'M', 'mM', 'g/L', 'umol/L', '__proto__', undefined, null, 1]) {
    assert.throws(() => calculateSoluteMass({ ...massInput(), concentration: { value: 1, unit } }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), stock: { value: 1, unit } }), Error);
    assert.throws(() => calculateDilution({ ...dilutionInput(), target: { value: 0.1, unit } }), Error);
  }
});

test('mass conversion requires a positive finite molar mass but dilution does not', () => {
  for (const molarMass of [0, -1, NaN, Infinity, -Infinity, '100', null, undefined, true]) {
    assert.throws(() => calculateSoluteMass({ ...massInput(), molarMass }), Error);
    for (const unit of ['g', 'mg']) {
      assert.throws(() => calculateMolarity({ amount: amount(1, unit), volume: volume(1), molarMass }), Error);
    }
    if (molarMass !== undefined) {
      assert.throws(() => calculateMolarity({ ...molarityInput(), molarMass }), Error);
    }
  }
  assert.doesNotThrow(() => calculateDilution(dilutionInput()));
});

test('molarity rejects overflow and zero-underflow in conversions and results', () => {
  const invalidInputs = [
    { amount: amount(Number.MIN_VALUE, 'mmol'), volume: volume(1) },
    { amount: amount(Number.MIN_VALUE, 'mg'), volume: volume(1), molarMass: 1 },
    { amount: amount(1), volume: volume(Number.MIN_VALUE, 'mL') },
    { amount: amount(1), volume: volume(Number.MIN_VALUE, 'µL') },
    { amount: amount(Number.MAX_VALUE, 'g'), volume: volume(1), molarMass: Number.MIN_VALUE },
    { amount: amount(Number.MIN_VALUE, 'g'), volume: volume(1), molarMass: Number.MAX_VALUE },
    { amount: amount(Number.MAX_VALUE), volume: volume(Number.MIN_VALUE) },
    { amount: amount(Number.MIN_VALUE), volume: volume(Number.MAX_VALUE) },
    { amount: amount(Number.MAX_VALUE), volume: volume(1), molarMass: 2 },
    { amount: amount(Number.MIN_VALUE), volume: volume(1), molarMass: Number.MIN_VALUE },
  ];
  for (const input of invalidInputs) assert.throws(() => calculateMolarity(input), /too large or too small/);
});

test('solute mass rejects overflow and zero-underflow in conversions and products', () => {
  const invalidInputs = [
    { ...massInput(), concentration: concentration(Number.MIN_VALUE, 'mmol/L') },
    { ...massInput(), concentration: concentration(Number.MIN_VALUE, 'µmol/L') },
    { ...massInput(), volume: volume(Number.MIN_VALUE, 'mL') },
    { ...massInput(), concentration: concentration(Number.MAX_VALUE), volume: volume(2) },
    { ...massInput(), concentration: concentration(Number.MIN_VALUE), volume: volume(0.1) },
    { concentration: concentration(1), volume: volume(2), molarMass: Number.MAX_VALUE },
    { concentration: concentration(Number.MIN_VALUE), volume: volume(1), molarMass: Number.MIN_VALUE },
  ];
  for (const input of invalidInputs) assert.throws(() => calculateSoluteMass(input), /too large or too small/);
});

test('dilution rejects overflow and zero-underflow in conversions, factor, and stock aliquot', () => {
  const invalidInputs = [
    { ...dilutionInput(), stock: concentration(Number.MIN_VALUE, 'mmol/L') },
    { ...dilutionInput(), target: concentration(Number.MIN_VALUE, 'µmol/L') },
    { ...dilutionInput(), finalVolume: volume(Number.MIN_VALUE, 'µL') },
    { stock: concentration(Number.MAX_VALUE), target: concentration(Number.MIN_VALUE), finalVolume: volume(1) },
    { stock: concentration(1), target: concentration(0.1), finalVolume: volume(Number.MIN_VALUE) },
  ];
  for (const input of invalidInputs) assert.throws(() => calculateDilution(input), /too large or too small/);
});

test('calculations never mutate the input quantities or add solvent-volume assumptions', () => {
  for (const [calculate, input] of [[calculateMolarity, molarityInput()], [calculateSoluteMass, massInput()], [calculateDilution, dilutionInput()]]) {
    const before = structuredClone(input);
    for (const nested of Object.values(input)) if (nested && typeof nested === 'object') Object.freeze(nested);
    Object.freeze(input);
    const result = calculate(input);
    assert.deepEqual(input, before);
    assert.equal(Object.hasOwn(result, 'solventLitres'), false);
    assert.equal(Object.hasOwn(result, 'addedSolventLitres'), false);
  }
});
