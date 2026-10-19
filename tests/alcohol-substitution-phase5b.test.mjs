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
const {rows,controls}=JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python',import.meta.url)),['-c',`
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/alcohol-substitution-phase5b.json').read_text());rows=[];controls=[]
for case in f['positive']:
 for symbol,reagent in [('Br','hydrogen-bromide'),('I','hydrogen-iodide')]+([('Cl','hydrogen-chloride')] if case.get('chloride') else []):
  for reverse in [False,True]:
   a,b={'smiles':case['substrate']},reagent
   if reverse:a,b=b,a
   for r in s.match_reactions(a,b,{'temperature':case['temperature']})['reactionOptions']:
    if r['mechanism']=='Alcohol substitution':rows.append(dict(case=case,symbol=symbol,reverse=reverse,reaction=r))
for c in [{},{'temperature':'ambient'},{'temperature':'heated','peroxide':True},{'temperature':'heated','catalyst':'acid'},{'temperature':'heated','solvent':'dry'}]:
 r=next(o for o in s.match_reactions('ethanol','hydrogen-bromide',c)['reactionOptions'] if o['mechanism']=='Alcohol substitution');controls.append(dict(conditions=c,reaction=r))
print(json.dumps(dict(rows=rows,controls=controls)))
`],{cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);

for(const {case:c,symbol,reverse,reaction:r} of rows){
 test(`HX amounts: ${c.label}, ${symbol}, reverse=${reverse}, ${r.site.siteId}`,()=>{
  const data=r.stoichiometry,context=copyCalculationContext(data.context);
  assert.equal(data.reactants.length,2);assert.deepEqual(data.excludedInputs,[]);
  const alcoholSlot=reverse?1:0,hxSlot=reverse?0:1;
  const alcohol=data.reactants.find(a=>a.inputSlot===alcoholSlot),hx=data.reactants.find(a=>a.inputSlot===hxSlot);
  const X={Cl:35.453,Br:79.904,I:126.904}[symbol];
  // Independent literal C/H/O/X formulas: all fixtures are acyclic saturated
  // graphs, except the two explicitly phenyl-containing (DBE 4) substrates.
  const carbons=(c.substrate.match(/[Cc]/g)??[]).length,oxygens=(c.substrate.match(/O/g)??[]).length;
  const rings=(c.substrate.match(/c/g)??[]).length/6,hydrogens=2*carbons+2-8*rings;
  close(alcohol.molarMass,carbons*12.011+hydrogens*1.008+oxygens*15.999);
  close(data.product.molarMass,carbons*12.011+(hydrogens-1)*1.008+(oxygens-1)*15.999+X);
  close(hx.molarMass,X+1.008);close(data.product.molarMass,alcohol.molarMass+X-17.007);
  const result=calculateReaction(data,{[alcoholSlot]:{value:4,unit:'mmol'},[hxSlot]:{value:X+1.008,unit:'mg'}});
  close(result.product.moles,0.001);close(result.product.grams,data.product.molarMass*0.001);
  assert.deepEqual(result.limitingInputs,[hxSlot]);
  const required=calculateRequiredAmounts(data,{value:data.product.molarMass*0.002,unit:'g'});
  assert.equal(required.reactants.length,2);required.reactants.forEach(a=>close(a.moles,0.002));
  const noHX=calculateReaction(data,{[alcoholSlot]:{value:1,unit:'mol'},[hxSlot]:{value:0,unit:'mol'}});
  close(noHX.product.moles,0);
  assert.equal(context.canGenerate3D,c.allow3D);assert.equal(context.canGenerate3D,r.assessment.evidence.canGenerate3D);
  assert.match(context.warning,/HX is consumed/);assert.match(context.warning,/not additive yields/);
  assert.match(conditionGuidance(r.assessment),/Structure\/site supported/);
  if(!c.allow3D)assert.match(conditionLabel(r.assessment),/conditional 2D only/);
 });
}
for(const {conditions,reaction:r}of controls){
 test(`HX calculation confidence cannot override conditions: ${JSON.stringify(conditions)}`,()=>{
  const context=copyCalculationContext(r.stoichiometry.context);
  assert.equal(context.canGenerate3D,false);assert.match(conditionGuidance(r.assessment),/Conditional 2D remains available/);
  assert.match(context.warning,/not experimental yields/);
  if(!conditions.temperature)assert.match(conditionGuidance(r.assessment),/Missing: temperature/);
  if(conditions.peroxide)assert.match(r.assessment.note,/peroxide/);
 });
}
test('HX uses existing controls and calculator context without a new layout',async()=>{
 const source=await read('src/reaction-lab.ts');
 assert.match(source,/if \(reaction\.mechanism === 'Alcohol substitution'\) conditionAssessment\.textContent \+= ` — \$\{conditionGuidance/);
 assert.match(source,/assessment\?\.canRun !== false/);
 assert.match(source,/reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
});
