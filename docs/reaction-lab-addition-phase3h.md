# Phase 3H — Addition-family consistency fixes

Completed 2026-10-15. Implements the **five priorities from Phase 3G only**. No new reactions, reagents, substrate permissions, mechanism chemistry, curated examples or layout redesign. No commit, push, publication or deployment.

## 1. Condition evidence and rendering permission

The six addition pathways now provide versioned `assessment.evidence`, separating:

- Structural eligibility and validated reagent identity.
- Required model settings and which are missing.
- Unevaluated/incomplete condition factors.
- Conditional net-product assertions versus experimental outcomes, which remain unpredicted.
- 2D preview and 3D rendering permission, explicitly identified as output policies.

The interface uses this evidence for its option badges, explanation headings and condition label. Missing acid activation or diol workup is no longer described as merely an incomplete comparison example. Confirmed diol release is labeled **“Release assumed · solvent not evaluated.”** Its solvent factor is explicitly unknown for every medium; no solvent-specific Os/H₂O₂ compatibility was invented.

**All existing chemistry/3D gates remain unchanged.** Unconfirmed diol release still blocks 3D. Qualified ionic HX can still render a representative conditional structure with unspecified medium, but this is now explicitly distinguished from condition completeness or a predicted outcome. Legacy `status`/`canRun` remain for existing callers; new consumers should use the evidence fields rather than interpreting a rendering flag as chemical confidence. The four earlier substitution/elimination pathways retain their condition behavior.

## 2. Visible and transferable calculation caveats

Addition stoichiometry now carries a versioned `context`: pathway, exact selected conditions, missing requirements, unassessed factors, rendering permission and assumptions. Conditional warnings are visible **inside the existing calculator, above its inputs**, not hidden solely in collapsed method notes. Diol warnings distinguish formal peroxide bookkeeping from an elementary osmium/proton mechanism.

The standalone Calculators catalog preserves and validates this context instead of stripping it. Catalog equations have unspecified conditions explicitly recorded; choosing one does not silently adopt an example's activation or workup. Invalid context fails closed, and defensive copying prevents later mutations from changing a selected basis. Changing/clearing the selected equation clears prior warnings, amounts and results.

The arithmetic, equation coefficients, exact compound identities, full reagent/salt molar masses, limiting-reactant calculation and theoretical/required amounts are unchanged. These remain hypothetical net-equation amounts, not actual yields, summed stereoisomer yields or a lab protocol.

## 3. Explanations and API label types

Hydration/HX diagram notes now correctly state that distant configuration is retained, reacting E/Z is consumed and new centers remain unassigned. They no longer direct users to nonexistent complete mapped mechanisms. The reasoning label type includes the actual server value `Model conditions match`; confidence-aware headings use the more precise evidence text. The existing epoxidation guide's stale “connectivity only” wording was also corrected without changing its layout.

No halonium or complete osmium mechanism was added. Epoxidation retains its previously validated formal concerted step. No new stereochemical assignment is inferred from a conformer.

## 4. Grouped hydration options and precise terminology

The match response now declares **`contractVersion: 2`** and supplies:

| Field | Meaning |
| --- | --- |
| `reactionOptions` | Grouped product choices used by Reaction Lab |
| `reactions` | Existing independently addressable site records, retained for compatibility |
| `optionIdentity.sourceReactionIds` | All retained legacy IDs represented by a grouped option |
| `optionIdentity.siteAliases` | Exact equivalent mapped site/face or capture-atom representations |
| `optionIdentity.aliasKind` | Distinguishes capture-atom maps from face indices |
| `optionCounts` | Separate option, mechanism, product and mapped-site counts |
| `structuralEligibility` | Structural availability, not condition completeness |
| `supportState: Conditional` | Addition-only matches are conditional net models, not guaranteed reactions |

Hydration now presents symmetric 1,11-dodecadiene as **one product choice with two mapped site aliases**, not two duplicate choices. Both original site IDs still work through diagram/run APIs. Full-graph chirality-aware equivalence and identical isomeric products are required before grouping; molecular formula alone is insufficient. Distinct capture orientations, non-equivalent sites and different stereoisomers remain separate.

Keeping the legacy site-addressable view is intentional: an original regression test requires those two IDs, and the fixed benchmark uses that contract. The new grouped API/UI view fixes duplication without deleting provenance, breaking those callers or disguising benchmark changes. A separate diagnostic explicitly verifies the grouped view.

Status and comparison headings now count **net product options**, not stereoisomers as separate mechanisms. The UI explains that alternatives may differ by site, orientation or face and does not predict ratios or a winner.

