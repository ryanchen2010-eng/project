import { calculateSolubility, compareSaturation, type DissolvedIon, type SolubilityModel } from './solubility-calculator';
import { type ActivityMode, type SpectatorSpecies } from './equilibrium-calculator';

let instance = 0;
const format = (value: number) => { const rounded = Number(value.toPrecision(6)); return Number.isFinite(rounded) && (rounded !== 0 || value === 0) ? String(rounded) : String(value); };
function text<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const node = document.createElement(tag); node.textContent = value;
  if (className) node.className = className;
  return node;
}

export function mountSolubilityCalculator(host: HTMLElement): { clear(): void } {
  const prefix = `solubility-${++instance}`;
  const form = text('form', '', 'calculator-form'); form.noValidate = true;
  const grid = text('div', '', 'calc-grid');
  const result = text('div', '', 'calc-result'); result.hidden = true;
  result.setAttribute('role', 'status'); result.setAttribute('aria-live', 'polite');
  const error = text('p', '', 'calc-error'); error.hidden = true; error.setAttribute('role', 'alert');
  const conditionNote = text('p', '', 'calc-note');
  const invalidate = () => { result.replaceChildren(); result.hidden = true; error.textContent = ''; error.hidden = true; };
  const field = (parent: HTMLElement, label: string, id: string, type = 'number') => {
    const wrapper = text('div', '', 'calc-field'); const title = text('label', label); const input = text('input');
    input.type = type; input.id = `${prefix}-${id}`; input.step = 'any'; input.inputMode = type === 'number' ? 'decimal' : 'text';
    title.htmlFor = input.id; input.addEventListener('input', invalidate); input.addEventListener('change', invalidate);
    wrapper.append(title, input); parent.append(wrapper); return { input, wrapper };
  };
  const select = (parent: HTMLElement, label: string, id: string, options: [string, string][]) => {
    const wrapper = text('div', '', 'calc-field'); const title = text('label', label); const input = text('select');
    input.id = `${prefix}-${id}`; title.htmlFor = input.id;
    for (const [value, name] of options) { const option = text('option', name); option.value = value; input.append(option); }
    input.addEventListener('change', invalidate); wrapper.append(title, input); parent.append(wrapper); return input;
  };
  const mode = select(grid, 'Calculation', 'mode', [['solubility', 'Saturation solubility with common ions'], ['compare', 'Compare Qsp with Ksp']]);
  const temperature = field(grid, 'Temperature (°C)', 'temperature').input; temperature.value = '25';
  const activity = select(grid, 'Activity model', 'activity', [['ideal', 'Ideal'], ['entered', 'Entered activity coefficients']]);
  const notation = select(grid, 'Constant notation', 'constant-type', [['K', 'Ksp'], ['pK', 'pKsp = −log₁₀ Ksp']]);
  const constant = field(grid, 'Solubility constant at this temperature', 'constant').input;
  const ionsHost = text('div', '', 'calc-table');
  const ions = [1, 2].map(index => {
    const box = text('fieldset'); box.append(text('legend', `Ion ${index}`));
    const fields = text('div', '', 'calc-grid');
    const name = field(fields, `Ion ${index} name`, `ion-${index}-name`, 'text').input; name.maxLength = 100;
    const coefficient = field(fields, `Ion ${index} coefficient`, `ion-${index}-coefficient`).input; coefficient.step = '1'; coefficient.min = '1'; coefficient.max = '20';
    const charge = field(fields, `Ion ${index} charge`, `ion-${index}-charge`).input; charge.step = '1'; charge.min = '-20'; charge.max = '20';
    const concentration = field(fields, `Ion ${index} initial/current concentration`, `ion-${index}-concentration`).input; concentration.min = '0';
    const unit = select(fields, `Ion ${index} concentration unit`, `ion-${index}-unit`, [['mol/L', 'mol/L'], ['mmol/L', 'mmol/L'], ['µmol/L', 'µmol/L']]);
    const gamma = field(fields, `Ion ${index} activity coefficient γ`, `ion-${index}-gamma`); gamma.input.min = '0';
    box.append(fields); ionsHost.append(box); return { name, coefficient, charge, concentration, unit, gamma };
  });
  const spectatorsHost = text('div', '', 'calc-table');
  const spectators: { name: HTMLInputElement; charge: HTMLInputElement; concentration: HTMLInputElement;
    unit: HTMLSelectElement; gamma: { input: HTMLInputElement; wrapper: HTMLElement } }[] = [];
  let spectatorSerial = 0;
  const updateActivity = () => [...ions, ...spectators].forEach(ion => { ion.gamma.wrapper.hidden = activity.value !== 'entered'; ion.gamma.input.disabled = activity.value !== 'entered'; });
  const addSpectator = () => {
    invalidate();
    if (spectators.length >= 4) { error.textContent = 'Use at most four fixed spectator species.'; error.hidden = false; return; }
    const serial = ++spectatorSerial;
    const box = text('fieldset'); box.append(text('legend', `Fixed spectator ${serial}`));
    const fields = text('div', '', 'calc-grid');
    const name = field(fields, `Spectator ${serial} name`, `spectator-${serial}-name`, 'text').input; name.maxLength = 100;
    const charge = field(fields, `Spectator ${serial} charge`, `spectator-${serial}-charge`).input; charge.step = '1'; charge.value = '1';
    const concentration = field(fields, `Spectator ${serial} concentration`, `spectator-${serial}-concentration`).input; concentration.min = '0';
    const unit = select(fields, `Spectator ${serial} concentration unit`, `spectator-${serial}-unit`, [['mol/L', 'mol/L'], ['mmol/L', 'mmol/L'], ['µmol/L', 'µmol/L']]);
    const gamma = field(fields, `Spectator ${serial} activity coefficient γ`, `spectator-${serial}-gamma`);
    const row = { name, charge, concentration, unit, gamma }; spectators.push(row);
    const remove = text('button', 'Remove spectator'); remove.type = 'button'; remove.setAttribute('aria-label', `Remove spectator ${serial}`);
    remove.addEventListener('click', () => { spectators.splice(spectators.indexOf(row), 1); box.remove(); invalidate(); });
    box.append(fields, remove); spectatorsHost.append(box); updateActivity();
  };
  const spectatorButton = text('button', 'Add fixed spectator / counterion'); spectatorButton.type = 'button'; spectatorButton.addEventListener('click', addSpectator);
  activity.addEventListener('change', updateActivity);
  notation.addEventListener('change', () => { constant.value = ''; });
  const resetConstants = () => {
    constant.value = ''; [...ions, ...spectators].forEach(ion => { ion.gamma.input.value = ''; }); invalidate();
    conditionNote.textContent = 'Temperature changed: enter Ksp/pKsp and activity coefficients again.';
  };
  temperature.addEventListener('input', resetConstants); temperature.addEventListener('change', resetConstants);
  const actions = text('div', '', 'calc-actions'); const calculate = text('button', 'Calculate'); calculate.type = 'submit';
  const clear = text('button', 'Clear'); clear.type = 'button'; actions.append(calculate, clear);
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
  form.addEventListener('submit', event => {
    event.preventDefault(); invalidate();
    try {
      const model: SolubilityModel = {
        constant: { notation: notation.value as 'K' | 'pK', value: read(constant, 'solubility constant') },
        activityMode: activity.value as ActivityMode, temperatureC: read(temperature, 'temperature'),
        ions: ions.map(ion => ({ name: ion.name.value.trim(), coefficient: read(ion.coefficient, 'ion coefficient'),
          charge: read(ion.charge, 'ion charge'), concentration: concentrationValue(ion.concentration, ion.unit),
          ...(activity.value === 'entered' ? { activityCoefficient: read(ion.gamma.input, 'activity coefficient') } : {}),
        })) as [DissolvedIon, DissolvedIon],
        spectators: spectators.map(row => ({ name: row.name.value.trim(), charge: read(row.charge, 'spectator charge'),
          concentration: concentrationValue(row.concentration, row.unit),
          ...(activity.value === 'entered' ? { activityCoefficient: read(row.gamma.input, 'spectator activity coefficient') } : {}),
        })) as SpectatorSpecies[],
      };
      if (mode.value === 'solubility') {
        const answer = calculateSolubility(model);
        result.append(text('p', `Additional salt dissolved: ${format(answer.solubility)} mol/L (formula units)`));
        ions.forEach((ion, index) => result.append(text('p', `${ion.name.value.trim()}: ${format(answer.concentrations[index])} mol/L at saturation`)));
        for (const row of model.spectators ?? []) result.append(text('p', `${row.name}: ${format(row.concentration)} mol/L · fixed spectator`));
      } else {
        const answer = compareSaturation(model);
        result.append(text('p', `Qsp: ${format(answer.quotient)} · ${answer.status}`));
        if (answer.status === 'supersaturated') result.append(text('p', 'Precipitation is thermodynamically favored in this model; its rate is not calculated.', 'calc-note'));
      }
      result.append(text('p', `${activity.value === 'ideal' ? 'Ideal' : 'Fixed entered activity coefficients'} · ${format(model.temperatureC)} °C · 1 mol/L standard state`, 'calc-note'));
      result.hidden = false;
    } catch (caught) { error.textContent = caught instanceof Error ? caught.message : 'Calculation failed.'; error.hidden = false; }
  });
  const reset = () => {
    invalidate(); mode.value = 'solubility'; temperature.value = '25'; activity.value = 'ideal'; notation.value = 'K'; constant.value = ''; conditionNote.textContent = '';
    spectatorsHost.replaceChildren(); spectators.splice(0); spectatorSerial = 0;
    ions.forEach((ion, index) => { ion.name.value = index === 0 ? 'M⁺' : 'X⁻'; ion.coefficient.value = '1'; ion.charge.value = index === 0 ? '1' : '-1'; ion.concentration.value = '0'; ion.unit.value = 'mol/L'; ion.gamma.input.value = ''; });
    updateActivity();
  };
  clear.addEventListener('click', reset);
  const assumptions = text('details', '', 'calc-note');
  assumptions.append(text('summary', 'Model, formulas and reference'),
    text('p', 'One neutral salt MₐXᵦ(s) ⇌ a M(aq) + b X(aq), yielding exactly two ion types. Ksp = (γM[M]/1 mol/L)ᵃ(γX[X]/1 mol/L)ᵇ. With common ions, [M] = [M]initial + a·s and [X] = [X]initial + b·s. Excess solid is assumed present, at fixed volume.'),
    text('p', 'Ideal mode uses γ = 1. Entered mode requires fixed activity coefficients for both salt ions and every spectator row. Spectators stay at their entered concentrations and are outside the Ksp expression. Supply the constant and coefficients for the displayed temperature and concentration standard state. No automatic corrections or constants lookup.'),
    text('p', 'No acid–base speciation, complexation, competing salts, precipitation quantity, experimental accuracy, or laboratory-safety assessment. Saturation comparisons use |ln(Qsp/Ksp)| ≤ 10⁻¹⁰.'));
  const reference = text('a', 'Solubility reference ↗'); reference.href = 'https://openstax.org/books/chemistry-2e/pages/15-1-precipitation-and-dissolution'; reference.target = '_blank'; reference.rel = 'noopener noreferrer'; assumptions.append(reference);
  form.append(grid, conditionNote, ionsHost, spectatorsHost, spectatorButton, actions, error);
  host.append(text('p', 'Supply Ksp and common-ion concentrations for one salt.', 'calc-note'), form, result, assumptions);
  reset(); return { clear: reset };
}
