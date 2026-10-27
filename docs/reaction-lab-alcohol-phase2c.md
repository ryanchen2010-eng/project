# Reaction Lab — Phase 2C: site-compatible alcohol oxidation

Completed locally on October 13, 2026. Only the existing alcohol oxidation
pathway adopts an oxidation-specific compatibility policy. No new reaction
family, reagent system, website layout or Calculator was added or changed.
Phase 2D has not started; no GitHub push, publication or deployment occurred.

## 1. What changed

The old C/H/O-wide matcher already accepted many longer, branched, cyclic,
ether-containing and multi-alcohol structures, but rejected specified centers
anywhere in the substrate. It did not independently screen all extra oxygen
groups for competing chemistry. This increment replaces that blanket handling
with [alcohol_oxidation_rule.py](../server/alcohol_oxidation_rule.py), a separate
consumer of the shared Phase 2 compatibility architecture.

- The actual saturated, neutral C–OH site is classified as primary (including
  methyl alcohol), secondary or tertiary. A carbon-bound H is required for the
  selected oxidation. Tertiary OH is never an ordinary carbonyl-forming site.
- Primary alcohol reports its **first-stage aldehyde**; secondary alcohol reports
  its ketone. Further primary oxidation is not folded into this rule. The existing
  separate aldehyde-to-acid pathway and its restrictions remain unchanged.
- Screened remote dialkyl/aryl–alkyl and cyclic ethers retain their C–O bonds.
  Other separated eligible OH groups are explicitly **alternative oxidation
  sites**, not automatically inert or selectively protected. A separate tertiary
  OH can remain in a bounded net edit but does not become an oxidation candidate.
- Competing unsaturation, existing aldehydes/carbonyls, vicinal polyols, potential
  five-/six-membered hydroxy-carbonyl cyclization, unknown oxygen environments
  and other unvalidated functional groups fail closed with specific reasons.
- Carbocyclic aromatic skeletons retain the previous bounded net option, with
  an explicit warning that chlorination and condition-specific side reactions
  are not experimentally excluded. Heteroaromatics are not generally opted in.
- Distant specified configurations are retained and checked physically by atom
  mapping, not by merely copying R/S letters. CIP priorities are recomputed.
  Adjacent specified centers with possible alpha-carbonyl epimerization remain
  outside distant-center retention.
- A specified **reactive secondary-alcohol center** legitimately loses its
  tetrahedral configuration when the selected carbon becomes planar C=O. Only
  that mapped center receives a checked stereo-loss permission; remote centers
  and all other pathways keep strict no-loss defaults. Unspecified centers are
  never assigned a configuration.

## 2. Exact redox and stereo validation

The existing supported alkali-metal hypochlorite graph is retained, including
its actual Li/Na/K/Rb/Cs counterion. Neither names/formulas nor a claimed CID
substitute for a different reagent. No TEMPO, additional oxidant or new catalyst
is implemented; the existing model remains a **balanced net stage**, not a
validated laboratory protocol.

The declared mapped edits are exactly:

1. Selected C–O order 1 → 2.
2. Remove one C–H and the selected O–H, retaining the original alcohol oxygen
   in the carbonyl and the original carbon skeleton.
3. Remove the oxidant O–Cl bond.
4. Attach those two removed hydrogens to the original oxidant oxygen, making
   water. Oxidant O changes −1 → 0 and Cl changes 0 → −1.
5. Keep the actual counterion unchanged; report its chloride salt separately
   from water and the main carbonyl product.

The shared edit contract now accepts only explicitly declared, initially verified,
balanced per-atom charge edits. No switch disables charge conservation. Every
other atom identity, isotope, radical state, individual charge and bond must
remain exact. Product sanitization, valence, conservation, connected components
and serialized mapped structures are all checked.

Authorized reactive-center stereo loss additionally requires the declared C–O
bond edit, one actual mapped H loss, the original C/O neighbors, an explicit
four-neighbor specified sp³ alcohol center before, and a three-neighbor unassigned
sp² carbonyl afterward. An untouched center cannot inherit that permission.
Unexpected retained/inverted/erased/invented tags fail validation. The same checks
run through serialization. Existing hydrogenation and ester consumers do not
request charge or tetrahedral-loss permissions and retain their strict behavior.

Public match → diagram → run uses this same transformation and validator.
Compatibility metadata includes site maps, group dispositions, exact bond changes,
per-atom charge changes and any consumed reactive-center map. Existing information
and reasoning panels explain the model without changing layout or controls.

## 3. Newly supported and checked structures

