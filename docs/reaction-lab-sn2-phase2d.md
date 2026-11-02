# Reaction Lab — Phase 2D: site-compatible hydroxide SN2

Completed locally on October 13, 2026. Only existing **SN2 substitution** adopts
the new policy. SN1, E1, E2, all earlier consumers, the website layout, controls
and Calculators retain their existing behavior. No new family, nucleophile or
leaving-group family was added. Nothing was published, pushed or deployed.

## 1. Implementation and structural compatibility

The previous SN2 matcher required the entire substrate to contain only C/H/Cl/
Br/I. It already inverted specified reacting centers, but lacked the shared exact
postconditions for spectator bonds and distant physical stereo. Consequently,
remote ethers/alcohols were blocked, while some other environments had not been
individually screened.

[sn2_rule.py](../server/sn2_rule.py) supplies a hydroxide/base-specific policy,
not a copy of hydrogenation or oxidation rules:

- Identify the actual single C(sp³)–Cl/Br/I bond, electrophilic carbon and the
  actual OH⁻ oxygen. Existing methyl, primary, selected secondary and benzylic
  net options remain. Ordinary tertiary, ring-bound, allylic and neighboring
  quaternary-carbon/neopentyl-type sites remain excluded.
- Screen remote saturated OH, dialkyl/carbocyclic aryl–alkyl ethers and qualifying
  cyclic ethers. Atoms and bonds are explicitly retained, not simply assumed
  inert because a group is distant.
- OH-to-electrophile paths capable of small intramolecular ether/epoxide closure
  (up to six members) are rejected: external hydroxide versus internal alkoxide
  attack is not resolved. Longer paths are bounded net options; proton equilibria,
  intermolecular ether formation and larger-ring cyclization are not predicted.
- Nearby ether oxygen, acetal/ketal/geminal-O environments, unsaturation, carbonyl
  chemistry, phenols, peroxides and other unvalidated groups fail closed.
- Carbocyclic aromatic skeletons retain bounded compatibility; methoxy-substituted
  benzylic halides now pass the screened aryl–alkyl ether policy. Heteroaromatics
  and non-alkyl halides do not automatically inherit approval.
- Other eligible alkyl-halide sites are separately mapped alternative sites.
  Only one reacts in each net option; further substitution, elimination and
  product-OH cyclization remain potential competing/follow-up chemistry.
- Unsupported additional halide sites and geminal multi-halides are not silently
  treated as harmless spectators. Their messages identify the missing policy.

The original neutral, closed-shell, non-isotopic single-substrate scope, minimum
five-member ring rule and 80-explicit-main-product-atom limit remain. Replacing
one leaving atom with OH adds one main-product atom in the size check.

Only the old SN2 candidate block was replaced. The neighboring SN1/E1/E2
candidate logic and conditions were not widened, and they cannot inherit new
oxygen-containing compatibility automatically.

## 2. Exact substitution and stereochemistry safeguards

For the selected site the declared edits are exactly:

1. Break its mapped C–leaving-group bond.
2. Form C–O using the actual hydroxide oxygen.
3. Change that O from −1 → 0 and the actual leaving atom from 0 → −1.
4. Preserve the hydroxide O–H, every substrate C–H, all unaffected atom identities,
   charges and bonds. Report one neutral alcohol and the actual halide anion.

The pre-existing inversion routine is retained. A new independent postcondition
uses explicit mapped neighbors to verify the replacement and physical inversion,
accounting for neighbor ordering. It does **not** validate a result merely because
R became S. CIP labels are recomputed independently with reaction maps excluded
from priority ranking.

The shared contract accepts only the declared C–X cleavage/C–O formation and
balanced per-atom charge edits. An inversion permission must name those same
center/leaving/incoming maps; it cannot authorize loss or inversion at a distant
center. Untouched tetrahedral and double-bond configurations keep strict retention
checks. Unsigned reacting or remote centers cannot acquire a specified tag.

A center that becomes non-stereogenic is handled conservatively: if specified
information can no longer be represented within this validated policy, the
candidate is rejected with a precise message rather than silently erasing it or
retaining an invalid tag. Directly heteroatom-substituted/geminal electrophiles
that could need different local chemistry are outside the public rule.

These checks run on both the product graph and its mapped serialization. Enhanced/
relative/nonstandard stereo is rejected before ordinary SMILES canonicalization
can discard it, for actual OH⁻ or supported hydroxide-salt inputs.

