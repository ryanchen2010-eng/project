# Phase 4E addendum — What the zero scores mean

2026-10-16. Investigation and design only. No implementation, condition-rule changes, test changes, benchmark edits, layout changes or new reactions. This supplements the [completed alkyne consistency review](reaction-lab-alkyne-phase4e-consistency-review.md) without rewriting its historical evidence.

## 1. Main conclusion

The three zeros do **not** mean every predicted product is wrong or every reaction is unsupported. They mix missing reporting assumptions, conservative output gates, genuine engine coverage gaps and limitations of the frozen scorer.

| Pathway | Frozen strict result | Positive pairs with net options | Missing information causing the common gate | After supplying current model settings: cases permitted to generate | Same frozen scoring logic on that separate replay |
| --- | ---: | ---: | --- | ---: | ---: |
| Alkyne X2 addition | **0/21** | 15/21 | Compatible-medium assumption | **12/21** | **6/21 full** |
| Alkyne HX addition | **0/21** | 15/21 | Compatible-medium and ambient-temperature assumptions | **11/21** | **11/21 full**; A304 still carries the known expectation-error flag |
| Alkene dihydroxylation | **0/11** | 10/11 | Confirmation that the represented endpoint is the released diol | **10/11** | **9/11 full** |

The replays retain the original substrate, reagent, equivalents and expected products. X2/HX add `solvent: dry` and `temperature: ambient`; dihydroxylation adds only `workup: aqueous-release`, retaining its original osmium setting. Public match, diagram and generation calls were exercised. These are **model-setting diagnostics**, not a newly implemented benchmark and not proof of scientifically complete experimental conditions. The original 347-case result is unchanged.

“Net options” counts supported substrate–reagent pairs, not substrate scope alone. In particular, dihydroxylation A255 has an ordinary alkene but an unsupported NMO reagent system; its failure is not evidence that the carbon skeleton is unsupported.

## 2. Classification of the causes

The four requested categories are not mutually exclusive. A matched case can lack a setting and also have unresolved stereo or competing chemistry.

### X2 addition: 0/21

1. **Missing information:** every frozen positive already selects one/two equivalents but omits solvent. All 15 matched positives therefore fail the selected 3D output gate. Temperature is also omitted, but it is **not required** by the X2 gate. A separate acid/metal catalyst or workup is not the missing requirement.
2. **Potentially excessive matching policy:** a compatible reaction medium matters, particularly for capture and stereochemistry. However, accepting only the generic `dry` category is a software boundary, not an independently validated list of all suitable solvents. Dryness alone does not establish non-nucleophilicity. The distinction between a hypothetical 3D graph and an asserted experimental product also needs the policy review identified in Phase 4E.
3. **Unsupported model scope:** six positives remain unmatched after settings are supplied: **A283–A285 and A294–A296** (cyclic alkyne, nearby OH/capture environment, phenylacetylene, in both stages). Three matched cases remain 2D-only: **A287, A298** (additional alkyne/selectivity) and **A322** (first-stage Cl2 stereo). These are limitations of the current model, not claims that the substances cannot react.
4. **Incorrect chemistry:** no new wrong returned product was established. The first-stage scorer deliberately retains its old partial-stereo flag even for a qualified, assigned Br2 graph. Consequently the **12 generation-qualified cases are not 12 full passes** under that scorer: six qualify as full, nine remain partial overall, six are unsupported. The original two controls remain correctly rejected.

Generation-qualified IDs in the replay: **A278–A282, A286, A289–A293, A297**. Six full replay scores: **A289–A293, A297**. No frozen row was rescored or replaced.

### HX addition: 0/21

1. **Missing information:** every frozen positive already selects the equivalent stage but omits **solvent and temperature**. These are the HX gate's missing settings; an extra acid catalyst is not required by this consumed-HX net model.
2. **Potentially excessive matching policy:** suitable reagent formulation and medium are relevant, but requiring the exact `ambient` category to display any qualified HX conformer is a bounded software policy, not a universal temperature law. The existing selectors cannot describe an independently verified formulation, temperature range, capture behavior or light/peroxide context. Replacing missing information with an arbitrary preset would not validate the reaction.
3. **Unsupported model scope:** six positives remain unmatched: **A305–A307 and A316–A318** (cyclic alkyne, nearby OH, aromatic-adjacent alkyne). Four stay conditional-only: **A303/A304** (internal first-stage E/Z unassigned) and **A309/A320** (additional alkyne/selectivity). HCl and two-HI output limitations also persist in the broader reagent models; the frozen alternatives include one HI case, not a complete HCl/HI challenge set.
4. **Incorrect expectation, not demonstrated incorrect product:** **A304** expects one shifted-double-bond product. Independent rebuilding confirms the engine's two original-site products instead. Its unchanged literal “Incorrect result” flag must be reported as an oracle defect, not hidden or used to force a wrong engine product. No new production graph error was demonstrated by these zero-score checks.

