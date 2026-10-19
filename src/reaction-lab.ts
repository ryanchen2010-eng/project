import './reaction-lab.css';
import './bond-measurements.css';
import { findReactantBySmiles, findReactantCandidates, mergePubChemCandidates, type PubChemReactantMatch, type Reactant } from './reactant-entry';
import { AtomInspector, safeDiagramSvg, type AtomLink, type AtomViewer, type DiagramAtom, type ModelAtom } from './atom-inspector';
import { ReactionCalculatorPanel } from './reaction-calculator-panel';
import type { ReactionStoichiometry } from './reaction-calculator';
import { BondMeasurements, type MeasurementViewer } from './bond-measurements';
import { molecules } from './molecules';
import { CALCULATOR_TRANSFER_KEY, calculatorCompoundFromReactant, encodeCalculatorTransfer } from './calculator-compound';
import { MechanismPanel, renderReasoning, renderComparison, type PathwayReasoning, type PathwayComparison, type ReactionMechanism } from './pathway-insights';
import { FunctionalGroupPanel } from './functional-group-panel';
import { conditionLabel, unsupportedInputMessage, reactionOptionSummary, conditionGuidance, type ConditionAssessment } from './reaction-conditions';
import { ReactionInformationPanel, type ReactionInformation } from './reaction-information-panel';
import { GuidedConditionsPanel, guidedControlValues, type GuidedConditions } from './guided-reaction-conditions';

type Byproduct = { name: string; formula: string };
type Reaction = {
  id: string;
  name: string;
  family: string;
  classifications?: string[];
  information?: ReactionInformation;
  mechanism: string;
  reactants: string[];
  equationReactants: string[];
  productName: string;
  productFormula: string;
  productEquationFormula: string;
  byproducts: Byproduct[];
  conditions: string;
  explanation: string;
  sourceUrl: string;
  productSmiles?: string;
  site?: { siteId: string; atomMaps: number[]; label: string; type: string };
  stoichiometry?: ReactionStoichiometry;
  assessment?: ConditionAssessment;
  reasoning?: PathwayReasoning;
  secondaryOxidationModel?: { profileId: string };
  guidedConditions?: GuidedConditions;
};
type Catalog = { reactants: Reactant[]; reactions: Reaction[] };
type Product = { molfile?: string; representation?: '3d' | '2d-only'; reason?: string; formula: string; smiles: string; molarMass: number; atoms: number; bonds: number; forceField: string; converged: boolean; atomLinks?: AtomLink[] };
type RunResult = { productName: string; product: Product; balanced: boolean; assessment: NonNullable<Reaction['assessment']>; interpretationNotes?: string[] };
type ReactionDiagram = {
  svg: string;
  summary: string;
  highlightsAvailable: boolean;
  legend: { kind: string; label: string; color: string }[];
  note: string | null;
  atoms?: DiagramAtom[];
  mechanism?: ReactionMechanism | null;
};
type Conditions = { solvent: string; temperature: string; catalyst: string; oxidationStage?: string; additionStage?: string; polymerUnits?: string; workup?: string; secondaryOxidationProfile?: string };
type ReactionFamily = 'Addition' | 'Elimination' | 'Substitution' | 'Oxidation' | 'Reduction' | 'Condensation' | 'Hydrolysis' | 'Polymerization';
type Example = {
  id: string;
  title: string;
  reactants: [string, string];
  families: ReactionFamily[];
  change: string;
  conditions: Conditions;
};
type Viewer = AtomViewer & MeasurementViewer & {
  removeAllModels: () => void;
  addModel: (data: string, format: string, options?: { keepH: boolean }) => { selectedAtoms: (selection: Record<string, never>) => ModelAtom[] };
  setStyle: (selection: Record<string, never>, style: Record<string, unknown>) => void;
  zoomTo: () => void;
  resize: () => void;
  render: () => void;
};

