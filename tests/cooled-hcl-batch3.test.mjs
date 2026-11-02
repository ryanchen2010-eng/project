import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const root=fileURLToPath(new URL('../',import.meta.url));
const load=async path=>{const source=await readFile(new URL(`../${path}`,import.meta.url),'utf8');const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;return import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`)};
const {guidedControlValues}=await load('src/guided-reaction-conditions.ts');
const {conditionGuidance,restoreNamedProfile}=await load('src/reaction-conditions.ts');
const {calculateReaction,copyCalculationContext}=await load('src/reaction-calculator.ts');
const model='cooled-isobutylene-hcl-v1';
const rows=JSON.parse(execFileSync(`${root}.venv/bin/python`,['-c',`
import json
from server import chemistry_server as s
c={'temperature':'cooled','solvent':'dry','catalyst':'none','conditionProfileId':'${model}','conditionProfileVersion':'1'}
rows={}
for name,conditions in [('qualified',c),('generic',{k:v for k,v in c.items() if not k.startswith('conditionProfile')}),('ambient',{**c,'temperature':'ambient'})]:
 rows[name]=next(o for o in s.match_reactions({'smiles':'C=C(C)C'},'hydrogen-chloride',conditions)['reactionOptions'] if o['mechanism']=='Hydrohalogenation')
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8'}));

test('reference guide requires confirmation and transports only authorized controls',()=>{
 const guide=rows.generic.guidedConditions; assert.equal(guide.requireConfirmation,true);
 assert.deepEqual(guidedControlValues(guide),{solvent:'dry',catalyst:'none',conditionProfileId:model,conditionProfileVersion:'1'});
 for(const extra of [{temperature:'cooled'},{pressure:'1 atm'},{solvent:'aqueous-protic'},{conditionProfileVersion:'2'}]) assert.throws(()=>guidedControlValues({...guide,targetConditions:{...guide.targetConditions,...extra}}));
});
test('reference provenance and calculator remain theoretical',()=>{
 const o=rows.qualified; assert.equal(o.assessment.canRun,true);assert.match(conditionGuidance(o.assessment),/theoretical/);
 const c=copyCalculationContext(o.stoichiometry.context);assert.equal(c.canGenerate3D,true);assert.match(c.warning,/not experimental yields/);
 assert.deepEqual(restoreNamedProfile(c.conditions),{conditionProfileId:model,conditionProfileVersion:'1'});
 const amount=calculateReaction(o.stoichiometry,{0:{value:1,unit:'mmol'},1:{value:1,unit:'mmol'}});
 assert.ok(Math.abs(amount.product.moles-0.001)<1e-12);
 assert.equal(rows.ambient.assessment.canRun,false);
});
