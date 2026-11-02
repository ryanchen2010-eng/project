# Phase 3E — Alkene epoxidation

Completed Phase 3E only. Existing peroxyacid epoxidation was expanded; no new reaction family, website layout, Calculator, curated examples, publication or deployment changes. Dihydroxylation was not started.

## 1. Implementation and newly supported structures

The existing [epoxidation rule](</Users/rc/Documents/Capstone project/server/epoxidation_rule.py>) now consumes the shared site-compatibility and strict mapped-edit architecture. It has its own peroxyacid, substrate, functional-group, competition and condition checks. Graphs determine eligibility, not names, formulas, CIDs or hard-coded example identities.

New benchmark support includes **styrene, E-3-hexene, Z-3-hexene and the distant specified stereocenter example**. Additional independent tests cover terminal/internal/branched chains, isolated 5–7-membered cyclic alkenes, substituted cyclohexene, alpha/beta-methylstyrenes, E/Z-stilbene, screened remote saturated alcohols/ethers, both distant configurations and several isolated C=C sites.

The original peroxyacid detector is retained. Peracetic, performic, peroxypropionic, perbenzoic and **mCPBA** examples remain supported with their own actual acid coproducts. Added screening rejects reagent environments with unresolved competing oxidation or unsupported stereochemistry. This is not a switch to peroxide-only, halogenation or dihydroxylation chemistry.

Only element-independent mapped reference/permutation helpers and chirality-aware graph equivalence are reused from earlier phases. Epoxidation implements its **own same-face relationship**, not the halogen anti rule. No existing bromination/chlorination/hydration/HX rule or shared validation permission was changed.

## 2. Exact oxygen/proton provenance and products

The terminal peroxyacid O—the oxygen farther from the acyl carbon—forms both new C–O bonds. The selected C=C becomes single, closing a three-membered epoxide. The actual acyl skeleton becomes its corresponding carboxylic acid.

The old connectivity-only model placed the peracid proton on the proximal oxygen while leaving the original carbonyl unchanged. This increment aligns the complete atom mapping with the **formal concerted textbook transfer**:

- Terminal peroxide O enters the epoxide.
- The original carbonyl O accepts the peracid proton.
- The proximal peroxide O becomes the acid carbonyl oxygen.

