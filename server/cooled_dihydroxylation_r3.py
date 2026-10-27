"""R3 source-specific free-product contracts, not an Os catalytic mechanism.

Selection accepts a documented reference assumption, never measured conditions.
No omitted catalyst/release species are treated as elementary mapped atoms.
"""
from dataclasses import dataclass
from types import MappingProxyType
from rdkit import Chem
if __package__:
    from .named_condition_profiles import descriptor, fact
else:
    from named_condition_profiles import descriptor, fact

SOURCE = 'https://doi.org/10.1021/ja01298a065'
ISOBUTYLENE = 'cooled-isobutylene-os-peroxide-v1'
CROTONIC = 'cooled-crotonic-os-peroxide-v1'
CINNAMIC = 'cooled-cinnamic-os-peroxide-v1'


@dataclass(frozen=True)
class Model:
    identifier: str
    substrate: str
    product: str
    title: str
    workup: str
    recovery: str
    peroxide_percent: str
    substrate_g: float
    substrate_mol: float
    peroxide_ml: float
    catalyst_ml: float
    isolated_g: float
    yield_percent: float
    yield_basis: str


MODELS = MappingProxyType({ISOBUTYLENE: Model(ISOBUTYLENE, 'C=C(C)C', 'CC(C)(O)CO',
    'Isobutylene · OsO4/H2O2 · tert-butanol reference', '',
    'Direct fractionation; collected 176–178 C free glycol fraction. No aqueous addition is documented for this experiment.',
    '6.62%', 4.3, 0.0768, 39.3, 0.75, 2.6, 37.6, 'theoretical amount from the initial substrate charge'),
    CROTONIC: Model(CROTONIC, 'CC=CC(=O)O', 'CC(O)C(O)C(=O)O',
        'Crotonic acid · OsO4/H2O2 · tert-butanol reference', 'aqueous-release',
        'Reduced-pressure solvent removal, residue taken up with water; unchanged crotonic acid extracted with chloroform; aqueous portion evaporated to free hydroxy-acid syrup.',
        '6.3%', 4.3, 0.05, 27.2, 1, 1.2, 53.8, 'crotonic acid consumed, after recovery of 2.7 g unchanged acid'),
    CINNAMIC: Model(CINNAMIC, 'O=C(O)C=Cc1ccccc1', 'O=C(O)C(O)C(O)c1ccccc1',
        'Cinnamic acid · OsO4/H2O2 · tert-butanol reference', 'aqueous-release',
        'Vacuum solvent removal, residue taken up with water; unchanged cinnamic acid filtered off; filtrate distilled under reduced pressure to noncrystallized semisolid free phenylglyceric acid.',
        '6.3%', 3.7, 0.025, 13.6, 2, 0.9, 56.2, 'cinnamic acid consumed, after recovery of 2.4 g unchanged acid')})


def identity(molecule):
    work = Chem.Mol(molecule)
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.RemoveHs(work), canonical=True, isomericSmiles=True)


def model_for_substrate(molecule):
    key = identity(molecule)
    return next((m for m in MODELS.values() if m.substrate == key), None)


def structural_reference(molecule, conditions):
    """Only a cold exact-parent preview or explicitly selected exact reference.

    This authorizes structural validation, not condition confidence or 3D.
    General non-cooled and other substrates keep their old compatibility rules.
    """
    model = model_for_substrate(molecule)
    if model and (conditions.get('temperature') == 'cooled' and not conditions.get('conditionProfileId')
            or conditions.get('conditionProfileId') == model.identifier and conditions.get('conditionProfileVersion') == '1'):
        return model.identifier
    return None


def scope_issue(reaction, model):
    if (reaction.get('mechanism') != 'Alkene dihydroxylation'
            or reaction.get('dihydroxylationSubstrateIdentity') != model.substrate
            or reaction.get('dihydroxylationReagentIdentity') != 'OO'
            or reaction.get('productSmiles') != model.product or reaction.get('byproducts')):
        return 'This exact named Os/H2O2 reference requires its documented substrate, actual neutral H2O2 and free product; other substrates, oxidants, configured outcomes or salt endpoints are not qualified.'
    report = reaction.get('compatibility', {})
    if (not report.get('eligible') or not report.get('validation')
            or set(report['validation'].values()) != {'verified'}
            or report.get('substrateSiteMaps') != (reaction.get('site') or {}).get('atomMaps')):
        return 'Existing mapped atom, charge, unaffected-bond and stereochemistry validation must pass independently.'
    return None


