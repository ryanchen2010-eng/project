import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const projectFile = (path) => new URL(`../${path}`, import.meta.url);
const catalog = JSON.parse(await readFile(projectFile('src/shared-molecules.json'), 'utf8'));
const moduleUrls = new Map();

// Exercise the real data and renderer without loading the browser application.
async function moduleUrl(path) {
  if (moduleUrls.has(path)) return moduleUrls.get(path);
  const source = await readFile(projectFile(path), 'utf8');
  let outputText;
  if (path.endsWith('.json')) {
    outputText = `export default ${JSON.stringify(JSON.parse(source))};`;
  } else {
    ({ outputText } = ts.transpileModule(source, {
      compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
    }));
    const imports = [...outputText.matchAll(/from\s+(['"])(\.\/[^'"]+)\1/g)];
    for (const [, quote, specifier] of imports) {
      const directory = path.slice(0, path.lastIndexOf('/') + 1);
      const dependency = `${directory}${specifier.slice(2)}${/\.(?:ts|json)$/.test(specifier) ? '' : '.ts'}`;
      const dependencyUrl = await moduleUrl(dependency);
      outputText = outputText.replaceAll(`${quote}${specifier}${quote}`, `${quote}${dependencyUrl}${quote}`);
    }
  }
  const url = `data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`;
  moduleUrls.set(path, url);
  return url;
}

const { PROPERTY_GUIDE } = await import(await moduleUrl('src/chemical-property-guide.ts'));
const { chemicalProfiles, chemicalProfileForCid } = await import(await moduleUrl('src/chemical-descriptions.ts'));
const { buildMoleculeInformation, normalizeInformationValue, renderMoleculeInformation } =
  await import(await moduleUrl('src/explorer-description.ts'));
const { molecules } = await import(await moduleUrl('src/molecules.ts'));

const commonKeys = ['flammability', 'reactivity', 'toxicity', 'acidity', 'oxidation', 'combustion'];
const coreKeys = ['formula', 'mass', 'geometry', 'polarity', 'bonds', 'melting', 'boiling', 'everyday'];
const registeredKeys = new Set(PROPERTY_GUIDE.map(({ key }) => key));
const rowFor = (information, key) => information.rows.find((row) => row.key === key);
const wordCount = (value) => String(value).trim().split(/\s+/).filter(Boolean).length;
const sourceUrls = (information) => information.references.map(({ url }) => url);

function assertDirectHttpsSource(source) {
  assert.equal(typeof source.label, 'string');
  assert.ok(source.label.trim(), 'references have readable labels');
  const url = new URL(source.url);
  assert.equal(url.protocol, 'https:', 'references use HTTPS');
  assert.ok(url.hostname && url.pathname !== '/', 'references link directly to an informative page');
  assert.ok(!/\/(?:search|search_query)(?:\/|$)/i.test(url.pathname), 'not a search-results page');
  assert.ok(!/(?:^|\.)google\.[a-z.]+$/i.test(url.hostname), 'not a search-engine link');
}

test('compact teaching profiles cover every featured compound by exact CID', () => {
  assert.equal(catalog.length, 20);
  const expectedCids = catalog.map(({ cid }) => cid).sort((left, right) => left - right);
  const actualCids = Array.isArray(chemicalProfiles)
    ? chemicalProfiles.map(({ cid }) => cid)
    : Object.keys(chemicalProfiles).map(Number);
  assert.equal(new Set(actualCids).size, actualCids.length, 'no duplicate compound identities');
  assert.deepEqual(actualCids.sort((left, right) => left - right), expectedCids);
  for (const { cid, name } of catalog) {
    const profile = chemicalProfileForCid(cid);
    assert.ok(profile, `${name} has a reviewed profile`);
    assert.ok(profile.overview.trim(), `${name} has an overview`);
    assert.ok(wordCount(profile.overview) <= 35, `${name}: overview stays brief`);
    assert.ok(profile.uses.trim(), `${name} has a compact everyday-use value`);
    assert.ok(wordCount(profile.uses) <= 12, `${name}: uses are a short phrase`);
    for (const [key, value] of Object.entries(profile.properties)) {
      assert.ok(registeredKeys.has(key), `${name}: ${key} is registered`);
      assert.equal(typeof value, 'string');
      assert.ok(value.trim(), `${name}: ${key} is not an empty explanation`);
      assert.ok(wordCount(value) <= 22, `${name}: ${key} is a value or short phrase`);
    }
    assert.ok(profile.sources.length > 0, `${name} has compound references`);
    profile.sources.forEach(assertDirectHttpsSource);
  }
});

test('the property registry permits useful additions instead of a fixed six-card model', () => {
  assert.equal(registeredKeys.size, PROPERTY_GUIDE.length, 'registered keys are unique');
  commonKeys.forEach((key) => assert.ok(registeredKeys.has(key), `${key} remains supported`));
  for (const key of ['state', 'appearance', 'solubility', 'density', 'functionalGroups', 'hydrogenBonding', 'stability']) {
    assert.ok(registeredKeys.has(key), `${key} is an available additional property`);
  }
  for (const property of PROPERTY_GUIDE) {
    assert.ok(property.label.trim());
    assert.ok(property.definition.trim());
    assertDirectHttpsSource(property.source);
  }
  assert.ok(chemicalProfiles.some(({ properties }) =>
    Object.keys(properties).some((key) => !commonKeys.includes(key))), 'profiles actually use relevant added properties');
});

test('missing, unchecked, and inapplicable information remain different statuses', () => {
  for (const value of [undefined, null, '', '  ', 'Unknown', 'No data', 'Not available', 'Not available from PubChem']) {
    assert.deepEqual(normalizeInformationValue(value), { value: 'Not available', status: 'unavailable' });
  }
  for (const value of ['Not reviewed', 'Not reviewed for this compound', 'Explanation not reviewed', 'See structure; explanation not reviewed']) {
    assert.deepEqual(normalizeInformationValue(value), { value: 'Not reviewed', status: 'unreviewed' });
  }
  for (const value of ['N/A', 'Not applicable']) {
    assert.deepEqual(normalizeInformationValue(value), { value: 'N/A', status: 'not-applicable' });
  }
});

test('normalization preserves verified values, units, conditions, and phase behaviour', () => {
  for (const value of ['46.07 g/mol', '100 °C at 1 atm', 'Sublimes at −78.5 °C at 1 atm', 'Decomposes', 'Ionic lattice', 'No normal boiling point; decomposes']) {
    assert.deepEqual(normalizeInformationValue(`  ${value}  `), { value, status: 'known' });
  }
});

test('numeric values remain usable while malformed non-text inputs become unavailable', () => {
  for (const value of [0, 46.07, -78.5]) {
    assert.deepEqual(normalizeInformationValue(value), { value: String(value), status: 'known' });
  }
  for (const value of [NaN, Infinity, -Infinity, false, {}, []]) {
    assert.deepEqual(normalizeInformationValue(value), { value: 'Not available', status: 'unavailable' });
  }
});

test('all featured compounds combine physical and chemical data into one compact row model', () => {
  for (const molecule of molecules) {
    const information = buildMoleculeInformation(molecule);
    const keys = information.rows.map(({ key }) => key);
    assert.equal(new Set(keys).size, keys.length, `${molecule.name}: no duplicate properties`);
    assert.deepEqual(keys.slice(0, coreKeys.length), coreKeys, `${molecule.name}: basic physical fields remain visible`);
    for (const key of commonKeys) assert.ok(rowFor(information, key), `${molecule.name}: common ${key} row remains available`);
    assert.equal(rowFor(information, 'formula').value, molecule.formula);
    assert.equal(rowFor(information, 'mass').value, molecule.properties.mass);
    assert.equal(rowFor(information, 'everyday').value, chemicalProfileForCid(molecule.cid).uses);
    assert.equal(information.overview, chemicalProfileForCid(molecule.cid).overview);
    for (const row of information.rows) {
      assert.ok(row.label.trim());
      assert.ok(row.value.trim());
      assert.ok(['known', 'unreviewed', 'unavailable', 'not-applicable'].includes(row.status));
    }
    information.references.forEach(assertDirectHttpsSource);
    assert.equal(information.references[0].url, `https://pubchem.ncbi.nlm.nih.gov/compound/${molecule.cid}`);
  }
});

test('additional registered rows are driven by each compound rather than padded with empty fields', () => {
  for (const molecule of molecules) {
    const information = buildMoleculeInformation(molecule);
    const profile = chemicalProfileForCid(molecule.cid);
    const optionalKeys = PROPERTY_GUIDE.filter(({ key }) => !commonKeys.includes(key)).map(({ key }) => key);
    for (const key of optionalKeys) {
      if (profile.properties[key]?.trim()) {
        assert.equal(rowFor(information, key)?.value, profile.properties[key], `${molecule.name}: include ${key}`);
      } else {
        assert.equal(rowFor(information, key), undefined, `${molecule.name}: omit irrelevant ${key}`);
      }
    }
  }
});

test('unknown exact identities never borrow notes through a familiar name or formula', () => {
  for (const cid of [0, -1, 999999999, NaN, Infinity]) {
    assert.equal(chemicalProfileForCid(cid), undefined, `no profile for ${cid}`);
  }
  const unknown = buildMoleculeInformation({ cid: 999999999, name: 'Water', formula: 'H₂O' });
  assert.equal(unknown.rows.length, coreKeys.length + commonKeys.length);
  for (const key of commonKeys) {
    assert.deepEqual({ value: rowFor(unknown, key).value, status: rowFor(unknown, key).status },
      { value: 'Not reviewed', status: 'unreviewed' });
  }
  assert.equal(rowFor(unknown, 'formula').value, 'H₂O');
  assert.equal(rowFor(unknown, 'mass').value, 'Not available');
  assert.equal(rowFor(unknown, 'everyday').value, 'Not available');
  assert.ok(!unknown.overview.includes(chemicalProfileForCid(962).overview));
  assert.deepEqual(sourceUrls(unknown), ['https://pubchem.ncbi.nlm.nih.gov/compound/999999999']);
});

test('unknown compounds retain supplied PubChem facts without inferring missing chemistry', () => {
  const information = buildMoleculeInformation({ cid: 2244, name: 'Aspirin', formula: 'C₉H₈O₄', properties: {
    mass: '180.16 g/mol', geometry: 'See 3D structure; explanation not reviewed', polarity: 'Not reviewed',
    bonds: 'See the structure; explanation not reviewed', melting: 'Not available', boiling: 'N/A',
  } });
  assert.equal(rowFor(information, 'mass').value, '180.16 g/mol');
  assert.equal(rowFor(information, 'geometry').value, 'Not reviewed');
  assert.equal(rowFor(information, 'bonds').value, 'Not reviewed');
  assert.equal(rowFor(information, 'melting').status, 'unavailable');
  assert.equal(rowFor(information, 'boiling').status, 'not-applicable');
  assert.equal(rowFor(information, 'toxicity').value, 'Not reviewed');
});

test('concise notes preserve distinctions between fuels, oxidizers, aqueous pH, and isomers', () => {
  const ethanol = chemicalProfileForCid(702);
  const ether = chemicalProfileForCid(8254);
  assert.notEqual(ethanol.overview, ether.overview);
  assert.notDeepEqual(ethanol.properties, ether.properties);
  const oxygen = chemicalProfileForCid(977);
  assert.match(oxygen.properties.flammability, /not (?:combustible|flammable)|non[- ]?flammable/i);
  assert.match(`${oxygen.properties.flammability} ${oxygen.properties.reactivity}`, /supports?.*(?:burning|combustion)|oxidiz/i);
  assert.match(chemicalProfileForCid(962).properties.acidity, /7.*25/);
  assert.match(chemicalProfileForCid(222).properties.acidity, /(?:aqueous|in water|solution)/i);
  for (const cid of [962, 977, 5234, 14798]) {
    assert.ok(!/\d(?:[.,]\d+)?\s*(?:kJ|MJ)\s*\/?\s*mol/i.test(chemicalProfileForCid(cid).properties.combustion),
      `CID ${cid}: no invented combustion enthalpy`);
  }
});

test('special phase and ionic geometry values survive simplification', () => {
  const carbonDioxide = buildMoleculeInformation(molecules.find(({ cid }) => cid === 280));
  assert.match(rowFor(carbonDioxide, 'boiling').value, /sublim/i);
  assert.match(rowFor(carbonDioxide, 'boiling').value, /1 atm/);
  const glucose = buildMoleculeInformation(molecules.find(({ cid }) => cid === 5793));
  assert.match(rowFor(glucose, 'boiling').value, /decompos/i);
  for (const cid of [5234, 14798]) {
    const information = buildMoleculeInformation(molecules.find((molecule) => molecule.cid === cid));
    assert.match(rowFor(information, 'geometry').value, /ionic lattice/i);
    assert.equal(rowFor(information, 'geometry').status, 'known');
  }
});

class FakeText {
  constructor(value) { this.textContent = String(value); }
}

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.dataset = {};
    this.className = '';
    this.id = '';
  }
  append(...nodes) {
    this.children.push(...nodes.map((node) => typeof node === 'string' ? new FakeText(node) : node));
  }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  set textContent(value) { this.children = value ? [new FakeText(value)] : []; }
  get textContent() { return this.children.map((node) => node.textContent).join(''); }
  set innerHTML(_) { throw new Error('Molecule information must not be rendered as HTML'); }
}

function elements(root) {
  const result = [];
  for (const child of root.children) {
    if (!(child instanceof FakeElement)) continue;
    result.push(child, ...elements(child));
  }
  return result;
}

function withDocument(run) {
  const saved = { present: Object.hasOwn(globalThis, 'document'), value: globalThis.document };
  const created = [];
  globalThis.document = {
    createElement(tagName) { const element = new FakeElement(tagName); created.push(element); return element; },
    createTextNode(value) { return new FakeText(value); },
  };
  try { return run(new FakeElement('section'), created); }
  finally {
    if (saved.present) globalThis.document = saved.value;
    else delete globalThis.document;
  }
}

function assertExternalLink(link) {
  assert.equal(link.target, '_blank');
  assert.ok(link.rel.split(/\s+/).includes('noopener'));
  assert.ok(link.rel.split(/\s+/).includes('noreferrer'));
  assert.ok(link.textContent.trim());
  assert.equal(new URL(link.href).protocol, 'https:');
}

test('all molecule values share one visible label/value grid outside the collapsed help', () => withDocument((host) => {
  const molecule = molecules.find(({ cid }) => cid === 702);
  const information = buildMoleculeInformation(molecule);
  renderMoleculeInformation(host, molecule);
  const nodes = elements(host);
  const heading = nodes.find((node) => node.id === 'molecule-information-heading');
  assert.equal(heading.textContent, 'Molecule information');
  assert.equal(nodes.filter((node) => node.className === 'molecule-information__grid').length, 1);
  const grid = nodes.find((node) => node.className === 'molecule-information__grid');
  assert.equal(grid.tagName, 'dl');
  assert.equal(grid.children.length, information.rows.length);
  for (const [index, card] of grid.children.entries()) {
    const row = information.rows[index];
    assert.equal(card.dataset.property, row.key);
    assert.equal(card.dataset.status, row.status);
    assert.equal(card.children[0].tagName, 'dt');
    assert.equal(card.children[0].textContent, row.label);
    assert.equal(card.children[1].tagName, 'dd');
    assert.equal(card.children[1].textContent, row.value);
  }
  const help = nodes.find((node) => node.className === 'molecule-information__help');
  assert.ok(help);
  assert.equal(help.tagName, 'details');
  assert.ok(!help.open, 'definitions and sources initially collapsed');
  assert.equal(help.children[0].tagName, 'summary');
  assert.equal(help.children[0].textContent, 'Definitions and sources');
  assert.ok(!elements(help).includes(grid), 'values never disappear behind More properties');
  assert.ok(!elements(help).some((node) => node.dataset.property), 'help contains explanations, not the main values');
  const overview = nodes.find((node) => node.className === 'molecule-information__overview');
  assert.equal(overview.textContent, information.overview);
}));

test('help definitions follow displayed registered fields and references use safe exact-CID links', () => withDocument((host) => {
  const molecule = molecules.find(({ cid }) => cid === 962);
  const information = buildMoleculeInformation(molecule);
  renderMoleculeInformation(host, molecule);
  const nodes = elements(host);
  const help = nodes.find((node) => node.className === 'molecule-information__help');
  const definitions = nodes.find((node) => node.className === 'molecule-information__definitions');
  const expectedDefinitions = PROPERTY_GUIDE.filter(({ key }) => rowFor(information, key));
  assert.equal(definitions.tagName, 'dl');
  assert.equal(definitions.children.length, expectedDefinitions.length);
  expectedDefinitions.forEach((property, index) => {
    assert.equal(definitions.children[index].children[0].textContent, property.label);
    assert.ok(definitions.children[index].children[1].textContent.startsWith(property.definition));
  });
  const sources = nodes.find((node) => node.className === 'molecule-information__sources');
  assert.ok(elements(help).includes(sources), 'references are contained in compact help');
  const compoundLinks = elements(sources).filter((node) => node.tagName === 'a');
  assert.deepEqual(compoundLinks.map(({ href }) => href), sourceUrls(information));
  assert.equal(compoundLinks[0].href, 'https://pubchem.ncbi.nlm.nih.gov/compound/962');
  nodes.filter((node) => node.tagName === 'a').forEach(assertExternalLink);
  assert.match(help.textContent, /not a safety data sheet/i);
}));

test('unreviewed compounds display short placeholders rather than the old explanatory paragraphs', () => withDocument((host) => {
  renderMoleculeInformation(host, { cid: 999999999, name: 'Unreviewed compound', formula: 'C₂H₆O' });
  const nodes = elements(host);
  const cards = nodes.filter((node) => node.dataset.property);
  assert.equal(cards.length, coreKeys.length + commonKeys.length);
  assert.equal(cards.find((card) => card.dataset.property === 'formula').children[1].textContent, 'C₂H₆O');
  commonKeys.forEach((key) => {
    const card = cards.find((node) => node.dataset.property === key);
    assert.equal(card.children[1].textContent, 'Not reviewed');
    assert.equal(card.dataset.status, 'unreviewed');
  });
  assert.ok(!host.textContent.includes('General definitions below are not claims'));
  assert.ok(!host.textContent.includes('have not been reviewed yet'));
  nodes.filter((node) => node.tagName === 'a').forEach(assertExternalLink);
}));

test('switching compounds removes previous optional fields, values, and references', () => withDocument((host) => {
  const first = molecules.find(({ cid }) => cid === 702);
  renderMoleculeInformation(host, first);
  const previousChildren = [...host.children];
  const previousReferences = sourceUrls(buildMoleculeInformation(first));
  renderMoleculeInformation(host, { cid: 999999999, name: 'Unreviewed compound' });
  assert.ok(host.children.every((node) => !previousChildren.includes(node)));
  const nodes = elements(host);
  assert.equal(nodes.filter((node) => node.id === 'molecule-information-heading').length, 1);
  assert.equal(nodes.filter((node) => node.dataset.property).length, coreKeys.length + commonKeys.length);
  assert.ok(!host.textContent.includes(chemicalProfileForCid(first.cid).overview));
  const sources = nodes.find((node) => node.className === 'molecule-information__sources');
  assert.deepEqual(elements(sources).filter((node) => node.tagName === 'a').map(({ href }) => href),
    ['https://pubchem.ncbi.nlm.nih.gov/compound/999999999']);
  assert.ok(!elements(sources).some((node) => previousReferences.includes(node.href)));
  renderMoleculeInformation(host, molecules.find(({ cid }) => cid === 962));
  assert.ok(!elements(host).some((node) => node.href?.endsWith('/999999999')));
}));

test('names, formulae, descriptions, and property values cannot create HTML elements', () => withDocument((host, created) => {
  const malicious = '<img src=x onerror="alert(1)"><script>alert(1)</script>';
  renderMoleculeInformation(host, {
    cid: 999999999, name: malicious, formula: malicious, description: malicious,
    properties: { bonds: malicious },
  });
  const nodes = elements(host);
  const formula = nodes.find((node) => node.dataset.property === 'formula');
  const bonds = nodes.find((node) => node.dataset.property === 'bonds');
  assert.equal(formula.children[1].textContent, malicious);
  assert.equal(bonds.children[1].textContent, malicious);
  assert.ok(!created.some((node) => ['img', 'script', 'iframe', 'style'].includes(node.tagName)));
  assert.equal(formula.children[1].children.length, 1);
  assert.ok(formula.children[1].children[0] instanceof FakeText);
  nodes.filter((node) => node.tagName === 'a').forEach(assertExternalLink);
}));

test('unsafe reference schemes and credential-bearing URLs are never rendered as links', () => withDocument((host) => {
  const molecule = molecules.find(({ cid }) => cid === 962);
  const profile = chemicalProfileForCid(molecule.cid);
  const originalSources = [...profile.sources];
  const unsafeUrls = ['javascript:alert(1)', 'http://example.com/chemistry', 'https://user:password@example.com/chemistry', 'not a URL'];
  try {
    profile.sources.push(...unsafeUrls.map((url) => ({ label: 'Untrusted reference', url })));
    renderMoleculeInformation(host, molecule);
    const links = elements(host).filter((node) => node.tagName === 'a');
    links.forEach(assertExternalLink);
    assert.ok(!links.some((node) => unsafeUrls.includes(node.href)));
    assert.ok(!links.some((node) => node.textContent === 'Untrusted reference'));
    assert.ok(links.some((node) => node.href === 'https://pubchem.ncbi.nlm.nih.gov/compound/962'));
  } finally {
    profile.sources.splice(0, profile.sources.length, ...originalSources);
  }
}));
