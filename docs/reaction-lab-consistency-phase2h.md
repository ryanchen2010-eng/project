# Phase 2H — Reaction consistency fixes

Completed October 14, 2026. This increment changes SN1/SN2/E1/E2 consistency only. No hydration, new reaction family, layout redesign, publication or new curated examples.

## 1. Corrections implemented

### Shared SN1/E1 ionization assessment

Added [carbocation_compatibility.py](</Users/rc/Documents/Capstone project/server/carbocation_compatibility.py>) for the already bounded secondary topology, alkyl/benzylic basis, ordinary halide environment and adjacent rearrangement risks. Both policies use it; capture and elimination permissions remain independent.

- Isopropyl (Me/Me) and sec-butyl (Me/Et) halides now expose water capture through SN1 as well as their existing E1 options. Cl/Br/I and both specified sec-butyl configurations were verified.
- SN1 still has separate positive planar carbocation, oxonium and deprotonation states. The reacting configuration is unassigned; no racemization ratio is invented. Ordinary secondary cations are not mislabeled as resonance contributors.
- Primary/methyl, general secondary, ring-bound, neighboring shift and unsupported functional-group restrictions remain. The shared secondary predicate is graph-based, not a compound-name list.

This narrow branch is supported as a possible solvolysis pathway, not a fast or selective preparation. Secondary substrates can give SN1/E1 products in ionizing conditions; the framework does not establish their measured conversion. [MSU primary chemistry reference](https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm).

### Evidence-based condition labels

Added [reaction_conditions.py](</Users/rc/Documents/Capstone project/server/reaction_conditions.py>) and a small existing-control label helper. API legacy states `aligned`/`alternative`/`incomplete` remain available; a new structured status provides the actual distinction.

| Status | Meaning |
| --- | --- |
| `model-match` | Reference settings match; an experimental outcome is not guaranteed. |
| `reference-difference` | Preset mismatch alone does not establish chemical disfavor. |
| `missing` | Comparison settings are incomplete; actual reagent validation is separate. |
| `disfavored` | A justified factor exists, currently protic solvation of hydroxide in SN2. This does not establish an impossible reaction or competing winner. |
| `unevaluated` | Added catalyst/activation or conflicting dry/water settings cannot be evaluated reliably. |

Heated SN1, ambient E1 and polar-aprotic E2 are no longer automatically called “Unfavorable” merely for differing from the reference. Actual hydroxide/water graph requirements remain enforced by the matcher. No new catalyst requirement is invented for these four models; unset solvent/temperature selectors are described as incomplete comparison settings, not missing chemical activation. Added acid is not treated as validated promotion or a quantitative pH/neutralization model.

Eligibility and condition assessment remain separate: matched net products can still be inspected under incomplete/alternative conditions with explicit warnings. Other reaction families retain their previous assessments unchanged. The supported SN2 solvent caveat follows the standard protic-solvation distinction. [Primary reference](https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction).

### Site-specific mixed-halide SN2

A selected, eligible primary C–X can now substitute while a screened distant ordinary tertiary C–X stays mapped and unchanged. For example:

`BrCCCCCCC(Cl)(C)C + OH⁻ → OCCCCCCC(Cl)(C)C + Br⁻`

The additional site is explicitly **not SN2-eligible**; competing hydroxide-driven elimination is disclosed and the option is qualified `Possible`, not selective mono-substitution.

This is intentionally narrow: primary selected site; ordinary saturated, acyclic tertiary spectator environment; at least five C–C path edges between sites. That keeps a prospective new product-OH/other-halide closure beyond the screened three–six-membered ring range. It is a conservative model boundary, not a claim that longer-range chemistry is impossible. Cl/Br/I changes, source remapping, distant specified tertiary configurations, NaOH/KOH masses and reversed inputs were verified. Closer sites, new secondary-site spectator permission, allylic/ring-bound/heteroatom environments and ordinary tertiary SN2 remain excluded.

### Precise ring and rejection explanations

Added one shortest-path helper for the existing SN2/E2 OH screens. An existing O–C bond is direct heteroatom substitution, not a hypothetical second bond forming a two-membered ring. Nonbonded endpoints count the shortest path's atoms: `OCCBr` gives a potential three-membered epoxide; four–six-membered paths are described as cyclic ethers. Messages identify the pathway and O/C substrate atoms. These wording changes do not broaden E2 eligibility or stereochemistry.

The UI now retains specific API 422 input reasons as text with a model-limitation caveat, instead of discarding them. Selected-site rejection is distinguished from an additional unsupported halide. No HTML injection path was introduced.

## 2. Differences deliberately retained

