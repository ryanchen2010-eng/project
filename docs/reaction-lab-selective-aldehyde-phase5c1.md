# Phase 5C.1 — Selective aldehyde condition validation

Reviewed 2026-10-17 (America/Toronto). **Outcome: prerequisite stop; selective-product gate remains unresolved.** No production code, existing test, reaction condition schema, benchmark input, companion approval, layout, Calculator or curated example was changed. No Phase 5D work was started.

The request explicitly requires stopping if no suitable selective oxidant is already implemented. Inspection found a formal alkali-hypochlorite redox model, but **no implemented selective aldehyde reagent/activation/formulation profile**. Therefore no profile was enabled. This is an implementation limitation, not a statement that selective alcohol oxidation or selective hypochlorite chemistry is impossible.

See [versioned verification and prerequisite evidence](reaction-lab-selective-aldehyde-phase5c1-v1.json). This standalone record is **not** an approved companion profile or a replacement benchmark.

## 1. Existing oxidants discovered

The only reagent family connected to primary `Alcohol oxidation` is an actual alkali-metal hypochlorite formula unit: Li/Na/K/Rb/Cs paired with `[O-]Cl`. Sodium hypochlorite is the named catalog entry; other supported counterions are graph-recognized. They share one formal redox edit, not five independently validated selective protocols.

Inspection locations: `reagent_role` and `oxidation_sites` in `server/reaction_engine.py`; `oxidant_atoms`/redox contracts in `server/alcohol_oxidation_rule.py`; primary validation and gates in `server/primary_alcohol_oxidation_rule.py`; catalog, normalization, matching and run gating in `server/chemistry_server.py`.

PCC, Dess–Martin periodinane (DMP), PDC and TEMPO-mediated oxidation are **not implemented** as primary oxidation reagent/activation models. Peroxyacids and hydrogen peroxide exist for other pathways, but do not thereby become supported primary-alcohol oxidants. PubChem identification, a molecular name, iodine/chromium in a structure, or a displayed compound record does not confer reaction-model support.

## 2. Profile selected—or reasons none qualifies

**Selected profile: none.** The existing hypochlorite first-stage model has no code path establishing selective aldehyde formation. Its condition assessment deliberately returns `canRun: false`, `conditionCompleteEligibility: false`, and `aldehydeEndpointValidated: false`.

Current fields are insufficient to substitute for a selective formulation:

| Field | Implemented values | Missing meaning for this task |
| --- | --- | --- |
| Reagent | Actual alkali hypochlorite | No PCC/DMP identity or selective catalytic hypochlorite system |
| Medium | Unspecified, generic polar aprotic, aqueous protic, ethanolic protic, dry | No specific solvent identity, biphasic formulation or applicable water-control model |
| Temperature | Unspecified, ambient, heated | No profile-specific validated temperature constraints |
| Activation | Unspecified, none, acid, Pd/Pt metal, Lindlar, osmium, radical initiation | No TEMPO/oxoammonium catalytic oxidation model; “radical initiation” cannot stand in for TEMPO |
| Oxidation level | Unspecified, first, further | Requested first-stage structure is not an aldehyde stopping guarantee |
| Workup | Unspecified, assumed aqueous diol release | No aldehyde-specific quench/release model; diol release is not a general workup |

There are no implemented pH/formulation, controlled exposure/supply or aldehyde endpoint-release requirements for selective primary hypochlorite oxidation. Entering unsupported keys is not permission to assume those details.

## 3. Chemical evidence and scope

The supplied references were checked against the actual engine rather than treated as proof that their reagents already exist in it:

