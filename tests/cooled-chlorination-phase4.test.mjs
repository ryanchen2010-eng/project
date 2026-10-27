/** Cooling Phase 4 v1: conditional Cl2 arithmetic is not cooled 3D approval. */
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const root=fileURLToPath(new URL('../',import.meta.url));
async function load(path){
  const source=await readFile(new URL(`../${path}`,import.meta.url),'utf8');
  const output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(output).toString('base64')}`);
}
const {conditionNextStep,conditionGuidance,REVIEWED_COOLING_MODELS}=await load('src/reaction-conditions.ts');
const {calculateReaction,calculateRequiredAmounts,copyCalculationContext}=await load('src/reaction-calculator.ts');
const rows=JSON.parse(execFileSync(`${root}.venv/bin/python`,['-c',`
import json
from server import chemistry_server as s
rows=[]
for source,mass in [('C=C',28.054),('C=CCCCC',84.162),('C/C=C/C',56.108),('C/C=C\\\\C',56.108),('C1=CCCCC1',82.146)]:
 for reverse in [False,True]:
  a,b={'smiles':source},'chlorine'
  if reverse:a,b=b,a
  for temp in ['cooled','ambient']:
   settings={'temperature':temp,'solvent':'dry','catalyst':'none'}
   options=[r for r in s.match_reactions(a,b,settings)['reactionOptions'] if r['mechanism']=='Chlorination']
   rows.append(dict(source=source,mass=mass,reverse=reverse,temp=temp,options=options))
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);

for(const f of rows.filter(r=>r.temp==='cooled')){
  test(`phase4 conditional Cl2: ${f.source}, reverse=${f.reverse}`,()=>{
    const ordinary=rows.find(r=>r.source===f.source&&r.reverse===f.reverse&&r.temp==='ambient');
    assert.ok(f.options.length>0);
    for(const o of f.options){
      const d=o.stoichiometry,substrate=f.reverse?1:0,chlorine=1-substrate;
      assert.equal(o.assessment.canRun,false);assert.equal(o.assessment.evidence.canPreview2D,true);
      assert.equal(d.context.canGenerate3D,false);assert.equal(d.context.conditions.temperature,'cooled');
      assert.equal(o.guidedConditions,undefined);
      assert.match(conditionNextStep(o.assessment),/3D stays unavailable/);
      assert.doesNotMatch(conditionNextStep(o.assessment),/^Supported cooled|View the theoretical 3D/);
      const guidance=conditionGuidance(o.assessment);
      assert.match(guidance,/No current dropdown combination qualifies cooled Cl2 3D/);
      assert.match(guidance,/chloride additives, light or atmosphere/);
      assert.match(guidance,/not proof that radical or substitution chemistry is absent/);
      assert.match(guidance,/do not substitute ambient conditions unless that is the model you intend/);
      assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);assert.equal(d.product.coefficient,1);
      close(d.reactants.find(r=>r.inputSlot===chlorine).molarMass,70.906);
      close(d.product.molarMass,f.mass+70.906);
      const answer=calculateReaction(d,{[substrate]:{value:10,unit:'mmol'},[chlorine]:{value:354.53,unit:'mg'}});
      close(answer.product.moles,0.005);close(answer.product.grams,(f.mass+70.906)*0.005);
      assert.deepEqual(answer.limitingInputs,[chlorine]);
      for(const required of calculateRequiredAmounts(d,{value:2,unit:'mmol'}).reactants)close(required.moles,0.002);
      assert.equal(copyCalculationContext(d.context).canGenerate3D,false);
      assert.match(d.notes.join(' '),/not a predicted or actual yield/);
      assert.match(d.notes.join(' '),/not an amount to add across alternatives/);
      const ambient=ordinary.options.find(r=>r.id===o.id);
      assert.equal(ambient.productSmiles,o.productSmiles);assert.equal(ambient.assessment.canRun,true);
      assert.deepEqual(ambient.chlorinationStereo,o.chlorinationStereo);
    }
  });
}

test('phase4: registry still advertises only the three previously reviewed profiles',()=>{
  assert.equal(REVIEWED_COOLING_MODELS['cooled-alkene-chlorination-v1'],undefined);
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).length,7);
  assert.deepEqual(new Set(Object.values(REVIEWED_COOLING_MODELS).map(p=>p.pathway)),new Set(['Bromination','Epoxidation','Hydrogenation','Alkene dihydroxylation']));
});

test('phase4: a fabricated cooled chlorine profile cannot create positive guidance',()=>{
  const a=structuredClone(rows[0].options[0].assessment);
  a.canRun=true;a.status='model-match';a.coolingUnvalidated=false;a.conditionIssues=[];a.missingSettings=[];
  Object.assign(a.cooling,{modelId:'cooled-alkene-chlorination-v1',status:'supported-model',canGenerate3D:true,profileVersion:1,reasonCodes:[]});
  Object.assign(a.evidence,{canGenerate3D:true,missingRequiredSettings:[],conditionIssues:[]});
  assert.doesNotMatch(conditionNextStep(a),/^Supported cooled|View the theoretical 3D/);
});
