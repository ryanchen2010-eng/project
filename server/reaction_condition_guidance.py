"""Read-only guidance for existing bounded reaction models, never permission.

Only serialized, structurally matched reactions enter here. Generation still
calls the original backend assessment, independently of this metadata.
"""
from copy import deepcopy

if __package__:
    from . import secondary_alcohol_oxidation_rule as secondary
    from . import alkyne_partial_hydrogenation_rule as partial
    from .reaction_conditions import assess_conditions
else:
    import secondary_alcohol_oxidation_rule as secondary
    import alkyne_partial_hydrogenation_rule as partial
    from reaction_conditions import assess_conditions


LABELS = {
    'solvent': ('Medium class', {'aqueous-protic': 'Aqueous / protic', 'dry': 'Dry / no water', 'polar-aprotic': 'Polar aprotic', 'ethanolic-protic': 'Ethanol / protic'}),
    'temperature': ('Temperature', {'ambient': 'Room temperature', 'heated': 'Heated'}),
    'catalyst': ('Additional catalyst / activation', {'none': 'None added', 'acid': 'Acid', 'metal': 'Metal (Pd/Pt)', 'lindlar': 'Lindlar', 'osmium': 'Os-based dihydroxylation', 'radical': 'Radical initiation model'}),
    'oxidationStage': ('Oxidation stage', {'first': 'First stage · alcohol → carbonyl', 'further': 'Further oxidation · aldehyde → acid'}),
    'workup': ('Diol release / work-up', {'aqueous-release': 'Aqueous diol release'}),
}


def lindlar_guidance(reaction_id, reaction, assessment, conditions):
    """Guide activation, not solvent/pressure/stopping or multi-site selectivity.

    The target is the existing engine profile, not a new chemistry declaration.
    A prospective read-only call to the same assessor verifies that changing
    just these UI fields can resolve the current gate. Unknown input and
    unvalidated medium/temperature are deliberately NOT cleared by a preset.
    """
    targets = dict(reaction['profile'])
    if targets != {'catalyst': 'lindlar'}:
        return None  # Unknown future model must not inherit this guidance.
    for field in ('oxidationStage', 'workup'):
        if conditions.get(field):
            targets[field] = ''
    issues = assessment.get('conditionIssues', [])
    uneditable = [i for i in issues if i['field'] not in targets]
    competing = reaction['alkynePartialStereo']['singleSiteBookkeepingOnly']
    proposed = deepcopy(conditions)
    proposed.update(targets)
    prospect = assess_conditions(reaction, proposed)
    qualified = assessment['canRun']
    available = not competing and not uneditable and prospect['canRun']
    state = ('outside-profile-scope' if competing else 'qualified' if qualified else
             'unsupported-conditions' if not available else
             'missing-conditions' if not conditions.get('catalyst') and not issues else 'conflicting-conditions')
    requirements = []
    for field, target in targets.items():
        selected = conditions.get(field, '')
        label, choices = LABELS[field]
        requirements.append({'field': field, 'label': label, 'selectedValue': selected, 'requiredValue': target,
                             'selectedLabel': choices.get(selected, 'Not specified' if not selected else 'Unsupported selection'),
                             'requiredLabel': choices.get(target, 'Clear unrelated setting'),
                             'state': 'matches' if selected == target else 'missing' if not selected else 'conflicting'})
    # These fields are intentionally preserved, including explicit unknowns.
    for field, label in [('solvent', 'Medium (preserved)'), ('temperature', 'Temperature (preserved)')]:
        value = conditions.get(field, '')
        text = LABELS[field][1].get(value, 'Not specified' if not value else 'Unsupported selection')
        requirements.append({'field': field, 'label': label, 'selectedValue': value, 'requiredValue': value,
                             'selectedLabel': text, 'requiredLabel': f'{text} · no protocol validation inferred', 'state': 'preserved'})
    messages = {
        'missing-conditions': 'The existing partial-reduction model requires Lindlar activation. Review and confirm this model choice; medium and temperature will not be filled or changed.',
        'conflicting-conditions': 'For partial reduction only: review the replacement activation and any unrelated settings to clear. Keep your current settings if you intend another pathway; ordinary metal, radical or other activation is not the Lindlar model.',
        'qualified': 'Lindlar activation matches the existing bounded net model. Theoretical 3D is available on request; solvent, pressure and stopping conditions are not validated.',
        'outside-profile-scope': 'Several alkyne sites compete. Selecting Lindlar cannot validate selective one-site conversion; only conditional 2D bookkeeping is available.',
        'unsupported-conditions': 'This medium, temperature or additional input is unvalidated for this model. The guide will not erase it or invent a compatible protocol.',
    }
    can_apply = bool(available and not qualified and any(conditions.get(field, '') != value for field, value in targets.items()))
    return {'version': 1, 'reactionId': reaction_id, 'siteId': (reaction.get('site') or {}).get('siteId'),
            'profileId': partial.PATHWAY, 'title': 'Alkyne partial hydrogenation · H₂/Lindlar net model',
            'state': state, 'message': messages[state], 'canApply': can_apply, 'requireConfirmation': True,
            'showOnInitialMatch': False,
            'requirements': requirements, **({'targetConditions': targets} if can_apply else {}),
            'limitations': [*(i['explanation'] for i in issues), partial.LIMITATION,
                            'Evidence supports bounded H₂/Lindlar net syn chemistry, not a fully specified experimental condition profile. A dry or unspecified medium does not validate a named solvent. No companion case is approved by selecting these controls.'],
            'sourceUrl': partial.PRIMARY_SOURCE}


