import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const root=fileURLToPath(new URL('../',import.meta.url));
async function load(path){
  const source=await readFile(new URL(`../${path}`,import.meta.url),'utf8');
  return import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText).toString('base64')}`);
}
const {restoreNamedProfile,conditionNextStep}=await load('src/reaction-conditions.ts');
const {copyCalculationContext,calculateReaction}=await load('src/reaction-calculator.ts');
const rows=JSON.parse(execFileSync(`${root}.venv/bin/python`,['-c',`
import json
from server import chemistry_server as s
rows=[]
for a,b,p in [('C=C','bromine','cooled-alkene-bromination-v1'),('C=C',{'smiles':'O=C(OO)c1cccc(Cl)c1'},'cooled-peroxyacid-epoxidation-v1'),('C=Cc1ccccc1',{'smiles':'O=C(OO)c1ccccc1'},'cooled-perbenzoic-epoxidation-v1')]:
 c={'temperature':'cooled','solvent':'dry','catalyst':'none','conditionProfileId':p,'conditionProfileVersion':'1'}
 rows.append(s.match_reactions({'smiles':a},b,c)['reactionOptions'][0])
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8'}));
for(const o of rows){
  test(`R1 selected ${o.assessment.namedConditionProfile.reference.id}: detached context`,()=>{
    const context=o.stoichiometry.context,copy=copyCalculationContext(context);
    assert.deepEqual(copy,context);assert.notEqual(copy.namedConditionProfile,context.namedConditionProfile);
    copy.namedConditionProfile.descriptor.facts.pop();
    assert.equal(context.namedConditionProfile.descriptor.facts.length,7);
    assert.match(conditionNextStep(o.assessment),/^Supported cooled/);
    const a=calculateReaction(o.stoichiometry,{0:{value:1,unit:'mmol'},1:{value:1,unit:'mmol'}});
    assert.equal(a.product.moles,0.001);
    assert.deepEqual(restoreNamedProfile(context.conditions),{conditionProfileId:context.conditions.conditionProfileId,conditionProfileVersion:'1'});
  });
}
test('R1 old drafts remain unchanged; obsolete selection remains explicit for backend reassessment',()=>{
  assert.equal(restoreNamedProfile({temperature:'cooled'}),null);
  assert.deepEqual(restoreNamedProfile({conditionProfileId:'obsolete-v7',conditionProfileVersion:'7'}),{conditionProfileId:'obsolete-v7',conditionProfileVersion:'7'});
  assert.equal(restoreNamedProfile({conditionProfileId:'x',conditionProfileVersion:true}).conditionProfileId,'invalid-restored-profile');
});
for(const key of ['id','pathway','profileVersion']){
  test(`R1 contradictory named descriptor ${key} cannot produce affirmative cooling wording`,()=>{
    const a=structuredClone(rows[0].assessment);a.namedConditionProfile.descriptor[key]='wrong';
    assert.doesNotMatch(conditionNextStep(a),/^Supported cooled/);
    const c=structuredClone(rows[0].stoichiometry.context);c.namedConditionProfile.descriptor[key]='wrong';
    assert.throws(()=>copyCalculationContext(c));
  });
}
test('R1 malformed or oversized named calculation metadata is rejected',()=>{
  for(const value of [null,[],{version:2},{version:1,selection:'explicit',status:'qualified',reference:{id:'x',version:'1'},descriptor:null}]){
    assert.throws(()=>copyCalculationContext({...rows[0].stoichiometry.context,namedConditionProfile:value}));
  }
});
