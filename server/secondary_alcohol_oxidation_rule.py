"""Secondary-only NaOCl/AcOH net model; no new oxidant or elementary mechanism.

Evidence: Stevens, Chapman, Weller, JOC 1980, 45, 2030–2032,
doi:10.1021/jo01298a066. Qualification is bounded model permission,
not an isolated-product, conversion, isotope-history or safety prediction.
"""
from rdkit import Chem
if __package__:
    from . import alcohol_oxidation_rule as base, molecular_graph as graph, stereochemistry as stereo
else:
    import alcohol_oxidation_rule as base, molecular_graph as graph, stereochemistry as stereo

SOURCE = 'https://pubs.acs.org/doi/10.1021/jo01298a066'
FULL_TEXT = 'https://ursula.chem.yale.edu/~chem220/PROBSETS/PS13spr/PS9-S13-ans/Stevens1980JOC.pdf'
PROFILE_KEY = 'secondaryOxidationProfile'
PROFILE = 'naocl-acetic-ketone-v1'
# The existing Phase 5D requirements, shared by assessment and read-only UI
# guidance. Moving these literals here does not change generation permission.
PROFILE_SETTINGS = {PROFILE_KEY: PROFILE, 'solvent': 'aqueous-protic',
                    'temperature': 'ambient', 'catalyst': 'none', 'oxidationStage': 'first'}


def is_secondary(mol, site):
    return (len(site) == 2 and len(set(site)) == 2 and all(type(i) is int and 0 <= i < mol.GetNumAtoms() for i in site)
            and tuple(site) in base.sites(mol) and base.classification(mol, site) == 'secondary')


def sites(mol):
    return [s for s in base.sites(mol) if is_secondary(mol,s)]


def assess(mol, site):
    report = base.assess(mol,site)
    if not is_secondary(mol,site) or mol.GetAtomWithIdx(site[0]).GetHybridization() != Chem.HybridizationType.SP3 or graph.attached_hydrogens(mol.GetAtomWithIdx(site[0])) != 1:
        report['eligible'] = False
        report['rejections'].append({'code':'secondary-site','category':'structural','message':'Select an ordinary saturated secondary C–OH with two carbon neighbors and one carbon-bound H; primary/tertiary sites do not use this layer.','atomIndices':list(site)})
    return report


def input_stereo_issue(smiles, normalized):
    issue = stereo.stereo_scope_issue(normalized,'secondary alcohol oxidation')
    if issue:return issue
    parser=Chem.SmilesParserParams();parser.sanitize=False;parser.removeHs=False
    raw=Chem.MolFromSmiles(smiles,parser)
    if raw is None:return 'Secondary alcohol oxidation cannot validate supplied stereo.'
    a=[x for x in raw.GetAtoms() if x.GetAtomicNum()!=1];b=[x for x in normalized.GetAtoms() if x.GetAtomicNum()!=1]
    if len(a)!=len(b) or any(x.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED and (x.GetChiralTag() not in stereo.TETRAHEDRAL or y.GetChiralTag() not in stereo.TETRAHEDRAL) for x,y in zip(a,b)):
        return 'Invalid secondary-alcohol stereo cannot be silently removed during normalization.'
    if any(b.GetBondDir()!=Chem.BondDir.NONE for b in raw.GetBonds()) and not graph.find_alkenes(normalized):
        return 'Directional annotations without a valid C=C are unsupported in secondary alcohol oxidation.'
    return None


def participants(substrate,reagent,site):
    carbon,oxygen=(substrate.GetAtomWithIdx(i) for i in site)
    oxidant_o,chlorine=base.oxidant_atoms(reagent)
    ch=[n for n in carbon.GetNeighbors() if n.GetAtomicNum()==1];oh=[n for n in oxygen.GetNeighbors() if n.GetAtomicNum()==1]
    if len(ch)!=1 or len(oh)!=1:raise ValueError('Secondary oxidation requires one actual mapped C–H and O–H.')
    return {'carbon':carbon.GetAtomMapNum(),'oxygen':oxygen.GetAtomMapNum(),'removedCarbonHydrogen':ch[0].GetAtomMapNum(),
            'removedOHHydrogen':oh[0].GetAtomMapNum(),'oxidantOxygen':oxidant_o.GetAtomMapNum(),'chlorine':chlorine.GetAtomMapNum()}


def validate(before,after,substrate,reagent,site):
    report=assess(substrate,site)
    if not report['eligible']:raise ValueError(' '.join(r['message'] for r in report['rejections']))
    base.validate(before,after,substrate,reagent,site)
    p=participants(substrate,reagent,site);atoms={a.GetAtomMapNum():a for a in after.GetAtoms()}
    c,o=atoms[p['carbon']],atoms[p['oxygen']]
    if (c.GetHybridization()!=Chem.HybridizationType.SP2 or c.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED
            or after.GetBondBetweenAtoms(c.GetIdx(),o.GetIdx()).GetBondTypeAsDouble()!=2
            or any(n.GetAtomicNum()==1 for n in c.GetNeighbors()) or o.GetFormalCharge() or o.GetDegree()!=1
            or sum(n.GetAtomicNum()==6 for n in c.GetNeighbors())!=2):
        raise ValueError('The selected secondary center must become its original-oxygen planar ketone without a C–H or tetrahedral tag.')
    water={p['oxidantOxygen'],p['removedCarbonHydrogen'],p['removedOHHydrogen']}
    if not any({a.GetAtomMapNum() for a in f.GetAtoms()}==water for f in Chem.GetMolFrags(after,asMols=True)):
        raise ValueError('Actual removed C–H/O–H atoms must form formal water with hypochlorite O, not invented H2.')


