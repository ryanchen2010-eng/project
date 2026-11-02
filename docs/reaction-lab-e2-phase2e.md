# Reaction Lab — Phase 2E: site-compatible hydroxide E2

Completed locally on October 13, 2026. Only the existing **E2** pathway adopts
this policy. No new family, base, leaving-group family, visible example, frontend,
page layout or Calculator change. SN1/SN2/E1 and Phases 1–2D remain independently
bounded. Nothing was pushed, published or deployed. No subsequent phase began.

## 1. Implementation and newly supported structures

[e2_rule.py](../server/e2_rule.py) identifies the actual alpha C–Cl/Br/I bond,
eligible saturated beta carbons and their actual hydrogens. Its own compatibility
policy replaces the previous E2 whole-molecule hydrocarbon/unsigned-stereo gates;
it does not copy or widen the SN2 spectator policy.

- Existing primary/secondary/tertiary, long/branched chains and bounded benzylic
  net options remain. A tertiary electrophile can eliminate when beta H exists;
  this does not make it SN2-compatible or imply experimental efficiency.
- Screened remote saturated alcohols and remote dialkyl/carbocyclic aryl–alkyl
  ethers can remain unchanged. Small intramolecular OH ring-closure paths,
  neighboring oxygen, beta heteroatoms, acetal/geminal-O and unclassified groups
  fail with specific reasons. Distance is not treated as proof of inertness.
- Other separated alkyl halides remain exact alternative sites. Every candidate
  transforms one alpha/beta position, retaining the other C–X bonds. Different
  constitutional products are selectable; symmetry-equivalent beta positions
  at one halide do not create duplicate constitutional options.
  Source atom-map labels are removed from symmetry ranking, but retained as
  provenance and exact reaction identities; renumbering cannot split an equivalent site.
- Distant specified centers are checked by mapped physical parity and original
  neighbor bonds. R/S is reassigned independently, not assumed unchanged.
- Carbon-bound hydrogen availability, saturated alpha/beta environments, rings,
  supported electronic states, atom counts and other groups are checked before
  any product can enter the public matching workflow.

Representative independently checked new cases:

| Substrate | Net products/options |
| --- | --- |
| `COCCC(Br)(C)C` | `COCC=C(C)C` and `C=C(C)CCOC`; remote ether retained |
| `COCCCBr` | `COCC=C`; screened remote ether |
| `OCCCCCCCBr` | `C=CCCCCCO`; screened remote OH, with proton/cyclization caveats |
| `CC[C@H](C)CCC(Br)(C)C` | Two constitutional alkenes; distant physical configuration retained |
| `CC[C@H](Br)CCC` | Hex-2-ene/hex-3-ene connectivity; reacting center planar, E/Z unassigned |
| `C[C@H](Br)[C@H](C)CC` | Terminal constitutional option plus a bounded Z internal-alkene option |
| `C[C@H](Br)[C@@H](C)CC` | Terminal constitutional option plus the complementary E internal-alkene option |

Other tests cover multiple halides, both local enantiomers, combined remote ether/
distant-center/local-stereo cases, all existing Cl/Br/I leaving groups, bare OH−,
full NaOH/KOH input masses, reverse inputs and source-map provenance. Test
structures are separate from the unchanged 20 curated examples.

## 2. Exact net edits, atom mapping and mechanism

Each selected option declares exactly four mapped bond edits:

1. C-alpha–X single bond breaks.
2. Selected C-beta–H single bond breaks.
3. C-alpha–C-beta changes single → double.
4. The actual hydroxide oxygen bonds to the transferred beta H.

That oxygen changes −1 → 0; the actual leaving atom changes 0 → −1. The product
is a neutral alkene-containing structure plus **water and halide anion**, not
HX or an invented carbocation. Original hydroxide O–H, all other atoms, element/
isotope/radical identities, charges, hydrogen maps and unaffected bonds are checked.
Main-product scope remains at most 80 explicit atoms; E2 removes two substrate
atoms from that main product. Product serialization must preserve the contract.

The mechanism remains **one concerted step**, with no stable intermediate:
base lone pair → beta H; beta C–H electron pair → C-beta/C-alpha; C-alpha–X
electron pair → X. The mechanism state now passes the same E2 edit/stereo validator
as the net product, and must agree with the selected mapped net structure.
This model follows the concerted anti-elimination framework, not kinetics or a
transition-state calculation. [OpenStax 11.8](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect).

The public match → diagram → run pipeline is exercised for each positive fixture.
The beta H remains mapped in water and X in the halide; neither is falsely linked
to a main-product 3D atom. Alpha/beta carbons and spectators remain exactly linked.
Real authenticated production HTTP routes and existing browser-local reaction
arithmetic are tested. One OH− equivalent per selected site is used. Full NaOH/KOH
molar masses remain full salts, with the cation omission explicitly noted in the
ionic equation; theoretical yield is not an experimental yield.

