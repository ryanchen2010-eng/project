# Explorer reference database fallback — Step 4

## Source review and scope

NIST CCCBDB publishes an experimental internal-coordinate entry for neutral sulfur hexafluoride (CAS 2551-62-4, charge 0), including Cartesian coordinates derived from the measured S–F distance and octahedral symmetry: [NIST entry](https://cccbdb.nist.gov/expgeom2.asp?casno=2551624&charge=0). PubChem identifies SF6 as [CID 17358](https://pubchem.ncbi.nlm.nih.gov/compound/17358). The bundled SDF transcribes NIST's tabulated coordinates and carries six explicit S–F connections. The UI describes this as an experimental-geometry-derived isolated gas-phase model, not raw crystal coordinates or a condensed-phase structure.

The reusable reviewed-reference registry matches exact CID and exact canonical selected-record graph, and is reached only after the normal PubChem/RDKit endpoint returns 404. It never matches by formula alone or changes the existing ionic-assembly information-only rule. Other records, charged forms, isotopologues, missing identity, and 503 errors do not qualify. Records are deliberately reviewed and bundled locally; no general-purpose live database retrieval or broad source matching is asserted.

NIST WebBook also offers calculated molecular structures, including an iron pentacarbonyl record, but the frozen benchmark's particular RDKit input fails valence parsing and an exact graph/stereo identity bridge to that specific entry has not been established. It is not silently substituted. The RhCl3 crystal record describes an extended solid, not a verified isolated molecular conformer, so it remains unavailable; the existing idealized gas-phase ZrCl4 reference is unchanged. Reference lookup is not a crystal viewer.

## Benchmark comparison

The unchanged 16-case offline benchmark had 8/16 available after Step 3: seven converged RDKit results and the existing idealized ZrCl4 reference. The reviewed exact SF6 reference adds one conditional displayable case: **9/16**, or +1 case (+6.25 percentage points), when the selected record is PubChem CID 17358 with the matching canonical graph and the existing 3D endpoint returns 404. This is a deterministic offline comparison, not a live PubChem availability survey and not a statistical estimate. Two ionic cases are intentionally information-only; the existing 7 calculated models were checked for graph/stereo/coordinate sanity, not independently proven experimentally accurate. The new SF6 reference was checked against the tabulated NIST graph and geometry.
