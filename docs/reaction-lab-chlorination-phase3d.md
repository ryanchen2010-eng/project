# Phase 3D — Alkene chlorination

Completed October 14, 2026. **Existing Cl₂ addition only.** No new reaction family, layout change, Calculator change, visible example additions, deployment or publication. Bromination behavior is preserved. Epoxidation has not been started.

## 1. Implementation and newly supported structures

Added a dedicated [chlorination policy](</Users/rc/Documents/Capstone project/server/chlorination_rule.py>) using the existing site compatibility architecture, exact edit contracts and strict spectator validation. Eligibility depends on actual structure and neutral Cl–Cl, not names, formulas, CIDs or test-example lookups.

The unchanged benchmark now supports **E-3-hexene, Z-3-hexene, styrene and the distant specified stereocenter example**. Ordinary terminal/branched alkenes now offer validated local R/S alternatives when appropriate instead of a single unsigned structure. Previously accepted cyclic connectivity has independently checked anti configurations.

Additional tests cover longer and branched chains, internal alkenes, isolated 5–8-membered carbocycles with the qualifications below, substituted cyclohexene, terminal alpha-methylstyrene, both distant configurations, widely separated double bonds and preservation of unselected E/Z. These structures are tests, not additions to the curated collection.

Cl₂ has its own reagent, group, site, competition and condition checks. Only element-independent mapped reference, tetrahedral parity, stereocenter perception and projection helpers are reused from Phase 3C through [halogen_addition_stereo.py](</Users/rc/Documents/Capstone project/server/halogen_addition_stereo.py>). The existing bromination rule and stereo files are unchanged. In particular, Br₂ oxygen-spectator permissions are **not** automatically transferred to Cl₂.

## 2. Validated products, mapping and calculations

Each selected option authorizes exactly four net edits:

1. Selected C=C changes from double to single.
2. The actual reagent Cl–Cl bond breaks.
3. One C–Cl bond forms at each selected endpoint.

One substrate plus one Cl₂ gives one connected neutral dichloride, with **no net byproduct**. Each chlorine retains its exact reagent map; no hydrogen transfer, HCl coproduct or consumed catalyst is fabricated. Element/charge conservation, valence, all unaffected bonds, mapped connectivity, the 80-explicit-atom limit and serialized stereochemistry remain validated. Existing global graph/stereo/edit validators are unchanged.

The public match, diagram and run APIs use the same selected mapped product. Independent tests compare complete reactant/product identities, all four edits, exact chlorine origins, 2D atom indexes and actual 3D atom links. Coordinate-derived CIP verifies already-selected configurations; coordinates never determine the expected product.

**34 public amount fixtures** exercise both input orders. They independently check full Cl₂ molar mass **70.906 g/mol**, product elemental mass, one-to-one stoichiometry, limiting reactants, theoretical product amounts and required inputs. Each stereochemical alternative has its own conditional complete-conversion upper bound; their quantities are not summed and are not product ratios.

## 3. Stereochemical outcomes

Ordinary halogen addition is modeled through the bounded halonium anti relationship. Chlorine and bromine can use the same local parity mathematics without assuming identical functional-group compatibility. [Halogenation reference](https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2).

New configurations follow exact mapped starting substituents and neighbor-order parity, followed by independent CIP assignment. They are not an R/S string swap or a result chosen from an arbitrary 3D conformer.

| Starting structure | Independently checked modeled outcome |
| --- | --- |
| E-2-butene | One meso dichloride with local R/S; equivalent face representations grouped |
| Z-2-butene | Separate R,R and S,S alternatives, without assigned populations |
| E/Z-3-hexene | Corresponding meso versus enantiomeric relationships |
| Unsymmetrical E-2-pentene | R,S and S,R alternatives; not automatically meso |
| Unsymmetrical Z-2-pentene | R,R and S,S alternatives |
| Ordinary 5–7-membered cycloalkenes | Trans Cl/Cl; symmetric ring examples independently verify R,R and S,S |
| Propene / terminal styrenes | Relevant single-new-center R/S alternatives |
| Unspecified internal geometry | New local centers remain unassigned |

**Anti is addition geometry, not a universal “trans product” label.** Only validated isolated 5–7-membered cyclic relationships are named trans Cl/Cl. Unspecified cyclooctene is not assumed cis. A valid specified cyclooctene can supply local anti configurations, but no generic ring-relative trans label is assigned to its product.

