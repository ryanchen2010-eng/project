# Reaction engine audit — before refactoring (2026-10-07)

Eligibility was implemented in `chemistry_server.py`; mapping repeated detection in `reaction_diagrams.py`.

| Reaction | Before | Dependencies / restrictions |
| --- | --- | --- |
| SN2 | B — partially generalized | C/H/Cl/Br only, acyclic, one halide, ≤5 heavy atoms, methyl/primary only; hydroxide |
| SN1 | B — partially generalized | Same artificial size/element restrictions, tertiary only; water |
| E2 | B — partially generalized | Same restrictions; rejects multiple distinct beta-elimination products |
| E1 | B — partially generalized | Same restrictions; tertiary only, rejects multiple distinct products |
| Alkene hydrogenation | B — partially generalized | One C=C, C/H only, acyclic, 2–6 heavy atoms; no specified stereo |
| Alkene halogenation | B — partially generalized | Same scope; bromine only |
| Alkene hydration | C — example-specific | Ethene + water only |
| Hydrohalogenation | Not implemented | No existing rule or example |
| Alcohol oxidation | C — example-specific | 2-propanol + sodium hypochlorite only |
| Aldehyde oxidation | Not implemented | No existing rule or example |
| Carbonyl reduction | C — example-specific | Acetone + hydrogen only |
| Esterification | C — example-specific | Ethanoic acid + ethanol only |
| Ester hydrolysis | C — example-specific | Ethyl ethanoate + water only |
| Acid–amine condensation | Not implemented | No amidation rule; not a supported family to claim |

The 17 previously working pathways, including their complete products, are captured in `tests/fixtures/reaction-baseline.json` before edits. Names/formulas/SMILES may remain as examples and identity/display data; they must no longer decide eligibility. PubChem CID does not currently decide reaction eligibility.

Implementation target: reusable graph detection, explicit site selection, one shared mapped transformation, validated product fragments, and existing net-equation/3D/stoichiometry integration. Preserve ordinary examples; expand bounded structural families, not unrestricted chemistry.
