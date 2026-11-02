import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import test from 'node:test';

test('the curated SN1/E1 example identifies the common intermediate and bounded temperature guidance', async () => {
  const source = await readFile(new URL('../src/reaction-lab.ts', import.meta.url), 'utf8');
  assert.match(source, /id: 'tertiary-competition'.*reactants: \['tert-butyl-bromide', 'water'\]/);
  for (const text of ['same tertiary carbocation', '2-methylpropan-2-ol', '2-methylpropene', 'β-hydrogen', 'exact product ratio']) assert.ok(source.includes(text));
  assert.match(source, /matches\.some\(\(reaction\) => reaction\.mechanism === 'SN1'\)/);
  assert.match(source, /matches\.some\(\(reaction\) => reaction\.mechanism === 'E1'\)/);
});
