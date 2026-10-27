export type ConditionAssessment = {
  state: 'aligned' | 'incomplete' | 'alternative'; note: string;
  status?: 'model-match' | 'reference-difference' | 'missing' | 'disfavored' | 'unevaluated' | 'activation-required' | 'unsupported-pathway';
  label?: string;
  canRun?: boolean;
  coolingUnvalidated?: boolean;
  productReleaseAssumptionConfirmed?: boolean;
  productRelease?: { version: 1; aqueousReleaseAssumed: boolean; observedRecovery: string; workupSimulated: false };
  namedConditionProfile?: {
    version: 1; selection: 'explicit' | 'legacy-inferred'; status: 'qualified' | 'unresolved' | 'rejected';
    reference: { id: string; version: string };
    descriptor: { version: 1; id: string; profileVersion: number; pathway: string; title: string;
      facts: { field: string; value: unknown; provenance: string; relevance: string; source?: string }[];
      evidence: { url: string; locator: string }[]; assumptions: string[]; unknowns: string[] } | null;
  };
  missingSettings?: string[];
  conditionIssues?: { field: string; kind: string; explanation: string }[];
  cooling?: {
    version: 1; pathway: string; modelId?: string | null;
    registryVersion?: 1; profileVersion?: 1 | null; reasonCodes?: string[];
    status: 'supported-model' | 'conditions-unresolved' | 'unvalidated-pathway';
    canGenerate3D: boolean; note: string; sourceUrls: string[];
    conditionIssues?: { field: string; kind: string; explanation: string }[];
  };
  evidence?: {
    version: 1; structuralEligibility: 'eligible'; reagentIdentity: 'validated'; assertionLevel: 'conditional-net';
    experimentalOutcome: 'not-predicted'; label: string; requiredSettings: string[]; missingRequiredSettings: string[];
    requirementsState: 'missing' | 'not-evaluated' | 'assumptions-satisfied';
    conditionCompleteness: 'incomplete' | 'model-assumptions-only' | 'unsupported-input' | 'conflicting-input' | 'not-evaluated'; unknownConditions: string[];
    conditionIssues?: { field: string; kind: 'unsupported' | 'conflicting' | 'unvalidated-alternative'; explanation: string }[];
    canPreview2D: boolean; canGenerate3D: boolean; renderingPolicy: string; renderingNote: string;
    aldehydeEndpointValidated?: boolean;
  };
};

const CONDITION_NAMES: Record<string, string> = { solvent: 'reaction medium', temperature: 'temperature', catalyst: 'additional catalyst / activation', oxidationStage: 'oxidation stage', additionStage: 'equivalents', workup: 'product release / work-up', secondaryOxidationProfile: 'secondary NaOCl/acetic-acid medium profile' };

export type NamedProfileSelection = { conditionProfileId: string; conditionProfileVersion: string };
/** Restore a reference, never cached facts or permission. Unknown/obsolete refs
 * are sent back for rejection, not silently dropped into an implicit model. */
export function restoreNamedProfile(value: Record<string, unknown> | undefined): NamedProfileSelection | null {
  if (!value || (!('conditionProfileId' in value) && !('conditionProfileVersion' in value))) return null;
  const id = value.conditionProfileId, version = value.conditionProfileVersion;
  return typeof id === 'string' && /^[a-z][a-z0-9-]{0,127}$/.test(id)
    && typeof version === 'string' && /^[1-9][0-9]{0,5}$/.test(version)
    ? { conditionProfileId: id, conditionProfileVersion: version }
    : { conditionProfileId: 'invalid-restored-profile', conditionProfileVersion: '1' };
}

/** V1 presentation mirror; parity-tested against the backend's immutable registry.
 * This contains labels, not reaction rules or an alternative generation gate.
 * Keep this module dependency-free for the existing isolated consumer tests.
 */
