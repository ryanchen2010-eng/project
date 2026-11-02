# Phase 4E — Alkyne-family consistency review

Date: 2026-10-16. **Read-only audit.** No production code, existing test, benchmark, layout, Calculator, curated example or earlier report was modified. Only this review, supporting evidence and an audit screenshot were added. No Phase 4F fixes or new chemistry were implemented.

## 1. Executive summary

The four pathways are internally consistent about their **represented net bond edits, reagent inventories, charge, product connectivity and mapped atom identities** in the exercised cases. No new incorrect product, failed conservation check or wrong assigned stereochemistry was demonstrated. This is a finite review, not proof of universal chemistry correctness.

All **2,829 existing tests pass unchanged**: 1,416 Python and 1,413 JavaScript. All 347 fixed benchmark rows, including notes and workflow fields, exactly match Phase 4D. The known A304 incorrect-result flag is independently confirmed to be a **frozen expected-product defect**, not a newly discovered engine defect.

The main outstanding problems are confidence consistency and usability:

1. **Confirmed API confidence defect:** unknown condition keys such as `peroxide: true` and `light: UV` are silently discarded. The four documented net models can still generate 3D after that explicit but unsupported information is supplied. The recognized `catalyst: radical` control does block correctly.
2. Lindlar selected-site diyne structures permit conditional 3D, while the other three pathways block analogous unresolved one-site 3D. This is a confirmed policy inconsistency, not evidence that the Lindlar product graph is impossible.
3. A “3D permitted” result consistently disclaims experimental prediction, but the requirements for permitting that hypothetical representation vary substantially. Some boundaries are chemistry-driven; others are software evidence/reporting choices, especially the HX ambient requirement and generic dry-medium selector.
4. The fixed benchmark conflates a blocked 3D run with a failed preview, and contains the A304 connectivity error. Its strict scores must not be read as structural coverage or silently corrected.
5. Missing-setting labels are visible, but actionable guidance, pathway-specific rejection reasons and equivalent-site discovery can be clearer. A genuine coverage gap also remains: phenylacetylene is excluded even from Lindlar reduction, despite the cited primary procedure demonstrating this substrate.

**Recommendation:** a small, separately authorized Phase 4F confidence/explanation/diagnostic fix phase is worthwhile before expanding chemistry. Do not use it to loosen unvalidated chemical restrictions or add a full mechanism.

## 2. Method and evidence

- Read all four rule modules, shared compatibility/edit validation, reaction planning, condition/evidence contracts, public match/diagram/run integrations, mechanism capabilities, frontend selection/gates and calculation context.
- Ran all existing tests, the unchanged fixed audit, all four existing independent pathway diagnostics, TypeScript, production build and whitespace checks.
- Ran a temporary read-only cross-pathway probe: **42 substrates × 12 modes = 504 structural cases**, plus **144 condition cases**. Its **416 returned options** yielded 150 3D representations and 266 correctly blocked run attempts; all 416 diagrams and independent net-contract checks passed. These are diagnostic scenarios, not new regression tests or curated examples.
- The probe separately reconstructed expected bond changes and incoming-atom inventories; checked unchanged mapped connectivity, charges, physical tetrahedral parity, reassigned CIP labels, local alkene tags, coefficients/mass balance and exact 2D/3D atom links. It used production parsing/mapped graph access, but did not substitute the production validator for the independent checks.
- Existing regression tests also check assigned graph versus generated coordinate stereo and authenticated HTTP routes. Browser checks exercised all four pathways using existing propyne examples, missing/entered settings, linked atoms and the calculator.
- Five additional authenticated read-only HTTP probes investigated unexpected condition keys: four affected pathway examples and one recognized-radical negative control. These exposed the confidence defect described below; they are separate from the 648 supported-schema diagnostic scenarios.
- A starting inventory of **317 existing project files** was hashed; every inventoried file remains byte-identical after the audit. Generated build/cache artifacts and temporary diagnostic output are not production-source edits.

Supporting results, exact case IDs, the 42-substrate/12-mode matrix, condition observations and hashes are in [the machine evidence](reaction-lab-alkyne-phase4e-consistency-review-results.json). The new probe remained temporary; no existing test or benchmark oracle was altered.

