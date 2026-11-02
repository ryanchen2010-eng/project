# Explorer inorganic and metal references — Step 5

## Identity investigation: Fe(CO)5

On 2026-10-27, PubChem CID 26040 returned formula C5FeO5, standard InChIKey FYOFOKCECDGJBF-UHFFFAOYSA-N, and SMILES `[C]=O.[C]=O.[C]=O.[C]=O.[C]=O.[Fe]`. NIST's [iron pentacarbonyl entry](https://webbook.nist.gov/cgi/cbook.cgi?ID=13463-40-6) reports the same standard InChIKey and a computed 3D SD file, but that file has five explicit Fe–C connections and C≡O bonds. The frozen benchmark input `[Fe](C#O)(C#O)(C#O)(C#O)C#O` fails RDKit sanitization because the neutral oxygen triple-bond representation is over-valent in that graph. PubChem's disconnected graph and NIST's coordination graph must not be silently treated as graph-identical based on formula or an InChIKey alone. No Fe reference is automatically substituted; Explorer explains why it stays in 2D. NIST labels its geometry a gas-phase calculation, not experimental coordinates. Its SD file is marked copyrighted; it is not bundled here.

## Implemented reference

Neutral isolated AlCl3 monomer, PubChem CID 24012 with canonical graph `[Cl][Al]([Cl])[Cl]`, matches NIST CCCBDB's [experimental-geometry entry](https://cccbdb.nist.gov/expgeom2x.asp?casno=7446700). NIST reports D3h symmetry and an Al–Cl distance of 2.060 Å. Its tabulated Cartesian geometry is incorporated as a reference-derived gas-phase monomer; it is not a crystal or Al2Cl6 dimer. The existing reviewed reference registry supplies it only after the normal structure endpoint returns 404, only for that exact CID and graph, and never for ionic assemblies. No graph matching by formula or generalized metal geometry is introduced. RhCl3 remains unsupported as an isolated molecule; its crystal record is not silently substituted. Existing ZrCl4 and SF6 references are unchanged.

## Scalable method investigation

GFN-xTB is a possible later candidate for class-specific evaluation, but is not installed here and has not been independently validated on this project's exact reference set. The [xTB documentation](https://xtb-docs.readthedocs.io/en/latest/spgfn.html) explains that its standard GFN1/GFN2 formulations are spin-independent; charge, spin, bonding and initial geometry remain material for transition metals. Force-field parameter availability alone is not an accuracy test. A future evaluation needs exact-species graph and charge/spin information, independent gas-phase or crystallographic reference geometries, explicit physical-form labels, geometry/convergence thresholds, bounded CPU/memory/time, and out-of-sample tests before any class is enabled. No new generator is enabled in this increment.

## Benchmark

The frozen 16-case benchmark from Step 4 remains **9/16 conditionally available**, unchanged: AlCl3 is a new additional test case, not a member of the 16. The Fe(CO)5 benchmark graph remains invalid to RDKit, RhCl3 lacks an eligible molecular reference, and ZrCl4 retains its separately labeled idealized reference. This comparison is offline and conditional on the reviewed reference being selected after a 404; it is not an online availability survey or proof of experimental accuracy for calculated models.
