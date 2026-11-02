# Reaction Lab — Phase 2G: site-compatible water E1

Completed locally on **October 14, 2026**. This increment changes only existing
E1 chemistry and its validation/information. No page layout, Calculator,
frontend, curated example, new family, base or leaving-group family changes.
SN1/SN2/E2 rule modules retain their Phase 2F hashes. Nothing was pushed,
published or deployed; no subsequent reaction increment has begun.

## 1. Structural compatibility and newly supported cases

[e1_rule.py](../server/e1_rule.py) applies an independent policy through the
shared site-compatibility architecture. It checks the actual saturated C–Cl/Br/I
site, screened cation environment, eligible saturated beta C–H and spectators.
It replaces the old whole-molecule hydrocarbon/unsigned-stereo E1 gate, not the
existing SN1 or E2 policies.

- Longer/branched tertiary and benzylic sites retain their existing valid net
  options, now with exact reaction-site/elementary validation.
- Screened distant saturated primary/secondary alcohols and ordinary dialkyl/
  carbocyclic aryl–alkyl ethers can remain. Nearby oxygen, small capture paths,
  acid-sensitive tertiary/benzyl/allyl oxygen and acetal/ketal environments are
  excluded. Distance is not proof of inertness: proton equilibria, larger-ring/
  intermolecular capture, acid buildup and later conversion remain unpredicted.
- Distant specified tetrahedra are physically retained. Reacting alpha tags are
  cleared during ionization; selected beta tags may be consumed only when that
  actual C–H is lost and C=C forms.
- Two saturated **Me/Me or Me/Et arms** identify a narrow acyclic secondary scope
  by graph topology (isopropyl/sec-butyl), not compound names or presets. No
  adjacent more-stable tertiary/benzylic shift destination is approved. Longer,
  branched and multifunctional secondary environments require further individual
  validation. These are conditional possibilities in the ionizing-water model,
  not claims of measurable efficiency or a dominant E1 product. This bounded
  scope uses the secondary/ionizing-solvent discussion in the
  [MSU author textbook](https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm).
