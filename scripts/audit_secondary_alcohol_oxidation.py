"""Versioned Phase 5D diagnostic, separate from frozen and approved companion.

Literal product sets and API invariants are checked independently of runtime
permission. A successful replay is not an experimental yield or case approval.
"""
import json
import hashlib
import math
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rdkit import Chem,RDLogger
from server import chemistry_server as service
from scripts import audit_reaction_lab as frozen

ROOT=Path(__file__).resolve().parents[1]
canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s))


def inspect(source,reagent,conditions,expected):
    a,b={'smiles':source},reagent
    response=service.match_reactions(a,b,conditions)
    found=[r for r in response['reactionOptions'] if r.get('secondaryOxidationModel')]
    row={'substrate':source,'reagent':reagent,'conditions':conditions,'options':[],'failures':[],'reasons':response['unsupportedReasons']}
    if {r['productSmiles'] for r in found}!={canonical(s) for s in expected}:row['failures'].append('Independent literal product set differs')
    for r in found:
        ev=r['assessment']['evidence'];item={'id':r['id'],'product':r['productSmiles'],'conditionCompleteEligibility':ev['conditionCompleteEligibility'],
                                          'qualified3D':ev['canGenerate3D'],'profileId':ev['profileId'],'run':'not-run','independentlyApprovedCompanionCase':False}
        try:
            d=service.reaction_diagram(r['id'],a,b,conditions);m=r['secondaryOxidationModel']
            before={x['mapId']:x for x in d['atoms'] if x['side']=='reactants'};after={x['mapId']:x for x in d['atoms'] if x['side']=='products'}
            if {k:v['element'] for k,v in before.items()}!={k:v['element'] for k,v in after.items()} or sum(x['formalCharge'] for x in before.values())!=sum(x['formalCharge'] for x in after.values()):raise ValueError('Atom/map/charge conservation')
            water=next(i for i,p in enumerate(d['products']) if p['smiles']=='O')
            if {x['mapId'] for x in after.values() if x['speciesIndex']==water}!={m['oxidantOxygen'],m['removedCarbonHydrogen'],m['removedOHHydrogen']}:raise ValueError('Actual water hydrogen/oxygen provenance')
            if after[m['oxygen']]['speciesIndex']!=0 or d['mechanism'] is not None:raise ValueError('Original alcohol oxygen or honest net-mechanism representation')
            if not r['stoichiometry']['balanced'] or len(r['stoichiometry']['reactants'])!=2:raise ValueError('Formal redox stoichiometry')
            item['diagram']='verified-conditional-net'
            try:
                p=service.run_curated_reaction(r['id'],a,b,conditions)['product']
                if not ev['canGenerate3D'] or p['representation']!='3d':raise ValueError('Output gate contradiction')
                links=[(x['atomIndex'],x['mapId'],x['element']) for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==0]
                if links!=[(x['index'],x['mapId'],x['element']) for x in p['atomLinks']]:raise ValueError('2D/3D mapped correspondence')
                mol=Chem.MolFromMolBlock(p['molfile'],removeHs=False);by_map={x['mapId']:x['index'] for x in p['atomLinks']}
                carbon=mol.GetAtomWithIdx(by_map[m['carbon']]);conf=mol.GetConformer();origin=conf.GetAtomPosition(carbon.GetIdx())
                vectors=[conf.GetAtomPosition(n.GetIdx())-origin for n in carbon.GetNeighbors()]
                if len(vectors)!=3 or not all(v.Length()>0 for v in vectors):raise ValueError('Ketone center must have three positioned neighbors')
                planarity=abs(vectors[0].CrossProduct(vectors[1]).DotProduct(vectors[2]))/math.prod(v.Length() for v in vectors)
                if not math.isfinite(planarity) or carbon.GetHybridization()!=Chem.HybridizationType.SP2 or carbon.GetChiralTag()!=Chem.ChiralType.CHI_UNSPECIFIED:raise ValueError('Invalid carbonyl geometry or retained tetrahedral stereochemistry')
                carbon_vectors=[conf.GetAtomPosition(n.GetIdx())-origin for n in carbon.GetNeighbors() if n.GetAtomicNum()==6]
                if len(carbon_vectors)!=2:raise ValueError('Ketone must retain two carbon neighbors')
                normal=carbon_vectors[0].CrossProduct(carbon_vectors[1]);oxygen_vector=conf.GetAtomPosition(by_map[m['oxygen']])-origin
                if normal.Length()==0:raise ValueError('Carbonyl neighbor plane is degenerate')
                angle=math.degrees(math.asin(min(1.,abs(normal.DotProduct(oxygen_vector))/(normal.Length()*oxygen_vector.Length()))))
                item['normalizedCarbonylPlanarityDeviation']=planarity
                item['carbonylOutOfPlaneDegrees']=angle
                item['geometryInterpretation']='Descriptive force-field conformer metric, not an independently validated accuracy tolerance or an experimental geometry.'
                item['run']='verified-qualified-net-3D'
            except service.ChemistryError:
                if ev['canGenerate3D']:raise
                item['run']='policy-blocked'
        except Exception as exc:row['failures'].append(str(exc))
        row['options'].append(item)
    return row


