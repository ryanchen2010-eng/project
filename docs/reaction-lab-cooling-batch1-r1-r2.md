# Cooling Batch 1 — R1 named profiles + R2 cyclohexene reference

26 October 2026 · Implementation report v1 · Local only

## 1. Outcome

**R1 and R2 are complete in this batch.** R1's contract/compatibility gate passed before R2 began. The three existing cooled profiles keep their prior permissions and chemistry. One additional, explicitly selected reference now permits an eligible theoretical cyclohexane conformer. No other hydrogenation substrate, catalyst or pathway is enabled by this addition.

Positive cooling inventory: **four profiles across three of the existing 24 rule types**, previously three profiles across two types. This is an inventory of bounded models, not a universal chemistry-success score. The other 21 types retain their restrictions.

Final verification: **4,321 tests pass: 2,150 Python + 2,171 JavaScript**, up from a freshly verified 4,281-test baseline. TypeScript, production build, desktop/320px browser checks and the unchanged 347-case audit pass as described below. The known frozen audit defect remains, not a new failure.

Nothing was pushed, merged or deployed. Render, frozen Beta v1, styles, layout, curated examples and frozen benchmark inputs are unchanged. Batch 2 has not started.

**Phase 3 reminder: Milas–Sussman pages 1303 and 1304 are still needed. Page 1302 is already supplied.**

## 2. R1 architecture

### Single backend-owned registry

`server/named_condition_profiles.py` supplies a small provenance/selection contract; it does not generate products. `server/reaction_temperature_profiles.py` remains the single immutable registration and applicability authority. There is no writable registration endpoint, client-authored recipe or parallel frontend chemistry registry.

Each profile has an exact ID and version, pathway, detached descriptor, evidence locators, assumptions and unknowns. Fact records distinguish **source observation**, **model assumption**, **unknown** and **not applicable**. Their seven categories are reagents, catalyst/formulation, medium, thermal history, hydrogen pressure, additives and product release. These can hold structured data without adding global numeric/dropdown controls. Thermal observations are not interpolated operating windows.

Descriptors are stored as immutable JSON on frozen registry records and returned as detached data. Mutating a response cannot change the next assessment. Descriptor schema v1, registry v1, profile version 1 and existing cooling-response v1 are separate, explicitly checked identities. The original three entries retain their IDs, implicit selection and original assessors; their new provenance is additive.

### Explicit selection and fail-closed behavior

Optional flat request fields are `conditionProfileId` and `conditionProfileVersion`. Both must be well-formed strings and supplied together. Arbitrary facts, pressure overrides and numerical temperatures are not accepted as named-profile definitions. Unknown/obsolete references and wrong pathway/temperature selections cannot fall through a legacy rule as ignored metadata.

Match, diagram and run independently resolve the current molecular graph, site and conditions. The new selection contract is checked even on non-cooled legacy routes. Wrong peracid identity, conflicting medium/activation, missing source-model scope, stronger underlying validation failures and unsupported fields remain blockers. A prior option ID or cached positive assessment is not permission for another graph or condition set.

Existing requests without a selection retain their behavior. Existing successful cooled assessments identify their descriptor as `legacy-inferred`; the new pilot requires `explicit`. No implicit `cooled`→`ambient` conversion occurs.

### Downstream consistency

- Assessment provenance reaches matching, 2D diagrams, run responses and calculation context. The frontend checks model/pathway/version consistency before displaying positive cooled-3D wording.
- Calculation context copies validate reference/input agreement and detach provenance. Copying metadata never grants chemistry permission or changes arithmetic.
- Drafts preserve explicit references for backend revalidation. Obsolete references stay explicit and blocked rather than silently becoming generic requests. Malformed restored references fail closed.
- Conditions, reactants, site and profile changes invalidate dependent results. Delayed responses cannot restore an old product or calculator answer.
- The existing Guided Conditions surface provides deliberate review/confirmation for the new pilot, read-only source facts and unknowns. A small **Clear Named Condition Profile** action clears only the reference and rematches; it does not rewrite temperature. There are no new general condition dropdowns or layout/style changes.

### R1 gate completed before R2

Eight new Python contract tests passed, followed by 78 existing cooling Python checks, 66 focused frontend checks including the eight R1 additions, and TypeScript. A before/R1 public snapshot compared **100 contexts**: removing only additive `namedConditionProfile` metadata made the responses deeply identical. R2 was not admitted until those checks passed.

