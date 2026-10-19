import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const read=p=>readFile(new URL(`../${p}`,import.meta.url),'utf8');
const load=async p=>import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(await read(p),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64')}`);
const {calculateReaction,calculateRequiredAmounts,copyCalculationContext}=await load('src/reaction-calculator.ts');
const {conditionLabel,conditionGuidance}=await load('src/reaction-conditions.ts');
const rows=JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python',import.meta.url)),['-c',`
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/primary-alcohol-oxidation-phase5c.json').read_text());rows=[]
for case in f['positive']:
 for symbol in ['Na','K']:
  for reverse in [False,True]:
   a,b={'smiles':case['substrate']},{'smiles':f'[{symbol}+].[O-]Cl'}
   if reverse:a,b=b,a
   options=[r for r in s.match_reactions(a,b,f['conditions'])['reactionOptions'] if r.get('primaryOxidationModel')]
   rows.append(dict(case=case,symbol=symbol,reverse=reverse,options=options))
print(json.dumps(rows))
`],{cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
for(const {case:c,symbol,reverse,options} of rows){
 test(`primary oxidation formal calculator: ${c.label}, ${symbol}, reverse=${reverse}`,()=>{
  assert.ok(options.length);
  // These literal fixtures contain saturated acyclic/ring and phenyl CHO
  // structures only. Independent atom/unsaturation count, not engine formula.
  const carbons=(c.substrate.match(/[Cc]/g)??[]).length,oxygens=(c.substrate.match(/O/g)??[]).length;
  const rings=(c.substrate.match(/\d/g)??[]).length/2,phenyl=(c.substrate.match(/c/g)??[]).length/6;
  const hydrogens=2*carbons+2-2*rings-6*phenyl;
  const sourceMass=carbons*12.011+hydrogens*1.008+oxygens*15.999;
  const productMass=sourceMass-2*1.008,metal={Na:22.990,K:39.098}[symbol];
  const oxidantMass=metal+35.453+15.999;
  for(const r of options){
   const data=r.stoichiometry,context=copyCalculationContext(data.context),alcoholSlot=reverse?1:0,oxidantSlot=1-alcoholSlot;
   close(data.product.molarMass,productMass);
   close(data.reactants.find(a=>a.inputSlot===alcoholSlot).molarMass,sourceMass);
   close(data.reactants.find(a=>a.inputSlot===oxidantSlot).molarMass,oxidantMass);
   assert.deepEqual(data.reactants.map(a=>a.coefficient),[1,1]);assert.deepEqual(data.excludedInputs,[]);
   const result=calculateReaction(data,{[alcoholSlot]:{value:5,unit:'mmol'},[oxidantSlot]:{value:oxidantMass,unit:'mg'}});
   close(result.product.moles,0.001);close(result.product.grams,productMass*0.001);assert.deepEqual(result.limitingInputs,[oxidantSlot]);
   const required=calculateRequiredAmounts(data,{value:productMass*0.002,unit:'g'});
   required.reactants.forEach(a=>close(a.moles,0.002));
   close(calculateReaction(data,{[alcoholSlot]:{value:1,unit:'mol'},[oxidantSlot]:{value:0,unit:'mol'}}).product.moles,0);
   assert.equal(context.canGenerate3D,false);assert.equal(r.assessment.evidence.conditionCompleteEligibility,false);
   assert.match(context.warning,/not an isolated aldehyde yield/);assert.match(context.warning,/No H2 gas/);
   assert.match(conditionLabel(r.assessment),/conditional 2D only/);
   assert.match(conditionGuidance(r.assessment),/No aldehyde-selective/);
   assert.match(conditionGuidance(r.assessment),/no existing selector completes one/i);
  }
 });
}
test('primary-only guidance uses existing layout, gating and calculator context',async()=>{
 const source=await read('src/reaction-lab.ts');
 assert.match(source,/reaction\.mechanism === 'Alcohol oxidation' && reaction\.assessment\?\.evidence/);
 assert.match(source,/assessment\?\.canRun !== false/);
 assert.match(source,/reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
});
