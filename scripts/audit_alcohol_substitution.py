"""Independent Phase 5B net/API diagnostic; not a benchmark replacement.

Literal product expectations are development specifications, not admission of
an experimentally validated HX concentration/medium/activation protocol.
"""
import json
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT=Path(__file__).resolve().parents[1]
PATHWAY='Alcohol substitution'
canonical=lambda s:Chem.MolToSmiles(Chem.MolFromSmiles(s))


def run():
    fixture=json.loads((ROOT/'tests/fixtures/alcohol-substitution-phase5b.json').read_text());rows=[]
    for case in fixture['positive']+fixture['negative']:
        a={'smiles':case['substrate']};b=case.get('reagent','hydrogen-bromide');c={'temperature':case.get('temperature','heated')}
        row={'label':case['label'],'substrate':case['substrate'],'positive':'products' in case,'options':[],'failures':[]}
        response=service.match_reactions(a,b,c);found=[r for r in response['reactionOptions'] if r['mechanism']==PATHWAY]
        if {r['productSmiles'] for r in found}!={canonical(s) for s in case.get('products',[])}:row['failures'].append('Independent net product-set mismatch')
        if 'products' not in case:row['reasons']=response['unsupportedReasons']
        for r in found:
            m=r['alcoholSubstitutionModel'];item={'id':r['id'],'product':r['productSmiles'],'allow3D':r['assessment']['canRun'],'model':m,'run':'not-run'}
            try:
                if item['allow3D']!=case['allow3D']:raise ValueError('Independent confidence specification disagrees')
                d=service.reaction_diagram(r['id'],a,b,c)
                identity=lambda side:{x['mapId']:(x['element'],x['formalCharge']) for x in d['atoms'] if x['side']==side}
                if identity('reactants')!=identity('products') or len(d['atoms'])!=2*len(identity('reactants')):raise ValueError('Atom/charge conservation failed')
                water={x['mapId'] for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==1}
                if water!={m['oxygen'],m['originalOHHydrogen'],m['reagentHydrogen']} or d['mechanism'] is not None:raise ValueError('Water maps or honest mechanism representation failed')
                if not r['stoichiometry']['balanced'] or len(r['stoichiometry']['reactants'])!=2 or r['stoichiometry']['excludedInputs']:raise ValueError('HX consumption/stoichiometry failed')
                item['diagram']='verified'
                try:
                    p=service.run_curated_reaction(r['id'],a,b,c)['product']
                    links=[(x['atomIndex'],x['mapId']) for x in d['atoms'] if x['side']=='products' and x['speciesIndex']==0]
                    if not item['allow3D'] or p['representation']!='3d' or links!=[(x['index'],x['mapId']) for x in p['atomLinks']]:raise ValueError('3D gate/correspondence failed')
                    item['run']='verified'
                except service.ChemistryError:
                    if item['allow3D']:raise
                    item['run']='policy-blocked'
            except Exception as exc:row['failures'].append(str(exc))
            row['options'].append(item)
        rows.append(row)
    positive=[r for r in rows if r['positive']]
    return {'phase':'5B','assertionScope':'Independent formal net structures/API invariants, not experimental protocols','caseCount':len(rows),
            'positiveDenominator':len(positive),'structuralMatching':sum(bool(r['options']) for r in positive),
            'casesWithAnyNet3D':sum(any(o['allow3D'] for o in r['options']) for r in positive),
            'runCounts':dict(Counter(o['run'] for r in rows for o in r['options'])),
            'failures':[{'label':r['label'],'messages':r['failures']} for r in rows if r['failures']],'results':rows}


if __name__=='__main__':
    RDLogger.DisableLog('rdApp.*');result=run();print(json.dumps(result,indent=2));raise SystemExit(bool(result['failures']))
