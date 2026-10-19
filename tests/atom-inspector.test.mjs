import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/atom-inspector.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
});
const { AtomInspector, indexModelAtoms, correspondenceMatches, pointerCoordinates } = await import(
  `data:text/javascript;base64,${Buffer.from(`${outputText}\n//# sourceURL=atom-inspector-under-test.js`).toString('base64')}`
);

const modelAtoms = [
  { index: 0, elem: 'C', x: 1, y: 2, z: 3 },
  { index: 1, elem: 'O', x: 4, y: 5, z: 6 },
];
const links = [{ index: 0, mapId: 7, element: 'C' }, { index: 1, mapId: 11, element: 'O' }];
const diagramAtom = (mapId, element, side = 'products', speciesIndex = 0, linkedTo3D = true) => ({
  mapId, element, label: `${element} atom ${mapId}`, side, speciesIndex,
  speciesName: side === 'products' ? 'Product' : 'Reactant', atomIndex: mapId,
  formalCharge: 0, lonePairs: element === 'O' ? 2 : 0, linkedTo3D,
});

test('model correspondence uses exact map IDs and indexes, not list ordering', () => {
  const indexed = indexModelAtoms([...links].reverse(), [...modelAtoms].reverse());
  assert.equal(indexed.get(7), modelAtoms[0]);
  assert.equal(indexed.get(11), modelAtoms[1]);
});

test('partial, duplicated, invalid, and element-mismatched model correspondence is rejected', () => {
  const invalid = [
    [[], modelAtoms], [links, []], [[links[0]], modelAtoms],
    [[links[0], { ...links[1], index: 2 }], modelAtoms],
    [[links[0], { ...links[1], index: 0 }], modelAtoms],
    [[links[0], { ...links[1], mapId: 7 }], modelAtoms],
    [[{ ...links[0], mapId: 0 }, links[1]], modelAtoms],
    [[{ ...links[0], mapId: 1.5 }, links[1]], modelAtoms],
    [[{ ...links[0], index: -1 }, links[1]], modelAtoms],
    [[{ ...links[0], element: 'O' }, links[1]], modelAtoms],
    [links, [{ ...modelAtoms[0], x: NaN }, modelAtoms[1]]],
    [links, [{ ...modelAtoms[0], z: Infinity }, modelAtoms[1]]],
    [links, [{ ...modelAtoms[0], index: 1 }, modelAtoms[1]]],
  ];
  for (const [candidateLinks, candidateAtoms] of invalid) {
    assert.equal(indexModelAtoms(candidateLinks, candidateAtoms).size, 0);
  }
});

test('diagram correspondence checks the entire main product while permitting reactants and byproducts', () => {
  const atoms = [diagramAtom(7, 'C'), diagramAtom(11, 'O'),
    diagramAtom(7, 'C', 'reactants'), diagramAtom(99, 'Br', 'products', 1, false)];
  assert.equal(correspondenceMatches(atoms, indexModelAtoms(links, modelAtoms)), true);
});

test('diagram correspondence rejects missing, duplicate, extra, and wrong-element product atoms', () => {
  const model = indexModelAtoms(links, modelAtoms);
  const invalid = [[], [diagramAtom(7, 'C')],
    [diagramAtom(7, 'C'), diagramAtom(7, 'C')],
    [diagramAtom(7, 'C'), diagramAtom(11, 'N')],
    [diagramAtom(7, 'C'), diagramAtom(11, 'O'), diagramAtom(12, 'H')],
    [diagramAtom(7, 'C', 'reactants'), diagramAtom(11, 'O', 'reactants')],
  ];
  for (const atoms of invalid) assert.equal(correspondenceMatches(atoms, model), false);
  assert.equal(correspondenceMatches([diagramAtom(7, 'C'), diagramAtom(11, 'O')], new Map()), false);
});

