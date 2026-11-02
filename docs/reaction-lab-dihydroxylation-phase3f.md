# Phase 3F — Alkene dihydroxylation

Completed 2026-10-15. This increment changes the existing catalytic Os/H₂O₂ dihydroxylation pathway only. No new reaction family, publication, deployment, overall layout redesign or Calculator changes. The addition-family consistency review has **not** started.

## 1. Original model and implementation

The original pathway accepted hydrocarbon-only, locally isolated alkenes without specified E/Z. It cleaved the formal H₂O₂ O–O bond, changed C=C to single, and attached one existing O–H to each carbon. It rejected distant specified tetrahedral centers and heteroatom spectators. Cyclic products were unsigned. Osmium was a condition selector, not an explicit mapped catalyst. NMO was a benchmark probe, **not an implemented alternative reagent**. No mapped mechanism or workup representation existed.

The new [dihydroxylation module](</Users/rc/Documents/Capstone project/server/dihydroxylation_rule.py>) supplies a pathway-specific policy using the existing site compatibility, atom conservation and exact edit-contract architecture. It independently screens the selected C=C, rings, additional functional groups, nearby oxidative-cyclization/direction risks and distant stereo. Only mapped-reference/permutation and chirality-aware whole-graph equivalence helpers are reused; no epoxidation or halogen chemistry permission is inherited.

The exact net contract is four changes: C=C double→single, formal peroxide O–O cleavage, and two new C–O bonds. The existing two mapped O–H bonds are retained. One substrate and one H₂O₂ give one diol, with no explicit net byproduct. Every represented atom, element, hydrogen, charge and unaffected bond is checked. Distant physical stereo is validated; only the two newly configured reaction atoms are masked for the unchanged spectator validator after independent local checks. Full local stereo is revalidated after mapped serialization.

## 2. Newly supported structures

New fixed-benchmark **structural** matches include 4-penten-1-ol, styrene, E-3-hexene, Z-3-hexene and the distant specified stereocenter example. They now have correct conditional net diagrams; confirmed-workup tests also verify their 3D models and calculations.

Independent cases additionally cover long and branched chains, both configurations of distant centers, remote ordinary alcohols/ethers, isolated 5–7-membered carbocycles, substituted cyclohexene, E/Z-stilbene, unequal internal substituents and several isolated C=C sites. This is a bounded net transformation scope, not proof that a functional group is universally inert or that one site can be selectively converted experimentally.

## 3. Independently verified syn stereochemistry

Syn hydroxylation places the two entering OH groups on the same face. It is distinct from epoxide hydrolysis/anti diol formation. Osmium-mediated syn hydroxylation and the cyclic osmate/product-release distinction are described in the [OpenStax reference](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation).

| Starting structure | Verified modeled alternatives |
| --- | --- |
| E-2-butene / E-3-hexene | R,R and S,S structures, separately selectable |
| Z-2-butene / Z-3-hexene | One meso R/S product after equivalent representations are grouped |
| Unsymmetrical E internal alkene | R,R/S,S alternatives in the independent test structures |
| Unsymmetrical Z internal alkene | Distinct R,S/S,R alternatives; not automatically meso |
| Cyclopentene, cyclohexene, cycloheptene | Validated cis OH/OH products; symmetric cases grouped |
| Substituted cyclohexene | Distinct validated face alternatives without a preferred face |
| Terminal propene / styrene | R/S face alternatives where a new center exists |
| Unknown internal alkene geometry | Newly formed centers remain unsigned |
| Identical substituents / achiral product | No invented tetrahedral tags |

Tags follow mapped neighbor-order parity, not identical R/S letters or a sampled conformer. CIP is independently reassigned. A distant test center changes S→R because priorities change **without physical inversion**. Input-order/map-label permutations, reordered products, meso deduplication, retained unselected E/Z and deliberately corrupted local/distant configurations are tested. Actual generated coordinates are reassigned independently against map-to-model indices to verify each chosen configuration, never to choose a reaction outcome. No stereoisomer ratios, enantiomeric excess or facial preference are predicted.

## 4. Reagent, workup and mechanism boundaries

