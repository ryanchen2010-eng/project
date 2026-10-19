import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';
import { runInNewContext } from 'node:vm';

const read = (p) => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const load = async (p) => import(`data:text/javascript;base64,${Buffer.from(ts.transpileModule(await read(p), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText).toString('base64')}`);
const { calculateReaction, calculateRequiredAmounts, copyCalculationContext } = await load('src/reaction-calculator.ts');
const { conditionLabel, conditionGuidance } = await load('src/reaction-conditions.ts');
const rows = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from pathlib import Path
from server import chemistry_server as s
f=json.loads(Path('tests/fixtures/alcohol-dehydration-phase5a.json').read_text());rows=[]
for case in f['positive']:
 for reverse in [False,True]:
  a,b={'smiles':case['substrate']},'sulfuric-acid'
  if reverse:a,b=b,a
  for r in s.match_reactions(a,b,f['conditions'])['reactionOptions']:
   if r['mechanism']=='Alcohol dehydration':rows.append(dict(case=case,reverse=reverse,reaction=r))
for conditions in [{},{'catalyst':'acid'},{'temperature':'heated'},{'catalyst':'acid','temperature':'ambient'},{'catalyst':'acid','temperature':'heated','peroxide':True}]:
 r=next(o for o in s.match_reactions('ethanol','sulfuric-acid',conditions)['reactionOptions'] if o['mechanism']=='Alcohol dehydration')
 rows.append(dict(conditions=conditions,reaction=r))
print(json.dumps(rows))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8' }));
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);

for (const { reaction: r, case: c, reverse } of rows.filter((r)=>r.case)) {
  test(`dehydration theoretical amounts: ${c.label}, reverse=${reverse}, ${r.site.siteId}`, () => {
    const data = r.stoichiometry, model = r.dehydrationModel;
    const n = (c.substrate.match(/C/g)??[]).length, oxygen = (c.substrate.match(/O/g)??[]).length;
    const expectedMass = n*12.011 + (2*n)*1.008 + (oxygen-1)*15.999;
    const input = reverse ? 1 : 0;
    close(data.product.molarMass,expectedMass);
    assert.equal(data.reactants.length,1); assert.equal(data.reactants[0].inputSlot,input);
    assert.equal(data.reactants[0].coefficient,1);
    close(data.reactants[0].molarMass,expectedMass+18.015);
    const result = calculateReaction(data,{[input]:{value:2,unit:'mmol'}});
    close(result.product.moles,0.002); close(result.product.grams,expectedMass*0.002);
    assert.deepEqual(result.limitingInputs,[input]);
    const required = calculateRequiredAmounts(data,{value:expectedMass*0.003,unit:'g'});
    assert.equal(required.reactants.length,1); close(required.reactants[0].moles,0.003);
    assert.match(data.excludedInputs[0].reason,/Acid catalyst.*not consumed/);
    const context = copyCalculationContext(data.context);
    assert.match(context.warning,/not additive yields/);
    assert.match(context.warning,/proton exchange/);
    assert.equal(context.canGenerate3D,!model.ezUnresolved && !model.oxygenCompetition);
    assert.equal(context.canGenerate3D,r.assessment.evidence.canGenerate3D);
    assert.match(conditionGuidance(r.assessment),/Structure\/site supported/);
    if (!context.canGenerate3D) assert.match(conditionLabel(r.assessment),/conditional 2D only/);
  });
}
for (const { reaction:r,conditions } of rows.filter((r)=>r.conditions)) {
  test(`dehydration condition context remains explicit: ${JSON.stringify(conditions)}`,()=>{
    const context = copyCalculationContext(r.stoichiometry.context);
    assert.equal(context.canGenerate3D,false);
    assert.equal(r.assessment.evidence.canPreview2D,true);
    assert.match(conditionGuidance(r.assessment),/Conditional 2D remains available/);
    assert.doesNotMatch(conditionLabel(r.assessment),/fit the example|guaranteed/);
    if (conditions.peroxide) assert.match(context.warning,/peroxide/);
    if (!conditions.temperature || !conditions.catalyst) assert.match(conditionGuidance(r.assessment),/Missing:/);
  });
}
test('existing controls display dehydration guidance without layout or calculator-formula changes',async()=>{
  const source=await read('src/reaction-lab.ts');
  assert.match(source,/reaction\.mechanism === 'Alcohol dehydration'\) conditionAssessment\.textContent/);
  assert.match(source,/assessment\?\.canRun !== false/);
  assert.match(source,/reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
  const equationFunction=source.slice(source.indexOf('function formatEquation('),source.indexOf('\nfunction showEmpty('));
  const js=ts.transpileModule(equationFunction,{compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText;
  const first={id:'alcohol',name:'Alcohol',formula:'C2H6O'}, second={id:'acid',name:'Sulfuric acid',formula:'H2SO4'};
  const format=runInNewContext(`${js}; formatEquation`,{catalog:{reactants:[first,second]},isReviewedReactant:()=>true});
  const reaction={mechanism:'Alcohol dehydration',reactants:['alcohol','acid'],equationReactants:['alcohol'],productName:'Ethene',productEquationFormula:'C2H4',byproducts:[{name:'Water',formula:'H2O'}]};
  assert.equal(format(reaction,first,second),'Alcohol (C2H6O) → Ethene (C2H4) + Water (H2O) · Sulfuric acid is the catalyst (not consumed)');
  assert.match(format({...reaction,mechanism:'E1'},first,second),/Sulfuric acid is the medium$/);
});
