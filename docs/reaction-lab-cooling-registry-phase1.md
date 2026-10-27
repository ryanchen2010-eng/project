# Cooling development — Phase 1: registry and confidence contracts

25 October 2026 · Local implementation only · Phase 1 complete

## Result

The two existing cooled profiles now use one immutable backend registry. Their chemical scope, product transformations, condition requirements, visible explanations and existing v1 identifiers are preserved:

- `cooled-alkene-bromination-v1` — actual Br₂ bromination.
- `cooled-peroxyacid-epoxidation-v1` — actual mCPBA epoxidation only.

No additional reaction type, peracid, catalyst, solvent, temperature range, work-up or stereochemical outcome was approved. In particular, perbenzoic epoxidation and cooled dihydroxylation remain unimplemented.

This completes **Phase 1 only** of the comprehensive cooling plan. No GitHub push, merge, frozen-beta update or Render deployment was performed.

## Implementation

### Shared backend registry

`server/reaction_temperature_profiles.py` owns the two existing validators, source records, exact IDs, presentation names and versioned lookup. Frozen entries and read-only mappings prevent accidental runtime registration. No research/backlog profile is executable.

The existing validators were extracted rather than replaced with a universal cooling rule. They still require their original reagent evidence and dry/non-capturing model, reject inappropriate activation and unrelated stages, and retain all original chemistry/product gates. The separate alkyne temperature guard is unchanged.

`server/reaction_conditions.py` remains the shared confidence overlay and re-exports the original v1 constants/helper for existing consumers. It now obtains model names and labels through registry lookup rather than reaction-specific label branches.

### Version and permission contract

All previous `cooling` v1 fields remain. Three additive fields are provided:

| Field | Meaning |
| --- | --- |
| `registryVersion` | Version of the reviewed registry contract; currently 1. |
| `profileVersion` | 1 for a recognized existing profile; null for an unreviewed pathway. |
| `reasonCodes` | Empty for a supported model; otherwise structured reasons such as medium unresolved, unsupported condition field, unreviewed pathway or unsupported endpoint. |

Exact model/pathway/version lookup fails closed. Unknown versions, IDs and contradictory cached permissions cannot bypass the shared overlay. A valid existing overlay remains non-mutating and idempotent. A cached positive also cannot be reused after its current conditions or peracid identity cease to satisfy the registered validator. Public requests independently re-resolve reactants and sites as before.

The invalid-contract rejection path blocks both `canRun` and any existing evidence 3D permission; it does not invent a replacement profile. Stronger missing/activation/unsupported explanations are preserved.

### Cooled-only legacy adapter

The six older condition-assessment families now receive explicit cooled-only defaults before the overlay: hydrogenation, carbonyl hydrogenation, esterification, ester hydrolysis, ester saponification and finite polymerization.

These defaults cannot grant cooled generation. They retain the original reference note and do not turn a teaching-example difference into missing chemical activation. Ambient, heated and unset assessments are unchanged.

### Frontend consistency

`src/reaction-conditions.ts` uses a small immutable presentation table instead of two branching model-name checks. A cross-language regression test compares it exactly with the backend's detached reviewed manifest, so it cannot grow independently without failing verification.

The frontend continues to defer to backend permission, while requiring recognized model/pathway/version metadata and consistent assessment, evidence and cooling flags before affirmative cooled wording. New registry metadata is checked when present; original v1 payloads without the additive fields remain compatible. The table contains labels, not a second chemistry engine or a generation permission source.

No layout, CSS, navigation, condition controls, calculator arithmetic or product-generation rules changed.

## Before/after equivalence

Baseline observations were captured before implementation, separately from permanent tests and the frozen benchmark.

| Comparison | Result |
| --- | --- |
| 35,000 original-versus-refactored assessment/overlay observations | Zero differences outside the three additive cooling fields. Includes temperature, medium, catalyst, peracid identity, unknown fields, unrelated stages and underlying failed assessments. |
| 100 public match/diagram contexts across all 24 types, including separate primary/secondary oxidation models | Zero differences outside additive cooling metadata. Cooled, ambient, heated and unset inputs were compared. |
| Original 347-case audit | Entire before/after JSON observations identical; benchmark file unchanged. |

