# Phase 5D — Secondary alcohol oxidation

Completed 2026-10-17 (America/Toronto). Scope: the existing secondary alcohol → ketone pathway only. No new oxidant family, structural permissions, detailed oxidation mechanism, curated example or overall page layout was added. Primary alcohol oxidation and its unresolved aldehyde gate remain unchanged. Phase 5E was not started.

**Outcome:** one explicitly declared, bounded **sodium hypochlorite/acetic-acid secondary ketone net profile**, with secondary-only validation, condition confidence, conservative competing-group gates, stereo checks and equivalent-site grouping. Qualified 3D means a theoretical mapped product under the declared model—not experimentally certain conversion, recovery, yield or safety.

See [versioned verification and all-row reconciliation](reaction-lab-secondary-alcohol-oxidation-phase5d.json). The separate replay is a diagnostic, not a replacement frozen benchmark or automatic companion approval.

## 1. Existing pathway baseline

Before production changes, the Phase 2C compatibility architecture, detector, redox edit, physical-stereo contract, public matching/diagram/run APIs, condition normalization, calculations and Phase 5C primary wrapper were inspected. A fresh 347-case baseline was captured.

The fixed Alcohol oxidation category has 14 rows: ten primary positives, **two secondary positives** and two negative controls. The secondary subset was **2/2 structural matches and 2/2 strict full**: A100 (`CCCC(O)CCC`, 4-heptanol) and A101 (`OC1CCCCCC1`, cycloheptanol). Both frozen inputs specify only `solvent=aqueous-protic`. The older secondary consumer allowed 3D even when activation/formulation information was missing. The combined category baseline was 2/12 full, seven partial primary positives, three unsupported primary positives and two correctly rejected controls.

This is not a new 8/12 or 9/12 secondary baseline; those historical totals mixed primary and secondary chemistry.

## 2. Existing reagents and condition profiles

The graph-recognized alcohol oxidant family is an actual Li/Na/K/Rb/Cs hypochlorite formula unit. Sodium hypochlorite is the catalog reagent. The original generic aqueous reference did not establish an acetic-acid formulation. No PCC, Dess–Martin or TEMPO oxidation was added.

The qualified profile is **sodium-specific**. Other existing hypochlorite counterions retain their exact formal net equations and chloride salts, but do not inherit sodium-specific condition evidence. Existing generic solvent/temperature/activation/stage/workup choices retain their parser values.

## 3. Scientific evidence and approved model scope

