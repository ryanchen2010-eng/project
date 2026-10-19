import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const source = await readFile(new URL('../src/mole-calculator.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { convertMoles, AVOGADRO_CONSTANT } = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= Math.abs(expected) * 1e-12, `${actual} != ${expected}`);
test('SI particle count and full salt mass count formula units, not ions', () => {
  assert.equal(AVOGADRO_CONSTANT, 6.02214076e23);
  const salt = convertMoles({ value: 58.443, unit: 'g', molarMass: 58.443, entityKind: 'formula-units' });
  assert.equal(salt.moles, 1); assert.equal(salt.particles, AVOGADRO_CONSTANT); assert.equal(salt.grams, 58.443);
  assert.equal(salt.entityKind, 'formula-units');
  const base = convertMoles({ value: 39.997, unit: 'g', molarMass: 39.997, entityKind: 'formula-units' });
  assert.equal(base.moles, 1);
});
test('all mass and mole units agree', () => {
  for (const [value, unit] of [[.018015, 'kg'], [18.015, 'g'], [18015, 'mg'], [18015000, 'µg'], [1, 'mol'], [1000, 'mmol'], [1000000, 'µmol'], [AVOGADRO_CONSTANT, 'particles']]) {
    const result = convertMoles({ value, unit, molarMass: 18.015, entityKind: 'molecules' });
    close(result.moles, 1); close(result.particles, AVOGADRO_CONSTANT); close(result.grams, 18.015);
  }
});
test('moles and particles work without molar mass and do not invent a mass', () => {
  const result = convertMoles({ value: AVOGADRO_CONSTANT / 2, unit: 'particles', entityKind: 'atoms' });
  assert.equal(result.moles, .5); assert.equal(Object.hasOwn(result, 'grams'), false);
  assert.equal(result.entityKind, 'atoms');
});
test('zero amounts remain exactly zero for every unit', () => {
  for (const unit of ['kg', 'g', 'mg', 'µg', 'mol', 'mmol', 'µmol', 'particles']) {
    const result = convertMoles({ value: 0, unit, molarMass: 58.443, entityKind: 'formula-units' });
    assert.equal(result.moles, 0); assert.equal(result.particles, 0); assert.equal(result.grams, 0);
  }
});
test('negative, nonnumeric, missing or unrepresentable amounts fail closed', () => {
  for (const value of [-1, NaN, Infinity, '1', null, undefined]) assert.throws(() => convertMoles({ value, unit: 'mol', entityKind: 'molecules' }));
  assert.throws(() => convertMoles({ value: Number.MAX_VALUE, unit: 'mol', entityKind: 'molecules' }), /numerical range/);
  assert.throws(() => convertMoles({ value: Number.MIN_VALUE, unit: 'particles', entityKind: 'molecules' }), /numerical range/);
  assert.throws(() => convertMoles({ value: Number.MIN_VALUE, unit: 'mg', molarMass: 100, entityKind: 'molecules' }), /numerical range/);
});
test('unknown units, entities and masses cannot be silently inferred', () => {
  for (const unit of ['', 'moles', '__proto__', 'toString', undefined]) assert.throws(() => convertMoles({ value: 1, unit, molarMass: 100, entityKind: 'atoms' }));
  for (const entityKind of ['', 'ions', undefined]) assert.throws(() => convertMoles({ value: 1, unit: 'mol', entityKind }));
  assert.throws(() => convertMoles({ value: 1, unit: 'g', entityKind: 'molecules' }), /molar mass/);
  for (const molarMass of [0, -1, NaN, Infinity, '100', null]) assert.throws(() => convertMoles({ value: 1, unit: 'mol', entityKind: 'molecules', molarMass }));
});
