# Light-blue Professional Research workspace

Date: 22 October 2026. Implemented locally on `codex/ui-ux-improvements-v1`.

## Approved scope

The user selected Phase 5K's **Professional Research Interface** and explicitly approved applying it to the actual Reaction Lab, not just the mockup. The requested blue color scheme, Builder navigation jump and Explorer long-name overflow are included. The earlier Phase 5K document remains a historical proposal, not a description of this implemented state.

No push, merge, commit, Render action or frozen-beta update was performed. Existing unrelated working changes were preserved.

## Changes

- Light-blue navigation rail, compact live reactant row and stable central chemistry workspace.
- Existing pathway controls in a collapsible selector; the selected mechanism remains named when collapsed. Selecting a pathway returns keyboard focus to its visible summary; background rematches do not steal focus. New/unrecognized inputs reopen pathway explanations.
- Product, mapped-atom and Conditions inspector. It is open by default on desktop and collapsible above the visualization on smaller screens.
- Real existing examples and reaction guide in native dialogs, without adding examples or copying static mockup results into the application.
- Existing 2D, 3D, Compare, measurements and atom-selection controls retained. Camera backgrounds now match the light-blue palette; molecular coordinates and chemical colors were not changed.
- Mechanism, reaction-amount and functional-group tools in an adjacent dock. Reactant shortcuts to Calculators are under Reaction amounts. Hiding an open mechanism clears its electron-role highlights from the net view.
- The exact confidence tier stays visible. Its full explanation remains available in a native disclosure, with Review conditions opening the actual settings. Repetitive long warnings were removed from the short status line, not from the scientific explanation or diagram notes. Missing-setting prompts now refer to Edit conditions rather than the old layout's “above.”
- Builder temporarily makes only the initializing Ketcher host inert through initialization/draft restoration and two animation frames. It does not force scroll position, steal focus, patch Ketcher or change editing/generation logic.
- Explorer wraps full systematic names and formulas in the title and result cards. No identity text is truncated or substituted.

`src/reaction-workspace.ts` reparents the existing live DOM nodes before the original event bindings run. Chemistry matching, confidence gates, atom correspondence, calculation arithmetic and API behavior remain in their existing modules. The new CSS is scoped to Reaction Lab; Explorer and Builder retain their current page designs.

## UI/UX Pro Max influence

Used its grid/hierarchy, visible-focus, compact-label and contrast guidance. The general design-system search included off-target portfolio framing, which was not adopted. A narrower Swiss Modernism style search confirmed the modular professional grid and Inter typography fit. The user's selected layout and light-blue preference took precedence over generic palette recommendations. Native grouped buttons and disclosures retain standard keyboard behavior; no custom tab-key trap or new UI dependency was introduced. Semantic confidence, bond-change and atom-highlight colors were preserved.

## Verification

| Check | Result |
|---|---|
| Python regression suite | 1,904 passed in 229.133 s |
| JavaScript suite | 1,912 passed, including 12 new checks |
| Total | **3,816 passed**, preserving the 3,804-test pre-change baseline |
| TypeScript and Vite production build | Passed |
| Whitespace | `git diff --check` passed |

Build warnings about dependency `use client` directives and large Ketcher chunks remain; they are not build failures.

New tests cover editor startup/release/restoration integration, live-node layout contracts, native dialogs and inspector relationships, confidence disclosures, mechanism containment, rejection visibility, focus handling, full-name wrapping, scoped responsive styling and measured AA text contrast.

### Real browser checks

- SN2 bromomethane/hydroxide: public matching, selected equation, 2D, generated methanol 3D, Compare and mapped carbon selection work. No duplicate DOM IDs were found.
- Bromoethane/hydroxide still offers separate SN2 and E2 options. Selecting E2 displays the existing elimination equation.
- Reaction calculator: 94.939 g bromomethane and 17.007 g hydroxide give 1 mol / 32.042 g theoretical methanol; switching to the mechanism preserves the existing concerted SN2 steps. Switching away closes mechanism highlights.
- Secondary-alcohol oxidation remains conditional 2D with disabled 3D before qualification. Review conditions exposes the existing Guided Conditions checklist, requires explicit replacement confirmation, and enables 3D only after applying the supported settings and backend rematching.
- Entering an unrecognized reagent clears the prior product/diagram and disables 3D while reopening the rejection explanation.
- Compare measured without page-wide horizontal overflow at 320, 390, 768, 1024, 1250 and 1440 CSS pixels. Narrow 2D diagrams retain their own local scroll region. Camera controls remain in the correct column when Compare stacks.
- Builder initial and restored-draft navigation both finish at `scrollY = 0`, with the editor no longer inert. Loading ethanol and generating its 3D preview still work.
- Explorer's real `ryan` PubChem result, the 181-character systematic name from the user's screenshot, fits both title and search card. At 1440 px: title client/scroll width 699/699 and card 182/182. At 320 px: title 256/256 and card 115/115. Full text is retained.
- Keyboard skip link reaches the workspace. Native example dialog focuses its Close button. Responsive inspector opens/collapses across the desktop breakpoint.

### Captures

- [Actual desktop Reaction Lab](../history/reaction-research-light-blue-desktop-2026-10-22.png)
- [Actual mobile Reaction Lab](../history/reaction-research-light-blue-mobile-2026-10-22.png)
- [Explorer long-name fix](../history/explorer-long-name-fixed-2026-10-22.png)
- [Builder restored startup](../history/builder-startup-fixed-2026-10-22.png)

## Preservation

No chemistry server, reaction rule, RDKit, molecular identity, stereochemistry, mapping algorithm, stoichiometry, calculation module, benchmark, deployment file or curated example definition was edited in this increment. The fixed 347-case benchmark was not rerun for this presentation-only work; the complete existing regression suites were rerun. The unchanged finite tests are not a universal chemistry guarantee.

Verified unchanged repository references:

- HEAD: `fa00ac9acc75b82e0df4e57148755a904dc80cec`
- main: `1635a3f5131a48603b30af474f9f555b6643d1a3`
- frozen beta branch: `e3fb8a3c9e91690bfc4c9df64a3e323f5b46b367`
- Git index SHA256: `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`

The live Render Beta v1 remains unchanged. This local UI update still needs the user's visual review before any separate release/deployment request.
