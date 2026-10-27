# Reaction Lab — completeness audit

Audit date: **October 9, 2026 (America/Toronto)**. Scope: current working-tree implementation, not an older GitHub version.

**Analysis only. No production source, existing tests, reaction rules, interface layout, or deployment settings were modified.** Added artifacts are this report, an isolated read-only audit runner, its observation snapshot, and a screenshot.

## 1. Executive summary

Reaction Lab is a genuinely structure-based, bounded net-reaction tool, **not merely a list of sample reactions**. There are **24 pathway types** in the current implementation, with additional equivalent/chain-length variants and dynamically generated site options. Names, formulas and PubChem CIDs supply identity/display data, not reaction eligibility.

Its strongest part is the shared mapped graph transformation: the successful audit candidates have correct independently expected main-product connectivity, balanced atoms/charge, unique mapped atom identities, and consistent main-product 2D/3D correspondence. Its weakest part is **scope**: ordinary molecules often stop at global element/stereo filters, limited reagent roles, ring guards, or an 80-explicit-product-atom cap.

### Results actually executed

- **347 independent matrix cases**: **309 applicable positive cases**, plus **38 negative controls**.
- Positive cases: **146 Fully supported**, **16 Partially supported**, **147 Unsupported** under the definitions below.
- **38/38 negative controls correctly rejected** for the target pathway.
- **197 generated reaction-site options** were exercised through matching, net-diagram and main-product run APIs. No incorrect main-product connectivity, conservation, exact main-product atom-link correspondence, or preview exception was found in this matrix.
- **35 generated SN/E mechanism options** also passed independent before/after atom/charge and electron-source endpoint checks.
- Existing suite rerun: **194 Python + 360 JavaScript tests passed (554 total)**. TypeScript `--noEmit` and `git diff --check` passed.
- Live desktop browser check found **overlapping atom labels in the six-unit polymer depiction**. Keyboard selection still linked the exact atom to 3D; no warning/error logs were captured in that temporary tab. This is a genuine rendering deficiency, separate from chemical connectivity.

**These are deliberately challenging, non-random tested-case counts—not percentages of all possible chemistry, and not proof of experimental applicability or universal correctness.**

**Recommendation:** improve existing ester hydrolysis/saponification coverage first (lactones and aryl esters), then preserve unaffected stereo/spectator groups through shared local compatibility checks. Do not add many new named reactions before reducing these cross-cutting exclusions.

## 2. Evidence and scoring method

### Code inspected

- [Public chemistry service](../server/chemistry_server.py): input resolution, condition vocabulary/assessment, match/run/diagram APIs, balanced stoichiometry and 3D generation.
- [Core structural engine](../server/reaction_engine.py), [additional rules](../server/extended_reaction_rules.py), [peroxyacid rule](../server/epoxidation_rule.py).
- [Functional-group graph helpers](../server/molecular_graph.py) and [inspection detector](../server/functional_groups.py).
- [Mapped net diagrams](../server/reaction_diagrams.py), [elementary mechanisms](../server/reaction_mechanisms.py), [stereo utilities](../server/stereochemistry.py).
- [Information registry](../server/reaction_information.py) and [deterministic reasoning](../server/reaction_reasoning.py).
- [Reaction Lab interface](../src/reaction-lab.ts), [styles](../src/reaction-lab.css), [mechanism panel](../src/pathway-insights.ts), [functional-group panel](../src/functional-group-panel.ts), [exact atom inspector](../src/atom-inspector.ts).
- Existing reaction, chemistry-depth, pathway-insight, preview, diagram, stoichiometry and frontend tests were read in addition to executing the complete existing suites.

The new [audit runner](../scripts/audit_reaction_lab.py) specifies expected structures independently as SMILES; it does **not** call production transformations to manufacture its expected products. It calls the public service functions used by the HTTP routes. Direct-transform feasibility probes are explicitly separate from matcher coverage scores.

### Reproduction

From the project directory:

```sh
.venv/bin/python scripts/audit_reaction_lab.py
.venv/bin/python scripts/audit_reaction_lab.py --json
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.mjs
node node_modules/typescript/bin/tsc --noEmit
git diff --check
```

The runner only prints observations; it does not write files or change application state. It uses RDKit **2026.03.6** in the existing virtual environment. The [JSON snapshot](reaction-lab-completeness-audit-results.json) preserves inputs, conditions, expected products, actual products, classifications, option counts, geometry notes, and audited production-file hashes.

### Classifications

- **Fully supported (F):** for that bounded test row, all independently expected main-product connectivities and required site options are generated; the serialized equation balances; mapped net preview and product run/linking succeed. Explicit SN2 inversion rows also require the independently expected isomeric product.
- **Partially supported (P):** net connectivity is produced, but a feature explicitly required by that row is missing (e.g. anti/cis/E/Z outcome or expected constitutional/site alternatives).
- **Unsupported (U):** the reaction is chemically applicable as a possible pathway, but input resolution, scope, reagent recognition, site matching or product bounds prevent it. Does **not** mean the molecules cannot react.
- **Correctly rejected (R):** a negative control lacks the target functional group, a necessary β-H, or the ordinary leaving-group/reactant requirements of that rule.
- **Incorrect result (I):** unexpected connectivity/coproduct, conservation, mechanism source/atom mapping, or specified SN2 inversion failure. **No such result was found in the automated chemical matrix.** The separately observed polymer display is partial end-to-end visualization support, not an incorrect molecular graph.

`score = F / (F + P + U) × 100%`. Negative controls are excluded. Mechanism absence is reported in its own column; it does not automatically reduce every non-SN/E net-reaction case to zero. Likewise, passing mapped-SVG generation is not a claim that every drawing is readable. Focused stereochemical probes are marked partial where connectivity alone is insufficient.

Positive cases mean **possible net transformations with a suitable stated model/reagent system**, not exclusive products, reaction rates or practical protocols. Ambiguous regio cases list constitutional possibilities without assuming their proportions. Amino/spectator-containing stress cases ask whether the selected site can be represented, not whether it reacts cleanly without protecting groups or acid/base speciation. Polymer scores concern the explicitly defined finite-chain graph model, not a verified bulk polymer synthesis.

Expected sets compare non-isomeric canonical connectivity except the two explicit SN2 inversion cases. Independent coproduct expectations are included for esterification, hydrolysis/saponification and finite oligomers. All generated options additionally receive conservation checks. Stereo tags in expectations of **rejected** stereo inputs are illustrative retained-identity expectations, not newly verified stereoproducts.

For all **16 partial stereo rows**, independent inspection of the actual returned product found one or more **unassigned potential stereo features** (recorded as `observedUnassignedStereoFeatures` in the JSON). These classifications are not inferred merely from a feature name or a missing documentation claim.

## 3. Complete pathway inventory and completeness scores

This is the complete current type inventory. Each type is tested with several structures; positional/site options are generated dynamically rather than listed as a finite set of molecule-specific rules.

Product accuracy statements below apply **only to generated audit cases**. The full per-case matrix at the end shows unsupported structures as well as successes.

| Reaction pathway | Structural coverage in code | Product accuracy observed | Mechanism support | Main limitations | Priority | Tested-case coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Hydrogenation | C/H isolated alkenes; branches, ≥5-member rings, separated sites and E/Z inputs; ≤80 explicit product atoms | 9 matched cases; expected main connectivity verified; see stereo caveats | No elementary model | Remote O/F/N, styrene/conjugation, any specified tetrahedral center | P2 | 9/14 = 64.3% |
| Bromination | Br₂; isolated C/H alkene, branches/rings/separated sites; unspecific C=C only | 7 matched cases; expected main connectivity verified; see stereo caveats | None | E/Z input rejected; anti/trans unassigned; remote heteroatoms/conjugation | P3 | 6/14 = 42.9% |
| Chlorination | Cl₂ counterpart of bromination, not a preset-only rule | 7 matched cases; expected main connectivity verified; see stereo caveats | None | Same stereo/spectator restrictions; F₂/I₂ are not equivalent reagents | P3 | 6/14 = 42.9% |
| Hydration | Water + acid profile; Markovnikov degree or end symmetry; branches/rings/multiple sites | 6 matched cases; expected main connectivity verified; see stereo caveats | None | Unequal internal ends with equal degree, rearrangement risks, E/Z/tetrahedral tags, remote groups | P3 | 6/14 = 42.9% |
| Hydrohalogenation | HCl/HBr/HI; same bounded alkene orientation; graph uses actual halogen | 8 matched cases; expected main connectivity verified; see stereo caveats | None | No peroxide route, ambiguous regio alternatives, stereo input or remote groups | P3 | 8/16 = 50.0% |
| Epoxidation | One peroxyacid including mCPBA; C/H isolated alkene; branches/rings/separated sites | 6 matched cases; expected main connectivity verified; see stereo caveats | None | E/Z/chiral input rejected; no stereospecific product or remote O; epoxide cannot re-enter current small-ring rules | P3 | 5/11 = 45.5% |
| SN2 | OH⁻ / recognized alkali hydroxide; methyl/primary/simple secondary C/H/Cl/Br/I; exocyclic rings; multiple sites | 8 matched cases; expected main connectivity verified; see stereo caveats | 1 concerted step; specified center inversion | No ring-bound center, allyl, remote O/F/N, other nucleophiles or severe neopentyl-type hindrance | P2 | 8/15 = 53.3% |
| SN1 | Water; acyclic tertiary or benzylic C/H/Cl/Br/I; multiple sites | 4 matched cases; expected main connectivity verified; see stereo caveats | 3 steps: carbocation, oxonium, solvent proton transfer | No secondary aliphatic, allylic or ring-bound center; no alcohol solvent, remote O/F/N, or specified center | P3 | 4/11 = 36.4% |
| E2 | OH⁻; acyclic halide with β-H; all distinct β constitutional options; multiple leaving sites | 6 matched cases; expected main connectivity verified; see stereo caveats | 1 concerted step; geometry utility not eligibility | No ring-bound center, specified centers or other bases; no conformer-gated outcome/E/Z | P3 | 4/13 = 30.8% |
| E1 | Water medium; tertiary/benzylic acyclic halide + β-H; several site options | 4 matched cases; expected main connectivity verified; see stereo caveats | 2 steps: ionization then coupled elimination | No secondary aliphatic, rings/allyl/remote groups/specified centers; no rearrangements/E/Z | P3 | 3/9 = 33.3% |
| Alcohol oxidation | Alkali hypochlorite; C/H/O primary/secondary alcohols, rings/aromatics/ethers/multiple OH sites | 8 matched cases; expected main connectivity verified; see stereo caveats | None; first-stage net equation | No C=C/C≡C, remote F/N or specified center; direct alcohol→acid not offered | P2 | 8/12 = 66.7% |
| Aldehyde oxidation | Alkali hypochlorite; C/H/O formyl group; aqueous + explicit Further stage; ring/aromatic/multiple sites | 7 matched cases; expected main connectivity verified; see stereo caveats | None; net oxidation stage | No unsaturation/remote F/N/specified center; neutral acid reporting, not actual protonation | P2 | 7/11 = 63.6% |
| Carbonyl hydrogenation | H₂/metal profile; C/H/O aldehydes and ketones; ring/aromatic/multiple carbonyls | 6 matched cases; expected main connectivity verified; see stereo caveats | None | No alkene/alkyne, remote F/N/stereo, NaBH₄/other reductants; not ester/amide reduction | P2 | 6/11 = 54.5% |
| Esterification | C/H/O acid × primary/secondary alcohol; branches/ring spectators/aromatics; Cartesian product of acid/OH sites | 7 matched cases; expected main connectivity verified; see stereo caveats | None; mapped acid OH + alcohol H→water | Specified stereo on either input, remote N/F, tertiary alcohol; no activated acid chemistry | P2 | 7/10 = 70.0% |
| Ester hydrolysis | Water/aqueous/acid; C/H/O acyclic ester acyl–O cut; branches, cyclic alkoxy spectator, aromatic acyl, diesters | 6 matched cases; expected main connectivity verified; see stereo caveats | None | Lactones explicitly blocked; aryl alkoxy excluded by sp³ detector; remote N/F/stereo | P1 | 6/10 = 60.0% |
| Alcohol dehydration | H₂SO₄ partner + acid/heat profile; saturated acyclic one-O alcohol with β-H; distinct β sites | 3 matched cases; expected main connectivity verified; see stereo caveats | None; net equation excludes acid | All cyclic/polyoxygen/benzylic/unsaturated/stereo inputs; rearrangement guard; only sulfuric acid | P2 | 2/8 = 25.0% |
| Alcohol substitution | HBr/HI for supported saturated acyclic one-O alcohol; HCl tertiary only; water coproduct | 5 matched cases; expected main connectivity verified; see stereo caveats | None; activation explained, not drawn | Cyclic, benzylic/polyoxygen/stereo; PBr₃/SOCl₂ activation absent; rearrangement-prone inputs | P2 | 5/11 = 45.5% |
| Ester saponification | OH⁻/alkali hydroxide; same ester sites; carboxylate + actual alcohol; full salt mass maintained | 7 matched cases; expected main connectivity verified; see stereo caveats | None | Same lactone/aryl-alkoxy/spectator/stereo gaps; main carboxylate intentionally 2D-only | P1 | 7/11 = 63.6% |
| Alkyne hydrogenation | 2 H₂/metal; C/H isolated acyclic C≡C; terminal/internal/branches/separated sites | 6 matched cases; expected main connectivity verified; see stereo caveats | None | Cyclic/conjugated, remote heteroatoms, aromatic neighbor or specified tetrahedral tag | P2 | 6/10 = 60.0% |
| Alkyne partial hydrogenation | 1 H₂/Lindlar; terminal C/H isolated acyclic C≡C only | 4 matched cases; expected main connectivity verified; see stereo caveats | None | Ordinary internal Lindlar cis product absent, cycles/conjugation/remote groups/stereo | P3 | 4/10 = 40.0% |
| Alkyne halogenation | Br₂/Cl₂; 1 equivalent→dihaloalkene; 2→tetrahaloalkane; bounded C/H sites | 13 matched cases; expected main connectivity verified; see stereo caveats | None | One-equivalent E/Z unassigned; cycles/conjugation/remote groups/stereo rejected | P3 | 6/21 = 28.6% |
| Alkyne hydrohalogenation | HCl/HBr/HI; 1→vinyl halide, 2→geminal dihalide; degree/symmetry orientation | 11 matched cases; expected main connectivity verified; see stereo caveats | None | Inequivalent internal orientations omitted; E/Z partial; cyclic/conjugated/remote groups, peroxide route | P3 | 10/21 = 47.6% |
| Alkene dihydroxylation | H₂O₂ + Os catalyst profile; isolated C/H alkene; branches/rings/separated sites | 5 matched cases; expected main connectivity verified; see stereo caveats | None; oxygen maps are net bookkeeping | Syn/cis unassigned, specified E/Z/tetrahedral rejected; no remote OH, styrene or NMO system | P3 | 4/11 = 36.4% |
| Polymerization model | Benzoyl peroxide; one isolated acyclic terminal C/H alkene; 2/4/6-unit two-chain combination model | 9 matched cases; expected main connectivity verified; see stereo caveats | None; no radical intermediates | Styrene/vinyl acetate/acrylonitrile excluded; larger selected oligomers hit 80-atom cap; crowded depiction | P4 | 9/21 = 42.9% |

