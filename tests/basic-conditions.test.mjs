import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';

const ui = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
test('basic conditions are a labeled native option with reagent and solvent guidance', () => {
  assert.match(ui, /<label for="reaction-catalyst">/);
  assert.match(ui, /<option value="base">Base \/ Basic Conditions<\/option>/);
  assert.match(ui, /aria-describedby="reaction-catalyst-help"/);
  assert.match(ui, /does not add or replace a reagent or select a solvent/);
  assert.match(ui, /Choose hydroxide \(OH⁻\) as a chemical input separately/);
});