| Newly supported case | Independently expected product |
| --- | --- |
| Distant specified center, `CC[C@H](C)CCO` | `CC[C@H](C)CC=O` |
| Opposite distant enantiomer | Opposite aldehyde configuration retained |
| Remote center plus ether, `CC[C@H](C)COCCCCO` | `CC[C@H](C)COCCCC=O` |
| Secondary alcohol with a remote center, `CC[C@H](C)CCCC(O)C` | `CC[C@H](C)CCCC(=O)C` |
| Either specified 2-butanol enantiomer, `C[C@H](O)CC` / `C[C@@H](O)CC` | The same unassigned planar butan-2-one, `CC(=O)CC` |
| Specified reactive plus distant center, `CC[C@H](C)CCCC[C@@H](O)C` | `CC[C@H](C)CCCCC(=O)C`; only the reactive center disappears |
| Multi-alcohol with two specified centers, `CC[C@H](C)C[C@@H](O)CCCCCCO` | Two independently selectable net products; the unselected OH/configuration remains checked |

Simple, longer and branched primary alcohols, secondary alcohols, cyclic alcohols,
remote ethers and separated polyols were not all previously unsupported. They
now receive independent multi-structure tests and explicit site/group screening.
Examples include methanol, ethanol, dodecan-1-ol, branched primary/secondary
alcohols, cyclopentanol/cycloheptanol, 3-methoxypropan-1-ol and 1,3-propanediol.
Symmetry-equivalent sites remain separately selectable by their actual atom maps.

An independent priority-changing example switches a retained center's CIP label
S → R (or R → S) during oxidation without physical inversion. Tests distinguish
that from illegitimate tag changes. A 3D preview is one representative conformer,
not a new assigned stereochemical outcome.

## 4. Chemistry boundaries and explanations

