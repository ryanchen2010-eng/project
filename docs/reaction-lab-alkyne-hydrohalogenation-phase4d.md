# Phase 4D — Alkyne hydrohalogenation

Completed 2026-10-16. This increment changes only the existing ionic alkyne HX pathway and its integrations. No new reaction family, radical pathway, layout, Calculator arithmetic, curated example, publication or subsequent review was added.

## Outcome and benchmark comparison

The original implementation already accepted HCl/HBr/HI atom inventories and one-/two-equivalent endpoints. It restricted whole substrates to simple acyclic hydrocarbons, rejected ambiguous internal orientations and specified distant stereochemistry, and did not independently gate these reagents/conditions. This phase replaces that pathway's matching with a dedicated shared-compatibility consumer and exact selected-site edit contract.

The fixed benchmark was rerun before and after implementation. Its script, inputs, expectations and scoring were not changed.

| Measure | Phase 4C baseline | Phase 4D |
| --- | ---: | ---: |
| Positive HX cases with structural matches | 11/21 (52.4%) | 15/21 (71.4%) |
| Strict fully supported under original conditions | 10/21 (47.6%) | 0/21 (0%) |
| Partially supported | 1 | 14 |
| Unsupported positive cases | 10 | 6 |
| Literal benchmark “Incorrect result” rows | 0 | 1 — A304 expectation defect, below |
| Correctly rejected negative controls | 2 | 2 |

“Structural match” means at least one validated net product option exists; it is not a claim of an experimentally established reaction. The 15 includes A304, whose generated connectivity is independently checked but disagrees with a defective frozen expectation. It is not silently counted as a strict benchmark success.

Every original HX input omits medium and temperature. Those omissions now prevent an experimental-looking 3D result; a labeled conditional 2D equation is still available for compatible structures. Internal one-equivalent products also retain unassigned E/Z, and multi-alkyne inputs do not establish selective one-site conversion. Thus the strict decline is principally an enforced conditions/output-policy change, not deletion of the ten previously matched products.

### Separate condition-aware replay — not a replacement benchmark

The same 21 positive inputs were replayed with only `solvent: dry` and `temperature: ambient` added. Original one-/two-equivalent settings were retained. Actual public generation was exercised for each allowed option.

| Replay outcome | Cases | IDs |
| --- | ---: | --- |
| Qualified conditional net-model structures, with verified 3D | 11 | A300–A302, A308, A311–A315, A319, A323 |
| Conditional 2D only | 4 | A303, A304, A309, A320 |
| Structurally unsupported | 6 | A305–A307, A316–A318 |

The 11 qualified cases produce 12 verified structures because A315 has two constitutional alternatives. These are net-model representations, not a new strict score, measured selectivity, isolated yield or laboratory protocol.

## Newly supported structures

- Unsymmetrical internal 2-pentyne and 2-hexyne: both distinct halogen-target orientations, in both pre-existing stages. A304 and A315 now match.
- Distant specified tetrahedral centers, including both enantiomeric inputs and internal alkynes: unaffected physical configuration is retained and CIP assignments are recalculated. A308 and A319 now match.
- Screened, sufficiently remote primary alcohols and ordinary dialkyl ethers: selected-site net equations preserve their bonds, but remain conditional 2D for all HX because substitution, protonation and ether cleavage are unresolved.
- Multiple well-separated alkynes: individual mapped sites remain addressable; equivalent choices are grouped without losing source IDs. Non-equivalent sites remain separate. All such selective equations are 2D bookkeeping only.
- Existing acetylene, terminal/long-chain/remote-branched and symmetric internal examples remain recognized. A remote ordinary saturated five- to eight-membered carbocycle can be preserved after screening; this does not permit cyclic alkynes.

Independent fixtures cover 18 positive and 29 negative structures, not new visible website examples. Generated products depend on graph structure, not molecule names or catalogue IDs.

## One versus two actual HX equivalents