test('pointer picking normalizes CSS pixels correctly with page offsets and boundary positions', () => {
  const rect = { left: 40, top: 80, width: 200, height: 100 };
  assert.deepEqual(pointerCoordinates(140, 130, rect), { x: 0, y: 0 });
  assert.deepEqual(pointerCoordinates(40, 80, rect), { x: -1, y: 1 });
  assert.deepEqual(pointerCoordinates(240, 180, rect), { x: 1, y: -1 });
  assert.equal(pointerCoordinates(39, 130, rect), null);
  assert.equal(pointerCoordinates(140, 181, rect), null);
  assert.equal(pointerCoordinates(140, 130, { ...rect, width: 0 }), null);
  assert.equal(pointerCoordinates(140, 130, { ...rect, height: 0 }), null);
  assert.equal(pointerCoordinates(NaN, 130, rect), null);
});

class FakeElement {
  constructor(mapId = null) {
    this.listeners = new Map();
    this.attributes = new Map();
    this.classes = new Set();
    this.nodes = [];
    this.dataset = {};
    this.hidden = false;
    this.disabled = false;
    this.textContent = '';
    this.rect = { left: 40, top: 80, width: 200, height: 100, right: 240, bottom: 180 };
    this.scrollCalls = [];
    this.boundsReads = 0;
    this.classList = { toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name) };
    if (mapId !== null) this.setAttribute('data-atom-map', String(mapId));
  }
  addEventListener(type, callback) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), callback]);
  }
  emit(type, event = {}) {
    const input = { target: this, relatedTarget: null, pointerType: 'mouse', buttons: 0,
      preventDefault() { this.prevented = true; }, ...event };
    for (const callback of this.listeners.get(type) ?? []) callback(input);
    return input;
  }
  setAttribute(name, value) {
    this.attributes.set(name, value);
    if (name === 'data-atom-map') this.dataset.atomMap = value;
  }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  closest() { return this.attributes.has('data-atom-map') ? this : null; }
  contains(node) { return node === this || this.nodes.includes(node); }
  querySelectorAll() { return this.nodes; }
  querySelector(selector) {
    if (selector === 'canvas') return this.canvas;
    const attributes = [...selector.matchAll(/\[([\w-]+)="([^"]*)"\]/g)];
    return attributes.length ? this.nodes.find((node) => attributes.every(([, name, value]) => node.getAttribute(name) === value)) ?? null : null;
  }
  getBoundingClientRect() { this.boundsReads++; return this.rect; }
  scrollBy(options) {
    this.scrollCalls.push(options);
    for (const node of this.nodes) {
      const rect = node.rect;
      node.rect = { ...rect, left: rect.left - options.left, right: rect.right - options.left,
        top: rect.top - options.top, bottom: rect.bottom - options.top };
    }
  }
}

function fixture(run, onAtomClick) {
  const saved = new Map(['Element', 'window', 'requestAnimationFrame', 'cancelAnimationFrame', 'setTimeout', 'clearTimeout']
    .map((key) => [key, { present: Object.hasOwn(globalThis, key), value: globalThis[key] }]));
  const frames = new Map();
  const timers = new Map();
  let frameId = 0;
  let timerId = 0;
  const diagram = new FakeElement();
  const host = new FakeElement();
  const status = new FakeElement();
  const clear = new FakeElement();
  const window = new FakeElement();
  host.canvas = new FakeElement();
  const nodes = [new FakeElement(7), new FakeElement(11), new FakeElement(7), new FakeElement(99)];
  nodes.forEach((node, index) => {
    node.setAttribute('data-side', index < 2 ? 'products' : 'reactants');
    node.setAttribute('data-species-index', index === 3 ? '1' : '0');
    node.rect = { left: 120, top: 110, width: 24, height: 24, right: 144, bottom: 134 };
  });
  diagram.nodes = nodes;
  const calls = { spheres: [], labels: [], removedShapes: [], removedLabels: [], picks: [], renders: 0, clickCallbacks: [] };
  const viewer = {
    targetedObjects(x, y, atoms) { calls.picks.push({ x, y, atoms }); return this.nextHit ? [{ clickable: this.nextHit }] : []; },
    setClickable(selection, enabled, callback) { calls.clickCallbacks.push(callback); },
    addSphere(spec) { const shape = { spec: { ...spec }, updateStyle(style) { Object.assign(this.spec, style); } }; calls.spheres.push(shape); return shape; },
    removeShape(shape) { calls.removedShapes.push(shape); },
    addLabel(text, spec, selection, noShow) {
      const label = { text, spec, noShow, visible: true,
        hide() { this.visible = false; }, show() { this.visible = true; } };
      calls.labels.push(label); return label;
    },
    removeLabel(label) { calls.removedLabels.push(label); },
    render() { calls.renders++; },
  };
  globalThis.Element = FakeElement;
  globalThis.window = window;
  globalThis.requestAnimationFrame = (callback) => { frames.set(++frameId, callback); return frameId; };
  globalThis.cancelAnimationFrame = (id) => frames.delete(id);
  globalThis.setTimeout = (callback, delay) => { timers.set(++timerId, { callback, delay }); return timerId; };
  globalThis.clearTimeout = (id) => timers.delete(id);
  try {
    const inspector = new AtomInspector(diagram, host, viewer, status, clear, onAtomClick);
    inspector.setDiagram([diagramAtom(7, 'C'), diagramAtom(11, 'O'),
      diagramAtom(7, 'C', 'reactants'), diagramAtom(99, 'Br', 'reactants', 1, false)]);
    inspector.setModel(modelAtoms, links);
    const flush = () => {
      const pending = [...frames.values()];
      frames.clear();
      for (const callback of pending) callback();
    };
    const flushTimers = () => {
      const pending = [...timers.values()];
      timers.clear();
      for (const { callback } of pending) callback();
    };
    run({ inspector, diagram, host, status, clear, window, nodes, calls, viewer, frames, timers, flush, flushTimers });
  } finally {
    for (const [key, entry] of saved) {
      if (entry.present) globalThis[key] = entry.value; else delete globalThis[key];
    }
  }
}

