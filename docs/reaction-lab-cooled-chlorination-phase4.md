# Cooling Phase 4 — Alkene chlorination evidence gate

Review date: 2026-10-26. Scope: existing alkene + actual neutral Cl₂ pathway only. Local work; no deployment, push or merge. This is cooling-plan Phase 4, not the earlier alkyne-development Phase 4.

## Decision

**Do not register or enable a cooled alkene-chlorination profile yet.** Cooled chlorine addition is experimentally possible; the unresolved issue is whether a particular documented formulation and endpoint can be honestly represented by this application's current inputs. This is not a conclusion that chlorine cannot add to a cold alkene.

The existing conditional 2D net transformation remains available for eligible structures. Its existing stereo alternatives describe the bounded net model, not a newly validated cold experiment. Cooled 3D remains unavailable. Previously supported ambient Cl₂ behavior and the three reviewed Br₂/peroxyacid cooling profiles are unchanged.

The review found direct cold Cl₂ evidence, but not sufficient matched evidence to approve a new no-additive/non-capturing profile. The plan's requested complete E09/E10 experimental-text gate also remains unresolved. Evidence access failures are recorded below rather than treated as chemical evidence.

## 1. Evidence reviewed and access limits

### Direct cold experimental lead — not a matching application profile

[WO2026128662A1, *Methods for the preparation of alkynes*](https://patents.google.com/patent/WO2026128662A1/en), published 2026-06-18: only its initial alkene chlorination is relevant here; no downstream alkyne chemistry was implemented.

Paragraphs **[0083]–[0089]**, printed pages **22–23**, describe Examples **22–27**: 1-hexene receives Cl₂/N₂ with ice-bath control at **0–20 °C**. The desired product is 1,2-dichlorohexane; other chlorinated products are discussed. Example 22 uses aqueous brine; later examples use quaternary-ammonium chlorides and, in Example 24, chloroform instead of water. Example 27 omits NaCl but still uses Aliquat 336. It is not an additive-free control. The accessible HTML omits Table 4's image; its cells were not inspected. Reaction duration, isolated-product work-up and stereo-specific identity were not established from this passage. A separate 50 °C example is not a cooled experiment.

**Engineering inference:** neither `Dry / no water` nor `None Added` represents this documented formulation. Chloride additives cannot silently become a second reagent or disappear into a catalyst label. A brine experiment is not evidence for the application's dry-medium choice. These patent examples are useful primary experimental evidence, not independent reproduction or a validated teaching-lab procedure. Their conversion/selectivity data are not used as application predictions.

The patent's general optional-additive claims do not supply a missing experimental no-additive control. Nor does a product's connectivity establish its physical configuration or exclusive experimental formation.

### Original plan E09 — relevant record, experimental text unavailable

[Taft, *Substitution vs. Addition in the Low Temperature Non-activated Chlorination of Olefins*](https://doi.org/10.1021/ja01190a044), JACS **70**, 3364–3369 (1948); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/18891863/).

The bibliographic record/title was located. Publisher full text returned an access error; an attempted archival scan could not be retrieved. **The complete article was not read.** Its title cannot establish the precise temperature, solvent, substrate, initiation controls, isolated product or stereochemical scope needed to approve a profile. It remains a retrieval priority, not an approved source of cold 3D permission.

### Original plan E10 — distinguish two Poutsma papers

The plan links [DOI 10.1021/ja01088a015](https://doi.org/10.1021/ja01088a015), **Part III**, concerning isomeric butenes and allyl chloride, JACS **87**, 2172–2183 (1965).

The cyclohexene **Part II** is a different paper: [DOI 10.1021/ja01088a014](https://doi.org/10.1021/ja01088a014), JACS **87**, 2161–2171 (1965). The publisher's bibliographic listing confirms that distinction. The original plan was not edited.

Both full-text retrievals were blocked. **Neither complete experimental section was reviewed.** Indexed excerpts and citations are leads only. No precise cold recipe, addition/substitution suppression or stereo outcome is inferred from a title, abstract or another paper's citation.

### Other leads excluded from approval

- Bloomfield's [1944 RSC paper](https://pubs.rsc.org/en/content/articlepdf/1944/jr/jr9440000114) was located in an index, but its full PDF could not be obtained. Mixed substitution/addition and different halogenating formulations cannot establish the requested Cl₂ model from snippets.
- [Palladium tetrachloride/chlorination study](https://pmc.ncbi.nlm.nih.gov/articles/PMC4116810/): indexed direct-Cl₂ controls involve additives/particular media; accessible leads did not establish a matching cooled no-extra-activation profile. Full text could not be retrieved in this environment, so this is not approval evidence.
- [Organoselenium-catalyzed syn dichlorination](https://pmc.ncbi.nlm.nih.gov/articles/PMC6876749/) is a different reagent/catalyst and stereochemical model, not permission to apply the existing ordinary Cl₂ anti model under cooling. No such catalyst was added.
- [US2829178A](https://patents.google.com/patent/US2829178A/en) describes a styrene/carbon-bed formulation; it is not a matching no-extra-activation cold model. Broad claimed temperature ranges are not substitutes for applicable demonstrated conditions.

No claim is made to have read inaccessible PDFs, missing experimental tables, or all cited papers in full. No secondary/vendor description qualifies a profile.

## 2. Condition/representation gate

| Candidate conditions | Phase 4 disposition | Why |
| --- | --- | --- |
| Actual Cl₂, cooled, dry, no extra activation | Conditional 2D; no cooled 3D | No admitted Cl₂ profile; generic selectors do not specify a reviewed cold formulation. |
| Actual Cl₂ in cooled water/ethanol | No asserted dichloride 3D | Existing nucleophilic-medium/halohydrin or solvent-capture gate remains. |
| Actual Cl₂, cooled, generic polar aprotic medium | No cooled 3D | That broad solvent class is not independently validated as non-capturing. |
| Actual Cl₂ with radical activation | No supported chlorination option | Existing radical/substitution exclusion remains; cooling does not cancel it. |
| Actual Cl₂ with added acid/metal activation | No cooled 3D | Added activation remains unvalidated, not an assumed compatible catalyst. |
| Previously supported ambient/dry net model | Unchanged | Phase 4 does not revise its existing contract or infer a cold equivalent. |

`None Added` means no selected additional activation. It is not a claim about illumination, atmosphere, absence of radical chains or absence of competing ionic substitution. Conversely, no new universal requirement for a particular light/oxygen protocol was invented: those details must come from an applicable source.

**Next evidence needed:** complete E09/E10 experimental text, or another directly applicable cold Cl₂ study identifying substrate, actual formulation/medium and activation conditions, product characterization, competing products and work-up. A smallest no-new-reagent profile could then be assessed. If the best evidence instead requires chloride additives, that needs a separately approved representation/formulation decision; it cannot be hidden in the current two-input model. E/Z/cyclic generalization would require its own applicable stereo evidence.

## 3. What changed

Only the existing `COOLING_LIMITATIONS["Chlorination"]` explanation in `server/reaction_temperature_profiles.py` changed. It now explicitly says:

- Br₂ cooling approval does not qualify Cl₂.
- Generic dry/none selections do not encode the reviewed formulation details.
- No current dropdown combination unlocks cooled Cl₂ 3D.
- Do not substitute ambient conditions simply to unlock a result.

The message flows through existing match, diagram, confidence and calculator-context serialization. No new profile, condition control, UI layout, stylesheet, reagent or reaction rule was added. The backend profile registry and its frontend mirror still contain **three profiles for two reaction types**: Br₂, mCPBA epoxidation and bounded perbenzoic-acid epoxidation.

Separate v1 safeguard suites were added:

- `tests/test_cooled_chlorination_phase4.py`: 15 Python tests.
- `tests/cooled-chlorination-phase4.test.mjs`: 12 JavaScript tests.

No existing test or benchmark expectation was changed. Test substrates remain separate from curated examples.

## 4. Chemistry, stereochemistry and visualization checks

Independent connectivity oracles cover ethene, 1-hexene, a branched alkene, E-/Z-but-2-ene, cyclohexene, styrene, a distant specified center and separated C=C sites. Tests exercise both input orders. These are **conditional-net and preservation checks**, not an approved cooled scope.

Verified contracts:

- Only the selected C=C changes to single; Cl–Cl breaks and two C–Cl bonds form. Both mapped chlorine atoms originate in the actual Cl₂ reagent.
- Every represented atom and formal charge is conserved; no spurious hydrogen source or byproduct is introduced.
- One Cl₂ equivalent is consumed per net addition. Calculator masses include both chlorine atoms.
- Existing E-butene meso and Z-butene enantiomeric alternatives are retained; cyclic trans relationships remain the existing bounded anti model. These are not validated cold product distributions.
- Distant physical configuration is preserved, including the existing example where changed CIP priorities relabel S to R. No random conformer determines stereo certainty.
- Multiple validated net alternatives remain selectable without claiming selective one-site conversion or additive stereoisomer yields.
- Near/remote oxygen restrictions, close diene capture including 1,7-octadiene, internal aryl restrictions and radical negatives remain unchanged.
- Authenticated public match/diagram calls preserve conditional 2D, while run rejects cooled Cl₂ before conformer embedding, including stale ambient IDs and fabricated cooling metadata.
- Conditional 2D mapped species retain correspondence with the same independently generated **ambient** 3D atom links. This is not evidence of a cooled 3D result.
- The chlorination mechanism remains honestly **net changes only** (`mechanism: null`); no resolved chloronium mechanism or intermediates were added.
- Calculators remain complete-conversion theoretical upper bounds with conditional confidence and no yield/selectivity prediction. Alternative results must not be summed.

## 5. Verification and preservation

Fresh baseline before changes: **2,081 Python + 2,111 JavaScript = 4,192 passing tests**.

Final regression result: **2,096 Python + 2,123 JavaScript = 4,219 passing tests**, no failures or skips. The 27 new tests supplement all 4,192 previous tests; no existing tests were removed or changed.

- TypeScript and production build pass (`pnpm run build`). Existing dependency-directive and large-bundle warnings remain; no new build failure was observed.
- All **347 frozen observations**, including recorded production fingerprints, are exactly equal before and after. Totals: **155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported, one pre-existing incorrect result**. Chlorination remains **9/14 fully supported (64.3%)**, with its additional negative control correctly rejected. No cold rows were inserted or rescored.
- All **100 public temperature/pathway observations** match except the intended cooled-Cl₂ explanatory text. Replacing that exact old string with the new one yields deep equality: no product, site, stereo, permission, equation or calculator arithmetic changes.
- Companion v1.0.0 and separate diagnostic replay both pass with no failures. Their evidence-gated totals remain separate from diagnostic generation; diagnostic counts of 10/12/11 for dihydroxylation/X₂/HX are not new validated cooling coverage.
- Desktop **1440 px** and mobile **320 px** Chrome checks pass for cooled Cl₂ conditional 2D, blocked 3D/Compare/run actions, visible guidance, calculator arithmetic, net-only mechanism, ambient 3D, clearing old products/amounts, aqueous capture and radical exclusions. A delayed ambient run response cannot restore a product after cooling is selected. No horizontal document overflow or uncaught page error was observed.
- Browser calculator display rounds the independently checked 0.155068 g theoretical mass to 0.15507 g; the test accounts for existing display rounding, not altered arithmetic.
- Previous cooled Br₂, mCPBA and bounded perbenzoic-acid browser regressions pass.
- UI/UX Pro Max was used only to check disabled-state clarity and responsive interaction; no design recommendations were implemented. Existing expanded confidence text is verbose on a narrow screen; layout/copy deduplication is outside this phase.

QA logs, retrieved primary patent HTML and screenshots: `/private/tmp/molecule-cooling-phase4.2UuLge` (temporary local artifacts). Preservation and whitespace check results are recorded on completion below.

Preservation hashes checked all 487 pre-existing files captured under server, src, tests, scripts, docs and benchmarks: **only `server/reaction_temperature_profiles.py` changed**, as intended. Its change is limited to the explanatory string, not permissions. The two new test files and this report are additions. Existing UI sources, all reaction-rule modules, the frozen audit and companion inputs are unchanged. Tracked and new-file whitespace checks pass.

Headless browser contexts were closed and the verified isolated localhost QA server was stopped after verification. No user development service was stopped. Nothing was pushed, merged or deployed.

## 6. Remaining work / stop boundary

The **review and conservative safeguard increment** is complete. The proposed cooled Cl₂ implementation is **deferred at the evidence/formulation gate**, not falsely marked supported. A conformer or a passing finite test suite does not resolve that gate or prove universal chemistry correctness.

No alkyne cooling, further profile, Phase 5, layout work or deployment is authorized by this increment. Stop for review.

Phase 3 remains separately paused: printed **pages 1303 and 1304** of Milas–Sussman (1936) are still needed; page 1302 has been supplied. No Phase 3 chemistry was changed here.
