import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/bond-measurements.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { BondMeasurements, measureGeometry } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`
);

const point = (x, y, z) => ({ x, y, z });
const close = (actual, expected, tolerance = 1e-9) => {
  assert.ok(Math.abs(actual - expected) < tolerance, `${actual} should be close to ${expected}`);
};

test('distance reports the Euclidean separation in angstroms', () => {
  const result = measureGeometry('distance', [point(1, 2, 3), point(4, 6, 3)]);
  assert.equal(result.unit, 'Å');
  close(result.value, 5);
  close(measureGeometry('distance', [point(0, 0, 0), point(1, 1, 1)]).value, Math.sqrt(3));
  close(measureGeometry('distance', [point(1, 2, 3), point(1, 2, 3)]).value, 0);
});

test('angle is centered on the second atom and supports 0, 90, and 180 degrees', () => {
  const center = point(0, 0, 0);
  for (const [third, expected] of [[point(2, 0, 0), 0], [point(0, 1, 0), 90], [point(-1, 0, 0), 180]]) {
    const result = measureGeometry('angle', [point(1, 0, 0), center, third]);
    assert.equal(result.unit, '°');
    close(result.value, expected);
  }
  close(measureGeometry('angle', [point(1, 1, 0), center, point(0, 1, 0)]).value, 45);
});

test('bundled water reference coordinates measure 104.5 degrees, not a forced VSEPR angle', async () => {
  const sdf = await readFile(new URL('../public/molecules/water-reference.sdf', import.meta.url), 'utf8');
  const lines = sdf.split('\n');
  assert.equal(Number(lines[3].slice(0, 3)), 3);
  assert.equal(Number(lines[3].slice(3, 6)), 2);
  const atoms = lines.slice(4, 7).map((line) => ({
    x: Number(line.slice(0, 10)), y: Number(line.slice(10, 20)), z: Number(line.slice(20, 30)),
    elem: line.slice(31, 34).trim(),
  }));
  assert.deepEqual(atoms.map(({ elem }) => elem), ['O', 'H', 'H']);
  assert.equal(measureGeometry('angle', [atoms[1], atoms[0], atoms[2]]).value.toFixed(1), '104.5');
  for (const hydrogen of atoms.slice(1)) close(measureGeometry('distance', [atoms[0], hydrogen]).value, .958, .0001);
  assert.deepEqual(lines.slice(7, 9).map((line) => line.trim().split(/\s+/).slice(0, 3)), [['1', '2', '1'], ['1', '3', '1']]);
  assert.match(sdf, /GEOMETRY_PROVENANCE/);
  assert.doesNotMatch(sdf, /<PUBCHEM_CONFORMER_ID>|<PUBCHEM_MMFF94_ENERGY>/);

  // The retained original is a different conformer. Measurement must report
  // its actual angle rather than silently snapping water to a reference value.
  const original = (await readFile(new URL('../public/molecules/water.sdf', import.meta.url), 'utf8'))
    .split('\n').slice(4, 7).map((line) => ({
      x: Number(line.slice(0, 10)), y: Number(line.slice(10, 20)), z: Number(line.slice(20, 30)),
    }));
  assert.equal(measureGeometry('angle', [original[1], original[0], original[2]]).value.toFixed(1), '104.0');
});

const planar = [point(0, 1, 0), point(0, 0, 0), point(1, 0, 0), point(1, 1, 0)];
const orthogonal = [point(0, 1, 0), point(0, 0, 0), point(1, 0, 0), point(1, 0, 1)];

test('torsion reports planar 0/180 and signed orthogonal dihedrals in degrees', () => {
  const flat = measureGeometry('torsion', planar);
  assert.equal(flat.unit, '°');
  close(flat.value, 0);
  close(Math.abs(measureGeometry('torsion', [...planar.slice(0, 3), point(1, -1, 0)]).value), 180);
  const right = measureGeometry('torsion', orthogonal).value;
  const reflected = measureGeometry('torsion', orthogonal.map(({ x, y, z }) => point(x, y, -z))).value;
  close(Math.abs(right), 90);
  close(reflected, -right);
  close(measureGeometry('torsion', [...orthogonal].reverse()).value, right);
  close(Math.abs(measureGeometry('torsion', [...planar.slice(0, 3), point(1, .5, Math.sqrt(3) / 2)]).value), 60);
  assert.ok(right >= -180 && right <= 180);
});

test('measurements are unchanged by translation and a proper 3D rotation', () => {
  const transform = ({ x, y, z }) => point(z + 17, x - 22, y + 5);
  for (const [mode, atoms] of [
    ['distance', orthogonal.slice(0, 2)], ['angle', orthogonal.slice(0, 3)], ['torsion', orthogonal],
  ]) {
    close(measureGeometry(mode, atoms).value, measureGeometry(mode, atoms.map(transform)).value);
  }
});

test('each measurement rejects the wrong atom count and non-finite coordinates', () => {
  for (const [mode, count] of [['distance', 2], ['angle', 3], ['torsion', 4]]) {
    const atoms = orthogonal.slice(0, count);
    assert.throws(() => measureGeometry(mode, atoms.slice(1)), Error);
    assert.throws(() => measureGeometry(mode, [...atoms, point(2, 2, 2)]), Error);
    for (const value of [NaN, Infinity, -Infinity]) {
      for (const coordinate of ['x', 'y', 'z']) {
        assert.throws(() => measureGeometry(mode, [{ ...atoms[0], [coordinate]: value }, ...atoms.slice(1)]), Error);
      }
    }
  }
});

test('undefined angles and torsions reject zero-length axes or collinear planes', () => {
  const origin = point(0, 0, 0);
  assert.throws(() => measureGeometry('angle', [origin, origin, point(1, 0, 0)]), Error);
  assert.throws(() => measureGeometry('angle', [point(1, 0, 0), origin, origin]), Error);
  for (const atoms of [
    [point(0, 1, 0), origin, origin, point(1, 1, 0)],
    [point(-1, 0, 0), origin, point(1, 0, 0), point(1, 1, 0)],
    [point(0, 1, 0), origin, point(1, 0, 0), point(2, 0, 0)],
  ]) assert.throws(() => measureGeometry('torsion', atoms), Error);
});

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.listeners = new Map();
    this.attributes = new Map();
    this.className = '';
    this.dataset = {};
    this.style = {};
    this.id = '';
    this.hidden = false;
    this.disabled = false;
    this.value = '';
    this._textContent = '';
    this.classList = {
      add: (...names) => this.setClasses([...this.classes(), ...names]),
      remove: (...names) => this.setClasses(this.classes().filter((name) => !names.includes(name))),
      contains: (name) => this.classes().includes(name),
      toggle: (name, enabled) => {
        const chosen = enabled ?? !this.classes().includes(name);
        chosen ? this.classList.add(name) : this.classList.remove(name);
        return chosen;
      },
    };
  }
  classes() { return this.className.split(/\s+/).filter(Boolean); }
  setClasses(names) { this.className = [...new Set(names)].join(' '); }
  set textContent(value) { this.children = []; this._textContent = String(value); }
  get textContent() { return this._textContent + this.children.map((child) => child.textContent).join(''); }
  set innerHTML(value) { throw new Error(`Unsafe innerHTML write: ${value}`); }
  append(...children) {
    for (const child of children) { child.parentNode = this; this.children.push(child); }
    if (this.tagName === 'SELECT' && !this.value) this.value = this.children.find((child) => child.tagName === 'OPTION')?.value ?? '';
  }
  appendChild(child) { this.append(child); return child; }
  replaceChildren(...children) { this.children = []; this._textContent = ''; this.append(...children); }
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((child) => child !== this); }
  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (name.startsWith('data-')) this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = String(value);
  }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  addEventListener(name, callback) { this.listeners.set(name, [...(this.listeners.get(name) ?? []), callback]); }
  emit(name, extra = {}) {
    const event = { target: this, prevented: false, preventDefault() { this.prevented = true; }, ...extra };
    for (const callback of this.listeners.get(name) ?? []) callback(event);
    return event;
  }
  click() { if (!this.disabled) this.emit('click'); }
  contains(node) { return this === node || descendants(this).includes(node); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  querySelectorAll(selector) {
    return descendants(this).filter((element) => {
      if (selector.startsWith('.')) return element.classes().includes(selector.slice(1));
      if (selector.startsWith('#')) return element.id === selector.slice(1);
      const attribute = /^\[([^=\]]+)(?:="([^"]*)")?\]$/.exec(selector);
      if (attribute) return attribute[2] === undefined ? element.attributes.has(attribute[1]) : element.getAttribute(attribute[1]) === attribute[2];
      return element.tagName === selector.toUpperCase();
    });
  }
}

const descendants = (element) => element.children.flatMap((child) => [child, ...descendants(child)]);
function find(host, predicate) {
  const element = descendants(host).find(predicate);
  assert.ok(element, 'Expected measurement control was not rendered');
  return element;
}
const selectFor = (host) => find(host, (node) => node.tagName === 'SELECT');
const optionFor = (host, value) => find(selectFor(host), (node) => node.tagName === 'OPTION' && node.value === value);
function changeMode(host, mode) { const select = selectFor(host); select.value = mode; select.emit('change'); }
const atomButton = (host, name) => find(host, (node) => node.tagName === 'BUTTON' && node.textContent === name);
const pressed = (host) => descendants(host).filter((node) => node.tagName === 'BUTTON' && node.getAttribute('aria-pressed') === 'true').map((node) => node.textContent);

const atoms = [
  { index: 0, elem: 'C', ...orthogonal[0], bonds: [1] },
  { index: 1, elem: 'O', ...orthogonal[1], bonds: [0, 2] },
  { index: 2, elem: 'N', ...orthogonal[2], bonds: [1, 3] },
  { index: 3, elem: 'H', ...orthogonal[3], bonds: [2] },
];

function fixture(run, { hasViewer = true, options } = {}) {
  const previous = { present: Object.hasOwn(globalThis, 'document'), value: globalThis.document };
  globalThis.document = { createElement: (tagName) => new FakeElement(tagName) };
  const calls = { callbacks: [], shapes: [], labels: [], removedShapes: [], removedLabels: [], renders: 0 };
  const viewer = {
    setClickable(selection, enabled, callback) { calls.callbacks.push({ selection, enabled, callback }); },
    addSphere(spec) { const shape = { kind: 'sphere', spec }; calls.shapes.push(shape); return shape; },
    addLine(spec) { const shape = { kind: 'line', spec }; calls.shapes.push(shape); return shape; },
    addCylinder(spec) { const shape = { kind: 'cylinder', spec }; calls.shapes.push(shape); return shape; },
    addLabel(text, spec) { const label = { text, spec }; calls.labels.push(label); return label; },
    removeShape(shape) { calls.removedShapes.push(shape); },
    removeLabel(label) { calls.removedLabels.push(label); },
    removeAllShapes() { throw new Error('Do not remove unrelated shapes'); },
    removeAllLabels() { throw new Error('Do not remove unrelated labels'); },
    render() { calls.renders++; },
  };
  try {
    const host = new FakeElement('section');
    host.ownerDocument = globalThis.document;
    const panel = new BondMeasurements(host, hasViewer ? viewer : undefined, options);
    return run({ host, panel, viewer, calls });
  } finally {
    if (previous.present) globalThis.document = previous.value;
    else delete globalThis.document;
  }
}

test('measurement controls stay hidden when there is no usable 3D model or viewer', () => {
  fixture(({ host, panel }) => {
    assert.equal(host.hidden, true);
    panel.setAtoms([atoms[0]]);
    assert.equal(host.hidden, true);
    panel.setAtoms(atoms);
    assert.equal(host.hidden, false);
    panel.reset();
    assert.equal(host.hidden, true);
  });
  fixture(({ host, panel }) => {
    panel.setAtoms(atoms);
    assert.equal(host.hidden, true);
    assert.equal(panel.pickAtom(atoms[0]), false);
  }, { hasViewer: false });
});

test('native measurement selector is labeled and disables modes without enough atoms', () => fixture(({ host, panel }) => {
  panel.setAtoms(atoms.slice(0, 2));
  const select = selectFor(host);
  assert.equal(select.value, 'off');
  assert.equal(optionFor(host, 'distance').disabled, false);
  assert.equal(optionFor(host, 'angle').disabled, true);
  assert.equal(optionFor(host, 'torsion').disabled, true);
  const label = descendants(host).find((node) => node.tagName === 'LABEL' && /Measure/.test(node.textContent));
  assert.ok(label || /Measure/.test(select.getAttribute('aria-label') ?? ''), 'Measure must have an accessible label');
  panel.setAtoms(atoms.slice(0, 3));
  assert.equal(optionFor(host, 'angle').disabled, false);
  assert.equal(optionFor(host, 'torsion').disabled, true);
  panel.setAtoms(atoms);
  assert.equal(optionFor(host, 'torsion').disabled, false);
}));

test('atom buttons expose exact model indexes and can complete a distance using keyboard clicks', () => fixture(({ host, panel, calls }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  atomButton(host, 'C1').click();
  atomButton(host, 'O2').click();
  assert.deepEqual(pressed(host), ['C1', 'O2']);
  assert.match(host.textContent, /1(?:\.0+)?\s*Å/);
  assert.ok(calls.shapes.length >= 2);
  assert.ok(calls.labels.length > 0);
  assert.ok(calls.renders > 0);
  const indexed = [{ ...atoms[0], index: 7 }, { ...atoms[1], index: 12 }];
  panel.setAtoms(indexed);
  changeMode(host, 'distance');
  assert.ok(atomButton(host, 'C8'));
  assert.ok(atomButton(host, 'O13'));
}));

test('changing measurement mode clears the old selection and computes angles and torsions', () => fixture(({ host, panel }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  assert.equal(panel.pickAtom(atoms[0]), true);
  assert.equal(panel.pickAtom(atoms[1]), true);
  changeMode(host, 'angle');
  assert.deepEqual(pressed(host), []);
  for (const atom of atoms.slice(0, 3)) assert.equal(panel.pickAtom(atom), true);
  assert.match(host.textContent, /90(?:\.0+)?\s*°/);
  changeMode(host, 'torsion');
  assert.deepEqual(pressed(host), []);
  for (const atom of atoms) assert.equal(panel.pickAtom(atom), true);
  assert.match(host.textContent, /-?90(?:\.0+)?\s*°/);
  changeMode(host, 'off');
  assert.deepEqual(pressed(host), []);
  assert.equal(panel.pickAtom(atoms[0]), false);
}));

test('picking the same atom removes it and truncates later atoms while a new full-sequence click restarts', () => fixture(({ host, panel }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'torsion');
  atoms.forEach((atom) => panel.pickAtom(atom));
  assert.deepEqual(pressed(host), ['C1', 'O2', 'N3', 'H4']);
  panel.pickAtom(atoms[1]);
  assert.deepEqual(pressed(host), ['C1']);
  panel.pickAtom(atoms[0]);
  assert.deepEqual(pressed(host), []);
  changeMode(host, 'distance');
  panel.pickAtom(atoms[0]);
  panel.pickAtom(atoms[1]);
  panel.pickAtom(atoms[2]);
  assert.deepEqual(pressed(host), ['N3']);
}));

test('clear selection removes only measurement overlays and keeps the current mode', () => fixture(({ host, panel, calls }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  panel.pickAtom(atoms[0]);
  panel.pickAtom(atoms[1]);
  const ownedShapes = [...calls.shapes];
  const ownedLabels = [...calls.labels];
  find(host, (node) => node.tagName === 'BUTTON' && /Clear selection/i.test(node.textContent)).click();
  assert.deepEqual(pressed(host), []);
  assert.equal(selectFor(host).value, 'distance');
  assert.ok(ownedShapes.every((shape) => calls.removedShapes.includes(shape)));
  assert.ok(ownedLabels.every((label) => calls.removedLabels.includes(label)));
}));

test('a new model resets mode, selections, and overlays and ignores stale 3D callbacks', () => fixture(({ host, panel, calls }) => {
  panel.setAtoms(atoms);
  const oldCallback = calls.callbacks.at(-1).callback;
  changeMode(host, 'distance');
  oldCallback(atoms[0]);
  oldCallback(atoms[1]);
  assert.deepEqual(pressed(host), ['C1', 'O2']);
  const shapes = [...calls.shapes];
  const labels = [...calls.labels];
  panel.setAtoms(atoms.map((atom) => ({ ...atom, x: atom.x + 10 })));
  assert.equal(selectFor(host).value, 'off');
  assert.deepEqual(pressed(host), []);
  assert.ok(shapes.every((shape) => calls.removedShapes.includes(shape)));
  assert.ok(labels.every((label) => calls.removedLabels.includes(label)));
  changeMode(host, 'distance');
  oldCallback(atoms[0]);
  assert.deepEqual(pressed(host), []);
  panel.reset();
  calls.callbacks.at(-1).callback(atoms[1]);
  assert.equal(host.hidden, true);
  assert.deepEqual(pressed(host), []);
}));

test('invalid whole models fail closed instead of offering partial geometry or arbitrary atom indexes', () => fixture(({ host, panel }) => {
  const invalid = [
    [{ ...atoms[0], index: -1 }, atoms[1]],
    [{ ...atoms[0], index: .5 }, atoms[1]],
    [atoms[0], { ...atoms[1], index: 0 }],
    [atoms[0], { ...atoms[1], x: NaN }],
    [atoms[0], { ...atoms[1], y: Infinity }],
  ];
  for (const model of invalid) {
    panel.setAtoms(atoms);
    changeMode(host, 'distance');
    panel.pickAtom(atoms[0]);
    panel.setAtoms(model);
    assert.equal(host.hidden, true);
    assert.equal(panel.pickAtom(atoms[0]), false);
    assert.deepEqual(pressed(host), []);
  }
}));

test('unknown or corrupted picked atoms are rejected even while a valid model is active', () => fixture(({ host, panel }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  for (const atom of [
    { ...atoms[0], index: 100 }, { ...atoms[0], index: -1 },
    { ...atoms[0], x: NaN }, { ...atoms[0], z: Infinity },
    { ...atoms[0], elem: 'N' }, { ...atoms[0], x: atoms[0].x + 10 },
  ]) assert.equal(panel.pickAtom(atom), false);
  assert.deepEqual(pressed(host), []);
  assert.equal(panel.pickAtom(atoms[0]), true);
}));

test('external click routing does not overwrite another 3D atom inspector callback', () => fixture(({ host, panel, calls }) => {
  panel.setAtoms(atoms);
  assert.equal(calls.callbacks.length, 0);
  assert.equal(panel.pickAtom(atoms[0]), false);
  changeMode(host, 'distance');
  assert.equal(panel.pickAtom(atoms[0]), true);
  panel.reset();
  assert.equal(calls.callbacks.length, 0);
}, { options: { bindClicks: false } }));

test('undefined geometry is shown as a short error rather than NaN or an invented value', () => fixture(({ host, panel }) => {
  const linear = atoms.map((atom, index) => ({ ...atom, x: index, y: 0, z: 0 }));
  panel.setAtoms(linear);
  changeMode(host, 'torsion');
  linear.forEach((atom) => panel.pickAtom(atom));
  assert.doesNotMatch(host.textContent, /NaN|Infinity/);
  assert.match(host.textContent, /undefined|collinear|straight|cannot|not available/i);
  assert.equal(find(host, (node) => node.classes().includes('measurement-value')).hidden, true);
}));

test('an arbitrary interatomic distance is clearly distinguished from a bonded chain', () => fixture(({ host, panel }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  panel.pickAtom(atoms[0]);
  panel.pickAtom(atoms[2]);
  assert.match(host.textContent, /1\.414\s*Å/);
  assert.match(host.textContent, /not a bonded chain/i);
  panel.setAtoms(atoms.map(({ bonds, ...atom }) => atom));
  changeMode(host, 'distance');
  panel.pickAtom(atoms[0]);
  panel.pickAtom(atoms[2]);
  assert.doesNotMatch(host.textContent, /not a bonded chain/i);
}));

test('text measurements and resetting remain usable if WebGL drawing or overlay cleanup fails', () => fixture(({ host, panel, viewer }) => {
  panel.setAtoms(atoms);
  changeMode(host, 'distance');
  panel.pickAtom(atoms[0]);
  viewer.addLine = () => { throw new Error('WebGL context unavailable'); };
  viewer.removeShape = () => { throw new Error('WebGL context unavailable'); };
  viewer.removeLabel = () => { throw new Error('WebGL context unavailable'); };
  assert.doesNotThrow(() => panel.pickAtom(atoms[1]));
  assert.match(host.textContent, /1(?:\.0+)?\s*Å/);
  assert.doesNotThrow(() => panel.reset());
  assert.equal(host.hidden, true);
  assert.deepEqual(pressed(host), []);
}));

test('atom text is never interpreted as markup', () => fixture(({ host, panel }) => {
  const named = [{ ...atoms[0], elem: '<img src=x onerror=alert(1)>' }, atoms[1]];
  panel.setAtoms(named);
  if (!host.hidden) {
    changeMode(host, 'distance');
    panel.pickAtom(named[0]);
    panel.pickAtom(named[1]);
  }
  assert.equal(descendants(host).some((node) => ['IMG', 'SCRIPT', 'SVG'].includes(node.tagName)), false);
}));
