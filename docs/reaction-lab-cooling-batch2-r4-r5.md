# Cooling Batch 2 (R4 + R5): evidence and safeguard report

26 October 2026 · Local only · Evidence-boundary increment, not a universal cooling model

## Decision

The reviewed evidence did **not** meet the existing profile-admission gate for a new cooled 3D model in this increment. No reaction is declared impossible. The seven previously admitted profiles across four rule types remain unchanged. Conditional 2D options, existing mechanisms and theoretical calculations remain available where their existing structural and condition checks allow them.

R4 and R5 were investigated independently rather than stopping when the first case failed its evidence gate. The search is a bounded literature review, not a claim that no qualifying experiment exists. No production code, chemistry rule, named profile, layout, curated example or benchmark input was changed. A new versioned cross-pathway regression suite records the actual boundaries.

## R4: chlorination and alkyne halogenation

| Candidate | Decision | Specific unresolved issue |
| --- | --- | --- |
| Alkene + Cl2 | Conditional net 2D only under cooled selection | The reviewed 1-hexene experiments use brine and/or chloride-bearing additives. The controls do not identify those formulations, and the source also discusses competing chlorinated products. The prior Taft and Poutsma complete experimental texts have not been checked here. No assumption that the generic dry/none selections establish that profile. |
| Alkyne + one Br2 | Conditional net 2D only | One-equivalent and product stopping must be supported for a specific eligible acyclic substrate and actual medium. An accessible low-temperature cyclic-alkyne experiment has a different substrate and substantial competing chemistry; it does not validate the acyclic model. |
| Alkyne + two Br2 | Conditional net 2D only | A one-equivalent precedent would not establish the two-equivalent tetrahalide endpoint. A separately documented cold formulation and net product are still needed. |
| Alkyne + Cl2 | Conditional net 2D where the existing matcher permits it | Independently requires chlorine-specific formulation and stage validation; first-stage chlorine geometry is already a separate confidence boundary. No bromine permission was transferred. |