Replay generation-qualified/full-score IDs: **A300–A302, A308, A311–A315, A319, A323** (11). Three additional positives score partial, A304 retains the incorrect-result flag, six are unsupported, and two controls remain correctly rejected.

### Dihydroxylation: 0/11

1. **Missing information:** all frozen cases select `catalyst: osmium` but omit **`workup: aqueous-release`**. The ten matched positives therefore retain conditional 2D and cannot run the free-diol 3D endpoint. Missing osmium is not the cause. Solvent is unevaluated, but is not the current gate's missing key.
2. **Potentially excessive matching policy:** distinguishing an osmate-bound stage from a released diol is chemically meaningful. Requiring one exact flag for every setting is nevertheless a reporting convention, not proof that every real osmylation requires a separate identical workup step. A validated aqueous reaction/release profile could eventually satisfy that semantic requirement without inventing a separate operation. Merely selecting “water,” however, must not silently prove release, catalyst removal, completion or a safe procedure.
3. **Unsupported reagent model:** **A255** selects actual **NMO**, not H2O2. The current engine implements only a bounded Os/H2O2 net model and rejects NMO. No choice of workup fixes that. It is a software/reagent-coverage gap, not a finding that NMO cannot support dihydroxylation. Do not replace NMO with peroxide to improve a score.
4. **Scoring/evidence limitations:** after release confirmation, **A242–A251** all have generation-qualified options. **A245** remains partial under the frozen cyclic-stereo verification flag, leaving **9/11 full**, one partial and one unsupported. The negative control **A252** remains correctly rejected. No newly incorrect product was demonstrated, but full protocol/chemoselectivity validation is a separate issue below.

## 3. Why simply filling selectors is not a scientifically complete benchmark

The model selectors describe much less than a complete, independently checked reaction context. They do not establish all relevant reagent formulations, concentrations, actual equivalents, exposure, temperature ranges, duration, release chemistry or competing conversions. Nor does a valid 3D conformer establish conversion or experimental selectivity.

