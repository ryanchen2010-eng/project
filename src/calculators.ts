import './home.css';
import './calculators.css';
import './solution-calculator.css';
import './reaction-calculator.css';
import { molecules, isIonicCompound } from './molecules';
import { CALCULATOR_TRANSFER_KEY, calculatorCompoundFromMolecule, decodeCalculatorTransfer, type CalculatorCompound } from './calculator-compound';
import { MoleCalculatorPanel } from './mole-calculator-panel';
import { SolutionCalculatorPanel } from './solution-calculator-panel';
import { mountReactionAmounts } from './calculator-reactions';
import { mountEquilibriumCalculator } from './equilibrium-calculator-panel';
import { mountAcidBaseCalculator } from './acid-base-calculator-panel';
import { mountSolubilityCalculator } from './solubility-calculator-panel';
import './ui-system.css';
import { mountWorkspaceShell } from './workspace-shell';
import './workspace-shell.css';

mountWorkspaceShell(document.querySelector<HTMLElement>('.calculator-shell')!);

const topics = [
  { id: 'moles', name: 'Moles and particles', description: 'Convert mass, moles and counts of a specified entity.', model: 'Local arithmetic' },
  { id: 'solutions', name: 'Solutions', description: 'Concentration, required solute mass and stock dilution.', model: 'Local arithmetic' },
  { id: 'reactions', name: 'Reaction amounts', description: 'Limiting reactants, theoretical yield and required amounts for a supported reaction.', model: 'Verified reaction catalog' },
  { id: 'equilibrium', name: 'Equilibrium', description: 'K/Q or final concentrations for one balanced reversible reaction.', model: 'Defined model · entered constants' },
  { id: 'acid-base', name: 'Acids, bases and buffers', description: 'pH and species concentrations for one acid/base family, including water.', model: 'Defined model · entered constants' },
  { id: 'solubility', name: 'Solubility', description: 'Saturation and Qsp for one salt producing two ion types.', model: 'Defined model · entered constants' },
] as const;
type TopicId = typeof topics[number]['id'];
function element<T extends Element>(id: string) {
  const item = document.getElementById(id); if (!item) throw new Error(`Missing calculator element: ${id}`); return item as unknown as T;
}
const menu = element<HTMLElement>('calculator-topics');
const mobileTopic = element<HTMLSelectElement>('calculator-topic');
const panels = element<HTMLElement>('calculator-panels');
const context = element<HTMLElement>('calculator-context');
const compoundSelect = element<HTMLSelectElement>('calculator-compound');
const notice = element<HTMLElement>('calculator-compound-notice');
const topicButtons = new Map<TopicId, HTMLButtonElement>();
const sections = new Map<TopicId, HTMLElement>();
const initializers = new Map<TopicId, () => void>();
const initialized = new Set<TopicId>();
const compoundRecords = new Map<string, CalculatorCompound>();
const manual = document.createElement('option'); manual.value = ''; manual.textContent = 'Manual entry'; compoundSelect.append(manual);
for (const molecule of molecules) {
  const compound = calculatorCompoundFromMolecule(molecule, isIonicCompound(molecule));
  compoundRecords.set(compound.id, compound);
  const option = document.createElement('option'); option.value = compound.id; option.textContent = `${compound.name} (${compound.formula})`; compoundSelect.append(option);
}
for (const topic of topics) {
  const button = document.createElement('button'); button.type = 'button'; button.textContent = topic.name;
  button.setAttribute('aria-controls', `calculator-panel-${topic.id}`); button.addEventListener('click', () => selectTopic(topic.id));
  menu.append(button); topicButtons.set(topic.id, button);
  const option = document.createElement('option'); option.value = topic.id; option.textContent = topic.name; mobileTopic.append(option);
  const section = document.createElement('section'); section.id = `calculator-panel-${topic.id}`;
  section.hidden = true; section.setAttribute('aria-label', topic.name); panels.append(section); sections.set(topic.id, section);
}
const molePanel = new MoleCalculatorPanel(sections.get('moles')!);
const solutionHost = document.createElement('details'); solutionHost.id = 'hub-solution-calculator'; solutionHost.open = true;
sections.get('solutions')!.append(solutionHost);
const solutionPanel = new SolutionCalculatorPanel(solutionHost);
initialized.add('moles'); initialized.add('solutions');
initializers.set('reactions', () => mountReactionAmounts(sections.get('reactions')!));
initializers.set('equilibrium', () => mountEquilibriumCalculator(sections.get('equilibrium')!));
initializers.set('acid-base', () => mountAcidBaseCalculator(sections.get('acid-base')!));
initializers.set('solubility', () => mountSolubilityCalculator(sections.get('solubility')!));

function setCompound(compound?: CalculatorCompound) {
  molePanel.setCompound(compound); solutionPanel.setCompound(compound);
  notice.textContent = compound ? `${compound.name} · exact compound mass${compound.molarMass ? ` ${compound.molarMass} g/mol` : ' unavailable; enter manually'}` : '';
}
compoundSelect.addEventListener('change', () => setCompound(compoundRecords.get(compoundSelect.value)));
mobileTopic.addEventListener('change', () => selectTopic(mobileTopic.value as TopicId));
function selectTopic(id: TopicId) {
  const topic = topics.find((item) => item.id === id); if (!topic) return;
  element<HTMLElement>('calculator-title').textContent = topic.name;
  element<HTMLElement>('calculator-description').textContent = topic.description;
  element<HTMLElement>('calculator-model').textContent = topic.model;
  for (const [key, section] of sections) section.hidden = key !== id;
  for (const [key, button] of topicButtons) button.setAttribute('aria-pressed', String(key === id));
  mobileTopic.value = id; context.hidden = id !== 'moles' && id !== 'solutions';
  if (!initialized.has(id)) { initializers.get(id)?.(); initialized.add(id); }
  // Allow bookmarking a calculator without sharing any entered quantities.
  try { history.replaceState(null, '', `#${id}`); } catch { /* Selection still works without History API. */ }
}

let transferred: CalculatorCompound | undefined;
try {
  const raw = sessionStorage.getItem(CALCULATOR_TRANSFER_KEY);
  transferred = decodeCalculatorTransfer(raw);
  sessionStorage.removeItem(CALCULATOR_TRANSFER_KEY);
  if (raw && !transferred) notice.textContent = 'Compound transfer unavailable. Select a compound or enter values manually.';
} catch { notice.textContent = 'Compound transfer unavailable in this browser. Manual entry still works.'; }
if (transferred) {
  const reviewed = compoundRecords.get(transferred.id);
  // Reuse a catalog option only for the exact identity, not a matching formula/name.
  if (reviewed && reviewed.cid === transferred.cid && reviewed.structure === transferred.structure) transferred = reviewed;
  else {
    const key = `transferred:${transferred.id}`;
    compoundRecords.set(key, transferred);
    const option = document.createElement('option'); option.value = key; option.textContent = `${transferred.name} (transferred compound)`; compoundSelect.append(option);
    compoundSelect.value = key;
  }
  if (transferred === reviewed) compoundSelect.value = transferred.id;
  setCompound(transferred);
}
function selectHashTopic() {
  const requested = location.hash.slice(1);
  selectTopic(topics.some((topic) => topic.id === requested) ? requested as TopicId : 'moles');
}
window.addEventListener('hashchange', selectHashTopic);
selectHashTopic();
