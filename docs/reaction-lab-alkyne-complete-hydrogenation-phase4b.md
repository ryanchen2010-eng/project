# Phase 4B — Complete alkyne hydrogenation

Completed 2026-10-15. **Existing complete-hydrogenation pathway only.** No new reaction family, catalyst selector, layout, Calculator arithmetic or curated example. No commit, push, publication or deployment. Phase 4A partial-hydrogenation rules and tests remain unchanged.

## 1. Baseline and updated fixed-audit coverage

The saved Phase 4A results establish the complete-hydrogenation baseline: **6/10 positive cases fully supported (60%)**, four unsupported positives and one correctly rejected control. The previous matcher accepted isolated acyclic C/H alkynes, including internal/branched/longer chains. It already consumed two H₂ equivalents, but excluded oxygen spectators and specified centers and used generic reference-condition labels without an activation/run gate. Selected-site products in multi-alkynes were previously allowed in 3D without validating selective retention.

Updated result: **7/10 fully supported (70%)**, one partial positive, two unsupported positives and the same correctly rejected control.

| Fixed case | Before | After |
| --- | --- | --- |
| A256: 1-butyne | Full | Full |
| A257: 1-decyne | Full | Full |
| A258: branched terminal alkyne | Full | Full |
| A259: 3-hexyne | Full | Full |
| A260: 2-hexyne | Full | Full |
| A261: cyclooctyne | Unsupported | Unsupported: ring-specific compatibility unvalidated |
| A262: 4-pentyn-1-ol | Unsupported | **Full: remote alcohol retained** |
| A263: phenylacetylene | Unsupported | Unsupported: aromatic/conjugated environment outside this model |
| A264: distant specified center | Unsupported | **Full: physical configuration retained** |
| A265: 1,7-octadiyne | Full | **Partial: selectable 2D equations, selective 3D blocked** |
| A266: saturated negative control | Correctly rejected | Correctly rejected |

The score is not 8/10: two previously unsupported cases improved, but the unvalidated selective multi-alkyne 3D claim was deliberately restricted. Validation was not relaxed to raise the percentage.

