# Cooling and clearer condition inputs

Historical first increment. The blanket cooled-3D restriction below is now
superseded **only for eligible alkene Br₂ addition** by the separately reviewed
[`cooled-alkene-bromination-v1` policy](cooled-alkene-bromination-3d.md).
Other cooled pathways retain their existing restriction.

## Controls

- Temperature now includes **Cooled / Low Temperature** (`cooled`), distinct
  from unspecified, ambient and heated. No numeric range is inferred.
- **Additional Catalyst / Activation** replaces the ambiguous shorter label.
  Existing serialized activation values remain unchanged; labels explain acid
  activation/catalysis, metal, Lindlar, Os and radical-initiation roles.
- **Molecule 2 · Reagent / Partner** explains that the chosen chemical may be
  consumed, act as solvent, or act as catalyst depending on the pathway.
- Linked, keyboard/screen-reader-accessible help explains that hydroxide is
  an actual chemical input in the supported base-driven reactions. No generic
  base-catalysis option, new reagent or reaction family is introduced.

## Cooling confidence boundary

Cooling is accepted and preserved in requests, saved conditions, summaries and
Guided Conditions. It is never normalized to ambient or heated.

No specific low-temperature profile has been independently validated in this
increment. Consequently a small shared confidence overlay keeps structurally
supported conditional 2D options, mechanisms and theoretical arithmetic, while
blocking asserted 3D/run output under cooled conditions. This is an output
confidence limit, not a claim that the chemical reaction is impossible or
unfavorable. It does not add temperature-dependent rates or selectivity.

Matching, diagram and run APIs, grouped product choices and calculator context
all use the same assessment. Stronger missing-activation and unimplemented
primary-aldehyde endpoint limits remain visible. Previous reference-match
notes are explicitly scoped to other settings, excluding unvalidated cooling.
Lindlar guidance preserves cooling rather than silently clearing it; an existing
secondary-oxidation guide may explicitly propose its supported ambient profile
only through the existing user-reviewed confirmation flow.

Unspecified/ambient/heated behavior, products, atom mapping, stereochemistry,
stoichiometry, reaction rules and calculator arithmetic remain unchanged.

## Verification

- Full Python regression run: 1,941 passing tests (includes the first 37 new
  cooling tests). A final additional note-scoping regression brought the new
  focused file to 38/38 passing; all 38 were rerun after that last wording fix.
- Full JavaScript regression run: 1,976 passing, including 14 new controls tests.
- TypeScript and production build pass. Existing dependency directive/chunk
  warnings remain; no new build failure.
- Whitespace checks pass.
- The fixed 347-case audit retains exactly the same case IDs, statuses, actual
  product structures and pathway coverage summaries. No benchmark input was
  modified. Both before/after runs retain 155 fully supported, 90 unsupported,
  38 correctly rejected, 63 partially supported and 1 pre-existing incorrect
  result classification; this increment did not create or resolve that baseline
  issue and does not certify universal chemistry correctness.
- Live browser: SN2 bromomethane/hydroxide remains a mapped 2D option with
  cooling selected; 3D controls disable with explicit guidance. Switching to
  ambient restores the original 3D workflow and generates methanol normally.
- At 320px the document width remains 320px, and the selected cooling value and
  associated help remain accessible.

Screenshots: `history/reaction-cooling-conditions-desktop-2026-10-23.png` and
`history/reaction-cooling-conditions-mobile-2026-10-23.png`.

Local implementation only. No Git push, merge, Render change, frozen beta
update or publication. Browser QA used temporary isolated localhost services;
the user's existing local preview was not interrupted. Restart the existing
local chemistry service before trying the new backend condition there.