Primary alcohols may oxidize beyond aldehydes, while secondary alcohols form
ketones and ordinary tertiary alcohol oxidation lacks the needed C–H.
[OpenStax, oxidation of alcohols](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols).
Published hypochlorite systems use specific catalysts/conditions and document
overoxidation, unsaturation side reactions, diol selectivity and lactone outcomes.
These support conservative boundaries, **not** unrestricted approval under the
UI's aqueous-medium choice. [Organic Syntheses, condition-specific alcohol oxidation](https://www.orgsyn.org/demo.aspx?prep=CV8P0367).
Recent work also reports substrate-dependent failures and strained-ring side
products under its particular TEMPO/NaOCl system.
[Naik et al., continuous-flow oxidation study](https://doi.org/10.1021/acs.oprd.3c00237).

Our graph-based cyclization, vicinal-polyol and spectator screens are conservative
software/chemoselectivity limits, not assertions that those substances cannot
be oxidized. Particular experimentally validated catalysts can support cases
outside this model; they were not added here.

Still unsupported:

- Remote halogens, amines/sulfur groups, heteroaromatics and unvalidated spectators.
- Additional C=C/C≡C, aldehydes, ketones, acids, esters, amides, phenols, peroxides
  and other competing/unvalidated environments.
- Vicinal/geminal OH, hemiacetals/geminal diols, possible five-/six-membered
  hydroxy-carbonyl closure/lactonization, acetals/ketals, benzyl/allyl and diaryl
  ether spectators requiring their own oxidant-specific validation.
- Near-site specified centers (other than the actual oxidized alcohol carbon),
  enhanced/relative/non-tetrahedral or ambiguous stereo and failed preservation.
- Invalid, disconnected, charged/radical/isotopic/query substrates, strained
  rings below five members and main products over 80 explicit atoms. The size
  check correctly counts the two H transferred out of the main product.
- New oxidants, new elementary mechanisms, pH-dependent speciation, selective
  mono-oxidation, practical yields, rates, stereochemical ratios or laboratory
  safety/procedure claims.

Missing/incompatible medium selections use the existing condition-assessment
states and individual reasoning factors. Choosing further oxidation for a primary
alcohol explains that an aldehyde first-stage input is required; it does not
invent a direct alcohol-to-acid product. Structural/size/stereo/competition failures
provide specific messages rather than a generic claim of chemical impossibility.

All oxidation options are conservatively labeled **Possible**: a validated net
graph is not proof that the chosen medium guarantees an experimental endpoint.
Safety warnings remain, including “Do not mix household chemicals.” Some formerly
unscreened multifunctional matches are intentionally rejected by the new policy;
no unrelated pathway restrictions were removed.

No unexpected product connectivity, charge, mapping or preview failure appeared
in the final tests/audit. Local loss of alcohol-center chirality and remote CIP
letter changes are deliberate, validated effects, not invented stereochemistry.

## 5. Same 347-case completeness audit

The pre-change rerun reproduced the preserved Phase 2B baseline. Inputs, independent
expected products, conditions, required sites and score categories are unchanged
for all **347 cases**. The formerly blocked alcohol remote-center row additionally
checks its exact independently specified isomeric product after reaching the
public workflow. Regression subcases are not added to the audit denominator.

| Pathway | Phase 2B baseline | Phase 2C |
| --- | --- | --- |
| Alcohol oxidation | 8/12 — 66.7% | 9/12 — 75.0% |
| Carbonyl hydrogenation | 7/11 — 63.6% | 7/11 — 63.6% |
| Alkene hydrogenation | 11/14 — 78.6% | 11/14 — 78.6% |
| Ester hydrolysis | 9/10 — 90.0% | 9/10 — 90.0% |
| Ester saponification | 10/11 — 90.9% | 10/11 — 90.9% |

Only **A086, remote stereocenter**, changes Unsupported → Fully supported.
Alcohol tested-case support improves **8.3 percentage points**. All **333 rows
outside alcohol oxidation**, all other pathway scores and all **38 negative
controls** retain their prior statuses.

Across 309 positives, fully supported is **155 → 156**, partial stays **16**,
and unsupported is **138 → 137**. There are zero incorrect-result rows and zero
preview failures. The rerun exercises **207 site options**, previously 206.
Remaining alcohol-audit positives are A084 remote F, A085 remote amine and A087
allyl alcohol: unvalidated spectator compatibility or competing unsaturation.

The [Phase 2B JSON](reaction-lab-carbonyl-phase2-results.json) is preserved.
[Phase 2C audit JSON](reaction-lab-alcohol-phase2c-results.json) contains every
observation and the final audited source hashes. These scores describe the fixed
tested matrix, not universal chemistry coverage or experimental probabilities.

## 6. Tests, TypeScript, production build and browser evidence

**All 686 tests pass: 284 Python + 402 JavaScript.** Added **28 Python tests and
10 JavaScript tests** above the previous 648, with many positive/negative molecular
subcases. No tests were deleted. Two old tests that deliberately asserted the
previous alcohol stereo restriction now assert that the separate aldehyde
oxidation pathway remains restricted; its chemistry was not opted in. The existing
capability expectation was updated. Product/conservation assertions were not
weakened.

Checks include:

- Independent exact products, original carbonyl-oxygen identity, byproducts,
  full salt counterions, balanced equations, mapped H transfers and charge changes.
- Simple/long/branched/cyclic structures, remote ethers, separated OH sites,
  distant enantiomers and simultaneous local stereo loss/remote retention.
- Independent CIP and 3D stereochemistry, unsigned centers, selected versus
  unselected OH, input reversal, source maps and size boundaries.
- Competing/unvalidated groups, near-site and enhanced stereo, wrong reagents,
  false names/formulas/CIDs, missing/incompatible conditions and oxidation stages.
- Corrupted atom/charge/bond/map/stereo contracts, attempts to permit loss at
  unrelated centers, invalid charge declarations and injected validation failures.
- Real authenticated production HTTP match/diagram/run routes and correct main-
  product 2D/3D atom links, with water and chloride-salt atoms still in the equation.
- Actual public stoichiometry fed into browser-local calculators: independent
  alcohol/carbonyl and full NaOCl molar masses, one equivalent per selected site,
  limiting reactants, required amounts and theoretical yields in either input order.
- All prior ester, hydrogenation, reaction, calculator, cross-page and deployment
  regressions remain passing.

TypeScript and the production build pass; `git diff --check` passes. Existing
dependency `use client` and large-builder-chunk warnings remain. No HTML, CSS
or frontend TypeScript was edited for this increment.

The public browser check imported exact `CC[C@H](C)CCO` through Builder's existing
structure dialog, checked it and sent it as molecule 1 to Reaction Lab. With the
existing sodium hypochlorite input and first-stage/aqueous settings, it produced
C6H12O plus NaCl and water. The mapped S center remains S in Advanced information;
selecting carbon 3 links the source, 2D product and 3D product. Browser search
initially reported PubChem temporarily unavailable, so this check used the actual
Builder hand-off rather than claiming a successful online lookup. No PubChem
implementation or external service was changed.

Evidence: [linked chiral carbon](reaction-lab-alcohol-phase2c-stereo.png) and
[stereochemistry information](reaction-lab-alcohol-phase2c-stereo-information.png).
The temporary verification tab was closed without overwriting user tabs. The
localhost preview is left running with the completed source.

## 7. Recommended next increment — not implemented

For Phase 2D, start with the existing **SN2 substitution** pathway: independently
screen remote ether/other spectators, preserve distant configurations, and enforce
the mapped local backside-inversion contract. Competing E2, base-induced chemistry
and unvalidated leaving-group environments must remain explicit limitations.
Do not broaden all addition/substitution rules at once.

This recommendation is not implemented. Work stops after Phase 2C.
