# Phase 3B — Alkene hydrohalogenation

Completed October 14, 2026. This increment improves the existing **ionic alkene + HCl/HBr/HI** pathway only. No new reaction family, layout change, Calculator change, curated example additions, publication or Phase 3C work.

## 1. Implementation

Added [hydrohalogenation_rule.py](</Users/rc/Documents/Capstone project/server/hydrohalogenation_rule.py>) as an HX-specific consumer of the shared compatibility architecture. It screens each C=C and capture orientation, the rest of the substrate and the actual neutral H–X reagent. It declares four exact mapped bond edits and independently validates the product.

Hydrohalogenation no longer depends on the old shared halogenation eligibility/orientation branch. Hydration's chemical policy, halogenation's rules, the graph/stereochemistry/edit validators, mechanism and diagram renderers remain unchanged. Only the existing raw-input directional-stereo warning is reused; it guards normalization loss, not chemical compatibility.

Matching, conditional 2D diagrams, eligible 3D products and amount calculations use the same selected mapped graph. The existing controls already honor `canRun`; no page panels or controls were rearranged. A small shared TypeScript status extension represents an unsupported requested pathway.

## 2. Newly supported and retained structures

New fixed-benchmark support:

- **2-Hexene:** separately selectable 2-bromohexane and 3-bromohexane net options.
- **E-3-hexene and Z-3-hexene:** each produces unsigned 3-bromohexane connectivity; the selected E/Z designation is consumed rather than retained or translated into a fabricated configuration.
- **Styrene:** screened benzylic capture gives unsigned 1-bromoethylbenzene.
- **Specified 4-methylhex-1-ene:** its distant physical configuration survives, with independently recalculated CIP descriptors.

Independent tests also verify longer/branched terminal and internal alkenes, unequal and equal-substitution internal orientations, methyl-substituted cyclic alkenes, alpha-/beta-methylstyrene, both distant tetrahedral configurations, unselected E/Z and widely separated multiple sites. Actual HCl, HBr and HI identities are tested separately, including reversed input slots. Simple, long, branched, symmetric internal and cyclic cases that already worked are retained support, not all new benchmark gains.

**Oxygen spectators are HX-specific:** only screened remote unactivated primary alcohols and ordinary saturated primary/secondary dialkyl ethers have a qualified **ambient-HCl** net reporting scope. Examples outside the curated collection include `C=CCCCCCCCO`, `C=CCCCCCCCOC` and a specified distant ether-bearing center. Multiple primary OH groups are screened individually. HBr/HI versions remain excluded for unresolved substitution/cleavage, regardless of distance. Secondary/tertiary OH, acid-labile tertiary/allylic/benzylic ethers, acetals and short intramolecular capture environments are not enabled.

