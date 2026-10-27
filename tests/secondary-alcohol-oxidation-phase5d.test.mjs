import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const read=p=>readFile(new URL(`../${p}`,import.meta.url),'utf8');
const compile=s=>ts.transpileModule(s,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const load=async p=>import(`data:text/javascript;base64,${Buffer.from(compile(await read(p))).toString('base64')}`);
const {calculateReaction,calculateRequiredAmounts,copyCalculationContext}=await load('src/reaction-calculator.ts');
const {conditionLabel,conditionGuidance}=await load('src/reaction-conditions.ts');
const {rows,controls}=JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python',import.meta.url)),['-c',`
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/secondary-alcohol-oxidation-phase5d.json').read_text());rows=[]
for case in f['positive']:
 for metal in ['Na','K']:
  for reverse in [False,True]:
   a,b={'smiles':case['substrate']},{'smiles':f'[{metal}+].[O-]Cl'}
   if reverse:a,b=b,a
   found=[r for r in s.match_reactions(a,b,f['profile'])['reactionOptions'] if r.get('secondaryOxidationModel')]
   rows.append(dict(case=case,metal=metal,reverse=reverse,options=found))
controls=[]
for c in [{},{'solvent':'aqueous-protic','oxidationStage':'first'},{**f['profile'],'temperature':'heated'},{**f['profile'],'oxidant':'PCC'},{**f['profile'],'workup':'aqueous-release'}]:
 r=next(r for r in s.match_reactions('2-propanol','sodium-hypochlorite',c)['reactionOptions'] if r.get('secondaryOxidationModel'));controls.append(dict(conditions=c,reaction=r))
print(json.dumps(dict(rows=rows,controls=controls)))
`],{cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8',maxBuffer:16*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
for(const {case:c,metal,reverse,options} of rows){
 test(`secondary ketone calculator: ${c.label}, ${metal}, reverse=${reverse}`,()=>{
  assert.ok(options.length);
  const carbons=(c.substrate.match(/[Cc]/g)??[]).length,oxygens=(c.substrate.match(/O/g)??[]).length;
  const rings=(c.substrate.match(/\d/g)??[]).length/2,phenyl=(c.substrate.match(/c/g)??[]).length/6;
  const H=2*carbons+2-2*rings-6*phenyl,sourceMass=carbons*12.011+H*1.008+oxygens*15.999;
  const productMass=sourceMass-2*1.008,oxidantMass={Na:22.990,K:39.098}[metal]+35.453+15.999;
  for(const r of options){
   const data=r.stoichiometry,context=copyCalculationContext(data.context),a=reverse?1:0,b=1-a;
   close(data.product.molarMass,productMass);close(data.reactants.find(x=>x.inputSlot===a).molarMass,sourceMass);
   close(data.reactants.find(x=>x.inputSlot===b).molarMass,oxidantMass);assert.deepEqual(data.reactants.map(x=>x.coefficient),[1,1]);assert.deepEqual(data.excludedInputs,[]);
   const result=calculateReaction(data,{[a]:{value:5,unit:'mmol'},[b]:{value:oxidantMass,unit:'mg'}});
   close(result.product.moles,0.001);close(result.product.grams,productMass*0.001);assert.deepEqual(result.limitingInputs,[b]);
   const required=calculateRequiredAmounts(data,{value:productMass*0.002,unit:'g'});required.reactants.forEach(x=>close(x.moles,0.002));
   close(calculateReaction(data,{[a]:{value:1,unit:'mol'},[b]:{value:0,unit:'mol'}}).product.moles,0);
   const allowed=c.qualified&&metal==='Na';assert.equal(context.canGenerate3D,allowed);assert.equal(r.assessment.evidence.conditionCompleteEligibility,allowed);
   assert.equal(context.conditions.secondaryOxidationProfile,'naocl-acetic-ketone-v1');assert.match(context.warning,/Full salt mass/);assert.match(context.warning,/No H2 gas/);assert.match(context.warning,/not predicted/);
   assert.match(context.warning,/not a consumed third reactant/);assert.match(context.warning,/not a laboratory procedure/);
   assert.match(conditionLabel(r.assessment),allowed?/theoretical 3D/:/conditional 2D only/);
   assert.match(conditionGuidance(r.assessment),/not measured exposure/);
  }
 });
}
for(const {conditions,reaction:r}of controls){
 test(`secondary calculation does not certify conditions: ${JSON.stringify(conditions)}`,()=>{
  const context=copyCalculationContext(r.stoichiometry.context);assert.equal(context.canGenerate3D,false);
  assert.match(conditionGuidance(r.assessment),/Conditional 2D remains available/);
  if(!conditions.secondaryOxidationProfile)assert.match(conditionGuidance(r.assessment),/secondary NaOCl\/acetic-acid medium profile/);
  assert.doesNotMatch(conditionLabel(r.assessment),/Unfavorable/);
 });
}
test('existing medium control serializes an explicit namespaced profile, never a default',async()=>{
 const source=await read('src/reaction-lab.ts'),start=source.indexOf('function currentConditions()');
 const fn=compile(source.slice(start,source.indexOf('\n}',start)+2));
 const names=['solventInput','temperatureInput','catalystInput','oxidationStageInput','additionStageInput','polymerUnitsInput','workupInput'];
 const run=new Function(...names,`const namedProfileSelection=null; ${fn}; return currentConditions();`);
 const values=['secondary-naocl-acetic','ambient','none','first','one','4',''];
 const result=run(...values.map(value=>({value})));
 assert.equal(result.solvent,'aqueous-protic');assert.equal(result.secondaryOxidationProfile,'naocl-acetic-ketone-v1');
 for(const solvent of ['','dry','aqueous-protic','polar-aprotic','ethanolic-protic']){
  const normal=run(...[solvent,...values.slice(1)].map(value=>({value})));
  assert.equal(normal.solvent,solvent);assert.equal(Object.hasOwn(normal,'secondaryOxidationProfile'),false);
 }
 assert.match(source,/draft\.conditions\?\.secondaryOxidationProfile === 'naocl-acetic-ketone-v1'/);
});
test('secondary blocked atom inspection does not describe an aldehyde',async()=>{
 const source=await read('src/reaction-lab.ts');
 assert.match(source,/reaction\.secondaryOxidationModel \? 'Conditional 2D only; secondary ketone profile unresolved\.'/);
 assert.match(source,/assessment\?\.canRun !== false/);assert.match(source,/reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
});
