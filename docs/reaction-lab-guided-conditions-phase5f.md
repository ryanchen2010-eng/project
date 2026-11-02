# Phase 5F — Guided conditions: existing Lindlar partial-reduction model

Completed 2026-10-17 (America/Toronto). Exactly one additional existing pathway is guided: **alkyne partial hydrogenation with actual H₂ and Lindlar activation**. No chemistry, reagent, structural compatibility, mechanism, product permission, calculator formula, curated example, layout or deployment change. The Phase 5E secondary-oxidation pilot is preserved. This phase stops here.

## 1. Selected profile and evidence scope

The engine already constructs the partial-reduction profile as `{'catalyst': 'lindlar'}`. It independently validates the mapped syn edit, internal cis/Z assignment, terminal non-applicability of E/Z and retained spectator configuration. Phase 5F guides that existing activation selection, not a newly invented condition model.

The checked [Lindlar/Dubuis Organic Syntheses preparation and notes](https://www.orgsyn.org/demo.aspx?prep=CV5P0880), DOI 10.15227/orgsyn.046.0089, support partial reduction and cis internal products, while explicitly warning that uptake does not simply halt at the desired endpoint. Its solvent/additive context cannot be replaced by a generic dropdown. [OpenStax §9.5](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes) independently supports the bounded syn/cis transformation and distinguishes ordinary metal-catalyzed complete reduction.

**Qualification is at the existing net-model level.** No fully specified experimental Lindlar condition profile exists in this engine, and none was created or approved. The scientific support is sufficient to guide an already implemented catalyst choice with its existing restrictions—not to certify solvent, pressure, catalyst state, stopping, conversion or selective mono-reduction. The original confidence label **“Lindlar net model · solvent/pressure/stopping not validated”** remains intact. No fallback reaction was introduced.

## 2. Existing requirements and structural boundaries

| Item | Existing behavior, unchanged |
| --- | --- |
| Reactant identity | Actual neutral H₂; names or guidance declarations cannot substitute for its graph |
| Activation | Existing `lindlar` select value; ordinary Pd/Pt is the complete-reduction model |
| Net stoichiometry | One H₂ per selected C≡C, unlike two for complete reduction |
| Substrate | Screened isolated acyclic C/H/O alkynes; existing size, stereo and spectator policies |
| Internal geometry | Independently validated cis/Z net product |
| Terminal product | No invented E/Z designation |
| Medium | Existing unspecified/dry model convention permits a representative conformer, not a solvent protocol |
| Temperature | Existing ambient/unspecified model convention; heated behavior remains unvalidated |
| Multiple separated alkynes | Selectable mapped 2D bookkeeping only; selective single-site 3D remains blocked |
| Other input | Unknown fields and incompatible oxidation/work-up settings retain their original gates |

Cyclic/conjugated or aromatic-adjacent alkynes, enynes, near-site oxygen/stereo, unscreened competing groups and unsupported electronic/element environments remain excluded. Supported remote alcohol/ether groups and distant stereo inherit no new chemical permission.

## 3. Guided Conditions interface changes

The existing panel and existing selectors are reused. **Choose the partial-hydrogenation option first.** Lindlar guidance does not appear as a competing recommendation when the user has merely loaded or selected a complete-reduction example. The complete-reduction pathway itself receives no new guidance. Secondary-oxidation discovery behaves exactly as in Phase 5E.

The selected partial option names the model, identifies missing/conflicting activation, shows current → suggested values and requires an explicit unchecked confirmation before any apply action—even when activation was missing rather than conflicting. Declining or closing review changes nothing. Replacing ordinary metal explicitly means choosing a different model; it does not claim that metal is invalid for complete hydrogenation.

Only catalyst selection and, after review, clearing unrelated oxidation-stage/diol-release values are suggested. Existing medium and temperature values are displayed as **preserved**, not falsely marked protocol-validated. They are never filled, reset to unknown or replaced with a generic “dry” choice to evade a gate. Unvalidated media, heating and unknown fields receive no apply action.

No new solvent, pressure, initiator, profile-declaration field, dropdown, page or tutorial overlay was added. Details remain collapsed. A small optional metadata flag controls initial discoverability, and the shared panel supports explicit confirmation and a preserved-field display state.

## 4. Frontend/backend contract

The guidance module copies the existing reaction profile and performs a **read-only prospective call to the same existing condition assessor** before offering a patch. It does not implement a parallel chemistry validator. Neither current conditions nor the reaction are mutated by producing guidance.

The metadata's `profileId` is the existing pathway name, **Alkyne partial hydrogenation**, used only to choose direct UI transport. It is not a new approved chemistry profile, is not serialized as a condition and cannot grant generation permission. API requests injecting `profileId`, approval flags, peroxide/light or other unimplemented condition fields remain blocked.

The frontend allows only the existing Lindlar activation control and explicit empty values for unrelated stage/work-up fields in this patch. It preserves exact context signatures, stale-action invalidation, double-apply protection, atomic control updates, draft saving and public revalidation from Phase 5E. The same site is reselected where still returned; only 2D opens automatically. 3D/Compare always requires another user action.

The run API independently reconstructs the reaction and repeats all existing structure, reagent, condition, competition and mapping/stereo checks. A client suggestion or checkbox never establishes chemistry confidence. Reaction/site IDs are **request-local addresses**, not globally content-bound authorization tokens: an ID can name a valid corresponding site on a different valid molecule. Tests verify that such a request reconstructs the correct current C6 product rather than returning an old C4 product; changed unsupported/multisite contexts remain blocked. The frontend separately rejects stale suggestions based on exact structures and conditions.

## 5. Unsupported situations remain blocked

- Several separated alkyne sites: every supported mapped alternative remains conditional; equivalent aliases and distinct products are preserved without a mono-site selectivity claim.
- Unvalidated aqueous/alcoholic/generic-aprotic medium or heating: the guide does not erase the choice to gain 3D permission.
- Unknown condition fields or a leftover secondary-oxidation declaration: no apply patch silently discards them.
- Radical conditions: no radical reaction is enabled. An explicit reviewed switch from the radical selector to Lindlar changes the requested activation model; the original radical request remains blocked. An additional peroxide/light field cannot be repaired by this suggestion.
- Unsupported rings, conjugation, competing reducible groups, invalid stereo and wrong reagents: no new structural match or product is created.
- Primary alcohol → aldehyde: the unresolved endpoint gate remains. No PCC/Dess–Martin or selective-aldehyde profile was introduced.

Theoretical 2D remains available where the existing chemistry supports it. No surface-catalytic mechanism, rates, yield, product ratios, exact stopping or experimental one-site conversion was invented.

## 6. Browser usability verification

Using the unchanged **Fully reduce propyne** example:

1. The complete-reduction option shows propane and two H₂, without Lindlar guidance.
2. Selecting partial reduction displays conditional propene, the metal → Lindlar review and preserved unknown medium/temperature.
3. Before consent, Apply is disabled and fields stay unchanged.
4. Explicit consent/application changes only activation, publicly revalidates and returns to the partial 2D option.
5. Compare is separately requested; Carbon 2 links between propyne, propene and 3D.
6. One mmol each of propyne and H₂ gives the formal **0.042081 g / 0.001 mol propene** result. Visible calculator text identifies unestablished solvent/temperature/pressure and theoretical complete-conversion assumptions.
7. Removing Lindlar clears old 3D, measurements/atom selection and calculator results, and disables generation.
8. An explicitly selected Lindlar value survives reload, but no old selected result/3D or permission is restored.

The original 2-propanol/NaOCl example was separately checked: its original medium-replacement consent, profile application, qualified theoretical acetone Compare and original-oxygen linkage all remain functional. Screenshots are below. Broader substrate, multisite, condition and stale-request scenarios are automated API/panel checks, not new browser-visible examples.

## 7. Tests added and total passing

**54 tests added: 26 Python and 28 JavaScript.** Full final verification passes **1,825 Python + 1,849 JavaScript = 3,674 tests**, retaining all 3,620 existing tests. No pre-existing test or fixture was changed, deleted, skipped or weakened.

New checks include explicit consent and declining changes, preserved settings, correctable versus uneditable input, actual reagent identity, positive/negative substrate fixtures, net-only qualification, switching partial/complete and original pilot behavior, current-structure reconstruction, stale UI/site changes, forged declarations, authentication, linked atom maps, null surface mechanism, exact one-H₂ amounts and theoretical calculator confidence.

A differential test compares complete matching payloads with guidance enabled versus disabled, removing only additive guidance metadata: structures, conditions, scores, products, maps, stereo, reasoning and calculator confidence agree. The existing Lindlar diagnostic passes unchanged: **52 cases, 33 options, 19 verified theoretical runs, 14 correctly blocked options, no failures**. These tests validate finite modeled behavior, not universal experimental correctness.

## 8. Frozen and companion results

All **347 complete frozen result rows are exactly identical to Phase 5E**. Lindlar remains **7/10 strict full**, with two unsupported positives, one partial positive and one correctly rejected control. A276's multisite restriction is unchanged. A100/A101 remain partial with their original incomplete oxidation inputs, and A304's frozen-oracle defect annotation is preserved.

Whole benchmark remains **156 full, 62 partial, 90 unsupported, 38 correctly rejected and one historical incorrect-result label**. Parent SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

The pinned v1.0.0 companion is unchanged: 40/53 structural matches; no newly approved condition-complete, generation or independent-review outcomes; five controls correctly rejected. Separate unvalidated overlays still generate 33 cases. Version comparison reports no changed cases, profiles or defect annotations. No case or solvent protocol was approved merely because guided selection succeeded.

[Machine-readable verification and preservation hashes](reaction-lab-guided-conditions-phase5f-results.json).

## 9. TypeScript, production build and integrity

TypeScript, the production build, `git diff --check` and the changed/new-text whitespace scan pass. The existing large Builder/chunk warning remains.

Production edits are restricted to the read-only guidance module, shared guidance-panel transport/presentation and one initial-discovery filter in Reaction Lab. All chemistry generation, compatibility, condition-assessment, atom/stereo validation and calculator modules remain byte-unchanged. Other pages, CSS, curated data, fixtures, existing tests, HTML, build/container configuration and benchmark manifests remain unchanged. No publication/deployment occurred. Temporary verification tab/server cleanup was performed.

## 10. Remaining usability limitations

This is not a complete experimental Lindlar preset. The panel intentionally cannot repair an unvalidated solvent/heating choice or unknown declaration. Users must not infer that blank medium means safe or scientifically complete conditions.

Changing an input/condition resets the selected pathway under the existing workflow; select partial reduction again to see its contextual guide. No new sticky-selection or workflow redesign was included. Detailed existing confidence explanations can still be long, and the sample library still has no new curated partial-reduction card.

Exactly two reaction models now have actionable guidance: the existing secondary NaOCl/acetic-acid model and the existing Lindlar net model. Primary oxidation has explanatory non-actionable guidance only. No general rollout or arbitrary profile solver exists.

## 11. Recommended next step and stopping point

Test the two guided flows with students/educators before selecting a third model. Prioritize terminology and discoverability feedback, especially partial versus complete reduction and net-model eligibility versus experimental completeness. If a fully specified Lindlar solvent/endpoint profile is desired, that requires a separately scoped, independently evidenced chemistry/condition-model phase; this UI increment does not supply it.

Any next guidance expansion should independently assess its own existing reagent/condition evidence and preserve all relevant limitations. Do not infer permissions from a legacy strict score or copy Lindlar conditions into another pathway. **Phase 5F only is complete; no subsequent phase was started.**

## Browser evidence

![Lindlar review with explicit replacement consent](reaction-lab-guided-conditions-phase5f-review.png)

![Existing Lindlar net-model guidance and linked carbon selection](reaction-lab-guided-conditions-phase5f-lindlar.png)

![Preserved secondary-oxidation guided pilot and original oxygen mapping](reaction-lab-guided-conditions-phase5f-secondary.png)
