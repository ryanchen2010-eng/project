/** Batch 1 R2 v1: exact reference transport; never a yield/temperature model. */
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const root=fileURLToPath(new URL('../',import.meta.url));
const read=path=>readFile(new URL(`../${path}`,import.meta.url),'utf8');
const compile=source=>ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const load=async path=>import(`data:text/javascript;base64,${Buffer.from(compile(await read(path))).toString('base64')}`);
const {conditionNextStep,conditionGuidance,restoreNamedProfile}=await load('src/reaction-conditions.ts');
const {calculateReaction,calculateRequiredAmounts,copyCalculationContext}=await load('src/reaction-calculator.ts');
const {guidedControlValues,GuidedConditionsPanel}=await load('src/guided-reaction-conditions.ts');
const source=await read('src/reaction-lab.ts');
const MODEL='cooled-cyclohexene-pd-silica-v1';
const rows=JSON.parse(execFileSync(`${root}.venv/bin/python`,['-c',`
import json
from server import chemistry_server as s
c={'temperature':'cooled','solvent':'dry','catalyst':'metal','conditionProfileId':'${MODEL}','conditionProfileVersion':'1'}
rows={}
for name,conditions in [('qualified',c),('generic',{k:v for k,v in c.items() if not k.startswith('conditionProfile')}),('unknown',{**c,'conditionProfileVersion':'2'}),('ambient',{**c,'temperature':'ambient'}),('water',{**c,'solvent':'aqueous-protic'})]:
 rows[name]=next(o for o in s.match_reactions({'smiles':'C1=CCCCC1'},'hydrogen',conditions)['reactionOptions'] if o['mechanism']=='Hydrogenation')
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);

test('R2 v1 exact selected profile carries detached provenance and theoretical-only confidence',()=>{
  const o=rows.qualified,c=copyCalculationContext(o.stoichiometry.context);
  assert.equal(o.assessment.canRun,true);assert.equal(c.canGenerate3D,true);
  assert.deepEqual(c.namedConditionProfile.reference,{id:MODEL,version:'1'});
  assert.notEqual(c.namedConditionProfile,o.stoichiometry.context.namedConditionProfile);
  assert.match(conditionNextStep(o.assessment),/^Supported cooled/);
  assert.match(conditionGuidance(o.assessment),/theoretical product conformer/);
  const facts=c.namedConditionProfile.descriptor.facts;
  assert.equal(facts.find(f=>f.field==='medium').value,'hexane');
  assert.equal(facts.find(f=>f.field==='hydrogenPressure').value.basis,'not stated');
});
test('R2 v1 one-H2 arithmetic never adopts the source partial-conversion endpoint',()=>{
  const d=rows.qualified.stoichiometry;
  const answer=calculateReaction(d,{0:{value:1,unit:'mmol'},1:{value:1,unit:'mmol'}});
  close(answer.product.moles,0.001);close(answer.product.grams,0.084162);
  const required=calculateRequiredAmounts(d,{value:1,unit:'mmol'});
  close(required.reactants.find(r=>r.inputSlot===1).grams,0.002016);
  assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);
  assert.match(d.context.warning,/not experimental yields/);
});
test('R2 v1 generic, obsolete, thermal and medium conflicts retain 2D-only confidence',()=>{
  for(const key of ['generic','unknown','ambient','water']){
    const o=rows[key];assert.equal(o.assessment.canRun,false,key);
    assert.doesNotMatch(conditionNextStep(o.assessment),/^Supported cooled/,key);
    assert.equal(o.assessment.evidence.canGenerate3D,false,key);
    if(o.stoichiometry.context)assert.equal(copyCalculationContext(o.stoichiometry.context).canGenerate3D,false);
  }
});
test('R2 v1 explicit calculation input version must agree with profile reference',()=>{
  const c=structuredClone(rows.qualified.stoichiometry.context);c.conditions.conditionProfileVersion='2';
  assert.throws(()=>copyCalculationContext(c),/conflicts/);
});
test('R2 v1 guide selects only the fixed identity, never temperature, pressure or arbitrary facts',()=>{
  const g=rows.generic.guidedConditions,values=guidedControlValues(g);
  assert.deepEqual(values,{solvent:'dry',catalyst:'metal',conditionProfileId:MODEL,conditionProfileVersion:'1'});
  for(const extra of [{temperature:'cooled'},{pressureMPa:'1.1'},{catalyst:'lindlar'},{conditionProfileVersion:'2'},{conditionProfileId:'cooled-cyclohexene-pd-c-v1'}]){
    assert.throws(()=>guidedControlValues({...g,targetConditions:{...g.targetConditions,...extra}}));
  }
});
test('R2 v1 restore retains exact/obsolete selections for backend revalidation, never implicit fallback',()=>{
  assert.deepEqual(restoreNamedProfile(rows.qualified.stoichiometry.context.conditions),{conditionProfileId:MODEL,conditionProfileVersion:'1'});
  assert.deepEqual(restoreNamedProfile({conditionProfileId:MODEL,conditionProfileVersion:'2'}),{conditionProfileId:MODEL,conditionProfileVersion:'2'});
  assert.equal(restoreNamedProfile({temperature:'cooled'}),null);
});
test('R2 v1 actual application preserves temperature, stores reference and reselects the same site',async()=>{
  const start=source.indexOf('async function applyGuidedConditions('),fn=compile(source.slice(start,source.indexOf('\n}',start)+2));
  const make=(value,options)=>({value,options:options.map(value=>({value}))});
  const controls=[make('dry',['dry']),make('cooled',['cooled']),make('metal',['metal']),make('',['']),make('',[''])];
  const calls=[],clear={hidden:true};
  const app=new Function('guidedControlValues','restoreNamedProfile','clearNamedProfile','guidanceSignature','saveDraft','updateMatches','solventInput','temperatureInput','catalystInput','oxidationStageInput','workupInput',
    `let namedProfileSelection=null;${fn};return {run:applyGuidedConditions,selected:()=>namedProfileSelection};`)(guidedControlValues,restoreNamedProfile,clear,()=> 'current',()=>calls.push('save'),async id=>calls.push(id),...controls);
  await app.run(rows.generic.guidedConditions,'current');
  assert.equal(controls[1].value,'cooled');assert.equal(clear.hidden,false);
  assert.deepEqual(app.selected(),{conditionProfileId:MODEL,conditionProfileVersion:'1'});
  assert.deepEqual(calls,['save',rows.generic.id]);
  await assert.rejects(app.run(rows.generic.guidedConditions,'old'),/changed/);
});
class Element {
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.listeners={};this._text='';this.disabled=false;this.checked=false;}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
  set innerHTML(_){throw new Error('Use inert text');}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this._text='';this.children=children;}
  setAttribute(){}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  async emit(name){await Promise.all((this.listeners[name]??[]).map(fn=>fn({target:this})));}
}
const all=host=>host.children.flatMap(c=>[c,...all(c)]);
async function fixture(fn){
  const old=globalThis.document;globalThis.document={createElement:tag=>new Element(tag)};
  try{await fn(new Element('section'));}finally{if(old===undefined)delete globalThis.document;else globalThis.document=old;}
}
test('R2 v1 source facts render safely and require deliberate confirmation without new selectors',async()=>fixture(async host=>{
  let calls=0;const panel=new GuidedConditionsPanel(host,async()=>{calls++;});
  const g=structuredClone(rows.generic.guidedConditions);g.profileDescriptor.unknowns.push('<img src=x onerror=alert(1)>');
  panel.setGuidance(g,'current');
  assert.match(host.textContent,/hydrogenPressure/);assert.match(host.textContent,/not stated/);
  assert.ok(host.textContent.includes('<img'));assert.equal(all(host).some(e=>e.tagName==='IMG'||e.tagName==='SELECT'),false);
  const button=all(host).find(e=>e.tagName==='BUTTON'),check=all(host).find(e=>e.tagName==='INPUT');
  assert.equal(button.disabled,true);await button.emit('click');assert.equal(calls,0);
  check.checked=true;await check.emit('change');await button.emit('click');assert.equal(calls,1);
}));
test('R2 v1 obsolete confirm action cannot apply after guidance context changes',async()=>fixture(async host=>{
  let calls=0;const panel=new GuidedConditionsPanel(host,async()=>{calls++;});
  panel.setGuidance(rows.generic.guidedConditions,'old');
  const button=all(host).find(e=>e.tagName==='BUTTON'),check=all(host).find(e=>e.tagName==='INPUT');
  check.checked=true;await check.emit('change');panel.setGuidance(rows.qualified.guidedConditions,'new');
  await button.emit('click');assert.equal(calls,0);
}));
test('R2 v1 profile clearing is a fresh backend request and does not rewrite temperature',()=>{
  const start=source.indexOf("clearNamedProfile.addEventListener('click'"),handler=source.slice(start,source.indexOf('\n});',start)+4);
  assert.ok(start>=0);assert.match(handler,/namedProfileSelection = null/);assert.match(handler,/saveDraft\(\)/);assert.match(handler,/updateMatches/);
  assert.doesNotMatch(handler,/temperatureInput.value\s*=/);
});
