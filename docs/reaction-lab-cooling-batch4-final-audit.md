# Cooling system — Batch 4 R8/R9 final audit

Local review, 26–27 October 2026. This finite audit is not a certification of universal chemistry, an experimental prediction, a laboratory protocol, or an instruction to deploy. Historical R1/R2, R3, R4/R5 and R6/R7 reports remain unchanged. R3's full Milas–Sussman PDF was supplied and reviewed; the older roadmap's missing-pages reminder is superseded.

## Executive decision

No new R8 profile is admitted. The six candidates were evaluated independently; the specific evidence inspected did not establish an exact source-compatible cooled product endpoint and condition contract for the existing rules. This is not a claim that cooled ester reactions or oxidations are impossible, nor that no suitable publication exists. All eight previously admitted profiles remain, across five of 24 rule types. R9's separate audit exercised all 24 pathway types through the existing 25-case cooling matrix and all eight admitted profiles through a new source-identity/endpoint fixture. Prior supported and unsupported decisions remain scoped; the frozen 347-case benchmark was not modified.

The key distinction is between an ice bath or cold reagent **addition**, a measured reaction temperature, a subsequent warm reaction or work-up, and the isolated product. A source-specific theoretical net product does not require a kinetics simulator, but it does require applicable evidence, correct participant identities and a representable endpoint. No generic cooled 3D permission is inferred.

## R8 candidate-by-candidate review