This HCl scope is a conservative conditional model inference, not independently established experimental chemoselectivity for every multifunctional substrate. Neutral oxygen connectivity in the report does not mean oxygen remains unprotonated or permanently inert. HCl and HBr/HI are not interchangeable spectator permissions: ordinary ether cleavage differs by acid, while alcohol conversion depends on substitution and conditions. [Ether-cleavage reference](https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage), [alcohol-reaction reference](https://openstax.org/books/organic-chemistry/pages/17-6-reactions-of-alcohols).

## 3. Regioselectivity and competing chemistry

For ordinary ionic addition, unequal substitution uses bounded Markovnikov capture; propene gives 2-halopropane. A single isolated phenyl attachment permits a narrowly screened benzylic orientation. Full-graph symmetry identifies equivalent ends. Equal but inequivalent internal ends generate separate constitutional alternatives, not an arbitrary winner or major/minor percentages. The introductory reference explicitly discusses both bromopentane connectivities from 2-pentene. [Orientation reference](https://openstax.org/books/organic-chemistry/pages/7-8-orientation-of-electrophilic-additions-markovnikovs-rule).

Equivalent multi-site results are grouped only when identical isomeric products **and a chirality-aware full-graph automorphism** establish equivalence of both C=C endpoints and the halogen-capture carbon. One mapped representative is displayed, with equivalent site maps retained in metadata and explanations. Non-equivalent sites/orientations remain independently selectable. A bounded search may retain a redundant option rather than falsely merge sites. This does not predict experimentally selective mono-addition.

Adjacent branched/quaternary shift risks, neighboring ring migration and potential shifts to a benzylic cation remain excluded. Conjugated/cumulated, directly heteroatom-substituted, multiply stabilized and other unvalidated cation environments fail closed. Rearrangement concerns are not solved by silently generating a guaranteed unrearranged product. [Rearrangement reference](https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements).

**Newly restricted benchmark case: 1,7-octadiene.** Its second pi bond creates a possible short intramolecular capture route, so an uncomplicated one-site HX product is no longer claimed. This is conservative graph-based risk screening, not a measured assertion that this substrate must cyclize or that cyclization dominates. More widely separated isolated bonds can have independently selectable net options, with further addition, larger-ring/intermolecular capture and actual selectivity explicitly unpredicted.

Other new explicit bounds include selected isolated **5–8-membered carbocycles**, excluding unvalidated small/large, fused/bridged, exocyclic and heterocyclic cation/geometry environments. Small/large-ring exclusion is a software/model limit, not a universal inability to add HX. Remote groups are not presumed inert simply because they are distant.

## 4. Reagents and conditions

HX supplies both incoming atoms and is consumed; it is not the regenerated acid catalyst used in hydration. No separate acid catalyst is required by this net model. Only actual neutral HCl/HBr/HI graphs pass; HF, free halide ions, X2, isotope/radical and multi-part reagent graphs are not substituted into this rule. [Ionic addition reference](https://openstax.org/books/organic-chemistry/pages/7-7-electrophilic-addition-reactions-of-alkenes).

| Settings | Assessment and action |
| --- | --- |
| Actual HX; dry/non-capturing ionic setting; no added activation | Model conditions match, with no experimental conversion or selectivity guarantee. |
| Medium unspecified; no oxygen spectators | Incomplete conditions. A conditional ionic net preview/3D assumes halide capture in a non-capturing medium; this does **not** establish water, alcohol or peroxide absence. |
| Polar-aprotic setting | Reference difference, potentially compatible; exact solvent identity/acid compatibility is not calculated. |
| Water or ethanol medium | Solvent-versus-halide capture is unvalidated. Conditional 2D only; 3D/run/compare are blocked and the run API returns 422. Not labeled chemically unfavorable. |
| Added acid, metal, Lindlar or Os activation | Additional chemistry unvalidated; conditional 2D only, not automatically favorable or required. |
| Radical initiation | No ionic or radical product option. Peroxide-initiated anti-Markovnikov HBr requires a separately validated radical model; no equivalent HCl/HI radical prediction is implied. |
| Screened oxygen groups + HCl, ambient explicitly selected | Qualified neutral-reporting net scope only, subject to compatible activation/medium settings. |
| Screened oxygen groups + HCl, temperature unset | Conditional 2D only until ambient settings are established. |
| Oxygen groups + heated HCl, or + HBr/HI | Unsupported spectator chemistry; no preserve-only product generated. |

Temperature selectors do not calculate rates, energy barriers, rearrangement suppression or product ratios. Condition changes clear obsolete selections and products. Theoretical amounts describe one selected complete-conversion net option, not an experimental protocol, actual yield or mixture composition.

## 5. Mapping and stereochemistry safeguards

- The selected C=C changes 2→1, the actual mapped H–X breaks, and the declared C–H and C–X bonds form. Both entering maps originate in the selected HX, including after reversed user input ordering.
- Exactly one substrate and one HX produce one connected neutral haloalkane; no fabricated byproduct or regenerated HX catalyst is added. Atom identities, element/charge conservation, unchanged bonds, valence, H counts and the 80-explicit-atom product bound remain enforced.
- Distant tetrahedral configurations are checked by mapped physical parity and after serialization, not by copying R/S labels. Independent coordinate-derived CIP checks verify specified centers in rendered 3D products.
- A dedicated case demonstrates **unchanged physical configuration with a changed CIP descriptor**: `C=CCCC[C@H](C)CCCCO` is S at its specified center, while the ambient-HCl product `CC(Cl)CCC[C@H](C)CCCCO` is R. The opposite physical configuration shows the reciprocal descriptor change. This is not an inversion.
- Only selected valid E/Z is consumed. Unselected alkene geometry remains checked. Near-site specified centers and directional annotations that normalization would erase fail closed rather than silently losing information.
- New or initially unspecified tetrahedral centers remain unsigned. No syn/anti assignment, exact enantiomer ratio or 3D-conformer-derived net stereochemistry is invented.

Visualization shows verified **net bond changes**. A full step-by-step protonation/carbocation/halide-capture hydrohalogenation mechanism remains unimplemented and is explicitly marked unsupported. Existing SN1/SN2/E1/E2 mechanisms are unchanged.

## 6. Fixed 347-case benchmark

The matrix, expectations, scoring and audit script are unchanged. Script SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

**Hydrohalogenation: 8/16 (50.0%) → 12/16 (75.0%).** Five gains minus one conservative restriction. The saturated negative control remains correctly rejected.

| Case | Before | After |
| --- | --- | --- |
| A051, 2-hexene | Unsupported | Two validated constitutional options |
| A052/A053, E/Z-3-hexene | Unsupported | Unsigned 3-bromohexane connectivity |
| A054, styrene | Unsupported | Screened benzylic capture |
| A057, distant specified center | Unsupported | Physical retention and independent CIP |
| A059, 1,7-octadiene | Fully supported | Unsupported short pi-capture/cyclization risk |

Remaining applicable exclusions:

- **A055, 4-penten-1-ol + HBr:** additional C–O substitution/capture is not a validated preserve-only spectator model. A nearby OH also fails the HCl short-capture screen.
- **A056, remote fluoroalkene:** F is outside this pathway's validated spectator set, not declared incapable of reacting everywhere.
- **A058, 1-triacontene:** product exceeds 80 explicit atoms.
- **A059, 1,7-octadiene:** unresolved competing intramolecular capture as above.

All **330 non-hydrohalogenation rows are identical** to Phase 3A, including statuses, actual products, option counts, notes, preview/geometry outcomes and mechanism-step counts. Overall: **173 fully supported, 120 unsupported, 16 partial, 38 correctly rejected**. No audit-flagged incorrect chemistry or failed preview appeared. Original benchmark stereochemistry-grading caveats remain; expectations were not changed to improve the score. Fixed tested-case coverage is not comprehensive experimental prediction or complete mechanism coverage.

## 7. Verification

**1,195 tests pass: 594 Python + 601 JavaScript; zero failures or skips.** Added **65 Python + 79 JavaScript = 144 tests**. All 1,051 original methods remain. Three existing methods were updated only for intentionally superseded HX scope/orientation assertions; none was deleted. Hydration's independent positive/negative assertions remain.

New independent cases cover all three actual HX reagents, chain lengths/branches, internal/regio alternatives, cyclic scope, E/Z consumption/retention, benzylic capture, HCl-specific oxygen conditions, distant physical stereo/CIP, multiple and graph-equivalent sites, unsupported rings/groups/elements/reagents, rearrangement/capture risks, radical conditions and size limits. Tampered spectator bonds, stereo, atom maps, halogen identity/charge and incoming H placement fail strict validators.

Six authenticated HTTP tests exercise normal matching, both internal regio products, exact diagrams/3D maps, reversed inputs, condition-gated 422 responses, radical rejection, forged selections and multi-site grouping without hosting or real credentials. **72 public calculation fixtures** independently check product elemental masses, full HX molar masses, limiting reagent, theoretical yield and required amounts in both input orders. Seven JS checks verify status labels and existing UI gates/reset behavior.

The previous four-pathway diagnostic passes unchanged: **48 substrates, 192 public matching calls, 48 condition checks, five reagent controls, 125 verified options, zero failures**.

TypeScript `--noEmit`, production build and `git diff --check` pass. Existing third-party directive warnings and the large Builder bundle remain. SHA-256 comparison confirms 142 of 152 pre-existing tracked snapshot paths unchanged; the ten changed paths are HX integration/explanation/status code and the three intentionally updated test files. HTML/CSS, Calculators, curated/public molecular data, fixed benchmark, hydration/halogenation and unrelated rule/graph/stereo/rendering modules remain untouched. The new policy and test hashes are separately recorded without editing the benchmark's hash inventory.

The final localhost service was refreshed. Browser verification shows propene + HBr producing linked 2D/3D 2-bromopropane at the reacting carbon. Selecting radical initiation clears the prior product and gives the specific unsupported-radical explanation. Nothing was pushed, deployed or published.

[Audit, diagnostics, preservation checks and source hashes](</Users/rc/Documents/Capstone project/docs/reaction-lab-hydrohalogenation-phase3b-results.json>).

![Verified ionic HX comparison and linked carbon](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3b-preview.jpg>)

## 8. Remaining limits and next recommendation

No unrestricted rearrangement, solvent-capture, cyclization, radical, selectivity, yield or rate solver was added. HBr/HI oxygen spectators, many acid-sensitive/competing groups, near-site specified stereo, unvalidated rings and other cation environments remain excluded with precise model reasons. Constitutional alternatives do not define experimental distributions; a new-center conformer does not specify a stereochemical outcome.

Recommended next existing pathway: **alkene halogenation**, with independently validated X2-specific compatibility and halonium/anti-addition stereochemistry. It must not inherit ionic HX or hydration permissions automatically.

**Phase 3B stops here. Phase 3C and all other implementation increments have not been started.**
