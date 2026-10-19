import { indexModelAtoms, safeDiagramSvg, type AtomLink, type AtomViewer, type ModelAtom } from './atom-inspector';

export type StructureReference = { name: string; smiles: string };
type Group = { id: string; type: string; label: string; atomMaps: number[]; reactions: { mechanism: string; classifications: string[] }[] };
type Model = { representation: string; reason?: string; molfile?: string; atomLinks?: AtomLink[]; forceField?: string; converged?: boolean };
type Inspection = { name: string; formula: string; groups: Group[]; svg: string; note: string; model?: Model;
  stereochemistry?: { chiralCenters: { atomMap: number; assignment: string | null }[]; alkenes: { atomMaps: number[]; assignment: string | null; cisTrans: string | null }[]; note: string };
  e2Geometry?: { atomMaps: number[]; dihedralDegrees: number; antiPeriplanar: boolean }[] };
export type GroupViewer = AtomViewer & {
  removeAllModels: () => void;
  addModel: (data: string, format: string, options?: { keepH: boolean }) => { selectedAtoms: (selection: Record<string, never>) => ModelAtom[] };
  setStyle: (selection: Record<string, never>, style: Record<string, unknown>) => void;
  zoomTo: () => void; resize: () => void;
};
function node<K extends keyof HTMLElementTagNameMap>(tag: K, text = '', className = '') {
  const result = document.createElement(tag); result.textContent = text; result.className = className; return result;
}

/** Exact static group overlays; no clickable halos competing with rotation. */
export class GroupHighlighter {
  private maps = new Set<number>();
  private model = new Map<number, ModelAtom>();
  private shapes: unknown[] = [];
  constructor(private root: HTMLElement, private viewer?: AtomViewer) {}
  setGroup(maps: number[]) { this.maps = new Set(maps); this.paint(); }
  setModel(atoms: ModelAtom[], links: AtomLink[]) { this.model = groupModelCorrespondence(this.root, atoms, links); this.paint(); }
  reset() { this.maps.clear(); this.model.clear(); this.paint(); }
  private paint() {
    for (const target of this.root.querySelectorAll<SVGElement>('.atom-target')) target.classList.toggle('is-functional-group', this.maps.has(Number(target.dataset.atomMap)));
    for (const shape of this.shapes) this.viewer?.removeShape(shape); this.shapes = [];
    for (const map of this.maps) {
      const atom = this.model.get(map); if (!atom || !this.viewer) continue;
      this.shapes.push(this.viewer.addSphere({ center: { x: atom.x, y: atom.y, z: atom.z }, color: '#208269', radius: .7, opacity: .28, clickable: false, hoverable: false }));
    }
    this.viewer?.render();
  }
}

export function groupModelCorrespondence(root: HTMLElement, atoms: ModelAtom[], links: AtomLink[]) {
  const model = indexModelAtoms(links, atoms);
  const targets = Array.from(root.querySelectorAll<SVGElement>('.atom-target'));
  return targets.length === model.size && new Set(targets.map((target) => Number(target.dataset.atomMap))).size === targets.length
    && targets.every((target) => model.get(Number(target.dataset.atomMap))?.elem === target.dataset.element) ? model : new Map<number, ModelAtom>();
}

