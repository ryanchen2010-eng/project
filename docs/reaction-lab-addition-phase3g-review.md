# Phase 3G — Addition-family consistency review

Reviewed 2026-10-15. **Read-only audit; no fixes implemented.** Production source, existing tests/fixtures, benchmark, layouts, Calculators and curated examples are unchanged. The only new project files are this report, its results JSON and a verification screenshot. Builds generated normal ignored artifacts. No commit, push, deployment or publication occurred.

## 1. Executive summary

The six pathways produce consistent, bounded **net transformations** in the cases checked. No incorrect product connectivity, explicit-species conservation, selected-site mapping or tested stereochemical outcome was found. That is evidence for the tested scope, not validation of arbitrary substrates or experimental selectivity.

They are **not fully consistent in how confidence is communicated**. The main issues are condition/rendering policy differences, an unassessed solvent dimension in dihydroxylation, conditional calculator assumptions that are easy to miss, inaccurate generic mechanism/stereochemistry text, and hydration equivalent-site duplication. These deserve a small consistency-fix phase before expanding chemistry. They do not justify removing the existing chemistry safeguards.

**All 1,704 existing tests pass**, as do TypeScript, production build and whitespace checks. All **347 fixed benchmark rows exactly match the saved Phase 3F results**, including products, options, notes and workflow outcomes. The strict dihydroxylation score remains **0/11**; the separate confirmed-workup replay remains **9/11**. Neither result is replaced by the other.

Evidence: [machine-readable results, preservation hashes and diagnostic source](</Users/rc/Documents/Capstone project/docs/reaction-lab-addition-phase3g-results.json>). The extra diagnostic suite exercised 51 substrates across six pathways, 72 condition contexts and 18 oxygen-substituent/HX contexts: **396 public matching calls, 287 product diagrams, 287 3D runs and 3,958 invariant checks, with zero diagnostic failures**. All 287 generated models reported convergence. These are diagnostic checks, not new permanent regression tests.

## 2. Six-pathway consistency table

Scores below are positive-case, full-workflow scores from the unchanged benchmark; negative controls are not in these denominators.

| Pathway | Defined reagent/model | Supported stereo representation | Important scope/condition boundary | Fixed score |
| --- | --- | --- | --- | ---: |
| Hydration | Water consumed; acid catalyst regenerated | Selected E/Z consumed; distant configuration retained; new centers unsigned | Screened carbocation orientation; rearrangement/capture risks rejected; acid activation required | 10/14, 71.4% |
| Hydrohalogenation | Actual HCl/HBr/HI consumed, ionic addition | Same distant-retention safeguards; new centers unsigned | HX-specific oxygen compatibility; no radical/peroxide model; conditional 3D permitted with unspecified medium | 12/16, 75.0% |
| Bromination | Actual Br₂; neutral non-nucleophilic net model | Validated anti face alternatives; meso deduplication; small-ring trans Br/Br | Water/alcohol capture, nearby nucleophiles/dienes and internal aryl stereo scrambling excluded | 9/14, 64.3% |
| Chlorination | Actual Cl₂; independently screened model | Validated anti alternatives and cyclic relationships | More conservative oxygen-substituent scope than Br₂; no radical or chlorohydrin model | 9/14, 64.3% |
| Epoxidation | Actual screened peroxyacid → epoxide + actual acid coproduct | Same-face transfer retains source substituent relationships; configured face alternatives | Isolated 5–7-membered carbocycles; screened oxygen groups; compatible medium required | 9/11, 81.8% |
| Syn dihydroxylation | Os selector + actual H₂O₂; formal net bookkeeping | Syn alternatives; cis small-ring diols; distant retention | Explicit aqueous-release assumption required for 3D; catalyst cycle/workup species not mapped | **0/11, 0% strict** |

Only epoxidation has an implemented mapped concerted mechanism among these six. A correct product graph does not establish a complete mechanism.

## 3. Confirmed inconsistencies and their classifications

### A. Conditional confidence and rendering permissions — policy/contract inconsistency

With propene/HBr and no conditions, the API returns `status: missing`, `canRun: true`, and a clear note assuming a non-capturing ionic medium. The UI generates 3D/Compare. Br₂, Cl₂ and peracid options with unspecified medium instead block 3D; diol options without release confirmation also block it. All retain conditional 2D.