export const REVIEWED_COOLING_MODELS: Readonly<Record<string, Readonly<{
  pathway: string; version: number; uiName: string;
}>>> = Object.freeze({
  'cooled-alkene-bromination-v1': Object.freeze({ pathway: 'Bromination', version: 1, uiName: 'alkene bromination' }),
  'cooled-peroxyacid-epoxidation-v1': Object.freeze({ pathway: 'Epoxidation', version: 1, uiName: 'mCPBA peroxyacid epoxidation' }),
  'cooled-perbenzoic-epoxidation-v1': Object.freeze({ pathway: 'Epoxidation', version: 1, uiName: 'perbenzoic-acid epoxidation' }),
  'cooled-cyclohexene-pd-silica-v1': Object.freeze({ pathway: 'Hydrogenation', version: 1, uiName: 'cyclohexene Pd/silica-A hydrogenation' }),
  'cooled-isobutylene-os-peroxide-v1': Object.freeze({ pathway: 'Alkene dihydroxylation', version: 1, uiName: 'Isobutylene · OsO4/H2O2 · tert-butanol reference' }),
  'cooled-crotonic-os-peroxide-v1': Object.freeze({ pathway: 'Alkene dihydroxylation', version: 1, uiName: 'Crotonic acid · OsO4/H2O2 · tert-butanol reference' }),
  'cooled-cinnamic-os-peroxide-v1': Object.freeze({ pathway: 'Alkene dihydroxylation', version: 1, uiName: 'Cinnamic acid · OsO4/H2O2 · tert-butanol reference' }),
});

/** Exact reviewed model, pathway and versions; absent new fields retain v1 compatibility. */
function coolingModelName(assessment: ConditionAssessment): string | undefined {
  const profile = assessment.cooling;
  if (profile?.version !== 1 || typeof profile.modelId !== 'string'
    || !Object.prototype.hasOwnProperty.call(REVIEWED_COOLING_MODELS, profile.modelId)) return undefined;
  const model = REVIEWED_COOLING_MODELS[profile.modelId];
  if (profile.pathway !== model.pathway
    || (profile.registryVersion !== undefined && profile.registryVersion !== 1)
    || (profile.profileVersion !== undefined && profile.profileVersion !== model.version)) return undefined;
  return model.uiName;
}

/** A supported cooling profile alone never overrides the server's other checks. */
function supportedCooled3D(assessment: ConditionAssessment): boolean {
  const named = assessment.namedConditionProfile;
  if (named && (named.version !== 1 || named.status !== 'qualified' || !named.descriptor
    || named.reference.id !== assessment.cooling?.modelId || named.descriptor.id !== named.reference.id
    || String(named.descriptor.profileVersion) !== named.reference.version
    || named.descriptor.pathway !== assessment.cooling?.pathway)) return false;
  return coolingModelName(assessment) !== undefined
    && assessment.coolingUnvalidated !== true && assessment.status === 'model-match'
    && assessment.canRun === true && assessment.evidence?.canGenerate3D === true
    && assessment.evidence.missingRequiredSettings.length === 0 && assessment.evidence.aldehydeEndpointValidated !== false
    && !assessment.evidence.conditionIssues?.length
    && !assessment.conditionIssues?.length && !assessment.missingSettings?.length
    && !assessment.cooling?.conditionIssues?.length && !assessment.cooling?.reasonCodes?.length
    && assessment.cooling?.status === 'supported-model' && assessment.cooling.canGenerate3D === true;
}

/** Remove repeated explanation sentences, not chemistry qualifications. */
export function conciseConditionNote(note: string): string {
  const seen = new Set<string>();
  return note.split(/(?<=[.!?])\s+/).filter(sentence => {
    const key = sentence.replace(/^[A-Za-z]+:\s*/, '').trim();
    if (seen.has(key)) return false;
    seen.add(key); return true;
  }).join(' ');
}

/** Guidance uses the same evidence and permission as the backend, not a second gate. */
export function conditionGuidance(assessment?: ConditionAssessment): string {
  const evidence = assessment?.evidence;
  if (!evidence) return assessment?.note ?? '';
  const parts = ['Structure/site supported.'];
  if (evidence.missingRequiredSettings.length) {
    const fields = [...new Set(evidence.missingRequiredSettings.map((k) => CONDITION_NAMES[k] ?? k))];
    parts.push(`Missing: ${fields.join(', ')}. Complete the existing condition fields using Edit conditions; options update automatically. If Guided conditions is available, open “Review supported settings” to review the supported model before applying it.`);
  }
  if (!evidence.missingRequiredSettings.length || evidence.conditionIssues?.length) parts.push(conciseConditionNote(assessment?.note ?? ''));
  if (assessment?.cooling) parts.push(conciseConditionNote(assessment.cooling.note));
  parts.push(assessment?.cooling && supportedCooled3D(assessment)
    ? 'Cooled 3D is a theoretical product conformer, not a temperature simulation or a prediction of rates, yields or selectivity.'
    : evidence.canGenerate3D && !assessment?.cooling ? '3D is a conditional net-model conformer, not a verified experimental outcome.'
    : evidence.aldehydeEndpointValidated === false ? 'Conditional 2D remains available. No existing setting enables selective aldehyde 3D; the required profile is not implemented.'
    : 'Conditional 2D remains available. 3D is blocked for the stated conditions or chemistry limitations.');
  return assessment?.cooling ? conciseConditionNote(parts.join(' ')) : parts.join(' ');
}

