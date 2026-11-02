# Phase 5E — Guided reaction conditions pilot

Completed 2026-10-17 (America/Toronto). Scope: one contextual guidance pilot for the existing Phase 5D secondary alcohol → ketone model. No new reaction, oxidant, chemistry permission, detailed mechanism, curated example, calculator formula, deployment or publication. The registry remains at 24 pathway types. No rollout to the other pathways was performed.

## 1. Existing condition-selection architecture

Reaction Lab already has medium, temperature, catalyst/activation and oxidation-stage selects. Existing contextual controls provide alkyne equivalents, finite-chain length and diol release/work-up. `currentConditions()` serializes their values; the special **Aqueous acetic acid · secondary NaOCl** medium maps to `solvent=aqueous-protic` plus the namespaced `secondaryOxidationProfile=naocl-acetic-ketone-v1` declaration.

The backend normalizes inputs, matches actual molecular structures and selected sites, and performs reaction-specific assessment. Its existing assessment/evidence controls 3D eligibility and calculator confidence. Missing conditions, unvalidated alternatives, unsupported inputs and profile-scope limitations are not equivalent to chemical impossibility.

Previously, users discovered the secondary profile by reading long condition notes and manually coordinating four controls. Changing any input already cleared outdated diagrams, 3D, measurements, selected atoms and calculator results. Session storage restored selected compounds and condition values, not a permission to generate products.

## 2. User problem solved

An eligible secondary alcohol could display a conditional option without making the supported combination of settings easy to discover. Generic water did not declare acetic-acid medium. Users could confuse missing settings with missing chemistry or believe a disabled 3D control meant that the molecule could never react.

The pilot puts the supported model and a reviewable set of selections in the existing conditions area. It does not turn a dropdown combination into new scientific evidence.

## 3. Implemented pilot

The compact **Guided conditions** section appears after a matched oxidation option is available. It is initially contextual to an available pilot option and follows the selected reaction thereafter. An unrelated selected pathway, unresolved reactants, a matching error or an input change clears the section.

The user can expand **Review supported settings**, inspect current → required selections, explicitly confirm replacements and choose **Apply supported settings**. Generic Water is explicitly listed as a replacement by the specific acetic-acid medium, rather than being called an existing profile match. Selected conflicting values are never silently overwritten. A conflicting diol-release setting is explicitly listed for clearing.

Applying saves the chosen fields, clears stale results, calls the public matcher again and reselects the same reaction/site option if it is still returned. The updated 2D result opens through the existing selection workflow. It does **not** automatically request 3D; that remains a separate user action. If revalidation fails, no qualified result is invented.

There are no new selectors, pages, overlays or large tutorial forms. Review details, limitations and the profile source remain collapsed. Buttons have explicit button types, and disclosure/checkbox/button controls are keyboard accessible. Guidance is rendered as inert text, not injected HTML.

## 4. Exact supported profile

This reuses **one existing profile**, not a duplicate:

| Model field | Existing required value |
| --- | --- |
| Actual consumed oxidant | Sodium hypochlorite graph |
| Specific profile | `naocl-acetic-ketone-v1` |
| Medium select | Aqueous acetic acid · secondary NaOCl |
| Serialized medium | `aqueous-protic`, with explicit profile declaration |
| Temperature | `ambient` / Room temperature |
| Additional catalyst/activation | `none` / None added |
| Oxidation stage | `first` / alcohol → carbonyl |
| Work-up | No isolated-workup assertion; conflicting diol release can be explicitly cleared |

The Phase 5D required-value literals were moved to the shared `PROFILE_SETTINGS` constant and consumed by the unchanged assessment logic and read-only guidance. The values and permission requirements did not change. The existing scientific evidence, bounded mono-oxygen/saturated substrate scope, counterion requirement and stereochemistry contract remain those documented in [Phase 5D](reaction-lab-secondary-alcohol-oxidation-phase5d.md).

These are declared assumptions for a bounded theoretical net model—not a complete experimental formulation, isolation procedure, exposure/pH model, yield or safety prediction.

## 5. Frontend/backend validation contract

