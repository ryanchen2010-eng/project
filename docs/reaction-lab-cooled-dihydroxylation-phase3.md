# Cooling development — Phase 3: dihydroxylation evidence gate

25 October 2026 · Local review and safeguard tests only

**Revisit status:** A page-1303 indexed experimental excerpt was recovered, but the complete three-page paper remains inaccessible. See the revisit section below. Full-paper review is still blocked; no candidate was enabled.

## Decision: do not enable the candidate yet

**The evidence gate has not passed. Cooled dihydroxylation 3D was not implemented.** The Phase 3 plan expressly requires source/formulation and product-release verification before registering `cooled-osmium-peroxide-diol-v1`; otherwise the existing conditional 2D/no-cooled-3D behavior must remain.

The review and boundary testing are finished, but the proposed feature is deferred—not described as a completed cooled profile. No production file, existing test, chemistry rule, layout, calculator, curated example or frozen benchmark was modified. Added only two separate Phase 3 test files and this report. No GitHub push, merge, deployment or frozen-beta change; no subsequent phase started.

The reviewed registry therefore remains **three profiles across two reaction types**: Br₂ bromination, mCPBA epoxidation and bounded perbenzoic-acid epoxidation. The dihydroxylation candidate is not executable or advertised as reviewed.

## Evidence review

### E07: primary experimental paper remains unavailable