def guidance(reaction_id, reaction, assessment, conditions):
    """No new chemistry assessment, default condition or profile approval."""
    if reaction.get('mechanism') == partial.PATHWAY:
        return lindlar_guidance(reaction_id, reaction, assessment, conditions)
    if reaction.get('primaryOxidationModel'):
        return {'version': 1, 'reactionId': reaction_id, 'state': 'no-validated-profile',
                'title': 'Primary alcohol → aldehyde: no validated profile implemented',
                'message': 'The secondary-ketone profile does not qualify a primary-alcohol aldehyde endpoint. No existing dropdown combination completes a selective aldehyde profile; PCC and Dess–Martin are not implemented.',
                'canApply': False, 'requirements': [], 'limitations': ['Conditional 2D remains available where supported; asserted aldehyde 3D remains blocked.']}
    model = reaction.get('secondaryOxidationModel')
    if not model:
        return None
    targets = dict(secondary.PROFILE_SETTINGS)
    # Only offer to clear a conflicting existing setting after explicit review.
    if conditions.get('workup'):
        targets['workup'] = ''
    requirements = []
    for field, target in targets.items():
        if field == secondary.PROFILE_KEY:
            continue  # The existing medium select represents both declarations.
        selected = conditions.get(field, '')
        valid_string = isinstance(selected, str)
        current = selected if valid_string else 'invalid-input'
        label, choices = LABELS[field]
        state = 'matches' if current == target else 'missing' if current == '' else 'conflicting'
        selected_label = choices.get(current, 'Not specified' if current == '' else 'Unsupported selection')
        required_label = choices.get(target, 'Clear unrelated diol release' if field == 'workup' else target)
        if field == 'solvent':
            profile = secondary.selected_profile(conditions)
            matching = profile == secondary.PROFILE and current == target
            state = 'matches' if matching else 'conflicting' if current or profile != '' else 'missing'
            label = 'Solvent / medium'
            selected_label = ('Aqueous acetic acid · secondary NaOCl' if matching else
                              'Unsupported or conflicting profile declaration' if profile != '' else
                              'Water · polar protic (generic)' if current == 'aqueous-protic' else selected_label)
            required_label = 'Aqueous acetic acid · secondary NaOCl'
        requirements.append({'field': field, 'label': label, 'selectedValue': current, 'requiredValue': target,
                             'selectedLabel': selected_label, 'requiredLabel': required_label, 'state': state})
    issues = assessment.get('conditionIssues', [])
    uneditable = [i for i in issues if i['field'] not in targets]
    in_scope = model['profileScopeEligible']
    qualified = assessment['canRun']
    state = ('outside-profile-scope' if not in_scope else 'qualified' if qualified else
             'unsupported-conditions' if uneditable else 'conflicting-conditions' if issues or any(r['state'] == 'conflicting' for r in requirements) else 'missing-conditions')
    messages = {
        'outside-profile-scope': 'This structure or reagent is outside the qualified secondary NaOCl/acetic-acid model. Changing dropdowns cannot establish the missing chemistry.',
        'qualified': 'Selected settings match the bounded secondary-ketone model. A theoretical 3D conformer is available on request; conversion and isolated yield are not predicted.',
        'unsupported-conditions': 'Additional unsupported condition inputs cannot be repaired by this pilot. Review the backend limitations; no preset can bypass them.',
        'conflicting-conditions': 'A supported model is available, but selected settings conflict or are unvalidated for it. Review every proposed replacement before applying.',
        'missing-conditions': 'A supported model is available. Review its missing settings, then explicitly apply them if this is the model you intend.',
    }
    can_apply = in_scope and not qualified and not uneditable and any(r['state'] != 'matches' for r in requirements)
    return {'version': 1, 'reactionId': reaction_id, 'siteId': (reaction.get('site') or {}).get('siteId'),
            'profileId': secondary.PROFILE, 'title': 'Secondary alcohol → ketone · NaOCl/acetic acid',
            'state': state, 'message': messages[state], 'canApply': can_apply,
            'requirements': requirements, **({'targetConditions': targets} if can_apply else {}),
            'limitations': [*model['qualificationLimitations'], *(i['explanation'] for i in issues),
                            'Bounded theoretical net model, not a laboratory procedure or guarantee of selective conversion. Work-up and isolated recovery are not modeled.'],
            'sourceUrl': model['sourceUrl']}