Thus the exact contract contains **eight edits**: three formed bonds, two broken bonds and three order changes. Both acid C–O order changes are explicit, in addition to C=C reduction. The unmapped acid identity is unchanged; its mapped oxygen/proton roles are now consistent with the displayed mechanism. This follows the [university-hosted concerted mechanism description](https://chem.ucalgary.ca/courses/351/Carey5th/Ch06/ch6-9.html).

All atoms, hydrogens and charges are conserved across **both** product fragments. One substrate plus one peroxyacid produces one epoxide plus one acid; the peroxyacid is consumed, not a catalyst. Untouched bonds, atoms and physical stereochemistry are checked before and after mapped serialization. The existing strict shared validators are unchanged. A regression deliberately restores the old acid mapping: although the unmapped chemical identities are identical, the new exact contract correctly rejects that mapping.

These are atom roles in a formal reaction model, not a simulation of later acid proton/oxygen exchange or an experimental isotope-label prediction. Isotopic inputs remain outside this rule's supported scope.

## 3. Verified stereochemical outcomes

Peroxyacid epoxidation preserves the reacting alkene's substituent relationship through same-face oxygen transfer. [Epoxidation reference](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation).

New tags are computed from exact mapped substituents and actual neighbor-order parity, followed by independent CIP assignment. Neither an R/S letter swap nor a sampled optimized conformer chooses the result.

| Starting structure | Independently verified modeled outcome |
| --- | --- |
| E-2-butene / E-3-hexene | Trans alkyl relationships; separate R,R and S,S alternatives |
| Z-2-butene / Z-3-hexene | Cis alkyl relationships; one meso R/S structure after equivalent representations are grouped |
| Unsymmetrical E/Z-2-pentene | Corresponding trans/cis structures remain distinct; not automatically meso |
| E/Z-stilbene | Trans enantiomeric alternatives versus cis meso structure |
| Ordinary cyclopentene/cyclohexene/cycloheptene | Configured cis-fused epoxides; independently checked R/S relationships for symmetric examples |
| Substituted cyclohexene | Distinct validated approach-face alternatives without a facial preference |
| Propene / terminal styrene | Single-new-center R/S alternatives where stereogenic |
| Unspecified internal/tetrasubstituted geometry | New local configurations remain unassigned |

The metadata names **which two mapped reference substituents** are cis/trans. It does not call every product universally cis because oxygen transfer is syn. Non-stereogenic centers do not acquire tags. Selected alkene geometry is consumed; unselected E/Z and distant specified physical configurations remain checked.

A retained distant center can change its CIP descriptor: an independent hydrocarbon example changes **S to R without physical inversion**. Source atom-order/map-label permutations, serialized structures and deliberately inverted/erased tags are tested. Actual 3D coordinates are independently reassigned and compared with selected CIP configurations using the map-to-model-index links; they verify a chosen structure rather than predict a product population.

## 4. Concerted mechanism support

The existing step-panel architecture can represent this model accurately, so a dedicated [epoxidation mechanism](</Users/rc/Documents/Capstone project/server/epoxidation_mechanism.py>) is implemented:

1. One concerted step contains all four formal electron-pair moves.
2. The exact C=C, peracid O–H, O–O and original C=O bonds are the sources.
3. Destinations are the two epoxide C–O bonds, new acid C=O and acid O–H.
4. Proton movement and all eight net edits are explicit.
5. There are **no stable intermediates**, carbocations, halonium ions or invented free hydroxide.

The mechanism reconstructs the reaction from the actual inputs, validates the full atom/edit/stereo contract and agrees with **both** mapped net products. A separate check enforces every source/destination. Missing/tampered arrows, wrong acid roles, changed spectator bonds, charge/map corruption and invalid configurations fail closed. Output atom reordering does not change validation.

This is a **formal textbook electron-pair description**, not computed synchronous electron flow, a transition-state structure, curved-arrow geometry, an energy calculation or a measured rate. Quantum-chemical analysis distinguishes arrow bookkeeping from detailed electron-flow timing; that distinction is stated in the mechanism limits. [Primary analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC6769425/).

The existing Mapped mechanism panel shows one step, starting/product states and four selectable electron-movement controls. No panel was redesigned or relocated. 3D highlights only main-product atoms; the complete acid coproduct remains in the mapped 2D states.

## 5. Conditions, competing chemistry and remaining limits

| Existing settings | Behavior |
| --- | --- |
| Dry compatible-medium model, no added activation | Conditional isolated-epoxide net option can run; not a solvent/protocol or actual isolation guarantee |
| Medium missing | Qualified 2D/mechanism inspection only; 3D run rejected |
| Water or ethanol | Acid-promoted epoxide opening/solvent capture is unresolved; qualified 2D only |
| Generic polar aprotic | Exact peracid/solvent compatibility and product stability are unvalidated; qualified 2D only |
| Added acid/metal/other activation, or heated settings | Outside the bounded model; qualified 2D only, not automatically labeled chemically impossible or unfavorable |
| Radical initiation | No concerted peroxyacid option is inferred |

Blocked runs return **422**, including direct API requests. Input/condition changes clear old products and mechanisms. The actual peroxyacid activates its own transfer; an additional acid catalyst is not required or silently consumed.

The Dry selector is coarse. It does not establish exact solvent, buffering, water content, safety, reaction time or product lifetime. The acid coproduct may promote later epoxide opening/rearrangement even when initial epoxidation is possible. Those secondary transformations, oxidation rates, isolated yields and facial/site ratios are not predicted.

Screened remote ordinary primary/secondary alcohols and unactivated dialkyl ethers can remain in the bounded neutral-reporting model. **Nearby OH/ether groups**, directed/acid-labile environments and potential 3–8-membered capture/opening routes remain excluded. Distance is not proof of universal inertness. The audit's 4-penten-1-ol still fails for a potential six-membered oxygen-capture route; longer remote examples are separately tested.

Other remaining restrictions include conjugated/cumulated or directly heteroatom-substituted alkenes, competing carbonyl oxidation, activated/fused/heteroaromatic environments, adjacent specified centers without a validated directed/facial model, unvalidated elements/electronic states and the 80-explicit-atom product/reagent bounds. Unsupported does not mean chemically incapable of epoxidation.

### Newly restricted cases

An in-memory replay of the saved pre-3E candidate rule confirms the following previously accepted candidate environments now fail closed:

- **Cyclooctene and larger selected rings:** the present configured ring scope is isolated 5–7-membered carbocycles. This is an independent geometry-validation boundary, not a claim that real cyclooctene cannot form an epoxide.
- **Exocyclic and fused/bridged selected sites:** no unsupported spiro/facial or ring-strain outcome is asserted.
- **Peroxyacid reagents with additional carbonyl/oxygen groups or unsaturated substituents:** unresolved competing reagent oxidation is no longer silently ignored. Common validated peroxyacids, including mCPBA, are retained.
- **Malformed/unsupported peracid stereo annotations:** a narrow pre-canonicalization guard rejects tags/directions that normalization would otherwise erase. Normal map labels remain valid bookkeeping, not CIP priorities.
- **Missing/capturing/unknown media, added activation/heat and radical conditions:** the old unconditional 3D epoxide behavior is restricted as described above.

These new restrictions do **not** reduce any formerly fully supported case in the fixed benchmark. No new invalid product or unexpected chemistry result was flagged by the tests/audit; this is not proof of unrestricted experimental chemoselectivity.

## 6. Multiple sites and unchanged audit

Each supported isolated C=C has its own one-oxygen-transfer option. Other sites and specified geometry remain intact. Equivalent site/face representations are grouped only when the full isomeric products agree and a chirality-aware whole-substrate automorphism relates the bonds. Distinct products/sites stay selectable. No experimental mono-epoxidation selectivity is claimed.

Unlike halonium addition, this concerted model does not automatically import a free-ion pi-capture screen: isolated 1,7-octadiene remains supported as conditional one-site epoxidation. Its exact equivalent-site aliases are tested, not inferred from merely counting R/S options. The fixed audit's minimum-site check counts options; the separate alias tests provide the stronger site-identity evidence without changing the benchmark.

The **347-case script, cases, expectations, scoring and hash inventory are unchanged**. Script SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

**Epoxidation: 5/11 fully supported (45.5%) → 9/11 (81.8%).**

| Benchmark cases | Result |
| --- | --- |
| A236, styrene | Unsupported → fully supported |
| A237/A238, E/Z-3-hexene | Unsupported → fully supported |
| A239, distant specified center | Unsupported → fully supported |
| A234, cycloheptene | Remains partial under the unchanged independent-stereoproduct criterion |
| A235, 4-penten-1-ol | Remains unsupported for nearby oxygen capture/direction |
| A240, multiple sites; A253, mCPBA | Full support retained |
| Saturated substrate and peroxide-only controls | Correct rejection retained |

The fixed cyclic row lacks an independent stereoproduct expectation and is not promoted simply because tags are assigned. New independent cyclic tests establish additional evidence separately. All **334 non-epoxidation rows are identical** to Phase 3D, including products, option counts, notes, geometry, previews, mechanisms and statuses.

Overall fixed results: **183 fully supported, 110 unsupported, 16 partial, 38 correctly rejected**. These are tested-case workflow scores, not experimental accuracy or general chemistry coverage.

## 7. Tests, build and preservation

**1,572 tests pass: 799 Python + 773 JavaScript; zero failures/skips.** Added **167 tests**:

- 70 independent compatibility/chemistry/mechanism tests.
- Nine authenticated public HTTP tests, including match/diagram/run, mCPBA, exact oxygen/acid/proton roles, reverse slots, multiple sites, configured products, condition gates and forged/stale selections.
- 84 public amount fixtures covering peracetic acid and mCPBA in both input orders, including correct full reagent masses, actual acid identities, total mass balance, limiting reagent, theoretical main-product amounts and required inputs.
- Four existing-UI gating/reset checks.

All **1,405 original tests remain**. Nine methods in three existing files intentionally update superseded epoxidation assumptions: configured alternatives instead of unsigned products, supported E/Z, actual acid bond-order changes, grouped equivalent sites, implemented mechanism/stereo and explicit dry conditions. Other-pathway assertions remain intact; no original method was removed.

An additional before/after differential check covers **120 public match contexts and 104 full diagrams** across bromination, chlorination, hydration and HBr addition. The complete payload hash is identical: `1b7b7928f37896bfaaa515f84dec58162627ec674b13782726b16e0d526f8c47`. The prior SN1/SN2/E1/E2 diagnostic also passes: **48 substrates, 192 public matching calls, 48 condition checks, five reagent controls, 125 verified options, no failures**.

**TypeScript, production build and whitespace checks pass.** Existing third-party ignored `use client` directives and large Builder-bundle warnings remain. Hashes confirm all HTML/CSS/frontend/Calculator/curated data files, other pathway rules and shared graph/stereo/edit/diagram validators are unchanged. Seven existing production files contain epoxidation-specific implementation/integration; two new backend modules supply stereo and mechanism behavior.

Browser verification confirms existing Propene + Peracetic acid inputs expose C2 R/S choices, the epoxide/ethanoic-acid equation and linked transferred **O14** in reagent, product and 3D. The mechanism panel has one concerted step and four working electron controls. Water clears prior results and disables 3D while preserving qualified 2D/mechanism inspection with an opening explanation. The local service was refreshed; the temporary test tab was closed. No commit, push, deployment or publication occurred.

[Machine-readable audit, diagnostics and source-preservation evidence](</Users/rc/Documents/Capstone project/docs/reaction-lab-epoxidation-phase3e-results.json>).

![Verified epoxidation and transferred oxygen linked across 2D/3D](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3e-preview.jpg>)

## 8. Recommended next pathway

Separately review and improve the **existing alkene dihydroxylation** pathway, with its own reagent system, exact two-oxygen/proton provenance and independently validated syn stereochemistry. Do not transfer peroxyacid or halogen permissions blindly.

**Phase 3E is complete and stops here. Dihydroxylation was not started.**
