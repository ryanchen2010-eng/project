import { calculateQuotient, compareQuotient, solveEquilibrium,
  type ActivityMode, type EquilibriumModel, type EquilibriumSpecies, type Quotient, type SpectatorSpecies } from './equilibrium-calculator';

type Mode = 'q' | 'k' | 'compare' | 'solve';
type SpeciesFields = {
  box: HTMLFieldSetElement;
  name: HTMLInputElement;
  side: HTMLSelectElement;
  coefficient: HTMLInputElement;
  phase: HTMLSelectElement;
  concentration: HTMLInputElement;
  unit: HTMLSelectElement;
  charge: HTMLInputElement;
  gamma: HTMLInputElement;
  gammaField: HTMLElement;
  concentrationLabel: HTMLLabelElement;
};
type SpectatorFields = { box: HTMLFieldSetElement; name: HTMLInputElement; charge: HTMLInputElement;
  concentration: HTMLInputElement; unit: HTMLSelectElement; gamma: HTMLInputElement; gammaField: HTMLElement };
let instance = 0;
const format = (value: number) => { const rounded = Number(value.toPrecision(6)); return Number.isFinite(rounded) && (rounded !== 0 || value === 0) ? String(rounded) : String(value); };
function text<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const node = document.createElement(tag);
  node.textContent = value;
  if (className) node.className = className;
  return node;
}

