import './reaction-calculator.css';
import { ReactionCalculatorPanel } from './reaction-calculator-panel';
import { copyCalculationContext, validateStoichiometry, type ReactionStoichiometry, type StoichiometricSpecies } from './reaction-calculator';

type ReviewedReaction = { id: string; name: string; family?: string; stoichiometry: ReactionStoichiometry };
let instance = 0;

const shortText = (value: unknown, maximum = 200): value is string =>
  typeof value === 'string' && Boolean(value.trim()) && value.length <= maximum;

function species(value: unknown): StoichiometricSpecies | undefined {
  if (!value || typeof value !== 'object') return;
  const item = value as Record<string, unknown>;
  if (!shortText(item.name) || !shortText(item.formula)
    || typeof item.molarMass !== 'number' || !Number.isFinite(item.molarMass) || item.molarMass <= 0
    || typeof item.coefficient !== 'number' || !Number.isSafeInteger(item.coefficient) || item.coefficient <= 0) return;
  return { name: item.name, formula: item.formula, molarMass: item.molarMass, coefficient: item.coefficient };
}

/** Accept calculation metadata only from the server's balanced, supported catalog. */
export function reviewedCalculatorReactions(payload: unknown): ReviewedReaction[] {
  if (!payload || typeof payload !== 'object') throw new Error('The reaction catalog is unavailable.');
  const reactions = (payload as Record<string, unknown>).reactions;
  if (!Array.isArray(reactions) || reactions.length > 1000) throw new Error('The reaction catalog is unavailable.');
  const reviewed: ReviewedReaction[] = [];
  const ids = new Set<string>();
  for (const value of reactions) {
    if (!value || typeof value !== 'object') continue;
    const item = value as Record<string, unknown>;
    if (!shortText(item.id) || !shortText(item.name) || ids.has(item.id)
      || !item.stoichiometry || typeof item.stoichiometry !== 'object') continue;
    const basis = item.stoichiometry as Record<string, unknown>;
    if (basis.balanced !== true || !Array.isArray(basis.reactants) || !basis.reactants.length || basis.reactants.length > 2) continue;
    const product = species(basis.product);
    if (!product) continue;
    const reactants: ReactionStoichiometry['reactants'] = [];
    for (const raw of basis.reactants) {
      const normalized = species(raw);
      const slot = raw && typeof raw === 'object' ? (raw as Record<string, unknown>).inputSlot : undefined;
      if (!normalized || (slot !== 0 && slot !== 1)) break;
      reactants.push({ ...normalized, inputSlot: slot });
    }
    if (reactants.length !== basis.reactants.length) continue;
    const notes = basis.notes ?? [];
    const excluded = basis.excludedInputs ?? [];
    if (!Array.isArray(notes) || notes.length > 25 || notes.some((note) => !shortText(note, 5000))
      || !Array.isArray(excluded) || excluded.length > 2) continue;
    const excludedInputs: ReactionStoichiometry['excludedInputs'] = [];
    const slots = new Set(reactants.map((reactant) => reactant.inputSlot));
    for (const raw of excluded) {
      if (!raw || typeof raw !== 'object') break;
      const role = raw as Record<string, unknown>;
      if ((role.inputSlot !== 0 && role.inputSlot !== 1) || slots.has(role.inputSlot)
        || !shortText(role.name) || !shortText(role.reason, 5000)) break;
      slots.add(role.inputSlot);
      excludedInputs.push({ inputSlot: role.inputSlot, name: role.name, reason: role.reason });
    }
    if (excludedInputs.length !== excluded.length) continue;
    const stoichiometry: ReactionStoichiometry = { balanced: true, reactants, product,
      notes: [...notes] as string[], excludedInputs };
    if (basis.context !== undefined) {
      try { stoichiometry.context = copyCalculationContext(basis.context); } catch { continue; }
    }
    try { validateStoichiometry(stoichiometry); } catch { continue; }
    ids.add(item.id);
    reviewed.push({ id: item.id, name: item.name,
      family: shortText(item.family) ? item.family : undefined, stoichiometry });
  }
  return reviewed;
}