| Endpoint | Selected bond | Actual incoming atoms | New bonds | HX bonds broken |
| --- | --- | --- | --- | --- |
| One equivalent: vinyl halide | C≡C → C=C | 1 H + 1 X | 1 C–H + 1 C–X | 1 H–X |
| Two equivalents: geminal dihalide | C≡C → C–C | 2 H + 2 X | 2 C–H + 2 C–X | 2 H–X |

Both halogens in the second stage attach to the same selected carbon; both incoming hydrogens attach to the other original alkyne carbon. Existing substrate C–H bonds and all unlisted bonds remain unchanged. Exactly one or two homogeneous actual HX molecules are required, with unique positive maps. Mixed donors, HF, salts, X2, radicals, isotopic donors and forged/obsolete IDs fail closed.

These are the pre-existing stages, not new functionality. They differ from X2 addition: HX adds hydrogen and gives a geminal second-stage product; X2 gives different atom inventories and connectivity. No coproduct is invented. Net charge remains zero and all atoms, including the two separate reagent copies, are conserved.

The bounded net endpoints and terminal Markovnikov orientation follow the established distinction between first-stage vinyl halides and further geminal addition. They do not establish experimental stopping or universal stereospecificity. [OpenStax Organic Chemistry, 9.3](https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2).

## Regioselectivity, stereochemistry and mapping

- Terminal alkyne: X attaches to the carbon without the terminal H; the CH2= product has no E/Z designation.
- Symmetric internal alkyne: chiral whole-graph automorphism checks establish equivalent ends, rather than atom numbering or local formula alone.
- Unsymmetric internal alkyne: both constitutional target choices are retained, with distinct existing site labels identifying the halogen-target carbon. No preference or percentage is assigned.
- Internal vinyl halide: potential E/Z remains explicitly unassigned. All three reagents are 2D-only for this first-stage case; random conformer geometry is not a stereochemical prediction.
- Saturated geminal product: no residual E/Z tag and no newly assigned local tetrahedral configuration. Two identical halogens do not create a local stereocenter.
- Distant centers: exact mapped-neighbor physical parity is checked before/after transformation and SMILES serialization. CIP assignments are computed independently. A regression using `C#CCC[C@H](C)CCCO` demonstrates S → R after two-HBr addition **without physical inversion**, due to changed priorities; its oxygen competition still blocks 3D.
- Invalid, enhanced or nonstandard input stereochemistry cannot silently disappear during normalization. A specified propargylic center remains outside this validated scope.

The shared strict validator was not weakened. It checks the complete expected bond edit inventory, all atom identities/charges, unchanged bonds, physical stereo and one-fragment connectivity. Serialized products are revalidated. Applicable generated 3D graphs are checked against the same mapped product and distant configuration; coordinates never decide the reaction outcome.

### Frozen benchmark defect A304

Starting structure: `CC#CCCC` (hex-2-yne). Its selected original bond is C2–C3.

| Constitutional alternative | Correct net product |
| --- | --- |
| X on C2 | `CC(Br)=CCCC` — 2-bromohex-2-ene |
| X on C3 | `CC=C(Br)CCC` — 3-bromohex-2-ene |

The frozen second expectation is `CCC(Br)=CCC`, which moves the double bond to C3–C4. The engine must not move that bond merely to agree with this expectation. An independent regression requires the C3-target product above and explicitly excludes the erroneous shifted-bond product. The unchanged benchmark therefore reports one literal “Incorrect result”; this is disclosed, not suppressed, rescored or described as a clean benchmark pass.

## Conditions and independent reagent policies

All potentially 3D-eligible net structures require an explicitly selected stage, compatible non-capturing dry-medium assumption and ambient temperature. “Dry / no water” is only the existing selector's bounded assumption: it does not prove that every dry solvent tolerates HX. Actual reagent formulation, amount, stopping, time, light exposure and peroxide absence are not measured.