`server/reaction_condition_guidance.py` supplies additive `guidedConditions` metadata on matched primary/secondary alcohol-oxidation options. It describes the existing assessment; it does not participate in product permission. Metadata is bound to the actual reaction ID and site. Unrelated options and the condition-free catalog do not receive pilot recommendations.

The frontend panel consumes that metadata and maps canonical server settings to the existing UI controls. This is transport/display logic, not another chemistry validator. Before any values change, all suggested controls/options must exist. A signature includes exact resolved reactant references, input values and current conditions, not merely compound labels or formulas. Changed context invalidates an old suggestion. Panel revisions reject detached stale buttons and delayed failures; double application is blocked while revalidation is pending.

The existing public run API still recomputes conditions, structural eligibility, scope and output permission before conformer generation. Client `canRun`, forged guidance, an old reaction ID and a valid profile declaration on an ineligible structure cannot bypass it. Saved profiles are revalidated for the current structure/reagent, not restored as scientific approval.

## 6. Distinguishing missing conditions from missing chemistry

| State | Pilot behavior |
| --- | --- |
| Supported site, missing settings | Reviewable supported settings; explicit apply action |
| Supported model, conflicting/unvalidated selections | Current and replacement values listed; separate replacement confirmation required |
| Model-qualified conditions | “Model conditions match”; no redundant apply action; 3D available only after selecting the option and requesting it |
| Structure/reagent outside qualified profile | Limitations shown; no apply action or target-settings payload |
| Primary alcohol → aldehyde | Explicit “No validated profile implemented”; no secondary-ketone suggestion |
| Unsupported additional condition fields | No apply action that silently deletes them or bypasses their gate |

Aromatic/extra-oxygen substrates, multiple competing alcohols and potassium hypochlorite do not inherit sodium-specific profile confidence. Existing structural exclusions are unchanged. Primary selective-aldehyde confidence stays unresolved; PCC and Dess–Martin remain unimplemented. The pilot does not imply that other dropdown settings fix that missing chemistry.

## 7. Conditional 2D, qualified 3D and calculators

Structurally valid conditional 2D net diagrams remain available through the existing public API. Missing or unsupported conditions and out-of-scope chemistry still block asserted 3D. Qualified runs preserve original oxygen mapping, formal hydrogen accounting, distant stereochemistry, exact site identity and 2D/3D correspondence. No elementary oxidation mechanism was added.

Changing back to generic Water removes the profile declaration and clears the old product, calculator amounts/results, measurements and linked selections. Changing the molecule has the same result-invalidating behavior. Previously selected control values may remain as the user's explicit settings, but eligibility is freshly assessed for the new molecule.

Calculator formulas and theoretical warnings are unchanged. In the browser, 1 mmol each of 2-propanol and full-formula NaOCl produced the formal **0.05808 g / 0.001 mol acetone** result, explicitly theoretical. Applying guidance never grants confidence through arithmetic or claims actual conversion.

## 8. Added tests and pilot scenarios

Added **60 tests: 26 Python and 34 JavaScript**.

Python checks cover missing/qualified/conflicting/unsupported guidance, generic-water replacement, direct/reversed inputs, 2-propanol, 4-heptanol, cycloheptanol, distant stereochemistry, aromatic/extra-oxygen/multi-site exclusions, actual potassium reagent identity, primary-aldehyde rejection, read-only metadata, unchanged stoichiometry, map correspondence and public authenticated match/diagram/run behavior. Forged metadata, stale site IDs and unrecognized conditions remain blocked before conformer generation.

JavaScript checks exercise the actual panel and extracted application handler: no automatic application; explicit replacement confirmation; applicable versus non-applicable states; atomic UI updates; exact structure/condition signatures; stale/detached controls; double submission; delayed failures; inert text; supported-control parsing; saved-profile integration; and existing calculator confidence/quantities.

Browser verification covered the existing 2-propanol example, explicit review/confirmation/application, backend-qualified acetone, separately requested Compare, original oxygen linkage, theoretical calculation, withdrawal to generic Water, saved settings restored after reload, and changing to ethanol with no inherited secondary approval. Longer-chain and cyclic scenarios were additionally verified through public service/API tests, not represented as new curated UI examples.

