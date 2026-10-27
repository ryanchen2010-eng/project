/** Cooling Phase 6 v1: one-H2 conditional bookkeeping, not cold conversion. */
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
for source,mass in [('C=C',30.07),('C1=CCCCC1',84.162),('C=CCCCO',88.15),('CC=C(C)CCC',100.205)]:
 for reverse in [False,True]:
  a,b={'smiles':source},'hydrogen'
  if reverse:a,b=b,a
  settings={'temperature':'cooled','solvent':'dry','catalyst':'metal'}
  o=next(o for o in s.match_reactions(a,b,settings)['reactionOptions'] if o['mechanism']=='Hydrogenation')
  ordinary=next(o for o in s.match_reactions(a,b,{**settings,'temperature':'ambient'})['reactionOptions'] if o['mechanism']=='Hydrogenation')
  rows.append(dict(source=source,mass=mass,reverse=reverse,option=o,ordinary=ordinary))
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
assert.equal(rows.length,8);

for(const f of rows){
  test(`phase6 v1 conditional H2: ${f.source}, reverse=${f.reverse}`,()=>{
    const o=f.option,d=o.stoichiometry,substrate=f.reverse?1:0,h2=1-substrate;
    assert.equal(o.assessment.canRun,false);assert.equal(o.assessment.evidence.canPreview2D,true);
    assert.equal(d.context.canGenerate3D,false);assert.equal(d.context.conditions.temperature,'cooled');
    assert.match(conditionNextStep(o.assessment),/3D stays unavailable/);
    assert.match(conditionGuidance(o.assessment),/No current selector combination qualifies cooled alkene-hydrogenation 3D/);
    assert.match(conditionGuidance(o.assessment),/catalyst\/support, solvent or H2 pressure/);
    assert.match(conditionGuidance(o.assessment),/do not substitute ambient conditions unless that is the model you intend/);
    close(d.product.molarMass,f.mass);close(d.reactants.find(r=>r.inputSlot===h2).molarMass,2.016);
    assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);assert.equal(d.product.coefficient,1);
    const answer=calculateReaction(d,{[substrate]:{value:20,unit:'mmol'},[h2]:{value:0.01008,unit:'g'}});
    close(answer.product.moles,0.005);close(answer.product.grams,f.mass*0.005);
    assert.deepEqual(answer.limitingInputs,[h2]);
    const required=calculateRequiredAmounts(d,{value:2,unit:'mmol'});
    for(const r of required.reactants){close(r.moles,0.002);close(r.grams,d.reactants.find(a=>a.inputSlot===r.inputSlot).molarMass*0.002);}
    assert.equal(copyCalculationContext(d.context).canGenerate3D,false);
    assert.match(d.notes.join(' '),/not a predicted or actual yield/);
    assert.match(d.notes.join(' '),/catalyst is not consumed/);
    assert.match(d.context.warning,/not experimental yields/);
    assert.equal(f.ordinary.productSmiles,o.productSmiles);
    assert.notEqual(f.ordinary.assessment.canRun,false); // Actual ambient runs are checked in Python.
    assert.deepEqual(f.ordinary.compatibility,o.compatibility);
    assert.deepEqual(f.ordinary.information.stereochemistry,o.information.stereochemistry);
  });
}

test('phase6: existing cooling profiles cannot advertise H2/metal permission',()=>{
  assert.equal(REVIEWED_COOLING_MODELS['cooled-alkene-hydrogenation-v1'],undefined);
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).length,7);
  assert.deepEqual(new Set(Object.values(REVIEWED_COOLING_MODELS).map(p=>p.pathway)),new Set(['Bromination','Epoxidation','Hydrogenation','Alkene dihydroxylation']));
});

test('phase6: forged hydrogenation profile cannot produce positive cooling guidance',()=>{
  const a=structuredClone(rows[0].option.assessment);
  a.canRun=true;a.status='model-match';a.coolingUnvalidated=false;a.conditionIssues=[];a.missingSettings=[];
  Object.assign(a.cooling,{modelId:'cooled-alkene-hydrogenation-v1',status:'supported-model',canGenerate3D:true,profileVersion:1,reasonCodes:[]});
  Object.assign(a.evidence,{canGenerate3D:true,missingRequiredSettings:[],conditionIssues:[]});
  assert.doesNotMatch(conditionNextStep(a),/^Supported cooled|View the theoretical 3D/);
});
