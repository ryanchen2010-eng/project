/** R3 v1 named endpoint/calculation/UI contracts; no experimental forecasting. */
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
const {conditionNextStep,conditionGuidance,restoreNamedProfile,REVIEWED_COOLING_MODELS}=await load('src/reaction-conditions.ts');
const {calculateReaction,calculateRequiredAmounts,copyCalculationContext}=await load('src/reaction-calculator.ts');
const {guidedControlValues,GuidedConditionsPanel}=await load('src/guided-reaction-conditions.ts');
const source=await read('src/reaction-lab.ts');
const data=JSON.parse(execFileSync(`${root}.venv/bin/python`,['-c',`
import json
from server import chemistry_server as s
from server import cooled_dihydroxylation_r3 as r
rows=[]
for m in r.MODELS.values():
 c={'temperature':'cooled','solvent':'dry','catalyst':'osmium','workup':m.workup,'conditionProfileId':m.identifier,'conditionProfileVersion':'1'}
 def option(c):return next(o for o in s.match_reactions({'smiles':m.substrate},'hydrogen-peroxide',c)['reactionOptions'] if o['mechanism']=='Alkene dihydroxylation')
 rows.append({'id':m.identifier,'qualified':option(c),'generic':option({k:v for k,v in c.items() if not k.startswith('conditionProfile')}),'conflict':option({**c,'workup':'' if m.workup else 'aqueous-release'}),'ambient':option({**c,'temperature':'ambient'})})
print(json.dumps(rows))
`],{cwd:root,encoding:'utf8',maxBuffer:8*1024*1024}));
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
const expected={'cooled-isobutylene-os-peroxide-v1':{mass:90.122,release:'',yield:37.6},'cooled-crotonic-os-peroxide-v1':{mass:120.104,release:'aqueous-release',yield:53.8},'cooled-cinnamic-os-peroxide-v1':{mass:182.175,release:'aqueous-release',yield:56.2}};