test('conditional primary preview does not invite a blocked Compare view', () => fixture(({ inspector, diagram, nodes, status, flush }) => {
  inspector.reset();
  inspector.setDiagram([diagramAtom(7, 'C'), diagramAtom(7, 'C', 'reactants')], 'Conditional 2D only; aldehyde endpoint unresolved.');
  assert.match(status.textContent, /Conditional 2D only/);
  diagram.emit('pointerover', { target: nodes[0] }); flush();
  assert.match(status.textContent, /aldehyde endpoint unresolved/);
  assert.doesNotMatch(status.textContent, /use Compare|linked in 3D/);
}));

test('optional confidence hint clears for subsequent ordinary diagrams', () => fixture(({ inspector, diagram, nodes, status, flush }) => {
  inspector.reset();
  inspector.setDiagram([diagramAtom(7, 'C')], 'Conditional 2D only; aldehyde endpoint unresolved.');
  inspector.reset();
  inspector.setDiagram([diagramAtom(7, 'C')]);
  diagram.emit('pointerover', { target: nodes[0] }); flush();
  assert.match(status.textContent, /use Compare/);
  assert.doesNotMatch(status.textContent, /aldehyde endpoint/);
}));

test('2D hover highlights every mapped occurrence and hides its reusable 3D overlay on exit', () => fixture(({ diagram, host, nodes, calls, status, flush }) => {
  diagram.emit('pointerover', { target: nodes[0] });
  flush();
  assert.equal(host.dataset.observedAtom, '7');
  assert.equal(nodes[0].classes.has('is-observed'), true);
  assert.equal(nodes[2].classes.has('is-observed'), true);
  assert.equal(nodes[1].classes.has('is-observed'), false);
  assert.deepEqual(calls.spheres.at(-1).spec.center, { x: 1, y: 2, z: 3 });
  assert.equal(calls.spheres.at(-1).spec.clickable, false);
  assert.match(status.textContent, /linked in 3D/);
  diagram.emit('pointerout', { target: nodes[0] });
  assert.equal(host.dataset.observedAtom, '');
  assert.equal(calls.spheres.at(-1).spec.hidden, true);
  assert.equal(calls.labels.at(-1).visible, false);
  assert.equal(calls.removedShapes.length, 0);
  assert.equal(calls.removedLabels.length, 0);
}));

