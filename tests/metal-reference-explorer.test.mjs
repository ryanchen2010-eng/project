import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import test from 'node:test';
import ts from 'typescript';

const resolverText = await readFile(new URL('../src/explorer-structure-resolver.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(resolverText, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } });
const { resolveExplorerStructure } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);

test('fallback is exact-CID and not used for connectivity or service errors', async () => {
  const source = await readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
  const resolver = await readFile(new URL('../src/explorer-structure-resolver.ts', import.meta.url), 'utf8');
  assert.match(resolver, /response\.status === 404 && molecule\.origin === 'pubchem' && molecule\.cid === 24817/);
  assert.match(resolver, /kind: 'idealized'/);
  assert.match(resolver, /Solid ZrCl₄ forms extended chains/);
  assert.match(source, /molecule\.cid === 24872/);
  assert.match(source, /No verified discrete molecular 3D model/);
  assert.match(source, /measurements\.setAtoms\(model\.selectedAtoms/);
});

test('resolver preserves source and non-convergence without claiming experimental geometry', async () => {
  const molecule = { origin: 'pubchem', cid: 702, structureFile: '/api/pubchem/structure?cid=702' };
  const fake = values => async () => ({ ok: true, status: 200, text: async () => 'SDF', headers: { get: name => values[name] ?? null } });
  const pubchem = await resolveExplorerStructure(molecule, fake({ 'X-Structure-Source': 'pubchem', 'X-Structure-Method': 'PubChem3D', 'X-Structure-Convergence': 'unknown' }));
  assert.equal(pubchem.provenance.kind, 'calculated');
  assert.equal(pubchem.provenance.source, 'PubChem3D');
  const rdkit = await resolveExplorerStructure(molecule, fake({ 'X-Structure-Source': 'rdkit', 'X-Structure-Method': 'UFF', 'X-Structure-Convergence': 'not-converged' }));
  assert.equal(rdkit.provenance.convergence, 'not-converged');
  assert.equal(rdkit.provenance.method, 'UFF');
  const unknown = await resolveExplorerStructure(molecule, fake({}));
  assert.equal(unknown.provenance.kind, 'unknown');
});

test('reviewed NIST SF6 record requires exact CID, identity, neutral molecule and a 404', async () => {
  const base = { origin: 'pubchem', cid: 17358, structureForm: 'FS(F)(F)(F)(F)F', structureFile: '/api/pubchem/structure?cid=17358' };
  const calls = [];
  const fetcher = async url => { calls.push(url); return url.startsWith('/api/') ? { ok: false, status: 404 } : { ok: true, text: async () => 'NIST-SDF' }; };
  const found = await resolveExplorerStructure(base, fetcher);
  assert.equal(found.structure, 'NIST-SDF');
  assert.equal(found.provenance.kind, 'experimental');
  assert.match(found.provenance.method, /derived|experimental internal/i);
  assert.match(found.provenance.limitations, /not direct crystal/i);
  for (const change of [{cid: 1}, {structureForm: '[S+](F)(F)(F)(F)F'}, {ionicAssembly: true}, {category: 'Ionic compound'}]) {
    calls.length = 0;
    await assert.rejects(resolveExplorerStructure({ ...base, ...change }, fetcher));
    assert.equal(calls.length, 1);
  }
  calls.length = 0;
  await assert.rejects(resolveExplorerStructure(base, async url => { calls.push(url); return { ok: false, status: 503 }; }));
  assert.equal(calls.length, 1);
});

test('NIST aluminum monomer requires exact identity and labels physical form', async () => {
  const base = { origin: 'pubchem', cid: 24012, structureForm: '[Cl][Al]([Cl])[Cl]', structureFile: '/api/pubchem/structure?cid=24012' };
  const fetcher = async url => url.startsWith('/api/') ? { ok: false, status: 404 } : { ok: true, text: async () => 'NIST AlCl3 SDF' };
  const found = await resolveExplorerStructure(base, fetcher);
  assert.equal(found.provenance.kind, 'experimental');
  assert.match(found.provenance.physicalForm, /gas-phase monomer/);
  assert.match(found.provenance.limitations, /not a crystal structure or the Al₂Cl₆ dimer/);
  for (const change of [{ cid: 6451240 }, { structureForm: '[Al+3].[Cl-].[Cl-].[Cl-]' }, { ionicAssembly: true }, { structureForm: '[37Cl][Al]([Cl])[Cl]' }]) {
    await assert.rejects(resolveExplorerStructure({ ...base, ...change }, fetcher));
  }
});

test('iron carbonyl source bridge requires exact reviewed CID and fragment graph', async () => {
  const base = { origin: 'pubchem', cid: 26040, structureForm: '[C]=O.[C]=O.[C]=O.[C]=O.[C]=O.[Fe]', structureFile: '/api/pubchem/structure?cid=26040' };
  const calls = [];
  const fetcher = async url => { calls.push(url); return url.includes('/reference/coordination') ? { ok: true, text: async () => 'NIST-CALCULATED-SDF' } : { ok: false, status: 404 }; };
  const result = await resolveExplorerStructure(base, fetcher);
  assert.equal(result.structure, 'NIST-CALCULATED-SDF');
  assert.equal(result.provenance.kind, 'calculated');
  assert.match(result.provenance.method, /B3LYP\/6-31G\*/);
  assert.match(result.provenance.limitations, /not an exact graph match/);
  for (const change of [{ cid: 518773 }, { structureForm: '[Fe].[C]=O' }, { ionicAssembly: true }, { category: 'Ionic compound' }]) {
    calls.length = 0;
    await assert.rejects(resolveExplorerStructure({ ...base, ...change }, fetcher));
    assert.equal(calls.some(url => url.includes('/reference/coordination')), false);
  }
});

test('nickel and chromium carbonyls use only their exact reviewed identity', async () => {
  for (const [cid, metal, count, name] of [[26039, 'Ni', 4, 'nickel tetracarbonyl'], [25589, 'Cr', 6, 'chromium hexacarbonyl']]) {
    const structureForm = `${Array(count).fill('[C-]#[O+]').join('.')}.[${metal}]`;
    const molecule = { origin: 'pubchem', cid, structureForm, structureFile: `/api/pubchem/structure?cid=${cid}` };
    const calls = [];
    const fetcher = async url => { calls.push(url); return url.includes('/reference/coordination') ? { ok: true, text: async () => 'NIST model' } : { ok: false, status: 404 }; };
    const result = await resolveExplorerStructure(molecule, fetcher);
    assert.equal(result.provenance.kind, 'calculated');
    assert.match(result.provenance.source, new RegExp(name));
    assert.equal(calls[1], `/api/reference/coordination?cid=${cid}`);
    await assert.rejects(resolveExplorerStructure({ ...molecule, structureForm: `${structureForm}.O` }, fetcher));
  }
});

test('general NIST metal lookup displays only a full selected-graph match', async () => {
  const molecule = { origin: 'pubchem', cid: 16682925, structureForm: '[CH3][Al]([CH3])[CH3]', structureFile: '/api/pubchem/structure?cid=16682925' };
  const response = { structure: 'NIST model', selectedStructure: molecule.structureForm, method: 'B3LYP/6-31G*', sourceUrl: 'https://webbook.nist.gov/cgi/cbook.cgi?ID=C75241' };
  const calls = [];
  const fetcher = async url => { calls.push(url); return url.includes('/reference/molecular') ? { ok: true, json: async () => response } : { ok: false, status: 404 }; };
  const result = await resolveExplorerStructure(molecule, fetcher);
  assert.equal(result.provenance.kind, 'calculated');
  assert.equal(result.provenance.method, 'B3LYP/6-31G*');
  assert.equal(result.provenance.convergence, 'not reported');
  assert.match(result.provenance.physicalForm, /environment not specified/);
  assert.match(result.provenance.limitations, /not experimental/);
  assert.equal(calls[1], '/api/reference/molecular?cid=16682925');
  await assert.rejects(resolveExplorerStructure({ ...molecule, structureForm: '[CH3][Al]([CH3])Cl' }, fetcher));
  await assert.rejects(resolveExplorerStructure({ ...molecule, ionicAssembly: true }, fetcher));
  await assert.rejects(resolveExplorerStructure(molecule, async url => url.includes('/reference/molecular')
    ? { ok: true, json: async () => ({ ...response, sourceUrl: 'https://evil.invalid/' }) } : { ok: false, status: 404 }));
});
