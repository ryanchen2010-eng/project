# Phase 4A — Alkyne partial hydrogenation

Completed 2026-10-15. **Existing Lindlar/H₂ pathway only.** No new reaction family, reducing system, layout, Calculator arithmetic or curated example was added. No commit, push, deployment or publication.

## 1. Original implementation and benchmark

The previous public matcher supported one-H₂/Lindlar reduction of isolated acyclic **terminal C/H alkynes**. Internal alkyne cis generation was explicitly unimplemented; oxygen spectators and specified tetrahedral centers were excluded. The mapped edit already distinguished one H₂ for partial reduction from two for full reduction. It had no catalytic surface mechanism and only generic reference-condition assessment.

The saved Phase 3H results establish the baseline: **4/10 positive cases fully supported (40%)**, plus one correctly rejected saturated control. The original 347-case script and expectations were not changed.

## 2. Updated benchmark

**8/10 positive cases fully supported (80%)**, two unsupported positives and the same correctly rejected control.

| Fixed case | Before | After |
| --- | --- | --- |
| A267: 1-butyne | Full | Full |
| A268: 1-decyne | Full | Full |
| A269: branched terminal alkyne | Full | Full |
| A270: 3-hexyne | Unsupported | Full, (Z)-hex-3-ene |
| A271: 2-hexyne | Unsupported | Full, (Z)-hex-2-ene |
| A272: cyclooctyne | Unsupported | Unsupported: ring-specific geometry/strain not validated |
| A273: 4-pentyn-1-ol | Unsupported | Full: remote OH retained |
| A274: phenylacetylene | Unsupported | Unsupported: aromatic-adjacent compatibility outside this increment |
| A275: distant specified center | Unsupported | Full: physical configuration retained |
| A276: 1,7-octadiyne | Full | Full: independent mapped sites retained |
| A277: saturated negative control | Correctly rejected | Correctly rejected |

The fixed benchmark mainly checks connectivity and workflow; **its internal-alkyne expectations are not independent Z specifications**. New separate fixtures, stereochemical checks and coordinate checks supply that verification, without rewriting the benchmark or inflating its denominator.

Whole benchmark: **183 full, 25 partial, 101 unsupported, 38 correctly rejected; no incorrect-result rows**. All 336 unrelated rows retain their exact products, option counts, statuses and workflow outcomes. Of those, 331 entire rows are identical; five full-hydrogenation rows have **notes-only** changes (A259, A260, A261, A263, A264): obsolete claims that internal partial reduction is unimplemented were removed, and partial-pathway rejection explanations now accompany pair-wide notes. Their full-reduction chemistry did not change.

Benchmark SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 3. Structural compatibility improvements

New dedicated [site policy](</Users/rc/Documents/Capstone project/server/alkyne_partial_hydrogenation_rule.py>) uses the existing shared compatibility/edit architecture, not molecule names or formulas. It supports screened neutral, closed-shell C/H/O substrates containing:

- Terminal and internal isolated acyclic alkynes, longer chains and branching.
- Ordinary remote saturated aliphatic alcohols and dialkyl ethers.
- Distant specified tetrahedral centers, including internal-alkyne substrates.
- Well-separated independent C≡C sites as theoretical single-site transformations.

The screen is intentionally bounded: oxygen must be at least four graph bonds from the selected triple-bond carbons; additional isolated triple bonds must have at least four bonds between their closest endpoints; specified centers must be at least two bonds away. These are conservative **software validation boundaries**, not measured kinetic thresholds or proof of universal inertness/selectivity.

Equivalent sites are grouped in the existing `reactionOptions` presentation, using identical isomeric products plus a chirality-aware full-graph automorphism. All original site IDs and mapped aliases remain addressable. Different sites/products stay selectable. The fixed benchmark's legacy two-site contract is preserved.

## 4. Stereochemistry and atom mapping

Internal products receive cis/Z geometry from the validated **net syn-addition relationship**, not a random conformer. Within this local C/H scope, each internal product carbon bears one carbon substituent and one hydrogen, so this same-side relationship is Z. Terminal products, including ethene, receive no invented E/Z designation. This distinction follows the existing [alkyne-reduction reference](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes).

The exact edit is C≡C → C=C, H–H cleavage, and one new C–H bond at each selected carbon. Both incoming hydrogen maps come from the actual H₂ molecule. Unselected bonds, atom identities, charges, explicit hydrogen inventory and distant physical configurations are checked through serialization. Independent CIP reassignment includes a demonstrated **R→S label change without physical inversion**.

The shared validator still rejects arbitrary new/lost stereochemistry. This pathway separately authorizes and verifies only its newly formed cis double bond; the shared spectator check is applied with only that independently checked new annotation removed from a validation copy. No generic stereo safeguard was relaxed. Trans/unsigned internal products, spectator edits and broken provenance have negative tests.

Enhanced/relative, nonstandard, invalid-center and misplaced directional annotations are screened before canonicalization can silently erase them. The flag is specific to this pathway and does not change other alkyne reaction permissions.

## 5. Reagents, conditions and calculator safeguards

