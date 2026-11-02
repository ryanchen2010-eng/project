# Phase 2 consistency review — SN1, SN2, E1 and E2

Review date: October 14, 2026. **Review only; no implementation.**

## 1. Verdict

The four mapped mechanisms are internally sound **within their explicitly bounded models**. This review found no incorrect generated product connectivity, broken atom correspondence, charge-conservation failure, distant-center inversion or malformed elementary mechanism in the tested options.

However, the four pathways are **not yet a fully consistent chemistry comparison system**. SN1/E1 admit different carbocation environments; SN2 sometimes rejects an eligible site because another distant halide cannot undergo SN2; and condition labels describe preset-profile matching more strongly than the underlying chemistry warrants. These are coverage/assessment issues, not evidence that the verified transformations should be discarded.

Passing this finite review is not proof of exhaustive chemical compatibility or an experimentally valid reaction protocol. The tools do not establish rates, product ratios, actual yields, selective conversion or laboratory safety.

## 2. Verification and scope

| Check | Result |
| --- | --- |
| Existing Python suite | 438 passed |
| Existing JavaScript suite | 476 passed |
| Existing total | **914 passed; zero failures** |
| Fixed completeness audit | **347 cases; unchanged from Phase 2G** |
| Additional substrate matrix | 48 structures × four pathway profiles = 192 public matching checks |
| Additional condition matrix | 48 checks |
| Additional reagent checks | Five, including full NaOH/KOH and unsupported reagent controls |
| Independently entered product/scope expectations | 27 comparisons passed |
| Public option previews and runs | **120 passed** |
| Additional real calculator integrations | 60 fixtures; limiting/yield and required-amount checks passed |
| TypeScript | Passed with `--noEmit` |
| Production build | Passed; existing dependency-directive and large-chunk warnings remain |
| Source preservation | SHA-256 hashes unchanged for all 143 inventoried source/config/test/script/public files |

The extra diagnostics exercised the actual public matching, diagram and run functions used by the API—not just internal transformations. Every eligible option was previewed and generated in 3D. Checks covered unique atom identities, total charge, unaffected bonds, mapped electron endpoints/source bonds, mechanism step count, carbocation/oxonium/hydronium states, physical stereo parity, specified-center CIP in generated geometry, and exact main-product 2D/3D atom order. All 120 generated models reported convergence; that is not validation of a transition state or experimental geometry.

The calculator checks used the unchanged browser arithmetic and included reversed input slots, full sodium-hydroxide molar mass, several constitutional products and exclusion of solvent water from E1 limiting-reactant arithmetic. They calculate theoretical quantities only.

No new permanent regression tests were added. Temporary diagnostics live outside the application at `/private/tmp/reaction-phase2-review.py`; no diagnostic cases were put into the visible example collection. This was a code/API review, not a new browser interaction or accessibility test pass.

Evidence: [complete audit and cross-pathway observations](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase2-consistency-review-results.json>) and [calculator/preservation checks](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase2-calculator-review-results.json>).

### Fixed benchmark comparison

| Pathway | Phase 2G | This review |
| --- | --- | --- |
| SN2 | 10/15 — 66.7% | 10/15 — 66.7% |
| SN1 | 5/11 — 45.5% | 5/11 — 45.5% |
| E2 | 7/13 — 53.8% | 7/13 — 53.8% |
| E1 | 5/9 — 55.6% | 5/9 — 55.6% |

All 347 result records—not only their scores—match the saved Phase 2G results. Overall: 164 fully supported, 129 unsupported, 16 partially supported and 38 correctly rejected controls. No audit-flagged incorrect result or failed preview occurred.

Existing benchmark caveats are retained: A190/E2 and A199/E1 have reversed-chain stereo expectation defects documented in earlier reports; A207/E1 and some E2 cases score full despite unassigned E/Z. Most rows compare connectivity rather than fully independent stereo. Therefore these percentages must not be read as complete stereochemical or experimental coverage. The fixed benchmark was not changed; stricter independent stereo checks remain separate.

## 3. Same-substrate comparison

