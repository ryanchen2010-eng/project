# Molecule Explorer 3D coverage audit — Step 7

## Scope and method

This is a finite, deliberately varied local audit, not an estimate of coverage across PubChem. The frozen 16-case set is unchanged. `tests/explorer_3d_benchmark_v2.json` adds 16 organic, inorganic, organometallic, coordination, charged, ionic, radical and invalid controls; `PYTHONPATH=. .venv/bin/python tests/explorer_3d_audit_v2.py` evaluates all 32. This deterministic offline test measures only the Explorer RDKit fallback, not live PubChem/NIST requests or the separately curated references. It preserves negative and invalid cases in the denominator, so 13/32 is not the rate for eligible molecules.

| Category | RDKit sanity/stereo checks pass | Unavailable | Information-only | Invalid input | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Organic | 8 | 0 | 0 | 0 | 8 |
| Inorganic | 5 | 1 | 0 | 0 | 6 |
| Metal | 0 | 5 | 0 | 1 | 6 |
| Coordination | 0 | 1 | 1 | 0 | 2 |
| Charged molecular | 0 | 4 | 0 | 0 | 4 |
| Ionic assembly | 0 | 0 | 3 | 0 | 3 |
| Radical | 0 | 2 | 0 | 0 | 2 |
| Invalid control | 0 | 0 | 0 | 1 | 1 |

The 13 accepted structures passed the generator's graph, atom, specified stereochemistry, coordinate, coarse bond-length and convergence checks. These are *sanity checks*, not independent structural accuracy measurements. In particular, a converged force field does not establish the experimental geometry or lowest-energy conformer. The offline sample intentionally includes an invalid Fe(CO)₅ SMILES; it does not evaluate the separate exact-CID reference bridge. The fragment-form ferrocene input is classified information-only by current ionic heuristics; this is a representation/eligibility limitation, not evidence that the neutral molecular complex is ionic or lacks a geometry. The v1 replay remains 7 generated plus one idealized ZrCl₄ reference, 8/16; it predates and does not measure later references.

## Route-by-route audit

1. **PubChem**: search supplies CID and molecular/ionic metadata; its 3D SDF is preferred. Availability, a chemically suitable physical form, identity and accuracy were not independently measured live for these 32 cases. Network and API failures are distinct from a nonexistent conformer.
2. **RDKit**: up to three ETKDG attempts and MMFF94/UFF optimization with convergence and structural checks. Connected neutral nonradical permitted elements only; charged molecules, radicals and many metals are excluded. Unknown stereochemistry remains unknown. Force-field parameterization and geometry remain approximate.
3. **References**: exact reviewed SF₆ and AlCl₃ molecular references, an explicitly idealized gas-phase ZrCl₄ model, and individually reviewed Fe/Ni/Cr carbonyl coordination-representation bridges. A separate live exact-InChI/key/graph NIST search covers additional neutral connected metal-containing records, including previously verified trimethylaluminum and tetraethyllead. No online replays were performed in this audit; NIST unavailable is not automatically a chemistry failure. The generic path does not accept formula-only matches or claim that all coordination conventions are equivalent.
4. **Crystals**: the currently selected PubChem CID 24872 can explicitly open an anhydrous RhCl₃ cell based on COD 1534198; it is not a molecule. The independent seven-case crystal catalog in `tests/explorer_crystal_benchmark_v1.json` records 1/7 selectable phases, 6/7 not supported. This is a catalog-capability inventory, not live COD search or a universal statistical rate. Browser tests verify the 16 unique expanded sites, 4 Rh/12 Cl, finite coordinates, no overlaps, an Rh–Cl distance between 2.2–2.5 Å, unit-cell rendering path and atom-list measurement. These checks do not validate every cell angle, boundary bond or stacking disorder against experimental uncertainty.

## Limitations and findings