const app = document.querySelector<HTMLDivElement>('#reaction-app');
if (!app) throw new Error('Reaction Lab root was not found.');
app.innerHTML = `
  <main class="lab-shell">
    <header class="lab-header">
      <div>
        <p class="eyebrow">Molecule Playground · Reaction Lab</p>
        <h1>Reaction Lab</h1>
        <p class="lab-copy">Choose two reactants. Explore a pathway and its product.</p>
      </div>
      <nav class="lab-nav" aria-label="Project pages">
        <a href="/">Home</a>
        <a href="/explore.html">Explore molecules</a>
        <a href="/builder.html">Build a molecule</a>
        <a class="is-current" href="/reaction-lab.html" aria-current="page">Reaction Lab</a>
        <a href="/calculators.html">Calculators</a>
      </nav>
    </header>
    <div class="lab-notice">Teaching tool · A matching pathway is not a prediction or lab instruction.</div>
    <details class="reaction-guide">
      <summary><span>Reaction guide</span><small>Brief explanations of every supported type</small></summary>
      <div class="guide-grid">
        <section><h2>Addition</h2><p>Atoms add across a selected double bond.</p><ul><li><strong>Hydrogenation:</strong> H₂ adds across C=C.</li><li><strong>Bromination:</strong> Br₂ adds across C=C; <strong>Chlorination:</strong> uses Cl₂.</li><li><strong>Hydrohalogenation:</strong> HCl, HBr or HI adds in a supported orientation.</li><li><strong>Hydration:</strong> H and OH add across C=C.</li><li><strong>Epoxidation:</strong> A peroxyacid supplies O to form an epoxide; also oxidation. Validated geometry is retained; unknown geometry stays unassigned.</li></ul></section>
        <section><h2>Elimination</h2><p>A small group leaves and a C=C bond forms.</p><ul><li><strong>E1:</strong> The leaving group goes first; a hydrogen is removed next.</li><li><strong>E2:</strong> Concerted loss; anti geometry can be measured in a reactant conformer.</li><li><strong>Alcohol dehydration:</strong> OH and beta H form water; acid/heat net model.</li></ul></section>
        <section><h2>Substitution</h2><p>One group replaces another.</p><ul><li><strong>SN1:</strong> The leaving group goes first; the new group attaches next.</li><li><strong>SN2:</strong> Concerted replacement; a specified tetrahedral center inverts.</li><li><strong>Alcohol substitution:</strong> HX activates OH, forming haloalkane and water.</li></ul></section>
        <section><h2>Oxidation</h2><p><strong>Alcohol oxidation:</strong> A primary alcohol gives an aldehyde stage; a secondary alcohol gives a ketone. <strong>Aldehyde oxidation:</strong> Select Further oxidation and water medium for the acid reporting structure. Isolation and solution protonation are not predicted.</p></section>
        <section><h2>Reduction</h2><p><strong>Carbonyl hydrogenation:</strong> C=O → alcohol. <strong>Alkyne hydrogenation:</strong> Two H₂ equivalents fully reduce C≡C; H₂/Lindlar gives a terminal alkene or validated internal cis/Z alkene. These are net models, not guaranteed experimental endpoints.</p></section>
        <section><h2>Condensation</h2><p><strong>Esterification:</strong> An acid and an alcohol form an ester plus water.</p></section>
        <section><h2>Hydrolysis</h2><p><strong>Ester hydrolysis:</strong> Acid-catalyzed water addition gives acid and alcohol/phenol. <strong>Saponification:</strong> Hydroxide gives carboxylate and alcohol/phenol; no acid work-up. Supported lactones open into one connected hydroxy acid or hydroxy carboxylate.</p></section>
        <section><h2>More additions</h2><p><strong>Alkyne X₂/HX:</strong> Choose one or two equivalents. <strong>Dihydroxylation:</strong> Os/H₂O₂ net model adds syn OH groups; confirm aqueous diol release. Unknown internal geometry stays unassigned.</p></section>
        <section><h2>Polymerization</h2><p>Finite 2/4/6-unit model with benzoyl peroxide, phenyl end groups and CO₂. No bulk-polymer size, tacticity or yield prediction.</p></section>
      </div>
    </details>
    <section class="lab-workspace" aria-label="Interactive reaction lab">
      <section class="lab-input-panel">
        <div class="panel-heading"><p class="eyebrow">01 · Reactants</p><h2>Choose two molecules</h2></div>
        <form id="reactant-form" autocomplete="off">
          <div class="reactant-fields">
            <div><label for="reactant-a">Molecule 1</label><div class="reactant-lookup"><input id="reactant-a" list="reactant-options" placeholder="Name or formula" required /><button id="reactant-a-search" type="button">Search PubChem</button></div><p id="reactant-a-lookup-status" class="reactant-lookup-status" role="status"></p><div id="reactant-a-choices" class="reactant-choices"></div><button id="reactant-a-calculators" class="calculator-shortcut" type="button" hidden>Use in Calculators ↗</button></div>
            <span class="reactant-plus" aria-hidden="true">+</span>
            <div><label for="reactant-b">Molecule 2 · reagent or solvent</label><div class="reactant-lookup"><input id="reactant-b" list="reactant-options" placeholder="Name or formula" required /><button id="reactant-b-search" type="button">Search PubChem</button></div><p id="reactant-b-lookup-status" class="reactant-lookup-status" role="status"></p><div id="reactant-b-choices" class="reactant-choices"></div><button id="reactant-b-calculators" class="calculator-shortcut" type="button" hidden>Use in Calculators ↗</button></div>
          </div>
          <datalist id="reactant-options"></datalist>
          <details class="field-help"><summary>Input tips</summary><p>Use a full name or correctly capitalized formula (CH3Br, not Ch3br). Choose a bracketed structure if several match. PubChem lookup needs internet. You can also draw in <a href="/builder.html">Builder</a>.</p></details>
          <p id="reactant-interpretation" class="reactant-interpretation" hidden></p>
          <div class="condition-fields" aria-label="Reaction conditions">
            <div><label for="reaction-solvent">Solvent / medium</label><select id="reaction-solvent"><option value="">Not specified</option><option value="polar-aprotic">Polar aprotic</option><option value="aqueous-protic">Water · polar protic</option><option value="ethanolic-protic">Ethanol · protic</option><option value="dry">Dry / no water</option><option value="secondary-naocl-acetic">Aqueous acetic acid · secondary NaOCl</option></select></div>
            <div><label for="reaction-temperature">Temperature</label><select id="reaction-temperature"><option value="">Not specified</option><option value="ambient">Room temperature</option><option value="heated">Heated</option></select></div>
            <div><label for="reaction-catalyst">Catalyst / activation</label><select id="reaction-catalyst"><option value="">Not specified</option><option value="none">None added</option><option value="acid">Acid</option><option value="metal">Metal (Pd/Pt)</option><option value="lindlar">Lindlar</option><option value="osmium">Os-based dihydroxylation</option><option value="radical">Radical initiation model</option></select></div>
            <div><label for="reaction-oxidation-stage">Oxidation stage</label><select id="reaction-oxidation-stage"><option value="">Not specified</option><option value="first">First stage · alcohol → carbonyl</option><option value="further">Further oxidation · aldehyde → acid</option></select></div>
          </div>
          <section id="guided-conditions" class="guided-conditions" aria-labelledby="guided-conditions-heading" hidden></section>
        </form>
        <details id="reactant-groups" class="functional-group-panel"></details>
        <section class="example-library" aria-labelledby="example-library-heading">
          <div class="library-heading"><div><p class="eyebrow">Guided examples</p><h3 id="example-library-heading">Try an example</h3></div><span id="example-count"></span></div>
          <div id="family-filters" class="family-filters" role="group" aria-label="Filter example reactions"></div>
          <div id="example-cards" class="example-cards"><p class="library-loading">Loading examples…</p></div>
        </section>
        <div class="panel-heading reaction-heading"><p class="eyebrow">02 · Matching options</p><h2>Choose a reaction</h2></div>
        <details id="reaction-pathway-settings" class="reaction-guide pathway-settings" hidden open>
          <summary id="reaction-settings-title">Pathway settings</summary>
          <div class="condition-fields">
            <div id="alkyne-addition-settings" hidden><label for="reaction-addition-stage">Alkyne X₂ / HX equivalents</label><select id="reaction-addition-stage"><option value="one">One equivalent</option><option value="two">Two equivalents</option></select></div>
            <div id="polymer-chain-settings" hidden><label for="reaction-polymer-units">Finite chain monomers</label><select id="reaction-polymer-units"><option value="2">2</option><option value="4" selected>4</option><option value="6">6</option></select></div>
            <div id="diol-workup-settings" hidden><label for="reaction-diol-workup">Diol release / work-up</label><select id="reaction-diol-workup"><option value="">Not confirmed</option><option value="aqueous-release">Assume aqueous release · net model</option></select><p class="field-help">Catalyst cycling and work-up species are not mapped.</p></div>
          </div>
        </details>
        <div id="reaction-options" class="reaction-options" aria-live="polite"><p class="empty-options">Choose both molecules to see supported pathways.</p></div>
        <div id="pathway-comparison" hidden></div>
        <div class="lab-actions">
          <button id="run-reaction" type="button" disabled>View 3D product</button>
          <p id="lab-status" role="status">Loading the reaction collection…</p>
        </div>
      </section>
      <aside class="lab-result-panel">
        <div class="panel-heading"><p class="eyebrow">03 · Result</p><h2>See what changes</h2></div>
        <p class="equation-label">Proposed net equation</p>
        <p id="reaction-equation" class="reaction-equation">Choose a pathway to preview its equation.</p>
        <p id="condition-assessment" class="condition-assessment" hidden></p>
        <p id="formula-note" class="formula-note" hidden></p>
        <details id="reaction-calculator" hidden></details>
        <div class="preview-toolbar">
          <p id="preview-label">Reactants → products</p>
          <div class="preview-switch" role="group" aria-label="Reaction preview view">
            <button id="view-2d" type="button" aria-pressed="true" aria-controls="reaction-diagram" disabled>2D reaction</button>
            <button id="view-3d" type="button" aria-pressed="false" aria-controls="reaction-viewer" disabled>3D product</button>
            <button id="view-compare" type="button" aria-pressed="false" aria-controls="reaction-diagram reaction-viewer" disabled>Compare</button>
          </div>
        </div>
        <div id="reaction-previews" class="reaction-previews">
        <div id="reaction-diagram" class="reaction-diagram" aria-busy="false">
          <p id="diagram-placeholder" role="status">Choose a pathway to see its structures and bond changes.</p>
          <div id="diagram-drawing" class="diagram-scroll" hidden></div>
          <p class="diagram-scroll-hint">Swipe sideways to see all structures ↔</p>
        </div>
        <div id="reaction-viewer" class="reaction-viewer" aria-label="Interactive 3D main-product preview"><p id="result-placeholder">Choose a pathway to generate its main product.</p></div>
        </div>
        <p id="viewer-hint" class="viewer-hint" hidden>Drag to rotate · scroll to zoom</p>
        <div id="product-measurements" hidden></div>
        <div id="atom-inspection" class="atom-inspection" hidden><p id="atom-status" role="status">Hover an atom to find it in both views. Click or tap to keep it selected.</p><button id="clear-atom" type="button" disabled>Clear atom</button></div>
        <p id="bond-summary" class="bond-summary" hidden></p>
        <ul id="bond-legend" class="bond-legend" aria-label="Bond highlight key" hidden></ul>
        <p id="diagram-note" class="diagram-note" hidden></p>
        <details id="reaction-mechanism" class="reaction-mechanism" hidden></details>
        <details id="result-details" class="result-details" hidden><summary>Product details</summary>
          <div class="result-facts">
            <div><span>Main product</span><strong id="product-name"></strong></div>
            <div><span>Molecular formula</span><strong id="product-formula"></strong></div>
            <div><span>Exact product structure · SMILES</span><strong id="product-smiles"></strong></div>
            <div><span>Atom + charge balance</span><strong id="atom-balance"></strong></div>
            <div><span>3D method</span><strong id="product-method"></strong></div>
          </div>
        </details>
        <details id="result-learning" class="result-learning" hidden></details>
        <details class="lab-limits"><summary>What this lab cannot predict</summary><p>These limited rules cannot determine rates, actual yields, product mixtures, rearrangements, or general stereochemical outcomes. Stereo inspection and inversion of a specified SN2 center are supported; E2 geometry checks describe one conformer, not a predicted product ratio. The calculator gives theoretical amounts from the selected balanced equation only. 3D shows one calculated main-product shape; byproducts appear in the equation. Many charged or multi-part drawings remain 2D-only or outside this Lab's rules.</p></details>
      </aside>
    </section>
  </main>
`;