The existing neutral H₂O₂ plus catalytic Os selector is retained. Catalytic osmylation with H₂O₂ is documented, but possible overoxidation is a real limitation; this is not a universally selective isolated-diol protocol. [Organic Syntheses reference](https://www.orgsyn.org/demo.aspx?prep=CV6P0342).

H₂O₂ maps are **formal net bookkeeping**, not elementary oxygen provenance through an omitted osmium cycle. O–H retention is not a prediction of experimental proton/isotope exchange. Osmium, hydrolysis/release medium, catalyst regeneration and workup species are not explicit calculated reactants. Conservation is claimed for all **explicitly represented** species, not for a complete unrepresented catalytic mechanism.

A small **Diol release / work-up** selector is added inside the existing contextual pathway-settings panel. It defaults to **Not confirmed**. The supported setting explicitly says **Assume aqueous release · net model**. It records a net-product assumption, not a complete workup protocol. Selecting water as medium alone does not confirm release.

Without osmium activation or confirmed aqueous release, conditional 2D net diagrams remain available; 3D/Compare/run are blocked in both UI and backend. Heated or incompatible activation settings are unvalidated, not mislabeled as proven chemical impossibility. Changing workup invalidates old results. The existing ethene example selects its explicit net assumptions; the curated collection remains 20 examples. No audit molecules were added.

**No mapped dihydroxylation mechanism was invented.** A complete cyclic osmate, osmium oxidation states, catalyst cycle, proton transfers and workup chemistry cannot be validated using the two explicit reactants in this net model. The mechanism remains unavailable and the interface states this honestly. No carbocation, epoxide intermediate or guessed electron arrows are displayed. NMO, stoichiometric mapped OsO₄, KMnO₄, oxidative cleavage and asymmetric ligand systems remain unimplemented.

## 5. Remaining limitations and newly restricted behavior

Unsupported structures include conjugated/cumulated/direct-heteroatom alkenes; competing carbonyl, alkyne, peroxide and other unvalidated groups; activated/acid-sensitive oxygen groups; near-site OH/ether direction/capture; adjacent specified centers without a directed model; activated/fused aromatic environments; selected exocyclic/fused/bridged/heterocyclic or non-5–7-membered rings; and products exceeding 80 explicit atoms. These are validation/model limits, not assertions that the molecules cannot undergo real dihydroxylation.

Nearby dienes with insufficient separation are conservatively excluded for unresolved oxidative-cyclization chemistry. Distant isolated C=C sites can be evaluated independently. Equivalent representations are grouped only when the isomeric product agrees and a chirality-aware whole-substrate mapping relates the sites; exact alternative site/face aliases remain recorded. No experimental one-site selectivity is asserted.

Previously connectivity-only cyclic cases outside the configured ring scope, exocyclic/fused sites, and nearby dienes are now restricted rather than assigned unvalidated stereo. Missing activation/workup no longer permits an unconditional 3D run. Malformed peroxide stereo annotations and incomplete source directions fail before normalization can silently discard them. These are intentional restrictions, not weakened validation to increase a score.

## 6. Unchanged 347-case benchmark — important qualification

The benchmark file, expectations, conditions, scoring and source inventory were **not changed**. SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`. Its original source hashes match the saved Phase 3E baseline.

**Original dihydroxylation: 4/11 fully supported (36.4%).**

**Updated strict unchanged benchmark: 0/11 fully supported (0%); ten partial, one unsupported positive, one correctly rejected negative.**

This decrease must not be hidden: the fixed inputs specify osmium but **do not confirm workup**, so the ten structurally supported cases now correctly fail the unconditional 3D-run check. They retain validated conditional 2D products. NMO remains unsupported. Structural matches increase from 5/11 to **10/11**, but that is not the full-workflow score.

Separately, an explicitly labeled **confirmed-workup supplement** replays the same twelve dihydroxylation rows with only `workup: aqueous-release` supplied. It produces **9/11 fully supported (81.8%)**, one partial cyclic row, one unsupported NMO row and one correctly rejected control. This supplement is **not** substituted for the fixed benchmark. The cyclic row stays partial because the unchanged benchmark lacks an independent expected stereoproduct; new independent cis/R/S tests supply that evidence separately. All ten available positive rows run with converged 3D correspondence in the supplement.

All **335 unrelated fixed rows remain identical** to Phase 3E, including products, option counts, notes, mechanisms, preview/run and geometry results. No incorrect-result rows appeared.

| Exclusive fixed status | Count |
| --- | ---: |
| Fully supported | 179 |
| Partially supported | 25 |
| Unsupported | 105 |
| Correctly rejected | 38 |
| Total | **347** |

Counting rules: the 24 pathway categories partition all 347 rows. The full-support denominators include 309 positive expectations; 38 negative controls are excluded only from those denominators, not from the total/status counts. Variant tables are subsets of their parent pathways and must not be added again. Supplementary probes and the confirmed-workup replay are separate, not extra benchmark cases. There are no omitted fixed rows or overlapping exclusive statuses. The minimum-site benchmark check counts options; stronger independent tests verify actual site identities and grouped aliases rather than treating two enantiomers as two reactive sites.

## 7. Verification and preservation

**1,704 tests pass: 884 Python + 820 JavaScript. Zero failures/skips.** Added **132** tests:

- 77 independent chemistry/stereo/compatibility/condition/tampering tests.
- Eight authenticated HTTP tests covering public matching, diagram and run routes.
- 42 public stoichiometric fixtures feeding the unchanged TypeScript calculator, both input orders, full H₂O₂ mass, formal total mass conservation, limiting reagent, theoretical product and required amounts.
- Five existing-UI gate, invalidation, contextual setting and curated-example checks.

All original 1,572 tests remain. Two older Python methods intentionally update obsolete unsigned/E/Z-rejection assumptions to the new independently configured outcomes. Two existing JavaScript test files extend their mocks/settings assertions for the workup control. No original test method was removed. Calculator source, HTML, CSS, curated compound data, other pathway modules and shared graph/stereo/compatibility validators are unchanged. The shared diagram file changes only this pathway's formerly incorrect unsigned-summary text.

The prior SN1/SN2/E1/E2 public diagnostic also passes: 48 substrates, 192 matching checks, 48 condition checks, five reagent controls, 125 verified options, no failures. **TypeScript, production build and whitespace checks pass.** Existing third-party directive and large Builder-bundle warnings remain; no unrelated bundling changes were made.

Browser verification confirms conditional 2D with unconfirmed workup, explicit confirmed-release settings, separate R/S choices, an unchanged page layout, current syn summary, a generated diol and oxygen **O10** linked from H₂O₂ through product 2D/3D. Clearing workup discards the old 3D result and disables its controls. The temporary verification tab is closed; the local preview remains running. No commit, push, deployment or publication occurred.

[Machine-readable fixed audit, supplemental observations and preservation evidence](</Users/rc/Documents/Capstone project/docs/reaction-lab-dihydroxylation-phase3f-results.json>).

![Phase 3F — oxygen linked through reagent, diol and 3D](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3f-preview.jpg>)

## 8. Recommended next step

Request a separate **addition-family consistency review**, concentrating on condition completeness, unknown-geometry handling, site/face deduplication and honest net-versus-mechanism claims across the completed pathways. Any catalyst-specific full osmium cycle/workup implementation needs its own validated model later.

**Phase 3F ends here. No subsequent review or reaction increment was started.**