The existing solution-integration test harness gained only a stub for the new panel's `clear()` dependency. Its previous calculator assertions were not removed or changed. No baseline test function or benchmark expectation was deleted, skipped or weakened.

## 9. Full regression verification

Final full suites pass **1,799 Python + 1,821 JavaScript = 3,620 tests**. This retains the 3,560 baseline tests and adds 60.

Existing public API, mechanism, mapping, stereochemistry, calculator, cross-page and deployment/authentication checks remain in the full suites. Expected invalid-SMILES/valence diagnostics are negative-test output, not unexpected failures.

The separate existing Phase 5D diagnostic also passes: 41 cases, 25/25 positive structural sets, 16 model-qualified cases, 16 verified theoretical 3D options, ten intentionally blocked options and no diagnostic failures. This is not independent experimental certification or automatic companion admission.

## 10. Frozen and companion benchmark regression

All **347 complete frozen result rows are identical to Phase 5D**, not just their aggregate scores. A100 and A101 remain **partial** with their original incomplete inputs. A276's historical restriction and A304's frozen-oracle defect annotation remain unchanged.

Totals remain **156 full, 62 partial, 90 unsupported, 38 correctly rejected and one historical incorrect-result label**. Secondary structural compatibility remains 2/2 and frozen strict support 0/2. The guided interface helps users explicitly supply the existing supported settings; it does not rewrite the frozen cases or inflate their scores.

The frozen parent SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. The pinned v1.0.0 companion files are unchanged: 40/53 structural matches, zero newly approved condition-complete/generation/independent-review outcomes, five correctly rejected controls. Separate unvalidated diagnostic overlays still produce 33 model-generation cases. Version self-comparison shows no changed cases, profiles or defect annotations. No automatic profile/case approval occurred.

See [verification results and integrity checks](reaction-lab-guided-conditions-phase5e-results.json).

## 11. TypeScript, build and integrity

TypeScript (`tsc --noEmit`), the production Vite build, `git diff --check` and a changed/new-text-file whitespace scan pass. The existing large Builder/chunk-size warning remains; this pilot does not solve that unrelated packaging issue.

Explorer, Builder, Calculators, other reaction rules, reaction transforms/validation, atom-mapping/stereo modules, calculator formulas, curated examples, page shells and benchmark manifests were checked against the pre-change content snapshot. Production changes are limited to additive match metadata, the shared unchanged secondary-profile values, the Reaction Lab integration, a small scoped stylesheet addition and the new panel. No publication or deployment was performed.

## 12. Remaining usability limitations

- The pilot covers only the existing secondary NaOCl/acetic-acid profile. It is not a 24-pathway preset catalogue.
- Existing detailed confidence notes elsewhere can still be long; no general content/layout rewrite was included.
- Applying conditions refreshes and selects the corresponding 2D option; it deliberately does not auto-run 3D.
- Unsupported extra condition fields cannot be repaired by hiding them. They require an appropriate supported input context or future implemented model.
- A saved setting is not universal applicability. Changed structures/sites/reagents still need fresh backend assessment.
- Model-qualified does not mean a complete laboratory protocol, unique experimental product, exact conformer geometry or measured yield. Existing Phase 5D geometry limitations remain.

## 13. Recommended next use of the pattern

Review user feedback on this one pilot first. Then select **one existing pathway with independently applicable reagent/condition evidence**, expose its own read-only requirements from its authoritative assessment, and reuse the review/explicit-replacement/revalidation UI pattern. Do not copy the secondary oxidation chemistry into other pathways or treat every missing-condition score as a preset opportunity.

Selective primary-alcohol aldehyde generation remains a missing validated implementation, not a UI task. Any future aldehyde-oxidation or addition-family pilot must first establish its own profile applicability, competing-chemistry, stage/work-up and stereochemical limits. No next pathway was started.

## Browser evidence

![Explicit review and replacement consent](reaction-lab-guided-conditions-phase5e-review.png)

![Qualified conditions with preserved original-oxygen linkage](reaction-lab-guided-conditions-phase5e-qualified.png)

![Primary-alcohol limitation remains explicit](reaction-lab-guided-conditions-phase5e-primary.png)
