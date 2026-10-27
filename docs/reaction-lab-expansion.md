# Incremental Reaction Lab expansion — 2026-10-07

This is the next implementation slice of the long-term tool direction, not a
claim that the whole roadmap is finished. The existing layout, structural
engine, mapped SN/E mechanisms, calculators and hover/measurement systems remain.
No publication, GitHub push, accounts or classroom-management features were added.

## 1. What was added

- Generalized alkene epoxidation, with peracetic acid as a convenient input
  identity/example. Other supported peroxyacid graphs also work without names
  being used to choose chemistry.
- Automatic functional-group inspection for either resolved input, independent
  of whether the pair matches any reaction. Click a group to highlight it in the
  reactant's 2D diagram; explicitly request the same reactant's 3D conformer to
  see exact corresponding atoms in green. Changing groups reuses the conformer.
- Basic, Explanation, Mechanism and Advanced depths for the selected pathway.
  The Mechanism action opens the existing mapped steps only where implemented.
  Other pathways explicitly distinguish a net transformation from a mechanism.
- Reusable reaction information and multiple classifications. Hydrogenation is
  Addition + Reduction; epoxidation is Addition + Oxidation. These are labels on
  one selected reaction, not duplicate products or independent engines.

## 2. Chemistry now supported

Epoxidation uses one neutral peroxyacid and one selected isolated hydrocarbon
C=C site. It supports terminal/internal, branched and larger substrates and
ordinary supported rings. Multiple isolated C=C sites remain separate choices.
The terminal peroxyacid oxygen is transferred; the correct corresponding acid
is retained as the coproduct. Maps, explicit H, elements, charge and valence
are checked by the same product validator as the existing reactions.

Inspection recognizes alkene, alkyne, alcohol, aldehyde, ketone, carboxylic acid,
ester, amine, amide, haloalkane and aromatic ring, plus peroxyacid. It covers
broader structures than reaction eligibility: recognizing alkyl fluoride or an
amide does not approve their substitution or hydrolysis. Suggestions contain
only implemented mechanisms at the group level, with partner/site/condition
requirements still enforced by the engine. Charged/disconnected structures
retain their actual identity and 2D-only limitation, rather than fake conformers.

## 3. Still unsupported

Epoxidation is connectivity-only. Specified E/Z or atom stereochemistry,
conjugation, heteroatom-substituted alkenes, strained substrate rings and
ambiguous multiple-peroxyacid reagents are rejected. No epoxide ring opening,
stereospecific outcome, experimental chemoselectivity, yield or rate is predicted.
Its step-by-step mechanism and energy diagram are not implemented.

The complete live-presentation controls, R/S/E/Z tools, stereochemical mechanism
outcomes, unrestricted university chemistry and reaction discovery/search remain
future work. Acid–amine amidation remains unsupported; salts and dehydrated
amides must not be treated as interchangeable reactions. A functional-group
match does not prove reaction availability. A computed conformer is not a
transition state, measured structure or validated reactive conformation.

## 4. Tests and verification

- 18 new Python tests cover independently specified epoxide products, reagent
  variants, both input orders, name independence, transferred O provenance,
  coproduct identity, maps/bond edits/balance, multiple sites, conditions,
  unsupported cases, product 3D, all group types and inspection bounds.
- One additional authenticated-gateway test checks the new endpoint; the
  existing anonymous-access test now covers it too. Existing exact catalog
  regression expectations were expanded by the new epoxide, not weakened.
- 12 new JavaScript tests cover progressive depth, safe rendering, exact-map
  overlays, invalid correspondence, lazy WebGL, same-identity retention,
  abort/stale-response protection, conformer reuse and ionic/unavailable 3D.
- All 507 checks pass: 159 Python + 348 JavaScript. TypeScript, production build
  and whitespace checks pass. Existing 476 regressions are retained.
- Live local browser: epoxidation equation/diagrams and main-product 3D;
  functional-group-linked reactant 3D; existing SN2 mechanism opened from the
  depth control; 320px containment and desktop two-column layout; no browser
  errors in these checks. Temporary viewport overrides were reset.
  Saved previews: `history/reaction-functional-groups-2026-10-07.png` and
  `history/reaction-epoxidation-information-2026-10-07.png`.

## 5. Architecture changes

- `epoxidation_rule.py`: bounded structural requirements and explicit mapped
  edits, composed with shared engine validation rather than molecule recipes.
- `reaction_information.py`: mechanism-level metadata and implemented group
  suggestions; detection and description never decide pair eligibility.
- `functional_groups.py`: bounded graph inspection, exact mapped 2D rendering,
  optional existing conformer service. `/api/reactions/inspect` is available in
  both development and the existing authenticated production gateway.
- `functional-group-panel.ts` and `reaction-information-panel.ts`: scoped
  components integrated into the existing input/result panels. One lazy
  inspection viewer, separate from the existing main-product viewer. Results
  are invalidated immediately when identity changes; old asynchronous results
  cannot restore an old structure or selection. No browser-state chemistry
  inference and no extra external service.

## 6. Best next step

Add a bounded acid–amine module that separates acid–base salt formation from
chemically justified amidation/activation conditions. Validate products and
mechanisms independently, then add live-presentation controls using the existing
progressive information and exact-map views. Continue incremental family coverage;
do not expand to arbitrary reaction prediction.

## Chemistry references

- John McMurry, OpenStax [functional groups](https://openstax.org/books/organic-chemistry/pages/3-1-functional-groups).
- John McMurry, OpenStax [alkene epoxidation](https://openstax.org/books/organic-chemistry/pages/8-7-oxidation-of-alkenes-epoxidation-and-hydroxylation).

These are fact references. No textbook images, exercises or passages were copied;
the diagrams are generated from the user's selected structures.
