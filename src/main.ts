import './styles.css';
import './bond-measurements.css';
import './solution-calculator.css';
import { explorerSamples, findMolecules, isIonicCompound, moleculeFromPubChem, normalizeQuery, type Molecule, type PubChemMatch } from './molecules';
import { renderMoleculeInformation } from './explorer-description';
import { BondMeasurements, type MeasurementAtom, type MeasurementViewer } from './bond-measurements';
import { SolutionCalculatorPanel } from './solution-calculator-panel';
import { solutionCompoundFromMolecule } from './solution-compound';
import { CALCULATOR_TRANSFER_KEY, calculatorCompoundFromMolecule, encodeCalculatorTransfer } from './calculator-compound';
import { mountViewerControls, type CameraViewer } from './viewer-controls';
import './ui-system.css';
import { mountWorkspaceShell } from './workspace-shell';
import './workspace-shell.css';

type Viewer = MeasurementViewer & CameraViewer & {
  removeAllModels: () => void;
  removeAllSurfaces: () => void;
  removeAllLabels: () => void;
  removeAllShapes: () => void;
  addModel: (data: string, format: string) => { selectedAtoms: (selection: Record<string, never>) => MeasurementAtom[] };
  setStyle: (selection: Record<string, never>, style: Record<string, unknown>) => void;
  zoomTo: () => void;
  render: () => void;
};

declare global {
  interface Window {
    $3Dmol?: {
      createViewer: (element: HTMLElement, options: Record<string, unknown>) => Viewer;
    };
  }
}

function mustElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Required element was not found: ${selector}`);
  return element;
}

const app = mustElement<HTMLDivElement>('#app');

app.innerHTML = `
  <a class="skip-link" href="#main-content">Skip to workspace</a>
  <main class="shell" id="main-content" tabindex="-1">
    <header class="hero">
      <div>
        <p class="eyebrow">Molecule Playground · Explorer</p>
        <h1>Explorer</h1>
        <p class="hero-copy">Search a compound. Explore its shape and properties.</p>
      </div>
      <div class="hero-mark" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>
      <nav class="hero-nav" aria-label="Project pages">
        <a class="builder-link" href="/">Home</a>
        <a class="builder-link is-current" href="/explore.html" aria-current="page">Explore</a>
        <a class="builder-link" href="/builder.html">Builder</a>
        <a class="builder-link" href="/reaction-lab.html">Reaction Lab</a>
        <a class="builder-link" href="/calculators.html">Calculators</a>
      </nav>
    </header>

    <section class="workspace" aria-label="Interactive molecule explorer">
      <aside class="library">
        <div class="section-heading">
          <p class="eyebrow">Molecule search</p>
          <h2>Find a molecule</h2>
        </div>
        <form id="molecule-search-form" class="molecule-search" role="search">
          <label for="molecule-search">Search by name or formula</label>
          <div class="molecule-search__controls">
            <input id="molecule-search" type="search" placeholder="Water, caffeine, H₂O…" autocomplete="off" />
            <button type="submit">Search</button>
          </div>
          <p id="search-status" role="status">${explorerSamples.length} sample molecules. Search PubChem for more.</p>
          <details class="search-help"><summary>Search tips</summary><p>Use a full name or correctly capitalized formula. Brackets distinguish structures with the same formula. Searches use PubChem. Ionic compounds show information only; some other compounds have a 2D view.</p></details>
        </form>
        <div id="molecule-list" class="molecule-list"></div>
      </aside>

      <section class="viewer-panel">
        <div class="viewer-toolbar">
          <div>
            <p id="category" class="eyebrow"></p>
            <h2 id="molecule-title"></h2>
          </div>
          <div id="formula" class="formula" aria-label="Molecular formula"></div>
        </div>

        <p id="ionic-notice" class="ionic-notice" role="status" hidden></p>
        <div class="viewer-stage">
          <div id="molecule-viewer" aria-label="Interactive 3D molecule viewer"></div>
          <div id="molecule-fallback" class="molecule-fallback" hidden>
            <img id="molecule-fallback-image" alt="" />
            <p>PubChem 2D depiction · no 3D model available here</p>
          </div>
          <div id="viewer-status" class="viewer-status" role="status">
            Preparing the 3D viewer…
          </div>
          <div id="viewer-hint" class="viewer-hint">Drag to rotate · scroll to zoom · right-drag to move</div>
        </div>
        <div id="explorer-measurements" hidden></div>

        <div class="details">
          <section id="molecule-information" class="molecule-information" aria-labelledby="molecule-information-heading"></section>
          <details id="explorer-solution-calculator"></details>
          <div class="explorer-transfer" aria-label="Use this compound in Calculators">
            <button type="button" id="open-in-calculators">Open in Calculators →</button>
            <span id="calculator-transfer-status" role="status"></span>
          </div>
          <div class="explorer-transfer" aria-label="Use this compound in Reaction Lab">
            <span>Use in Reaction Lab</span>
            <button type="button" data-reaction-slot="0">Use as molecule 1</button>
            <button type="button" data-reaction-slot="1">Use as molecule 2</button>
          </div>
        </div>
      </section>
    </section>
  </main>
