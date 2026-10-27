# Phase 5C — Primary alcohol oxidation

Scope: the existing primary-alcohol → aldehyde net transformation only. No new oxidant family, secondary-oxidation rule, reaction family, page layout, Calculator formula or curated example was added. This increment stops at Phase 5C.

**Outcome:** stronger primary-site validation, exact redox/mapping checks, equivalent-site grouping, explicit competing-alcohol metadata and corrected endpoint confidence. **No newly validated structural permissions or selective aldehyde protocol were established.** The requested expansion cannot honestly be reported as achieved merely by retaining old graph matches. The supported hypochlorite model still lacks a condition profile establishing an aldehyde endpoint.

Finite graph tests are not universal chemistry validation, experimental predictions or laboratory instructions. Supporting evidence and an ID-by-ID reconciliation of all 347 frozen rows are in [the machine-readable verification record](reaction-lab-primary-alcohol-oxidation-phase5c.json).

## 1. Original structural and fully supported coverage

Before production edits, the Phase 2C detector, site policy, exact redox edits, stereo validator, public matcher/diagram/run APIs, condition handling and calculations were inspected, and the complete unchanged audit was captured.

Phase 2C already supported saturated long/branched primary alcohols, bounded benzylic/phenyl environments, screened remote ethers, distant specified centers and separated alcohol sites. Its actual oxidant is an alkali-metal hypochlorite formula unit. PCC, Dess–Martin and TEMPO condition models were not implemented. The detailed oxidation mechanism was absent; the engine represented net bond changes.

The frozen **Alcohol oxidation** category contains 14 rows: **10 primary positives, two secondary positives and two negative controls**. Before this phase, primary structural matching and strict full support were both **7/10 (70.0%)**. The combined category was **9/12 full (75.0%)**, not a primary-only denominator. Missing/alternative medium settings were reference comparisons rather than reliable aldehyde-endpoint requirements.

Parent audit SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 2. Updated structural and fully supported coverage

| Primary-only measurement | Before | After |
| --- | ---: | ---: |
| Structural matches | 7/10 | 7/10 |
| Frozen scorer: fully supported | 7/10 | 0/10 |
| Frozen scorer: partial positives | 0/10 | 7/10 |
| Unsupported positives | 3/10 | 3/10 |
| Explicit condition-complete endpoint eligibility | Not previously separated | 0/10 |
| Independently approved complete endpoint profiles | Not previously established | 0/10 |

Zero endpoint support is a **confidence correction**, not changed aldehyde connectivity. All seven matched cases retain their mapped conditional 2D equations. They do not regain asserted 3D simply by selecting Water and First stage: no existing selector supplies a validated selective formulation. This does not mean primary alcohol oxidation is chemically impossible.

The combined category now has **2/12 strict full (16.7%)**, seven partial positives, three unsupported positives and two correctly rejected controls. Both full cases are unchanged secondary alcohols. The frozen scorer combines preview/run errors and labels policy-blocked 3D as `preview: failed`; separate public-API checks establish that conditional 2D actually succeeds.

Independent literal graph specifications verify all 20 positive development cases and reject all 20 primary-negative controls. That is verification of net connectivity, mapping and permissions, **not** 20 approved experimental aldehyde preparations. No companion profile was promoted to independently approved status.

## 3. Newly supported molecules

**None newly admitted on chemical structural grounds.** The useful changes are validation, confidence and multiple-site presentation, rather than unsubstantiated expansion. Existing long/branched, benzyl, phenethyl, remote-ether and distant-chiral examples remain available as conditional net graphs.

New independent fixtures cover methanol, ethanol, propanol, dodecanol, isobutyl/neopentyl/remote-branched alcohols, benzyl and methoxybenzyl alcohols, phenethyl alcohol, a remote ether, both distant enantiomers, both CIP-relabeling controls, equivalent and distinct diols, a primary/secondary diol, a remote tertiary-OH spectator and an already permitted five-membered ring spectator. These are test cases, not additions to the website's visible examples or new chemistry permissions.

## 4. Remaining unsupported structures

The three frozen primary exclusions remain:

| ID | Structure | Reason |
| --- | --- | --- |
| A084 | `OCCCCF` | Fluorine/haloalkane spectator compatibility is outside the retained oxidation policy; not a claim that a C–F bond prevents oxidation. |
| A085 | `NCCCCO` | Amine/hypochlorite competing chemistry is not modeled. |
| A087 | `C=CCO` | Additional alkene oxidation/addition chemistry and selective allylic aldehyde formation are not validated. |

Also retained: unscreened heteroatoms/charge/isotopes, invalid or enhanced stereo, propargylic/conjugated substrates, additional carbonyls, phenols/peroxides/acetals, sensitive benzyl/allyl ethers, vicinal diols, short lactol/lactone closure environments, adjacent specified epimerization-prone centers, unvalidated strained rings and the existing 80-explicit-atom product bound. Secondary and tertiary sites cannot enter the new primary-only validator. Methanol is explicitly treated as the methyl-alcohol special case.