function required<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing Reaction Lab element: ${selector}`);
  return element;
}

const inputA = required<HTMLInputElement>('#reactant-a');
const inputB = required<HTMLInputElement>('#reactant-b');
const solventInput = required<HTMLSelectElement>('#reaction-solvent');
const temperatureInput = required<HTMLSelectElement>('#reaction-temperature');
const catalystInput = required<HTMLSelectElement>('#reaction-catalyst');
const oxidationStageInput = required<HTMLSelectElement>('#reaction-oxidation-stage');
const extensionConditions = required<HTMLDetailsElement>('#reaction-pathway-settings');
const extensionTitle = required<HTMLElement>('#reaction-settings-title');
const additionSettings = required<HTMLElement>('#alkyne-addition-settings');
const chainSettings = required<HTMLElement>('#polymer-chain-settings');
const additionStageInput = required<HTMLSelectElement>('#reaction-addition-stage');
const polymerUnitsInput = required<HTMLSelectElement>('#reaction-polymer-units');
const diolSettings = required<HTMLElement>('#diol-workup-settings');
const workupInput = required<HTMLSelectElement>('#reaction-diol-workup');
const inputs = [inputA, inputB] as const;
const searchButtons = [required<HTMLButtonElement>('#reactant-a-search'), required<HTMLButtonElement>('#reactant-b-search')] as const;
const lookupStatuses = [required<HTMLParagraphElement>('#reactant-a-lookup-status'), required<HTMLParagraphElement>('#reactant-b-lookup-status')] as const;
const calculatorButtons = [required<HTMLButtonElement>('#reactant-a-calculators'), required<HTMLButtonElement>('#reactant-b-calculators')] as const;
const choiceHosts = [required<HTMLDivElement>('#reactant-a-choices'), required<HTMLDivElement>('#reactant-b-choices')] as const;
const datalist = required<HTMLDataListElement>('#reactant-options');
const optionsHost = required<HTMLDivElement>('#reaction-options');
const comparisonHost = required<HTMLDivElement>('#pathway-comparison');
const runButton = required<HTMLButtonElement>('#run-reaction');
const status = required<HTMLParagraphElement>('#lab-status');
const interpretation = required<HTMLParagraphElement>('#reactant-interpretation');
const viewerHost = required<HTMLDivElement>('#reaction-viewer');
const placeholder = required<HTMLParagraphElement>('#result-placeholder');
const equation = required<HTMLParagraphElement>('#reaction-equation');
const conditionAssessment = required<HTMLParagraphElement>('#condition-assessment');
const formulaNote = required<HTMLParagraphElement>('#formula-note');
const details = required<HTMLDetailsElement>('#result-details');
const learning = required<HTMLDetailsElement>('#result-learning');
const diagramHost = required<HTMLDivElement>('#reaction-diagram');
const diagramPlaceholder = required<HTMLParagraphElement>('#diagram-placeholder');
const diagramScroll = required<HTMLDivElement>('.diagram-scroll');
const previewHost = required<HTMLDivElement>('#reaction-previews');
const workspace = required<HTMLElement>('.lab-workspace');
const atomInspection = required<HTMLDivElement>('#atom-inspection');
const bondSummary = required<HTMLParagraphElement>('#bond-summary');
const bondLegend = required<HTMLUListElement>('#bond-legend');
const diagramNote = required<HTMLParagraphElement>('#diagram-note');
const view2D = required<HTMLButtonElement>('#view-2d');
const view3D = required<HTMLButtonElement>('#view-3d');
const viewCompare = required<HTMLButtonElement>('#view-compare');
const previewLabel = required<HTMLParagraphElement>('#preview-label');
const viewerHint = required<HTMLParagraphElement>('#viewer-hint');
const measurementsHost = required<HTMLDivElement>('#product-measurements');
const familyFilters = required<HTMLDivElement>('#family-filters');
const exampleCards = required<HTMLDivElement>('#example-cards');
const exampleCount = required<HTMLSpanElement>('#example-count');
const reactionCalculator = new ReactionCalculatorPanel(required<HTMLDetailsElement>('#reaction-calculator'));

const FAMILIES: ReactionFamily[] = ['Addition', 'Elimination', 'Substitution', 'Oxidation', 'Reduction', 'Condensation', 'Hydrolysis', 'Polymerization'];
const EXAMPLES: Example[] = [
  { id: 'alkene-hydrogenation', title: 'Hydrogenate ethene', reactants: ['ethene', 'hydrogen'], families: ['Addition', 'Reduction'], change: 'C=C becomes C–C; hydrogen adds', conditions: { solvent: '', temperature: '', catalyst: 'metal' } },
  { id: 'alkene-epoxidation', title: 'Form an epoxide', reactants: ['ethene', 'peracetic-acid'], families: ['Addition', 'Oxidation'], change: 'Peroxyacid O forms two C–O bonds; connectivity only', conditions: { solvent: 'dry', temperature: '', catalyst: 'none' } },
  { id: 'alkene-bromination', title: 'Add bromine to ethene', reactants: ['ethene', 'bromine'], families: ['Addition'], change: 'C=C becomes C–C; two C–Br bonds form', conditions: { solvent: 'dry', temperature: '', catalyst: '' } },
  { id: 'alkene-hydration', title: 'Hydrate ethene', reactants: ['ethene', 'water'], families: ['Addition'], change: 'H and OH add across C=C', conditions: { solvent: '', temperature: '', catalyst: 'acid' } },
  { id: 'methyl-substitution', title: 'Substitute bromomethane', reactants: ['bromomethane', 'hydroxide'], families: ['Substitution'], change: 'SN2: C–Br breaks as C–O forms', conditions: { solvent: 'polar-aprotic', temperature: '', catalyst: '' } },
  { id: 'ethyl-competition', title: 'Compare SN2 and E2', reactants: ['bromoethane', 'hydroxide'], families: ['Substitution', 'Elimination'], change: 'Same pair; conditions can favor different pathways', conditions: { solvent: 'ethanolic-protic', temperature: 'heated', catalyst: '' } },
  { id: 'secondary-elimination', title: 'Eliminate from 2-bromopropane', reactants: ['2-bromopropane', 'hydroxide'], families: ['Elimination'], change: 'E2: C–Br breaks as C=C forms', conditions: { solvent: 'ethanolic-protic', temperature: 'heated', catalyst: '' } },
  { id: 'tertiary-competition', title: 'Compare SN1 and E1', reactants: ['tert-butyl-chloride', 'water'], families: ['Substitution', 'Elimination'], change: 'Same pair; temperature changes the comparison', conditions: { solvent: 'aqueous-protic', temperature: 'ambient', catalyst: '' } },
  { id: 'fischer-esterification', title: 'Make an ester', reactants: ['ethanoic-acid', 'ethanol'], families: ['Condensation'], change: 'Acid + alcohol → ester + water', conditions: { solvent: '', temperature: '', catalyst: 'acid' } },
  { id: 'ester-hydrolysis', title: 'Split an ester', reactants: ['ethyl-ethanoate', 'water'], families: ['Hydrolysis'], change: 'Ester + water → acid + alcohol', conditions: { solvent: 'aqueous-protic', temperature: '', catalyst: 'acid' } },
  { id: 'secondary-oxidation', title: 'Oxidize 2-propanol', reactants: ['2-propanol', 'sodium-hypochlorite'], families: ['Oxidation'], change: 'Secondary alcohol → ketone; simplified net equation', conditions: { solvent: 'aqueous-protic', temperature: '', catalyst: '' } },
  { id: 'ketone-reduction', title: 'Reduce acetone', reactants: ['acetone', 'hydrogen'], families: ['Reduction'], change: 'Ketone C=O → secondary alcohol C–OH', conditions: { solvent: '', temperature: '', catalyst: 'metal' } },
  { id: 'alcohol-dehydration', title: 'Dehydrate ethanol', reactants: ['ethanol', 'sulfuric-acid'], families: ['Elimination'], change: 'OH + beta H → water; C=C forms', conditions: { solvent: '', temperature: 'heated', catalyst: 'acid' } },
  { id: 'alcohol-substitution', title: 'Replace ethanol OH with Br', reactants: ['ethanol', 'hydrogen-bromide'], families: ['Substitution'], change: 'Activated OH → Br; water forms', conditions: { solvent: '', temperature: 'heated', catalyst: '' } },
  { id: 'saponification', title: 'Saponify an ester', reactants: ['ethyl-ethanoate', 'hydroxide'], families: ['Hydrolysis'], change: 'Ester → carboxylate + alcohol (2D ionic product)', conditions: { solvent: 'aqueous-protic', temperature: '', catalyst: '' } },
  { id: 'alkyne-hydrogenation', title: 'Fully reduce propyne', reactants: ['propyne', 'hydrogen'], families: ['Reduction', 'Addition'], change: 'C≡C + 2 H₂ → C–C', conditions: { solvent: '', temperature: '', catalyst: 'metal' } },
  { id: 'alkyne-halogenation', title: 'Add bromine to propyne', reactants: ['propyne', 'bromine'], families: ['Addition'], change: 'One Br₂ → dihaloalkene; two → tetrahaloalkane', conditions: { solvent: 'dry', temperature: '', catalyst: '', additionStage: 'one' } },
  { id: 'alkyne-hx', title: 'Add HBr to propyne', reactants: ['propyne', 'hydrogen-bromide'], families: ['Addition'], change: 'Selected HX equivalents; bounded orientation', conditions: { solvent: '', temperature: '', catalyst: '', additionStage: 'one' } },
  { id: 'dihydroxylation', title: 'Make a vicinal diol', reactants: ['ethene', 'hydrogen-peroxide'], families: ['Oxidation', 'Addition'], change: 'Two same-face OH groups · conditional Os/H₂O₂ net model', conditions: { solvent: '', temperature: '', catalyst: 'osmium', workup: 'aqueous-release' } },
  { id: 'polymerization', title: 'Build a finite chain model', reactants: ['ethene', 'benzoyl-peroxide'], families: ['Polymerization', 'Addition'], change: 'Defined phenyl-ended oligomer, not bulk polymer', conditions: { solvent: '', temperature: 'heated', catalyst: 'radical', polymerUnits: '4' } },
];
let activeFamily: ReactionFamily | 'All' = 'All';
let reactionSiteShapes: unknown[] = [];

const viewerFactory = (window as unknown as { $3Dmol?: { createViewer: (host: HTMLElement, options: Record<string, unknown>) => Viewer } }).$3Dmol;
const viewer = viewerFactory?.createViewer(viewerHost, { backgroundColor: '#f5f3ee', antialias: true });
if (viewer) new ResizeObserver(() => {
  if (!viewerHost.hidden) { viewer.resize(); viewer.render(); }
}).observe(viewerHost);
// Initialize WebGL at a real size, then default to the 2D reaction view.
viewerHost.hidden = true;
const measurements = new BondMeasurements(measurementsHost, viewer, { bindClicks: false });
const atomInspector = new AtomInspector(diagramScroll, viewerHost, viewer, required<HTMLElement>('#atom-status'), required<HTMLButtonElement>('#clear-atom'),
  (atom) => measurements.pickAtom(atom));
const mechanismPanel = new MechanismPanel(required<HTMLDetailsElement>('#reaction-mechanism'), required<HTMLElement>('.lab-result-panel'), viewer ?? null);
const informationPanel = new ReactionInformationPanel(learning, () => {
  const host = required<HTMLDetailsElement>('#reaction-mechanism');
  if (!host.hidden) { host.open = true; host.querySelector('summary')?.focus(); }
  else setStatus('The mapped mechanism is still loading or unavailable. Try again once the 2D diagram is ready.');
});
const groupPanel = new FunctionalGroupPanel(required<HTMLDetailsElement>('#reactant-groups'), viewerFactory
  ? (host) => viewerFactory.createViewer(host, { backgroundColor: '#f5f3ee', antialias: true }) : undefined);

let catalog: Catalog | null = null;
let selectedReaction: Reaction | null = null;
let revision = 0;
let runController: AbortController | null = null;
let diagramController: AbortController | null = null;
let diagramData: ReactionDiagram | null = null;
let productReady = false;
let previewMode: '2d' | '3d' | 'compare' = '2d';
let selectedIds: [string | null, string | null] = [null, null];
let drawnInputs: [Reactant | null, Reactant | null] = [null, null];
type PubChemLookup = { query: string; items: Reactant[] };
let pubchemLookups: [PubChemLookup | null, PubChemLookup | null] = [null, null];
const lookupRevisions = [0, 0];
const DRAFT_KEY = 'molecule-playground.reaction-draft.v1';
const TRANSFER_KEY = 'molecule-playground.builder-reactant.v1';
const EXPLORER_TRANSFER_KEY = 'molecule-playground.explorer-reactant.v1';
const guidedConditions = new GuidedConditionsPanel(required<HTMLElement>('#guided-conditions'), applyGuidedConditions);

function guidanceSignature(): string {
  return JSON.stringify({ values: inputs.map(input => input.value), reactants: [resolveReactant(0), resolveReactant(1)].map(r => r ? reactantReference(r) : null), conditions: currentConditions() });
}

async function applyGuidedConditions(guidance: GuidedConditions, signature: string) {
  if (signature !== guidanceSignature()) throw new Error('The reaction or conditions changed. Review the updated suggestion.');
  const targets = guidedControlValues(guidance);
  const controls: Record<string, HTMLSelectElement> = { solvent: solventInput, temperature: temperatureInput, catalyst: catalystInput, oxidationStage: oxidationStageInput, workup: workupInput };
  // Validate all UI values before changing any field. No chemistry permission is
  // inferred here; matching and generation independently revalidate on server.
  for (const [key, value] of Object.entries(targets)) {
    if (!controls[key] || ![...controls[key].options].some(option => option.value === value)) throw new Error('The suggested settings do not match the available controls. Refresh the page.');
  }
  for (const [key, value] of Object.entries(targets)) controls[key].value = value;
  saveDraft();
  await updateMatches(guidance.reactionId);
}

function setStatus(message: string, error = false) {
  status.textContent = message;
  status.classList.toggle('is-error', error);
}

function renderExampleLibrary() {
  if (!catalog) return;
  familyFilters.replaceChildren();
  for (const family of ['All', ...FAMILIES] as const) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = family;
    button.setAttribute('aria-pressed', String(activeFamily === family));
    button.addEventListener('click', () => {
      activeFamily = family;
      renderExampleLibrary();
    });
    familyFilters.append(button);
  }
  const visible = EXAMPLES.filter((example) => activeFamily === 'All' || example.families.includes(activeFamily));
  exampleCount.textContent = `${visible.length} example${visible.length === 1 ? '' : 's'}`;
  exampleCards.replaceChildren();
  for (const example of visible) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'example-card';
    button.dataset.example = example.id;
    const badges = document.createElement('span');
    badges.className = 'example-families';
    badges.textContent = example.families.join(' · ');
    const title = document.createElement('strong');
    title.textContent = example.title;
    const pair = document.createElement('span');
    pair.className = 'example-pair';
    pair.textContent = example.reactants.map((id) => catalog!.reactants.find((item) => item.id === id)?.name ?? id).join(' + ');
    button.title = example.change;
    button.setAttribute('aria-description', example.change);
    button.append(badges, title, pair);
    exampleCards.append(button);
  }
}

function candidatesFor(slot: 0 | 1): Reactant[] {
  const drawn = drawnInputs[slot];
  if (drawn && inputs[slot].value === drawn.name) return [drawn];
  const lookup = pubchemLookups[slot];
  if (lookup && lookup.query === inputs[slot].value.trim()) return lookup.items;
  return catalog ? findReactantCandidates(catalog.reactants, inputs[slot].value) : [];
}

function resolveReactant(slot: 0 | 1): Reactant | undefined {
  const candidates = candidatesFor(slot);
  if (candidates.length === 1) return candidates[0];
  return candidates.find((item) => item.id === selectedIds[slot]);
}

function updateCalculatorLinks() {
  calculatorButtons.forEach((button, index) => {
    const reactant = resolveReactant(index as 0 | 1);
    button.hidden = !reactant;
    button.disabled = !reactant;
    button.setAttribute('aria-label', reactant ? `Calculate solutions for molecule ${index + 1}: ${reactant.name}` : `Calculate solutions for molecule ${index + 1}`);
  });
}

function openSolutionCalculator(slot: 0 | 1) {
  const reactant = resolveReactant(slot);
  if (!reactant) { setStatus('Select an exact compound before opening Calculators.'); return; }
  try {
    sessionStorage.setItem(CALCULATOR_TRANSFER_KEY, encodeCalculatorTransfer(calculatorCompoundFromReactant(reactant, molecules)));
    saveDraft();
    window.location.assign('/calculators.html#solutions');
  } catch { setStatus('Compound transfer is unavailable. Open Calculators from the menu and enter the compound manually.', true); }
}

function updatePathwaySettings(matches: Pick<Reaction, 'mechanism'>[]) {
  const addition = matches.some((reaction) => ['Alkyne halogenation', 'Alkyne hydrohalogenation'].includes(reaction.mechanism));
  const chain = matches.some((reaction) => reaction.mechanism === 'Polymerization model');
  const diol = matches.some((reaction) => reaction.mechanism === 'Alkene dihydroxylation');
  additionSettings.hidden = !addition;
  chainSettings.hidden = !chain;
  diolSettings.hidden = !diol;
  extensionConditions.hidden = !addition && !chain && !diol;
  extensionTitle.textContent = diol ? 'Dihydroxylation net-model settings' : addition && chain ? 'Pathway settings' : chain ? 'Finite chain settings' : 'Alkyne addition settings';
}

function saveDraft() {
  try {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ values: inputs.map((input) => input.value), selectedIds, drawnInputs, pubchemLookups, conditions: currentConditions() }));
  } catch { /* Entries still work when browser storage is unavailable. */ }
}

function currentConditions(): Conditions {
  const secondaryProfile = solventInput.value === 'secondary-naocl-acetic';
  return { solvent: secondaryProfile ? 'aqueous-protic' : solventInput.value, temperature: temperatureInput.value, catalyst: catalystInput.value, oxidationStage: oxidationStageInput.value, additionStage: additionStageInput.value, polymerUnits: polymerUnitsInput.value, workup: workupInput.value,
    ...(secondaryProfile ? { secondaryOxidationProfile: 'naocl-acetic-ketone-v1' } : {}) };
}

function isReviewedReactant(reactant: Reactant): boolean {
  return Boolean(catalog?.reactants.some((item) => item.id === reactant.id && item.smiles === reactant.smiles));
}

function restoreLookup(value: unknown, slot: 0 | 1): PubChemLookup | null {
  if (!value || typeof value !== 'object') return null;
  const saved = value as Partial<PubChemLookup>;
  if (typeof saved.query !== 'string' || saved.query !== inputs[slot].value.trim() || saved.query.length > 100
      || !Array.isArray(saved.items) || saved.items.length > 25) return null;
  const valid = saved.items.every((item) => item && typeof item === 'object'
    && typeof item.id === 'string' && item.id.length <= 60
    && typeof item.name === 'string' && item.name.length <= 200
    && typeof item.formula === 'string' && item.formula.length <= 40
    && typeof item.smiles === 'string' && item.smiles.length <= 1024
    && Array.isArray(item.aliases) && item.aliases.every((alias: unknown) => typeof alias === 'string' && alias.length <= 200));
  return valid ? saved as PubChemLookup : null;
}

function reactantReference(reactant: Reactant): string | { smiles: string; name: string } {
  return isReviewedReactant(reactant) ? reactant.id : { smiles: reactant.smiles, name: reactant.name.slice(0, 200) };
}

function renderChoices(slot: 0 | 1) {
  const host = choiceHosts[slot];
  host.replaceChildren();
  const candidates = candidatesFor(slot);
  if (candidates.length < 2) return;
  const prompt = document.createElement('p');
  prompt.textContent = `${inputs[slot].value.trim()} matches multiple structures. Choose one:`;
  host.append(prompt);
  for (const candidate of candidates) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${candidate.name} [${candidate.smiles}] · ${candidate.formula}`;
    button.setAttribute('aria-pressed', String(selectedIds[slot] === candidate.id));
    button.addEventListener('click', () => {
      selectedIds[slot] = candidate.id;
      saveDraft();
      updateMatches();
    });
    host.append(button);
  }
}

