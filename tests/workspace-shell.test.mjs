import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const source = await read('src/workspace-shell.ts');
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { mountWorkspaceShell, workspaceIcon } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.children = []; this.parent = null;
    this.attributes = {}; this.classes = new Set(); this.hidden = false; this._text = '';
    this.classList = { add: (...names) => names.forEach(name => this.classes.add(name)), contains: name => this.classes.has(name) };
  }
  set className(value) { this.classes = new Set(value.split(/\s+/).filter(Boolean)); }
  get className() { return [...this.classes].join(' '); }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key] ?? null; }
  move(child) {
    if (child.parent) child.parent.children.splice(child.parent.children.indexOf(child), 1);
    child.parent = this;
  }
  append(...children) { for (const child of children) { this.move(child); this.children.push(child); } }
  prepend(child) { this.move(child); this.children.unshift(child); }
  closest(tag) { for (let node = this; node; node = node.parent) if (node.tagName === tag.toUpperCase()) return node; return null; }
  descendants() { return this.children.flatMap(child => [child, ...child.descendants()]); }
  matches(selector) {
    if (selector.startsWith('.')) return this.classes.has(selector.slice(1));
    if (selector === 'nav[aria-label="Project pages"]') return this.tagName === 'NAV' && this.attributes['aria-label'] === 'Project pages';
    return this.tagName === selector.toUpperCase();
  }
  querySelectorAll(selector) {
    if (selector.startsWith(':scope > ')) return this.children.filter(child => child.matches(selector.slice(9)));
    return this.descendants().filter(child => child.matches(selector));
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
}

function fixture(callback, brandOnly = false) {
  const original = globalThis.document;
  const body = new Element('body');
  globalThis.document = { body, createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag) };
  try {
    const shell = new Element('main'), header = new Element('header'), nav = new Element('nav');
    nav.setAttribute('aria-label', 'Project pages');
    const brand = new Element('a'); brand.className = 'site-brand'; brand.textContent = 'Molecule Playground';
    const links = ['/', '/explore.html', '/builder.html', '/reaction-lab.html', '/calculators.html'].map((route, index) => {
      const link = new Element('a'); link.setAttribute('href', route); link.textContent = ['Home', 'Explore', 'Builder', 'Reaction Lab', 'Calculators'][index];
      if (index === 2) link.setAttribute('aria-current', 'page');
      return link;
    });
    const heading = new Element('h1'); heading.textContent = 'Existing tool';
    header.append(brandOnly ? brand : heading, nav); nav.append(...links);
    const tool = new Element('section'); tool.setAttribute('id', 'existing-tool');
    shell.append(header, tool); body.append(shell);
    callback({ shell, header, nav, brand, links, heading, tool, body });
  } finally { globalThis.document = original; }
}

test('shared shell moves the original navigation without replacing links or tools', () => fixture(({ shell, nav, links, tool, header }) => {
  const listener = () => {}; links[2].onclick = listener;
  mountWorkspaceShell(shell);
  const rail = shell.querySelector('.workspace-rail');
  assert.ok(rail);
  assert.equal(rail.querySelector('nav'), nav);
  assert.deepEqual(nav.querySelectorAll('a'), links);
  assert.equal(links[2].onclick, listener);
  assert.equal(links[2].getAttribute('aria-current'), 'page');
  assert.equal(tool.parent, shell);
  assert.equal(header.hidden, false, 'tool title stays visible');
}));

test('Home/Calculators brand is reused and their empty former top bar is hidden', () => fixture(({ shell, brand, header }) => {
  mountWorkspaceShell(shell);
  assert.equal(shell.querySelector('.workspace-brand'), brand);
  assert.equal(brand.textContent, 'Molecule\nPlayground');
  assert.equal(brand.getAttribute('aria-label'), 'Molecule Playground home');
  assert.equal(brand.href, '/');
  assert.equal(header.hidden, true);
}, true));

test('shell initialization is idempotent and does not duplicate icons or navigation', () => fixture(({ shell }) => {
  mountWorkspaceShell(shell); mountWorkspaceShell(shell);
  assert.equal(shell.querySelectorAll('.workspace-rail').length, 1);
  assert.equal(shell.querySelectorAll('nav').length, 1);
  assert.equal(shell.querySelectorAll('svg').length, 5);
}));

