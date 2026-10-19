"""Independent Phase 5A net-structure diagnostics, stdout only.

Not imported by production, not a replacement for the frozen 347-case audit,
and not independent approval of an experimental condition profile.
"""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT = Path(__file__).resolve().parents[1]
PATHWAY = "Alcohol dehydration"
canonical = lambda value: Chem.MolToSmiles(Chem.MolFromSmiles(value))


def run():
    fixture = json.loads((ROOT / "tests/fixtures/alcohol-dehydration-phase5a.json").read_text())
    rows = []
    for case in fixture["positive"] + fixture["negative"]:
        a, b, conditions = {"smiles": case["substrate"]}, "sulfuric-acid", fixture["conditions"]
        row = {"label": case["label"], "substrate": case["substrate"], "positive": "products" in case, "options": [], "failures": []}
        response = service.match_reactions(a, b, conditions)
        options = [r for r in response["reactionOptions"] if r["mechanism"] == PATHWAY]
        expected = {canonical(s) for s in case.get("products", [])}
        if {r["productSmiles"] for r in options} != expected:
            row["failures"].append("Independent product-set mismatch")
        for r in options:
            item = {"id":r["id"],"product":r["productSmiles"],"model":r["dehydrationModel"],"allowed3D":r["assessment"]["canRun"]}
            try:
                d = service.reaction_diagram(r["id"],a,b,conditions)
                identity = lambda side: {x["mapId"]:(x["element"],x["formalCharge"]) for x in d["atoms"] if x["side"] == side}
                if identity("reactants") != identity("products") or len(d["atoms"]) != 2*len(identity("reactants")):
                    raise ValueError("Atom/charge correspondence failed")
                m = item["model"]
                water = {x["mapId"] for x in d["atoms"] if x["side"]=="products" and x["speciesIndex"]==1}
                if water != {m["oxygen"],m["originalOHHydrogen"],m["betaHydrogen"]} or d["mechanism"] is not None:
                    raise ValueError("Water provenance or unimplemented-mechanism claim failed")
                if not r["stoichiometry"]["balanced"] or r["stoichiometry"]["context"]["canGenerate3D"] != item["allowed3D"]:
                    raise ValueError("Calculator balance/confidence failed")
                item["diagram"] = "verified"
                try:
                    product = service.run_curated_reaction(r["id"],a,b,conditions)["product"]
                    links = [(x["atomIndex"],x["mapId"]) for x in d["atoms"] if x["side"]=="products" and x["speciesIndex"]==0]
                    if not item["allowed3D"] or product["representation"]!="3d" or links != [(x["index"],x["mapId"]) for x in product["atomLinks"]]:
                        raise ValueError("3D permission or mapped atom correspondence failed")
                    item["run"] = "verified"
                except service.ChemistryError:
                    if item["allowed3D"]: raise
                    item["run"] = "policy-blocked"
            except Exception as exc:
                row["failures"].append(str(exc))
            row["options"].append(item)
        rows.append(row)
    positive = [r for r in rows if r["positive"]]
    return {"phase":"5A","assertionScope":"Independent formal net structures and API invariants; no experimental approval",
            "benchmarkSha256":hashlib.sha256((ROOT/"scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
            "caseCount":len(rows),"positiveDenominator":len(positive),"structuralMatching":sum(bool(r["options"]) for r in positive),
            "casesWithAnyModel3D":sum(any(o["allowed3D"] for o in r["options"]) for r in positive),
            "casesWithAllOptionsModel3D":sum(bool(r["options"]) and all(o["allowed3D"] for o in r["options"]) for r in positive),
            "runCounts":dict(Counter(o.get("run","failed") for r in rows for o in r["options"])),
            "failures":[{"label":r["label"],"messages":r["failures"]} for r in rows if r["failures"]],"results":rows}


if __name__ == "__main__":
    RDLogger.DisableLog("rdApp.*")
    result = run(); print(json.dumps(result,indent=2)); raise SystemExit(bool(result["failures"]))
