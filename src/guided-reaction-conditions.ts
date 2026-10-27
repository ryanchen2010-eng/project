/** Render backend guidance. This module neither matches chemistry nor grants 3D. */
export type GuidedConditions = {
  version: 1;
  reactionId: string;
  siteId?: string;
  profileId?: string;
  title: string;
  state: 'missing-conditions' | 'conflicting-conditions' | 'qualified' | 'outside-profile-scope' | 'no-validated-profile' | 'unsupported-conditions';
  message: string;
  canApply: boolean;
  requireConfirmation?: boolean;
  showOnInitialMatch?: boolean;
  requirements: { field: string; label: string; selectedValue: string; requiredValue: string; selectedLabel: string; requiredLabel: string; state: 'missing' | 'conflicting' | 'matches' | 'preserved' }[];
  targetConditions?: Record<string, string>;
  limitations: string[];
  sourceUrl?: string;
  profileDescriptor?: { facts: { field: string; value: unknown; provenance: string; relevance: string; source?: string }[]; assumptions: string[]; unknowns: string[] };
};

export function guidedControlValues(guidance: GuidedConditions): Record<string, string> {
  if (!guidance.canApply || !guidance.targetConditions) throw new Error('No applicable settings were supplied by the backend.');
  if (['cooled-isobutylene-os-peroxide-v1','cooled-crotonic-os-peroxide-v1','cooled-cinnamic-os-peroxide-v1'].includes(guidance.profileId ?? '')) {
    const values = guidance.targetConditions;
    if (values.solvent !== 'dry' || values.catalyst !== 'osmium' || values.workup !== (guidance.profileId === 'cooled-isobutylene-os-peroxide-v1' ? '' : 'aqueous-release')
      || values.conditionProfileId !== guidance.profileId || values.conditionProfileVersion !== '1'
      || Object.keys(values).some(key => !['solvent','catalyst','workup','conditionProfileId','conditionProfileVersion'].includes(key))) {
      throw new Error('These settings do not match the source-specific free-product reference.');
    }
    return { ...values }; // Explicit reviewed release contract, never automatic work-up substitution.
  }
  if (guidance.profileId === 'cooled-cyclohexene-pd-silica-v1') {
    const values = guidance.targetConditions;
    if (values.solvent !== 'dry' || values.catalyst !== 'metal'
      || values.conditionProfileId !== guidance.profileId || values.conditionProfileVersion !== '1'
      || Object.keys(values).some(key => !['solvent', 'catalyst', 'conditionProfileId', 'conditionProfileVersion'].includes(key))) {
      throw new Error('These settings do not match the exact cyclohexene Pd/silica reference.');
    }
    return { ...values }; // Deliberate reference selection, never temperature or arbitrary facts.
  }
  if (guidance.profileId === 'cooled-perbenzoic-epoxidation-v1') {
    const controls = guidance.targetConditions;
    if (controls.solvent !== 'dry' || controls.catalyst !== 'none'
      || Object.keys(controls).some(key => !['solvent', 'catalyst'].includes(key))) {
      throw new Error('These settings do not match the bounded perbenzoic-acid medium/activation model.');
    }
    return { ...controls }; // No temperature changes, stage clearing or chemistry permission.
  }
  if (guidance.profileId === 'Alkyne partial hydrogenation') {
    // Direct transport for the existing activation control. Do not fill a
    // solvent/temperature or silently discard unknown profile declarations.
    const controls = guidance.targetConditions;
    if (controls.catalyst !== 'lindlar' || Object.entries(controls).some(([key, value]) =>
      key !== 'catalyst' && (!['oxidationStage', 'workup'].includes(key) || value !== ''))) {
      throw new Error('These settings cannot be represented by the existing Lindlar guidance controls.');
    }
    return { ...controls };
  }
  const { secondaryOxidationProfile, ...controls } = guidance.targetConditions;
  // Transport alias for the existing combined medium control, not eligibility.
  if (secondaryOxidationProfile !== 'naocl-acetic-ketone-v1' || controls.solvent !== 'aqueous-protic') {
    throw new Error('This profile cannot be represented by the existing medium control.');
  }
  if (Object.entries(controls).some(([key, value]) => !['solvent', 'temperature', 'catalyst', 'oxidationStage', 'workup'].includes(key) || typeof value !== 'string')) {
    throw new Error('The suggested settings include a control this pilot cannot edit.');
  }
  return { ...controls, solvent: 'secondary-naocl-acetic' };
}

function node<K extends keyof HTMLElementTagNameMap>(tag: K, text = ''): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.textContent = text;
  return element;
}