This does **not prove an incorrect HX product**: a conditional representative structure is legitimate. The inconsistency is that `canRun` simultaneously encodes rendering permission and the completeness of different chemistry models. API consumers cannot infer comparable confidence from it alone. A related ambiguity is top-level `supportState: Supported` whenever any structural option exists, even if every option is condition-blocked. Per-option assessment is more accurate than that broad flag. Evidence: [matching response](</Users/rc/Documents/Capstone project/server/chemistry_server.py:594>), [condition assessment](</Users/rc/Documents/Capstone project/server/reaction_conditions.py>).

### B. Diol solvent dimension is not assessed — validation/confidence gap

Confirmed Os activation and aqueous release produce `model-match` for dry, aqueous, ethanolic and generic aprotic media alike. `assess_dihydroxylation_conditions` inspects catalyst, workup and temperature, but not solvent. No solvent factor explains that omission. This is not proof that all these cases give wrong diols: a dry reaction followed by aqueous release is not inherently contradictory. It is a gap between the broad top-level label and the actual dimensions validated. Solvent-specific compatibility must remain unknown unless independently supported. [Condition function](</Users/rc/Documents/Capstone project/server/reaction_conditions.py:168>).

### C. Generic mechanism/stereo note is wrong for hydration/HX — confirmed explanation defect

Their diagram footer says the view omits stereochemistry and directs users to separate mapped mechanism steps. Distant configured stereo is actually retained, and neither pathway implements those steps. Their detailed information panels are more accurate. The generic fallback should not contradict them. [Footer](</Users/rc/Documents/Capstone project/server/reaction_diagrams.py:431>).

### D. Labels/types overstate or misclassify options — confirmed interface/contract defects

- Generic frontend `missing` text is “Comparison conditions incomplete,” including missing genuinely required diol release/activation, not just a comparison example. [Label mapping](</Users/rc/Documents/Capstone project/src/reaction-conditions.ts:14>).
- The server emits reasoning label `Model conditions match` for diol options, but the TypeScript `PathwayReasoning.label` union omits it. Runtime rendering works; passing TypeScript does not validate this externally cast JSON contract. [Type](</Users/rc/Documents/Capstone project/src/pathway-insights.ts:4>).
- Generic status/comparison text calls site/face stereoisomers separate “pathways” that “may compete.” Diol has a better custom site/face label, but the generic comparison table still does not distinguish mechanism, site, orientation and face. It explicitly disclaims probabilities, so no numerical ratio bug was found. [Status](</Users/rc/Documents/Capstone project/src/reaction-lab.ts:751>), [comparison](</Users/rc/Documents/Capstone project/src/pathway-insights.ts:56>).

### E. Hydration equivalent-site duplication — confirmed deduplication inconsistency

For symmetric 1,11-dodecadiene (`C=CCCCCCCCCC=C`), hydration returns two different site IDs with identical isomeric product `C=CCCCCCCCCC(C)O`, without equivalence aliases. HX groups the symmetry-related sites into one product option with both mapped aliases; Br/Cl/epoxide/diol group equivalent site/face representations similarly. Hydration's key includes the chosen bond identity, so symmetry-related sites never merge. Products and maps are valid; the duplicate choice/count is the defect. It should eventually group equivalents without erasing site provenance. [Deduplication branches](</Users/rc/Documents/Capstone project/server/reaction_engine.py:508>).

No confirmed incorrect-chemistry bug was found in the tested products. Findings A/B are confidence/validation gaps, C/D are explanation/contracts, and E is redundant option handling—not evidence that all pathways should accept identical molecules.

## 4. Scientifically justified structural differences

The shared architecture identifies the selected bond, applies pathway-specific functional-group policies and validates exact edits. It does not confer universal spectator permissions.