### Individual model variants

Do not hide a weak one-equivalent or long-chain branch inside a stronger aggregate:

| Variant | Fully supported / applicable cases | Tested-case coverage |
| --- | --- | --- |
| Alkyne halogenation / 1 equivalent(s) | 0/11 | 0.0% |
| Alkyne halogenation / 2 equivalent(s) | 6/10 | 60.0% |
| Alkyne hydrohalogenation / 1 equivalent(s) | 5/11 | 45.5% |
| Alkyne hydrohalogenation / 2 equivalent(s) | 5/10 | 50.0% |
| Polymerization model / 2 monomers | 4/7 | 57.1% |
| Polymerization model / 4 monomers | 3/7 | 42.9% |
| Polymerization model / 6 monomers | 2/7 | 28.6% |

**Lowest aggregate:** alcohol dehydration, **2/8 = 25.0%**. **Lowest individual variant:** one-equivalent alkyne halogenation, **0/11 = 0.0%**: seven cases generated correct dihaloalkene connectivity but lacked the tested E/Z feature, and four were unsupported. Zero fully supported here does **not** mean its bond-edit rule never works.

### Catalog versus actual engine

The catalog endpoint exposes **19 example/site options covering 12 pathway types**, not every currently implemented type. The UI has **20 example cards**; the engine registry has **24 distinct types**. Pair matching reaches the newer pathways, including ones absent from the static catalog. Consequently, the standalone Calculators reaction selector is not currently a complete enumeration of Reaction Lab coverage. This is a verified discoverability/integration gap, not evidence that those newer graph rules are absent.

## 4. Structural, reagent and site behavior

### Shared restrictions versus chemical restrictions

1. **Input resolution:** custom structures must be connected, neutral, closed-shell, non-isotopic and use the resolver's element set. Exceptions normalize simple alkali hydroxides to OH⁻ and accept alkali hypochlorite salts. Arbitrary salts/nucleophiles are not generalizable through this resolver yet.
2. **Global engine filter:** substrates are limited to C/H/O/Cl/Br/I, with no formal charge, radical, isotope or query, and no ring smaller than five. This silently makes the resolver's broader N/F/Si/P/S acceptance ineffective for many reactions.
3. **Specified tetrahedral stereo:** `plan()` blocks **all** non-SN2 transformations when **any** substrate center is specified, including distant centers the selected reaction does not touch. Stereo-specified alcohol partners also fail esterification's reagent guard.
4. **Pathway-specific family filters:** alkene/alkyne and polymer models often require only C/H; oxygen chemistry only C/H/O; SN/E only C/H/Cl/Br/I. A remote ether, amine, F, or alcohol can therefore block a perfectly detected site.
5. **Product size:** the main product must contain at most **80 explicit atoms including H**. This is not an eight-/six-carbon whitelist, but ordinary longer chains and larger requested oligomers can still exceed it. The resolver checks drawn/heavy atoms first, so a molecule may enter but fail later with the generic “product failed validation” notice.
6. **Single-site net edits:** separated unsaturated sites, repeated acids/alcohols/esters/halides and multiple β positions generally produce separate options. They are not complete simultaneous conversion or chemoselectivity predictions.
7. **Constitutional equivalence:** β-carbon ranks deduplicate equivalent elimination positions at one leaving site; independent functional sites can remain separate even if their constitutional products are the same. This is legitimate site provenance, not necessarily duplicate chemistry.
8. **Rearrangement/conjugation exclusions:** conservative rather than statements of nonreactivity. Markovnikov ambiguity, potential shifts, allylic resonance and ring conformations deserve their own chemistry models, unlike many remote-spectator exclusions.

Genuine ordinary-chemistry exclusions include tertiary-carbon SN2, aryl/vinyl SN2, ordinary fluoride as leaving group, oxidation of tertiary alcohol into a simple carbonyl, ester-only rules applied to amides, and dehydration/elimination without an appropriate β-H. Do **not** remove these just to improve scores. [SN2 substrate/leaving-group reference](https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction), [alcohol oxidation reference](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols).

### Supported ordinary structures actually tested

Longer and branched chains are not generally tied to sample names: dodecene hydrogenation, heptanol oxidation, branched acid/alcohol esterification, cyclic ketone reduction, cyclic alkoxy ester hydrolysis, alkali hypochlorite identities, iodoalkane substitution, separated multiple double/triple bonds, diols/diesters, and distinct elimination products all worked within their family guards.

Exocyclic ring-containing halides can work (cyclohexylmethyl SN2), whereas **ring-bound** leaving groups do not. Cyclic alkenes work for several additions, while cyclic alcohol dehydration and cyclic halide SN/E do not. Carbonyl and acid rules tolerate aromatic spectators; styrene is excluded from isolated-alkene and polymer rules. These differences are caused by specific filters, not “all rings unsupported.”

### Functional-group inspection is broader than reaction matching

The inspection detector recognizes alkenes, alkynes, SP³ alcohols, aldehydes (including formaldehyde), ketones, acids, esters, amines, amides, haloalkanes, peroxyacids and aromatic rings. It recognizes a phenyl ester and a lactone even though the reaction matcher rejects their hydrolysis. It also recognizes alkene + alcohol together in a remote-OH substrate.

The displayed group suggestions are **not reaction approval**; their caveat is correct. However, two independent detector systems (`functional_groups.PATTERNS` versus `molecular_graph.find_*`) explain why “ester found” can lead to “no supported pathway.” Centralize the scope explanation rather than incorrectly reporting that the ester was absent.

### Reagents and conditions

| Pathway set | Recognized consumed partner | Condition treatment | Important missing ordinary alternatives |
| --- | --- | --- | --- |
| SN2 / E2 | OH⁻ or simple alkali hydroxide | Solvent/heat are illustrative fit labels | Alkoxide, iodide, thiolate, amine nucleophiles; bulky bases; appropriate sulfonate leaving groups |
| SN1 / E1 | Water (E1 medium, excluded from net equation) | Aqueous protic and ambient/heated profiles | Alcohol trapping solvents; broader secondary/allylic and activated leaving groups |
| Alkene/alkyne reduction | H₂ | Metal or Lindlar profile | Other selective reduction systems; internal Lindlar products |
| Halogen/HX addition | Br₂, Cl₂, HCl, HBr, HI | Dry and/or one/two-equivalent model | Peroxide HBr, halohydrin/media-specific competition |
| Carbonyl reduction | H₂ | Generic suitable-metal profile | NaBH₄, LiAlH₄ and their proper multistep/work-up models |
| Alcohol/aldehyde oxidation | Alkali hypochlorite | Aqueous profile; aldehyde additionally needs explicit Further stage + water medium | Other oxidants/protocols, acid/base speciation and side reactions |
| Esterification / hydrolysis | Alcohol / water | Acid profile (hydrolysis also aqueous) | Other activated acyl transformations; ordinary lactone/aryl ester sites |
| Saponification | OH⁻ / alkali hydroxide | Aqueous profile | Other bases, broader salts; no acid work-up assumed |
| Alcohol dehydration | H₂SO₄ partner | Acid + heat profile; acid not consumed | H₃PO₄/other acid systems, cyclic/polyoxygen substrates |
| Alcohol substitution | HBr/HI; tertiary HCl | Heat/ambient by degree; OH activation explained | PBr₃, SOCl₂/ZnCl₂ systems; fuller protonation/departure model |
| Dihydroxylation | H₂O₂ + Os activation choice | Catalyst fit label | Other co-oxidants such as NMO; syn products |
| Finite chain | Benzoyl peroxide | Radical initiation + heat + 2/4/6 choice | Styrene, vinyl acetate and acrylonitrile within a safe finite model |

Alternative reagents are **not automatically interchangeable**: e.g. a borohydride reduction needs its own atom inventory and work-up, and a bulky-base E2 rule must not copy hydroxide selectivity. Missing these is reagent coverage, not an error in the existing hydroxide rule.

## 5. Biggest gaps, separated by category

### A. Structural coverage

**Highest cross-cutting impact:** whole-molecule element and specified-stereo filters instead of local reaction-site compatibility and explicit spectator preservation. Rejected cases include remote OH alkene/alkyne substrates, fluoro spectators, amino-functional carbonyl/ester substrates and unaffected remote chiral centers.

**Ordinary cyclic/aryl ester examples:** γ-butyrolactone and phenyl acetate should have valid hydrolysis/saponification pathways under appropriate models. These are software exclusions, not a chemistry prohibition. Lactone applicability is explicitly discussed in the [ester reference](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters).

**Alcohol dehydration:** only saturated, acyclic, one-O substrates. Cycloheptanol and a remote ether/second OH fail despite ordinary selected-site chemistry being possible.

**SN/E rings and allyl:** real geometry/resonance considerations exist; expanding them needs more than deleting every guard. Plain ring-bound secondary SN2 and accessible trans-diaxial E2 are narrower feasible additions than arbitrary polycyclic systems.

### B. Product generation

No chemically wrong generated main graph was found in the tested matrix. Nonetheless:

- Correct atom balance/sanitization is necessary, not sufficient proof of reaction selectivity or actual accessibility.
- Connected lactone-opening and aryl-ester products are currently blocked **before** generation, not impossible for the edit engine.
- The size cap suppresses ordinary large products and some selectable 4/6-unit models. The UI should distinguish size bounds from invalid chemistry.
- Regio-ambiguous HX/hydration gives no options instead of displaying carefully bounded alternatives.
- Most newly created stereocenters/E/Z possibilities are not assigned.
- Saponification correctly remains an anion; adding a neutral acid without a separate work-up would be chemically wrong.

