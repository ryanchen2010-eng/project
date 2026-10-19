import { calculateDilution, calculateMolarity, calculateSoluteMass,
  type Concentration, type ConcentrationUnit, type SoluteAmountUnit, type Volume, type VolumeUnit } from './solution-calculator';

export type SolutionCompound = { id: string; name: string; formula?: string; molarMass?: number };
type Mode = 'concentration' | 'mass' | 'dilution';
type Field = { input: HTMLInputElement; unit?: HTMLSelectElement; row: HTMLDivElement };
const AMOUNT_UNITS: SoluteAmountUnit[] = ['g', 'mg', 'mol', 'mmol'];
const VOLUME_UNITS: VolumeUnit[] = ['mL', 'L', 'µL'];
const CONCENTRATION_UNITS: ConcentrationUnit[] = ['mol/L', 'mmol/L', 'µmol/L'];
const format = (value: number) => {
  const rounded = Number(value.toPrecision(5));
  // Rounding a finite value at the floating-point limit can itself overflow.
  return Number.isFinite(rounded) && rounded > 0 ? rounded.toString() : value.toString();
};
let instance = 0;

function text<K extends keyof HTMLElementTagNameMap>(tag: K, value = '', className = '') {
  const node = document.createElement(tag);
  node.textContent = value;
  if (className) node.className = className;
  return node;
}

/** Local arithmetic only; no solubility prediction or solution-preparation procedure. */
export class SolutionCalculatorPanel {
  private compound: SolutionCompound | undefined;
  private mode: Mode = 'concentration';
  private readonly prefix: string;
  private readonly context = text('p', '', 'solution-context');
  private readonly caption = text('p', '', 'solution-caption');
  private readonly fields = text('div', '', 'solution-fields');
  private readonly form = text('form');
  private readonly output = text('div', '', 'solution-output');
  private readonly error = text('p', '', 'solution-error');
  private readonly modeButtons = new Map<Mode, HTMLButtonElement>();
  private readonly inputs = new Map<string, Field>();
  private massField: Field | undefined;
  private massSource: HTMLElement | undefined;

