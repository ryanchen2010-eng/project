# Phase 5H — Chemistry confidence and usability fixes

Completed 2026-10-18. Scope: corrections to existing confidence contracts and presentation, not additional chemistry.

All **3,754 tests pass**: 1,873 Python and 1,881 JavaScript, including 80 new regression tests. TypeScript and the production build pass. The original 347-case benchmark, existing tests, 24 pathway types, two guided profiles, layout, curated examples and calculator formulas are unchanged.

The important chemistry decision is explicit: the older aldehyde oxidation product remains a **neutral-acid reporting structure**, not a validated isolated acid or a prediction of aqueous acid/carboxylate speciation. Unsupported supplied conditions and unresolved competing sites now block its 3D generation. Existing eligible reporting conformers are retained with explicit limitations; their generation does not establish complete reaction conditions or experimental conversion.

Detailed evidence, all 347 benchmark row comparisons and source-preservation hashes: [machine-readable results](reaction-lab-phase5h-confidence-usability-results.json). The Phase 5G review is [here](reaction-lab-phase5g-consistency-usability-review.md).

## 1. Phase 5G issues reproduced

Before editing, the existing public match, diagram and run APIs reproduced all four confirmed findings:

| Finding | Reproduction | Correction verified |
| --- | --- | --- |
| F1: ignored aldehyde conditions | Pentanal + actual sodium hypochlorite, Water / polar protic and Further oxidation still generated 3D with radical activation, a diol-release workup, an unknown pressure field, added acid, or the secondary-oxidation profile namespace. | Each isolated extra input now produces a specific issue and blocks generation; an eligible conditional 2D reporting diagram remains inspectable. |
| F2: inconsistent confidence | Top-level oxidation match support could say Supported while its option evidence remained conditional. | The top-level state now agrees that these oxidation options are conditional; per-option evidence still distinguishes output permission. |
| F3: conflicting guide summary | The secondary guide's Water replacement row was conflicting while its headline suggested only missing settings. | The headline now reflects conflicting replacement rows and still requires review/consent. |
| F4: unavailable linked view | A blocked 2D preview invited inspection in both views even when no 3D product was available. | Conditional captions accurately describe mapped 2D inspection only. |

Two associated usability problems were also reproduced: editing conditions made the chosen guide difficult to rediscover, and warnings repeated sentences or used internal condition names. These were corrected without changing page structure.

## 2. Root cause of ignored aldehyde conditions

The legacy matcher checked the aqueous medium and Further oxidation setting, and its graph transformation validated the existing product. It did not route the aldehyde pathway through a pathway-specific reviewed condition assessor. Consequently, a valid reporting graph could reach conformer generation despite additional settings that were unsupported, conflicting or unevaluated.

Normalization alone was not a chemistry check: preserved unknown-field metadata needed to be consumed by the assessor. Successful valence, atom mapping and conformer generation were insufficient evidence for the supplied condition combination. The run endpoint needed an independent current-input gate rather than confidence inferred from a previously returned option.

This issue is separate from primary-alcohol-to-aldehyde oxidation, which remains restricted.

## 3. Exact production corrections

A new `server/aldehyde_oxidation_conditions.py` describes the existing reporting model, classifies supplied conditions, records unresolved competing groups and returns existing confidence fields. It introduces no new reagent, reaction transformation or guided profile.

Nine existing production files changed:

- `server/reaction_conditions.py`: dispatch the existing aldehyde pathway to its reviewed assessor.
- `server/reaction_engine.py`: attach reporting/competition metadata and precise missing-setting explanations. Existing matching scope and graph edits remain unchanged.
- `server/chemistry_server.py`: serialize the metadata, reconcile top-level oxidation support, carry assessment into diagrams, and revalidate before product generation.
- `server/addition_contract.py`: explicit reporting-form evidence, 2D/3D permissions and calculator context.
- `server/reaction_information.py`: accurate endpoint, speciation, competition and mechanism limitations.
- `server/reaction_condition_guidance.py`: make the secondary guide summary agree with conflicting requirement rows.
- `src/reaction-conditions.ts`: concise guidance, sentence deduplication and an honest explanation when no selective primary-aldehyde profile exists.
- `src/reaction-lab.ts`: accurate 2D-only captions and fresh rematching of a selected option after condition changes. Old output is immediately cleared; only a newly returned eligible option can be selected. No automatic 3D generation occurs.
- `src/reaction-calculator-panel.ts`: friendly condition labels in displayed warnings, with arithmetic unchanged.