export class FunctionalGroupPanel {
  private geometry = node('div', '', 'group-geometry');
  private references: (StructureReference | null)[] = [];
  private signature = '';
  private revision = 0;
  private controller: AbortController | null = null;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private list = node('div', '', 'group-compounds');
  private scene = node('div', '', 'group-scene');
  private drawing = node('div', '', 'group-drawing');
  private modelHost = node('div', '', 'group-model');
  private status = node('p', '', 'insight-note');
  private selection = node('p', '', 'group-selection');
  private viewButton = node('button', 'View reactant 3D');
  private viewer?: GroupViewer;
  private highlighter: GroupHighlighter;
  private chosen: { slot: number; data: Inspection; group: Group | null } | null = null;
  constructor(private host: HTMLDetailsElement, private factory?: (host: HTMLElement) => GroupViewer) {
    host.append(node('summary', 'Inspect functional groups'), this.list, this.scene);
    this.status.setAttribute('role', 'status'); this.drawing.tabIndex = 0; this.drawing.setAttribute('role', 'region');
    this.drawing.setAttribute('aria-label', 'Selected reactant structure'); this.viewButton.type = 'button';
    this.viewButton.addEventListener('click', () => void this.show3D());
    this.scene.append(this.selection, this.drawing, this.viewButton, this.modelHost, this.status, this.geometry);
    this.scene.hidden = true; this.modelHost.hidden = true;
    this.highlighter = new GroupHighlighter(this.drawing);
    host.addEventListener('toggle', () => { if (host.open && !this.modelHost.hidden) this.resize(); });
    if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => this.resize()).observe(this.modelHost);
  }
  setReactants(references: (StructureReference | null)[]) {
    const signature = JSON.stringify(references);
    if (this.signature === signature) return; // Conditions do not change identity.
    this.signature = signature; this.references = references; this.revision += 1;
    this.controller?.abort(); this.controller = null; clearTimeout(this.timer);
    this.chosen = null; this.clearModel(); this.drawing.replaceChildren(); this.scene.hidden = true;
    this.list.replaceChildren(node('p', references.some(Boolean) ? 'Inspecting resolved structures…' : 'Select an exact structure to inspect its groups.', 'insight-note'));
    if (references.some(Boolean)) this.timer = setTimeout(() => void this.inspect(this.revision), 180);
  }
  private resize() { if (!this.modelHost.hidden && this.host.open) { this.viewer?.resize(); this.viewer?.render(); } }
  private clearModel() { this.highlighter.reset(); this.viewer?.removeAllModels(); this.modelHost.hidden = true; this.status.textContent = ''; this.geometry.replaceChildren(); this.viewButton.disabled = false; }
  private async request(reference: StructureReference, include3D: boolean, controller: AbortController): Promise<Inspection> {
    const response = await fetch('/api/reactions/inspect', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reactant: reference, include3D }), signal: controller.signal });
    const payload = await response.json() as Inspection | { error: string };
    if (!response.ok || 'error' in payload) throw new Error('error' in payload ? payload.error : 'Group inspection is unavailable.');
    return payload;
  }
  private async inspect(revision: number) {
    const controller = new AbortController(); this.controller = controller;
    const results = await Promise.all(this.references.map(async (reference) => {
      if (!reference) return null;
      try { return await this.request(reference, false, controller); } catch (error) { return error instanceof Error ? error.message : 'Inspection unavailable'; }
    }));
    if (revision !== this.revision || controller.signal.aborted) return;
    this.controller = null; this.list.replaceChildren();
    results.forEach((result, slot) => {
      const section = node('section'); section.append(node('h3', `Molecule ${slot + 1} · ${this.references[slot]?.name ?? 'Not selected'}`));
      if (!result || typeof result === 'string') { section.append(node('p', result ?? 'Select an exact structure.', 'insight-note')); this.list.append(section); return; }
      const choices = node('div', '', 'group-choices'); choices.setAttribute('role', 'group'); choices.setAttribute('aria-label', `Molecule ${slot + 1} functional groups`);
      for (const group of result.groups) {
        const button = node('button', `${group.label} · atoms ${group.atomMaps.join('–')}`); button.type = 'button'; button.setAttribute('aria-pressed', 'false');
        button.addEventListener('click', () => {
          for (const other of this.list.querySelectorAll('button')) other.setAttribute('aria-pressed', String(other === button));
          this.choose(slot, result, group);
        }); choices.append(button);
      }
      const view = node('button', 'Inspect structure'); view.type = 'button';
      view.addEventListener('click', () => { for (const other of this.list.querySelectorAll('button')) other.setAttribute('aria-pressed', 'false'); this.choose(slot, result, null); });
      section.append(choices); if (!result.groups.length) section.append(node('p', 'No listed functional group detected.', 'insight-note'));
      section.append(view); this.list.append(section);
      if (result.stereochemistry) {
        const stereo = node('details'); stereo.append(node('summary', 'Stereochemistry'));
        for (const center of result.stereochemistry.chiralCenters) stereo.append(node('p', `Atom ${center.atomMap}: ${center.assignment ?? 'potential center · unassigned'}`));
        for (const alkene of result.stereochemistry.alkenes) stereo.append(node('p', `C=C ${alkene.atomMaps.join('–')}: ${alkene.assignment ?? 'E/Z capable · unassigned'}${alkene.cisTrans ? ` · ${alkene.cisTrans} (H/H reference)` : ''}`));
        if (!result.stereochemistry.chiralCenters.length && !result.stereochemistry.alkenes.length) stereo.append(node('p', 'No listed tetrahedral center or E/Z-capable bond.'));
        stereo.append(node('p', result.stereochemistry.note, 'insight-note')); section.append(stereo);
      }
    });
  }
  private choose(slot: number, data: Inspection, group: Group | null) {
    // A new selection also invalidates an in-flight conformer request.
    const sameStructure = this.chosen?.slot === slot && this.chosen.data === data;
    this.revision += 1; this.controller?.abort(); this.controller = null;
    if (!sameStructure) this.clearModel();
    this.viewButton.disabled = !this.factory;
    this.chosen = { slot, data, group }; this.scene.hidden = false;
    if (!sameStructure) {
      const svg = safeDiagramSvg(data.svg);
      for (const target of svg.querySelectorAll('.atom-target')) { target.removeAttribute('tabindex'); target.setAttribute('role', 'presentation'); }
      this.drawing.replaceChildren(svg);
    }
    this.highlighter.setGroup(group?.atomMaps ?? []);
    this.selection.textContent = `${data.name} · ${data.formula}${group ? ` · ${group.label}` : ''}`;
    const available = group?.reactions.map((reaction) => reaction.mechanism).join(', ');
    this.status.textContent = group ? (available ? `Implemented group-level rules: ${available}. ${data.note}` : 'Group recognized; no reaction rule for this group is implemented yet.') : data.note;
    if (!this.modelHost.hidden) this.status.textContent += ' Green marks the group in both views; this conformer is not a mechanism geometry.';
  }
  private async show3D() {
    const chosen = this.chosen, reference = chosen && this.references[chosen.slot]; if (!chosen || !reference || !this.factory) return;
    const revision = this.revision; this.controller?.abort(); const controller = new AbortController(); this.controller = controller;
    this.viewButton.disabled = true; this.status.textContent = 'Calculating this reactant’s 3D shape…';
    try {
      const payload = await this.request(reference, true, controller);
      if (revision !== this.revision || controller.signal.aborted) return;
      const model = payload.model;
      if (!model || model.representation !== '3d' || !model.molfile) { this.status.textContent = model?.reason ?? '3D is unavailable for this structure.'; return; }
      this.modelHost.hidden = false;
      if (!this.viewer) { this.viewer = this.factory(this.modelHost); this.highlighter = new GroupHighlighter(this.drawing, this.viewer); }
      this.viewer.removeAllModels();
      const atoms = this.viewer.addModel(model.molfile, 'sdf', { keepH: true }).selectedAtoms({});
      const links = model.atomLinks ?? [];
      if (!groupModelCorrespondence(this.drawing, atoms, links).size) throw new Error('Exact atom correspondence is unavailable; the model was not shown.');
      this.viewer.setStyle({}, { stick: { radius: .11 }, sphere: { scale: .27 } });
      this.highlighter.setModel(atoms, links); this.highlighter.setGroup(chosen.group?.atomMaps ?? []);
      this.viewer.zoomTo(); this.resize();
      this.status.textContent = `Green marks the same group in both views. Drag to rotate · scroll to zoom. ${model.forceField ?? 'Calculated'} conformer${model.converged === false ? ' · optimization not converged' : ''}; not a mechanism geometry.`;
      if (payload.e2Geometry?.length) {
        const geometry = node('details', '', 'e2-geometry'); geometry.append(node('summary', 'E2 torsions · this conformer only'));
        for (const site of payload.e2Geometry) geometry.append(node('p', `${site.atomMaps.join('–')}: ${site.dihedralDegrees}° · ${site.antiPeriplanar ? 'anti-periplanar (±15°)' : 'not anti-periplanar'}`));
        geometry.append(node('p', 'Calculated reactant conformer only; not proof of accessible reaction geometry or an E/Z product prediction.', 'insight-note'));
        this.geometry.replaceChildren(geometry);
      }
    } catch (error) {
      if (revision === this.revision && !controller.signal.aborted) { this.clearModel(); this.status.textContent = error instanceof Error ? error.message : '3D unavailable.'; }
    } finally { if (revision === this.revision) { this.controller = null; this.viewButton.disabled = false; } }
  }
}