async function searchPubChem(slot: 0 | 1) {
  if (!catalog) return;
  const query = inputs[slot].value.trim();
  if (!query) {
    lookupStatuses[slot].textContent = 'Enter a molecule name or formula first.';
    inputs[slot].focus();
    return;
  }
  const requestRevision = ++lookupRevisions[slot];
  const button = searchButtons[slot];
  button.disabled = true;
  lookupStatuses[slot].textContent = 'Searching PubChem…';
  try {
    const response = await fetch(`/api/pubchem/search?q=${encodeURIComponent(query)}`);
    const payload = await response.json() as { results: PubChemReactantMatch[]; limited: boolean } | { error: string };
    if (requestRevision !== lookupRevisions[slot] || inputs[slot].value.trim() !== query) return;
    if (!response.ok || 'error' in payload) throw new Error('error' in payload ? payload.error : 'PubChem search failed.');
    const candidates = mergePubChemCandidates(catalog.reactants, query, payload.results);
    pubchemLookups[slot] = { query, items: candidates };
    if (!candidates.some((candidate) => candidate.id === selectedIds[slot])) selectedIds[slot] = null;
    lookupStatuses[slot].textContent = candidates.length
      ? `${candidates.length} distinct structure${candidates.length === 1 ? '' : 's'} available${payload.limited ? ' (first results shown)' : ''}.${candidates.length > 1 ? ' Choose one below.' : ''}`
      : 'No PubChem record found. Try a full name or formula.';
    saveDraft();
    updateMatches();
  } catch (error) {
    if (requestRevision !== lookupRevisions[slot]) return;
    pubchemLookups[slot] = null;
    lookupStatuses[slot].textContent = error instanceof Error ? error.message : 'PubChem search is unavailable.';
    updateMatches();
  } finally {
    if (requestRevision === lookupRevisions[slot]) button.disabled = false;
  }
}