Distant physical configurations and unselected alkene geometry must remain. CIP is recalculated, including an independent hydrocarbon case where retained physical configuration changes its descriptor from **S to R** after chlorine addition. Both local and unaffected configurations are checked after mapped serialization. Only separately validated new local tags are projected out for the unchanged strict spectator validator; no unrelated stereo or graph change is permitted.

Existing site labels expose the selected local R/S assignments. Existing 2D wedges/dashes and 3D correspondence use the configured mapped product. No layout or control was added.

## 4. Conditions and competing chemistry

| Existing setting | Chlorination behavior |
| --- | --- |
| Dry, no added activation | Qualified neutral non-nucleophilic net model; not an exact solvent or protocol validation |
| Medium unspecified | Conditional 2D only; 3D run rejected |
| Water | Chlorohydrin capture is different chemistry; conditional dichloride net inspection only |
| Ethanol | Alcohol capture/chloroether chemistry is unvalidated; conditional 2D only |
| Generic polar aprotic | Does not establish a non-nucleophilic solvent; conditional 2D only |
| Acid/metal/other added activation or heated conditions | Outside the bounded neutral model; conditional 2D only, not labeled chemically impossible or automatically unfavorable |
| Radical initiation | No ionic chlorination option or 3D dichloride; radical substitution is a separate unsupported pathway |