| Candidate | Evidence and conditions inspected | Decision / exact gap |
| --- | --- | --- |
| Esterification | Existing acetic acid + ethanol net model; the cited [batch-reaction study](https://communityresearch.org.nz/wp-content/uploads/formidable/Esterification-of-Ethanol-and-Acetic-Acid-in-a-Batch-Reactor-in-Presence-of-Sulfuric-Acid-Catalyst.pdf) reports a heated 80 °C reaction, not a 0 °C experiment. | Defer cooled reference: obtain an applicable reaction-stage cold source with actual acid, alcohol, catalyst, medium and net ester/water outcome. Equilibrium conversion is not predicted. A cooled receiver is not evidence of a cooled reaction. |
| Acid ester hydrolysis | [A methyl/ethyl acetate HCl kinetic procedure](https://jrc.ac.in/working_folder/DOWNLOAD-D-9-283-672CFA88615F0.pdf) describes an acid-catalyzed aqueous net model but does not establish the required specifically cooled reaction-stage observation in the reviewed material. | Defer: obtain a matched cold reaction, aqueous acid formulation and endpoint; preserve ester identity, water provenance, aryl/lactone scope and stereochemistry. Do not confuse cold quenching or samples with the reaction temperature. |
| Ester saponification | The independently reported [ethyl acetate/NaOH kinetic study](https://isca.me/rjcs/Archives/v5/i11/8.ISCA-RJCS-2015-150.php) describes measurements at 25–50 °C, not 0 °C. | Defer a source-specific cooled confidence profile. Existing formal net graph gives **carboxylate + alcohol** and preserves its negative charge; the existing ionic-geometry boundary remains 2D-only. A separate acid work-up cannot be invented to obtain 3D. |
| Secondary alcohol oxidation | The [UCSB cyclohexanol/NaOCl/acetic-acid procedure](https://labs.chem.ucsb.edu/pettus/tom/courses/untitled%20folder/manual/Chem6BManual%28Fall09%29.pdf), Experiment 2, chills before and during addition, then removes the bath and stirs at room temperature for one hour. | Defer a *cooled-only* endpoint: this source does not establish that the measured reaction and product formation remained at 0 °C. The existing secondary NaOCl/acetic-acid model's ambient requirement remains; no blanket cold translation. |
| Primary alcohol oxidation / aldehyde stopping | [Organic Syntheses CV8P0367](https://www.orgsyn.org/demo.aspx?prep=CV8P0367) describes cold-controlled selective oxidation using a nitroxyl radical catalyst, buffered hypochlorite and a dichloromethane/water system. | Defer: it is useful direct evidence for a **different, catalyst/formulation-specific system**, not permission for the existing generic NaOCl net rule. The present engine does not model the TEMPO-like catalyst/buffer/phase-transfer roles or validate selective stopping. Do not silently add those reagents. |
| Aldehyde oxidation | Existing NaOCl further-oxidation graph reports a neutral acid; the inspected cold nitroxyl work discusses oxidation under separately specified conditions and additives. | Defer: obtain a matched aldehyde/oxidant, reaction-stage temperature and specific acid versus carboxylate/recovery contract. The neutral displayed graph is not measured solution speciation; do not silently acidify. |

Independent R8 negative fixtures check each displayed formal product, byproducts, atom identities, total charge and blocked embedding. Saponification retains `CC(=O)[O-]` for ethyl acetate rather than inventing acetic acid. Primary and secondary oxidation share a rule name but have separate stopping/condition assessments. These fixtures check the current modeled graph; they do not establish experimental conversion, isotope transfer, all lactones, all aryl esters, or every competing pathway.

## Eight admitted profiles (all version 1)

The registry is the backend authority. Here “dry” is a coarse non-capturing assumption, not proof of an actual measured solvent or zero water. Actual chemical structures, supported sites and all existing chemistry checks remain required.

| Profile | Supported scope and model conditions | Evidence and limitations |
| --- | --- | --- |
| `cooled-alkene-bromination-v1` | Screened eligible alkenes + actual Br2; dry/non-capturing assumption; no extra activation. | Existing cooled [bromination review](cooled-alkene-bromination-3d.md) and [Organic Syntheses example](https://www.orgsyn.org/demo.aspx?prep=CV2P0171). Source scope is narrower than the bounded graph scope; no exact temperature interval, general dry-solvent certification, full bromonium mechanism or selectivity is claimed. |
| `cooled-peroxyacid-epoxidation-v1` | Screened alkenes + actual neutral mCPBA; dichloromethane-reference compatible dry assumption; no additional activation. | [mCPBA report](reaction-lab-cooling-compatibility-v1.md), [source](https://doi.org/10.1081/SCC-120004069): near-zero source reference with addition controlled below 10 °C, not a validated continuous temperature range. The carboxylic-acid coproduct and existing stereochemical screens remain. |
| `cooled-perbenzoic-epoxidation-v1` | Actual perbenzoic acid + terminal styrene-type hydrocarbon scope, including bounded screened ring-alkyl variants; named chloroform-reference assumption, no extra activation. | [Perbenzoic report](reaction-lab-cooled-perbenzoic-phase2.md), [Organic Syntheses styrene-oxide example](https://www.orgsyn.org/demo.aspx?prep=CV1P0494), 0 °C reaction-stage observation. Variants are bounded inference, not individual experimental demonstrations. |
| `cooled-cyclohexene-pd-silica-v1` | Exact cyclohexene + H2, explicit reference; dry/metal selectors represent source-defined hexane and Pd/silica-A, not generic Pd/Pt. | [Batch 1](reaction-lab-cooling-batch1-r1-r2.md) and [JP2004250387A](https://patents.google.com/patent/JP2004250387A/en), [0087]: 5 wt% Pd/silica-A, hexane, 0 °C, 1.1 MPa H2, 15 min; pressure basis unspecified. GC endpoint is not complete conversion. No full surface mechanism. |
| `cooled-isobutylene-hcl-v1` | Exact isobutylene + actual HCl, explicit source reference; dry/non-capturing and no-extra-activation model. | [Batch 3](reaction-lab-cooling-batch3-r6-r7.md) and [RU2280636C1](https://patents.google.com/patent/RU2280636C1/en), example 2: 0 °C, product-medium tert-butyl chloride; no proof that every dry medium or ionic elementary mechanism applies. Neutralization/recovery are not simulated. |
| `cooled-isobutylene-os-peroxide-v1` | Exact isobutylene + H2O2, explicit OsO4/tert-butanol source reference; direct fractionation free-glycol endpoint, **not** aqueous release. | [R3 report](reaction-lab-cooled-dihydroxylation-r3.md), Milas–Sussman [p. 1303](https://doi.org/10.1021/ja01298a065): 6.62% peroxide reagent, 0.5% OsO4 stock, 0 °C overnight. Stock bases/actual water are not quantified; work-up is not simulated. |
| `cooled-crotonic-os-peroxide-v1` | Exact unconfigured crotonic acid + H2O2, explicit reference and water-recovery endpoint. | Milas–Sussman p. 1303: 6.3% peroxide, solution-catalyst cross-reference, 0 °C overnight; water recovery and chloroform extraction. Os stock cross-reference is an assumption, not restated source fact. New product stereo remains unassigned. |
| `cooled-cinnamic-os-peroxide-v1` | Exact unconfigured cinnamic acid + H2O2, explicit reference and distinct water-recovery endpoint. | Milas–Sussman p. 1303: 6.3% peroxide, equal-volume tert-butanol, solution-catalyst cross-reference, 0 °C overnight; unchanged acid filtered. Product stereo remains unassigned; source did not establish facial ratios. |

The named references are not input measurements. Products, H/halogen/peroxide maps and catalyst omissions are formal net bookkeeping, not proof of elementary isotope provenance. All calculators remain theoretical complete-conversion arithmetic, not source-yield forecasts. The cyclohexene, HCl and dihydroxylation profiles do not require a fabricated full mechanism. For the latter, no Os catalytic cycle is modeled. Source observations, fixed assumptions and unknowns are available in detached descriptors.

## All 24 existing reaction types

S = at least one bounded cooled profile; P = potentially supportable, not admitted; I = conflicts with the current specific profile; O = endpoint/output limitation. Conditional 2D is available only after the existing structure matcher succeeds. “Non-cooled 3D” denotes applicable representative models, not a promise for every substrate.

| # | Rule type | Cooled classification and remaining gate |
| --- | --- | --- |
| 1 | Hydrogenation | S: exact named cyclohexene/Pd-silica only; other catalysts/substrates P. |
| 2 | Bromination | S: bounded Br2 non-capturing net model; preserve anti/stereo and competing-capture screens. |
| 3 | Chlorination | P: Cl2-specific medium/additive, competing chemistry and stereo evidence remain. |
| 4 | Hydration | P: cold acid/water, endpoint, rearrangement and capture evidence outstanding. |
| 5 | Hydrohalogenation | S: exact isobutylene/HCl reference only; other HX/cold oxygen-spectator scope remains P/I. |
| 6 | Epoxidation | S: actual mCPBA and bounded perbenzoic models; other oxidants remain unapproved. |
| 7 | SN2 | P: separate cold aqueous-OH formulation/product review, site inversion and competition. |
| 8 | SN1 | P: cold water-solvolysis product evidence distinct from conductivity and E1 competition. |
| 9 | E2 | P: cold base/product/geometry and substitution competition unreviewed. |
| 10 | E1 | P: cold elimination endpoint and rearrangement/competition not established by ionization alone. |
| 11 | Alcohol oxidation | Primary O for selective stopping; secondary I under current ambient profile. |
| 12 | Aldehyde oxidation | I: cold formulation and neutral acid/carboxylate reporting remain unqualified. |
| 13 | Carbonyl hydrogenation | P: source-specific C=O reduction and competing unsaturation required. |
| 14 | Esterification | P: matched cold acid/alcohol model and equilibrium endpoint needed. |
| 15 | Ester hydrolysis | P: cold acid/water and release/site-specific scope needed. |
| 16 | Alcohol dehydration | I: current sulfuric-acid profile requires heated conditions; no cold dehydration inference. |
| 17 | Alcohol substitution | I: bounded HX substitution conditions remain independently validated; no generic cold allowance. |
| 18 | Ester saponification | P: cold evidence/conditions; ionic 3D O under present output policy, carboxylate retained. |
| 19 | Alkyne hydrogenation | P: active catalyst, two-H2 endpoint and competing reduction must be independently matched. |
| 20 | Alkyne partial hydrogenation | P: cold Lindlar source substrate has ester/nearby alcohol outside current matcher; do not infer stopping. |
| 21 | Alkyne halogenation | P: Br2 and Cl2, one/two equivalents, media and first-stage geometry require separate reviews. |
| 22 | Alkyne hydrohalogenation | I under current ambient ionic model; radical evidence does not qualify ionic HX. |
| 23 | Alkene dihydroxylation | S: three exact Os/H2O2 profiles; fumaric acid/overoxidation and other substrates remain excluded. |
| 24 | Polymerization model | O: finite net graph only; no cold initiation, conversion or bulk polymer prediction. |

The [earlier 25-case matrix](../tests/test_cooling_profiles_v1.py) separately covers primary and secondary alcohol oxidation, in addition to all 24 rule names. Its diagnostics exercise cold 2D/evidence/3D gates and matching reference conditions. It is not a substitute for independent experimental validation. Earlier R4/R5 and R6/R7 reviews are preserved; **reviewed but deferred is not implemented**.

## Lifecycle, interfaces and verification

The new backend audit fixtures test all eight actual profile IDs, detached provenance, representative matching, 2D diagram, mapped element/charge conservation, 3D output, theoretical calculator context, version conflicts, wrong solvent/activation, unsupported fields and wrong-path selection. Existing per-profile suites provide additional product, stereo, mechanism and API coverage. The new R8 boundary suite checks six cases independently.

The separate [browser lifecycle suite](../tests/cooling-batch4-browser.cjs) runs against an isolated localhost service, not the frozen benchmark. It tests delayed 3D responses after temperature, solvent, catalyst, named-profile removal and reagent changes across all eight profiles at desktop size; the isobutylene/HCl profile repeats all five at 320 px. A populated product/measurement/calculator scenario and a delayed mapped SN2-diagram scenario are additionally checked. Profile removal for an implicitly eligible older profile can legitimately fall back to its existing generic model; old output is still invalidated and newly assessed. Cross-path profile references are checked at the backend; replacing one valid named profile with a different valid one was not independently exercised as a delayed browser race.

Final verification:

- **4,364 automated regression tests passed:** 2,181 Python and 2,183 JavaScript, including four new Python audit methods with multiple independent subcases. All 4,360 previous test cases remain.
- TypeScript and the production build passed. The existing large-bundle and third-party directive warnings remain.
- The frozen benchmark was rerun: **347 of 347 per-case results match the saved baseline**, with totals unchanged at 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported and one pre-existing incorrect-result classification. The frozen inputs and expectations were not changed.
- Desktop 1440 px and mobile 320 px HCl lifecycle checks passed for five changes while a valid run response was delayed. Desktop checks repeated these changes across all eight profiles, and obsolete saved versions were rejected for all eight; for the two exact acid-diol cases no eligible option remained. The populated product/measurement/calculator and delayed SN2-diagram/mechanism checks passed. No uncaught page errors or page overflow were observed in the checked views. This does not establish every possible browser or timing interleaving.
- The browser suite is an explicitly invoked integration test, not part of `node --test tests/*.test.mjs`. RDKit emits warnings for deliberately invalid negative-control structures during the Python suite; the suite itself passes.

No changes to layout, curated examples, reaction rules, profile permissions or benchmark were made in Batch 4. Existing uncommitted Batch 2/3 work was preserved.

## Remaining work and beta recommendation

The remaining chemistry backlog includes independently validated cooled alkene/alkyne Cl2 and Br2 formulations/stages, SN1/SN2/E1/E2 source-specific outcomes and competition, Lindlar substrate compatibility, full alkyne/carbonyl reductions, hydration, ionic alkyne HX, alcohol substitution, all six R8 categories, diol overoxidation and unsupported configured stereochemistry. Do not generalize one catalyst, reagent, solvent or profile to a family. No yields, rates, ratios or laboratory safety are predicted.

**Recommendation:** suitable for a carefully labeled *limited educational beta* only after the owner reviews this report, validates deployment/security configuration and explicitly approves publishing. The report and finite fixtures cannot certify all possible inputs or experimental chemistry. Clearly show theoretical-model limitations, retain missing-condition and 2D-only disclosures, and do not describe the product as general reaction prediction. This recommendation is not authorization to push, merge or deploy.