### C. Reagents and conditions

**Verified condition inconsistency:** supplying `catalyst: none` still returns and allows preview/run of hydrogenation, hydration and Os dihydroxylation; assessments become `alternative` / “Unfavorable.” This is deliberate comparison behavior, not silent catalyst recognition. But “it may still compete” is too permissive for a model whose required activation system is absent. Separate **required activation unavailable**, **unknown conditions**, and **competing solvent/temperature preference** in a future change.

Conversely aldehyde oxidation is hard-gated by `oxidationStage=further` and aqueous medium. The gate is a defined-model requirement, not a claim that all other aldehyde oxidation chemistry is impossible. The supplementary probes preserve these exact observations.

The `Metal (Pd/Pt)` UI option is too generic to validate actual carbonyl/arene chemoselectivity or reaction pressure. It must remain illustrative. Oxidant stage labels and neutral acid reporting are not pH/kinetic predictions.

### D. Mechanisms

Exactly **four of the 24 types** have reusable elementary-step data/visualization:

| Mechanism | Actual model | Verified | Missing |
| --- | --- | --- | --- |
| SN2 | One concerted attack/departure state | Exact oxygen source, C destination, forming/breaking bond, specified-center inversion | Transition-state geometry, general nucleophiles/activation, automatic curved arrows |
| E2 | One concerted base attack / C–H→π / C–X departure state | Real selected β-H, three coupled electron moves, no invented intermediate | Conformer search/gated geometry and stereoproducts |
| SN1 | Ionization → water capture → separate solvent-water deprotonation | Carbocation and oxonium; explicit proton transfer; hydronium/halide aqueous explanation | Rearrangements, racemization ratios, general solvent/nucleophile scope |
| E1 | Ionization → coupled β-H abstraction and π formation | Carbocation, water base and mapped proton transfer | Rearrangements, ring scope and E/Z outcomes |

The mechanism ends at the same mapped main product as the net equation. In SN1/E1, an extra water appears in elementary proton transfer only; the net equation reports HX while the aqueous elementary states show hydronium + halide. This convention is disclosed rather than quietly consuming extra solvent in the reaction calculator.

The **other 20 types have net bond changes and explanatory data, not an elementary mechanism**. They do not fabricate one. Highest-value next mechanism family is nucleophilic acyl substitution (acid hydrolysis/saponification, then esterification), with tetrahedral intermediates and separate proton transfers. [Ester mechanism reference](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters).

### E. Stereochemistry

Implemented foundations are real, but only one reaction uses a specified stereochemical outcome:

- RDKit potential tetrahedral-center inspection and accurate CIP assignment for specified centers.
- Potential/specified double-bond E/Z; H/H-reference cis/trans only, not general ring relationships.
- Atom-map numbers removed before CIP priority assignment.
- Physical SN2 inversion with neighbor-order parity and re-evaluation of CIP, **not** a blind R↔S letter swap. Both independently expected enantiomer test rows worked.
- H–Cβ–Cα–X dihedral measurement and anti-periplanar flag from one **actual supplied/generated reactant conformer**; degenerate/2D inputs rejected.

Missing: preserving unaffected specified centers across non-SN2 rules, conformer-aware E2 products, cyclohexane trans-diaxial treatment, anti halogen addition, syn dihydroxylation/epoxidation, internal Lindlar cis products, broader ring stereo and any stereoisomer ratios. The current E2 conformer utility does not influence eligibility or the product stereochemistry.

These are different chemistry constraints: [E2 geometry](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect), [anti halogen addition](https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2), [syn oxidation chemistry](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation), [Lindlar cis reduction](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes).

### F. Visualization

- **Verified good:** conserved explicit-H map identities, main-product atom-index linkage, bond-change metadata, real keyboard-selectable targets, and safe SVG ingestion. The rerun regression suite includes bond highlights stopping short of labels and hover/pointer state tests.
- **Verified bad:** six-unit ethylene polymer output packs seven reactant species into an 800-wide drawing and three product cells with fixed 24-unit atom labels. Benzoyl peroxide and the 58-atom oligomer visibly overlap. Matching/mapping tests cannot detect this. The browser trial is **Partially supported visually**, separate from its fully supported net-graph matrix row.
- **Intentional limitation:** 3D is the main final product only. Byproducts, ionic products and charged intermediates do not all become linked 3D molecules. This is disclosed.
- **Potential risk, not fully browser-tested:** explicit-H large structures and mechanisms at fixed cell/font sizes may crowd in other reactions too. Convergence and exact mapping do not prove label readability.
- This audit did not perform a fresh exhaustive mobile or hover-smoothness sweep. Do not infer full 320px or touch performance from the desktop check.

![Observed overlapping labels in the six-unit polymer model](reaction-lab-audit-polymer-6.png)

## 6. Isolated feasibility probes (not implemented changes)

The existing `transform()` was invoked directly with independently selected lactone/aryl ester indices in an isolated process, **without modifying matching or scope guards**. Atom/charge/valence product validation succeeded:

| Existing transform | Substrate | Actual validated products |
| --- | --- | --- |
| Ester hydrolysis | γ-Butyrolactone (`O=C1OCCC1`) | Connected hydroxy acid `O=C(O)CCCO` |
| Ester saponification | Same lactone | Connected hydroxy carboxylate `O=C([O-])CCCO` |
| Ester hydrolysis | Phenyl acetate (`CC(=O)Oc1ccccc1`) | `CC(=O)O` + `Oc1ccccc1` |
| Ester saponification | Same aryl ester | `CC(=O)[O-]` + `Oc1ccccc1` |

**Verified inference:** the public rejection is in candidate/detector scope, not an inherent inability to generate those particular product graphs. Future public/API/stereo/display tests are still required before enabling them. This is evidence for a feasible next increment, not a hidden production fix.

## 7. Ranked recommendations and direct answers

| Rank | Work | Why / feasibility | What not to do |
| --- | --- | --- | --- |
| 1 | Generalize current ester hydrolysis + saponification to lactones and aryl esters; retain acid/base distinction | Two existing types gain ordinary cyclic/aromatic coverage; direct edit feasibility verified | Do not invent neutral acid work-up or require two disconnected products |
| 2 | Shared reaction-local spectator/stereo-preservation contract; precise exclusion reasons | Broadest reusable improvement; distant safe centers/groups currently block many types | Do not remove element/stereo filters without checking atom provenance, local compatibility and unchanged stereo |
| 3 | Expand bounded cyclic alcohol dehydration/substitution and appropriate acid/activation choices | Dehydration has the lowest aggregate matrix score; common structures are rejected | Do not bypass rearrangement/activation chemistry or assume OH is a leaving group |
| 4 | Internal-alkyne Lindlar cis generation, syn/anti addition stereochemistry, then conformer-aware E2 | Stereo groundwork exists; expands ordinary university examples | Do not assign configurations from a random optimized product shape |
| 5 | Reusable acyl elementary mechanisms; additional selected mechanisms afterward | Twenty current types lack mechanisms; existing step API can be reused | Do not interpret a net O/H bookkeeping map as catalyst-cycle atom provenance |
| 6 | Explicit reagent roles/required-condition handling; selected additional nucleophiles and bases | Useful substitution/reduction breadth, coherent fit labels | Do not reuse OH⁻ net stoichiometry for a different reagent |
| 7 | Adaptive diagram cell/font layout and selectable-size bounds; fuller catalog enumeration | Verified rendering/discovery issues; keep the outer page layout unchanged | Do not redesign pages or equate unreadable SVG with missing molecule data |

1. **Which existing reaction first?** Ester hydrolysis/saponification as one closely related increment. It has a demonstrated scope-only fix for useful ordinary examples and a strong basis for future mechanisms.
2. **Most unnecessary restrictions?** Those two ester rules' lactone/aryl-alkoxy exclusions are most clearly demonstrated as unnecessary software barriers. Alcohol dehydration has the broadest very restrictive structural contract (acyclic, saturated, one O), but some activation/rearrangement checks are genuine chemistry.
3. **Lowest measured coverage?** Alcohol dehydration **25.0%** by type; one-equivalent alkyne halogenation **0.0% fully supported** by variant, with correct connectivity in seven partial cases.
4. **Capability with greatest cross-pathway benefit?** Shared site-local compatibility plus retention/revalidation of unaffected stereo and spectators. Better reagent-role parsing is the next broad capability.
5. **Already sufficiently generalized for the current bounded scope?** Esterification, simple primary/secondary alcohol oxidation, aqueous aldehyde net oxidation, ordinary aldehyde/ketone H₂ reduction, isolated alkene H₂ reduction and complete isolated acyclic alkyne reduction. They work beyond presets with branches, longer chains and often multiple sites. They are sufficient **only within** the stated element/stereo/reagent boundaries—not complete reaction families.
6. **Postpone:** unrestricted reaction prediction, arbitrary simultaneous chemoselectivity, general carbocation rearrangement networks, quantitative stereoisomer ratios/kinetics/energies, conformationally complex polycycles, catalytic-cycle metal coordination, full radical-polymer distributions/tacticity and enzyme mechanisms. Acid–amine chemistry remains later and must separate ammonium carboxylate salt from activated amidation.

## 8. Recommended next implementation phase (proposal only)

**Phase: broader ester transformations and reusable unchanged-structure guarantees.**

1. Reuse/align ester inspection and engine site definitions while continuing to exclude carbonate/amide false matches.
2. Enable selected ordinary lactone opening and aryl-alkoxy cleavage via the existing mapped edit; allow one connected hydroxy acid/carboxylate or multiple fragments as appropriate.
3. Preserve remote stereo through atom mapping and verify retained center configuration/CIP changes independently; do not guess newly created configurations.
4. Add multiple-ring sizes, phenyl/naphthyl esters, branched acyl/alkoxy groups, separated ester sites and two input orders to public match/diagram/run/stoichiometry tests.
5. Keep base product ionic and distinguish any later acid work-up. Ensure information-only/2D-only behavior is honest.
6. Add acid/base acyl-substitution mechanism data using the existing mechanism panel after net products are verified.
7. Fix drawing readability locally without changing the page layout, and rerun this audit plus all existing tests.

No part of this proposed phase was implemented in this audit.

## 9. Uncertainty and boundaries of this report

- Matrix coverage is a **chosen stress-test sample**, not random population sampling. Scores depend on including challenging spectator/stereo/reagent variants. They cannot be extrapolated to all molecular chemistry or compared directly with an earlier easier matrix.
- No experimental reactions, yields, temperature thresholds, rate constants or toxicity/safety outcomes were verified.
- PubChem live lookup/isomer-search coverage was not benchmarked here; known SMILES isolate reaction behavior from network/search failures.
- Multiple functional groups do not imply every competing reaction is modeled. The proposed “applicable” examples are possible selected-site transformations, not clean isolated-product promises.
- No incorrect chemical matrix result was observed; this does not rule out errors outside the tested sample, and a passing sanitization/conservation check is not sufficient chemical proof.
- Existing tests deliberately assert some exclusions. A future intended expansion will need to revise those specific scope assertions without weakening genuine chemistry/identity/mapping regressions.
- The six-unit browser example verifies a visualization problem, not the readability of every pathway at every viewport. User's original open tab/draft was not edited; the separate diagnostic tab was closed.
- Production hashes in the JSON are working-tree fingerprints, not a claim that the repository has no pre-existing uncommitted changes.

## 10. Chemistry references used for applicability review

The report's implementation findings come from local code/tests; external references support chemical restrictions and missing outcome features, not software coverage percentages.

