import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import ts from 'typescript';
const read = p => readFile(new URL(`../${p}`, import.meta.url), 'utf8');
const compile = s => ts.transpileModule(s, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const load = async p => import(`data:text/javascript;base64,${Buffer.from(compile(await read(p))).toString('base64')}`);
const { calculateReaction, calculateRequiredAmounts, copyCalculationContext } = await load('src/reaction-calculator.ts');
const { conditionLabel, conditionGuidance, conciseConditionNote } = await load('src/reaction-conditions.ts');
const { GuidedConditionsPanel } = await load('src/guided-reaction-conditions.ts');
const source = await read('src/reaction-lab.ts');
const rows = JSON.parse(execFileSync(fileURLToPath(new URL('../.venv/bin/python', import.meta.url)), ['-c', `
import json
from server import chemistry_server as s
b={'solvent':'aqueous-protic','oxidationStage':'further'}
out=[]
for metal in ['Na','K']:
 for reverse in [False,True]:
  for extra in [{},{'catalyst':'none','temperature':'ambient'},{'pressure':'unknown'},{'workup':'aqueous-release'},{'catalyst':'radical'},{'temperature':'heated'}]:
   a,r={'smiles':'CCC=O'},{'smiles':f'[{metal}+].[O-]Cl'}
   if reverse:a,r=r,a
   result=s.match_reactions(a,r,{**b,**extra})
   out.append({'metal':metal,'reverse':reverse,'extra':extra,'supportState':result['supportState'],'reaction':result['reactionOptions'][0]})
c={k:v for k,v in {'solvent':'aqueous-protic','temperature':'ambient','catalyst':'none','oxidationStage':'first'}.items()}
g=s.match_reactions({'smiles':'CC(O)C'},'sodium-hypochlorite',c)['reactionOptions'][0]['guidedConditions']
p=s.match_reactions({'smiles':'CCO'},'sodium-hypochlorite',c)['reactionOptions'][0]['assessment']
print(json.dumps({'rows':out,'waterGuide':g,'primary':p}))
`], { cwd: fileURLToPath(new URL('..', import.meta.url)), encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 }));
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);

for (const { metal, reverse, extra, supportState, reaction: r } of rows.rows) {
  test(`aldehyde reporting arithmetic/confidence: ${metal}, reverse=${reverse}, ${JSON.stringify(extra)}`, () => {
    const basis = r.stoichiometry, ctx = copyCalculationContext(basis.context);
    const oxidantMass = { Na: 22.990, K: 39.098 }[metal] + 35.453 + 15.999;
    const a = reverse ? 1 : 0, b = 1 - a;
    close(basis.product.molarMass, 74.079); // Independent C3H6O2 atom sum.
    close(basis.reactants.find(x => x.inputSlot === a).molarMass, 58.080);
    close(basis.reactants.find(x => x.inputSlot === b).molarMass, oxidantMass);
    const result = calculateReaction(basis, { [a]: { value: 2, unit: 'mmol' }, [b]: { value: oxidantMass, unit: 'mg' } });
    close(result.product.moles, 0.001); close(result.product.grams, 0.074079);
    assert.deepEqual(result.limitingInputs, [b]);
    const required = calculateRequiredAmounts(basis, { value: 0.148158, unit: 'g' });
    required.reactants.forEach(x => close(x.moles, 0.002));
    const allowed = !Object.keys(extra).some(k => !['catalyst', 'temperature'].includes(k))
      && !extra.pressure && !extra.workup && !['radical'].includes(extra.catalyst) && extra.temperature !== 'heated';
    assert.equal(r.assessment.canRun, allowed); assert.equal(ctx.canGenerate3D, allowed);
    assert.equal(supportState, 'Conditional'); assert.equal(r.assessment.evidence.conditionCompleteEligibility, false);
    assert.match(ctx.warning, /not isolated acid yields/); assert.match(ctx.warning, /Full salt masses/);
    assert.match(ctx.warning, /acid\/carboxylate speciation/); assert.match(ctx.warning, /complete conversion is assumed/);
    assert.match(conditionLabel(r.assessment), allowed ? /speciation\/work-up not established/ : /2D only/);
    assert.doesNotMatch(conditionLabel(r.assessment), /Unfavorable|Strong match/);
    assert.match(conditionGuidance(r.assessment), /Structure\/site supported/);
    if (!allowed) assert.match(conditionGuidance(r.assessment), /Conditional 2D remains available/);
  });
}

class Element {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {}; this.attributes = {}; this.disabled = false; this.checked = false; this.hidden = false; this._text = ''; }
  set textContent(s) { this._text = String(s); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; this._text = ''; }
  setAttribute(k, v) { this.attributes[k] = v; }
  addEventListener(k, f) { (this.listeners[k] ??= []).push(f); }
  async emit(k) { await Promise.all((this.listeners[k] ?? []).map(f => f({ target: this }))); }
}
const all = host => host.children.flatMap(x => [x, ...all(x)]);