export function mountEquilibriumCalculator(host: HTMLElement): { clear(): void } {
  const prefix = `equilibrium-${++instance}`;
  const form = text('form', '', 'calculator-form');
  form.noValidate = true;
  const controls = text('div', '', 'calc-grid');
  const rowsHost = text('div', '', 'calc-table');
  const rows: SpeciesFields[] = [];
  const spectatorsHost = text('div', '', 'calc-table');
  const spectators: SpectatorFields[] = [];
  const result = text('div', '', 'calc-result');
  result.hidden = true;
  result.setAttribute('role', 'status');
  result.setAttribute('aria-live', 'polite');
  const error = text('p', '', 'calc-error');
  error.hidden = true;
  error.setAttribute('role', 'alert');
  const conditionNote = text('p', '', 'calc-note');
  let rowSerial = 0;
  let spectatorSerial = 0;
  const invalidate = () => { result.replaceChildren(); result.hidden = true; error.textContent = ''; error.hidden = true; };
  const fail = (message: string) => { invalidate(); error.textContent = message; error.hidden = false; };
  const field = (parent: HTMLElement, label: string, id: string, type = 'number') => {
    const wrapper = text('div', '', 'calc-field');
    const title = text('label', label);
    const input = text('input');
    input.type = type;
    input.id = `${prefix}-${id}`;
    input.step = 'any';
    input.inputMode = type === 'number' ? 'decimal' : 'text';
    title.htmlFor = input.id;
    input.addEventListener('input', invalidate);
    input.addEventListener('change', invalidate);
    wrapper.append(title, input);
    parent.append(wrapper);
    return { input, wrapper, title };
  };
  const select = (parent: HTMLElement, label: string, id: string, options: [string, string][]) => {
    const wrapper = text('div', '', 'calc-field');
    const title = text('label', label);
    const input = text('select');
    input.id = `${prefix}-${id}`;
    title.htmlFor = input.id;
    for (const [value, name] of options) {
      const option = text('option', name); option.value = value; input.append(option);
    }
    input.addEventListener('change', invalidate);
    wrapper.append(title, input); parent.append(wrapper);
    return { input, wrapper };
  };
  const mode = select(controls, 'Calculation', 'mode', [
    ['q', 'Current concentrations → Q'], ['k', 'Equilibrium concentrations → K'],
    ['compare', 'Compare Q with K'], ['solve', 'Initial concentrations → equilibrium'],
  ]).input;
  const temperature = field(controls, 'Temperature (°C)', 'temperature').input;
  temperature.value = '25';
  const activity = select(controls, 'Activity model', 'activity', [['ideal', 'Ideal'], ['entered', 'Entered activity coefficients']]).input;
  const constantType = select(controls, 'Constant notation', 'constant-type', [['K', 'K'], ['pK', 'pK = −log₁₀ K']]);
  const constant = field(controls, 'Equilibrium constant at this temperature', 'constant');
  const confirmRow = text('div', '', 'calc-field');
  const confirmLabel = text('label', 'I confirm this single equation is atom- and charge-balanced.');
  const confirm = text('input');
  confirm.id = `${prefix}-balanced`; confirm.type = 'checkbox';
  confirmLabel.htmlFor = confirm.id;
  confirm.addEventListener('change', invalidate);
  confirmRow.append(confirm, confirmLabel);

  const updateRows = () => {
    const isSolve = mode.value === 'solve';
    const isEntered = activity.value === 'entered';
    rows.forEach((row, index) => {
      row.concentrationLabel.textContent = `${isSolve ? 'Initial' : mode.value === 'k' ? 'Equilibrium' : 'Current'} concentration · species ${index + 1}`;
      const pure = row.phase.value !== 'aq';
      row.concentration.disabled = pure;
      row.unit.disabled = pure;
      row.charge.disabled = pure;
      if (pure) row.charge.value = '0';
      row.gamma.disabled = pure || !isEntered;
      row.gammaField.hidden = pure || !isEntered;
    });
    spectators.forEach(row => { row.gamma.disabled = !isEntered; row.gammaField.hidden = !isEntered; });
    const needsK = mode.value === 'compare' || isSolve;
    constant.wrapper.hidden = !needsK;
    constantType.wrapper.hidden = !needsK;
  };
  const addRow = (side: 'reactant' | 'product', name = '') => {
    if (rows.length >= 12) { fail('This single-reaction model supports at most 12 species.'); return; }
    const serial = ++rowSerial;
    const box = text('fieldset');
    box.append(text('legend', `Species ${serial}`));
    const grid = text('div', '', 'calc-grid');
    const nameField = field(grid, `Name · species ${serial}`, `row-${serial}-name`, 'text').input;
    nameField.maxLength = 100; nameField.value = name;
    const sideField = select(grid, `Side · species ${serial}`, `row-${serial}-side`, [['reactant', 'Reactant'], ['product', 'Product']]).input;
    sideField.value = side;
    const coefficient = field(grid, `Coefficient · species ${serial}`, `row-${serial}-coefficient`).input;
    coefficient.value = '1'; coefficient.min = '1'; coefficient.max = '20'; coefficient.step = '1';
    const phase = select(grid, `Phase · species ${serial}`, `row-${serial}-phase`, [['aq', 'Dissolved (aq)'], ['solid', 'Pure solid'], ['liquid', 'Pure liquid']]).input;
    const concentration = field(grid, `Concentration · species ${serial}`, `row-${serial}-concentration`);
    concentration.input.min = '0';
    const unit = select(grid, `Concentration unit · species ${serial}`, `row-${serial}-unit`, [['mol/L', 'mol/L'], ['mmol/L', 'mmol/L'], ['µmol/L', 'µmol/L']]).input;
    const charge = field(grid, `Charge · species ${serial}`, `row-${serial}-charge`).input;
    charge.value = '0'; charge.step = '1'; charge.min = '-20'; charge.max = '20';
    const gamma = field(grid, `Activity coefficient γ · species ${serial}`, `row-${serial}-gamma`);
    gamma.input.min = '0';
    const remove = text('button', 'Remove species'); remove.type = 'button';
    remove.setAttribute('aria-label', `Remove species ${serial}`);
    const row = { box, name: nameField, side: sideField, coefficient, phase,
      concentration: concentration.input, unit, charge, gamma: gamma.input,
      gammaField: gamma.wrapper, concentrationLabel: concentration.title };
    remove.addEventListener('click', () => {
      if (rows.length <= 2) { fail('Keep at least two species.'); return; }
      rows.splice(rows.indexOf(row), 1); box.remove(); invalidate(); updateRows();
    });
    phase.addEventListener('change', updateRows);
    box.append(grid, remove); rowsHost.append(box); rows.push(row); updateRows(); invalidate();
  };
  const add = text('button', 'Add species'); add.type = 'button'; add.addEventListener('click', () => addRow('product'));
  const addSpectator = () => {
    if (spectators.length >= 4) { fail('Use at most four fixed spectator species.'); return; }
    const serial = ++spectatorSerial;
    const box = text('fieldset'); box.append(text('legend', `Fixed spectator ${serial}`));
    const grid = text('div', '', 'calc-grid');
    const name = field(grid, `Spectator ${serial} name`, `spectator-${serial}-name`, 'text').input; name.maxLength = 100;
    const charge = field(grid, `Spectator ${serial} charge`, `spectator-${serial}-charge`).input; charge.step = '1'; charge.value = '1';
    const concentration = field(grid, `Spectator ${serial} concentration`, `spectator-${serial}-concentration`).input; concentration.min = '0';
    const unit = select(grid, `Spectator ${serial} concentration unit`, `spectator-${serial}-unit`, [['mol/L', 'mol/L'], ['mmol/L', 'mmol/L'], ['µmol/L', 'µmol/L']]).input;
    const gamma = field(grid, `Spectator ${serial} activity coefficient γ`, `spectator-${serial}-gamma`);
    const row = { box, name, charge, concentration, unit, gamma: gamma.input, gammaField: gamma.wrapper };
    const remove = text('button', 'Remove spectator'); remove.type = 'button'; remove.setAttribute('aria-label', `Remove spectator ${serial}`);
    remove.addEventListener('click', () => { spectators.splice(spectators.indexOf(row), 1); box.remove(); invalidate(); });
    box.append(grid, remove); spectatorsHost.append(box); spectators.push(row); updateRows(); invalidate();
  };
  const spectatorButton = text('button', 'Add fixed spectator / counterion'); spectatorButton.type = 'button'; spectatorButton.addEventListener('click', addSpectator);
  const actions = text('div', '', 'calc-actions');
  const calculate = text('button', 'Calculate'); calculate.type = 'submit';
  const clear = text('button', 'Clear'); clear.type = 'button';
  actions.append(calculate, clear);
  const read = (input: HTMLInputElement, label: string) => {
    if (!input.value.trim() || !Number.isFinite(input.valueAsNumber)) throw new Error(`Enter a finite ${label}.`);
    return input.valueAsNumber;
  };
  const concentrationValue = (input: HTMLInputElement, unit: HTMLSelectElement) => {
    if (!['mol/L', 'mmol/L', 'µmol/L'].includes(unit.value)) throw new Error('Choose a supported concentration unit.');
    const entered = read(input, 'concentration');
    const value = entered * (unit.value === 'mmol/L' ? 1e-3 : unit.value === 'µmol/L' ? 1e-6 : 1);
    if (!Number.isFinite(value) || (entered !== 0 && value === 0)) throw new Error('Concentration conversion is outside the supported numeric range.');
    return value;
  };
  const quotientText = (q: Quotient) => q.kind === 'undefined' ? `Undefined: ${q.reason}`
    : q.kind === 'infinite' ? `Undefined finite quotient (zero denominator). ${q.reason}`
      : format(q.value);
  form.addEventListener('submit', event => {
    event.preventDefault(); invalidate();
    try {
      const model: EquilibriumModel = {
        activityMode: activity.value as ActivityMode, temperatureC: read(temperature, 'temperature'),
        balancedConfirmed: confirm.checked,
        species: rows.map(row => ({
          name: row.name.value.trim(), side: row.side.value as EquilibriumSpecies['side'],
          phase: row.phase.value as EquilibriumSpecies['phase'], coefficient: read(row.coefficient, 'coefficient'),
          concentration: row.phase.value !== 'aq' ? 0 : concentrationValue(row.concentration, row.unit),
          charge: row.phase.value !== 'aq' ? 0 : read(row.charge, 'species charge'),
          ...(activity.value === 'entered' && row.phase.value === 'aq' ? { activityCoefficient: read(row.gamma, 'activity coefficient') } : {}),
        })),
        spectators: spectators.map(row => ({ name: row.name.value.trim(), charge: read(row.charge, 'spectator charge'),
          concentration: concentrationValue(row.concentration, row.unit),
          ...(activity.value === 'entered' ? { activityCoefficient: read(row.gamma, 'spectator activity coefficient') } : {}),
        })) as SpectatorSpecies[],
      };
      const selectedMode = mode.value as Mode;
      if (selectedMode === 'solve') {
        const answer = solveEquilibrium(model, { notation: constantType.input.value as 'K' | 'pK', value: read(constant.input, 'equilibrium constant') });
        result.append(text('p', `Equilibrium extent: ${format(answer.extent)} mol/L (forward positive)`));
        for (const row of answer.concentrations) result.append(text('p', `${row.name}: ${row.phase === 'aq' ? `${format(row.concentration!)} mol/L` : 'pure phase · activity 1'}`));
        for (const row of model.spectators ?? []) result.append(text('p', `${row.name}: ${format(row.concentration)} mol/L · fixed spectator`));
        result.append(text('p', `Final Q: ${quotientText(answer.quotient)}`));
      } else {
        const q = calculateQuotient(model);
        if (selectedMode === 'k' && (q.kind === 'undefined' || q.kind === 'infinite' || q.kind === 'zero')) {
          throw new Error('These concentrations cannot define a positive finite equilibrium constant.');
        }
        result.append(text('p', `${selectedMode === 'k' ? 'K (entered equilibrium concentrations)' : 'Q'}: ${quotientText(q)}`));
        if (selectedMode === 'compare') {
          const direction = compareQuotient(q, { notation: constantType.input.value as 'K' | 'pK', value: read(constant.input, 'equilibrium constant') });
          result.append(text('p', direction === 'equilibrium' ? 'Q = K within numerical tolerance.' : direction === 'forward' ? 'Q < K · forward thermodynamic tendency.' : 'Q > K · reverse thermodynamic tendency.'));
        }
      }
      result.append(text('p', `${activity.value === 'ideal' ? 'Ideal' : 'Fixed entered activity coefficients'} · ${format(model.temperatureC)} °C · 1 mol/L standard state`, 'calc-note'));
      result.hidden = false;
    } catch (caught) { fail(caught instanceof Error ? caught.message : 'Calculation failed.'); }
  });
  mode.addEventListener('change', updateRows);
  activity.addEventListener('change', updateRows);
  constantType.input.addEventListener('change', () => { constant.input.value = ''; });
  const resetConstants = () => {
    constant.input.value = ''; rows.forEach(row => { row.gamma.value = ''; });
    spectators.forEach(row => { row.gamma.value = ''; });
    conditionNote.textContent = 'Temperature changed: enter the constant and any activity coefficients again.';
    invalidate();
  };
  temperature.addEventListener('input', resetConstants);
  temperature.addEventListener('change', resetConstants);
  const reset = () => {
    invalidate(); mode.value = 'q'; activity.value = 'ideal'; temperature.value = '25';
    constantType.input.value = 'K'; constant.input.value = ''; confirm.checked = false;
    conditionNote.textContent = ''; rowsHost.replaceChildren(); rows.splice(0); rowSerial = 0;
    spectatorsHost.replaceChildren(); spectators.splice(0); spectatorSerial = 0;
    addRow('reactant', 'A'); addRow('product', 'B'); updateRows();
  };
  clear.addEventListener('click', reset);
  const assumptions = text('details', '', 'calc-note');
  assumptions.append(text('summary', 'Model, formulas and reference'),
    text('p', 'One balanced reversible reaction at fixed volume. Q = ∏(γᵢcᵢ / 1 mol/L)^νᵢ and cᵢ = cᵢ,initial + νᵢx. Concentrations are nonnegative; zero values are never replaced. Pure solids/liquids have activity 1 and must remain present throughout.'),
    text('p', 'Ideal mode uses γ = 1. Entered mode requires coefficients for every dissolved row, including fixed spectators, and holds them fixed. Supply constants and coefficients for the displayed temperature and concentration standard state; no temperature correction is estimated. Spectator concentrations stay unchanged and are excluded from Q. Names are not checked against chemical identities; atom balance is your confirmation.'),
    text('p', 'No gases, coupled equilibria, changing volume, reaction speed, experimental accuracy, or laboratory-safety assessment. Numerical equality uses |ln(Q/K)| ≤ 10⁻¹⁰.'));
  const reference = text('a', 'Equilibrium reference ↗');
  reference.href = 'https://openstax.org/books/chemistry-2e/pages/13-2-equilibrium-constants'; reference.target = '_blank'; reference.rel = 'noopener noreferrer';
  assumptions.append(reference);
  form.append(controls, conditionNote, confirmRow, rowsHost, add, spectatorsHost, spectatorButton, actions, error);
  host.append(text('p', 'Enter one balanced equation. Constants are supplied by you.', 'calc-note'), form, result, assumptions);
  reset();
  return { clear: reset };
}