test('click pins an atom while temporary hover overrides it and restores the pinned selection on exit', () => fixture(({ diagram, host, nodes, calls, flush }) => {
  calls.clickCallbacks.at(-1)(modelAtoms[0]);
  assert.equal(host.dataset.observedAtom, '7');
  assert.equal(nodes[0].getAttribute('aria-pressed'), 'true');
  diagram.emit('pointerover', { target: nodes[1] });
  flush();
  assert.equal(host.dataset.observedAtom, '11');
  diagram.emit('pointerout', { target: nodes[1] });
  assert.equal(host.dataset.observedAtom, '7');
  diagram.emit('click', { target: nodes[0] });
  assert.equal(host.dataset.observedAtom, '');
  assert.equal(nodes[0].getAttribute('aria-pressed'), 'false');
}));

test('keyboard selection, Escape, and clear button work without a mouse', () => fixture(({ diagram, host, nodes, window, clear }) => {
  const input = diagram.emit('keydown', { target: nodes[1], key: 'Enter' });
  assert.equal(input.prevented, true);
  assert.equal(host.dataset.observedAtom, '11');
  window.emit('keydown', { key: 'Escape' });
  assert.equal(host.dataset.observedAtom, '');
  assert.equal(clear.disabled, true);
  diagram.emit('keydown', { target: nodes[0], key: ' ' });
  assert.equal(host.dataset.observedAtom, '7');
  clear.emit('click');
  assert.equal(host.dataset.observedAtom, '');
}));

test('reactant atoms outside the main product do not glow an unrelated 3D atom', () => fixture(({ diagram, host, nodes, calls, status, flush }) => {
  const shapes = calls.spheres.length;
  diagram.emit('pointerover', { target: nodes[3] });
  flush();
  assert.equal(diagram.dataset.observedAtom, '99');
  assert.equal(host.dataset.observedAtom, '');
  assert.equal(calls.spheres.length, shapes);
  assert.match(status.textContent, /outside the main-product 3D view/);
}));

test('3D ray picking links back to 2D and supports same-atom pointer reentry', () => fixture(({ host, diagram, nodes, viewer, calls, flush }) => {
  viewer.nextHit = modelAtoms[1];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.deepEqual({ x: calls.picks.at(-1).x, y: calls.picks.at(-1).y }, { x: 0, y: 0 });
  assert.equal(diagram.dataset.observedAtom, '11');
  assert.equal(nodes[1].classes.has('is-observed'), true);
  host.emit('pointerleave');
  assert.equal(diagram.dataset.observedAtom, '');
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.equal(diagram.dataset.observedAtom, '11');
}));

test('a burst of 3D pointer moves keeps one scheduled frame and picks the latest position', () => fixture(({ host, viewer, calls, frames, flush }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 100, clientY: 130 });
  const firstFrame = [...frames.keys()][0];
  for (let clientX = 101; clientX <= 200; clientX++) host.emit('pointermove', { clientX, clientY: 130 });
  assert.deepEqual([...frames.keys()], [firstFrame], 'fast events must not cancel and postpone the next frame');
  assert.equal(calls.picks.length, 0);
  const renders = calls.renders;
  flush();
  assert.equal(calls.picks.length, 1);
  assert.ok(Math.abs(calls.picks[0].x - .6) < 1e-12);
  assert.equal(calls.picks[0].y, 0);
  assert.equal(calls.renders, renders + 1);
}));

test('moving between 2D targets in one frame switches directly without an empty highlight', () => fixture(({ diagram, host, nodes, calls, frames, flush }) => {
  diagram.emit('pointerover', { target: nodes[0] });
  flush();
  const previous = calls.spheres[0];
  const renders = calls.renders;
  diagram.emit('pointerout', { target: nodes[0], relatedTarget: diagram });
  diagram.emit('pointerover', { target: nodes[1] });
  diagram.emit('pointerover', { target: nodes[1] });
  assert.equal(frames.size, 1);
  assert.equal(host.dataset.observedAtom, '7');
  assert.equal(previous.spec.hidden, false);
  assert.equal(calls.renders, renders);
  flush();
  assert.equal(host.dataset.observedAtom, '11');
  assert.equal(previous.spec.hidden, true);
  assert.equal(calls.renders, renders + 1);
}));