test('generic water conflict headline and unchecked consent agree', async () => {
  const old = globalThis.document; globalThis.document = { createElement: tag => new Element(tag) };
  try {
    const host = new Element('section'); let calls = 0;
    const panel = new GuidedConditionsPanel(host, async () => { calls += 1; }); panel.setGuidance(rows.waterGuide, 'fresh');
    assert.match(host.textContent, /Review conflicting selections/); assert.match(host.textContent, /replace selected setting/);
    const checkbox = all(host).find(x => x.tagName === 'INPUT'), button = all(host).find(x => x.tagName === 'BUTTON');
    assert.equal(checkbox.checked, false); assert.equal(button.disabled, true);
    await button.emit('click'); assert.equal(calls, 0);
    checkbox.checked = true; await checkbox.emit('change'); await button.emit('click'); assert.equal(calls, 1);
    panel.clear(); await button.emit('click'); assert.equal(calls, 1);
  } finally { if (old === undefined) delete globalThis.document; else globalThis.document = old; }
});

test('primary guidance does not invite finding an unimplemented selector', () => {
  assert.equal(rows.primary.canRun, false);
  const text = conditionGuidance(rows.primary);
  assert.match(text, /No existing setting enables selective aldehyde 3D/);
  assert.match(text, /No aldehyde-selective/);
  assert.doesNotMatch(text, /until these requirements or model limitations are resolved/);
});

test('deduplication retains caveats but removes repeated condition sentences', () => {
  const text = 'catalyst: Ordinary metal can over-reduce. Ordinary metal can over-reduce. No ratio is predicted. No ratio is predicted.';
  assert.equal(conciseConditionNote(text), 'catalyst: Ordinary metal can over-reduce. No ratio is predicted.');
  assert.equal(conciseConditionNote('pH, pressure and stopping are unknown.'), 'pH, pressure and stopping are unknown.');
});

test('condition fields have friendly names including oxidation stage', () => {
  const text = conditionGuidance({ state: 'incomplete', note: '', evidence: { missingRequiredSettings: ['oxidationStage'], canGenerate3D: false } });
  assert.match(text, /oxidation stage/); assert.doesNotMatch(text, /oxidationStage/);
});

test('every blocked reaction receives an explicit 2D-only inspector caption', () => {
  assert.match(source, /reaction\.assessment\?\.canRun === false \? 'Conditional 2D only; 3D is blocked/);
  assert.match(source, /atomInspector\.setDiagram\(payload\.atoms/);
});

test('condition changes remember only the selected address and rematch it', () => {
  const begin = source.indexOf("for (const select of [solventInput, temperatureInput, catalystInput, oxidationStageInput");
  const block = source.slice(begin, source.indexOf("exampleCards.addEventListener", begin));
  const callback = compile(`function change() {${block.slice(block.indexOf("=> {") + 4, block.lastIndexOf('}));'))}}`);
  const calls = [], old = { id: 'selected-site', assessment: { canRun: true } };
  const change = new Function('selectedReaction', 'saveDraft', 'updateMatches', `${callback}; return change;`)(old, () => calls.push('save'), id => calls.push(['rematch', id]));
  change(); assert.deepEqual(calls, ['save', ['rematch', 'selected-site']]);
  assert.doesNotMatch(block, /showProduct3D|productReady\s*=\s*true|canRun\s*=/);
  const rematch = source.slice(source.indexOf('async function updateMatches('), source.indexOf("required<HTMLFormElement>('#reactant-form')"));
  assert.ok(rematch.indexOf('resetResult();') < rematch.indexOf("fetch('/api/reactions/match'"));
  assert.match(rematch, /requestRevision !== revision/); assert.match(rematch, /if \(preferredButton\) preferredButton\.click\(\)/);
  assert.match(rematch, /reaction\.id === preferredReactionId/);
});

test('structure changes do not preserve a selected-site preference', () => {
  const begin = source.indexOf("inputs.forEach((input, index) => input.addEventListener('input'");
  const block = source.slice(begin, source.indexOf('for (const select', begin));
  assert.match(block, /updateMatches\(\)/); assert.doesNotMatch(block, /preferredReactionId|\bselectedId\b/);
});

test('new aldehyde confidence uses existing controls and no new guide or formula', async () => {
  const information = await read('server/reaction_information.py');
  assert.match(information, /No acidification or carboxylate transformation is implemented/);
  assert.match(source, /reaction\.mechanism === 'Aldehyde oxidation'\) conditionAssessment\.textContent/);
  assert.match(source, /reactionCalculator\.setReaction\(reaction\.stoichiometry\)/);
});
