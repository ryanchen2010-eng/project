import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
const source = await readFile(new URL('../src/thermochemistry.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const { heat, reactionChange, gibbs, classifyEnthalpy } = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
test('specific and total heat handle heating and cooling', () => { assert.equal(heat(100,4.184,10,true),4184); assert.equal(heat(0,500,-5,false),-2500); assert.throws(() => heat(0,4,10,true)); });
test('stoichiometric enthalpy and entropy include negative values and zero', () => { const rows = [{side:'reactant',coefficient:2,value:0},{side:'reactant',coefficient:1,value:0},{side:'product',coefficient:2,value:-285.8}]; assert.ok(Math.abs(reactionChange(rows)+571.6)<1e-9); assert.equal(classifyEnthalpy(reactionChange(rows)),'Exothermic'); assert.equal(classifyEnthalpy(0),'Neither (ΔH = 0)'); assert.equal(reactionChange([{side:'reactant',coefficient:2,value:10},{side:'product',coefficient:1,value:50}]),30); });
test('missing species, invalid coefficients and nonfinite values fail closed', () => { assert.throws(() => reactionChange([])); assert.throws(() => reactionChange([{side:'product',coefficient:0,value:3},{side:'reactant',coefficient:1,value:1}])); assert.throws(() => gibbs(1,NaN,298)); assert.throws(() => gibbs(1,10,0)); });
test('Gibbs converts entropy J to kJ and keeps standard-state interpretation separate', () => { assert.equal(gibbs(10,100,300),-20); assert.equal(gibbs(-20,-100,300),10); });
test('independently worked H2 + Cl2 → 2 HCl and reversed equation', () => {
  const forward = [{side:'reactant',coefficient:1,value:0},{side:'reactant',coefficient:1,value:0},{side:'product',coefficient:2,value:-92.3}];
  assert.ok(Math.abs(reactionChange(forward) + 184.6) < 1e-10);
  assert.ok(Math.abs(reactionChange(forward.map(r => ({...r,side:r.side === 'product' ? 'reactant' : 'product'}))) - 184.6) < 1e-10);
});
test('zero heat and fractional stoichiometric coefficients are handled', () => {
  assert.equal(heat(100,4.184,0,true), 0);
  assert.equal(reactionChange([{side:'reactant',coefficient:0.5,value:100},{side:'product',coefficient:1,value:90}]),40);
  assert.throws(() => reactionChange([{side:'reactant',coefficient:1,value:1},{side:'product',coefficient:1,value:1},{side:'other',coefficient:1,value:2}]));
});