- Narrow allylic support covers **CH2=C(R)–CH(X)R'** and
  **CH2=C(R)–C(X)(R')R''**, with ordinary saturated alkyl substituents. The central
  pi carbon has **no H**: the other localized resonance contributor cannot
  deprotonate that sp² beta carbon to a cumulene. Only saturated beta-H loss at
  the original secondary/tertiary site is generated. General allylic regioisomers,
  rearranged/cumulated products and atom-path populations are not predicted.
  Both relevant resonance termini are included in the oxygen-capture screen.

Representative independent positives (not added to visible examples):

| Substrate | Independently checked products/options |
| --- | --- |
| `COCCCCCCC(Br)(C)C` | `COCCCCCC=C(C)C`, `C=C(C)CCCCCCOC`; screened distant ether |
| `OCCCCCCC(Br)(C)C` | Two constitutional alkenes; distant primary OH retained |
| `CC[C@H](C)CCC(Br)(C)C` | `CC[C@H](C)CC=C(C)C`, `CC[C@H](C)CCC(C)=C`; distant physical configuration retained |
| `C[C@H](Br)c1ccccc1` / `@@` | `C=Cc1ccccc1`; reacting configuration lost, not inverted |
| `CCC(Br)C` | `C=CCC` and `CC=CC`; internal E/Z unassigned |
| `CC(Cl)C` | `C=CC`; symmetry-equivalent beta methyls give one option |
| `C=C(C)C(Br)C` | `C=C(C)C=C`; narrow secondary allylic net pathway |
| `C=C(C)C(Cl)(C)C` | `C=C(C)C(=C)C`; narrow tertiary allylic net pathway |
| `CCCC(Br)(C)CC` | Three distinct constitutional beta-position products |
| `CC(Br)(C)CCC(Br)(C)C` | Four mapped site options at two C–X identities; two unique constitutions |

Source map labels are removed only from symmetry ranking, not reaction identity
or provenance. Equivalent beta sites at one C–X do not duplicate products; a final
same-C–X/product-identity check also removes equivalents. Different C–X identities
remain selectable even if the final product constitution is identical. Every
option is one-site chemistry, not selective mono-elimination.

## 2. Carbocation and stereochemistry validation

A new **E1-stage permission** is separate from SN1 solvolysis and E2 anti stereo:

- Ionization starts at neutral tetrahedral alpha C–X and makes a +1, degree-three
  sp² alpha carbon with no tetrahedral tag, plus −1 halide. Beta C–H and C–C
  remain intact at this stage; distant and beta configurations remain checked.
- Elimination must start at that actual positive unassigned cation. Beta loses
  its selected mapped H, alpha–beta single becomes double, alpha becomes neutral
  and the actual water oxygen accepts H to form hydronium.
- Only the participating alpha/beta centers may become planar. Exact neighbor
  changes, bond orders, charges, valence, map/atom identities, unaffected bonds,
  serialization and distant physical parity are checked. Invalid, lost or
  invented tags fail closed.
- New alkene geometry is **unassigned**. E1 does not inherit local anti-E2
  stereoselectivity, even from a specified starting alpha center. No E/Z or
  stereoisomer ratios are invented from a single conformer or relative stability.
- CIP is reassigned independently. A remote-Cl test retains its physical center
  while its label remains R for one beta position and becomes S for the other;
  the expected products are independently specified, not a forced R/S flip.

Existing enhanced/relative/non-tetrahedral stereo guards reject unsupported
input before ordinary canonicalization can silently discard it. Ordinary primary/
methyl permission, SN1 facial outcomes and E2 anti outcomes are not expanded by E1.

## 3. Mechanism, proton transfer and net calculation

The existing **two-step mechanism** remains intact, with one carbocation
intermediate. Each state now passes the exact E1 contract:

1. **Ionization:** C-alpha–X electrons → X; +C/−X form. No beta-H loss yet.
2. **Elimination:** water lone pair → beta H; beta C–H electrons → C-beta/C-alpha
   pi bond. Water becomes hydronium while alpha becomes neutral and X remains −1.

The two electron movements in step 2 are coupled; the existing UI calls that
individual step “Concerted.” This does **not** describe the overall E1 mechanism:
leaving-group departure occurred in step 1, with a real intermediate between.
The description explicitly distinguishes this from one-step E2. No fictitious
stable beta-carbanion or rearranged cation is inserted. The overall two-step
topology follows [OpenStax 11.10](https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions).

Net reporting stays **R–X → alkene + HX**; water is the medium and excluded from
the simplified net amount calculation. The mechanism explicitly includes water
and reports **alkene + H3O+ + X−**, not undissociated HX in aqueous solution.
HX is an acid-equivalent reporting form. Every net/elementary graph conserves
all mapped atoms and total charge. The final mechanism main fragment must equal
the selected net product.

Independent browser-local calculator tests check whole-substrate molar masses,
both input orders, all selected sites, required amounts and theoretical yield.
Missing/zero solvent quantity does not falsely make water a limiting reactant.
Notes explicitly distinguish net arithmetic from solvent quantity, selective
conversion, experimental yield, major-product or E/Z distributions.

## 4. Competition and remaining exclusions

E1/SN1 competition is explained qualitatively, including cation environment,
actual beta-H availability, water, temperature and screened spectators. A valid
net option is not a claim that E1 dominates; absence of an SN1 option is not
proof that substitution cannot occur. Medium/temperature selectors retain their
existing qualitative behavior: missing conditions are incomplete; mismatches
are unfavorable alternatives, not laboratory protocols or absolute impossibility.
Invalid selectors and wrong actual reagents are rejected.

Still outside scope:

- Arbitrary ordinary primary, longer/unvalidated secondary and unequal/general
  allylic environments; sp²/aromatic beta-H removal, cumulenes and propargyl systems.
- Ring-bound/bridgehead alpha, ring-bound beta and unvalidated exocyclic geometry;
  adjacent cyclic migration, branched/quaternary hydride/alkyl shifts and potential
  shifted benzylic cations. Previously unscreened E1 shift-risk candidates are
  now rejected as unvalidated, rather than generating confident unrearranged results.
- Nearby O/4–6-member capture paths; acid-sensitive OH/ethers/acetal/ketal;
  nearby coupled halides, unclassified groups, carbonyl/acid/ester/peroxide,
  additional unsaturation, heteroaromatics and unvalidated elements such as F.
- Other base/solvent reagent families, disconnected/charged/radical/isotopic/query
  substrates, strained rings, unsupported stereo and the existing 80-explicit-atom
  main-product limit.

Rearrangement/capture/acid-sensitive screens are conservative model boundaries,
not exhaustive predictions or claims that accepted groups are always inert.
Related chemistry principles are supported by
[carbocation rearrangements](https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements)
and [ether acid cleavage](https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage).
No rates, measured energies, experimental yields or product distributions are calculated.

## 5. Fixed 347-case audit and separate benchmark caveats

All original case inputs, expected products, conditions, minimum-site counts,
coproducts and variant fields are unchanged. The audit script only adds the new
module to its hash inventory. Saved results:
[phase2g-results.json](reaction-lab-e1-phase2g-results.json).

| Measure | Phase 2F baseline | Phase 2G, unchanged scoring |
| --- | --- | --- |
| E1 fully supported applicable cases | 3/9 (33.3%) | **5/9 (55.6%)** |
| E1 unsupported / partial | 5 / 1 | 3 / 1 |
| E1 negative control | 1 correctly rejected | 1 correctly rejected |
| Overall fully supported | 162 | 164 |
| Overall unsupported / partial | 131 / 16 | 129 / 16 |
| All negative controls | 38 correctly rejected | 38 correctly rejected |
| Public options across benchmark | 216 | 220 |

Only **A199** (distant stereocenter) and **A207** (sec-butyl) improve their score.
All **337 non-E1 case statuses** remain unchanged, including Phase 1–2F
improvements. No audit-flagged incorrect result or failed preview appears.
New distant-oxygen and narrow allylic cases outside this matrix do not change
its denominator or enter the curated collection.

Remaining benchmark limitations: **A195** ring-bound tertiary; **A197** “remote
ether” actually offers a potential four-membered oxygen-capture path; **A198** F
is not a validated spectator. **A196** benzylic secondary gives its correct net
alkene but remains partial because E/Z is unassigned.

Two pre-existing benchmark defects/limits are reported separately, not fixed:

1. **A199 reversed-chain stereo expected literal:** its terminal product is listed
   as `C=C(C)CC[C@H](C)CC` (R), whereas retaining the original mapped S center
   requires `C=C(C)CC[C@@H](C)CC` (S). The fixed scorer compares E1 connectivity,
   not that physical parity. Independent strict isomeric, mapped-parity and 3D CIP
   tests verify the retained S product; no code is altered to match an inverted
   benchmark literal. This parallels the separately documented E2 A190 defect.
2. **A207 lacks an E/Z scoring flag:** its new internal but-2-ene stays unassigned,
   but the original scorer counts this row as fully supported. **5/9 is the
   unchanged benchmark score, not five completely stereoresolved E1 cases.**
   Independent tests explicitly reject invented E/Z tags. No stronger experimental
   or stereochemical completeness claim is made from this score.

## 6. Tests, production checks and preservation

**914 tests pass: 438 Python + 476 JavaScript.** This adds **43 independent
Python tests + 24 real calculator integration tests** to the previous 847.
Three existing test methods update their intentional E1 assertions (secondary
scope, new E1 capability label, E1 now alongside unchanged SN1 for stereo/ether
fixtures); no test was deleted or SN1/SN2/E2 chemistry validator weakened.

Coverage includes independent products/formulas/masses; primary/secondary/
tertiary/benzylic/allylic positives and negatives; symmetry/source-map labels;
multiple C–X/beta positions; spectator/configuration retention; valid serialized
elementary charges; electron endpoints; actual proton destination; corrupted
maps/bonds/stereo/charges/stage permissions; failure injection; wrong conditions/
reagents; size limits; no preset dependence; authenticated public positive/negative
match → diagram → run; and 2D/3D exact main-product correspondence.

- Python full suite: **438/438**, including expected invalid-input parser diagnostics.
- JavaScript full suite: **476/476**, none skipped/cancelled.
- TypeScript: **pass**. Production build: **pass**, all five pages packaged.
- Existing dependency `use client` and large-chunk warnings remain, not build failures.
- Whitespace check: **pass**. SN1/SN2/E2 rule and Reaction Lab frontend hashes match
  Phase 2F; shared validators gain only an explicit separate E1 permission.

## 7. Browser verification and current preview

The actual Builder import/check/transfer workflow was exercised with
`CC[C@H](C)CC[C@H](Br)c1ccccc1` (C13H19Br), using water/protic medium and Heated.
The public UI offers both the unchanged SN1 option and newly supported E1.
E1 gives C13H18 + HBr net reporting, water marked as medium, and a linked 3D product.
Exact beta **carbon 6** is keyboard-linked in both views. Mechanism roles are
alpha **7**, Br **8**, beta H **26**, solvent O **34**; ionization and the later
beta-H/pi-bond movements appear separately and electron highlighting works.
Information reports **reactant 7 S → planar**, distant **3 S → S** and new
**C=C 6–7 unassigned**. No browser warning/error entries were recorded.

Saved evidence: [linked model](reaction-lab-e1-phase2g-linked.png),
[mechanism](reaction-lab-e1-phase2g-mechanism.png),
[stereochemistry](reaction-lab-e1-phase2g-stereo.png),
[final existing-example preview](reaction-lab-e1-phase2g-final-preview.png).
After the final restart, the existing tert-butyl chloride/water example still
offers unchanged SN1 alongside E1. E1 produces C4H8 + HCl with water as medium,
links exact beta carbon 1 in 2D/3D, and shows the separate ionization/second
elimination step with the explicit non-E2 clarification. No browser warnings/errors.
The existing all-H net 2D view still omits stereo annotations and can be cramped
for larger structures; no diagram layout redesign was made. Charged intermediates
remain 2D, and only retained main-product atoms link to the final 3D conformer.
The local preview is running with final E1 code; temporary verification tabs were
closed after checks. No publication or deployment is included.

## 8. Recommended next increment — not started

Improve existing **alkene hydration** next, using its own carbocation/site and
spectator policy, explicit rearrangement/capture checks and honest stereo limits.
Do not automatically reuse E1's beta-H permissions or assume every alkene shares
the same selectivity. Await a separate request before starting that work.