function resetResult() {
  informationPanel.setReaction();
  mechanismPanel.reset();
  for (const shape of reactionSiteShapes) viewer?.removeShape(shape);
  reactionSiteShapes = [];
  reactionCalculator.setReaction();
  revision += 1;
  selectedReaction = null;
  runController?.abort();
  diagramController?.abort();
  runController = null;
  diagramController = null;
  diagramData = null;
  measurements.reset();
  measurementsHost.hidden = true;
  atomInspector.reset();
  diagramScroll.replaceChildren();
  diagramScroll.hidden = true;
  atomInspection.hidden = true;
  diagramScroll.scrollLeft = 0;
  diagramScroll.scrollTop = 0;
  diagramPlaceholder.hidden = false;
  diagramPlaceholder.textContent = 'Choose a pathway to see its structures and bond changes.';
  diagramHost.setAttribute('aria-busy', 'false');
  bondSummary.hidden = true;
  bondSummary.textContent = '';
  bondLegend.hidden = true;
  bondLegend.replaceChildren();
  diagramNote.hidden = true;
  diagramNote.textContent = '';
  productReady = false;
  viewer?.removeAllModels();
  if (!viewerHost.hidden) viewer?.render();
  placeholder.hidden = false;
  placeholder.textContent = 'Choose a pathway to generate its main product.';
  details.hidden = true;
  details.open = false;
  learning.hidden = true;
  learning.open = false;
  equation.textContent = 'Choose a pathway to preview its equation.';
  conditionAssessment.hidden = true;
  formulaNote.hidden = true;
  setPreview('2d');
  updatePreviewActions();
}

function updatePreviewActions() {
  const canRun = Boolean(selectedReaction) && selectedReaction?.assessment?.canRun !== false;
  view2D.disabled = !selectedReaction;
  view3D.disabled = !canRun;
  viewCompare.disabled = !canRun;
  runButton.disabled = !canRun || Boolean(runController);
  runButton.textContent = runController ? 'Calculating 3D…' : 'View 3D product';
  if (!selectedReaction) for (const control of [view3D, viewCompare, runButton]) control.title = '';
}

function setPreview(mode: '2d' | '3d' | 'compare') {
  atomInspector.clearHover();
  previewMode = mode;
  view2D.setAttribute('aria-pressed', String(mode === '2d'));
  view3D.setAttribute('aria-pressed', String(mode === '3d'));
  viewCompare.setAttribute('aria-pressed', String(mode === 'compare'));
  diagramHost.hidden = mode === '3d';
  viewerHost.hidden = mode === '2d';
  viewerHint.hidden = mode === '2d';
  measurementsHost.hidden = mode === '2d' || !productReady || !measurements.available;
  bondLegend.hidden = mode === '3d' || !diagramData?.highlightsAvailable;
  diagramNote.hidden = mode === '3d' || !diagramData?.note;
  previewHost.classList.toggle('is-comparing', mode === 'compare');
  workspace.classList.toggle('is-comparing', mode === 'compare');
  previewLabel.textContent = mode === 'compare' ? 'Linked atom comparison' : mode === '2d' ? 'Reactants → products' : 'Main product only';
  if (mode !== '2d') requestAnimationFrame(() => {
    if (previewMode !== '2d') { viewer?.resize(); viewer?.render(); }
  });
}