## 5. Independent diagnostics, separate from the benchmark

New read-only diagnostic: [audit_addition_consistency.py](</Users/rc/Documents/Capstone project/scripts/audit_addition_consistency.py>).

It exercises all six pathways with **48 cases and 66 canonical product options**, including independently specified E/Z-2-butene and cyclic stereochemical expectations, unknown internal geometry, distant physical retention/CIP-priority changes, equivalent distant sites, missing settings and conjugated negative controls.

Diagram and run results are recorded separately: a valid conditional 2D preview remains `verified` even when 3D is correctly `blocked`. Site counts expand mapped aliases and do not count two enantiomers as two C=C sites. Checks include explicit atom/charge conservation, unique complete maps, net bond edits, actual reagent provenance, unselected double bonds, local CIP outcomes, coordinate-to-configured-identity correspondence, distant physical parity, calculation context and honest mechanism availability. Fault-injection tests demonstrate that a genuine diagram failure is still reported independently.

This layer does **not** alter any fixed benchmark input, expectation, fixture or scoring rule. All audit cases remain separate from the visible curated collection.

## 6. Verification and preservation

**1,800 tests pass: 953 Python + 847 JavaScript.** This preserves all **1,704 original tests unchanged** and adds **96 checks**: 69 Python and 27 JavaScript. No original test file was edited, removed or skipped. Coverage includes authenticated public match/diagram/run routes, grouped site identity, context parsing/copying, visible warnings, invalidation and unchanged calculator arithmetic.

| Verification | Result |
| --- | --- |
| Python full regression suite | 953 passed, zero failures/skips |
| JavaScript full regression suite, including calculator fixtures | 847 passed, zero failures/skips |
| New independent addition diagnostic | 48 cases, 66 diagrams; 57 verified runs, 9 correctly blocked; no failures |
| Existing public SN1/SN2/E1/E2 diagnostic | 192 match checks, 48 condition checks, 5 reagent controls, 125 verified options; no failures |
| TypeScript | Pass |
| Production build | Pass; existing third-party/large Builder bundle warnings remain |
| Whitespace | Pass |

The original **347-case benchmark file is byte-identical**, SHA-256 `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. All 347 fixed result rows remain identical to Phase 3G: **179 full, 25 partial, 105 unsupported and 38 correctly rejected**. No incorrect-result rows appeared.

| Addition pathway | Unchanged strict full-workflow score |
| --- | ---: |
| Hydration | 10/14, 71.4% |
| Hydrohalogenation | 12/16, 75.0% |
| Bromination | 9/14, 64.3% |
| Chlorination | 9/14, 64.3% |
| Epoxidation | 9/11, 81.8% |
| Dihydroxylation | **0/11, 0% strict** |

The separately rerun confirmed-workup supplement remains **9/11 full**, one partial cyclic positive, one unsupported NMO positive and one correctly rejected control. It is not substituted for the strict score. There are still 12 total diol rows: 11 positives plus one negative, leaving 335 unrelated rows.

Preservation hashes confirm no changes to existing tests/fixtures, the benchmark, chemistry transformation/compatibility/stereochemistry modules, curated molecule data, CSS or root HTML. Build/container configuration was also left untouched. Changes to existing source are limited to nine files for metadata, labels, explanation text and calculator-context handling; the new contract module does not grant chemistry eligibility.

Browser verification confirmed the explicit solvent-unknown label, missing-release badge, conditional 2D diagram, disabled 3D/Compare and visible calculation warning with method notes still collapsed. The temporary tab was closed. The local preview was refreshed; no hosting or publication was performed.

[Machine-readable benchmark, separate replay, independent diagnostics and preservation evidence](</Users/rc/Documents/Capstone project/docs/reaction-lab-addition-phase3h-results.json>).

## 7. Remaining boundaries and stopping point

These fixes clarify validated net models; they do not establish solvent-specific protocols, reaction completion, selectivity, rates, yields or safety. Existing restrictions on Cl₂ oxygen spectators, competing capture/rearrangement, directed stereo, unsupported rings and missing workup remain. Conditional geometry is not an experimental outcome.

Old callers may continue using legacy site records and legacy condition status fields; the versioned evidence and grouped option view are the authoritative new presentation contract. This compatibility boundary is documented rather than silently changing old IDs or benchmark expectations.

**All five Phase 3G priorities are addressed. This phase stops here; no new reaction-development phase was started.**

![Visible conditional calculator warning and unchanged diol workup gate](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3h-preview.png>)