Independent primary source: Stevens, Chapman and Weller, *J. Org. Chem.* **1980**, 45, 2030–2032, [DOI 10.1021/jo01298a066](https://pubs.acs.org/doi/10.1021/jo01298a066). The [public Yale-hosted article scan](https://ursula.chem.yale.edu/~chem220/PROBSETS/PS13spr/PS9-S13-ans/Stevens1980JOC.pdf), especially page 2031/Table I, was read rather than relying on the title alone. It supports secondary ketone formation using sodium hypochlorite in acetic acid without an additional catalyst and includes linear and cyclic examples. Its observations about methyl ketones and diols are condition-specific, not universal permissions. [OpenStax §17.7](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols) supplies the independent secondary-alcohol/ketone oxidation-level distinction.

The implementation admits a **bounded structural-class model**, not only the named literature examples: neutral ordinary saturated C/H/O secondary alcohols already passing Phase 2C, exactly one oxygen, and an acyclic skeleton or one saturated five-to-seven-membered ring. A distant specified center may remain if the existing physical-stereo validator accepts it. Larger/complex ring systems, aromatic groups, extra OH/ether groups and non-sodium counterions are not condition-qualified in this increment.

Cyclohexanol and 2-octanol are directly represented in the cited experimental table. Other tested homologues, ring sizes and branching patterns are explicitly **model-class generalizations**, not claims that the paper experimentally examined each molecule. No experimental yield or product ratio is inferred from them.

The represented requirements are:

| Requirement | Explicit model input |
| --- | --- |
| Reagent identity | Actual sodium hypochlorite graph |
| Medium declaration | `secondaryOxidationProfile=naocl-acetic-ketone-v1`, alongside aqueous-protic medium |
| Temperature | Ambient model category |
| Additional activation | None added |
| Oxidation level | First alcohol-to-carbonyl stage |
| Workup | No isolated-workup assertion; the separate diol-release setting does not qualify |
| Substrate | Bounded sodium/mono-oxygen saturated scope above |

**Condition-complete eligibility means all represented model requirements are declared**, not that concentration, actual supply, temperature control, exposure, quench, extraction or recovery have been measured. Controlled oxidation is an explicit model assumption. The website does not provide or validate a laboratory procedure. Different pH, prolonged/excess oxidant, halogenation/haloform/cleavage and isolated recovery remain outside its prediction.

## 4. Changes made

Added `server/secondary_alcohol_oxidation_rule.py`, reusing the unchanged Phase 2C graph policy and net edit. It adds secondary-site classification/validation, exact participant maps, a profile-scope assessment, explicit conditions, conservative output gates, calculator context and chirality-aware equivalent-site checks.

Only secondary options attach `secondaryOxidationModel`. Primary matching, edits, metadata, confidence, reasoning and gates are not routed through the new module. The shared base and `primary_alcohol_oxidation_rule.py` are byte-unchanged.

The condition declaration is namespaced: it is carried as secondary-specific context while remaining an unknown field to unrelated consumers. No global solvent enum was reinterpreted. The existing medium menu gains **Aqueous acetic acid · secondary NaOCl**; it serializes the explicit profile declaration rather than silently turning ordinary Water into the profile. Draft restoration preserves that distinction. Existing layout, controls, examples and Calculator formulas remain in place.

Secondary public matching, reasoning, diagrams, run gates and Calculator context now share the same confidence decision. Invalid, stale, incomplete and forged requests cannot grant 3D before conformer generation. Unsupported explicit profile values—including non-string values—are rejected as unsupported, not accepted as defaults.

## 5. Structural coverage before and after

Frozen secondary coverage remains **2/2 → 2/2 structural matches (100%)**. No structural restriction was relaxed and no new structural permission was claimed. Longer/branched alcohols, screened ethers, distant stereo and bounded cyclic structures already benefited from Phase 2C; this phase independently exercises them rather than falsely counting them as newly admitted chemistry.

Both benchmark ketone connectivities remain exactly the same. The primary subset stays 7/10 structurally matched and 0/10 strict full, unchanged from Phase 5C.1.

## 6. Strict fully supported coverage

With the **unchanged frozen inputs**, secondary strict support changes **2/2 → 0/2**. A100 and A101 become partial because their generic Water-only settings omit the specific medium declaration, temperature, activation and stage requirements. They still have conditional 2D previews with the original ketone structures.

This is a corrected condition-confidence requirement, not loss of ketone chemistry. Users can qualify these two simple substrates by explicitly selecting the supported profile settings. That statement does not apply to extra-oxygen, aromatic or other unresolved cases.

The combined Alcohol oxidation category is now **0/12 full**, nine partial positives, three unsupported positives and two correctly rejected controls. The unchanged scorer combines preview/run errors; its `preview: failed` label on these cases reflects blocked asserted 3D. Separate APIs verify successful conditional 2D.

Frozen parent SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 7. Separate condition-aware diagnostic

`scripts/audit_secondary_alcohol_oxidation.py` emits the separate version `secondary-naocl-acetic-net-diagnostic-1.0.0`. It preserves original frozen inputs and records an additional explicit-profile replay, without changing the parent cases or asserting experimental validation from software success.

| Separate measurement | Result |
| --- | --- |
| Frozen secondary structural compatibility | 2/2 |
| Frozen secondary strict full | 0/2 |
| Explicit-profile frozen-substrate model eligibility | 2/2 |
| Explicit-profile frozen-substrate qualified theoretical 3D | 2/2 |
| Independent external evidence for the bounded profile | One primary-reference-supported model |
| Newly approved cases in the pinned companion | Zero |

The development diagnostic contains **41 cases: 25 positives and 16 secondary-negative controls**. All 25 positive literal product sets match; 16 positive cases qualify for theoretical 3D. There are 26 canonical positive net options: **16 verified 3D and ten intentionally blocked options**. The extra option is a genuinely distinct oxidation position, not an additive yield. All 16 negative controls reject the secondary pathway; primary controls may still have their separately gated primary pathway.

The fixed v1.0.0 companion remains unchanged: structural 40/53, zero approved condition-complete/full-generation/independently approved outcomes and five controls correctly rejected. Its separate unvalidated diagnostic overlays still generate 33 cases. No profile or case was automatically promoted to reviewed-applicable status. Runtime evidence-supported model permission is not independent approval of every experimental substrate/condition combination.

## 8. Newly condition-qualified examples

Under the explicit profile, checked examples include 2-propanol, 2-butanol, 3-pentanol, 2-octanol, 4-heptanol, branched/hindered saturated secondary alcohols, cyclopentanol/cyclohexanol/cycloheptanol, methylcyclohexanol and distant-chiral substrates.

These are newly **condition-qualified and validated** examples of an existing transformation—not new structural matches, reaction families or visible curated drawings. Their old unqualified successful-run behavior is intentionally no longer treated as sufficient evidence.

## 9. Remaining excluded and conditional structures

No ordinary primary or tertiary carbon enters the secondary validator. Tertiary oxidation does not invent C–C cleavage. Existing structural exclusions remain: competing C=C/C≡C, aldehyde/ketone/acid/ester and sensitive groups, vicinal/geminal OH environments, possible short hydroxy-carbonyl closure, adjacent epimerization-sensitive specified centers, unscreened heteroatoms/isotopes/charge/radicals, strained rings and size limits.

Structurally accepted remote ethers, aromatic/benzylic substrates, additional alcohols, more complex rings and non-sodium hypochlorites retain conditional net equations, not qualified 3D. The paper's particular diol result does not justify a universal primary/secondary site-selectivity rule. No unsupported spectator is silently removed.

## 10. Stereochemistry verification

The selected carbon must have two carbon neighbors and one actual mapped C–H, then become an unassigned planar SP2 ketone with no attached H. Both specified 2-butanol enantiomers give the same unassigned ketone. A specified reacting center is consumed only by the declared oxidation edit.

Distant configurations are retained physically, with CIP recomputed independently. Tests check both distant enantiomers, a substrate containing both distant and reacting centers, deliberately inverted/erased remote tags, invalid raw input stereo, and atom-order renumbering. Qualified molfile coordinates and 2D atom rows must have identical map/index/element correspondence; specified distant CIP assignments are independently checked on the actual 3D molfile.

Unspecified starting centers do not gain reaction-defined stereochemistry from an arbitrary conformer. Extra-oxygen stereo cases remain conditional, with their mapped source configurations retained in the formal graph.

**3D precision limitation:** a final numeric geometry diagnostic found that the converged MMFF94 cyclohexanone conformer places C=O about **4.75° out of the plane of its two C–C vectors** (normalized scalar triple product 0.0740). The graph is correctly SP2 with no tetrahedral tag. An initial diagnostic-only cutoff of 0.05 flagged it, but that cutoff had no independent physical-accuracy validation; it is not an existing production safeguard. The diagnostic now reports the actual numeric deviations rather than inventing a validated tolerance. No coordinates were projected, product permissions changed, or existing validation relaxed. This representative conformer must not be described as exactly planar or experimentally optimized. Future conformer geometry QA remains a separate limitation.

## 11. Atom and hydrogen accounting

The preserved formal equation is:

`R2CHOH + NaOCl → R2C=O + H2O + NaCl`

The original alcohol oxygen remains in the ketone. Its O–H and the actual reacting C–H become formal water with hypochlorite oxygen; the actual counterion and chloride remain accounted for. Individual O/Cl formal-charge edits and total mapped atom/charge conservation are validated. This is not a measured solution proton/isotope history.

The validator rejects swapped oxygen provenance, lost maps, incorrect charge, retained carbonyl tetrahedral tags, invented H2 and corrupted distant stereo. Na/K reversed-input Calculator fixtures independently check full salt molar masses, exact product mass loss, 1:1 coefficients, limiting amounts, zero oxidant and required amounts. Acetic-acid medium is not added as an invented consumed third reactant or mapped workup species.

Browser check: formal 1 mmol each 2-propanol and NaOCl gives 1 mmol / **0.05808 g** acetone, clearly labeled theoretical—not actual yield.

## 12. Mechanism limitations

Detailed mapped oxidation mechanisms remain **unsupported**. The existing view shows net C–O bond-order change and formal H transfer, not a validated sequence of elementary electron arrows. No hypochlorite ester, proton-transfer chain, chromate, periodinane, radical intermediate or new coproduct was fabricated. Mechanism data remain null and capability reporting is explicit.

## 13. Tests and total passing

Added **180 tests: 73 Python and 107 JavaScript**. Fresh full verification passes **1,773 Python + 1,787 JavaScript = 3,560 tests**, retaining all 3,380 baseline test functions.

New checks cover literal positive/negative products, classification, exact O/H/charge mapping, corrupted products/stereo, reacting-center loss, distant CIP/configuration, actual 3D correspondence, equivalent versus distinct sites, wrong counterions, missing/conflicting/invalid profile declarations, authentication, forged/stale permissions, frontend serialization/restoration and Calculator confidence.

Scientifically necessary legacy expectation corrections were limited to secondary consumers: the Phase 2C helper and authenticated API check now require the explicit profile for eligible 3D and retain conditional gates for extra groups; two mixed-secondary assertions in the primary test file now expect the new secondary gate; curated/cross-page/linked-view loops supply explicit qualifying secondary settings while also checking old unqualified rejection; standalone catalog confidence now includes secondary context. No primary product expectation, test function or frozen oracle was deleted, skipped or weakened. All former product, balance, mapping and applicable stereo checks remain.

## 14. Unrelated benchmark regression results

All **347 IDs** are reconciled in the verification JSON. Exactly A100 and A101 change, full → partial for missing modeled conditions; actual ketone products and structural counts do not change. All **345 non-target rows** are identical to the captured baseline, including all ten primary positive rows and both negative controls in the Alcohol oxidation category.

Global totals: **158→156 full**, **60→62 partial**, 90 unsupported, 38 correctly rejected, one historical incorrect-result label. A276's historical restriction and A304's frozen-oracle defect/annotation are preserved. The original benchmark, pinned companion and curated example collection remain byte-unchanged.

Primary/base oxidation rule hashes, unrelated pathway hashes, Calculator formula files, CSS and page shells were checked against the pre-change snapshot. Shared integration branches are guarded by secondary metadata; no unrelated pathway was implemented or relaxed.

## 15. TypeScript, build, whitespace and UI

TypeScript (`tsc --noEmit`), production Vite build, `git diff --check` and a changed/new-file whitespace scan pass. The pre-existing large-chunk build warning remains. No deployment or publication occurred.

Browser verification covered: unchanged example → conditional water-only preview; explicit profile selection → qualified theoretical acetone 3D; original oxygen selected across reactant/product 2D and product 3D; full-mass theoretical Calculator amounts; and return to Water clearing stale 3D and restoring the conditional gate. Only a medium choice and scoped confidence wiring were added; the overall layout was not redesigned.

![Qualified secondary ketone with mapped oxygen linkage](reaction-lab-secondary-alcohol-oxidation-phase5d-preview.png)

## 16. Recommendation for Phase 5E

Review the existing **aldehyde → carboxylic acid** pathway next, especially reagent conditions, acid versus carboxylate reporting and workup confidence. Keep the unresolved selective-primary-aldehyde gap explicit; this secondary profile does not resolve or approve it.

A future expansion of secondary spectator or multi-site qualification should be separately evidence-scoped rather than automatically inheriting this simple-substrate profile. No Phase 5E implementation was started.
