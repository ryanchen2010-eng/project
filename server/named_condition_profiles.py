"""Small provenance contract; no molecular rules or executable client facts.

Descriptors are stored as immutable JSON in the reviewed cooling registry and
returned as detached data. A reference selects a model, not experimental truth.
"""
import json

SELECTION_FIELDS = frozenset({"conditionProfileId", "conditionProfileVersion"})


def descriptor(facts, evidence, assumptions, unknowns):
    return json.dumps({"version": 1, "facts": facts, "evidence": evidence,
                       "assumptions": assumptions, "unknowns": unknowns}, sort_keys=True)


def fact(field, value, provenance, relevance, source=None):
    if provenance not in {"source-observation", "model-assumption", "unknown", "not-applicable"}:
        raise ValueError("Unknown provenance category")
    return {"field": field, "value": value, "provenance": provenance,
            "relevance": relevance, **({"source": source} if source else {})}


def describe(profile):
    data = json.loads(profile.descriptor_json)
    return {**data, "id": profile.model_id, "profileVersion": profile.version,
            "pathway": profile.pathway, "title": profile.ui_name}


def reference(conditions):
    if not any(k in conditions for k in SELECTION_FIELDS):
        return None
    return {"id": conditions.get("conditionProfileId"), "version": conditions.get("conditionProfileVersion")}


def selection_issue(profile, reaction, conditions):
    selected = reference(conditions)
    if selected is None:
        return None
    if (profile is None or selected != {"id": profile.model_id, "version": str(profile.version)}
            or profile.pathway != reaction.get("mechanism")):
        return "The named condition profile ID, version or pathway does not match a reviewed model. No facts or 3D permission were inferred."
    if conditions.get("temperature") != "cooled":
        return "This named condition profile covers cooled conditions only. The selected temperature conflicts; it was not changed automatically."
    return None


def reject_selection(assessment, conditions, note):
    # Detached, explicit permission even for legacy pathways. Preserve their
    # ordinary behavior when no new selection is present.
    from copy import deepcopy
    result = deepcopy(assessment)
    result.update(canRun=False, state="incomplete", status="unsupported-pathway",
                  label="Named condition profile unresolved", confidenceLabel="Named profile unresolved · conditional 2D only",
                  note=note + " " + result.get("note", ""))
    issue = {"field": "conditionProfileId", "kind": "unsupported", "explanation": note}
    result.setdefault("conditionIssues", []).append(issue)
    result.setdefault("factors", {})["temperature"] = {"status": "unevaluated", "effect": "unknown", "explanation": note}
    result["namedConditionProfile"] = {"version": 1, "selection": "explicit", "status": "rejected",
                                       "reference": reference(conditions), "descriptor": None}
    result["evidence"] = {"version": 1, "structuralEligibility": "eligible", "reagentIdentity": "validated",
        "assertionLevel": "conditional-net", "experimentalOutcome": "not-predicted", "label": result["confidenceLabel"],
        "requiredSettings": [], "missingRequiredSettings": [], "requirementsState": "not-evaluated",
        "conditionCompleteness": "unsupported-input", "unknownConditions": ["conditionProfileId"],
        "conditionIssues": [issue], "canPreview2D": True, "canGenerate3D": False,
        "renderingPolicy": "named-profile-conflict", "renderingNote": note}
    return result