def endpoint_assessment(reaction, conditions):
    """A separate explicit release contract; never silently waive aqueous release."""
    model = MODELS.get(conditions.get('conditionProfileId'))
    if model is None or conditions.get('conditionProfileVersion') != '1': return None
    issues = []
    note = scope_issue(reaction, model)
    if note: issues.append({'field': 'substrateProfile', 'kind': 'unsupported', 'explanation': note})
    required = {'temperature': 'cooled', 'solvent': 'dry', 'catalyst': 'osmium', 'workup': model.workup}
    for key, expected in required.items():
        if conditions.get(key, '') != expected:
            issues.append({'field': key, 'kind': 'conflicting', 'explanation':
                f'The {model.title} requires {key}={expected or "no separate aqueous-release declaration"}; selections are not silently cleared or reinterpreted.'})
    known = {'temperature', 'solvent', 'catalyst', 'workup', 'oxidationStage', 'additionStage', 'polymerUnits', 'conditionProfileId', 'conditionProfileVersion'}
    for key in sorted(set(getattr(conditions, 'unsupported_fields', ())) | (set(conditions)-known)):
        issues.append({'field': key, 'kind': 'unsupported', 'explanation': f'Unmodeled field {key} cannot override the fixed source formulation or free-product endpoint.'})
    if conditions.get('oxidationStage'):
        issues.append({'field': 'oxidationStage', 'kind': 'conflicting', 'explanation': 'No additional oxidation stage, cleavage or predicted endpoint mixture is included.'})
    release = {'version': 1, 'id': model.identifier + ':release', 'selection': 'explicit-named-profile',
        'endpoint': 'source-identified neutral free product', 'observedRecovery': model.recovery,
        'aqueousReleaseAssumed': bool(model.workup), 'workupSimulated': False, 'sourceUrl': SOURCE, 'sourcePage': 1303}
    explanation = ('Explicit named free-product reporting contract: ' + model.recovery +
        ' This is an observed recovery reference, not a simulated release, catalyst cycle, protocol, complete conversion or isolated-yield prediction.')
    return {'state': 'incomplete' if issues else 'aligned', 'status': 'unevaluated' if issues else 'model-match',
        'label': 'Named release conditions unresolved' if issues else 'Named free-product reference matches',
        'canRun': not issues, 'note': ' '.join(i['explanation'] for i in issues) if issues else explanation,
        'missingSettings': [], 'referenceDifferences': [], 'conditionIssues': issues,
        'reagentRequirement': 'actual neutral H2O2', 'reagentValidated': not bool(scope_issue(reaction, model)),
        'activationRequirement': 'Exact source OsO4/tert-butanol formulation and explicit named release contract',
        'workupRepresented': False, 'workupAssumptionConfirmed': bool(model.workup),
        'productReleaseAssumptionConfirmed': not issues, 'productRelease': release,
        'factors': {key: {'status': 'model-match' if conditions.get(key, '') == expected else 'unevaluated',
            'effect': 'unknown', 'explanation': explanation if key == 'workup' else 'Fixed source-reference assumption, not measured or simulated conditions.'}
            for key, expected in required.items()}}


