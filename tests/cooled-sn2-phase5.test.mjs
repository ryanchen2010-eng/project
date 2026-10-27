/** Cooling Phase 5 v1: actual-OH bookkeeping does not approve cooled SN2 3D. */
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
for source,mass in [('CBr',32.042),('CI',32.042),('C[C@H](Br)CC',74.123)]:
 for reagent,name,molar in [('hydroxide','OH',17.007),('sodium-hydroxide','NaOH',39.997),({'smiles':'[K+].[OH-]'},'KOH',56.105)]:
  for reverse in [False,True]:
   a,b={'smiles':source},reagent
   if reverse:a,b=b,a
   settings={'temperature':'cooled','solvent':'polar-aprotic','catalyst':'none'}
   options=[r for r in s.match_reactions(a,b,settings)['reactionOptions'] if r['mechanism']=='SN2']
   ordinary=[r for r in s.match_reactions(a,b,{**settings,'temperature':'ambient'})['reactionOptions'] if r['mechanism']=='SN2']
   rows.append(dict(source=source,mass=mass,reagent=name,molar=molar,reverse=reverse,option=options[0],ordinary=ordinary[0]))
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
assert.equal(rows.length,18);

for(const f of rows){
  test(`phase5 conditional SN2: ${f.source}, ${f.reagent}, reverse=${f.reverse}`,()=>{
    const o=f.option,d=o.stoichiometry,substrate=f.reverse?1:0,hydroxide=1-substrate;
    assert.equal(o.assessment.canRun,false);assert.equal(o.assessment.evidence.canPreview2D,true);
    assert.equal(d.context.canGenerate3D,false);assert.equal(d.context.conditions.temperature,'cooled');
    assert.equal(o.guidedConditions,undefined);
    assert.match(conditionNextStep(o.assessment),/3D stays unavailable/);
    assert.doesNotMatch(conditionNextStep(o.assessment),/^Supported cooled|View the theoretical 3D/);
    assert.match(conditionGuidance(o.assessment),/No current selector combination qualifies cooled SN2 3D/);
    assert.match(conditionGuidance(o.assessment),/aqueous phosphate buffers/);
    assert.match(conditionGuidance(o.assessment),/do not substitute ambient conditions unless that is the model you intend/);
    close(d.product.molarMass,f.mass);
    close(d.reactants.find(r=>r.inputSlot===hydroxide).molarMass,f.molar);
    assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);assert.equal(d.product.coefficient,1);
    const answer=calculateReaction(d,{[substrate]:{value:20,unit:'mmol'},[hydroxide]:{value:f.molar*0.005,unit:'g'}});
    close(answer.product.moles,0.005);close(answer.product.grams,f.mass*0.005);
    assert.deepEqual(answer.limitingInputs,[hydroxide]);
    const required=calculateRequiredAmounts(d,{value:2,unit:'mmol'});
    for(const r of required.reactants){close(r.moles,0.002);close(r.grams,d.reactants.find(a=>a.inputSlot===r.inputSlot).molarMass*0.002);}
    assert.equal(copyCalculationContext(d.context).canGenerate3D,false);
    assert.match(d.notes.join(' '),/not a predicted or actual yield/);
    if(f.reagent!=='OH')assert.match(d.notes.join(' '),/full salt molar mass/);
    assert.equal(f.ordinary.productSmiles,o.productSmiles);
    // Legacy non-cooled SN2 responses omit canRun; Python checks actual 3D runs.
    assert.notEqual(f.ordinary.assessment.canRun,false);
    assert.deepEqual(f.ordinary.compatibility,o.compatibility);
    assert.deepEqual(f.ordinary.information.stereochemistry,o.information.stereochemistry);
  });
}

test('phase5: reviewed profiles do not advertise hydroxide, water-solvolysis or elimination cooling',()=>{
  assert.equal(REVIEWED_COOLING_MODELS['cooled-hydroxide-sn2-v1'],undefined);
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).length,7);
  assert.deepEqual(new Set(Object.values(REVIEWED_COOLING_MODELS).map(p=>p.pathway)),new Set(['Bromination','Epoxidation','Hydrogenation','Alkene dihydroxylation']));
});

test('phase5: fabricated SN2 metadata cannot become positive cooling guidance',()=>{
  const a=structuredClone(rows[0].option.assessment);
  a.canRun=true;a.status='model-match';a.coolingUnvalidated=false;a.conditionIssues=[];a.missingSettings=[];
  Object.assign(a.cooling,{modelId:'cooled-hydroxide-sn2-v1',status:'supported-model',canGenerate3D:true,profileVersion:1,reasonCodes:[]});
  Object.assign(a.evidence,{canGenerate3D:true,missingRequiredSettings:[],conditionIssues:[]});
  assert.doesNotMatch(conditionNextStep(a),/^Supported cooled|View the theoretical 3D/);
});