Unrecognized or contradictory cached contracts intentionally now fail closed instead of being trusted merely because a `coolingPolicy` marker exists. This is permission-contract hardening, not expanded chemistry or a change to any legitimate reviewed product.

The existing frozen audit's source-fingerprint list was not expanded. Separate file-hash checks cover the modified condition sources and preservation of existing tests, product rules and benchmark artifacts; an unchanged frozen fingerprint alone is not claimed to describe every dependency.

## Verification

### Regression tests

- Verified starting baseline: **2,029 Python + 2,011 JavaScript = 4,040 passing tests**.
- New suites: `tests/test_cooling_registry_phase1.py` (**22 tests**) and `tests/cooling-registry-phase1.test.mjs` (**37 tests**).
- Final complete suite: **2,051 Python + 2,048 JavaScript = 4,099 passing tests**.
- All original test files were preserved without edits, including the cooling v1 suites.

New checks cover registry immutability, exact two-profile membership, detached manifest data, backend/frontend parity, old v1 compatibility, strict version handling, unknown IDs, underlying blockers, legacy normalization, specific rejection codes, idempotence, stale cached positives, public unknown-profile requests and contradictory evidence.

Existing suites continue to verify mapped products, charge/atom conservation, stereochemistry, authenticated APIs, mechanisms, calculator fixtures and lifecycle behavior.

### Frozen benchmark

All **347 cases** remain identical:

| Classification | Before | After |
| --- | ---: | ---: |
| Fully supported | 155 | 155 |
| Unsupported | 90 | 90 |
| Correctly rejected | 38 | 38 |
| Partially supported | 63 | 63 |
| Pre-existing incorrect-result classification | 1 | 1 |

The known benchmark issue remains visible; no expectations, case IDs or inputs were changed. No cooled examples were added to the frozen benchmark or curated website collection.

### Build and browser checks

- TypeScript and production build pass through `pnpm run build`.
- Existing dependency module-directive and large-chunk warnings remain; no build failure.
- Python compile checks and scoped whitespace checks pass.
- Browser checks used an isolated localhost server serving the production build and the actual chemistry APIs, plus a fresh headless Chrome profile. No live service or normal browser profile was modified.
- Actual cooled Br₂ and mCPBA workflows generate mapped main-product conformers and retain theoretical, non-temperature-simulation confidence wording.
- mCPBA was entered through the existing Builder-transfer contract. Its 2D equation retains the actual acid coproduct; the existing concerted mechanism has one step and four electron moves. Br₂ remains net-only, without an invented full mechanism.
- Reaction calculators retain the balanced 1:1 theoretical accounting and clear their output when conditions change.
- Switching cooled/ambient/heated settings and changing to an aqueous medium clears old products and calculations. Incompatible water settings block cooled 3D with the existing pathway-specific explanation.
- A deliberately delayed real run response cannot restore a product after a condition change aborts/invalidates it.
- At **320px**, document width remains **320px**; existing Inspector controls, theoretical epoxide 3D and water-medium blocking work. No uncaught browser errors occurred.

## Preservation and limitations

Only the existing condition-assessment module and frontend condition-contract module changed among pre-existing source/test/document/benchmark files. A new registry, two new test suites and this report were added. Existing user edits were retained.

All original product-rule modules, identities, mapping/stereo utilities, mechanisms, calculators, layouts, curated examples, previous cooling reports and benchmark artifacts remain byte-identical to their pre-phase versions. Production assets were rebuilt locally for verification; they were not published.

The registry does not establish experimental rates, conversion, yields, solvent universality, mixture composition or temperature-dependent geometry. The successful finite regression suite is not proof of universal chemistry correctness.

## Recommended next step — not started

Review this Phase 1 result, then separately approve the plan's bounded perbenzoic-acid epoxidation evidence/condition phase if desired. It remains an evidence-gated extension, not an automatic follow-on. No Phase 2 work was begun.
