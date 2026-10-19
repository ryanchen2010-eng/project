/** Exact atom correspondence and interaction for Reaction Lab's 2D / 3D views. */
export type DiagramAtom = {
  mapId: number;
  element: string;
  label: string;
  side: 'reactants' | 'products';
  speciesIndex: number;
  speciesName: string;
  atomIndex: number;
  formalCharge: number;
  lonePairs: number | null;
  linkedTo3D: boolean;
};
export type AtomLink = { index: number; mapId: number; element: string };
export type ModelAtom = { index: number; elem: string; x: number; y: number; z: number; bonds?: number[] };
type AtomHalo = { updateStyle: (spec: Record<string, unknown>) => void };
type AtomLabel = { hide: () => void; show: () => void };
type AtomOverlay = { halo: AtomHalo; label: AtomLabel };
type HoverIntent = { kind: 'diagram'; map: number | null }
  | { kind: 'model'; clientX: number; clientY: number };
export type AtomViewer = {
  targetedObjects: (x: number, y: number, atoms: ModelAtom[]) => { clickable: ModelAtom }[];
  setClickable: (selection: Record<string, never>, enabled: boolean, callback: (atom: ModelAtom) => void) => void;
  addSphere: (spec: Record<string, unknown>) => AtomHalo;
  removeShape: (shape: unknown) => void;
  addLabel: (text: string, spec: Record<string, unknown>, selection?: undefined, noShow?: boolean) => AtomLabel;
  removeLabel: (label: unknown) => void;
  render: () => void;
};

/** Reject partial or inconsistent correspondence instead of highlighting an arbitrary atom. */
export function indexModelAtoms(links: AtomLink[], atoms: ModelAtom[]): Map<number, ModelAtom> {
  if (!links.length || links.length !== atoms.length) return new Map();
  const byIndex = new Map(atoms.map((atom) => [atom.index, atom]));
  const result = new Map<number, ModelAtom>();
  const indexes = new Set<number>();
  for (const link of links) {
    const atom = byIndex.get(link.index);
    if (!Number.isInteger(link.index) || link.index < 0 || !Number.isInteger(link.mapId) || link.mapId <= 0
        || !atom || atom.elem !== link.element || ![atom.x, atom.y, atom.z].every(Number.isFinite)
        || indexes.has(link.index) || result.has(link.mapId)) return new Map();
    indexes.add(link.index);
    result.set(link.mapId, atom);
  }
  return result;
}

export function correspondenceMatches(atoms: DiagramAtom[], model: Map<number, ModelAtom>): boolean {
  const product = atoms.filter((atom) => atom.side === 'products' && atom.speciesIndex === 0);
  return Boolean(model.size) && product.length === model.size
    && new Set(product.map((atom) => atom.mapId)).size === product.length
    && product.every((atom) => model.get(atom.mapId)?.elem === atom.element);
}

export function pointerCoordinates(clientX: number, clientY: number, rect: Pick<DOMRect, 'left' | 'top' | 'width' | 'height'>): { x: number; y: number } | null {
  if (!rect.width || !rect.height) return null;
  const x = 2 * (clientX - rect.left) / rect.width - 1;
  const y = 1 - 2 * (clientY - rect.top) / rect.height;
  return Math.abs(x) <= 1 && Math.abs(y) <= 1 ? { x, y } : null;
}