## 3. Four-pathway consistency table

“3D” below means a qualified hypothetical net conformer, **not a completed experiment**.

| Pathway | Net endpoint / consumed reagent | Local stereochemistry | Key output conditions | Multiple separated alkynes | Full mapped mechanism |
| --- | --- | --- | --- | --- | --- |
| Partial hydrogenation | C≡C → C=C; 1 H2 | Internal cis/Z from syn relation; terminal CH2= has no E/Z | Lindlar required; unspecified/dry medium permitted; explicit heating or unvalidated media block 3D | Grouped/site-addressable; conditional 3D allowed | Not implemented |
| Complete hydrogenation | C≡C → C–C; 2 H2 | Saturated CH2/CH3; no local E/Z or new center | Existing Pd/Pt metal required, not Lindlar; unspecified/dry/ethanolic medium permitted; heating/unvalidated media block 3D | Conditional selected-site 2D only | Not implemented |
| X2 halogenation | 1 X2 → vicinal dihaloalkene; 2 X2 → 1,1,2,2-tetrahaloalkane | Qualified opposite-Br/E first stage; Cl first stage unsigned; saturated endpoint has no E/Z | Explicit stage and dry-compatible-medium assumption; capture/radical/extra activation/heating gate 3D | Conditional selected-site 2D only | Not implemented |
| HX hydrohalogenation | 1 HX → vinyl halide; 2 HX → geminal dihalide | Terminal Markovnikov CH2=; internal regio-alternatives unsigned; saturated endpoint no E/Z | Explicit stage/medium/ambient; independent HCl/HBr/HI gates | Conditional selected-site 2D only | Not implemented |

