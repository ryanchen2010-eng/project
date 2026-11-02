# R3 - Cooled Os/H2O2 dihydroxylation, full-paper completion

26 October 2026 - Implementation/evidence report v1 - Local only

## 1. Decision and completed scope

**The missing-source requirement is resolved.** All three original PDF pages were rendered, visually read and cross-checked with extracted text. This report supersedes the earlier Phase 3 source-access deferral, not the historical record of what was available then. Earlier reports are preserved.

Three separate, explicit named profiles are admitted:

| Profile ID, version 1 | Exact structural scope | Free-product reporting contract |
| --- | --- | --- |
| `cooled-isobutylene-os-peroxide-v1` | Isobutylene -> 2-methylpropane-1,2-diol | Source fractionation; **no assumed aqueous release**. |
| `cooled-crotonic-os-peroxide-v1` | Unconfigured crotonic-acid identity -> unconfigured 2,3-dihydroxybutyric acid | Source water recovery, chloroform extraction of unchanged acid, aqueous evaporation. |
| `cooled-cinnamic-os-peroxide-v1` | Unconfigured cinnamic-acid identity -> unconfigured phenylglyceric acid | Source water recovery, filtration of unchanged acid, reduced-pressure filtrate concentration. |

Eligible neutral net products have verified 2D diagrams and actual converged theoretical 3D conformers. The two acid profiles do **not** assign product configurations, validate specified starting E/Z variants, or claim a stereoisomer distribution. They are exact-parent reference models, not general unsaturated-acid compatibility.

**Fumaric acid is not admitted.** Its cold experiment explicitly includes further oxidation and calcium-salt recovery. The existing single free-diol net graph cannot faithfully represent that endpoint/mixture. It is not represented as a completed neutral tartaric-acid reaction.

Cooling inventory is now **seven profiles across four of the existing 24 rule types**, previously four profiles across three types. All earlier profiles retain their behavior. This is bounded model coverage, not an experimental success percentage.

Final verification: **4,347 tests pass (2,166 Python + 2,181 JavaScript)**, 26 above the freshly verified 4,321 baseline. TypeScript, production build and browser checks pass. All 347 frozen per-case audit results are unchanged. No push, merge, Render deployment, new reaction family or Batch 2 work occurred.

## 2. Primary-source record

