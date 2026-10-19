"""Confidence for the EXISTING hypochlorite neutral-acid reporting graph.

No new reagent, transformation, isolated-acid work-up or speciation model.
Rendering this reporting structure never establishes the solution's protonation
state. Structural matching and mapped edits remain owned by reaction_engine.
"""
if __package__:
    from . import molecular_graph as graph
else:
    import molecular_graph as graph

PATHWAY = 'Aldehyde oxidation'
REPORTING_LIMIT = ('Neutral carboxylic acid reporting form only; pH, acid/carboxylate speciation and isolated acid work-up are not established. '
                   'A carboxylate or an acidification step is not silently generated. No complete mapped oxidation mechanism is implemented.')


def metadata(substrate):
    """Describe competition without granting or expanding structural matches."""
    competing = []
    if len(graph.find_aldehydes(substrate)) > 1:
        competing.append('Several aldehyde sites can oxidize; selective one-site conversion is unresolved.')
    if graph.find_alcohols(substrate):
        competing.append('Additional alcohol groups can oxidize; their selective preservation is unresolved.')
    if graph.find_ketones(substrate):
        competing.append('Additional ketone/halogenation chemistry has no validated spectator model here.')
    return {'version': 1, 'reportingForm': 'neutral-carboxylic-acid', 'solutionSpeciationEstablished': False,
            'acidWorkupImplemented': False, 'mappedMechanism': 'unsupported', 'competition': competing}


def assess_conditions(reaction, conditions):
    required = {'solvent': 'aqueous-protic', 'oxidationStage': 'further'}
    missing = [k for k in required if not conditions.get(k)]
    known = {'solvent', 'oxidationStage', 'temperature', 'catalyst', 'workup', 'additionStage', 'polymerUnits'}
    unknown = set(getattr(conditions, 'unsupported_fields', ())) | (set(conditions) - known)
    issues = [{'field': k, 'kind': 'unsupported', 'explanation': f"Setting '{k}' is not implemented for aldehyde oxidation; it cannot qualify this reporting product."} for k in sorted(unknown)]
    for k, wanted in required.items():
        value = conditions.get(k, '')
        if value and value != wanted:
            issues.append({'field': k, 'kind': 'conflicting' if k == 'oxidationStage' else 'unvalidated-alternative',
                           'explanation': 'Select Further oxidation for an aldehyde, not the alcohol first stage.' if k == 'oxidationStage' else
                           'This existing aqueous net model requires Water / polar protic. Other media are unvalidated here, not chemically impossible.'})
    catalyst = conditions.get('catalyst', '')
    if catalyst not in {'', 'none'}:
        issues.append({'field': 'catalyst', 'kind': 'unsupported' if catalyst == 'radical' else 'unvalidated-alternative',
                       'explanation': 'Radical activation is not the implemented aldehyde oxidation model.' if catalyst == 'radical' else
                       'Added activation is unvalidated for this hypochlorite reporting model; it does not establish acid work-up.'})
    if conditions.get('temperature') not in {'', 'ambient'}:
        issues.append({'field': 'temperature', 'kind': 'unvalidated-alternative',
                       'explanation': 'Heated aldehyde oxidation and side chemistry are not qualified by this existing net model.'})
    if conditions.get('workup'):
        issues.append({'field': 'workup', 'kind': 'conflicting',
                       'explanation': 'Aqueous diol release is not acidification or carboxylic-acid isolation. No acid work-up model is implemented.'})
    competition = reaction.get('aldehydeOxidationModel', {}).get('competition', [])
    allowed = not missing and not issues and not competition
    status = 'unsupported-pathway' if any(i['kind'] == 'unsupported' for i in issues) else 'missing' if missing else 'unevaluated' if issues or competition else 'model-match'
    note = ' '.join(['Existing aldehyde-to-acid net reporting transformation.',
                     *(['Missing required settings: ' + ', '.join(missing) + '.'] if missing else []),
                     *(i['explanation'] for i in issues), *competition, REPORTING_LIMIT,
                     'Theoretical reporting conformer only; conversion is not predicted.' if allowed else
                     'Only conditional 2D reporting is available for these inputs.'])
    factors = {i['field']: {'status': 'unsupported-pathway' if i['kind'] == 'unsupported' else 'unevaluated',
                            'effect': 'unknown', 'explanation': i['explanation']} for i in issues}
    return {'state': 'aligned' if allowed else 'incomplete', 'status': status,
            'label': 'Neutral-acid reporting model' if allowed else 'Aldehyde oxidation conditions unresolved',
            'confidenceLabel': 'Neutral-acid reporting conformer · speciation/work-up not established' if allowed else 'Conditional acid reporting preview · 2D only',
            'canRun': allowed, 'missingSettings': missing, 'conditionIssues': issues, 'referenceDifferences': [], 'note': note,
            'notApplicableSettings': [k for k in ('additionStage', 'polymerUnits') if conditions.get(k)],
            'reagentValidated': True, 'reagentRequirement': 'actual alkali-metal hypochlorite, consumed in the net equation',
            'workupRepresented': False, 'workupAssumptionConfirmed': False,
            'factors': {**{k: {'status': 'missing' if not conditions.get(k) else 'model-match' if conditions[k] == wanted else 'unevaluated',
                             'effect': 'unknown', 'explanation': f'{k}={wanted} is a net reporting requirement, not experimental certification.'} for k, wanted in required.items()},
                        **factors,
                        'temperature': factors.get('temperature', {'status': 'unevaluated', 'effect': 'unknown', 'explanation': 'Ambient/unspecified temperature preserves the existing net convention; exact temperature and kinetics are not established.'}),
                        'speciation / isolation': {'status': 'unevaluated', 'effect': 'unknown', 'explanation': REPORTING_LIMIT},
                        'competing chemistry': {'status': 'unevaluated', 'effect': 'unknown', 'explanation': ' '.join(competition) or 'Other experimental pathways, conversion and product distributions are not predicted.'}}}
