"""Evidence-gated companion, NOT a replacement for the frozen 347-case audit.

Default: draft profile backlog and runtime observations. --diagnostic applies
explicit UNVALIDATED overlays, never promotes them. Stdout only. Versions are
content-pinned in benchmarks/reaction-conditions/index.json; publish a new file
and pin rather than overwriting an old version. No production imports this file.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import audit_reaction_lab as frozen
from server import chemistry_server as service
from rdkit import Chem, RDLogger

PARENT_SHA = "1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55"
DIRECTORY = ROOT / "benchmarks/reaction-conditions"
DIMENSIONS = frozenset({"reagentIdentity", "formulation", "amountBasis", "medium", "catalyst", "temperature", "initiation", "release", "competingChemistry", "siteScope"})
SCOPE = frozenset([*(f"A{i:03}" for i in range(278, 324)), *(f"A{i:03}" for i in range(242, 253)), "A255"])
HISTORICAL = {path: {"positiveDenominator": denominator, "frozenStrictFull": 0, "diagnosticGeneration": generated, "oldScorerDiagnosticFull": scored}
              for path, denominator, generated, scored in (("Alkyne halogenation", 21, 12, 6), ("Alkyne hydrohalogenation", 21, 11, 11), ("Alkene dihydroxylation", 11, 10, 9))}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def engine_fingerprint():
    """Content identity includes uncommitted/untracked chemistry implementation."""
    return digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "server").glob("*.py"))})


def parents():
    if hashlib.sha256((ROOT / "scripts/audit_reaction_lab.py").read_bytes()).hexdigest() != PARENT_SHA:
        raise ValueError("Frozen parent changed; do not silently adopt a new benchmark.")
    frozen.CASES.clear()
    frozen.build_matrix()
    result = {f"A{i:03}": deepcopy(c) for i, c in enumerate(frozen.CASES, 1)}
    if len(result) != 347:
        raise ValueError("Parent must retain all 347 cases.")
    return result


def reviewed(record, *, oracle=False):
    """Explicit evidence admission, independent of runtime pass/fail.

    This validates recorded review requirements, not the truth of a URL. Human
    scientific source/scope review remains necessary; engine tests never sign it.
    """
    if record.get("status") != "reviewed-applicable":
        return False
    approval = record.get("approval") or {}
    sources = record.get("evidence", [])
    if (not all(isinstance(approval.get(k), str) and approval[k].strip() for k in ("reviewer", "reviewedAt", "scope"))
            or approval.get("independentOfEngine") is not True
            or not sources or any(s.get("kind") != "primary" or not str(s.get("url", "")).startswith("https://")
                                  or not s.get("location") or not s.get("rationale") for s in sources)):
        return False
    if oracle:
        return (bool(record.get("products")) and isinstance(record.get("byproducts"), list)
                and all(record.get(k) for k in ("connectivityRationale", "stereochemistryScope", "mappingContract"))
                and record.get("origin") == "independent-specification")
    fields = record.get("dimensions", {})
    return (set(fields) == DIMENSIONS and all(v.get("state") in {"specified", "not-applicable"}
            and v.get("rationale") and (v.get("value") or v["state"] == "not-applicable") for v in fields.values()))


def load(version="1.0.0"):
    index = json.loads((DIRECTORY / "index.json").read_text())
    pinned = index["versions"][version]
    path = DIRECTORY / pinned["file"]
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pinned["sha256"]:
        raise ValueError("Immutable companion version digest mismatch; publish a new version.")
    manifest = json.loads(raw)
    validate(manifest)
    if manifest["version"] != version:
        raise ValueError("Version identity mismatch.")
    return manifest


def validate(manifest):
    original = parents()
    if manifest.get("schemaVersion") != 1 or manifest.get("parentSha256") != PARENT_SHA:
        raise ValueError("Unknown companion schema or parent.")
    if manifest.get("parentCaseDigests") != {k: digest(v) for k, v in original.items()}:
        raise ValueError("Parent identities, reagents, conditions or expectations changed.")
    if manifest.get("historicalDiagnostics") != HISTORICAL:
        raise ValueError("Historical diagnostics must be preserved; record new measurements separately.")
    bindings = manifest.get("cases", [])
    if len(bindings) != len(SCOPE) or {b["id"] for b in bindings} != SCOPE:
        raise ValueError("Companion must retain all 58 scope rows exactly once.")
    for binding in bindings:
        profile = manifest["profiles"][binding["profile"]]
        changes = profile["conditions"]
        if any(k not in service.CONDITION_VALUES or not isinstance(v, str) or v not in service.CONDITION_VALUES[k] for k, v in changes.items()):
            raise ValueError("Unsupported condition overlay; no reagent substitution permitted.")
        before = original[binding["id"]]["conditions"]
        if any(before.get(k) and before[k] != v for k, v in changes.items()):
            raise ValueError("Overlay must not replace an explicit frozen condition.")
        if binding.get("status") == "reviewed-applicable" and not reviewed(profile):
            raise ValueError("Case cannot be admitted without an independently reviewed profile.")
        if binding.get("status") == "reviewed-applicable" and not reviewed(binding.get("applicability", {})):
            raise ValueError("Profile needs independent case-specific applicability, not just family evidence.")
        if binding.get("status") == "reviewed-applicable" and any(binding["applicability"].get(k) != v for k, v in
                (("caseId", binding["id"]), ("profileId", binding["profile"]), ("profileVersion", manifest["version"]))):
            raise ValueError("Applicability approval must name this exact case, profile and version.")
        oracle = binding.get("oracle", {})
        if oracle.get("status") == "reviewed-applicable" and not reviewed(oracle, oracle=True):
            raise ValueError("Incomplete independent oracle review.")
        if oracle.get("products") is not None and binding["id"] == "A304" and not oracle.get("erratumVersion"):
            raise ValueError("A304 corrected oracle requires an explicit erratum version.")
    defect = manifest.get("defects", {}).get("A304", {})
    if defect.get("status") != "frozen-oracle-defect" or defect.get("appliedToFrozen") is not False:
        raise ValueError("A304 defect must remain visible and unapplied to frozen results.")
    if defect.get("originalExpected") != original["A304"]["expected"]:
        raise ValueError("A304 annotation must preserve its exact frozen expectation.")
    return original


def canonical(value):
    molecule = Chem.MolFromSmiles(value)
    if molecule is None:
        raise ValueError("Invalid independent oracle structure.")
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(molecule, isomericSmiles=True)


def observe(case, conditions):
    a, b = frozen.reference(case["substrate"]), frozen.reference(case["reagent"])
    result = {"matched": False, "options": [], "errors": []}
    try:
        found = [o for o in service.match_reactions(a, b, conditions)["reactionOptions"] if o["mechanism"] == case["path"]]
        result["matched"] = bool(found)
        for option in found:
            row = {"id": option["id"], "product": option["productSmiles"], "byproducts": [p["smiles"] for p in option["byproducts"]],
                   "evidence": option["assessment"].get("evidence"), "permission": option["assessment"].get("canRun", True),
                   "diagram": False, "mapping": False, "run": "not-run"}
            try:
                diagram = service.reaction_diagram(option["id"], a, b, conditions)
                row["diagram"] = bool(diagram["svg"])
                identity = lambda side: {x["mapId"]: (x["element"], x["formalCharge"]) for x in diagram["atoms"] if x["side"] == side}
                row["mapping"] = identity("reactants") == identity("products") and len(diagram["atoms"]) == 2 * len(identity("products"))
                row["mechanism"] = "net-only" if diagram["mechanism"] is None else "mapped-mechanism"
                row["balanced"] = option["stoichiometry"]["balanced"]
                if row["permission"]:
                    product = service.run_curated_reaction(option["id"], a, b, conditions)["product"]
                    links = [(x["atomIndex"], x["mapId"]) for x in diagram["atoms"] if x["side"] == "products"]
                    row["run"] = "3d-passed" if product["representation"] == "3d" and product["smiles"] == row["product"] and links == [(x["index"], x["mapId"]) for x in product["atomLinks"]] else "failed"
                else:
                    try:
                        service.run_curated_reaction(option["id"], a, b, conditions)
                        row["run"] = "incorrectly-allowed"
                    except service.ChemistryError:
                        row["run"] = "policy-blocked"
            except Exception as exc:
                row["error"] = str(exc)
            result["options"].append(row)
    except service.ChemistryError as exc:
        result["errors"].append(str(exc))
    return result


def run(manifest, diagnostic=False):
    original = validate(manifest)
    rows = []
    for binding in manifest["cases"]:
        case = original[binding["id"]]
        profile = manifest["profiles"][binding["profile"]]
        ready = binding["status"] == "reviewed-applicable" and reviewed(profile) and reviewed(binding.get("applicability", {}))
        settings = deepcopy(case["conditions"])
        changes = profile["conditions"] if ready or diagnostic else {}
        transformations = [{"field": k, "before": settings.get(k, ""), "after": v, "profile": binding["profile"], "independentlyReviewed": ready} for k, v in changes.items() if settings.get(k, "") != v]
        settings.update(changes)
        observation = observe(case, settings)
        opts = observation["options"]
        generation = bool(opts) and all(o["diagram"] and o["mapping"] and o.get("balanced") and o["run"] == "3d-passed" for o in opts)
        oracle = binding.get("oracle", {})
        independent = False
        oracle_ready = ready and reviewed(oracle, oracle=True)
        if oracle_ready and opts:
            independent = ({canonical(o["product"]) for o in opts} == {canonical(p) for p in oracle["products"]}
                           and all({canonical(p) for p in o["byproducts"]} == {canonical(p) for p in oracle["byproducts"]} for o in opts)
                           and all(o["mapping"] and o.get("balanced") for o in opts))
        chemistry_state = ("unsupported-engine-model" if not opts else "passed-independent-oracle" if independent else
                           "failed-independent-oracle" if oracle_ready else "frozen-oracle-defect" if binding["id"] in manifest["defects"] else "unreviewed")
        rows.append({"id": binding["id"], "path": case["path"], "positive": case["expected"] is not None,
                     "oracleStatus": oracle.get("status", "unreviewed"), "oracleVersion": oracle.get("erratumVersion", "frozen-parent-unmodified"),
                     "profile": binding["profile"], "profileStatus": binding["status"], "conditionComplete": ready,
                     "transformations": transformations, "inputConditions": settings, "observation": observation,
                     "generationPassedUnderModel": generation, "fullySupportedGeneration": ready and generation and independent,
                     "independentChemistryPassed": independent, "chemistryState": chemistry_state,
                     "oracleDefect": binding["id"] in manifest["defects"]})
    positive = [r for r in rows if r["positive"]]
    def metrics(items):
        return {"denominator": len(items), "structuralMatching": sum(r["observation"]["matched"] for r in items),
                "conditionCompleteEligibility": sum(r["conditionComplete"] and r["observation"]["matched"] for r in items),
                "fullySupportedProductGeneration": sum(r["fullySupportedGeneration"] for r in items),
                "independentlyVerifiedChemistry": sum(r["independentChemistryPassed"] for r in items),
                "diagnosticModelGenerationOnly": sum(r["generationPassedUnderModel"] for r in items)}
    failures = [{"id": r["id"], "reason": "Unexpected control match"} for r in rows if not r["positive"] and r["observation"]["matched"]]
    failures += [{"id": r["id"], "option": o["id"], "reason": "Diagram/mapping/generation contract failure"}
                 for r in rows for o in r["observation"]["options"]
                 if not o["diagram"] or not o["mapping"] or not o.get("balanced") or o["run"] not in {"3d-passed", "policy-blocked"}]
    failures += [{"id": r["id"], "reason": "Independent product oracle mismatch"} for r in rows if r["chemistryState"] == "failed-independent-oracle"]
    return {"schemaVersion": 1, "version": manifest["version"], "engineSha256": engine_fingerprint(), "parentSha256": PARENT_SHA, "failures": failures,
            "mode": "unvalidated-diagnostic-overlay" if diagnostic else "evidence-gated-companion",
            "scope": {"parentRows": 347, "reviewedScopeRows": len(rows), "positiveDenominator": len(positive), "controls": len(rows)-len(positive), "outOfReviewScope": 347-len(rows)},
            "metrics": metrics(positive), "byPathway": {path: metrics([r for r in positive if r["path"] == path]) for path in sorted({r["path"] for r in positive})},
            "controlsCorrectlyRejected": sum(not r["observation"]["matched"] for r in rows if not r["positive"]),
            "profileBacklog": dict(Counter(r["profileStatus"] for r in positive)),
            "historicalDiagnostics": manifest["historicalDiagnostics"], "defects": manifest["defects"], "results": rows}


def compare(before, after):
    validate(before); validate(after)
    if before["version"] == after["version"] and digest(before) != digest(after):
        raise ValueError("An existing version must not be overwritten.")
    if before["historicalDiagnostics"] != after["historicalDiagnostics"]:
        raise ValueError("Historical diagnostics must be preserved; record new measurements separately.")
    old = {r["id"]: r for r in before["cases"]}
    return {"before": before["version"], "after": after["version"], "parentUnchanged": True,
            "changedCases": [r["id"] for r in after["cases"] if r != old[r["id"]]],
            "changedProfiles": [k for k, v in after["profiles"].items() if before["profiles"].get(k) != v],
            "defectChanges": before["defects"] != after["defects"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--compare", help="Compare pinned version with --version; no engine run")
    parser.add_argument("--diagnostic", action="store_true", help="Unvalidated model-setting replay, never validated coverage")
    args = parser.parse_args()
    RDLogger.DisableLog("rdApp.*")
    manifest = load(args.version)
    output = compare(load(args.compare), manifest) if args.compare else run(manifest, args.diagnostic)
    print(json.dumps(output, indent=2))
    raise SystemExit(1 if output.get("failures") else 0)