## 5. Validated oxidants and conditions

Actual Li/Na/K/Rb/Cs hypochlorite graphs retain the existing **formal net accounting**. Counterion acceptance is not experimental protocol validation. Bare hypochlorite without its supported counterion, HOCl, chloride salt, water, hydrogen/peroxide and a reagent merely named PCC/Dess–Martin do not acquire this model.

No selective aldehyde condition profile was added. Missing medium/stage, alternative media, heated conditions, extra activation, unrelated release/workup settings and unknown explicit fields receive separate explanations. Background alkyne-equivalent/chain-length settings are explicitly not applicable, not oxidation stoichiometry. Direct alcohol-to-acid is still rejected; the separate aldehyde-oxidation pathway is unchanged.

Independent primary evidence: Anelli, Montanari and Quici's checked [Organic Syntheses method](https://www.orgsyn.org/demo.aspx?prep=CV8P0367), DOI 10.15227/orgsyn.069.0212, describes a condition-specific catalytic/biphasic system and discusses acid formation and unsaturated-substrate side reactions. **Inference for this software:** its generic dropdowns cannot stand in for that formulation. The referenced catalyst system was not implemented or silently assumed.

## 6. Overoxidation safeguards

Primary options now expose `aldehydeEndpointValidated: false`, `selectiveOxidantProfileImplemented: false` and `conditionCompleteEligibility: false`. Public matching distinguishes structural eligibility from conditions, endpoint confidence and independent review. Conditional diagrams explicitly describe a hypothetical first-stage equation.

The public run API rejects primary aldehyde assertions **before conformer generation**. Forged/stale permissions and unsupported condition keys cannot bypass the backend. 3D/Compare controls are disabled, stale secondary 3D models clear on input changes, and the atom inspector no longer invites Compare for a primary preview. Reasoning labels use the same unresolved confidence rather than calling an alternative medium chemically “Unfavorable.”

No acid product is substituted for an uncertain aldehyde, and no selector claims to suppress further oxidation. Unsupported condition profiles require future validated implementation, not guessing another dropdown value.

## 7. Multiple-site compatibility

Each eligible primary site is independently assessed using the preserved Phase 2C compatibility report. Competing primary/secondary alcohol maps are exposed; additional OH groups are not described as protected or selectively inert.

Whole-graph chirality-aware automorphisms group proven equivalent primary options. Propane-1,3-diol has one canonical product choice with two exact, independently addressable legacy source-site IDs. A nonsymmetric long diol retains two distinct constitutional choices. Mixed primary/secondary alcohols retain their separate secondary options and existing secondary 3D behavior. These are theoretical alternatives, not additive yields or experimental selective mono-oxidation.

## 8. Stereochemistry verification

The existing physical-stereo edit contract remains authoritative. New tests independently check both remote enantiomers, unchanged mapped configurations, atom-order renumbering and a retained center whose CIP assignment changes S→R or R→S because priorities change—not because physical inversion occurred.

Deliberately inverted/erased distant centers fail validation. Invalid supplied tetrahedral/directional annotations cannot silently normalize away in the primary consumer. Alpha-carbonyl epimerization exclusions remain. The selected carbonyl carbon must be planar SP2 without a tetrahedral tag; new centers are not invented.

Primary asserted 3D is deliberately unavailable, so this report does **not** claim primary-product conformer/stereo verification. Exact 2D provenance and backend output gates are tested. Secondary actual 2D/3D links and browser selection were independently checked and remain working.

## 9. Oxygen and hydrogen accounting

The primary wrapper preserves the existing formal equation:

`RCH2OH + MOCl → RCHO + H2O + MCl`

Methanol analogously gives a hypothetical methanal stage. The selected original alcohol oxygen remains in the carbonyl. One actual mapped carbon-bound H and the actual O–H hydrogen become net water with the hypochlorite oxygen; the actual chloride/counterion are retained. Individual oxidant O/Cl formal charges change correctly; total represented charge and mapped elemental identities are conserved.

Exact-edit validation rejects swapped oxygen provenance, lost/duplicate maps, incorrect charge, an acid instead of the aldehyde, retained carbonyl chirality and fabricated H2. The formal equation is not a measured isotope history, solvent proton-exchange model or complete oxidation-endpoint equation.

Calculators retain full salt molar masses and the one-stage 1:1 ratio. New fixtures check both input orders, Na/K formula units, unit conversions, limiting amounts, zero oxidant and target amounts. Warnings state that this is not isolated aldehyde yield, total further-oxidation demand or proof of completion. Browser check: 1 mmol each ethanol and NaOCl gives the **formal** 1 mmol / 0.044053 g carbonyl amount while 3D remains blocked.

## 10. Mechanism limitations

Detailed reagent-specific oxidation mechanisms remain **unsupported**. No chromate, periodinane, oxoammonium, radical, hydride-transfer or imagined catalyst intermediate was added. Public mechanism data remain null and capability reporting says net transformation only. Net C–O order change and H-transfer highlighting are bookkeeping, not elementary curved-arrow steps.