async function loadDiagram(reaction: Reaction, first: Reactant, second: Reactant) {
  const requestRevision = revision;
  const controller = new AbortController();
  diagramController = controller;
  diagramPlaceholder.textContent = 'Drawing the net bond changes…';
  diagramHost.setAttribute('aria-busy', 'true');
  try {
    const response = await fetch('/api/reactions/diagram', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: controller.signal,
      body: JSON.stringify({ reactionId: reaction.id, reactantA: reactantReference(first), reactantB: reactantReference(second), conditions: currentConditions() }),
    });
    const payload = await response.json() as ReactionDiagram | { error: string };
    if (requestRevision !== revision) return;
    if (!response.ok || 'error' in payload) throw new Error('error' in payload ? payload.error : 'Could not draw this pathway.');
    diagramData = payload;
    const svg = safeDiagramSvg(payload.svg);
    svg.setAttribute('role', 'group');
    svg.setAttribute('aria-label', `${formatEquation(reaction, first, second)}. Net bond changes: ${payload.summary}`);
    diagramScroll.replaceChildren(svg);
    mechanismPanel.setMechanism(payload.mechanism);
    atomInspector.setDiagram(payload.atoms ?? [], reaction.mechanism === 'Alcohol oxidation' && reaction.assessment?.evidence?.canGenerate3D === false
      ? reaction.secondaryOxidationModel ? 'Conditional 2D only; secondary ketone profile unresolved.' : 'Conditional 2D only; aldehyde endpoint unresolved.'
      : reaction.assessment?.canRun === false ? 'Conditional 2D only; 3D is blocked by the stated conditions or chemistry limitations.' : '');
    atomInspection.hidden = !payload.atoms?.length;
    diagramScroll.hidden = false;
    diagramPlaceholder.hidden = true;
    bondSummary.textContent = payload.summary;
    bondSummary.hidden = false;
    bondLegend.replaceChildren();
    for (const item of payload.legend) {
      const entry = document.createElement('li');
      const swatch = document.createElement('span');
      swatch.className = 'bond-swatch';
      swatch.style.backgroundColor = item.color;
      swatch.setAttribute('aria-hidden', 'true');
      entry.append(swatch, document.createTextNode(item.label));
      bondLegend.append(entry);
    }
    diagramNote.textContent = payload.note ?? '';
    setPreview(previewMode);
  } catch (error) {
    if (requestRevision !== revision) return;
    diagramPlaceholder.textContent = error instanceof Error ? `${error.message} You can still try the 3D product.` : 'The 2D diagram is unavailable. Try the 3D product.';
  } finally {
    if (diagramController === controller) {
      diagramController = null;
      diagramHost.setAttribute('aria-busy', 'false');
    }
  }
}

function formatEquation(reaction: Reaction, first: Reactant, second: Reactant): string {
  if (!catalog) return '';
  const active = [first, second] as const;
  const availableReactants = [...catalog.reactants, ...active.flatMap((item, index) =>
    isReviewedReactant(item) ? [] : [{ ...item, id: `drawn-${index + 1}` }])];
  const equationInputs = reaction.equationReactants.map((id) => availableReactants.find((item) => item.id === id)).filter((item): item is Reactant => Boolean(item));
  const mediumId = reaction.reactants.find((id) => !reaction.equationReactants.includes(id));
  const medium = availableReactants.find((item) => item.id === mediumId);
  const mediumNote = medium ? ` · ${medium.name} ${reaction.mechanism === 'Alcohol dehydration' ? 'is the catalyst (not consumed)' : 'is the medium'}` : '';
  const counts = new Map<string, { item: Reactant; count: number }>();
  for (const item of equationInputs) { const previous = counts.get(item.id); counts.set(item.id, { item, count: (previous?.count ?? 0) + 1 }); }
  return `${[...counts.values()].map(({ item, count }) => `${count > 1 ? count + ' ' : ''}${item.name} (${item.formula})`).join(' + ')} → ${reaction.productName} (${reaction.productEquationFormula})${reaction.byproducts.map((item) => ` + ${item.name} (${item.formula})`).join('')}${mediumNote}`;
}

function showEmpty(message: string) {
  optionsHost.replaceChildren();
  const paragraph = document.createElement('p');
  paragraph.className = 'empty-options';
  paragraph.textContent = message;
  optionsHost.append(paragraph);
}

async function updateMatches(preferredReactionId?: string) {
  guidedConditions.clear();
  resetResult();
  renderComparison(comparisonHost);
  updateCalculatorLinks();
  updatePathwaySettings([]);
  interpretation.hidden = true;
  interpretation.textContent = '';
  selectedReaction = null;
  runButton.disabled = true;
  if (!catalog) return;
  renderChoices(0);
  renderChoices(1);
  const first = resolveReactant(0);
  const second = resolveReactant(1);
  groupPanel.setReactants([first, second].map((reactant) => reactant ? { name: reactant.name, smiles: reactant.smiles } : null));
  if (!inputA.value.trim() || !inputB.value.trim()) {
    showEmpty('Choose both molecules to see supported pathways.');
    setStatus('Choose two molecules and, if known, their conditions.');
    return;
  }
  if (inputs.some((_, index) => candidatesFor(index as 0 | 1).length === 0)) {
    showEmpty('One or both molecules are not recognized yet. Search PubChem beside that input, type a listed molecule, or send a drawing from Builder.');
    setStatus('Search for an unlisted molecule or choose a reviewed example.');
    return;
  }
  if (!first || !second) {
    showEmpty('A formula matches more than one structure. Choose the intended molecule above.');
    setStatus('Select a structure for each ambiguous formula.');
    return;
  }
  const requestRevision = revision;
  showEmpty('Checking supported reaction rules…');
  setStatus('Matching structures and comparing conditions…');
  let matches: Reaction[];
  let unsupportedReasons: string[] = [];
  try {
    const response = await fetch('/api/reactions/match', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reactantA: reactantReference(first), reactantB: reactantReference(second), conditions: currentConditions() }),
    });
    const payload = await response.json() as { reactions: Reaction[]; reactionOptions?: Reaction[]; interpretationNotes?: string[]; unsupportedReasons?: string[]; comparison?: PathwayComparison | null } | { error: string };
    if (requestRevision !== revision) return;
    if (!response.ok || 'error' in payload) {
      if (response.status === 422) {
        showEmpty(unsupportedInputMessage('error' in payload ? payload.error : undefined));
        setStatus('This input is outside the supported reaction model.');
        return;
      }
      throw new Error('error' in payload ? payload.error : 'Could not check the reaction rules.');
    }
    matches = payload.reactionOptions ?? payload.reactions;
    renderComparison(comparisonHost, payload.comparison);
    unsupportedReasons = payload.unsupportedReasons ?? [];
    if (payload.interpretationNotes?.length) {
      interpretation.textContent = payload.interpretationNotes.join(' ');
      interpretation.hidden = false;
    }
  } catch (error) {
    if (requestRevision === revision) {
      showEmpty('Could not check the reaction rules right now.');
      setStatus(error instanceof Error ? error.message : 'The chemistry service is unavailable.', true);
    }
    return;
  }
  if (!matches.length) {
    const customInput = [first, second].some((reactant) => !isReviewedReactant(reactant));
    showEmpty(unsupportedReasons.length ? unsupportedReasons.join(' ') : customInput
      ? 'No supported structural pathway for this pair. PubChem identifies molecules; it does not predict reactions. This does not prove the pair cannot react.'
      : 'No supported pathway for this pair yet. That does not prove the molecules cannot react.');
    setStatus(unsupportedReasons.length ? 'No qualified option yet. Review the requirements above.' : 'No supported rule matches these structures.');
    return;
  }
  updatePathwaySettings(matches);
  const requestSignature = guidanceSignature();
  let preferredButton: HTMLButtonElement | undefined;
  optionsHost.replaceChildren();
  for (const reaction of matches) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'reaction-option';
    button.setAttribute('aria-pressed', 'false');
    const title = document.createElement('strong');
    title.textContent = `${reaction.mechanism} · ${(reaction.classifications ?? [reaction.family]).join(' + ')}`;
    const summary = document.createElement('span');
    summary.textContent = `Main product: ${reaction.productName} · ${reaction.productEquationFormula}`;
    const assessment = document.createElement('em');
    assessment.className = `assessment-${reaction.assessment?.state ?? 'incomplete'}`;
    assessment.textContent = reaction.assessment?.evidence ? conditionLabel(reaction.assessment) : reaction.reasoning?.label ?? conditionLabel(reaction.assessment);
    button.append(title, summary, assessment);
    if (reaction.site) {
      const site = document.createElement('small');
      site.textContent = `${reaction.site.label} · amber marks the selected site`;
      button.append(site);
    }
    if (reaction.family === 'Oxidation') {
      const warning = document.createElement('small');
      warning.textContent = 'Illustrative equation only · Never mix chemicals to test it.';
      button.append(warning);
    }
    button.addEventListener('click', () => {
      resetResult();
      selectedReaction = reaction;
      guidedConditions.setGuidance(reaction.guidedConditions, requestSignature);
      reactionCalculator.setReaction(reaction.stoichiometry);
      equation.textContent = formatEquation(reaction, first, second);
      conditionAssessment.textContent = conditionLabel(reaction.assessment);
  if (reaction.mechanism.startsWith('Alkyne ') || reaction.mechanism === 'Alcohol dehydration') conditionAssessment.textContent += ` — ${conditionGuidance(reaction.assessment)}`;
  if (reaction.mechanism === 'Alcohol substitution') conditionAssessment.textContent += ` — ${conditionGuidance(reaction.assessment)}`;
  if (reaction.mechanism === 'Alcohol oxidation' && reaction.assessment?.evidence) {
    conditionAssessment.textContent += ` — ${conditionGuidance(reaction.assessment)}`;
  }
  if (reaction.mechanism === 'Aldehyde oxidation') conditionAssessment.textContent += ` — ${conditionGuidance(reaction.assessment)}`;
      const guidance = conditionGuidance(reaction.assessment);
      for (const control of [view3D, viewCompare, runButton]) control.title = guidance;
      conditionAssessment.title = guidance;
      conditionAssessment.className = `condition-assessment assessment-${reaction.assessment?.state ?? 'incomplete'}`;
      conditionAssessment.hidden = false;
      for (const option of optionsHost.querySelectorAll<HTMLButtonElement>('button')) {
        option.setAttribute('aria-pressed', String(option === button));
      }
      informationPanel.setReaction(reaction);
      updatePreviewActions();
      void loadDiagram(reaction, first, second);
      setStatus(reaction.assessment?.canRun === false
        ? `${reaction.mechanism}: conditional 2D net option. ${reaction.assessment.note}`
        : `${reaction.mechanism} selected. Inspect the 2D changes or view the 3D product.`);
    });
    const wrapper = document.createElement('div');
    wrapper.className = 'reaction-option-wrap';
    wrapper.append(button);
    if (reaction.reasoning) wrapper.append(renderReasoning(reaction.reasoning, reaction.assessment?.evidence?.label));
    optionsHost.append(wrapper);
    if (reaction.id === preferredReactionId) preferredButton = button;
  }
  if (preferredButton) preferredButton.click();
  else {
    // Do not recommend switching a complete-reduction choice to Lindlar before
    // the user selects partial reduction. Existing oxidation discovery stays.
    const guidedMatches = matches.filter(reaction => reaction.guidedConditions?.showOnInitialMatch !== false);
    const pilot = guidedMatches.find(reaction => reaction.guidedConditions?.canApply) ?? guidedMatches.find(reaction => reaction.guidedConditions);
    guidedConditions.setGuidance(pilot?.guidedConditions, requestSignature);
    setStatus(reactionOptionSummary(matches));
  }
}

