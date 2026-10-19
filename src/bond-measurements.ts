export type MeasurementMode = 'distance' | 'angle' | 'torsion';
export type Point3D = { x: number; y: number; z: number };
export type MeasurementAtom = Point3D & { index: number; elem: string; bonds?: number[] };
export type MeasurementViewer = {
  setClickable: (selection: Record<string, never>, enabled: boolean, callback: (atom: MeasurementAtom) => void) => void;
  addSphere: (spec: Record<string, unknown>) => unknown;
  addLine: (spec: Record<string, unknown>) => unknown;
  removeShape: (shape: unknown) => void;
  addLabel: (text: string, spec: Record<string, unknown>) => unknown;
  removeLabel: (label: unknown) => void;
  render: () => void;
};

const COUNTS: Record<MeasurementMode, number> = { distance: 2, angle: 3, torsion: 4 };
type Vector = [number, number, number];
const subtract = (a: Point3D, b: Point3D): Vector => [a.x - b.x, a.y - b.y, a.z - b.z];
const dot = (a: Vector, b: Vector) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vector, b: Vector): Vector => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const magnitude = (v: Vector) => Math.hypot(...v);
function normalized(v: Vector): Vector {
  const length = magnitude(v);
  if (!Number.isFinite(length) || length <= 1e-12) throw new Error('Undefined geometry: two selected positions coincide.');
  return v.map((value) => value / length) as Vector;
}

/** Coordinates are in ångströms as loaded from the displayed SDF/Molfile model. */
export function measureGeometry(mode: MeasurementMode, atoms: Point3D[]): { value: number; unit: 'Å' | '°' } {
  if (!(mode in COUNTS) || !Array.isArray(atoms) || atoms.length !== COUNTS[mode]) throw new Error('Choose the required number of atoms in order.');
  if (atoms.some((atom) => !atom || ![atom.x, atom.y, atom.z].every(Number.isFinite))) throw new Error('Valid 3D coordinates are required.');
  let value: number;
  if (mode === 'distance') {
    value = magnitude(subtract(atoms[1], atoms[0]));
  } else if (mode === 'angle') {
    const first = normalized(subtract(atoms[0], atoms[1]));
    const second = normalized(subtract(atoms[2], atoms[1]));
    value = Math.acos(Math.max(-1, Math.min(1, dot(first, second)))) * 180 / Math.PI;
  } else {
    const first = normalized(subtract(atoms[0], atoms[1]));
    const axis = normalized(subtract(atoms[2], atoms[1]));
    const last = normalized(subtract(atoms[3], atoms[2]));
    const project = (vector: Vector): Vector => vector.map((component, index) => component - dot(vector, axis) * axis[index]) as Vector;
    const firstPlane = project(first);
    const lastPlane = project(last);
    if (magnitude(firstPlane) <= 1e-12 || magnitude(lastPlane) <= 1e-12) throw new Error('Torsion is undefined for collinear atoms.');
    const v = normalized(firstPlane);
    const w = normalized(lastPlane);
    value = Math.atan2(dot(cross(axis, v), w), dot(v, w)) * 180 / Math.PI;
  }
  if (!Number.isFinite(value)) throw new Error('These coordinates cannot be measured reliably.');
  return { value: Math.abs(value) < 1e-10 ? 0 : value, unit: mode === 'distance' ? 'Å' : '°' };
}

function element<K extends keyof HTMLElementTagNameMap>(tag: K, text = '', className = '') {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}

/** One controller owns only its labels/shapes, never another feature's highlights. */
export class BondMeasurements {
  private atoms = new Map<number, MeasurementAtom>();
  private selected: MeasurementAtom[] = [];
  private mode: MeasurementMode | 'off' = 'off';
  private generation = 0;
  private shapes: unknown[] = [];
  private labels: unknown[] = [];
  private readonly select = element('select');
  private readonly status = element('p', '', 'measurement-status');
  private readonly value = element('strong', '', 'measurement-value');
  private readonly order = element('ol', '', 'measurement-order');
  private readonly atomList = element('div', '', 'measurement-atom-buttons');
  private readonly clear = element('button', 'Clear selection');
  private readonly options = new Map<MeasurementMode | 'off', HTMLOptionElement>();