test('brief 3D hit gaps retain the current highlight and reentry cancels its expiry', () => fixture(({ host, diagram, viewer, calls, timers, flush, flushTimers }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  const renders = calls.renders;
  viewer.nextHit = null;
  host.emit('pointermove', { clientX: 141, clientY: 130 });
  flush();
  assert.equal(diagram.dataset.observedAtom, '7');
  assert.equal(timers.size, 1);
  assert.equal([...timers.values()][0].delay, 70);
  assert.equal(calls.renders, renders);
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.equal(timers.size, 0);
  flushTimers();
  assert.equal(diagram.dataset.observedAtom, '7');
  assert.equal(calls.spheres.length, 1);
  assert.equal(calls.labels.length, 1);
  assert.equal(calls.renders, renders);
}));

test('continuous misses expire after one grace period without extending it for each move', () => fixture(({ host, diagram, viewer, timers, flush, flushTimers }) => {
  viewer.nextHit = modelAtoms[1];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  viewer.nextHit = null;
  host.emit('pointermove', { clientX: 141, clientY: 130 });
  flush();
  const firstTimer = [...timers.keys()][0];
  for (let i = 0; i < 10; i++) { host.emit('pointermove', { clientX: 141 + i, clientY: 130 }); flush(); }
  assert.deepEqual([...timers.keys()], [firstTimer]);
  flushTimers();
  assert.equal(diagram.dataset.observedAtom, '');
}));

test('leaving, dragging, cancelling, and zooming clear a pending hover gap immediately', () => {
  for (const event of ['pointerleave', 'pointerdown', 'pointercancel', 'wheel']) {
    fixture(({ host, diagram, viewer, timers, flush, flushTimers }) => {
      viewer.nextHit = modelAtoms[0];
      host.emit('pointermove', { clientX: 140, clientY: 130 }); flush();
      viewer.nextHit = null;
      host.emit('pointermove', { clientX: 141, clientY: 130 }); flush();
      assert.equal(timers.size, 1);
      host.emit(event);
      assert.equal(timers.size, 0);
      assert.equal(diagram.dataset.observedAtom, '');
      flushTimers();
      assert.equal(diagram.dataset.observedAtom, '');
    });
  }
});

test('revisiting atoms reuses overlays, updates once, and does not repeatedly lay out the diagram', () => fixture(({ host, diagram, nodes, viewer, calls, flush }) => {
  const initialRenders = calls.renders;
  for (const atom of [modelAtoms[0], modelAtoms[1], modelAtoms[0]]) {
    viewer.nextHit = atom;
    host.emit('pointermove', { clientX: 140, clientY: 130 }); flush();
  }
  assert.equal(calls.renders, initialRenders + 3);
  assert.equal(calls.spheres.length, 2);
  assert.equal(calls.labels.length, 2);
  assert.ok(calls.labels.every((label) => label.noShow), 'label creation must not draw an intermediate frame');
  assert.equal(calls.spheres.filter((shape) => !shape.spec.hidden).length, 1);
  assert.equal(calls.labels.filter((label) => label.visible).length, 1);
  assert.equal(calls.removedShapes.length, 0);
  assert.equal(calls.removedLabels.length, 0);
  const boundsReads = nodes[0].boundsReads + nodes[1].boundsReads + diagram.boundsReads;
  for (let i = 0; i < 30; i++) { host.emit('pointermove', { clientX: 140, clientY: 130 }); flush(); }
  assert.equal(calls.renders, initialRenders + 3);
  assert.equal(nodes[0].boundsReads + nodes[1].boundsReads + diagram.boundsReads, boundsReads);
}));

test('model replacement cancels hover expiry and disposes cached overlays before reusing map IDs', () => fixture(({ inspector, host, diagram, viewer, calls, timers, flush, flushTimers }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 }); flush();
  const oldShape = calls.spheres[0];
  const oldLabel = calls.labels[0];
  viewer.nextHit = null;
  host.emit('pointermove', { clientX: 141, clientY: 130 }); flush();
  inspector.setModel(modelAtoms, links);
  assert.equal(timers.size, 0);
  assert.ok(calls.removedShapes.includes(oldShape));
  assert.ok(calls.removedLabels.includes(oldLabel));
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 }); flush();
  assert.notEqual(calls.spheres.at(-1), oldShape);
  flushTimers();
  assert.equal(diagram.dataset.observedAtom, '7');
}));