required<HTMLFormElement>('#reactant-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const slot = document.activeElement === inputB ? 1 : 0;
  void searchPubChem(slot);
});
calculatorButtons.forEach((button, index) => button.addEventListener('click', () => openSolutionCalculator(index as 0 | 1)));
searchButtons.forEach((button, index) => button.addEventListener('click', () => void searchPubChem(index as 0 | 1)));
inputs.forEach((input, index) => input.addEventListener('input', () => {
  const slot = index as 0 | 1;
  lookupRevisions[slot] += 1;
  searchButtons[slot].disabled = false;
  lookupStatuses[slot].textContent = '';
  pubchemLookups[slot] = null;
  selectedIds[slot] = null;
  drawnInputs[slot] = null;
  saveDraft();
  updateMatches();
}));
for (const select of [solventInput, temperatureInput, catalystInput, oxidationStageInput, additionStageInput, polymerUnitsInput, workupInput]) select.addEventListener('change', () => {
  // Remember only the selected address, never old results/permission. The
  // rematch clears everything immediately and reselects only a fresh option.
  const selectedId = selectedReaction?.id;
  saveDraft();
  updateMatches(selectedId);
});
exampleCards.addEventListener('click', (event) => {
  const target = (event.target as HTMLElement).closest<HTMLButtonElement>('[data-example]');
  if (!target || !catalog) return;
  const example = EXAMPLES.find((item) => item.id === target.dataset.example);
  if (!example) return;
  const [firstId, secondId] = example.reactants;
  inputA.value = catalog.reactants.find((item) => item.id === firstId)?.name ?? '';
  inputB.value = catalog.reactants.find((item) => item.id === secondId)?.name ?? '';
  solventInput.value = example.conditions.solvent;
  temperatureInput.value = example.conditions.temperature;
  catalystInput.value = example.conditions.catalyst;
  oxidationStageInput.value = example.conditions.oxidationStage ?? '';
  additionStageInput.value = example.conditions.additionStage ?? 'one';
  polymerUnitsInput.value = example.conditions.polymerUnits ?? '4';
  workupInput.value = example.conditions.workup ?? '';
  selectedIds = [null, null];
  drawnInputs = [null, null];
  pubchemLookups = [null, null];
  lookupRevisions[0] += 1;
  lookupRevisions[1] += 1;
  searchButtons.forEach((button) => { button.disabled = false; });
  lookupStatuses.forEach((item) => { item.textContent = ''; });
  saveDraft();
  updateMatches();
});

async function showProduct3D(mode: '3d' | 'compare' = 'compare') {
  const first = resolveReactant(0);
  const second = resolveReactant(1);
  const reaction = selectedReaction;
  if (!first || !second || !reaction) return;
  if (reaction.assessment?.canRun === false) {
    setStatus(reaction.assessment.note);
    return;
  }
  setPreview(mode);
  if (productReady || runController) return;
  const requestRevision = revision;
  const controller = new AbortController();
  runController = controller;
  updatePreviewActions();
  placeholder.textContent = 'Calculating the main product’s 3D shape…';
  setStatus('Checking atom balance and calculating the product shape…');
  try {
    const response = await fetch('/api/reactions/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({ reactionId: reaction.id, reactantA: reactantReference(first), reactantB: reactantReference(second), conditions: currentConditions() }),
    });
    const payload = await response.json() as RunResult | { error: string };
    if (requestRevision !== revision) return;
    if (!response.ok || 'error' in payload) throw new Error('error' in payload ? payload.error : 'Could not calculate this reaction.');
    if (payload.product.representation === '2d-only' || !payload.product.molfile) {
      const reason = payload.product.reason?.includes('charged atoms')
        ? 'Charged product · shown in 2D; no neutral 3D molecule assumed.'
        : payload.product.reason ?? 'This product is shown in 2D only.';
      setPreview('2d'); placeholder.textContent = reason;
      required<HTMLElement>('#product-name').textContent = payload.productName;
      required<HTMLElement>('#product-formula').textContent = payload.product.formula;
      required<HTMLElement>('#product-smiles').textContent = payload.product.smiles;
      required<HTMLElement>('#atom-balance').textContent = payload.balanced ? 'Atoms and charge accounted for' : 'Not balanced';
      required<HTMLElement>('#product-method').textContent = '2D only'; details.hidden = false;
      setStatus(`${payload.productName}: ${reason}`);
      return;
    }
    if (!viewer) throw new Error('The 3D viewer did not load. Check the network connection.');
    measurements.reset();
    measurementsHost.hidden = true;
    atomInspector.reset();
    if (diagramData?.atoms) atomInspector.setDiagram(diagramData.atoms);
    mechanismPanel.clearModel();
    viewer.removeAllModels();
    const model = viewer.addModel(payload.product.molfile, 'mol', { keepH: true });
    viewer.setStyle({}, { stick: { colorscheme: 'Jmol', radius: 0.1 }, sphere: { scale: 0.28 } });
    const productAtoms = model.selectedAtoms({});
    const siteMaps = new Set(reaction.site?.atomMaps ?? []);
    for (const link of payload.product.atomLinks ?? []) {
      const atom = productAtoms.find((item) => item.index === link.index);
      if (atom && siteMaps.has(link.mapId)) {
        reactionSiteShapes.push(viewer.addSphere({ center: { x: atom.x, y: atom.y, z: atom.z },
          radius: 0.65, color: '#b87916', opacity: 0.25, clickable: false, hoverable: false }));
      }
    }
    atomInspector.setModel(productAtoms, payload.product.atomLinks ?? []);
    mechanismPanel.setModel(productAtoms, payload.product.atomLinks ?? []);
    measurements.setAtoms(productAtoms);
    viewer.zoomTo();
    if (previewMode !== '2d') { viewer.resize(); viewer.render(); }
    productReady = true;
    measurementsHost.hidden = previewMode === '2d' || !measurements.available;
    placeholder.hidden = true;
    equation.textContent = formatEquation(reaction, first, second);
    conditionAssessment.textContent = conditionLabel(payload.assessment);
    conditionAssessment.className = `condition-assessment assessment-${payload.assessment.state}`;
    conditionAssessment.hidden = false;
    formulaNote.hidden = reaction.productEquationFormula === payload.product.formula;
    formulaNote.textContent = `${reaction.productEquationFormula} is a condensed structural formula; ${payload.product.formula} is the molecular formula.`;
    required<HTMLElement>('#product-name').textContent = payload.productName;
    required<HTMLElement>('#product-formula').textContent = payload.product.formula;
    required<HTMLElement>('#product-smiles').textContent = payload.product.smiles;
    required<HTMLElement>('#atom-balance').textContent = payload.balanced ? 'Atoms and charge accounted for' : 'Not balanced';
    required<HTMLElement>('#product-method').textContent = payload.product.converged ? payload.product.forceField : `${payload.product.forceField} · not fully minimized`;
    details.hidden = false;
    setStatus(`${payload.productName} is ready${payload.assessment.evidence ? ' as a conditional net-model structure, not a predicted reaction outcome' : ''}. Use Compare to inspect the same atom in 2D and 3D.`);
  } catch (error) {
    if (requestRevision === revision) {
      measurements.reset();
      measurementsHost.hidden = true;
      for (const shape of reactionSiteShapes) viewer?.removeShape(shape);
      reactionSiteShapes = [];
      atomInspector.reset();
      if (diagramData?.atoms) atomInspector.setDiagram(diagramData.atoms);
      productReady = false;
      mechanismPanel.clearModel();
      viewer?.removeAllModels();
      if (!viewerHost.hidden) viewer?.render();
      placeholder.hidden = false;
      const message = error instanceof Error ? error.message : 'Could not show this product.';
      placeholder.textContent = `${message} Retry 3D or switch back to 2D.`;
      setStatus(message, true);
    }
  } finally {
    if (runController === controller) {
      runController = null;
      updatePreviewActions();
    }
  }
}

