# Phase 5A — Alcohol dehydration

Completed 2026-10-16. Scope: the existing sulfuric-acid alcohol-dehydration pathway only. No new reaction family, reagent family, layout, Calculator formula or curated example was added. Phase 5A stops here.

This is a bounded **net-structure model**, not an experimental reaction predictor or laboratory protocol. Passing finite tests does not establish universal chemistry correctness.

## 1. Original coverage and implementation

The dehydration implementation and its public workflow were inspected before production changes. It accepted simple saturated acyclic C/H/O mono-alcohols, rejected specified stereochemistry and additional oxygen groups, enumerated beta positions, and returned an alkene plus water. Its acid/heated settings were reference assessments rather than a dehydration-specific product-generation gate. There was no complete mapped acid-catalytic mechanism.

The frozen 347-case benchmark contains **10 dehydration rows: eight positive cases and two negative controls**. Before changes: **2/8 fully supported (25.0%)**, **3/8 positive structural matches**, one partial, five unsupported, and two correctly rejected controls. The separately captured pre-change dehydration rows agree with the completed Phase 4F artifact. The pre-change server-content fingerprint also matches Phase 4F.

The parent benchmark was not edited. Its SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 2. Updated frozen coverage

After changes: **2/8 fully supported (25.0%)**, **4/8 positive structural matches**, two partial, four unsupported, and both controls correctly rejected. The higher structural count is not presented as higher fully supported coverage.

| Case | Structure / scope | Before → after | Interpretation |
| --- | --- | --- | --- |
| A208 | Long primary alcohol, `CCCCCCCO` | Full → full | Terminal alkene and mapped water remain available. |
| A209 | Secondary internal alcohol, `CCCC(O)CC` | Partial → partial | Both constitutional products remain; unresolved E/Z now prevents asserted 3D. |
| A210 | Branched tertiary alcohol, `CCCC(O)(C)C` | Full → full | Two distinct products remain; three source-site aliases are retained. |
| A211 | Cycloheptanol | Unsupported → unsupported | Ring/rearrangement chemistry remains unvalidated. |
| A212 | `COCCCCO` | Unsupported → unsupported | Possible five-membered oxygen capture; not an inert remote ether. |
| A213 | `OCCCCO` | Unsupported → unsupported | Possible five-membered intramolecular closure. |
| A214 | Specified reacting center, `CC[C@H](O)CCC` | Unsupported → partial | Two mapped constitutional alkenes now work in conditional 2D; E/Z remains unresolved. |
| A215 | Ether without an alcohol | Correct rejection → same | No invented alcohol site. |
| A225 | Phosphoric-acid reagent | Unsupported → unsupported | Existing sulfuric-acid model only; no new acid family. |
| A226 | Methanol | Correct rejection → same | No beta carbon/hydrogen to eliminate. |

The unchanged scorer combines diagram and run failures into one `preview` field: A209/A214 therefore say `preview: failed` when 3D is policy-blocked, although separate public API tests verify their conditional SVGs. Also, a frozen row marked full is not proof that every alternative has 3D: A210's terminal option runs, while its internal unsigned-E/Z option is blocked. These scorer limitations are documented, not repaired by changing the benchmark.

## 3. Newly supported structures

The new `server/alcohol_dehydration_rule.py` uses site-specific compatibility, explicit edit contracts and the existing stereochemistry/atom-mapping architecture. Production contains no fixture-name lookup.

New support includes specified reacting alcohol centers whose configuration is correctly consumed, distant specified tetrahedral centers, screened sufficiently separated ether/alcohol groups, and independent alcohol sites. Remote additional oxygen groups are **conditional 2D only**, not a claim that they remain inert in hot acid.

Independent fixtures include remote `@` and `@@` centers, `COCCCCCCCCO`, `OCCCCCCCCO`, and `CC(O)CCCCCCCCO`. Long, branched, secondary and tertiary structures are regression-tested too; simple long-chain substrates already worked before this phase and are not claimed as newly discovered coverage.

A separate 40-case diagnostic has **20/20 positive structural matches and 20/20 rejected negative controls**. Of 32 canonical positive options, 16 have verified conditional net-model 3D and 16 are intentionally policy-blocked. Fifteen of 20 positive cases have at least one allowed 3D option; only eight have all their alternatives allowed. These are development fixtures, not replacements for the frozen benchmark or independently approved experimental condition profiles.

