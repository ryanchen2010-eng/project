export type ConditionAssessment = {
  state: 'aligned' | 'incomplete' | 'alternative'; note: string;
  status?: 'model-match' | 'reference-difference' | 'missing' | 'disfavored' | 'unevaluated' | 'activation-required' | 'unsupported-pathway';
  label?: string;
  canRun?: boolean;
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

const CONDITION_NAMES: Record<string, string> = { solvent: 'reaction medium', temperature: 'temperature', catalyst: 'catalyst / activation', oxidationStage: 'oxidation stage', additionStage: 'equivalents', workup: 'product release / work-up', secondaryOxidationProfile: 'secondary NaOCl/acetic-acid medium profile' };

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
    parts.push(`Missing: ${evidence.missingRequiredSettings.map((k) => CONDITION_NAMES[k] ?? k).join(', ')}. Complete the existing condition fields and refresh the options.`);
  }
  if (!evidence.missingRequiredSettings.length || evidence.conditionIssues?.length) parts.push(conciseConditionNote(assessment?.note ?? ''));
  parts.push(evidence.canGenerate3D ? '3D is a conditional net-model conformer, not a verified experimental outcome.'
    : evidence.aldehydeEndpointValidated === false ? 'Conditional 2D remains available. No existing setting enables selective aldehyde 3D; the required profile is not implemented.'
    : 'Conditional 2D remains available. 3D is blocked for the stated conditions or chemistry limitations.');
  return parts.join(' ');
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