runButton.addEventListener('click', () => void showProduct3D('compare'));
view3D.addEventListener('click', () => void showProduct3D('3d'));
viewCompare.addEventListener('click', () => void showProduct3D('compare'));
view2D.addEventListener('click', () => setPreview('2d'));
window.addEventListener('pagehide', (event) => {
  if (event.persisted) return; // A back/forward-cache restore retains the preview and pending state.
  runController?.abort();
  diagramController?.abort();
  atomInspector.clearHover();
});

try {
  const response = await fetch('/api/reactions/catalog');
  if (!response.ok) throw new Error('The local chemistry service is unavailable.');
  catalog = await response.json() as Catalog;
  renderExampleLibrary();
  for (const reactant of catalog.reactants) {
    const option = document.createElement('option');
    option.value = reactant.name;
    option.label = reactant.formula;
    datalist.append(option);
  }
  for (const formula of new Set(catalog.reactants.map((item) => item.formula))) {
    const option = document.createElement('option');
    option.value = formula;
    option.label = catalog.reactants.filter((item) => item.formula === formula).map((item) => item.name).join(' / ');
    datalist.append(option);
  }
  try {
    const draft = JSON.parse(sessionStorage.getItem(DRAFT_KEY) ?? 'null') as { values?: unknown; selectedIds?: unknown; drawnInputs?: unknown; pubchemLookups?: unknown; conditions?: Record<string, unknown> } | null;
    if (Array.isArray(draft?.values) && draft.values.length === 2 && draft.values.every((value) => typeof value === 'string')) {
      inputs.forEach((input, index) => { input.value = (draft.values as string[])[index]; });
      if (Array.isArray(draft.selectedIds) && draft.selectedIds.length === 2) {
        selectedIds = draft.selectedIds.map((id) => typeof id === 'string' ? id : null) as [string | null, string | null];
      }
      if (Array.isArray(draft.drawnInputs) && draft.drawnInputs.length === 2) {
        drawnInputs = draft.drawnInputs.map((item, index) => {
          if (!item || typeof item !== 'object') return null;
          const saved = item as Partial<Reactant>;
          if (saved.id !== `drawn-${index + 1}` || typeof saved.name !== 'string' || typeof saved.formula !== 'string'
              || typeof saved.smiles !== 'string' || saved.smiles.length > 1024 || inputs[index].value !== saved.name) return null;
          return { id: saved.id, name: saved.name, formula: saved.formula, smiles: saved.smiles, aliases: [] };
        }) as [Reactant | null, Reactant | null];
      }
      if (Array.isArray(draft.pubchemLookups) && draft.pubchemLookups.length === 2) {
        pubchemLookups = [restoreLookup(draft.pubchemLookups[0], 0), restoreLookup(draft.pubchemLookups[1], 1)];
        pubchemLookups.forEach((lookup, index) => {
          if (lookup) lookupStatuses[index].textContent = `${lookup.items.length} saved structure${lookup.items.length === 1 ? '' : 's'} available.`;
        });
      }
      for (const [key, select] of [['solvent', solventInput], ['temperature', temperatureInput], ['catalyst', catalystInput], ['oxidationStage', oxidationStageInput], ['additionStage', additionStageInput], ['polymerUnits', polymerUnitsInput], ['workup', workupInput]] as const) {
        const value = draft.conditions?.[key];
        if (typeof value === 'string' && [...select.options].some((option) => option.value === value)) select.value = value;
      }
      if (draft.conditions?.secondaryOxidationProfile === 'naocl-acetic-ketone-v1' && draft.conditions?.solvent === 'aqueous-protic') solventInput.value = 'secondary-naocl-acetic';
    }
    const transfer = JSON.parse(sessionStorage.getItem(TRANSFER_KEY) ?? 'null') as { slot?: unknown; smiles?: unknown; formula?: unknown } | null;
    sessionStorage.removeItem(TRANSFER_KEY);
    const explorerTransfer = JSON.parse(sessionStorage.getItem(EXPLORER_TRANSFER_KEY) ?? 'null') as { slot?: unknown; id?: unknown; name?: unknown; formula?: unknown; smiles?: unknown } | null;
    sessionStorage.removeItem(EXPLORER_TRANSFER_KEY);
    if (transfer && (transfer.slot === 0 || transfer.slot === 1) && typeof transfer.smiles === 'string') {
      const found = findReactantBySmiles(catalog.reactants, transfer.smiles);
      if (found) {
        inputs[transfer.slot].value = found.name;
        selectedIds[transfer.slot] = found.id;
        drawnInputs[transfer.slot] = null;
        pubchemLookups[transfer.slot] = null;
        saveDraft();
        updateMatches();
        setStatus(`${found.name} was added from Builder as molecule ${transfer.slot + 1}.`);
      } else if (typeof transfer.formula === 'string' && transfer.formula.length <= 40 && transfer.smiles.length <= 1024) {
        const slot = transfer.slot;
        const drawn: Reactant = { id: `drawn-${slot + 1}`, name: `Drawn structure · ${transfer.formula}`, formula: transfer.formula, smiles: transfer.smiles, aliases: [] };
        drawnInputs[slot] = drawn;
        inputs[slot].value = drawn.name;
        selectedIds[slot] = drawn.id;
        pubchemLookups[slot] = null;
        saveDraft();
        updateMatches();
        setStatus(`Drawing added as molecule ${slot + 1}. Checking supported structural rules…`);
      } else {
        updateMatches();
        setStatus('The Builder transfer was incomplete. Please generate the drawing again.', true);
      }
    } else if (explorerTransfer && (explorerTransfer.slot === 0 || explorerTransfer.slot === 1)
        && typeof explorerTransfer.name === 'string' && explorerTransfer.name.length <= 200
        && typeof explorerTransfer.formula === 'string' && explorerTransfer.formula.length <= 40
        && typeof explorerTransfer.smiles === 'string' && explorerTransfer.smiles.length <= 1024) {
      const slot = explorerTransfer.slot;
      const found = catalog.reactants.find((item) => item.id === explorerTransfer.id && item.smiles === explorerTransfer.smiles)
        ?? findReactantBySmiles(catalog.reactants, explorerTransfer.smiles);
      const molecule: Reactant = found ?? {
        id: typeof explorerTransfer.id === 'string' ? explorerTransfer.id : `explorer-${slot + 1}`,
        name: explorerTransfer.name, formula: explorerTransfer.formula,
        smiles: explorerTransfer.smiles, aliases: [],
      };
      inputs[slot].value = molecule.name;
      selectedIds[slot] = molecule.id;
      drawnInputs[slot] = null;
      pubchemLookups[slot] = found ? null : { query: molecule.name, items: [molecule] };
      saveDraft();
      updateMatches();
      setStatus(`${molecule.name} was added from Explorer as molecule ${slot + 1}. Choose the other molecule to compare supported reactions.`);
    } else if (inputA.value || inputB.value) {
      updateMatches();
    } else {
      setStatus('Type two molecules, draw in Builder, or try an example pair.');
    }
  } catch {
    setStatus('Type two molecules or try an example pair.');
  }
} catch (error) {
  setStatus(error instanceof Error ? error.message : 'Could not load the reaction collection.', true);
}