function text<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}

/** Reaction arithmetic does not require the 3D viewer or a generated product. */
export function mountReactionAmounts(host: HTMLElement): { clear(): void } {
  const prefix = host.id || `reaction-amounts-${++instance}`;
  const controls = text('div', '', 'reaction-amounts-controls');
  const label = text('label', 'Supported balanced reaction');
  const select = text('select');
  select.id = `${prefix}-reaction`;
  label.htmlFor = select.id;
  const status = text('p', '', 'reaction-amounts-status');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.id = `${prefix}-status`;
  select.setAttribute('aria-describedby', status.id);
  const retry = text('button', 'Retry reaction catalog', 'reaction-amounts-retry');
  retry.type = 'button';
  retry.hidden = true;
  const context = text('p', '', 'reaction-amounts-context');
  context.hidden = true;
  const clearButton = text('button', 'Clear');
  clearButton.type = 'button';
  clearButton.hidden = true;
  const details = text('details');
  details.id = `${prefix}-calculator`;
  details.open = true;
  const calculator = new ReactionCalculatorPanel(details);
  controls.append(label, select);
  host.append(text('p', 'Choose a supported pathway to calculate theoretical amounts. Other calculators work without the chemistry service.', 'reaction-amounts-caption'),
    controls, status, retry, context, details, clearButton);
  let available: ReviewedReaction[] = [];
  let revision = 0;
  let controller: AbortController | undefined;

  const placeholder = () => {
    const option = text('option', 'Choose a reaction');
    option.value = '';
    select.replaceChildren(option);
    select.value = '';
  };
  const clear = () => {
    select.value = '';
    context.textContent = '';
    context.hidden = true;
    clearButton.hidden = true;
    calculator.setReaction();
  };
  clearButton.addEventListener('click', clear);
  const showSelection = () => {
    const selected = available.find((reaction) => reaction.id === select.value);
    calculator.setReaction(selected?.stoichiometry);
    context.hidden = !selected;
    clearButton.hidden = !selected;
    context.textContent = selected ? `${selected.stoichiometry.reactants.map((reactant) => reactant.name).join(' + ')} → ${selected.stoichiometry.product.name}` : '';
    details.open = true;
  };
  select.addEventListener('change', showSelection);
  const load = async () => {
    const requestRevision = ++revision;
    controller?.abort();
    const requestController = new AbortController();
    controller = requestController;
    const timeout = setTimeout(() => requestController.abort(), 15_000);
    clear();
    available = [];
    placeholder();
    select.disabled = true;
    retry.hidden = true;
    retry.disabled = true;
    status.setAttribute('role', 'status');
    status.textContent = 'Loading supported reactions…';
    try {
      const response = await fetch('/api/reactions/catalog', { signal: requestController.signal });
      if (!response.ok) throw new Error('The reaction catalog is unavailable.');
      const payload: unknown = await response.json();
      if (requestRevision !== revision) return;
      const reviewed = reviewedCalculatorReactions(payload);
      if (!reviewed.length) throw new Error('No verified balanced reactions are available.');
      available = reviewed;
      for (const reaction of available) {
        const identities = reaction.stoichiometry.reactants.map((reactant) => reactant.name).join(' + ');
        const option = text('option', `${reaction.name} · ${identities} → ${reaction.stoichiometry.product.name}`);
        option.value = reaction.id;
        select.append(option);
      }
      select.disabled = false;
      status.textContent = 'Amounts assume complete conversion, not actual yield.';
    } catch {
      if (requestRevision !== revision) return;
      available = [];
      placeholder();
      select.disabled = true;
      status.setAttribute('role', 'alert');
      status.textContent = 'Reaction catalog unavailable. Start the chemistry service and retry. Other calculators still work.';
      retry.hidden = false;
    } finally {
      clearTimeout(timeout);
      if (requestRevision === revision) {
        controller = undefined;
        retry.disabled = false;
      }
    }
  };
  retry.addEventListener('click', () => { void load(); });
  void load();
  return { clear };
}