test('shared route icons are decorative, non-focusable vectors beside real link labels', () => fixture(({ shell, links }) => {
  mountWorkspaceShell(shell);
  for (const link of links) {
    const icon = link.querySelector('svg');
    assert.equal(icon.getAttribute('aria-hidden'), 'true');
    assert.equal(icon.getAttribute('focusable'), 'false');
    assert.equal(icon.getAttribute('viewBox'), '0 0 24 24');
    assert.ok(icon.innerHTML.includes('<'));
    assert.ok(link.textContent.length);
  }
  assert.notEqual(links[0].querySelector('svg').innerHTML, links[4].querySelector('svg').innerHTML);
  assert.equal(workspaceIcon('<script>untrusted</script>').innerHTML, links[1].querySelector('svg').innerHTML);
}));

test('missing navigation fails explicitly without hiding any tool', () => fixture(({ shell, nav, tool }) => {
  nav.setAttribute('aria-label', 'Different navigation');
  assert.throws(() => mountWorkspaceShell(shell), /existing project navigation/);
  assert.equal(tool.hidden, false);
  assert.equal(shell.querySelector('.workspace-rail'), null);
}));

test('shared shell is presentation-only and cannot alter chemistry, stored compounds or calculations', () => {
  assert.doesNotMatch(source, /fetch\(|sessionStorage|localStorage|\.focus\(|scrollTo|setStyle|addModel|molarMass|smiles|atomMap|calculateReaction/);
  assert.doesNotMatch(source, /addEventListener/, 'existing route links keep ordinary native navigation');
});

test('all five pages use the same shell and CSS, including the static Home build entry', async () => {
  assert.match(await read('index.html'), /type="module" src="\/src\/home\.ts"/);
  for (const path of ['src/home.ts', 'src/main.ts', 'src/builder.ts', 'src/calculators.ts']) {
    const text = await read(path);
    assert.match(text, /mountWorkspaceShell/);
    assert.match(text, /import '\.\/workspace-shell\.css'/);
  }
  assert.match(await read('src/reaction-workspace.ts'), /mountWorkspaceShell\(shell\)/);
  assert.match(await read('src/reaction-lab.ts'), /import '\.\/workspace-shell\.css'/);
});

test('theme preserves semantic errors, scientific diagram colors and embedded editor styling', async () => {
  const css = await read('src/workspace-shell.css');
  assert.doesNotMatch(css, /\.atom-target|\.atom-glow|\.atom-oxygen|\.atom-hydrogen|\.bond-swatch|\.is-electron/);
  assert.match(css, /:not\(:where\(\.ketcher-frame \*\)\)/);
  assert.match(css, /\.viewer-status\.is-error \{ color: var\(--ui-danger\)/);
  assert.match(css, /strong:not\(\.is-valid\):not\(\.is-invalid\)/);
  assert.doesNotMatch(css, /(?:solution-error|calculator-error|calc-error)\s*\{/);
});

test('responsive shell reserves desktop rail space and switches to flowing mobile navigation', async () => {
  const css = await read('src/workspace-shell.css');
  assert.match(css, /grid-template-columns: 196px minmax\(0, 1fr\)/);
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /\.workspace-shell \.workspace-rail \{ position: static; height: auto/);
  assert.match(css, /\.workspace-shell \.workspace-nav \{ display: flex; flex-wrap: wrap/);
  assert.match(css, /\.workspace-shell #calculator-topic \{ display: block/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /\[hidden\] \{ display: none !important/);
});

test('Builder startup guard and Explorer full-identity wrapping remain installed', async () => {
  assert.match(await read('src/builder.ts'), /guardEditorStartup\(editorHost\)/);
  assert.match(await read('src/styles.css'), /\.molecule-card__text strong, #molecule-title, #search-status\s*\{\s*overflow-wrap: anywhere/);
  assert.match(await read('src/main.ts'), /moleculeTitle\.textContent = molecule\.name/);
});
