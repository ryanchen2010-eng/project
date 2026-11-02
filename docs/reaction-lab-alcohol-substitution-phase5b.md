# Phase 5B — Alcohol substitution

Completed 2026-10-16. Scope: existing HX/alcohol substitution only. No new reaction family, activating reagent mode, page layout, Calculator formula or curated example was introduced. Phase 5B stops here.

These are bounded theoretical net structures. Finite regression tests and benchmark labels do not establish universal chemical correctness, experimental selectivity or a complete laboratory protocol.

## 1. Original structural coverage

Before modifying production code, the existing matcher, net edit, reagent classification, product validation, stereochemistry gate, conditions, diagrams and calculations were inspected. A complete pre-change 347-case audit was captured.

The old rule accepted neutral saturated acyclic C/H/O mono-alcohols without specified stereocenters. It excluded rings, additional oxygen groups, benzylic/allylic systems and some adjacent branching. Actual HBr/HI were recognized; HCl was limited to tertiary alcohols. SOCl2/PBr3 were not implemented. This was a simplified net replacement, not a complete SN1/SN2 activation mechanism. Temperature was a reference comparison, not an HX-specific 3D-confidence gate.

The frozen audit has **13 alcohol-substitution rows: 11 positive chemical cases and two negative controls**. Baseline positive structural matching was **5/11 (45.5%)**.

## 2. Original fully supported coverage

The unchanged scorer reported **5/11 fully supported (45.5%)**, six unsupported positive cases, and two correctly rejected controls. No baseline percentage was inferred from preset examples.

The frozen parent SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 3. Updated structural and fully supported coverage

Structural matching is now **7/11 (63.6%)**. Strict full coverage is **3/11 (27.3%)**, with four partial positives, four unsupported positives and both controls correctly rejected.

The lower strict score is intentional confidence correction, not lost product connectivity or an inflated denominator:

| Case | Frozen input | Before → after | Current result |
| --- | --- | --- | --- |
| A216 | Long primary alcohol + HBr, heated | Full → full | Qualified mapped net product and 3D remain. |
| A217 | Secondary internal alcohol + HBr, heated | Full → partial | Same haloalkane connectivity; secondary mechanism/stereo and heated competition unresolved, 2D only. |
| A218 | Branched tertiary alcohol + HBr, heated | Full → partial | Same connectivity; heated elimination competition is not validated as a unique substitution outcome. |
| A219 | Cyclic alcohol | Unsupported → same | No new ring-bound mechanism permissions. |
| A220 | `COCCCCO` | Unsupported → same | Possible five-membered oxygen capture; HX ether cleavage also matters. |
| A221 | `OCCCCO` | Unsupported → same | Possible five-membered intramolecular closure. |
| A222 | Specified reacting secondary center | Unsupported → partial | Correct mapped constitutional net product; local configuration remains unsigned. |
| A223 | Benzyl alcohol | Unsupported → partial | Benzyl-halide net connectivity available; mechanism/formulation confidence remains conditional. |
| A224 | Ether without an alcohol | Correct rejection → same | No invented alcohol site or new ether-cleavage family. |
| A227 | Primary alcohol + HI, heated | Full → full | Actual iodine provenance and HX consumption retained. |
| A228 | Tertiary alcohol + HCl, ambient | Full → full | Existing bounded tertiary-HCl scope retained. |
| A229 | PBr3 activation | Unsupported → same | Precise explanation; still no new reagent mode. |
| A230 | Alcohol + hydroxide | Correct rejection → same | No displacement of unactivated OH. |

A218 can obtain a qualified net-model conformer with the existing ambient setting; that is not a validated experimental protocol. A217/A222/A223 cannot be made fully confident merely by picking another dropdown value: their mechanism/stereochemical/formulation gaps remain. The frozen inputs and expectations were not altered.

The frozen scorer combines diagram and run errors: policy-blocked 3D can appear as `preview: failed`. Separate API checks confirm that these cases retain their explicitly conditional 2D diagrams.

## 4. Newly supported substrates

