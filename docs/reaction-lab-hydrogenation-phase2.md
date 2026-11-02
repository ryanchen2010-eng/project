# Reaction Lab — Phase 2 initial increment: site-compatible hydrogenation

Completed locally on October 9, 2026. Only the existing **alkene hydrogenation**
pathway adopts the new compatibility policy. No reaction family, website layout,
example collection, publication or subsequent increment was added.

## 1. Restrictions investigated and changes implemented

The previous hydrogenation matcher required the **entire substrate to contain
only C/H**. The common candidate planner also blocked specified tetrahedral
centers, except for existing SN2 and Phase 1 ester exceptions. Consequently, an
ordinary distant alcohol or an unchanged remote center prevented an otherwise
supported isolated C=C edit. These were software coverage restrictions, not
evidence that the corresponding hydrogenation is chemically impossible.

The global neutral/closed-shell/non-isotopic input guards, small-ring exclusions,
80-explicit-product-atom limit and local isolated-alkene check are retained.
Conjugation, competing reducible groups and catalyst-sensitive environments need
their own chemistry validation; distance alone is not permission to ignore them.
Other reaction pathways retain their existing element/stereo/site restrictions.

New implementation:

- [reaction_compatibility.py](../server/reaction_compatibility.py) provides a
  per-pathway policy with actual reactive graph indices, functional-group
  inventory, group-to-site distances, dispositions and structured rejection
  codes/categories. Unknown groups fail closed. Structural failures, software
  limits, unvalidated environments and possible competing chemistry are distinct.
- [hydrogenation_rule.py](../server/hydrogenation_rule.py) is the **only initial
  consumer**. It screens the actual isolated C=C and ordinary saturated aliphatic
  alcohol groups, excluding allylic/benzylic alcohols and multiple-oxygen carbon
  environments. Applicable remote specified centers may be retained; a center
  at/adjacent to the selected C=C remains outside this increment.
- Every additional group is evaluated, including other isolated/non-isolated
  C=C bonds, alkynes, carbonyl groups, esters, aromatic rings, ethers, peroxides,
  phenols and unclassified oxygen environments. Element filtering is pathway
  specific, not globally widened.
- The exact mapped edit contract requires C=C order 2 → 1, removal of the
  actual reagent H–H bond, and two C–H bonds. All other atom identities, isotope
  identities, individual charges, bonds and connected-component counts must
  remain correct. The existing sanitization, valence, radical and total
  conservation checks run as well.
- The stereo-retention validator was extracted from Phase 1 into the shared
  [stereochemistry utilities](../server/stereochemistry.py), with the ester
  wrapper and strict no-stereo-loss behavior preserved. Only the declared,
  actually reduced C=C may consume its original E/Z geometry. Physical mapped
  tetrahedral configurations and unselected alkene geometries are checked again
  through product serialization. CIP labels are recomputed, not blindly copied.
- A failed postcondition removes the candidate and gives its specific reason.
  A specified center that ceases to be stereogenic is rejected rather than
  silently erased. Enhanced/relative or unsupported stereo is rejected before
  input canonicalization can remove that metadata.
- Public match responses include the validated group dispositions, reactive
  atom maps, bond-edit contract and verification summary. The existing reasoning
  and information panels explain the retained groups and bounded model. Alcohol
  products are no longer misleadingly called simply “Alkane product.”

The actual public match → diagram → run workflow uses this same validator; this
is not an internal-transform-only expansion. No other pathway was opted in.

## 2. Previously unsupported cases that now work

| Case | Result |
| --- | --- |
| 4-Penten-1-ol, `C=CCCCO` | Pentan-1-ol, `CCCCCO`; C–O and O–H retained |
| Tested homoallylic, branched and cyclic alkenols | Selected isolated C=C reduced; screened OH connectivity retained |
| Tested separated saturated alcohol groups | Each qualifying OH retained, not treated as an arbitrary inert heteroatom |
| Remote specified center, `C=CC[C@H](C)CC` | `CCC[C@H](C)CC`; physical configuration retained |
| Tested remote OH plus one/two specified centers, and opposite enantiomers | Exact independent isomeric identities retained |
| Multiple isolated C=C sites with qualifying remote OH or specified unselected E/Z | Distinct one-site candidates; other C=C and its specified geometry retained |

