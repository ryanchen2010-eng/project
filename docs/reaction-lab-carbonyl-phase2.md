# Reaction Lab — Phase 2B: site-compatible carbonyl hydrogenation

Completed locally on October 11, 2026. This increment applies the shared Phase 2
compatibility system only to the existing **carbonyl hydrogenation** pathway.
No reaction family, website layout, example collection or subsequent pathway
was added. Nothing was pushed, published or deployed.

Reverified on October 13, 2026 against the explicit Phase 2B checklist. The
implementation and audited core source hashes are unchanged. A fresh run of
all 648 tests, TypeScript, the production build and the 347-case audit passes;
all case observations match the saved carbonyl results. No additional chemistry
code or duplicate tests were needed. Phase 2A is alkene hydrogenation; the next
recommended increment, Phase 2C, is alcohol oxidation and remains unimplemented.

## 1. Investigation and implementation

The previous matcher admitted C/H/O aldehydes and ketones without C=C/C≡C, but
the candidate planner rejected specified tetrahedral centers anywhere in the
substrate. Some additional oxygen groups were accepted without a specific
compatibility check. The update replaces that handling with a carbonyl-specific
policy, rather than inheriting the alkene whitelist or widening global guards.

- [carbonyl_hydrogenation_rule.py](../server/carbonyl_hydrogenation_rule.py)
  identifies the actual aldehyde/ketone carbon and oxygen. Acids, esters, amides
  and other carbonyls cannot masquerade as the selected site.
- The shared compatibility inventory now accepts consumer-specific group
  queries. The carbonyl consumer screens ordinary remote saturated alcohols,
  dialkyl and carbocyclic aryl–alkyl ethers, including qualifying cyclic ethers.
  Each receives a mapped disposition and explanation; unknown groups fail
  closed. The original alkene policy is unchanged.
- Additional C=C/C≡C, peroxides, unvalidated carbonyl arrangements and other
  competing/unvalidated groups produce precise rejections. Hydroxy-carbonyl
  cyclization, adjacent carbonyls, alpha-hydroxy sites, benzyl/allyl ethers,
  acetals/ketals and catalyst-sensitive alcohols are screened separately.
- The exact edit contract requires selected C=O order **2 → 1**, removal of the
  actual H–H bond, and formation of **C–H and O–H** using those two hydrogens.
  The original carbonyl oxygen remains the alcohol oxygen. One connected
  neutral product is formed, with one H₂ consumed and no invented byproduct.
- Every other mapped atom, individual charge, isotope/electronic identity and
  bond must remain unchanged. Existing valence, sanitization and overall atom/
  charge conservation checks remain active. Contract failures remove the public
  candidate and explain why; product serialization is checked again.
- Distant specified tetrahedral configurations survive the mapped edit. CIP
  priorities are recomputed rather than copying R/S letters. Newly created
  alcohol stereocenters remain unassigned. A previously specified center that
  ceases to be stereogenic is rejected, not silently erased.
- A carbonyl/H₂-specific input guard rejects enhanced/unsupported stereo before
  canonicalization can strip its metadata. It does not opt unrelated reactions
  into this policy, and preserves existing input-size bounds.
- Public match → diagram → run exposes the same validated compatibility, site
  maps, bond changes, products and stoichiometry. Existing reasoning/information
  panels describe the bounded model; no frontend layout was modified.

The neutral, closed-shell, non-isotopic, single-connected-substrate restriction,
C/H/O element boundary, five-member minimum ring policy and 80-explicit-product-
atom cap remain in force. Distance alone never establishes chemical inertness.

## 2. Newly supported and independently validated structures

| Case | Checked result |
| --- | --- |
| Remote specified center, `CC[C@H](C)CC=O` | `CC[C@H](C)CCO`; mapped physical configuration retained |
| Opposite remote enantiomer | Opposite product enantiomer retained, not merged with the first |
| Remote center plus ether, `CC[C@H](C)COCCCC=O` | `CC[C@H](C)COCCCCO`; ether bonds and specified configuration preserved |
| Remote alcohol plus two specified centers, `CC[C@H](C)C[C@@H](O)CCCCCC=O` | `CC[C@H](C)C[C@@H](O)CCCCCCO`; both original configurations and OH retained |
| Remote specified center in a ketone, `CC[C@H](C)CCCC(=O)C` | `CC[C@H](C)CCCC(O)C`; old center retained, new alcohol center unassigned |

The browser-tested (3S)-3-methylpentanal case now produces the corresponding
3-methylpentan-1-ol with its mapped S center retained. This is the newly supported
fixed-audit case A115.

