/** Progressive information about one engine-selected pathway, not four recipes. */
export type ReactionInformation = {
  version: number; name: string; primaryFamily: string; classifications: string[];
  reactantGroups: string[]; productGroups: string[]; transformation: string; difficulty: string;
  requirements: Record<string, string>; capabilities: Record<string, string>;
  limitations: string[]; references: { title: string; url: string }[];
  stereochemistry?: { reactant: { chiralCenters: { atomMap: number; assignment: string | null }[]; alkenes: { atomMaps: number[]; assignment: string | null }[] };
    product: { chiralCenters: { atomMap: number; assignment: string | null }[]; alkenes: { atomMaps: number[]; assignment: string | null }[] }; effect: string; geometryRequirement: string | null };
};
type Snapshot = { information?: ReactionInformation; explanation: string; conditions: string; sourceUrl: string };
function node<K extends keyof HTMLElementTagNameMap>(tag: K, text = '', className = '') {
  const result = document.createElement(tag); result.textContent = text; result.className = className; return result;
}
const title = (value: string) => {
  const text = value.replace(/([a-z])([A-Z])/g, '$1 $2').replaceAll('-', ' ').toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export class ReactionInformationPanel {
  private snapshot: Snapshot | null = null;
  private depth = 'Basic';
  constructor(private host: HTMLDetailsElement, private openMechanism: () => void) { this.setReaction(); }
  setReaction(snapshot?: Snapshot) {
    this.snapshot = snapshot ?? null; this.depth = 'Basic'; this.host.hidden = !snapshot; this.host.open = false; this.render();
  }
  private render() {
    this.host.replaceChildren(); this.host.append(node('summary', 'Reaction information'));
    const snapshot = this.snapshot; if (!snapshot) return;
    const info = snapshot.information;
    if (!info) { this.host.append(node('p', snapshot.explanation), node('p', snapshot.conditions)); return; }
    const controls = node('div', '', 'information-depth'); controls.setAttribute('role', 'group'); controls.setAttribute('aria-label', 'Information depth');
    for (const depth of ['Basic', 'Explanation', 'Mechanism', 'Advanced']) {
      const button = node('button', depth); button.type = 'button'; button.setAttribute('aria-pressed', String(depth === this.depth));
      // An unavailable mechanism is visibly labelled, not a fake action.
      if (depth === 'Mechanism' && info.capabilities.mappedMechanism !== 'supported') button.textContent = 'Mechanism · unavailable';
      button.addEventListener('click', () => { this.depth = depth; this.render(); }); controls.append(button);
    }
    const content = node('div', '', 'information-content'); content.setAttribute('aria-live', 'polite');
    if (this.depth === 'Basic') {
      content.append(node('p', info.classifications.join(' + '), 'information-classifications'), node('p', info.transformation),
        node('p', `${info.reactantGroups.join(' / ')} → ${info.productGroups.join(' / ')}`, 'insight-note'));
    } else if (this.depth === 'Explanation') {
      content.append(node('p', snapshot.explanation), node('h3', 'Conditions'), node('p', snapshot.conditions));
    } else if (this.depth === 'Mechanism') {
      content.append(node('p', info.capabilities.mappedMechanism === 'supported'
        ? 'Atom-mapped steps are available in the Mapped mechanism panel.' : 'A validated step-by-step mechanism is not implemented for this pathway. The net equation is not a mechanism.'));
      if (info.capabilities.mappedMechanism === 'supported') {
        const open = node('button', 'Open mapped mechanism'); open.type = 'button'; open.addEventListener('click', this.openMechanism); content.append(open);
      }
    } else {
      content.append(node('p', `Scope level: ${info.difficulty}`));
      const list = node('ul');
      for (const [key, value] of Object.entries(info.capabilities)) list.append(node('li', `${title(key)}: ${value}`));
      for (const note of info.limitations) list.append(node('li', note)); content.append(list);
      if (info.stereochemistry) {
        content.append(node('h3', 'Mapped stereochemistry'), node('p', info.stereochemistry.effect));
        for (const [label, value] of [['Reactant', info.stereochemistry.reactant], ['Product', info.stereochemistry.product]] as const) {
          for (const center of value.chiralCenters) content.append(node('p', `${label} atom ${center.atomMap}: ${center.assignment ?? 'unassigned'}`));
          for (const bond of value.alkenes) content.append(node('p', `${label} C=C ${bond.atomMaps.join('–')}: ${bond.assignment ?? 'unassigned'}`));
        }
        if (info.stereochemistry.geometryRequirement) content.append(node('p', info.stereochemistry.geometryRequirement));
      }
    }
    const references = node('details'); references.append(node('summary', 'References'));
    for (const reference of info.references) {
      if (!/^https:\/\//i.test(reference.url)) continue;
      const link = node('a', `${reference.title} ↗`); link.href = reference.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; references.append(link);
    }
    this.host.append(controls, content, references);
  }
}
