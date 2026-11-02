/* Run against a local QA server: QA_URL=http://127.0.0.1:PORT node tests/cooling-batch4-browser.cjs.
   These lifecycle fixtures are separate from the frozen chemistry benchmark. */
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const url=process.env.QA_URL;
if (!url || !/^http:\/\/127\.0\.0\.1:\d+$/.test(url)) throw Error('QA_URL must be a localhost-only QA server.');
const model='cooled-isobutylene-hcl-v1';
const cold={temperature:'cooled',solvent:'dry',catalyst:'none',conditionProfileId:model,conditionProfileVersion:'1'};
const fixtures=[
 {id:'cooled-alkene-bromination-v1',path:'Bromination',substrate:'C=C',reagent:'bromine',name:'Bromine',catalyst:'none'},
 {id:'cooled-peroxyacid-epoxidation-v1',path:'Epoxidation',substrate:'C=C',reagentSmiles:'O=C(OO)c1cccc(Cl)c1',name:'mCPBA reference',catalyst:'none'},
 {id:'cooled-perbenzoic-epoxidation-v1',path:'Epoxidation',substrate:'C=Cc1ccccc1',reagentSmiles:'O=C(OO)c1ccccc1',name:'Perbenzoic reference',catalyst:'none'},
 {id:'cooled-cyclohexene-pd-silica-v1',path:'Hydrogenation',substrate:'C1=CCCCC1',reagent:'hydrogen',name:'Hydrogen',catalyst:'metal'},
 {id:model,path:'Hydrohalogenation',substrate:'C=C(C)C',reagent:'hydrogen-chloride',name:'Hydrogen chloride',catalyst:'none'},
 {id:'cooled-isobutylene-os-peroxide-v1',path:'Alkene dihydroxylation',substrate:'C=C(C)C',reagent:'hydrogen-peroxide',name:'Hydrogen peroxide',catalyst:'osmium',workup:''},
 {id:'cooled-crotonic-os-peroxide-v1',path:'Alkene dihydroxylation',substrate:'CC=CC(=O)O',reagent:'hydrogen-peroxide',name:'Hydrogen peroxide',catalyst:'osmium',workup:'aqueous-release'},
 {id:'cooled-cinnamic-os-peroxide-v1',path:'Alkene dihydroxylation',substrate:'O=C(O)C=Cc1ccccc1',reagent:'hydrogen-peroxide',name:'Hydrogen peroxide',catalyst:'osmium',workup:'aqueous-release'},
];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const results=[];
 async function open(width,conditions=cold){
  const context=await browser.newContext({viewport:{width,height:1000}});
  await context.addInitScript(conditions=>{const molecule={id:'drawn-1',name:'Drawn structure · C4H8',formula:'C4H8',smiles:'C=C(C)C',aliases:[]};sessionStorage.setItem('molecule-playground.reaction-draft.v1',JSON.stringify({values:[molecule.name,'Hydrogen chloride'],selectedIds:['drawn-1','hydrogen-chloride'],drawnInputs:[molecule,null],conditions}));},conditions);
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url+'/reaction-lab.html',{waitUntil:'domcontentloaded'});
  const option=page.locator('.reaction-option').filter({has:page.locator('strong',{hasText:/^Hydrohalogenation ·/})}).first();await option.waitFor({timeout:30000});
  const pending=page.waitForResponse(r=>r.url().endsWith('/api/reactions/diagram')&&r.status()===200);await option.click();const diagram=await(await pending).json();
  return {page,context,errors,diagram};
 }
 async function edit(page){if(!await page.locator('#reaction-temperature').isVisible())await page.getByRole('button',{name:'Edit conditions',exact:true}).click();}
 async function mutate(page,kind){
  await edit(page);
  if(kind==='profile') {await page.getByRole('button',{name:'Clear Named Condition Profile',exact:true}).click();return;}
  if(kind==='reagent') {await page.locator('#reactant-b').fill('not a valid reagent');return;}
  const field={temperature:'#reaction-temperature',solvent:'#reaction-solvent',catalyst:'#reaction-catalyst'}[kind];
  const value={temperature:'ambient',solvent:'aqueous-protic',catalyst:'acid'}[kind];
  await page.locator(field).selectOption(value);
 }
 try{
  for(const width of [1440,320]) for(const kind of ['temperature','solvent','catalyst','profile','reagent']){
   const {page,context,errors,diagram}=await open(width);assert.equal(diagram.assessment.canRun,true);
   let release,started;const held=new Promise(r=>release=r),ready=new Promise(r=>started=r);
   await page.route('**/api/reactions/run',async route=>{const response=await route.fetch();started();await held;try{await route.fulfill({response});}catch{}});
   await page.locator('#view-compare').click();await ready;await mutate(page,kind);release();
   await page.waitForTimeout(700);
   assert.equal(await page.locator('#result-details').evaluate(e=>e.hidden),true,kind);
   assert.equal(await page.locator('#product-measurements').evaluate(e=>e.hidden),true,kind);
   assert.equal(await page.locator('#reaction-calculator .calculator-output').evaluate(e=>e.hidden),true,kind);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
   results.push({width,kind,lateProduct:'discarded'});await context.close();
  }
  for(const version of ['1','2']){
   const {page,context,diagram}=await open(1440,{...cold,conditionProfileVersion:version});
   assert.equal(diagram.assessment.canRun,version==='1');
   if(version==='2')assert.equal(await page.locator('#view-3d').isDisabled(),true);
   results.push({draftVersion:version,canRun:diagram.assessment.canRun});await context.close();
  }
  {
   const {page,context,diagram}=await open(1440);assert.equal(diagram.assessment.canRun,true);
   const run=page.waitForResponse(r=>r.url().endsWith('/api/reactions/run')&&r.status()===200);await page.locator('#view-compare').click();await run;
   await page.waitForFunction(()=>document.querySelector('#result-placeholder').hidden);
   await page.getByRole('button',{name:'Reaction amounts',exact:true}).click();
   const fields=page.locator('#reaction-calculator .calculator-fields');
   for(let i=0;i<2;i++){await fields.locator('select').nth(i).selectOption('mol');await fields.locator('input').nth(i).fill('0.001');}
   await page.locator('#reaction-calculator button[type=submit]').click();assert.equal(await page.locator('#reaction-calculator .calculator-output').evaluate(e=>e.hidden),false);
   await mutate(page,'solvent');
   assert.equal(await page.locator('#result-details').evaluate(e=>e.hidden),true);
   assert.equal(await page.locator('#product-measurements').evaluate(e=>e.hidden),true);
   assert.equal(await page.locator('#reaction-calculator .calculator-output').evaluate(e=>e.hidden),true);
   results.push({case:'populated product, measurements and calculation',changed:'solvent',cleared:true});await context.close();
  }
  {
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   await context.addInitScript(()=>sessionStorage.setItem('molecule-playground.reaction-draft.v1',JSON.stringify({values:['Bromomethane','Hydroxide ion'],selectedIds:['bromomethane','hydroxide'],drawnInputs:[null,null],conditions:{temperature:'cooled',solvent:'polar-aprotic',catalyst:'none'}})));
   const page=await context.newPage();await page.goto(url+'/reaction-lab.html',{waitUntil:'domcontentloaded'});
   const option=page.locator('.reaction-option').filter({has:page.locator('strong',{hasText:/^SN2 ·/})}).first();await option.waitFor({timeout:30000});
   let release,started;const held=new Promise(r=>release=r),ready=new Promise(r=>started=r);
   await page.route('**/api/reactions/diagram',async route=>{const response=await route.fetch();started();await held;try{await route.fulfill({response});}catch{}});
   await option.click();await ready;await page.locator('#reactant-b').fill('not a valid reagent');release();await page.waitForTimeout(700);
   assert.equal(await page.locator('#reaction-mechanism').evaluate(e=>e.hidden),true);
   assert.equal(await page.locator('#diagram-drawing svg').count(),0);
   results.push({case:'delayed mapped SN2 diagram and mechanism',changed:'reagent',discarded:true});await context.close();
  }
  for(const f of fixtures) for(const kind of ['temperature','solvent','catalyst','profile','reagent']){
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   await context.addInitScript(f=>{
    const a={id:'drawn-1',name:'Fixture substrate',formula:'C',smiles:f.substrate,aliases:[]};
    const b=f.reagentSmiles?{id:'drawn-2',name:f.name,formula:'C',smiles:f.reagentSmiles,aliases:[]}:null;
    const conditions={temperature:'cooled',solvent:'dry',catalyst:f.catalyst,conditionProfileId:f.id,conditionProfileVersion:'1',...(f.workup!==undefined?{workup:f.workup}:{})};
    sessionStorage.setItem('molecule-playground.reaction-draft.v1',JSON.stringify({values:[a.name,f.name],selectedIds:['drawn-1',f.reagent||'drawn-2'],drawnInputs:[a,b],conditions}));
   },f);
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url+'/reaction-lab.html',{waitUntil:'domcontentloaded'});
   const option=page.locator('.reaction-option').filter({has:page.locator('strong',{hasText:new RegExp('^'+f.path+' ·')})}).first();await option.waitFor({timeout:30000});
   const pending=page.waitForResponse(r=>r.url().endsWith('/api/reactions/diagram')&&r.status()===200);await option.click();const diagram=await(await pending).json();
   assert.equal(diagram.assessment.canRun,true,f.id);assert.equal(diagram.assessment.cooling.modelId,f.id);
   let release,started;const held=new Promise(r=>release=r),ready=new Promise(r=>started=r);
   await page.route('**/api/reactions/run',async route=>{const response=await route.fetch();started();await held;try{await route.fulfill({response});}catch{}});
   await page.locator('#view-compare').click();await ready;await mutate(page,kind);release();await page.waitForTimeout(700);
   assert.equal(await page.locator('#result-details').evaluate(e=>e.hidden),true,`${f.id} ${kind}`);
   assert.equal(await page.locator('#product-measurements').evaluate(e=>e.hidden),true,`${f.id} ${kind}`);
   assert.equal(await page.locator('#reaction-calculator .calculator-output').evaluate(e=>e.hidden),true,`${f.id} ${kind}`);
   assert.deepEqual(errors,[]);results.push({profile:f.id,kind,lateProduct:'discarded'});await context.close();
  }
  for(const f of fixtures){
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   await context.addInitScript(f=>{
    const a={id:'drawn-1',name:'Fixture substrate',formula:'C',smiles:f.substrate,aliases:[]};
    const b=f.reagentSmiles?{id:'drawn-2',name:f.name,formula:'C',smiles:f.reagentSmiles,aliases:[]}:null;
    const conditions={temperature:'cooled',solvent:'dry',catalyst:f.catalyst,conditionProfileId:f.id,conditionProfileVersion:'2',...(f.workup!==undefined?{workup:f.workup}:{})};
    sessionStorage.setItem('molecule-playground.reaction-draft.v1',JSON.stringify({values:[a.name,f.name],selectedIds:['drawn-1',f.reagent||'drawn-2'],drawnInputs:[a,b],conditions}));
   },f);
   const page=await context.newPage();const matching=page.waitForResponse(r=>r.url().endsWith('/api/reactions/match')&&r.status()===200);await page.goto(url+'/reaction-lab.html',{waitUntil:'domcontentloaded'});await matching;await page.waitForTimeout(500);
   const option=page.locator('.reaction-option').filter({has:page.locator('strong',{hasText:new RegExp('^'+f.path+' ·')})}).first();
   if(!await option.count()) {assert.equal(await page.locator('#view-3d').isDisabled(),true);results.push({profile:f.id,obsoleteDraft:'rejected; no eligible option'});await context.close();continue;}
   const pending=page.waitForResponse(r=>r.url().endsWith('/api/reactions/diagram')&&r.status()===200);await option.click();const diagram=await(await pending).json();
   assert.equal(diagram.assessment.canRun,false,f.id);assert.equal(await page.locator('#view-3d').isDisabled(),true);
   results.push({profile:f.id,obsoleteDraft:'rejected'});await context.close();
  }
  console.log(JSON.stringify(results));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
