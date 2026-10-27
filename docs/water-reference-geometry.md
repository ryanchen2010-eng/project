# Water reference geometry

Explorer's curated water record now loads `public/molecules/water-reference.sdf`.
The original PubChem file `public/molecules/water.sdf` is retained unmodified.
Its H-O-H angle is 103.97994°, correctly measured as 104.0° by Measure 3D.
This is a model/reference difference, not a trigonometry or rounding defect.

The new, explicitly reference-based model uses a 104.5° H-O-H angle and
approximately 0.958 Å O-H bonds, rounded to four-decimal coordinates. See
[OpenStax's water geometry discussion](https://openstax.org/books/chemistry/pages/8-2-hybrid-atomic-orbitals)
and the neutral-water entries in
[NIST CCCBDB](https://cccbdb.nist.gov/listgeomexpx.asp?casno=7732185&charge=0).
It preserves the oxygen-first atom order, two hydrogen atoms and two single bonds.
It does not carry the original conformer's energy, shape or computed-charge metadata.
PubChem search hits for the curated water CID reuse this same reviewed model.

VSEPR charts describe ideal arrangements and qualitative distortions. They do
not supply an exact angle for every molecule: tetrahedral is approximately
109.5°, while water's two lone pairs accompany a smaller bent angle. Do not
snap measured angles in arbitrary structures to 90°, 109°, 120° or 180°.
Measure 3D remains a coordinate-based measurement, not an experimental claim.
Builder and Reaction Lab generated conformers remain unchanged.
