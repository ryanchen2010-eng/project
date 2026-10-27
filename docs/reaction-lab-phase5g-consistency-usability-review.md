# Phase 5G — Alcohol-family and guided-conditions consistency review

Reviewed 2026-10-17 (America/Toronto). **Read-only review completed.** No production code, existing test, benchmark, Calculator formula, curated example, condition profile, chemistry permission or layout was changed. No deployment occurred.

## 1. Executive summary

The four scoped alcohol transformations and the two guided models retain their intended boundaries. In the inspected cases, their net products, represented atom/charge conservation, site mapping and 2D/3D correspondence agree. Primary-alcohol aldehyde generation remains conditional 2D only. Secondary guidance cannot qualify primary alcohols or broaden the bounded sodium/mono-oxygen substrate scope. Lindlar guidance cannot qualify selective multisite reduction or invent a solvent/stopping protocol.

All **3,674 existing tests pass: 1,825 Python + 1,849 JavaScript**. TypeScript, production build and whitespace checks pass. Every complete result row of the **347-case frozen benchmark is identical to Phase 5F**. The registry still has 24 pathway types. These finite checks are not universal chemistry or experimental certification.

There are nevertheless confirmed confidence/presentation inconsistencies:

- The adjacent legacy **aldehyde-to-acid** pathway can ignore unsupported extra condition inputs and still generate 3D. It lacks the newer evidence/calculator-context contract.
- The top-level matching response calls primary/secondary alcohol oxidation `Supported` even when its own per-option evidence blocks 3D or says no qualified profile exists.
- Secondary guidance can headline generic-water replacement as “Missing required settings,” although its review correctly calls this a replacement and requires consent.
- A blocked Lindlar 2D preview still invites finding an atom “in both views.”
- Correct caveats are repetitive, and editing conditions clears pathway selection; Lindlar guidance then requires reselection to reappear.

Recommendation: a small **confidence-contract and explanation consistency phase**, not more presets or broader chemistry. The implemented guides did not bypass backend gates in this audit.

## 2. Alcohol-family correctness review

| Pathway | Actual model and net accounting | Stereo/mechanism confidence | Review outcome |
| --- | --- | --- | --- |
| Alcohol dehydration | Actual sulfuric acid; explicit acid/heated confirmation. Alcohol → selected alkene + water. Acid excluded from consumed amounts. | Reacting carbons become sp2; distant configurations checked. E/Z-capable new alkenes remain unsigned and 3D-blocked. No complete mapped acid cycle. | Consistent within bounded acyclic scope. |
| Alcohol substitution | Actual HBr/HI, or bounded tertiary HCl. Alcohol + HX → haloalkane + water; HX consumed 1:1. | Methyl/ordinary primary SN2-type and tertiary SN1-type **rationales**, not imported alkyl-halide elementary mechanisms. Secondary/benzylic partition or unresolved product stereo stays conditional. | Consistent; does not treat bare OH as a leaving group. |
| Primary oxidation | Actual alkali hypochlorite; original alcohol O becomes aldehyde O. Removed C–H/O–H form formal water with oxidant O; actual chloride salt retained. | No implemented selective-aldehyde profile; all asserted aldehyde 3D blocked. No detailed oxidation mechanism. | Correctly distinguishes a possible net stage from an established endpoint. |
| Secondary oxidation | Actual NaOCl plus explicit NaOCl/acetic-acid declaration, aqueous medium, ambient, no extra activation, first stage. Original O becomes ketone O; formal water/chloride accounted for. | Selected center becomes untagged sp2, distant physical configuration checked independently of CIP-label retention. No detailed oxidation mechanism. | Correct within the existing saturated mono-oxygen, acyclic/single 5–7-membered ring scope. |

Classification excludes ethers, phenols and carboxylic acids from ordinary alcohol-site matching. Methanol is handled as the methyl/primary oxidation limit, but cannot dehydrate without a beta carbon/H. Tertiary alcohols do not undergo ordinary alcohol-to-carbonyl oxidation. A change of a distant CIP label is not automatically physical inversion; existing independent coordinate/CIP regression checks pass.