## 11. New restrictions

The new restriction is asserted primary-aldehyde endpoint generation for the existing inadequately qualified hypochlorite inputs. Structural matches and original net products were not removed. Raw invalid stereo is now explicitly rejected rather than normalized away. Unknown/unsupported conditions cannot silently certify an endpoint.

Secondary rules and their condition gates were not changed. Remaining uncertainty in that older chemistry is outside this primary-only phase; preserving it here does not independently endorse every secondary protocol.

## 12. Tests added and regression results

Added **153 tests**: **70 Python** primary-site/product/provenance/stereo/condition/public-API tests; **81 JavaScript** formal calculator/guidance fixtures; **two JavaScript** inspector confidence/reset tests. There are **1,700 Python + 1,680 JavaScript = 3,380 passing tests** in the completed verification, preserving the 3,227 baseline test functions.

Some previous primary assertions necessarily changed: the Phase 2C shared test helper's generic `Possible` label and successful primary run expectation, the authenticated primary HTTP run's 200 expectation and the cross-pathway primary 3D test. They now require explicit conditional confidence and blocked 3D while retaining connectivity, atom, stereo and balance assertions. Secondary branches retain their old successful-run assertions. These expectation corrections are documented, not hidden as unchanged historical assertions; no test was deleted or skipped and the frozen benchmark was untouched.

The 40-case read-only development diagnostic reports 20/20 positive product sets, 20/20 primary-negative controls, 21 canonical positive net options, 21 intentional run-policy blocks and no invariant failures. Production API tests include authentication, direct legacy IDs, multiple sites, mixed secondary behavior, forged permissions and gates before conformer generation. Layout, Calculator formulas, curated data and unrelated rule-file content hashes match the pre-change snapshot.

## 13. Unrelated benchmark results and all-row reconciliation

All **347** case IDs are enumerated with before/after results in the verification JSON. Partition rules: ten specified primary positives; two secondary positives; two oxidation controls; 333 rows outside Alcohol oxidation. Therefore **337 non-target rows** are unchanged, including all their products, counts, notes, preview/run statuses and geometry findings—not just their score labels.

| IDs | Classification | Before → after |
| --- | --- | --- |
| A080, A081, A082, A083, A086, A088, A102 | Matched primary positives | Full → partial; same actual connectivity, conditional 2D, endpoint run blocked |
| A084, A085, A087 | Unsupported primary positives | Unchanged |
| A100, A101 | Secondary positives | Full → full, actual 3D retained |
| A089, A103 | Alcohol-oxidation negative controls | Correctly rejected → same |
| All other 333 IDs | Outside target category | Entire result rows unchanged |

Global strict totals: **165→158 full, 53→60 partial, 90 unsupported, 38 correctly rejected, one historical incorrect-result label**. This accounts for all 309 positives and 38 controls. Only the seven primary confidence rows change.

**A276** retains the historical separated-alkyne single-site restriction and partial label. **A304** retains the frozen incorrect product expectation and its separate proposed-not-applied oracle-defect annotation. Neither was edited or reclassified to improve scores.

The pinned v1.0.0 companion remains unchanged: 58 scoped rows, 53 positives, five controls, 289 out-of-review rows; structural 40/53; condition-complete, fully supported generation and independently verified endpoint metrics all zero. Diagnostic-only overlays still generate 33 cases (10 dihydroxylation, 12 alkyne X2, 11 alkyne HX). Those are unvalidated overlays, not approved chemistry. Version self-comparison reports no case/profile/defect changes. No primary profiles were added to or approved in the companion.

## 14. TypeScript, build, whitespace and UI verification

TypeScript `tsc --noEmit` and the production Vite build pass. The existing large-chunk warning remains; no new publication/deployment occurred. `git diff --check` and an additional trailing-whitespace scan of changed/new source files pass.

Browser verification used the actual existing page: the 2-propanol example still generated linked acetone 3D; selecting a mapped carbon linked both views. Changing to ethanol cleared that output; missing/first-stage primary choices stayed conditional; original oxygen selected both 2D occurrences with an honest unavailable-3D hint; the existing calculator produced the formal amount with confidence warnings. No overall layout was changed.

![Verified conditional primary-alcohol preview](reaction-lab-primary-alcohol-oxidation-phase5c-preview.png)

## 15. Recommended next development step

Before expanding primary structural coverage or restoring asserted primary 3D, independently validate and explicitly represent a narrowly bounded **selective aldehyde condition profile**, including its supported formulation/activation, medium, exposure/supply, endpoint/release assumptions and spectator limits. This requires a separate approved scope decision; it must not be inferred from an “ambient” or “first stage” dropdown. Then test suitable allylic/heteroatom cases individually against that exact chemistry, rather than globally removing the Phase 2C filters.

No Phase 5D work or additional oxidant family was begun. The present result is a completed conservative confidence/validation increment, with structural expansion and selective-endpoint chemistry explicitly remaining unimplemented.