The earlier chlorination review records the direct 1-hexene/Cl2 cold patent examples, their 0–20 °C reaction control, chloride-containing formulations and missing table/work-up details: [WO2026128662A1, paragraphs 0083–0089](https://patents.google.com/patent/WO2026128662A1/en). Those details do not demonstrate an additive-free dry reference. The previous [R4 chlorination report](reaction-lab-cooled-chlorination-phase4.md) remains the detailed source-access record.

A newly inspected primary-source control is the [supporting information for Herges et al., *cis-Bromination of Alkynes Without Cationic Intermediates*](https://application.wiley-vch.de/contents/jc_2001/2005/z461632_s.pdf), PDF pp. 2–4. Its cyclooctyne/Br2 experiment uses CDCl3 and a −70 °C mixing condition and reports several products, including differently configured dibromoalkenes. This is **not** a validating example for the application's acyclic one-Br2 reference, nor evidence for a two-Br2 tetrahalide endpoint. Its separately synthesized cyclooctene derivative is not an alkyne-addition control. The paper demonstrates why reagent, temperature, structure and endpoint cannot be collapsed into a universal cold rule.

Textbook descriptions of 0 °C alkyne dibromination and additional indexed/vendor protocols were found as research leads, but their primary experimental source, precise formulation, work-up and applicability to the existing engine were not established in this review. They are not used as approval evidence. Cold bromination and chlorination remain chemically possible; their scope is not proven by this implementation.

## R5: substitution and elimination

| Candidate | Decision | Specific unresolved issue |
| --- | --- | --- |
| Hydroxide SN2 | Conditional net 2D only | The existing methyl-halide kinetic work near 287 K used aqueous buffers and does not establish a generic cold polar-aprotic model or directly validate each represented product and competing reaction. The complete earlier source/formulation limitation remains. |
| Water SN1 | Conditional net 2D only; strongest next evidence candidate | A directly inspected low-temperature aqueous-solvolysis study includes tert-butyl chloride at 273.22 K. It measures conductivity, not independently identified cold alcohol and alkene products; a small acetone stock injection is part of the actual formulation. A separate product/competition check for that condition is still required before a source-specific product profile is admitted. |
| Water E1 | Conditional net 2D only | A cold ionization/conductivity measurement cannot establish that the alkene endpoint occurred or its abundance. Direct relevant cold alkene-product evidence remains necessary. |
| Hydroxide E2 | Conditional net 2D only | No matched cooled hydroxide/alkyl-halide experiment with an independently confirmed represented alkene endpoint was validated in this review. Base activity, SN2 competition and anti geometry must remain site-specific. |

For SN1, Adams and Sheppard, [*Effect of temperature on the specific heat of activation for the solvolysis of tert-butyl chloride and tert-pentyl chloride in water*](https://doi.org/10.1039/F19807602114), J. Chem. Soc., Faraday Trans. 1 **76**, 2114–2123 (1980), is a significant new primary-source lead. The available [paper scan](https://file1.lookchem.com/doi/2022/3/24/a740ec5f-ab0d-4678-9f50-b9af38ba244b.pdf), pp. 2114–2116 and Table 2 on p. 2118, describes distilled deionized water, conductivity monitoring, substrate introduced in a small acetone stock aliquot, and a tert-butyl chloride measurement at **273.22 K (approximately 0.07 °C)**. The acetone is not a separate nucleophile in the engine, but its actual concentration and experimental role must not be silently represented as identically pure water. The paper is kinetic evidence; the inspected method does not identify or quantify the cold alcohol and elimination products separately. The smallest useful next review is independent product/competition evidence matched to this specific aqueous reference, not a generic tertiary-halide or SN1/E1 approval.

For SN2, [Baesman and Miller's primary record](https://doi.org/10.1007/s10874-005-1904-0) and the directly reviewed aqueous methyl-iodide studies described in the [earlier SN2 report](reaction-lab-cooled-sn2-phase5.md) remain relevant. The buffered 287 K methyl-halide measurements and other warmer product work cannot be silently combined into an exact near-zero, hydroxide-only product profile. No alcohol formation, inversion, rate or solvent conclusion is generalized to other substrates.

The net SN1 diagram uses HX as an acid-equivalent bookkeeping representation; its existing mechanism represents water attack and proton transfer. Neither that diagram nor the existence of an E1 option proves a product distribution. E1 and E2 retain distinct stepwise versus concerted mechanisms, and neither receives inferred rates, product ratios or stereochemical assignments from a conformer.

## Safeguards and integration

Added [tests/test_cooling_batch2_boundaries.py](../tests/test_cooling_batch2_boundaries.py), a separate v1 suite with six tests and independently specified product-connectivity oracles for eight candidate settings. It checks both input orders; conditional previews; exact mapped-element inventory and total charge; existing mechanisms; one- versus two-equivalent stoichiometry; theoretical-calculator warnings; the seven-profile registry; rejection of another pathway's named profile and forged confidence; stale ambient-to-cooled permissions; and authenticated match, diagram and blocked-run endpoints.

No product rule, stereo rule, frontend selector, named-profile descriptor, condition gate, benchmark or curated example was edited. The R3 isobutylene fractionation contract, distinct crotonic/cinnamic water recoveries and unassigned acid-product stereochemistry remain intact. A 3D conformer remains a theoretical representation, not a simulation of temperature or experimental yield.

## Verification

Final regression runs: **4,353 passed** (2,172 Python + 2,181 JavaScript), six above the 4,347-test R3 baseline. TypeScript and production build passed; the existing large Builder-bundle warning remains.

- The complete unchanged **347-case** frozen audit was rerun and exactly matched the R3 saved results, including its recorded fingerprint. Totals remain 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported and one pre-existing incorrect-result classification. No new cooled case was inserted into that benchmark.
- Both version-1.0.0 companion runs matched all saved R3 result data after excluding `engineSha256`. The earlier saved companion output has a different engine fingerprint; current production files themselves have not been changed during this batch. Normal replay: 40/53 structural matches, zero evidence-qualified full generations; diagnostic-only replay: 33/53 model generations, not validated cold coverage. Both report no failures. The initial raw equality check failed solely on that fingerprint and was not treated as a chemistry regression.
- Desktop 1440 px and mobile 320 px: conditional 2D, disabled cooled 3D/run, no overflow and no page errors were checked for Cl2, alkyne Br2, SN1, SN2, E1 and E2. The three existing R3 profiles were additionally checked on both viewports for confirmed 3D, distinct recovery, calculator output, temperature/release invalidation, keyboard confirmation and delayed-response rejection. An initial browser-test assertion incorrectly treated collapsed text as visible; the test was corrected to inspect the existing text without altering the UI.
- Focused v1 suite: six tests passed, including authenticated endpoints and both alkyne equivalent counts. Source-specific R3 browser checks passed; no newly admitted profile exists to test as a positive.
- QA artifacts are in `/private/tmp/molecule-batch2.wiOmDD`, separate from the R3 artifacts. The isolated localhost test server was stopped. No push, merge or Render deployment occurred during this batch. The previously authorized public backup branch is a separate earlier action and is not described as absent.

## Recommendation and stop boundary

Obtain or independently review product identification and competing-elimination evidence for the near-zero aqueous tert-butyl chloride study, including the acetone-stock and acid-equivalent reporting assumptions. If that evidence supports a bounded theoretical product contract, review an explicit, exact-substrate SN1 profile separately. It would not automatically approve E1, all tertiary substrates, arbitrary solvent mixtures or an experimental product ratio.

For alkyne Br2, obtain primary full experimental details for a matching acyclic one-equivalent product and separately for the two-equivalent endpoint. For Cl2, obtain full experimental details for a formulation the named-profile system can honestly describe; do not disguise chloride additives or competing radical chemistry. Continue treating E1/E2 as separate evidence gates.

Stop after this Batch 2 report. No Batch 3 was started.
