/** Public stoichiometry, confidence and confirmed guidance for Phase 2 only. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const root = fileURLToPath(new URL('../', import.meta.url));
const load = async path => {
  const text = await readFile(new URL(`../${path}`, import.meta.url), 'utf8');
  const output = ts.transpileModule(text, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(output).toString('base64')}`);
};
const { calculateReaction, calculateRequiredAmounts, copyCalculationContext } = await load('src/reaction-calculator.ts');
const { conditionNextStep, conditionGuidance, REVIEWED_COOLING_MODELS } = await load('src/reaction-conditions.ts');
const { GuidedConditionsPanel, guidedControlValues } = await load('src/guided-reaction-conditions.ts');
const data = JSON.parse(execFileSync(`${root}.venv/bin/python`, ['-c', `
import json
from server import chemistry_server as s
c={'temperature':'cooled','solvent':'dry','catalyst':'none'}
pba={'smiles':'O=C(OO)c1ccccc1'}
def options(source,settings,reverse=False):
 a,b={'smiles':source},pba
 if reverse:a,b=b,a
 return [r for r in s.match_reactions(a,b,settings)['reactionOptions'] if r['mechanism']=='Epoxidation']
rows=[]
for source,carbons,hydrogens in [('C=Cc1ccccc1',8,8),('C=Cc1ccccc1C',9,10),('C=Cc1cccc(C)c1',9,10),
 ('C=Cc1ccc(C)cc1',9,10),('C=Cc1ccc(CC)cc1',10,12),('C=Cc1c(C)ccc(C)c1',10,12),('C=Cc1ccc([C@H](C)CC)cc1',12,16)]:
 for reverse in [False,True]:
  for option in options(source,c,reverse):
   rows.append({'source':source,'carbons':carbons,'hydrogens':hydrogens,'reverse':reverse,'option':option})
guidance={}
for name,source,extra in [('qualified','C=Cc1ccccc1',{}),('missing','C=Cc1ccccc1',{'solvent':''}),
 ('water','C=Cc1ccccc1',{'solvent':'aqueous-protic'}),('acid','C=Cc1ccccc1',{'catalyst':'acid'}),
 ('unknown','C=Cc1ccccc1',{'future':'unreviewed'}),('workup','C=Cc1ccccc1',{'workup':'aqueous-release'}),
 ('outside','C=CC',{})]:
 guidance[name]=options(source,{**c,**extra})[0]
print(json.dumps({'rows':rows,'guidance':guidance}))
`], {cwd:root,encoding:'utf8',maxBuffer:16*1024*1024}));
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-8, `${a} != ${b}`);
assert.equal(data.rows.length,28);

for(const fixture of data.rows) {
  test(`cooled perbenzoic amounts: ${fixture.source}, reverse=${fixture.reverse}, ${fixture.option.id}`,()=>{
    const option=fixture.option,d=option.stoichiometry,substrate=fixture.reverse?1:0,oxidant=1-substrate;
    const substrateMass=fixture.carbons*12.011+fixture.hydrogens*1.008;
    assert.equal(d.balanced,true);
    assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);
    assert.equal(d.product.coefficient,1);
    close(d.reactants.find(r=>r.inputSlot===oxidant).molarMass,138.122);
    close(d.reactants.find(r=>r.inputSlot===substrate).molarMass,substrateMass);
    close(d.product.molarMass,substrateMass+15.999);
    close(substrateMass+138.122,d.product.molarMass+122.123);
    assert.deepEqual(option.byproducts,[{name:option.byproducts[0].name,formula:'C7H6O2'}]);
    const result=calculateReaction(d,{[substrate]:{value:20,unit:'mmol'},[oxidant]:{value:0.69061,unit:'g'}});
    close(result.product.moles,0.005);
    close(result.product.grams,(substrateMass+15.999)*0.005);
    assert.deepEqual(result.limitingInputs,[oxidant]);
    close(result.reactants.find(r=>r.inputSlot===substrate).remainingMoles,0.015);
    const needed=calculateRequiredAmounts(d,{value:2,unit:'mmol'});
    for(const row of needed.reactants){close(row.moles,0.002);close(row.grams,(row.inputSlot===oxidant?138.122:substrateMass)*0.002);}
    assert.equal(d.context.canGenerate3D,true);
    assert.match(d.context.warning,/not experimental yields/);
    assert.match(d.context.assumptions.join(' '),/chloroform-reference/);
    assert.match(conditionNextStep(option.assessment),/^Supported cooled perbenzoic-acid epoxidation model/);
    assert.match(conditionGuidance(option.assessment),/not a temperature simulation/);
    assert.match(conditionGuidance(option.assessment),/not establish an actual experimental solvent/);
  });
}

test('perbenzoic remains a distinct epoxidation identity alongside the named hydrogenation pilot',()=>{
  assert.equal(Object.keys(REVIEWED_COOLING_MODELS).length,7);
  assert.equal(new Set(Object.values(REVIEWED_COOLING_MODELS).map(x=>x.pathway)).size,4);
  assert.equal(REVIEWED_COOLING_MODELS['cooled-perbenzoic-epoxidation-v1'].pathway,'Epoxidation');
});

for(const name of ['missing','water','acid','unknown','workup','outside']) {
  test(`${name}: rejected cooled perbenzoic context never gains positive 3D wording or calculator permission`,()=>{
    const option=data.guidance[name],before=structuredClone(option);
    assert.equal(option.assessment.canRun,false);
    assert.doesNotMatch(conditionNextStep(option.assessment),/^Supported cooled|View the theoretical 3D/);
    assert.doesNotMatch(conditionGuidance(option.assessment),/Cooled 3D is a theoretical product conformer/);
    const context=copyCalculationContext(option.stoichiometry.context);
    assert.equal(context.canGenerate3D,false);
    const result=calculateReaction(option.stoichiometry,{0:{value:1,unit:'mmol'},1:{value:1,unit:'mmol'}});
    close(result.product.moles,0.001); // Arithmetic does not qualify the reaction.
    assert.equal(context.canGenerate3D,false);
    assert.deepEqual(option,before);
  });
}

for(const extra of [{temperature:'ambient'},{oxidationStage:''},{workup:''},{future:'unreviewed'},{solvent:'aqueous-protic'},{catalyst:'acid'}]) {
  test(`perbenzoic guidance transport refuses hidden changes ${JSON.stringify(extra)}`,()=>{
    const g=structuredClone(data.guidance.missing.guidedConditions);
    g.targetConditions={solvent:'dry',catalyst:'none',...extra};
    assert.throws(()=>guidedControlValues(g));
  });
}

class Element {
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.listeners={};this.attributes={};this.disabled=false;this.checked=false;this.hidden=false;this._text='';}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
  set innerHTML(_){throw new Error('Unsafe guidance rendering');}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this._text='';this.children=children;}
  setAttribute(key,value){this.attributes[key]=value;}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  async emit(name){await Promise.all((this.listeners[name]??[]).map(fn=>fn({target:this})));}
}
const descendants=node=>node.children.flatMap(child=>[child,...descendants(child)]);
const tag=(host,name)=>descendants(host).find(x=>x.tagName===name.toUpperCase());
async function fixture(run,apply=async()=>{}){
  const previous=globalThis.document;globalThis.document={createElement:tag=>new Element(tag)};
  try{const host=new Element('section');await run(host,new GuidedConditionsPanel(host,apply));}
  finally{if(previous===undefined)delete globalThis.document;else globalThis.document=previous;}
}

for(const name of ['missing','water','acid']) {
  test(`${name}: existing guidance requires explicit confirmation, preserves temperature and revalidates`,async()=>{
    const calls=[],g=data.guidance[name].guidedConditions;
    assert.deepEqual(guidedControlValues(g),{solvent:'dry',catalyst:'none'});
    await fixture(async(host,panel)=>{
      panel.setGuidance(g,'exact-reactant-condition-signature');
      assert.match(host.textContent,/chloroform-reference/);
      assert.match(host.textContent,/not.*experimental solvent/);
      assert.match(host.textContent,/not.*temperature simulation/);
      assert.ok(descendants(host).some(x=>x.attributes.role==='status'));
      assert.equal(descendants(host).filter(x=>x.tagName==='SELECT').length,0);
      const button=tag(host,'button'),check=tag(host,'input');
      assert.equal(button.disabled,true);assert.equal(calls.length,0);
      await button.emit('click');assert.equal(calls.length,0);
      check.checked=true;await check.emit('change');await button.emit('click');
      assert.equal(calls.length,1);assert.equal(calls[0][1],'exact-reactant-condition-signature');
      assert.equal(calls[0][0],g);
    },async(...args)=>calls.push(args));
  });
}

for(const name of ['qualified','unknown','workup','outside']) {
  test(`${name}: non-applicable guidance cannot apply settings`,async()=>{
    const g=data.guidance[name].guidedConditions;
    assert.equal(g.canApply,false);assert.equal(g.targetConditions,undefined);
    assert.throws(()=>guidedControlValues(g));
    await fixture(async(host,panel)=>{
      panel.setGuidance(g,'context');assert.equal(tag(host,'button'),undefined);
      assert.match(host.textContent,/chloroform-reference/);
    });
  });
}

test('obsolete perbenzoic confirmation cannot apply after a different substrate is selected',async()=>{
  let calls=0;
  await fixture(async(host,panel)=>{
    panel.setGuidance(data.guidance.missing.guidedConditions,'old');
    const oldButton=tag(host,'button'),oldCheck=tag(host,'input');
    oldCheck.checked=true;await oldCheck.emit('change');
    panel.setGuidance(data.guidance.outside.guidedConditions,'new');
    await oldButton.emit('click');assert.equal(calls,0);
  },async()=>{calls+=1;});
});

for(const [field,value] of [['modelId','cooled-perbenzoic-epoxidation-v2'],['version',2],['registryVersion',2],['profileVersion',2]]) {
  test(`unknown perbenzoic ${field} fails closed`,()=>{
    const a=structuredClone(data.guidance.qualified.assessment);a.cooling[field]=value;
    assert.doesNotMatch(conditionNextStep(a),/^Supported cooled/);
    assert.doesNotMatch(conditionGuidance(a),/Cooled 3D is a theoretical product conformer/);
  });
}
