# Cooling Phase 6 — Alkene hydrogenation evidence gate

2026-10-26. This increment covers **alkene + actual H₂ only** under the existing Pd/Pt teaching model. It does not cover Lindlar, complete alkyne reduction or carbonyl hydrogenation. Local only; no push, merge or deployment.

## Decision

**The evidence review and safeguard increment are complete. No cooled alkene-hydrogenation profile was admitted; cooled 3D remains deferred.**

Cold hydrogenation is experimentally possible. The obstacle is not a chemically impossible product or a wrong C=C reduction rule. The strongest applicable experiment identifies catalyst/support, solvent and H₂ pressure that the current broad selectors cannot distinguish. The approved cooling plan explicitly says to defer if those facts cannot be represented, rather than guess or redesign controls without approval.

Eligible conditional 2D products, bond-change highlighting and theoretical reaction calculations remain available. Existing supported non-cooled 3D continues to work. There is no new reaction, catalyst, temperature simulation or claim of experimental conversion/selectivity.

## 1. Evidence and its limits

### Direct cold primary experiment: JP2004250387A

[*Method for catalytic hydrogenation reaction using palladium carried by silica gel with dual pore system*](https://patents.google.com/patent/JP2004250387A/en), published 2004-09-09. [Original 17-page Japanese PDF](https://patentimages.storage.googleapis.com/27/d6/88/c4e424165867a6/JP2004250387A.pdf).

Original printed **pp. 14–15**, paragraphs **[0087]–[0092]**, were visually inspected and cross-checked with the translated HTML. Example 1 hydrogenates cyclohexene in hexane at **0 °C**, **1.1 MPa H₂**, for **15 minutes**, using pretreated supported Pd catalyst A. Filtration and GC identify cyclohexane; the reported 9.7% is an analytical endpoint, not an isolated preparative yield. Reference Example 1 repeats the operation with commercial **5 wt% Pd/C**. Table 1 labels the reference row “2,” unlike the preceding prose's “1”; no reference-catalyst yield was inferred from that table. The PDF's reaction temperature is 0 °C despite awkward translated “heated” wording. Catalyst preparation temperatures are not reaction temperatures.

**Applicability inference:** this is useful direct cold alkene/H₂ product evidence, not independent replication or permission for every metal, support, solvent or pressure. It supplies no distant-stereo or multifunctional scope for this increment. A modest conversion does not invalidate the identified net product, and complete conversion is not an evidence-gate requirement.

### Historical platinum lead: not an independently reviewed cold profile

[Farkas and Farkas, *The Catalytic Interaction of Ethylene and Heavy Hydrogen on Platinum*](https://doi.org/10.1021/ja01268a006), JACS **60**, 22–28 (1938). The publisher record was located, but the original full PDF was inaccessible. **Its complete experimental section was not read.**

An accessible archival [NBS evaluated review](https://www.govinfo.gov/content/pkg/GOVPUB-C13-a2e38560dc075a53901bb67f90b351be/pdf/GOVPUB-C13-a2e38560dc075a53901bb67f90b351be.pdf), Horiuti and Miyahara, *Hydrogenation of Ethylene on Metallic Catalysts*, NSRDS-NBS 13 (1968), section **5.1.3**, printed **p. 19**, Table **10**, points to cold ethene/platinized-Pt-foil kinetic measurements and the Farkas paper. That is a retrieval lead, not a substituted full-primary-source review. Foil/gas partial-pressure and isotope/para-H₂ experiments cannot silently become a generic liquid-medium Pd/Pt profile.

### Other leads screened out

- [Felpin and Fouquet, DOI 10.1002/chem.201001377](https://doi.org/10.1002/chem.201001377): the accessible abstract describes in-situ Pd/C at **25 °C**, not a cold reaction. Transfer-hydrogenation variants also differ from the actual-H₂ input model.
- The cooling plan's E12, [Staiger et al., DOI 10.1002/cctc.202001121](https://doi.org/10.1002/cctc.202001121), concerns distinct colloidal-Pd/phosphane formulations and alkyne semi-hydrogenation. Abstract-level cold evidence is not transferred to the present alkene/current-metal model. No complete-paper review or approval is claimed here.
- Cold catalyst preparation, a cooling step before a warm reaction, and separately ligated Rh/Ir systems do not qualify the current reaction. No new reagent family was introduced to fit a source.

## 2. Why no profile was registered

| Gate | Finding |
| --- | --- |
| Actual cold reaction-stage product | Established for the narrowly documented cyclohexene/Pd experiment. Cooling itself is not an impossibility flag. |
| Existing graph endpoint | Cyclohexene → cyclohexane is already representable and passes public matching, mapped diagrams and independent non-cooled 3D checks. |
| Catalyst identity | `Metal Catalyst (Pd/Pt)` does not select commercial Pd/C versus prepared Pd/silica, Pt foil, catalyst pretreatment or loading. |
| Medium | `Dry / no water` is not an explicit hexane formulation. Broad solvent classes are not interchangeable validated experiments. |
| Hydrogen conditions | Actual H₂ identity is checked, but pressure is not represented by a supported field or an expressly selected, versioned profile assumption. |
| Stereochemical scope | The identified simple substrate does not validate new stereocenter assignments, cold face selection, or broader spectator retention. |
| Competing chemistry | Current isolated-alkene, reducible-group, remote-alcohol and stereo checks must remain; cooling cannot establish selective mono-reduction. |
| Public contract | Legacy cooled hydrogenation intentionally exposes conditional 2D and blocks run. A registry name alone would not constitute consistent backend/frontend approval. |

These are applicability/representation limits, not demands for a universal kinetic model, high isolated yield or experimentally perfect selectivity. Numeric pressure/temperature controls are not inherently necessary: a clearly selected, documented named model can carry reviewed assumptions. **No such catalyst-specific model is currently selected by these generic controls.** Silently assigning it would conflate different inputs.

To revisit the gate, first approve how a smallest catalyst-specific profile would expose its catalyst/support, medium and H₂-pressure assumptions without pretending they are user-entered or measured. Then validate the directly evidenced structural scope and its confidence/run contract. Broader substrate classes require their own applicability review. Do not borrow Lindlar, alkyne or carbonyl evidence, or relabel cooled as ambient to unlock output.

## 3. Scoped changes

Only one production value changed: `COOLING_LIMITATIONS["Hydrogenation"]` in `server/reaction_temperature_profiles.py`.

The explanation now acknowledges real cold evidence, identifies the missing catalyst/support–solvent–pressure distinction, states that no current selector combination qualifies cooled alkene-hydrogenation 3D, and discourages switching temperature merely to unlock output. It reaches match, diagram, calculator context and the existing UI through unchanged serialization.

**No permissions, registry entries, reaction rules, atom mapping, product generation, mechanisms, stereochemistry, frontend code, styles, layouts or Calculators changed.** The registry and frontend mirror still have three existing profiles across two reaction types: Br₂ addition, mCPBA epoxidation and bounded perbenzoic-acid epoxidation.

Two separate v1 suites were added, outside the frozen benchmark and curated examples:

- `tests/test_cooled_hydrogenation_phase6.py`: **16 tests**.
- `tests/cooled-hydrogenation-phase6.test.mjs`: **10 tests**.

No pre-existing test or expectation was edited. These independently specified net-product fixtures are **preservation checks, not newly approved experimental cold scope**.

## 4. Verified chemistry and confidence contracts

- Ethene, longer/branched alkenes, cyclohexene, a screened remote alcohol, distant specified centers, E/Z reactants and a product with an unassigned new center retain their existing net structures. Both input orders are exercised.
- The selected C=C changes from double to single; actual H–H breaks; one mapped reagent H attaches to each selected carbon. All represented atoms and total charge are conserved. There is no byproduct or consumed catalyst.
- Unaffected compatibility contracts remain verified. Distant physical configuration is retained, including the independent R→S CIP relabeling case. Reacting E/Z is consumed; an unselected E/Z bond stays specified. New centers remain unassigned.
- Separate isolated C=C sites retain independent one-H₂ options and atom identities. Equivalent connectivities are not newly deduplicated or claimed as experimental site selectivity.
- Conjugated/cumulated systems, competing alkynes/carbonyls, unvalidated ethers/aromatics/halides, near specified centers and small-ring controls remain rejected for their existing specific reasons. A display name cannot replace actual H₂, and isotope substitution remains unsupported.
- Every cooled option remains conditional 2D with no qualified model ID and no 3D permission. Generic solvent choices, alternate catalysts, borrowed profile IDs, fabricated metadata and unsupported extra pressure/support fields cannot grant permission.
- Authenticated public match/diagram endpoints still provide the conditional net result; run rejects cooled inputs before embedding, even after a successful ambient request using the same option ID.
- Conditional 2D atom links agree with the independently exercised **non-cooled** theoretical 3D products. That correspondence is not evidence of a cooled experiment.
- Hydrogenation stays **net transformation only**: `mechanism: null`, mapped mechanism unsupported. No resolved catalyst surface intermediates, syn-face assignment, energies or cold rates were fabricated.
- One H₂ per selected site, exact H₂ molar mass 2.016 g/mol, input-order independence, limiting reactants and target amounts are checked. Calculator values remain complete-conversion theoretical upper bounds, not actual yields, catalyst-activity or experimental-selectivity predictions. Cold confidence is retained in copied calculation context.

## 5. Verification

Fresh baseline: **2,112 Python + 2,143 JavaScript = 4,255 passing tests**.

Final full-suite result: **2,128 Python + 2,153 JavaScript = 4,281 passing tests**, no failures or skips. All 4,255 existing tests remain, with **26 additions**. The focused Phase 6 suites also pass independently.

- **TypeScript and production build pass** (`tsc && vite build`). Existing third-party `use client`/large-bundle warnings remain; no new build error appeared.
- The frozen **347-case audit is deeply identical before/after**, including its recorded production hashes: **155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported, one pre-existing incorrect result**. Hydrogenation stays **11/14 (78.6%)**, with two separate correctly rejected controls. No cooled rows were inserted or relabeled.
- The separate pinned **condition companion 1.0.0** is unchanged: 40/53 structural matches, zero evidence-qualified condition-complete/generated cases and five correct controls. Its explicitly unvalidated overlay still observes 33 model generations (10 dihydroxylation, 12 alkyne X₂, 11 alkyne HX); those are not approved cooling coverage. Both runs report no framework failures.
- A **100-context public match/diagram comparison across all 24 reaction types** is identical after allowing only the intended Hydrogenation limitation-text substitution. Exactly one cooled-Hydrogenation context changes, in 12 serialized string locations. The other 99 contexts are exactly equal; no product, mapping, confidence permission or mechanism changed.
- Production-build Chrome checks pass at **1440 px and 320 px**: conditional diagrams and the catalyst/support–pressure explanation render; cooled Compare/3D/run remain disabled; no false mapped mechanism is displayed; the ethane calculator returns **0.03007 g from 0.001 mol** as a theoretical amount; independently selected ambient ethane/cyclohexane 3D works. Temperature changes clear the product and calculator output. A deliberately delayed ambient response does not resurrect stale 3D after cooling. No horizontal document overflow or page errors were observed.
- Existing unchanged browser regressions pass for cooled Br₂, mCPBA and perbenzoic profiles, and for the cooled Cl₂/SN2 boundaries. This UI/UX Pro Max quality-control pass was limited to disabled-state clarity/responsiveness; it did not prescribe a new design. Expanded confidence text is still lengthy on small screens; its existing disclosure/layout was not reworked in this chemistry increment.
- Preservation hashes cover **491 pre-existing files** captured before Phase 6. Only `server/reaction_temperature_profiles.py` differs. Restoring its single old Hydrogenation string in memory reproduces the exact original file hash. Existing tests, frozen and companion inputs, all other captured production code and reports are unchanged. The two suites and this report are additions. Tracked and added-file whitespace checks pass.

Local run evidence, logs and screenshots are under `/private/tmp/molecule-cooling-phase6.7M9x0z/`; this temporary directory is not part of the benchmark or application. The isolated localhost QA server was stopped after verification. No existing development server was stopped.

No unexpected chemistry regression was found. The finite tests and unchanged audit do not establish universal chemistry correctness, and the pre-existing benchmark defect remains separate from this scoped review.

## 6. Stop point

This completes **Cooling Phase 6: alkene hydrogenation evidence review/safeguards only**. Positive cooled 3D admission is explicitly deferred at the representable-profile gate. Existing chemistry is not disabled by this increment.

No Lindlar/complete alkyne, carbonyl, SN1/E1/E2, Phase 7 or further cooling work is started. Nothing is pushed, merged or deployed; Render and frozen Beta v1 are unchanged.

Reminder: Cooling Phase 3 remains paused pending Milas–Sussman (1936), printed **pages 1303 and 1304**. Page 1302 has been supplied.
