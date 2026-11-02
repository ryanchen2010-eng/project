# Reaction Lab — Phase 2F: site-compatible water SN1

Completed locally on October 13, 2026. Only the existing **SN1** pathway adopts
this policy. No new reaction family, nucleophile/leaving-group family, page layout,
Calculator or visible example changes. SN2/E2/E1 and earlier phases retain their
own policies. Nothing was pushed, published or deployed; Phase 2G was not begun.

## 1. Implementation and newly supported structures

[sn1_rule.py](../server/sn1_rule.py) supplies a water/carbocation-specific policy
to the existing shared compatibility architecture. It identifies the actual
saturated C–Cl/Br/I bond, classifies the formal cation, screens spectators and
declares exact mapped net/elementary edits. It does not inherit the more permissive
base-driven SN2/E2 oxygen policies. Every product passes matching and validation
before being offered through the public Reaction Lab workflow.

- Longer/branched tertiary chains, existing primary/secondary/tertiary benzylic
  sites, distant ordinary OH/ethers, specified distant/local stereocenters and
  separated multiple C–X sites can work where the individual policy passes.
- Remote saturated primary/secondary alcohols and ordinary dialkyl/aryl–alkyl
  ethers receive **bounded** retention, not an unconditional inertness claim.
  Direct/vicinal oxygen, potential 4–6-membered oxygen-to-cation capture paths,
  tertiary/benzyl/allyl acid-sensitive oxygen groups and acetal/ketal environments
  are excluded. Larger-ring/intermolecular capture and acid accumulation remain
  unpredicted, even for accepted net structures.
- Another separated eligible halide is an alternative reaction site, not an inert
  group or a prediction of selective mono-conversion. A separated ordinary primary
  halide may remain in a net product but does **not** gain SN1 ionization permission.
- A narrow allylic increment accepts CH2–X/CH2 **terminal-equivalent** allyl systems,
  including a saturated alkyl substituent at the central sp² carbon. Equivalent
  resonance termini give the same product constitution. A single localized formal
  contributor/mapped attack path is drawn; charge density, atom-path proportions,
  SN1 versus SN2 dominance and general allylic regioselectivity are not predicted.
- Ordinary secondary aliphatic substrates were investigated but not enabled.
  Ordinary methyl/primary carbocations and general unequal allylic systems remain
  unsupported; unsupported is not a claim of chemical impossibility.

Representative independently tested structures (not added to curated examples):

| Substrate | Independently checked net product |
| --- | --- |
| `CCCCCC(Br)(C)CC` | `CCCCCC(O)(C)CC`; longer tertiary chain |
| `CC(C)CCC(Cl)(C)C` | `CC(C)CCC(O)(C)C`; screened branching |
| `C[C@H](Br)c1ccccc1` / corresponding `@@` | `CC(O)c1ccccc1`; original reacting configuration lost, product unassigned |
| `COCCCCCCC(Br)(C)C` | `COCCCCCCC(O)(C)C`; distant ordinary ether |
| `OCCCCCCC(Br)(C)C` | `OCCCCCCC(O)(C)C`; distant primary OH |
| `CC[C@H](C)CCC(Br)(C)C` | `CC[C@H](C)CCC(O)(C)C`; distant physical configuration retained |
| `CCC[C@H](CCCCl)CCC(Br)(C)C` | `CCC[C@H](CCCCl)CCC(O)(C)C`; physical retention but independently reassigned remote CIP R → S |
| `CC(Br)(C)CCCC(Cl)(C)CC` | Two selectable one-site alcohol structures; other C–X retained |
| `C=CCBr`, `C=C(C)CCl`, `C=C(CC)CI` | Allyl alcohol and central-alkyl variants; narrow equivalent-terminal model only |

All existing Cl/Br/I families, reverse inputs and independent source map labels
are checked. No alternate trapping solvent or nucleophile was added. Methanol
gets an explicit water-model limitation rather than an empty explanation.

## 2. Carbocation, net equation and mechanism verification

Net reporting remains **R–X + H2O → R–OH + HX** with four exact edits:
break C–X and original water O–H; form C–O and X–H. Neutral net charges and every
unchanged atom/bond are conserved. HX is an **acid-equivalent reporting form**,
not a claim of undissociated hydrogen halide in aqueous solution.

The existing three-step mechanism is preserved and each step now passes its own
exact edit/charge/stereo contract:

