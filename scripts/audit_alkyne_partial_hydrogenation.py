"""Separate Phase 4A diagnostic. Stdout only; fixed benchmark stays untouched."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolTransforms
from server import chemistry_server as service

ROOT = Path(__file__).resolve().parents[1]
PATHWAY = "Alkyne partial hydrogenation"


def canonical(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: raise ValueError("Invalid independent diagnostic expectation")
    return Chem.MolToSmiles(mol)


def inspect_option(option, source, conditions):
    row = {"id": option["id"], "product": option["productSmiles"], "diagram": "not-run", "run": "not-run", "failures": []}
    def check(ok, message):
        if not ok: row["failures"].append(message)
    try:
        d = service.reaction_diagram(option["id"], source, "hydrogen", conditions)
        row["diagram"] = "verified"
        check(d["mechanism"] is None, "Unimplemented surface mechanism was fabricated")
        before = [a for a in d["atoms"] if a["side"] == "reactants"]
        after = [a for a in d["atoms"] if a["side"] == "products"]
        identity = lambda rows: {a["mapId"]: (a["element"], a["formalCharge"]) for a in rows}
        check(identity(before) == identity(after) and len(identity(before)) == len(before) == len(after), "Atom/map/charge conservation mismatch")
        check(len(d["changes"]) == 4 and [(c["before"], c["after"]) for c in d["bondOrderChanges"]] == [(3, 2)], "Net edit inventory mismatch")
        hydrogen = set(option["alkynePartialStereo"]["hydrogenAtomMaps"])
        check(hydrogen == set(d["bondsBroken"][0]["atomMaps"]), "Actual H2 provenance mismatch")
        basis = option["stoichiometry"]
        check(basis["balanced"] and [r["coefficient"] for r in basis["reactants"]] == [1, 1], "Partial-reduction coefficients mismatch")
        check(abs(sum(r["molarMass"] for r in basis["reactants"]) - basis["product"]["molarMass"]) < 1e-6, "Molar-mass balance mismatch")
        check(basis["context"]["canGenerate3D"] == option["assessment"]["canRun"], "Calculator condition context mismatch")
    except Exception as exc:
        row["diagram"] = "failed"; row["failures"].append("Diagram: " + str(exc))
        return row
    if not option["assessment"]["canRun"]:
        try:
            service.run_curated_reaction(option["id"], source, "hydrogen", conditions)
            row["run"] = "incorrectly-allowed"; row["failures"].append("Missing/incompatible activation allowed 3D")
        except service.ChemistryError:
            row["run"] = "blocked"
        return row
    try:
        p = service.run_curated_reaction(option["id"], source, "hydrogen", conditions)["product"]
        row["run"] = "verified" if p["representation"] == "3d" else "2d-only"
        row["converged"] = p.get("converged")
        check(p["smiles"] == option["productSmiles"], "Run product identity mismatch")
        check([(a["atomIndex"], a["mapId"], a["element"]) for a in after] ==
              [(a["index"], a["mapId"], a["element"]) for a in p.get("atomLinks", [])], "Exact 2D/3D atom correspondence mismatch")
        if option["alkynePartialStereo"]["assignment"] == "Z":
            shape = Chem.MolFromMolBlock(p["molfile"], removeHs=False)
            ends = set(option["site"]["atomMaps"])
            bond = next(b for b in shape.GetBonds() if {b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()} == ends)
            a, b = bond.GetBeginAtom(), bond.GetEndAtom()
            refs = [next(n.GetIdx() for n in c.GetNeighbors() if n.GetAtomicNum() == 6 and n.GetAtomMapNum() not in ends) for c in (a, b)]
            angle = rdMolTransforms.GetDihedralDeg(shape.GetConformer(), refs[0], a.GetIdx(), b.GetIdx(), refs[1])
            row["cisCarbonDihedralDegrees"] = angle
            check(abs(angle) < 25, "Configured cis graph not represented in 3D")
    except Exception as exc:
        row["run"] = "failed"; row["failures"].append("Run: " + str(exc))
    return row


def run():
    fixture = json.loads((ROOT / "tests/fixtures/alkyne-partial-hydrogenation.json").read_text())
    rows = []
    for case in fixture["positive"] + fixture["negative"]:
        source = {"name": "Independent diagnostic", "smiles": case["substrate"]}
        row = {"label": case["label"], "source": case["substrate"], "failures": [], "options": []}
        expected = {canonical(p) for p in case.get("products", [])}
        try:
            match = service.match_reactions(source, "hydrogen", fixture["conditions"])
            found = [r for r in match["reactionOptions"] if r["mechanism"] == PATHWAY]
            if {r["productSmiles"] for r in found} != expected:
                row["failures"].append("Independent stereochemical/connectivity product set mismatch")
            row["options"] = [inspect_option(r, source, fixture["conditions"]) for r in found]
            row["reasons"] = match["unsupportedReasons"]
        except service.ChemistryError as exc:
            row["reasons"] = [str(exc)]
            if expected: row["failures"].append("Supported diagnostic input rejected")
        rows.append(row)
    for condition in [{}, {"catalyst": "none"}, {"catalyst": "metal"}, {"catalyst": "radical"}, {"catalyst": "acid"},
                      {"catalyst": "osmium"}, {"catalyst": "lindlar", "temperature": "heated"},
                      *[{"catalyst": "lindlar", "solvent": m} for m in ["aqueous-protic", "ethanolic-protic", "polar-aprotic"]]]:
        source = {"smiles": "CC#CC"}
        found = [r for r in service.match_reactions(source, "hydrogen", condition)["reactionOptions"] if r["mechanism"] == PATHWAY]
        rows.append({"label": "conditional-preview", "conditions": condition,
                     "failures": [] if len(found) == 1 and not found[0]["assessment"]["canRun"] else ["Invalid condition gate"],
                     "options": [inspect_option(r, source, condition) for r in found]})
    failures = [{"label": r["label"], "messages": r["failures"] + [m for o in r["options"] for m in o["failures"]]}
                for r in rows if r["failures"] or any(o["failures"] for o in r["options"])]
    return {"phase": "4A", "fixedBenchmarkModified": False,
            "benchmarkSha256": hashlib.sha256((ROOT / "scripts/audit_reaction_lab.py").read_bytes()).hexdigest(),
            "caseCount": len(rows), "optionCount": sum(len(r["options"]) for r in rows), "failures": failures, "results": rows}


if __name__ == "__main__":
    RDLogger.DisableLog("rdApp.*")
    result = run()
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["failures"] else 0)
