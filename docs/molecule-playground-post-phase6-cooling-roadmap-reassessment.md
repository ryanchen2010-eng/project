# Post-Phase 6 cooling roadmap reassessment

26 October 2026 · Planning report v1 · **Awaiting approval**

**PLAN ONLY.** This report does not register a profile, authorize 3D, change production code or the UI, edit tests or benchmark inputs, or publish anything. The original nine-phase plan and historical reports are retained unchanged.

## 1. Recommendation

Choose **C: a narrowly scoped hybrid**. Implement a small, behavior-preserving shared **named condition-profile contract** first. Then revisit one deferred, directly evidenced chemistry profile at a time, while obtaining missing sources separately. Do not continue mechanically through Phases 7–8 with the same underspecified selectors, and do not build a general experimental-reaction simulator.

The repeated gates are **not evidence that the project is scientifically unachievable**:

- Alkene hydrogenation has a directly documented cold product that the existing graph engine can represent. Its dominant remaining problem is representing and deliberately selecting the particular conditions, followed by bounded applicability review.
- Dihydroxylation has both a real missing-source requirement and a mismatch between the reported recovery and the engine's particular aqueous-release assumption.
- Chlorination has direct cold experimental leads, but formulation, competing chemistry and applicable product/stereo evidence remain intertwined. Merely adding a solvent dropdown will not settle them.
- SN2 has cooler aqueous evidence, but the exact formulation/product applicability remains incompletely resolved. This is not evidence that cooler aqueous SN2 is impossible or that only polar-aprotic solvents permit it.
- Several other cases have genuine endpoint or output-policy limitations that condition metadata alone cannot repair.

Current positive cooling coverage remains **three profiles across two of the 24 rule types**, not six completed chemistry expansions. The other 22 types have no admitted cooled profile. This is a scope inventory, not an overall website-quality score or a prediction of experimental success.

**Single best next implementation phase:** revised **R1 — Shared Named Condition Profiles and Provenance, without new cooled chemistry**. Its explicit acceptance criteria are at the end of this report.

## 2. Review basis and verification limits

Read the complete [comprehensive plan](molecule-playground-comprehensive-cooling-plan.md), [Phase 1](reaction-lab-cooling-registry-phase1.md), [Phase 2](reaction-lab-cooled-perbenzoic-phase2.md), [Phase 3 including its revisit](reaction-lab-cooled-dihydroxylation-phase3.md), [Phase 4](reaction-lab-cooled-chlorination-phase4.md), [Phase 5](reaction-lab-cooled-sn2-phase5.md) and [Phase 6](reaction-lab-cooled-alkene-hydrogenation-phase6.md) reports. Also checked the preceding [bromination](cooled-alkene-bromination-3d.md) and [mCPBA/matrix](reaction-lab-cooling-compatibility-v1.md) records.

Inspected current definitions, condition normalization/assessment, cooling registry, guidance, public run gates, relevant product rules and frontend condition/guidance transport. Fresh read-only public-function diagnostics exercised all **24 types / 25 model fixtures**, including separate primary/secondary alcohol oxidation: matching, 2D diagrams, cooled generation attempts and non-cooled reference generation. Additional probes checked actual perbenzoic cooling, aqueous heated alcohol substitution and unrecognized hydrogenation condition fields. These are finite diagnostics, not a new benchmark or exhaustive chemistry validation.

The Phase 6 patent's relevant original Japanese pages **14–15** and translated experimental paragraphs were rechecked. The supplied Milas–Sussman page **1302** was inspected; pages **1303 and 1304 are still missing**. Other literature access levels are inherited from the cited reports unless explicitly stated otherwise; bibliographic leads are not promoted to full-paper reviews.

The **4,281-test baseline** is the completed Phase 6 result, corroborated by its saved logs: 2,128 Python and 2,153 JavaScript tests. This planning review did **not** rerun the full suite, TypeScript, build or browser automation. No implementation changed that would warrant claiming a new regression result. No deployment or live service was accessed.

## 3. Original phases versus actual completed scope

| Original phase | Completed increment | Still incomplete / deferred |
| --- | --- | --- |
| 1 — Registry/contracts | Consolidated existing Br₂ and mCPBA profiles; legacy cooled normalization and frontend parity. | It did not create a general formulation/pressure/thermal-history input model. |
| 2 — Perbenzoic epoxidation | Added a bounded actual-perbenzoic, terminal styrene-type profile with a disclosed chloroform-reference assumption. | Other peracids and broader perbenzoic substrate classes remain unapproved. |
| 3 — Os/H₂O₂ dihydroxylation | Evidence review, revisit and safeguard fixtures; conditional 2D retained. | **Positive profile not implemented. Full source and product-release applicability unresolved. Pages 1303–1304 required.** |
| 4 — Halogen additions | Reviewed **alkene Cl₂ only**, improved explanations and added safeguards; no positive cooled Cl₂ profile. | Original later subincrements for **alkyne Br₂ one-equivalent and two-equivalent endpoints were not completed**. Alkyne Cl₂ is a separate evidence/stereo decision, also outstanding. |
| 5 — Substitution/elimination | Reviewed **hydroxide SN2 only**, improved explanations and added safeguards; no positive cooled SN2 profile. | **Water-based SN1 was not completed. E1/E2 received no dedicated cooled product-evidence review or profile.** Existing negative/regression checks do not complete those reviews. The plan never promised automatic paired elimination approval. |
| 6 — Catalyst-specific reductions | Reviewed **alkene/H₂ only**, improved explanations and added safeguards; no positive cooled reduction profile. | **Lindlar partial and active-metal complete alkyne reduction remain separate unstarted increments.** Carbonyl hydrogenation needs its own additional review. |
| 7 — Acid-mediated candidates | Not started. | Hydration, alkene/alkyne ionic HX and narrow alcohol/HCl substitution, each separately. |
| 8 — Ester/oxidation boundaries | Not started. | Esterification/hydrolysis/saponification research; separate oxidation evidence reassessment, not blanket permission. |
| 9 — Consolidated acceptance | Not completed. | Must follow admitted profiles and explicitly classify exclusions; 24/24 cooled 3D is not its target. |

Use “review/safeguards complete; profile deferred” for Phases 3–6. Do not describe all of their original multi-increment scope as delivered. The latest narrower user approvals correctly constrained what was attempted; that does not cancel the original backlog.

## 4. What the current condition model actually represents