/** Short visible next step, never a new permission or guessed condition preset. */
export function conditionNextStep(assessment?: ConditionAssessment): string {
  const evidence = assessment?.evidence;
  if (evidence?.aldehydeEndpointValidated === false) {
    return '2D only: a validated selective-aldehyde model is not implemented. Changing dropdowns will not enable 3D.';
  }
  const missing = evidence?.missingRequiredSettings ?? [];
  if (missing.length) {
    return `Complete: ${[...new Set(missing.map(k => CONDITION_NAMES[k] ?? k))].join(', ')}. Use Edit conditions to review these settings; the options update automatically.${assessment?.cooling ? ` Cooling assessment: ${conciseConditionNote(assessment.cooling.note)}` : assessment?.coolingUnvalidated ? ' Cooled conditions are also unvalidated and do not qualify 3D.' : ''}`;
  }
  if (assessment?.cooling) {
    if (supportedCooled3D(assessment)) {
      return `Supported cooled ${coolingModelName(assessment)} model. View the theoretical 3D product conformer; this is not a temperature simulation or a prediction of rates, yields or selectivity.`;
    }
    return `Review cooled conditions: ${conciseConditionNote(assessment.cooling.note)} Conditional 2D remains available; 3D stays unavailable. Use Edit conditions to review the stated requirements—do not substitute room temperature unless that is your intended setting.`;
  }
  if (assessment?.coolingUnvalidated) {
    return 'Cooled conditions are recorded, but no low-temperature profile is validated. Conditional 2D remains available; 3D stays unavailable. Review the pathway conditions—do not substitute room temperature unless that is your intended setting.';
  }
  if (assessment?.canRun === false) {
    return '3D is unavailable for this selection. Review the condition explanation and model limitations; a setting change may not resolve them.';
  }
  if (assessment?.status === 'missing') {
    return 'Some comparison settings are not specified. Review Reaction conditions; this alone does not mean the reaction is impossible.';
  }
  return '';
}

/** Honest identity fallback when no bounded/local name is available. */
export function productStructureLabel(productName: string, smiles?: string): string {
  return smiles && /(?:\bproduct|\bcoproduct|\bcarboxylate ion|\boligomer)$/i.test(productName)
    ? `Structure identifier (SMILES): ${smiles}` : '';
}

export function conditionLabel(assessment?: ConditionAssessment): string {
  if (assessment?.evidence) return assessment.evidence.label;
  switch (assessment?.status) {
    case 'unsupported-pathway': return 'Requested pathway unsupported · no product prediction';
    case 'activation-required': return 'Acid activation required · conditional 2D option only';
    case 'model-match': return 'Model conditions match · outcome not guaranteed';
    case 'reference-difference': return 'Reference conditions differ · not proof of disfavor';
    case 'missing': return 'Comparison conditions incomplete';
    case 'disfavored': return 'Disfavoring factor present · reaction may still occur';
    case 'unevaluated': return 'Conditions not reliably evaluated';
  }
  // Other reaction families keep their existing assessment, unchanged.
  if (assessment?.state === 'aligned') return 'Conditions fit the example · outcome not guaranteed';
  if (assessment?.state === 'alternative') return 'Conditions differ from the example';
  return 'Check the conditions for this pathway';
}

export function reactionOptionSummary(options: { mechanism: string }[]): string {
  const mechanisms = new Set(options.map((option) => option.mechanism)).size;
  return `${options.length} net product option${options.length === 1 ? '' : 's'} across ${mechanisms} mechanism${mechanisms === 1 ? '' : 's'}. Options may differ by site, orientation or face; no ratios predicted.`;
}

export function unsupportedInputMessage(error?: string): string {
  const detail = typeof error === 'string' && error.trim() ? error.trim() : 'The selected structure is outside the supported reaction model.';
  return `${detail} This is a model limitation, not proof that the molecules cannot react.`;
}