- **Adjacent branching:** hydration/HX reject screened hydride/alkyl-shift risks; Br/Cl and concerted oxygen transfer need not inherit a free-carbocation rearrangement rule. This distinction is appropriate. Carbocation rearrangement is a separate mechanistic concern. [OpenStax](https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements).
- **Aromatic adjacency:** terminal styrene/α-methylstyrene fit Br/Cl's one-new-center scope. Internal aryl alkenes are excluded where benzylic-ion stereo scrambling is unvalidated. Epoxidation/diol accept screened internal aryl substrates under their different mechanisms. These are validated-model differences, not claims that internal aryl alkenes cannot be halogenated.
- **Oxygen groups:** hydration allows screened remote ordinary OH/ether; HBr/HI reject them for unresolved additional substitution/cleavage. HCl permits a narrower ambient, no-added-activation spectator model. Cl₂ rejects even remote OH/ethers, whereas Br₂ screens and permits sufficiently distant ordinary ones. The Cl₂ exclusion is conservative unvalidated competing chemistry, not a demonstrated universal chemical prohibition.
- **Distance cutoffs differ:** cation hydration/HX screen possible short capture rings; Br₂ screens paths of up to eight atoms for halonium/oxygen capture; peracid screens nearby acid-sensitive/opening environments; diol uses its own coordination/oxidative-cyclization limits. These graph-distance bounds are conservative screens, not measured kinetic boundaries.
- **Rings:** hydration/HX and Br/Cl accept screened isolated 5–8-membered carbocycles. Epoxide/diol have validated geometry only for 5–7-membered carbocycles. Wider ring support is a future validation task, not an inconsistency requiring immediate relaxation.

## 5. Structural gaps and rejection quality

All six remain bounded neutral, closed-shell substrate models with conservative C/H/O compatibility, unsupported isotope/query/enhanced-stereo environments, and an 80-explicit-atom product limit. Actual reagents have their own element validation. The substrate filter does not reject the halogen reagent merely for containing halogen.

Shared unsupported categories include conjugated/cumulated/direct-heteroatom alkenes, exocyclic/fused/bridged or unvalidated ring sites, adjacent specified centers without a facial model, and competing carbonyl/peroxide/amine/other unscreened groups. Remote organic fluorides also fail this bounded scope despite some potentially compatible real reactions. These are software/model limits, not chemical impossibility.

Hydration/HX's treatment of phenyl groups remote from the selected alkene is narrower than Br/Cl/oxygen-transfer aromatic spectator policies. This is a candidate unnecessary restriction for a later independently tested increment, not enough evidence to enable it now. Near-site direction, oxidation or cyclization exclusions likewise need reaction-specific evidence, not blanket spectator acceptance.

Most rejection messages correctly identify the unscreened group, shift/capture/ring risk or size limit. NMO fails earlier in the shared neutral-input scope with a generic message, obscuring the more helpful “alternative co-oxidant not implemented” explanation. That is an explanation limitation, not a reason to enable NMO here.

## 6. Independent stereochemistry findings

The audit checked configured graph outcomes separately from conformer generation. For E/Z-2-butene, independent expectations were:

| Source | Br₂/Cl₂ anti addition | Peracid epoxide | Os/H₂O₂ syn diol |
| --- | --- | --- | --- |
| E | One meso R/S structure | R,R and S,S alternatives | R,R and S,S alternatives |
| Z | R,R and S,S alternatives | One meso R/S structure | One meso R/S structure |

These assignments apply to these symmetric examples, not every E/Z alkene. Unequal substituents can make R,S and S,R distinct enantiomers; R/S letters alone do not define syn/anti or meso symmetry. Halonium anti addition and cyclic relationships are consistent with the [halogenation reference](https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2). Concerted epoxide transfer and osmium syn hydroxylation have different geometrical foundations. [Oxidation reference](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation).

Small 5–7-membered cyclic products were checked against the independent existing trans halide and cis epoxide/diol expectations. Unsigned cyclooctene remains unsigned under Br/Cl; specified E/Z cyclooctene has source-dependent alternatives without a generic “trans product” claim. Epoxide/diol reject that ring size. Unknown internal geometry remains locally unassigned; terminal one-center face alternatives are not invented E/Z.

Hydration/HX consume the selected alkene geometry and leave new tetrahedral centers unassigned. All six preserve distant physical parity. The independent substrate `C=CCC[C@H](C)CCC(C)(C)C` changes a distant CIP descriptor **S→R without inversion**, because priorities change. This worked across all six. Each configured generated 3D center was reassigned from its coordinates with atom-map labels cleared and compared to the independently specified graph identity. Coordinates verify representation; they do not choose the reaction outcome.