Nicholas A. Milas and Sidney Sussman, *The Hydroxylation of the Double Bond*, JACS **58** (1936), **1302-1304**, [DOI 10.1021/ja01298a065](https://doi.org/10.1021/ja01298a065).

User-supplied source: `/Users/rc/Downloads/ja01298a065.pdf`, three pages. SHA-256: `4d01cfb44385f905adbf4560f6df65ce5678febda4b1ba14e83b775bbfcc475c`. The PDF was not altered. Both page images and native extracted text were inspected; OCR alone was not used to establish numerical details.

- **1302:** article opening, Table I, reagent preparation, catalyst discussion and warning of further oxidation.
- **1303:** all experimental paragraphs, including the four requested 0 C cases and the distinct room-temperature/control examples.
- **1304:** the article's concluding summary. The subsequent aldoxime article, and preceding unrelated text at the top of 1302, are not Milas-Sussman experiments.

### 2.1 Common preparation context - p. 1302

The preparation combines **100 cc of 30% aqueous H2O2** with **400 cc pure tert-butanol**. Anhydrous sodium sulfate effects layer separation; the alcohol layer is dried with sodium sulfate and then calcium sulfate/Drierite. The prepared reagent is reported as **6.32% H2O2**, with **93.8% peroxide recovery**. That is a reagent-preparation recovery, not a reaction-product yield. The authors describe concentration by room-temperature vacuum removal of alcohol.

The Os catalyst is OsO4 in tert-butanol. The paper discusses decomposition in water and reduction to a colloidal oxide in the presence of isobutylene. Those observations do not provide a resolved catalyst cycle or a kinetic model for this tool.

The general 6.32% preparation is **not silently equated** to the **6.62%** isobutylene reagent or the **6.3%** acid reagents. Percentage bases and quantitative residual water are not specified. “Anhydrous” is the source description, not an entered zero-water assay. Drying/preparation species are not consumed participants in the formal net equation.

### 2.2 Isobutylene -> isobutylene glycol - p. 1303, left column, first experiment

- Substrate: **4.3 g, 0.0768 mol** isobutylene, dissolved in **36.3 g tert-butanol**.
- Oxidant: **39.3 cc, 0.0768 mol**, reported **6.62% H2O2 reagent**.
- Catalyst: **0.75 cc of 0.5% OsO4 in tert-butanol**. This stock strength/carrier is explicit in this paragraph; the percentage basis is not given.
- Thermal history: ice-bath cooling before catalyst addition, then **overnight at 0 C**. The authors report completion the following day; no exact hour count or continuous low-temperature interval is supplied.
- Recovery: the mixture is **fractionated directly**, collecting the **176-178 C** fraction. No aqueous addition or aqueous-release step is documented for this experiment.
- Recovered product: **2.6 g isobutylene glycol**, reported as **37.6% of theoretical**. Density **0.999 at 25 C** and the boiling range are compared with literature values. This is an isolated fraction and an identification argument, not a quantitative purity certificate.

**Decision:** direct isolation establishes an appropriately bounded free-glycol reporting endpoint. A separate explicit fractionation-reference contract is justified; pretending that this is an observed aqueous work-up is not. Fractionation is a later thermal operation, not evidence that isolation occurred at 0 C.

### 2.3 Cinnamic acid -> phenylglyceric acid - p. 1303, left column, final experiment

- Substrate: **3.7 g, 0.025 mol** cinnamic acid.
- Oxidant: **13.6 cc, 0.025 mol**, reported **6.3% H2O2 reagent**, plus an **equal volume of tert-butanol**. The descriptor identifies 13.6 mL additional solvent as derived from that wording, not a separately measured number.
- Catalyst: **2 cc of the osmium tetroxide solution catalyst**. Interpreting that cross-reference as the preceding 0.5% OsO4/tert-butanol stock is explicitly labeled a **model assumption**; the concentration is not repeated here.
- Thermal history: ice-bath cooling, catalyst addition, **overnight at 0 C**, following-day recovery. Exact hours and isolation temperature are unstated.
- Recovery: vacuum removal of solvent; residue taken up with water; **2.4 g unchanged cinnamic acid** removed by filtration; filtrate concentrated under reduced pressure.
- Product: **0.9 g noncrystallized semisolid phenylglyceric acid**. Reported yield **56.2% of the cinnamic acid consumed**, not of the initial charge and not a conversion percentage. Neutralization equivalent **190**, compared with theoretical **182**, supports the historical assignment but does not establish purity or stereochemical composition.

**Decision:** a source-specific neutral hydroxy-acid net endpoint is supported, with an independently checked acid-group preservation policy. Starting E/Z and configured product outcomes are not explicitly assigned in this procedure; the admitted input and product identities remain unconfigured. The profile does not enable specified E/Z cinnamic acids or broader aromatic-adjacent acids.

### 2.4 Crotonic acid -> dihydroxybutyric acid - p. 1303, right column, first experiment

- Substrate: **4.3 g, 0.05 mol** crotonic acid.
- Oxidant: **27.2 cc, 0.05 mol**, reported **6.3% H2O2 reagent**. No separate tert-butanol addition is stated in this paragraph; the reagent already supplies its carrier.
- Catalyst: **1 cc of the osmium tetroxide solution catalyst**, with the same explicitly labeled stock cross-reference assumption as above.
- Thermal history: ice-bath cooling and **overnight at 0 C**, recovery the next day; no exact hours are inferred.
- Recovery: solvent removed under reduced pressure; residue taken up with water; unchanged crotonic acid extracted with chloroform. Evaporation recovers **2.7 g unchanged acid**. The aqueous portion is then evaporated under reduced pressure.
- The paper references Braun (1929) for the extraction method. That separate paper was not reviewed here; unreported details of its procedure are not reconstructed or treated as simulated work-up chemistry.
- Product: **1.2 g thick syrup**, reported as **53.8% of the crotonic acid consumed**. Neutralization equivalent **122**, versus calculated **120**. This is not the same isolation as the cinnamic-acid filtration procedure and does not establish configured stereochemistry or complete purity.

**Decision:** admit only the exact unconfigured parent/free-acid reference. Preserve its acid C=O, acid C-O and neutral charge independently. Related chain lengths, esters, carboxylate salts and specified E/Z variants are not automatically included.

### 2.5 Fumaric acid -> racemic acid, with oxalic acid - p. 1303, right column, final experiment

- Substrate: **2.9 g, 0.025 mol** fumaric acid.
- Oxidant: **27.2 cc, 0.05 mol**, reported **6.3% H2O2 reagent**: **two charged peroxide equivalents**, not the one-equivalent charge used in the preceding acid experiments.
- Catalyst: **2 cc of the osmium tetroxide solution catalyst**; its stock strength is cross-referenced rather than restated.
- Temperature/time: **two days at 0 C**, not “overnight.”
- Recovery: reduced-pressure solvent removal; residue taken up with a small volume of water; **1.7 g unchanged fumaric acid** removed by filtration.
- Isolated/analyzed materials: **0.3 g calcium oxalate** precipitated in acetic-acid solution, and **1.3 g calcium racemate** precipitated in ammoniacal solution. The paper reports corresponding yields of **9.9% oxalic acid** and **48.3% racemic acid**. Calcium analysis is reported for the racemate hydrate; the free neutral acid is not what was directly weighed.

The paragraph does not repeat every calcium-reagent concentration or explicitly restate the yield denominator. The recovered starting acid and salt-equivalent calculations support a consumed-acid interpretation, but the report does not silently turn those percentages into initial-feed conversion or isolated pure free-acid yield. The preceding maleic-acid experiment's complete precipitation sequence is **not assumed identical** to the fumaric work-up.

**Decision: retain the restriction.** Explicit further oxidation, two-equivalent feed, acid/salt isolation and multiple endpoints need a different independently validated oxidation/recovery model. A single formal one-peroxide tartaric-acid graph would not account for those observations. Backend rejection text identifies the oxalic-acid/calcium-salt issue, not chemical impossibility. No racemization ratio is synthesized from the source term “racemic acid.”

### 2.6 Other observations do not enlarge cooled scope

Trimethylethylene is a **room-temperature, 24-hour** experiment. Allyl alcohol is cooled under running water after warming, without a documented 0 C hold. Maleic acid is an **overnight room-temperature** experiment and also yields oxalate. The introductory cyclohexene/adipic-acid observation is a warning against assuming universal free-diol stopping. The summary's ethylene/pinacol and ester examples do not supply separate verified 0 C procedures. None is registered as a cooled profile here.

## 3. Implementation and scientific safeguards

### Reuse of R1/R2

`server/cooled_dihydroxylation_r3.py` holds immutable exact-parent source records, endpoint validation and detached provenance builders. The existing cooling registry remains the single registration/3D authority. The three additions are **explicit-only**, version 1; generic cooling, Os activation or a dry-medium selection never selects them implicitly.

The backend validates exact substrate, actual neutral H2O2, expected product, no invented coproduct, compatibility-report identity and verified atom/bond/charge/stereo checks. Existing flat profile ID/version transport, restored-draft checks, cached-permission rejection and all public match/diagram/run gates are reused.

### Explicit release contracts, not a bypass

The new versioned `productRelease` assessment records source recovery, free-product endpoint, aqueous-release assumption, explicit selection and the fact that work-up is **not simulated**. For isobutylene, `workupAssumptionConfirmed` for the legacy aqueous assumption is false while the separate named-product-release confirmation is true. Evidence requirements identify the named profile instead of falsely demanding an aqueous step.

An existing aqueous-release selection **conflicts** with the isobutylene reference. Guided Conditions lists the replacement and requires user confirmation before clearing it. The two acid profiles separately require aqueous recovery and preserve their distinct isolation descriptions. Blank release, wrong medium/activation, unrelated oxidation stage, unknown facts/versions and incompatible temperature remain blockers. No generic release requirement is removed.

### Narrow structural compatibility

The hydrocarbon candidate uses the existing transformation unchanged. For the two exact acid parents only, a separate site policy validates the real C=C and permits the independently evidenced carboxylic-acid environment. It does not globally relax the existing conjugation/group filters. The scoped reference is used for cold conditional previews or explicit references; unrelated/non-cooled generic matching remains unchanged.

Transformation validation independently preserves unaffected acid bonds, aromatic bonds, atoms, charges and stereo. The same mapped graph feeds the 2D diagram and 3D generation. Invalid related acids, additional functionality, salts, extra sites, isotopes and configured variants cannot borrow a profile merely by name or formula.

### Stereochemistry and geometry

Isobutylene glycol has no newly stereogenic center. The acid products have unassigned centers because the admitted source identities lack specified starting geometry. Product SMILES, 2D structures and reaction stereo metadata do not invent R/S, E/Z or proportions. Specified E/Z acid inputs are rejected rather than stripped to match a source record.

A 3D conformer necessarily embodies one geometry; a toolkit can infer a configuration when re-reading its coordinates. That **does not assign** the declared reaction product. The source-profile explanation explicitly distinguishes representative geometry from stereochemical prediction. Tests compare declared identities without invented tags and independently verify geometry connectivity and atom links. All three checked conformers converge; ordinary embedding/force-field failures retain the existing fallback behavior.

### Mechanisms and calculators

No full Os catalytic cycle, cyclic-osmate intermediate or elementary oxygen/proton provenance is claimed. Mechanism output remains `null`/unsupported. H2O2 supplies **formal net** O/H inventory: C=C becomes C-C, O-O is removed and two C-O bonds form. All represented atoms/charge are conserved; no hidden consumed catalyst or fabricated byproduct appears.

One mole of each admitted substrate plus one formal H2O2 gives one mole of the selected net product. H2O2 molar mass is **34.014 g/mol**. At 1 mmol theoretical product, masses are **0.090122 g**, **0.120104 g** and **0.182175 g**, respectively. These are complete-conversion upper-bound calculations, not source-yield forecasts. The existing five-significant-figure UI formatting remains unchanged; stock-solution reference volumes are not calculator dosing instructions.

### UI integration, without redesign

The existing Guided Conditions panel shows exact reference facts, assumptions, unknowns and source page locators, with confirmation and backend revalidation. The existing blank release choice is labeled as a **named fractionated endpoint** when that contract is actually qualified, instead of misleadingly calling it unconfirmed. These are text/contract changes, not new controls, layout, styles or a general reaction-condition form. UI/UX Pro Max was used for confirmation feedback, keyboard operation and mobile quality checks only.

## 4. Verification and preservation

Fresh baseline: **2,150 Python + 2,171 JavaScript = 4,321 passing**. Final full suites: **2,166 Python + 2,181 JavaScript = 4,347 passing**, no failures or skips.

- New `tests/test_cooled_dihydroxylation_r3.py`: **16 tests**, with independent product oracles, both input orders, actual 3D, mapped inventories, preserved acid bonds, neutral endpoints, source distinctions, condition/profile conflicts, unsupported structures/stereo, fumaric exclusions, cached-permission checks and authenticated public APIs.
- New `tests/cooled-dihydroxylation-r3.test.mjs`: **10 tests**, covering theoretical arithmetic, detached provenance, exact guide transport, release confirmation, stale suggestions, inert rendering and draft/version consistency.
- Focused checks passed **between candidates**: eight tests for isobutylene before adding crotonic acid; eight with crotonic before adding cinnamic; eight including cinnamic before expanding the final negative/contract suite.
- Existing test cases remain in the runs. Registry-size/type expectations now recognize seven entries/four types. The old isobutylene “no guide” expectation now requires the explicitly confirmed guide while retaining its generic 2D-only assertions. No chemistry validation assertion was removed to improve coverage.
- Initial diagnostic assumptions were corrected without weakening production code: 3D-coordinate re-import can infer tags, the independent phenylglyceric mass oracle is 182.175, and browser expectations use the calculator's existing display precision. Those were test-oracle issues, not reasons to alter product chemistry.
- **TypeScript and production build pass.** Existing third-party directive and large-bundle warnings remain, with no new build failure.
- **All 347 frozen observations are exactly unchanged:** 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported, one pre-existing incorrect-result classification. Only production-source fingerprints differ. No benchmark input, expectation, ID or audit rule changed.
- All **100 pre-existing public temperature/pathway contexts** preserve chemistry, diagrams, maps, mechanisms and permissions. Normalizing only the revised generic-dihydroxylation explanation makes the responses deeply identical. The frozen/100-context fixtures do not include the new explicit acid profiles and are not relabeled as cooling coverage.
- The separate pinned companion remains separate and unchanged: **40/53** structural matches, zero evidence-qualified condition-complete generations in its existing manifest; diagnostic-only generation remains **33/53**. Neither replay has failures. Its unchanged manifest does not automatically select these new references.
- **Desktop 1440px/mobile 320px** checks pass for each of the three profiles: conditional preview, keyboard-confirmed source/recovery selection, source locators, actual 3D, calculator, temperature/release conflicts, stale result clearing, valid/obsolete draft restoration and delayed-response rejection. No uncaught page errors or horizontal document overflow. Existing Fit/Zoom controls were checked; the wider phenyl conformer needs zoom-out at 320px. Automatic viewer fitting was not redesigned in this chemistry increment.
- Browser preservation checks pass for prior Br2, mCPBA, perbenzoic and cyclohexene profiles, deferred Cl2/SN2 boundaries, and the legacy ambient aqueous-release diol workflow. Generic cooled isobutylene still does not generate 3D without the named reference.
- Of 501 captured pre-existing files, **480 are byte-identical and 21 have intended scoped production/test changes**. Four files are new: the R3 helper, two suites and this report. All unrelated chemistry, benchmark data/scripts, styles, curated examples and earlier reports are preserved; no user work was deleted or discarded. Tracked diff and changed/new-file whitespace checks pass. The source PDF hash is unchanged.

Local QA logs, native text/page renders, public/audit observations, browser scripts and screenshots are under `/private/tmp/molecule-cooling-r3.pOrBv5/`. The final full-suite logs are `python-complete.log` and `js-complete.log`; earlier intermediate logs are not completion evidence. Source images and representative molecular screenshots were visually inspected. The isolated QA server was stopped after verification; no pre-existing development server was stopped.

## 5. Updated inventory across all 24 rule types

S = bounded admitted cooling profile; P = potentially supportable but unapproved; I = incompatible with a specific current condition profile; O = endpoint/output capability outside current scope. These are software/evidence boundaries, not universal chemical impossibility. This table carries forward prior reviews; only dihydroxylation changes here.

| # | Rule type | Cooling after R3 | Output/gate |
| --- | --- | --- | --- |
| 1 | Hydrogenation | S, exact named cyclohexene only | Prior Pd/silica-A 2D/3D preserved; other substrates/catalysts P. |
| 2 | Bromination | S | Prior bounded actual-Br2 2D/3D preserved. |
| 3 | Chlorination | P | Conditional 2D; independent Cl2 formulation/competition gate. |
| 4 | Hydration | P | Conditional 2D; no new cooled acid/water profile. |
| 5 | Hydrohalogenation | P; particular subprofile I | Conditional 2D; no ionic/radical/solvent generalization. |
| 6 | Epoxidation | S, two profiles | Prior actual-mCPBA and bounded perbenzoic 2D/3D preserved. |
| 7 | SN2 | P | Conditional 2D/mechanism; no new cooled substitution permission. |
| 8 | SN1 | P | Conditional 2D/mechanism; independent solvolysis review outstanding. |
| 9 | E2 | P | Conditional 2D/mechanism; no cold base/geometry expansion. |
| 10 | E1 | P | Conditional 2D/mechanism; no carbocation/competition expansion. |
| 11 | Alcohol oxidation | Primary O; secondary I | Conditional 2D; no selective stopping/cold formulation change. |
| 12 | Aldehyde oxidation | I | Conditional 2D; current reporting profile not broadened. |
| 13 | Carbonyl hydrogenation | P | Conditional 2D; no catalyst-profile transfer. |
| 14 | Esterification | P | Conditional 2D; cold endpoint/equilibrium unreviewed. |
| 15 | Ester hydrolysis | P | Conditional 2D; existing lactone/aryl/site safeguards retained. |
| 16 | Alcohol dehydration | I | Conditional 2D; heated sulfuric-acid profile unchanged. |
| 17 | Alcohol substitution | I | Conditional 2D; existing HX activation/stereo limits retained. |
| 18 | Ester saponification | P; ionic 3D O | Conditional carboxylate 2D; no neutralization workaround. |
| 19 | Alkyne hydrogenation | P | Conditional 2D; separate two-H2 completion gate. |
| 20 | Alkyne partial hydrogenation | P | Conditional 2D; no cold Lindlar stopping inference. |
| 21 | Alkyne halogenation | P by halogen/stage | Conditional 2D; equivalents, medium and stereo remain separate. |
| 22 | Alkyne hydrohalogenation | I under current ambient model | Conditional 2D; no new HX/stage/regio permission. |
| 23 | Alkene dihydroxylation | **S, three exact named references** | Eligible theoretical 2D/3D only within the new contracts; fumaric/other substrates/configured acids remain excluded. |
| 24 | Polymerization model | O for cooled initiation/outcome | Conditional finite graph only; no bulk/temperature simulation. |

## 6. Remaining limits and stop point

The source-access task is complete, but there is no blanket cooled dihydroxylation rule. Source observation, named assumption, validated net structure, theoretical conformer and actual experimental outcome remain separate.

Unresolved work includes configured acid stereochemistry, broader substrate applicability, further oxidation/cleavage, calcium-salt isolation, full Os mechanisms, actual solution speciation and kinetic/yield models. Fumaric acid requires a separately reviewed endpoint/competing-oxidation proposal, not a relaxed free-diol gate. The existing narrow profiles do not imply that other substrates are incapable of reacting.

**R3 is complete for all justified candidates in this task. Stop for review. No Batch 2 or other cooling family was started; nothing was pushed, merged or deployed.**