def run():
    f=json.loads((ROOT/'tests/fixtures/secondary-alcohol-oxidation-phase5d.json').read_text());rows=[]
    for case in f['positive']+f['negative']:
        row=inspect(case['substrate'],'sodium-hypochlorite',f['profile'],case.get('products',[]));row.update(label=case['label'],positive='products' in case)
        if 'products' in case and any(o['qualified3D']!=case['qualified'] for o in row['options']):row['failures'].append('Independent confidence expectation differs')
        rows.append(row)
    frozen.build_matrix();ids={'A100','A101'};replays=[]
    for i,c in enumerate(frozen.CASES,1):
        case_id=f'A{i:03}'
        if case_id not in ids:continue
        replays.append({'caseId':case_id,'frozenInputProbe':inspect(c['substrate'],c['reagent'],c['conditions'],c['expected']),
                        'declaredProfileReplay':inspect(c['substrate'],c['reagent'],f['profile'],c['expected']),
                        'measurementClass':'condition-aware net diagnostic, not approved experimental benchmark'})
    positives=[r for r in rows if r['positive']]
    failures=[{'label':r['label'],'messages':r['failures']} for r in rows if r['failures']]
    failures.extend({'label':r['caseId']+'/'+key,'messages':r[key]['failures']} for r in replays for key in ['frozenInputProbe','declaredProfileReplay'] if r[key]['failures'])
    return {'schemaVersion':1,'version':'secondary-naocl-acetic-net-diagnostic-1.0.0','phase':'5D',
            'parentSha256':hashlib.sha256((ROOT/'scripts/audit_reaction_lab.py').read_bytes()).hexdigest(),
            'profile':f['profile'],'assertionScope':'Explicit model-condition eligibility, literal net graphs and API invariants; no experimental yields or automatic companion admission',
            'caseCount':len(rows),'positiveDenominator':len(positives),'structuralMatching':sum(bool(r['options']) for r in positives),
            'conditionCompleteModelCases':sum(any(o['conditionCompleteEligibility'] for o in r['options']) for r in positives),
            'casesWithQualifiedNet3D':sum(any(o['qualified3D'] for o in r['options']) for r in positives),
            'independentlyEvidenceSupportedProfile':1,'independentlyApprovedCompanionCases':0,
            'runCounts':dict(Counter(o['run'] for r in rows for o in r['options'])),
            'geometryScope':'SP2 topology and loss of tetrahedral tags are asserted; numeric out-of-plane deviations are reported without inventing a physical accuracy cutoff.',
            'failures':failures,'results':rows,'frozenCaseReplays':replays}


if __name__=='__main__':
    RDLogger.DisableLog('rdApp.*');data=run();print(json.dumps(data,indent=2));raise SystemExit(bool(data['failures']))