Simple, branched, cyclic and specified E/Z alkene regressions remain working.
Separate site IDs are retained even when molecular symmetry gives the same
constitutional product. Multiple isolated C=C sites were already supported in
the hydrocarbon-only model; they remain available and now use the same explicit
compatibility and bond-preservation checks.

Each candidate consumes **one H₂ per selected C=C** and forms one connected
neutral product with no invented byproduct. This is a one-site net option, not
a prediction that one double bond can be selectively reduced in an experiment.

## 3. Cases still unsupported and why

- Conjugated/cumulated, aromatic-adjacent or directly heteroatom-substituted C=C;
  a second non-isolated C=C elsewhere also blocks selective one-site handling.
- Additional alkynes, aldehydes/ketones and peroxides: potentially competing or
  catalyst-dependent reductions are not resolved by this policy.
- Aromatic-containing substrates, esters/acids/amides, ethers, phenols, remote
  halogens, amines/thiols and other unvalidated spectators: excluded pending
  specific compatibility validation, **not declared incapable of reaction**.
- Allylic/benzylic OH, geminal diols/hemiacetals, near-site specified centers,
  enhanced/relative/non-tetrahedral stereo, and any failed stereo-retention check.
- Strained rings below five members, products exceeding 80 explicit atoms,
  charged/radical/isotopic/query substrates and disconnected substrates.

In the fixed hydrogenation audit, the three remaining positive failures are
styrene, the remote-fluoro alkene and 1-triacontene. Their public explanations
identify the unvalidated local/aromatic environment, the F/haloalkane spectator
policy, and the size limit, respectively.

These bounds distinguish missing software/chemoselectivity support from genuine
structural invalidity. They do not claim universal inertness or impossibility.

## 4. Chemistry and stereochemistry risks

No unexpected product connectivity, charge, balance, mapping or preview failures
were found in the final matrix or independent regression cases.

One deliberate test changes a retained center's CIP label from R to S because
hydrogenation changes substituent priority; the physical configuration does not
invert. A separate example makes two arms identical and destroys stereogenicity;
the tool rejects it instead of retaining an invalid tag or silently removing it.

New stereocenters remain unassigned. Existing 3D generation renders a
representative conformer, not a predicted stereoisomer or selected reaction face.
Preserved mapped stereo describes the bounded net edit, not an experimental
guarantee against epimerization, hydrogenolysis, isomerization or further reduction.

