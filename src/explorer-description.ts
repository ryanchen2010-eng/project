import { chemicalProfileForCid } from './chemical-descriptions';
import { PROPERTY_GUIDE } from './chemical-property-guide';

type InformationMolecule = {
  cid: number;
  name: string;
  formula?: string;
  description?: string;
  properties?: Partial<Record<'mass' | 'geometry' | 'polarity' | 'bonds' | 'melting' | 'boiling' | 'everyday', string>>;
};

export type InformationStatus = 'known' | 'unreviewed' | 'unavailable' | 'not-applicable';
export type InformationRow = { key: string; label: string; value: string; status: InformationStatus };
const commonProperties = new Set(['flammability', 'reactivity', 'toxicity', 'acidity', 'oxidation', 'combustion']);

/** Short missing-data labels never erase known phase behaviour or conditions. */
export function normalizeInformationValue(raw: unknown): { value: string; status: InformationStatus } {
  const value = typeof raw === 'string' ? raw.trim()
    : typeof raw === 'number' && Number.isFinite(raw) ? String(raw) : '';
  if (!value || /^(?:not available|unknown|no data)(?:\b|$)/i.test(value)) {
    return { value: 'Not available', status: 'unavailable' };
  }
  if (/^(?:n\/?a|not applicable)$/i.test(value)) {
    return { value: 'N/A', status: 'not-applicable' };
  }
  if (/^not reviewed\b|not been reviewed|explanation not reviewed|^no curated.*note/i.test(value)) {
    return { value: 'Not reviewed', status: 'unreviewed' };
  }
  return { value, status: 'known' };
}

/** Exact CID matching prevents another compound's reviewed properties leaking into a search result. */
export function buildMoleculeInformation(molecule: InformationMolecule) {
  const profile = chemicalProfileForCid(molecule.cid);
  const properties = molecule.properties ?? {};
  const basicRows: [string, string, unknown][] = [
    ['formula', 'Molecular formula', molecule.formula],
    ['mass', 'Molar mass', properties.mass],
    ['geometry', 'Geometry', properties.geometry],
    ['polarity', 'Polarity', properties.polarity],
    ['bonds', 'Bond types', properties.bonds],
    ['melting', 'Melting point', properties.melting],
    ['boiling', 'Boiling / phase behaviour', properties.boiling],
    ['everyday', 'Everyday uses', profile?.uses ?? properties.everyday],
  ];
  const rows: InformationRow[] = basicRows.map(([key, label, value]) => ({ key, label, ...normalizeInformationValue(value) }));
  for (const property of PROPERTY_GUIDE) {
    if (!commonProperties.has(property.key) && !Object.hasOwn(profile?.properties ?? {}, property.key)) continue;
    rows.push({ key: property.key, label: property.label, ...normalizeInformationValue(profile?.properties[property.key] ?? 'Not reviewed') });
  }
  const references: { label: string; url: string }[] = [];
  if (Number.isSafeInteger(molecule.cid) && molecule.cid > 0) {
    references.push({ label: `PubChem · CID ${molecule.cid}`, url: `https://pubchem.ncbi.nlm.nih.gov/compound/${molecule.cid}` });
  }
  for (const reference of profile?.sources ?? []) {
    if (!references.some((existing) => existing.url === reference.url)) references.push(reference);
  }
  return { overview: profile?.overview ?? molecule.description ?? 'PubChem record; properties not reviewed.', rows, references };
}

/** One visible panel for values; definitions and references remain optional. */
export function renderMoleculeInformation(host: HTMLElement, molecule: InformationMolecule) {
  const information = buildMoleculeInformation(molecule);
  host.replaceChildren();
  const heading = document.createElement('h3');
  heading.id = 'molecule-information-heading';
  heading.textContent = 'Molecule information';
  const overview = document.createElement('p');
  overview.className = 'molecule-information__overview';
  overview.textContent = information.overview;
  const grid = document.createElement('dl');
  grid.className = 'molecule-information__grid';
  for (const property of information.rows) {
    const row = document.createElement('div');
    row.dataset.property = property.key;
    row.dataset.status = property.status;
    const term = document.createElement('dt');
    const value = document.createElement('dd');
    term.textContent = property.label;
    value.textContent = property.value;
    row.append(term, value);
    grid.append(row);
  }
  const help = document.createElement('details');
  help.className = 'molecule-information__help';
  const summary = document.createElement('summary');
  summary.textContent = 'Definitions and sources';
  const legend = document.createElement('p');
  legend.className = 'molecule-information__legend';
  legend.textContent = 'Not available: no verified value · Not reviewed: not checked · N/A: not applicable';
  const definitions = document.createElement('dl');
  definitions.className = 'molecule-information__definitions';
  const displayedKeys = new Set(information.rows.map((row) => row.key));
  for (const property of PROPERTY_GUIDE) {
    if (!displayedKeys.has(property.key)) continue;
    const row = document.createElement('div');
    const term = document.createElement('dt');
    const definition = document.createElement('dd');
    term.textContent = property.label;
    definition.append(document.createTextNode(`${property.definition} `));
    const link = sourceLink(property.source.label, property.source.url);
    if (link) definition.append(link);
    row.append(term, definition);
    definitions.append(row);
  }
  const sources = document.createElement('p');
  sources.className = 'molecule-information__sources';
  sources.append(document.createTextNode('References: '));
  let sourceCount = 0;
  for (const reference of information.references) {
    const link = sourceLink(reference.label, reference.url);
    if (!link) continue;
    if (sourceCount++) sources.append(document.createTextNode(' · '));
    sources.append(link);
  }
  const disclaimer = document.createElement('p');
  disclaimer.className = 'molecule-information__disclaimer';
  disclaimer.textContent = 'Educational overview—not a safety data sheet. pH describes a solution; behaviour depends on conditions.';
  help.append(summary, legend, definitions, sources, disclaimer);
  host.append(heading, overview, grid, help);
}

function sourceLink(label: string, url: string): HTMLAnchorElement | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password) return null;
    const link = document.createElement('a');
    link.textContent = label;
    link.href = parsed.href;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    return link;
  } catch {
    return null;
  }
}
