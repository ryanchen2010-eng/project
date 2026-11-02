# Phase 5J — local visual pass

## Scope and protection

Local branch: `codex/ui-ux-improvements-v1`, created from the development checkout with all existing tracked and untracked work preserved. The preceding local product-name/condition-prompt improvements are retained. No GitHub push, merge, Render request, deployment setting or environment-variable change is part of this work.

Frozen local beta reference before work: `e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367`. Git index before work: SHA256 `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`. A UI source backup was captured at `/private/tmp/capstone-phase5j-ui-before.tar.gz`; chemistry/benchmark file hashes were recorded separately for comparison. No release directory was present in this checkout; no release was created, replaced or removed.

## Skill provenance and recommendations

Used installed UI/UX Pro Max from `/Users/rc/.codex/skills/ui-ux-pro-max`, including its full SKILL.md, professional checklist and relevant web quick-reference rules. The installed package does not expose a semantic version in its skill header; identify this copy by its SHA256 recorded in the verification section rather than guessing a version.

Design-system query: `scientific interactive workspace` with variance 3, motion 1, density 7. Its Minimalism/Swiss-style recommendation fits a professional tool. Its generated orange/dark palette and landing-page conversion pattern do **not** fit this established green, multi-tool application. A narrower `scientific laboratory dashboard` retry did not produce a better product fit; its neumorphic effect was also rejected. Retained the verified functional, high-contrast, low-decoration principles and adapted them to the existing architecture. Targeted searches covered unobscured keyboard focus and actionable error recovery.

Actual stack: Vite, TypeScript, vanilla DOM/CSS, Python/RDKit backend. React is used only by the embedded Ketcher editor. No UI framework, font CDN, animation dependency or icon package was added.

## Original visual audit

- Every page independently defined its header/navigation. Labels varied between short names and long arrow-suffixed actions.
- Large serif utility headings and heavy gradient/shadowed surfaces occupied space needed for scientific controls.
- Many functional labels and helper messages were 10–12px. Several compact buttons were below a comfortable touch size.
- Reaction conditions lacked a clear visual grouping. The example collection and matching results competed for attention.
- Selected reaction cards shared the same green appearance even when their previews were conditional; explanatory text existed but lacked visual hierarchy.
- Viewers relied on drag/scroll gestures without visible camera alternatives.
- Existing responsive layouts and chemistry-confidence gates were valuable and should be retained, not replaced.

## Adapted design system

Source of tokens: `src/ui-system.css` (loaded after existing page/component styles).

| Role | Value / rule |
| --- | --- |
| Brand | Existing forest green `#315c4b`; white labels |
| Canvas / surface | `#f3f6f4` / `#ffffff` |
| Secondary surface | `#f7f9f8` |
| Text / secondary text | `#182f26` / `#52665c` |
| Control boundary | `#7d9386` |
| Focus | Blue `#235fba`, 3px outline plus 3px offset |
| Conditional / attention | Amber `#80500d` on `#fff7e8`; explicit text retained |
| Error | `#a33232`, text plus visible boundary |
| Spacing | 4, 8, 12, 16, 24, 32px |
| Corners | 8px controls; 12px sub-panels; 16px main workspaces |
| Typography | System sans for tools; restrained existing serif Home headline |
| Type scale | 12px metadata, 13–15px helper/control text, 16px mobile inputs, 20–26px panel headings, 32–48px utility page titles |
| Numeric output | Tabular figures; existing units and precision unchanged |
| Motion | 120ms color/border feedback only; no scroll reveals or auto-spin; reduced-motion override |

Component rules: visible labels; native controls; 44px minimum action/input height outside Ketcher; visible current-page state; wrapping navigation rather than hiding tools; keyboard skip links; legends and explicit confidence wording rather than color alone. Do not recolor atoms, bond-change legends, mechanism electron colors or stereochemical diagrams to match the brand.

## Implemented first pass