## 3. Stereochemistry and geometry safeguards

The shared validator has a separate E2 permission, requiring these same four
bond edits, actual hydroxide proton acceptance and balanced per-atom charge edits.
It permits only the actual alpha/beta tetrahedra to become planar sp² carbons
with their proper lost H/X neighbors. It cannot discard distant configurations,
authorize arbitrary bond changes or retain invalid tetrahedral tags on sp² carbon.
SN2 inversion and alcohol-oxidation consumption retain their separate contracts.

A new, bounded local utility constructs ideal anti H–C-beta–C-alpha–X geometry
from the mapped physical parities of **two specified local tetrahedral centers
with one beta H**. Its two remaining substituent references determine physical
same/opposite sides; CIP E/Z is then assigned by the library independently of
reaction map numbering. The product and its serialized SMILES are checked against
that local relationship. Incorrect, lost or invented alkene stereo fails closed.
Unspecified/incompletely specified local centers and CH2/CH3 beta sites do not
receive an E/Z prediction. A representative actual H map is used in the net edit;
the other H maps are listed, not claimed stereochemically equivalent or assigned
populations. All actual beta-H torsions remain inspectable with the existing utility.

An independent utility-level reference checks meso (R,S) dibromodiphenylethane → E
and (R,R)/(S,S) → Z against the textbook anti example. That reference does **not**
enable public vicinal-dibromide chemistry; its competing environment is rejected.
Additional strict isomeric product and independent 3D CIP/E/Z tests check ordinary
supported acyclic structures, both enantiomers and distant-center retention.

