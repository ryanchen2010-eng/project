import type { Molecule } from './molecules';

export type StructureProvenance = {
  kind: 'calculated' | 'idealized' | 'experimental' | 'unknown';
  source: string; physicalForm: string; method: string; convergence: string; limitations: string; sourceUrl?: string;
};

type ReferenceRecord = { cid: number; structureForm: string; path: string; provenance: StructureProvenance };
// Each entry is separately reviewed against its exact PubChem identity and source.
// Formula-only, neutralized, isomeric, hydrate and crystal matches are not accepted.
const reviewedReferences: readonly ReferenceRecord[] = [{
  cid: 17358, structureForm: 'FS(F)(F)(F)(F)F', path: '/molecules/sulfur-hexafluoride-nist-reference.sdf',
  provenance: {
    kind: 'experimental', source: 'NIST CCCBDB SF₆ experimental geometry', physicalForm: 'isolated gas-phase molecule',
    method: 'NIST tabulated Cartesian coordinates from experimental internal geometry', convergence: 'not applicable',
    limitations: 'Coordinates are derived from experimental internal coordinates and symmetry; not direct crystal-refinement coordinates. Not a model of the condensed phase.',
    sourceUrl: 'https://cccbdb.nist.gov/expgeom2.asp?casno=2551624&charge=0',
  },
}, {
  cid: 24012, structureForm: '[Cl][Al]([Cl])[Cl]', path: '/molecules/aluminum-trichloride-nist-reference.sdf',
  provenance: {
    kind: 'experimental', source: 'NIST CCCBDB AlCl₃ experimental geometry', physicalForm: 'isolated gas-phase monomer',
    method: 'NIST tabulated Cartesian coordinates from experimental internal geometry', convergence: 'not applicable',
    limitations: 'Geometry derived from experimental internal coordinates and symmetry; this monomer is not a crystal structure or the Al₂Cl₆ dimer.',
    sourceUrl: 'https://cccbdb.nist.gov/expgeom2x.asp?casno=7446700',
  },
}];

const reviewedCarbonyls = [
  { cid: 26040, structureForm: '[C]=O.[C]=O.[C]=O.[C]=O.[C]=O.[Fe]', name: 'iron pentacarbonyl', cas: '13463-40-6' },
  { cid: 26039, structureForm: '[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[Ni]', name: 'nickel tetracarbonyl', cas: '13463-39-3' },
  { cid: 25589, structureForm: '[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[C-]#[O+].[Cr]', name: 'chromium hexacarbonyl', cas: '13007-92-6' },
] as const;