- [OpenStax §17.7, Oxidation of Alcohols](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols): distinguishes oxidation levels and discusses DMP chemistry. Its DMP model is not the implemented hypochlorite edit.
- [OpenStax §19.2, Preparing Aldehydes and Ketones](https://openstax.org/books/organic-chemistry/pages/19-2-preparing-aldehydes-and-ketones): describes primary-alcohol aldehyde preparation using DMP in dichloromethane at room temperature. This is a potential future reagent model, not an existing option.
- [University of Calgary, Oxidation of Alcohols](https://www.chem.ucalgary.ca/courses/353/Carey5th/Ch15/ch15-4-6.html): the official search-index excerpt distinguishes PCC/PDC in dichloromethane from aqueous oxidation. Direct page fetch timed out; no inaccessible mechanism detail was used for approval.
- Independent primary evidence: [Anelli, Montanari and Quici, Organic Syntheses, DOI 10.15227/orgsyn.069.0212](https://www.orgsyn.org/demo.aspx?prep=CV8P0367), Discussion and Notes. Selective hypochlorite oxidation uses a defined nitroxyl-catalyzed, buffered, biphasic formulation. Exposure and co-reagents affect further oxidation, and unsaturation/other alcohols can introduce competing chemistry.

**Software inference:** generic hypochlorite + Water/First stage/Ambient is not an implementation of that literature system. Adding its catalyst and formulation assumptions silently would introduce an unimplemented chemistry model. No existing counterion or spectator permission was extrapolated into selective experimental validation.

No reagent-specific temperature window, activation, workup, substrate class or competing-group selectivity was approved in this increment. External evidence identifies what must be represented next; test success cannot supply those missing chemical assumptions.

## 4. Structural coverage before and after

Primary structural matching remains **7/10 (70.0%)**. No structural compatibility rule was expanded or restricted.

| Frozen ID | Existing matched substrate/context | Current qualification |
| --- | --- | --- |
| A080 | `CCCCCCCO`, long primary alcohol | Conditional first-stage 2D; selective profile absent |
| A081 | `CC(C)CCO`, branched primary alcohol | Same |
| A082 | `OCCc1ccccc1`, phenethyl alcohol | Same; phenyl spectator retention is net bookkeeping, not universal oxidant inertness |
| A083 | `COCCCO`, remote ether | Same; requires profile-specific spectator review before qualification |
| A086 | `CC[C@H](C)CCO`, distant specified center | Same; unchanged stereochemistry is checked, but does not establish endpoint chemistry |
| A088 | `CCCCCO` with actual potassium hypochlorite | Same; no substitution of sodium hypochlorite, PCC or DMP by changing a label |
| A102 | `OCCCO`, two equivalent primary alcohol sites | Same; unresolved competing oxidation also prevents selective one-site assertion |

**None of these seven qualifies under an existing implemented selective profile.** A080's substrate appears in the selective hypochlorite literature, but the required formulation is not present in the engine. A substrate example alone is not profile validation. The three excluded positive cases remain A084 (unscreened fluorinated spectator), A085 (amine competition) and A087 (allylic/alkene competition).

## 5. Frozen fully supported coverage before and after

Primary-only strict full coverage remains **0/10 → 0/10**. Seven positives are partial; three remain unsupported. The broader Alcohol oxidation category still has two unchanged secondary positives: **2/12 strict full**, seven partial, three unsupported and two correctly rejected controls. These denominators must not be mixed.

The original 347 inputs, expectations and scorer remain unchanged. Parent SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

## 6. Separate condition-aware replay results

**A validated condition-complete selective replay was not performed:** there is no approved implemented profile to supply. Recording an invented PCC/DMP/TEMPO overlay as a successful qualified replay would violate the stop condition.

Instead, a separate, versioned **read-only current-setting diagnostic** probed the same seven matched case IDs under nine setting combinations: frozen inputs, aqueous first-stage ambient, generic dry/aprotic alternatives, heated aqueous, extra acid, unrelated diol workup, an unknown explicit PCC field and an unsupported TEMPO enum. These are gate probes, **not scientifically justified selective protocols**.

Results: **63 probes**, comprising **56 conditional-2D cases with verified net mapping and blocked 3D**, plus **seven unsupported-setting rejections**. An unsupported enum rejects the request before an option is generated; that is not a conclusion that the substrate cannot oxidize.

The three requested evidence categories remain separate:

| Measurement | Result |
| --- | --- |
| Frozen primary structural matching | 7/10 |
| Frozen primary strict full | 0/10 |
| Primary condition-complete eligibility | 0/10 |
| Primary qualified 3D generation | 0/10 |
| Independently approved primary selective endpoint profiles | 0 |
| Validated selective diagnostic replay | Not performed—prerequisites absent |

The unchanged pinned v1.0.0 companion has 53 reviewed-scope positive cases for other pathways: 40 structural matches; zero condition-complete, fully supported generation or independently approved outcomes; five controls correctly rejected. Its unvalidated diagnostic overlay remains 33 model-generation cases, not approved chemistry. No primary profile was added or promoted, and version self-comparison has no case, profile or defect changes.

## 7. Cases newly qualifying for 3D

**None.** A conformer is not used to certify an oxidation endpoint. All primary public-run gates remain in place, including direct legacy site IDs and requests with unsupported/conflicting conditions.

## 8. Cases still restricted

All seven matched primary benchmark cases remain conditional for endpoint reasons. A102 additionally requires independently justified treatment of competing alcohol sites. A088 cannot inherit a sodium-specific protocol solely because both reagents contain hypochlorite. A084/A085/A087 retain their structural/competition restrictions. Existing short oxygen-capture, unsaturation, invalid-stereo, epimerization, ring, size and sensitive-group exclusions are unchanged.

Future implementation prerequisites—**not work performed here**:

1. Explicitly authorize a new selective reagent or activation/formulation model. DMP is one possible future candidate to assess, not a profile selected or approved in this phase.
2. Implement exact reagent identity and reagent-specific scope; do not disguise a new oxidant as hypochlorite or “none” activation.
3. Represent the actual medium/formulation, applicable temperature constraints and validated endpoint/release assumptions. Do not map the existing diol workup to aldehyde isolation or assume “dry” means dichloromethane.
4. Define independently sourced substrate and competing-group limits. Keep multiple alcohols conditional unless site selectivity is independently established; do not blanket-approve all seven cases.
5. Implement reagent-specific atom/redox accounting. The existing hypochlorite water/chloride/counterion contract cannot be borrowed for an iodine- or chromium-based reagent. Explicitly model validated coproducts or honestly label an incomplete net representation, withholding unsupported balanced-reagent calculations.
6. Retain physical-stereo, oxygen-provenance, valence, charge and source-map validation. Only then add scoped 3D permission and independently reviewed companion evidence with a new version.

Changing the reagent in A088 for a future diagnostic would need explicit recording as a reagent-changing comparison, not a condition-only completion of its original frozen input.

## 9. Stereochemistry and atom-mapping verification

Existing Phase 5C tests were rerun without changing expectations. They cover distant physical configuration retention, independent CIP relabeling, invalid stereo rejection, selected-carbon SP2 geometry, original alcohol oxygen retention, exact mapped H transfer, unchanged connectivity and rejection of corrupted products. The setting diagnostic separately checked mapped elemental identities, total formal charge and exact formal water provenance for every available 2D option.

No new primary 3D stereochemical assertion was made. Existing linked 2D/3D regression tests for eligible pathways remain passing; no new interactive browser session or production UI change was necessary for this documentation-only stop.

## 10. Overoxidation safeguards

The Phase 5C flags remain false for selective profile implementation, aldehyde endpoint validation and condition-complete eligibility. Generic first-stage/medium choices cannot bypass them. No primary alcohol-to-acid pathway, replacement acid product, detailed oxidation mechanism, H2 gas or new oxidant coproduct was introduced.

## 11. Public UI and Calculator confidence behavior

Public matching, diagram and run regressions retain explicit conditional 2D versus blocked primary 3D behavior. Unknown explicit condition keys and unsupported values are not silent defaults. The primary atom inspector does not invite a blocked Compare view, and changing inputs clears stale 3D output.

The calculator still describes hypothetical balanced hypochlorite **first-stage amounts**, not isolated aldehyde yield, total further-oxidation demand, selective conversion or a laboratory procedure. Its warning and full-counterion molar-mass tests pass. No formula, field, layout or wording was edited in this phase.

## 12. New tests and total passing tests

**Zero new persistent tests; zero modified expectations.** The explicit prerequisite-stop branch leaves all 3,380 baseline tests unchanged. Fresh verification: **1,700 Python + 1,680 JavaScript = 3,380 passing tests**. This includes public matching/generation, mechanisms, mapping, stereo, linked-view behavior, calculator fixtures and companion evidence gates.

The 63 read-only setting probes are separately reported diagnostics, not added to the regression count or visible examples. There is no “valid selective conditions” positive test because the corresponding feature was deliberately not implemented; fabricating one would hide the unresolved prerequisite.

## 13. Unrelated chemistry regression results

All **347 frozen result rows** are unchanged from completed Phase 5C, including all **337 non-target rows**, both secondary oxidation rows, A276's historical restriction and A304's separately annotated frozen-oracle defect. Global totals remain 158 full, 60 partial, 90 unsupported, 38 correctly rejected and one historical incorrect-result label. The versioned record enumerates every case ID and unchanged-result check.

Production, test, script, HTML and benchmark source hashes were compared before and after the review. No source or benchmark changes were made. No unreviewed companion approval was filled in.

## 14. TypeScript and production-build results

Fresh `tsc --noEmit`, production Vite build and whitespace checks pass. The pre-existing large-chunk warning remains. No website publication or chemistry-service deployment occurred. Generated build output is verification output, not a new production feature.

## 15. Recommendation on Phase 5D

The existing code is regression-stable, but **selective primary-aldehyde product generation is still unresolved**. Do not describe Phase 5C.1 as enabling qualified aldehyde 3D or as meeting a chemistry-completion prerequisite for Phase 5D.

Recommended next decision: authorize one narrowly scoped selective-oxidation model and the prerequisites above, or explicitly defer this gap before choosing other work. This report does not authorize or start either implementation. Phase 5C.1 ends here at the requested prerequisite stop.