## 4. Remaining unsupported cases

Restrictions remain for cyclic/ring-containing substrates, rearrangement-risk branching, nearby oxygen capture, acid-sensitive ether/acetal environments, heteroatom-substituted beta positions, conjugated/unsaturated competing groups, unsupported elements, invalid stereo annotations, and the existing molecular-size limit. Methanol and sites without an actual beta C–H cannot eliminate. Phosphoric acid and other unvalidated reagent systems are not enabled.

Messages distinguish unsupported modeling from chemical impossibility. A distant oxygen group is screened for topology and local environment rather than automatically treated as inert. Even a screened group does not acquire experimental one-site selectivity.

## 5. Regioselectivity and multiple sites

Every eligible alpha/O/beta combination is assessed separately. Distinct constitutional alkenes are separate options; no automatic Zaitsev-only choice or major/minor percentages are generated. Whole-molecule, chirality-aware graph equivalence groups equivalent UI choices while retaining their original reaction IDs, exact map aliases and source-site selection.

For example, tert-butanol retains three mapped beta-site aliases under one canonical product. A tertiary alcohol with three non-equivalent arms can yield three separate net alternatives. Multiple-alcohol examples preserve the other groups in conditional equations; amounts for alternative outcomes must not be added as simultaneous yields.

## 6. Stereochemistry and mechanisms

Only validated participating sp3 carbons becoming sp2 lose their tetrahedral tags. Unchanged atom identities, bonds and distant physical configurations are checked by the edit contract. Invalid specified input is rejected rather than silently normalized away.

Independent checks include both enantiomeric inputs, deliberately corrupted mapped products, and `C[C@H](CCCCO)CCC(C)C`: its remote physical configuration is retained although independently recalculated CIP changes **R → S**. A separate coordinate-based check agrees with the resulting assignment. The CIP-label change is not physical inversion.

New E/Z-capable alkenes remain explicitly unsigned and are conditional 2D only. No E/Z, syn/anti outcome or stereoisomer ratio is inferred from conformer optimization.

**No complete dehydration mechanism was invented.** Mechanism payloads remain null and the mapped-mechanism capability is marked unsupported. Primary alcohols are not given a free primary carbocation. Secondary/tertiary substrates receive a bounded E1-type rationale, not borrowed alkyl-halide elementary steps. The diagram is explicitly net bond bookkeeping: it does not depict bare OH departure as an elementary reaction, or claim a verified protonation/carbocation/deprotonation sequence with mapped catalyst atoms.

## 7. Reagents and condition confidence

The actual sulfuric-acid reagent is required. Acid activation and heated temperature must be explicitly confirmed for the bounded model; missing settings receive actionable guidance, keep conditional 2D available, and block 3D. Conflicting activation, unevaluated media, incompatible workup/oxidation settings and unsupported condition fields also block 3D without silently inventing chemistry.

Unspecified or dry medium preserves the existing narrow net-model convention; it is **not** an independently validated experimental solvent/concentration/temperature profile. Aqueous, alcoholic and generic polar-aprotic alternatives are labelled unvalidated, not universally unfavorable. Ether formation, sulfate-ester intermediates, isomerization, water activity, conversion and experimental product distribution remain outside the model.