The selective versus active-metal hydrogenation distinction and internal Lindlar cis relationship are scientifically grounded. The checked primary Lindlar procedure also warns that uptake slows rather than necessarily stops, supporting the existing stopping/over-reduction caveats; it distinguishes solvent compatibility rather than treating every medium as interchangeable. [Lindlar and Dubuis, checked Organic Syntheses procedure](https://www.orgsyn.org/demo.aspx?prep=CV5P0880).

## 4. Structural compatibility: similarities, differences and classification

This table is **matching eligibility**, not 3D permission or a claim of experimental inertness. More detailed mode-specific results are in the machine evidence.

| Representative structure/environment | Partial H2 | Complete H2 | X2 | HX | Classification of difference/restriction |
| --- | --- | --- | --- | --- | --- |
| Acetylene, 1-butyne, 1-decyne | Match | Match | Match | Match | Chemically justified net inventory/orientation differences |
| Symmetric 3-hexyne / asymmetric 2-hexyne | Match | Match | Match | Match; two HX orientations for asymmetric case | Chemically justified; no arbitrary internal HX preference |
| Remote branch `CC(C)CC#C` | Match | Match | Match | Match | Consistent bounded scope |
| Direct branch `C#CC(C)C` / adjacent quaternary carbon | Match | Match | Match | Rejected | Valid conservative HX scope restriction; not proof that these substrates cannot add HX or must rearrange |
| Primary OH four bonds from nearest alkyne end, `C#CCCCO` | Match | Match | Rejected | Rejected | Different adsorption/hydrogenolysis versus electrophilic capture risks are chemically justified; numeric cutoffs are conservative software boundaries |
| Sufficiently remote primary OH / ordinary ether | Match | Match | Match | Match | Matching consistent; output gates differ because HX O substitution/cleavage and Cl2/O compatibility remain unresolved |
| Remote secondary/tertiary alcohol or tertiary ether | Match | Match | Match in screened cases | Rejected | Valid conservative HX substitution/cleavage restriction, not universal inertness in other pathways |
| Distant specified tetrahedral center | Match | Match | Match | Match | Physical parity retained, CIP independently recomputed |
| Specified propargylic center | Rejected | Rejected | Rejected | Rejected | Unsupported directed/near-site chemistry requiring future validation; not demonstrated stereo corruption |
| Equivalent and non-equivalent separated diynes | Match | Match | Match | Match | Matching consistent; Lindlar 3D permission differs, discussed below |
| Isolated enyne / specified remote E-alkene | Rejected | Rejected | Rejected | Rejected | Competing chemistry unmodeled; Lindlar chemoselective coverage is a future development opportunity, not an automatic permission |
| Conjugated diyne/enyne, cyclic alkyne | Rejected | Rejected | Rejected | Rejected | Valid conservative restrictions: no conjugated-site or strained-ring model |
| Remote saturated cyclohexane | Match | Match | Match | Match | Consistent bounded spectator treatment |
| Remote saturated fused rings | Match in tested case | Match in tested case | Rejected | Rejected | Valid conservative electrophilic-model restriction; no evidence every fused spectator is chemically incompatible |
| Phenylacetylene | Rejected | Rejected | Rejected | Rejected | **Unnecessary implementation restriction for the independently documented Lindlar example**; other pathways need their own validation |
| Carbonyl, ester, amine, peroxide, aromatic spectators | Rejected in probe | Rejected in probe | Rejected in probe | Rejected in probe | Unsupported chemistry/competing groups; some may eventually be validated individually |

The primary Lindlar procedure's phenylacetylene-to-styrene check makes that particular partial-reduction exclusion an evidenced coverage gap. It does not authorize arbitrary aromatic/multifunctional hydrogenation or retention of every aromatic ring under full reduction. No restriction was removed.

All four share neutral connected closed-shell C/H/O scope, unsupported isotope/nonstandard-stereo exclusions and an 80-explicit-atom product cap that includes the incoming atoms. These are finite implementation boundaries, not general chemistry laws. Small-ring, raw stereochemical-annotation and complex-environment checks fail conservatively.

## 5. Reagents and scientifically justified condition differences

### Hydrogenation

Lindlar is not an interchangeable label for ordinary Pd/Pt. The partial product stays only a net alkene representation; active-metal full reduction consumes two actual H2 molecules and does not inherit the partial gate. The UI correctly switches permissions when the catalyst changes. Exact H2 amount/pressure, contact time, loading, catalyst state and experimental conversion are unknown in both models.

Allowing screened substrate OH while rejecting an alcohol **solvent** under Lindlar is not itself contradictory: these are different environments, and the checked primary procedure cautions about alcohol media. Complete reduction's ethanolic-medium permission is a different bounded catalyst model, not borrowed Lindlar permission.

### Halogenation

Br2 and Cl2 are independently identified; neither is HX. Water/alcohol capture and radical/photochemical alternatives must not be silently represented as ordinary X2-only addition. A suitable-medium requirement is therefore chemically meaningful when claiming a reaction outcome. However, the UI's “Dry / no water” category does **not** by itself establish solvent non-nucleophilicity or compatibility; the backend appropriately calls this an assumption.

Qualified Br2 first-stage anti geometry is not claimed to be universal or exclusively E under all protocols. Cl2 first-stage unsigned/2D-only handling, and its separate oxygen-functionality gate, are conservative evidence limitations rather than demonstrated wrong stereochemistry. Two-Cl2 non-O products may be represented in 3D because no first-stage E/Z is being asserted.

An evidence-traceability concern remains: the rule's `CHLORINE_SOURCE` points to **photochlorination of 1-butyne**, while the selected ionic net model excludes radical initiation. The bibliographic identity was verified; the full paper was not accessible during this audit, so no quantitative or general ionic-mechanism conclusion was borrowed from it. That citation cannot alone validate all dark/non-nucleophilic Cl2 settings. [Bibliographic record and original DOI](https://hero.epa.gov/reference/5573823/).

### Hydrohalogenation

| Reagent/stage | Conditional 3D policy after explicit dry/ambient/stage settings |
| --- | --- |
| HBr, terminal first stage | Allowed if all structural/competition gates pass |
| HBr, second stage | Allowed for bounded single-site geminal alternatives |
| HI, terminal first stage | Allowed in bounded net model |
| HI, second stage | Still 2D-only: reagent-specific completion/stability scope unvalidated |
| HCl, either stage | Still 2D-only: current selectors do not establish validated formulation/activation |
| Any HX, internal first stage | E/Z unsigned, 2D-only |
| Any HX, retained remote O or additional alkyne | Competing chemistry unresolved, 2D-only |

The reagent-specific caution is reasonable. Published HBr work reports formulation-dependent capture, ether cleavage and internal stereochemistry; none of those protocol-specific outcomes may be imported simply by selecting generic HBr. [Primary HBr–DMPU study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5682921/). Specialized HCl transfer catalysis is not an ordinary HCl/acid/Pd-Pt selector and cannot supply missing permissions here. [Primary iridium shuttle-catalysis study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7028031/).

The **exact ambient requirement for HX**, versus unspecified temperature permitted by the other three, is an explicit software output boundary, not a universal chemical necessity established by this audit. Likewise, missing solvent is treated more permissively for hydrogenation conformers than electrophilic-addition conformers. Neither discrepancy proves the product graph is incorrect. A future policy review should separate graph rendering, evidence completeness and predicted outcomes without automatically relaxing capture, catalyst or stereo safeguards.

### Confirmed unexpected condition-input defect

`_conditions` validates known field values but does not reject or report unknown field names. Authenticated public match, diagram and run calls with otherwise allowed settings plus **`peroxide: true, light: UV`** returned **HTTP 200 and a 3D net product for all four pathways**. Both extra keys disappeared from normalized conditions. For HX, its generic “radical initiation absence” unknown factor remained, but the submitted contrary information was not acknowledged or made blocking.

The control `catalyst: radical` returned `canRun: false` and **HTTP 422** on the HX run route. Thus the radical gate works for the documented selector; the defect is silently discarded unsupported information at the API boundary. Invalid values inside recognized fields are already rejected. The current UI has no peroxide/light input and was not observed bypassing its recognized radical selector.

This is a **condition/confidence bug**, not implementation of a radical family, an anti-Markovnikov product, or proof that every returned graph is chemically impossible. Rejecting unknown keys with a concise unsupported-condition explanation would be safer than silently normalizing them away. Interpreting those keys as a newly supported mechanism would be inappropriate. No production fix was made.

## 6. Strict scores, structural scores and separate replays

| Pathway | Frozen positive cases | Structural matches now | Strict full workflow now | Separate dry/ambient replay: qualified / conditional-only / unsupported |
| --- | ---: | ---: | ---: | --- |
| Partial hydrogenation | 10 | 8/10 | 8/10 | 8 / 0 / 2 |
| Complete hydrogenation | 10 | 8/10 | 7/10 | 7 / 1 / 2 |
| X2 halogenation | 21 | 15/21 | 0/21 | 12 / 3 / 6 |
| HX hydrohalogenation | 21 | 15/21 | 0/21 | 11 / 4 / 6 |

Structural match means at least one returned net option, not a fully validated experiment. HX's 15 includes the independently correct A304 products that disagree with the frozen defective expectation. Replays retain the original substrate/reagent/stage and add only `solvent: dry`, `temperature: ambient`. **These are not replacement scores.** Their permitted options were actually generated and checked as 3D; no outcome probability is implied.

Exactly what is missing from the frozen X2/HX inputs:

- **X2:** all 21 positives already select one/two equivalents; every one omits **solvent**. Temperature is omitted too, but is **not** a mandatory X2 setting. Separate extra catalyst activation is not required.
- **HX:** all 21 positives already select one/two equivalents; every one omits **solvent and temperature**. Extra acid is not a required consumed reagent or missing catalyst.
- Partial/full hydrogenation inputs already select Lindlar/metal respectively. Their gates allow unspecified medium/temperature under qualified net assumptions.

Therefore every matched X2/HX frozen option is 3D-blocked. The strict audit requires a successful run, so no row is fully supported. That is an honest strict result under current policy, not proof that all these reactions stopped working. Adding settings does not fix every case: internal HX first-stage geometry, competing sites, Cl first stage and structural exclusions still apply.

For X2 the separate qualified cases are **A278–A282, A286, A289–A293 and A297** (12). Its conditional-only cases are **A287, A298 and A322** (both multi-site stages and first-stage Cl2). Unsupported cases are A283–A285 and A294–A296. For HX, qualified cases are **A300–A302, A308, A311–A315, A319 and A323** (11); conditional-only cases are **A303, A304, A309 and A320**; unsupported cases are A305–A307 and A316–A318.

The frozen first-stage X2 scorer also deliberately retains its old “partial stereo not independently verified” flag; it does not automatically award full support just because the current qualified graph has E assignment. In addition, the audit sets `preview = failed` when a later 3D run raises a gate error, even after a valid 2D diagram. This is a **measurement-label limitation**, not an observed 2D rendering failure. The fixed scorer was not modified.

## 7. Reconciliation of every benchmark row

The question's “21 affected + 324 unrelated = 345” mixes **positive coverage denominator** with **all-row counts**. The two omitted rows are the affected pathway's negative controls.

| Bucket | Positive IDs | Negative IDs | All rows |
| --- | --- | --- | ---: |
| Complete H2 | A256–A265 | A266 | 11 |
| Partial H2 | A267–A276 | A277 | 11 |
| X2 | A278–A287, A289–A298, A322 | **A288, A299** | 23 |
| HX | A300–A309, A311–A320, A323 | **A310, A321** | 23 |
| All other pathways | A001–A255, A324–A347, classified by their existing `path` and `expected` fields | Included within these ranges | 279 |
| Total | 62 alkyne positives + 247 other positives | 6 alkyne controls + 32 other controls | **347** |

Thus each X2/HX comparison is **21 positives + 2 controls + 324 other rows = 347**. A322 is the Cl2 row; A323 is the HI row. Neither is missing or double-counted. All four alkyne buckets together span A256–A323 = 68 rows; 68 + 279 = 347.

The unchanged final whole-audit distribution is **168 fully supported + 47 partially supported + 93 unsupported + 38 correctly rejected + 1 incorrect-result flag = 347**. All 347 rows are exactly identical to Phase 4D, not just their status totals.

## 8. Independent investigation of A304

- ID: **A304**, asymmetric internal hex-2-yne.
- Input: `CC#CCCC` + actual `hydrogen-bromide`.
- Frozen conditions: `{additionStage: one}`; no solvent or temperature.
- Frozen expected set: `CC(Br)=CCCC` and **`CCC(Br)=CCC`**.
- Actual canonical products: `CCCC=C(C)Br` and `CC=C(Br)CCC`.

`CCCC=C(C)Br` is the canonical equivalent of `CC(Br)=CCCC`, 2-bromohex-2-ene. The other correct orientation is `CC=C(Br)CCC`, 3-bromohex-2-ene. The original selected bond remains **C2–C3** in both. The frozen `CCC(Br)=CCC` instead places the double bond at **C3–C4**; that is not the alternative orientation of simple addition at the original triple bond.

For an independent check, a fresh RDKit editor was built directly from the original input, C2–C3 was changed from triple to double, and H/Br were added to opposite endpoints in each orientation without invoking the production transformer. Its two canonical results exactly equal the engine's results.

Public diagrams preserve source maps **2 and 3** as the reacting carbon pair. **Br17 and H18** come from the actual HBr. One alternative adds Br17→C2 / H18→C3; the other Br17→C3 / H18→C2. All other bonds and charges remain unchanged. Both internal E/Z configurations remain unassigned, ratios are null and 3D is blocked; no unsupported stereo result rescues or causes the discrepancy.

**Conclusion: confirmed benchmark defect, not a demonstrated production chemistry defect.** Future corrective action should be a separately authorized versioned benchmark correction/erratum with independent atom-site expectations, preserving the present frozen baseline for historical comparison. Do not change production products to fit the shifted-double-bond expectation. This review did not alter either.

## 9. Cross-pathway stereochemistry

- **Partial H2:** constructed same-side incoming-H relation gives internal cis/Z within the bounded carbon/hydrogen scope. Terminal CH2= products have no invented E/Z. This is a net outcome, not a simulated catalytic surface sequence.
- **Complete H2:** selected site is CH2/CH3, without residual alkene geometry or invented tetrahedral centers.
- **X2:** qualified Br2 places the actual incoming Br atoms opposite, then independently assigns CIP E in its C/H local scope. Anti relationship is not used as a universal “trans product” shortcut. Cl2 first-stage geometry stays unsigned. Two equivalents remove local E/Z and do not create a stereocenter with two identical halogens on each carbon.
- **HX:** terminal Markovnikov products lack E/Z; internal constitutional alternatives remain unsigned; geminal products remove C=C and local E/Z. No anti/trans claim or stereoisomer ratio was invented.
- **Distant stereo:** independent mapped-neighbor parity and reassigned CIP checks passed for both enantiomeric inputs and the priority-changing example `C#CCC[C@H](C)CCCO`. That example stays S under the two hydrogenation graphs but becomes R under the tested X2/HX graphs **without physical inversion**. A CIP-letter change is not itself a stereochemistry bug.

Near-site/enhanced/nonstandard stereo exclusions, Cl2 geometry gaps, unspecified internal HX geometry and unimplemented directed/asymmetric selectivity are **missing coverage**, not observed incorrect assigned configurations. No conformer was used to establish chemical selectivity; generated coordinates only represent an already chosen graph.

## 10. Multiple sites and competing chemistry

For equivalent `C#CCCCCC#C`, each pathway retains two legacy mapped IDs while presenting one canonical product choice with two aliases. Distinct diyne sites remain distinct options; internal HX capture orientations are not incorrectly collapsed. The tested alias routes preserve their own atom maps. The frontend displays the canonical representative but does not expose a full equivalent-alias picker/count at the option itself; this is a discovery limitation, not loss of a distinct constitutional product.

All four preserve the unselected triple bond only in a theoretical one-site equation, not a guaranteed experimental distribution. Complete H2, X2 and HX explicitly block selective 3D. **Lindlar does not have the corresponding competition factor in its run gate** and allows one-site 3D even for non-equivalent multiple sites. Existing notes warn about mono-conversion, so this is not a new false product/connectivity finding. However, catalyst selectivity for triple versus double bonds does not establish selectivity between two isolated triple bonds. The policy difference needs an explicit decision and consistent presentation.

Mixed enynes, close/conjugated diynes, nearby nucleophiles and cyclic alkynes are rejected. Some are chemically reactive, but no validated competitive/all-sites transformation is being offered. No rearranged, cyclized or all-sites product was invented.

Oxygen closure messages calculate the **shortest potential path**, not the reaction's established ring outcome. For propargyl OH the shortest path is three atoms; the other alkyne endpoint can give a different path. Those messages should not be interpreted as a prediction of a three-membered product. Pair-wide `unsupportedReasons` can also combine full/partial hydrogenation messages, obscuring which candidate a reason belongs to. No arithmetic ring-size error was demonstrated here, but pathway/site-specific explanations would be clearer.

## 11. Atom mapping, stoichiometry and mechanisms

| Mode | Incoming atoms | Broken reagent bonds | Formed substrate–reagent bonds | Selected order |
| --- | --- | ---: | ---: | --- |
| Partial H2 | 2 actual H | 1 H–H | 2 C–H | 3 → 2 |
| Complete H2 | 4 actual H in 2 molecules | 2 H–H | 4 C–H | 3 → 1 |
| One X2 | 2 actual X | 1 X–X | 2 C–X, one at each end | 3 → 2 |
| Two X2 | 4 actual X | 2 X–X | 4 C–X, two at each end | 3 → 1 |
| One HX | 1 H + 1 X | 1 H–X | 1 C–H + 1 C–X | 3 → 2 |
| Two HX | 2 H + 2 X | 2 H–X | 2 C–H + 2 C–X; X geminal | 3 → 1 |

All represented atoms/charges and unchanged bonds were conserved in returned options. No coproduct was required or invented for these net additions. Actual donor identities and separate second reagent copies agree across equation, changes, maps and calculator coefficients. H2 maps are net bookkeeping, not experimentally traced surface H exchange.

All four honestly return `mechanism: null` and mark mapped mechanism capability unsupported. The UI hides an absent mapped-mechanism panel rather than showing an alkene carbocation, fictitious vinyl cation or catalytic surface cycle. Summary wording “across mechanisms” counts pathway types and should not be confused with implemented elementary mechanism visualization.

## 12. Public UI and calculator confidence

Observed in a temporary local browser tab, subsequently closed:

- Complete propyne/H2 with Pd/Pt shows C3H8 and two H2, labeled conditional net outcome. Switching to Lindlar clears the result, blocks the alkane endpoint and permits the C3H6 partial option.
- Propyne/Br2 with missing medium retains unsigned conditional 2D and disables 3D/Compare. Entering the dry-medium assumption clears stale state and permits the qualified Br2 graph.
- Propyne/HBr with missing medium/temperature explicitly lists both missing keys, preserves 2D, and disables 3D. Its prose emphasizes ambient policy but does not list all corrective steps; the card and calculator labels supply the complete missing list.
- Entering dry/ambient/two equivalents gives C3H6Br2 with two actual HBr molecules. Br10 highlights in reagent, product and linked 3D. No complete mechanism panel appears.
- At 0.040065 g propyne plus 0.080912 g HBr (1 mmol each), HBr is limiting for the two-HX equation: **0.0005 mol / 0.1009445 g** theoretical product (display 0.10094 g); 0.0005 mol propyne remains.
- Calculators show complete conversion as an assumption, warn against summing alternatives, and explicitly distinguish theoretical amounts from yields/protocols. Conditional 2D options can still be calculated with those warnings. Existing unit/target/limiting fixtures pass; no arithmetic change was needed.

![Audit evidence: missing conditions, conditional 2D and theoretical calculator warnings](reaction-lab-phase4e-confidence-review.png)

Usability concerns: raw “solvent/temperature” keys rather than control-specific instructions; some unvalidated reagent modes have no available selector combination that enables 3D; equivalent-site metadata is less discoverable in the UI; changing settings clears selection and calculated amounts, requiring reselection. Clearing is safe and intentional, but can make exploration repetitive. None justifies bypassing validation.

## 13. Verification results

| Verification | Result |
| --- | --- |
| Python regression | 1,416 passed; 0 failures |
| JavaScript regression | 1,413 passed; 0 failures/skips |
| Total existing regression | **2,829 passed unchanged** |
| Authenticated alkyne match/diagram/run test methods | 26 passed, included above |
| Fixed benchmark | 347 rows; exactly identical to Phase 4D; known A304 flag retained |
| Existing partial diagnostic | 52 cases / 33 options; no failures; exactly unchanged |
| Existing complete diagnostic | 52 cases / 32 options; no failures; exactly unchanged |
| Existing X2 diagnostic | 177 cases / 85 options; no failures; exactly unchanged |
| Existing HX diagnostic | 291 cases / 153 options; no failures; exactly unchanged |
| Additional temporary cross-probe | 648 cases / 416 options; no contract failures; 150 3D and 266 correct blocks |
| Additional condition-schema HTTP probes | 4 unexpected-key inputs incorrectly accepted for 3D; recognized-radical control correctly blocked; confirmed confidence defect |
| Separate condition-aware replays | 62 positive cases; permissions and generated structures checked separately from frozen scoring |
| TypeScript | Passed |
| Production build | Passed; existing large Builder/vendor chunk warning remains |
| Whitespace / protected-file hashes | Passed; all 317 original inventoried files unchanged |

No unexpected regression failures appeared. The separate condition-schema probes exposed a real confidence-validation defect that the current passing suite does not cover; it must not be hidden by the green regression result. The temporary net-contract probe initially needed harness-only corrections: mapped graph atom order cannot be reconstructed by assigning diagram indices to canonical unmapped product SMILES, and an unspecified stage uses the actual first-stage metadata, not the probe's requested-mode label. Those corrections were confined to the temporary diagnostic; final contract checks passed. No engine/test change was made to obtain a pass.

## 14. Five highest-priority improvements

Ranked by chemical-confidence impact and implementation risk; **proposed, not implemented**.

| Rank | Proposed improvement | Classification | Evidence / acceptance target | Risk and scope |
| ---: | --- | --- | --- | --- |
| 1 | Reject or explicitly block unrecognized condition fields at the public boundary | **Condition/confidence correction** | Four authenticated examples silently discard peroxide/light information and still run; add future regressions for unknown keys, recognized radical control and stale confidence | Medium shared-API compatibility risk; reject rather than invent support for new settings/mechanisms; preserve documented inputs |
| 2 | Make the Lindlar multi-alkyne confidence decision explicit and consistent with the other families | **Condition/confidence correction** | Equivalent and distinct diynes currently permit partial-only 3D despite unresolved mono-conversion; retain all net options/maps and disclaimers | Low–medium code risk; existing tests encode current permission and any justified expectation change must be disclosed; no new selectivity model |
| 3 | Review the conformer/condition contract, evidence and actionable explanations within the current layout | **Condition/confidence correction**; supporting **explanation or usability correction** | Explain differing missing-medium/ambient policies, dry assumption, unsupported HCl/two-HI protocols and unavailable versus fixable settings; strengthen protocol-appropriate citations and pathway/site/alias explanations | Medium policy/low wording risk; preserve capture, radical, catalyst and stereo safeguards; do not simply unlock every gate or claim “dry” certifies a solvent |
| 4 | Add a versioned benchmark erratum and separate diagnostic fields without rewriting the frozen result | **Explanation or usability correction** | Independently correct A304 in a separately authorized oracle; distinguish 2D success, 3D policy block and real generation error; retain historical frozen score and all 347 IDs | Low chemistry risk; metric compatibility requires explicit versioning and authorization |
| 5 | Validate a narrow phenylacetylene Lindlar expansion before broader spectator permissions | **Structural coverage expansion** | Primary procedure already documents the exact case; add independent product, catalyst, stereo/mapping and competing-group controls | Medium chemistry risk; defer until confidence fixes; not permission for all aryl/conjugated substrates or other pathways |

No wrong mapped-product graph requiring a **critical production chemistry correction** was established under the documented inputs. The confirmed condition-input bug is nevertheless important and should be fixed before expanding coverage. Full surface, halonium or reagent-specific electrophilic mechanisms remain **future mechanism development**, lower priority than confidence correctness; they should not be fabricated from net edits.

## 15. Recommended stopping point

**Yes: plan a small Phase 4F first**, focused on priorities 1–4 after agreeing the intended confidence policy. Keep the frozen 347 inputs unchanged; any corrected oracle must be separately versioned/authorized. Do not bundle structural coverage expansion or new mechanism families into that fix phase. Then consider the narrow, independently validated coverage work.

Phase 4E ends with this report. No fixes, relaxed restrictions, new tests/reactions, curated examples or next-phase work were started.

### Code evidence reviewed

- [Condition gates](</Users/rc/Documents/Capstone project/server/reaction_conditions.py:194>) and [confidence/presentation contract](</Users/rc/Documents/Capstone project/server/addition_contract.py:20>).
- [Condition-input normalization that ignores extra keys](</Users/rc/Documents/Capstone project/server/chemistry_server.py:427>) and [authenticated public route forwarding](</Users/rc/Documents/Capstone project/server/production_app.py:357>).
- [Partial scope/geometry](</Users/rc/Documents/Capstone project/server/alkyne_partial_hydrogenation_rule.py:47>), [complete scope](</Users/rc/Documents/Capstone project/server/alkyne_complete_hydrogenation_rule.py:40>), [X2 scope/geometry](</Users/rc/Documents/Capstone project/server/alkyne_halogenation_rule.py:39>) and [HX scope/orientations](</Users/rc/Documents/Capstone project/server/alkyne_hydrohalogenation_rule.py:52>).
- [Shared strict compatibility/edit checks](</Users/rc/Documents/Capstone project/server/reaction_compatibility.py:81>), [public generation gates](</Users/rc/Documents/Capstone project/server/chemistry_server.py:704>), [selection/confidence UI](</Users/rc/Documents/Capstone project/src/reaction-lab.ts:730>) and [calculator warnings](</Users/rc/Documents/Capstone project/src/reaction-calculator-panel.ts:78>).
- [Frozen case construction](</Users/rc/Documents/Capstone project/scripts/audit_reaction_lab.py:233>) and [workflow scoring/catch behavior](</Users/rc/Documents/Capstone project/scripts/audit_reaction_lab.py:289>).