`;

mountWorkspaceShell(mustElement<HTMLElement>('.shell'));

const moleculeList = mustElement<HTMLDivElement>('#molecule-list');
const searchForm = mustElement<HTMLFormElement>('#molecule-search-form');
const searchInput = mustElement<HTMLInputElement>('#molecule-search');
const searchStatus = mustElement<HTMLParagraphElement>('#search-status');
const moleculeTitle = mustElement<HTMLHeadingElement>('#molecule-title');
const category = mustElement<HTMLParagraphElement>('#category');
const formula = mustElement<HTMLDivElement>('#formula');
const moleculeInformation = mustElement<HTMLElement>('#molecule-information');
const viewerStage = mustElement<HTMLDivElement>('.viewer-stage');
const ionicNotice = mustElement<HTMLParagraphElement>('#ionic-notice');
const viewerStatus = mustElement<HTMLDivElement>('#viewer-status');
const fallbackView = mustElement<HTMLDivElement>('#molecule-fallback');
const fallbackImage = mustElement<HTMLImageElement>('#molecule-fallback-image');
const viewerHint = mustElement<HTMLDivElement>('#viewer-hint');
const transferButtons = [...document.querySelectorAll<HTMLButtonElement>('[data-reaction-slot]')];
const EXPLORER_TRANSFER_KEY = 'molecule-playground.explorer-reactant.v1';

const buttons = new Map<string, HTMLButtonElement>();
let displayedMolecules: Molecule[] = [...explorerSamples];
let searchRevision = 0;

function renderMoleculeCards(items: Molecule[], emptyMessage = 'No molecule found. Try a full name or correctly capitalized formula.') {
  displayedMolecules = items;
  moleculeList.replaceChildren();
  buttons.clear();
  const formulaCounts = new Map<string, number>();
  for (const molecule of items) {
    const key = normalizeQuery(molecule.formula);
    formulaCounts.set(key, (formulaCounts.get(key) ?? 0) + 1);
  }
  for (const molecule of items) {
    const button = document.createElement('button');
    button.className = 'molecule-card';
    button.type = 'button';
    button.dataset.moleculeId = molecule.id;
    const formulaBadge = document.createElement('span');
    formulaBadge.className = 'molecule-card__formula';
    formulaBadge.textContent = molecule.formula;
    const text = document.createElement('span');
    text.className = 'molecule-card__text';
    const name = document.createElement('strong');
    name.textContent = molecule.name;
    const detail = document.createElement('small');
    const sameFormula = (formulaCounts.get(normalizeQuery(molecule.formula)) ?? 0) > 1;
    detail.textContent = sameFormula && molecule.structureForm
      ? `[${molecule.structureForm}] · ${molecule.category}`
      : molecule.category;
    if (sameFormula && molecule.structureForm) detail.title = 'Bracketed SMILES notation shows this molecule’s atom connections.';
    text.append(name, detail);
    const arrow = document.createElement('span');
    arrow.className = 'molecule-card__arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '→';
    button.append(formulaBadge, text, arrow);
    moleculeList.append(button);
    buttons.set(molecule.id, button);
  }
  if (!items.length) {
    const empty = document.createElement('p');
    empty.className = 'molecule-list__empty';
    empty.textContent = emptyMessage;
    moleculeList.append(empty);
  }
}

renderMoleculeCards(explorerSamples);

const viewerHost = mustElement<HTMLDivElement>('#molecule-viewer');
const viewerFactory = window.$3Dmol;
const viewer = viewerFactory?.createViewer(viewerHost, {
  backgroundColor: '#f7fbff',
  antialias: true,
});
const measurements = new BondMeasurements(mustElement<HTMLElement>('#explorer-measurements'), viewer);
const cameraControls = mountViewerControls(mustElement<HTMLElement>('.viewer-stage'), viewer);
const solutionCalculator = new SolutionCalculatorPanel(mustElement<HTMLDetailsElement>('#explorer-solution-calculator'));

let activeMoleculeId = '';
let activeMolecule: Molecule | null = null;
let loadSequence = 0;
let modelReady = false;
let depictionUrl: string | null = null;

async function showMolecule(molecule: Molecule) {
  activeMolecule = molecule;
  solutionCalculator.setCompound(solutionCompoundFromMolecule(molecule));
  if (activeMoleculeId === molecule.id && modelReady) {
    for (const [id, button] of buttons) {
      button.classList.toggle('is-active', id === molecule.id);
      button.setAttribute('aria-pressed', String(id === molecule.id));
    }
    return;
  }

  activeMoleculeId = molecule.id;
  modelReady = false;
  cameraControls.setEnabled(false);
  const sequence = ++loadSequence;
  measurements.reset();

  for (const [id, button] of buttons) {
    const selected = id === molecule.id;
    button.classList.toggle('is-active', selected);
    button.setAttribute('aria-pressed', String(selected));
    button.disabled = true;
  }

  category.textContent = molecule.category;
  moleculeTitle.textContent = molecule.name;
  formula.textContent = molecule.formula;
  renderMoleculeInformation(moleculeInformation, molecule);

  const ionic = isIonicCompound(molecule);
  cameraControls.setVisible(!ionic);
  viewerStage.hidden = ionic;
  ionicNotice.hidden = !ionic;
  ionicNotice.textContent = ionic ? 'Ionic compound — no 3D diagram in this viewer. Information is shown below.' : '';

  viewerStatus.textContent = `Loading ${molecule.name}…`;
  viewerStatus.classList.remove('is-hidden', 'is-error');
  fallbackView.hidden = true;
  fallbackImage.removeAttribute('src');
  if (depictionUrl) URL.revokeObjectURL(depictionUrl);
  depictionUrl = null;
  viewerHint.textContent = 'Drag to rotate · scroll to zoom · right-drag to move';

  try {
    if (ionic) {
      // This information-only path must not depend on a working WebGL viewer.
      try {
        viewer?.removeAllModels();
        viewer?.removeAllSurfaces();
        viewer?.removeAllLabels();
        viewer?.removeAllShapes();
      } catch {
        // Hidden viewer cleanup cannot trigger a diagram request for an ionic record.
      }
      modelReady = true;
      viewerStatus.textContent = '';
      return;
    }
    viewer?.removeAllModels();
    viewer?.removeAllSurfaces();
    viewer?.removeAllLabels();
    viewer?.removeAllShapes();
    viewer?.render();
    if (!viewer) throw new Error('3Dmol.js did not load. Check the network connection.');
    const response = await fetch(molecule.structureFile);
    if (!response.ok) throw new Error('A 3D structure is not available for this compound.');
    const structure = await response.text();

    if (sequence !== loadSequence) return;

    viewer.removeAllSurfaces();
    viewer.removeAllLabels();
    viewer.removeAllShapes();
    const model = viewer.addModel(structure, 'sdf');
    viewer.setStyle({}, { stick: { colorscheme: 'Jmol', radius: 0.1 }, sphere: { scale: 0.25 } });
    viewer.zoomTo();
    measurements.setAtoms(model.selectedAtoms({}));
    viewer.render();
    modelReady = true;

    cameraControls.setEnabled(true);

    if (sequence === loadSequence) {
      viewerStatus.textContent = `${molecule.name} ready`;
      window.setTimeout(() => {
        if (sequence === loadSequence) viewerStatus.classList.add('is-hidden');
      }, 700);
    }
  } catch (error) {
    if (sequence !== loadSequence) return;
    measurements.reset();
    if (molecule.origin === 'pubchem') {
      try {
        const response = await fetch(`/api/pubchem/depiction?cid=${molecule.cid}`);
        if (!response.ok) throw new Error('Neither a 3D model nor a 2D depiction is available for this compound.');
        const blob = await response.blob();
        if (sequence !== loadSequence) return;
        depictionUrl = URL.createObjectURL(blob);
        fallbackImage.src = depictionUrl;
        fallbackImage.alt = `PubChem 2D depiction of ${molecule.name}`;
        fallbackView.hidden = false;
        viewerHint.textContent = '2D reference · rotation is unavailable';
        viewerStatus.textContent = '3D model unavailable here; showing PubChem’s 2D depiction.';
        modelReady = true;
        return;
      } catch (fallbackError) {
        if (sequence !== loadSequence) return;
        error = fallbackError;
      }
    }
    console.error(error);
    modelReady = false;
    viewerStatus.textContent = error instanceof Error ? error.message : `Could not load ${molecule.name}.`;
    viewerStatus.classList.add('is-error');
  } finally {
    if (sequence === loadSequence) {
      for (const button of buttons.values()) button.disabled = false;
    }
  }
}

transferButtons.forEach((button) => button.addEventListener('click', () => {
  const molecule = activeMolecule;
  if (!molecule?.structureForm) {
    searchStatus.textContent = 'This compound has no structure to send to Reaction Lab.';
    return;
  }
  try {
    sessionStorage.setItem(EXPLORER_TRANSFER_KEY, JSON.stringify({
      slot: Number(button.dataset.reactionSlot), id: molecule.id, name: molecule.name,
      formula: molecule.formula, smiles: molecule.structureForm,
    }));
    window.location.assign('/reaction-lab.html');
  } catch {
    searchStatus.textContent = 'Browser storage is unavailable; this compound could not be sent to Reaction Lab.';
  }
}));

function openInCalculators() {
  const status = mustElement<HTMLElement>('#calculator-transfer-status');
  if (!activeMolecule) { status.textContent = 'Select a compound first.'; return; }
  try {
    const compound = calculatorCompoundFromMolecule(activeMolecule, isIonicCompound(activeMolecule));
    sessionStorage.setItem(CALCULATOR_TRANSFER_KEY, encodeCalculatorTransfer(compound));
    window.location.assign('/calculators.html#moles');
  } catch { status.textContent = 'Browser storage is unavailable. Open Calculators and select the compound manually.'; }
}
mustElement<HTMLButtonElement>('#open-in-calculators').addEventListener('click', openInCalculators);

moleculeList.addEventListener('click', (event) => {
  const target = (event.target as HTMLElement).closest<HTMLButtonElement>(
    '[data-molecule-id]',
  );
  if (!target) return;

  const molecule = displayedMolecules.find((item) => item.id === target.dataset.moleculeId);
  if (molecule) void showMolecule(molecule);
});

searchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const query = searchInput.value.trim();
  const requestRevision = ++searchRevision;
  if (!query) {
    renderMoleculeCards(explorerSamples);
    searchStatus.textContent = `${explorerSamples.length} sample molecules. Search PubChem for more.`;
    return;
  }
  const local = findMolecules(query);
  renderMoleculeCards(local, 'Searching PubChem…');
  searchStatus.textContent = 'Searching PubChem by name or formula…';
  try {
    const response = await fetch(`/api/pubchem/search?q=${encodeURIComponent(query)}`);
    const payload = await response.json() as { results: PubChemMatch[]; limited: boolean } | { error: string };
    if (requestRevision !== searchRevision) return;
    if (!response.ok || 'error' in payload) throw new Error('error' in payload ? payload.error : 'PubChem search failed.');
    const remote = payload.results.map(moleculeFromPubChem);
    const byCid = new Map(remote.map((item) => [item.cid, item]));
    const combined = [...local.map((item) => byCid.get(item.cid) ?? item), ...remote.filter((item) => !local.some((localItem) => localItem.cid === item.cid))];
    renderMoleculeCards(combined);
    searchStatus.textContent = combined.length
      ? `${combined.length} structure${combined.length === 1 ? '' : 's'} found${payload.limited ? ' (first results shown)' : ''}. Select a form to explore.`
      : 'No PubChem record found. Try a full name or correctly capitalized formula.';
    const exact = combined.filter((molecule) => [molecule.name, molecule.formula, molecule.id].some((value) => normalizeQuery(value) === normalizeQuery(query)));
    if (combined.length === 1 && exact.length === 1) void showMolecule(exact[0]);
  } catch (error) {
    if (requestRevision !== searchRevision) return;
    renderMoleculeCards(local);
    searchStatus.textContent = local.length
      ? 'PubChem is unavailable; showing saved matching compounds.'
      : error instanceof Error ? error.message : 'PubChem is unavailable. Try again later.';
  }
});

searchInput.addEventListener('input', () => {
  searchRevision += 1;
  if (!searchInput.value.trim()) {
    renderMoleculeCards(explorerSamples);
    searchStatus.textContent = `${explorerSamples.length} sample molecules. Search PubChem for more.`;
  }
});

await showMolecule(explorerSamples[0]);