def metadata(substrate,reagent,product,site,report):
    limitations=[]
    metal=next(a.GetSymbol() for a in reagent.GetAtoms() if a.GetSymbol() in {'Li','Na','K','Rb','Cs'})
    if metal!='Na':limitations.append('The reviewed medium profile is sodium hypochlorite only; another counterion retains a formal 2D equation, not transferred protocol validation.')
    if sum(a.GetAtomicNum()==8 for a in substrate.GetAtoms())!=1:
        limitations.append('Additional alcohol/ether oxygen has no qualified inertness or selective one-site oxidation under this acidic profile; conditional 2D only.')
    if any(a.GetIsAromatic() for a in substrate.GetAtoms()):limitations.append('Aromatic/benzylic spectator chlorination and acidic compatibility need separate profile validation.')
    rings=list(substrate.GetRingInfo().AtomRings())
    if len(rings)>1 or any(len(r) not in {5,6,7} for r in rings):limitations.append('This qualified scope is acyclic or a single saturated five-to-seven-membered ring; other ring environments remain net-only.')
    return {**participants(substrate,reagent,site),'version':1,'stage':'secondary-alcohol-to-ketone-net-stage','profileId':PROFILE,
            'profileScopeEligible':not limitations,'qualificationLimitations':limitations,'counterion':metal,
            'competingAlcoholSites':[[substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in g['atomIndices']] for g in report['groups'] if g['type']=='alcohol' and g['disposition']=='alternative-site'],
            'provenance':'Original alcohol oxygen stays in the ketone; actual C–H/O–H hydrogen atoms form formal water with hypochlorite O. The actual counterion/chloride remain. Solution proton exchange and isotope history are not modeled.',
            'sourceUrl':SOURCE,'mappedMechanism':'unsupported','profileEvidence':'Independent primary reference supports the bounded secondary NaOCl/acetic-acid net model; runtime graph validation is not experimental certification.'}


def selected_profile(conditions):
    return getattr(conditions,'secondary_oxidation_profile',conditions.get(PROFILE_KEY,''))


def assess_conditions(reaction,conditions):
    m=reaction['secondaryOxidationModel'];selection=selected_profile(conditions)
    required={k:v for k,v in PROFILE_SETTINGS.items() if k!=PROFILE_KEY}
    missing=[k for k in required if not conditions.get(k)]
    if not selection:missing.insert(0,PROFILE_KEY)
    issues=[]
    unknown=set(getattr(conditions,'unsupported_fields',())) | (set(conditions)-{'solvent','temperature','catalyst','oxidationStage','additionStage','polymerUnits','workup',PROFILE_KEY})
    unknown.discard(PROFILE_KEY)
    for k in sorted(unknown):issues.append({'field':k,'kind':'unsupported','explanation':f"Condition field '{k}' is not implemented for secondary oxidation; it cannot certify ketone formation."})
    if selection != '' and selection!=PROFILE:issues.append({'field':PROFILE_KEY,'kind':'unsupported','explanation':'The selected secondary oxidation profile is not implemented; no PCC, DMP or TEMPO system is substituted.'})
    for key,wanted in required.items():
        value=conditions.get(key,'')
        if value and value!=wanted:
            issues.append({'field':key,'kind':'conflicting' if key in {'oxidationStage','solvent'} else 'unvalidated-alternative',
                           'explanation':f'This bounded secondary NaOCl/acetic-acid profile requires {key}={wanted}; {value} is not qualified by this model, not proof the reaction is impossible.'})
    if conditions.get('workup'):issues.append({'field':'workup','kind':'conflicting','explanation':'Diol aqueous-release is not a ketone isolation/quench model. This pathway represents net ketone formation, not isolated workup products.'})
    allowed=not missing and not issues and m['profileScopeEligible']
    note=('Select Aqueous acetic acid · secondary NaOCl in the existing medium menu, Room temperature, None added activation and First stage. '
          'This explicitly declares the bounded NaOCl/AcOH net model; generic Water alone does not. '
          'Controlled oxidation is a model assumption, not measured exposure or a laboratory procedure. Workup/recovery species and isolated yield are not modeled. '
          +' '.join(i['explanation'] for i in issues)+' '+' '.join(m['qualificationLimitations'])+
          ' Prolonged/excess or different-pH halogenation, haloform/cleavage and actual conversion are not predicted. Do not mix household chemicals.')
    return {'state':'aligned' if allowed else 'alternative' if issues else 'incomplete',
            'status':'model-match' if allowed else 'unsupported-pathway' if any(i['kind']=='unsupported' for i in issues) else 'missing' if missing else 'unevaluated',
            'label':'Qualified secondary ketone net model' if allowed else 'Secondary ketone conditions unresolved',
            'confidenceLabel':'NaOCl/AcOH ketone net model · theoretical 3D' if allowed else 'Hypothetical ketone stage · conditional 2D only',
            'canRun':allowed,'missingSettings':missing,'conditionIssues':issues,'referenceDifferences':[],
            'notApplicableSettings':[k for k in ('additionStage','polymerUnits') if conditions.get(k)],
            'conditionCompleteEligibility':allowed,'profileSelection':selection if isinstance(selection,str) and len(selection)<=80 else 'invalid-profile-input',
            'reagentValidated':True,'note':note,'factors':{
                **{k:{'status':'model-match' if conditions.get(k)==v else 'missing' if not conditions.get(k) else 'unevaluated','effect':'neutral' if conditions.get(k)==v else 'unknown','explanation':f'{k}={v} is a bounded model requirement, not experimental validation.'} for k,v in required.items()},
                PROFILE_KEY:{'status':'model-match' if selection==PROFILE else 'missing' if not selection else 'unsupported-pathway','effect':'neutral' if selection==PROFILE else 'unknown','explanation':'Acetic-acid medium must be explicitly declared; a generic protic solvent is not the same profile.'},
                'competing chemistry':{'status':'model-match' if m['profileScopeEligible'] else 'unevaluated','effect':'neutral' if m['profileScopeEligible'] else 'unknown','explanation':' '.join(m['qualificationLimitations']) or 'Bounded sodium/mono-oxygen saturated substrate scope; no experimental product distribution is claimed.'}}}