test('clicking a new 2D atom and keyboard focus supersede an older queued hover', () => fixture(({ diagram, host, nodes, viewer, frames, calls, flush }) => {
  diagram.emit('pointerover', { target: nodes[0] }); flush();
  diagram.emit('pointerover', { target: nodes[1] });
  diagram.emit('click', { target: nodes[1] });
  assert.equal(frames.size, 0);
  assert.equal(host.dataset.observedAtom, '11');
  assert.equal(nodes[1].getAttribute('aria-pressed'), 'true');
  viewer.nextHit = modelAtoms[1];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  const picks = calls.picks.length;
  diagram.emit('focusin', { target: nodes[0] });
  flush();
  assert.equal(calls.picks.length, picks);
  assert.equal(host.dataset.observedAtom, '7');
}));

test('pointerleave and reset cancel queued 3D selection and remove old correspondence', () => fixture(({ inspector, host, diagram, viewer, flush, frames, calls }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  assert.equal(frames.size, 1);
  host.emit('pointerleave');
  assert.equal(frames.size, 0);
  flush();
  assert.equal(calls.picks.length, 0);
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  inspector.reset();
  flush();
  assert.equal(diagram.dataset.observedAtom, '');
  assert.equal(host.dataset.observedAtom, '');
  calls.clickCallbacks.at(-1)(modelAtoms[0]);
  assert.equal(host.dataset.observedAtom, '');
}));

test('touch movement does not pretend to hover, and hidden 3D preview is not ray-picked', () => fixture(({ host, viewer, flush, calls }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130, pointerType: 'touch' });
  flush();
  assert.equal(calls.picks.length, 0);
  host.hidden = true;
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.equal(calls.picks.length, 0);
}));

test('drag motion cancels an earlier queued hover instead of restoring it during rotation', () => fixture(({ host, diagram, viewer, flush }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  host.emit('pointermove', { clientX: 160, clientY: 130, buttons: 1 });
  flush();
  assert.equal(diagram.dataset.observedAtom, '');
}));

test('retained click callback cannot select an atom after a new model replaces its correspondence', () => fixture(({ inspector, diagram, host, calls }) => {
  const oldClick = calls.clickCallbacks.at(-1);
  inspector.reset();
  const replacementLinks = [{ ...links[0], mapId: 17 }, { ...links[1], mapId: 21 }];
  inspector.setDiagram([diagramAtom(17, 'C'), diagramAtom(21, 'O')]);
  inspector.setModel(modelAtoms, replacementLinks);
  oldClick(modelAtoms[0]);
  assert.equal(host.dataset.observedAtom, '');
  assert.equal(diagram.dataset.observedAtom, '');
  calls.clickCallbacks.at(-1)(modelAtoms[0]);
  assert.equal(host.dataset.observedAtom, '17');
}));

test('model or diagram replacement cancels a queued pick from the previous preview', () => fixture(({ inspector, host, diagram, viewer, calls, flush }) => {
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  inspector.setDiagram([diagramAtom(7, 'C'), diagramAtom(11, 'O')]);
  flush();
  assert.equal(calls.picks.length, 0);
  assert.equal(diagram.dataset.observedAtom, '');
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  inspector.setModel(modelAtoms, links);
  flush();
  assert.equal(calls.picks.length, 0);
  assert.equal(diagram.dataset.observedAtom, '');
}));

test('3D hover reveals the matching main-product 2D atom by scrolling only the diagram viewport', () => fixture(({ host, diagram, nodes, viewer, window, flush }) => {
  nodes[0].rect = { left: 450, top: 230, width: 24, height: 24, right: 474, bottom: 254 };
  // The reactant occurrence is already visible; the preferred main product is the far target.
  viewer.nextHit = modelAtoms[0];
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.deepEqual(diagram.scrollCalls, [{ left: 248, top: 88, behavior: 'instant' }]);
  assert.deepEqual(window.scrollCalls, []);
  assert.equal(nodes[0].rect.right, diagram.rect.right - 14);
  assert.equal(nodes[0].rect.bottom, diagram.rect.bottom - 14);
  host.emit('pointermove', { clientX: 140, clientY: 130 });
  flush();
  assert.equal(diagram.scrollCalls.length, 1, 'The newly visible atom should not cause repeated scrolling.');
}));