Numbers below are **selectable mapped site options**, not yields or product ratios. SN2/E2 use actual hydroxide; SN1/E1 use actual water. Each column uses its own existing profile, so this table does not imply all four mechanisms occur under one reagent/condition combination.

| Substrate | SN2 | E2 | SN1 | E1 |
| --- | --- | --- | --- | --- |
| Methyl bromide | 1 | 0 | 0 | 0 |
| Ethyl bromide | 1 | 1 | 0 | 0 |
| Isopropyl bromide | 1 | 1 | 0 | 1 |
| sec-Butyl bromide | 1 | 2 | 0 | 2 |
| 2-Bromopentane | 1 | 2 | 0 | 0 |
| tert-Butyl bromide | 0 | 1 | 1 | 1 |
| Benzyl bromide | 1 | 0 | 1 | 0 |
| 1-Bromoethylbenzene | 1 | 1 | 1 | 1 |
| Allyl bromide | 0 | 0 | 1 | 0 |
| Narrow allylic `C=C(C)C(Br)C` | 0 | 0 | 0 | 1 |
| Mixed distant primary/tertiary halides `BrCCCCCCC(Cl)(C)C` | 0 | 3 | 1 | 2 |

Methyl/no-β-H elimination is correctly rejected. Ordinary tertiary SN2 is rejected. Benzyl bromide lacks an eligible saturated β-H for these elimination models, while secondary benzylic substrates can have one. Neopentyl, ring-bound, aryl/vinyl and alkyl-fluoride controls remain rejected in this model. Longer, branched, remote-O and distant-stereo cases were also exercised in the evidence matrix.

These substrate/base distinctions agree with the standard mechanistic framework, but the engine's exclusions are narrower than chemistry in general. In particular, ordinary allylic SN2 and some secondary solvolysis are chemically possible despite missing engine options. [SN2 substrate/solvent reference](https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction), [MSU substitution/elimination comparison](https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm).

## 4. Incorrect, contradictory or potentially misleading behavior

### A. SN1/E1 carbocation admission is uneven — high priority

`CCC(Br)C` gives water-based E1 options for but-1-ene and but-2-ene, but no SN1 option. Isopropyl behaves similarly. The E1 policy deliberately accepts only small Me/Me or Me/Et secondary arm topologies; the SN1 policy excludes ordinary secondary aliphatic ionization entirely.

The enabled E1 product is not itself shown to be wrong. The inconsistency is that the common cation can be admitted for elimination but is not represented as a possible water-capture branch. E1-specific narrow allylic inputs have a similar gap: E1 is offered, while SN1 resonance capture is unimplemented. Do not resolve this by blindly copying scope: allylic capture may need multiple constitutional products and mapped resonance-site validation.

