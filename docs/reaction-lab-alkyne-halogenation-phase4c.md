# Phase 4C — Alkyne halogenation

Completed 2026-10-15. Existing alkyne X₂ pathway only. No new reaction family, reagent selector, layout, Calculator arithmetic or curated example. No commit, publication or deployment. Phase 4D has not started.

## 1. What existed before this phase

Both **Br₂ and Cl₂**, and both * *one- and two-equivalent modes**, already existed. The legacy graph edit changed C≡C to C=C or C–C and attached the actual reagent atoms. It was limited to hydrocarbon substrates without specified tetrahedral centers. First-stage E/Z was unsigned. It had no complete mapped halonium mechanism, no experimental stopping/selectivity model and no appropriate pathway-specific condition/run gate.

The freshly rerun, unchanged 347-case benchmark exactly reproduced the saved Phase 4B results. Alkyne halogenation originally scored **6/21 fully supported (28.6%)**, with seven partial positives, eight unsupported positives and two correctly rejected controls. Counting structural matches, not full-workflow scores, it matched **13/21** positive cases.

## 2. Fixed benchmark: improved matching, deliberately stricter qualification

| Measure | Before | After |
| --- | --- | --- |
| Fully supported positive cases under the exact fixed inputs | 6/21 (28.6%) | **0/21 (0%)** |
| Structurally matched positive cases, including conditional 2D | 13/21 (61.9%) | **15/21 (71.4%)** |
| Partial positive cases | 7 | 15 |
| Unsupported positive cases | 8 | 6 |
| Correctly rejected controls | 2 | 2 |

**The fully-supported score fell; it did not improve.** All fixed halogenation inputs omit the dry-medium setting. The previous implementation allowed their 3D runs despite that omission. The new rule requires an explicit compatible non-nucleophilic-medium assumption and equivalent stage before permitting a qualified 3D endpoint. Those same inputs now retain conditional 2D but correctly block 3D. Six formerly full rows therefore become partial. This is a documented restriction, not a claim that their underlying reactions are impossible.

The benchmark also unconditionally marks all first-stage X₂ cases partial for “E/Z selectivity is unassigned,” regardless of the new conditional Br₂ assignment. Neither that historical scoring rule nor its inputs were changed to improve the score.

A **separate companion probe**, adding only `solvent: dry` to the same 21 positive cases, finds **12 cases permitted as qualified net conformers, three conditional-only cases and six unsupported cases**. This is not a replacement benchmark or a rescored 347-case result. New independently configured tests verify the actual first-stage Br₂ geometry, not the historical unsigned expectation.

The fixed script SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

### Exact affected rows

| Fixed rows | Change |
| --- | --- |
| A278–A282 | Simple, long, branched and internal one-equivalent Br₂ cases stay partial; missing-medium gate replaces the previously allowed run. Connectivity is unchanged. |
| A283–A285 | Cyclic alkyne, nearby OH and phenylacetylene remain unsupported, with precise site/capture/conjugation explanations. |
| **A286** | Distant specified center: unsupported → partial under the fixed missing-medium input; qualified E product works with the compatible-medium setting. |
| A287 | Multiple alkynes, one equivalent: stays partial; selective 3D is explicitly blocked. |
| **A289–A293** | Simple, long, branched and internal two-equivalent Br₂ cases: full → partial because the fixed inputs omit the required medium assumption. Products are unchanged. |
| A294–A296 | Cyclic alkyne, nearby OH and phenylacetylene remain unsupported; explanations improved. |
| **A297** | Distant specified center, two equivalents: unsupported → partial under fixed conditions; qualified saturated product works with the compatible-medium setting. |
| **A298** | Multiple alkynes, two equivalents: full → partial for both missing-medium and unresolved one-site selectivity safeguards. |
| A322 | Cl₂ first stage stays partial; E/Z remains unassigned and single-geometry 3D is blocked. |
| A288, A299 | Saturated controls unchanged and correctly rejected. |

Exactly **21 rows changed**, all belonging to alkyne halogenation. All **324 unrelated rows are entirely identical**, including notes, products, option counts, statuses and diagram/run outcomes. Whole-benchmark totals are 178 full, 34 partial, 97 unsupported and 38 correctly rejected; there are no incorrect-result rows.

## 3. Structural compatibility and newly supported structures

A dedicated [alkyne halogenation policy](</Users/rc/Documents/Capstone project/server/alkyne_halogenation_rule.py>) now uses the shared site/edit/stereo validators. Eligibility is graph-based, never based on molecule names or example membership.

