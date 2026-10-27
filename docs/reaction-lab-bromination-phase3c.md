# Phase 3C — Alkene bromination

Completed October 14, 2026. This increment improves **existing Br2 addition only**. No new family, chlorination implementation, layout redesign, Calculator change, curated molecule/example additions or publication.

## 1. Implementation and new support

Added [bromination_rule.py](</Users/rc/Documents/Capstone project/server/bromination_rule.py>) and [bromination_stereo.py](</Users/rc/Documents/Capstone project/server/bromination_stereo.py>) as bromination-specific consumers of the shared site compatibility/edit architecture. The selected C=C and actual neutral Br–Br are identified by graphs, never names, formulas or CIDs.

New benchmark support includes **E-3-hexene, Z-3-hexene, styrene and an alkene with a distant specified stereocenter**. Previously accepted terminal/branched alkenes now expose their relevant R/S alternatives instead of one unsigned product. The cyclic example now has independently verified relative configurations, although the fixed audit still grades it partial (see section 6).

Independent tests additionally verify longer/branched chains, internal alkenes, ordinary isolated 5–7-membered cyclic alkenes, a substituted cyclohexene, terminal alpha-methylstyrene, screened remote primary/secondary alcohols and ordinary dialkyl ethers, both distant configurations, widely separated C=C sites and unselected E/Z preservation. These test structures were **not** added to the visible example collection.

Bromination does not inherit ionic HX's carbocation-rearrangement screen or acid-dependent oxygen permissions. For example, `C=CC(C)C` and `C=CC(C)(C)C` retain their carbon skeletons in this Br2 model rather than being rejected solely because an HX cation could rearrange. A bromonium-type addition is different chemistry. [Halogenation reference](https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2).

## 2. Stereochemistry

New local tags are derived from **exact mapped substituent relationships**, not an optimized/random 3D conformer and not an R-to-S text swap. With reference order `[other alkene carbon, reference 1, reference 2, entering Br]`, opposite Br faces require matching tetrahedral parities exactly when those starting reference groups are same-side. Actual neighbor order is accounted for; CIP is independently recalculated afterward.

Validated independent checks include:

| Starting structure | Verified modeled outcome |
| --- | --- |
| E-2-butene | One meso 2,3-dibromobutane structure, R/S local centers; equivalent face representations grouped |
| Z-2-butene | Separate R,R and S,S alternatives, without numerical populations |
| E/Z-3-hexene | Corresponding meso versus enantiomeric relationships verified independently |
| Unsymmetrical E-2-pentene | Two R,S / S,R alternatives, **not** automatically meso |
| Unsymmetrical Z-2-pentene | Two R,R / S,S alternatives |
| Ordinary 5–7-membered cycloalkenes | Trans Br/Br structures; R,R and S,S verified for the symmetric test rings |
| Propene / terminal styrene | Relevant single-new-center R/S alternatives |
| Unspecified internal alkene geometry | New local configurations left unassigned; no invented E/Z starting identity |