No new experimental condition profile was admitted. Primary research gives reasons not to promote generic settings to universal selectivity: catalyst-dependent primary-alcohol dehydration can involve ether formation/isomerization ([RSC experimental study, DOI 10.1039/D4GC01038H](https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc01038h)). Studied secondary-alcohol mechanisms also depend on the reaction environment; hydrothermal results do not validate this sulfuric-acid selector ([ACS study, DOI 10.1021/acsearthspacechem.8b00030](https://pubs.acs.org/doi/10.1021/acsearthspacechem.8b00030)). Publisher-indexed abstracts/summaries were accessible; direct full-text requests were denied. No substrate-specific protocol approval is inferred from that limited access.

## 8. Atom mapping, water and calculations

The exact net contract breaks alpha–O and beta–H, changes alpha–beta from single to double, and forms O–beta-H. Water retains the original alcohol oxygen, original OH hydrogen and selected beta hydrogen. All represented atom identities, total charge and unaffected bonds must agree; water/main-product fragments and main-product 2D/3D links are checked independently.

This is **formal net provenance**, not elementary isotope provenance: catalyst/solvent proton exchange is not modeled. Sulfuric acid is regenerated, excluded from consumed inputs, and labelled **catalyst (not consumed)** in the equation, diagram metadata and amount explanations.

Calculators retain 1 alcohol → 1 alkene + 1 water, including the 18.015 g/mol mass difference. Tests check both reactant orders, gram/mmol conversions, required amounts and limiting-input selection. Results remain theoretical stoichiometry, not actual conversion/yield or a prediction of which alternative dominates.

## 9. Newly restricted confidence and unresolved chemistry

The deliberate observable restriction is stronger product confidence: missing acid/heated confirmation no longer permits 3D merely because an example differs, and unresolved new E/Z (including A209) no longer receives an arbitrary asserted stereochemical conformer. Screened extra-oxygen single-site equations are 2D only. Unknown condition fields cannot reuse stale permissions.

Rearrangement, near-oxygen capture and acid-sensitive groups are rejected precisely. No existing ring or alternative-acid restriction was removed to raise coverage. An allowed 3D structure is labelled a conditional net-model conformer, never a guaranteed experimental product.

## 10. New tests and regression results

**155 tests added; 3,055 pass: 1,558 Python + 1,497 JavaScript. All 2,900 original tests remain passing.**

The new tests comprise 85 Python and 70 JavaScript tests, using 20 independently specified positive structures, 20 negatives, multiple conditions and every canonical option. Coverage includes map/bond/charge mutation rejection, water coproducts, stereo consumption/retention, CIP changes, duplicate source aliases, molecular-size boundaries, reversed inputs, public authenticated match/diagram/run APIs, forged IDs, stale condition permissions, amount calculations and equation catalyst labels. The standalone 40-case diagnostic reports no failures.

Browser verification used the existing ethanol example: linked 2D/3D carbon selection worked; clearing temperature removed the old product and disabled 3D; selecting the conditional option still displayed 2D and explicit missing-temperature guidance. No example collection or layout was edited. The temporary test tab and locally started preview were closed afterward.

![Existing linked comparison view](reaction-lab-alcohol-dehydration-phase5a-preview.png)

![Missing temperature keeps conditional 2D and blocks 3D](reaction-lab-alcohol-dehydration-phase5a-conditions.png)

## 11. Unrelated benchmark and Phase 4F preservation

All **337 non-dehydration frozen rows are exactly unchanged** from Phase 4F. All 347 rows reconcile to 167 full, 49 partial, 92 unsupported, 38 correct rejections and one known incorrect-oracle result. The one status improvement is A214 unsupported → partial. No new incorrect-result row appeared.

A276 remains partial with the Phase 4F multi-site Lindlar confidence restriction. A304 remains the known frozen product-expectation defect; its annotation and production treatment were not changed. Snapshot-covered original tests, benchmark inputs/scorer, historical reports, companion manifests, styles, Calculators and curated example data remain byte-identical. No HTML layout file was edited.

Versioned companion **1.0.0** validates unchanged. Both default and diagnostic row observations are exactly identical to Phase 4F: 40/53 structural matches, **0 condition-complete / independently verified / fully supported**, and five rejected controls. Diagnostic-only generation remains 33 (12 alkyne X2, 11 alkyne HX, 10 dihydroxylation), not validated coverage. There are no companion failures and no promoted unreviewed cases.

## 12. TypeScript, build and whitespace

TypeScript `tsc --noEmit`: pass. Production Vite build: pass. Existing dependency `use client` notices and the large-bundle warning remain; they are not new compile failures. `git diff --check` and changed/new text whitespace checks: pass.

Machine-readable observations, hashes, case comparisons and verification totals are in `reaction-lab-alcohol-dehydration-phase5a-results.json`. No publication, repository push or unrelated chemistry change was performed.

## 13. Recommended next pathway

Next candidate: the existing **alcohol-substitution** pathway, beginning with an independent compatibility/conditions audit rather than borrowing dehydration permissions. Separately, any future dehydration expansion needs source-reviewed substrate-specific conditions, justified ring/rearrangement handling and an independently validated acid-catalytic mechanism before claiming those capabilities.

No next pathway or further dehydration mechanism was implemented in this phase.