Current caveats correctly state that absent SN1 does not prove no substitution. Nevertheless, an options-only comparison can suggest a completeness it does not have. A shared cation eligibility assessment should distinguish validated ionization from separately supported capture/elimination branches. [SN1/E1 common-intermediate reference](https://www2.chemistry.msu.edu/faculty/reusch/VirtTxtJml/alhalrx3.htm).

Code evidence: [SN1 admission](</Users/rc/Documents/Capstone project/server/sn1_rule.py:91>), [E1 admission](</Users/rc/Documents/Capstone project/server/e1_rule.py:76>).

### B. Condition ranking overstates preset mismatch — high priority

For tert-butyl bromide + water, aqueous/ambient gives SN1 `Possible` and E1 `Unfavorable`; aqueous/heated reverses those labels. Both options remain available. tert-Butyl bromide + hydroxide in polar-aprotic/ambient conditions is also labeled E2 `Unfavorable` solely because it differs from the ethanolic/heated profile.

These are not demonstrated product errors, and accompanying text says competition can remain. But a fixed profile mismatch cannot establish an intrinsically unfavorable pathway. Solvent, temperature and leaving-group effects are qualitative here; concentration, actual solvent identity, pH and kinetics are absent. Additional acid/metal catalysts are explicitly unevaluated, not approved conditions. Missing settings produce `incomplete`; mismatches remain runnable alternatives. Acid–base neutralization with an added acid is not modeled.

Recommend clearer condition-fit wording and individually justified chemical incompatibility checks—not a numerical selectivity score. [Condition logic](</Users/rc/Documents/Capstone project/server/reaction_reasoning.py:129>), [current card wording](</Users/rc/Documents/Capstone project/src/reaction-lab.ts:311>). SN1/E1 competition under ionizing conditions is expected in the standard framework. [Reference](https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions).

### C. Distant non-SN2 halide blocks an otherwise eligible SN2 site — medium priority

`BrCCCCCCC(Cl)(C)C` has a primary bromide far from a tertiary chloride. SN2 rejects the entire molecule because the other C–X site cannot itself pass SN2. E2 exposes three options, and SN1/E1 retain the separated primary bromide while transforming the tertiary site.

Competing E2 at the tertiary site is real and should remain disclosed, but it need not make primary-site SN2 chemically impossible. This is a conservative software coverage gap, not a wrong generated product. Any expansion needs one-site preservation and competition tests; the distant group must not simply be called inert. [SN2 whole-molecule halide gate](</Users/rc/Documents/Capstone project/server/sn2_rule.py:44>).

### D. Rejection explanations lose useful detail — medium priority

Unsupported neutral inputs receive pooled strings from multiple pathways, not structured per-pathway/site explanations. For an API 422, the UI replaces the actual error with a generic unsupported-structure message. Sodium methoxide/iodide salt probes fail closed, but their detailed API reason is not retained in that UI branch. Some valid options also coexist with unrelated rejected-pathway notes.

A small wording defect also labels a hypothetical two-membered OH capture path as ether/epoxide closure: `OCBr` is correctly rejected overall, but its SN2 reason says “2-membered intramolecular ether/epoxide closure.” By contrast, `OCCBr` reports the plausible three-membered closure risk. Direct oxygen participation should be distinguished from feasible ring-size competition; the first explanation is chemically incorrect even though no incorrect product is generated.

These problems can make safe exclusions seem chemically absolute or irrelevant to the selected site. [422 handling](</Users/rc/Documents/Capstone project/src/reaction-lab.ts:671>), [near-O explanation](</Users/rc/Documents/Capstone project/server/sn2_rule.py:60>).

## 5. Shared compatibility: preserved features and remaining gaps

Passed: screened distant OH/ordinary ethers, distant specified tetrahedral centers, exact atom identity, unaffected connectivity/bonds, net charges and byproducts. Independent mapped-parity checks passed; R/S was checked separately against generated geometry, not used as a substitute for physical retention. Full NaOH/KOH identities remain correctly represented in input quantities while their cations are omitted from simplified ionic diagrams.

Some differences are justified: SN1/E1 screen carbocation capture and acid-sensitive O groups more strictly; SN2/E2 apply base/neighboring-group screens. `COCCC(Br)(C)C` can match E2 but is rejected by SN1/E1 for a potential four-membered O-capture path. That distinction is not automatically an inconsistency to remove.

Remaining unsupported or conservative scope includes:

- General allylic SN2/SN2′ and allylic E2; unsymmetrical SN1 resonance capture.
- Most ordinary secondary water solvolysis/E1 beyond the narrow E1 scaffold.
- Ring-bound reaction sites, bridgeheads, ring-bound β geometry and adjacent ring-migration risks.
- Additional unsaturation, carbonyl/acid/ester/amine/peroxide and heteroaromatic spectators without pathway-specific validation.
- Remote F as a spectator, as distinct from F being a poor leaving group.
- Charged/disconnected substrates, radicals, isotopes, query atoms, enhanced/relative or non-tetrahedral stereo, small strained rings and size limits.
- Distant centers becoming non-stereogenic: current policy rejects rather than silently discarding tags; a validated configuration-loss classification could improve this.
- Only hydroxide and water reagent models; no general nucleophile/base-strength or concentration model.

Multiple equivalent molecular products can legitimately retain separate mapped C–X site options. E1/E2 remove equivalent β-position duplicates at a given site; identical products from distinct C–X identities are not automatically erroneous duplicates. One-site options are not selective mono-conversion predictions.

## 6. Mechanisms and stereochemistry

| Pathway | Implemented and verified | Partial/unsupported behavior |
| --- | --- | --- |
| SN2 | One concerted step; O lone pair → C and C–X → X. Actual physical backside inversion, independent CIP relabeling and distant retention. | No transition-state trajectory or general steric/energy search; no configuration invented for unsigned input. |
| E2 | One concerted step; base → β-H, C–H → C=C, C–X → X. Actual mapped β-H and bounded anti relationship. | E/Z only from two specified local tetrahedra with a unique β-H. Acyclic anti rotation is kinematic, not clash/energy validation; cyclic trans-diaxial modeling unsupported. |
| SN1 | Separate ionization, water capture and deprotonation; positive planar C, oxonium, then neutral alcohol + hydronium/halide. Only reacting-center configuration removed. | No ion pairs, facial preference, rearranged products, general resonance regioselectivity or measured racemization ratio. |
| E1 | Ionization before β-H removal/C=C formation; positive planar C followed by neutral alkene and hydronium/halide. Distant centers retained. | New E/Z always unassigned; no conformational populations, rearranged products or major-product ratio. |

Reference principles: [SN1 elementary steps and ion-pair limits](https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction), [E2 geometry](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect), [cyclic E2 geometry](https://openstax.org/books/organic-chemistry/pages/11-9-the-e2-reaction-and-cyclohexane-conformation).

The E1 second step is marked `Concerted` because proton removal and π formation occur together **after** a separate ionization. This is not an E2 mechanism. The step description explains that correctly, but the heading could say “coupled proton loss/π formation” to avoid ambiguity.

Electron movement has precise mapped source/destination highlights and step states, not geometrically drawn curved arrows. Charged intermediates are 2D only; 3D shows the final main product. Lewis diagrams intentionally omit stereo annotations, so they do not visually prove inversion. An unsigned 3D conformer is only one representative shape, not an assigned enantiomer or alkene-isomer distribution. Qualitative energy topology is not calculated energetics; `rateDeterminingStep: 1` is textbook model metadata, not measured kinetics.

SN1/E1 net equations use HX as an explicitly documented acid-equivalent reporting form; their aqueous mechanism shows hydronium + X⁻. SN2 gives alcohol + X⁻; E2 gives alkene + water + X⁻. These distinct charge/byproduct representations are consistent with their different input/net models; HX reporting must not be confused with dissolved undissociated acid. E1 solvent water is correctly excluded from net amount arithmetic.

## 7. Five highest-priority improvements

1. **Align SN1/E1 cation assessment and competitor disclosure.** Start with the already screened secondary cases; separately validate allylic capture sites. Do not enable arbitrary primary or rearranged cations.
2. **Improve condition-fit assessments.** Separate preset mismatch, unevaluated conditions and genuinely incompatible chemistry; avoid implying rates or a winner from ambient/heated labels.
3. **Make mixed-halide SN2 compatibility truly site-specific.** Validate primary-site options with distant competing halides while preserving maps, spectator bonds and explicit competition warnings.
4. **Strengthen stereo/conformation evidence.** Add clear local inversion/undefined-isomer depiction and stricter independent benchmark grading; extend E2 conformational capability only with validated models. Preserve the original fixed audit separately.
5. **Return precise per-pathway/site reasons to the UI.** Preserve 422 details safely, separate unsupported competitors from the selected valid option, and correct near-O/“Concerted” wording without redesigning layout.

## 8. Before alkene hydration

**A targeted consistency/assessment increment is recommended first**, especially items 1–2 and accurate rejection explanations. The mapped transformation foundation is strong enough to retain; a redesign or blanket restriction removal is unnecessary. Completing every cyclic/conformer/stereo capability is not a prerequisite for hydration, provided limitations remain explicit.

After those scoped fixes are independently tested, hydration can adopt the shared cation/competition assessment rather than duplicate its current inconsistencies. **No fix or hydration implementation was started during this review.** Only review documentation/results were saved; the build refreshed ignored `dist` output, not source or deployment.