The geometry utility separately measures a supplied conformer and constructs an
anti candidate by rotating the selected acyclic C–C bond, independently checking
retention of specified 3D configurations. Default matching samples one bounded
ETKDG substrate conformer, then attempts that rotation. A sampled non-anti
conformer is **not** a reaction rejection. Failure is explicitly `unresolved`.
The candidate is **kinematic only**: no relaxed energy, clash-free accessibility,
transition state, conformer population, rate or experimental preference is claimed.
The implementation uses the documented torsion measurement/rotation operations.
[RDKit rdMolTransforms](https://www.rdkit.org/docs/source/rdkit.Chem.rdMolTransforms.html).

Alpha/beta ring-bound elimination remains rejected, including exocyclic ring
outcomes. It needs separate constrained geometry, such as trans-diaxial checks,
and cannot receive the acyclic rotation permission.
[OpenStax 11.9](https://openstax.org/books/organic-chemistry/pages/11-9-the-e2-reaction-and-cyclohexane-conformation).

## 4. Remaining unsupported cases and chemistry concerns

Four positive benchmark cases remain unsupported:

- **A186:** ring-bound tertiary halide: ring-specific conformations unvalidated.
- **A204:** cyclic secondary halide: cyclic E2 geometry unvalidated.
- **A189:** remote F: unvalidated element/spectator policy, not a new leaving group.
- **A206:** potassium tert-butoxide: an additional base family outside this phase.

**A187** benzylic secondary and **A203** secondary internal sites remain partial
because their unsigned local structures do not determine assigned E/Z outcomes.
Other exclusions include methyl/no-beta-H/neopentyl controls, allylic/propargylic,
existing unsaturation, geminal/vicinal halides, beta heteroatoms, neighboring
oxygen, small OH cyclization paths, acids/carbonyls/esters, phenols/peroxides,
heteroaromatics, unknown groups and unsupported electronic/stereo/size states.
An unsupported structure is not described as chemically incapable of elimination.

Substitution, OH deprotonation/internal alkoxide attack, further elimination and
selective mono-conversion are not resolved. Existing condition profiles remain
qualitative; even aligned conditions do not claim rates, ratios, actual yields,
laboratory safety or efficient primary/secondary E2. No other pathway is widened
to fill an E2 rejection. No unexpected net chemistry/preview failure appeared.

## 5. Same 347-case audit comparison

The fresh pre-change audit reproduced Phase 2D. All 347 input structures, expected
products, conditions, minimum-site requirements and score categories remain fixed.

| Pathway | Before Phase 2E | After Phase 2E |
| --- | --- | --- |
| E2 | 4/13 — 30.8% | 7/13 — 53.8% |
| SN2 | 10/15 — 66.7% | 10/15 — 66.7% |
| Alcohol oxidation | 9/12 — 75.0% | 9/12 — 75.0% |
| Carbonyl hydrogenation | 7/11 — 63.6% | 7/11 — 63.6% |
| Alkene hydrogenation | 11/14 — 78.6% | 11/14 — 78.6% |
| Ester hydrolysis | 9/10 — 90.0% | 9/10 — 90.0% |
| Ester saponification | 10/11 — 90.9% | 10/11 — 90.9% |

Only **A188 remote ether, A190 remote stereocenter and A205 specified secondary
center** change Unsupported → Fully supported. All **333 non-E2 rows**, including
all SN1/SN2/E1 rows, keep their status. All **38 negative controls** remain correct.
Across 309 positives: full **158 → 161**, partial **16 → 16**, unsupported
**135 → 132**. There are zero audit-flagged incorrect results and zero failed
previews; public site options **209 → 215**. The separate
[Phase 2E JSON](reaction-lab-e2-phase2e-results.json) includes all observations and
audited source hashes. The Phase 2D baseline and original audit matrix are preserved.

### Benchmark stereochemical caveat found during independent checks

The existing audit's E2 expected-product comparison is connectivity-based; it is
not a strict isomeric/physical-configuration test. A190's second expected literal
`C=C(C)CC[C@H](C)CC` uses the wrong tetrahedral traversal parity for retention.
The physically retained reversed-chain representation is
`C=C(C)CC[C@@H](C)CC`, equivalently the forward-order `CC[C@H](C)CCC(C)=C`.
The fixed 347-case matrix was **not edited** to improve the score. New independent
tests use the physically retained expected structure and exact mapped parity;
they would reject the benchmark's flipped literal. Thus 7/13 is the unchanged
benchmark score, not a claim that it alone verifies all E2 stereochemistry.

## 6. Regression tests, build and browser

**All 794 tests pass: 352 Python + 442 JavaScript.** Added **36 Python tests and
26 JavaScript tests**, with many independent positive/negative structural subcases,
above the previous 732. All prior tests remain present. Three old assertions were
updated specifically for the requested E2 expansion: filter the SN2 inversion
test to SN2 without weakening its expected product; keep SN1/E1 exclusion and
require E2's own policy instead of asserting it is unimplemented; update the E2
capability label. No conservation, product or inversion assertions were removed.

Tests cover structures beyond examples; exact products/coproducts/H/charge/maps;
all existing leaving groups; β-position symmetry and multiple sites; untouched
bonds; reacting-center planarity; remote parity and CIP; strict local E/Z and 3D
stereo; injected bad edits/permissions/stereo/mechanisms; real HTTP routes; supplied
gauche-to-anti rotation, all beta H, ring exclusion, explicit unresolved geometry
and immutable cached payloads; salts/input orders/calculator arithmetic; and
previous phase, frontend, cross-page, Calculator and deployment regressions.

TypeScript and production build pass. `git diff --check` passes. Existing dependency
`use client` and large-builder-chunk warnings remain. No HTML/CSS/frontend code or
curated sample data was edited in this increment.

The actual Builder import/check/preview → Use as molecule 1 → Reaction Lab workflow
was verified with `CC[C@H](C)COCCC[C@H](Br)[C@H](C)CC`. The existing hydroxide,
ethanolic-medium and heated selectors expose two E2 sites beside the unchanged
SN2 option. Selected site **10,11,12** gives `C13H26O + H2O + Br−` from
`C13H27BrO + OH−`. Advanced information shows distant atom **3 S → S** and new
**C=C 10–12 Z** from local source **10 S / 12 R**. Keyboard selection of beta carbon
12 links both 2D structures and the 3D model. A mouse click on the crowded large-
structure SVG hit a nearby atom; exact keyboard targeting worked. This existing
dense-view mouse-targeting limitation was not redesigned in this chemistry phase.

Mapped mechanism shows one concerted step: base **43 → H34**,
**C12–H34 → C12–C10**, and **C10–Br11 → Br11**. All three moves highlight together.
No warning/error console entries were captured. Saved [stereo information](reaction-lab-e2-phase2e-stereo-information.png),
[linked atoms](reaction-lab-e2-phase2e-linked-atoms.png) and
[mechanism](reaction-lab-e2-phase2e-mechanism.png). Temporary verification tab
closed; the local preview was restarted to load the final symmetry correction.
After restart, the existing 2-bromopropane → propene option was rechecked through
the browser, with one symmetry-distinct E2 site, water/Br−, linked carbon 2 and no
console warning/error entries. [Final-server preview](reaction-lab-e2-phase2e-final-preview.png).
No hosting, publication or external molecule lookup was needed.

## 7. Recommended next pathway — not implemented

Consider existing **SN1** in a separate controlled increment: its own carbocation
stability/rearrangement and spectator compatibility checks, preservation of
distant configurations, and explicit limits on reacting-center stereochemistry.
Do not reuse E2's whitelist or assign a racemization ratio without a validated model.

This is a recommendation only. Work stops after Phase 2E.