New independent public-API probes include primary, secondary and tertiary alcohols; remote specified stereo; extra ether/OH; non-sodium hypochlorite; an eight-membered ring; primary versus secondary/tertiary HX substitution; missing dehydration activation; cyclic dehydration; and internal versus terminal Lindlar products. All literal expected graph/generation-gate checks pass. Multiple secondary oxidation sites give separate unsigned net options, not experimental selective mono-oxidation.

Interactions with SN1/SN2/E1/E2 are appropriately **not identical eligibility rules**. OH needs activation to water; an alkyl halide already has a different leaving-group environment. Alcohol substitution does not inherit a universal SN2 inversion permission. Primary dehydration does not invent a free primary carbocation; secondary/tertiary E1-type rationale does not claim the implemented alkyl-halide E1 sequence is an alcohol mechanism. Heating/other oxygen sites expose competition warnings rather than invented winner/ratio predictions. Existing SN1/SN2/E1/E2 mechanism, conservation and stereo tests remain passing.

Source scope was checked, not promoted into new permissions. The [2024 primary-alcohol dehydration study](https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc01038h) discusses catalyst-dependent and ether-mediated behavior; it does not make one “Heated” category an exact general protocol. The [Gerrard–Madden–Tolcher alcohol/HX paper](https://onlinelibrary.wiley.com/doi/abs/10.1002/jctb.5010050104) emphasizes activation and formulation-dependent mechanistic behavior. Neither justifies assuming one stereochemical route for every secondary alcohol. [Ether-cleavage research](https://pubs.rsc.org/en/content/articlelanding/2017/ob/c7ob01096f) supports treating ether retention as formulation-dependent, not guaranteed by distance alone.

## 3. Guided Conditions consistency review

| Check | Secondary NaOCl/acetic-acid guide | H₂/Lindlar guide |
| --- | --- | --- |
| Backend authority | Describes existing profile/scope and assessment. | Copies the existing catalyst profile and prospectively uses the same condition assessor. |
| Review/apply | Proposed medium, temperature, activation and stage listed. Work-up clear shown when needed. | Catalyst replacement and explicit unrelated stage/work-up clears only. |
| Consent | Conflicting selections require an unchecked confirmation. When all fields are missing, explicit Apply is the consent action. | Every actionable patch requires unchecked confirmation. |
| Preserve selections | Matching values retained; generic water is not falsely accepted as acetic acid. | Medium/temperature explicitly preserved, including unknown values. No invented solvent/pressure/stopping settings. |
| Scope exclusions | Primary, extra O, unscreened rings/aromatics, non-Na and competing sites cannot gain qualification. | Multisite single-site bookkeeping remains outside selective 3D scope. |
| Unsupported declarations | Unknown/conflicting uneditable input cannot be silently discarded. | Unknown keys, secondary namespace, unvalidated medium/heating cannot be erased to obtain permission. |
| Apply/revalidation | Exact context signature, revision checks, backend rematch; 2D reselection only. | Same, and no suggestion to switch models merely from loading a complete-reduction example. |
| 3D permission | Separate explicit action, independently rechecked by run API. | Separate explicit action; net-model qualification only. |

No forged `canRun`, guidance state or profile declaration grants output. Wrong condition enums are rejected. Detached stale panel actions and delayed responses are covered by the existing epoch/signature tests. Reaction IDs are request-local site addresses, **not global content-bound authorizations**: a reused address may legitimately name a valid site on a changed valid molecule, but the server reconstructs the current graph rather than returning a stale product. Unsupported changed contexts remain blocked.

The secondary model's primary evidence supports bounded ketone formation, not universal spectator inertness or actual conversion. [Stevens, Chapman and Weller, JOC 1980](https://ursula.chem.yale.edu/~chem220/PROBSETS/PS13spr/PS9-S13-ans/Stevens1980JOC.pdf), pp. 2030–2032, includes secondary examples and different primary-alcohol behavior. Its wider examples do not automatically expand this engine's intentionally narrower scope.

The [Lindlar/Dubuis Organic Syntheses preparation](https://www.orgsyn.org/demo.aspx?prep=CV5P0880) supports partial/cis internal net chemistry but also distinguishes medium and endpoint handling. Thus the current guide honestly qualifies a **net conformer**, not a fully specified laboratory protocol. The [selective-aldehyde Organic Syntheses reference](https://www.orgsyn.org/demo.aspx?prep=CV8P0367) uses a distinct catalyst/formulation and endpoint context absent here. No selector or secondary profile supplies that missing implementation. No PCC/Dess–Martin was added.

## 4. Confirmed errors or contradictions

### F1 — Adjacent aldehyde oxidation ignores unassessed conditions

Authenticated public reproduction: pentanal `CCCCC=O` + sodium hypochlorite, `solvent=aqueous-protic`, `oxidationStage=further`, returns pentanoic-acid reporting connectivity and 3D (HTTP 200). Adding **each separately** of `catalyst=radical`, `workup=aqueous-release`, unknown `pressure=unknown`, or the secondary-oxidation namespace still returns `state=aligned` and HTTP 200. Adding `catalyst=acid` changes assessment to incomplete but still returns 3D.

Cause: the legacy fallback in `server/chemistry_server.py:488` compares the old profile, ignores unsupported fields and only notices some extra catalysts. The run function has no aldehyde-oxidation confidence gate. Its diagram has no assessment, only the generic net note; stoichiometry has no confidence context.

**Classification: Confidence or condition validation**, with a chemistry-reporting risk. This is not evidence that pentanoic-acid connectivity is intrinsically incorrect. The engine intentionally calls it a neutral acid reporting form; pH, dominant solution species and isolated acid work-up are unresolved. It must not imply that selecting water establishes neutral isolated acid or that radical/unknown conditions have been validated. This is adjacent legacy behavior, not a bypass of either guide or the primary-aldehyde gate.

### F2 — Top-level API support state disagrees with oxidation evidence

`match_reactions` uses membership in `NET_PATHWAYS` for top-level `supportState` (`server/chemistry_server.py:677`). Alcohol oxidation is handled through primary/secondary metadata instead. Ethanol + NaOCl under the secondary profile returns **`supportState=Supported`**, while its option has `canRun=false`, `conditionCompleteEligibility=false` and “no validated profile.” An incomplete secondary case likewise returns `Supported`.

**Classification: Confidence or condition validation.** The current browser correctly uses per-option evidence and disables 3D, so no observed frontend permission leak follows. External consumers must not use the coarse top-level field as chemical qualification. A future additive, versioned clarification should distinguish structural support from condition/output permission.

### F3 — Replacement headline versus review state

For 2-propanol with generic aqueous medium and the other secondary settings matching, guidance headlines “Missing required settings” but marks medium “replace selected setting.” The row detects the absent acetic-acid declaration; the panel summary derives conflict only from assessment issues (`server/reaction_condition_guidance.py:126`), not all review rows.

**Classification: Usability.** Consent is enforced and the original selection is preserved until Apply. Fix the description, not the chemistry gate.

### F4 — Conditional 2D inspector suggests an unavailable second view

Partial propyne hydrogenation with ordinary metal selected correctly blocks 3D, but its atom inspector says “Hover an atom to find it in both views.” Alcohol oxidation has a special conditional-2D caption; other blocked net pathways do not (`src/reaction-lab.ts:605`).

**Classification: Visualization.** Mapped 2D atoms are valid; the instruction is misleading, not a broken map or secretly generated 3D.

No new incorrect target-family product, atom-balance or mapped-stereo result was observed in the tested cases. That limited finding does not certify untested chemistry.

## 5. Chemically justified restrictions

- Tertiary alcohol carbonyl oxidation is rejected without inventing C–C cleavage.
- Rearrangement-prone dehydration/HX cases, nearby oxygen capture, acid-sensitive ethers and unresolved secondary HX mechanism/stereo are not repaired with arbitrary dropdowns.
- Dehydration E/Z ambiguity and Lindlar multisite competition block asserted single-product 3D; 2D bookkeeping can remain useful.
- Secondary qualified scope excludes non-sodium reagent, extra oxygen, aromatic/complex-ring environments and unvalidated competing sites. These are bounded implementation/evidence restrictions, not universal claims that those molecules cannot oxidize.
- Primary aldehyde scope remains a genuine missing model, not merely missing user selections. No implemented dropdown combination resolves it.
- NaOCl/acetic-acid and Lindlar requirements should not be copied to another pathway. Actual reagent graphs, not labels or molecular formulas, establish identity.

Some restrictions could be expanded by future independent validation. No such expansion was made or scientifically implied here.

## 6. Unsupported mechanisms and chemistry

The four alcohol pathways and Lindlar return **null complete mapped mechanisms** in the checked public previews. Correct net bond edits/provenance do not resolve hypochlorite intermediates, the full acid catalytic cycle, HX protonation/departure/capture or catalytic surface chemistry. No new electron-arrow sequence, free primary cation, perfect racemization, exact stereo ratio or experimental yield was invented.

Formal water hydrogens/oxygens and salt maps balance the represented net equation; they are not experimental isotope histories under solution proton exchange. Distant physical stereo is checked; local oxidation/dehydration stereocenters becoming planar lose their tags. Unresolved HX configurations are unsigned and cannot acquire certainty from a random conformer. Lindlar internal geometry uses the validated mapped syn/CIP rule; terminal products have no invented E/Z.

Primary selective-aldehyde conditions, arbitrary HX activation, detailed alcohol mechanisms, broader secondary oxidation profiles and experimental mono-site selectivity remain unsupported. A source citation or software pass is not admission of a new experimental profile.

## 7. Condition-confidence issues

Use five separate questions when interpreting existing results:

| Question | Current evidence and limitation |
| --- | --- |
| Is the selected graph/site supported? | Structural match; independent of whether conditions are complete. |
| Are required represented model settings supplied? | Missing/conflicting inputs and per-option assessment. Not an exact solvent/concentration/time protocol. |
| Can this model render the theoretical net product? | Backend run gate; a conformer is not evidence of experimental formation. |
| Is chemistry unsupported or competing? | Specific rejection/scope reasons; changing controls cannot solve every chemistry gap. |
| What independent evidence is approved? | Source/model review and separately approved companion cases; never inferred from test count or 3D success. |

The two guides mostly communicate this correctly, but “Model conditions match” and secondary `conditionCompleteEligibility` can be overread as experimental completeness. Secondary evidence also explicitly says `model-assumptions-only`; Lindlar explicitly says solvent/pressure/stopping unvalidated. These qualifiers must survive any future wording simplification.

The legacy aldehyde pathway and top-level oxidation state are the principal cross-pathway exceptions. They should be brought into a consistent **confidence vocabulary and input-validation contract**, not treated as permission to weaken the newer gates. The neutral-acid reporting/work-up question needs an explicit decision before any acid-isolation claim.

## 8. Student usability findings

This was an expert walkthrough, **not a recruited student usability study**.

Browser-verified workflow:

1. Selected 2-propanol in Explorer and transferred it as molecule 1, retaining exact identity.
2. Entered recognized sodium hypochlorite; missing-settings guide appeared without applying anything.
3. Reviewed proposed settings and applied them. The backend revalidated and selected 2D; 3D did not start automatically.
4. Explicitly requested Compare; selected original alcohol Oxygen 4 and observed its ketone/3D linkage.
5. Calculated the theoretical ketone amount. Changing the medium back to generic water cleared the model, atom selection, equation selection and old yield. The replacement checkbox was unchecked and Apply disabled.
6. Replaced the substrate with ethanol; primary no-profile explanation appeared, conditional 2D worked and 3D stayed disabled.
7. Loaded the existing ethanol Builder drawing, validated it, and transferred it to Reaction Lab as the same ethanol identity. No examples were added.
8. Loaded the existing complete-propyne example; selected partial reduction to discover its guide, reviewed metal → Lindlar and preserved unknown medium/temperature, confirmed and applied. 2D first, separate Compare, linked Carbon 2.
9. Reloaded: Lindlar and exact reactants restored, but no selected pathway, old 3D or calculated result restored. Selecting complete reduction did not inherit partial permissions. Replacing H₂ with water removed the choices and disabled output.

Source/regression/API checks additionally cover stale asynchronous actions, forged values, changed structures, distinct/equivalent sites and site selection. The walkthrough did not manually draw every negative structure or click every multisite combination; those broader cases are automated, not claimed as human trials.

One rapid back-to-back Builder “Load ethanol” / “Check” action issued HTTP 422 before the loaded drawing was ready. Waiting for the visible loaded state and checking again produced valid ethanol and a successful transfer. The load handler does not disable the separate Check control while awaiting editor replacement; this is a reproducible-risk timing observation, not evidence of incorrect ethanol chemistry. The failed request body was not captured, so its precise backend rejection reason is not asserted. No Builder fix was made.

Usability friction:

- “Net model,” “profile,” “first stage,” `oxidationStage` and “none added” require interpretation. The last means **no additional** catalyst, not absence of acidity from HX.
- The same long warning appears in option guidance, status, result banner, tooltips, diagram note and calculator. In particular, metal/Lindlar conflict explanations repeat a sentence within one message.
- A condition change clears selected pathway; Lindlar guidance is deliberately hidden until partial is selected again. Safe invalidation should remain, but the extra selection step is hard to discover.
- The selected site is presented largely by atom numbers. Equivalent-site aliases and actual distinct alternatives need a concise distinction, not an experimental selectivity promise.
- “3D unavailable until requirements or limitations are resolved” can sound actionable for primary oxidation even when **no current control can resolve it**. Its dedicated no-profile guide is clearer.
- The top-level API contradiction and blocked-view atom prompt should not survive a general guidance rollout.

Preserve explicit consent, backend revalidation and separate 3D actions in any later improvement. No interface changes were made now.

## 9. Public API and Calculator consistency

The additional authenticated diagnostic checked **28 input scenarios, 24 scoped reaction options**: 24 successful conditional/qualified diagrams; **7 allowed 3D runs and 17 correctly blocked runs**; no literal product, charge, map, stoichiometry or linked-atom failures. Six separate adjacent legacy observations reproduced F1. The detailed evidence is in the accompanying JSON.

The initial temporary public diagnostic exceeded the default test-app 40-requests/minute budget and produced HTTP 429; those were harness throttling, not chemistry failures. It was rerun with the existing configurable budget increased **only in the temporary in-process test instance**. No running website or production limiter was changed. The final diagnostic has no throttled cases. The separate transient Builder 422 observation is documented in section 8; the loaded-state retry succeeded.

Calculator integration remains theoretical and independent of asserted 3D. Browser check: **0.060096 g 2-propanol + 0.074442 g NaOCl** represents 1 mmol each and gives **0.058080 g / 0.001 mol acetone**, with both inputs exhausted in the formal 1:1 equation. Full NaOCl formula-unit mass is counted; acetic acid is not a consumed third reagent. Conditional primary amounts remain explicitly hypothetical while 3D is blocked.

Existing fixtures check dehydration acid exclusion, consumed HX, one-H₂ partial versus two-H₂ complete reduction, limiting amounts, target amounts, zero inputs and unit conversions. Alternatives are not additive yields. The observed issue is the adjacent aldehyde pathway's missing condition context, not a new arithmetic defect. Calculator formulas and pages are unchanged.

## 10. Frozen benchmark verification

The parent SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. Exactly **A001 through A347**, no duplicates or missing IDs. The accompanying JSON enumerates every ID with before/after status; all complete rows, not merely counts, match Phase 5F.

| Scope | Structural positives | Frozen strict full | Other positive statuses | Controls |
| --- | --- | --- | --- | --- |
| Primary alcohol oxidation | 7/10 | 0/10 | 7 partial, 3 unsupported | Shared oxidation controls below |
| Secondary alcohol oxidation | 2/2 | 0/2 | 2 partial | Shared oxidation controls below |
| Combined alcohol oxidation | 9/12 | 0/12 | 9 partial, 3 unsupported | 2 correctly rejected |
| Alcohol dehydration | 4/8 | 2/8 | 2 partial, 4 unsupported | 2 correctly rejected |
| Alcohol substitution | 7/11 | 3/11 | 4 partial, 4 unsupported | 2 correctly rejected |
| Lindlar partial reduction | 8/10 | 7/10 | 1 partial, 2 unsupported | 1 correctly rejected |
| Adjacent aldehyde oxidation | 7/11 | 7/11 | 4 unsupported | 2 correctly rejected |

Alcohol-family reconciliation: **37 rows = 31 positive + 6 controls**. Alcohol oxidation is A080–A089 and A100–A103; dehydration is A208–A215 plus A225/A226; substitution is A216–A224 plus A227–A230. The other **310 rows** are also enumerated unchanged. Whole benchmark: **156 full + 62 partial + 90 unsupported + 38 correctly rejected + 1 historical incorrect label = 347**; 309 positive/applicable rows and 38 controls.

Interpretation safeguards:

- Secondary A100/A101 lack the explicit profile in frozen inputs. Separate declared-profile replays qualify both theoretical net products; **not** a change to their frozen scores or an experimental guarantee.
- The primary 0/10 is a missing selective model, not repairable merely by selecting ambient/water/first stage.
- A218 tertiary HX has conditional connectivity under frozen heated inputs; ambient can qualify its bounded net model. Secondary/benzylic unresolved cases are not all dropdown-repairable.
- The scorer conflates preview/run failure: its `preview=failed` can mean successful conditional 2D followed by a deliberate 3D block.
- A210 dehydration is historically “full” when a permitted terminal alternative runs although another internal E/Z-capable option stays blocked. Do not interpret a case-level score as every alternative being qualified.
- **A276** remains partial: multisite Lindlar single-site 3D restricted.
- **A304** retains the historical incorrect-result label and the separate proposed-not-applied oracle-defect annotation. Hex-2-yne first HBr addition must retain the original C2–C3 bond position; the frozen second expected connectivity moves it. No expectation, score or annotation was changed.

Separate condition-aware diagnostics, all without failures:

| Existing diagnostic | Cases | Structural positive matches | Theoretical 3D observations |
| --- | --- | --- | --- |
| Dehydration | 40 | 20/20 | 16 allowed options; 16 blocked; 15 positive cases have any allowed, 8 have all options allowed |
| HX alcohol substitution | 45 | 21/21 | 9 allowed options; 13 blocked |
| Primary oxidation | 40 | 20/20 | All 21 options blocked; no selective profile approved |
| Secondary oxidation | 41 | 25/25 | 16 qualified cases/options; 10 blocked options; A100/A101 separately replayed |
| Lindlar | 52 | Diagnostic uses option-level reporting | 33 options: 19 allowed, 14 blocked |

Pinned companion v1.0.0 remains **58 reviewed rows = 53 positives + 5 controls**, with 289 outside its scope. Default: **40/53 structural**, zero newly approved condition-complete/generation/independent-review results, five controls rejected. Separate draft-overlay diagnostics generate 33 cases; that is not approval. Version comparison: parent unchanged, no case/profile/defect changes. The 24 pathway registry is unchanged.

## 11. Total passing tests and integrity

| Verification | Result |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests` | 1,825 pass; 116.442 seconds |
| Node `--test tests/*.test.mjs` | 1,849 pass; 0 fail/cancelled/skipped/todo |
| Existing frozen audit | 347 rows identical to Phase 5F |
| Existing companion default/diagnostic/version checks | Pass; original evidence distinctions preserved |
| Five existing pathway diagnostics | No failures |
| Additional temporary public diagnostic | 28 cases, 24 scoped options, no failures after correcting harness throttling |
| Mechanism, mapping, linked views, calculator fixtures | Existing suites and representative public/browser checks pass |
| TypeScript `tsc --noEmit` | Pass |
| Vite production build | Pass; 9.80 seconds; existing large-chunk warning remains |
| `git diff --check` and new-report text whitespace | Pass |
| Protected-file snapshot | All 229 pre-existing source/test/script/benchmark/root files byte-identical |

No tests were added to or changed in the regression suite. Temporary diagnostic code/logs are separate verification artifacts, not new visible examples or benchmark rows. Browser screenshots record observations only. The owned temporary server/tab were cleaned up after the review.

## 12. Five highest-priority next improvements

Ranked by chemistry-confidence impact first, then implementation risk. These are recommendations, **not implemented fixes**.

| Rank | Recommendation | Classification | Risk / acceptance boundary |
| --- | --- | --- | --- |
| 1 | Add explicit evidence, unsupported-input assessment and run/diagram/calculator confidence to the existing aldehyde-to-acid reporting pathway. Decide neutral reporting form versus solution/work-up claims explicitly. | Confidence or condition validation; chemistry correctness review required for speciation claims | Medium. Keep valid conditional net connectivity; do not invent acid work-up, radical chemistry or a new profile. Reproduce F1 with isolated condition inputs. |
| 2 | Reconcile top-level match support with per-option oxidation evidence and make guide summary conflicts agree with the replacement rows. | Confidence or condition validation | Low–medium. Version/add fields carefully; preserve current consumers and all chemistry gates. “Structurally supported” must not imply qualified output. |
| 3 | Make the chosen pathway/guide easier to rediscover after condition editing while retaining immediate output invalidation and explicit replacement consent. | Usability | Medium asynchronous-state risk. Retain signature/revision checks, rematch changed inputs and never auto-generate 3D. |
| 4 | Consolidate duplicated warnings into concise current-state guidance; use friendly names rather than internal keys and distinguish no-current-profile from fixable missing settings. | Usability | Low chemistry risk but high wording care. Preserve source/evidence scope and theoretical/experimental distinction; no layout redesign or safety-caveat deletion. |
| 5 | Use actual availability when describing atom inspection: mapped 2D-only when blocked; linked 2D/3D only when permitted/loaded. | Visualization | Low. Test Lindlar, dehydration and HX conditional options plus qualified results; no map/index changes. |

Future structural coverage and complete mapped mechanisms should be separate later scopes, not bundled into these confidence fixes. Do not expand secondary multi-oxygen/ring or primary-aldehyde permissions to improve a score.

## 13. Recommended next small implementation scope

First address **F1 only** as a bounded aldehyde-oxidation confidence-contract increment: independently review existing reporting/speciation language, surface unknown/unsupported activation/work-up, carry conditional context into diagrams/calculators and independently gate any asserted 3D. No new reagent systems, products, experimental outcome predictions or expanded structural permissions. Preserve the frozen benchmark inputs and disclose any resulting score changes rather than editing expectations.

If acid/speciation chemistry needs a larger redesign, retain conditional reporting and document the gap rather than forcing an isolated-product claim. Then a separate small presentation increment can handle F2–F4 and guide discoverability, with no chemistry permission expansion. User testing with students/educators should precede a third guided model.

**Phase 5G stops here. No recommended fix or next pathway was started.**

Evidence: [machine-readable results, complete benchmark ID reconciliation and preservation hashes](reaction-lab-phase5g-consistency-usability-results.json).

### Browser observations

![Existing secondary profile and theoretical calculator result](reaction-lab-phase5g-qualified.png)

![Existing Lindlar net model, preserved unknown conditions and linked carbon](reaction-lab-phase5g-lindlar.png)
