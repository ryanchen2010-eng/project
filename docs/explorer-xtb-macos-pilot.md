# Local xTB geometry pilot

An isolated micromamba environment was installed under `.xtb-pilot/env` (Git-ignored); the existing `.venv` Python 3.14 environment was not modified. The executable reports xTB 6.7.1 on macOS arm64. This environment is not part of the production Docker image and is not deployed.

## Procedure and scope

`PYTHONPATH=. .venv/bin/python tests/explorer_xtb_pilot.py` runs GFN2-xTB optimization with total charge 0 and zero unpaired electrons for five neutral, assumed closed-shell isolated molecules. The input Cartesian coordinates were taken from the very reference geometries used for comparison. Fe/Ni references are NIST-calculated molecular models obtained at the fixed URLs in `server/coordination_reference.py`; their review checks exact metal/CO topology, charge and coordination shape. The remaining starting coordinates are the existing water reference, NIST-derived AlCl₃ geometry and idealized tetrahedral ZrCl₄ reconstructed from an experimental distance. The Fe/Ni SDF files are downloaded into the ignored pilot folder and are not distributed with the project.

All five optimizations reported convergence and preserved atom element/order. The analysis compares all original mapped bond distances and sorted central bond angles. XYZ output contains no bonds, so these checks do **not** prove full output connectivity or exclude newly formed bonds; no stereogenic examples or charged/open-shell structures were tested. Net input charge and spin are assumptions, not independently validated charge distributions; partial charges and alternative spin states were not compared. Angles and distances are comparisons to different kinds of references, not uniform experimental error estimates.

| Case | Reference / shape | Largest central distance difference | Largest central angle difference | Largest mapped bond distance difference |
| --- | --- | ---: | ---: | ---: |
| H₂O | reference-based bent | 0.001 Å | 2.78° | 0.001 Å |
| AlCl₃ | NIST-derived trigonal planar | 0.030 Å | 0.00° | 0.030 Å |
| ZrCl₄ | idealized tetrahedral based on 2.32 Å experimental distance | 0.069 Å | 0.00° | 0.069 Å |
| Fe(CO)₅ | NIST-calculated trigonal bipyramidal | 0.040 Å | 0.05° | 0.040 Å |
| Ni(CO)₄ | NIST-calculated tetrahedral | 0.005 Å | 0.02° | 0.014 Å |

Results are rounded. Because optimization starts at each reference, agreement does not demonstrate reliable conformer generation from a selected PubChem graph; metal–ligand coordination, ambiguity, missing bonds, molecular stereochemistry and physical form still need separate handling. No general chemical class was validated for automatic Explorer fallback. Charge/spin selection, output connectivity/stereo validation, robust starting geometry, network-independent runtime packaging, runtime limits and negative tests are required before integration. Isolated RhCl₃ was not inferred from its solid phase. xTB's spin limitations are described in [its documentation](https://xtb-docs.readthedocs.io/en/latest/spgfn.html).

The frozen 32-case offline generator audit remains 13/32 internal sanity-validated RDKit results; no xTB output is integrated, so the change in Explorer coverage is zero. This denominator includes ionic and invalid controls and does not measure live PubChem/NIST/reference availability. Seventeen focused Python tests passed. No production chemistry, resolver, GitHub or Render changes were made.