for(const f of data){
  test(`R3 v1 ${f.id}: theoretical one-peroxide arithmetic retains exact source provenance`,()=>{
    const o=f.qualified,c=copyCalculationContext(o.stoichiometry.context),e=expected[f.id];
    assert.equal(o.assessment.canRun,true);assert.equal(c.canGenerate3D,true);
    assert.deepEqual(c.namedConditionProfile.reference,{id:f.id,version:'1'});
    assert.equal(c.namedConditionProfile.descriptor.pathway,'Alkene dihydroxylation');
    const isolated=c.namedConditionProfile.descriptor.facts.find(x=>x.field==='productRelease').value;
    assert.equal(isolated.reportedYieldPercent,e.yield);
    const result=calculateReaction(o.stoichiometry,{0:{value:1,unit:'mmol'},1:{value:1,unit:'mmol'}});
    close(result.product.moles,0.001);close(result.product.grams,e.mass*0.001);
    close(calculateRequiredAmounts(o.stoichiometry,{value:1,unit:'mmol'}).reactants.find(r=>r.inputSlot===1).grams,0.034014);
    assert.match(c.warning,/not experimental yields/);assert.match(c.warning,/formal net bookkeeping/);
    assert.equal(o.assessment.productRelease.aqueousReleaseAssumed,Boolean(e.release));
    assert.match(conditionNextStep(o.assessment),/^Supported cooled/);
    assert.match(conditionGuidance(o.assessment),/not a stereochemical prediction/);
    assert.equal(REVIEWED_COOLING_MODELS[f.id].pathway,'Alkene dihydroxylation');
  });
  test(`R3 v1 ${f.id}: explicit guide keeps reaction temperature and distinguishes release histories`,()=>{
    const g=f.generic.guidedConditions,v=guidedControlValues(g);
    assert.deepEqual(v,{solvent:'dry',catalyst:'osmium',workup:expected[f.id].release,conditionProfileId:f.id,conditionProfileVersion:'1'});
    assert.equal(g.requireConfirmation,true);assert.equal(Object.hasOwn(v,'temperature'),false);
    assert.equal(f.generic.assessment.canRun,false);assert.equal(f.conflict.assessment.canRun,false);assert.equal(f.ambient.assessment.canRun,false);
    for(const extra of [{temperature:'cooled'},{conditionProfileVersion:'2'},{release:'fractionation'},{catalyst:'none'},{pressure:'1'}])assert.throws(()=>guidedControlValues({...g,targetConditions:{...v,...extra}}));
    assert.doesNotMatch(conditionNextStep(f.conflict.assessment),/^Supported cooled/);
    assert.equal(copyCalculationContext(f.conflict.stoichiometry.context).canGenerate3D,false);
  });
}
test('R3 v1 no automatic stereo assignment or source-yield substitution',()=>{
  for(const f of data){
    assert.equal(f.qualified.productSmiles.includes('@'),false);
    assert.deepEqual(f.qualified.dihydroxylationStereo.assignedAtomMaps,[]);
    assert.equal(f.qualified.dihydroxylationStereo.ratios,null);
    assert.equal(f.qualified.assessment.productRelease.workupSimulated,false);
    assert.equal(f.qualified.assessment.evidence.experimentalOutcome,'not-predicted');
  }
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).some(id=>id.includes('fumaric')),false);
});
test('R3 v1 real application transports the reviewed release and reference atomically',async()=>{
  const start=source.indexOf('async function applyGuidedConditions('),fn=compile(source.slice(start,source.indexOf('\n}',start)+2));
  for(const f of data){
    const g=f.generic.guidedConditions,calls=[];
    const controls=['dry','cooled','osmium','','aqueous-release'].map((value,i)=>({value,options:(i===4?['','aqueous-release']:[value]).map(value=>({value}))}));
    const app=new Function('guidedControlValues','restoreNamedProfile','clearNamedProfile','guidanceSignature','saveDraft','updateMatches','solventInput','temperatureInput','catalystInput','oxidationStageInput','workupInput',
      `let namedProfileSelection=null;${fn};return {run:applyGuidedConditions,selected:()=>namedProfileSelection};`)(guidedControlValues,restoreNamedProfile,{hidden:true},()=> 'current',()=>calls.push('save'),async id=>calls.push(id),...controls);
    await app.run(g,'current');assert.equal(controls[1].value,'cooled');assert.equal(controls[4].value,expected[f.id].release);
    assert.deepEqual(app.selected(),{conditionProfileId:f.id,conditionProfileVersion:'1'});assert.deepEqual(calls,['save',g.reactionId]);
    await assert.rejects(app.run(g,'stale'),/changed/);
  }
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
test('R3 v1 release replacement requires confirmation; an obsolete action cannot apply',async()=>{
  const previous=globalThis.document;globalThis.document={createElement:tag=>new Element(tag)};
  try{
    const host=new Element('section');let calls=0;const panel=new GuidedConditionsPanel(host,async()=>{calls++;});
    const g=structuredClone(data[0].generic.guidedConditions);g.profileDescriptor.unknowns.push('<img src=x onerror=alert(1)>');
    panel.setGuidance(g,'initial');const button=all(host).find(e=>e.tagName==='BUTTON'),check=all(host).find(e=>e.tagName==='INPUT');
    assert.equal(button.disabled,true);await button.emit('click');assert.equal(calls,0);
    assert.match(host.textContent,/NOT aqueous release/);assert.ok(host.textContent.includes('<img'));
    assert.equal(all(host).some(e=>e.tagName==='IMG'||e.tagName==='SELECT'),false);
    check.checked=true;await check.emit('change');panel.setGuidance(data[1].generic.guidedConditions,'new-site');
    await button.emit('click');assert.equal(calls,0);
  }finally{if(previous===undefined)delete globalThis.document;else globalThis.document=previous;}
});
test('R3 v1 context copying and draft restoration cannot mutate or silently replace identities',()=>{
  for(const f of data){
    const c=copyCalculationContext(f.qualified.stoichiometry.context);
    c.namedConditionProfile.descriptor.facts.pop();assert.equal(f.qualified.stoichiometry.context.namedConditionProfile.descriptor.facts.length,7);
    assert.deepEqual(restoreNamedProfile(f.qualified.stoichiometry.context.conditions),{conditionProfileId:f.id,conditionProfileVersion:'1'});
    const obsolete={conditionProfileId:f.id,conditionProfileVersion:'2'};assert.deepEqual(restoreNamedProfile(obsolete),obsolete);
    const bad=structuredClone(f.qualified.stoichiometry.context);bad.namedConditionProfile.descriptor.id=data.find(x=>x.id!==f.id).id;
    assert.throws(()=>copyCalculationContext(bad));
  }
});
