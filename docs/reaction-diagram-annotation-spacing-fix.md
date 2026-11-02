# Reaction diagram annotation spacing fix

22 October 2026. Local implementation only; no Phase 5K redesign or deployment.

## Changed

- `server/reaction_diagrams.py`: measure RDKit's generated element glyph outlines separately from the small charge/isotope glyphs, center annotations on the element, and reserve space for the entire label. Visible site and selection outlines share a label-sized ellipse instead of concentric fixed-radius rings.
- Lone-pair placement reserves a gap outside the visible halo, checks neighboring labels/highlights, bond strokes, other electron pairs and drawing edges, and retains the original electron counts. The invisible click target is not used as a second visible circle.
- Small disconnected mechanism states (up to four fragments) have separate drawing cells and explicit plus separators. This prevents the original bromomethane/hydroxide overlap. Larger assemblies retain RDKit's existing packing rather than receiving unusably narrow cells.
- `src/reaction-lab.css`: mechanism source/destination colors use the same measured halo. Keyboard focus remains visibly dashed around that halo; the shared rectangular focus outline is overridden only for these SVG atom controls.

No reaction rules, conditions, product generation, identities, atom mapping, stereochemistry, lone-pair bookkeeping, calculator arithmetic, page layout or release settings were changed.

## Verification

- Nine new Python rendering tests and three new frontend style/compatibility tests.
- Tests cover the reported esterification structures, water, hydroxide, methanol, Br/Br⁻, Cl⁻, ammonium, charged multi-letter elements, deuterium, disconnected states, retained input maps/stereo and annotation edge clearance.
- Existing non-SVG output for all 20 curated reaction records was compared against the pre-fix renderer and remains identical, including atom maps, charges and mechanism data.
- Browser checks used the actual public Reaction Lab workflow: esterification; SN2 net and mechanism states; keyboard selection; linked oxygen selection in 2D/3D; 320px page width without horizontal page overflow. An unrelated Grammarly extension error appeared in browser logs; no application error was observed in these checks.
- TypeScript and production build pass. Existing third-party MUI directive and large-bundle warnings remain.
- The fixed 347-case benchmark and its inputs were not changed; no new chemistry coverage score is claimed for this rendering change.

Regression results: **1,904 Python + 1,900 JavaScript = 3,804 passing tests** (12 added to the 3,792 baseline). The final large-assembly guard and focus-style refinement also pass targeted checks. TypeScript and the production build pass. The geometry tests are representative, not a universal guarantee for arbitrary crowded structures or fonts. This change uses RDKit's current path-font output; non-path font output falls back to bounded symbol-based annotation geometry.

## Actual application captures

- [Esterification with selected oxygen](../history/reaction-atom-spacing-2026-10-22.png)
- [SN2 mechanism with Br⁻ and electron-movement highlights](../history/reaction-mechanism-atom-spacing-2026-10-22.png)

UI/UX Pro Max's general spacing, visible-focus and stable-interaction guidance informed the change. Its searches did not supply a chemistry-specific diagram algorithm; glyph measurements and independent geometry regression checks determined the implementation.

The Phase 5K design proposals remain separate and are not implemented by this fix. GitHub, Render and frozen Beta v1 are unchanged.