  constructor(private readonly host: HTMLElement, private readonly viewer: MeasurementViewer | undefined,
    private readonly optionsConfig: { bindClicks?: boolean } = {}) {
    host.classList.add('bond-measurements');
    const disclosure = element('details');
    const body = element('div', '', 'measurement-body');
    const controls = element('div', '', 'measurement-controls');
    this.select.setAttribute('aria-label', 'Measure');
    for (const [mode, label] of [['off', 'Off'], ['distance', 'Distance · 2 atoms'], ['angle', 'Angle · 3 atoms'], ['torsion', 'Torsion · 4 atoms']] as const) {
      const option = element('option', label);
      option.value = mode;
      this.options.set(mode, option);
      this.select.append(option);
    }
    this.select.value = 'off';
    this.select.addEventListener('change', () => {
      const mode = this.select.value as MeasurementMode | 'off';
      this.mode = mode in COUNTS && this.atoms.size >= COUNTS[mode as MeasurementMode] ? mode as MeasurementMode : 'off';
      this.select.value = this.mode;
      this.selected = [];
      this.render();
    });
    this.clear.type = 'button';
    this.clear.addEventListener('click', () => { this.selected = []; this.render(); });
    this.status.setAttribute('role', 'status');
    this.status.setAttribute('aria-live', 'polite');
    this.order.setAttribute('aria-label', 'Selected atoms in measurement order');
    const chooser = element('details', '', 'measurement-atoms');
    chooser.append(element('summary', 'Choose atoms by list'), this.atomList);
    controls.append(this.select, this.clear);
    body.append(controls, this.status, this.order, this.value,
      element('p', 'Displayed-model geometry · not an experimental measurement.', 'measurement-note'), chooser);
    disclosure.append(element('summary', 'Measure 3D'), body);
    host.append(disclosure);
    host.hidden = true;
    this.render();
  }

  setAtoms(atoms: MeasurementAtom[]) {
    const generation = ++this.generation;
    this.removeOverlays();
    this.atoms.clear();
    this.selected = [];
    this.mode = 'off';
    this.select.value = 'off';
    // Reject the entire model on ambiguous IDs/non-3D data rather than guess.
    const valid = Array.isArray(atoms) && atoms.length <= 10000
      && new Set(atoms.map((atom) => atom?.index)).size === atoms.length
      && atoms.every((atom) => atom && Number.isSafeInteger(atom.index) && atom.index >= 0
        && typeof atom.elem === 'string' && /^[A-Z][a-z]?$/.test(atom.elem)
        && [atom.x, atom.y, atom.z].every(Number.isFinite));
    if (valid && this.viewer) for (const atom of atoms) this.atoms.set(atom.index, atom);
    this.host.hidden = this.atoms.size < 2;
    this.atomList.replaceChildren();
    for (const atom of this.atoms.values()) {
      const button = element('button', this.atomName(atom));
      button.type = 'button';
      button.dataset.atomIndex = String(atom.index);
      button.addEventListener('click', () => { if (generation === this.generation) this.pickAtom(atom); });
      this.atomList.append(button);
    }
    for (const [mode, option] of this.options) option.disabled = mode !== 'off' && this.atoms.size < COUNTS[mode];
    if (this.optionsConfig.bindClicks !== false && this.viewer && this.atoms.size >= 2) {
      this.viewer.setClickable({}, true, (atom) => { if (generation === this.generation) this.pickAtom(atom); });
    }
    this.render();
  }

  reset() { this.setAtoms([]); }

  get available(): boolean { return this.atoms.size >= 2; }

  /** Return true only while measurement mode consumes a valid atom click. */
  pickAtom(candidate: MeasurementAtom): boolean {
    if (this.mode === 'off' || this.host.hidden || !candidate) return false;
    const atom = this.atoms.get(candidate.index);
    if (!atom || atom.elem !== candidate.elem || atom.x !== candidate.x || atom.y !== candidate.y || atom.z !== candidate.z) return false;
    const index = this.selected.findIndex((item) => item.index === atom.index);
    if (index >= 0) this.selected = this.selected.slice(0, index);
    else {
      if (this.selected.length >= COUNTS[this.mode]) this.selected = [];
      this.selected.push(atom);
    }
    this.render();
    return true;
  }