Missing functionality remains: no facial preference, exact mixture composition, neighboring-center induction, general atropisomerism or arbitrary ring geometry. With a pre-existing stereocenter, opposite local faces may be diastereomers, not an enantiomer pair. No equal ratios are established. An optimized unsigned conformer necessarily depicts one spatial arrangement; it must not be interpreted as an assigned stereochemical product.

## 7. Multiple sites and 1,7-octadiene

| Pathway | Current 1,7-octadiene result | Classification |
| --- | --- | --- |
| Hydration | Rejected; possible six-membered intramolecular carbon capture after protonation | Specific carbocation competition concern; conservative net-model limit |
| HX | Rejected for analogous unresolved cation/π capture | Appropriate pathway-specific caution |
| Br₂/Cl₂ | Rejected for nearby π capture/cyclization of halonium chemistry | Conservative screen; not a claim of a guaranteed cyclic product |
| Peracid | Independent one-site epoxidation alternatives allowed | Concerted oxygen transfer does not inherit the free-cation blanket restriction |
| Os/H₂O₂ | One-site net diol alternatives allowed with explicit release assumption | Different separation threshold; nearer 1,5-dienes remain excluded |

No universal one-site experimental selectivity follows from the allowed cases. Exact cutoff adequacy remains a future chemical-validation question; this review does not prove a particular competing pathway dominates.

For epoxide/diol, two displayed 1,7-octadiene options are **two configured face products**, not proof of two independent sites. Their `equivalentSiteFaces` record both symmetry-related C=C map pairs. Farther unequal dienes retain independent non-equivalent sites. Unselected double-bond connectivity and existing E/Z are preserved by validation and regression tests. Chirality-aware whole-substrate equivalence prevents false merging of genuinely different environments. Hydration is the exception described in finding E.

## 8. Mechanisms, mapping and explicit-species accounting

The net inventory passed independent map uniqueness, element/charge conservation, molar-mass balance, coproduct count, reagent-origin and 2D→3D atom-index checks. No atom is silently invented to repair a product.

- **Hydration:** one actual water supplies balanced net H/OH; acid is catalytic, excluded from consumed arithmetic. Net H maps do not model experimental proton exchange.
- **HX:** H and the correct halogen come from the chosen actual HX. Br₂/Cl₂ cannot substitute by formula/name. HX is consumed, not a separate catalyst.
- **Br₂/Cl₂:** X–X cleavage, two C–X formations and selected C=C reduction are mapped. No full halonium mechanism is returned or validated.
- **Epoxidation:** one formal concerted step, four electron-pair moves, no invented stable intermediate. Terminal peracid O enters the epoxide. O–O and terminal O–H break; two C–O bonds and the coproduct O–H form; acyl C–O bond orders exchange in the formal cyclic electron flow. The original carbonyl O receives the proton in this mapped representation, and all remaining actual reagent atoms are accounted for in its acid coproduct. Both atom inventory and electron source/destination bonds were checked. There are no calculated activation barriers or experimental rates.
- **Diol:** H₂O₂ O/H maps balance the **formal net** equation, not elementary catalyst oxygen provenance. Osmium oxidation states, cyclic osmate, release species, catalyst regeneration and proton exchange are absent. `mechanism: null` is honest; no complete osmium cycle can be inferred from two explicit reactants.

Existing diagram controls/highlights and main-product links remain intact. The 3D view displays the main product, not every coproduct/catalyst; the 2D equation accounts for represented coproducts. Net validity must not be relabeled as full mechanistic validation.

## 9. Conditions and workup consistency

Acid hydration requires acid activation, not merely a reference-example match. The water reactant can establish the bounded water-capture assumption with otherwise unspecified medium. HX has distinct ionic reagent and oxygen-retention conditions. Br/Cl/peracid require a defined compatible model medium; aqueous/alcohol capture, unvalidated generic aprotic media, heat and additional activation are not automatically equivalent. Radical HX/halogen/peracid settings produce no ionic-addition option. None of these tests mislabeled a mere preset mismatch as experimentally “unfavorable.”