- [SN2 scope, nucleophiles and leaving groups](https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction).
- [SN1 carbocation/solvent scope](https://openstax.org/books/organic-chemistry/pages/11-5-characteristics-of-the-sn1-reaction).
- [E1 chemistry](https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions).
- [E2 geometry](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect).
- [Alcohol reactions](https://openstax.org/books/organic-chemistry/pages/17-6-reactions-of-alcohols), [alcohol oxidation](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols), [aldehyde oxidation](https://openstax.org/books/organic-chemistry/pages/19-3-oxidation-of-aldehydes-and-ketones).
- [Ester and lactone chemistry](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters).
- [Alkene anti halogenation](https://openstax.org/books/organic-chemistry/pages/8-2-halogenation-of-alkenes-addition-of-x2).
- [Epoxidation / syn dihydroxylation](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation).
- [Alkyne HX/X₂ chemistry](https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2), [Lindlar reduction](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes).
- [Finite radical chain-growth reasoning and vinyl monomers](https://openstax.org/books/organic-chemistry/pages/8-10-radical-additions-to-alkenes-chain-growth-polymers).

The code's H₂O₂/Os research citation was blocked by a PubMed browser challenge during this audit; the specific paper was **not verified**, and no claim is made that it validates all of this code's selected catalytic conditions.

## 11. Complete executed matrix

Codes: **F** fully supported bounded net row; **P** partial required feature; **U** applicable but unsupported; **R** correctly rejected negative; **I** incorrect result (none in chemical matrix). Each case ID identifies the JSON observation and runner input.

“Expected” lists independent main-product **connectivity**; multiple listed products are constitutional alternatives, not amounts or ratios. Coproducts, model variants, minimum site counts, conditions and full returned notes are in the JSON. Notes returned by matching are pair-wide; they can refer to another candidate (e.g. E2 rejected while SN2 works). They must not automatically be attributed to the chosen successful pathway.

The table's expected connectivity for a U case does not imply that its stereo outcome is implemented. “3D verified” means the main-product run produced a model with exact link correspondence; it is not proof of the correct stereoisomer, readable labels, or measured geometry.

### Hydrogenation

9/14 fully supported applicable cases (64.3%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A001 · simple terminal: 1-pentene | `C=CCCC` + `hydrogen` | `CCCCC` | `CCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A002 · longer terminal: 1-dodecene | `C=CCCCCCCCCCC` + `hydrogen` | `CCCCCCCCCCCC` | `CCCCCCCCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A003 · branched: 2-methyl-1-pentene | `C=C(C)CCC` + `hydrogen` | `CC(C)CCC` | `CCCC(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A004 · symmetric internal: 3-hexene | `CCC=CCC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A005 · cyclic: cycloheptene | `C1=CCCCCC1` + `hydrogen` | `C1CCCCCC1` | `C1CCCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A006 · position/regio ambiguity: 2-hexene | `CC=CCCC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A007 · specified E isomer: E-3-hexene | `CC/C=C/CC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A008 · specified Z isomer: Z-3-hexene | `CC/C=C\CC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A009 · aromatic conjugation: styrene | `C=Cc1ccccc1` + `hydrogen` | `CCc1ccccc1` | None; 0 option(s) | **U** | Conjugated or heteroatom-substituted alkenes need additional selectivity rules. |
| A010 · remote OH: 4-penten-1-ol | `C=CCCCO` + `hydrogen` | `CCCCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A011 · remote F: 5-fluoro-1-pentene | `C=CCCCF` + `hydrogen` | `CCCCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A012 · remote chiral center | `C=CC[C@H](C)CC` + `hydrogen` | `CCC[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A013 · size boundary: 1-triacontene | `C=CCCCCCCCCCCCCCCCCCCCCCCCCCCCC` + `hydrogen` | `CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A014 · two separated C=C sites: 1,7-octadiene | `C=CCCCCC=C` + `hydrogen` | `C=CCCCCCC` | `C=CCCCCCC`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A015 · negative: saturated pentane | `CCCCC` + `hydrogen` | No target pathway | None; 0 option(s) | **R** |  |
| A076 · negative: aromatic benzene (ordinary alkene rule) | `c1ccccc1` + `hydrogen` | No target pathway | None; 0 option(s) | **R** |  |

### Bromination

6/14 fully supported applicable cases (42.9%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A016 · simple terminal: 1-pentene | `C=CCCC` + `bromine` | `BrCC(Br)CCC` | `CCCC(Br)CBr`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A017 · longer terminal: 1-dodecene | `C=CCCCCCCCCCC` + `bromine` | `BrCC(Br)CCCCCCCCCC` | `CCCCCCCCCCC(Br)CBr`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A018 · branched: 2-methyl-1-pentene | `C=C(C)CCC` + `bromine` | `BrCC(Br)(C)CCC` | `CCCC(C)(Br)CBr`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A019 · symmetric internal: 3-hexene | `CCC=CCC` + `bromine` | `CCC(Br)C(Br)CC` | `CCC(Br)C(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A020 · cyclic: cycloheptene | `C1=CCCCCC1` + `bromine` | `BrC1C(Br)CCCCC1` | `BrC1CCCCCC1Br`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Anti/trans stereochemical outcome is unassigned. |
| A021 · position/regio ambiguity: 2-hexene | `CC=CCCC` + `bromine` | `CC(Br)C(Br)CCC` | `CCCC(Br)C(C)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A022 · specified E isomer: E-3-hexene | `CC/C=C/CC` + `bromine` | `CCC(Br)C(Br)CC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A023 · specified Z isomer: Z-3-hexene | `CC/C=C\CC` + `bromine` | `CCC(Br)C(Br)CC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A024 · aromatic conjugation: styrene | `C=Cc1ccccc1` + `bromine` | `BrCC(Br)c1ccccc1` | None; 0 option(s) | **U** | Conjugated or heteroatom-substituted alkenes need additional selectivity rules. |
| A025 · remote OH: 4-penten-1-ol | `C=CCCCO` + `bromine` | `BrCC(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A026 · remote F: 5-fluoro-1-pentene | `C=CCCCF` + `bromine` | `BrCC(Br)CCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A027 · remote chiral center | `C=CC[C@H](C)CC` + `bromine` | `BrCC(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A028 · size boundary: 1-triacontene | `C=CCCCCCCCCCCCCCCCCCCCCCCCCCCCC` + `bromine` | `BrCC(Br)CCCCCCCCCCCCCCCCCCCCCCCCCCCC` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A029 · two separated C=C sites: 1,7-octadiene | `C=CCCCCC=C` + `bromine` | `BrCC(Br)CCCCC=C` | `C=CCCCCC(Br)CBr`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A030 · negative: saturated pentane | `CCCCC` + `bromine` | No target pathway | None; 0 option(s) | **R** |  |
| A079 · negative: iodine substituted for bromine | `C=CCCC` + `II` | No target pathway | None; 0 option(s) | **R** |  |

### Chlorination

6/14 fully supported applicable cases (42.9%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A031 · simple terminal: 1-pentene | `C=CCCC` + `chlorine` | `ClCC(Cl)CCC` | `CCCC(Cl)CCl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A032 · longer terminal: 1-dodecene | `C=CCCCCCCCCCC` + `chlorine` | `ClCC(Cl)CCCCCCCCCC` | `CCCCCCCCCCC(Cl)CCl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A033 · branched: 2-methyl-1-pentene | `C=C(C)CCC` + `chlorine` | `ClCC(Cl)(C)CCC` | `CCCC(C)(Cl)CCl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A034 · symmetric internal: 3-hexene | `CCC=CCC` + `chlorine` | `CCC(Cl)C(Cl)CC` | `CCC(Cl)C(Cl)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A035 · cyclic: cycloheptene | `C1=CCCCCC1` + `chlorine` | `ClC1C(Cl)CCCCC1` | `ClC1CCCCCC1Cl`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Anti/trans stereochemical outcome is unassigned. |
| A036 · position/regio ambiguity: 2-hexene | `CC=CCCC` + `chlorine` | `CC(Cl)C(Cl)CCC` | `CCCC(Cl)C(C)Cl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A037 · specified E isomer: E-3-hexene | `CC/C=C/CC` + `chlorine` | `CCC(Cl)C(Cl)CC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A038 · specified Z isomer: Z-3-hexene | `CC/C=C\CC` + `chlorine` | `CCC(Cl)C(Cl)CC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A039 · aromatic conjugation: styrene | `C=Cc1ccccc1` + `chlorine` | `ClCC(Cl)c1ccccc1` | None; 0 option(s) | **U** | Conjugated or heteroatom-substituted alkenes need additional selectivity rules. |
| A040 · remote OH: 4-penten-1-ol | `C=CCCCO` + `chlorine` | `ClCC(Cl)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A041 · remote F: 5-fluoro-1-pentene | `C=CCCCF` + `chlorine` | `ClCC(Cl)CCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A042 · remote chiral center | `C=CC[C@H](C)CC` + `chlorine` | `ClCC(Cl)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A043 · size boundary: 1-triacontene | `C=CCCCCCCCCCCCCCCCCCCCCCCCCCCCC` + `chlorine` | `ClCC(Cl)CCCCCCCCCCCCCCCCCCCCCCCCCCCC` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A044 · two separated C=C sites: 1,7-octadiene | `C=CCCCCC=C` + `chlorine` | `ClCC(Cl)CCCCC=C` | `C=CCCCCC(Cl)CCl`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A045 · negative: saturated pentane | `CCCCC` + `chlorine` | No target pathway | None; 0 option(s) | **R** |  |

### Hydration

6/14 fully supported applicable cases (42.9%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A061 · simple terminal: 1-pentene | `C=CCCC` + `water` | `CC(O)CCC` | `CCCC(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A062 · longer terminal: 1-dodecene | `C=CCCCCCCCCCC` + `water` | `CC(O)CCCCCCCCCC` | `CCCCCCCCCCC(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A063 · branched: 2-methyl-1-pentene | `C=C(C)CCC` + `water` | `CC(O)(C)CCC` | `CCCC(C)(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A064 · symmetric internal: 3-hexene | `CCC=CCC` + `water` | `CCC(O)CCC` | `CCCC(O)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A065 · cyclic: cycloheptene | `C1=CCCCCC1` + `water` | `OC1CCCCCC1` | `OC1CCCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A066 · position/regio ambiguity: 2-hexene | `CC=CCCC` + `water` | `CC(O)CCCC` / `CCC(O)CCC` | None; 0 option(s) | **U** | Equal alkene substitution with inequivalent ends: regioselectivity is ambiguous; no orientation selected. |
| A067 · specified E isomer: E-3-hexene | `CC/C=C/CC` + `water` | `CCC(O)CCC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A068 · specified Z isomer: Z-3-hexene | `CC/C=C\CC` + `water` | `CCC(O)CCC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A069 · aromatic conjugation: styrene | `C=Cc1ccccc1` + `water` | `CC(O)c1ccccc1` | None; 0 option(s) | **U** | Conjugated or heteroatom-substituted alkenes need additional selectivity rules. |
| A070 · remote OH: 4-penten-1-ol | `C=CCCCO` + `water` | `CC(O)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A071 · remote F: 5-fluoro-1-pentene | `C=CCCCF` + `water` | `CC(O)CCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A072 · remote chiral center | `C=CC[C@H](C)CC` + `water` | `CC(O)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A073 · size boundary: 1-triacontene | `C=CCCCCCCCCCCCCCCCCCCCCCCCCCCCC` + `water` | `CC(O)CCCCCCCCCCCCCCCCCCCCCCCCCCCC` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A074 · two separated C=C sites: 1,7-octadiene | `C=CCCCCC=C` + `water` | `CC(O)CCCCC=C` | `C=CCCCCC(C)O`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A075 · negative: saturated pentane | `CCCCC` + `water` | No target pathway | None; 0 option(s) | **R** |  |

### Hydrohalogenation

8/16 fully supported applicable cases (50.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A046 · simple terminal: 1-pentene | `C=CCCC` + `hydrogen-bromide` | `CC(Br)CCC` | `CCCC(C)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A047 · longer terminal: 1-dodecene | `C=CCCCCCCCCCC` + `hydrogen-bromide` | `CC(Br)CCCCCCCCCC` | `CCCCCCCCCCC(C)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A048 · branched: 2-methyl-1-pentene | `C=C(C)CCC` + `hydrogen-bromide` | `CC(Br)(C)CCC` | `CCCC(C)(C)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A049 · symmetric internal: 3-hexene | `CCC=CCC` + `hydrogen-bromide` | `CCC(Br)CCC` | `CCCC(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A050 · cyclic: cycloheptene | `C1=CCCCCC1` + `hydrogen-bromide` | `BrC1CCCCCC1` | `BrC1CCCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A051 · position/regio ambiguity: 2-hexene | `CC=CCCC` + `hydrogen-bromide` | `CC(Br)CCCC` / `CCC(Br)CCC` | None; 0 option(s) | **U** | Equal alkene substitution with inequivalent ends: regioselectivity is ambiguous; no orientation selected. |
| A052 · specified E isomer: E-3-hexene | `CC/C=C/CC` + `hydrogen-bromide` | `CCC(Br)CCC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A053 · specified Z isomer: Z-3-hexene | `CC/C=C\CC` + `hydrogen-bromide` | `CCC(Br)CCC` | None; 0 option(s) | **U** | Specified alkene stereochemistry is supported only when hydrogenation removes it. |
| A054 · aromatic conjugation: styrene | `C=Cc1ccccc1` + `hydrogen-bromide` | `CC(Br)c1ccccc1` | None; 0 option(s) | **U** | Conjugated or heteroatom-substituted alkenes need additional selectivity rules. |
| A055 · remote OH: 4-penten-1-ol | `C=CCCCO` + `hydrogen-bromide` | `CC(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A056 · remote F: 5-fluoro-1-pentene | `C=CCCCF` + `hydrogen-bromide` | `CC(Br)CCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A057 · remote chiral center | `C=CC[C@H](C)CC` + `hydrogen-bromide` | `CC(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A058 · size boundary: 1-triacontene | `C=CCCCCCCCCCCCCCCCCCCCCCCCCCCCC` + `hydrogen-bromide` | `CC(Br)CCCCCCCCCCCCCCCCCCCCCCCCCCCC` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A059 · two separated C=C sites: 1,7-octadiene | `C=CCCCCC=C` + `hydrogen-bromide` | `CC(Br)CCCCC=C` | `C=CCCCCC(C)Br`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A060 · negative: saturated pentane | `CCCCC` + `hydrogen-bromide` | No target pathway | None; 0 option(s) | **R** |  |
| A077 · actual reagent: hydrogen-chloride | `C=CCCC` + `hydrogen-chloride` | `CC(Cl)CCC` | `CCCC(C)Cl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A078 · actual reagent: hydrogen-iodide | `C=CCCC` + `hydrogen-iodide` | `CC(I)CCC` | `CCCC(C)I`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |

### Epoxidation

5/11 fully supported applicable cases (45.5%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A231 · long terminal | `C=CCCCCCC` + `peracetic-acid` | `CCCCCCC1CO1` | `CCCCCCC1CO1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A232 · branched terminal | `C=C(C)CCC` + `peracetic-acid` | `CCCC1(C)CO1` | `CCCC1(C)CO1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A233 · internal alkene | `CCC=CCC` + `peracetic-acid` | `CCC1OC1CC` | `CCC1OC1CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A234 · cyclic cycloheptene | `C1=CCCCCC1` + `peracetic-acid` | `C1CCC2OC2CC1` | `C1CCC2OC2CC1`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Syn/cis outcome is unassigned. |
| A235 · remote OH | `C=CCCCO` + `peracetic-acid` | `OCCCC1CO1` | None; 0 option(s) | **U** | Epoxidation currently supports hydrocarbon alkenes; chemoselectivity with other functional groups is not evaluated. |
| A236 · aromatic conjugation | `C=Cc1ccccc1` + `peracetic-acid` | `c1ccccc1C1CO1` | None; 0 option(s) | **U** | Epoxidation of conjugated or heteroatom-substituted alkenes needs additional selectivity rules. |
| A237 · specified E alkene | `CC/C=C/CC` + `peracetic-acid` | `CCC1OC1CC` | None; 0 option(s) | **U** | Stereospecific epoxidation of an E/Z-specified alkene is not implemented; no stereoisomer is guessed. |
| A238 · specified Z alkene | `CC/C=C\CC` + `peracetic-acid` | `CCC1OC1CC` | None; 0 option(s) | **U** | Stereospecific epoxidation of an E/Z-specified alkene is not implemented; no stereoisomer is guessed. |
| A239 · remote stereocenter | `C=CC[C@H](C)CC` + `peracetic-acid` | `CC[C@H](C)CC1CO1` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A240 · two separated C=C sites | `C=CCCCCC=C` + `peracetic-acid` | `C=CCCCCC1CO1` | `C=CCCCCC1CO1`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A241 · negative: saturated alcohol | `CCCCO` + `peracetic-acid` | No target pathway | None; 0 option(s) | **R** | Epoxidation currently supports hydrocarbon alkenes; chemoselectivity with other functional groups is not evaluated. |
| A253 · actual peroxyacid: mCPBA | `C=CCCC` + `O=C(OO)c1cccc(Cl)c1` | `CCCC1CO1` | `CCCC1CO1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A254 · negative: peroxide alone | `C=CCCC` + `hydrogen-peroxide` | No target pathway | None; 0 option(s) | **R** |  |

### SN2

8/15 fully supported applicable cases (53.3%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A153 · long primary | `CCCCCCCCCI` + `hydroxide` | `CCCCCCCCCO` | `CCCCCCCCCO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A154 · branched primary | `CCC(C)CBr` + `hydroxide` | `CCC(C)CO` | `CCC(C)CO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A155 · secondary | `CCCC(Br)CCC` + `hydroxide` | `CCCC(O)CCC` | `CCCC(O)CCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A156 · benzyl | `COc1ccc(CBr)cc1` + `hydroxide` | `COc1ccc(CO)cc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A157 · cyclohexylmethyl (exocyclic) | `BrCC1CCCCC1` + `hydroxide` | `OCC1CCCCC1` | `OCC1CCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A158 · ring-bound bromocyclohexane | `BrC1CCCCC1` + `hydroxide` | `OC1CCCCC1` | None; 0 option(s) | **U** | Ring-bound leaving groups need conformational/stereochemical checks. |
| A159 · allyl bromide | `C=CCBr` + `hydroxide` | `C=CCO` | None; 0 option(s) | **U** | Allylic rearrangement/regioselectivity is not currently modeled. |
| A160 · remote ether | `COCCCBr` + `hydroxide` | `COCCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A161 · remote F | `FCCCCBr` + `hydroxide` | `FCCCCO` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A162 · multiple halides two sites | `BrCCCCBr` + `hydroxide` | `OCCCCBr` | `OCCCCBr`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A163 · specified center R input | `CC[C@H](Br)CCC` + `hydroxide` | `CC[C@@H](O)CCC` | `CCC[C@H](O)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s). Pair-wide caveat: Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A164 · specified center S input | `CC[C@@H](Br)CCC` + `hydroxide` | `CC[C@H](O)CCC` | `CCC[C@@H](O)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s). Pair-wide caveat: Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A165 · alternative nucleophile: methoxide | `CCCCBr` + `[Na+].[O-]C` | `CCCCOC` | None; 0 option(s) | **U** | ChemistryError: This multi-part compound is outside the current reaction rules. |
| A166 · alternative nucleophile: iodide | `CCCCBr` + `[Na+].[I-]` | `CCCCI` | None; 0 option(s) | **U** | ChemistryError: This multi-part compound is outside the current reaction rules. |
| A167 · unsubstituted benzyl bromide | `BrCc1ccccc1` + `hydroxide` | `OCc1ccccc1` | `OCc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A168 · negative: tertiary | `CCC(Br)(C)C` + `hydroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A169 · negative: aryl | `Brc1ccccc1` + `hydroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A170 · negative: vinyl | `C=CBr` + `hydroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A171 · negative: fluoride | `CCCCF` + `hydroxide` | No target pathway | None; 0 option(s) | **R** | This rule needs a neutral, closed-shell substrate in its supported element family. |

### SN1

4/11 fully supported applicable cases (36.4%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A172 · long tertiary | `CCCCCC(Br)(C)C` + `water` | `CCCCCC(O)(C)C` | `CCCCCC(C)(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 3 step(s).  |
| A173 · branched tertiary | `CC(C)CC(Br)(C)C` + `water` | `CC(C)CC(O)(C)C` | `CC(C)CC(C)(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 3 step(s).  |
| A174 · benzylic secondary | `CC(Br)c1ccccc1` + `water` | `CC(O)c1ccccc1` | `CC(O)c1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 3 step(s).  |
| A175 · cyclic tertiary | `CC1(Br)CCCCC1` + `water` | `CC1(O)CCCCC1` | None; 0 option(s) | **U** | Ring-bound leaving groups need conformational/stereochemical checks. |
| A176 · allylic tertiary | `C=CC(Br)(C)C` + `water` | `C=CC(O)(C)C` | None; 0 option(s) | **U** | Allylic rearrangement/regioselectivity is not currently modeled. |
| A177 · remote ether | `COCCCC(Br)(C)C` + `water` | `COCCCC(O)(C)C` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A178 · remote F | `FCCCC(Br)(C)C` + `water` | `FCCCC(O)(C)C` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A179 · specified benzylic center | `C[C@H](Br)c1ccccc1` + `water` | `CC(O)c1ccccc1` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A180 · two tertiary sites | `CC(Br)(C)CCC(Br)(C)C` + `water` | `CC(O)(C)CCC(Br)(C)C` | `CC(C)(O)CCC(C)(C)Br`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 3 step(s).  |
| A181 · alternative trapping solvent: methanol | `CCC(Br)(C)C` + `CO` | `CCC(OC)(C)C` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A182 · secondary aliphatic: possible solvolysis, not a dominant-product claim | `CCC(Br)C` + `water` | `CCC(O)C` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A183 · negative: methyl carbocation | `CBr` + `water` | No target pathway | None; 0 option(s) | **R** |  |

### E2

4/13 fully supported applicable cases (30.8%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A184 · tertiary longer chain | `CCCC(Br)(C)C` + `hydroxide` | `C=C(C)CCC` / `CCC=C(C)C` | `C=C(C)CCC` / `CCC=C(C)C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A185 · branched tertiary | `CC(C)CC(Br)(C)C` + `hydroxide` | `C=C(C)CC(C)C` / `CC(C)C=C(C)C` | `C=C(C)CC(C)C` / `CC(C)=CC(C)C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A186 · ring-bound tertiary | `CC1(Br)CCCCC1` + `hydroxide` | `C=C1CCCCC1` / `CC1=CCCCC1` | None; 0 option(s) | **U** | Ring-bound leaving groups need conformational/stereochemical checks. |
| A187 · benzylic secondary | `CCC(Br)c1ccccc1` + `hydroxide` | `CC=Cc1ccccc1` | `CC=Cc1ccccc1`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified; mechanism 1 step(s). E/Z outcome is unassigned. |
| A188 · remote ether | `COCCC(Br)(C)C` + `hydroxide` | `COCC=C(C)C` / `C=C(C)CCOC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A189 · remote F | `FCCC(Br)(C)C` + `hydroxide` | `FCCC(C)=C` / `FCC=C(C)C` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A190 · remote stereocenter | `CC[C@H](C)CCC(Br)(C)C` + `hydroxide` | `CC[C@H](C)CC=C(C)C` / `C=C(C)CC[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A191 · two tertiary reactive sites | `CC(Br)(C)CCC(Br)(C)C` + `hydroxide` | `C=C(C)CCC(Br)(C)C` / `CC(C)=CCC(Br)(C)C` | `C=C(C)CCC(C)(C)Br` / `CC(C)=CCC(C)(C)Br`; 4 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A192 · negative: no beta H (methyl) | `CBr` + `hydroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A202 · long primary | `CCCCCCCBr` + `hydroxide` | `C=CCCCCC` | `C=CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 1 step(s).  |
| A203 · secondary internal sites | `CCCC(Br)CC` + `hydroxide` | `CCC=CCC` / `CC=CCCC` | `CC=CCCC` / `CCC=CCC`; 2 option(s) | **P** | Mapped preview verified; 3D/link verified; mechanism 1 step(s). E/Z outcomes are unassigned. |
| A204 · cyclic secondary | `BrC1CCCCCC1` + `hydroxide` | `C1=CCCCCC1` | None; 0 option(s) | **U** | Ring-bound leaving groups need conformational/stereochemical checks. |
| A205 · specified secondary center | `CC[C@H](Br)CCC` + `hydroxide` | `CCC=CCC` / `CC=CCCC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A206 · alternative base: potassium tert-butoxide | `CCC(Br)(C)C` + `[K+].[O-]C(C)(C)C` | `C=C(C)CC` / `CC=C(C)C` | None; 0 option(s) | **U** | ChemistryError: This multi-part compound is outside the current reaction rules. |

### E1

3/9 fully supported applicable cases (33.3%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A193 · tertiary longer chain | `CCCC(Br)(C)C` + `water` | `C=C(C)CCC` / `CCC=C(C)C` | `C=C(C)CCC` / `CCC=C(C)C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 2 step(s).  |
| A194 · branched tertiary | `CC(C)CC(Br)(C)C` + `water` | `C=C(C)CC(C)C` / `CC(C)C=C(C)C` | `C=C(C)CC(C)C` / `CC(C)=CC(C)C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 2 step(s).  |
| A195 · ring-bound tertiary | `CC1(Br)CCCCC1` + `water` | `C=C1CCCCC1` / `CC1=CCCCC1` | None; 0 option(s) | **U** | Ring-bound leaving groups need conformational/stereochemical checks. |
| A196 · benzylic secondary | `CCC(Br)c1ccccc1` + `water` | `CC=Cc1ccccc1` | `CC=Cc1ccccc1`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified; mechanism 2 step(s). E/Z outcome is unassigned. |
| A197 · remote ether | `COCCC(Br)(C)C` + `water` | `COCC=C(C)C` / `C=C(C)CCOC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A198 · remote F | `FCCC(Br)(C)C` + `water` | `FCCC(C)=C` / `FCC=C(C)C` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A199 · remote stereocenter | `CC[C@H](C)CCC(Br)(C)C` + `water` | `CC[C@H](C)CC=C(C)C` / `C=C(C)CC[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A200 · two tertiary reactive sites | `CC(Br)(C)CCC(Br)(C)C` + `water` | `C=C(C)CCC(Br)(C)C` / `CC(C)=CCC(Br)(C)C` | `C=C(C)CCC(C)(C)Br` / `CC(C)=CCC(C)(C)Br`; 4 option(s) | **F** | Mapped preview verified; 3D/link verified; mechanism 2 step(s).  |
| A201 · negative: no beta H (methyl) | `CBr` + `water` | No target pathway | None; 0 option(s) | **R** |  |
| A207 · secondary aliphatic: possible elimination, not a dominant-product claim | `CCC(Br)C` + `water` | `C=CCC` / `CC=CC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |

### Alcohol oxidation

8/12 fully supported applicable cases (66.7%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A080 · long primary / aldehyde | `CCCCCCCO` + `sodium-hypochlorite` | `CCCCCCC=O` | `CCCCCCC=O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A081 · branched primary / aldehyde | `CC(C)CCO` + `sodium-hypochlorite` | `CC(C)CC=O` | `CC(C)CC=O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A082 · aromatic spectator | `OCCc1ccccc1` + `sodium-hypochlorite` | `O=CCc1ccccc1` | `O=CCc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A083 · remote ether | `COCCCO` + `sodium-hypochlorite` | `COCCC=O` | `COCCC=O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A084 · remote F | `OCCCCF` + `sodium-hypochlorite` | `O=CCCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A085 · remote amine | `NCCCCO` + `sodium-hypochlorite` | `NCCCC=O` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A086 · remote stereocenter | `CC[C@H](C)CCO` + `sodium-hypochlorite` | `CC[C@H](C)CC=O` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A087 · unsaturation: allyl alcohol / acrolein | `C=CCO` + `sodium-hypochlorite` | `C=CC=O` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A088 · actual oxidant: potassium hypochlorite | `CCCCCO` + `[K+].[O-]Cl` | `CCCCC=O` | `CCCCC=O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A089 · negative: ether instead of alcohol/aldehyde | `COCCC` + `sodium-hypochlorite` | No target pathway | None; 0 option(s) | **R** |  |
| A100 · secondary: 4-heptanol | `CCCC(O)CCC` + `sodium-hypochlorite` | `CCCC(=O)CCC` | `CCCC(=O)CCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A101 · cyclic: cycloheptanol | `OC1CCCCCC1` + `sodium-hypochlorite` | `O=C1CCCCCC1` | `O=C1CCCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A102 · diol two sites | `OCCCO` + `sodium-hypochlorite` | `O=CCCO` | `O=CCCO`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A103 · negative: tertiary alcohol | `CCC(O)(C)C` + `sodium-hypochlorite` | No target pathway | None; 0 option(s) | **R** | Tertiary alcohols do not match ordinary alcohol-to-carbonyl oxidation. |

### Aldehyde oxidation

7/11 fully supported applicable cases (63.6%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A090 · long primary / aldehyde | `CCCCCCC=O` + `sodium-hypochlorite` | `CCCCCCC(=O)O` | `CCCCCCC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A091 · branched primary / aldehyde | `CC(C)CC=O` + `sodium-hypochlorite` | `CC(C)CC(=O)O` | `CC(C)CC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A092 · aromatic spectator | `O=CCc1ccccc1` + `sodium-hypochlorite` | `O=C(O)Cc1ccccc1` | `O=C(O)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A093 · remote ether | `COCCC=O` + `sodium-hypochlorite` | `COCCC(=O)O` | `COCCC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A094 · remote F | `O=CCCCF` + `sodium-hypochlorite` | `O=C(O)CCCF` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A095 · remote amine | `NCCCC=O` + `sodium-hypochlorite` | `NCCCC(=O)O` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A096 · remote stereocenter | `CC[C@H](C)CC=O` + `sodium-hypochlorite` | `CC[C@H](C)CC(=O)O` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A097 · unsaturation: allyl alcohol / acrolein | `C=CC=O` + `sodium-hypochlorite` | `C=CC(=O)O` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A098 · actual oxidant: potassium hypochlorite | `CCCCC=O` + `[K+].[O-]Cl` | `CCCCC(=O)O` | `CCCCC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A099 · negative: ether instead of alcohol/aldehyde | `COCCC` + `sodium-hypochlorite` | No target pathway | None; 0 option(s) | **R** |  |
| A104 · ring spectator: cyclohexanecarbaldehyde | `O=CC1CCCCC1` + `sodium-hypochlorite` | `O=C(O)C1CCCCC1` | `O=C(O)C1CCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A105 · dialdehyde two sites | `O=CCCC=O` + `sodium-hypochlorite` | `O=CCCC(=O)O` | `O=CCCC(=O)O`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A106 · negative: ketone | `CCCC(=O)CCC` + `sodium-hypochlorite` | No target pathway | None; 0 option(s) | **R** |  |

### Carbonyl hydrogenation

6/11 fully supported applicable cases (54.5%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A107 · long aldehyde | `CCCCCCC=O` + `hydrogen` | `CCCCCCCO` | `CCCCCCCO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A108 · branched ketone | `CC(C)CC(=O)C` + `hydrogen` | `CC(C)CC(O)C` | `CC(C)CC(C)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A109 · internal ketone | `CCCC(=O)CCC` + `hydrogen` | `CCCC(O)CCC` | `CCCC(O)CCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A110 · cyclic ketone | `O=C1CCCCCC1` + `hydrogen` | `OC1CCCCCC1` | `OC1CCCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A111 · aromatic aldehyde | `COc1ccc(C=O)cc1` + `hydrogen` | `COc1ccc(CO)cc1` | `COc1ccc(CO)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A112 · diketone two sites | `CC(=O)CCCC(=O)C` + `hydrogen` | `CC(O)CCCC(=O)C` | `CC(=O)CCCC(C)O`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A113 · remote F | `FCCCCC=O` + `hydrogen` | `FCCCCCO` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A114 · remote amine | `NCCCC=O` + `hydrogen` | `NCCCCO` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A115 · remote stereocenter | `CC[C@H](C)CC=O` + `hydrogen` | `CC[C@H](C)CCO` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A116 · unsaturated carbonyl | `C=CCC=O` + `hydrogen` | `C=CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A117 · alternative reductant: sodium borohydride | `CCCC(=O)CCC` + `[Na+].[BH4-]` | `CCCC(O)CCC` | None; 0 option(s) | **U** | ChemistryError: This multi-part compound is outside the current reaction rules. |
| A118 · negative: carboxylic acid | `CCCC(=O)O` + `hydrogen` | No target pathway | None; 0 option(s) | **R** |  |

### Esterification

7/10 fully supported applicable cases (70.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A119 · long acid and alcohol | `CCCCCCC(=O)O` + `CCCCO` | `CCCCCCC(=O)OCCCC` | `CCCCCCC(=O)OCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A120 · branched acid/alcohol | `CC(C)C(=O)O` + `CC(C)CO` | `CC(C)C(=O)OCC(C)C` | `CC(C)COC(=O)C(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A121 · cyclic acid and cyclic alcohol | `O=C(O)C1CCCCC1` + `OC1CCCCC1` | `O=C(OC1CCCCC1)C1CCCCC1` | `O=C(OC1CCCCC1)C1CCCCC1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A122 · aromatic acid | `COc1ccc(C(=O)O)cc1` + `CCO` | `COc1ccc(C(=O)OCC)cc1` | `CCOC(=O)c1ccc(OC)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A123 · diacid two acyl sites | `O=C(O)CCC(=O)O` + `CCO` | `CCOC(=O)CCC(=O)O` | `CCOC(=O)CCC(=O)O`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A124 · diol two alcohol sites | `CCCC(=O)O` + `OCCCO` | `CCCC(=O)OCCCO` | `CCCC(=O)OCCCO`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A125 · remote ester spectator | `COC(=O)CC(=O)O` + `CO` | `COC(=O)CC(=O)OC` | `COC(=O)CC(=O)OC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A126 · remote amine on acid | `NCCC(=O)O` + `CO` | `NCCC(=O)OC` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A127 · remote stereocenter on acid | `CC[C@H](C)CC(=O)O` + `CO` | `CC[C@H](C)CC(=O)OC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A128 · specified alcohol center | `CCCC(=O)O` + `CC[C@H](O)C` | `CCCC(=O)O[C@H](C)CC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A129 · negative: acid plus ether | `CCCC(=O)O` + `COC` | No target pathway | None; 0 option(s) | **R** |  |

### Ester hydrolysis

6/10 fully supported applicable cases (60.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A130 · long ester | `CCCCCCC(=O)OCCCC` + `water` | `CCCCCCC(=O)O` | `CCCCCCC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A131 · branched ester | `CC(C)C(=O)OCC(C)C` + `water` | `CC(C)C(=O)O` | `CC(C)C(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A132 · cyclic alkoxy group | `CCCC(=O)OC1CCCCC1` + `water` | `CCCC(=O)O` | `CCCC(=O)O`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A133 · aromatic acyl group | `COc1ccc(C(=O)OCC)cc1` + `water` | `COc1ccc(C(=O)O)cc1` | `COc1ccc(C(=O)O)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A134 · diester two sites | `COC(=O)CCCCCC(=O)OC` + `water` | `COC(=O)CCCCCC(=O)O` | `COC(=O)CCCCCC(=O)O`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A135 · remote hydroxyl | `OCCCC(=O)OCC` + `water` | `OCCCC(=O)O` | `O=C(O)CCCO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A136 · aryl alkoxy: phenyl acetate | `CC(=O)Oc1ccccc1` + `water` | `CC(=O)O` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A137 · lactone ring opening | `O=C1OCCC1` + `water` | `OCCCC(=O)O` | None; 0 option(s) | **U** | Lactone ring-opening products are not supported by this two-product hydrolysis model. |
| A138 · remote amine | `NCCCC(=O)OCC` + `water` | `NCCCC(=O)O` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A139 · remote stereo | `CC[C@H](C)CC(=O)OCC` + `water` | `CC[C@H](C)CC(=O)O` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A140 · negative: amide | `CCCC(=O)N` + `water` | No target pathway | None; 0 option(s) | **R** | This rule needs a neutral, closed-shell substrate in its supported element family. |

### Alcohol dehydration

2/8 fully supported applicable cases (25.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A208 · long primary | `CCCCCCCO` + `sulfuric-acid` | `C=CCCCCC` | `C=CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A209 · secondary internal | `CCCC(O)CC` + `sulfuric-acid` | `CCC=CCC` / `CC=CCCC` | `CC=CCCC` / `CCC=CCC`; 2 option(s) | **P** | Mapped preview verified; 3D/link verified. E/Z outcomes are unassigned. |
| A210 · tertiary branched | `CCCC(O)(C)C` + `sulfuric-acid` | `C=C(C)CCC` / `CCC=C(C)C` | `C=C(C)CCC` / `CCC=C(C)C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A211 · cyclic alcohol | `OC1CCCCCC1` + `sulfuric-acid` | `C1=CCCCCC1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A212 · remote ether | `COCCCCO` + `sulfuric-acid` | `COCCC=C` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A213 · diol multiple groups | `OCCCCO` + `sulfuric-acid` | `C=CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A214 · specified center | `CC[C@H](O)CCC` + `sulfuric-acid` | `CCC=CCC` / `CC=CCCC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A215 · negative: ether | `COCCC` + `sulfuric-acid` | No target pathway | None; 0 option(s) | **R** |  |
| A225 · alternative acid: phosphoric acid | `CCCCCO` + `OP(=O)(O)O` | `C=CCCC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A226 · negative: methanol lacks beta carbon | `CO` + `sulfuric-acid` | No target pathway | None; 0 option(s) | **R** |  |

### Alcohol substitution

5/11 fully supported applicable cases (45.5%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A216 · long primary | `CCCCCCCO` + `hydrogen-bromide` | `CCCCCCCBr` | `CCCCCCCBr`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A217 · secondary internal | `CCCC(O)CC` + `hydrogen-bromide` | `CCCC(Br)CC` | `CCCC(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A218 · tertiary branched | `CCCC(O)(C)C` + `hydrogen-bromide` | `CCCC(Br)(C)C` | `CCCC(C)(C)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A219 · cyclic alcohol | `OC1CCCCCC1` + `hydrogen-bromide` | `BrC1CCCCCC1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A220 · remote ether | `COCCCCO` + `hydrogen-bromide` | `COCCCCBr` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A221 · diol multiple groups | `OCCCCO` + `hydrogen-bromide` | `OCCCCBr` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A222 · specified center | `CC[C@H](O)CCC` + `hydrogen-bromide` | `CCCC(Br)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A223 · benzyl alcohol | `OCc1ccccc1` + `hydrogen-bromide` | `BrCc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A224 · negative: ether | `COCCC` + `hydrogen-bromide` | No target pathway | None; 0 option(s) | **R** |  |
| A227 · actual HX: HI | `CCCCCO` + `hydrogen-iodide` | `CCCCCI` | `CCCCCI`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A228 · tertiary HX: HCl | `CCCC(O)(C)C` + `hydrogen-chloride` | `CCCC(Cl)(C)C` | `CCCC(C)(C)Cl`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A229 · alternative activation: PBr3 | `CCCCCO` + `P(Br)(Br)Br` | `CCCCCBr` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A230 · negative: bare OH is not activated | `CCCCCO` + `hydroxide` | No target pathway | None; 0 option(s) | **R** |  |

### Ester saponification

7/11 fully supported applicable cases (63.6%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A141 · long ester | `CCCCCCC(=O)OCCCC` + `hydroxide` | `CCCCCCC(=O)[O-]` | `CCCCCCC(=O)[O-]`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A142 · branched ester | `CC(C)C(=O)OCC(C)C` + `hydroxide` | `CC(C)C(=O)[O-]` | `CC(C)C(=O)[O-]`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A143 · cyclic alkoxy group | `CCCC(=O)OC1CCCCC1` + `hydroxide` | `CCCC(=O)[O-]` | `CCCC(=O)[O-]`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A144 · aromatic acyl group | `COc1ccc(C(=O)OCC)cc1` + `hydroxide` | `COc1ccc(C(=O)[O-])cc1` | `COc1ccc(C(=O)[O-])cc1`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A145 · diester two sites | `COC(=O)CCCCCC(=O)OC` + `hydroxide` | `COC(=O)CCCCCC(=O)[O-]` | `COC(=O)CCCCCC(=O)[O-]`; 2 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A146 · remote hydroxyl | `OCCCC(=O)OCC` + `hydroxide` | `OCCCC(=O)[O-]` | `O=C([O-])CCCO`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |
| A147 · aryl alkoxy: phenyl acetate | `CC(=O)Oc1ccccc1` + `hydroxide` | `CC(=O)[O-]` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A148 · lactone ring opening | `O=C1OCCC1` + `hydroxide` | `OCCCC(=O)[O-]` | None; 0 option(s) | **U** | Lactone saponification needs a connected ring-opening product rule. |
| A149 · remote amine | `NCCCC(=O)OCC` + `hydroxide` | `NCCCC(=O)[O-]` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A150 · remote stereo | `CC[C@H](C)CC(=O)OCC` + `hydroxide` | `CC[C@H](C)CC(=O)[O-]` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A151 · negative: amide | `CCCC(=O)N` + `hydroxide` | No target pathway | None; 0 option(s) | **R** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A152 · actual full salt: KOH | `CCCC(=O)OCCC` + `[K+].[OH-]` | `CCCC(=O)[O-]` | `CCCC(=O)[O-]`; 1 option(s) | **F** | Mapped preview verified; charged main product 2D-only.  |

### Alkyne hydrogenation

6/10 fully supported applicable cases (60.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A256 · simple: 1-butyne | `CCC#C` + `hydrogen` | `CCCC` | `CCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A257 · long terminal: 1-decyne | `CCCCCCCCC#C` + `hydrogen` | `CCCCCCCCCC` | `CCCCCCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A258 · branched terminal | `CC(C)CC#C` + `hydrogen` | `CC(C)CCC` | `CCCC(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A259 · symmetric internal: 3-hexyne | `CCC#CCC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified. Pair-wide caveat: Internal-alkyne Lindlar stereoproduct generation remains unimplemented; full reduction is available. |
| A260 · asymmetric internal: 2-hexyne | `CC#CCCC` + `hydrogen` | `CCCCCC` | `CCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified. Pair-wide caveat: Internal-alkyne Lindlar stereoproduct generation remains unimplemented; full reduction is available. |
| A261 · cyclic: cyclooctyne | `C1#CCCCCCC1` + `hydrogen` | `C1CCCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A262 · remote OH: 4-pentyn-1-ol | `C#CCCCO` + `hydrogen` | `CCCCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A263 · aromatic conjugation: phenylacetylene | `C#Cc1ccccc1` + `hydrogen` | `CCc1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A264 · remote stereocenter | `C#CC[C@H](C)CC` + `hydrogen` | `CCC[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A265 · two separated triple bonds: 1,7-octadiyne | `C#CCCCCC#C` + `hydrogen` | `C#CCCCCCC` | `C#CCCCCCC`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A266 · negative: saturated octane | `CCCCCCCC` + `hydrogen` | No target pathway | None; 0 option(s) | **R** |  |

### Alkyne partial hydrogenation

4/10 fully supported applicable cases (40.0%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A267 · simple: 1-butyne | `CCC#C` + `hydrogen` | `C=CCC` | `C=CCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A268 · long terminal: 1-decyne | `CCCCCCCCC#C` + `hydrogen` | `C=CCCCCCCCC` | `C=CCCCCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A269 · branched terminal | `CC(C)CC#C` + `hydrogen` | `CC(C)CC=C` | `C=CCC(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A270 · symmetric internal: 3-hexyne | `CCC#CCC` + `hydrogen` | `CCC=CCC` | None; 0 option(s) | **U** | Internal-alkyne Lindlar stereoproduct generation remains unimplemented; full reduction is available. |
| A271 · asymmetric internal: 2-hexyne | `CC#CCCC` + `hydrogen` | `CC=CCCC` | None; 0 option(s) | **U** | Internal-alkyne Lindlar stereoproduct generation remains unimplemented; full reduction is available. |
| A272 · cyclic: cyclooctyne | `C1#CCCCCCC1` + `hydrogen` | `C1=CCCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A273 · remote OH: 4-pentyn-1-ol | `C#CCCCO` + `hydrogen` | `C=CCCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A274 · aromatic conjugation: phenylacetylene | `C#Cc1ccccc1` + `hydrogen` | `C=Cc1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A275 · remote stereocenter | `C#CC[C@H](C)CC` + `hydrogen` | `C=CC[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A276 · two separated triple bonds: 1,7-octadiyne | `C#CCCCCC#C` + `hydrogen` | `C=CCCCCC#C` | `C#CCCCCC=C`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A277 · negative: saturated octane | `CCCCCCCC` + `hydrogen` | No target pathway | None; 0 option(s) | **R** |  |

### Alkyne halogenation

6/21 fully supported applicable cases (28.6%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A278 · simple: 1-butyne · 1 equivalent(s) | `CCC#C` + `bromine` | `CCC(Br)=CBr` | `CCC(Br)=CBr`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A279 · long terminal: 1-decyne · 1 equivalent(s) | `CCCCCCCCC#C` + `bromine` | `CCCCCCCCC(Br)=CBr` | `CCCCCCCCC(Br)=CBr`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A280 · branched terminal · 1 equivalent(s) | `CC(C)CC#C` + `bromine` | `CC(C)CC(Br)=CBr` | `CC(C)CC(Br)=CBr`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A281 · symmetric internal: 3-hexyne · 1 equivalent(s) | `CCC#CCC` + `bromine` | `CCC(Br)=C(Br)CC` | `CCC(Br)=C(Br)CC`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A282 · asymmetric internal: 2-hexyne · 1 equivalent(s) | `CC#CCCC` + `bromine` | `CC(Br)=C(Br)CCC` | `CCCC(Br)=C(C)Br`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A283 · cyclic: cyclooctyne · 1 equivalent(s) | `C1#CCCCCCC1` + `bromine` | `BrC1=C(Br)CCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A284 · remote OH: 4-pentyn-1-ol · 1 equivalent(s) | `C#CCCCO` + `bromine` | `BrC=C(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A285 · aromatic conjugation: phenylacetylene · 1 equivalent(s) | `C#Cc1ccccc1` + `bromine` | `BrC=C(Br)c1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A286 · remote stereocenter · 1 equivalent(s) | `C#CC[C@H](C)CC` + `bromine` | `BrC=C(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A287 · two separated triple bonds: 1,7-octadiyne · 1 equivalent(s) | `C#CCCCCC#C` + `bromine` | `BrC=C(Br)CCCCC#C` | `C#CCCCCC(Br)=CBr`; 2 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |
| A288 · negative: saturated octane · 1 equivalent(s) | `CCCCCCCC` + `bromine` | No target pathway | None; 0 option(s) | **R** |  |
| A289 · simple: 1-butyne · 2 equivalent(s) | `CCC#C` + `bromine` | `CCC(Br)(Br)C(Br)Br` | `CCC(Br)(Br)C(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A290 · long terminal: 1-decyne · 2 equivalent(s) | `CCCCCCCCC#C` + `bromine` | `CCCCCCCCC(Br)(Br)C(Br)Br` | `CCCCCCCCC(Br)(Br)C(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A291 · branched terminal · 2 equivalent(s) | `CC(C)CC#C` + `bromine` | `CC(C)CC(Br)(Br)C(Br)Br` | `CC(C)CC(Br)(Br)C(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A292 · symmetric internal: 3-hexyne · 2 equivalent(s) | `CCC#CCC` + `bromine` | `CCC(Br)(Br)C(Br)(Br)CC` | `CCC(Br)(Br)C(Br)(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A293 · asymmetric internal: 2-hexyne · 2 equivalent(s) | `CC#CCCC` + `bromine` | `CC(Br)(Br)C(Br)(Br)CCC` | `CCCC(Br)(Br)C(C)(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A294 · cyclic: cyclooctyne · 2 equivalent(s) | `C1#CCCCCCC1` + `bromine` | `BrC1(Br)C(Br)(Br)CCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A295 · remote OH: 4-pentyn-1-ol · 2 equivalent(s) | `C#CCCCO` + `bromine` | `BrC(Br)C(Br)(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A296 · aromatic conjugation: phenylacetylene · 2 equivalent(s) | `C#Cc1ccccc1` + `bromine` | `BrC(Br)C(Br)(Br)c1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A297 · remote stereocenter · 2 equivalent(s) | `C#CC[C@H](C)CC` + `bromine` | `BrC(Br)C(Br)(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A298 · two separated triple bonds: 1,7-octadiyne · 2 equivalent(s) | `C#CCCCCC#C` + `bromine` | `BrC(Br)C(Br)(Br)CCCCC#C` | `C#CCCCCC(Br)(Br)C(Br)Br`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A299 · negative: saturated octane · 2 equivalent(s) | `CCCCCCCC` + `bromine` | No target pathway | None; 0 option(s) | **R** |  |
| A322 · alternative appropriate halogen · 1 equivalent(s) | `CCCC#C` + `chlorine` | `CCCC(Cl)=CCl` | `CCCC(Cl)=CCl`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Dihaloalkene E/Z selectivity is unassigned. |

### Alkyne hydrohalogenation

10/21 fully supported applicable cases (47.6%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A300 · simple: 1-butyne · 1 equivalent(s) | `CCC#C` + `hydrogen-bromide` | `CCC(Br)=C` | `C=C(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A301 · long terminal: 1-decyne · 1 equivalent(s) | `CCCCCCCCC#C` + `hydrogen-bromide` | `CCCCCCCCC(Br)=C` | `C=C(Br)CCCCCCCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A302 · branched terminal · 1 equivalent(s) | `CC(C)CC#C` + `hydrogen-bromide` | `CC(C)CC(Br)=C` | `C=C(Br)CC(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A303 · symmetric internal: 3-hexyne · 1 equivalent(s) | `CCC#CCC` + `hydrogen-bromide` | `CCC(Br)=CCC` | `CCC=C(Br)CC`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Vinyl-halide E/Z outcomes are unassigned. |
| A304 · asymmetric internal: 2-hexyne · 1 equivalent(s) | `CC#CCCC` + `hydrogen-bromide` | `CC(Br)=CCCC` / `CCC(Br)=CCC` | None; 0 option(s) | **U** | Inequivalent internal alkyne ends have no supported regioselectivity assignment. |
| A305 · cyclic: cyclooctyne · 1 equivalent(s) | `C1#CCCCCCC1` + `hydrogen-bromide` | `BrC1=CCCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A306 · remote OH: 4-pentyn-1-ol · 1 equivalent(s) | `C#CCCCO` + `hydrogen-bromide` | `C=C(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A307 · aromatic conjugation: phenylacetylene · 1 equivalent(s) | `C#Cc1ccccc1` + `hydrogen-bromide` | `C=C(Br)c1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A308 · remote stereocenter · 1 equivalent(s) | `C#CC[C@H](C)CC` + `hydrogen-bromide` | `C=C(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A309 · two separated triple bonds: 1,7-octadiyne · 1 equivalent(s) | `C#CCCCCC#C` + `hydrogen-bromide` | `C=C(Br)CCCCC#C` | `C#CCCCCC(=C)Br`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A310 · negative: saturated octane · 1 equivalent(s) | `CCCCCCCC` + `hydrogen-bromide` | No target pathway | None; 0 option(s) | **R** |  |
| A311 · simple: 1-butyne · 2 equivalent(s) | `CCC#C` + `hydrogen-bromide` | `CCC(Br)(Br)C` | `CCC(C)(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A312 · long terminal: 1-decyne · 2 equivalent(s) | `CCCCCCCCC#C` + `hydrogen-bromide` | `CCCCCCCCC(Br)(Br)C` | `CCCCCCCCC(C)(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A313 · branched terminal · 2 equivalent(s) | `CC(C)CC#C` + `hydrogen-bromide` | `CC(C)CC(Br)(Br)C` | `CC(C)CC(C)(Br)Br`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A314 · symmetric internal: 3-hexyne · 2 equivalent(s) | `CCC#CCC` + `hydrogen-bromide` | `CCC(Br)(Br)CCC` | `CCCC(Br)(Br)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A315 · asymmetric internal: 2-hexyne · 2 equivalent(s) | `CC#CCCC` + `hydrogen-bromide` | `CC(Br)(Br)CCCC` / `CCC(Br)(Br)CCC` | None; 0 option(s) | **U** | Inequivalent internal alkyne ends have no supported regioselectivity assignment. |
| A316 · cyclic: cyclooctyne · 2 equivalent(s) | `C1#CCCCCCC1` + `hydrogen-bromide` | `BrC1(Br)CCCCCCC1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A317 · remote OH: 4-pentyn-1-ol · 2 equivalent(s) | `C#CCCCO` + `hydrogen-bromide` | `CC(Br)(Br)CCCO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A318 · aromatic conjugation: phenylacetylene · 2 equivalent(s) | `C#Cc1ccccc1` + `hydrogen-bromide` | `CC(Br)(Br)c1ccccc1` | None; 0 option(s) | **U** | Ring/conjugated alkynes need additional selectivity rules. |
| A319 · remote stereocenter · 2 equivalent(s) | `C#CC[C@H](C)CC` + `hydrogen-bromide` | `CC(Br)(Br)C[C@H](C)CC` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A320 · two separated triple bonds: 1,7-octadiyne · 2 equivalent(s) | `C#CCCCCC#C` + `hydrogen-bromide` | `CC(Br)(Br)CCCCC#C` | `C#CCCCCC(C)(Br)Br`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A321 · negative: saturated octane · 2 equivalent(s) | `CCCCCCCC` + `hydrogen-bromide` | No target pathway | None; 0 option(s) | **R** |  |
| A323 · alternative appropriate halogen · 1 equivalent(s) | `CCCC#C` + `hydrogen-iodide` | `CCCC(I)=C` | `C=C(I)CCC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |

### Alkene dihydroxylation

4/11 fully supported applicable cases (36.4%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A242 · long terminal | `C=CCCCCCC` + `hydrogen-peroxide` | `CCCCCCC(O)CO` | `CCCCCCC(O)CO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A243 · branched terminal | `C=C(C)CCC` + `hydrogen-peroxide` | `CCCC(O)(C)CO` | `CCCC(C)(O)CO`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A244 · internal alkene | `CCC=CCC` + `hydrogen-peroxide` | `CCC(O)C(O)CC` | `CCC(O)C(O)CC`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A245 · cyclic cycloheptene | `C1=CCCCCC1` + `hydrogen-peroxide` | `OC1C(O)CCCCC1` | `OC1CCCCCC1O`; 1 option(s) | **P** | Mapped preview verified; 3D/link verified. Syn/cis outcome is unassigned. |
| A246 · remote OH | `C=CCCCO` + `hydrogen-peroxide` | `OCCCC(O)CO` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A247 · aromatic conjugation | `C=Cc1ccccc1` + `hydrogen-peroxide` | `OCC(O)c1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A248 · specified E alkene | `CC/C=C/CC` + `hydrogen-peroxide` | `CCC(O)C(O)CC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A249 · specified Z alkene | `CC/C=C\CC` + `hydrogen-peroxide` | `CCC(O)C(O)CC` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A250 · remote stereocenter | `C=CC[C@H](C)CC` + `hydrogen-peroxide` | `CC[C@H](C)CC(O)CO` | None; 0 option(s) | **U** | Specified tetrahedral stereochemistry is currently transformed only by the mapped SN2 inversion rule. |
| A251 · two separated C=C sites | `C=CCCCCC=C` + `hydrogen-peroxide` | `C=CCCCCC(O)CO` | `C=CCCCCC(O)CO`; 2 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A252 · negative: saturated alcohol | `CCCCO` + `hydrogen-peroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A255 · alternative co-oxidant: NMO | `C=CCCC` + `C[N+]1([O-])CCOCC1` | `CCCC(O)CO` | None; 0 option(s) | **U** | ChemistryError: This structure is outside the supported neutral, non-radical molecule scope. |

### Polymerization model

9/21 fully supported applicable cases (42.9%).

| ID / case | Inputs (substrate + reagent) | Expected main connectivity | Actual main products / options | Status | Verified features / gap |
| --- | --- | --- | --- | --- | --- |
| A324 · ethylene · 2 monomers | `C=C` + `benzoyl-peroxide` | `c1ccccc1CCCCc1ccccc1` | `c1ccc(CCCCc2ccccc2)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A325 · propylene · 2 monomers | `C=CC` + `benzoyl-peroxide` | `c1ccccc1CC(C)C(C)Cc1ccccc1` | `CC(Cc1ccccc1)C(C)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A326 · 1-butene · 2 monomers | `C=CCC` + `benzoyl-peroxide` | `c1ccccc1CC(CC)C(CC)Cc1ccccc1` | `CCC(Cc1ccccc1)C(CC)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A327 · remote branching: 4-methyl-1-pentene · 2 monomers | `C=CCC(C)C` + `benzoyl-peroxide` | `c1ccccc1CC(CC(C)C)C(CC(C)C)Cc1ccccc1` | `CC(C)CC(Cc1ccccc1)C(Cc1ccccc1)CC(C)C`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A328 · styrene · 2 monomers | `C=Cc1ccccc1` + `benzoyl-peroxide` | `c1ccccc1CC(c2ccccc2)C(c2ccccc2)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A329 · vinyl acetate · 2 monomers | `C=COC(C)=O` + `benzoyl-peroxide` | `c1ccccc1CC(OC(C)=O)C(OC(C)=O)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A330 · acrylonitrile · 2 monomers | `C=CC#N` + `benzoyl-peroxide` | `c1ccccc1CC(C#N)C(C#N)Cc1ccccc1` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A331 · negative: saturated ethane · 2 monomers | `CC` + `benzoyl-peroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A332 · ethylene · 4 monomers | `C=C` + `benzoyl-peroxide` | `c1ccccc1CCCCCCCCc1ccccc1` | `c1ccc(CCCCCCCCc2ccccc2)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A333 · propylene · 4 monomers | `C=CC` + `benzoyl-peroxide` | `c1ccccc1CC(C)CC(C)C(C)CC(C)Cc1ccccc1` | `CC(Cc1ccccc1)CC(C)C(C)CC(C)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A334 · 1-butene · 4 monomers | `C=CCC` + `benzoyl-peroxide` | `c1ccccc1CC(CC)CC(CC)C(CC)CC(CC)Cc1ccccc1` | `CCC(Cc1ccccc1)CC(CC)C(CC)CC(CC)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A335 · remote branching: 4-methyl-1-pentene · 4 monomers | `C=CCC(C)C` + `benzoyl-peroxide` | `c1ccccc1CC(CC(C)C)CC(CC(C)C)C(CC(C)C)CC(CC(C)C)Cc1ccccc1` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A336 · styrene · 4 monomers | `C=Cc1ccccc1` + `benzoyl-peroxide` | `c1ccccc1CC(c2ccccc2)CC(c2ccccc2)C(c2ccccc2)CC(c2ccccc2)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A337 · vinyl acetate · 4 monomers | `C=COC(C)=O` + `benzoyl-peroxide` | `c1ccccc1CC(OC(C)=O)CC(OC(C)=O)C(OC(C)=O)CC(OC(C)=O)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A338 · acrylonitrile · 4 monomers | `C=CC#N` + `benzoyl-peroxide` | `c1ccccc1CC(C#N)CC(C#N)C(C#N)CC(C#N)Cc1ccccc1` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A339 · negative: saturated ethane · 4 monomers | `CC` + `benzoyl-peroxide` | No target pathway | None; 0 option(s) | **R** |  |
| A340 · ethylene · 6 monomers | `C=C` + `benzoyl-peroxide` | `c1ccccc1CCCCCCCCCCCCc1ccccc1` | `c1ccc(CCCCCCCCCCCCc2ccccc2)cc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A341 · propylene · 6 monomers | `C=CC` + `benzoyl-peroxide` | `c1ccccc1CC(C)CC(C)CC(C)C(C)CC(C)CC(C)Cc1ccccc1` | `CC(Cc1ccccc1)CC(C)CC(C)C(C)CC(C)CC(C)Cc1ccccc1`; 1 option(s) | **F** | Mapped preview verified; 3D/link verified.  |
| A342 · 1-butene · 6 monomers | `C=CCC` + `benzoyl-peroxide` | `c1ccccc1CC(CC)CC(CC)CC(CC)C(CC)CC(CC)CC(CC)Cc1ccccc1` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A343 · remote branching: 4-methyl-1-pentene · 6 monomers | `C=CCC(C)C` + `benzoyl-peroxide` | `c1ccccc1CC(CC(C)C)CC(CC(C)C)CC(CC(C)C)C(CC(C)C)CC(CC(C)C)CC(CC(C)C)Cc1ccccc1` | None; 0 option(s) | **U** | This structural case is not currently supported: its product failed validation. |
| A344 · styrene · 6 monomers | `C=Cc1ccccc1` + `benzoyl-peroxide` | `c1ccccc1CC(c2ccccc2)CC(c2ccccc2)CC(c2ccccc2)C(c2ccccc2)CC(c2ccccc2)CC(c2ccccc2)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A345 · vinyl acetate · 6 monomers | `C=COC(C)=O` + `benzoyl-peroxide` | `c1ccccc1CC(OC(C)=O)CC(OC(C)=O)CC(OC(C)=O)C(OC(C)=O)CC(OC(C)=O)CC(OC(C)=O)Cc1ccccc1` | None; 0 option(s) | **U** | No target pathway; silent family/detector/role exclusion (see code inventory). |
| A346 · acrylonitrile · 6 monomers | `C=CC#N` + `benzoyl-peroxide` | `c1ccccc1CC(C#N)CC(C#N)CC(C#N)C(C#N)CC(C#N)CC(C#N)Cc1ccccc1` | None; 0 option(s) | **U** | This rule needs a neutral, closed-shell substrate in its supported element family. |
| A347 · negative: saturated ethane · 6 monomers | `CC` + `benzoyl-peroxide` | No target pathway | None; 0 option(s) | **R** |  |

## 12. Final audit verdict

**Structurally generalized but deliberately narrow; mostly accurate generated net graphs, incomplete reaction-family breadth and stereochemical/mechanistic depth.** The priority is removing demonstrated scope barriers safely, not growing an example-name collection. The whole website layout and production behavior were preserved.