Water interception is not the same reaction as ordinary dichloride formation. [Halohydrin reference](https://openstax.org/books/organic-chemistry/pages/8-3-halohydrins-from-alkenes-addition-of-ho-x).

The existing Dry/no-water selector is coarse: dryness alone does not prove non-nucleophilicity, solvent compatibility or actual selectivity. The displayed net option explicitly assumes a suitable non-nucleophilic medium. No experimental protocol, safety assurance, rate, yield or product percentage is supplied.

All condition gates also apply to programmatic run requests, returning **422** when unsupported. Changing inputs or conditions clears stale products and selections. Conditional 2D previews remain explicitly qualified rather than claiming the displayed dichloride must form.

Alcohol/ether structures are screened for nearby oxygen capture, with potential ring sizes counted from actual connectivity. **Even distant ordinary OH/ethers remain unsupported in this Cl₂ increment:** chlorine-specific oxygen chlorination, oxidation/cleavage, capture and chemoselectivity have not been independently validated. This is a conservative model limitation, not a claim that no such substrate can undergo alkene chlorination. Br₂'s separately bounded remote-oxygen behavior is unchanged.

## 5. Multiple sites, remaining limits and new restrictions

Widely separated screened double bonds have independent selectable net transformations. Unselected bonds, atoms and specified stereo are retained. Grouping requires both identical full isomeric products and a chirality-aware full-substrate automorphism relating the sites. Non-equivalent sites and distinct stereoisomers are not merged. No experimental one-site selectivity or subsequent-addition distribution is predicted.

- **New structural restriction: 1,7-octadiene (A044).** Nearby pi capture/cyclization is unresolved, so the old uncomplicated one-site dichloride is no longer produced. This screening does not assert that cyclization must occur or dominate. Related nearby polyenes also fail closed.
- **4-Penten-1-ol (A040):** potential six-membered oxygen capture competes; no dichloride-only outcome is asserted.
- **5-Fluoro-1-pentene (A041):** F remains outside the validated spectator set.
- **1-Triacontene (A043):** product exceeds the 80-explicit-atom software bound.
- Distant alcohols/ethers remain excluded pending independent Cl₂ compatibility validation, despite screened Br₂ support.
- Conjugated/cumulated alkenes, internal/multiple aryl-adjacent environments with unvalidated benzylic opening, activated/hetero/fused aromatic rings and other additional reactive groups remain excluded.
- Adjacent specified stereocenters and small/large, fused/bridged, exocyclic/junction or heterocyclic selected ring environments need separate validation. Unknown starting geometry does not acquire invented configurations.
- Missing/capturing/unknown media, added activation and heat now restrict 3D instead of silently accepting an ordinary dichloride. Radical settings no longer return an ionic-addition option.
- **Complete chloronium mechanism visualization is unsupported.** Implemented behavior is the mapped net transformation and validated bounded stereo, not invented intermediates or curved arrows.

No invalid product or unexpected chemistry result was flagged by the new checks or audit. This is not proof of unrestricted chemical correctness: exact solvent effects, open-ion stereochemical behavior beyond the screened scope, large-ring/intermolecular capture, polymerization and experimental chemoselectivity remain unresolved.

## 6. Fixed benchmark comparison

The **347 cases, matrix, expectations and scoring are unchanged**. Script SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

**Chlorination: 6/14 fully supported (42.9%) → 9/14 (64.3%).** Four gains minus one justified restriction.

| Benchmark cases | Before → after |
| --- | --- |
| A037/A038, E/Z-3-hexene | Unsupported → fully supported |
| A039, styrene | Unsupported → fully supported |
| A042, distant specified stereocenter | Unsupported → fully supported |
| A044, 1,7-octadiene | Fully supported → unsupported for unresolved competing capture |
| A035, cycloheptene | Remains partial under the unchanged benchmark's independent-stereo criterion |

The fixed cyclic row lacks an independent stereoproduct expectation, so it is not promoted just because the engine assigns tags. New independent cyclic tests supply additional evidence, reported separately without changing the score. The saturated negative control remains correctly rejected.

All **332 non-chlorination rows are identical** to Phase 3C, including products, option counts, notes, previews, geometry, mechanisms and statuses. Overall: **179 fully supported, 114 unsupported, 16 partial, 38 correctly rejected**. These are tested-case workflow scores, not experimental accuracy or comprehensive reaction coverage.

## 7. Verification and preservation

**1,405 tests pass: 720 Python + 685 JavaScript; zero failures/skips.** Added **106 tests**:

- 60 chemistry/compatibility tests, including independently specified connectivity, CIP/meso/cyclic stereo, exact atom/bond conservation, unselected stereo, map/atom reorder invariance, competition, limits, wrong reagents/conditions and tampered products.
- Eight authenticated public HTTP tests covering match, diagrams, runs, exact 2D/3D links, reversed slots, stereochemical alternatives, rejection explanations and stale selections.
- 34 public reaction-amount fixtures and four UI gating/reset checks.

All **1,299 original tests remain**. Only two existing methods in two files intentionally update superseded Cl₂ expectations: terminal products now expose configured alternatives, and E/Z chlorination is no longer globally rejected. Their bromination/HX/hydration assertions are preserved; none was deleted.

An additional before/after bromination differential check compares **45 public match contexts and 46 complete diagram payloads**, including O spectators, E/Z, rings, distant chirality, multiple sites and condition gates. SHA-256 is identical: `18fd279bfc1488aea3a436297f84d1a338c699e7856ac20b4fef0fb7b08761bd`. Retained bromination tests also verify actual 3D maps/configurations.

The earlier four-pathway diagnostic passes: **48 substrates, 192 public matching calls, 48 condition checks, five reagent controls, 125 verified options, no failures**.

**TypeScript, production build and whitespace checks pass.** Pre-existing third-party ignored `use client` directives and the large Builder chunk warning remain. Source hashes confirm all HTML/CSS/frontend/Calculator files, shared molecule data, fixed audit, bromination rule/stereo, other reaction rules and shared graph/stereo/edit/diagram validators are unchanged. Five production integration files gained chlorination-specific branches; the two new modules supply its policy and generic parity adapter.

Browser verification confirms Propene + Chlorine shows separate C2 R/S choices. In the dry model, incoming Cl map 10 links reagent, product and 3D. Switching to water clears the selected product, leaves qualified 2D inspection, disables 3D and explains chlorohydrin competition. The local preview was restarted with the updated backend; the temporary test tab was closed. Nothing was committed, pushed, deployed or published.

[Machine-readable audit, tests and preservation evidence](</Users/rc/Documents/Capstone project/docs/reaction-lab-chlorination-phase3d-results.json>).

![Verified chlorination and linked chlorine atom](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3d-preview.jpg>)

## 8. Recommended next pathway

The next candidate is the **existing epoxidation pathway**, beginning with a separate chemistry/stereochemistry review and independently verified oxygen-transfer compatibility. It should not inherit halogen anti geometry or unvalidated spectator permissions.

**Phase 3D is complete and stops here. Epoxidation and other implementation phases were not started.**