The selectors are broad model choices: “Dry / no water” alone does not prove non-nucleophilicity or complete solvent compatibility. Condition notes acknowledge this. `model-match` does not establish conversion, isolation, speed, safety or a unique experimental product.

The diol release requirement is **defensible as an explicit reporting assumption**: a free product should not be asserted as completed if metal-bound/release chemistry is unresolved. It is not a universally demonstrated extra workup reaction for every catalytic Os/H₂O₂ process. Catalytic cycles can release product in an aqueous reaction; a stoichiometric osmate-cleavage protocol cannot simply be imposed on all catalytic conditions. The [OpenStax discussion](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation) distinguishes those roles. The [Organic Syntheses discussion](https://www.orgsyn.org/demo.aspx?prep=CV6P0342) documents catalytic H₂O₂ chemistry and overoxidation concerns, but its displayed procedure uses NMO; it does not independently validate every H₂O₂ substrate or this checkbox as a complete workup.

Balanced `alkene + H₂O₂ → diol` does not require inventing another consumed O/H source in the explicit net equation. The selector confirms an assumption, not actual measured completion. Missing release should prevent an **unqualified** completed-product claim. Whether it should block a clearly conditional 3D structure is a product policy decision: 3D establishes completion no more than 2D does. Current blocking is conservative, but inconsistent with qualified HX rendering and potentially restrictive. No gate was relaxed in this review.

## 10. Strict benchmark, separate replay and exact counts

| Diol assessment | Fully supported positive cases | Other outcomes |
| --- | ---: | --- |
| Original pre-3F baseline | 4/11, 36.4% | Original model, as recorded in Phase 3F |
| Current **unchanged strict benchmark** | **0/11, 0%** | 10 partial positives; 1 unsupported positive; 1 correctly rejected control |
| Separate replay, only `workup: aqueous-release` added | **9/11, 81.8%** | 1 partial cyclic positive; 1 unsupported NMO positive; 1 correctly rejected control |

The original fully supported cases lose that status because fixed benchmark inputs do not contain the newly required release confirmation. Ten positives now structurally match, but all ten fail the strict unconditional run gate. Their conditional 2D diagrams are available. The audit's combined try/except overwrites `preview` with `failed` after a later run error; that field therefore does **not** demonstrate failure of the independent 2D endpoint. This diagnostic/scoring limitation is documented, not edited.

The replay changes only that one condition and does not alter fixed scoring. All ten available positive rows generate converged 3D. Cycloheptene stays partial because the fixed audit lacks its independently expected stereoproduct, even though separate cis/R/S checks pass. NMO remains unsupported. The replay is not evidence of a complete osmium mechanism or experimental protocol.

**The counting discrepancy has an exact explanation:** “11 dihydroxylation cases” referred to the **11 positive expectations**, not the entire category. There are **12 dihydroxylation rows**: A242–A251 (ten positives), A252 (negative saturated-alcohol control), and A255 (positive NMO probe). Thus **347 − 12 = 335 unrelated rows**. The 24 pathway categories are disjoint; variant tables are subsets, not extra rows. Across all pathways, 309 positives + 38 negative controls = 347.

Current exclusive statuses: **179 full + 25 partial + 105 unsupported + 38 correctly rejected = 347**, with zero incorrect-result rows. All 347 rows are unchanged from Phase 3F; there is no new regression in this review. The original benchmark hash remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 11. Public interface, calculators and verification

Public service match/diagram/run functions were exercised across the diagnostic matrix; the existing authenticated HTTP-route tests also pass. Condition probes produced 68 conditional/model diagrams, with **39 blocked and 29 allowed runs**, all agreeing with their API `canRun` flag. Wrong-reagent and malformed-input controls remain covered by existing tests. The browser independently confirmed propene/HBr option selection, conditional 2D and generated linked 3D with unspecified conditions. The temporary tab was closed; no saved user examples or settings were changed.

Calculator arithmetic remains correct for the **selected balanced net equation**, including actual HX/X₂/peracid/H₂O₂ molar masses, theoretical/required amounts, limiting reagent and represented coproduct mass. Existing calculator fixtures all pass. Epoxidation uses the full actual peracid, not an oxygen-only substitute. Catalyst/solvent quantities are not calculated.

Conditional stoichiometry is mathematically legitimate if clearly hypothetical; it should not certify an eligible experimental reaction. Reaction Lab displays a condition badge and a theoretical-only caption, but pathway-specific workup/provenance caveats are inside collapsed calculator assumptions. The standalone catalog validates balanced equations without carrying the full condition assessment. This is a **visibility/context gap**, not a found arithmetic error. [Calculator assumption placement](</Users/rc/Documents/Capstone project/src/reaction-calculator-panel.ts:65>).

| Verification | Result |
| --- | --- |
| Python `unittest discover -s tests -p 'test_*.py'` | **884 passed**, no failures/skips |
| Node `--test tests/*.test.mjs` | **820 passed**, no failures/skips; includes calculator fixtures |
| Total existing tests | **1,704 passed; none changed or added** |
| Original `scripts/audit_reaction_lab.py --json` | 347 rows; exactly unchanged from Phase 3F |
| Existing four-mechanism public diagnostic | 48 substrates, 192 matches, 48 condition checks, 5 reagent controls, 125 verified options; zero failures |
| Temporary addition diagnostics | 396 matches, 287 diagram/run pairs, 3,958 checks; zero failures |
| TypeScript `tsc --noEmit` | Pass |
| Vite production build | Pass; pre-existing large Builder chunk/third-party directive warnings remain |
| `git diff --check` and new-artifact whitespace/JSON checks | Pass |
| Preservation | All 157 snapshotted source/test/fixture/script/HTML hashes unchanged; benchmark hash unchanged |

Runtime: project `.venv` Python and bundled Node at `/Users/rc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`. Diagnostic source and exact observations are preserved in the results JSON. No benchmark expectation was promoted using production-generated stereochemical tags alone.

## 12. Five highest-priority improvements

Ranked by correctness/confidence risk first, then scope. These are recommendations, not completed changes.

1. **Separate structural eligibility, required assumptions, evaluated conditions and rendering permission.** Address broad `Supported`/`model-match` flags, the unassessed diol solvent dimension and qualified HX versus blocked conditional 3D. Scope: small-to-medium API/condition/UI contract change with cross-pathway tests. Do not blindly equalize chemical permissions or remove workup gates.
2. **Keep conditional calculation context visible and transferable.** Show a concise conditional-net warning and carry relevant assumptions into standalone reaction calculations. Scope: small data/presentation change; unchanged arithmetic. Risk: theoretical output otherwise looks more experimentally authoritative than its model supports.
3. **Correct mechanism/stereo and condition explanations; align types with actual API labels.** Fix hydration/HX's footer, required-versus-comparison missing text, and `Model conditions match` union coverage. Scope: small, independently testable changes with no chemistry expansion.
4. **Normalize equivalent-site/face grouping and option terminology.** Add hydration aliases and distinguish product, regioisomer, face and reaction-site counts from mechanism counts. Scope: small-to-medium; must preserve mapped identities and chirality-aware equivalence. Do not merge distinct diastereomeric environments.
5. **Strengthen a separate diagnostic layer without rewriting the fixed benchmark.** Separate 2D failure from run gating, verify unique sites through aliases rather than option counts, independently specify cyclic expected stereo, and enforce unknown-stereo/net-provenance contracts across all six. Scope: medium verification work; existing benchmark stays comparable. Unknown geometry and missing mechanisms must remain explicit until separately validated.

## 13. Recommendation and stopping point

**Yes: complete one small addition-family consistency-fix phase before adding more chemistry.** Focus on the five items above, not automatic expansion of substrate scope. No evidence here supports removing Cl₂ oxygen, diene-capture, rearrangement or directed-stereo restrictions merely to raise coverage.

Later enhancements—complete hydration/HX/halonium mechanisms, catalyst-specific osmium cycling, additional ring sizes and broader spectator compatibility—need separately scoped chemical validation. They are missing capabilities, not findings that the current net products are wrong.

**Phase 3G ends with this review. No fixes or subsequent reaction phase were started.**

![Audit verification: conditional HX option with linked 2D/3D views](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3g-review.png>)