Plain remote alcohol/ether substrates were already accepted in parts of the old
C/H/O model; they are **not counted as newly supported** merely because tests
were added. They now receive explicit group screening and preservation checks.
Examples checked through public match/diagram/run include 3-methoxypropanal,
long and branched aldehydes, branched/cyclic ketones, cyclic ethers and remote
alcohols that do not meet the excluded local/cyclization patterns.

Existing carbocyclic aromatic net reductions and separated multi-carbonyl site
options remain working. For multiple separated C=O groups, each option transforms
only its selected site with one H₂; it does not claim selective partial conversion.

## 3. Chemistry boundaries and remaining limitations

The transformation is a bounded aldehyde/ketone-to-alcohol net option. The general
carbonyl reduction reference describes the product classes, not a universal
metal/H₂ procedure. [OpenStax, alcohols from carbonyl compounds](https://openstax.org/books/organic-chemistry/pages/17-4-alcohols-from-carbonyl-compounds-reduction).
An aldehyde hydrogenation study uses a particular iridium catalyst; it does not
validate every substrate under the UI's generic metal choice.
[A Versatile Iridium Catalyst for Aldehyde Reduction in Water](https://doi.org/10.1002/cssc.200700086).

Carbocyclic aromatic skeletons are retained only in the bounded net option.
Ring hydrogenation and benzylic deoxygenation are condition/catalyst-dependent,
so aromatic or additional-carbonyl options are labeled **Possible**, not presented
as proven selective Pd/Pt protocols. [OpenStax, reduction of aromatic compounds](https://openstax.org/books/organic-chemistry/pages/16-9-reduction-of-aromatic-compounds).

Alcohol addition to carbonyl groups and acetal chemistry justify checking more
than distance. Our potential five-/six-membered hemiacetal/hemiketal closure
screen is a conservative graph-based model boundary, **not** a prediction that
every such substrate necessarily cyclizes. [OpenStax, alcohol addition and acetal formation](https://openstax.org/books/organic-chemistry/pages/19-10-nucleophilic-addition-of-alcohols-acetal-formation).
Benzyl/allyl ether retention is likewise not assumed under hydrogenation; the
documented hydrogenolysis concern supports retaining a separate exclusion.
[Organic Syntheses, ether protecting-group cleavage discussion](https://www.orgsyn.org/demo.aspx?prep=v84p0295).

Still outside this increment:

- Additional alkene/alkyne sites, including specified E/Z that would require
  validated chemoselective retention; conjugated/cumulated and adjacent or
  1,3-dicarbonyl arrangements.
- Extra acid/ester/amide/phenol/peroxide groups, heteroaromatics, remote halogens,
  amines, sulfur groups and other spectators without a validated policy.
- Alpha-hydroxy carbonyls, potential five-/six-membered hydroxy-carbonyl closures,
  benzyl/allyl and diaryl ethers, acetals/ketals/geminal diols, and allylic/benzylic
  alcohol spectators.
- Specified centers at/adjacent to the selected carbonyl, unsupported enhanced/
  relative/non-tetrahedral stereo, and any failed preservation postcondition.
- Small strained rings, oversized products, disconnected, charged, radical,
  isotopic, invalid or query substrates.
- NaBH₄ or other newly supported reductants, a new elementary mechanism, chosen
  reaction faces, predicted stereoisomer ratios, complete multi-carbonyl reduction,
  experimental catalyst protocols, rates, practical yields or safety claims.

These exclusions distinguish unsupported modeling from chemical impossibility.
They are specific to this consumer; other reaction rules keep their restrictions.

No unexpected connectivity, charge, atom mapping or preview failure appeared in
the final checks. Two deliberate stereochemical edge cases were important:
R/S can switch when substituent priorities change without physical inversion;
and equal product arms can destroy a previously specified center, which fails
closed. Both are independently tested.

Some previously unscreened carbonyl matches are now deliberately rejected. For
example, levulinic acid contains an additional carboxylic acid without a validated
spectator policy. Its public rejection explains that distinction rather than
quietly promising selective ketone reduction. This is targeted chemistry
tightening, not a removal of unrelated pathway functionality.

## 4. Fixed-matrix audit comparison

The pre-change rerun reproduced the saved previous Phase 2 baseline. The same
**347 cases** retain identical inputs, expected products, conditions, required
sites and score categories. A115 additionally requires its independently entered
isomeric expectation now that it reaches the public workflow; connectivity alone
cannot earn stereo-retention support. New regression examples do not inflate
the audit denominator.

| Pathway | Before this increment | After this increment |
| --- | --- | --- |
| Carbonyl hydrogenation | 6/11 — 54.5% | 7/11 — 63.6% |
| Alkene hydrogenation | 11/14 — 78.6% | 11/14 — 78.6% |
| Ester hydrolysis | 9/10 — 90.0% | 9/10 — 90.0% |
| Ester saponification | 10/11 — 90.9% | 10/11 — 90.9% |

Carbonyl tested-case coverage improves **9.1 percentage points**. Only A115
changes status: Unsupported → Fully supported. All **335 rows outside carbonyl
hydrogenation** have unchanged statuses; all other pathway scores are unchanged.
Across the 309 positives, full support is **154 → 155**, partial remains **16**,
and unsupported is **139 → 138**. All **38 negative controls** remain correctly
rejected. There are **zero incorrect-result rows and zero preview failures**.
The rerun checks **206 generated site options**, previously 205.

The four remaining positive carbonyl failures are the remote-fluoro substrate,
remote amine, competing unsaturated carbonyl and NaBH₄ reagent case. These are
unvalidated spectators/selectivity or unsupported reagent coverage, not assertions
that the corresponding real-world reactions cannot occur.

Preserved baselines: [previous Phase 2 report](reaction-lab-hydrogenation-phase2.md),
[previous Phase 2 JSON](reaction-lab-hydrogenation-phase2-results.json), and
[Phase 1 ester results](reaction-lab-ester-phase1-results.json).
New [carbonyl audit JSON](reaction-lab-carbonyl-phase2-results.json) records all
observations and the final audited core source hashes. Scores describe this
bounded tested matrix, not universal reaction coverage or experimental probability.

## 5. Tests, production build and browser verification

**All 648 tests pass: 256 Python + 392 JavaScript.** This preserves the previous
616 and adds **24 Python tests + 8 JavaScript tests**, with multiple molecular
subcases. The existing carbonyl capability expectation was updated to reflect
checked spectator retention; no product/conservation assertion was weakened.

The new checks include:

- Independently entered products for simple/long/branched/cyclic carbonyls,
  qualifying alcohols/ethers, both remote enantiomers and combined spectator groups.
- Correct selected versus unselected carbonyl sites, exact stoichiometry,
  source-map provenance, reversed input order, original-oxygen retention and all
  mapped atom/charge/bond changes.
- CIP priority changes versus inversion, lost stereogenicity rejection, unsigned
  newly created alcohol centers and enhanced-stereo rejection before canonicalization.
- Actual diagram → run 2D/3D atom correspondence and independent conformer CIP
  checks for old specified centers, even when a new center remains unassigned.
- Competing/unvalidated groups, invalid inputs, size and catalyst boundaries,
  counterfeit names/formulas/CIDs, deliberate atom/charge/bond/map/stereo corruption
  and injected validation failures.
- Authenticated production HTTP match/diagram/run routes with real chemistry
  responses, and preservation of Phase 1 esters, alkene compatibility and other
  pathway restrictions.
- Real public stoichiometry fed to the browser calculator: independent product
  molar masses, one H₂ per site, limiting reactants, required amounts and theoretical
  yields, including both input orders and two separated ketone sites.

The production build passes (`tsc` and `vite build`). Existing dependency
`use client` and large-builder-chunk warnings remain; they are not new failures.
`git diff --check` passes. No frontend HTML, CSS or TypeScript was changed by
this increment.

The localhost preview was refreshed to the final source. A separate temporary
browser tab verified:

- PubChem search for 3-methoxypropanal, correct ether-containing alcohol product,
  and exact original carbonyl-oxygen linking across 2D and 3D.
- PubChem search for (3S)-3-methylpentanal, its mapped retained S configuration,
  and selection of carbon 3 in the linked comparison view.
- Levulinic acid's precise additional-carboxylic-acid rejection.
- No warning/error console logs. The temporary tab was closed; user tabs were
  not overwritten. The local preview remains running.

Evidence: [ether correspondence](reaction-lab-carbonyl-phase2-ether.png),
[retained chiral carbon](reaction-lab-carbonyl-phase2-stereo.png),
[stereochemistry information](reaction-lab-carbonyl-phase2-stereo-information.png),
and [specific rejection](reaction-lab-carbonyl-phase2-rejection.png).

## 6. Recommended Phase 2C pathway — not implemented

Next, evaluate the existing **alcohol oxidation** pathway with its own
oxidant-specific competing-group policy and distant-center retention checks.
Oxidizing a chiral alcohol carbon can legitimately remove that center by making
a planar carbonyl; that local change needs a declared, tested stereo contract,
not a global bypass of stereo preservation. Apply it in another controlled
increment only after reviewing those boundaries.

This recommendation has not been implemented. This work stops at carbonyl
hydrogenation.
