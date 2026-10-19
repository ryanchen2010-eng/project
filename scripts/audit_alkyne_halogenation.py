"""Independent Phase 4C public-workflow diagnostic; never edits fixed scoring."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT = Path(__file__).resolve().parents[1]
PATHWAY = "Alkyne halogenation"


def connectivity(smiles):
    m=Chem.MolFromSmiles(smiles)
    if m is None: raise ValueError("Invalid independent diagnostic expectation")
    for b in m.GetBonds(): b.SetStereo(Chem.BondStereo.STEREONONE); b.SetBondDir(Chem.BondDir.NONE)
    return Chem.MolToSmiles(m)


def inspect(option, source, reagent, conditions):
    row={"id":option["id"],"product":option["productSmiles"],"diagram":"not-run","run":"not-run","failures":[]}
    def check(ok,message):
        if not ok: row["failures"].append(message)
    try:
        d=service.reaction_diagram(option["id"],source,reagent,conditions)
        row["diagram"]="verified"
        check(d["mechanism"] is None,"Unvalidated halonium/carbocation mechanism was invented")
        n=option["alkyneHalogenModel"]["equivalents"]
        check(len(d["bondsFormed"])==2*n and len(d["bondsBroken"])==n,"X2 net edit count")
        check([(v["before"],v["after"]) for v in d["bondOrderChanges"]]==[(3,3-n)],"Stage bond-order mismatch")
        before=[a for a in d["atoms"] if a["side"]=="reactants"]
        after=[a for a in d["atoms"] if a["side"]=="products"]
        identity=lambda rows:{a["mapId"]:(a["element"],a["formalCharge"]) for a in rows}
        check(identity(before)==identity(after) and len(identity(before))==len(before)==len(after),"Atom/map/charge identity")
        pairs=option["alkyneHalogenModel"]["halogenPairs"]
        check({frozenset(v["atomMaps"]) for v in d["bondsBroken"]}=={frozenset(p) for p in pairs},"Actual halogen provenance")
        local=[v for v in option["stereochemistry"]["product"]["alkenes"] if set(v["atomMaps"])==set(option["site"]["atomMaps"])]
        assigned=option["alkyneHalogenModel"]["stereoAssignment"]
        check((len(local)==1 and local[0]["assignment"]==assigned) if n==1 else not local,"Stage-specific CIP assignment")
        basis=option["stoichiometry"]
        check(basis["balanced"] and sorted(v["coefficient"] for v in basis["reactants"])==[1,n],"Equivalent stoichiometry")
        check(abs(sum(v["molarMass"]*v["coefficient"] for v in basis["reactants"])-basis["product"]["molarMass"])<1e-6,"Mass conservation")
        check(basis["context"]["canGenerate3D"]==option["assessment"]["canRun"],"Calculator confidence")
        if not option["assessment"]["canRun"]:
            try:
                service.run_curated_reaction(option["id"],source,reagent,conditions)
                row["run"]="incorrectly-allowed"; check(False,"Unsupported selective 3D allowed")
            except service.ChemistryError: row["run"]="blocked"
            return row
        p=service.run_curated_reaction(option["id"],source,reagent,conditions)["product"]
        row["run"]="verified" if p["representation"]=="3d" else "2d-only"
        row["converged"]=p.get("converged")
        check(p["smiles"]==option["productSmiles"],"3D graph identity")
        check([(a["atomIndex"],a["mapId"],a["element"]) for a in after]==[(a["index"],a["mapId"],a["element"]) for a in p["atomLinks"]],"Exact 2D/3D atom correspondence")
    except Exception as exc:
        row["failures"].append(type(exc).__name__+": "+str(exc))
    return row


def run():
    f=json.loads((ROOT/"tests/fixtures/alkyne-halogenation.json").read_text()); rows=[]
    for case in f["positive"]+f["negative"]:
        for halogen,reagent in (("Br","bromine"),("Cl","chlorine")):
            for stage in ("one","two"):
                source={"name":"Independent X2 diagnostic","smiles":case["substrate"]}
                conditions={"solvent":"dry","additionStage":stage}
                row={"label":case["label"],"substrate":case["substrate"],"halogen":halogen,"stage":stage,"failures":[],"options":[]}
                try:
                    m=service.match_reactions(source,reagent,conditions)
                    found=[r for r in m["reactionOptions"] if r["mechanism"]==PATHWAY]
                    expected={connectivity(p.replace("Br",halogen)) for p in case.get(stage,[])}
                    if {connectivity(r["productSmiles"]) for r in found}!=expected:row["failures"].append("Independent product/configuration expectation")
                    allowed=not case.get("bookkeepingOnly") and (halogen=="Br" or stage=="two" and not case.get("oxygen"))
                    if any(r["assessment"]["canRun"]!=allowed for r in found):row["failures"].append("Condition/multi-site/stereo gate")
                    row["options"]=[inspect(r,source,reagent,conditions) for r in found]
                    row["reasons"]=m["unsupportedReasons"]
                except service.ChemistryError as exc:
                    row["reasons"]=[str(exc)]
                    if stage in case:row["failures"].append("Supported independent input rejected")
                rows.append(row)
    for conditions in ({},{"solvent":"dry"},{"additionStage":"one"},{"solvent":"aqueous-protic","additionStage":"one"},
                       {"solvent":"ethanolic-protic","additionStage":"two"},{"solvent":"polar-aprotic","additionStage":"one"},
                       {"solvent":"dry","additionStage":"one","catalyst":"radical"},{"solvent":"dry","additionStage":"two","catalyst":"metal"},
                       {"solvent":"dry","additionStage":"one","temperature":"heated"}):
        source={"smiles":"CC#CC"}
        found=[r for r in service.match_reactions(source,"bromine",conditions)["reactionOptions"] if r["mechanism"]==PATHWAY]
        rows.append({"label":"conditional-preview","conditions":conditions,"failures":[] if len(found)==1 and not found[0]["assessment"]["canRun"] else ["Invalid condition gate"],
                     "options":[inspect(r,source,"bromine",conditions) for r in found]})
    failures=[{"label":r["label"],"messages":r["failures"]+[m for o in r["options"] for m in o["failures"]]} for r in rows if r["failures"] or any(o["failures"] for o in r["options"])]
    return {"phase":"4C","fixedBenchmarkModified":False,"benchmarkSha256":hashlib.sha256((ROOT/"scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
            "caseCount":len(rows),"optionCount":sum(len(r["options"]) for r in rows),"failures":failures,"results":rows}


if __name__=="__main__":
    RDLogger.DisableLog("rdApp.*")
    result=run(); print(json.dumps(result,indent=2)); raise SystemExit(1 if result["failures"] else 0)
