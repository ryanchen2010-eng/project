import { AVOGADRO_CONSTANT, convertMoles, type EntityKind, type MoleInputUnit } from './mole-calculator';
import type { CalculatorCompound } from './calculator-compound';

function node<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const el = document.createElement(tag); el.textContent = value; el.className = className; return el;
}
const numberText = (value: number) => {
  const rounded = Number(value.toPrecision(6));
  return Number.isFinite(rounded) && (value === 0 || rounded > 0) ? String(rounded) : String(value);
};
const ENTITY_LABELS: Record<EntityKind, string> = { molecules: 'Molecules', atoms: 'Atoms', 'formula-units': 'Ionic formula units' };

export class MoleCalculatorPanel {
  private compound?: CalculatorCompound;
  private readonly amount = node('input');
  private readonly unit = node('select');
  private readonly mass = node('input');
  private readonly entity = node('select');
  private readonly context = node('p', '', 'calc-note');
  private readonly massNote = node('small');
  private readonly result = node('div', '', 'calc-result');
  private readonly error = node('p', '', 'calc-error');

  constructor(host: HTMLElement) {
    const form = node('form', '', 'calculator-form'); form.noValidate = true;
    const grid = node('div', '', 'calc-grid');
    for (const [input, id, label] of [[this.amount, 'moles-amount', 'Amount'], [this.mass, 'moles-mass', 'Molar mass (g/mol)']] as const) {
      input.id = id; input.type = 'number'; input.step = 'any'; input.min = '0'; input.inputMode = 'decimal';
      const row = node('div', '', 'calc-field'); const title = node('label', label); title.htmlFor = id;
      row.append(title, input);
      if (input === this.amount) {
        this.unit.setAttribute('aria-label', 'Amount unit');
        for (const unit of ['g', 'mg', 'kg', 'µg', 'mol', 'mmol', 'µmol', 'particles']) {
          const option = node('option', unit === 'particles' ? 'Particle count' : unit); option.value = unit; this.unit.append(option);
        }
        row.append(this.unit);
      } else { input.setAttribute('aria-describedby', 'moles-mass-note'); this.massNote.id = 'moles-mass-note'; row.append(this.massNote); }
      grid.append(row);
    }
    const entityRow = node('div', '', 'calc-field'); const entityLabel = node('label', 'Counted entity');
    this.entity.id = 'moles-entity'; entityLabel.htmlFor = this.entity.id;
    for (const [value, label] of Object.entries(ENTITY_LABELS)) { const option = node('option', label); option.value = value; this.entity.append(option); }
    entityRow.append(entityLabel, this.entity); grid.append(entityRow);
    this.entity.addEventListener('change', () => {
      // A compound molar mass cannot silently become an atomic molar mass.
      if (this.compound && this.entity.value !== this.compound.entityKind) {
        this.compound = undefined; this.mass.value = ''; this.updateContext();
      }
      this.invalidate();
    });
    this.mass.addEventListener('input', () => { this.massNote.textContent = 'Entered value · must match the counted entity.'; });
    form.addEventListener('input', () => this.invalidate()); form.addEventListener('change', () => this.invalidate());
    this.error.setAttribute('role', 'alert'); this.error.hidden = true;
    this.result.setAttribute('role', 'status'); this.result.setAttribute('aria-live', 'polite'); this.result.hidden = true;
    form.addEventListener('submit', (event) => {
      event.preventDefault(); this.invalidate();
      try {
        if (!this.amount.value.trim()) throw new Error('Enter an amount.');
        const massValue = this.mass.value.trim() ? Number(this.mass.value) : undefined;
        const output = convertMoles({ value: Number(this.amount.value), unit: this.unit.value as MoleInputUnit,
          molarMass: massValue, entityKind: this.entity.value as EntityKind });
        const facts: [string, string][] = [['Amount', `${numberText(output.moles)} mol`],
          [ENTITY_LABELS[output.entityKind], numberText(output.particles)]];
        if (output.grams !== undefined) facts.push(['Mass', `${numberText(output.grams)} g`]);
        for (const [label, value] of facts) { const row = node('p'); row.append(node('span', label), node('strong', value)); this.result.append(row); }
        this.result.append(node('small', 'Specified entities · pure material · displayed rounding only'));
        this.result.hidden = false;
      } catch (err) { this.error.textContent = err instanceof Error ? err.message : 'Unable to calculate this amount.'; this.error.hidden = false; }
    });
    const actions = node('div', '', 'calc-actions'); const calculate = node('button', 'Calculate'); calculate.type = 'submit';
    const clear = node('button', 'Clear'); clear.type = 'button'; clear.addEventListener('click', () => this.clear()); actions.append(calculate, clear);
    form.append(grid, actions, this.error);
    const info = node('details'); info.append(node('summary', 'Formulas, assumptions and reference'),
      node('p', `n = m / M; N = n × Nₐ. Nₐ = ${AVOGADRO_CONSTANT} mol⁻¹ (exact SI definition).`),
      node('p', 'Molar mass must match the exact entity, including salts and hydrates. Formula units are not molecules or the sum of dissolved ions. “Atoms” means a specified atomic species, not all atoms inside a compound. Counts are continuous amount estimates, not rounded integer enumerations. No purity, experimental accuracy, or safety prediction.'));
    const link = node('a', 'SI definition of the mole ↗'); link.href = 'https://www.bipm.org/en/si-base-units/mole'; link.target = '_blank'; link.rel = 'noopener noreferrer'; info.append(link);
    host.append(this.context, form, this.result, info); this.updateContext();
  }
  private invalidate() { this.result.replaceChildren(); this.result.hidden = true; this.error.textContent = ''; this.error.hidden = true; }
  private updateContext() {
    this.context.textContent = this.compound ? `${this.compound.name}${this.compound.formula ? ` (${this.compound.formula})` : ''}` : 'Manual entry · molar mass is optional for moles ↔ particles.';
    this.massNote.textContent = this.compound?.molarMass ? 'From exact compound data · editable.' : 'Enter the exact entity’s molar mass to calculate mass.';
  }
  setCompound(compound?: CalculatorCompound) { this.compound = compound; this.clear(); }
  clear() {
    this.amount.value = ''; this.unit.value = 'g'; this.mass.value = this.compound?.molarMass ? String(this.compound.molarMass) : '';
    this.entity.value = this.compound?.entityKind ?? 'molecules'; this.updateContext(); this.invalidate();
  }
}