SN2 is a single concerted backside substitution, not a stable-carbocation
sequence. [OpenStax, the SN2 reaction](https://openstax.org/books/organic-chemistry/pages/11-2-the-sn2-reaction).
Steric and condition limits motivate keeping tertiary/neopentyl exclusions and
not promising efficient secondary substitution.
[OpenStax, SN2 characteristics](https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction).
Base-induced halohydrin cyclization motivates a separate OH compatibility screen;
our broader path-size exclusions are conservative model boundaries, not predictions
that every such molecule must cyclize.
[OpenStax, cyclic ethers and epoxides](https://openstax.org/books/organic-chemistry/pages/18-4-cyclic-ethers-epoxides).

## 3. Newly supported and independently checked examples

| Case | Independently expected product |
| --- | --- |
| 1-Bromo-3-methoxypropane, `COCCCBr` | 3-Methoxypropan-1-ol, `COCCCO` |
| 4-Methoxybenzyl bromide, `COc1ccc(CBr)cc1` | 4-Methoxybenzyl alcohol, `COc1ccc(CO)cc1` |
| Screened remote OH, `OCCCCCCCBr` | `OCCCCCCCO`; original OH connectivity retained |
| Remote ether plus specified center, `CC[C@H](C)COCCCCBr` | `CC[C@H](C)COCCCCO`; original physical configuration retained |
| Multiple eligible sites with a screened ether | Separate one-site products; unselected C–X unchanged |

Longer/branched chains, simple secondary/benzylic substrates, distant specified
centers without added O and multiple hydrocarbon halide sites were already
accepted in parts of the previous engine. They now receive stricter independent
validation; they are not all counted as newly supported.

Additional tests check both reacting-center enantiomers, alternative source atom
orders, simultaneous local inversion and distant retention, unsigned structures
and combinations with remote ether/alcohol groups. A retained distant center can
change R/S because replacing remote Br with OH changes substituent priority; its
physical configuration stays unchanged.

The old priority-change stereo test used `C[C@](Cl)(Br)I`, an unvalidated geminal
trihalide. Its original same-R/S-under-inversion assertion is preserved as an
independent mapped **stereochemistry utility** test with the exact expected
isomeric graph. The public chemistry test additionally rejects this substrate.
It is not reopened merely to make a test pass or presented as a validated product.

## 4. Mechanisms, visualization and reaction amounts

The existing SN2 mechanism remains one concerted step, with:

- Hydroxide lone pair → selected electrophilic carbon.
- Selected C–X electron pair → leaving atom.
- One C–O bond formed and one C–X bond broken, no proton-transfer step and no
  invented stable intermediate or transition-state geometry calculation.

The generated mechanism state now also passes the same SN2 edit/inversion
validator. It must match the selected mapped net product. Incorrect retention
in the mechanism cannot pass merely because the net reaction inverted correctly.
SN1/E1/E2 mechanisms retain their prior implementations.

Public match → diagram → run checks correct products, byproducts, maps, charges,
selected/unselected site bonds, full mechanism endpoints and 2D/3D main-product
correspondence. The incoming OH oxygen/H appear in the main-product atom links;
the released halide remains in the 2D equation, not falsely linked to a main-
product 3D atom. Independent conformer CIP checks cover reacting and distant
specified centers; an unspecified model remains one representative conformer.

One equivalent of active OH⁻ is used per selected site. Existing Calculator
handling is preserved: entered NaOH/KOH use their **full salt molar masses**,
while the spectator cation is explicitly omitted from the ionic net equation.
Tests cover bare OH⁻, full salts, both input orders, limiting reactants, required
amounts and theoretical yields. No actual yield or product distribution is inferred.

## 5. Remaining unsupported structures and explanations

In the fixed audit, remaining positive failures are:

- A158 ring-bound bromocyclohexane: unvalidated backside access/conformation.
- A159 allyl bromide: allylic SN2/SN2′ regioselectivity not enabled.
- A161 remote F: fluoride/halo spectator policy is not validated in this increment.
- A165 methoxide and A166 iodide reagents: new nucleophile families not enabled.

Other exclusions include tertiary/neopentyl-type electrophiles, non-alkyl leaving
groups, additional unvalidated halide sites, near ether oxygen, small OH closure
paths, carbonyl/base competition, unsaturation, heteroaromatics, geminal halides,
phenols, peroxides, unknown groups, electronic/size limits and failed stereo
postconditions. Unsupported means missing validated model coverage, not chemical
impossibility for all reagents and conditions.

Secondary/benzylic, oxygen-spectator and multiple-site options are conservatively
qualified. Hydroxide can also eliminate or deprotonate; this model does not solve
those competitions or predict efficiency, rates, isolated products or laboratory
safety. Missing/incompatible conditions retain the existing assessment states
and explicit reasoning factors. No unrelated pathway was expanded to fill a gap.

No unexpected connectivity, charge, atom-map, stereochemical or preview failure
appeared in the final regression matrix. Deliberate inversion/retention corruption,
lost stereogenicity and invented tags are separately tested and fail closed.

## 6. Same 347-case audit comparison

The pre-change rerun reproduced the Phase 2C baseline. All **347 inputs, independent
expected products, conditions, required sites and score categories are unchanged**.
The original SN2 specified-center cases still require their exact independent
isomeric expectations. New regression subcases do not inflate the denominator.

| Pathway | Before Phase 2D | After Phase 2D |
| --- | --- | --- |
| SN2 | 8/15 — 53.3% | 10/15 — 66.7% |
| Alcohol oxidation | 9/12 — 75.0% | 9/12 — 75.0% |
| Carbonyl hydrogenation | 7/11 — 63.6% | 7/11 — 63.6% |
| Alkene hydrogenation | 11/14 — 78.6% | 11/14 — 78.6% |
| Ester hydrolysis | 9/10 — 90.0% | 9/10 — 90.0% |
| Ester saponification | 10/11 — 90.9% | 10/11 — 90.9% |

Only two statuses change Unsupported → Fully supported:

- **A156:** methoxy-substituted benzyl bromide.
- **A160:** remote ether, 1-bromo-3-methoxypropane.

All **328 rows outside SN2**, including every SN1/E1/E2 row, keep their status;
all other pathway scores remain unchanged. All **38 negative controls** remain
correctly rejected. Across 309 positives, full support is **156 → 158**, partial
stays **16**, and unsupported is **137 → 135**. There are zero incorrect-result
rows and zero preview failures. The rerun exercises **209 site options**, previously
207, through public matching/diagram/run.

The [Phase 2C baseline JSON](reaction-lab-alcohol-phase2c-results.json) is preserved.
[Phase 2D JSON](reaction-lab-sn2-phase2d-results.json) records every observation and
the final audited source hashes. These scores describe the fixed tested matrix,
not universal chemistry coverage or experimental success probabilities.

## 7. Tests and build

**All 732 tests pass: 316 Python + 416 JavaScript.** Added **32 Python tests and
14 JavaScript tests** above the previous 686, with many independent positive/
negative structural subcases. No tests were deleted or product/conservation
assertions weakened. The one legacy geminal-trihalide test was corrected as
described above; its CIP-versus-physical-inversion check remains enforced.

Checks cover independent products, charges/H counts, all three existing leaving
groups, source maps, reverse inputs, bare/full-salt reagent masses, multiple sites,
local inversion/distant retention, priority changes, lost stereogenicity, unsigned
centers, enhanced-stereo rejection, competing groups, scope/size/condition limits,
corrupted bonds/charges/maps/stereo, invalid permissions, injected failures and
mechanism-versus-net agreement. Real authenticated HTTP match/diagram/run routes
and actual browser-local calculation arithmetic are exercised. Prior phases,
SN1/E1/E2, frontend, Calculator, cross-page and deployment regressions remain passing.

TypeScript and production build pass; `git diff --check` passes. Existing dependency
`use client` and large-builder-chunk warnings remain. No HTML, CSS or frontend
TypeScript was edited in this increment.

### Browser verification

The actual Builder paste/check/preview → Use as molecule 1 → Reaction Lab
workflow was verified with `CC[C@H](C)COCCC[C@@H](Br)C`, containing a remote
ether, a distant specified center and a specified reacting center. Hydroxide
with the existing polar-aprotic setting matched one bounded SN2 option.

- Net equation: `C10H21BrO + OH− → C10H22O2 + Br−`.
- Advanced information independently labels mapped atom 10 **S → R** and
  distant atom 3 **S → S**; no assumption that all inversion swaps CIP letters.
- Compare selects the same carbon 10 in both mapped 2D structures and labels
  it in the rendered main-product 3D model.
- Mapped mechanism shows one concerted step, nucleophile 34, carbon 10 and
  leaving atom 12: electron pair `34 → 10` and bond pair `10–12 → 12`, with
  `10–34` forming and `10–12` breaking. Both movements highlight together.
- No warning/error console entries were captured during this local check.

Saved evidence: [linked atoms](reaction-lab-sn2-phase2d-linked-atoms.png),
[mapped stereochemistry](reaction-lab-sn2-phase2d-stereo-information.png) and
[concerted mechanism](reaction-lab-sn2-phase2d-mechanism.png). The temporary
verification tab was closed; the local preview remains running. This did not
change the page layout or claim experimental selectivity.

## 8. Recommended next pathway — not implemented

Consider the existing **E2** pathway next, in one controlled increment: its own
base/functional-group policy, mapped beta-H selection, unaffected stereochemistry,
and explicit limitations for anti-periplanar geometry and E/Z outcomes. It must
not simply inherit SN2's whitelist or a generic stereo-loss exemption.

This recommendation is not implemented. Work stops after Phase 2D.