Milas and Sussman, [The Hydroxylation of the Double Bond](https://doi.org/10.1021/ja01298a065), JACS 1936, 58, 1302–1304, remains the plan's lead. The [three-page scan](https://electronicsandbooks.com/edt/manual/Magazine/J/Journal%20of%20the%20American%20Chemical%20Society%20US/1936%20%20%28vol%20058%29/07%20%20%281067-1320%29/1302-1304.pdf) could not be retrieved through the web reader or direct archive requests. Both HTTPS host variants failed to connect; an HTTP request timed out. The ACS article/PDF endpoint was inaccessible/403.

Search-index fragments are not a substitute for inspection of the complete experimental section. This review does **not** claim to have verified all three pages, an experimental aqueous-release sequence, a continuous temperature range or an independently applicable substrate table.

### Accessible primary corroboration does not close the model-specific gate

Milas's [US2437648A primary patent](https://patents.google.com/patent/US2437648A/en) describes initially substantially anhydrous peroxide/tertiary-alcohol systems, multiple catalysts and oxidation endpoints. It includes cold examples, but these do not establish the proposed narrow, non-stereogenic hydrocarbon/aqueous-release profile. Some involve conjugated cyclic substrates or functionalized molecules outside current rule scope. Broad patent claims are not individual experimental validation for every eligible graph.

The existing rule cites [Organic Syntheses CV6P0342](https://www.orgsyn.org/demo.aspx?prep=CV6P0342). Its checked procedure uses Os/NMO at room temperature, not the candidate cold H₂O₂ system. Its discussion also warns of further oxidation with peroxide. It cannot be reused as proof of this candidate's cold formulation or free-diol reporting conditions.

These findings do not show that cold dihydroxylation is chemically impossible. They show that this specific software profile has not yet met its agreed evidence/representation gate. No reaction-rate, yield, selectivity or safety conclusion is drawn.

## Current engine and representation findings

| Area | Verified behavior | Why cooling alone is insufficient |
| --- | --- | --- |
| Oxidant | Actual neutral H₂O₂; another peroxide, NMO or a matching name cannot substitute. | Evidence for a different oxidant is not transferable. |
| Activation | Existing `osmium` selection is required. | The generic selector does not specify every experimental catalyst formulation. |
| Medium | Existing categories are dry, aqueous, ethanol/protic and polar-aprotic. Solvent-specific dihydroxylation compatibility remains unevaluated. | Ethanol is not tert-butanol; “dry” is not proof of a named solvent/formulation. A future named assumption needs an evidence-backed contract. |
| Product release | Explicit `aqueous-release` assumption is required. Work-up species are not mapped. | Recovering a glycol in another preparation does not independently validate this particular aqueous-release history. |
| Net transformation | C=C becomes C–C, formal peroxide O–O breaks and two C–O bonds form. | This inventory is not a resolved catalytic osmium mechanism or literal elementary atom provenance. |
| Stereochemistry | Existing validated syn structures/alternatives and distant configurations remain unchanged. | The proposed non-stereogenic starting scope cannot justify all E/Z-derived products or facial selectivity. |
| Confidence | Eligible cooled inputs receive a conditional 2D net graph; run/3D is blocked. | Structural compatibility is distinct from reviewed cooled applicability. |

Ambient/unset existing net-model permission still requires osmium and confirmed release. Heated conditions remain unvalidated. No selective mono-dihydroxylation, overoxidation suppression, catalyst cycle, cyclic-osmate intermediate or complete mechanism was added.

## New separate tests

Added `tests/test_cooled_dihydroxylation_phase3.py` and `tests/cooled-dihydroxylation-phase3.test.mjs`, each containing **10 tests**. These are versioned evidence-gate fixtures, not a new benchmark or experimental cooling-coverage claim.

Independent 2D net-product oracles cover ethene, 2-methylpropene, a terminal alkene with identical ethyl substituents and tetramethylethylene. None creates a local stereocenter. For each, both input orders verify products, no invented coproduct, charge/atom conservation, four formal bond changes, formal peroxide O/H maps, 1:1 bookkeeping and complete peroxide molar mass. Existing ambient 3D and 2D/3D atom correspondence are checked separately.

Other checks cover specified E/Z substrates, a distant specified stereocenter, multiple sites, unsupported nearby functionality, wrong oxidants, all existing medium classes, missing osmium/release, unknown conditions, stale ambient option IDs and fabricated candidate-profile metadata. Authenticated public match/diagram APIs retain conditional previews; run rejects cooled generation before embedding. Frontend wording and calculator context cannot create permission.

The calculator still permits conditional theoretical arithmetic without asserting experimental conversion. An independent isobutylene example gives 0.001 mol → 0.090122 g theoretical diol; this is not a measured or predicted cold yield. Osmium cycling and release species remain omitted, not calculated consumed reagents.

## Verification

- Fresh starting regression: **2,071 Python + 2,101 JavaScript = 4,172 passing**.
- Focused additions: **10 Python and 10 JavaScript tests pass**.
- Final complete regression: **2,081 Python + 2,111 JavaScript = 4,192 passing**, no failures. All 4,172 previous tests remain passing and unmodified.
- TypeScript and production build (`pnpm run build`, including `tsc`) pass. Existing dependency directive and large-bundle warnings remain; no build failure.
- Python compilation and whitespace checks pass.

### Frozen and separate measurements

All **347 frozen observations**, including production fingerprints, inputs, product expectations/outputs, per-case statuses and summaries, are exactly equal before/after. The counts remain 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported and one pre-existing incorrect-result classification. All pre-existing files in the preservation snapshot remain byte-for-byte unchanged.

The 100 public match/diagram contexts across all existing types/models and four temperature selections are exactly unchanged. Existing tests and frozen/companion artifacts were not edited.

The separate pinned `1.0.0` condition companion and its explicit diagnostic replay both report no failures. Their evidence-gated counts are not increased: 40/53 structural matches, 0/53 evidence-complete and 0/53 independently verified chemistry under that draft manifest. The diagnostic-only overlay generates 33/53 net-model results (including 10/11 dihydroxylation cases), not validated cooled coverage. Five negative controls remain correctly rejected. This draft manifest's evidence backlog is not a claim that the existing educational net rules are broken.

### Real browser checks

Used isolated Chrome and the current production build with the actual local chemistry API. At desktop and 320 px mobile, verified:

- Isobutylene/H₂O₂ offers the existing conditional 2D diol with visible cooling-specific explanation and disabled 3D/Compare/run.
- Existing conditional calculator works and retains theoretical wording.
- No fabricated mapped osmium mechanism appears.
- Switching to the existing ambient model permits 3D; switching back to cooled clears the product and calculator result.
- Removing release confirmation remains blocked.
- A delayed ambient run response cannot restore a product after switching to cooling.
- Document width does not exceed the viewport; no uncaught page errors.

Previously approved cooled Br₂, mCPBA and perbenzoic desktop/mobile browser workflows also pass unchanged. Screenshots were inspected. UI/UX Pro Max was used only to assess the existing disabled-state explanation and interaction; no UI code or styling changed.

Verification logs, before/after observations and screenshots are in `/private/tmp/molecule-cooling-phase3.jjWDyN`; source-access failures are described above. Local QA services are stopped after verification; no external publication is involved.

## Exact requirements to resume this candidate

1. Obtain the complete E07 experimental paper, or another independently applicable primary experimental source, with verifiable cold reaction-stage conditions and identified free-diol endpoint.
2. Resolve the named tert-butanol/peroxide/osmium formulation and whether the current explicit aqueous-release assumption is defensible. If the source uses another release history, do not relabel it as aqueous release or remove the existing release gate.
3. Initially admit only an independently justified non-stereogenic substrate scope. Broader alkenes and E/Z outcomes need their own evidence review; software test success is not experimental validation.
4. Only then register the candidate, add confirmed representable guidance and verify positive cooled public 3D behavior. Do not substitute Os/NMO, permanganate, a different catalyst or an unsupported oxidant.

An uploaded copy of the three-page E07 paper would permit the missing source review to continue. Until then, the candidate remains deferred, with conditional 2D available and no cooled 3D assertion. **Stop here; do not proceed to another cooling phase.**

## Phase 3 revisit — original-paper access and page-specific finding

This section supplements the original review above; it does not represent a completed reading of pages 1302–1304. The user requested full experimental inspection, not reconstruction from snippets. No PDF was attached, and no local copy was found in the task's attachment/workspace locations.

### Access and reading record

| Source page | What was obtained in this revisit | What can be claimed |
| --- | --- | --- |
| 1302 | A search-index fragment including the article header, table and catalyst discussion; no complete page image or continuous verified page text. | Not a complete page reading; reagent-preparation context remains unverified. |
| 1303 | An indexed paragraph under the heading “Isobutylene Glycol from Isobutylene,” including the page header. | A bounded excerpt-level observation only, summarized below. Other procedures and surrounding text were not read in full. |
| 1304 | No complete page text or image. | No page-specific experimental claims. |

The DOI, ACS PDF, public archive variants, independent web-reader fetch and PDF screenshot attempts still did not deliver all three pages. A new direct archive download failed to connect. Search indexing is partial access, not successful retrieval of the original PDF. **The explicit “read all three pages” task remains incomplete.**

### Page 1303 — demonstrated cold isobutylene paragraph, excerpt only

Source: [indexed original-paper scan, printed page 1303](https://electronicsandbooks.com/edt/manual/Magazine/J/Journal%20of%20the%20American%20Chemical%20Society%20US/1936%20%20%28vol%20058%29/07%20%20%281067-1320%29/1302-1304.pdf), experimental paragraph identified above.

| Requested item | Explicit in the recovered paragraph |
| --- | --- |
| Substrate and medium | Isobutylene, 4.3 g (0.0768 mol), dissolved in 36.3 g tert-butanol. |
| Reagent | 39.3 mL (0.0768 mol) of a reagent reported as 6.62% hydrogen peroxide. |
| Catalyst | 0.75 mL of a reported 0.5% OsO₄ solution in tert-butanol. |
| Reaction temperature and duration | Ice-bath cooling; overnight at 0 °C, completion reported the next day. |
| Isolated product | Isobutylene glycol, identified through fractionation and comparison of physical properties. |
| Work-up stated here | Fractionation; collection of the 176–178 °C fraction. No aqueous-release step is described in this paragraph. |

“Overnight” is not an exact hour count. Percentage bases, full reagent preparation, residual water and omitted surrounding qualifications cannot be independently established from this excerpt. Fractionation occurs after the cold reaction stage; it is not evidence that product isolation stays at 0 °C. Absence of water addition in this paragraph is not proof that no water is used anywhere in the complete paper. No experimental yield from this excerpt is used as a software yield prediction.

### Engine check and decision

The existing engine represents isobutylene → 2-methylpropane-1,2-diol as `C=C(C)C` → `CC(C)(O)CO`, with no newly stereogenic center. The existing Phase 3 independent oracle, charge/atom inventory, four net bond changes and 2D/3D correspondence tests cover that graph. Formal peroxide O/H maps remain bookkeeping, not an experimentally established catalyst-oxygen or proton-exchange mechanism.

This strengthens the parent-substrate lead but does not approve the current candidate:

1. Complete original-paper inspection is still missing, so the full list of cooled experiments cannot honestly be reported.
2. The explicit excerpt describes fractionation, not the engine's required `aqueous-release` assumption. The reporting assumption must not be relabeled as a documented experimental step. Its defensibility still requires review of the full formulation and release history.
3. Generic `dry`, `ethanolic-protic` and `osmium` selections are not verified declarations of this particular tert-butanol/peroxide/OsO₄ formulation. In particular, ethanol is not tert-butanol.
4. A non-stereogenic parent observation does not justify broadening to every alkene, E/Z-derived outcome or competing functional-group environment.

**Final decision for this revisit: retain the restriction.** No production code, condition field, reagent model, stereochemical rule, profile registration or test expectation was changed. No new tests were needed; the existing focused safeguard suites were included in the complete regression rerun. No Phase 4 work was performed.

Please supply the actual three-page PDF or legible images of printed pages 1302–1304 to complete the requested evidence review. A DOI alone has not provided accessible full text in this environment.

### Fresh verification for the revisit

Verification logs are stored separately under `/private/tmp/molecule-cooling-phase3-revisit.GNwWdn`. Fresh results:

- **2,081 Python + 2,111 JavaScript = 4,192 passing tests**, no failures. No tests added, removed or changed in this revisit.
- `pnpm run build` passes, including TypeScript; existing dependency-directive and large-bundle warnings remain.
- Frozen audit: all 347 observations and source fingerprints exactly equal to the prior Phase 3 output; classifications remain 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported and one pre-existing incorrect result.
- All 100 public API temperature/pathway observations exactly equal to the prior output.
- Fresh desktop/320 px Chrome checks pass for conditional diols, ambient 3D, cooled blocking, theoretical calculator context, missing release and delayed-response invalidation. The Br₂, mCPBA and perbenzoic regression browser scripts also pass, with no uncaught page errors. Existing screenshots were regenerated by the same temporary QA scripts and inspected.
- Preservation hashes confirm that only this report changed among pre-existing task files. Production sources, UI, tests, curated examples and frozen/companion benchmarks remain byte-for-byte unchanged. Whitespace checks pass.

Local QA server and headless browsers were stopped after checks. Nothing was pushed, merged or deployed. No source or benchmark approval is inferred from a successful build or conformer.