| Existing input | Actual scope | Missing distinction |
| --- | --- | --- |
| Molecular reactant/reagent inputs | Validated structures, including actual H₂, HX, X₂, peroxide/peracid and supported salts. | A molecule's identity alone does not describe its solution formulation, concentration, buffering, carrier or catalyst support. |
| `catalyst` | Unset, none, acid, generic Pd/Pt metal, Lindlar, Os-based, radical. | Exact metal/formulation/support, poisoning/ligands, preparation state and material additional components. |
| `solvent` | Unset, dry, aqueous-protic, ethanolic-protic, polar-aprotic. UI also has a specific secondary-NaOCl/acetic-acid transport alias. | Exact solvent or mixture, water activity, buffers, chloride additives and phase behavior. tert-Butanol is not ethanol; dry is not a solvent identity. |
| `temperature` | Unset, cooled, ambient, heated. | Numerical reaction versus bath temperature, observed point versus validated interval, addition/hold/warming history. |
| Hydrogen conditions | **No pressure setting exists**, in backend accepted condition fields or the frontend. | Pressure value, unit and basis, actual supply/uptake and catalyst-contact assumptions. Stoichiometric H₂ counts are not pressure. |
| `oxidationStage` / `additionStage` | First/further oxidation and one/two X₂ or HX endpoint assumptions. | Actual oxidant activity, available equivalents, stopping, subsequent conversion and experimental yield. |
| `workup` | Unset or an explicitly assumed aqueous diol-release endpoint. | Alternative product-release evidence, acid work-up/speciation and separation of release from isolation. It is not a work-up simulator. |
| Guided Conditions | Specific implementations for secondary oxidation, Lindlar and cooled perbenzoic assumptions; primary oxidation has no resolving profile. | A reusable, explicitly selected exact-profile reference and common descriptor/provenance contract. |

### Important implementation asymmetry

`_conditions()` rejects invalid values for known keys but records unknown key **names** in `unsupported_fields`; their values are not accepted as modeled conditions. Consumers differ in how they handle those names. Reviewed cooling validators and alkyne guards reject them; legacy non-cooled hydrogenation still returns an aligned teaching-model assessment and can generate its ordinary conformer without using them.

A fresh probe supplying `pressure`, `catalystSupport` and `solventIdentity` confirmed that behavior. The same cooled request remains blocked. Thus neither the plan nor the UI should claim these fields are already understood or that all legacy unknown-input behavior is uniformly fail-closed. This is a contract-consistency risk, **not a demonstrated cooled-permission bypass**. Do not silently rewrite all legacy behavior in the proposed foundation phase; separately scope broader hardening if desired. Any new explicit profile-selection contract must reject unknown/conflicting selections on every route.

There is a second asymmetry: non-cooled legacy/SN responses may omit explicit `canRun`, while cooled adapters supply it. For legacy hydrogenation the cooled evidence serializer currently hardcodes no 3D. A new positive registry name alone would therefore be insufficient; pathway-specific base validation, overlay, serialization and run must agree. Normalize the new profile contract without globally replacing unrelated rule assessments.

## 5. Repeated gates: science, representation and policy

Evidence availability, chemical applicability, implementation capability and depiction policy are separate questions. An inaccessible paper is an **evidence-access gap**, not proof that chemistry is unknown to science. An omitted full mechanism is not automatically a reason to prohibit an independently valid net-product conformer. Conversely, a correct graph or successful embedding is not evidence of an experimental reaction.

| Deferred candidate | Evidence position | Condition-model limitation | Genuine chemistry/output boundary | Reassessment |
| --- | --- | --- | --- | --- |
| Os/H₂O₂ dihydroxylation | Page 1302 is now available; a page-1303 excerpt was previously recovered, not the complete experimental pages. | No explicit tert-butanol/peroxide/Os formulation; only the particular aqueous-release assumption. | Further oxidation and whether free diol is appropriately reported; broader stereochemical/substrate scope. | **Mixed source + representation + endpoint gate.** A profile field alone is insufficient. |
| Cl₂ alkene chlorination | Prior report records direct cold examples with materially specific media/additives; full historical studies and some product/stereo detail remain missing. | Generic dry/none cannot express chloride additives, capture conditions or the actual formulation. | Radical/substitution, solvent capture and stereo applicability cannot be inferred absent relevant evidence. | **Mixed formulation + evidence + chemistry gate.** Not simply “chlorine is unsupported.” |
| Hydroxide SN2 | Cooler aqueous methyl-halide work exists; complete relevant source/formulation and product applicability remain unresolved. | No buffered aqueous-OH identity/activity profile, distinct from a generic aprotic choice. | Competing nucleophiles, elimination/cyclization and substrate-dependent stereo/competition. | **Evidence/applicability + formulation gate.** Aqueous solvation is not an SN2 prohibition. |
| Alkene/H₂ hydrogenation | Direct cold parent-substrate/product experiment and a commercial-Pd/C reference exist. | No selectable exact catalyst/support/solvent/pressure model. | Extrapolation to other catalysts, substrates and competing reductions still needs review. | **Predominantly representation/approval-policy gate for the narrow documented parent.** Not missing evidence that any cold alkene hydrogenation can occur. |

### 5.1 Phase 3: update the access record without inventing the missing pages

The uploaded original **p. 1302** describes peroxide in tert-butanol, OsO₄ activation, reagent preparation and catalyst behavior. It also reports further oxidation in some cases, including an acid endpoint from cyclohexene. Its table is not a table of independently confirmed cold reaction conditions for every substrate. The old revisit report's “1302 unavailable” entry predates the upload; this new report records that update without rewriting history.

The earlier **p. 1303 excerpt** reports a cold isobutylene/glycol experiment and fractionation, not the current engine's specifically named aqueous release. Full pages **1303 and 1304** are still required to resolve context, preparation/release details and other experiments. The reagent percentage in the supplied preparation page also must not simply be assumed identical to an indexed excerpt's formulation.

The smallest plausible future scope remains a reviewed non-stereogenic endpoint first. Do not demand a complete mapped Os catalytic cycle merely to show an eligible free-diol net product, but do not turn formal peroxide O/H bookkeeping into elementary isotope provenance. If the full source supports free-diol reporting without the current release assumption, that requires a separately reviewed endpoint contract—not a hidden bypass or a misleading “aqueous work-up” label.

### 5.2 Phase 4: distinguish additive-specific evidence from absent generic evidence

