import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const startupSource = await read('src/editor-startup.ts');
const compiled = ts.transpileModule(startupSource, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { guardEditorStartup } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
function startup(inert = false) {
  const attributes = new Map();
  const host = { inert, setAttribute: (k, v) => attributes.set(k, v), removeAttribute: k => attributes.delete(k) };
  const frames = [];
  const release = guardEditorStartup(host, callback => { frames.push(callback); return frames.length; });
  return { host, attributes, frames, release };
}
test('editor startup prevents clipboard autofocus until initialization and restoration finish', () => {
  const { host, attributes, frames, release } = startup();
  assert.equal(host.inert, true);
  assert.equal(attributes.get('aria-busy'), 'true');
  assert.equal(frames.length, 0, 'there is no early timer that races draft restoration');
  release();
  frames.shift()(); assert.equal(host.inert, true);
  frames.shift()(); assert.equal(host.inert, false);
  assert.equal(attributes.has('aria-busy'), false);
});
test('editor guard releases once and preserves a previously inert host', () => {
  const { host, frames, release } = startup(true);
  release(); release();
  assert.equal(frames.length, 1);
  frames.shift()(); frames.shift()();
  assert.equal(host.inert, true);
});
test('startup fix does not forcibly scroll, focus, or patch Ketcher internals', async () => {
  assert.doesNotMatch(startupSource, /scrollTo|scrollIntoView|\.focus\(|setInterval|prototype\./);
  const builder = await read('src/builder.ts');
  assert.match(builder, /guardEditorStartup\(editorHost\)/);
  assert.match(builder, /\.finally\(releaseEditorStartup\)/);
  assert.match(builder, /errorHandler:[\s\S]*?releaseEditorStartup\(\)/);
});
test('research layout mounts before the existing chemistry bindings and keeps live nodes', async () => {
  const lab = await read('src/reaction-lab.ts');
  assert.ok(lab.indexOf('const researchWorkspace = mountResearchWorkspace') < lab.indexOf('const inputA = required'));
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /workspace\.replaceChildren\(command, inspector, pathways, stage\)/);
  assert.doesNotMatch(ui, /fetch\(|localStorage|sessionStorage|cloneNode|EXAMPLES|productSmiles|molfile|setStyle|addModel|calculateReaction/);
  assert.match(ui, /stage\.replaceChildren\(confidenceStrip, net, toolbar, preview, \.\.\.afterPreview, dock\)/);
  assert.match(ui, /get\('#guided-conditions'\)/);
});
test('dialogs, inspector and tool controls have native semantics and named relationships', async () => {
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /dialog\.setAttribute\('aria-labelledby', titleNode\.id\)/);
  assert.match(ui, /dialog\.showModal\(\)/);
  assert.match(ui, /dialog\.close\(\)/);
  assert.match(ui, /control\.setAttribute\('aria-controls', pane\.id\)/);
  assert.match(ui, /control\.setAttribute\('aria-pressed'/);
  assert.doesNotMatch(ui, /role', 'tab'/, 'ordinary grouped buttons retain native keyboard behavior');
});
test('confidence tier stays visible while the full explanation remains in a native disclosure', async () => {
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /confidenceDetails\.append\(confidenceSummary, confidence\)/);
  assert.match(ui, /confidence\.textContent\?\.split\(' — '\)\[0\]/);
  assert.match(ui, /confidenceDetails\.hidden = confidence\.hidden/);
  assert.doesNotMatch(ui, /confidence\.textContent\s*=/);
});
test('mechanism navigation opens its containing tool and hidden mechanisms clear role highlights', async () => {
  const lab = await read('src/reaction-lab.ts');
  assert.match(lab, /researchWorkspace\.openDock\('mechanism'\); host\.open = true/);
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /if \(key !== 'mechanism'\) get<HTMLDetailsElement>\('#reaction-mechanism'\)\.open = false/);
});
test('new input matches reopen pathways instead of leaving rejection explanations hidden', async () => {
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /if \(!selected\) pathways\.open = true/);
  assert.match(ui, /desktop\.addEventListener\('change'/);
});
test('pathway collapse preserves visible user focus but synthetic rematches never steal it', async () => {
  const ui = await read('src/reaction-workspace.ts');
  assert.match(ui, /if \(event\.isTrusted\) pathwaySummary\.focus\(\{ preventScroll: true \}\)/);
  assert.match(await read('src/reaction-conditions.ts'), /Use Edit conditions to review these settings/);
  assert.doesNotMatch(await read('src/reaction-conditions.ts'), /settings above/);
});
test('Explorer wraps full names, formulas and result cards without discarding identity text', async () => {
  const css = await read('src/styles.css');
  assert.match(css, /\.molecule-card__text strong, #molecule-title, #search-status\s*\{\s*overflow-wrap: anywhere/);
  assert.match(css, /\.viewer-toolbar > div:first-child[^}]*min-width: 0/);
  assert.match(css, /\.viewer-toolbar \.formula[^}]*max-width: 100%[^}]*overflow-wrap: anywhere/);
  const main = await read('src/main.ts');
  assert.match(main, /moleculeTitle\.textContent = molecule\.name/);
});
test('light-blue workspace is scoped, responsive and leaves chemistry diagram styling alone', async () => {
  const css = await read('src/reaction-research.css');
  assert.match(css, /body\.reaction-research-page/);
  assert.match(css, /--ui-bg: #f4f9ff/);
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /prefers-reduced-motion/);
  assert.doesNotMatch(css, /\.atom-target|\.atom-glow|\.bond-swatch|\.is-electron-source/);
  assert.match(css, /\.lab-research \[hidden\] \{ display: none !important/);
});
function luminance(hex) {
  const c = hex.match(/../g).map(v => parseInt(v, 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return c[0] * .2126 + c[1] * .7152 + c[2] * .0722;
}
test('blue primary and muted text meet AA contrast against their actual surfaces', () => {
  for (const [a, b] of [['ffffff', '21639b'], ['52677c', 'f4f9ff'], ['173c5a', 'e3f1ff'], ['174c78', 'c6e2ff']]) {
    const [dark, light] = [luminance(a), luminance(b)].sort((x, y) => x - y);
    assert.ok((light + .05) / (dark + .05) >= 4.5, `${a}/${b}`);
  }
});