- Shared visual layer across all five existing pages, consistent navigation labels and current-page styles.
- Flatter light surfaces, restrained shadows, smaller utility titles, clearer typography and form grouping.
- Reaction Lab retains its two-panel layout, all existing fields, options, examples and gates. Added a static three-stage workflow cue and a semantic reaction-conditions fieldset.
- Conditional reaction-card selection uses amber rather than an apparently successful green; existing backend confidence labels and restrictions remain authoritative.
- Clearer Guided Conditions review panel, mechanism/measurement controls, equation and theoretical-result presentation.
- Visible camera-only fit/zoom/rotation buttons for Explorer, Builder and Reaction Lab, disabled until a genuine 3D model is ready. No auto-rotation, atomic coordinate modification or 3D-confidence bypass. Camera calls follow the [3Dmol GLViewer API](https://3dmol.org/doc/GLViewer.html).
- Home cards, Explorer search/information, Builder wrapper and Calculators receive safe shared improvements. Ketcher internal controls are excluded.

## Screenshots

| View | Before | After |
| --- | --- | --- |
| Home | [Before](ui-phase5j-home-before.png) | [After](ui-phase5j-home-after.png) |
| Explorer | [Before](ui-phase5j-explorer-before.png) | [Overview](ui-phase5j-explorer-overview-after.png), [measurement](ui-phase5j-explorer-after.png) |
| Builder | [Before](ui-phase5j-builder-before.png) | [After](ui-phase5j-builder-after.png) |
| Reaction Lab | [Before](ui-phase5j-reaction-before.png) | [Selected pathway](ui-phase5j-reaction-after.png), [final overview](ui-phase5j-reaction-final-overview.png) |
| Calculators | [Before](ui-phase5j-calculators-before.png) | [After](ui-phase5j-calculators-after.png) |
| 320px phone | [Before](ui-phase5j-mobile-before.png) | [Overview](ui-phase5j-mobile-after.png), [populated 3D result](ui-phase5j-mobile-result-after.png) |

Additional checks: [linked atoms/mechanism](ui-phase5j-reaction-linked-after.png), [guided review and confirmation](ui-phase5j-guided-review-after.png). Screenshots capture local UI states, not the live beta. Builder baseline was captured during editor initialization; its final generation/transfer workflow was separately exercised after initialization.

## Files changed in this phase

- New shared presentation: `src/ui-system.css`.
- New camera-only component: `src/viewer-controls.ts`.
- Imports, camera lifecycle and navigation/skip-link markup: `src/main.ts`, `src/builder.ts`, `src/reaction-lab.ts`, `src/calculators.ts`.
- Shared stylesheet/skip-link/navigation markup: `index.html`, `calculators.html`.
- Nine new UI/camera regression tests: `tests/ui-phase5j.test.mjs`.
- Added the camera-control dependency to isolated lifecycle test fixtures in `tests/builder-measurements.test.mjs`, `tests/explorer-ionic.test.mjs`, `tests/reaction-measurements.test.mjs`; existing assertions were not removed or weakened.
- This report and the screenshot files listed above.

No existing page CSS was replaced. No backend, chemistry arithmetic, atom inspector, reaction-conditions logic, Guided Conditions logic, diagram generator, scientific dataset, visible example collection, deployment configuration or benchmark source changed in this phase.

## Verification

Completed locally on 2026-10-22:

| Check | Result |
| --- | --- |
| Python regression suite | **1,895 passed** (`.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`) |
| JavaScript regression suite | **1,897 passed**, zero skipped/failed (`node --test tests/*.test.mjs`) |
| Total | **3,792 passed** — previous 3,783 plus 9 new UI tests |
| TypeScript + production build | **Passed** (`pnpm build`, which runs `tsc && vite build`) |
| Frozen 347-case audit | **Unchanged**, zero changed case-status rows against the recorded beta baseline |
| Audit breakdown | 155 fully supported; 63 partial; 90 unsupported; 38 correctly rejected; 1 existing incorrect-result benchmark row |
| Frozen audit source SHA256 | `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55` |
| Chemistry/benchmark source integrity | All **51** pre-recorded file hashes match after testing |
| Source preservation | All **45** actual original UI source files remain; six intentionally updated, no original files removed (tar-generated AppleDouble metadata excluded) |
| Frozen beta ref / Git index | Both unchanged from the values above; only the requested new local branch was created |
| Whitespace | `git diff --check` and explicit new-file trailing-whitespace scan passed |

Skill copy fingerprint: `SKILL.md` SHA256 **`c5ee968793ba605104a218afcc740da1179e4db52e8b5f326f833547c27e5332`**. No semantic version was available locally.

The audit's existing incorrect-result row remains A304, the previously documented frozen expected-product defect; this visual phase neither changes nor reclassifies it. Finite regression results do not establish universal chemical correctness.

### Browser and accessibility checks

- Chrome: all five pages checked at **320×800, 375×812, 768×1024, 1024×768 and 1920×1080**, plus the normal 1414px desktop viewport. No document-level horizontal overflow at any tested size. The temporary viewport override was reset.
- Populated SN2 comparison also checked at 320px: document width 320px, viewer width 260px; the larger 2D SVG remains inside its existing horizontally scrollable diagram region, not the page.
- New camera buttons measured at least **44×44px**. Native Tab/Enter reached the skip link and focused `main-content`. Focus indicators and visible labels were checked. Shared text/background contrast pairs pass 4.5:1; focus/control-boundary pairs pass 3:1. Reduced-motion rules are covered by source tests; an OS reduced-motion session and formal screen-reader audit were not performed.
- SN2: mapped methanol 2D/3D generation, camera fit/zoom/rotation, selected carbon linked to both 2D occurrences and the 3D label, mapped concerted mechanism and electron-movement descriptions remained working.
- Guided Conditions: both **secondary NaOCl/acetic-acid oxidation** and **H₂/Lindlar partial reduction** were checked before and after confirmation/apply. Missing settings blocked 3D. Applying required approval and backend revalidation. Lindlar preserved unspecified medium and temperature. The resulting theoretical/conditional warnings remained visible.
- Explorer: water 3D and camera controls; list-selected O–H distance **0.969 Å**; sodium chloride remains information-only with the viewer/camera controls hidden and the correct 58.443 g/mol information.
- Transfers: Explorer water → Calculators retained exact identity/mass; Builder ethanol → Reaction Lab retained ethanol after catalog initialization. Ethanol plus the retained hydroxide input correctly did not invent a supported SN2 reaction.
- Builder: ethanol checked/generated as C₂H₆O, 46.069 g/mol, 9 atoms, 8 bonds, MMFF94; camera controls and transfer remained working. Visible Ketcher toolbar buttons retain their internal 28px sizing while the outside primary action is 44px. Internal drawing behavior was not restyled.
- Calculators: 18.015g water → **1 mol**, **6.02214e+23 molecules**; 5.8443g NaCl in 100mL → **1 mol/L** with solubility/suitability disclaimer; SN2 with 0.1mol bromomethane + 0.2mol hydroxide → bromomethane limiting, **0.1mol / 3.2042g theoretical methanol**, with theoretical-only warning.

### Failures and warnings

The initial new contrast test found that the first control-border token fell below 3:1; it was darkened and retested successfully. The first JavaScript run also exposed missing camera-control stubs in three isolated test harnesses; those dependencies were added without changing the existing assertions, and the full suite was rerun successfully.

The production build still warns about the pre-existing large Ketcher bundle. The browser recorded a Grammarly extension error, not an application error. No application console error was observed in the exercised workflows. A browser zoom shortcut attempt did not change the effective viewport, so it is **not** counted as a verified high-zoom test.

Detailed command logs are available for this local session at `/private/tmp/capstone-phase5j-python.log`, `/private/tmp/capstone-phase5j-js-verified.log`, `/private/tmp/capstone-phase5j-build-final.log`, and `/private/tmp/capstone-phase5j-audit.json`.

## Local preview

Run `"/Users/rc/Documents/Capstone project/start-local.command"` and open `http://127.0.0.1:5173/`. This local design does not change the hosted beta. Review locally before authorizing any future push or deployment.

## Later iterations / known scope limits

- Do not equate these smoke checks with a full accessibility certification or exhaustive chemistry proof.
- Dark mode is not introduced; the established light interface is explicit.
- Major rearrangement of the example collection, sticky panels and a shared navigation component are deferred to avoid changing workflows in this first pass.
- Ketcher mobile toolbar accessibility remains controlled by the editor, not patched with global CSS.
- More complete screen-reader, real-device and high-zoom testing can follow after visual review.
- Reaction explanations remain lengthy where necessary to preserve confidence limitations. A later progressive-disclosure pass could reduce scanning effort without hiding missing conditions or theoretical-result warnings.
- Panning still uses the existing viewer gesture; fit/zoom/two-axis rotation now have buttons. Broader viewer keyboard shortcuts and 2D diagram zoom controls are future work.

**Stopped after Phase 5J. No commit, push, merge, publication or Render change was made.**