/** The local renderer's SVG is still treated as data; only drawing / interaction attributes survive. */
export function safeDiagramSvg(source: string): SVGSVGElement {
  if (source.length > 1_500_000 || /<!DOCTYPE|<!ENTITY/i.test(source)) throw new Error('The reaction diagram could not be read safely.');
  const document = new DOMParser().parseFromString(source, 'image/svg+xml');
  if (document.querySelector('parsererror') || document.documentElement.localName !== 'svg') throw new Error('The reaction diagram could not be read.');
  const tags = new Set(['svg', 'g', 'path', 'line', 'polyline', 'polygon', 'circle', 'ellipse', 'rect', 'text', 'tspan', 'title', 'desc']);
  const attributes = new Set(['xmlns', 'viewBox', 'width', 'height', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry', 'd', 'points', 'transform', 'class', 'fill', 'stroke', 'stroke-width', 'stroke-opacity', 'fill-opacity', 'opacity', 'stroke-linecap', 'stroke-linejoin', 'fill-rule', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'dominant-baseline', 'pointer-events', 'role', 'aria-label', 'aria-hidden', 'tabindex', 'data-atom-map', 'data-element', 'data-side', 'data-species-index']);
  const styles = new Set(['fill', 'stroke', 'stroke-width', 'stroke-opacity', 'fill-opacity', 'opacity', 'stroke-linecap', 'stroke-linejoin', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'fill-rule', 'pointer-events']);
  for (const element of Array.from(document.querySelectorAll('*'))) {
    if (!tags.has(element.localName) || element.namespaceURI !== 'http://www.w3.org/2000/svg') { element.remove(); continue; }
    for (const attribute of Array.from(element.attributes)) {
      if (attribute.name === 'style') {
        const safe = attribute.value.split(';').filter((rule) => {
          const separator = rule.indexOf(':');
          return separator > 0 && styles.has(rule.slice(0, separator).trim().toLowerCase())
            && !/url\s*\(|expression|@|javascript:|\\|\/\*|[\u0000-\u001f]/i.test(rule);
        }).join(';');
        if (safe) element.setAttribute('style', safe); else element.removeAttribute('style');
      } else if (!attributes.has(attribute.name) || /url\s*\(|javascript:|\\|\/\*/i.test(attribute.value)) {
        element.removeAttribute(attribute.name);
      }
    }
  }
  return window.document.importNode(document.documentElement, true) as unknown as SVGSVGElement;
}

export class AtomInspector {
  private atoms: DiagramAtom[] = [];
  private modelAtoms: ModelAtom[] = [];
  private model = new Map<number, ModelAtom>();
  private mapByIndex = new Map<number, number>();
  private atomsByMap = new Map<number, DiagramAtom[]>();
  private targetsByMap = new Map<number, SVGGElement[]>();
  private productTargets = new Map<number, SVGGElement>();
  private linked = false;
  private hovered: number | null = null;
  private pinned: number | null = null;
  private observed: number | null = null;
  private overlays = new Map<number, AtomOverlay>();
  private activeOverlay: AtomOverlay | null = null;
  private renderedPinned: number | null = null;
  private frame: number | null = null;
  private pendingHover: HoverIntent | null = null;
  private hoverLossTimer: ReturnType<typeof setTimeout> | null = null;
  private modelGeneration = 0;
  private unavailable3D = '';

  constructor(private diagram: HTMLElement, private host3D: HTMLElement, private viewer: AtomViewer | undefined,
    private status: HTMLElement, private clearButton: HTMLButtonElement,
    private onAtomClick?: (atom: ModelAtom) => boolean) {
    const targetMap = (target: EventTarget | null): number | null => {
      if (!(target instanceof Element)) return null;
      const targetAtom = target.closest('[data-atom-map]');
      if (!targetAtom || !diagram.contains(targetAtom)) return null;
      const map = Number(targetAtom.getAttribute('data-atom-map'));
      return this.atomsByMap.has(map) ? map : null;
    };
    diagram.addEventListener('pointerover', (event) => {
      if (event.pointerType !== 'touch') this.queueHover({ kind: 'diagram', map: targetMap(event.target) });
    });
    diagram.addEventListener('pointerout', (event) => {
      if (event.pointerType === 'touch') return;
      if (event.relatedTarget instanceof Element && diagram.contains(event.relatedTarget)) {
        this.queueHover({ kind: 'diagram', map: targetMap(event.relatedTarget) });
      } else this.clearHover();
    });
    diagram.addEventListener('pointerleave', () => this.clearHover());
    diagram.addEventListener('pointercancel', () => this.clearHover());
    diagram.addEventListener('focusin', (event) => {
      this.cancelFrame();
      this.hover(targetMap(event.target));
    });
    diagram.addEventListener('focusout', (event) => {
      this.cancelFrame();
      this.hover(targetMap(event.relatedTarget));
    });
    diagram.addEventListener('click', (event) => {
      const map = targetMap(event.target);
      if (map !== null) this.pin(map);
    });
    diagram.addEventListener('keydown', (event) => {
      const map = targetMap(event.target);
      if (map !== null && (event.key === 'Enter' || event.key === ' ')) { event.preventDefault(); this.pin(map); }
    });
    host3D.addEventListener('pointermove', (event) => {
      if (event.pointerType === 'touch') return;
      if (event.buttons || !this.linked) { this.clearHover(); return; }
      this.queueHover({ kind: 'model', clientX: event.clientX, clientY: event.clientY });
    });
    host3D.addEventListener('pointerleave', () => this.clearHover());
    host3D.addEventListener('pointerdown', () => this.clearHover());
    host3D.addEventListener('pointercancel', () => this.clearHover());
    host3D.addEventListener('wheel', () => this.clearHover(), { passive: true });
    clearButton.addEventListener('click', () => this.clearSelection());
    window.addEventListener('keydown', (event) => { if (event.key === 'Escape') this.clearSelection(); });
    this.render();
  }

  setDiagram(atoms: DiagramAtom[], unavailable3D = '') {
    this.unavailable3D = unavailable3D;
    this.cancelFrame();
    this.cancelHoverLoss();
    this.hovered = null;
    this.removeOverlays();
    this.atoms = atoms;
    this.atomsByMap.clear();
    this.targetsByMap.clear();
    this.productTargets.clear();
    for (const atom of atoms) {
      const occurrences = this.atomsByMap.get(atom.mapId) ?? [];
      occurrences.push(atom);
      this.atomsByMap.set(atom.mapId, occurrences);
    }
    if (this.pinned !== null && !this.atomsByMap.has(this.pinned)) this.pinned = null;
    for (const target of this.diagram.querySelectorAll<SVGGElement>('[data-atom-map]')) {
      const map = Number(target.dataset.atomMap);
      const targets = this.targetsByMap.get(map) ?? [];
      targets.push(target);
      this.targetsByMap.set(map, targets);
      if (target.getAttribute('data-side') === 'products' && target.getAttribute('data-species-index') === '0') {
        this.productTargets.set(map, target);
      }
    }
    this.reconcile();
  }

  setModel(atoms: ModelAtom[], links: AtomLink[]) {
    this.cancelFrame();
    this.cancelHoverLoss();
    this.hovered = null;
    this.removeOverlays();
    const generation = ++this.modelGeneration;
    this.modelAtoms = atoms;
    this.model = indexModelAtoms(links, atoms);
    this.mapByIndex = new Map([...this.model].map(([map, atom]) => [atom.index, map]));
    this.viewer?.setClickable({}, true, (atom) => {
      if (generation !== this.modelGeneration) return;
      // Measurement mode shares this click binding; it must not break ordinary
      // atom inspection or depend on an available 2D correspondence.
      if (this.onAtomClick?.(atom)) { this.clearSelection(); return; }
      const map = this.linked ? this.mapForIndex(atom.index) : null;
      if (map !== null) { this.pin(map); this.revealDiagramAtom(map); }
    });
    this.reconcile();
  }

  private mapForIndex(index: number): number | null {
    return this.mapByIndex.get(index) ?? null;
  }

  /** Scroll only the diagram's own viewport, never the page under the pointer. */
  private revealDiagramAtom(map: number) {
    const target = this.productTargets.get(map);
    if (!target || this.diagram.hidden) return;
    const bounds = target.getBoundingClientRect();
    const viewport = this.diagram.getBoundingClientRect();
    if (!viewport.width || !viewport.height) return;
    const padding = 14;
    const left = bounds.left < viewport.left + padding ? bounds.left - viewport.left - padding
      : bounds.right > viewport.right - padding ? bounds.right - viewport.right + padding : 0;
    const top = bounds.top < viewport.top + padding ? bounds.top - viewport.top - padding
      : bounds.bottom > viewport.bottom - padding ? bounds.bottom - viewport.bottom + padding : 0;
    if (left || top) this.diagram.scrollBy({ left, top, behavior: 'instant' });
  }

  private reconcile() {
    this.linked = correspondenceMatches(this.atoms, this.model);
    this.render(true);
  }

  /** Use the latest pointer position once per frame; never postpone an already queued frame. */
  private queueHover(intent: HoverIntent) {
    this.pendingHover = intent;
    if (this.frame !== null) return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      const pending = this.pendingHover;
      this.pendingHover = null;
      if (!pending) return;
      if (pending.kind === 'diagram') { this.hover(pending.map, true); return; }
      const canvas = this.host3D.querySelector('canvas');
      if (!canvas || this.host3D.hidden || !this.linked || !this.viewer) return;
      const point = pointerCoordinates(pending.clientX, pending.clientY, canvas.getBoundingClientRect());
      if (!point) { this.hover(null); return; }
      const hit = this.viewer.targetedObjects(point.x, point.y, this.modelAtoms)[0]?.clickable;
      const map = hit ? this.mapForIndex(hit.index) : null;
      const previous = this.observed;
      this.hover(map, true);
      // A steady pointer on the same atom needs no repeated DOM layout reads
      // or scrolling of the neighboring diagram.
      if (map !== null && map !== previous) this.revealDiagramAtom(map);
    });
  }

  private hover(map: number | null, allowBriefGap = false) {
    // Tiny gaps at atom edges should not flash the highlight off and on.
    // Leaving a view, dragging, clearing, and keyboard input still act immediately.
    if (map === null && allowBriefGap && this.hovered !== null) {
      if (this.hoverLossTimer === null) this.hoverLossTimer = setTimeout(() => {
        this.hoverLossTimer = null;
        this.hovered = null;
        this.render();
      }, 70);
      return;
    }
    this.cancelHoverLoss();
    this.hovered = map;
    this.render();
  }

  private pin(map: number) {
    this.cancelFrame();
    this.cancelHoverLoss();
    this.hovered = null;
    this.pinned = this.pinned === map ? null : map;
    this.render();
  }

  private cancelHoverLoss() {
    if (this.hoverLossTimer !== null) clearTimeout(this.hoverLossTimer);
    this.hoverLossTimer = null;
  }

  private cancelFrame() {
    if (this.frame !== null) cancelAnimationFrame(this.frame);
    this.frame = null;
    this.pendingHover = null;
  }

  clearHover() {
    this.cancelFrame();
    this.cancelHoverLoss();
    this.hover(null);
  }

  clearSelection() { this.pinned = null; this.clearHover(); }

  reset() {
    this.unavailable3D = '';
    this.modelGeneration++;
    this.clearSelection();
    this.removeOverlays();
    this.atoms = [];
    this.modelAtoms = [];
    this.model.clear();
    this.mapByIndex.clear();
    this.atomsByMap.clear();
    this.linked = false;
    this.render(true);
    this.targetsByMap.clear();
    this.productTargets.clear();
  }

  private hideOverlay() {
    this.activeOverlay?.halo.updateStyle({ hidden: true });
    this.activeOverlay?.label.hide();
    this.activeOverlay = null;
  }

  private removeOverlays() {
    this.hideOverlay();
    for (const overlay of this.overlays.values()) {
      this.viewer?.removeShape(overlay.halo);
      this.viewer?.removeLabel(overlay.label);
    }
    this.overlays.clear();
  }

  private render(force = false) {
    const map = this.hovered ?? this.pinned;
    if (!force && map === this.observed && this.pinned === this.renderedPinned) return;
    const changedMaps = force ? this.targetsByMap.keys()
      : new Set([this.observed, map, this.renderedPinned, this.pinned]);
    this.observed = map;
    this.renderedPinned = this.pinned;
    for (const id of changedMaps) {
      if (id === null) continue;
      for (const target of this.targetsByMap.get(id) ?? []) {
        target.classList.toggle('is-observed', id === map);
        target.setAttribute('aria-pressed', String(id === this.pinned));
      }
    }
    const occurrences = map === null ? [] : this.atomsByMap.get(map) ?? [];
    const info = occurrences.find((atom) => atom.side === 'products') ?? occurrences[0];
    const atom3D = this.linked && map !== null ? this.model.get(map) : undefined;
    const previousOverlay = this.activeOverlay;
    let overlay: AtomOverlay | null = null;
    if (atom3D && this.viewer && map !== null) {
      overlay = this.overlays.get(map) ?? null;
      if (!overlay) {
        const center = { x: atom3D.x, y: atom3D.y, z: atom3D.z };
        overlay = {
          halo: this.viewer.addSphere({ center, radius: atom3D.elem === 'H' ? .5 : .72,
            color: '#9061de', opacity: .4, clickable: false, hoverable: false }),
          label: this.viewer.addLabel(info?.label ?? atom3D.elem, { position: center, fontSize: 12,
            fontColor: '#58348a', backgroundColor: '#f2e9ff', backgroundOpacity: .95, borderThickness: 0,
            inFront: true, alignment: 'bottomLeft' }, undefined, true),
        };
        this.overlays.set(map, overlay);
      }
    }
    if (overlay !== previousOverlay) {
      this.hideOverlay();
      overlay?.halo.updateStyle({ hidden: false });
      overlay?.label.show();
      this.activeOverlay = overlay;
    }
    this.host3D.dataset.observedAtom = atom3D && map !== null ? String(map) : '';
    this.diagram.dataset.observedAtom = map !== null ? String(map) : '';
    this.clearButton.disabled = map === null;
    if (!info) {
      this.status.textContent = this.unavailable3D
        ? `${this.unavailable3D} Click or tap an atom to inspect its mapped 2D occurrences.`
        : this.modelAtoms.length && !this.linked && this.atoms.length
        ? 'Atom linking is unavailable for this preview.'
        : 'Hover an atom to find it in both views. Click or tap to keep it selected.';
    } else {
      const species = [...new Set(occurrences.map((atom) => atom.speciesName))].join(' → ');
      const state = this.pinned === map ? ' · selected' : '';
      const linkNote = this.unavailable3D ? ` · ${this.unavailable3D}` : atom3D ? ' · linked in 3D' : !info.linkedTo3D ? ' · outside the main-product 3D view'
        : !this.modelAtoms.length ? ' · use Compare to link with 3D' : ' · atom linking unavailable';
      this.status.textContent = `${info.label} · ${species}${linkNote}${state}`;
    }
    if (!this.host3D.hidden && (force || overlay !== previousOverlay)) this.viewer?.render();
  }
}
