# Reaction Lab — Phase 4F consistency fixes and companion framework

Completed 2026-10-16. Phase 4F only. No new chemistry, reaction families, reagents, curated examples, layout changes, publication or Calculator formula changes.

## 1. Confirmed issues reproduced

The Phase 4E review and zero-score addendum were read before editing. The public condition parser validated known selectors but discarded unknown condition fields. Thus explicit `peroxide: true` or `light: UV` could disappear before all four alkyne assessments and leave 3D permitted. Recognized radical activation was already blocked; these were distinct input routes, not evidence for a radical mechanism.

The second issue was the Lindlar multi-site policy: independently selectable, mapped single-site reductions preserved other triple bonds and could generate 3D despite unresolved experimental mono-site selectivity. Complete hydrogenation, X2 and HX already restricted their corresponding multi-alkyne choices to conditional 2D.

## 2. Exact production fixes

- The shared parser retains unsupported **field names**, without interpreting or echoing arbitrary values. Invalid values for existing fields return a field-specific 422 error.
- A guard on the **four alkyne assessments only** records explicit unsupported, conflicting and unvalidated-alternative inputs. Unknown fields and unsupported combinations block 3D while retaining structurally valid conditional 2D options.
- Partial hydrogenation now exposes `singleSiteBookkeepingOnly` from the existing site-compatibility report. The Lindlar assessment uses it to block an unvalidated selective 3D output.
- Existing `assessment`, `evidence`, `canRun`, `canGenerate3D` and calculator context carry consistent permissions and explanations. The frontend consumes those fields; it does not calculate a second chemistry permission.

Production files: [parser/API](</Users/rc/Documents/Capstone project/server/chemistry_server.py>), [conditions](</Users/rc/Documents/Capstone project/server/reaction_conditions.py>), [partial-hydrogenation metadata](</Users/rc/Documents/Capstone project/server/alkyne_partial_hydrogenation_rule.py>), [evidence/calculator context](</Users/rc/Documents/Capstone project/server/addition_contract.py>), [frontend labels](</Users/rc/Documents/Capstone project/src/reaction-conditions.ts>) and [existing Reaction Lab controls](</Users/rc/Documents/Capstone project/src/reaction-lab.ts>).

No transform, stereochemistry-assignment, reagent, molecular-compatibility expansion or stoichiometric formula was introduced.

## 3. Condition validation

| Input category | Current behavior |
| --- | --- |
| Existing supported model settings | Existing bounded net-model 3D permission remains; this is not independent experimental validation. |
| Required setting absent | Specific missing fields remain listed; valid 2D inspection remains; 3D is blocked. |
| Unknown field, e.g. peroxide/light/pressure/solventName | Field named in issues, label and explanation; unsupported input cannot disappear into a positive assessment. |
| Existing selector with invalid value | 422 identifies the field; no unsupported value is converted into a supported alias. |
| Conflicting activation, e.g. ordinary metal for Lindlar, or Lindlar for complete reduction | Conflict identified; no asserted alternate endpoint. |
| Unvalidated alternative, e.g. generic polar-aprotic medium | Explicitly unvalidated, not declared chemically impossible. |
| Recognized radical activation | Unsupported pathway remains blocked; no radical chemistry is inferred. |
| Oxidation-stage or diol-workup setting on an alkyne model | Explicit conflict; clear the unrelated setting. |
| Persistent polymer/irrelevant stage selectors | Acknowledged as `notApplicableSettings`, not treated as activation, reagent supply or chemical evidence. |

Existing active-metal complete reduction in ethanolic medium remains permitted within its prior bounded model. This phase did not admit new named solvents or claim that this broad selector is a reviewed experimental profile. Missing information, unvalidated alternatives and genuine conflicts are not collapsed into “unfavorable.”

## 4. Lindlar multi-site resolution

Theoretical single-site diagrams, site IDs, exact source maps and unchanged triple bonds remain available. Whole-graph equivalent choices still group under one canonical product with all original aliases; distinct products remain separate. Neither deduplication nor a canonical option hides the additional reactive site from the confidence gate.

The separate diagnostic changes four options across three existing fixtures: two non-equivalent sites, equivalent terminal sites and equivalent internal sites. They now return valid mapped 2D and reject selective 3D. All other partial-hydrogenation diagnostic outcomes are unchanged. Its 33 options comprise 19 permitted 3D and 14 policy-blocked options, with zero diagnostic failures.