def cooling_support(reaction, conditions, assessment, review):
    model = MODELS[conditions['conditionProfileId']]
    checked = endpoint_assessment(reaction, conditions)
    review.update(modelId=model.identifier, sourceUrls=[SOURCE], profileLabel=model.title,
        temperatureScope='Documented 0 C overnight reaction; exact hours, continuous range and isolation temperature are not inferred.')
    if (not checked['canRun'] or assessment.get('canRun') is not True
            or assessment.get('conditionIssues') or not assessment.get('productReleaseAssumptionConfirmed')):
        review.update(status='conditions-unresolved', conditionIssues=checked['conditionIssues'] or assessment.get('conditionIssues') or
            [{'field':'workup','kind':'unsupported','explanation':'The independently checked named release contract is unresolved.'}], note=checked['note'])
    else:
        review.update(status='supported-model', canGenerate3D=True,
            note=model.title + '. ' + checked['note'] + ' Cooled 3D is a theoretical product conformer, not a temperature simulation or experimental outcome. Unspecified stereocenters remain unassigned in the product identity; the single displayed geometry is not a stereochemical prediction. Formal H2O2 O/H mapping is net bookkeeping, not elementary Os oxygen cycling or proton provenance. No experimental yield, rate or stereo ratio is predicted.')
    return review


def description(model):
    return descriptor([
        fact('reagents', {'substrate':model.substrate, 'oxidant':'actual neutral H2O2', 'reportedPeroxide':model.peroxide_percent,
            'referenceSubstrateG':model.substrate_g, 'referenceSubstrateMol':model.substrate_mol, 'referenceReagentMl':model.peroxide_ml},
            'source-observation', 'source formulation, not calculator dosing or an elementary mechanism', 'p. 1303'),
        fact('catalyst', {'identity':'OsO4 in tert-butanol', 'reportedStock':'0.5%', 'referenceVolumeMl':model.catalyst_ml,
            'basis':'stock strength explicitly stated for isobutylene; same solution catalyst cross-reference for other experiments'},
            'source-observation' if model.identifier == ISOBUTYLENE else 'model-assumption',
            'Explicit 0.5% source stock, not every Os catalyst.' if model.identifier == ISOBUTYLENE else
            'Source solution catalyst cross-reference; 0.5% is not repeated in the acid paragraph. Not every Os catalyst, ligand or co-oxidant.', 'pp. 1302–1303'),
        fact('medium', {'identity':'source-described anhydrous tert-butanol/peroxide reagent',
            **({'additionalTertButanolG':36.3} if model.identifier == ISOBUTYLENE else
               {'additionalTertButanolMl':13.6,'volumeBasis':'equal to the stated reagent volume; derived from the source wording, not separately measured'} if model.identifier == CINNAMIC else
               {'additionalTertButanol':'no separate addition stated in this paragraph'})},
            'source-observation', 'named reference; dry does not mean any dry solvent or quantitatively zero water', 'pp. 1302–1303'),
        fact('thermalHistory', {'reactionC':0, 'duration':'overnight; following day', 'hours':None, 'rangeValidated':False},
            'source-observation', 'subsequent isolation is not a 0 C operation', 'p. 1303'),
        fact('hydrogenPressure', None, 'not-applicable', 'No H2 is consumed'),
        fact('additives', 'No extra reaction additive chemistry is modeled; stock drying agents are preparation context, not consumed net species',
            'model-assumption', 'source reagent preparation is not simulated', 'p. 1302'),
        fact('productRelease', {'endpoint':model.product, 'recovery':model.recovery, 'isolatedG':model.isolated_g,
            'reportedYieldPercent':model.yield_percent, 'yieldBasis':model.yield_basis},
            'source-observation', 'not a forecast, conversion percentage, purity certification or laboratory instructions', 'p. 1303')],
        [{'url':SOURCE,'locator':'Milas–Sussman (1936), pp. 1302 preparation/catalyst; 1303 specific experiment; 1304 summary'}],
        ['Explicit profile selection accepts a fixed source reference, not entered experimental measurements.',
         'Only the exact parent and neutral free-product net endpoint are admitted.',
         'H2O2 supplies formal balanced O/H inventory; catalyst cycling and release species are omitted.'],
        ['Percentage bases, quantitatively residual water, exact overnight duration and complete catalyst state are not specified.',
         'The general prepared stock is 6.32%, not silently equated to every 6.3% or 6.62% experiment.',
         *(['Starting E/Z geometry and product configurations are not explicitly assigned in this acid experiment; only unconfigured identities are in scope.'] if model.workup else []),
         'Actual conversion, isolated purity, yields, rates, mixture composition and temperature dependence are not predicted.'])
