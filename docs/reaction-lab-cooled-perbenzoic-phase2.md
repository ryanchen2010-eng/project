# Cooling development — Phase 2: bounded perbenzoic-acid epoxidation

25 October 2026 · Local implementation only · Phase 2 complete

## Result and scope

Added `cooled-perbenzoic-epoxidation-v1` to the reviewed cooling registry. Eligible terminal styrene-type hydrocarbons can now request a theoretical epoxide 3D conformer with actual perbenzoic acid under the named cold-medium net assumption. Benzoic acid remains the coproduct.

There are now **three reviewed profiles across two reaction types**: Br₂ bromination, mCPBA epoxidation and this separately bounded perbenzoic-acid epoxidation profile. This is not a third reaction family or permission for every peracid or alkene.

The existing reaction transformations, stereochemistry utilities, mechanism rules, calculators, layout and frozen benchmark were not changed. No push, merge, deployment or frozen Beta v1 update was performed. Phase 3 was not started.

## Evidence and the representation gate

The accessible, checked [Organic Syntheses styrene-oxide preparation](https://www.orgsyn.org/demo.aspx?prep=CV1P0494), DOI 10.15227/orgsyn.008.0102, documents actual perbenzoic acid in chloroform at a 0 °C reaction stage and an identified epoxide. Acid removal occurs after the reaction. That observation supports the parent styrene precedent, not all dry solvents, all temperatures or all substrates.

The cited original Hibbert–Burt paper is [JACS 1925, 47(8), 2240–2243](https://doi.org/10.1021/ja01685a025). Its publisher full experimental text was not accessible in this review, so no additional experimental details or substrate scope are attributed to it.

The existing same-face peracid transfer model is consistent with the general chemistry summarized in [OpenStax Organic Chemistry §8.7](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation). That general reference is not additional cold perbenzoic-acid experimental evidence.

### Deliberately narrow substrate policy

The new condition profile requires:

- Actual neutral perbenzoic acid, canonical identity `O=C(OO)c1ccccc1`, rather than a name or formula match.
- One terminal `CH₂=CH–phenyl` site in a neutral closed-shell hydrocarbon.
- Exactly one all-carbon aromatic six-membered ring; optional saturated acyclic alkyl substituents on that ring.
- No additional unsaturation, rings or heteroatom functional groups.
- All existing epoxidation site, reagent, size, competing-reaction, stereochemistry and product-validation checks must already pass.

Ring-alkyl variants are a **bounded net-model inference**, explicitly labeled as such, not separately verified cold experiments. These substituents retain the same local vinylbenzene reaction environment; the profile does not infer experimental selectivity, stability or yields. Alpha/beta-substituted styrenes and ordinary aliphatic/internal/cyclic alkenes are not approved by this increment.

### Medium and temperature are assumptions, not experimental inputs

The existing **Dry / no water** control selects a named **chloroform-reference theoretical net assumption** for this profile. It does not establish that chloroform was actually entered or that every dry solvent is compatible. The API records `referenceSolvent: chloroform` and `experimentalSolventEntered: false`; guidance and confidence text explain the limitation.

The source's 0 °C point is a reference, not a numerical input, validated continuous range or arbitrary cryogenic permission. Cooling is reaction control, not evidence for a new stereochemical outcome.

No added activation is approved. Water, alcohol, generic aprotic media, unrelated work-up/oxidation-stage declarations and unknown condition fields cannot qualify the profile. Existing acid-opening and competing-chemistry restrictions remain. The source's later acid removal is not silently represented as a catalyst, work-up or isolated epoxide guarantee.

## Implementation

| Component | Change |
| --- | --- |
| `server/reaction_temperature_profiles.py` | Exact-identity selection for a third registered profile, bounded substrate predicate, model-specific condition assessment, evidence/assumption metadata and a specific substrate-scope rejection code. |
| `server/reaction_engine.py` | Adds internal canonical epoxidation substrate identity alongside the existing actual peracid identity. No graph transformation changes. |
| `server/reaction_condition_guidance.py` | Uses the same backend assessor to offer only representable medium/activation model choices, with explicit confirmation. Cannot erase unknown inputs, clear unrelated stages, change temperature or bypass substrate rejection. |
| `src/reaction-conditions.ts` | Adds the profile to the immutable presentation mirror; exact backend/frontend parity remains tested. |
| `src/guided-reaction-conditions.ts` | Allows only this profile's exact medium/activation target fields; unexpected hidden changes fail closed. |
| `src/reaction-lab.ts` | Adds one sentence to existing temperature help. No layout, controls, CSS or navigation changes. |

Registry and response protocol remain version 1; this is an additional individually versioned v1 entry, not a protocol change. Existing mCPBA fallback behavior and Br₂ validators remain unchanged. Unknown profile IDs/versions, failed underlying assessments and stale cached permissions still fail closed.

UI/UX Pro Max informed only guidance clarity and the existing accessible review/confirmation interaction. Nothing is automatically filled. A user must review the named assumption, confirm replacements and apply; the backend then revalidates current inputs. Outside-scope structures do not receive a misleading Apply action.

## Products, mapping, mechanisms and amounts

The existing epoxidation engine supplies the product graph and same-face alternatives. The new profile does not derive stereochemical certainty from an optimized conformer or predict facial populations.

Independent positive fixtures cover:

1. Styrene.
2. Ortho-methylstyrene.
3. Meta-methylstyrene.
4. Para-methylstyrene.
5. Para-ethylstyrene.
6. A dimethylstyrene.
7. A ring-alkyl variant with a distant specified stereocenter.

Each fixture checks two separately represented face alternatives against independently written product graphs. Parent products are independently checked as the R and S structures; no stereoisomer ratio is asserted. The distant configuration is independently retained, and assigned graph configurations agree with reconstructed 3D configurations.

Checks verify the transferred oxygen, retained peracid proton in the acid coproduct, all represented atom-map identities, charges, eight net bond edits and four electron moves in the existing one-step concerted mechanism. No stable intermediate is invented. Main-product 3D contains only that product's mapped atoms; 2D retains the benzoic-acid coproduct.

Amounts remain the existing theoretical 1:1 net calculation. Fixtures independently verify full perbenzoic-acid molar mass (138.122 g/mol), benzoic-acid mass (122.123 g/mol), elemental mass balance, input-slot provenance in both orders, limiting amounts and required amounts. Complete conversion is an arithmetic assumption, not predicted yield or experimental site selectivity.

Negative tests cover other peracids, formula/name spoofing, missing actual substrate metadata, ordinary/internal/cyclic alkenes, extra rings or unsaturation, heteroatom/strained/conjugated environments, inappropriate medium/activation, unknown inputs, unrelated stages, failed underlying checks and stale positive overlays. Wider existing non-cooled peracid behavior is preserved.

## Verification

### Regression and public API

| Check | Result |
| --- | --- |
| Fresh pre-change baseline | 2,051 Python + 2,048 JavaScript = **4,099 passing**. |
| New Phase 2 suites | `tests/test_cooled_perbenzoic_phase2.py`: **20**; `tests/cooled-perbenzoic-phase2.test.mjs`: **53**. |
| Complete final regression | 2,071 Python + 2,101 JavaScript = **4,172 passing**, no failures. |
| Public workflow | Match, diagram and run, including authenticated production-app requests; stale option IDs revalidated and auth requirements retained. |
| Existing public observations | **100 contexts**, covering all 24 types / 25 models across four temperature selections, exactly unchanged. These fixtures are not the new perbenzoic positive set. |
| TypeScript and production build | `pnpm run build` (`tsc && vite build`) passes. Existing dependency directive and large-bundle warnings remain. |
| Additional checks | Python compilation, tracked diff whitespace and modified/new-file whitespace checks pass. |

Three existing cooling test files received only narrowly superseded expectations: profile count/membership becomes three, and out-of-scope perbenzoic reactions now report the new profile's precise substrate limitation instead of an mCPBA reagent mismatch. Prior positive/negative safeguards remain, and no tests were removed.

### Frozen 347-case benchmark

Inputs, expectations and audit code remain byte-for-byte unchanged. All result rows, statuses, pathway summaries and supplementary observations are exactly identical before/after; only the audit's recorded production fingerprints for `server/reaction_engine.py` and `src/reaction-lab.ts` differ as expected. The source fingerprint list is not exhaustive, so separate preservation hashes also cover the other modified sources.

| Frozen classification | Before | After |
| --- | ---: | ---: |
| Fully supported | 155 | 155 |
| Unsupported | 90 | 90 |
| Correctly rejected | 38 | 38 |
| Partially supported | 63 | 63 |
| Incorrect result | 1 | 1 |
| Total | 347 | 347 |

The pre-existing incorrect-result classification is not corrected or hidden in this phase. The frozen audit is not the cooling coverage measure; the new separate versioned fixtures demonstrate this profile without modifying the benchmark or adding visible examples.

### Real browser checks

Isolated headless Chrome used the current production build plus the actual existing local chemistry API, not mocked chemistry responses. Passed:

- Desktop cooled styrene/perbenzoic selection, conditional 2D, benzoic coproduct and mapped 3D Compare.
- Existing concerted mechanism display and reaction-amount calculator (0.001 mol styrene oxide → theoretical 0.12015 g).
- Missing medium blocks 3D; existing guidance visibly names the solvent assumption, requires a checkbox and explicitly applies/revalidates without changing cooling.
- Temperature changes and water selection clear prior product/calculator results and update 3D permission.
- An actual delayed run response cannot restore a product after conditions invalidate it.
- Propene/perbenzoic remains conditional 2D only, without a misleading Apply action.
- At 320 px: cooled 3D, accessible condition changes and water blocking; document width remains 320 px.
- Existing Br₂ and mCPBA desktop/mobile checks, mechanisms where implemented, calculators and stale-response races still pass.
- No uncaught page errors. Existing layout was retained; desktop/mobile screenshots were inspected.

A first temporary browser assertion expected a rounded calculator value; it was corrected to the calculator's actual existing precision. No calculator code or permanent expectations changed for that diagnostic adjustment.

QA logs, before/after captures and screenshots are under `/private/tmp/molecule-cooling-phase2.91vlFl`. The temporary QA server and headless browser sessions were stopped after verification.

## Remaining limits and stop point

This phase does not validate peracetic acid, all aromatic-adjacent alkenes, alpha/beta-substituted styrenes, multifunctional substrates, selective multisite epoxidation, an experimental solvent selector, a numerical cooling range, acid removal or isolated recovery. Existing broader mCPBA scope is not transferred to perbenzoic acid.

No new stereochemistry, surface mechanism, reaction-rate, experimental-yield or safety prediction was added. A theoretical conformer remains a representation of a validated net-product graph, not a temperature simulation.

**Phase 2 is complete. Stop for review; no further cooling profile or Phase 3 work is included.**
