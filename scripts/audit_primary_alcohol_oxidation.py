"""Phase 5C literal net-stage/API specifications, not protocol approval.

Read-only stdout diagnostic. Does not change or replace the frozen benchmark.
"""
import json
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT=Path(__file__).resolve().parents[1]


def run():
    f=json.loads((ROOT/'tests/fixtures/primary-alcohol-oxidation-phase5c.json').read_text());rows=[]
    for case in f['positive']+f['negative']:
        a={'smiles':case['substrate']};b='sodium-hypochlorite';conditions=f['conditions']
        response=service.match_reactions(a,b,conditions)
        found=[r for r in response['reactionOptions'] if r.get('primaryOxidationModel')]
        row={'label':case['label'],'substrate':case['substrate'],'positive':'products' in case,'options':[],'failures':[]}
        expected={Chem.MolToSmiles(Chem.MolFromSmiles(s)) for s in case.get('products',[])}
        if {r['productSmiles'] for r in found}!=expected:row['failures'].append('Literal product-set mismatch')
        if not expected:row['reasons']=response['unsupportedReasons']
        for r in found:
            item={'id':r['id'],'product':r['productSmiles'],'conditionComplete':False,'allow3D':r['assessment']['canRun']}
            try:
                d=service.reaction_diagram(r['id'],a,b,conditions);m=r['primaryOxidationModel']
                identities=lambda side:{x['mapId']:(x['element'],x['formalCharge']) for x in d['atoms'] if x['side']==side}
                # Individual O/Cl charges change; represented element IDs and
                # total charge, not individual atom charges, are conserved.
                before,after=identities('reactants'),identities('products')
                if {k:v[0] for k,v in before.items()}!={k:v[0] for k,v in after.items()} or sum(v[1] for v in before.values())!=sum(v[1] for v in after.values()):raise ValueError('Element/map/charge conservation')
                water=next(i for i,p in enumerate(d['products']) if p['smiles']=='O')
                if {x['mapId'] for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==water}!={m['oxidantOxygen'],m['removedCarbonHydrogen'],m['removedOHHydrogen']}:raise ValueError('Net water provenance')
                if d['mechanism'] is not None or not r['stoichiometry']['balanced']:raise ValueError('Mechanism/stoichiometry contract')
                if r['assessment']['evidence']['conditionCompleteEligibility'] or item['allow3D']:raise ValueError('Unsupported endpoint permission')
                try:service.run_curated_reaction(r['id'],a,b,conditions)
                except service.ChemistryError:item['run']='policy-blocked'
                else:raise ValueError('3D endpoint gate bypass')
                item['diagram']='verified'
            except Exception as exc:row['failures'].append(str(exc))
            row['options'].append(item)
        rows.append(row)
    positive=[r for r in rows if r['positive']]
    return {'phase':'5C','assertionScope':'Literal net structures and API invariants; no independent experimental protocol approval',
            'caseCount':len(rows),'positiveDenominator':len(positive),'structuralMatching':sum(bool(r['options']) for r in positive),
            'conditionCompleteEligibility':0,'fullySupportedProductGeneration':0,'independentlyApprovedProfiles':0,
            'runCounts':dict(Counter(o.get('run','failed') for r in rows for o in r['options'])),
            'failures':[{'label':r['label'],'messages':r['failures']} for r in rows if r['failures']],'results':rows}


if __name__=='__main__':
    RDLogger.DisableLog('rdApp.*');result=run();print(json.dumps(result,indent=2));raise SystemExit(bool(result['failures']))
