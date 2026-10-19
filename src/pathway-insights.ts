import { indexModelAtoms, safeDiagramSvg, type AtomLink, type AtomViewer, type ModelAtom } from './atom-inspector';

export type PathwayReasoning = {
  label: 'Model conditions match' | 'Strong match' | 'Possible' | 'Unfavorable' | 'Unsupported' | 'Reference differs' | 'Conditions incomplete' | 'Disfavored factors' | 'Not evaluated' | 'Acid activation required' | 'Lindlar activation required' | 'Active-metal activation required' | 'Radical pathway unsupported';
  factors: { factor: string; value: string; effect: 'favors' | 'disfavors' | 'neutral' | 'unknown'; explanation: string; atomMaps: number[] }[];
  note: string;
};
export type PathwayComparison = {
  columns: { id: string; pathway: string; site: string; label: string }[];
  rows: { factor: string; cells: { reactionId: string; effect: string; value: string; explanation: string }[] }[];
  note: string;
};
export type ElectronEndpoint = { type: 'atom' | 'bond' | 'lone-pair'; atomMaps: number[] };
export type ElectronMove = { id: string; source: ElectronEndpoint; destination: ElectronEndpoint; description: string };
export type BondChange = { atomMaps: number[]; kind: string; before: number | null; after: number | null };
export type MechanismStep = {
  id: string; title: string; description: string; concerted: boolean;
  electronMoves: ElectronMove[]; bondsFormed: BondChange[]; bondsBroken: BondChange[]; bondOrderChanges: BondChange[];
  intermediate: { kind: 'Intermediate'; name: string; svg: string } | null;
  state: { kind: string; name: string; svg: string };
  beforeState?: { kind: string; name: string; svg: string };
  protonTransfers?: BondChange[];
};
export type ReactionMechanism = {
  version: number; type: string; siteId: string; roles: Record<string, number>; steps: MechanismStep[];
  energyProfile: { qualitative: boolean; stepCount: number; rateDeterminingStep: number; intermediates: number; activationEnergies: null; note: string };
  limitations: string[];
};

const labels: Record<string, string> = { 'functional-group': 'Functional group', 'reaction-site': 'Selected site',
  substrate: 'Substrate', 'leaving-group': 'Leaving group', nucleophile: 'Nucleophile', 'base-strength': 'Base',
  'steric-hindrance': 'Sterics', 'beta-hydrogen': 'Beta hydrogen', 'carbocation-stability': 'Carbocation',
  'oxidation-stage': 'Oxidation stage', oxidationStage: 'Stage setting', 'reagent-group': 'Reagent group' };
const label = (key: string) => labels[key] ?? key.charAt(0).toUpperCase() + key.slice(1).replaceAll('-', ' ');
function element<K extends keyof HTMLElementTagNameMap>(tag: K, text = '', className = ''): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag); node.textContent = text; node.className = className; return node;
}

export function renderReasoning(reasoning: PathwayReasoning, confidenceLabel?: string): HTMLDetailsElement {
  const details = element('details', '', 'pathway-reasoning');
  details.append(element('summary', confidenceLabel ? `Why This Option? · ${confidenceLabel}` : `Why This Pathway? · ${reasoning.label}`));
  const list = element('ul');
  for (const factor of reasoning.factors) {
    const item = element('li', '', `factor-${factor.effect}`);
    item.append(element('strong', `${label(factor.factor)}: ${factor.value} · ${factor.effect}`), element('span', factor.explanation));
    list.append(item);
  }
  details.append(list, element('p', reasoning.note, 'insight-note'));
  return details;
}