The original **347-case script, inputs, expectations and scoring are byte-identical**, SHA-256 `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. Whole-benchmark statuses are now **184 full, 26 partial, 99 unsupported, 38 correctly rejected; no incorrect-result rows**.

## 2. Expanded structural compatibility

New [complete-hydrogenation site policy](</Users/rc/Documents/Capstone project/server/alkyne_complete_hydrogenation_rule.py>) is a separate consumer of the shared compatibility/edit architecture. General molecular graphs, not names/formulas/CIDs, determine eligibility.

Supported net scope includes isolated acyclic terminal/internal alkynes, longer and branched chains, screened remote ordinary saturated alcohols/dialkyl ethers, and distant specified tetrahedral centers. Multiple well-separated isolated triple bonds can supply individually selectable **bookkeeping-only** equations, not experimental selective conversion.

Conservative screens require oxygen at least four graph bonds from the selected alkyne, additional triple bonds separated by at least four graph bonds between closest endpoints, and specified centers at least two bonds from the selected site. These are software validation boundaries, not measured kinetic cutoffs or proof that arbitrary remote groups are inert. Benzylic/allylic, nearby/propargylic, cyclic-oxygen and acetal-like environments do not inherit ordinary ether/alcohol permission.

## 3. Correct products, stoichiometry and provenance

The existing net edit remains **selected C≡C → C–C + four incoming H**. Two actual neutral H–H graphs are required, with unique reaction maps. Each H₂ contributes one H to each selected carbon. The independent edit contract requires exactly seven changes: one triple-to-single order change, two H–H cleavages and four C–H formations.

Shared validation checks exact atom identity/isotope/charge, explicit hydrogen inventory, unchanged bonds, physical configurations, connectedness and mapped serialization. The saturated selected carbons must be sp³ CH₂/CH₃, with neither residual π bonding nor invented E/Z/tetrahedral configurations. No byproduct is invented.

The displayed equation and calculator use coefficients **1 substrate : 2 H₂ : 1 selected-site product**. Supplying one mole each of substrate and H₂ therefore gives a theoretical maximum of 0.5 mole product, not one mole. The separate X₂/HX-equivalents selector does not change hydrogen stoichiometry. The actual available hydrogen supply is not established by choosing an H₂ identity.

This two-equivalent reduction and its distinction from selective Lindlar reduction are grounded in the [alkyne-reduction reference](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes). Surface-mediated chemistry and competing unsaturation require more than a balanced equation; see the [hydrogenation reference](https://openstax.org/books/organic-chemistry/pages/8-6-reduction-of-alkenes-hydrogenation).

## 4. Catalyst, conditions and confidence safeguards

The existing **Metal (Pd/Pt)** selector activates the bounded full-reduction model. No Ni-specific profile or new catalyst/reductant family was added. Unknown catalyst values, Na/NH₃ and Li/NH₃ are not aliases for this model.

- Missing/no catalyst: required activation is absent; conditional 2D remains, 3D is blocked.
- Lindlar: explicitly identified as the separate partial-hydrogenation setting; it cannot validate this alkane endpoint.
- Acid, osmium or radical activation: not validated as this complete-hydrogenation catalyst; no full 3D result is asserted.
- Unspecified/dry/ethanolic medium with the existing active-metal selector permits a **qualified net conformer**, not a solvent-specific protocol. No Lindlar solvent permissions were copied.
- Aqueous/generic-aprotic media and heated conditions need separately validated catalyst/substrate compatibility and block the full-reduction 3D assertion in this bounded model. They are not called universally chemically impossible or experimentally unfavorable.

Versioned evidence distinguishes structural eligibility, required activation, unknown factors and rendering permission. Hydrogen supply, pressure/uptake, catalyst support/loading, contact time, temperature dependence and experimental completion remain explicitly unestablished. Visible and standalone calculator context carries the same limitations; arithmetic is unchanged. A permitted 3D conformer is never labeled a measured or guaranteed reaction outcome.

## 5. Multiple sites and newly restricted cases

Equivalent sites require identical isomeric products **and** a chirality-aware full-substrate automorphism before their presentation choices merge. Every original mapped site ID and alias remains addressable. Non-equivalent constitutional products stay separate.

Active-metal conditions can also reduce another C≡C. Consequently, molecules with multiple separated alkynes retain theoretical selected-site 2D equations and amounts, but **all selective one-site full-reduction 3D calls are blocked**. Their unselected bonds remain unchanged only in the explicitly hypothetical equation. No all-sites product or selective product distribution was invented.

This is intentionally more conservative than Phase 4A's existing qualified one-equivalent conformer policy, which is unchanged. It does not claim that Lindlar selects only one alkyne experimentally. Output permission is distinguished from chemistry confidence.

Other newly restricted full-reduction cases include enynes and nearby additional alkynes, unvalidated activation/medium/heating, invalid/enhanced stereo annotations, and specified centers that cease to be stereogenic after reduction. The latter fail with a precise explanation rather than silently dropping a tag. Previously possible full-product calls without active-metal activation now stop at conditional 2D.

## 6. Stereochemistry, mechanism and visualization

Full saturation creates no E/Z at the selected bond and no new local centers at its CH₂/CH₃ carbons. Distant physical configurations are compared independently of their R/S letters and survive serialization. An independently checked example changes **R→S without inversion** because CIP priorities change. Coordinate-derived assignments are checked against already specified graph configurations, never used to choose a reaction outcome.

This is a verified **net transformation**, not a catalytic surface mechanism. The mechanism field remains `null`; no carbocation, radical, ionic intermediate, surface cycle, rates or activation energies were invented. Hydrogen maps account for the explicit net species, not an experimental surface-exchange history.

Exact 2D/3D atom correspondence, changed-bond highlighting, site selection and calculators pass. Browser verification searched **4-pentyn-1-ol + H₂**, retained its OH, generated the saturated linked model and selected the same oxygen in both views. Entering 0.001 mol substrate and 0.001 mol H₂ correctly gave **0.0005 mol (0.044075 g)** theoretical pentanol. Switching to Lindlar cleared the old model/calculator result and blocked the full pathway's 3D control while keeping its conditional 2D equation. The temporary tab was closed.

## 7. Regression results and preservation

| Verification | Result |
| --- | --- |
| Full Python suite | **1,140 passed**, zero failures/skips |
| Full JavaScript suite, including calculator fixtures | **954 passed**, zero failures/skips |
| Total | **2,094 passed**: all 1,945 existing tests unchanged, plus 149 new tests |
| New tests | 94 Python, including six authenticated public-route tests; 55 JavaScript |
| Separate full-reduction diagnostic | 52 cases, 32 canonical options: 32 verified diagrams, 19 verified runs, 13 correctly blocked runs; no failures |
| Phase 4A partial diagnostic | 52 cases, 33 options; products, diagrams, geometry and gates exactly unchanged apart from pair-wide reasons |
| Six-addition diagnostic | 48 cases, 66 options, **exactly unchanged** |
| TypeScript, production build | Pass; pre-existing third-party/large Builder bundle warnings remain |
| Whitespace and preservation checks | Pass |

All **336 unrelated fixed rows retain their exact products, option counts, statuses and workflow outcomes**. Of these, 333 whole rows are identical. Three partial-hydrogenation rows have notes-only changes: A272/A274 now include the full pathway's more precise rejection reasons, and A275 no longer falsely says the full pathway rejects its distant center. Partial-hydrogenation coverage stays **8/10 (80%)**. Alkyne halogenation and hydrohalogenation results are unchanged.

No original test expectation required modification. Preservation hashes confirm the Phase 4A rule, existing tests/fixtures, shared stereo/compatibility validators, other chemistry-rule modules, Calculator arithmetic, CSS/HTML, curated data and build/container configuration are unchanged. Edits to existing source are limited to nine metadata/integration/condition/explanation files; the new full-reduction module does not grant permissions to unrelated reactions.

The fixed audit combines diagram/run error handling, so A265's `preview: failed` reflects the correctly blocked later **run**, not failure of conditional 2D. The separate diagnostic records diagram and run separately without altering fixed scoring.

[Machine-readable results, fixed benchmark and preservation hashes](</Users/rc/Documents/Capstone project/docs/reaction-lab-alkyne-complete-hydrogenation-phase4b-results.json>).

## 8. Remaining limitations and next recommendation

Cyclic/conjugated/aromatic-containing substrates, competing alkenes/carbonyls, unscreened nearby groups, unsupported catalyst environments, broader elements/electronic states, unretainable stereo and products over 80 explicit atoms remain outside scope. These exclusions are model limitations, not declarations of chemical impossibility. No experimental one-site selectivity, complete reaction conditions, rates, pressure, yields or distributions are predicted. Complete reduction of all unsaturated sites is not implemented.

Recommended next increment: review **existing alkyne halogenation**, particularly equivalent counts, one-equivalent stereochemistry and condition confidence, with separate validation. It has **not** been started.

**Phase 4B is complete; stop here.** Passing tests establish consistency within the defined tested net model, not universal chemistry correctness.

![Complete selected-site reduction, preserved oxygen link and two-H2 calculation](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase4b-preview.png>)