Real catalytic hydrogenation is syn addition, and chemoselectivity depends on
the catalyst and conditions. This increment does not assign syn-face outcomes
or selective partial conversion; the exclusion of other reducible groups is a
conservative model boundary. See the primary
[OpenStax hydrogenation reference](https://openstax.org/books/organic-chemistry/pages/8-6-reduction-of-alkenes-hydrogenation).
No rates, product ratios, measured energies, practical yields or laboratory
procedure/safety claims are generated.

## 5. Audit comparison with Phase 1

The preserved **347 matrix cases**, input structures, conditions, independent
expectations, required sites and score categories were compared field by field
and are unchanged. The remote-chiral-center row additionally checks its exact
independent isomeric expectation now that it reaches the public workflow; a
connectivity-only match cannot earn this stereo-retention improvement.

| Pathway | Phase 1 | Initial Phase 2 | Change |
| --- | --- | --- | --- |
| Alkene hydrogenation | 9/14 — 64.3% | 11/14 — 78.6% | +14.3 percentage points |
| Ester hydrolysis | 9/10 — 90.0% | 9/10 — 90.0% | Unchanged |
| Ester saponification | 10/11 — 90.9% | 10/11 — 90.9% | Unchanged |

Exactly two statuses changed, both Unsupported → Fully supported:

- A010: remote OH, 4-penten-1-ol.
- A012: remote specified chiral center.

All **331 rows outside hydrogenation** have unchanged status. Across 309
applicable positives, full support increased **152 → 154**, partial remains
**16**, and unsupported decreased **141 → 139**. All **38 negative controls**
remain correctly rejected. There are **zero incorrect-result rows and zero
preview failures**. The rerun exercises **205 site options** through public
match/diagram/run, including exact main-product 2D/3D correspondence.

These are bounded tested-case coverage figures, not universal chemistry coverage
or experimental probabilities. The additional multi-molecule regression cases
are not mixed into the denominator to inflate the comparison.

- Preserved [Phase 1 report](reaction-lab-ester-phase1.md) and
  [Phase 1 JSON](reaction-lab-ester-phase1-results.json).
- [Phase 2 rerun JSON](reaction-lab-hydrogenation-phase2-results.json), including
  all case observations and audited core source hashes.

## 6. Tests, build and browser checks

**All 616 tests pass: 232 Python + 384 JavaScript.** Added **22 Python tests and
8 JavaScript tests**, with multiple independent molecular/negative subcases.
Only the existing hydrogenation capability expectation was updated to describe
validated spectator retention; chemistry/conservation assertions were retained.

Checks include independent isomeric product identities, both remote enantiomers,
priority-changing CIP retention, unchanged OH/bonds/individual charges, multiple
sites, selected versus unselected E/Z, actual newly created unassigned centers,
source map provenance, reversed inputs, product-size boundaries, invalid and
unsupported structures, wrong reagents, missing catalysts, deliberately corrupted
bond/map/atom/charge/stereo contracts and injected validation failures. Unknown
groups fail closed. Other pathways cannot automatically inherit the policy.

Authenticated production HTTP match/diagram/run routes were tested with real
backend responses. Public stoichiometry also feeds the actual browser reaction
calculator in JavaScript tests: one H₂ per site, independent molar masses,
limiting reactants, theoretical yield and required amounts, in either input order.
All Phase 1 ester regression tests remain passing.

The production build passes (`tsc` followed by `vite build`). Existing dependency
`use client` and large-chunk warnings remain; these are not Phase 2 build
failures. `git diff --check` passes. No frontend HTML, CSS or TypeScript was
changed by this increment.

The local preview backend was refreshed. In a separate browser test tab:

- Public Search PubChem resolved 4-penten-1-ol; H₂ plus the existing metal setting
  exposed its hydrogenation pathway, correct equation, 2D product and 3D model.
  Selecting the retained oxygen linked that exact atom across both views.
- Public search for 1,7-octadiene exposed both isolated site options, and the
  second site could be selected and previewed independently.
- Allyl alcohol remained unsupported, with a precise allylic/benzylic
  compatibility explanation rather than the old generic failure.
- No warning/error console logs were observed. The temporary tab was closed;
  the user's tabs were not overwritten. The local preview remains running.

Evidence: [linked remote alcohol](reaction-lab-hydrogenation-phase2-alcohol.png),
[separate isolated sites](reaction-lab-hydrogenation-phase2-multisite.png), and
[specific rejection](reaction-lab-hydrogenation-phase2-rejection.png).

## 7. Recommended next consumer — not implemented

Next, consider the **existing carbonyl hydrogenation** pathway, one controlled
increment at a time: validate isolated aldehyde/ketone sites with screened remote
alcohols and distant specified centers. Reuse the mapped edit/retention contract,
but independently validate the C=O-specific group policy and reject competing
C=C/C≡C, unvalidated functional groups and unsupported new stereochemical
outcomes. It must not simply inherit the alkene whitelist.

After that, bounded existing alcohol oxidation could be evaluated with its own
oxidant-competition policy. Neither adoption was performed here. Nothing was
pushed, published or deployed, and no subsequent phase was started.