export function renderComparison(host: HTMLElement, comparison?: PathwayComparison | null) {
  host.replaceChildren(); host.hidden = !comparison || comparison.columns.length < 2;
  if (host.hidden || !comparison) return;
  const details = element('details', '', 'pathway-comparison');
  details.append(element('summary', `Compare ${comparison.columns.length} net product options`));
  const scroll = element('div', '', 'comparison-scroll'); scroll.tabIndex = 0;
  scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', 'Pathway factors; scroll to compare columns');
  const table = element('table');
  table.append(element('caption', 'Qualitative factors — not probabilities or a predicted winner'));
  const head = element('thead'); const header = element('tr');
  header.append(element('th', 'Factor'));
  for (const column of comparison.columns) {
    const cell = element('th', `${column.pathway} · ${column.label}\n${column.site}`); cell.scope = 'col'; header.append(cell);
  }
  head.append(header); table.append(head); const body = element('tbody');
  for (const row of comparison.rows) {
    const line = element('tr'); const heading = element('th', label(row.factor)); heading.scope = 'row'; line.append(heading);
    for (const column of comparison.columns) {
      const value = row.cells.find((cell) => cell.reactionId === column.id);
      const cell = element('td', '', `factor-${value?.effect ?? 'unknown'}`);
      cell.append(element('strong', `${value?.effect ?? 'unknown'} · ${value?.value ?? 'N/A'}`), element('span', value?.explanation ?? 'Not available'));
      line.append(cell);
    }
    body.append(line);
  }
  table.append(body); scroll.append(table); details.append(scroll, element('p', comparison.note, 'insight-note')); host.append(details);
}

/** Mechanism colors are independent of purple hover/pin and amber selected-site rings. */
export class MechanismHighlighter {
  private model = new Map<number, ModelAtom>();
  private shapes: unknown[] = [];
  private source = new Set<number>();
  private destination = new Set<number>();
  constructor(private root: HTMLElement, private viewer: AtomViewer | null) {}
  setModel(atoms: ModelAtom[], links: AtomLink[]) { this.clearModel(); this.model = indexModelAtoms(links, atoms); this.paint(); }
  clearModel() { this.removeShapes(); this.model.clear(); }
  setMoves(moves: ElectronMove[]) {
    this.source = new Set(moves.flatMap((move) => move.source.atomMaps));
    this.destination = new Set(moves.flatMap((move) => move.destination.atomMaps)); this.paint();
  }
  refresh() { this.paint(); }
  reset() { this.source.clear(); this.destination.clear(); this.clearModel(); this.paint(); }
  private removeShapes() { for (const shape of this.shapes) this.viewer?.removeShape(shape); this.shapes = []; }
  private paint() {
    for (const target of this.root.querySelectorAll<SVGElement>('.atom-target')) {
      const map = Number(target.dataset.atomMap);
      target.classList.toggle('is-electron-source', this.source.has(map));
      target.classList.toggle('is-electron-destination', this.destination.has(map));
    }
    this.removeShapes();
    for (const map of new Set([...this.source, ...this.destination])) {
      const atom = this.model.get(map); if (!atom || !this.viewer) continue;
      const color = this.source.has(map) && this.destination.has(map) ? '#7f5cc1' : this.source.has(map) ? '#bd5923' : '#168ba0';
      this.shapes.push(this.viewer.addSphere({ center: { x: atom.x, y: atom.y, z: atom.z }, radius: .69,
        color, opacity: .28, clickable: false, hoverable: false }));
    }
    this.viewer?.render();
  }
}

