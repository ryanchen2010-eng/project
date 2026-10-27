# Reaction Lab chemistry depth — 2026-10-07

This increment preserves the existing layout, exact compound identities, atom
mapping, reaction-site selection, linked 2D/3D inspection, and calculators.
No deployment, GitHub push, or acid–amine amidation implementation is included.

## Mechanism foundation

`server/reaction_mechanisms.py` builds reusable mapped states for SN2, E2, SN1
and E1 from the selected structural reaction site. Every step now carries its
before state, after state, exact electron-source/destination endpoints, bond
formation/cleavage/order changes, and explicit proton-transfer changes.

- SN2: one concerted attack/departure step. A specified tetrahedral center is
  physically inverted; no stable carbocation is inserted.
- E2: concerted beta-H removal, pi-bond formation and leaving-group departure.
- SN1: actual carbocation, oxonium capture intermediate, then a separate
  solvent-water proton transfer producing alcohol and hydronium.
- E1: carbocation followed by coupled beta-H removal and pi-bond formation.

The interface uses highlighted before/after Lewis states and selectable
electron moves, not automatically routed curved arrows. Source bonds must
exist in the before state. Each step preserves atoms, isotope identities,
charge and valid explicit-H valence. The final main product must agree with
both the connectivity and stereochemical identity of the selected net result.
Extra solvent water is mechanism context, not additional net stoichiometry.
Intermediate structures remain 2D; the linked 3D model is the final product.

## Reusable stereochemistry

`server/stereochemistry.py` provides:

- Potential tetrahedral-center detection and specified R/S assignments using
  RDKit's accurate CIP labeler. Atom-map numbers are removed before priority
  calculation, then restored as identity references in the report.
- Potential double-bond stereo detection and specified E/Z assignment.
- Cis/trans descriptions for the unambiguous common H/H reference only.
  Ring-relative cis/trans and non-tetrahedral coordination stereo are pending.
- Mapped SN2 inversion accounting for changes in neighbor ordering. CIP labels
  are recomputed, not blindly exchanged: physical inversion can retain the same
  R/S letter when substitution changes priorities.
- Signed H–Cβ–Cα–X torsion measurement from an actual explicit-H 3D conformer,
  with anti-periplanar tolerance (default 15°). Degenerate, nonfinite, missing,
  or 2D coordinates are rejected.
- Enumeration of beta-H geometry checks for supported alkyl halides. Reports
  describe only the supplied conformer, not an optimized reacting geometry.

Reactant inspection and Advanced reaction information expose these reports.
Unspecified stereo stays unassigned. Apart from specified-center SN2 inversion,
new stereochemical reaction outcomes are not predicted. E2 anti-periplanar
measurements do not establish feasibility, select an E/Z product, or search
conformers. Specified tetrahedral inputs are rejected by other transformations
until their stereochemical handling is implemented.

## Structural reaction coverage

New net rules are modular in `server/extended_reaction_rules.py`; eligibility
does not depend on names, formulas, PubChem CIDs, or sample membership.