Actual neutral H₂ and **Lindlar activation** are required by the selected model. Missing/none activation, ordinary metal, acid, osmium or radical settings do not establish selective partial reduction. Ordinary unpoisoned hydrogenation can continue beyond alkene; a stoichiometric one-H₂ calculation alone does not establish experimental stopping. The [checked Lindlar procedure](https://www.orgsyn.org/demo.aspx?prep=CV5P0880) also documents that hydrogen uptake does not simply stop completely after the target amount.

The Phase 3H evidence/context contract now covers this pathway without changing the six alkene-addition assessments. Structural eligibility, required activation, unassessed conditions and rendering permission are separate. Missing/incompatible settings retain a **clearly conditional 2D preview but block 3D/Compare generation**. A selected Lindlar model with unspecified/dry medium permits only a qualified representative conformer; pressure, catalyst state, exact solvent, temperature dependence, contact time, stopping and over-reduction remain unvalidated. Heated, aqueous, alcoholic or generic aprotic settings require separate validation and block this model's 3D output; they are not labeled universally chemically impossible or merely unfavorable preset mismatches.

Visible calculator warnings carry these assumptions, including to the existing standalone catalog. Amounts remain the balanced **one H₂ per selected site** calculation, not an actual yield, sum of alternative products, mono-reduction guarantee or protocol. All formulas, full molar masses and existing arithmetic remain unchanged.

Na/NH₃, Li/NH₃, alternative hydrogen donors and isotope-specific mechanisms were not added.

## 6. Mechanism and visualization

This is a mapped **net syn transformation**, not a catalytic surface mechanism. No discrete ionic/radical intermediates, activation energies, facial ratios or catalyst cycle were invented. The public mechanism field remains `null`, and capability/diagram/information text says so explicitly.

Tests verify exact 2D/3D atom links and independent cis geometry of generated internal products, including coordinate-derived stereochemical reassignment. Coordinates represent the assigned identity; they do not select or predict the outcome. Distant configured 3D centers are independently checked against the graph assignment.

Browser verification used searched **2-butyne + H₂** through the existing controls: the cis product appeared in 2D and 3D, clicking carbon 2 selected it in both views, and the conditional calculator warning remained visible. Changing activation cleared the previous result and blocked 3D while preserving conditional 2D. No user tab was modified; the temporary verification tab was closed.

## 7. Remaining scope and newly restricted cases

Still excluded: cyclic alkynes; aromatic-adjacent/conjugated systems; enynes; carbonyls and other competing reducible groups; nearby O/π environments; propargylic/directed specified centers; unsupported elements/electronic states/stereo; and products exceeding 80 explicit atoms. Phenylacetylene can undergo Lindlar reduction in documented chemistry, but this model's aromatic compatibility is deliberately not enabled here; unsupported does not mean chemically impossible.

Compared with the old permissive terminal rule, **enyne substrates and nearby isolated diynes** now fail closed for unresolved competing chemistry. Previously ungated partial-product 3D calls now require supported Lindlar settings. Unsupported solvent/heating combinations and invalid/enhanced stereo cannot silently acquire a validated alkene outcome. These are documented safeguards, not coverage-driven relaxations. Other alkyne transformation rules remain unchanged.

## 8. Verification

| Check | Result |
| --- | --- |
| Full Python suite | **1,046 passed**, no failures/skips |
| Full JavaScript suite, including calculator fixtures | **899 passed**, no failures/skips |
| Total | **1,945 passed**: previous 1,800 plus 145 new tests |
| New tests | 93 Python, including six authenticated public-route tests; 52 JavaScript |
| Separate partial-reduction diagnostic | 52 cases, 33 canonical options, no failures |
| Existing six-addition diagnostic | 48 cases, 66 options, no failures |
| Unchanged fixed benchmark | 347 cases; four newly supported target rows, no unrelated outcome regressions |
| TypeScript and production build | Pass; existing third-party/large Builder bundle warnings remain |
| Whitespace and artifact checks | Pass |

One original test's obsolete assertion that internal reduction is unavailable was **strengthened and renamed**, not deleted: it now requires the independently specified cis product and verifies that missing catalyst still blocks 3D. Every other original test/fixture is unchanged. Existing shared compatibility/stereochemistry utilities, alkene-addition chemistry modules, curated data, CSS, page HTML, Calculator arithmetic and build/container configuration remain unchanged.

[Machine-readable results and preservation hashes](</Users/rc/Documents/Capstone project/docs/reaction-lab-alkyne-partial-hydrogenation-phase4a-results.json>).

## 9. Recommendation and stopping point

Next recommended increment: review **existing complete alkyne hydrogenation** with its own catalyst/condition assessment and screened spectator compatibility. Do not automatically transfer Lindlar stopping or solvent permissions to it. Its legacy reference-condition labels remain outside this phase's scope.

**Phase 4A is complete and stops here.** These tests support the defined net model, not universal chemical correctness, experimentally complete conditions or product selectivity.

![Internal cis-alkene with linked atom selection and visible calculator caveat](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase4a-preview.png>)
