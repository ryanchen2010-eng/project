// Isolated Phase 5K design exploration. Never imported by a production entry point.
const fixtures = await fetch('./fixtures.json').then(r => r.json());
const query = new URLSearchParams(location.search);
let concept = ['workbench', 'studio', 'research'].includes(query.get('concept')) ? query.get('concept') : 'workbench';
let fixtureName = query.get('fixture') === 'secondary' ? 'secondary' : 'sn2';
let qualified = false;
let mode = innerWidth <= 760 ? '2d' : 'compare';
let inspectorTab = 'Product';
let studioStep = 3;
let observed = Number(query.get('atom')) || 1;
let pinned = true;
let viewer;
let halo;
let mechanismShown = false;
let researchTab = 'Pathways';
const root = document.querySelector('#prototype');
const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const current = () => fixtureName === 'sn2' ? fixtures.sn2 : qualified ? fixtures.secondaryQualified : fixtures.secondaryMissing;
const icon = (name = 'molecule') => {
  const paths = {
    molecule: '<path d="M6 7l6-3 6 4v8l-6 4-6-4zM6 7l6 5 6-4M12 12v8"/><circle cx="6" cy="7" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="12" cy="20" r="2"/>',
    check: '<path d="M5 12l4 4L19 6"/>',
    warn: '<path d="M12 3L2 21h20L12 3zM12 9v5M12 17v1"/>',
    fit: '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
    home: '<path d="M3 11l9-8 9 8M6 9v12h12V9M10 21v-7h4v7"/>',
    build: '<path d="M4 20l4-1 12-12-3-3L5 16zM14 7l3 3"/>',
    lab: '<path d="M8 3h8M10 3v7L4 20h16l-6-10V3M7 15h10"/>',
    calc: '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 11h2M14 11h2M8 15h2M14 15h2M8 19h2M14 19h2"/>',
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.molecule}</svg>`;
};
const names = {workbench:'Scientific Workbench', studio:'Guided Chemistry Studio', research:'Professional Research Interface'};
function header() {
  const nav = [['Home','/','home'],['Explorer','/explore.html','molecule'],['Builder','/builder.html','build'],['Reaction Lab','/reaction-lab.html','lab'],['Calculators','/calculators.html','calc']];
  return `<header class="app-header"><a class="brand" href="/" target="_blank" rel="noopener">${icon()}<span>Molecule Playground</span></a><button class="tools-toggle" aria-expanded="false" aria-controls="app-navigation">Tools ▾</button><nav id="app-navigation" class="app-nav" aria-label="Main tools">${nav.map(([n,url,i]) => `<a href="${url}" target="_blank" rel="noopener" ${n === 'Reaction Lab' ? 'aria-current="page"' : ''}>${icon(i)}${n}</a>`).join('')}</nav></header>`;
}
function title() {
  return `<div class="prototype-tag"><span>DESIGN PROPOSAL</span> · Frozen display fixtures <span class="desktop-only">· Not the live website or a laboratory procedure</span></div><div class="page-title"><div><h1>Reaction Lab</h1><p>Choose a pathway. Inspect the chemistry.</p></div><div><span class="eyebrow">${names[concept]}</span></div></div>`;
}
function identities() {
  return fixtureName === 'sn2' ? {a:'Bromomethane',af:'CH₃Br',b:'Hydroxide ion',bf:'OH⁻',p:'Methanol',pf:'CH₄O',path:'SN2 substitution',sub:'Hydroxide · concerted substitution',pair:'Bromomethane + hydroxide'} : {a:'2-Propanol',af:'C₃H₈O',b:'Sodium hypochlorite',bf:'NaOCl',p:'Propan-2-one',pf:'C₃H₆O',path:'Secondary alcohol oxidation',sub:'NaOCl · ketone net model',pair:'2-Propanol + sodium hypochlorite'};
}
function conditionRows() {
  if (fixtureName === 'sn2') return [['Medium','Polar aprotic'],['Temperature','Not specified'],['Additional activation','Not specified']];
  if (!qualified) return [['Medium','Generic aqueous (unvalidated profile)'],['Temperature','Not specified'],['Activation','Not specified'],['Oxidation stage','Not specified']];
  return [['Medium','Aqueous acetic acid profile'],['Temperature','Room temperature'],['Activation','None added'],['Oxidation stage','First stage → carbonyl']];
}
function setup() {
  const n = identities();
  return `<section class="panel setup-panel" aria-label="Reaction setup"><div class="panel-title"><h2>Reaction setup</h2><small>Display fixture</small></div><div class="panel-body">${[['a','Reactant'],['b','Reagent']].map(([k,label]) => `<div class="setup-field"><label for="fixture-${k}">${label}<small>Exact identity</small></label><div class="compound-box"><span class="compound-symbol">${n[k+'f']}</span><div><input id="fixture-${k}" readonly value="${n[k]}" aria-label="${label} · fixed review fixture"><small>${k === 'a' ? 'Selected compound' : fixtureName === 'sn2' ? 'Consumed nucleophile' : 'Supported oxidant'}</small></div></div></div>`).join('')}<p class="setup-note">These inputs are read-only design fixtures. Use the review selector to compare the two verified cases.</p><div class="pathway-list"><p>Matching pathway</p><button class="pathway-option" aria-pressed="true"><strong>${n.path}</strong><small>${n.sub}</small></button><span class="pathway-count">1 selected structural option · not experimental selectivity</span></div>${fixtureName !== 'sn2' && !qualified ? `<div class="guided-callout"><strong>Complete the reaction conditions</strong><p>The generic water setting does not establish the supported oxidation profile.</p><button data-action="guidance">Review Guided Conditions</button></div>` : ''}<details class="setup-details" open><summary>Selected conditions</summary><dl>${conditionRows().map(([a,b]) => `<div><dt>${a}</dt><dd>${b}</dd></div>`).join('')}</dl>${fixtureName !== 'sn2' ? '<button data-action="guidance">Review Guided Conditions</button>' : ''}</details><details class="setup-details"><summary>Examples & saved structures</summary><p>Proposed compact picker. The curated collection stays separate from audit cases.</p><button data-action="example">Use SN2 display fixture</button></details><details class="setup-details"><summary>Functional groups</summary><p>${fixtureName === 'sn2' ? 'Selected site: C–Br. Nucleophile: hydroxide oxygen.' : 'Selected site: secondary alcohol. Product model: ketone.'}</p></details></div></section>`;
}
function confidence() {
  const blocked = !current().run;
  return `<div class="confidence-line ${blocked ? 'warn' : ''}" role="status">${icon(blocked ? 'warn' : 'check')}<span><strong>${blocked ? 'Conditions incomplete or conflicting' : 'Supported theoretical model'}</strong> · ${blocked ? 'Conditional 2D preview only. Complete Guided Conditions before 3D product generation.' : 'Selected inputs match the supported model. No yield, rate or selectivity guarantee.'}</span>${blocked ? '<button data-action="guidance">Review conditions</button>' : ''}</div>`;
}
function equation() {
  return fixtureName === 'sn2' ? 'CH₃Br + OH⁻ → CH₃OH + Br⁻' : 'C₃H₈O + NaOCl → C₃H₆O + NaCl + H₂O';
}
function stage() {
  const blocked = !current().run;
  if (blocked && mode === '3d') mode = '2d';
  return `<section class="panel visualization" aria-label="Molecular workspace"><div class="equation-strip"><span class="eyebrow">${blocked ? 'Conditional net transformation' : 'Net transformation'}</span><p>${equation()}</p><p class="byproduct-note">${fixtureName === 'sn2' ? '2D shows methanol and bromide. 3D shows the main product only.' : 'Bounded oxidation net model · no work-up or isolated recovery modeled.'}</p></div><div class="stage-toolbar"><span>Linked molecular views</span><div class="segmented" role="group" aria-label="Molecular view">${[['2d','2D'],['3d','3D'],['compare','Compare']].map(([id,label]) => `<button data-mode="${id}" aria-pressed="${mode === id}" ${blocked && id !== '2d' ? 'disabled' : ''}>${label}</button>`).join('')}</div></div><div class="molecule-stage" data-mode="${mode}"><section class="diagram-pane" ${mode === '3d' ? 'hidden' : ''}><div class="pane-heading"><strong>2D · ${fixtureName === 'sn2' ? 'Lewis-style' : 'net reaction'}</strong><span>Mapped atoms</span></div><div class="diagram-host"></div><div class="diagram-caption">${fixtureName === 'sn2' ? 'Hover or select an atom to link the views. Separate charge labels and spaced lone pairs are proposed here.' : 'Existing verified 2D fixture. Conditional until the supported profile is confirmed.'}</div></section><section class="model-pane" ${mode === '2d' ? 'hidden' : ''}><div class="pane-heading"><strong>3D · main product</strong><span>Illustrative conformer</span></div><div class="model-host" role="img" aria-label="${identities().p} 3D conformer"></div><div class="camera-bar"><button data-camera="fit">${icon('fit')}<span class="sr-only">Fit molecule</span></button><button data-camera="in" aria-label="Zoom in">＋</button><button data-camera="out" aria-label="Zoom out">−</button><button data-camera="rotate" aria-pressed="false">Rotate</button><small>Not a stereochemical guarantee</small></div></section></div><div class="atom-strip"><span class="atom-readout"></span><button data-action="clear-atom">Clear pin</button></div><div class="bond-key"><span><i></i>Bond broken</span><span><i></i>Bond formed</span><span>Color + labels, not color alone</span></div></section>`;
}
function mechanism() {
  return `<section class="panel mechanism-dock"><div class="panel-title"><h2>Mechanism</h2><span>${fixtureName === 'sn2' ? '1 concerted step' : 'Net model only'}</span></div>${fixtureName === 'sn2' ? `<div class="mechanism-row"><button data-mechanism="net" aria-pressed="${!mechanismShown}">Net bond changes</button><button data-mechanism="step" aria-pressed="${mechanismShown}">1 · Concerted substitution</button></div><p>No carbocation intermediate. The electron movements belong to the same step.</p>${mechanismShown ? '<div class="mechanism-moves"><button data-observe="6">Electron source: O6 lone pair → C1 · C–O bond forms</button><button data-observe="2">C1–Br2 bond electrons → Br2 · C–Br bond breaks</button></div>' : ''}` : '<p>The fixture supplies a net oxidation transformation, not a validated complete elementary mechanism.</p>'}</section>`;
}
function inspector() {
  return `<aside class="panel inspector" aria-label="Reaction inspector"><div class="panel-title"><h2>Inspector</h2><small>Selected pathway</small></div><div class="inspector-tabs" role="group" aria-label="Inspector section">${['Product','Atom','Conditions'].map(t => `<button data-inspector="${t}" aria-pressed="${inspectorTab === t}">${t}</button>`).join('')}</div><div class="inspector-content">${inspectorContent()}</div></aside>`;
}
function inspectorContent() {
  const f = current(), n = identities();
  if (inspectorTab === 'Atom') {
    const atom = f.diagram.atoms.find(a => a.mapId === observed);
    const linked = f.run?.product.atomLinks.find(a => a.mapId === observed);
    return `<span class="eyebrow">Mapped atom inspector</span><h3>${e(atom?.element || 'No atom')} · map ${observed}</h3><dl class="info-list"><div><dt>Identity</dt><dd>${e(atom?.speciesName || 'Select an atom')}</dd></div><div><dt>3D correspondence</dt><dd>${linked ? `Product atom index ${linked.index}` : 'Not present in the main-product 3D view'}</dd></div><div><dt>Selection</dt><dd>${pinned ? 'Pinned · pointer movement does not replace it' : 'Transient hover · click to pin'}</dd></div></dl><p>Map IDs identify the same atom, not equal screen positions. Byproduct atoms stay inspectable in 2D.</p>`;
  }
  if (inspectorTab === 'Conditions') return `<span class="eyebrow">Model requirements</span><dl class="info-list">${conditionRows().map(([k,v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>${fixtureName !== 'sn2' ? '<button data-action="guidance" style="margin-top:14px">Review Guided Conditions</button>' : ''}<p>Condition status is separate from structural eligibility. Matching a model does not establish experimental safety or conversion.</p>`;
  return `<div class="product-wordmark"><h3>${n.p}</h3><span>${n.pf}</span></div><dl class="info-list"><div><dt>Product status</dt><dd>${f.run ? 'Theoretical product available' : 'Conditional 2D preview · 3D blocked'}</dd></div><div><dt>Molar mass</dt><dd>${f.run ? `${e(f.run.product.molarMass)} g/mol` : 'Not asserted in this incomplete state'}</dd></div><div><dt>Other represented products</dt><dd>${fixtureName === 'sn2' ? 'Bromide ion · Br⁻' : 'Sodium chloride + water'}</dd></div><div><dt>Bond changes</dt><dd>${fixtureName === 'sn2' ? 'Break C1–Br2; form C1–O6' : 'Selected alcohol C–O → C=O; hydrogen transfer in net model'}</dd></div></dl><a class="calc-link" href="/calculators.html" target="_blank" rel="noopener">Open Calculators ↗</a><p>Theoretical amounts are not actual yields. This proposal does not calculate or transfer quantities.</p><details><summary>Confidence & limitations</summary><p>Uses an existing supported reaction fixture. No reaction rate, product ratio, isolated yield or laboratory safety claim. A 3D conformer is a visualization, not a uniquely predicted experimental geometry.</p></details>`;
}
function mobileContext() {
  return `<div class="mobile-context"><strong>${identities().pair}</strong><button data-mobile="setup">Edit</button></div><div class="mobile-work-tabs" role="group" aria-label="Workspace section">${[['workspace','Workspace'],['setup','Setup'],['details','Details']].map(([k,v]) => `<button data-mobile="${k}" aria-pressed="${k === 'workspace'}">${v}</button>`).join('')}</div>`;
}
function workbench() {
  return `${mobileContext()}<div class="work-grid">${setup()}<div class="workspace-column">${confidence()}${stage()}${mechanism()}</div>${inspector()}</div>`;
}
function studio() {
  return `<div class="studio-body"><nav class="studio-steps" aria-label="Reaction workflow">${['Inputs','Conditions','Pathway','Inspect'].map((v,i) => `<button data-studio="${i}" aria-pressed="${studioStep === i}"><b>${i + 1}</b>${v}</button>`).join('')}</nav>${studioStep !== 3 ? `<div class="studio-edit">${setup()}<button class="primary" data-studio="3" style="margin-top:14px;width:100%">Return to molecular workspace</button></div>` : `<div class="studio-summary"><div><span>Selected reaction</span><strong>${identities().pair} · ${identities().path}</strong></div><button data-studio="0">Edit inputs</button></div><div class="studio-layout"><div class="workspace-column">${confidence()}${stage()}${mechanism()}</div>${inspector()}</div><div class="studio-backbar"><button data-studio="2">← Review pathway</button><p>Inspect first. Full requirements remain available without repeating the whole form.</p></div>`}</div>`;
}
function expertDock() {
  let body;
  if (researchTab === 'Mechanism') body = mechanism();
  else if (researchTab === 'Amounts') body = '<p>Theoretical reaction amounts belong to the existing calculator, not an implied experimental yield.</p><a class="calc-link" href="/calculators.html" target="_blank" rel="noopener">Open reaction amounts in Calculators ↗</a>';
  else if (researchTab === 'Mapping') body = `<table><thead><tr><th>Atom / bond</th><th>Net change</th><th>Correspondence</th></tr></thead><tbody>${fixtureName === 'sn2' ? '<tr><td>C1–Br2</td><td>Bond broken</td><td>Br2 → bromide byproduct</td></tr><tr><td>C1–O6</td><td>Bond formed</td><td>Both mapped into methanol</td></tr>' : '<tr><td>Selected C–O</td><td>Single → double</td><td>Mapped alcohol → ketone</td></tr>'}</tbody></table>`;
  else body = `<table><thead><tr><th>Pathway</th><th>Site / status</th></tr></thead><tbody><tr><td>${identities().path}</td><td>${fixtureName === 'sn2' ? 'C1–Br2 · OH⁻ attacks C1' : 'Secondary alcohol · selected C–O'}<br><small>${current().run ? 'Supported model conditions' : 'Conditions require review'}</small></td></tr></tbody></table>`;
  return `<section class="panel expert-dock"><div class="expert-tabbar" role="group" aria-label="Expert detail section">${['Pathways','Mechanism','Mapping','Amounts'].map(t => `<button data-expert="${t}" aria-pressed="${researchTab === t}">${t}</button>`).join('')}</div><div class="expert-dock-body">${body}</div></section>`;
}
function research() {
  const n = identities();
  return `<div class="research-content"><div class="expert-command"><div><small>Reactant · exact identity</small><strong>${n.a}</strong><span>${n.af}</span></div><div><small>Reagent</small><strong>${n.b}</strong><span>${n.bf}</span></div><div><small>Conditions</small><span>${fixtureName === 'sn2' ? 'Polar aprotic · model match' : qualified ? 'Supported acetic acid profile' : 'Generic aqueous · incomplete'}</span><button data-action="${fixtureName === 'sn2' ? 'inspect-conditions' : 'guidance'}">Inspect</button></div></div><div class="research-layout"><div class="workspace-column">${confidence()}${stage()}${expertDock()}</div>${inspector()}</div><p class="reading-note">Expert proposal · single-site theoretical transformation, not experimental product distribution.</p></div>`;
}
function render() {
  viewer?.clear(); viewer = undefined; halo = undefined;
  document.body.classList.toggle('capture', query.get('capture') === '1');
  document.querySelectorAll('[data-concept]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.concept === concept)));
  document.querySelector('#fixture-choice').value = fixtureName;
  if(query.get('detail')==='1') {
    root.innerHTML=`<main class="diagram-detail"><span class="eyebrow">Phase 5K · rendering proposal only</span><h1>Atoms, charges & lone pairs</h1><p>Same verified SN2 atom identities. Current renderer on the left; an isolated spacing proposal on the right.</p><div class="detail-grid"><section class="panel"><div class="panel-title"><h2>Current mechanism starting state</h2></div><div class="raw-diagram">${fixtures.sn2.diagram.mechanism.steps[0].beforeState.svg}</div><div class="panel-title"><h2>Current mechanism product state</h2></div><div class="raw-diagram">${fixtures.sn2.diagram.mechanism.steps[0].state.svg}</div><p class="detail-note">Br/O approach and charge-dependent centering can crowd the annotations. This is the existing renderer, not a changed chemical graph.</p></section><section class="panel"><div class="panel-title"><h2>Proposed label-aware spacing</h2><small>One verified fixture</small></div><div class="diagram-host"></div><p class="detail-note">Center the base element on the mapped atom anchor. Offset the charge separately. Leave a clear pair-to-label gap and explicit space between disconnected species. One label-sized pin halo; no concentric stack.</p></section></div><p>SN2 remains a single concerted step: O6 → C1; C1–Br2 electrons → Br2. No carbocation intermediate is introduced.</p><p class="reading-note">This fixture illustrates a direction, not a general-purpose renderer fix. Production code is unchanged.</p></main>`;
    drawDiagram();updateAtom();return;
  }
  root.innerHTML = `<main class="app ${concept}" data-mobile-panel="workspace">${header()}${title()}${concept === 'workbench' ? workbench() : concept === 'studio' ? studio() : research()}</main>`;
  drawDiagram(); initViewer(); updateAtom(); bind();
}
function line(a,b,klass='') {
  const dx=b.x-a.x,dy=b.y-a.y,length=Math.hypot(dx,dy),pad=15;
  return `<line class="bond-line ${klass}" x1="${a.x+dx/length*pad}" y1="${a.y+dy/length*pad}" x2="${b.x-dx/length*pad}" y2="${b.y-dy/length*pad}"/>`;
}
function sn2SVG(width) {
  const w=Math.max(300,width), left=w*.24,right=w*.77,bond=Math.min(60,w*.12),y1=118,y2=336;
  const atoms = [
    {id:1,s:'C',x:left-8,y:y1},{id:2,s:'Br',x:left-8+bond,y:y1,pairs:['top','right','bottom']},
    {id:3,s:'H',x:left-8-bond,y:y1},{id:4,s:'H',x:left-8,y:y1-bond},{id:5,s:'H',x:left-8,y:y1+bond},
    {id:6,s:'O',x:right-9,y:y1,q:'−',pairs:['top','left','bottom']},{id:7,s:'H',x:right-9+bond,y:y1},
    {id:1,s:'C',x:left+8,y:y2},{id:6,s:'O',x:left+8-bond,y:y2,pairs:['top','bottom']},
    {id:7,s:'H',x:left+8-2*bond,y:y2},{id:3,s:'H',x:left+8+bond,y:y2},
    {id:4,s:'H',x:left+8,y:y2-bond},{id:5,s:'H',x:left+8,y:y2+bond},
    {id:2,s:'Br',x:right+5,y:y2,q:'−',pairs:['top','right','bottom','left']},
  ];
  const a=atoms.slice(0,7),p=atoms.slice(7);
  let body=[[0,1,'broken'],[0,2],[0,3],[0,4],[5,6]].map(([i,j,k])=>line(a[i],a[j],k)).join('');
  body += [[0,1,'formed'],[1,2],[0,3],[0,4],[0,5]].map(([i,j,k])=>line(p[i],p[j],k)).join('');
  body += atoms.map((a,i)=>{
    const rad=a.s==='Br'?31:27;
    const dots=(a.pairs||[]).map(side=>{
      const [x,y,h]=side==='top'?[0,-rad,true]:side==='bottom'?[0,rad,true]:side==='left'?[-rad,0,false]:[rad,0,false];
      return [-3.5,3.5].map(d=>`<circle class="electron-dot" cx="${x+(h?d:0)}" cy="${y+(h?0:d)}" r="1.75"/>`).join('');
    }).join('');
    return `<g class="diagram-atom" role="button" tabindex="0" aria-label="${a.s} map ${a.id} · ${i<7?'reactant':'product'}" data-map="${a.id}" transform="translate(${a.x} ${a.y})"><title>${a.s} · mapped atom ${a.id}</title><ellipse class="pin-ring" rx="${a.s==='Br'?23:19}" ry="21"/><text font-size="24" text-anchor="middle" dominant-baseline="central">${a.s}</text>${a.q?`<text font-size="14" x="${a.s==='Br'?23:15}" y="-19" text-anchor="middle">${a.q}</text>`:''}${dots}</g>`;
  }).join('');
  return `<svg class="diagram-svg" viewBox="0 0 ${w} 454" xmlns="http://www.w3.org/2000/svg" aria-label="Mapped SN2 Lewis-style reaction design proposal"><text class="side-label" x="${w/2}" y="23" text-anchor="middle">REACTANTS</text><text class="plus-sign" x="${w*.53}" y="${y1+5}" text-anchor="middle">+</text><text class="species-name" x="${left}" y="205" text-anchor="middle">Bromomethane</text><text class="species-name" x="${right}" y="205" text-anchor="middle">Hydroxide</text><path class="net-arrow" d="M${w/2} 219v28m-5-6 5 6 5-6"/><text class="side-label" x="${w/2}" y="271" text-anchor="middle">PRODUCTS</text><text class="plus-sign" x="${w*.53}" y="${y2+5}" text-anchor="middle">+</text><text class="species-name" x="${left}" y="435" text-anchor="middle">Methanol</text><text class="species-name" x="${right}" y="435" text-anchor="middle">Bromide</text>${body}</svg>`;
}
function drawDiagram() {
  const host=root.querySelector('.diagram-host');
  if (!host) return;
  host.innerHTML=fixtureName==='sn2'?sn2SVG(Math.max(300,host.clientWidth)):current().diagram.svg;
  host.querySelectorAll('[data-map],.atom-target').forEach(node=>{
    const id=Number(node.getAttribute('data-map') || node.getAttribute('data-atom-map'));
    if (!id) return;
    node.addEventListener('pointerenter',()=>{if (!pinned) selectAtom(id,false);});
    node.addEventListener('click',()=>selectAtom(id,true));
    node.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();selectAtom(id,true);}});
  });
}
function initViewer() {
  const host=root.querySelector('.model-host');
  if (!host || mode==='2d') return;
  const run=current().run;
  if (!run) {host.innerHTML='<div class="view-unavailable">3D product unavailable until conditions are complete.</div>';return;}
  if (!window.$3Dmol) {host.innerHTML='<div class="view-unavailable">3D library unavailable. The 2D fixture remains accessible.</div>';return;}
  viewer=window.$3Dmol.createViewer(host,{backgroundColor:'#f5f8f6',antialias:true});
  viewer.addModel(run.product.molfile,'sdf');
  viewer.setStyle({},{stick:{radius:.14},sphere:{scale:.27}});
  viewer.zoomTo(); viewer.zoom(2.1); viewer.render();
  viewer.setHoverable({},true,(_a)=>{
    const link=current().run?.product.atomLinks.find(l=>l.index===_a.index);
    if(link&&!pinned)selectAtom(link.mapId,false);
  },()=>{});
  viewer.setClickable({},true,(_a)=>{
    const link=current().run?.product.atomLinks.find(l=>l.index===_a.index);
    if(link)selectAtom(link.mapId,true);
  });
  updateAtom();
}
function selectAtom(id,pin) {observed=id;pinned=pin;updateAtom();}
function updateAtom() {
  root.querySelectorAll('[data-map]').forEach(n=>n.setAttribute('data-observed',String(Number(n.dataset.map)===observed)));
  root.querySelectorAll('.atom-target').forEach(n=>n.classList.toggle('is-proposal-selected',Number(n.getAttribute('data-atom-map'))===observed));
  const atom=current().diagram.atoms.find(a=>a.mapId===observed);
  const link=current().run?.product.atomLinks.find(a=>a.mapId===observed);
  const readout=root.querySelector('.atom-readout');
  if(readout)readout.innerHTML=`<strong>${pinned?'Pinned':'Hover'}: ${e(atom?.element||'atom')} · map ${observed}</strong><br>${!current().run?'3D correspondence unavailable until conditions are complete':link?'Same atom highlighted in both views':'Byproduct / reactant only · no main-product 3D counterpart'}`;
  if(viewer){
    if(halo)viewer.removeShape(halo);
    const a=link?viewer.getModel().selectedAtoms({index:link.index})[0]:null;
    halo=a?viewer.addSphere({center:{x:a.x,y:a.y,z:a.z},radius:.56,color:'#9364c4',opacity:.22}):null;
    viewer.render();
  }
  if(inspectorTab==='Atom'){const el=root.querySelector('.inspector-content');if(el)el.innerHTML=inspectorContent();}
}
function guideDialog() {
  const g=fixtures.secondaryMissing.reaction.guidedConditions;
  const dialog=document.createElement('dialog');dialog.className='dialog';
  dialog.innerHTML=`<header><h2>Review Guided Conditions</h2><button aria-label="Close condition review">×</button></header><div class="dialog-content"><p><strong>Design demonstration only.</strong> Applying switches to a separately validated static fixture. It does not run chemistry or change production settings.</p><ul>${g.requirements.map(r=>`<li><strong>${e(r.label)}:</strong> ${e(r.selectedLabel)} → ${e(r.requiredLabel)}</li>`).join('')}</ul><p>${e(g.limitations[0])}</p><label><input type="checkbox">I have reviewed all proposed replacements and model limitations.</label></div><footer><button data-cancel>Cancel</button><button class="primary" data-apply disabled>Show condition-complete fixture</button></footer>`;
  document.body.append(dialog);dialog.showModal();
  const close=()=>{dialog.close();dialog.remove();};
  dialog.querySelector('header button').onclick=close;dialog.querySelector('[data-cancel]').onclick=close;
  dialog.querySelector('input').onchange=ev=>dialog.querySelector('[data-apply]').disabled=!ev.target.checked;
  dialog.querySelector('[data-apply]').onclick=()=>{qualified=true;mode='compare';studioStep=3;close();render();};
  dialog.addEventListener('cancel',()=>dialog.remove());
}
function bind() {
  root.querySelector('.tools-toggle')?.addEventListener('click',ev=>{
    const open=ev.currentTarget.getAttribute('aria-expanded')!=='true';
    ev.currentTarget.setAttribute('aria-expanded',String(open));root.querySelector('.app-nav').classList.toggle('is-open',open);
  });
  root.querySelectorAll('[data-mode]').forEach(b=>{if(b.tagName==='BUTTON')b.onclick=()=>{mode=b.dataset.mode;render();};});
  root.querySelectorAll('[data-inspector]').forEach(b=>b.onclick=()=>{inspectorTab=b.dataset.inspector;render();});
  root.querySelectorAll('[data-mobile]').forEach(b=>b.onclick=()=>{
    root.querySelector('.app').dataset.mobilePanel=b.dataset.mobile;
    root.querySelectorAll('.mobile-work-tabs button').forEach(t=>t.setAttribute('aria-pressed',String(t.dataset.mobile===b.dataset.mobile)));
  });
  root.querySelectorAll('[data-studio]').forEach(b=>b.onclick=()=>{studioStep=Number(b.dataset.studio);render();});
  root.querySelectorAll('[data-mechanism]').forEach(b=>b.onclick=()=>{mechanismShown=b.dataset.mechanism==='step';render();});
  root.querySelectorAll('[data-expert]').forEach(b=>b.onclick=()=>{researchTab=b.dataset.expert;render();});
  root.querySelectorAll('[data-observe]').forEach(b=>b.onclick=()=>selectAtom(Number(b.dataset.observe),true));
  root.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{
    if(b.dataset.action==='guidance')guideDialog();
    if(b.dataset.action==='clear-atom'){pinned=false;updateAtom();}
    if(b.dataset.action==='example'){fixtureName='sn2';mode='compare';render();}
    if(b.dataset.action==='inspect-conditions'){inspectorTab='Conditions';render();}
  });
  root.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>{
    if(!viewer)return;
    if(b.dataset.camera==='fit'){viewer.zoomTo();viewer.zoom(2.1);}
    if(b.dataset.camera==='in')viewer.zoom(1.15);
    if(b.dataset.camera==='out')viewer.zoom(.87);
    if(b.dataset.camera==='rotate'){
      const rotating=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(rotating));viewer.spin(rotating?'y':false,rotating?.5:0);
    }
    viewer.render();
  });
}
document.querySelectorAll('[data-concept]').forEach(b=>b.onclick=()=>{concept=b.dataset.concept;studioStep=3;query.set('concept',concept);history.replaceState(null,'',`?${query}`);render();});
document.querySelector('#fixture-choice').onchange=ev=>{fixtureName=ev.target.value;qualified=false;observed=1;mode=fixtureName==='sn2'?'compare':'2d';studioStep=3;render();};
let resizeTimer;
window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{drawDiagram();updateAtom();viewer?.resize();viewer?.render();},150);});
render();