- **Confirmed regression:** full JS suite's `solution-integrations.test.mjs` fails because the new crystal control uses `class="explorer-transfer"` earlier than the embedded solution calculator. Its static ordering assertion now matches the wrong element; this is a test-selector/class collision, not evidence of lost calculator functionality. It needs a narrowly scoped follow-up and a rerun. No production fix was made during this audit.
- The current PubChem 3D route lacks a benchmark with fixed captured source payloads, graph/stereo comparison, independent bond/angle references and measured per-route failure reasons. More availability must not be called verified geometry.
- Generic NIST matching rejects charged and disconnected records, including many valid complexes; identity cannot safely be inferred from a molecular formula or disconnected standard InChI. Exact graphs and explicit form must remain safeguards. The older general-metal-reference report still describes a gas-phase label, while the current frontend correctly says environment not specified for the generic record.
- Crystal pilot is CID-specific and embeds a reviewed symmetry expansion, not a general CIF reader. Phase, hydration, uncertainty, temperature, disorder, occupancy, site symmetry, unit-cell setting, revisions and attribution need explicit representation and validation before a general route. Do not silently select a phase from formula alone.
- Measurement currently uses straight Cartesian distances for displayed positions, with no periodic images. Correct periodic distances for oblique cells require a tested nearest lattice-vector search, not merely component-wise fractional rounding; angle/torsion image choices must be explicit. Unit-cell boundary measurements require independently checked crystal fixtures and consistent atom-image labels.
- CIF geometry is one reported structural model and may omit disorder. 3Dmol is loaded from a remote script, so network or WebGL failures remain distinct from missing structural data. Atom selection and measurements remain limited to rendered sites.

## Specialist geometry opportunities

xTB/GFN2 is a candidate for independently benchmarked neutral closed-shell metal complexes and small metal halides that lack PubChem or trusted NIST models, e.g. constrained pilot forms of AlCl₃, ZrCl₄, and selected carbonyl complexes. Existing reference models should act as independent comparisons, not be replaced by unvalidated optimization. The [GFN2-xTB paper](https://doi.org/10.1021/acs.jctc.8b01176) and [transition-metal optimization benchmark](https://pubmed.ncbi.nlm.nih.gov/31141262/) support investigation, not blanket correctness. Input geometry, connectivity, charge and spin must be defined, multiple conformers bounded, element coverage validated, convergence/error/resource limits enforced, and geometry compared against experimental structures or credible independent calculations. Charged molecular species and open-shell compounds are future candidates only with explicit charge/spin and validation; the [xTB spin documentation](https://xtb-docs.readthedocs.io/en/latest/spgfn.html) describes method limitations. RhCl₃ extended solid must not be passed off as an isolated molecule.

## Priorities

1. Repair the crystal-control/test selector collision and add browser lifecycle tests for switch/late responses; rerun complete suites.
2. Build a versioned offline source fixture benchmark with source-specific coverage, failure taxonomy, charge/stereo and numerical geometry references, then separately document controlled online replays.
3. Pilot bounded xTB on a small, closed-shell, exact-identity set with trusted independent reference geometries; report failures and calibration, never auto-admit all metals.
4. Generalize CIF handling through reviewed phase-specific records, robust parser and symmetry/occupancy validation, using [COD's versioned records](https://wiki.crystallography.net/howtoquerycod/) and attribution.
5. Add explicit periodic image selection and independently verified skew-cell minimum-distance/angle/torsion tests, with clear limitations in the viewer.

## Verification

- 32-case offline generator audit: 13 validated by internal sanity/stereo checks; category breakdown above.
- Seven-phase crystal inventory: one explicitly supported, six not supported; 16 unique RhCl₃ sites checked.
- 50 focused JS Explorer/measurement checks passed, including the crystal catalog inventory test added after the full JS run.
- Crystal browser checks passed at 1440px and 320px with mocked PubChem search; atom-list distance selection and switch back verified. Live PubChem integration and actual drag movement were not independently tested in this audit.
- Full JS suite: 2,198 passed, 1 failed (selector collision described above); the later added catalog test passed separately.
- Full Python suite: 2,209 tests passed in 284 seconds.
- TypeScript `tsc --noEmit`: passed. `git diff --check`: passed.
