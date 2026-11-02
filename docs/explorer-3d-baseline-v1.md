# Explorer 3D baseline v1

Recorded before the provenance-resolver change using `PYTHONPATH=. .venv/bin/python tests/explorer_3d_baseline_v1.py` and the fixed cases in `tests/explorer_3d_benchmark_v1.json`. This is an **offline local-fallback baseline**, not a live PubChem availability survey. PubChem's remote responses, network outages and all alternative records were not measured. The zirconium row counts the existing exact-CID gas reference, conditional on the PubChem endpoint returning 404.

| Category | Cases | Local 3D or existing reference | Other results |
| --- | ---: | ---: | --- |
| Organic | 4 | 4 generated; identity checks pass | 0 |
| Inorganic | 4 | 3 generated; identity checks pass | SF6 2D-only |
| Metal | 3 | 1 idealized gas reference (ZrCl4) | RhCl3 2D-only; iron pentacarbonyl input invalid to this parser |
| Charged | 2 | 0 | 2 2D-only |
| Ionic assembly | 2 | 0 | 2 deliberately information-only |
| Radical | 1 | 0 | 1 2D-only |

Total: 8/16 displayed by the offline calculation/reference paths; seven generated structures passed an isomeric molecular-identity comparison and one is a source-informed idealization. Identity preservation is **not** an independent validation of geometric accuracy. The invalid metal SMILES represents an input/parser limitation, not proof that the chemical species lacks a structure. Ionic exclusions are intentional and should not be treated as regressions.

The benchmark does not claim representative statistical coverage or universal correctness. Future runs must distinguish live PubChem availability, transient failure, model category, geometry/reference validation, stereochemical identity and deliberate ionic exclusion. Freeze this fixture for comparison; any additions should use a new benchmark version.