1. **Ionization:** C–X electrons go to X. C becomes +1, degree 3/sp² and unassigned;
   X becomes −1. No C–O bond is formed yet.
2. **Water capture:** the actual water oxygen donates to C. C returns to neutral;
   O becomes +1 oxonium. No face-specific product configuration is assigned.
3. **Deprotonation:** distinct actual solvent water accepts the original water
   proton; O–H electrons remain on the alcohol O. Alcohol becomes neutral,
   hydronium becomes +1 and X remains −1.

Each elementary state preserves all mapped atoms and total charge; source bonds
must exist, electron endpoints must be present and no distant edits are authorized.
The final main fragment must equal the chosen net main product. The additional
solvent water accounts for the explicit hydrated acid representation; it is not
silently charged as a second net stoichiometric input to the existing calculator.
The calculator uses one net water equivalent and theoretical arithmetic, with a
note that this is not a solvent quantity or experimental conversion prescription.
The three-step/planar-ion-pair framework follows
[OpenStax 11.4](https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction).

## 3. Stereochemistry and visualization

A separate shared **solvolysis-stage** permission allows loss only at the exact
reacting carbon, with the corresponding elementary bond and charge edits. It
cannot erase distant stereo or permit unrelated bonds to change. Specified
reacting configuration is cleared at ionization, not retained on a carbocation or
reintroduced during capture. Products with unspecified or absent stereogenicity
receive no invented R/S tag; no exact 50:50 racemization ratio is asserted.

Distant tetrahedral configurations are compared by mapped physical parity and
neighbors, not matching R/S letters. CIP is independently reassigned through
serialization. The remote-Cl test above deliberately changes R → S while retaining
physical configuration; changing physical parity, losing that tag, inventing local
tags, changing charge/maps or modifying spectator bonds fails validation.
Enhanced/relative/non-tetrahedral stereo is rejected before canonicalization can
silently discard it.

Public match → diagram → run and authenticated production HTTP routes are tested.
Net 2D/3D correspondences use exact map IDs: reacting C and incoming O are linked;
departed halogen and transferred proton are not falsely attached to a main-product
3D atom. Specified distant 3D configurations are checked against independently
computed CIP labels. One conformer at an unsigned product center is a representative
shape, not an assigned configuration or enantiomeric mixture.

The existing all-H net 2D depiction still explicitly omits stereochemical drawing
annotations; mapped stereochemistry is available in Reaction information and
applicable specified configurations in the 3D model. Dense large 2D net structures
can remain cramped at narrow compare widths. No diagram layout redesign was made.
Charged intermediate structures remain 2D, with atom-linked highlights only for
atoms retained in the final 3D main product.

## 4. Remaining exclusions and chemistry risks

- Ordinary methyl/primary and secondary aliphatic ionization; unequal/substituted
  allylic regioisomers, propargylic, aryl/vinyl halides and alkyl fluoride.
- Ring-bound/bridgehead cations and adjacent cyclic ring-expansion possibilities;
  adjacent branched/quaternary carbons with competing shifts and neighboring
  potential benzylic-cation rearrangements. No rearranged products are generated.
- Small intramolecular oxygen capture, acid-sensitive oxygen groups, coupled
  nearby halides, unscreened unsaturation, carbonyls/acids/esters/peroxides,
  heteroaromatics, other unvalidated elements/groups and charged/radical/isotopic
  or disconnected substrates.
- Existing 80-explicit-atom main-product, ring-strain and unsupported-stereo limits.
- Alcohol trapping solvents and other nucleophiles. Conditions remain qualitative:
  missing inputs are incomplete, mismatches are unfavorable alternatives, not an
  experimental claim that SN1 is impossible or a validated solvent/pH protocol.