  private atomName(atom: MeasurementAtom) { return `${atom.elem}${atom.index + 1}`; }

  private removeOverlays() {
    for (const shape of this.shapes) { try { this.viewer?.removeShape(shape); } catch { /* A failed/hidden WebGL context must not block resets. */ } }
    for (const label of this.labels) { try { this.viewer?.removeLabel(label); } catch { /* As above. */ } }
    this.shapes = [];
    this.labels = [];
  }

  private render() {
    this.removeOverlays();
    this.clear.disabled = !this.selected.length;
    this.value.hidden = true;
    this.value.textContent = '';
    this.order.replaceChildren();
    for (const atom of this.selected) this.order.append(element('li', this.atomName(atom)));
    this.order.hidden = !this.selected.length;
    for (const button of this.atomList.querySelectorAll<HTMLButtonElement>('button')) {
      button.disabled = this.mode === 'off';
      button.setAttribute('aria-pressed', String(this.selected.some((atom) => String(atom.index) === button.dataset.atomIndex)));
    }
    this.status.textContent = this.mode === 'off' ? 'Choose a measurement, then click atoms in 3D or use the atom list.'
      : this.mode === 'angle' ? `Pick 3 atoms in order; the angle is at atom 2. (${this.selected.length}/3)`
      : this.mode === 'torsion' ? `Pick 4 atoms in order; the axis is atoms 2–3. (${this.selected.length}/4)`
      : `Pick 2 atoms. (${this.selected.length}/2)`;
    let result: ReturnType<typeof measureGeometry> | null = null;
    if (this.mode !== 'off' && this.selected.length === COUNTS[this.mode]) {
      try {
        result = measureGeometry(this.mode, this.selected);
        const value = `${result.value.toFixed(this.mode === 'distance' ? 3 : 1)} ${result.unit}`;
        this.value.textContent = value;
        this.value.hidden = false;
        this.status.textContent = `${this.mode === 'distance' ? 'Distance' : this.mode === 'angle' ? 'Angle' : 'Signed torsion'}: ${value} · ${this.selected.map((atom) => this.atomName(atom)).join(' → ')}`;
        const knownBonds = this.selected.every((atom) => Array.isArray(atom.bonds));
        if (knownBonds && this.selected.slice(0, -1).some((atom, index) => !atom.bonds!.includes(this.selected[index + 1].index))) {
          this.status.textContent += ' · Not a bonded chain.';
        }
      } catch (error) { this.status.textContent = error instanceof Error ? error.message : 'This geometry is undefined.'; }
    }
    if (!this.viewer || this.host.hidden) return;
    try {
      this.selected.forEach((atom, index) => {
        this.shapes.push(this.viewer!.addSphere({ center: { x: atom.x, y: atom.y, z: atom.z }, radius: atom.elem === 'H' ? .42 : .66,
          color: '#db8e30', opacity: .35, clickable: false, hoverable: false }));
        this.labels.push(this.viewer!.addLabel(`${index + 1}: ${this.atomName(atom)}`, { position: atom, fontSize: 12,
          fontColor: '#6c421c', backgroundColor: '#fff4df', backgroundOpacity: .92, borderThickness: 0, inFront: true }));
        if (index > 0) this.shapes.push(this.viewer!.addLine({ start: this.selected[index - 1], end: atom, color: '#c87e22', dashed: true, linewidth: 2 }));
      });
      if (result) {
        const middle = this.selected[Math.floor((this.selected.length - 1) / 2)];
        this.labels.push(this.viewer.addLabel(this.value.textContent, { position: middle, fontSize: 13,
          fontColor: '#fff', backgroundColor: '#8d5d23', backgroundOpacity: .95, inFront: true, alignment: 'topRight' }));
      }
      this.viewer.render();
    } catch { /* Text measurements remain usable if decorative rendering fails. */ }
  }
}