The E/Z and meso reference checks use independently specified expectations rather than the production transformation. [University-hosted halogenation/stereo reference](https://www.chem.uci.edu/files/smith_textbook/smi96656_c10_001_030.pdf).

**Anti is an addition geometry, not a universal “trans product” label.** Only the bounded ordinary small-ring relationship is named trans Br/Br. Unspecified cyclooctene is not assumed cis; its product stays unsigned. Valid specified cyclooctene geometry can supply local anti configurations, but this increment does not assign a generic ring-relative cis/trans label to the eight-membered product. Large-ring conformational/facial preferences are not predicted.

Distant specified physical configurations remain checked independently, including through serialization; CIP letters need not remain identical. One independent remote-center case changes its CIP descriptor after Br addition while retaining physical configuration. New local stereo is validated both before and after full mapped serialization. The unchanged strict edit/spectator validator receives a projection masking **only those two separately checked new local tags**; no spectator atom, bond, map, charge or stereochemistry is masked. No global permission to invent new stereo was introduced.

Conformer-derived CIP is checked against selected specified configurations using the actual **map-to-model-index correspondence**, not source atom order. Unsigned centers in a displayed conformer are not represented as a predicted product configuration or population.

## 3. Exact products, maps and multiple sites

Each option declares exactly four net edits: C=C changes 2→1, Br–Br breaks, and one C–Br forms at each endpoint. One substrate plus one actual Br2 gives one connected neutral dibromide, with **no net byproduct**. The two bromine maps retain reagent provenance. Hydrogen counts, element/charge conservation, all unaffected bonds, valence, product size and serialized structure remain validated.

Widely separated screened C=C sites can be selected independently. Equivalent site/face representations are grouped only when the full isomeric product agrees and a chirality-aware full-substrate automorphism relates the selected bonds. Enantiomers and non-equivalent sites remain separate. The chosen representative retains exact maps and records grouped site/face metadata. No selective mono-bromination, subsequent conversion or product distribution is inferred.

Existing 2D diagrams use the actual configured structures, including wedge/dash bonds. R/S assignments appear in existing site labels and Advanced reaction information. 2D/3D atom links, highlighted incoming bromines, bond-order changes and theoretical reaction calculations use the same selected mapped product. No UI panel or control was added or relocated.

## 4. Competing chemistry and condition gates

| Settings | Behavior |
| --- | --- |
| Existing Dry setting, no added activation | Qualified neutral, non-nucleophilic **net model**; exact solvent compatibility and experimental selectivity are not guaranteed |
| Medium unspecified | Conditional 2D only; no 3D dibromide until model-compatible medium is selected |
| Water | Bromohydrin capture can compete; conditional dibromide net inspection only, not an identical reaction |
| Ethanol | Solvent capture/bromoether formation is unvalidated; conditional 2D only |
| Generic polar-aprotic setting | Does not specify a non-nucleophilic solvent; nitrile/DMSO/other solvent chemistry is unvalidated, conditional 2D only |
| Added acid/metal/other activation, or heated conditions | Outside this bounded neutral model; conditional 2D only, not automatically called chemically unfavorable |
| Radical initiation | No ionic dibromide option; radical/allylic substitution is a different unimplemented pathway |

The Dry/no-water control is an existing coarse selector, **not a solvent-identity or laboratory protocol validator**. Dryness by itself does not establish non-nucleophilicity; the net option is explicitly qualified by that assumption. No claim of solvent safety or experimental conversion is made.

Blocked 3D requests return 422, including programmatic requests; condition changes clear previous selections/products. Water interception of a bromonium intermediate is distinct chemistry. [Halohydrin reference](https://openstax.org/books/organic-chemistry/pages/8-3-halohydrins-from-alkenes-addition-of-ho-x).

Remote oxygen groups are screened for ordinary saturated environments and potential **3–8-membered intramolecular capture**, at every alkene end. Nearby alkenols/ethers, activated/aromatic oxygen, acetals, other oxidizable/unvalidated groups and short pi-capture routes fail closed. Longer-range/intermolecular capture and eventual side chemistry are not resolved; distance is not proof of inertness. A primary discussion documents polar alkenol bromocyclizations under other reagent systems; this motivates risk screening, not a transferred Br2 protocol or universal ring-size/selectivity law. [Organic Syntheses discussion](https://www.orgsyn.org/Content/pdfs/procedures/v89p0409.pdf).

Internal/multiply aryl-adjacent alkenes remain excluded where stereospecific benzylic opening is unvalidated. Terminal styrene's single new center does not require inventing an internal two-center anti relationship. Activated/hetero/fused aromatic rings are not treated as inert spectators.

## 5. Remaining limits and newly restricted cases

- **New benchmark restriction: 1,7-octadiene (A029).** A nearby pi bond offers unresolved intramolecular capture/cyclization. The former uncomplicated one-site dibromide is no longer generated. This is conservative structural-risk screening, not evidence that cyclization must occur or dominate.
- **4-Penten-1-ol (A025):** nearby O capture is unresolved; longer remote ordinary OH/ethers are separately tested, not a blanket oxygen whitelist.
- **Remote fluoroalkene (A026):** F is outside this pathway's screened spectator set.
- **1-Triacontene (A028):** product exceeds the 80-explicit-atom software bound.
- Selected small/large, fused/bridged, exocyclic/junction and heterocyclic ring environments, conjugation/cumulenes, adjacent specified stereocenters, internal aryl-adjacent sites and additional unvalidated groups remain excluded.
- Reagent graphs other than actual neutral Br2 do not enter this pathway. No new NBS, halohydrin, radical or arbitrary prediction model was added.
- Missing/capturing/unknown media and added activation now restrict 3D generation instead of silently accepting the same dibromide-only model. This is not a claim those real reactions cannot occur.
- Full bromonium intermediate/mechanism visualization remains **unsupported**. This increment implements validated net changes and bounded stereo, not a fictitious complete mechanism.

## 6. Unchanged 347-case benchmark

Script, matrix, expectations and scoring are unchanged. Script SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

**Bromination: 6/14 (42.9%) → 9/14 (64.3%).** Four applicable cases gain full support, minus one newly restricted case. Both negative controls remain correctly rejected.

| Case | Change |
| --- | --- |
| A022/A023, E/Z-3-hexene | Unsupported → fully supported |
| A024, styrene | Unsupported → fully supported |
| A027, distant specified center | Unsupported → fully supported |
| A029, 1,7-octadiene | Fully supported → unsupported, unresolved competing capture |
| A020, cycloheptene | Remains **partial in the fixed audit**, despite newly assigned and separately verified trans structures |

The A020 grading is deliberately unchanged: the benchmark explicitly requires an independent stereoproduct expectation before awarding full support. It does not promote the row merely because tags are now assigned. The new independent R,R/S,S ring tests provide additional evidence, reported separately rather than altering the benchmark or its score.

All **331 non-bromination rows are identical** to Phase 3B, including statuses, products, option counts, notes, preview/geometry outcomes and mechanism-step counts. Overall: **176 fully supported, 117 unsupported, 16 partial, 38 correctly rejected**. No audit-flagged incorrect result or failed preview appeared. This is tested-case workflow coverage, not experimental accuracy or unrestricted chemistry coverage.

## 7. Verification

**1,299 tests pass: 652 Python + 647 JavaScript, zero failures/skips.** Added **58 Python + 46 JavaScript = 104 tests**. All 1,195 original methods remain. Eight existing methods in six test files update intentionally superseded bromination product/option IDs, stereo capabilities, scope or required-medium expectations; none was deleted. Independent assertions for other pathways remain intact.

New checks include independent connectivity, R/S/meso and cyclic relative configurations, exact H/Br maps, conservation, four bond edits, remote parity/CIP, full serialized stereo, 2D wedges, actual coordinate-derived configuration through model map links, source atom-order/map-number invariance, multiple sites/deduplication, wrong reagents/conditions and deliberately tampered products. No random embedding decides expected chemistry.

Five authenticated HTTP tests exercise real matching, E/Z/ring alternatives, 2D/3D maps, reversed input slots, oxygen capture rejection, condition-gated 422 responses and stale/forged radical selections without hosting or real credentials. **42 independent public amount fixtures** check Br2's full molar mass, product elemental masses, limiting reagent, theoretical yield and required amounts in both input orders. Stereoisomer alternatives are separate upper-bound calculations, not quantities to sum or assigned proportions.

The prior four-pathway diagnostic passes unchanged: **48 substrates, 192 public matching calls, 48 condition checks, five reagent controls, 125 verified options, zero failures**.

TypeScript `--noEmit`, production build and whitespace checks pass. Existing third-party directive and large Builder-bundle warnings remain. Source hashes confirm HTML/CSS, all frontend source/Calculator files, curated/public data, fixed benchmark, chlorination, hydration, hydrohalogenation, other rule modules and the shared graph/stereo/edit/diagram validators are unchanged. Five shared production files have bromination-specific integration/explanation branches; six existing test files have the eight intentional expectation updates.

Browser verification: the unchanged propene/bromine inputs display separate C2 R/S options; absent medium permits conditional 2D with disabled 3D; changing to the qualified neutral model clears stale results and permits the selected mapped 3D product. Incoming Br map 11 is linked in reactant, product and 3D views. The local service was refreshed. Nothing was committed, pushed, deployed or published.

[Audit, diagnostics and source-preservation evidence](</Users/rc/Documents/Capstone project/docs/reaction-lab-bromination-phase3c-results.json>).

![Verified bromination product and linked bromine atom](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3c-preview.jpg>)

## 8. Recommendation

Next candidate: the **existing alkene chlorination** pathway, but only in a separately requested increment with independently validated Cl2 compatibility, conditions and stereo. It must not inherit all Br2 permissions automatically.

**Phase 3C is complete and stops here. Chlorination and other implementation phases were not started.**