- Existing terminal/internal, longer and branched alkynes retain their net transformations.
- Distant absolute tetrahedral configurations survive the selected edit, including both opposite configurations and internal-alkyne examples.
- Screened remote saturated alcohols and dialkyl ethers now have conditional net support. Examples beyond the fixed collection include `C#CCCCCCO`, `C#CCCCCC(O)C`, `C#CCCCCCOC` and `CC#CCCCCCOC`. Br₂ can produce qualified one-/two-stage conformers under the defined settings; Cl₂ with oxygen functionality remains 2D-only pending independent capture/oxidation compatibility.
- Equivalent and inequivalent isolated alkyne sites are separately evaluated. Full-graph, chirality-aware automorphism plus identical isomeric product is required for presentation grouping. Every original mapped site ID remains addressable.
- An ordinary remote saturated cyclohexane ring is independently checked for unchanged ring bonds. Small, fused/polycyclic, heterocyclic and unsaturated ring environments remain conservatively restricted.

Oxygen must be an ordinary saturated, nonactivated environment and at least six bonds from the closest selected alkyne carbon. This excludes short potential capture rings; it is a **software validation boundary, not a measured inertness cutoff**. The fixed “remote OH” example, 4-pentyn-1-ol, has a shortest potential five-membered O–C closure and therefore remains excluded. Near-site/propargylic stereo, acetals, peroxides, carbonyls, competing alkenes and aromatic/conjugated systems do not acquire blanket spectator permission.

## 4. One versus two equivalents and atom provenance

| Selected stage | Net product | Required inventory | Exact net edits |
| --- | --- | --- | --- |
| One X₂ | Vicinal dihaloalkene, C=C | One actual neutral Br–Br or Cl–Cl | 3→2 bond order; one X–X cleavage; two C–X formations |
| Two X₂ | 1,1,2,2-tetrahaloalkane, C–C | Two actual molecules of the same X₂ | 3→1 bond order; two X–X cleavages; four C–X formations |

Every incoming halogen has a unique map from its actual selected reagent molecule. HX, mixed halogens, arbitrary halogen donors, unsupported halogens, isotopes and invalid equivalent counts cannot substitute for X₂. No H is added or removed, no byproduct is invented and the carbon skeleton is retained. Exact identity, charge, connectivity, valence, spectator bonds, fragment count and mapped serialization are validated. The existing 80-explicit-atom limit counts the actual two/four entering halogens.

The existing calculator coefficients are **1:1:1** or **1:2:1**. Equal one-millimole inputs in the two-equivalent propyne/Br₂ model give **0.5 mmol (0.1798405 g)** theoretical tetrahalide, with bromine limiting—not one millimole. Available reagent and experimental completion are not established by choosing a stage. Missing stage defaults only to an explicitly hypothetical unsigned first-stage 2D equation; it cannot authorize 3D.

## 5. Stereochemical outcomes and safeguards

For first-stage **Br₂ under the explicit compatible-medium, nonradical model**, the incoming Br atoms define an opposite-side relationship. The implementation does not simply stamp E onto an arbitrary drawing: it verifies the actual reference atoms, checks their CIP priority over the remaining local C/H substituents, independently reassigns CIP with map numbers removed, and checks serialization. In this bounded local scope the result is E, including **terminal alkynes and acetylene**. Golden structures and coordinate-derived assignments independently verify the representation. This is a qualified anti net model, not an exclusive-product or ratio prediction.

Incomplete/incompatible Br₂ settings leave first-stage geometry unsigned. **Cl₂ does not inherit Br₂ stereospecificity**: first-stage E/Z remains unassigned and is 2D-only. Its generic selectors do not establish a trustworthy single stereochemical product. Qualified carbon-only two-equivalent Cl₂ net products remain available because each former alkyne carbon has two identical Cl substituents and no local E/Z or new stereocenter.

Distant configurations are checked through mapped neighbor-order parity, independently reassigned CIP and representative 3D coordinates. R/S letters are not blindly copied or swapped. The two-equivalent endpoint has no former C=C designation and no invented tetrahedral tag. Tampered cis/unsigned anti-model products, extra bond edits and invalid raw stereo annotations fail validation rather than silently losing information.

## 6. Conditions, competing chemistry and newly restricted calls

The existing condition-confidence framework now includes this pathway. It distinguishes missing settings, the defined net assumptions, unvalidated media/activation and unsupported radical chemistry—not generic “unfavorable” preset mismatches. Evidence and both calculator surfaces carry the same qualification.

3D requires an explicit equivalent stage and the existing dry-medium selector **as a compatible non-nucleophilic net assumption**, not proof that any dry solvent is inert. Water/alcohol media may participate in capture; generic polar-aprotic medium, extra acid/metal activation, radical settings and heated conditions lack the needed model validation. Unknown supply, stopping, concentration, light exposure, time, temperature dependence and experimental selectivity are not invented.