The new `server/alcohol_substitution_rule.py` supplies generalized site/group assessment, exact mapped edit contracts, stereo validation and condition confidence. Molecular names, formulas and fixture labels do not grant production eligibility.

New coverage includes distant specified stereocenters, specified reacting centers with explicitly unresolved net products, primary benzylic net connectivity, screened sufficiently separated ether groups and independently selectable alcohol groups. Simple long-chain alcohols already worked; they are regression-tested, not falsely counted as newly supported chemistry.

Independent positive fixtures include both remote enantiomers, alkyl-substituted benzyl alcohol, `COCCCCCCCCO`, `OCCCCCCCCO` and a primary/secondary diol with distinct selectable products. Extra-oxygen and benzylic cases are conditional 2D, not claimed experimental spectator inertness or selective conversion.

The separate development diagnostic covers **45 cases: 21 positives and 24 negatives**. All 21 positive product sets match independent literal expectations; all 24 controls reject substitution. There are 22 canonical positive net options: **nine verified conditional net-model 3D products and 13 intentionally blocked 3D options**. These figures are not substitutes for the frozen benchmark or independently reviewed experimental conditions.

## 5. Remaining unsupported chemistry

Still excluded: cyclic/ring-bound substitution; fused/complex aromatic environments; secondary/tertiary benzylic and allylic/propargylic capture; neighboring-group participation; short oxygen closures; shift-prone or highly hindered adjacent branching; acid-sensitive tertiary/benzylic/acetal ether environments; competing unsaturation/carbonyl/amine groups; unsupported elements/charge/isotopes; invalid stereo; and products beyond the existing 80-explicit-atom bound.

Mixed pi/alcohol inputs retain the existing HX-addition assessment and rejection behavior; this phase does not grant alcohol-substitution permission or change those unrelated pathway messages. Ordinary primary/secondary/benzylic HCl activation remains outside the supported tertiary-HCl model. Unsupported does not mean chemically impossible.

## 6. Reagent and activation validation

The selected reagent must be actual neutral HCl/HBr/HI with its hydrogen and halogen; identity, charges, connectivity and electronic state are checked. Bare halide, hydroxide, HF, salts without activation, SOCl2 and PBr3 are not silently substituted for HX.

The explanation requires OH protonation so that **water**, not unactivated hydroxide, can depart. Actual HX supplies acid activation and the entering halide. “None added” means no extra catalyst, not absence of the selected acid reagent. No ZnCl2, PBr3, SOCl2 or other new activation system is inferred from the generic catalyst selector.

## 7. SN1/SN2 mechanism correctness and limits

The pathway remains an honest **net transformation**, with null mechanism payloads and `mappedMechanism: unsupported`. No fabricated protonation arrows, charged intermediates or concerted bare-OH displacement was added.

Methyl/primary substrates have an activated-water SN2 rationale without an invented free primary carbocation. Screened tertiary substrates have an SN1-type rationale without a guaranteed ratio or rearranged cation. Secondary and benzylic SN1/SN2 partition is explicitly unresolved and 2D-only.

No new stereogenic-center SN2 inversion is claimed: the admitted methyl/ordinary-primary SN2-type centers are non-stereogenic in this non-isotopic model. A source-validated stereospecific secondary HX mode was **not** invented just to demonstrate inversion. The existing alkyl-halide SN2 inversion engine and tests are unchanged; they are not reused as permission for alcohol chemistry.

