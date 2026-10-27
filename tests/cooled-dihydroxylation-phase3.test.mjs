/** Phase 3 evidence gate: conditional arithmetic never approves cooled 3D. */
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
for source,c,h in [('C=C',2,4),('C=C(C)C',4,8),('C=C(CC)CC',6,12),('CC(C)=C(C)C',6,12)]:
 for reverse in [False,True]:
  a,b={'smiles':source},'hydrogen-peroxide'
  if reverse:a,b=b,a
  for temp in ['cooled','ambient']:
   settings={'temperature':temp,'solvent':'dry','catalyst':'osmium','workup':'aqueous-release'}
   option=next(r for r in s.match_reactions(a,b,settings)['reactionOptions'] if r['mechanism']=='Alkene dihydroxylation')
   rows.append(dict(source=source,c=c,h=h,reverse=reverse,temp=temp,option=option))
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);

for(const f of rows.filter(r=>r.temp==='cooled')){
  test(`phase3 deferred cooling: ${f.source}, reverse=${f.reverse}`,()=>{
    const o=f.option,d=o.stoichiometry,substrate=f.reverse?1:0,peroxide=1-substrate,mass=f.c*12.011+f.h*1.008;
    assert.equal(o.assessment.canRun,false);assert.equal(o.assessment.evidence.canPreview2D,true);
    assert.equal(d.context.canGenerate3D,false);assert.equal(d.context.conditions.temperature,'cooled');
    if(f.source==='C=C(C)C'){
      assert.equal(o.guidedConditions.profileId,'cooled-isobutylene-os-peroxide-v1');
      assert.equal(o.guidedConditions.requireConfirmation,true);
    }else assert.equal(o.guidedConditions,undefined);
    assert.match(conditionNextStep(o.assessment),/3D stays unavailable/);
    assert.doesNotMatch(conditionNextStep(o.assessment),/^Supported cooled|View the theoretical 3D/);
    assert.match(conditionGuidance(o.assessment),/No generic cooled Os\/H2O2 profile is reviewed/);
    assert.match(conditionGuidance(o.assessment),/not mean the reaction is impossible/);
    assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);assert.equal(d.product.coefficient,1);
    close(d.reactants.find(r=>r.inputSlot===peroxide).molarMass,34.014);
    close(d.product.molarMass,mass+34.014);
    const answer=calculateReaction(d,{[substrate]:{value:10,unit:'mmol'},[peroxide]:{value:170.07,unit:'mg'}});
    close(answer.product.moles,0.005);close(answer.product.grams,(mass+34.014)*0.005);
    assert.deepEqual(answer.limitingInputs,[peroxide]);
    for(const required of calculateRequiredAmounts(d,{value:2,unit:'mmol'}).reactants)close(required.moles,0.002);
    assert.equal(copyCalculationContext(d.context).canGenerate3D,false);
    assert.match(d.notes.join(' '),/Formal O\/H maps are not catalyst oxygen\/proton-exchange provenance/);
    const ordinary=rows.find(r=>r.source===f.source&&r.reverse===f.reverse&&r.temp==='ambient').option;
    assert.equal(ordinary.productSmiles,o.productSmiles);
    assert.equal(ordinary.assessment.canRun,true);
    assert.deepEqual(ordinary.dihydroxylationStereo,o.dihydroxylationStereo);
  });
}

test('phase3: no candidate or third reaction type is advertised before evidence approval',()=>{
  assert.equal(REVIEWED_COOLING_MODELS['cooled-osmium-peroxide-diol-v1'],undefined);
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).length,7);
  assert.deepEqual(new Set(Object.values(REVIEWED_COOLING_MODELS).map(p=>p.pathway)),new Set(['Bromination','Epoxidation','Hydrogenation','Alkene dihydroxylation']));
});

test('phase3: a fabricated candidate profile cannot create positive cooled guidance',()=>{
  const a=structuredClone(rows[0].option.assessment);
  a.canRun=true;a.status='model-match';a.coolingUnvalidated=false;a.conditionIssues=[];a.missingSettings=[];
  Object.assign(a.cooling,{modelId:'cooled-osmium-peroxide-diol-v1',status:'supported-model',canGenerate3D:true,profileVersion:1,reasonCodes:[]});
  Object.assign(a.evidence,{canGenerate3D:true,missingRequiredSettings:[],conditionIssues:[]});
  const before=structuredClone(a);
  assert.doesNotMatch(conditionNextStep(a),/^Supported cooled|View the theoretical 3D/);
  assert.deepEqual(a,before);
});
