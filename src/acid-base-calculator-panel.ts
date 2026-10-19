import { calculateAcidBase, type AcidBaseInput, type AcidBaseModel, type ConstantInput } from './acid-base-calculator';

type NumberField = { input: HTMLInputElement; unit?: HTMLSelectElement };
const models: [AcidBaseModel, string][] = [
  ['strong-acid', 'Strong monoprotic acid'], ['strong-base', 'Strong monoprotic base'],
  ['weak-acid', 'Weak monoprotic acid'], ['weak-base', 'Weak monoprotic base'],
  ['buffer', 'Conjugate-pair buffer'], ['polyprotic', 'Polyprotic acid family'],
];
let instances = 0;
const format = (value: number) => {
  const rounded = Number(value.toPrecision(6));
  return Number.isFinite(rounded) && (value === 0 || rounded !== 0) ? String(rounded) : String(value);
};
function node<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}

/** Browser-local pH calculation for one defined aqueous family, not a general mixture solver. */
export function mountAcidBaseCalculator(host: HTMLElement): { clear(): void } {
  const prefix = `${host.id || 'acid-base'}-${++instances}`;
  const form = node('form', '', 'calculator-form');
  form.noValidate = true;
  const conditions = node('div', '', 'calc-grid');
  const parameters = node('div', '', 'calc-grid');
  const output = node('div', '', 'calc-result');
  output.hidden = true;
  output.setAttribute('role', 'status');
  output.setAttribute('aria-live', 'polite');
  const error = node('p', '', 'calc-error');
  error.id = `${prefix}-error`;
  error.hidden = true;
  error.setAttribute('role', 'alert');
  const fields = new Map<string, NumberField>();
  const constantFields: NumberField[] = [];
  const gammaFields: NumberField[] = [];
  let bufferKind: 'acid' | 'base' = 'acid';
  let steps: 1 | 2 | 3 = 2;

  function invalidate() {
    output.replaceChildren();
    output.hidden = true;
    error.textContent = '';
    error.hidden = true;
  }
  function selectField(key: string, label: string, options: [string, string][], parent: HTMLElement) {
    const row = node('div', '', 'calc-field');
    const title = node('label', label);
    const select = node('select');
    select.id = `${prefix}-${key}`;
    title.htmlFor = select.id;
    for (const [value, text] of options) {
      const option = node('option', text);
      option.value = value;
      select.append(option);
    }
    select.addEventListener('change', invalidate);
    row.append(title, select);
    parent.append(row);
    return select;
  }
  function numberField(key: string, label: string, parent: HTMLElement, units?: [string, string][], placeholder = 'Value') {
    const row = node('div', '', 'calc-field');
    const title = node('label', label);
    const input = node('input');
    input.type = 'number';
    input.inputMode = 'decimal';
    input.step = 'any';
    input.required = true;
    input.id = `${prefix}-${key}`;
    input.placeholder = placeholder;
    title.htmlFor = input.id;
    const controls = node('div', '', 'calc-quantity');
    controls.append(input);
    const unit = units ? node('select') : undefined;
    if (unit) {
      unit.setAttribute('aria-label', `Unit or notation for ${label}`);
      for (const [value, text] of units!) {
        const option = node('option', text);
        option.value = value;
        unit.append(option);
      }
      unit.addEventListener('change', () => {
        // K and pK are different representations, not interchangeable numeric units.
        if (key === 'kw' || key.startsWith('constant-')) input.value = '';
        invalidate();
      });
      controls.append(unit);
    }
    input.addEventListener('input', invalidate);
    row.append(title, controls);
    parent.append(row);
    const field = { input, unit };
    fields.set(key, field);
    return field;
  }
  const model = selectField('model', 'Acid–base model', models, conditions);
  const activity = selectField('activity', 'Activity mode', [['ideal', 'Ideal'], ['entered', 'Entered activity coefficients']], conditions);
  const temperature = numberField('temperature', 'Temperature (°C)', conditions);
  temperature.input.value = '25';
  const kw = numberField('kw', 'Water constant (Kw)', conditions, [['K', 'K'], ['pK', 'pK']], 'Enter Kw for this temperature');
  constantFields.push(kw);
  const modeNote = node('p', '', 'calc-note');
  const units: [string, string][] = [['mol/L', 'mol/L'], ['mmol/L', 'mmol/L'], ['µmol/L', 'µmol/L']];

  function renderParameters() {
    invalidate();
    parameters.replaceChildren();
    for (const key of [...fields.keys()]) if (!['temperature', 'kw'].includes(key)) fields.delete(key);
    constantFields.splice(1);
    gammaFields.splice(0);
    const selected = model.value as AcidBaseModel;
    let familyNames: string[] = [];
    let counterName: string | undefined;
    let constantName: string | undefined;
    let constantCount = 1;
    if (selected === 'buffer') {
      const pair = selectField('buffer-kind', 'Conjugate pair', [['acid', 'HA / A−'], ['base', 'BH+ / B']], parameters);
      pair.value = bufferKind;
      pair.addEventListener('change', () => { bufferKind = pair.value as 'acid' | 'base'; renderParameters(); });
      familyNames = bufferKind === 'acid' ? ['HA', 'A−'] : ['BH+', 'B'];
      constantName = bufferKind === 'acid' ? 'Ka' : 'Kb';
      counterName = bufferKind === 'acid' ? 'M+ spectator' : 'X− spectator';
      numberField('acid-concentration', `Initial ${familyNames[0]} concentration`, parameters, units);
      numberField('base-concentration', `Initial ${familyNames[1]} concentration`, parameters, units);
      modeNote.textContent = bufferKind === 'acid' ? 'One HA / monovalent A− salt pair; no other added acids or bases.' : 'One B / monovalent BH+ salt pair; no other added acids or bases.';
    } else if (selected === 'polyprotic') {
      const count = selectField('steps', 'Dissociation steps', [['1', '1'], ['2', '2'], ['3', '3']], parameters);
      count.value = String(steps);
      count.addEventListener('change', () => { steps = Number(count.value) as 1 | 2 | 3; renderParameters(); });
      familyNames = steps === 1 ? ['HA', 'A−'] : steps === 2 ? ['H₂A', 'HA−', 'A²−'] : ['H₃A', 'H₂A−', 'HA²−', 'A³−'];
      counterName = 'M+ spectator';
      constantName = 'Ka';
      constantCount = steps;
      numberField('concentration', 'Total acid-family concentration', parameters, units);
      const counter = numberField('counter-concentration', 'Monovalent spectator cation concentration', parameters, units);
      counter.input.value = '0';
      modeNote.textContent = `One neutral ${familyNames[0]} family. M+ represents salt/base equivalents (0 to ${steps} × total family concentration).`;
    } else {
      numberField('concentration', 'Analytical concentration', parameters, units);
      if (selected === 'weak-acid' || selected === 'weak-base') {
        familyNames = selected === 'weak-acid' ? ['HA', 'A−'] : ['BH+', 'B'];
        constantName = selected === 'weak-acid' ? 'Ka' : 'Kb';
        modeNote.textContent = selected === 'weak-acid' ? 'One neutral monoprotic weak acid HA.' : 'One neutral monoprotic weak base B.';
      } else {
        counterName = selected === 'strong-acid' ? 'X− spectator' : 'M+ spectator';
        modeNote.textContent = selected === 'strong-acid' ? 'Complete dissociation of a monoprotic acid HX; one monovalent spectator anion.' : 'Complete dissociation of a monoprotic base MOH; one monovalent spectator cation.';
      }
    }
    if (constantName) for (let i = 0; i < constantCount; i++) {
      const field = numberField(`constant-${i}`, `${constantName}${constantCount > 1 ? i + 1 : ''}`, parameters, [['K', 'K'], ['pK', 'pK']]);
      constantFields.push(field);
    }
    if (activity.value === 'entered') {
      for (const [key, label] of [['hydrogen', 'H+'], ['hydroxide', 'OH−']] as const) {
        gammaFields.push(numberField(`gamma-${key}`, `γ(${label})`, parameters));
      }
      familyNames.forEach((name, i) => gammaFields.push(numberField(`gamma-family-${i}`, `γ(${name})`, parameters)));
      if (counterName) gammaFields.push(numberField('gamma-counter-0', `γ(${counterName})`, parameters));
      modeNote.textContent += ' Enter γ for every shown species, including neutral forms and spectators.';
    }
  }
  function clearConstants() {
    for (const field of [...constantFields, ...gammaFields]) field.input.value = '';
    invalidate();
  }
  temperature.input.addEventListener('input', clearConstants);
  temperature.input.addEventListener('change', clearConstants);
  model.addEventListener('change', () => { kw.input.value = ''; renderParameters(); });
  activity.addEventListener('change', renderParameters);

  function number(key: string, label: string) {
    const field = fields.get(key);
    if (!field || !field.input.value.trim()) throw new Error(`Enter ${label}.`);
    const value = Number(field.input.value);
    if (!Number.isFinite(value)) throw new Error(`${label} must be finite.`);
    return value;
  }
  function amount(key: string, label: string) {
    const field = fields.get(key)!;
    const scale = field.unit!.value === 'mol/L' ? 1 : field.unit!.value === 'mmol/L' ? 1e-3 : field.unit!.value === 'µmol/L' ? 1e-6 : NaN;
    const value = number(key, label) * scale;
    if (!Number.isFinite(value) || (number(key, label) !== 0 && value === 0)) throw new Error(`${label} is outside the numeric range.`);
    return value;
  }
  function constant(key: string, label: string): ConstantInput {
    return { value: number(key, label), notation: fields.get(key)!.unit!.value as 'K' | 'pK' };
  }
  function calculate() {
    invalidate();
    try {
      const selected = model.value as AcidBaseModel;
      const familyCount = selected === 'strong-acid' || selected === 'strong-base' ? 0 : selected === 'polyprotic' ? steps + 1 : 2;
      const hasCounter = selected === 'strong-acid' || selected === 'strong-base' || selected === 'buffer' || selected === 'polyprotic';
      const input: AcidBaseInput = {
        model: selected, temperatureC: number('temperature', 'temperature'), kw: constant('kw', 'Kw'),
        activities: activity.value === 'ideal' ? { mode: 'ideal' } : {
          mode: 'entered', hydrogen: number('gamma-hydrogen', 'γ(H+)'), hydroxide: number('gamma-hydroxide', 'γ(OH−)'),
          family: Array.from({ length: familyCount }, (_, i) => number(`gamma-family-${i}`, `family γ${i + 1}`)),
          counterions: hasCounter ? [number('gamma-counter-0', 'spectator γ')] : [],
        },
      };
      if (selected === 'buffer') {
        input.bufferKind = bufferKind;
        input.acidConcentration = amount('acid-concentration', 'initial acid-form concentration');
        input.baseConcentration = amount('base-concentration', 'initial base-form concentration');
      } else input.concentration = amount('concentration', 'analytical concentration');
      if (selected === 'polyprotic') {
        input.steps = steps;
        input.counterionConcentration = amount('counter-concentration', 'spectator cation concentration');
      }
      if (familyCount > 0) input.constants = Array.from({ length: selected === 'polyprotic' ? steps : 1 }, (_, i) => constant(`constant-${i}`, `dissociation constant ${i + 1}`));
      const result = calculateAcidBase(input);
      const facts = node('div', '', 'calc-grid');
      const fact = (label: string, value: string) => {
        const row = node('div');
        row.append(node('span', label), node('strong', value));
        facts.append(row);
      };
      fact('pH', format(result.pH));
      fact('pOH', format(result.pOH));
      output.append(facts, node('p', `${result.activityMode === 'ideal' ? 'Ideal model' : 'Fixed entered γ model'} · ${format(result.temperatureC)} °C · water, charge and family mass balances checked.`, 'calc-note'));
      const table = node('table', '', 'calc-table');
      const heading = node('tr');
      heading.append(node('th', 'Species'), node('th', 'mol/L'));
      const head = node('thead');
      head.append(heading);
      const body = node('tbody');
      for (const species of result.species) {
        const row = node('tr');
        row.append(node('td', species.name), node('td', format(species.concentration)));
        body.append(row);
      }
      table.append(head, body);
      output.append(table);
      output.hidden = false;
    } catch (caught) {
      error.textContent = caught instanceof Error ? caught.message : 'The acid–base calculation could not be completed.';
      error.hidden = false;
    }
  }
  form.addEventListener('submit', (event) => { event.preventDefault(); calculate(); });
  const actions = node('div', '', 'calc-actions');
  const submit = node('button', 'Calculate');
  submit.type = 'submit';
  const reset = node('button', 'Clear');
  reset.type = 'button';
  function clear() {
    temperature.input.value = '25';
    kw.input.value = '';
    kw.unit!.value = 'K';
    renderParameters();
  }
  reset.addEventListener('click', clear);
  actions.append(submit, reset);
  form.append(conditions, modeNote, parameters, actions, error);
  const details = node('details');
  details.append(node('summary', 'Formulas, assumptions and references'),
    node('p', 'aᵢ = γᵢ(cᵢ / 1 mol/L); pH = −log₁₀(aH+); Kw = aH+ × aOH−. Dissociation, total family mass and electroneutrality are solved together. A base uses Ka = Kw / Kb. Pure liquid water has activity 1. Spectator ions stay at their entered analytical amounts.'),
    node('p', 'Constants and fixed activity coefficients must apply to the entered temperature and the same concentration-based 1 mol/L standard state. Temperature changes clear these values; no lookup, ionic-strength model or temperature correction is used. Ideal sets every γ to 1. Entered mode requires all species, even neutral forms and spectators.'),
    node('p', 'Only the chosen single family is included. No gas exchange, precipitation, metal complexation, unrelated acids/bases or arbitrary mixtures. Results are model calculations, not experimental accuracy, reaction speed or laboratory-safety advice. Unsupported numeric ranges or failed balances produce no result.'));
  for (const [label, href] of [['Acid/base constants', 'https://openstax.org/books/chemistry-2e/pages/14-3-relative-strengths-of-acids-and-bases'],
    ['Conjugate-pair buffers', 'https://openstax.org/books/chemistry-2e/pages/14-6-buffers']] as const) {
    const reference = node('a', `${label} ↗`);
    reference.href = href;
    reference.target = '_blank';
    reference.rel = 'noopener noreferrer';
    details.append(reference);
  }
  host.append(form, output, details);
  renderParameters();
  return { clear };
}