The checked Lindlar preparation establishes bounded partial reduction and cautions about reaction stopping; it does not independently establish selective mono-reduction for these multiple-alkyne fixtures. No case-specific evidence was manufactured to grant that permission. [Checked Organic Syntheses preparation, procedure and notes](https://www.orgsyn.org/demo.aspx?prep=CV5P0880).

## 5. Confidence status

The existing evidence contract now makes these distinctions without a competing status system:

- **Structure/site:** `structuralEligibility: eligible` means the net site and reagent model matched, not that conditions are complete.
- **Conditions:** `conditionCompleteness` retains incomplete/model-assumptions-only and adds unsupported-input, conflicting-input and not-evaluated. `conditionIssues` names each field and issue kind. Required missing fields remain independently visible.
- **Generation:** `canRun`, evidence `canGenerate3D` and calculator `canGenerate3D` agree. Conditional 2D permission is independent of this 3D gate.
- **Independent correctness:** alkyne evidence explicitly states `not-independently-certified-at-runtime`. Mapped graph checks, a conformer and regression passes cannot certify experimental chemoselectivity or protocol applicability.

The runtime still represents conditional net outcomes, not measured yields, rates, product ratios, laboratory instructions or universally verified chemistry. A blocked generation request is not labeled an incorrect molecular product.

## 6. Frontend explanations

The existing result explanation now identifies missing medium, temperature, activation or equivalents using readable field names and tells users to complete the existing fields and refresh options. The same guidance appears on existing 3D controls. Explicit condition conflicts and competing-site explanations come from the backend. No new page, panel layout or profile selector was added.

Conditional 2D remains visibly labeled. Calculator warnings preserve theoretical complete-conversion assumptions and now explicitly carry the blocked condition/site context; arithmetic does not grant generation permission. Stale result/permission clearing is preserved, including clearing obsolete control hints.

Browser verification used the existing propyne/HBr example: keyboard option selection produced conditional 2D with missing medium/temperature and disabled 3D/Compare. Entering the existing dry/ambient settings enabled the bounded 3D model. Clearing them removed the old product and restored the block. No browser console errors were observed. [Screenshot](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase4f-conditional-preview.png>).

## 7. Versioned companion framework

Implemented [framework](</Users/rc/Documents/Capstone project/scripts/reaction_conditions_companion.py>) and [versioned catalogue/documentation](</Users/rc/Documents/Capstone project/benchmarks/reaction-conditions/README.md>).

Version **1.0.0** is explicitly `draft-evidence-backlog`, content-pinned by SHA-256 in its index. It binds all 347 original IDs to normalized case digests and the exact frozen script hash. Its initial profile-review scope retains 58 original rows: 53 positives and five controls. The other 289 rows remain explicitly outside profile review, not silently certified.

Overlays only add allowed condition fields and cannot replace explicit frozen settings, reagent identities, substrates or expectations. Every executed overlay records field, before/after value, profile and independent-review status. Default mode applies only admitted overlays; `--diagnostic` applies draft overlays with an explicit unvalidated label. Neither mode writes files or overwrites history.

New versions require separate files and digest pins. Comparison reports changed case bindings, profiles and defect annotations; same-version replacement and rewriting historical diagnostic numbers are rejected. Pins support reproducibility, not cryptographic trust or scientific approval.

Results also record the content fingerprint of the chemistry engine (including uncommitted implementation), the profile-manifest version and each oracle's status/version. A reviewed oracle disagreement is explicitly `failed-independent-oracle`, distinct from an unreviewed profile, engine-unsupported case or known frozen-oracle defect, and makes the command fail rather than disappearing into a missing-evidence count.

## 8. Independent evidence gate and backlog

No independently approved condition profile was fabricated. All three initial profiles remain evidence gaps. Among the 53 positive bindings, **52 are evidence gaps and A255 is an unsupported engine reagent model**. A255 remains actual NMO; it is not replaced with H2O2.

Admission requires:

1. A primary source with precise location, applicable reaction system and chemical rationale.
2. Independent reviewer/date/assertion-scope approval, not an engine/test success flag.
3. Explicitly specified or justified-not-applicable reagent identity, formulation, amount basis, medium, catalyst, temperature, initiation, release, competing chemistry and site scope. Unknown is not complete.
4. Separate case-specific applicability approval naming the exact case, profile and version.
5. For independent product correctness, an independently specified, reviewed oracle covering product alternatives, byproducts, connectivity rationale, mapped edit contract and stereochemical uncertainty.

The software checks the completeness and identity of these records; a human scientific review must establish that their content is true and applicable. It cannot establish that simply by checking a citation URL.

Potential named alternative media/formulations remain future review candidates. No generic solvent or ambient token was promoted to an approved protocol. The prior Os/H2O2 versus NMO evidence mismatch is retained as an unresolved gap; dihydroxylation chemistry remains unchanged.

## 9. A304 handling

The original expected products remain unchanged. The companion flags `frozen-oracle-defect`, `appliedToFrozen: false` and a proposed, unapplied connectivity erratum.

A304 is hex-2-yne plus one actual HBr. The two net orientations preserve the original C2–C3 unsaturation position. The frozen second expectation shifts it to C3–C4. The proposed connectivity-only alternatives are `CC(Br)=CCCC` and `CC=C(Br)CCC`; E/Z remains unassigned. No corrected companion oracle is admitted, and no production product was changed to satisfy the bad expectation. A future corrected oracle requires an explicit erratum version and independent approval.

## 10. Frozen strict versus diagnostic results

The frozen script remains byte-identical: SHA-256 `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

| Measurement | Phase 4E | Phase 4F |
| --- | --- | --- |
| All 347 frozen rows | 168 full / 47 partial / 93 unsupported / 38 correctly rejected / 1 incorrect-expectation flag | 167 full / 48 partial / 93 unsupported / 38 correctly rejected / same 1 flag |
| Lindlar positive strict score | 8/10 | 7/10 |
| X2 strict / diagnostic generation / old-scorer diagnostic full | 0/21 / 12/21 / 6/21 | unchanged |
| HX strict / diagnostic generation / old-scorer diagnostic full | 0/21 / 11/21 / 11/21 | unchanged |
| Diol strict / diagnostic generation / old-scorer diagnostic full | 0/11 / 10/11 / 9/11 | unchanged |

**Every changed frozen row: A276 only**, full → partial. Its product graph and structural matches are unchanged; the scientifically unestablished selective Lindlar 3D output is now blocked. The frozen scorer's `preview: failed` reflects its combined 2D/run exception handling, not a failed public 2D diagram. The public diagram remains valid. All other **346 complete row records** compare equal, including A304 and every dihydroxylation row. No baseline input, expected product, partial flag or denominator was edited.

The separate old-scorer replay was rerun, not merely copied from history. Its X2 outcomes remain six full, nine partial, six unsupported and two controls rejected; HX eleven full, three partial, one known oracle defect, six unsupported and two controls rejected; diol nine full, one partial, one unsupported and one control rejected.

## 11. Four companion metrics

All denominators are original positive cases, not options or aliases. These are **new framework measurements**, separate from frozen and diagnostic scores.

| Initial scope | Structural matches | Condition-complete eligibility | Fully supported generation | Independently verified chemistry |
| --- | ---: | ---: | ---: | ---: |
| X2 | 15/21 | 0/21 | 0/21 | 0/21 |
| HX | 15/21 | 0/21 | 0/21 | 0/21 |
| Diol | 10/11 | 0/11 | 0/11 | 0/11 |
| All initial positives | **40/53** | **0/53** | **0/53** | **0/53** |

The zeros in the last three columns are an **unreviewed evidence backlog**, not 53 newly incorrect products. In the explicitly unvalidated diagnostic mode, 33/53 cases permit and pass the current model's generation policy (12 + 11 + 10), but still earn no independently admitted coverage. All 49 returned diagnostic options pass diagram/mapping/balance checks; allowed runs pass and blocked requests reject correctly. All five controls are rejected. Thirteen positive substrate–reagent pairs remain engine-unsupported.

Fully supported generation requires admitted conditions, successful diagrams/mapping/balance/3D for the option set and agreement with an independent reviewed oracle. Independent chemistry correctness is separately evaluated in its stated scope and need not claim an experimentally unique 3D product. Policy blocks, profile gaps, unsupported chemistry, runtime failures and frozen oracle defects stay distinguishable.

## 12. Tests and diagnostics

**2,900 tests pass: 1,473 Python + 1,427 JavaScript.** This retains all 2,829 baseline test cases and adds **71**: 57 Python (42 authenticated public confidence/API checks and 15 framework checks) plus 14 JavaScript guidance/calculator checks.

Existing Lindlar assertions in three test files were deliberately updated where they expected multi-site 3D permission. No test case was removed or skipped. Those cases retain product, site, atom/charge/mapping, stoichiometry and 2D assertions and now require the correct 3D block. Single-site cis/Z and distant-configuration 3D checks remain.

The four pre-existing alkyne diagnostics pass with zero failures: partial 52 cases/33 options; complete 52/32; X2 177/85; HX 291/153. Complete/X2/HX diagnostic result records compare equal to Phase 4E. Partial changes only the four multi-site run permissions described above. Existing authenticated public checks, mechanism/null-capability tests, exact mapping, one/two-equivalent accounting and calculator fixtures are included in the passing suites.

Commands, from the project root:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/audit_reaction_lab.py --json
.venv/bin/python scripts/audit_alkyne_partial_hydrogenation.py
.venv/bin/python scripts/audit_alkyne_complete_hydrogenation.py
.venv/bin/python scripts/audit_alkyne_halogenation.py
.venv/bin/python scripts/audit_alkyne_hydrohalogenation.py
.venv/bin/python scripts/reaction_conditions_companion.py
.venv/bin/python scripts/reaction_conditions_companion.py --diagnostic
.venv/bin/python scripts/reaction_conditions_companion.py --compare 1.0.0 --version 1.0.0
```

The bundled Node runtime was used for `--test tests/*.test.mjs`, `node_modules/typescript/bin/tsc --noEmit` and `node_modules/vite/bin/vite.js build`. Results and preservation details are in the [machine-readable verification summary](</Users/rc/Documents/Capstone project/docs/reaction-lab-alkyne-phase4f-results.json>).

## 13. Unrelated behavior and preservation

No changed unrelated chemistry outcome was found. All 279 non-alkyne frozen rows are identical, and 346/347 total rows are identical. The entire dihydroxylation behavior and its documented replay remain unchanged. All pre-existing reports and historical result artifacts are unchanged. Of 307 inventoried pre-existing source/test/script/docs/history files, nine were intentionally edited and 298 remain byte-identical. No Calculator formula module, HTML layout, stylesheet, curated molecule data or frozen benchmark file was edited.

The shared parser's invalid-value error is more specific; new semantic confidence guards are scoped to the four alkyne pathways. No claim is made that unrelated pathways have now received the same unsupported-input review.

## 14. TypeScript, production build and whitespace

TypeScript passes. The production build passes; only the existing large bundle-size advisory remains. `git diff --check` and changed/new text-file trailing-whitespace checks pass. No deployment was performed.

## 15. Remaining limitations

- No independent condition profiles/oracles are approved in companion v1.0.0. Draft overlays are not a scientifically complete replacement benchmark.
- Exact reagent formulations, catalyst state, pressure, exposure, stopping and experimental site selectivity remain unmodeled; unsupported extra inputs cannot supply those capabilities.
- HCl, two-HI, internal one-HX stereo, Cl2 first-stage geometry, remote oxygen and multiple-site restrictions remain as before.
- The four alkyne pathways still represent net bond changes, not complete catalytic-surface or electrophilic elementary mechanisms.
- The A304 frozen expectation defect remains visible; no erratum was applied.
- Passing finite tests and graph invariants does not establish universal chemistry correctness, experimental conversion, yields or safety.

## 16. Recommended next development phase

Before adding chemistry, independently review a small, clearly bounded set of **existing** reagent/medium/substrate profiles and their product oracles. Admit only supported records in a new companion version, compare it explicitly with v1.0.0, and leave evidence gaps visible. Separately resolve the Os/H2O2 evidence mismatch before claiming a validated diol profile; do not silently substitute NMO. Named alternative conditions should be accepted only after that review, not to make frozen zeros disappear.

**Phase 4F stops here. No further pathway or chemistry expansion was started.**
