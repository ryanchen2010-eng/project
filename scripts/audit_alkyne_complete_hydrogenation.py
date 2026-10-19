"""Independent Phase 4B diagnostics; stdout only, never edits the fixed audit."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from server import chemistry_server as service

ROOT = Path(__file__).resolve().parents[1]
PATHWAY = "Alkyne hydrogenation"


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None: raise ValueError("Invalid independent diagnostic expectation")
    return Chem.MolToSmiles(molecule)


def inspect_option(option, source, conditions):
    row = {"id": option["id"], "product": option["productSmiles"], "diagram": "not-run", "run": "not-run", "failures": []}
    def check(ok, message):
        if not ok: row["failures"].append(message)
    try:
        d = service.reaction_diagram(option["id"], source, "hydrogen", conditions)
        row["diagram"] = "verified"
        check(d["mechanism"] is None, "Unimplemented catalytic mechanism was fabricated")
        before = [a for a in d["atoms"] if a["side"] == "reactants"]
        after = [a for a in d["atoms"] if a["side"] == "products"]
        identity = lambda rows: {a["mapId"]: (a["element"], a["formalCharge"]) for a in rows}
        check(identity(before) == identity(after) and len(identity(before)) == len(before) == len(after), "Atom/map/charge conservation mismatch")
        check(len(d["changes"]) == 7 and len(d["bondsFormed"]) == 4 and len(d["bondsBroken"]) == 2, "Two-H2 edit inventory mismatch")
        check([(c["before"], c["after"]) for c in d["bondOrderChanges"]] == [(3, 1)], "Selected triple bond not fully saturated")
        pairs = option["alkyneCompleteModel"]["hydrogenPairs"]
        check({tuple(sorted(c["atomMaps"])) for c in d["bondsBroken"]} == {tuple(sorted(p)) for p in pairs}, "Actual two-H2 provenance mismatch")
        check(len({m for p in pairs for m in p}) == 4, "Incoming H identity duplicated")
        basis = option["stoichiometry"]
        check(basis["balanced"] and sorted(r["coefficient"] for r in basis["reactants"]) == [1, 2], "Full reduction stoichiometry mismatch")
        check(abs(sum(r["molarMass"] * r["coefficient"] for r in basis["reactants"]) - basis["product"]["molarMass"]) < 1e-6, "Molar-mass balance mismatch")
        check(basis["context"]["canGenerate3D"] == option["assessment"]["canRun"], "Calculator confidence context mismatch")
        check(not any(c["atomMap"] in option["site"]["atomMaps"] for c in option["stereochemistry"]["product"]["chiralCenters"]), "A former alkyne carbon became an invented stereocenter")
    except Exception as exc:
        row["diagram"] = "failed"; row["failures"].append("Diagram: " + str(exc)); return row
    if not option["assessment"]["canRun"]:
        try:
            service.run_curated_reaction(option["id"], source, "hydrogen", conditions)
            row["run"] = "incorrectly-allowed"; row["failures"].append("Unsupported/selective condition gate allowed 3D")
        except service.ChemistryError:
            row["run"] = "blocked"
        return row
    try:
        p = service.run_curated_reaction(option["id"], source, "hydrogen", conditions)["product"]
        row["run"] = "verified" if p["representation"] == "3d" else "2d-only"
        row["converged"] = p.get("converged")
        check(p["smiles"] == option["productSmiles"], "Run product identity mismatch")
        check([(a["atomIndex"], a["mapId"], a["element"]) for a in after] ==
              [(a["index"], a["mapId"], a["element"]) for a in p.get("atomLinks", [])], "2D/3D atom correspondence mismatch")
    except Exception as exc:
        row["run"] = "failed"; row["failures"].append("Run: " + str(exc))
    return row


def run():
    fixture = json.loads((ROOT / "tests/fixtures/alkyne-complete-hydrogenation.json").read_text())
    rows = []
    for case in fixture["positive"] + fixture["negative"]:
        source = {"name": "Independent diagnostic", "smiles": case["substrate"]}
        row = {"label": case["label"], "source": case["substrate"], "failures": [], "options": []}
        expected = {canonical(p) for p in case.get("products", [])}
        try:
            match = service.match_reactions(source, "hydrogen", fixture["conditions"])
            found = [r for r in match["reactionOptions"] if r["mechanism"] == PATHWAY]
            if {r["productSmiles"] for r in found} != expected:
                row["failures"].append("Independent product/configuration expectation mismatch")
            if found and any(r["assessment"]["canRun"] == case.get("bookkeepingOnly", False) for r in found):
                row["failures"].append("Competing multi-site 3D gate mismatch")
            row["options"] = [inspect_option(r, source, fixture["conditions"]) for r in found]
            row["reasons"] = match["unsupportedReasons"]
        except service.ChemistryError as exc:
            row["reasons"] = [str(exc)]
            if expected: row["failures"].append("Supported diagnostic input rejected")
        rows.append(row)
    for condition in [{}, {"catalyst": "none"}, {"catalyst": "lindlar"}, {"catalyst": "radical"}, {"catalyst": "acid"},
                      {"catalyst": "osmium"}, {"catalyst": "metal", "temperature": "heated"},
                      {"catalyst": "metal", "solvent": "aqueous-protic"}, {"catalyst": "metal", "solvent": "polar-aprotic"}]:
        source = {"smiles": "CC#CC"}
        found = [r for r in service.match_reactions(source, "hydrogen", condition)["reactionOptions"] if r["mechanism"] == PATHWAY]
        rows.append({"label": "conditional-preview", "conditions": condition,
                     "failures": [] if len(found) == 1 and not found[0]["assessment"]["canRun"] else ["Invalid condition gate"],
                     "options": [inspect_option(r, source, condition) for r in found]})
    failures = [{"label": r["label"], "messages": r["failures"] + [m for o in r["options"] for m in o["failures"]]}
                for r in rows if r["failures"] or any(o["failures"] for o in r["options"])]
    return {"phase": "4B", "fixedBenchmarkModified": False,
            "benchmarkSha256": hashlib.sha256((ROOT / "scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
            "caseCount": len(rows), "optionCount": sum(len(r["options"]) for r in rows), "failures": failures, "results": rows}


if __name__ == "__main__":
    RDLogger.DisableLog("rdApp.*")
    result = run()
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["failures"] else 0)