test('3D click reveals atoms to the left or above without moving the page', () => fixture(({ diagram, nodes, calls, window }) => {
  nodes[1].rect = { left: -40, top: 25, width: 24, height: 24, right: -16, bottom: 49 };
  calls.clickCallbacks.at(-1)(modelAtoms[1]);
  assert.deepEqual(diagram.scrollCalls, [{ left: -94, top: -69, behavior: 'instant' }]);
  assert.deepEqual(window.scrollCalls, []);
}));

test('already-visible or explicitly hidden 2D atoms do not move the diagram viewport', () => fixture(({ diagram, nodes, calls }) => {
  calls.clickCallbacks.at(-1)(modelAtoms[0]);
  assert.deepEqual(diagram.scrollCalls, []);
  diagram.hidden = true;
  nodes[1].rect = { left: 450, top: 230, width: 24, height: 24, right: 474, bottom: 254 };
  calls.clickCallbacks.at(-1)(modelAtoms[1]);
  assert.deepEqual(diagram.scrollCalls, []);
}));

test('2D preview hidden by an ancestor with no layout bounds does not scroll', () => fixture(({ diagram, nodes, calls }) => {
  // Display:none on the enclosing reaction panel leaves drawing.hidden false, but removes its box.
  diagram.rect = { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 };
  nodes[0].rect = { ...diagram.rect };
  calls.clickCallbacks.at(-1)(modelAtoms[0]);
  assert.deepEqual(diagram.scrollCalls, []);
}));

test('measurement click hook consumes an atom click without ordinary pinning or diagram scrolling', () => {
  const picked = [];
  fixture(({ diagram, host, nodes, calls }) => {
    // Ordinary selection can coexist until measurement mode takes the next click.
    diagram.emit('click', { target: nodes[0] });
    assert.equal(host.dataset.observedAtom, '7');
    calls.clickCallbacks.at(-1)(modelAtoms[1]);
    assert.deepEqual(picked, [modelAtoms[1]]);
    assert.equal(host.dataset.observedAtom, '');
    assert.equal(nodes[0].getAttribute('aria-pressed'), 'false');
    assert.equal(nodes[1].getAttribute('aria-pressed'), 'false');
    assert.deepEqual(diagram.scrollCalls, []);
  }, (atom) => { picked.push(atom); return true; });
});

test('inactive measurement click hook passes through to normal exact-atom inspection', () => {
  const picked = [];
  fixture(({ host, nodes, calls }) => {
    calls.clickCallbacks.at(-1)(modelAtoms[1]);
    assert.deepEqual(picked, [modelAtoms[1]]);
    assert.equal(host.dataset.observedAtom, '11');
    assert.equal(nodes[1].getAttribute('aria-pressed'), 'true');
  }, (atom) => { picked.push(atom); return false; });
});

test('measurement click hook still receives product atoms when 2D correspondence is unavailable', () => {
  const picked = [];
  fixture(({ inspector, host, calls }) => {
    inspector.setModel(modelAtoms, []);
    calls.clickCallbacks.at(-1)(modelAtoms[0]);
    assert.deepEqual(picked, [modelAtoms[0]]);
    assert.equal(host.dataset.observedAtom, '');
  }, (atom) => { picked.push(atom); return true; });
});

test('stale model callbacks cannot pass atoms into the measurement hook after reset or replacement', () => {
  const picked = [];
  fixture(({ inspector, calls }) => {
    const oldClick = calls.clickCallbacks.at(-1);
    inspector.reset();
    oldClick(modelAtoms[0]);
    assert.deepEqual(picked, []);
    inspector.setModel(modelAtoms, links);
    oldClick(modelAtoms[1]);
    assert.deepEqual(picked, []);
    calls.clickCallbacks.at(-1)(modelAtoms[1]);
    assert.deepEqual(picked, [modelAtoms[1]]);
  }, (atom) => { picked.push(atom); return true; });
});
