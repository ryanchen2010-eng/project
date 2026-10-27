"""Read-only guidance for existing bounded reaction models, never permission.

Only serialized, structurally matched reactions enter here. Generation still
calls the original backend assessment, independently of this metadata.
"""
from copy import deepcopy
if __package__:
    from . import reaction_temperature_profiles as profiles
else:
    import reaction_temperature_profiles as profiles

if __package__:
    from . import secondary_alcohol_oxidation_rule as secondary
    from . import alkyne_partial_hydrogenation_rule as partial
    from .reaction_conditions import assess_conditions
    from .reaction_temperature_profiles import COOLED_PERBENZOIC_MODEL, COOLED_PERBENZOIC_SOURCES
else:
    import secondary_alcohol_oxidation_rule as secondary
    import alkyne_partial_hydrogenation_rule as partial
    from reaction_conditions import assess_conditions
    from reaction_temperature_profiles import COOLED_PERBENZOIC_MODEL, COOLED_PERBENZOIC_SOURCES


LABELS = {
    'solvent': ('Medium class', {'aqueous-protic': 'Aqueous / protic', 'dry': 'Dry / no water', 'polar-aprotic': 'Polar aprotic', 'ethanolic-protic': 'Ethanol / protic'}),
    'temperature': ('Temperature', {'cooled': 'Cooled / Low Temperature', 'ambient': 'Room temperature', 'heated': 'Heated'}),
    'catalyst': ('Additional Catalyst / Activation', {'none': 'None Added', 'acid': 'Acid Activation / Catalysis', 'metal': 'Metal Catalyst (Pd/Pt)', 'lindlar': 'Lindlar Catalyst', 'osmium': 'Os-Based Dihydroxylation Catalyst', 'radical': 'Radical Initiation (Supported Model)'}),
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


def perbenzoic_guidance(reaction_id, reaction, assessment, conditions):
    """Expose the named medium assumption through existing confirmed guidance.

    Never change temperature, clear unknown fields/stages or bypass a substrate
    rejection. This is theoretical model selection, not an experimental recipe.
    """
    review = assessment.get('cooling', {})
    targets = {'solvent': 'dry', 'catalyst': 'none'}
    proposed = deepcopy(conditions)
    proposed.update(targets)
    prospect = assess_conditions(reaction, proposed)
    available = prospect.get('canRun') is True
    qualified = assessment.get('canRun') is True
    outside = any(i['field'] in {'substrateProfile', 'reagentIdentity'} for i in review.get('conditionIssues', []))
    state = ('outside-profile-scope' if outside else 'qualified' if qualified else
             'unsupported-conditions' if not available else
             'missing-conditions' if not conditions.get('solvent') else 'conflicting-conditions')
    requirements = []
    for field, target in targets.items():
        selected = conditions.get(field, '')
        label, choices = LABELS[field]
        matches = selected == target or field == 'catalyst' and selected == ''
        requirements.append({'field': field, 'label': label, 'selectedValue': selected, 'requiredValue': target,
                             'selectedLabel': choices.get(selected, 'Not specified'),
                             'requiredLabel': 'Dry / no water · assume the chloroform-reference net model' if field == 'solvent' else 'None Added · no extra activation',
                             'state': 'matches' if matches else 'missing' if not selected else 'conflicting'})
    requirements.append({'field': 'temperature', 'label': 'Temperature (preserved)', 'selectedValue': 'cooled',
                         'requiredValue': 'cooled', 'selectedLabel': 'Cooled / Low Temperature',
                         'requiredLabel': 'Cooled / Low Temperature · qualitative reference, not a measured temperature', 'state': 'preserved'})
    messages = {
        'qualified': 'The bounded perbenzoic-acid net model matches. It assumes the documented chloroform medium; Dry / no water is not an entered or verified experimental solvent.',
        'outside-profile-scope': 'This substrate is outside the bounded cooled perbenzoic-acid profile. Changing condition fields cannot establish missing substrate evidence; the broader existing non-cooled peracid rule is not changed.',
        'unsupported-conditions': 'Other stage or unsupported inputs remain unresolved. This guide will not erase them, change temperature or infer a compatible experimental formulation.',
        'missing-conditions': 'Review the named chloroform-reference theoretical assumption and the missing medium setting. Nothing is filled until you confirm and apply.',
        'conflicting-conditions': 'The current medium or activation differs from this bounded model. Review and confirm replacements only if you intend the chloroform-reference theoretical assumption.',
    }
    can_apply = available and not qualified and any(conditions.get(field, '') != value for field, value in targets.items())
    return {'version': 1, 'reactionId': reaction_id, 'siteId': (reaction.get('site') or {}).get('siteId'),
            'profileId': COOLED_PERBENZOIC_MODEL, 'title': 'Cooled perbenzoic acid · chloroform-reference net model',
            'state': state, 'message': messages[state], 'canApply': bool(can_apply), 'requireConfirmation': True,
            'showOnInitialMatch': False, 'requirements': requirements,
            **({'targetConditions': targets} if can_apply else {}),
            'limitations': ['The source documents styrene; saturated ring-alkyl variants are a bounded modeling inference, not separately verified cold experiments.',
                            'Dry / no water selects the named chloroform-reference assumption, not validation of every dry solvent. No exact experimental solvent or numerical temperature is entered.',
                            'Theoretical product conformer only—not a temperature simulation, a laboratory procedure or a guarantee of conversion, epoxide isolation, rates, yields or face populations.',
                            'Actual benzoic acid remains in the equation. Post-reaction acid removal and work-up are not represented.',
                            *(i['explanation'] for i in review.get('conditionIssues', []))],
            'sourceUrl': COOLED_PERBENZOIC_SOURCES[0]}


def guidance(reaction_id, reaction, assessment, conditions):
    """No new chemistry assessment, default condition or profile approval."""
    if reaction.get('mechanism') == 'Alkene dihydroxylation' and conditions.get('temperature') == 'cooled':
        return dihydroxylation_r3_guidance(reaction_id, reaction, assessment, conditions)
    if conditions.get('temperature') == 'cooled' and reaction.get('mechanism') == 'Hydrogenation':
        return cyclohexene_guidance(reaction_id, reaction, assessment, conditions)
    if conditions.get('temperature') == 'cooled' and assessment.get('cooling', {}).get('modelId') == COOLED_PERBENZOIC_MODEL:
        return perbenzoic_guidance(reaction_id, reaction, assessment, conditions)
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


def cyclohexene_guidance(reaction_id, reaction, assessment, conditions):
    """Existing confirmed guide selects a reference; never an experiment."""
    if profiles.cyclohexene_scope_issue(reaction):
        return None
    targets = {'solvent': 'dry', 'catalyst': 'metal', 'conditionProfileId': profiles.COOLED_CYCLOHEXENE_MODEL,
               'conditionProfileVersion': '1'}
    proposed = deepcopy(conditions)
    proposed.update(targets)
    prospective = profiles.assess_cooling_support(reaction, proposed, {})
    available = prospective['canGenerate3D']
    qualified = assessment.get('canRun') is True and assessment.get('cooling', {}).get('modelId') == profiles.COOLED_CYCLOHEXENE_MODEL
    selected = profiles.reference(conditions)
    # Unknown/obsolete selections must be cleared deliberately, never overwritten
    # by a preset. Other valid selected profiles can be explicitly replaced.
    if selected and (profiles.selected_profile(conditions) is None or selected['version'] != '1'):
        available = False
    requirements = []
    for field in ('solvent', 'catalyst'):
        current = conditions.get(field, '')
        label, choices = LABELS[field]
        requirements.append({'field': field, 'label': label, 'selectedValue': current, 'requiredValue': targets[field],
            'selectedLabel': choices.get(current, 'Not specified'), 'requiredLabel': choices[targets[field]],
            'state': 'matches' if current == targets[field] else 'conflicting' if current else 'missing'})
    requirements.append({'field': 'conditionProfileId', 'label': 'Named condition model',
        'selectedValue': (selected or {}).get('id', ''), 'requiredValue': profiles.COOLED_CYCLOHEXENE_MODEL,
        'selectedLabel': (selected or {}).get('id', 'No exact catalyst/pressure model selected'),
        'requiredLabel': 'Pd/silica catalyst A · hexane · 0 °C · reported 1.1 MPa H₂ reference (not entered measurements)',
        'state': 'matches' if qualified else 'conflicting' if selected else 'missing'})
    state = 'qualified' if qualified else 'missing-conditions' if available else 'unsupported-conditions'
    return {'version': 1, 'reactionId': reaction_id, 'siteId': (reaction.get('site') or {}).get('siteId'),
        'profileId': profiles.COOLED_CYCLOHEXENE_MODEL, 'title': 'Cooled cyclohexene · Pd/silica-A reference',
        'state': state, 'message': 'Review this exact source-reference model. Selecting it assumes the documented catalyst, hexane and H₂ conditions; generic Pd/Pt alone does not qualify. Temperature is preserved.',
        'canApply': bool(available and not qualified), 'requireConfirmation': True, 'showOnInitialMatch': False,
        'requirements': requirements, **({'targetConditions': targets} if available and not qualified else {}),
        'limitations': ['Only cyclohexene + actual H₂ → cyclohexane; not substituted rings, Pd/C, Pt, alkynes or carbonyls.',
            '0 °C and 1.1 MPa H₂ are fixed documented reference observations, not measured inputs or a continuous operating window. The pressure basis is not stated.',
            'The source uses pretreated 5 wt% Pd on dual-pore silica catalyst A. Other catalyst formulations are not equivalent.',
            'The 15-minute analytical endpoint is not complete conversion, an isolated yield or a prediction. Calculators remain theoretical complete-conversion arithmetic.',
            'Theoretical conformer only—not a temperature/pressure simulation, laboratory procedure, rate/yield or selectivity guarantee.',
            *([prospective['note']] if not available else [])],
        'sourceUrl': profiles.CYCLOHEXENE_SOURCE,
        'profileDescriptor': profiles.describe(profiles.PROFILES_BY_ID[profiles.COOLED_CYCLOHEXENE_MODEL])}


def dihydroxylation_r3_guidance(reaction_id, reaction, assessment, conditions):
    from rdkit import Chem
    if __package__: from . import cooled_dihydroxylation_r3 as r3
    else: import cooled_dihydroxylation_r3 as r3
    molecule = Chem.MolFromSmiles(reaction.get('dihydroxylationSubstrateIdentity', ''))
    model = r3.model_for_substrate(molecule) if molecule is not None else None
    if model is None or r3.scope_issue(reaction, model): return None
    targets = {'solvent':'dry','catalyst':'osmium','workup':model.workup,
        'conditionProfileId':model.identifier,'conditionProfileVersion':'1'}
    proposed = deepcopy(conditions); proposed.update(targets)
    available = r3.endpoint_assessment(reaction, proposed)['canRun']
    qualified = assessment.get('canRun') is True and assessment.get('cooling', {}).get('modelId') == model.identifier
    selected = profiles.reference(conditions)
    if selected and (profiles.selected_profile(conditions) is None or selected['version'] != '1'): available = False
    requirements = []
    for key in ('solvent','catalyst','workup'):
        value = conditions.get(key, '')
        label, choices = LABELS[key]
        requirements.append({'field':key,'label':label,'selectedValue':value,'requiredValue':targets[key],
            'selectedLabel':choices.get(value,'No separate declaration'),
            'requiredLabel':'Named tert-butanol reagent reference' if key=='solvent' else
                'Exact source OsO4 solution reference' if key=='catalyst' else
                'Source water-based free-acid recovery' if model.workup else 'Named fractionated free glycol; NOT aqueous release',
            'state':'matches' if value==targets[key] else 'conflicting' if value else 'missing'})
    requirements.append({'field':'conditionProfileId','label':'Named condition model',
        'selectedValue':(selected or {}).get('id',''),'requiredValue':model.identifier,
        'selectedLabel':(selected or {}).get('id','No exact source model selected'), 'requiredLabel':model.title,
        'state':'matches' if qualified else 'conflicting' if selected else 'missing'})
    return {'version':1,'reactionId':reaction_id,'siteId':reaction.get('site',{}).get('siteId'),
        'profileId':model.identifier,'title':model.title,'state':'qualified' if qualified else 'missing-conditions' if available else 'unsupported-conditions',
        'message':'Review the exact source formulation and recovery. The named endpoint is separate from the legacy aqueous-release assumption; temperature is preserved.',
        'canApply':bool(available and not qualified),'requireConfirmation':True,'showOnInitialMatch':False,
        'requirements':requirements, **({'targetConditions':targets} if available and not qualified else {}),
        'limitations':[model.recovery,'0 C overnight is a source observation, not a simulated range or exact hour count.',
            'Theoretical net product only; actual conversion, isolated yield, purity, rates and mixtures are not predicted.',
            *([] if available else [r3.endpoint_assessment(reaction, proposed)['note']])],
        'sourceUrl':r3.SOURCE,'profileDescriptor':profiles.describe(profiles.PROFILES_BY_ID[model.identifier])}
