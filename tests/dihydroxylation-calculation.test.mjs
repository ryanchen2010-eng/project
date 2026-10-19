import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';

const transpile = (text) => ts.transpileModule(text, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const source = await readFile(new URL('../src/reaction-calculator.ts', import.meta.url), 'utf8');
const { calculateReaction, calculateRequiredAmounts } = await import(`data:text/javascript;base64,${Buffer.from(transpile(source)).toString('base64')}`);
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-8, `${a} != ${b}`);
const fixtures = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python',import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
rows=[]
# Independent substrate element counts, product net increment and multiplicity.
cases=[('C=C',2,4,0,1),('C=CC',3,6,0,2),('C/C=C/C',4,8,0,2),('C/C=C\\\\C',4,8,0,1),
 ('CC=CCCC',6,12,0,1),('C1=CCCCC1',6,10,0,1),('C=Cc1ccccc1',8,8,0,2),
 ('C=CC[C@H](C)CC',7,14,0,2),('C=CCCCO',5,10,1,2),('C=CCCCOC',6,12,1,2),
 ('C=CCCCCC=C',8,14,0,2),('C=CCCCCC=CC',9,16,0,3)]
for substrate,c,h,o,count in cases:
 for reverse in [False,True]:
  a,b={'smiles':substrate},'hydrogen-peroxide'
  if reverse:a,b=b,a
  rs=[r for r in s.match_reactions(a,b,{'catalyst':'osmium','workup':'aqueous-release'})['reactions'] if r['mechanism']=='Alkene dihydroxylation']
  assert len(rs)==count,(substrate,len(rs))
  for r in rs:
   assert r['assessment']['canRun'] and not r['byproducts']
   rows.append(dict(substrate=substrate,reverse=reverse,id=r['id'],basis=r['stoichiometry'],mass=c*12.011+h*1.008+o*15.999))
print(json.dumps(rows))
`], { cwd:fileURLToPath(new URL('..',import.meta.url)),encoding:'utf8' }));
assert.equal(fixtures.length,42);
for (const f of fixtures) {
  test(`Diol net amounts: ${f.substrate}, reversed=${f.reverse}, ${f.id}`, () => {
    const d=f.basis, substrate=f.reverse?1:0, peroxide=1-substrate;
    assert.equal(d.balanced,true); assert.deepEqual(d.reactants.map(r=>r.coefficient),[1,1]);
    assert.equal(d.product.coefficient,1); assert.deepEqual(d.excludedInputs,[]);
    close(d.product.molarMass,f.mass+34.014);
    close(d.reactants.find(r=>r.inputSlot===peroxide).molarMass,34.014);
    close(d.reactants.find(r=>r.inputSlot===substrate).molarMass,f.mass);
    const result=calculateReaction(d,{[substrate]:{value:20,unit:'mmol'},[peroxide]:{value:170.07,unit:'mg'}});
    close(result.product.moles,0.005); close(result.product.grams,(f.mass+34.014)*0.005);
    assert.deepEqual(result.limitingInputs,[peroxide]);
    close(result.reactants.find(r=>r.inputSlot===substrate).remainingMoles,0.015);
    const required=calculateRequiredAmounts(d,{value:(f.mass+34.014)*0.002,unit:'g'});
    for (const r of required.reactants) { close(r.moles,0.002); close(r.grams,(r.inputSlot===peroxide?34.014:f.mass)*0.002); }
    assert.ok(d.notes.some(n=>/Formal O\/H maps/.test(n)));
    assert.ok(d.notes.some(n=>/Os catalyst and aqueous release species are omitted/.test(n)));
  });
}

const ui=await readFile(new URL('../src/reaction-lab.ts',import.meta.url),'utf8');
const actions=transpile(ui.slice(ui.indexOf('function updatePreviewActions()'),ui.indexOf('function setPreview(')));
function controls(canRun) {
  const view2D={},view3D={},viewCompare={},runButton={};
  new Function('selectedReaction','runController','view2D','view3D','viewCompare','runButton',actions+'\nupdatePreviewActions();')(
    {mechanism:'Alkene dihydroxylation',assessment:{canRun}},null,view2D,view3D,viewCompare,runButton);
  return {view2D,view3D,viewCompare,runButton};
}
test('missing diol workup keeps 2D but disables 3D/compare/run',()=>{
  const c=controls(false);assert.equal(c.view2D.disabled,false);
  for (const x of [c.view3D,c.viewCompare,c.runButton]) assert.equal(x.disabled,true);
});
test('confirmed diol net settings enable existing controls',()=>{
  for (const c of Object.values(controls(true))) assert.equal(c.disabled,false);
});
test('workup changes invalidate results and are saved/restored explicitly',()=>{
  assert.match(ui,/polymerUnitsInput, workupInput\]\) select.addEventListener\('change'[^]*?updateMatches\(\)/);
  assert.match(ui,/workup: workupInput.value/);assert.match(ui,/\['workup', workupInput\]/);
  assert.match(ui,/workupInput.value = example.conditions.workup \?\? ''/);
  assert.match(ui,/value="">Not confirmed/);
});
test('diol settings appear only in existing contextual pathway panel',()=>{
  const start=ui.indexOf('function updatePathwaySettings('),end=ui.indexOf('function saveDraft(',start);
  const fn=transpile(ui.slice(start,end));
  const extensionConditions={},extensionTitle={},additionSettings={},chainSettings={},diolSettings={};
  const update=new Function('extensionConditions','extensionTitle','additionSettings','chainSettings','diolSettings',fn+'\nreturn updatePathwaySettings;')(
    extensionConditions,extensionTitle,additionSettings,chainSettings,diolSettings);
  update([{mechanism:'Alkene dihydroxylation'}]);assert.equal(diolSettings.hidden,false);assert.equal(extensionConditions.hidden,false);
  update([{mechanism:'SN2'}]);assert.equal(diolSettings.hidden,true);assert.equal(extensionConditions.hidden,true);
});
test('no new audit molecules enter the visible dihydroxylation example',()=>{
  const line=ui.split('\n').find(s=>s.includes("id: 'dihydroxylation'"));
  assert.match(line,/reactants: \['ethene', 'hydrogen-peroxide'\]/);
  assert.match(line,/workup: 'aqueous-release'/);
  assert.doesNotMatch(line,/stereo unassigned/);
});