export class MechanismPanel {
  private mechanism: ReactionMechanism | null = null;
  private current = 0;
  private content: HTMLDivElement;
  private highlighter: MechanismHighlighter;
  constructor(private host: HTMLDetailsElement, root: HTMLElement, viewer: AtomViewer | null) {
    this.highlighter = new MechanismHighlighter(root, viewer);
    host.append(element('summary', 'Mapped mechanism'));
    this.content = element('div', '', 'mechanism-content'); host.append(this.content);
    host.addEventListener('toggle', () => {
      if (host.open) this.highlightStep(); else this.highlighter.setMoves([]);
    });
  }
  setMechanism(mechanism?: ReactionMechanism | null) {
    this.reset(); this.mechanism = mechanism ?? null;
    this.host.hidden = !this.mechanism;
    if (this.mechanism) this.render();
  }
  setModel(atoms: ModelAtom[], links: AtomLink[]) { this.highlighter.setModel(atoms, links); }
  clearModel() { this.highlighter.clearModel(); }
  reset() { this.highlighter.reset(); this.mechanism = null; this.current = 0; this.host.hidden = true; this.host.open = false; this.content.replaceChildren(); }
  private highlightStep() {
    this.highlighter.setMoves(this.host.open ? this.mechanism?.steps[this.current]?.electronMoves ?? [] : []);
  }
  private render() {
    const mechanism = this.mechanism; if (!mechanism) return;
    this.content.replaceChildren();
    const controls = element('div', '', 'mechanism-step-buttons'); controls.setAttribute('role', 'group'); controls.setAttribute('aria-label', 'Mechanism steps');
    mechanism.steps.forEach((step, index) => {
      const button = element('button', `${index + 1}. ${step.title}`); button.type = 'button';
      button.setAttribute('aria-pressed', String(this.current === index));
      button.addEventListener('click', () => { this.current = index; this.render(); }); controls.append(button);
    });
    const step = mechanism.steps[this.current];
    this.content.append(controls, element('h3', `${mechanism.type} · Step ${this.current + 1}${step.concerted ? ' · Concerted' : ''}`), element('p', step.description));
    this.content.append(element('p', Object.entries(mechanism.roles).map(([role, map]) => `${label(role)}: atom ${map}`).join(' · '), 'mechanism-roles'));
    for (const record of [step.beforeState, step.state].filter((value): value is NonNullable<typeof value> => Boolean(value))) {
      const state = element('div', '', 'mechanism-state');
      state.tabIndex = 0; state.setAttribute('role', 'region'); state.setAttribute('aria-label', `${record.kind}; scroll for the full mapped structure`);
      state.append(element('strong', `${record.kind} — ${record.name}`));
      const svg = safeDiagramSvg(record.svg);
      // Intermediate atoms are not part of the final-product measurement model.
      for (const atom of svg.querySelectorAll('.atom-target')) { atom.removeAttribute('tabindex'); atom.setAttribute('role', 'presentation'); }
      state.append(svg); this.content.append(state);
    }
    const changes = element('ul', '', 'mechanism-bond-changes');
    for (const [title, items] of [['Bond forming', step.bondsFormed], ['Bond breaking', step.bondsBroken], ['Bond order', step.bondOrderChanges]] as const) {
      for (const change of items ?? []) changes.append(element('li', `${title}: atoms ${change.atomMaps.join('–')}${title === 'Bond order' ? ` (${change.before} → ${change.after})` : ''}`));
    }
    if (step.protonTransfers?.length) changes.append(element('li', 'Proton movement is shown explicitly in the mapped H-containing bond changes.'));
    this.content.append(changes);
    this.content.append(element('p', 'Electron source: orange · destination: teal · both: purple. 3D highlights only atoms retained in the final main product.', 'insight-note'));
    const moves = element('div', '', 'electron-moves');
    for (const move of step.electronMoves) {
      const button = element('button', `${move.description}\n${move.source.type} ${move.source.atomMaps.join('–')} → ${move.destination.type} ${move.destination.atomMaps.join('–')}`);
      button.type = 'button'; button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => {
        for (const other of moves.querySelectorAll('button')) other.setAttribute('aria-pressed', String(other === button));
        this.highlighter.setMoves([move]);
      }); moves.append(button);
    }
    const all = element('button', 'Highlight all moves in this step'); all.type = 'button';
    all.addEventListener('click', () => { for (const button of moves.querySelectorAll('button')) button.setAttribute('aria-pressed', 'false'); this.highlightStep(); });
    moves.append(all); this.content.append(moves);
    const energy = element('details'); energy.append(element('summary', 'Qualitative energy topology'));
    const sequence = ['Reactants'];
    for (const item of mechanism.steps) sequence.push('barrier (not calculated)', item.intermediate ? item.intermediate.name : 'Products');
    energy.append(element('p', sequence.join(' → ')), element('p', mechanism.energyProfile.note, 'insight-note')); this.content.append(energy);
    const caveats = element('details'); caveats.append(element('summary', 'Mechanism limits'));
    const list = element('ul'); for (const note of mechanism.limitations) list.append(element('li', note)); caveats.append(list); this.content.append(caveats);
    this.highlightStep();
  }
}