const STATES: Record<GuidedConditions['state'], string> = {
  'missing-conditions': 'Missing required settings',
  'conflicting-conditions': 'Review conflicting selections',
  'qualified': 'Model conditions match',
  'outside-profile-scope': 'Outside qualified profile scope',
  'no-validated-profile': 'No validated profile implemented',
  'unsupported-conditions': 'Unsupported condition inputs',
};

export class GuidedConditionsPanel {
  private epoch = 0;
  constructor(private host: HTMLElement, private apply: (guidance: GuidedConditions, signature: string) => Promise<void>) {
    this.clear();
  }
  clear() {
    this.epoch += 1;
    this.host.hidden = true;
    this.host.replaceChildren();
  }
  setGuidance(guidance: GuidedConditions | undefined, signature: string) {
    this.clear();
    if (!guidance || guidance.version !== 1) return;
    const epoch = this.epoch;
    this.host.hidden = false;
    const title = node('h3', 'Guided conditions'); title.id = 'guided-conditions-heading';
    this.host.append(title, node('strong', guidance.title));
    const status = node('p', STATES[guidance.state]); status.setAttribute('role', 'status');
    this.host.append(status, node('p', guidance.message));
    const changes = guidance.requirements.filter(row => row.state === 'missing' || row.state === 'conflicting');
    if (guidance.canApply && changes.length) {
      const next = node('p', 'Next: open “Review supported settings” below. Nothing changes until you review and apply.');
      const checklist = node('ul'); checklist.setAttribute('aria-label', 'Settings to review');
      for (const row of changes) {
        checklist.append(node('li', row.state === 'missing'
          ? `Choose ${row.label}: ${row.requiredLabel}.`
          : `Review ${row.label}: ${row.selectedLabel} → ${row.requiredLabel} (confirmation required).`));
      }
      this.host.append(next, checklist);
    }
    const details = node('details');
    details.append(node('summary', guidance.canApply ? 'Review supported settings' : 'Settings and limitations'));
    const list = node('ul');
    for (const row of guidance.requirements) {
      list.append(node('li', `${row.label}: ${row.selectedLabel} → ${row.requiredLabel}${row.state === 'matches' ? ' (matches)' : row.state === 'conflicting' ? ' (replace selected setting)' : row.state === 'preserved' ? ' (preserved)' : ' (missing)'}`));
    }
    if (guidance.requirements.length) details.append(list);
    for (const text of guidance.limitations) details.append(node('p', text));
    if (guidance.profileDescriptor) {
      const facts = node('details'); facts.append(node('summary', 'Source Observations, Assumptions and Unknowns'));
      for (const item of guidance.profileDescriptor.facts) {
        facts.append(node('p', `${item.field} — ${item.provenance}: ${typeof item.value === 'string' ? item.value : JSON.stringify(item.value)}. ${item.relevance}${item.source ? ` Source: ${item.source}.` : ''}`));
      }
      for (const text of guidance.profileDescriptor.assumptions) facts.append(node('p', `Model assumption: ${text}`));
      for (const text of guidance.profileDescriptor.unknowns) facts.append(node('p', `Unknown / not modeled: ${text}`));
      details.append(facts);
    }
    if (guidance.sourceUrl?.startsWith('https://')) {
      const source = node('a', 'Profile reference'); source.href = guidance.sourceUrl;
      source.target = '_blank'; source.rel = 'noopener noreferrer'; details.append(source);
    }
    if (guidance.canApply) {
      const replacements = guidance.requirements.filter(row => row.state === 'conflicting').length;
      let confirmation: HTMLInputElement | undefined;
      const button = node('button', 'Apply supported settings'); button.type = 'button';
      if (replacements || guidance.requireConfirmation) {
        confirmation = node('input'); confirmation.type = 'checkbox';
        const label = node('label'); label.className = 'guided-replacement-confirmation';
        label.append(confirmation, node('span', replacements ? 'I agree to replace the selected settings listed above.' : 'I confirm the suggested model settings listed above.'));
        details.append(label); button.disabled = true;
        confirmation.addEventListener('change', () => { if (epoch === this.epoch) button.disabled = !confirmation?.checked; });
      }
      const message = node('p'); message.setAttribute('role', 'status');
      button.addEventListener('click', async () => {
        if (epoch !== this.epoch || button.disabled || (confirmation && !confirmation.checked)) return;
        button.disabled = true; message.textContent = 'Applying selections and asking the backend to revalidate…';
        try {
          await this.apply(guidance, signature);
        } catch (error) {
          if (epoch !== this.epoch) return;
          message.textContent = error instanceof Error ? error.message : 'Settings could not be applied. Refresh the reaction options.';
          button.disabled = Boolean(confirmation && !confirmation.checked);
        }
      });
      details.append(button, message);
    }
    this.host.append(details);
  }
}