A significant evidence mismatch emerged for dihydroxylation. Its cited checked Organic Syntheses preparation uses **NMO/OsO4 for the productive olefin-to-diol step**; H2O2 is used in preparing NMO. The discussion separately distinguishes peroxide-based osmylation and its overoxidation limitations. That source cannot be treated as validation that generic Os/H2O2 plus a checkbox gives a clean diol for every benchmark structure. [Checked Organic Syntheses preparation](https://www.orgsyn.org/demo.aspx?prep=CV6P0342).

The publisher's abstract of the Milas-reaction reinvestigation reports substantial competing carbonyl products under its studied conditions. Full experimental text was not accessible here; its abstract supports caution, not a ready-made universal H2O2 profile. [Norton and White, Reinvestigations of the Milas Reaction](https://pubs.acs.org/doi/10.1021/ba-1965-0051.ch002).

Likewise, the primary HBr–DMPU work demonstrates formulation-dependent behavior, including competing capture and oxygen-group chemistry. A named formulation is not interchangeable with every “polar aprotic” setting. [Primary HBr formulation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5682921/). Specialized iridium transfer-HCl chemistry uses a different donor/catalytic system and cannot be substituted for the frozen actual-HCl identity merely as a condition alias. [Primary transfer-HCl study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7028031/).

Therefore **no claim is made that all 53 positive cases already have independently validated, condition-complete profiles**. Some profiles need source verification; some chemistry is outside the engine; some stereo/selectivity remains unresolved. A proposed benchmark must expose those gaps rather than fabricate favorable settings.

## 4. Proposed versioned condition-complete benchmark — design, not implementation

Proposed identity: **Reaction Conditions Companion v1.0**, initially a **draft specification**. It must run beside, never overwrite, the frozen benchmark.

### Identity and coverage

- Retain immutable parent identities **A001–A347**, chemical structures, actual reagent identities, equivalent stages, negative controls and original expectations, with parent-file checksum. Do not select only cases that already work.
- First activation scope: **58 original rows** — X2 23, HX 23, dihydroxylation 12 — comprising **53 positives and five controls**. The other 289 parent rows remain explicitly “not condition-profile-reviewed in v1 scope,” not silently certified as complete.
- The selected rows are A278–A299 plus A322; A300–A321 plus A323; A242–A252 plus A255. All sets are disjoint. These remain the same chemical cases; condition variants are child records, not additional positive cases in the denominator.
- Keep the frozen result untouched, including A304. A separate proposed v1 oracle erratum can preserve the original expectation and identify the independently corrected one. It needs explicit approval/versioning before use. No erratum is applied by this addendum.

### Required per-case record

| Field group | Required content / guard |
| --- | --- |
| Parent identity | Original ID, parent SHA-256, exact substrate/reagent identity and selected site/stage |
| Reference profile | Versioned profile ID; named reaction model and assertion scope; actual reagent formulation and amount basis; compatible medium; catalyst/activation; temperature range; relevant initiation exclusions; release/workup semantics |
| Applicable/not applicable | Every field explicitly specified, verified not applicable, or unknown; do not insert a fictitious catalyst/workup where none is needed |
| Independent evidence | Primary source and exact location, experimental scope, matched features, justified extrapolation to this case, exclusions/competing chemistry, reviewer sign-off and evidence status |
| Release/catalyst accounting | Whether product release is modeled or assumed; omitted catalytic/workup species; formal net mapping versus experimental atom provenance |
| Independent product oracle | Original-site bond edits, atom/charge inventory, permitted constitutional/stereo alternatives, spectator retention, explicit unknowns and expected byproducts; not generated by the production transformer |
| Profile validity | `reviewed-applicable`, `evidence-gap`, `incompatible`, `unsupported-engine-model`, or `out-of-review-scope`; only the first establishes profile completeness |
| Workflow observations | Match outcome, 2D result, 3D permission and actual result, stereo assertion scope, mapping/calculation checks, mechanism capability, reason codes |
| Version history | Separate chemistry-engine, condition-profile and oracle versions; approvals, changes and old/new comparison |

“Condition-complete” must mean **complete for the stated bounded assertion**, not a claim of laboratory readiness or complete experimental reproduction. Time, supply, release or other relevant variables cannot be left unknown while claiming they were verified. No profiles may claim rates, actual yields, major/minor percentages or safety certification.

### Profile admission procedure

1. Verify a primary reference matches the actual reagent/catalyst system, not merely the reaction-family name. In particular, do not use NMO evidence as H2O2 evidence or photochlorination as generic ionic Cl2 evidence.
2. Assess each parent structure against that evidence: substrate class, additional groups, sites, stereo and competing capture/reduction/oxidation. Explicitly document any bounded extrapolation; unsupported extrapolations remain evidence gaps.
3. Independently specify the acceptable product graph/set and uncertainty before checking engine output. Correct atom mapping does not independently validate chemoselectivity or experimental yield.
4. Review the profile against positive cases and counterexamples. An alternative solvent profile requires independent support, not automatic approval of a whole broad menu category.
5. Only then designate the profile ready and run the future companion. Unvalidated cases remain present and visible; report **profile-ready cases / all original positives**, alongside generation outcomes. Do not report only passes / the conveniently ready subset.

### Special cases that must not be normalized away

- **A255:** keep NMO. An evidence-supported NMO profile may still be engine-unsupported; future implementation would require its correct co-oxidant/byproduct and mapping/stoichiometry model. It is not a condition-only fix.
- **A304:** retain the frozen expectation in the parent. Any corrected companion expectation is explicitly versioned, independently rebuilt and kept separate from the frozen score.
- **Internal first-stage HX:** complete conditions do not establish E/Z unless the reference profile actually establishes it; otherwise uncertainty remains a supported result, not a secretly assigned conformer.
- **Multiple sites:** profile completeness does not prove mono-site selectivity. Require an appropriately bounded alternative/set representation or retain the selectivity limitation.
- **Controls:** expect rejection of the particular unsupported pathway, not a claim that the material is inert to every possible reaction. Do not use deliberately missing activation to make an incorrect positive result disappear.

This document specifies the benchmark and evidence gates. **No new executable benchmark, populated approved-profile catalogue or new coverage score has been implemented.**

## 5. Reporting system: separate the four questions

| Dimension | Suggested states | What it must not imply |
| --- | --- | --- |
| Structural compatibility | Eligible site(s); partially covered; unsupported environment; invalid structure; separately record reagent support | A valid substrate is not equivalent to a supported reagent system, and “unsupported” is not “chemically impossible” |
| Condition completeness | Missing information; model assumptions entered; independently reviewed profile applicable; incompatible; unsupported/unknown input | Filling every selector is not independent scientific validation |
| Product generation | Verified net graph/set; uncertainty represented; 2D passed; qualified 3D passed; policy-blocked; generation failed | A blocked run is not a broken diagram; a conformer is not evidence of conversion or stereo selectivity |
| Chemistry / oracle correctness | Passed independent stated-scope checks; confirmed wrong product/charge/stereo; unresolved competing chemistry; unsupported model; benchmark-oracle defect | Never merge a defective expectation, unknown chemistry and a demonstrated engine product error into one failure count |

Display mechanisms and calculator confidence as capabilities attached to these results, not as a disguised fifth claim of complete chemistry. For example, all three reviewed families may have valid net diagrams while their full elementary mechanism remains unimplemented.

Recommended aggregate lines, each with count and denominator:

- Eligible substrate–reagent cases / all original positives; separately break down substrate versus reagent exclusions.
- Reviewed applicable condition profiles / all original positives, and model-settings completeness / matched cases.
- Independently verified product-generation cases / all original positives, with optional ready-subset result also shown and clearly labeled.
- Policy-blocked, unsupported, failed generation, confirmed chemistry error and oracle defect counts, each distinct.
- The original frozen strict score, unaltered, beside the model-setting diagnostic and future profile-validated companion score. Every value carries its version and assertion scope.

Count **cases**, not individual faces, regioisomers or equivalent aliases, for coverage denominators. Required alternatives must all pass the oracle; they are not additive yields or extra successes. An unknown stereochemical input can have a valid uncertainty-aware connectivity result but must not earn credit for a fully specified stereoproduct prediction.

Current headline, stated honestly: **X2: 15 matched / 12 model-generation-qualified / 6 full under replayed old scorer / 0 frozen strict**; **HX: 15 / 11 / 11 / 0**, with A304 separately flagged; **diol: 10 / 10 / 9 / 0**. None is a measured experimental-success rate or an approved v1 profile-complete score.

## 6. Scientifically justified alternative conditions worth evaluating

| Opportunity | Required evidence before acceptance | Safeguard that stays |
| --- | --- | --- |
| X2: named compatible non-capturing media rather than exact `dry` token | Halogen-, substrate- and stage-specific primary support; solvent nucleophilicity, water and initiation context | Do not turn aqueous/alcohol capture, photo/radical chemistry, Cl2 stereo gaps or multiple-site uncertainty into ordinary dihalogenation |
| HX: validated reagent formulations and temperature ranges | Same actual HX identity, protocol-specific orientation/stereo and competing-group assessment | Do not grant all polar-aprotic solvents or all heated settings permission; no peroxide/radical model inferred |
| HX: optional separate activation only where a validated model needs it | Exact compatible catalyst/reagent system and source scope | Pd/Pt or “acid” is not a substitute for an unimplemented specialized HCl protocol; do not change donor identity invisibly |
| Diol: semantically equivalent release in a validated aqueous profile | Evidence that the represented free-diol endpoint is justified, with explicit release/catalyst-species limitations | Water selection alone does not prove completion, isolation, catalyst removal or safety |
| Diol: source-supported reaction media | Correct Os/co-oxidant-specific evidence and substrate scope | Do not borrow NMO solvent/chemoselectivity claims for H2O2; keep overoxidation and uncertain stereochemistry visible |

These are candidates for bounded validation, not permissions granted by this review. Unspecified does not mean unfavorable, and unsupported does not mean impossible. Conversely, a source-supported alternative may still require future engine work; it must not be admitted merely to eliminate a zero score.

## 7. Specific frontend proposals, within the existing layout

1. Show compact independent badges: **“Structure supported”**, **“Conditions incomplete”**, **“Conditional 2D available”**. For unsupported NMO use **“Reagent system not supported”**, not a generic no-reaction claim.
2. Provide a **“Complete missing conditions”** action that focuses the existing fields and lists all missing requirements together. X2: medium; HX: medium and temperature; diol: release/workup confirmation. Explain when no current control can resolve a protocol/stereo limitation.
3. Explain “Dry / no water” as a model assumption, not a scientifically approved solvent list. Future reviewed profiles should show actual medium/formulation and remaining unknowns.
4. Once profiles are independently approved, offer an opt-in **“Use reviewed profile”** action with a visible preview of changed settings and linked evidence. Never silently fill assumptions or substitute a different reagent/compound.
5. For the diol release field, state what is being assumed about the displayed free diol and what remains unmapped. A reviewed profile may satisfy an equivalent release semantic; otherwise require explicit acknowledgment or retain 2D-only.
6. Beside a disabled 3D control, provide keyboard-accessible **“Why unavailable?”** guidance. Distinguish missing information, unsupported chemistry, unassigned stereo, policy limitation and actual generation failure. A block must not erase the valid 2D result or label it failed.
7. Keep current stale-result protections and theoretical-amount warnings. Revalidate any retained site choice after condition changes; never preserve an old 3D permission or calculated outcome without rechecking. Aliases and constitutional alternatives must remain distinguishable.

No frontend change, profile button, new example or layout redesign was made.

## 8. Narrow Phase 4F recommendation

**Yes, but do not define success as making the frozen zeros disappear.**

Recommended controlled scope:

1. Fix the independently reproduced unsupported-condition-key validation issue from the main Phase 4E audit. Reject/report unknown fields; do not infer new chemistry from them.
2. Separate eligibility, missing settings, uncertainty and render permission in the shared evidence/reporting contract. Resolve the Lindlar multi-site policy inconsistency explicitly rather than broadening unrelated permissions.
3. Add the concise condition-completion/why-blocked guidance above within existing cards and controls. Preserve calculators, existing theoretical warnings and stale-result handling.
4. Implement the **separate versioned companion framework and reviewed-profile manifest**, only after approving this design. Start with a small independently reviewed subset; keep all target cases represented and visibly report the profile-review backlog. Preserve the original benchmark and historical scores. Any A304 oracle correction is versioned and explicitly authorized, never a production-product workaround.
5. Independently validate the proposed profile mappings before accepting any alternative conditions. Clarify the Os/H2O2 versus NMO evidence gap; keep unvalidated systems conditional/unsupported. If this requires a new reagent, mechanism or selectivity model, document and defer it rather than expanding Phase 4F.

Acceptance: the 2,829 existing regression tests remain the baseline; future justified expectation changes are disclosed. Add independent tests for condition schemas, missing versus alternate profiles, negative controls, stale permissions, release semantics, product alternatives and confidence propagation. The frozen 347-case inputs must remain byte-identical. Report profile-review coverage and correctness independently of score improvements.

Excluded from this small phase: adding NMO, unvalidated HCl/two-HI completion, radical pathways, arbitrary competing-reaction prediction, new stereoselectivity, relaxed structural guards, new reaction families, curated examples, experimental rates/yields or publication.

## 9. Evidence and preservation

- The separate replay covers the **58 target rows**, not a replacement 347 run. Every matched option produced a valid diagram; allowed runs returned 3D, and blocked options remained blocked. The literal scorer outcomes above were obtained without editing its code or expectations.
- The original benchmark script SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.
- All **320 pre-existing inventoried project files**, including production, tests, benchmark and prior reports, remain unchanged. Only this addendum and its evidence JSON were added. No benchmark implementation or application change was performed.
- The preceding Phase 4E full run of 2,829 tests, TypeScript and build remains the verified baseline; this addendum did not rerun that entire suite or claim new regression tests. Its additional work consists of read-only replays, source/reference review and preservation checks.

[Per-case replay and preservation evidence](reaction-lab-phase4e-zero-score-addendum-results.json). Source points: [diol condition gate](</Users/rc/Documents/Capstone project/server/reaction_conditions.py:168>), [X2/HX condition gates](</Users/rc/Documents/Capstone project/server/reaction_conditions.py:269>), [diol reagent model/reference](</Users/rc/Documents/Capstone project/server/dihydroxylation_rule.py:1>), [frozen evaluation](</Users/rc/Documents/Capstone project/scripts/audit_reaction_lab.py:289>) and [existing release selector](</Users/rc/Documents/Capstone project/src/reaction-lab.ts:133>).

**Stop: Phase 4E investigation/design complete. Phase 4F is proposed only.**