def equivalent_sites(mol,left,right):
    work=Chem.Mol(mol)
    for a in work.GetAtoms():a.SetAtomMapNum(0)
    return any(tuple(match[i] for i in left)==tuple(right) for match in work.GetSubstructMatches(work,uniquify=False,useChirality=True,maxMatches=1024))


def evidence(reaction,assessment,conditions):
    allowed=assessment['canRun'];missing=assessment['missingSettings'];issues=assessment['conditionIssues']
    return {'version':1,'structuralEligibility':'eligible','reagentIdentity':'validated','assertionLevel':'conditional-net','experimentalOutcome':'not-predicted',
            'label':assessment['confidenceLabel'],'requiredSettings':[PROFILE_KEY,'solvent','temperature','catalyst','oxidationStage'],
            'missingRequiredSettings':missing,'requirementsState':'assumptions-satisfied' if allowed else 'missing' if missing else 'not-evaluated',
            'conditionCompleteness':'model-assumptions-only' if allowed else 'unsupported-input' if any(i['kind']=='unsupported' for i in issues) else 'conflicting-input' if issues else 'incomplete' if missing else 'not-evaluated',
            'conditionCompleteEligibility':allowed,'conditionIssues':issues,'notApplicableSettings':assessment['notApplicableSettings'],
            'unknownConditions':[] if allowed else [k for k,v in assessment['factors'].items() if v['status']!='model-match'],
            'evaluatedFactors':assessment['factors'],'canPreview2D':True,'canGenerate3D':allowed,
            'renderingPolicy':'qualified-secondary-net-conformer' if allowed else 'secondary-condition-or-scope-gate',
            'renderingNote':'A qualified ketone conformer is a theoretical net structure, not measured conversion, isolation or a complete experimental protocol.',
            'profileId':PROFILE,'chemistryCorrectness':{'status':'evidence-supported-bounded-model','sourceUrl':SOURCE,'scope':'Secondary ketone net chemistry reviewed independently of software tests; no runtime or universal experimental certification.'}}


def calculation_context(reaction,assessment,conditions,notes):
    fact=assessment['evidence']
    return {'version':1,'assertionLevel':'conditional-net','pathway':reaction['mechanism'],'label':fact['label'],'conditionStatus':assessment['status'],
            'conditions':{**dict(conditions),PROFILE_KEY:assessment['profileSelection']},'missingRequiredSettings':fact['missingRequiredSettings'],
            'unknownConditions':fact['unknownConditions'],'canGenerate3D':fact['canGenerate3D'],
            'assumptions':['Explicit secondary NaOCl/acetic-acid net profile only; formation is theoretical, not isolated yield or a laboratory protocol.',
                           *(i['explanation'] for i in assessment['conditionIssues']),*reaction['secondaryOxidationModel']['qualificationLimitations'],*notes],
            'warning':'Theoretical secondary oxidation amounts only: one alcohol and one actual hypochlorite formula unit give ketone, water and actual chloride salt in the formal net equation. Full salt mass is counted. Acetic-acid medium is not a consumed third reactant. Complete conversion is assumed, not predicted; alternatives are not additive yields. No H2 gas, isolated yield, exposure/halogenation control or selective oxidation of other sites is established by arithmetic. Workup species and solution proton exchange are not mapped; this is not a laboratory procedure.'}