No CSS/layout, reaction edit functions, reagent identity model, stereochemical permission, curated collection, existing test or benchmark input/expectation was changed. Client flags cannot authorize generation.

## 4. Acid/carboxylate and workup findings

The existing balanced reporting equation is:

`R–CHO + M⁺ OCl⁻ → R–COOH + M⁺ Cl⁻`

Here M is the actual supported alkali counterion, not an omitted or substituted mass. This is formal net reporting, not a demonstrated proton-transfer sequence or isotope-provenance mechanism. Tests independently verify product connectivity, represented atom/charge conservation, incoming oxygen maps, the formyl-hydrogen reporting map and chloride-salt identity.

Under applicable basic solution conditions a carboxylate may be relevant, and isolated neutral acid can require a separate workup. This implementation does **not** establish pH, dominant solution speciation or an acid-isolation protocol. It neither silently neutralizes a carboxylate nor invents an acidification transformation. The existing aqueous diol-release selector is not an acid workup, and choosing added acid as activation does not validate isolation.

The evidence therefore explicitly reports `acidEndpointValidated=false`, `conditionCompleteEligibility=false` and `solutionSpeciationEstablished=false`, including when an existing reporting conformer is allowed. `canGenerate3D` is an output policy, not an acid-endpoint certification.

Scientific context: [OpenStax's aldehyde oxidation discussion](https://openstax.org/books/organic-chemistry/pages/19-3-oxidation-of-aldehydes-and-ketones) supports the general transformation, not a universal hypochlorite protocol. The specific formulation and workup in [Organic Syntheses, CV8P0367](https://www.orgsyn.org/demo.aspx?prep=CV8P0367) cannot be silently substituted for this website's legacy model. No such additional protocol was implemented.

## 5. Changes to condition-confidence behavior

| Current input | Interpretation and output |
| --- | --- |
| Existing actual hypochlorite, Water / polar protic, Further oxidation, no new issue/competition | Existing neutral-acid reporting conformer remains available, explicitly conditional and not an experimental endpoint. |
| Missing medium or oxidation stage | Precise missing requirements; the legacy public matcher still withholds this option. No new matching permission. |
| Wrong oxidation stage | Conflicting stage explained; no aldehyde option under the old gate. |
| Alternative medium | Unvalidated by this aqueous reporting model, not declared chemically impossible; no new structural match. |
| Radical activation | Unsupported model; conditional reporting diagram only, generation blocked. |
| Added acid/metal/Lindlar/osmium activation or heating | Unvalidated alternative; conditional diagram only, generation blocked. |
| Diol-release workup | Conflicting workup; not acidification, generation blocked. |
| Unknown fields, explicit pH/pressure, or a secondary-profile namespace | Unsupported input is retained in the explanation, not silently discarded; generation blocked. |
| Several aldehydes or additional oxidizable/unscreened alcohol/ketone chemistry | Selected net connectivity can be inspected, but selective preservation is unresolved and 3D is blocked. |
| Background alkyne-equivalent or finite-chain selectors | Explicitly not applicable to this pathway; they do not change its coefficients. |

Match options, 2D diagrams, calculator context and the run endpoint agree on the current assessment. Direct run requests recompute it before calling conformer generation. Malformed enums retain the existing input-validation rejection.

No new confidence enum was needed. Existing issue kinds distinguish unsupported input, conflicting settings and unvalidated alternatives. Existing state/evidence fields distinguish structural matching, incomplete information, conditional previews and output permission.

## 6. Improved student-facing explanations

Students now see which setting is missing or unvalidated and why it matters, rather than a vague Unfavorable claim. Primary-alcohol first-stage guidance states that no existing setting enables a selective aldehyde 3D product; it does not invite endless dropdown changes. Conditional preview captions no longer promise an unavailable second view. Repeated sentences are consolidated without deleting reporting or experimental-confidence caveats.

Condition editing immediately invalidates old output, then rematches the remembered pathway ID against fresh backend options. If it still exists it is freshly selected so the relevant guide/explanation remains discoverable. An absent option is not restored. Molecule and reagent replacement do not carry this selection preference. Request-revision checks still discard stale responses, and 3D requires a separate action.

Browser verification showed a qualified reporting conformer disappearing immediately when radical activation was selected, while the fresh conditional option and its precise explanation remained available:

![Aldehyde reporting preview with unsupported radical activation, mapped 2D inspection and blocked 3D](reaction-lab-phase5h-aldehyde-blocked.png)

## 7. Guided Conditions regression results

Both existing profiles retain their exact targets, substrate restrictions and explicit review/application workflow. No aldehyde guide was added.

Secondary oxidation browser checks covered the Water replacement conflict, unchecked consent, explicit application, fresh backend match, separate 3D generation and invalidation on subsequent medium changes. The selected option remains discoverable after that fresh rematch.

Lindlar browser checks covered replacement of metal activation, explicit consent/application, unchanged unspecified medium/temperature, separate 3D generation and linked Carbon 2 inspection. Reload restored inputs/settings, not the old result or generation permission. Reverting the catalyst immediately cleared the old result and showed the current conflict. Replacing hydrogen with water cleared the option, guide and output.

Automated regression checks additionally exercise changed sites/inputs, forged flags, direct run requests, primary-aldehyde non-inheritance and unresolved multisite hydrogenation. These automated checks are not presented as extra manual browser scenarios.

Separate existing diagnostic suites passed: primary first-stage restriction, 40 cases with all 21 option runs blocked; secondary profile, 41 cases with 16 qualified net 3D options and 10 blocked option runs; Lindlar, 52 cases/33 options with 19 allowed and 14 blocked. All reported zero diagnostic failures. The distinct case and option denominators are intentional.

![Preserved Lindlar workflow and linked atom inspection](reaction-lab-phase5h-lindlar.png)

## 8. Calculator and mechanism confidence results

Calculator formulas are unchanged. New tests check full sodium/potassium hypochlorite masses, actual chloride counterions, 1:1 net coefficients and independently specified acid molar mass. Conditional arithmetic stays available with explicit complete-conversion assumptions. It does not establish reaction conversion, isolation, selective stopping, an actual yield or a laboratory protocol. Blocked condition/site inputs are identified in calculator warnings too.

For aldehyde oxidation the mapped complete mechanism remains unsupported and the diagram mechanism is null. Formal bond/hydrogen/oxygen bookkeeping is not described as a sequence of experimentally resolved elementary steps. No electron arrows or intermediates were invented. Existing detailed mechanisms and mapping tests pass unchanged.

## 9. Frozen benchmark outcomes and companion checks

The frozen source hash remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. All 347 IDs A001–A347 are present exactly once; no input or expectation changed.

Only **A105 — dialdehyde two sites**, `O=CCCC=O` + sodium hypochlorite, changed status: **Fully supported → Partially supported**. Its existing selected-site product `O=CCCC(=O)O`, maps and 2D diagram remain valid reporting connectivity. Other aldehyde sites also compete; the old model does not validate selective one-site conversion. Generating an asserted selective 3D product is now blocked. Selecting different conditions does not supply a missing independently validated selectivity model.

| Metric | Phase 5G | Phase 5H |
| --- | --- | --- |
| Aldehyde positive structural matches | 7/11 | 7/11 |
| Aldehyde strict fully supported | 7/11 (63.6%) | 6/11 (54.5%) |
| Whole benchmark fully supported | 156 | 155 |
| Whole benchmark partial | 62 | 63 |
| Unsupported / correctly rejected controls / historical incorrect | 90 / 38 / 1 | 90 / 38 / 1 |

The 334 non-aldehyde result rows are identical to the Phase 5G snapshot, including their full recorded row contents. A276 remains restricted; the historical A304 expected-product defect remains annotated and unchanged. The frozen legacy scoring label is **not** a claim that its six remaining reporting-form conformers have validated solution speciation or isolated-acid endpoints.

The versioned companion remains v1.0.0: 58 scope rows = 53 positives + 5 controls, with 289 outside scope. Structural matching stays 40/53. Approved condition-complete eligibility, approved full generation and independent chemistry certification stay zero; no draft case was approved. The separate diagnostic overlay produces 33 model-only cases. Version comparison reports no case, profile or defect changes and an unchanged parent benchmark.

## 10. New tests and total tests passing

Added 48 Python tests in `tests/test_confidence_phase5h.py` and 32 JavaScript tests in `tests/confidence-phase5h.test.mjs`.

Positive structures include independently specified formaldehyde, propanal, 2-methylpropanal, benzaldehyde, a remote ether aldehyde and cyclohexanecarbaldehyde. Both existing sodium/potassium identities and input orders are exercised: 24 positive reporting/mapping combinations. These are test fixtures, not newly curated website examples or expanded matching permissions.

Negatives cover unsupported activation/workup/unknown fields, missing settings, competing aldehyde/alcohol/ketone sites, actual oxidant identity, unchanged scope/stereochemistry restrictions, forged flags, stale reaction IDs and changed request context. JavaScript cases cover theoretical arithmetic, captions, guide summaries, wording, selection rematching and stale-output invalidation.

| Suite | Passing | Failures / skips |
| --- | --- | --- |
| Python unittest discovery | 1,873 | 0 / 0 |
| JavaScript node test suite | 1,881 | 0 / 0 |
| Total | **3,754** | **0 / 0** |
| Increase from 3,674 baseline | **80** | No old test edited or removed |

The existing independent public diagnostic replay also passes: 28 cases, 24 options, seven allowed runs and 17 blocked runs. The five ignored-condition reproductions each changed from HTTP 200 to HTTP 422 at the public run endpoint; eligible diagram requests still return HTTP 200. The original reporting-form control still returns HTTP 200 with explicit limitations.

## 11. TypeScript, production build and integrity

Executed full Python discovery, the complete JavaScript suite, unchanged frozen audit, default/diagnostic companion checks and version comparison, existing primary/secondary/Lindlar diagnostics, independent public probes, TypeScript checking, production build and whitespace checks.

- TypeScript `--noEmit`: pass.
- Vite production build: pass, 13.27 seconds; existing large-chunk warning remains, not a build failure.
- `git diff --check` and touched-text trailing-whitespace checks: pass.
- Before/after hashes of 229 pre-existing source/test/script/config files identify only the nine intended production edits. Three implementation/test files were added. No old test, benchmark, collection, layout or configuration changed.
- Browser tests used a temporary local development server. No deployment, publication, commit, push or new profile approval occurred.

The evidence JSON records exact benchmark rows, conditions, assessments, verification summaries and preservation hashes. Runtime logs were diagnostic artifacts, not new benchmark expectations.

## 12. Remaining known chemistry limitations

The legacy aldehyde pathway is not an independently validated condition-complete oxidation protocol. It does not solve pH/speciation, acid isolation, reaction kinetics or experimental selectivity; ambient/unspecified temperature preserves the prior reporting convention rather than validating a temperature range. Its requirement for medium/stage before public matching remains a legacy workflow limitation.

Primary-alcohol-to-aldehyde qualified generation remains blocked: no selective stopping profile, PCC or Dess–Martin was added. Secondary oxidation still has its screened substrate limits. Both guided profiles and Lindlar multisite restrictions remain bounded. A276 and A304 are not silently repaired by this phase.

Unrecognized alternatives mean unvalidated by this implementation, not chemically impossible. Unknown conditions cannot authorize products. Detailed oxidation mechanisms remain unsupported. No universal chemistry correctness is inferred from these finite tests.

The previously observed Builder Load/Check asynchronous timing issue is outside this corrective scope and remains separately documented in Phase 5G. No unrelated Builder implementation was changed.

## 13. Five recommended next improvements

Ranked by user impact and chemistry-correctness risk; recommendations only, not started:

| Rank | Improvement | Classification / risk |
| --- | --- | --- |
| 1 | Independently validate a bounded aldehyde oxidation condition/speciation/workup contract before claiming an isolated acid endpoint; explicitly decide whether reporting-only output remains sufficient. | Chemistry correctness and confidence; medium/high scientific review risk. Do not manufacture a workup or approve a draft profile. |
| 2 | Run structured student/educator usability sessions on the two current guides, conditional previews and theoretical calculators before adding another guide. | Usability/confidence; low chemistry risk, high immediate user value. |
| 3 | Improve compact disclosure of reporting versus qualified output and human-readable site aliases using observed testing feedback, without hiding limitations. | Explanation/usability; low chemistry risk, moderate asynchronous UI regression risk. |
| 4 | Investigate the documented Builder Load/Check timing race in a separate, narrowly tested increment. | Reliability/usability; moderate state-management risk, no new reaction permission. |
| 5 | Only with independent chemistry evidence, evaluate a future selective primary-aldehyde profile or validated one-site selectivity scope. | Future chemistry development; high correctness risk. Keep existing restrictions until validated. |

## 14. Readiness for structured student usability testing

**Yes, for structured testing of the existing bounded tool**, with an instructor/reviewer aware of conditional reporting, unsupported models and theoretical amount assumptions. The fixes address the confirmed confidence contradictions, keep both explicit guided workflows working and prevent unsupported conditions from silently authorizing aldehyde generation.

This is not readiness for universal prediction, experimental yield forecasts, laboratory procedures or unrestricted chemistry validation. Track whether students can identify missing conditions, distinguish a conditional 2D diagram from an allowed reporting conformer, understand why primary aldehyde generation remains blocked, and use the two guides without believing they certify an experimental result.

Phase 5H ends here. No additional reaction pathway, chemistry expansion or implementation phase was begun.
