import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/crystal-unit-cell.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext}}).outputText;
const {rhodiumUnitCell} = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const cif = await readFile(new URL('../public/crystals/rhodium-trichloride-cod-1534198.cif', import.meta.url), 'utf8');

test('reviewed sites expand to exactly four Rh and twelve Cl, without duplicate positions', () => {
  const result = rhodiumUnitCell(cif);
  const rows = result.split('\n').filter(x => /^(Rh|Cl)\d+ /.test(x));
  assert.equal(rows.length, 16);
  assert.equal(rows.filter(x => x.startsWith('Rh')).length, 4);
  assert.equal(rows.filter(x => x.startsWith('Cl')).length, 12);
  assert.equal(new Set(rows.map(x => x.split(' ').slice(1).join(' '))).size, 16);
  assert.throws(() => rhodiumUnitCell(cif.replace('_cell_length_a 5.95', '_cell_length_a 9.95')));
  assert.throws(() => rhodiumUnitCell(cif.replace('0.226 0 0.219', '0.227 0 0.219')));
});

test('seven-case crystal inventory records only the implemented anhydrous phase', async () => {
  const cases = JSON.parse(await readFile(new URL('./explorer_crystal_benchmark_v1.json', import.meta.url), 'utf8'));
  const source = await readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.equal(cases.length, 7);
  assert.deepEqual(cases.filter(item => item.supported).map(item => item.id), ['rhcl3-anhydrous']);
  assert.match(source, /molecule\.cid === 24872/);
  assert.match(source, /rhodium-trichloride-cod-1534198\.cif/);
});
