"""Primary-only confidence and validation over the preserved Phase 2C net edit.

No new oxidant/catalyst profile. Current hypochlorite selectors cannot certify
an aldehyde endpoint, so primary net stages are conditional 2D only.
"""
from rdkit import Chem
if __package__:
    from . import alcohol_oxidation_rule as base, molecular_graph as graph, stereochemistry as stereo
else:
    import alcohol_oxidation_rule as base, molecular_graph as graph, stereochemistry as stereo

SOURCE = "https://www.orgsyn.org/demo.aspx?prep=CV8P0367"
SELECTIVITY_LIMIT = ("No aldehyde-selective hypochlorite condition profile is implemented; no existing selector completes one. "
                     "Generic aqueous/aprotic medium, first-stage selection or ambient temperature does not establish catalyst/formulation, "
                     "pH, oxidant supply, residence time or aldehyde release. These controls cannot confirm stopping at an aldehyde; "
                     "use the conditional 2D first-stage equation, not an asserted final 3D product.")


def is_primary(mol, site):
    return (len(site) == 2 and len(set(site)) == 2 and all(type(i) is int and 0 <= i < mol.GetNumAtoms() for i in site)
            and tuple(site) in base.sites(mol) and base.classification(mol, site) == "primary")


def sites(mol):
    return [site for site in base.sites(mol) if is_primary(mol, site)]


