# Consolidated xTB validation

## Experimental scope

Using local xTB 6.7.1/GFN2, `tests/explorer_xtb_independent_pilot.py` tests eight reproducible random ligand orientations for each of nine neutral, zero-unpaired-electron models. Starting coordinates are heuristic, independently randomized rather than derived from reference coordinates, but the ligand graph, atom identities and approximate bond lengths are specified in advance. Results depend on these starting assumptions; this is not a representative sample of molecules or conformer space.

The pilot compares distances and sorted central angles with source geometries using exploratory 0.12 Å/8° tolerances. It checks atom element/order and conservative mapped-bond distances. This is not full graph reconstruction, does not rule out new bonds, and cannot establish actual charge/spin or stereochemistry; no charged, open-shell or stereogenic cases were tested. AlCl₃ and SF₆ references are NIST experimental-geometry-derived models; ZrCl₄ is an idealized reconstruction; water is reference-based; NIST Fe/Ni/Cr carbonyls, SO₃ and NH₃ are calculated. The reference-based structures should not be conflated with xTB-generated coverage. The source data for this research is locally cached, excluded from Git, and must be acquired from the NIST URLs before replay.

| Geometry / model | Passing starts |
| --- | ---: |
| Water, bent | 8/8 |
| NH₃, pyramidal | 8/8 |
| AlCl₃, planar | 8/8 |
| SO₃, planar | 1/8 |
| ZrCl₄, tetrahedral | 8/8 |
| Ni(CO)₄, tetrahedral | 8/8 |
| Fe(CO)₅, trigonal bipyramidal | 7/8 |
| Cr(CO)₆, octahedral | 8/8 |
| SF₆, octahedral | 8/8 |

These are per-case results, not validated class-wide success rates. All 72 optimizations reported convergence; 64/72 met the exploratory geometry checks. SO₃ had seven mismatches despite convergence, illustrating sensitivity to the start and/or local minima; no mechanistic explanation is established by this pilot.

## Fe(CO)₅ failure

The mismatching Fe output had a maximum central-distance deviation 0.171 Å, central-angle deviation 51.90°, and one oxygen 2.127 Å from Fe, compared with other oxygen distances about 2.905–3.032 Å. This is consistent with a non-reference metal–ligand arrangement, not proof of a specific electronic mechanism or a physically characterized isomer. The existing independently authored `validate_carbonyl_sdf` screen, applied to the optimized coordinates on the reviewed graph, rejected this case and accepted the other seven Fe starts. That is one successful detection in a tiny known-geometry sample, not proof that the screen detects every error or prevents false negatives. The generic RDKit geometry validator alone did not establish this coordination identity.

## Decision, coverage, and Render

No generalized automatic xTB class is admitted: insufficient chemically diverse examples per class, unsupported output connectivity/new-bond and stereo validation, unvalidated charge/spin selection, reliance on a known molecular graph and initial radial construction, and no production resource/security assessment. 32-case offline RDKit benchmark remains 13/32 internal-sanity passes; xTB-generated Explorer coverage increased by zero. Existing reviewed NIST/idealized reference fallbacks are separate and unchanged.

The Mac executable is arm64 Mach-O and cannot run inside the current Linux `python:3.12-slim-bookworm` Docker image. [Conda-forge offers Linux builds](https://anaconda.org/channels/conda-forge/packages/xtb/files), so a future separately reviewed Linux build is possible, but not proven on this host: no Docker executable was available, no image was changed or built, and Render runtime, binary dependencies, memory, CPU, concurrency, timeout, subprocess isolation and licensing/package reproducibility remain to be tested. The local .xtb-pilot is not copied to Render.

Nineteen focused Python tests and the 32-case offline replay passed; no full regression suite or Linux/container test was run in this batch. No production resolver, existing chemistry, GitHub or Render changes were made.