- **Restricted allylic E1 is not automatically SN1.** `CH2=C(R)–C(X)(R')R''` may have the existing bounded elimination option, but water capture can involve inequivalent resonance termini and different constitutions. Generalized mapped resonance capture would require a separate model; this phase explains that boundary rather than generating only one speculative alcohol.
- **SN1 does not require an eligible β-H; E1 does.** Benzyl bromide and the symmetric terminal allyl capture model do not thereby gain a saturated β-H elimination option.
- **Basic and carbocation spectator screens differ legitimately.** Oxygen capture, acid-sensitive cleavage and neighboring-group risks remain stricter in water/carbocation models than in screened hydroxide net edits.
- **SN2/E2 versus SN1/E1 reagent and elementary-step requirements remain distinct.** No new nucleophile or base families were added. No tertiary SN2 permission comes from E1/SN1 admission.

SN1/E1 share the ionization foundation, not automatic product scope or a measured competition ratio. [SN1 elementary-step reference](https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction).

## 3. Fixed 347-case benchmark

The benchmark script/input matrix/expectations/scoring were not edited; script SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

| Pathway | Before | After |
| --- | --- | --- |
| SN1 | 5/11 — 45.5% | **6/11 — 54.5%** |
| SN2 | 10/15 — 66.7% | 10/15 — 66.7% |
| E1 | 5/9 — 55.6% | 5/9 — 55.6% |
| E2 | 7/13 — 53.8% | 7/13 — 53.8% |

Only **A182**, sec-butyl water SN1, changes status/products/site count: unsupported → fully supported, with one alcohol option. All other 346 rows retain their status, product set and option count. Overall: 165 fully supported, 128 unsupported, 16 partial, 38 correctly rejected. No audit-flagged incorrect result or failed preview.

Some explanatory notes change as intended. The new mixed-halide SN2 examples are outside the fixed matrix, so its percentage does not increase. Existing A190/A199 stereo-literal and A207/unassigned-E/Z grading caveats from the review remain; the audit score is not comprehensive stereochemical or experimental validation.

## 4. Tests and public workflow

**976 tests pass: 476 Python + 500 JavaScript.** Added **38 Python + 24 JavaScript** regressions. All original 914 test methods remain; nine existing methods update scope/label expectations to reflect these requested changes, with no method deleted and no product/stereo validator weakened.

New tests cover shared secondary ionization, independently entered alcohol/alkene products, carbocation/oxonium/hydronium states, local configuration loss and retained distant configurations, explicit competing pathways, mixed-halide primary-site independence, negative near/ring/allylic controls, source atom remapping, exact net edit validation and forced validator failure, correct ring-size explanations, five condition statuses and unchanged eligibility under condition changes.

The unchanged browser reaction arithmetic is exercised with 16 new real public fixtures, including reverse slots, independently specified formulas/masses, pure OH⁻ versus full NaOH/KOH mass, limiting amounts, theoretical yield and required amounts. No actual yield or product distribution is estimated.

The prior public review checks were rerun: **48 substrates, 192 matching calls, 48 condition checks, five reagent controls and 125 verified public options** (previously 120). The sec-butyl SN1 expected product is updated only in the temporary diagnostic, not the fixed benchmark. All net/elementary atom and charge checks, mapped bond changes, physical parity, specified-center 3D CIP and exact 2D/3D atom correspondence pass. No new public diagnostic failure occurred.

TypeScript `--noEmit`, the production build and `git diff --check` pass. Existing dependency-directive and large-bundle warnings remain. HTML, CSS, Calculators, public molecular data, curated molecule data and the audit script hashes are unchanged.

Browser verification: typed existing 2-bromopropane + water with aqueous/heated settings; both SN1/E1 appear; SN1 shows `Reference differs`; the resulting 2-propanol loads in 3D and carbon 2 is selected in both views. The existing page layout was retained. The local preview is running; nothing was deployed.

[Saved results, hashes and observations](</Users/rc/Documents/Capstone project/docs/reaction-lab-consistency-phase2h-results.json>).

![Verified secondary SN1 product with linked carbon 2](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase2h-preview.jpg>)

## 5. Remaining problems and readiness

General allylic resonance capture, rearranged cations, broad secondary solvolysis, cyclic E2, kinetic/solvent/pH models and quantitative competition remain outside the model. Mixed-halide SN2 support is deliberately not generalized to every distant unsupported group. E2 anti/E/Z predictions are unchanged; E1 new E/Z stays unassigned. Existing dense explicit-H 2D rendering and pooled rejection strings for some other pathways remain.

**Ready for a separately scoped alkene-hydration increment.** The verified Phase 2 consistency blockers are corrected or precisely bounded; broader chemistry gaps are documented rather than forced. Hydration must independently screen cations, competing capture/rearrangement, conditions and stereo—it cannot inherit blanket permission from these fixes.

**Phase 2H stops here. No alkene hydration or further reaction increment was started.**