The primary literature cautions against a universal second-step mechanism for alcohol/HX reactions ([Gerrard, *Interaction of alcohols with hydrogen halides*, DOI 10.1002/jctb.5010050104](https://onlinelibrary.wiley.com/doi/abs/10.1002/jctb.5010050104)). This supports retaining uncertainty rather than declaring every secondary alcohol SN1 or SN2. Its accessible abstract does not independently validate every fixture or an experimental condition profile.

## 8. Stereochemistry safeguards

Only the exact selected reacting carbon may lose its configuration in an explicitly unsigned net product. Its atom identity, original neighbors, replacement oxygen/halogen and legitimate specified input are checked. It does not acquire a copied R/S letter, automatic R↔S flip, invented retention, or perfect 50:50 racemization.

All other mapped physical configurations and serialized bond relationships must remain valid. Tests include both reacting enantiomers, specified tertiary centers, invalid annotations and deliberately corrupted stereo/charge/maps/bonds. Remote `@`/`@@` products also pass independent coordinate-derived CIP checks after clearing carried stereo tags.

For `C[C@H](CCCCO)CCCCOC`, replacing the selected OH with Br changes the remote CIP label **R → S while retaining physical configuration**. Both a literal independent product specification and the physical map-based validator agree. This extra-ether case remains 2D-only; no conformer is used to manufacture certainty.

## 9. Atom mapping and coproduct conservation

The contract breaks C–O and H–X, forms C–X and O–H, and preserves every other bond. The incoming halogen is the actual reagent atom. Neutral net water contains the original alcohol oxygen, its original OH hydrogen and the HX hydrogen. Represented atoms, charge, valence, fragments and serialized map identities are checked.

This is formal net hydrogen provenance, not a claim about solution proton/isotope exchange. Both reactant orders and user-supplied original atom maps are tested. Equivalent alcohol-site choices are grouped in the UI while every legacy source reaction ID and map alias remains addressable; each alias is checked with its own water oxygen. Different constitutional products are not collapsed.

The calculator uses **1 ROH + 1 HX → 1 RX + 1 H2O**. HX remains a consumed input and can be limiting; it is not excluded as a catalyst. Independent literal formulas check alcohol, HX and product masses, amount/target conversions and zero-HX behavior. Amounts refer to pure-compound equivalents, not an assumed concentration or mass of aqueous HX solution.

## 10. Competing dehydration and other chemistry

The alcohol-dehydration rule was not edited. All ten dehydration benchmark rows remain exactly unchanged, including its catalyst accounting, confidence gates, stereo handling and two negative controls.

HX substitution explains competing dehydration, ether formation, capture and rearrangements without inventing competing product ratios. Heated tertiary cases are conditional 2D; secondary/benzylic mechanisms remain unresolved even without heating. Near intramolecular oxygen capture is rejected, and screened more distant oxygen groups remain conditional rather than presumed inert.

Primary research directly demonstrates formulation-dependent ether cleavage with HBr ([Hart, Aldous and Harper, DOI 10.1039/C7OB01096F](https://pubs.rsc.org/en/content/articlelanding/2017/ob/c7ob01096f)). Its publisher-indexed abstract was accessible, but direct full-text access was denied. It is a reason not to assert universal ether stability, not approval of a new ionic-liquid or aqueous profile.

## 11. Condition-confidence behavior and frontend verification

Structural eligibility, actual HX identity/activation, required model settings, unevaluated factors and output permission are reported separately. Explicit temperature confirmation is required for 3D; methyl/primary use the existing heated net convention, tertiary the ambient convention. Neither certifies concentration, acid activity, solvent-specific mechanism or a complete protocol.

Additional activation, unvalidated dry/aprotic/alcoholic media, incompatible oxidation/workup and unknown fields such as peroxide block 3D. They retain clearly conditional 2D where the net structure is eligible. No preset difference is automatically called chemically unfavorable.

The existing frontend sends persistent alkyne-equivalent and finite-chain selectors even when hidden. Those recognized, chemically irrelevant fields are now explicitly recorded as **not applicable**, explained in the note, and never alter the 1:1 HX stoichiometry. Unsupported conditions are not silently discarded.

Browser checks used the unchanged ethanol example: mapped reagent bromine linked across 2D/3D; both reactants appeared in the calculator; 0.001 mol ethanol and 0.0005 mol HBr correctly gave an HBr-limited theoretical 0.0005 mol bromoethane (0.054483 g). Clearing temperature removed stale 3D/calculator results and kept a conditional 2D option. A secondary-alcohol example visibly stayed 2D-only with the mechanism limitation. No layout or example collection was changed. The temporary browser tab and locally started test preview were closed.

![Existing comparison view with reagent-derived bromine linked](reaction-lab-alcohol-substitution-phase5b-preview.png)

## 12. Newly restricted cases

The principal restrictions are confidence corrections, not removal of valid net product graphs:

- A217: unsigned secondary HX mechanism/stereochemistry no longer acquires an asserted product conformer.
- A218: heated tertiary HX no longer implies selective substitution rather than unresolved elimination competition.
- Missing temperature, unknown or incompatible condition inputs no longer permit 3D by default.
- Specified reacting stereochemistry is not silently retained; unresolved local products and screened additional oxygen chemistry remain 2D-only.

Choosing another condition can resolve a missing setting, but it cannot resolve a mechanism/stereo evidence gap. No unrestricted new acid, activator or spectator whitelist was added.

## 13. Tests added and regression results

**172 tests added: 72 Python + 100 JavaScript. Total: 3,227 passing tests (1,630 Python + 1,597 JavaScript).**

All 3,055 pre-existing test functions were retained. **One obsolete assertion was updated**, in `test_separate_aldehyde_oxidation_and_other_paths_do_not_inherit_policy`: it encoded the blanket HX stereo ban explicitly replaced by Phase 5B. It now verifies that the new HX-specific policy owns permission and returns conditional 2D without temperature, while preserving its unrelated oxidation, dehydration and water-reagent assertions. No other pre-existing test file was edited; there is no claim that every old assertion remained byte-identical.

New checks cover independently specified positive/negative structures, Br/I and allowed tertiary Cl, both reactant orders, every canonical site, equivalent source aliases, stereo consumption/retention, coordinate-derived CIP, edit corruption, input normalization, atom-size boundaries, conditions and non-applicable UI selectors, public authenticated match/diagram/run APIs, stale/forged requests, exact water maps, linked 2D/3D indices and theoretical arithmetic. The standalone 45-case diagnostic has no failures.

## 14. Unrelated benchmark regression and row reconciliation

All **334 non-substitution frozen rows are exactly unchanged** from the pre-phase run. Only eight substitution rows have changed observations/reasons. Overall frozen counts reconcile to 165 full, 53 partial, 90 unsupported, 38 correct rejections and one known incorrect-oracle result: **347 total**.

Phase 5A's separate count was also correct: **337 unrelated + eight positive dehydration cases + two negative dehydration controls = 347**. The remaining two are **A215 (ether without an alcohol)** and **A226 (methanol lacks beta-H)**, both correctly rejected. This is a denominator distinction, not a missing-row error.

A276 remains partial with its Phase 4F multi-site Lindlar restriction. A304 and its historical frozen-oracle defect annotation remain unchanged. The frozen benchmark/scorer, companion files, historical reports, dedicated dehydration/SN1/SN2/E1/E2/alkene/alkyne rule modules, styles, HTML, Calculator modules and visible curated data retain their pre-phase bytes.

Companion version **1.0.0** validates unchanged. Default and diagnostic observations exactly match Phase 5A: 40/53 structural matches, zero admitted condition-complete/independently verified/fully supported cases, five correctly rejected controls, and 33 diagnostic-only generations (12 X2, 11 HX, 10 dihydroxylation). No unreviewed profile was promoted and no companion failure appeared.

## 15. TypeScript, build and whitespace

`tsc --noEmit`: pass. Production Vite build: pass. Existing dependency `use client` notices and large-bundle warnings remain; no new compile failure. `git diff --check` and changed/new text whitespace checks pass.

Machine-readable hashes, audit comparisons, diagnostic observations and verification totals are in `reaction-lab-alcohol-substitution-phase5b-results.json`. No repository push, deployment or publication was performed.

## 16. Recommended next pathway

Next candidate: an independent review of the existing **aldehyde-to-carboxylic-acid oxidation** pathway before changing it. Separately, any future HX stereo/mechanism expansion needs substrate- and formulation-specific evidence plus validated protonation/water-departure/capture states; dropdown changes alone are not evidence.

No next pathway or additional activation mode was implemented.
