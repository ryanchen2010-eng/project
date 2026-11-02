# Cooled alkene bromination: assessment and theoretical 3D

This historical first profile remains unchanged. The next scoped review adds
actual-mCPBA epoxidation only; see the [version-1 cooling compatibility matrix
and evidence](reaction-lab-cooling-compatibility-v1.md). Statements below that
epoxidation was still restricted describe the original increment, not the
later mCPBA-only exception.

Local increment, 24 October 2026. No deployment, layout redesign, new reaction
family, benchmark change, chemistry-rule expansion or curated example change.

## Implemented result

The shared cooling assessment now recognizes one versioned policy:
`cooled-alkene-bromination-v1`. A substrate already accepted by the existing
alkene bromination rule can generate its existing mapped dibromide conformer
with actual Br₂, `temperature=cooled`, the existing `solvent=dry` non-capturing
net-model assumption and no added activation (`none` or the existing unset
neutral-model setting). The alkene rule, product transformations, atom
identities, validation and anti-addition implementation are unchanged.

Cooling remains a qualitative choice. This feature does **not** establish an
exact temperature range, arbitrary cryogenic conditions, experimental rate,
yield, conversion, isolation, one-site selectivity, stereoisomer ratio or a
complete experimental procedure. 3D is a theoretical product conformer, not a
temperature-dependent molecular simulation. Selecting “Dry / no water” is a
bounded modeling assumption, not proof of a non-nucleophilic solvent.

The existing public match, diagram, run and stoichiometry contexts use the same
assessment. It exposes `cooling.version`, `pathway`, `modelId`, `status`,
`canGenerate3D`, `note` and `sourceUrls`. The three cooling states are
`supported-model`, `conditions-unresolved` and `unvalidated-pathway`.
Structural eligibility and conditional theoretical output are still separate
from experimental confidence; the public support state remains `Conditional`.

All other cooled pathways remain 2D-only where previously restricted,
including alkene chlorination, epoxidation and every alkyne pathway. Unset,
ambient and heated behavior is unchanged. Changing conditions rechecks output
permission; a formerly valid reaction ID cannot bypass the current gate.

## Boundaries and explanations

- Missing medium, water, alcohol or generic polar-aprotic medium does not
  qualify cooled dibromide 3D. Water capture is explained as possible
  bromohydrin chemistry; no bromohydrin product is invented.
- Added acid, metal, radical or other activation is not silently treated as
  neutral electrophilic Br₂ addition. Existing radical structural rejection
  remains in force.
- Unknown input fields and explicit oxidation-stage/work-up settings do not
  silently qualify this model. They are reported by their actual field, not
  incorrectly blamed on cooling. Existing persistent alkyne-equivalent and
  finite-chain selectors are explicitly not applicable to this alkene model;
  they do not change its 1:1 stoichiometry.
- Existing conjugation, ring, aromatic-adjacent, near-site stereochemistry,
  intramolecular-capture, spectator and multiple-site restrictions remain.
  Cooling never overrides a structural or product validation failure.
- Existing anti outcomes, mapped stereochemical alternatives, meso
  deduplication and distant physical configuration retention remain. Unknown
  alkene geometry is not converted into an invented stereochemical claim.
- No full bromonium mechanism was added. Net bond changes and existing
  mechanism-availability wording remain honest about that limitation.
- Calculator quantities remain theoretical complete-conversion arithmetic,
  not predicted experimental amounts or additive yields of alternatives.

## Chemistry evidence and inference limits

The primary sources establish that cooled alkene/Br₂ dibromination is feasible;
they do not experimentally validate every structure accepted by the engine.

1. [Organic Syntheses, “1,2-Dibromocyclohexane”](https://www.orgsyn.org/demo.aspx?prep=CV2P0171),
   DOI 10.15227/orgsyn.012.0026, documents cooled cyclohexene/Br₂ addition.
   Its historical medium includes a small alcohol additive; it is **not**
   evidence that all dry or alcohol-containing media are inert. The notes also
   acknowledge substitution competition despite cooling.
2. Amrani and Aizenshtat, [“Mechanisms of sulfur introduction chemically
   controlled: δ³⁴S imprint”](https://doi.org/10.1016/j.orggeochem.2004.06.019),
   Organic Geochemistry 35 (2004), 1319–1336, experimental §2.1, documents
   cooled Br₂ addition to 1-hexene in a non-capturing medium to prepare
   1,2-dibromohexane. The study reports NMR/GC/GC-MS verification of prepared
   substrate identities. [Accessible primary manuscript](https://repository.geologyscience.ru/bitstream/handle/123456789/39625/Amra_04.pdf?sequence=1).

Applying this qualitative cooling compatibility to the **already screened**
alkene dibromination net model is a bounded modeling inference. It is not a
new universal substrate or solvent claim, an experimental protocol, or a
claim that cooling guarantees a pure dibromide. No laboratory recipe or
new solvent selector was introduced.

## Verification

New backend checks use independent connectivity and stereochemical fixtures,
not products copied from generated conformers. They cover ethene, propene,
longer/branched/internal alkenes, E/Z butenes, cyclohexene, styrene, screened
remote alcohol/ether groups, distant chirality and separated/equivalent sites.
Assertions check actual mapped 3D output, anti configurations, charge/atom
conservation, hydrogen and bromine provenance, bond changes and stoichiometry.
Negative fixtures cover competing structures, media, activation, malformed or
unrelated conditions and other cooled pathways. Authenticated HTTP match,
diagram and run checks include condition changes and stale option IDs.

- New backend tests: 31 passing.
- New frontend tests: 14 passing; legacy post-run lifecycle behavior preserved.
- Final full regression suites: 1,973 Python tests and 1,990 JavaScript tests
  passing (3,963 total), preserving the 3,918-test baseline and adding 45 tests.
  TypeScript and the production build pass. Existing bundle-size/dependency
  directive warnings remain; no new build failure. Scoped whitespace checks
  pass.
- The 347-case frozen audit was rerun before and after. All case IDs, results,
  actual products, statuses, pathway summaries, variants and supplementary
  results are identical; only the production-source hash changes. Bromination
  retains 9/14 fully supported frozen cases (64.3%). The frozen inputs contain
  no cooled cases, so this increment is measured by separate cooling tests,
  not by inflating that benchmark.
- Frozen totals remain 155 fully supported, 90 unsupported, 38 correctly
  rejected, 63 partially supported and one pre-existing incorrect-result
  classification. This change does not create or resolve that known frozen
  issue, nor certify universal chemistry correctness.
- Browser: cooled ethene + Br₂ generates 1,2-dibromoethane in linked 2D/3D;
  existing zoom/rotation controls work. Selecting water clears the 3D result
  and disables run/compare with a solvent-specific explanation. Returning to
  dry/none restores 3D permission without changing the selected cooling value.
- At 320px, the document width is 320px; cooling and activation controls and
  explanations remain accessible through the existing Inspector.

Screenshots: `history/cooled-bromination-3d-2026-10-24.png` and
`history/cooled-bromination-mobile-2026-10-24.png`.

UI/UX Pro Max informed the status wording and feedback hierarchy only; no
layout, CSS or new control was introduced in this increment. Browser QA used
isolated localhost services; the user's existing preview was not interrupted.
Restart the existing local chemistry server before trying these backend
changes there. No Git push, merge, Render or frozen-beta update was performed.