| Reagent | Terminal, one equivalent | Two equivalents | Internal, one equivalent |
| --- | --- | --- | --- |
| HBr | Qualified net-model 3D if all other gates pass | Qualified net-model 3D; separate internal regio-alternatives if applicable | Unsigned conditional 2D |
| HCl | Conditional 2D; formulation/activation not validated by current selectors | Conditional 2D | Conditional 2D |
| HI | Qualified net-model 3D if all other gates pass | Conditional 2D; reagent-specific completion/stability scope unvalidated | Unsigned conditional 2D |

These are software evidence/output boundaries, not claims that HCl reactions are impossible or that every HBr/HI experiment follows the represented endpoint. Published HBr formulation studies show why medium, stoichiometry and competing oxygen chemistry cannot be treated as interchangeable. This phase does not implement their DMPU-specific conditions or import their stereochemical outcomes. [HBr–DMPU: The First Aprotic Organic Solution of Hydrogen Bromide](https://pmc.ncbi.nlm.nih.gov/articles/PMC5682921/).

Specialized hydrochlorination/transfer protocols likewise cannot be inferred from a generic “Acid” or Pd/Pt selector. No Au, Ir, directed or transfer system was added. [Primary study of transfer hydrochlorination and related methodology](https://pmc.ncbi.nlm.nih.gov/articles/PMC7028031/).

Missing settings, generic polar-aprotic medium, aqueous/alcohol capture, heating, extra activation, remote oxygen competition, competing alkynes and internal unsigned geometry have precise separate explanations. Radical initiation is outside the ionic pathway; it does not generate anti-Markovnikov HBr or analogous HCl/HI predictions. Unknown values cannot reuse an earlier allowed condition state. Conditional 2D, calculator warnings and the public run gate agree.

New output restrictions include required medium/temperature/stage, HCl and two-HI gates, unsigned internal first-stage geometry, and selective multi-alkyne 3D blocking. Additional structural exclusions include directly adjacent branching/ring environments and nearby capture risks. These are deliberately conservative compatibility limits, not proof of chemical impossibility.

## Remaining unsupported structures

The six fixed positive exclusions remain:

- A305/A316, cyclooctyne: strained cyclic-alkyne addition/geometry unvalidated.
- A306/A317, 4-pentyn-1-ol: its oxygen is near enough for a shortest potential five-membered capture path, not a proven inert remote OH.
- A307/A318, phenylacetylene: aromatic-adjacent/conjugated orientation and mechanism outside this increment.

Other restrictions include conjugated/nearby diynes, enynes, directly heteroatom-substituted alkynes, aromatic spectators, nearby nucleophiles, activated/cyclic/acetal ethers, secondary/tertiary alcohols, carbonyl/ester/amine/halide/peroxide spectators, directly adjacent branched/quaternary or ring-bound carbon, unvalidated small/fused/complex rings, near-site specified stereo, charged/open-shell inputs and products over 80 explicit atoms including incoming H/X. Rejections name the selected-site environment; an unsupported structure is not described as chemically unable to react.

Remote oxygen and isolated additional alkynes are only partially modeled. Full solvent-specific selectivity, rearrangement, cyclization, radical chemistry, exact stereoisomer distributions and physical reaction rates/yields remain unimplemented.

## Mechanism, diagrams and calculations

The pathway honestly exposes a **net transformation only**. `mechanism` is null and the mechanism capability is unsupported. No ordinary alkene carbocation sequence, invented validated vinyl cation, elementary curved-arrow sequence or transition state is attached. Bond changes and incoming atom provenance remain highlighted.

The public match, diagram and authenticated run routes were exercised, including reversed reactant order, multiple-site aliases, missing conditions, forged/stale IDs and wrong reagents. 2D atoms and allowed 3D `atomLinks` agree exactly by index, map and element. All listed changes match the selected triple bond and actual H–X bonds.

Calculator fixtures exercise both stages, reactant slots, regio-alternatives, molar masses, limiting reactants and required amounts. Context warns that complete conversion and the selected number of equivalents are assumptions; alternatives must not be summed as simultaneous yields. No arithmetic was changed.

Browser checks used the existing propyne/HBr example:

- One equivalent gives C3H5Br, with Br8 linked in reactants, 2D product and 3D.
- Switching to two equivalents clears the old structure/amounts and gives C3H6Br2 with two distinct HBr atom inventories.
- 0.040065 g propyne and 0.080912 g HBr mean 1 mmol each. At the two-HX endpoint, HBr limits the theoretical product to 0.0005 mol / 0.1009445 g (displayed 0.10094 g); 0.0005 mol propyne remains.
- Selecting radical activation clears prior results, retains a labeled ionic conditional 2D equation and blocks 3D. It does not show a predicted radical product.

![Existing layout with mapped bromine selected in both views](reaction-lab-phase4d-preview.png)

## Tests and regression evidence

| Check | Result |
| --- | --- |
| Python | 1,416 passed |
| JavaScript | 1,413 passed |
| Total | **2,829 passed; zero failures/skips** |
| New tests | 459: 161 Python + 298 JavaScript |
| Authenticated HX route tests | 7 passed, included above |
| Independent HX diagnostic | 291 cases, 153 options/diagrams, 31 verified 3D runs, 122 correctly blocked runs, zero failures |
| Partial hydrogenation regression | 52 cases / 33 options, exactly unchanged |
| Complete hydrogenation regression | 52 cases / 32 options, exactly unchanged |
| Alkyne halogenation regression | 177 cases / 85 options, exactly unchanged |
| Six alkene-addition diagnostic | 48 cases / 66 options, exactly unchanged |
| TypeScript | Passed |
| Production build | Passed; existing large Builder/vendor chunk warnings remain |
| Whitespace / preservation checks | Passed |

All 2,370 existing tests are retained and passing, with **one disclosed obsolete expectation updated**: the old chemistry-depth assertion rejected unsymmetrical 2-pentyne entirely. It now requires both independently correct orientations, no ratio claim and an incomplete-condition 3D block. Keeping its old rejection assertion would contradict this phase's explicitly requested functionality. No other original test/fixture expectation was changed or removed.

The final fixed audit has 168 fully supported, 47 partially supported, 93 unsupported, 38 correctly rejected and one literal incorrect-result row: **347 total**. Its HX bucket is 23 rows: A300–A321 plus A323, comprising 21 positive cases and two controls. A322 belongs to halogenation, not HX. All **324 unrelated rows are entirely identical**, including products, notes, status and workflow fields. All pathway bucket counts also sum to 347; there is no overlap/double counting. The two HX negative controls are unchanged; 21 positive HX rows changed outputs or explanations.

Unrelated alkyne strict scores remain partial hydrogenation 8/10, complete hydrogenation 7/10 and halogenation 0/21 under its unchanged missing-medium inputs. Their rule modules, tests and fixtures, the alkene-addition modules, shared stereo/edit validators, frontend, Calculator arithmetic, curated data and packaging were not changed.

The source/test/config hash inventory records nine existing files changed (eight server integration files plus the one disclosed old test), six new implementation/test/diagnostic files and every other original inventoried file unchanged. The fixed audit script SHA-256 remains `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

Detailed row comparisons, hashes, companion results, preservation inventory and verification evidence are saved in [the Phase 4D machine report](reaction-lab-alkyne-hydrohalogenation-phase4d-results.json). The reproducible additional workflow is `scripts/audit_alkyne_hydrohalogenation.py`; the fixed benchmark remains `scripts/audit_reaction_lab.py`.

## Recommended next phase — not started

Perform a controlled combined **alkyne-family consistency review** of partial/complete hydrogenation, X2 addition and HX addition, especially reagent-specific output confidence, equivalent stages, stereo and grouped site identities. Treat the A304 benchmark defect as a separately authorized benchmark maintenance issue; do not silently fix it during coverage comparison. Any future formulation-specific HCl/HI or internal E/Z support needs independent evidence and tests.

Phase 4D is complete. No next implementation or combined review was started.