Multiple well-separated alkynes can consume X₂ at other positions. Their selected-site structures retain unselected C≡C only as **conditional 2D bookkeeping**; selective one-site 3D and an automatically saturated/halogenated all-sites product are not asserted. Constitutionally distinct choices remain selectable; equivalent aliases are grouped without losing identities.

Newly restricted calls therefore include previously ungated 3D under incomplete/nucleophilic/radical/forcing settings, selective multi-alkyne 3D, Cl₂ first-stage single-geometry 3D, unscreened complex-ring substrates and malformed stereo. These are explicit model boundaries, not declarations of chemical impossibility.

## 7. Mechanism, visualization and browser verification

Mechanism support remains **net-only**, with `mechanism: null` and an honest unsupported mapped-mechanism capability. No stable vinyl carbocation, complete halonium intermediate, fabricated curved arrows, rates or energy profile were added.

Public match, diagram and run routes verify the same mapped graph. Tests cover halogen placement, order changes, actual one-/two-equivalent provenance, exact 2D/3D atom order and spectator configurations. Browser verification used the existing propyne example: linked Br8 selection appeared in reactants, product and 3D; changing to two equivalents cleared the old result and updated the equation/calculator; changing to Cl₂ first stage cleared old amounts and kept 2D while disabling 3D/Compare. No user tab was changed; the temporary tab was closed.

![Qualified Br₂ first-stage model with linked Br8 selection](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase4c-preview.png>)

## 8. Verification and preservation

| Check | Result |
| --- | --- |
| Python | **1,255 passing** |
| JavaScript | **1,115 passing** |
| Total | **2,370 passing**; all 2,094 original tests unchanged; **276 new** (115 Python, 161 JavaScript) |
| Public authenticated workflow | Seven new route tests pass |
| Independent alkyne X₂ diagnostic | 177 cases, 85 canonical options: 85 verified diagrams, 44 verified runs, 41 correctly blocked runs; no failures |
| Complete hydrogenation regression | 52 cases/32 options, exactly unchanged |
| Partial hydrogenation regression | 52 cases/33 options, exactly unchanged |
| Six-addition regression | 48 cases/66 options, exactly unchanged |
| Fixed benchmark | 347 cases unchanged; all 324 unrelated rows entirely identical |
| TypeScript / production build | Pass; pre-existing large Builder bundle/third-party warnings remain |
| Whitespace | Pass |

No original test expectation was edited. Preservation hashes cover all original source/test/fixture files. Only eight existing server integration, evidence and explanation files changed, plus the new independent pathway module, diagnostic, tests and fixture. Shared chemistry/stereo validators, partial/full hydrogenation rules, alkyne HX, alkene Br₂/Cl₂ rules, frontend/CSS/HTML, Calculator arithmetic, build/container configuration and curated data are unchanged.

The fixed audit combines diagram and subsequent run handling: its “preview failed” on gated cases records the blocked run, not failure of conditional 2D. The separate diagnostic distinguishes verified diagrams from correctly rejected runs without modifying benchmark scoring.

[Machine-readable comparison, preservation hashes and verification](</Users/rc/Documents/Capstone project/docs/reaction-lab-alkyne-halogenation-phase4c-results.json>).

## 9. Chemistry grounding and next recommendation

The existing one-/two-X₂ net accounting and ordinary trans addition context are described in [OpenStax, alkyne HX/X₂ additions](https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2). This textbook summary is not proof of universal substrate compatibility or exclusive products. The primary [photochlorination study of 1-butyne](https://www.sciencedirect.com/science/article/abs/pii/S0040402001821372) reports different addition/substitution outcomes under photochemical conditions; it supports excluding that regime, not permission to copy Br₂ stereochemistry. A separately identified [alkylacetylene chlorination study](https://pubs.acs.org/doi/10.1021/jo01300a024) was accessible only as citation/first-page metadata here; no unseen quantitative result from it is asserted.

Graph-distance and functional-group gates are conservative implementation judgments, not experimentally fitted selectivity rules. Passing tests establish consistency of these defined net models, not universal chemical correctness. Broader Cl₂ stereochemical prediction, capture mechanisms, complex cyclic/conjugated substrates and full multi-site conversion need separate validation.

Recommended next pathway: **existing alkyne hydrohalogenation**, with its own orientation, equivalent accounting, condition and stereochemistry review. A separately versioned condition-aware audit could supplement—not silently replace—the frozen benchmark. Neither project has been started. **Phase 4C only is complete; stop here.**
