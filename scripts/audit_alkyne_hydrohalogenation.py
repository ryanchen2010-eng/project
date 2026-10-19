"""Independent Phase 4D public workflow; fixed 347-case inputs stay untouched."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT=Path(__file__).resolve().parents[1]
PATHWAY="Alkyne hydrohalogenation"


def canonical(s):
    m=Chem.MolFromSmiles(s)
    if m is None:raise ValueError("Invalid independent diagnostic structure")
    return Chem.MolToSmiles(m)


def inspect(option,source,reagent,conditions):
    row={"id":option["id"],"product":option["productSmiles"],"diagram":"not-run","run":"not-run","failures":[]}
    def check(ok,message):
        if not ok:row["failures"].append(message)
    try:
        d=service.reaction_diagram(option["id"],source,reagent,conditions);row["diagram"]="verified"
        model=option["alkyneHxModel"];n=model["equivalents"]
        check(d["mechanism"] is None,"Unvalidated vinyl-cation/elementary mechanism invented")
        check(len(d["bondsBroken"])==n and len(d["bondsFormed"])==2*n,"HX edit count")
        check([(c["before"],c["after"]) for c in d["bondOrderChanges"]]==[(3,3-n)],"Selected order/stage")
        before=[a for a in d["atoms"] if a["side"]=="reactants"];after=[a for a in d["atoms"] if a["side"]=="products"]
        identity=lambda xs:{a["mapId"]:(a["element"],a["formalCharge"]) for a in xs}
        check(identity(before)==identity(after) and len(identity(before))==len(before)==len(after),"Unique atom/map/charge identity")
        check({frozenset(c["atomMaps"]) for c in d["bondsBroken"]}=={frozenset(p) for p in model["hxPairs"]},"Actual HX provenance")
        expected={frozenset((model["hydrogenCarbon"],h)) for h,_ in model["hxPairs"]}|{frozenset((model["halogenCarbon"],x)) for _,x in model["hxPairs"]}
        check({frozenset(c["atomMaps"]) for c in d["bondsFormed"]}==expected,"H and X target provenance")
        local=[a for a in option["stereochemistry"]["product"]["alkenes"] if set(a["atomMaps"])==set(option["site"]["atomMaps"])]
        check((len(local)==1 and local[0]["assignment"] is None and not local[0]["specified"]) if n==1 and model["internal"] else not local,"Unassigned versus non-applicable E/Z")
        basis=option["stoichiometry"]
        check(basis["balanced"] and sorted(v["coefficient"] for v in basis["reactants"])==[1,n],"Actual equivalent stoichiometry")
        check(abs(sum(v["coefficient"]*v["molarMass"] for v in basis["reactants"])-basis["product"]["molarMass"])<1e-6,"Mass balance")
        check(basis["context"]["canGenerate3D"]==option["assessment"]["canRun"],"Calculator confidence mismatch")
        if not option["assessment"]["canRun"]:
            try:
                service.run_curated_reaction(option["id"],source,reagent,conditions)
                row["run"]="incorrectly-allowed";check(False,"Unvalidated conditional option allowed 3D")
            except service.ChemistryError:row["run"]="blocked"
            return row
        p=service.run_curated_reaction(option["id"],source,reagent,conditions)["product"]
        row["run"]="verified" if p["representation"]=="3d" else "2d-only";row["converged"]=p.get("converged")
        check(p["smiles"]==option["productSmiles"],"3D exact product graph")
        check([(a["atomIndex"],a["mapId"],a["element"]) for a in after]==[(a["index"],a["mapId"],a["element"]) for a in p["atomLinks"]],"2D/3D exact atom correspondence")
    except Exception as exc:row["failures"].append(type(exc).__name__+": "+str(exc))
    return row


def run():
    fixture=json.loads((ROOT/"tests/fixtures/alkyne-hydrohalogenation.json").read_text());rows=[]
    for case in fixture["positive"]+fixture["negative"]:
        for symbol,reagent in (("Cl","hydrogen-chloride"),("Br","hydrogen-bromide"),("I","hydrogen-iodide")):
            for stage in ("one","two"):
                source={"name":"Independent HX diagnostic","smiles":case["substrate"]}
                conditions={"solvent":"dry","temperature":"ambient","additionStage":stage}
                row={"label":case["label"],"substrate":case["substrate"],"halogen":symbol,"stage":stage,"failures":[],"options":[]}
                try:
                    m=service.match_reactions(source,reagent,conditions)
                    found=[r for r in m["reactionOptions"] if r["mechanism"]==PATHWAY]
                    expected={canonical(p.replace("Br",symbol)) for p in case.get(stage,[])}
                    if {r["productSmiles"] for r in found}!=expected:row["failures"].append("Independent constitutional/configuration expectation")
                    allowed=not case.get("oxygen") and not case.get("bookkeepingOnly") and symbol!="Cl" and not(stage=="one" and case.get("internal")) and not(symbol=="I" and stage=="two")
                    if any(r["assessment"]["canRun"]!=bool(allowed) for r in found):row["failures"].append("Reagent/stereo/competition gate")
                    row["options"]=[inspect(r,source,reagent,conditions) for r in found];row["reasons"]=m["unsupportedReasons"]
                except service.ChemistryError as exc:
                    row["reasons"]=[str(exc)]
                    if stage in case:row["failures"].append("Supported independent net input rejected")
                rows.append(row)
    for conditions in ({},{"additionStage":"one"},{"solvent":"dry","additionStage":"one"},{"solvent":"dry","temperature":"ambient"},
                       {"solvent":"aqueous-protic","temperature":"ambient","additionStage":"one"},
                       {"solvent":"ethanolic-protic","temperature":"ambient","additionStage":"two"},
                       {"solvent":"polar-aprotic","temperature":"ambient","additionStage":"one"},
                       {"solvent":"dry","temperature":"ambient","additionStage":"one","catalyst":"radical"},
                       {"solvent":"dry","temperature":"heated","additionStage":"two"}):
        source={"smiles":"CCC#C"}
        found=[r for r in service.match_reactions(source,"hydrogen-bromide",conditions)["reactionOptions"] if r["mechanism"]==PATHWAY]
        rows.append({"label":"conditional-preview","conditions":conditions,"failures":[] if len(found)==1 and not found[0]["assessment"]["canRun"] else ["Invalid condition gate"],
                     "options":[inspect(r,source,"hydrogen-bromide",conditions) for r in found]})
    failures=[{"label":r["label"],"messages":r["failures"]+[m for o in r["options"] for m in o["failures"]]} for r in rows if r["failures"] or any(o["failures"] for o in r["options"])]
    return {"phase":"4D","fixedBenchmarkModified":False,"benchmarkSha256":hashlib.sha256((ROOT/"scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
            "caseCount":len(rows),"optionCount":sum(len(r["options"]) for r in rows),"failures":failures,"results":rows}


if __name__=="__main__":
    RDLogger.DisableLog("rdApp.*")
    result=run();print(json.dumps(result,indent=2));raise SystemExit(1 if result["failures"] else 0)
