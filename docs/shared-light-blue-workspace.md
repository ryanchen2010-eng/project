# Shared light-blue workspace

Implemented locally on 22 October 2026 on `codex/ui-ux-improvements-v1`.

## What changed

Home, Explorer, Builder and Calculators now match the approved light-blue Professional Research design. All five pages use `src/workspace-shell.ts` for the same brand, route links, vector icons and active-page treatment. `src/workspace-shell.css` supplies the shared blue surfaces, typography, controls, spacing and responsive navigation. Reaction Lab keeps its specialized workbench and scientific confidence controls.

- **Home:** matching navigation rail, blue/white entrance panels, consistent tool cards and vector icons. All four tool links, the labeled water illustration and model limitations remain.
- **Explorer:** blue search library, compound cards, molecular-viewer background and information panels. Full identity wrapping, 2D/ionic fallbacks, measurements, solution calculator and cross-page transfers remain.
- **Builder:** matching app wrapper, model preview and result facts. Ketcher's internal controls, chemical colors, startup focus guard, drawing restoration, structure checks and reaction transfers remain.
- **Calculators:** matching topic menu, compound context, inputs, results and assumptions. All six existing topics remain. The compact native topic selector now appears sooner on narrower screens so the application rail does not crowd the tool.
- **Reaction Lab:** existing navigation construction is reused through the common shell rather than duplicated. Its chosen layout, mechanisms, condition guidance and eligibility gates are unchanged.

The shell moves existing links rather than cloning them or replacing their behavior. It does not read/write chemistry data, storage, reactions or calculations. Initialization is idempotent. Home's small new module supplies presentation only; it does not load Ketcher, RDKit or the 3D viewer.

## Design guidance

UI/UX Pro Max informed the modular grid, consistent hierarchy, accessible contrast, native controls, visible focus and reduced-motion treatment. A generic design-system recommendation was off-target and was not adopted; a narrower Swiss Modernism style search matched the professional grid direction. The user's existing light-blue selection remained the palette reference. Scientific atom/bond colors and semantic validation errors were not made blue.

## Verification

| Check | Result |
|---|---|
| Python regressions | 1,904 passed |
| JavaScript regressions | 1,922 passed, including 10 new shell tests |
| Total | **3,826 passing tests**; all 3,816 previous tests preserved |
| TypeScript + Vite production build | Passed |
| Whitespace | `git diff --check` passed |

Existing dependency `use client` and large-bundle warnings remain non-fatal. The fixed chemistry audit was not changed or rerun for this presentation-only increment.

### Browser checks completed

- Home's four tool links and shared five-route navigation are present; the active page is preserved.
- Home, Explorer and Builder have no page-wide horizontal overflow at 320, 390, 768 and 1024 CSS pixels, and were visually inspected at 1440 px.
- All six calculator topics render their existing controls. Each topic was checked at 320, 390, 768 and 1024 px without page-wide overflow; the mobile selector changes topics correctly.
- Explorer's water model supports list-based atom selection and reports the displayed-model O–H distance, 0.969 Å. Measurement semantics remain explicitly model-based.
- Changing to ethanol resets the selection. The solution calculator gives 1 mol/L from 46.07 g with the selected 46.07 g/mol identity and 1000 mL final volume.
- Explorer → Calculators preserves ethanol's identity and 46.07 g/mol molar mass. The mole converter gives 1 mol and 6.02214e+23 molecules from 46.07 g.
- Calculator validation still displays an explicit error; “Enter molar mass.” retained red `rgb(163, 50, 50)` styling rather than becoming muted blue.
- Builder initializes at `scrollY = 0` with the startup guard released. Loading ethanol and generating 3D returns C2H6O, 46.069 g/mol, 9 atoms, 8 bonds and the existing MMFF94 method. The exact values are the existing backend's, not theme substitutions for the Explorer data.
- Reaction Lab still matches bromomethane/hydroxide, generates methanol, displays the balanced mapped equation and 14 net-view atom targets, and opens its concerted SN2 mechanism and reaction-amount calculator. No duplicate DOM IDs were found. This increment did not rerun Reaction Lab's mobile Compare checks: the browser approval connection became unavailable during the final optional replay. Those sizes were verified in the immediately preceding Reaction Lab layout increment; the current regression tests pass.

### Real screenshots

| Page | Desktop | Mobile |
|---|---|---|
| Home | [Desktop](../history/blue-home-desktop-2026-10-22.png) | [390 px](../history/blue-home-mobile-2026-10-22.png) |
| Explorer | [Desktop](../history/blue-explorer-desktop-2026-10-22.png) | [390 px](../history/blue-explorer-mobile-2026-10-22.png) |
| Builder | [Desktop](../history/blue-builder-desktop-2026-10-22.png) | [390 px](../history/blue-builder-mobile-2026-10-22.png) |
| Calculators | [Desktop](../history/blue-calculators-desktop-2026-10-22.png) | [390 px](../history/blue-calculators-mobile-2026-10-22.png) |

## Preservation

SHA256 comparison of all 173 pre-existing files returned by `rg --files server benchmarks tests` found **zero changes**. Only the new `tests/workspace-shell.test.mjs` was added in those directories. No calculation modules, compound records, example definitions, chemistry backend, deployment settings or benchmark inputs were edited. Existing dirty working changes were preserved.

No staging, commit, push, merge, Render action or frozen-beta update was performed. Repository references and Git index remain:

- HEAD `fa00ac9acc75b82e0df4e57148755a904dc80cec`
- main `1635a3f5131a48603b30af474f9f555b6643d1a3`
- frozen beta `e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367`
- index SHA256 `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`

This is a local presentation update. The live Render Beta remains unchanged. Passing these finite checks is not a claim of universal chemistry correctness.