  constructor(private readonly host: HTMLDetailsElement) {
    this.prefix = `${host.id || `solution-${++instance}`}`;
    host.classList.add('solution-calculator');
    const body = text('div', '', 'solution-body');
    const modes = text('div', '', 'solution-modes');
    modes.setAttribute('role', 'group');
    modes.setAttribute('aria-label', 'Solution calculation mode');
    for (const [mode, label] of [['concentration', 'Find concentration'], ['mass', 'Find solute mass'], ['dilution', 'Dilute a stock']] as const) {
      const button = text('button', label);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(mode === this.mode));
      button.addEventListener('click', () => {
        if (mode === this.mode) return;
        this.mode = mode;
        for (const [key, item] of this.modeButtons) item.setAttribute('aria-pressed', String(key === mode));
        this.renderFields();
      });
      this.modeButtons.set(mode, button);
      modes.append(button);
    }
    this.error.id = `${this.prefix}-error`;
    this.error.hidden = true;
    this.error.setAttribute('role', 'alert');
    this.form.noValidate = true;
    this.form.addEventListener('submit', (event) => { event.preventDefault(); this.calculate(); });
    const submit = text('button', 'Calculate solution', 'solution-submit');
    submit.type = 'submit';
    const clear = text('button', 'Clear amounts', 'solution-clear');
    clear.type = 'button';
    clear.addEventListener('click', () => this.renderFields());
    const actions = text('div', '', 'solution-actions');
    actions.append(submit, clear);
    this.form.append(this.fields, actions, this.error);
    this.output.hidden = true;
    this.output.setAttribute('role', 'status');
    this.output.setAttribute('aria-live', 'polite');
    const assumptions = text('details', '', 'solution-assumptions');
    assumptions.append(text('summary', 'Assumptions and formulas'),
      text('p', 'Use pure solute amounts and total final solution volume. Molar mass must match the exact compound, including any hydrate. Purity, solubility, temperature, solvent compatibility, and hazards are not checked. Ionic-salt molarity counts formula units, not the sum of dissolved ions.'),
      text('p', 'c = n / V; n = mass / molar mass; mass = c × V × molar mass. Dilution uses c₁V₁ = c₂V₂ for the same solute with no reaction or solute loss. Volumes are not assumed additive, so an exact added-solvent volume is not calculated. Values normally show 5 significant digits, not a claim of measurement precision.'));
    const reference = text('a', 'Molarity and dilution reference ↗');
    reference.href = 'https://openstax.org/books/chemistry-2e/pages/3-3-molarity';
    reference.target = '_blank';
    reference.rel = 'noopener noreferrer';
    assumptions.append(reference);
    body.append(this.context, modes, this.caption, this.form, this.output, assumptions);
    host.append(text('summary', 'Solution calculator'), body);
    host.hidden = false;
    this.renderFields();
  }

  setCompound(compound?: SolutionCompound) {
    const next = compound && typeof compound.id === 'string' && compound.id.trim()
      && typeof compound.name === 'string' && compound.name.trim() ? {
        id: compound.id, name: compound.name.slice(0, 200),
        formula: typeof compound.formula === 'string' ? compound.formula.slice(0, 80) : undefined,
        molarMass: typeof compound.molarMass === 'number' && Number.isFinite(compound.molarMass) && compound.molarMass > 0
          ? compound.molarMass : undefined,
      } : undefined;
    if (JSON.stringify(next) === JSON.stringify(this.compound)) return;
    this.compound = next;
    this.renderFields();
  }

  reset() { this.compound = undefined; this.renderFields(); }

  private clearOutput() {
    this.output.replaceChildren();
    this.output.hidden = true;
    this.error.textContent = '';
    this.error.hidden = true;
  }

  private field(key: string, label: string, units?: readonly string[]): Field {
    const row = text('div', '', 'solution-field');
    const title = text('label', label);
    const input = text('input');
    input.id = `${this.prefix}-${key}`;
    input.type = 'number';
    input.inputMode = 'decimal';
    input.min = '0';
    input.step = 'any';
    input.required = true;
    input.placeholder = 'Value';
    title.htmlFor = input.id;
    const controls = text('div', '', 'solution-quantity');
    const unit = units ? text('select') : undefined;
    if (unit) {
      unit.setAttribute('aria-label', `Unit for ${label}`);
      for (const value of units!) {
        const option = text('option', value);
        option.value = value;
        unit.append(option);
      }
      controls.append(input, unit);
    } else controls.append(input);
    const invalidate = () => {
      this.clearOutput();
      if (key === 'amount') this.updateMassVisibility();
      if (key === 'molar-mass' && this.massSource) this.massSource.textContent = 'Entered value · check the exact compound form.';
    };
    input.addEventListener('input', invalidate);
    unit?.addEventListener('change', invalidate);
    row.append(title, controls);
    this.fields.append(row);
    const result = { input, unit, row };
    this.inputs.set(key, result);
    return result;
  }

  private renderFields() {
    this.clearOutput();
    this.fields.replaceChildren();
    this.inputs.clear();
    this.massField = undefined;
    this.massSource = undefined;
    this.context.textContent = this.compound
      ? `Solute: ${this.compound.name}${this.compound.formula ? ` (${this.compound.formula})` : ''}`
      : 'Manual solute · enter molar mass when needed.';
    if (this.mode === 'dilution') {
      this.caption.textContent = 'Same solute. Final volume means the whole diluted solution.';
      this.field('stock-concentration', 'Stock concentration', CONCENTRATION_UNITS);
      this.field('target-concentration', 'Target concentration', CONCENTRATION_UNITS);
      this.field('final-volume', 'Final solution volume', VOLUME_UNITS);
    } else {
      this.caption.textContent = 'Final volume means the whole solution, not the added solvent.';
      if (this.mode === 'concentration') this.field('amount', 'Amount of solute', AMOUNT_UNITS);
      else this.field('concentration', 'Target concentration', CONCENTRATION_UNITS);
      this.field('volume', 'Final solution volume', VOLUME_UNITS);
      this.massField = this.field('molar-mass', 'Molar mass (g/mol)');
      if (this.compound?.molarMass) this.massField.input.value = String(this.compound.molarMass);
      this.massSource = text('small', this.compound?.molarMass ? 'From compound data · editable for the exact form.' : 'No molar mass available · enter it manually.');
      this.massSource.id = `${this.prefix}-mass-source`;
      this.massField.input.setAttribute('aria-describedby', this.massSource.id);
      this.massField.row.append(this.massSource);
      this.updateMassVisibility();
    }
  }

  private updateMassVisibility() {
    if (!this.massField) return;
    const unit = this.inputs.get('amount')?.unit?.value;
    const needed = this.mode === 'mass' || unit === 'g' || unit === 'mg';
    this.massField.row.hidden = !needed;
    this.massField.input.required = needed;
  }

  private number(key: string, label: string): number {
    const field = this.inputs.get(key);
    if (!field || !field.input.value.trim()) throw new Error(`Enter ${label.toLowerCase()}.`);
    const value = field.input.valueAsNumber;
    if (!Number.isFinite(value) || value <= 0) throw new Error(`${label} must be a positive finite number.`);
    return value;
  }

  private volume(key: string): Volume {
    return { value: this.number(key, 'Final solution volume'), unit: this.inputs.get(key)!.unit!.value as VolumeUnit };
  }

  private concentration(key: string, label: string): Concentration {
    return { value: this.number(key, label), unit: this.inputs.get(key)!.unit!.value as ConcentrationUnit };
  }

  private displayedVolume(litres: number, key: string): string {
    const unit = this.inputs.get(key)?.unit?.value;
    const scale = unit === 'mL' ? 1000 : unit === 'µL' ? 1_000_000 : 1;
    const value = litres * scale;
    // Fall back to the validated base unit if a display conversion is out of range.
    return Number.isFinite(value) && value > 0 ? `${format(value)} ${unit}` : `${format(litres)} L`;
  }

  private fact(label: string, value: string) {
    const row = text('div', '', 'solution-fact');
    row.append(text('span', label), text('strong', value));
    this.output.append(row);
  }

  private calculate() {
    this.clearOutput();
    try {
      if (this.mode === 'concentration') {
        const unit = this.inputs.get('amount')!.unit!.value as SoluteAmountUnit;
        const mass = unit === 'g' || unit === 'mg' ? this.number('molar-mass', 'Molar mass') : undefined;
        const result = calculateMolarity({ amount: { value: this.number('amount', 'Amount of solute'), unit },
          volume: this.volume('volume'), molarMass: mass });
        this.fact('Solute concentration', `${format(result.molarity)} mol/L`);
        this.fact('Solute amount', `${format(result.moles)} mol`);
      } else if (this.mode === 'mass') {
        const result = calculateSoluteMass({ concentration: this.concentration('concentration', 'Target concentration'),
          volume: this.volume('volume'), molarMass: this.number('molar-mass', 'Molar mass') });
        this.fact('Required pure solute', `${format(result.grams)} g`);
        this.fact('Solute amount', `${format(result.moles)} mol`);
        this.fact('Final total volume', this.displayedVolume(result.litres, 'volume'));
      } else {
        const result = calculateDilution({ stock: this.concentration('stock-concentration', 'Stock concentration'),
          target: this.concentration('target-concentration', 'Target concentration'), finalVolume: this.volume('final-volume') });
        this.fact('Stock aliquot', this.displayedVolume(result.stockLitres, 'final-volume'));
        this.fact('Final total volume', this.displayedVolume(result.finalLitres, 'final-volume'));
        this.fact('Dilution factor', `${format(result.dilutionFactor)}×`);
        if (result.dilutionFactor === 1) this.output.append(text('p', 'Same concentration · no dilution required.', 'solution-caption'));
        else this.output.append(text('p', 'Bring the stock aliquot to the final total volume; this is not an added-solvent volume.', 'solution-caption'));
      }
      this.output.append(text('p', 'Solubility and suitability are not checked.', 'solution-caption'));
      this.output.hidden = false;
    } catch (error) {
      this.output.replaceChildren();
      this.error.textContent = error instanceof Error ? error.message : 'Check the values and units.';
      this.error.hidden = false;
    }
  }
}
