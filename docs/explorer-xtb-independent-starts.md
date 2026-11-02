# xTB independent-start research pilot

`tests/explorer_xtb_independent_pilot.py` tests xTB 6.7.1 GFN2 from eight deterministic, independently randomized radial starts per compound, not rotations or perturbations of known reference coordinates. It uses the reviewed molecular graph to place each ligand around a central atom at a heuristic starting radius; CO is initially radial. This is an informed coordination-specific start, not arbitrary 2D SMILES embedding. It still requires a trusted exact molecular graph, existing reviewed references, and explicit `charge=0, uhf=0` assumptions. No charged, open-shell, chiral, solvent-bound, crystal or multi-metal cases were studied. Input assumptions and spin assignments were not independently established by these runs.

The comparison uses internal exploratory thresholds of 0.12 Å maximum central-bond deviation and 8° maximum sorted central-angle deviation, plus mapped-bond distance bands; they are not a universal accuracy standard. Exact element and atom order are checked; xTB's XYZ has no bond graph. Bond length screens are not a complete connectivity or new-bond test, and stereochemical identity is not tested. Geometry agreement is not a validated rate for a class.

| Case | Reference | Passing starts | Largest observed central-distance deviation | Largest central-angle deviation |
| --- | --- | ---: | ---: | ---: |
| Water | Reference-based bent | 8/8 | 0.002 Å | 2.77° |
| AlCl₃ | NIST-derived planar | 8/8 | 0.031 Å | 0.35° |
| ZrCl₄ | Idealized tetrahedral, experimental distance | 8/8 | 0.069 Å | 0.43° |
| Fe(CO)₅ | NIST calculated trigonal bipyramidal | 7/8 | 0.171 Å | 51.90° |
| Ni(CO)₄ | NIST calculated tetrahedral | 8/8 | 0.006 Å | 2.74° |

All 40 optimizations converged, including the Fe mismatch. A converged calculation can therefore yield a different structure. These starts use net-neutral zero-unpaired-electron input and do not validate partial charges or competing spin states. NIST metal carbonyl coordinates are calculated, not experimental. AlCl₃'s source is [NIST CCCBDB](https://cccbdb.nist.gov/expgeom2x.asp?casno=7446700); the limitations of open-shell treatment are noted in [xTB documentation](https://xtb-docs.readthedocs.io/en/latest/spgfn.html).

No class is admitted into Explorer: one compound and eight closely related heuristic starts per geometry are not enough to establish a reusable class; safe atom/coordination graph reconstruction, nonbonded contacts, stereochemistry, spin/charge selection, independently prepared starts, runtime limits, production packaging and error handling remain unresolved. The unchanged 32-case offline benchmark remains 13 internal RDKit-sanity passes; no new user-facing coverage is claimed. The benchmark includes invalid and ionic controls and does not measure PubChem/NIST live paths.

Nineteen focused tests passed, including reproducibility and unsupported-structure checks. The script requires the separately installed Git-ignored `.xtb-pilot/env/bin/xtb` and two previously downloaded NIST carbonyl reference files. All work is local; no change was made to the production resolver or deployment.
