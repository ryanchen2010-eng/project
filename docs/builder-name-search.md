# Builder molecule-name loading

Builder now offers **Load a Molecule by Name** above the editable Ketcher canvas.
Submit a name to the existing authenticated, bounded `/api/pubchem/search`
endpoint, check the returned name/formula/CID and choose **Load into Builder**.
Results are not automatically selected, even when only one match is returned.
No molecule is inferred from a molecular formula or substituted for an isomer.

The exact returned canonical isomeric SMILES is passed unchanged to Ketcher.
The selected structure is editable; **Check + preview 3D** remains the existing,
separate chemistry validation workflow. A name match does not guarantee a
reliable 3D model for a salt, metal compound or other unsupported structure.
This feature requires the existing chemistry service and PubChem connectivity.

## State and drawing safeguards

- Name loading is enabled only after editor initialization, saved-draft restoration
  and startup focus suppression finish.
- Nonempty canvases require explicit replacement confirmation. Cancellation,
  no results and search failures do not alter the drawing or existing preview.
- Query edits abort and invalidate old searches. Out-of-order results cannot
  revive stale choices. Searches are explicitly submitted, capped at 20 results,
  and time out after 35 seconds.
- During import, the editor is inert and example/preview/transfer actions are
  locked. Successful import clears stale 3D, measurement and transfer state,
  and saves through the existing draft mechanism.
- Ketcher parses before replacing its micromolecule canvas. An import error
  asks the user to check the drawing; it does not claim transactional rollback.
- The loaded identity summary is invalidated after subsequent manual edits.
- Remote names, formulas, IUPAC names and errors are rendered as plain text.
- Controls are keyboard accessible; full names wrap, results have bounded
  scrolling, and the controls fit a 320px viewport without page overflow.

## Verification

Independent module tests cover readiness, exact identity and stereochemical
SMILES, isomer alternatives, cancellation, competing operations, malformed
payloads, network/timeout failures, stale responses and safe text handling.
Builder measurement/startup tests retain the existing lifecycle safeguards.
Real local browser testing loaded aspirin into Ketcher and generated its 3D
preview (C9H8O4, 180.159 g/mol); ethanol also passed the existing 3D workflow.
Actual Ketcher V2000 exports, read through its Save Structure preview and
independently parsed with RDKit, retained the S center of L-lactic acid and
the E double-bond configuration of trans-2-butene. At 320px the document width
remained 320px, with a 228px input fitting inside the search panel.
All 1,962 JavaScript tests and the TypeScript/production build pass. The full
Python regression suite was not rerun for this frontend-only addition.
No production chemistry rules, public backend endpoints, deployment settings,
frozen beta files or Render service were changed.
