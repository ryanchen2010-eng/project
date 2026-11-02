# Calculator models

All amounts and equilibrium arithmetic run in the browser. Only the supported
reaction selector calls the existing local chemistry service. Nothing in these
tools predicts reaction speed, experimental accuracy, actual yield or safety.

## Moles and solutions

- Convert kg/g/mg/µg, mol/mmol/µmol and specified entity counts. Avogadro's
  constant is exactly 6.02214076 × 10²³ mol⁻¹ ([BIPM SI definition](https://www.bipm.org/en/si-base-units/mole)).
- Count molecules, specified atomic species or ionic formula units, not total
  constituent atoms or dissolved ions. Changing the entity kind drops a selected
  whole-compound mass rather than treating it as an atomic mass.
- Identity sharing keeps the exact ID, PubChem CID and structure; formula alone
  never resolves an isomer or salt. Full salt/hydrate molar mass must be supplied.
- Solutions reuse the existing molarity, pure-solute mass and dilution code.
  Final volume is total solution volume; volumes are not assumed additive.

## Reaction amounts

The service's 17 reviewed reaction equations supply balanced stoichiometry and
exact reactant/product molar masses. The selector rejects missing/unbalanced
metadata. Limiting-reactant, main-product theoretical yield and target-amount
calculations reuse the existing calculator. Solvent-only inputs and catalysts
are not stoichiometric quantities. The model assumes pure material and complete
conversion; it does not predict equilibrium-limited or actual yield.

## Equilibrium conventions

All constants are entered by the user, as K or pK = −log₁₀K. Use constants and
fixed activity coefficients appropriate to the specified temperature and the
same concentration-based standard state: aᵢ = γᵢ(cᵢ / 1 mol/L). Ideal sets γᵢ=1.
Entered mode requires γ for every included dissolved species, including neutral
forms and fixed spectator counterions. Temperature edits clear all constants
and coefficients. There is no lookup, ionic-strength correction, automatic
temperature extrapolation or activity model.

General equilibrium has 2–12 species, positive integer coefficients, explicit
charges and aqueous/pure-solid/pure-liquid phases. The user must confirm a
balanced equation: names do not chemically verify it. Pure phases have activity
1 and must remain present. Fixed spectators do not react. At fixed volume,
cᵢ(final) = cᵢ(initial) + νᵢx. A bounded extent solve enforces nonnegative
concentrations and checks mass-action residual, material balance and charge
balance. Zero concentrations remain exact zeros; 0/0 is undefined. Q/K indicates
thermodynamic direction only, not rate. Gases are excluded.

## Acid/base family

One neutral monoprotic acid or base, one conjugate-pair buffer, one fully
dissociated strong monoprotic acid/base, or one neutral HₙA family with 1–3
dissociation steps. Buffers include their monovalent salt counterion. Polyprotic
salt/base equivalents are represented by a fixed monovalent spectator cation,
between 0 and n × total family concentration.

The solver includes Kw, every dissociation step, total family mass and
electroneutrality together. There is no small-x or Henderson–Hasselbalch shortcut.
pH is −log₁₀(aH+), not necessarily −log₁₀[H+]. Water's pure liquid activity is
assumed 1. Kw is mandatory, never silently assigned 10⁻¹⁴.

## Solubility

One electrically neutral salt dissolving into exactly two ion types, with
integer stoichiometry, fixed common ions and nonreacting spectators. Excess
solid and fixed solution volume are assumed. Ksp uses the ion activity product;
the solver reports extra formula-unit molarity dissolved to saturation.
Qsp comparison reports undersaturated/saturated/supersaturated. A supersaturated
initial mixture cannot be solved by the dissolution-only mode; precipitation
amounts and coupled acid/base systems are not calculated.

## Checks and references

- [OpenStax equilibrium constants](https://openstax.org/books/chemistry-2e/pages/13-2-equilibrium-constants):
  quotient arithmetic and reversible-reaction concentration relationships.
  Gaseous textbook numerical ratios can check algebra only; the app does not
  represent those gases as aqueous chemistry.
- [OpenStax buffers](https://openstax.org/books/chemistry-2e/pages/14-6-buffers):
  0.1 M acetic acid + 0.1 M acetate, Ka=1.8×10⁻⁵, gives pH approximately 4.74;
  the app solves full charge/mass balance rather than only the initial ratio.
- [OpenStax polyprotic acids](https://openstax.org/books/chemistry-2e/pages/14-5-polyprotic-acids):
  carbonic acid and three phosphate dissociation steps, including independent
  mass-action and material-balance checks.
- [OpenStax solubility](https://openstax.org/books/chemistry-2e/pages/15-1-precipitation-and-dissolution):
  pure-water solubility, common-ion suppression and Qsp/Ksp comparison.

Automated checks also cover unit conversions, full salts, exact identity,
temperature clearing, all-species coefficients, zero inputs, invalid models,
overflow/underflow and nonconvergence. Display rounding does not assert measured
precision. Values beyond the bounded numerical range fail explicitly. No
arbitrary mixtures, coupled precipitation, complexation or thermochemistry.