export async function resolveExplorerStructure(molecule: Molecule, fetcher: typeof fetch = fetch): Promise<{ structure: string; provenance: StructureProvenance }> {
  let response = await fetcher(molecule.structureFile);
  const carbonyl = reviewedCarbonyls.find(record => record.cid === molecule.cid && record.structureForm === molecule.structureForm);
  if (response.status === 404 && molecule.origin === 'pubchem' && carbonyl
      && !molecule.ionicAssembly && molecule.category !== 'Ionic compound') {
    response = await fetcher(`/api/reference/coordination?cid=${carbonyl.cid}`);
    if (response.ok) return { structure: await response.text(), provenance: {
      kind: 'calculated', source: `NIST Chemistry WebBook ${carbonyl.name}`, physicalForm: 'isolated gas-phase molecule',
      method: 'NIST B3LYP/6-31G* calculated geometry', convergence: 'reported local minimum',
      limitations: 'The selected PubChem record represents separate metal and CO fragments; this reviewed NIST reference uses metal–C coordination bonds. The shared identity is source-verified, not an exact graph match. Calculated geometry is not experimental coordinates or a condensed-phase structure.',
      sourceUrl: `https://webbook.nist.gov/cgi/cbook.cgi?ID=${carbonyl.cas}`,
    } };
  }
  if (response.status === 404 && molecule.origin === 'pubchem' && !molecule.ionicAssembly && molecule.category !== 'Ionic compound') {
    const reference = reviewedReferences.find(entry => entry.cid === molecule.cid && entry.structureForm === molecule.structureForm);
    if (reference) {
      response = await fetcher(reference.path);
      if (response.ok) return { structure: await response.text(), provenance: reference.provenance };
    }
  }
  if (response.status === 404 && molecule.origin === 'pubchem' && molecule.cid === 24817) {
    response = await fetcher('/molecules/zirconium-tetrachloride-gas-reference.sdf');
    if (response.ok) return { structure: await response.text(), provenance: {
      kind: 'idealized', source: 'Kimura et al. gas electron diffraction', physicalForm: 'isolated gas-phase molecule',
      method: 'tetrahedron reconstructed from 2.32 Å Zr–Cl distance', convergence: 'not applicable',
      limitations: 'Not deposited experimental coordinates. Solid ZrCl₄ forms extended chains, not this isolated molecule.', sourceUrl: 'https://doi.org/10.1246/bcsj.29.95',
    } };
  }
  // Unknown records are eligible only for an exact graph match, never a
  // formula, name or coordination-fragment guess. The backend also checks the
  // live CID and rejects charged/disconnected structures and invalid geometry.
  const ordinary = new Set(['H', 'B', 'C', 'N', 'O', 'F', 'Si', 'P', 'S', 'Cl', 'Ge', 'As', 'Se', 'Br', 'Sb', 'Te', 'I']);
  const symbols = [...(molecule.structureForm ?? '').matchAll(/\[(?:\d+)?([A-Z][a-z]?)/g)].map(match => match[1]);
  if (response.status === 404 && molecule.origin === 'pubchem' && molecule.cid && !molecule.ionicAssembly
      && molecule.category !== 'Ionic compound' && symbols.some(symbol => !ordinary.has(symbol))) {
    const exact = await fetcher(`/api/reference/molecular?cid=${molecule.cid}`);
    if (exact.ok) {
      const record = await exact.json() as { structure?: unknown; selectedStructure?: unknown; method?: unknown; sourceUrl?: unknown };
      if (typeof record.structure === 'string' && record.selectedStructure === molecule.structureForm
          && typeof record.method === 'string' && typeof record.sourceUrl === 'string'
          && /^https:\/\/webbook\.nist\.gov\/cgi\/cbook\.cgi\?ID=C\d{4,14}$/.test(record.sourceUrl)) {
        return { structure: record.structure, provenance: {
          kind: 'calculated', source: 'NIST Chemistry WebBook exact molecular match', physicalForm: 'isolated molecular model; environment not specified',
          method: record.method, convergence: 'not reported', sourceUrl: record.sourceUrl,
          limitations: 'Exact molecular graph match. Calculated coordinates are not experimental; method and convergence may be unreported. The model does not represent a crystal or guarantee the lowest-energy structure.',
        } };
      }
    }
  }
  if (!response.ok) throw new Error('A 3D structure is not available for this compound.');
  const structure = await response.text();
  const header = (name: string) => response.headers?.get(`X-Structure-${name}`) ?? '';
  const source = header('Source');
  if (source === 'pubchem' || source === 'rdkit') return { structure, provenance: {
    kind: 'calculated', source: source === 'pubchem' ? 'PubChem3D' : 'RDKit', physicalForm: 'molecular conformer; environment not specified',
    method: header('Method') || 'not reported', convergence: header('Convergence') || 'unknown',
    limitations: source === 'pubchem' ? 'A calculated conformer, not experimental coordinates or necessarily the lowest-energy shape.' : 'A calculated candidate, not an experimental measurement or guaranteed lowest-energy shape.',
  } };
  if (molecule.structureFile === '/molecules/water-reference.sdf') return { structure, provenance: {
    kind: 'idealized', source: 'Bundled water reference', physicalForm: 'isolated molecule', method: 'reference-based model', convergence: 'not applicable', limitations: 'A reference-based model, not deposited experimental coordinates.',
  } };
  const bundled = /^\/molecules\/(methane|carbon-dioxide|ethanol|glucose|caffeine)\.sdf$/.test(molecule.structureFile);
  return { structure, provenance: bundled ? {
    kind: 'calculated', source: 'Bundled PubChem conformer', physicalForm: 'molecular conformer; environment not specified', method: 'PubChem3D', convergence: 'unknown', limitations: 'Calculated coordinates; not an experimental measurement or necessarily the lowest-energy shape.',
  } : {
    kind: 'unknown', source: 'Unreported', physicalForm: 'not established', method: 'not reported', convergence: 'unknown', limitations: 'The source did not provide enough provenance to classify this model.',
  } };
}