def assess(mol, site):
    report = base.assess(mol, site)
    if not is_primary(mol, site) or mol.GetAtomWithIdx(site[0]).GetHybridization() != Chem.HybridizationType.SP3 or graph.attached_hydrogens(mol.GetAtomWithIdx(site[0])) < 2:
        report['rejections'].append({'code':'primary-site','category':'structural','message':'Select a primary (or methyl) saturated C–OH with at least two carbon-bound H; secondary/tertiary sites do not use this primary-only layer.','atomIndices':list(site)})
        report['eligible'] = False
    report['primaryStageOnly'] = True
    return report


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized, 'primary alcohol oxidation')
    if issue: return issue
    parser = Chem.SmilesParserParams(); parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None: return 'Primary alcohol oxidation cannot validate supplied stereochemistry.'
    a = [x for x in raw.GetAtoms() if x.GetAtomicNum() != 1]; b = [x for x in normalized.GetAtoms() if x.GetAtomicNum() != 1]
    if len(a) != len(b) or any(x.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED and (x.GetChiralTag() not in stereo.TETRAHEDRAL or y.GetChiralTag() not in stereo.TETRAHEDRAL) for x,y in zip(a,b)):
        return 'Invalid specified primary-alcohol stereo cannot be silently removed in normalization.'
    if any(b.GetBondDir() != Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return 'Directional annotations without a valid C=C are unsupported in primary alcohol oxidation.'
    return None


def participants(substrate, reagent, site):
    carbon, oxygen = (substrate.GetAtomWithIdx(i) for i in site)
    oxidant_o, chlorine = base.oxidant_atoms(reagent)
    hydrogens = lambda atom: [n.GetAtomMapNum() for n in atom.GetNeighbors() if n.GetAtomicNum() == 1]
    ch, oh = hydrogens(carbon), hydrogens(oxygen)
    if len(ch) < 2 or len(oh) != 1: raise ValueError('Primary oxidation requires actual mapped alcohol O–H and at least two C–H atoms.')
    return {'carbon':carbon.GetAtomMapNum(),'oxygen':oxygen.GetAtomMapNum(),
            'removedCarbonHydrogen':ch[0],'removedOHHydrogen':oh[0],
            'oxidantOxygen':oxidant_o.GetAtomMapNum(),'chlorine':chlorine.GetAtomMapNum()}


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report['eligible']: raise ValueError(' '.join(r['message'] for r in report['rejections']))
    # The Phase 2C redox edits, charge contract and physical stereo validator
    # are reused without broadening secondary or other pathway permissions.
    base.validate(before, after, substrate, reagent, site)
    p = participants(substrate, reagent, site); atoms = {a.GetAtomMapNum():a for a in after.GetAtoms()}
    carbon, oxygen = atoms[p['carbon']], atoms[p['oxygen']]
    if (after.GetBondBetweenAtoms(carbon.GetIdx(),oxygen.GetIdx()).GetBondTypeAsDouble() != 2
            or carbon.GetHybridization() != Chem.HybridizationType.SP2 or carbon.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
            or oxygen.GetFormalCharge() or oxygen.GetDegree() != 1
            or sum(n.GetAtomicNum() == 1 for n in carbon.GetNeighbors()) != sum(n.GetAtomicNum() == 1 for n in substrate.GetAtomWithIdx(site[0]).GetNeighbors())-1):
        raise ValueError('The selected primary C–OH must become its original-oxygen planar aldehyde, not an acid, retained tetrahedron or invented hydrogens.')
    water = {p['oxidantOxygen'],p['removedCarbonHydrogen'],p['removedOHHydrogen']}
    if not any({a.GetAtomMapNum() for a in f.GetAtoms()} == water for f in Chem.GetMolFrags(after,asMols=True)):
        raise ValueError('Removed C–H/O–H hydrogen atoms must form net water with the actual hypochlorite oxygen; no H2 gas is produced.')


def metadata(substrate, reagent, product, site, report):
    p = participants(substrate,reagent,site)
    return {**p,'version':1,'stage':'primary-alcohol-to-aldehyde-net-stage','aldehydeEndpointValidated':False,
            'selectiveOxidantProfileImplemented':False,'conditionCompleteEligibility':False,
            'experimentalChemistryStatus':'not-independently-certified-at-runtime',
            'competingAlcoholSites':[[substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in g['atomIndices']] for g in report['groups'] if g['type']=='alcohol' and g['disposition']=='alternative-site'],
            'spectatorAssumptions':[g['explanation'] for g in report['groups'] if g['disposition'] in {'preserved','alternative-site'}],
            'provenance':'Original alcohol oxygen remains in the formal aldehyde. Two removed H form water with hypochlorite O, and actual counterion/chloride are retained. This is net bookkeeping, not a catalyst mechanism or solution isotope history.',
            'endpointLimitation':SELECTIVITY_LIMIT,'mappedMechanism':'unsupported'}


def assess_conditions(reaction, conditions):
    model = reaction['primaryOxidationModel']
    missing = [k for k in ('solvent','oxidationStage') if not conditions.get(k)]
    known = {'solvent','temperature','catalyst','oxidationStage','additionStage','polymerUnits','workup'}
    unknown = set(getattr(conditions,'unsupported_fields',())) | (set(conditions)-known)
    issues = [{'field':k,'kind':'unsupported','explanation':f"Condition field '{k}' is not implemented for primary alcohol oxidation; no selective chemistry is inferred."} for k in sorted(unknown)]
    medium = conditions.get('solvent',''); catalyst = conditions.get('catalyst','')
    if medium and medium != 'aqueous-protic':
        issues.append({'field':'solvent','kind':'unvalidated-alternative','explanation':'A dry, alcoholic or generic polar-aprotic setting is not a validated selective hypochlorite formulation and does not substitute PCC or Dess–Martin chemistry.'})
    if catalyst not in {'','none'}:
        issues.append({'field':'catalyst','kind':'unsupported' if catalyst=='radical' else 'unvalidated-alternative','explanation':'Added acid/metal/radical activation does not establish a selective primary-alcohol oxidant. TEMPO/PCC/periodinane profiles and their reagent-specific chemistry are not implemented. Do not mix household chemicals.'})
    if conditions.get('temperature') == 'heated':
        issues.append({'field':'temperature','kind':'unvalidated-alternative','explanation':'Heated oxidation has unresolved further oxidation/chlorination/cleavage risks; no aldehyde stopping point is asserted.'})
    for key in ('workup',):
        if conditions.get(key): issues.append({'field':key,'kind':'conflicting','explanation':'The diol-release workup selector is not an implemented aldehyde isolation/quench model.'})
    if conditions.get('oxidationStage') not in {'','first'}:
        issues.append({'field':'oxidationStage','kind':'conflicting','explanation':'Further oxidation starts from an aldehyde in a separate pathway; direct alcohol-to-acid conversion is not implemented.'})
    not_applicable = [k for k in ('additionStage','polymerUnits') if conditions.get(k)]
    note = ' '.join([SELECTIVITY_LIMIT,
                     *(['Missing existing model settings: '+', '.join(missing)+'.'] if missing else []),
                     *(i['explanation'] for i in issues),
                     *(['Other primary/secondary alcohol sites can also oxidize. The selected site is a net alternative, not experimentally selective mono-oxidation.'] if model['competingAlcoholSites'] else []),
                     *(['Alkyne equivalents/finite-chain length are not applicable and do not change this one-stage redox equation.'] if not_applicable else []),
                     'First stage describes a formal aldehyde, not its isolation. Aqueous hypochlorite permits overoxidation risk; pH, catalyst/formulation, exposure, supply and release are unresolved. No acid product, selectivity, rate or experimental yield is predicted. Do not mix household chemicals.'])
    return {'state':'alternative' if any(i['field']=='solvent' for i in issues) else 'incomplete',
            'status':'unsupported-pathway' if any(i['kind']=='unsupported' for i in issues) else 'missing' if missing else 'unevaluated',
            'label':'Aldehyde endpoint not established','confidenceLabel':'Hypothetical aldehyde stage · conditional 2D only',
            'canRun':False,'missingSettings':missing,'conditionIssues':issues,'notApplicableSettings':not_applicable,'referenceDifferences':[],
            'reagentValidated':True,'reagentRequirement':'Actual alkali-metal hypochlorite, consumed in the formal redox stage',
            'activationRequirement':'No implemented aldehyde-selective condition profile; no existing selector completes one',
            'conditionCompleteEligibility':False,'note':note,'factors':{
                'solvent':{'status':'missing' if not medium else 'unevaluated','effect':'unknown','explanation':'Aqueous oxidation does not establish an aldehyde endpoint; alternative solvent names are not selective protocols.'},
                'oxidationStage':{'status':'missing' if not conditions.get('oxidationStage') else 'unevaluated','effect':'unknown','explanation':'First stage is a requested net structure, not suppression of further oxidation.'},
                'aldehyde selectivity':{'status':'unevaluated','effect':'unknown','explanation':SELECTIVITY_LIMIT},
                'competing alcohol sites':{'status':'unevaluated','effect':'unknown','explanation':'Other alcohols are not automatically inert or selectively protected.'}}}


def equivalent_sites(mol,left,right):
    work = Chem.Mol(mol)
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    return any(tuple(match[i] for i in left)==tuple(right) for match in work.GetSubstructMatches(work,uniquify=False,useChirality=True,maxMatches=1024))
