import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');
const source = await read('src/viewer-controls.ts');
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { mountViewerControls } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

class Element {
  children = []; attributes = {}; listeners = {}; hidden = false; disabled = false;
  setAttribute(key, value) { this.attributes[key] = value; }
  append(child) { this.children.push(child); }
  addEventListener(event, handler) { this.listeners[event] = handler; }
  insertAdjacentElement(where, child) { assert.equal(where, 'afterend'); this.after = child; }
}
function fixture(callback, noViewer = false) {
  const previous = globalThis.document;
  globalThis.document = { createElement: () => new Element() };
  try {
    const calls = [];
    const viewer = Object.fromEntries(['zoomTo', 'zoom', 'rotate', 'render'].map(name => [name, (...args) => calls.push([name, ...args])]));
    const host = new Element();
    const controls = mountViewerControls(host, noViewer ? undefined : viewer);
    callback({ controls, bar: host.after, buttons: host.after.children, calls });
  } finally { globalThis.document = previous; }
}

test('camera toolbar has seven named native buttons and starts disabled', () => fixture(({ bar, buttons }) => {
  assert.equal(bar.attributes.role, 'group');
  assert.equal(bar.attributes['aria-label'], '3D view controls');
  assert.equal(buttons.length, 7);
  assert.deepEqual(buttons.map(b => b.attributes['aria-label']), ['Fit molecule', 'Zoom in', 'Zoom out', 'Rotate left', 'Rotate right', 'Rotate up', 'Rotate down']);
  assert.ok(buttons.every(b => b.disabled && b.type === 'button'));
  assert.ok(buttons.slice(1).every(b => b.innerHTML.includes('aria-hidden="true"')));
}));

test('disabled camera controls cannot manipulate an unready or conditional viewer', () => fixture(({ buttons, calls, controls }) => {
  for (const button of buttons) button.listeners.click();
  assert.deepEqual(calls, []);
  controls.setEnabled(true); controls.setEnabled(false);
  buttons[0].listeners.click(); assert.deepEqual(calls, []);
}));

test('fit and zoom operate on the camera only and render once per action', () => fixture(({ controls, buttons, calls }) => {
  controls.setEnabled(true);
  for (const button of buttons.slice(0, 3)) button.listeners.click();
  assert.deepEqual(calls, [['zoomTo'], ['render'], ['zoom', 1.2], ['render'], ['zoom', 1 / 1.2], ['render']]);
  assert.doesNotMatch(source, /addModel|setStyle|atomLinks|fetch\(|setInterval|requestAnimationFrame/);
}));

test('rotation has both axes and directions with no automatic animation', () => fixture(({ controls, buttons, calls }) => {
  controls.setEnabled(true);
  for (const button of buttons.slice(3)) button.listeners.click();
  assert.deepEqual(calls.filter(c => c[0] === 'rotate'), [['rotate', -15, 'y'], ['rotate', 15, 'y'], ['rotate', -15, 'x'], ['rotate', 15, 'x']]);
}));

test('missing WebGL stays disabled; view visibility is explicitly controlled', () => fixture(({ controls, buttons, bar, calls }) => {
  controls.setEnabled(true); assert.ok(buttons.every(b => b.disabled));
  controls.setVisible(false); assert.equal(bar.hidden, true);
  controls.setVisible(true); assert.equal(bar.hidden, false);
  buttons[0].listeners.click(); assert.deepEqual(calls, []);
}, true));

test('all five routes load the shared visual layer and provide keyboard skip links', async () => {
  assert.match(await read('index.html'), /href="\/src\/ui-system\.css"/);
  for (const file of ['src/main.ts', 'src/builder.ts', 'src/reaction-lab.ts', 'src/calculators.ts']) {
    assert.match(await read(file), /import '\.\/ui-system\.css'/);
  }
  for (const file of ['index.html', 'calculators.html', 'src/main.ts', 'src/builder.ts', 'src/reaction-lab.ts']) {
    const text = await read(file);
    assert.match(text, /class="skip-link" href="#main-content"/);
    assert.match(text, /<main[^>]*id="main-content"[^>]*tabindex="-1"/);
  }
});

test('presentation preserves reaction confidence gates, conditional labeling and stale-model resets', async () => {
  const lab = await read('src/reaction-lab.ts');
  assert.match(lab, /button\.dataset\.preview = reaction\.assessment\?\.canRun === false \|\| reaction\.assessment\?\.evidence \? 'conditional' : 'model'/);
  assert.match(lab, /view3D\.disabled = !canRun/);
  assert.match(lab, /cameraControls\.setVisible\(mode !== '2d'\)/);
  for (const file of ['src/main.ts', 'src/builder.ts', 'src/reaction-lab.ts']) {
    const text = await read(file);
    assert.match(text, /cameraControls\.setEnabled\(false\)/);
    assert.match(text, /cameraControls\.setEnabled\(true\)/);
  }
});

function luminance(hex) {
  const rgb = hex.match(/[\da-f]{2}/gi).map(c => parseInt(c, 16) / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
}
const contrast = (a, b) => { const [dark, light] = [luminance(a), luminance(b)].sort((x, y) => x - y); return (light + .05) / (dark + .05); };
test('shared text and focus tokens meet measured contrast targets', async () => {
  const css = await read('src/ui-system.css');
  const token = name => {
    const value = css.match(new RegExp(`--ui-${name}:\\s*#([\\da-f]{6});`, 'i'));
    assert.ok(value, `actual CSS defines ${name}`);
    return value[1];
  };
  for (const [text, background] of [[token('text'),token('surface')], [token('muted'),token('subtle')], ['ffffff',token('brand')], [token('warning'),token('warning-bg')], [token('danger'),'fff1f1']]) {
    assert.ok(contrast(text, background) >= 4.5, `${text} on ${background}`);
  }
  assert.ok(contrast(token('focus'), token('bg')) >= 3);
  assert.ok(contrast(token('control-border'), token('surface')) >= 3);
});

test('shared styles exclude Ketcher internals and respect reduced motion and hidden camera controls', async () => {
  const css = await read('src/ui-system.css');
  assert.match(css, /not\(:where\(\.ketcher-frame \*\)\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /\.viewer-controls\[hidden\] \{ display: none; \}/);
  assert.doesNotMatch(css, /\.atom-target|\.bond-swatch|\.atom-glow/);
});