| Pathway | Implemented model / boundary |
| --- | --- |
| Aldehyde → carboxylic acid | Existing graph rule retained and verified on formaldehyde, chain, branched and aromatic aldehydes. Requires explicit further-oxidation stage and aqueous medium. Neutral acid is a reporting form, not a predicted solution protonation state. |
| Alcohol dehydration | Simple acyclic monofunctional alcohols, acid/heated profile, independently selected beta sites, alkene + water. Possible modeled-adjacent rearrangement cases are excluded; no E/Z or ether-competition prediction. Sulfuric acid is not consumed in net stoichiometry. |
| Alcohol → haloalkane | Actual HBr/HI; HCl limited to tertiary alcohols. Protonation/activation is acknowledged; net halide + water. No bare-OH leaving-group mechanism, rearrangement or general activation protocol. |
| Ester saponification | Selected ester acyl–O cleavage gives the actual carboxylate ion and alcohol. Hydroxide net equation; full input salt mass and spectator notes retained. No neutral acid work-up or lactone ring opening invented. Charged main product is 2D-only. |
| Alkyne hydrogenation | Two H₂ equivalents to the saturated selected bond; terminal Lindlar partial-reduction option with one H₂. Internal Lindlar cis stereoproduct generation is pending. Conjugated/ring alkynes excluded. |
| Alkyne halogenation | One or two Br₂/Cl₂ equivalents: dihaloalkene or tetrahaloalkane, respectively. Product E/Z ratios unassigned. |
| Alkyne hydrohalogenation | One or two actual HX equivalents with supported terminal/symmetric orientation; two gives a geminal dihalide. Ambiguous inequivalent internal ends and radical/peroxide orientation excluded. |
| Alkene dihydroxylation | Isolated hydrocarbon alkene, explicit Os-based/H₂O₂ catalytic net model, connectivity-only vicinal diol. Syn configurations, catalyst cycling and work-up are not depicted. Peroxide maps represent formal net balance, not elementary oxygen provenance. |
| Polymerization model | Finite 2/4/6-monomer acyclic terminal-vinyl hydrocarbon model. Consumed benzoyl peroxide initiates two phenyl-ended chains; head-to-tail propagation and combination termination give one oligomer + two CO₂. Not a bulk-polymer, tacticity, molecular-weight-distribution or experimental-product prediction. Explicit product size is bounded. |

Multiple molecules and distinct sites are tested for each family. Products are
sanitized and checked for atom/map/charge conservation before display. Repeated
equation species aggregate into stoichiometric coefficients; addition stage and
chain-length variants have distinct IDs so stale selections cannot silently
change their product. Model parameters are separate from substrate atom indices.

Ordinary acid + amine is **not** converted automatically to an amide. Salt
formation and activation-dependent amidation remain separate future work.

## Verification

- 194 Python tests and 353 JavaScript tests pass (547 total; 40 added this turn).
- New cases cover multiple non-preset molecules, exact coproducts, charges,
  full salt masses, reagent equivalents, rejected scope, stale variant IDs,
  both SN2 enantiomers, priority-changing inversion, mapped stereo invariance,
  E/Z versus unspecified stereo, cis/trans bounds, and anti/syn/gauche torsions.
- Mechanism tests verify before/after graphs, source bonds, actual intermediate
  charges, proton transfers and no fictitious stable concerted intermediate.
- UI tests cover before/after mechanism states, stereo/geometry invalidation,
  Advanced CIP display and charged-product 2D fallback without a fake 3D model.
- TypeScript, production build and whitespace checks pass. Browser checks
  include existing SN1 proton transfer, multi-equivalent equations, charged
  saponification results, and 320px containment with keyboard-focusable internal
  scrolling instead of page-wide overflow.

## Sources

- [RDKit stereochemistry and potential-stereo detection](https://rdkit.org/docs/RDKit_Book.html)
- [RDKit accurate CIP labeler](https://rdkit.org/docs/source/rdkit.Chem.rdCIPLabeler.html)
- [OpenStax: reactions of alcohols](https://openstax.org/books/organic-chemistry/pages/17-6-reactions-of-alcohols)
- [OpenStax: preparing alkyl halides from alcohols](https://openstax.org/books/organic-chemistry/pages/10-5-preparing-alkyl-halides-from-alcohols)
- [OpenStax: chemistry of esters](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters)
- [OpenStax: alkyne addition of HX and X₂](https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2)
- [OpenStax: alkyne reduction](https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes)
- [Primary paper: Os/H₂O₂ alkene dihydroxylation model](https://pubmed.ncbi.nlm.nih.gov/23113538/)
- [OpenStax: radical chain-growth polymerization](https://openstax.org/books/organic-chemistry/pages/8-10-radical-additions-to-alkenes-chain-growth-polymers)

## Recommended next chemistry increment

Reuse the stereo foundation for conformer-aware E2 outcome handling and explicit
syn-addition products (including internal Lindlar reduction). Add stereochemical
regressions before expanding scope; continue to label unsupported outcomes and
keep acid–amine amidation deferred.