## 3. R2 evidence and scientific decision

Primary source: [JP2004250387A, original PDF](https://patentimages.storage.googleapis.com/27/d6/88/c4e424165867a6/JP2004250387A.pdf) and [translated patent text](https://patents.google.com/patent/JP2004250387A/en). Original printed pp. 14–15 and paragraphs [0082], [0087]–[0092] were rechecked; catalyst preparation is located in [0081]–[0082].

The selected experiment uses cyclohexene, hexane and **5 wt% Pd on dual-pore silica catalyst A**: 1 µm macropores, 6 nm mesopores, 68 µm average particles. Its source-defined preparation uses palladium acetate and post-impregnation calcination at 500°C for two hours. Catalyst pretreatment is room-temperature H₂ reduction for one hour, then drying at 110°C for twelve hours. The substrate reaction is separately **0°C, 1.1 MPa H₂, fifteen minutes**. Filtration/GC identifies cyclohexane, with a reported 9.7% analytical endpoint—not an isolated yield or complete conversion. The pressure's gauge/absolute basis is unstated. Commercial Pd/C in [0090] is a different reference; the table/prose reference-number discrepancy does not justify transferring its performance. Broad patent claim ranges are not experimentally validated windows. [Source: JP2004250387A](https://patents.google.com/patent/JP2004250387A/en).

**Decision:** the identified net product and existing validated graph engine justify a static theoretical conformer for this exact parent/reference. High conversion and a fully resolved catalytic surface mechanism are not prerequisites for depicting that molecule. They would be prerequisites for claims this tool does **not** make. This is a bounded software applicability decision, not independent replication or laboratory guidance.

## 4. Exact implemented scope

Profile: **`cooled-cyclohexene-pd-silica-v1`, version `1`**.

Required current inputs are unsubstituted, neutral, non-isotopic cyclohexene and actual H₂, with the existing selected-site compatibility/validation passing and cyclohexane as the validated net product. Canonically equivalent graph orderings and both input orders are accepted; display names do not establish identity.

The user must deliberately confirm this named reference while retaining **Cooled**, **Dry / no water** and **Metal Catalyst (Pd/Pt)** in the existing controls. Here the explicit profile supplies the exact catalyst-A/hexane/reference-pressure assumptions; those coarse controls alone never select them. The descriptor separates catalyst preparation from substrate reaction temperature and labels unmeasured/reference information honestly.

The pilot:

- Reuses the existing C=C→C–C transformation and one consumed H₂. It introduces no new reaction family or product editor.
- Preserves the skeleton and the complete 18-atom explicit-H ledger; breaks mapped H–H, forms two mapped C–H bonds and reduces only the selected C=C bond order. Charge is conserved and there is no byproduct or consumed catalyst.
- Uses the same mapped graph for 2D and actual theoretical 3D. Cyclohexane has no new R/S or E/Z assignment in this scope. Arbitrary conformers are not used as evidence of stereochemical selectivity.
- Retains `mechanism: null`/net-only support. It does not invent catalyst-surface intermediates, isotope-transfer experiments, syn-face outcomes or energies.
- Keeps calculator quantities theoretical: 1 mmol each substrate/H₂ permits 1 mmol cyclohexane = **0.084162 g**, requiring **0.002016 g H₂**. The reported experimental endpoint is not used as a forecast, multiplier or yield.

Persistent alkyne-equivalent and finite-chain selectors are not applicable to this one-H₂ pathway; they do not create additional H₂ consumption. Explicit work-up/oxidation declarations belonging to another stage, unsupported facts and conflicting activation/media remain blockers rather than being silently cleared.

## 5. Boundaries retained

No cooled approval is transferred to Pd/C, Pt, other pore formulations, substituted cyclohexenes, other rings, terminal/internal acyclic alkenes, multifunctional substrates, multiple C=C sites, carbonyl hydrogenation or either alkyne hydrogenation pathway. Existing competing-group, atom, bond, charge and stereo safeguards remain authoritative.

No arbitrary temperature/pressure range, catalyst activity, conversion, reaction speed, yield, isolated recovery, facial selectivity or experimental site selectivity is predicted. Actual pressure basis, manufacturing behavior, gas transfer and the physical work-up are not simulated. A source-reference selection is not a claim that a user's experiment has those measured conditions.

Generic cooled hydrogenation still returns conditional 2D with an actionable explanation. For exact cyclohexene it also offers review of the named model. Other substrates do not receive that guide. Changing temperature while retaining the reference is a conflict until it is deliberately cleared or compatible settings are restored. Aqueous/ethanolic media, Lindlar/acid/radical activation, unknown versions, extra numerical facts and forged metadata cannot unlock 3D.

## 6. Updated 24-type cooling inventory

This is a carried-forward compatibility inventory checked against registry/public boundary tests, **not a new literature review or chemistry expansion for the remaining families**. S = admitted bounded cooled profile; P = potential but unapproved; I = incompatible with a specific current profile; O = unresolved endpoint/output scope. Categories do not mean a reaction is universally impossible. Conditional 2D is available only where the structural rule itself supports the net transformation. Existing non-cooled permissions are unchanged.

| # | Existing rule type | Cooled state after this batch | Cooled output / remaining gate |
| --- | --- | --- | --- |
| 1 | Hydrogenation | **S, exact cyclohexene named pilot only**; other substrates P | Eligible 2D/3D for the explicit reference; generic Pd/Pt remains 2D-only. |
| 2 | Bromination | S, existing actual-Br₂ profile | Existing bounded 2D/3D; medium, competing chemistry and anti-addition screens retained. |
| 3 | Chlorination | P | Conditional 2D; Cl₂ formulation/capture/radical evidence not resolved by Br₂ approval. |
| 4 | Hydration | P | Conditional 2D; acid/water, rearrangement and capture applicability need independent review. |
| 5 | Hydrohalogenation | P; oxygen/HCl subprofile I | Conditional 2D; no cold ionic/radical or solvent generalization. |
| 6 | Epoxidation | S, existing mCPBA and bounded perbenzoic profiles | Existing eligible 2D/3D; exact peracid, medium, substrate and stereo scope unchanged. |
| 7 | SN2 | P | Conditional 2D/mechanism; aqueous formulation/product and competition evidence remain. |
| 8 | SN1 | P | Conditional 2D/mechanism; independent water-solvolysis cold review outstanding. |
| 9 | E2 | P | Conditional 2D/mechanism; no new cold base/geometry/product permission. |
| 10 | E1 | P | Conditional 2D/mechanism; no new carbocation/elimination/competition profile. |
| 11 | Alcohol oxidation | Primary O; secondary I | Conditional 2D; primary stopping and secondary cold-formulation gates remain distinct. |
| 12 | Aldehyde oxidation | I | Conditional 2D; current neutral-acid reporting profile is not cooled qualification. |
| 13 | Carbonyl hydrogenation | P | Conditional 2D; no transfer of the cyclohexene catalyst reference. |
| 14 | Esterification | P | Conditional 2D; cold endpoint/equilibrium applicability not reviewed. |
| 15 | Ester hydrolysis | P | Conditional 2D; acid/water, lactone/aryl/site and stereo safeguards retained. |
| 16 | Alcohol dehydration | I | Conditional 2D; existing heated sulfuric-acid profile not broadened. |
| 17 | Alcohol substitution | I | Conditional 2D; existing HX activation/substrate boundaries retained. |
| 18 | Ester saponification | P; ionic 3D O | Conditional carboxylate 2D; no neutral-acid substitution or ionic-geometry workaround. |
| 19 | Alkyne hydrogenation | P | Conditional 2D; two-H₂/catalyst/competition scope remains separate. |
| 20 | Alkyne partial hydrogenation | P | Conditional 2D; no cold Lindlar stopping/selectivity inference. |
| 21 | Alkyne halogenation | P, each halogen/stage separate | Conditional 2D; one/two-equivalent and medium/stereo gates unchanged. |
| 22 | Alkyne hydrohalogenation | I under current ambient model | Conditional 2D; HX identity, stage and regio/E/Z limits unchanged. |
| 23 | Alkene dihydroxylation | P, paused source/release gate | Conditional 2D; pages 1303–1304 and free-diol/formulation decision still required. |
| 24 | Polymerization model | O for cooled initiation/outcome | Finite conditional 2D graph only; no bulk-polymer or cooled initiation prediction. |

## 7. Tests and integration results

Fresh pre-change baseline: **2,128 Python + 2,153 JavaScript = 4,281**, all passing. Final full run: **2,150 Python + 2,171 JavaScript = 4,321**, with no failures, cancellations or skips.

Forty new v1 checks are separated from curated examples and the frozen benchmark:

| Suite | New tests | Main purpose |
| --- | --- | --- |
| `tests/test_named_condition_profiles_batch1.py` | 8 | R1 backend ownership, immutable/detached facts, API selection, legacy preservation and fail-closed conflicts. |
| `tests/named-condition-profiles-batch1.test.mjs` | 8 | R1 descriptor/context parity, copying, drafts and contradictory metadata. |
| `tests/test_cooled_cyclohexene_batch1.py` | 14 | R2 exact graph/reference, both orders, mapping, actual 3D, stereo absence, negative scopes, authenticated APIs and calculator/mechanism boundaries. |
| `tests/cooled-cyclohexene-batch1.test.mjs` | 10 | R2 confirmed transport, exact-version agreement, safe fact rendering, reference clearing, stale suggestions and theoretical arithmetic. |

All pre-existing test cases remain in the runs. Existing tests that asserted the old registry count/pathway set or old condition-field set were updated for the approved fourth entry and two optional fields. Isolated frontend harnesses now supply the additional closure state. Their chemistry, inversion, mapping and negative-case assertions were not removed. An initial new 3D test compared mapped and unmapped SMILES; its oracle now clears map labels **after independently checking atom correspondence**, rather than altering production mapping.

Additional verification:

- **TypeScript and production build pass** (`tsc && vite build`). Existing third-party `use client` and large-bundle warnings remain; no new build error.
- The **347 frozen rows are exactly identical before/after**: 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported, one pre-existing incorrect-result classification. Only recorded production-source fingerprints differ. No input, expectation, case ID or classification rule changed; the benchmark has no cooled inputs and does not measure this new profile.
- The **100-context public match/diagram comparison** is exact after excluding additive named descriptors and normalizing only the documented Hydrogenation explanation that points to the new reference. Products, diagrams/maps, old permissions, mechanisms and other contexts do not differ.
- The separate pinned condition companion remains separate: 40/53 structural matches, zero evidence-qualified condition-complete generations; its unvalidated diagnostic replay remains 33. Neither replay has failures. Those fixtures were not rewritten to select this new reference, and their zeros are not a failure of the new pilot.
- **Desktop 1440px and mobile 320px**: deliberate keyboard confirmation, source/unknown disclosure, conditional→qualified preview, actual cyclohexane 3D, calculator mass, reference clearing, temperature conflicts, aqueous blocking and draft restoration pass without horizontal document overflow or page errors. A delayed valid 3D response after a condition change is discarded.
- Existing browser checks for cooled Br₂, mCPBA, perbenzoic, deferred Cl₂/SN2 and generic hydrogenation all pass. Mechanism availability remains honest. Readable diagram/viewer captures and full-page screenshots were inspected; long pre-existing confidence prose remains in its existing disclosure rather than being redesigned.
- Tracked diff and changed/new-file whitespace checks pass. Of 495 captured pre-existing files, 468 are byte-identical and 27 have intended implementation/test changes; six new files are the helper, four suites and this report. All benchmark scripts/data, layouts/styles, curated data and earlier reports are unchanged. Nothing was deleted or discarded.

Commands used include `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`, `node --test tests/*.test.mjs`, `pnpm run build`, `.venv/bin/python scripts/audit_reaction_lab.py --json` and both normal/diagnostic `scripts/reaction_conditions_companion.py --version 1.0.0` replays. Local logs, public/audit JSON, browser scripts and screenshots are under `/private/tmp/molecule-cooling-batch1.HM8sTo/`. They are QA artifacts, not application examples or benchmark replacements. The isolated localhost QA server was stopped after verification; no pre-existing development server was stopped.

The finite tests do not establish universal scientific correctness. No unexpected chemistry regression was found within the checked scope.

## 8. Recommended Batch 2 and stop point

Recommend a **single evidence/endpoint-led R3 increment** once Milas–Sussman **pages 1303 and 1304** arrive: review the complete formulation, thermal history and free-diol recovery, then decide whether the smallest non-stereogenic Os/H₂O₂ reference and product-release contract is justified. The shared profile metadata is now available, but it cannot repair missing endpoint evidence or silently substitute an aqueous work-up.

If those pages remain unavailable, the alternative proposal is a separately approved **R4 alkene-Cl₂ evidence/formulation review**, not automatic Cl₂/alkyne/SN approval. Do not bundle unresolved halogens, equivalence stages or substitutions merely because their facts can now be stored.

**Stop here: Batch 1 only. No Batch 2 implementation, push, merge or Render deployment.**