The [Phase 4 report](reaction-lab-cooled-chlorination-phase4.md) identifies [WO2026128662A1](https://patents.google.com/patent/WO2026128662A1/en), paragraphs [0083]–[0089], as a cold Cl₂ lead using specified brine/quaternary-ammonium/chloride formulations. The no-NaCl example still contains another additive; it is not a no-additive control. That source was not newly read in full here. Missing table and historical-paper access limits remain as recorded.

A named model could represent a reviewed formulation, but a text label cannot establish how additives affect competing pathways or validate an unmeasured stereochemical result. Retrieve and assess the relevant product/condition evidence before enabling. Ordinary Br₂ approval is not transferable to Cl₂, nor alkene Cl₂ evidence to alkyne Cl₂.

### 5.3 Phase 5: use an appropriate evidence standard for a theoretical tool

The [USGS author record](https://pubs.usgs.gov/publication/70028000) and [2005 paper](https://doi.org/10.1007/s10874-005-1904-0) are leads for aqueous methyl-halide chemistry at cooler temperatures, not blanket cold/aprotic hydroxide scope. The complete relevant formulation/product text still matters; the previously noted buffer-value discrepancy remains unresolved.

The accessible [1977 primary study](https://www.jstage.jst.go.jp/article/jnst1964/14/5/14_5_370/_article/-char/en) discusses both physical dissolution and hydrolysis. Its overall temperature span must not be treated as proof that every depicted product trace was measured at the coldest point. The prior full-text review distinguishes those observations.

An isolated high-yield preparation is **not mandatory** for every theoretical SN2 profile. Directly applicable kinetic/product-analysis evidence can suffice when the endpoint, formulation and inference limits are clear. Do not reject a bounded methyl model merely because it is slow, aqueous or lacks preparative isolation. Equally, do not turn solubility measurements or a broad abstract into unverified product/stereo scope.

### 5.4 Phase 6: what JP2004250387A actually supplies

Rechecked [translated experimental text](https://patents.google.com/patent/JP2004250387A/en) and original pp. 14–15, [0087]–[0092]. Example 1 identifies cyclohexane from cyclohexene in hexane at **0 °C**, **1.1 MPa H₂**, after **15 minutes**, using pretreated **5 wt% Pd on dual-pore silica catalyst A**. Its reported analytical endpoint is **9.7%**, not an isolated yield or proof of completion. [0090] substitutes commercial **5 wt% Pd/C** under the same operation. Table 1's reference numbering disagrees with that prose; do not transfer catalyst A's yield to Pd/C. Catalyst-preparation heating is not the substrate reaction temperature. No pressure-basis conversion is justified where the source does not specify gauge versus absolute.

**Consequence for our software:** the graph and a cold parent endpoint exist; the present UI does not select either exact formulation. It also cannot state whether a solvent or H₂ pressure is a source reference, an accepted model assumption or a user-entered value. The specialized silica catalyst, commercial Pd/C and unspecified Pt are **not interchangeable permissions**. Broad patent claim ranges are not tested windows.

The next scientifically reasonable target is a separately reviewed, expressly selected narrow reference model, not “all Pd/Pt + cooling.” High conversion, a full surface mechanism and a pressure/kinetics simulator are not prerequisites for a static net conformer. Relevant catalyst/formulation distinctions and honest applicability are prerequisites. The source's other substrate chemistry must not bypass existing competing-carbonyl restrictions.

### 5.5 Correct the inconsistent threshold

Phase 2 already permits a named **chloroform-reference net assumption** rather than an experimentally entered solvent. Its checked [styrene-oxide procedure](https://www.orgsyn.org/demo.aspx?prep=CV1P0494) supplies a cold precedent; software fixtures do not independently prove all admitted variants experimentally.

It would be unnecessarily restrictive to require every later profile to have new numeric controls while accepting disclosed named assumptions for epoxidation. It would also be unsafe to infer specialized conditions silently from a generic metal or dry selector. Adopt one consistent standard:

1. Traceable, sufficiently applicable reaction/product evidence.
2. Independently reviewed existing net chemistry and proposed structural scope.
3. Explicitly selected named assumptions for material unentered conditions.
4. Clear distinction between observations, model assumptions and unknowns.
5. No unsupported stoichiometric participants, products or stereochemistry.
6. Backend revalidation and honest depiction/output limits.

Use this standard for future additions and document it for existing profiles. It is neither a retrospective automatic expansion nor a reason to disable current approved behavior. Depiction confidence remains distinct from experimental certainty; any separate conditional-3D viewing policy would require its own approval and is not proposed as a shortcut here.

## 6. Complete 24-type inventory

**Legend:** S = admitted bounded cooled profile; P = potential, unapproved; I = conflicts with the current specific profile; O = endpoint/output capability outside scope. Categories can coexist. “2D” below means an eligible **conditional net preview**, not an asserted experiment. All existing structure/site restrictions still apply. Reference 3D means representative non-cooled settings can generate a theoretical main-product conformer, not every substrate or setting.

| # | Existing rule type | Current cooling | Existing views |
| --- | --- | --- | --- |
| 1 | Hydrogenation | P; no admitted cold model | Cooled 2D only; reference alkane 3D. |
| 2 | Bromination | S, actual Br₂ bounded model | Cooled 2D + main dibromide 3D. |
| 3 | Chlorination | P; no admitted cold model | Cooled 2D only; reference dichloride 3D. |
| 4 | Hydration | P | Cooled 2D only; qualified acid/water reference 3D. |
| 5 | Hydrohalogenation | P; oxygen/HCl subprofile I | Cooled 2D only; bounded non-cooled HX 3D. |
| 6 | Epoxidation | S for exact mCPBA and bounded perbenzoic; other peracids P | Cooled 2D/3D only within those profiles; wider reference peracid scope is not cold approval. |
| 7 | SN2 | P | Cooled 2D and mapped conditional mechanism; non-cooled alcohol 3D. |
| 8 | SN1 | P; dedicated review outstanding | Cooled 2D and mapped conditional mechanism; non-cooled alcohol 3D. |
| 9 | E2 | P; dedicated cold product review outstanding | Cooled 2D and mapped conditional mechanism; reference alkene 3D. |
| 10 | E1 | P; dedicated cold product review outstanding | Cooled 2D and mapped conditional mechanism; reference alkene 3D. |
| 11 | Alcohol oxidation | Primary O; secondary I | Primary aldehyde stage 2D only at every temperature. Qualified secondary ketone has reference 3D, not cooled 3D. |
| 12 | Aldehyde oxidation | I | Cooled 2D only; ambient/unset neutral-acid reporting 3D, not solution-speciation proof. |
| 13 | Carbonyl hydrogenation | P; separate review outstanding | Cooled 2D only; screened non-cooled alcohol 3D. |
| 14 | Esterification | P | Cooled 2D only; reference ester 3D. |
| 15 | Ester hydrolysis | P | Cooled 2D only; reference main neutral product 3D, other products in 2D. |
| 16 | Alcohol dehydration | I | Cooled 2D only; current heated sulfuric-acid net model 3D. |
| 17 | Alcohol substitution | I; narrow HCl research candidate | Cooled 2D only; some heated primary/ambient tertiary reference 3D. Secondary/stereo/oxygen cases can remain conditional even non-cooled. |
| 18 | Ester saponification | P for cold net chemistry; O for present ionic 3D | Carboxylate equation 2D; non-cooled run can return `2d-only`. Cold run remains blocked. |
| 19 | Alkyne hydrogenation | P; separate review outstanding | Cooled 2D only; qualified two-H₂ non-cooled alkane 3D. |
| 20 | Alkyne partial hydrogenation | P; separate review outstanding | Cooled 2D only; qualified non-cooled H₂/Lindlar cis/Z net 3D. |
| 21 | Alkyne halogenation | P, separately by halogen and stage | Cooled 2D only; some non-cooled Br₂ one/two and Cl₂ two-equivalent 3D. First-stage Cl₂ remains conditional. |
| 22 | Alkyne hydrohalogenation | I under current ambient ionic profile | Cooled 2D only; bounded terminal HBr one/two and HI one-equivalent non-cooled 3D. Other subprofiles remain conditional. |
| 23 | Alkene dihydroxylation | P; paused source/release gate | Cooled 2D only; existing ambient/unset Os/H₂O₂ + release-assumption diol 3D. |
| 24 | Polymerization model | O for a cooled initiation/outcome claim | Cooled finite net graph 2D only; current reference finite oligomer 3D is not bulk polymer prediction. |

### Per-type evidence, gaps and required safeguards

The following complements the view inventory above. “Not established” means not established in the bounded reviews, **not absent from the world's literature**. E01–E18 refer to the original plan's evidence catalog; their original access qualifications remain. A full mechanism is missing for most net rules but is not itself a requirement for their static product depiction.

#### 1. Hydrogenation

- **Evidence / missing:** Phase 6 patent supplies a cold parent endpoint; wider Pd/Pt, spectator and stereofacial applicability is not established.
- **Condition gap:** explicit catalyst/support/formulation, solvent and H₂ reference assumptions; optional pressure basis and contact-history provenance.
- **Engine gap:** selected isolated C=C reduction already works. Catalyst-dependent competing reduction, stereofacial outcome and experimental completion are unmodeled, not repaired by metadata.
- **Safeguards:** actual one H₂, preserve graph/maps/remote configuration, no generalized Pt/Pd permission, no claimed selective mono-conversion, no surface mechanism invented.

#### 2. Bromination

- **Evidence / missing:** E01/E02 support bounded cold Br₂ feasibility; experimental proof for every eligible structure/medium and exact ratios remains absent.
- **Condition gap:** exact non-capturing-medium assumptions should have reusable provenance rather than imply all dry solvents.
- **Engine gap:** existing dibromide/anti alternatives work; full bromonium mechanism and competing capture/radical products are not implemented.
- **Safeguards:** retain actual Br₂, medium/activation and intramolecular-capture screens, independent stereo/maps and all present positive/negative behavior. No range inferred from “cooled.”

#### 3. Chlorination

- **Evidence / missing:** Phase 4 formulation-specific cold lead; full applicable no-extra-additive/stereo evidence and E09/E10 experimental review unresolved.
- **Condition gap:** specific medium, material chloride/additive formulation and relevant initiation assumptions.
- **Engine gap:** dichloride graph/anti alternatives exist; competing halohydrin, radical and additive-dependent pathways are not predicted.
- **Safeguards:** validate Cl₂ independently; preserve unresolved diene/cyclization restrictions, do not reuse Br₂ permission or assert stereochemistry from connectivity/GC alone.

#### 4. Hydration

- **Evidence / missing:** established existing acid/water net chemistry; no sufficiently matched cold direct-alcohol profile established in this review.
- **Condition gap:** acid formulation, water availability/medium and cold-versus-later-hydrolysis history.
- **Engine gap:** bounded regioisomer alternatives exist; rearrangement, sulfate-intermediate release and general intramolecular capture are not modeled.
- **Safeguards:** actual consumed water, regenerated acid, existing rearrangement/site screens, no invented syn/anti or major-product percentages. A sulfate process is not silently direct hydration.

#### 5. Hydrohalogenation

- **Evidence / missing:** existing ionic HX products; no admitted reagent-specific cooled ionic formulation. Radical HBr evidence is not a substitute.
- **Condition gap:** exact HX formulation, non-capturing medium, activation/initiation assumptions and existing ambient-only HCl/O boundary.
- **Engine gap:** bounded orientations exist; unrestricted rearrangement/radical chemistry and acid-sensitive spectator reactions do not.
- **Safeguards:** actual HCl/HBr/HI independently, retained maps, consume selected E/Z, new centers unassigned, no cooling-based expansion of oxygen compatibility.

#### 6. Epoxidation

- **Evidence / missing:** E03/E04 mCPBA and checked E05 perbenzoic precedent; perbenzoic variants are bounded inference. Peracetic formulation/warming and broader scope remain unqualified.
- **Condition gap:** exact solvent/formulation and observed thermal stages should be reusable named descriptors; current perbenzoic profile already demonstrates disclosure/confirmation.
- **Engine gap:** epoxide/acid graphs and concerted mapped mechanism exist; subsequent acid opening/buffering and other oxidation systems do not.
- **Safeguards:** exact peracid, existing substrate screens, actual acid coproduct, validated same-face relationships; do not transfer permission among peracids or infer facial ratios from cooling.

#### 7. SN2

- **Evidence / missing:** E13 and Phase 5 cooler aqueous leads; complete applicable buffer/OH/product details and broader substrate evidence remain unresolved.
- **Condition gap:** named aqueous base/buffer formulation and relevant activity/pH assumptions, not generic polar-aprotic equivalence.
- **Engine gap:** concerted OH replacement, inversion and distant retention already exist; competition, solvent activity and intramolecular outcomes are bounded, not universal.
- **Safeguards:** methyl/primary/selected secondary scope only, actual OH, independent CIP after physical inversion, site-specific checks, no tertiary SN2 or automatic elimination winner.

#### 8. SN1

- **Evidence / missing:** E14 lower-temperature water-solvolysis leads, not a completed dedicated cold product/formulation review.
- **Condition gap:** water/solvent composition and supported ionization/capture assumptions.
- **Engine gap:** existing ionization, positive intermediate, water attack and deprotonation work; general rearrangement and SN1/E1 distributions do not.
- **Safeguards:** supported carbocation classes only, reacting configuration lost, distant configuration retained, no ordinary methyl/primary cation or 50:50 claim. SN2 cold evidence is not SN1 approval.

#### 9. E2

- **Evidence / missing:** no adequately reviewed cooled current-OH alkene-product profile in the plan; dedicated review is outstanding.
- **Condition gap:** base/medium formulation and applicable cold conditions distinct from the heated reference.
- **Engine gap:** acyclic β-H selection and bounded anti geometry exist; arbitrary cyclic geometry and unrestricted E/Z/competition do not.
- **Safeguards:** real β-H, correct concerted electron/bond edits, existing local stereo rules, no claim that one non-anti conformer proves impossibility or heating is universally necessary.

#### 10. E1

- **Evidence / missing:** no dedicated cold elimination-product review; SN1 ionization kinetics alone cannot establish the alkene endpoint.
- **Condition gap:** water/medium and temperature-specific elimination model assumptions.
- **Engine gap:** existing positive carbocation then β-H removal works; unrestricted rearrangements and SN1/E1 ratios do not.
- **Safeguards:** supported cation and β-H, no concerted E2 substitution, preserve distant stereo, newly created E/Z unassigned unless separately validated; no guaranteed major alkene.

#### 11. Alcohol oxidation — two distinct model assessments

- **Evidence / missing:** E15 supports the existing secondary NaOCl/acetic-acid model with bath-versus-mixture distinctions, not a validated near-zero profile. E16 cold selective-primary chemistry uses additional reagents.
- **Condition gap:** exact NaOCl/acid/pH/formulation and internal thermal reference; primary selective stopping/release needs its own legitimate reagent model.
- **Engine gap:** primary→aldehyde and secondary→ketone net edits exist. A selective primary final endpoint is unqualified; tertiary oxidation is excluded; additional oxygen/spectator scope is narrower in the qualified secondary profile.
- **Safeguards:** keep primary 3D blocked, no hidden TEMPO/KBr/PCC/new oxidant, no residual tetrahedral tag on planar carbonyl, preserve mapped original oxygen and balanced byproducts.

#### 12. Aldehyde oxidation

- **Evidence / missing:** existing hypochlorite further-oxidation reporting model; no admitted cold profile resolving endpoint/speciation.
- **Condition gap:** aqueous formulation/pH, neutral reporting versus carboxylate and any separately evidenced acid work-up.
- **Engine gap:** acid net graph works; arbitrary solution speciation, coupled work-up and ionic-output extension do not.
- **Safeguards:** neutral acid reporting is not measured solution composition; no silent acidification or temperature-based resolution of charge/output policy.

#### 13. Carbonyl hydrogenation

- **Evidence / missing:** existing aldehyde/ketone H₂ reduction model; no completed matching cold catalyst/formulation review.
- **Condition gap:** catalyst/support, medium/H₂ assumptions and C=O-specific activity, separately from alkene hydrogenation.
- **Engine gap:** selected C=O→C–OH net edits and remote retention work; broader chemoselectivity and facial outcomes remain unmodeled.
- **Safeguards:** do not transfer patent alkene evidence to C=O; keep competing reducible-group screens, actual H₂ mapping and unassigned new centers.

#### 14. Esterification

- **Evidence / missing:** current acid/alcohol net chemistry; adequately matched cold reaction-stage evidence not established here.
- **Condition gap:** acid/solvent/water formulation and reaction-stage versus catalyst-addition temperature history.
- **Engine gap:** ester/water connectivity exists; equilibrium conversion, removal of water and arbitrary multifunctional scope are not predicted.
- **Safeguards:** retain current acid/alcohol and site rules, both net products and charge balance; do not claim completion, rate or a cold equilibrium yield.

#### 15. Ester hydrolysis

- **Evidence / missing:** existing ordinary/validated lactone/aryl cleavage; no admitted cold scope-specific acid/water profile.
- **Condition gap:** acid/water activity and product-release/work-up distinctions.
- **Engine gap:** selected acyl cleavage and supported ring opening work; arbitrary ring sizes, coupled multi-site conversion and experimental stereoretention do not.
- **Safeguards:** preserve Phase 1 ester restrictions and mapped connectivity/charges; validate ordinary, aryl and lactone scope separately rather than assuming one source covers all.

#### 16. Alcohol dehydration

- **Evidence / missing:** E17 supports a heated reaction, not its cooled receiver as a cold reaction.
- **Condition gap:** no matched cold current-H₂SO₄ profile; merely making temperature numeric supplies none.
- **Engine gap:** alkene net products exist; alternative cold reagents, coupled substitution/ether pathways and unrestricted rearrangement are outside scope.
- **Safeguards:** keep the present heated model boundary; do not introduce a different dehydrating system through a condition label or invent product ratios.

#### 17. Alcohol substitution

- **Evidence / missing:** E18 cites a historical cold tertiary-HCl lead; original applicable experiment not fully reviewed. Current qualified scopes are narrower than all formal HX products.
- **Condition gap:** actual HX formulation, aqueous/medium activity and substrate-class thermal assumptions.
- **Engine gap:** formal replacement/water mapping works; secondary/benzylic mechanism partition, unresolved reacting stereo and competing oxygen chemistry can block even non-cooled 3D.
- **Safeguards:** HX consumed, not just a catalyst; no automatic SN2 inversion or universal SN1, no transfer tertiary HCl→primary HBr/HI, no silently cleared oxygen/rearrangement limits.

#### 18. Ester saponification

- **Evidence / missing:** cold alkaline hydrolysis is a research candidate; no qualified source/formulation profile admitted in these phases.
- **Condition gap:** actual OH/aqueous formulation and separation of hydrolysis from acid work-up.
- **Engine gap:** carboxylate net products and validated lactone opening exist. Present ionic-geometry policy remains independently 2D-only; adding a cold profile would not itself solve it.
- **Safeguards:** retain carboxylate charge, full salt calculator masses and alcohol/phenol coproducts. Never protonate merely to get 3D. Improved cold 2D confidence could be useful without new 3D.

#### 19. Alkyne hydrogenation — complete

- **Evidence / missing:** no dedicated matched cold active-metal alkane-endpoint review; E12's specialized Pd formulation is not generic Pd/Pt.
- **Condition gap:** exact active catalyst/H₂/medium and completion-model assumptions.
- **Engine gap:** two-H₂ saturation works; retention of other reducible sites, partial reduction and all-sites conversion are not generally represented.
- **Safeguards:** two actual H₂, do not reuse Lindlar permission or selected-site bookkeeping as selectivity, preserve mapped hydrogen inventory and remove invalid alkene geometry.

#### 20. Alkyne partial hydrogenation

- **Evidence / missing:** E08 validates Lindlar chemistry, not a demonstrated cold reaction stage; catalyst manufacture temperatures are not substrate temperatures.
- **Condition gap:** exact selective catalyst/formulation, compatible medium, H₂ and stopping/uptake reference.
- **Engine gap:** bounded syn/cis/Z alkene graph works; automatic stopping/over-reduction, rates and general multi-site selectivity do not.
- **Safeguards:** actual H₂/Lindlar, terminal products have no invented E/Z, retain over-reduction warnings. The checked source says uptake slows rather than stops; cooling is not a stopping model.

#### 21. Alkyne halogenation

- **Evidence / missing:** cold Br₂ one- and two-stage reviews from original Phase 4 remain uncompleted; Cl₂ needs independent reagent/stereo evidence.
- **Condition gap:** reagent-specific non-capturing formulation and explicit stage/supply assumptions; current separate alkyne temperature guard must be integrated per profile.
- **Engine gap:** both net endpoints exist. First-stage Cl₂ E/Z remains unresolved; multi-site selectivity and chlorine/oxygen compatibility have additional gates.
- **Safeguards:** one versus two X₂ atom inventories, no global removal of the alkyne thermal guard, no extrapolation from alkene Br₂, no invented first-stage Cl₂ E/Z or cyclization suppression.

#### 22. Alkyne hydrohalogenation

- **Evidence / missing:** E11's cold homolytic HBr chemistry does not validate the current ionic model. Matching cold ionic reagent-specific evidence remains missing.
- **Condition gap:** actual HX activity/formulation, non-capturing medium, stage and activation assumptions; qualified profile is explicitly ambient.
- **Engine gap:** vinyl/geminal net graphs exist; HCl activation, internal first-stage E/Z, two-HI compatibility and oxygen/multiple-site competition remain unresolved.
- **Safeguards:** do not infer radical anti-Markovnikov chemistry, universal anti/trans or reagent interchangeability; retain separate one/two-equivalent and stronger non-thermal blockers.

#### 23. Alkene dihydroxylation

- **Evidence / missing:** actual page 1302 plus the earlier 1303 excerpt strengthen the Os/H₂O₂ lead; **complete pages 1303–1304 remain required**. Os/NMO evidence is a different oxidant model.
- **Condition gap:** named tert-butanol/peroxide/Os formulation and evidence-appropriate free-diol/release declaration.
- **Engine gap:** syn net diol graphs/maps work; overoxidation/cleavage, catalytic Os cycle and proton exchange are not simulated. A new release endpoint must be reviewed if the current assumption is inappropriate.
- **Safeguards:** source before admission, smallest justified non-stereogenic scope first, preserve actual H₂O₂ and all competition/stereo checks, no imported NMO or claimed literal oxygen-cycling history.

#### 24. Polymerization model

- **Evidence / missing:** no reviewed cold initiation/outcome evidence for the present finite BPO model; other low-temperature initiation systems are not substitutes.
- **Condition gap:** relevant initiator/activation/thermal-history model, not just a lower temperature.
- **Engine gap:** finite phenyl-ended chain connectivity is implemented, not propagation/termination kinetics, bulk polymer properties or an arbitrary initiator engine.
- **Safeguards:** keep 2/4/6-unit meaning explicit, actual represented atoms/end groups and balance, no new redox/photo/amine initiation, no claimed degree of polymerization or cold conversion.

## 7. Smallest reusable condition-system extensions

### 7.1 Reuse the registry, do not replace it

Extend the existing immutable registry/assessment architecture with a small typed **condition-profile descriptor** and an optional **explicit profile selection**. Do not build a second product engine or a separate frontend chemistry allowlist. Keep research candidates in documentation, not the executable positive registry.

Proposed descriptor responsibilities:

| Information | Minimal representation | When it matters |
| --- | --- | --- |
| Identity/version | Stable profile ID/version tied to existing pathway and site policy. | Every selected profile; unknown/revoked/mismatched selections fail closed. |
| Actual chemical participants | Existing structural identity predicates and explicit consumed/catalyst/medium/additive roles. | Every profile. Formula/name matching never substitutes a reagent. |
| Catalyst formulation | Exact metal, support/poisoning/ligands/material preparation distinctions supported by the source. | Pd/Pt, Lindlar, Os and other reviewed catalyst profiles, not every reaction. |
| Medium/formulation | Named solvent or defined mixture, water/buffer/additive facts where material. | Only to the scope actually reviewed. Dryness remains distinct from identity/nucleophilicity. |
| Thermal observations | Reaction-stage point or justified interval; separate bath/addition/hold/warming observations. | No automatic range interpolation or a universal cooling threshold. |
| Gas conditions | Reported H₂ pressure/unit/basis, or explicitly unknown basis; reference/assumption provenance. | Hydrogenation profiles. Not a general pressure control on every form. |
| Endpoint/release | Net endpoint, omitted species, existing release assumption and any separately reviewed later stage. | Especially diols, acids/carboxylates and partial reductions. |
| Evidence/inference | Source locator, observed scope, generalized scope rationale, unresolved limitations. | Every admitted model; software tests are not experimental replication. |
| Validation/output | Existing assessor and graph/stereo validators; structured reasons and explicit permissions. | Every route. Geometry availability remains a separate result. |

Each material datum must identify its provenance: **source observation**, **accepted fixed model assumption**, **user-entered selection**, or **unknown/not modeled**. Mark whether it affects product identity, competing chemistry, endpoint release, or only unpredicted kinetics. Do not require a student to enter all laboratory details when they do not change the bounded net-model claim.

A minimal optional selection could be a typed `{id, version}` reference beside the existing condition dictionary. Exact wire naming is a schema decision for the approved implementation, not a new accepted input created here. The client sends the reference, not an arbitrary catalyst/solvent JSON that can self-certify chemistry. The backend resolves immutable facts, checks actual reagents/site and explicit-field conflicts, and recomputes permissions for match/diagram/run/calculation context.

Keep old payloads/drafts valid. For the first foundation increment, describe and transport **only the existing three cooled profiles**; preserve their current IDs, versions, fallback behavior and accepted scope. New source-backed candidates require separate admission. An extended descriptor view can be generated from the same registry without changing the original minimal manifest consumed by v1 parity checks.

### 7.2 What to add now versus later

| Candidate improvement | Recommendation |
| --- | --- |
| Specific catalyst identities/formulations | Add descriptor capability first; later admit exact profile choices, not a globally permissive Pd/C menu. |
| Reagent/oxidant identities | Reuse exact structure checks. Add formulation/role metadata where relevant; no new reagent family in the foundation. |
| Exact solvents | Prefer a few source-backed named profile media. Do not create a long generic solvent catalog whose options all appear validated. |
| Low-temperature ranges | Preserve qualitative selection; annotate observed points/stages. Accept ranges only with actual reviewed applicability, not endpoints guessed from a bath. |
| Hydrogen pressure | Add typed reference capability, not a mandatory global input or universal threshold. A profile can disclose fixed reported conditions; arbitrary numeric validation is later work. |
| Other conditions | pH/buffer, additives, equivalents and time only when material to the endpoint/competition gate. Reference time is not a predicted time-to-completion. |
| Work-up/release | Keep existing meaning; describe unmodeled isolation separately. A new chemically different release/speciation stage requires its own reviewed increment. |
| Guided selections | Extend the existing confirm/apply/signature pattern after the contract is verified; no silent temperature change, reactant replacement or clearing conflicts. |

Do **not** add a general activity model, pressure-dependent rate solver, automatic constants lookup, full catalytic simulation, arbitrary mixture reaction predictor or laboratory-safety recommendation system.

### 7.3 A simple future student interaction

Use the existing Inspector/Guided Conditions surfaces rather than redesigning the page:

1. Select reactants and an eligible pathway.
2. If an admitted matching model exists, show one short named option with its material assumptions.
3. Review the proposed selections and conflicts; explicitly confirm and apply.
4. Reassess through the backend; show 2D/3D only under its existing permission contract.
5. Keep evidence, thermal observations and omitted factors in details. If only evidence/release work is missing, say so and provide **no misleading Apply action**.

Distinguish “conditions you can complete,” “profile not reviewed,” “outside chemical scope,” “endpoint unsupported” and “geometry unavailable.” Preserve visible labels, accessible status feedback and current invalidation/race protection. UI/UX Pro Max informed those form-feedback/label recommendations; progressive disclosure here is a product recommendation, not a claimed exact database match. **No UI changes were made.**

### 7.4 Invariants for any future implementation

- A selected profile never overrides invalid structure, wrong reagent, atom/charge imbalance, stereochemistry failure or unsupported output.
- Existing explicit selections conflict visibly; a named profile cannot silently reinterpret a different solvent, temperature, catalyst or release history.
- Backend selection is independent of client permissions; unknown IDs/versions, stale signatures and contradictory fields fail closed.
- No added component supplies unmapped consumed atoms. Material new chemistry cannot hide as a “catalyst” annotation.
- A profile can define a bounded net depiction without simulating experimental yields/rates or needing a full mechanism. It cannot claim its unmodeled competitors are absent.
- Conformer generation remains theoretical, with a separate geometry-failure state. No temperature simulation, isolation or experimental selectivity claim.
- Changes clear diagrams, 3D, mechanism states, atom/measurement selection and calculator results. Late responses and obsolete restored drafts cannot reinstate stale permission.
- Calculators keep current theoretical stoichiometry and full salt masses; carry profile/version/provenance without changing arithmetic or summing alternative products as predicted yields.

## 8. Options A, B and C

Effort estimates are relative engineering/review scope, not elapsed-time promises.

| Option | Benefits | Risks / costs | Effort | Assessment |
| --- | --- | --- | --- | --- |
| A — Proceed directly to 7–9 | Lowest immediate architecture work; may find a simple independently representable case. | Likely repeats generic acid/solvent/work-up gates; leaves original 4–6 subincrements unaccounted for; more one-off guidance. | Low first step, potentially high cumulative research/rework. | Not recommended as the default. Phase 9 can audit exclusions without approving chemistry, but that is not new coverage. |
| B — Complete broad shared model first | Consistent identities/formulation/history and future reuse. | Risk of a large unused schema, complex student forms and treating software fields as scientific validation. Missing papers/endpoints remain missing. | Medium–high upfront if comprehensive. | Appropriate only if narrowed; do not build every possible experimental control first. |
| C — Minimal foundation plus one evidence-backed pilot at a time | Resolves the demonstrated representation bottleneck, preserves student simplicity and exposes missing science honestly. | Requires disciplined separate approval boundaries and real compatibility/migration checks. | Medium, bounded foundation; low–medium per simple profile, higher for new endpoints/chemistry. | **Recommended.** Research backlog can progress independently; no gate is automatically bypassed. |

The useful outcome is more **honestly qualified models**, not more dropdowns or a higher unchanged frozen score. The frozen benchmark has no cooled cases, so it cannot measure cooling progress.

## 9. Proposed revised sequence, with original-scope traceability

These **R labels are new approval boundaries**, not a claim that historical phases were rolled back or fully implemented. Each implementation remains separately authorized and ends for review. Evidence can change the ordering of the next *approved* candidate.

| Revised phase | Scope and original mapping | Exit decision |
| --- | --- | --- |
| **R1 — Shared named-profile foundation** | Extend Phase 1's contract to carry condition descriptors/selection/provenance for the **three existing profiles only**. No new chemistry permission; no new global condition form. | Existing behavior preserved; typed contract and parity/invalidation tests pass. See final acceptance criteria. |
| **R2 — One catalyst-specific alkene/H₂ pilot** | Revisit original Phase 6's narrow documented parent model after R1. Independently assess whether a specific Pd/C or specified Pd/silica reference is the smallest defensible profile. Do not combine them or include Pt. | Admit only the justified structural class with explicit assumptions and consistent legacy/base/run evidence; otherwise document the exact unresolved gate. No alkyne/carbonyl transfer. |
| **R3 — Resume dihydroxylation after source arrival** | Original Phase 3, **only after pages 1303–1304 are supplied and reviewed**. Resolve actual formulation/free-diol reporting before any named release variant. | Narrow profile if fully justified; otherwise retain restriction. If pages arrive earlier, its evidence review can inform ordering without authorizing implementation. |
| **R4 — Halogen backlog as separate increments** | Original Phase 4: alkene Cl₂ evidence/formulation first when ready; then separately alkyne Br₂ one-equivalent and two-equivalent endpoints. Alkyne Cl₂ remains independent and potentially deferred. | One profile at a time, independent atom/stereo/endpoints; no global alkyne thermal-guard removal. Additive-dependent chemistry may need separate authorization beyond metadata. |
| **R5 — Substitution and elimination backlog** | Original Phase 5: complete SN2 formulation/product evidence, then a separate water-SN1 review. E1 and E2 remain research/negative scope until direct relevant alkene-product evidence supports a specific proposal. | No automatic paired substitution/elimination approval or product-ratio model. |
| **R6 — Remaining reduction increments** | Original Phase 6: Lindlar partial, then active-metal complete alkyne reduction as individually evidenced profiles; carbonyl reduction only after another explicit review. | Correct one/two-H₂ endpoint; no stopping/selectivity inferred from cooling; no catalyst substitution. |
| **R7 — Acid-mediated candidates** | Original Phase 7: individual acid/water hydration, ionic HX and narrow alcohol/HCl candidates, reordered by evidence quality. | Reagent-specific conditions; no radical evidence used for ionic products or unmodeled hydrolysis/rearrangement. |
| **R8 — Ester and endpoint-limited work** | Original Phase 8: cold esterification/hydrolysis/saponification evidence separately. Secondary oxidation only if matching cold evidence appears; primary stopping, heated dehydration and finite-polymer initiation remain separate limitations. | Cold 2D confidence may be a valid saponification outcome; never require neutralizing an ion to meet a 3D target. |
| **R9 — Whole-system acceptance audit** | Original Phase 9. No new profiles during the review. Include all 24 types, both alcohol-oxidation models, all admitted profiles and outstanding exclusions. | Traceable evidence, coherent reason/output contracts and no regressions; explicitly permit deferred/O classifications. |

R2 is a promising first *chemistry pilot* because the source has a represented simple endpoint; it is **not** the next implementation authorized by this report. R1 must demonstrate the shared contract first. Do not wait for every literature gap to be solved before improving the contract, and do not approve a reaction merely because the contract can now describe it.

## 10. Measures and preservation for future increments

Report independently:

1. Structural matches/site compatibility.
2. Condition completeness and conflict state.
3. Evidence-backed profile applicability, distinguishing direct observations from bounded inference.
4. Correct validated net products, maps, charges and applicable stereo.
5. Theoretical 3D permission **and actual geometry availability**.
6. Unresolved category: source access, formulation, chemistry competition, endpoint, output policy or geometry failure.

Use denominators for **24 types**, **25+ model fixtures** and separate **profile cases**. Count profiles separately from types. Do not merge evidence qualification with the draft companion's diagnostic-only generations. Preserve all frozen 347 IDs/inputs/expectations; any future companion/cooling dataset gets a separate pinned version. Report the known frozen defect separately, never silently fix it to claim improvement.

For every approved implementation: ratchet the current **4,281** regression floor upward; run full Python/JavaScript, focused chemistry/API/contract/mapping/mechanism/calculator suites, TypeScript, production build, fixed audit, separate condition-aware measurements, whitespace and desktop/mobile/race checks. Preserve the existing UI layout, tools, curated examples and local-only boundary. Production source fingerprints may legitimately change; frozen case identities, chemistry expectations and comparison rules may not.

### This planning deliverable's preservation record

The completed preservation check confirms **all 494 captured pre-existing files are unchanged** under server, src, tests, scripts, benchmarks and docs. Only this new Markdown report was added. No tests or accepted profiles were added. No builds, live UI changes, commits, pushes, merges or Render actions were performed. Tracked diff and new-report whitespace checks pass.

**Phase 3 reminder remains active: obtain pages 1303 and 1304 of Milas–Sussman (1936). Page 1302 is already supplied.**

## 11. Single best next implementation phase and acceptance criteria

**Propose R1 — Shared Named Condition Profiles and Provenance, without new cooled chemistry. Wait for approval before starting.**

Scope is deliberately smaller than a general condition editor: reuse the current registry, add a typed server-owned descriptor and explicit-selection transport for existing profiles, maintain backwards compatibility, and test all downstream contracts. Do not register hydrogenation, dihydroxylation, chlorination, SN2 or any other new positive profile in R1. No new UI layout or general numeric controls are required.

R1 is accepted only when all of the following are verified:

1. **Exactly three existing cooled profile IDs and two supported types remain.** Existing implicit/v1 requests and products retain their behavior; no new substrate/reagent/stereo scope or 3D permission is introduced.
2. Each existing descriptor distinguishes actual molecular identities, documented observations, named medium/thermal assumptions and unmodeled facts. Profile facts come from the backend registry, not arbitrary client JSON or a second frontend chemistry table.
3. The new optional selection is validated on match, diagram and run; wrong pathway/reagent/site, unknown ID/version, contradictory existing fields, stale cached metadata and forged permissions fail closed. No `cooled`→`ambient` rewrite or hidden clearing/substitution occurs.
4. Original manifest/payload/draft compatibility is preserved. Any additive protocol fields are versioned and tested. Existing non-cooled legacy unknown-field behavior is not silently rewritten as an unrelated change; the new selection contract itself must never fall through as ignored legacy metadata.
5. 2D, confidence, mechanism availability, 3D permission/geometry outcome and calculator context agree on the selected profile/version and provenance. Existing actual mapping, charges, coproducts and stereo invariants remain unchanged.
6. Selection and condition changes immediately invalidate all dependent outputs; delayed responses and restored obsolete drafts cannot resurrect a previous result. Guide/application remains advisory and backend-revalidated. No current UI is redesigned; any later chooser behavior beyond existing surfaces needs explicit approval.
7. **All 4,281 existing tests pass**, with separate versioned contract/provenance additions. TypeScript, production build, relevant public API and desktop/320px/mobile/lifecycle tests pass. Existing Br₂/mCPBA/perbenzoic positives and all deferred-pathway negatives remain intact.
8. The **unchanged 347-case audit** retains the same per-case chemical results/classifications, totals and comparison rules; source-fingerprint changes are explained. No frozen expectations or visible examples are edited, and no diagnostic-only count is relabeled as validated cooling coverage.
9. A short implementation report lists exact changes, preservation evidence and limitations. No push, merge or deployment; stop before R2 or any new chemistry admission.

