# Visual focal-point audit — 30 October 2026

Local, first-visit screenshots: 1440 × 900 desktop and 390 × 844 mobile, captured as full-page images. Before/after files are in `history/visual-progress-upload-part-2/`, named by page, viewport and stage. They show default states, not a complete audit of every result or compound.

| Page | Focal point and flow | Findings and decision |
| --- | --- | --- |
| Home | The main headline and Explore action lead to four tool choices. | Clear on both sizes; mobile cards require scrolling but retain understandable labels and the educational-model warning. No redesign. |
| Explorer | Search and selected molecule lead to its viewer and properties. | On mobile the bounded sample list can look cut off. Added a short scroll hint at the stacked-layout breakpoint. Provenance and information remain visible; the long property list still requires scrolling. |
| Builder | Drawing/search inputs lead to Check + preview 3D and the result. | The editor and its primary action are clear; mobile requires scrolling between drawing and preview, an existing limitation. No tools or scientific details removed. |
| Reaction Lab | Reactants lead to pathways and the visual result. | Before selection the empty diagram consumed unnecessary space, especially on mobile. Reduced only the placeholder height; actual diagrams retain their original viewing area. The theoretical-model notice and condition details remain. |
| Calculators | Topic selector leads to inputs and Calculate. | The topic and action are clear; formulas and assumptions remain available in their disclosure, and the model limitation remains visible. No redesign. |

These screenshots represent initial states, not every combination of warnings, data, molecule or reaction. Existing visual hierarchy browser checks cover keyboard disclosure controls and narrow-screen overflow; the audit does not establish full accessibility conformance or scientific correctness of all data.

Verification: all 2,206 JavaScript tests passed; TypeScript and the production build passed; browser hierarchy and keyboard checks passed at 1440 px and 320 px. The build reports a large Builder bundle warning. Screenshots use a separate 390 px mobile viewport; one Reaction Lab after image shows the collection loading, so it should not be interpreted as a completed reaction result. Python chemistry tests were not rerun for this presentation-only change.
