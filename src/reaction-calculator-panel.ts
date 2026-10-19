import { calculateReaction, calculateRequiredAmounts, toMoles, validateStoichiometry,
  type AmountUnit, type Quantity, type ReactionStoichiometry } from './reaction-calculator';

const UNITS: AmountUnit[] = ['g', 'mg', 'mol', 'mmol'];
const formatted = (value: number) => value === 0 ? '0' : Number(value.toPrecision(5)).toString();

function textElement<K extends keyof HTMLElementTagNameMap>(tag: K, text: string, className?: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

/** A local calculator; selecting a new equation clears every prior amount/result. */
export class ReactionCalculatorPanel {
  private data: ReactionStoichiometry | null = null;
  private mode: 'yield' | 'required' = 'yield';
  private readonly body = document.createElement('div');
  private readonly form = document.createElement('form');
  private readonly fields = document.createElement('div');
  private readonly notes = document.createElement('div');
  private readonly methodNotes = document.createElement('div');
  private readonly output = document.createElement('div');
  private readonly error = textElement('p', '', 'calculator-error');
  private readonly amounts = new Map<number, { input: HTMLInputElement; unit: HTMLSelectElement; conversion: HTMLElement }>();
  private target: { input: HTMLInputElement; unit: HTMLSelectElement; conversion: HTMLElement } | null = null;
  private readonly modeButtons: HTMLButtonElement[] = [];

  constructor(private readonly host: HTMLDetailsElement) {
    host.classList.add('reaction-calculator');
    host.append(textElement('summary', 'Reaction calculator'), this.body);
    this.body.className = 'calculator-body';
    const modes = document.createElement('div');
    modes.className = 'calculator-modes';
    modes.setAttribute('role', 'group');
    modes.setAttribute('aria-label', 'Calculation mode');
    for (const [mode, label] of [['yield', 'Amounts → yield'], ['required', 'Target → amounts']] as const) {
      const button = textElement('button', label);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(mode === this.mode));
      button.addEventListener('click', () => {
        if (this.mode === mode) return;
        this.mode = mode;
        this.modeButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
        this.renderFields();
      });
      this.modeButtons.push(button);
      modes.append(button);
    }
    this.fields.className = 'calculator-fields';
    this.notes.className = 'calculator-notes';
    this.error.id = 'calculator-error';
    this.error.hidden = true;
    this.error.setAttribute('role', 'alert');
    const submit = textElement('button', 'Calculate', 'calculator-submit');
    submit.type = 'submit';
    this.form.append(this.fields, submit, this.error);
    this.form.addEventListener('submit', (event) => { event.preventDefault(); this.calculate(); });
    this.output.className = 'calculator-output';
    this.output.hidden = true;
    this.output.setAttribute('role', 'status');
    this.output.setAttribute('aria-live', 'polite');
    const assumptions = document.createElement('details');
    assumptions.className = 'calculator-assumptions';
    assumptions.append(textElement('summary', 'Assumptions and method'),
      textElement('p', 'Pure reactants; complete conversion into the selected pathway; no losses or side reactions. Reversible reactions may give much less. Mass means reagent mass, not solution mass. Catalysts and solvent quantities are not calculated.'),
      textElement('p', 'n = mass ÷ molar mass. Reaction extent = smallest n ÷ coefficient. Product moles = extent × product coefficient. Results are rounded to 5 significant digits for display.'));
    const source = textElement('a', 'Stoichiometry reference ↗');
    source.href = 'https://openstax.org/books/chemistry-2e/pages/4-4-reaction-yields';
    source.target = '_blank';
    source.rel = 'noopener noreferrer';
    assumptions.append(this.methodNotes, source);
    this.body.append(modes, textElement('p', 'Theoretical amounts only—not actual yield or a lab procedure.', 'calculator-caption'),
      this.notes, this.form, this.output, assumptions);
    this.host.hidden = true;
  }

  setReaction(data?: ReactionStoichiometry) {
    this.data = null;
    this.clearOutput();
    this.fields.replaceChildren();
    this.amounts.clear();
    this.target = null;
    this.notes.replaceChildren();
    this.methodNotes.replaceChildren();
    this.host.hidden = !data;
    if (!data) return;
    try {
      validateStoichiometry(data);
      this.data = data;
      this.form.hidden = false;
      if (data.context) {
        const context = data.context;
        this.notes.append(textElement('p', `${context.label}. ${context.warning}`, 'calculator-context-warning'));
        const conditionNames: Record<string, string> = { oxidationStage: 'oxidation stage', catalyst: 'catalyst / activation', workup: 'product release / work-up', secondaryOxidationProfile: 'secondary oxidation medium profile', additionStage: 'equivalents', polymerUnits: 'chain length' };
        if (context.unknownConditions.length) this.notes.append(textElement('p', `Not established: ${context.unknownConditions.map(key => conditionNames[key] ?? key).join(', ')}.`));
        for (const assumption of context.assumptions) this.methodNotes.append(textElement('p', assumption));
      }
      for (const note of data.notes ?? []) this.methodNotes.append(textElement('p', note));
      if (data.notes?.some((note) => note.includes('spectator'))) {
        this.notes.append(textElement('p', 'Spectator ion omitted from the equation; amounts use the full selected salt.'));
      }
      for (const excluded of data.excludedInputs ?? []) this.notes.append(textElement('p', `${excluded.name}: ${excluded.reason}`));
      this.renderFields();
    } catch {
      this.form.hidden = true;
      this.notes.append(textElement('p', 'Calculator unavailable: this equation has not been verified as balanced.'));
    }
  }

  private clearOutput() {
    this.output.hidden = true;
    this.output.replaceChildren();
    this.error.hidden = true;
    this.error.textContent = '';
  }

  private quantityField(key: string, label: string, molarMass: number) {
    const row = document.createElement('div');
    row.className = 'calculator-field';
    const title = textElement('label', label);
    const input = document.createElement('input');
    input.id = `calculator-${key}`;
    input.type = 'number';
    input.inputMode = 'decimal';
    input.min = '0';
    input.step = 'any';
    input.required = true;
    input.placeholder = 'Amount';
    title.htmlFor = input.id;
    const unit = document.createElement('select');
    unit.setAttribute('aria-label', `Unit for ${label}`);
    for (const value of UNITS) {
      const option = textElement('option', value);
      option.value = value;
      unit.append(option);
    }
    const controls = document.createElement('div');
    controls.className = 'calculator-quantity';
    controls.append(input, unit);
    const conversion = textElement('small', `${formatted(molarMass)} g/mol`);
    conversion.id = `${input.id}-conversion`;
    input.setAttribute('aria-describedby', conversion.id);
    const update = () => {
      this.clearOutput();
      try {
        const quantity = this.readQuantity({ input, unit });
        const mol = toMoles(quantity, molarMass);
        conversion.textContent = `${formatted(molarMass)} g/mol · ${formatted(mol)} mol`;
      } catch { conversion.textContent = `${formatted(molarMass)} g/mol`; }
    };
    input.addEventListener('input', update);
    unit.addEventListener('change', update);
    row.append(title, controls, conversion);
    this.fields.append(row);
    return { input, unit, conversion };
  }

  private renderFields() {
    this.fields.replaceChildren();
    this.clearOutput();
    this.amounts.clear();
    this.target = null;
    if (!this.data) return;
    if (this.mode === 'yield') {
      for (const reactant of this.data.reactants) {
        this.amounts.set(reactant.inputSlot, this.quantityField(`reactant-${reactant.inputSlot}`,
          `${reactant.name} (${reactant.formula})`, reactant.molarMass));
      }
    } else {
      this.target = this.quantityField('target', `Target: ${this.data.product.name} (${this.data.product.formula})`, this.data.product.molarMass);
    }
  }

  private readQuantity(field: { input: HTMLInputElement; unit: HTMLSelectElement }): Quantity {
    if (!field.input.value.trim()) throw new Error('Enter an amount in every box.');
    return { value: field.input.valueAsNumber, unit: field.unit.value as AmountUnit };
  }

  private fact(label: string, value: string) {
    const item = document.createElement('div');
    item.className = 'calculator-fact';
    item.append(textElement('span', label), textElement('strong', value));
    this.output.append(item);
  }

  private calculate() {
    this.clearOutput();
    if (!this.data) return;
    try {
      if (this.mode === 'yield') {
        const quantities: Partial<Record<0 | 1, Quantity>> = {};
        for (const [slot, field] of this.amounts) quantities[slot as 0 | 1] = this.readQuantity(field);
        const result = calculateReaction(this.data, quantities);
        const limiting = this.data.reactants.filter((item) => result.limitingInputs.includes(item.inputSlot));
        this.fact(result.limitingInputs.length > 1 ? 'Stoichiometric amounts · both exhausted' : 'Limiting reactant', limiting.map((item) => item.name).join(' + '));
        this.fact(`Theoretical yield · ${this.data.product.name}`, `${formatted(result.product.grams)} g · ${formatted(result.product.moles)} mol`);
        for (const reactant of result.reactants) {
          this.fact(`Remaining · ${reactant.name}`, `${formatted(reactant.remainingGrams)} g · ${formatted(reactant.remainingMoles)} mol`);
        }
      } else if (this.target) {
        const result = calculateRequiredAmounts(this.data, this.readQuantity(this.target));
        this.fact(`Target · ${this.data.product.name}`, `${formatted(result.product.grams)} g · ${formatted(result.product.moles)} mol`);
        for (const reactant of result.reactants) this.fact(`Required · ${reactant.name}`, `${formatted(reactant.grams)} g · ${formatted(reactant.moles)} mol`);
        this.output.append(textElement('p', 'Stoichiometric minimum at 100% conversion; not a predicted practical amount.', 'calculator-caption'));
      }
      this.output.hidden = false;
    } catch (error) {
      this.output.replaceChildren();
      this.error.textContent = error instanceof Error ? error.message : 'Check the amounts and units.';
      this.error.hidden = false;
    }
  }
}