Water solvolysis can compete with E1/SN2, ion-pair/facial effects, rearrangements,
capture and further conversion. Accepted options are bounded net transformations,
not selective product predictions; rates, yields and distributions are not computed.
An absent E1 option is not proof that E1 cannot occur. E1 was not expanded.
Resonance/solvent boundaries use
[OpenStax 11.5](https://openstax.org/books/organic-chemistry/pages/11-5-characteristics-of-the-sn1-reaction),
shift screening uses
[OpenStax 7.11](https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements),
and acid-sensitive ether exclusions are bounded by
[OpenStax 18.3](https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage).
These references support mechanism principles, not every substrate-specific
experimental outcome or an unconditional spectator assumption.

## 5. Fixed 347-case audit comparison

The original input/expected/conditions/minimum-sites/coproduct/variant fields for
all 347 cases are unchanged. The script only adds the new module to its source-hash
inventory. Results are saved separately in
[phase2f-results.json](reaction-lab-sn1-phase2f-results.json).

| Measure | Phase 2E baseline | Phase 2F |
| --- | --- | --- |
| SN1 fully supported applicable cases | 4/11 (36.4%) | **5/11 (45.5%)** |
| SN1 unsupported applicable cases | 7 | 6 |
| SN1 negative control | 1 correctly rejected | 1 correctly rejected |
| Overall fully supported cases | 161 | 162 |
| Overall unsupported / partial | 132 / 16 | 131 / 16 |
| All negative controls | 38 correctly rejected | 38 correctly rejected |
| Public site options across benchmark | 215 | 216 |

Only **A179**, the specified benzylic center, improves its score. All **335
non-SN1 case statuses** remain unchanged. No audit-flagged incorrect result or
failed preview appears. New distant-oxygen/stereo/allyl examples outside the fixed
matrix improve practical scope, not the benchmark denominator.

Six applicable SN1 cases remain outside scope: A175 ring-bound tertiary; A176
unequal allylic tertiary; A177 nearby ether with a potential **5-membered oxygen
capture path**; A178 unvalidated remote F; A181 methanol trapping; A182 ordinary
secondary aliphatic. Calling A177 “remote ether” in the benchmark does not make it
a validated inert spectator, so its expectation was not used to weaken the policy.
The pre-existing reversed-stereo expected literal for **E2 A190**, documented in
Phase 2E, remains a separate benchmark limitation; no SN1 benchmark defect or
benchmark expectation was changed in this phase.

## 6. Regression checks and browser evidence

**847 tests pass: 395 Python + 452 JavaScript.** This adds 43 independent Python
SN1 tests and 10 browser-arithmetic integration tests to the previous 794. Two
old assertions were updated, without deleting tests: simple `C=CCBr` is now a
validated narrow allyl positive (the old negative is replaced by unequal
`C=CC(Br)C`); SN1 capability metadata now reports validated distant retention and
an unassigned reacting center. Existing SN2/E2/E1 and earlier-phase tests all pass.

Checks cover independent products/formulas/masses; exact maps and unchanged bonds;
charge/proton balances; all three elementary states; input reversal; local/distant
stereo and CIP changes; multiple sites; hidden competition; malformed inputs;
injected net/stage failures; authenticated public endpoints; real required amounts,
limiting reactant and theoretical-yield arithmetic.

- Python full suite: **395/395**, including invalid-control parser diagnostics.
- JavaScript full suite: **452/452**; no skipped/cancelled tests.
- TypeScript: **pass**. Vite production build: **pass**, all five pages packaged.
- Existing dependency `use client`/large-chunk warnings remain; not build failures.
- Whitespace check: **pass**. No source/curated-example/layout/Calculator expansion
  outside the stated SN1 increment.

Browser verified a Builder-imported remote ether with two specified centers:
`CC[C@H](C)COCCCCCC[C@H](Br)c1ccccc1`. The public workflow offers SN1, maps C13/X14/
water O50/H51/solvent O53, produces C18H30O2, reports reacting **13 S → unassigned**
and distant **3 S → S**, and links exact product carbon 13 in both views. All three
mechanism buttons show the appropriate intermediate, bond edits and proton transfer.
No warning/error console entries were recorded. Temporary verification tabs closed;
local preview restarted with final code.

Evidence: [linked product](reaction-lab-sn1-phase2f-linked.png),
[stereochemistry](reaction-lab-sn1-phase2f-stereo.png),
[mechanism](reaction-lab-sn1-phase2f-mechanism.png),
[final existing-example preview](reaction-lab-sn1-phase2f-final-preview.png).
After the final backend restart, the original tert-butyl chloride + water example
still offers SN1 and unchanged E1, produces tert-butanol through SN1, links exact
carbon 2 in 2D/3D and records no browser warning/error entries.

## 7. Recommended next increment — not implemented

Adapt **existing E1** next with a separately validated carbocation/spectator policy,
explicit beta-H options, configuration loss, rearrangement screening and bounded
alkene geometry. SN1's net substitution permissions must not automatically grant
E1 product selectivity or stereo. Await a separate request before Phase 2G.
