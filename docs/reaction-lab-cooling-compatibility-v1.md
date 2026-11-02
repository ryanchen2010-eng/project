# Cooling support: compatibility review and profiles v1

Review version: **1.0.0** · 24 October 2026 · local implementation only.

## Executive result

All 24 existing reaction definitions were reviewed. Alcohol oxidation requires
separate primary- and secondary-alcohol assessments, giving 25 model fixtures.
The completed cooled alkene-bromination profile is consistent across matching,
diagrams, generation, mapping, confidence wording and theoretical arithmetic.
One additional profile was implemented: **actual mCPBA epoxidation only**.
No other cooled pathway was approved.

The result is a bounded **theoretical molecular conformer**, never a temperature
simulation, guaranteed reaction outcome, experimental protocol or prediction
of rates, yields, face populations, site selectivity or product ratios.

The review does not establish universal experimental correctness. A finite
graph test suite and successful conformer embedding cannot do that.

## Classification meaning

- **S — Supported documented model:** the specifically reviewed reagent,
  substrate and condition assumptions can qualify a theoretical conformer.
- **P — Potentially supportable, validation needed:** no cooled profile has
  been approved. This is not a claim that cooling prevents the chemistry.
- **I — Incompatible with the current supported profile:** that profile has
  an explicit different temperature/formulation boundary. This does not mean
  the reaction is impossible under all cooled conditions.
- **O — Outside present output/model scope:** an endpoint, ionic geometry or
  mechanistic limitation remains even beyond validating a temperature setting.

## Compatibility matrix

These classifications are software-confidence assessments, not experimental
rate or thermodynamic comparisons. Existing substrate and product restrictions
apply to every row.

| Existing reaction-rule type | Cooled class after this increment | Boundary / remaining work |
| --- | --- | --- |
| Hydrogenation | P | Review an actual H₂/metal catalyst–substrate profile; cooling does not establish catalyst activity, completion or retention of other reducible groups. |
| Bromination | S, bounded | Existing actual Br₂, screened alkene, dry/non-capturing net assumption, no added activation; no full bromonium mechanism or outcome guarantee. |
| Chlorination | P | Independently validate Cl₂ medium capture, radical competition and stereo confidence; Br₂ approval is not transferable evidence. |
| Hydration | P | Review cooled acid/water activation; existing rearrangement, water-capture and cyclization screens remain. |
| Hydrohalogenation | P; some subprofiles I | Review cooled ionic HX. The oxygen-spectator HCl scope is explicitly ambient; radical HBr and unresolved capture/rearrangement remain excluded. |
| Epoxidation | S **only for mCPBA**; other peracids P | Actual meta-chloroperbenzoic-acid identity plus the documented mild-cooled/dry-compatible/no-added-activation net model. No automatic approval of peracetic acid or positional isomers. |
| SN2 | P | Review cooled hydroxide/medium activity and substitution–elimination competition. Validated backside inversion is not cooling evidence. |
| SN1 | P | Review cooled water-solvolysis ionization, capture and competing E1 chemistry. |
| E2 | P | Heated is a reference, not a universal chemical requirement. Validate cooled base activity and competition without weakening geometry checks. |
| E1 | P | Heated is a reference, not proof that cooled E1 is impossible. Validate ionization and competing SN1 chemistry. |
| Alcohol oxidation — primary | O | No selective hypochlorite aldehyde-stopping profile exists at any selected temperature. Cooling cannot establish the aldehyde endpoint. |
| Alcohol oxidation — secondary | I | Qualified NaOCl/acetic-acid ketone profile explicitly uses ambient conditions; cooled formulation compatibility needs separate review. |
| Aldehyde oxidation | I | Current neutral-acid reporting confidence accepts ambient/unset temperature; cooled hypochlorite, pH/speciation and separate acid work-up are unresolved. |
| Carbonyl hydrogenation | P | Review cooled H₂/metal C=O reduction and catalyst-specific competing reductions. |
| Esterification | P | Review cooled acid-catalyzed esterification; progress and equilibrium composition are not inferred from cooling. |
| Ester hydrolysis | P | Review cooled acid/water conditions while preserving lactone/aryl/site/stereo screens; no conversion or equilibrium prediction. |
| Alcohol dehydration | I | Existing actual sulfuric-acid model requires heating. Cooled activation and ether/other competition are not qualified. |
| Alcohol substitution | I | Existing HX profiles use heated methyl/primary or ambient secondary/tertiary settings. Cooled activation, elimination competition and stereo need review. |
| Ester saponification | O for 3D, chemistry P | Charged carboxylate meets the present ionic-geometry exclusion. A cooled chemistry review alone cannot qualify neutral 3D or silently replace carboxylate with acid. |
| Alkyne hydrogenation | P | Review cooled two-H₂/active-metal completion and competing-site behavior. |
| Alkyne partial hydrogenation | P | Review cooled Lindlar stopping confidence; one H₂ equivalent and syn graph geometry do not establish a stopped endpoint. |
| Alkyne halogenation | P | Review reagent-specific one-/two-X₂ conditions; equivalent count, medium capture, competing sites and first-stage chlorine stereo remain independent limits. |
| Alkyne hydrohalogenation | I | Present qualified conformer profile explicitly requires ambient conditions; HCl activation, unresolved internal E/Z, two-HI and oxygen competition remain blockers. |
| Alkene dihydroxylation | P | Review cooled Os/H₂O₂ while retaining Os activation and confirmed aqueous release; no inferred solvent/work-up compatibility. |
| Polymerization model | O | Finite BPO-initiated chain connectivity is not a cooled initiation/propagation/termination model or temperature-dependent polymer simulation. |

## Verified existing bromination profile

`cooled-alkene-bromination-v1` remains intact. Actual Br₂ supplies the two
incoming atoms; the existing screened alkene graph, dry/non-capturing model
and no-added-activation assumption are required. Cooling never overrides
medium, structure, stereo, mapping or product-generation failures.

Public match, diagram, run and calculator contexts agree. Independent existing
tests exercise anti products, E/Z-dependent meso/enantiomer alternatives,
distant physical configuration retention, exact mapped Br atoms, valid 3D
coordinates and 1:1 stoichiometry. The complete bromonium mechanism remains
unimplemented (`None`); this increment does not claim otherwise.

See [the original bromination implementation and its primary references](cooled-alkene-bromination-3d.md).

## Implemented epoxidation profile

Profile: `cooled-peroxyacid-epoxidation-v1`.

| Requirement | Meaning |
| --- | --- |
| Actual mCPBA identity | Canonical graph `O=C(OO)c1cccc(Cl)c1`, derived from the already validated reagent molecule. A name, matching formula, ortho/para isomer or another peracid cannot qualify. |
| Existing substrate eligibility | No new substrate class; all current peracid site, element, ring, acid-lability, nearby-OH/ether, competing oxidation and stereochemical restrictions remain. |
| Cooled | A mild cooled reaction-control reference, anchored to a documented near-0 °C example with addition kept at or below 10 °C. This is **not** a validated continuous 0–10 °C operating window, an actual numeric input or arbitrary cryogenic approval. |
| Dry / no water | Existing compatible non-capturing net-model assumption. Source evidence is anchored to dichloromethane; the selector does not establish compatibility of every dry solvent. |
| No added activation | `none` or the existing unset neutral-model setting. No extra acid, metal, Lindlar, Os or radical activation, buffering system or new reagent is inferred. |
| No unrelated stages | Explicit oxidation-stage/work-up settings and unknown fields block confidence. Persistent known alkyne-equivalent/finite-chain selectors remain not applicable; they do not change oxygen-transfer stoichiometry. |
| Output | Existing epoxide plus the actual m-chlorobenzoic-acid coproduct in the mapped net equation. 3D shows the main epoxide only, not a simulation of the mixture. |

The engine now retains the exact normalized peroxyacid reagent identity as
internal condition-evidence metadata. This does not alter transformations or
chemical identity. No compounds are substituted by formula, display name or
search alias. Missing identity metadata fails closed.

Other actual peracids remain supported under their **existing non-cooled**
rules; this increment does not remove that behavior. Under cooling they receive
a specific `reagentIdentity` limitation, not a claim that peracid epoxidation is
chemically impossible. The curated peracetic-acid example is unchanged.

## Evidence and what it does not establish

### Cooled product evidence

1. Srinivasan et al., [“Epoxidation of Olefins at Low Temperature Using
   m-Chloroperbenzoic Acid”](https://doi.org/10.1081/SCC-120004069), Synthetic
   Communications 32 (2002), 1853–1858. The publisher abstract describes
   mCPBA/olefin epoxidation in dichloromethane without catalyst at low
   temperature. Full experimental text was not retrievable; **no exact
   temperature or substrate table is attributed to that abstract**.
2. [US7612123B2, Example 4](https://patents.google.com/patent/US7612123B2/en),
   the mCPBA oxidation stage after synthesis of 4-cyclohexylcyclohexene,
   documents initial and subsequent 0 °C conditions with addition at or below
   10 °C and identifies the epoxide using reported proton NMR data. Aqueous
   bicarbonate is added after reaction, not as the oxidation catalyst.
   This is primary experimental reporting in a patent, **not independently
   checked Organic Syntheses evidence** or universal validation.

Together these support a mild-cooled mCPBA **net-model** candidate. Applying
that compatibility to the engine's already screened substrate scope is a
bounded modeling inference; the test molecules are not all individually
validated cold experiments. No solvent recipe, experimental yields or reagent
handling procedure is added to the application.

### Stereochemistry is a separate question

The checked [Organic Syntheses preparation of trans-stilbene oxide](https://www.orgsyn.org/demo.aspx?prep=CV4P0860),
DOI 10.15227/orgsyn.038.0083, independently illustrates retained substituent
relationship under peracid epoxidation. It uses **peracetic acid**, an acetate
neutralizer and different temperatures; it is evidence for the relationship,
**not** for this cooled mCPBA condition profile or cold-specific facial
selectivity.

The existing mechanism represents same-face transfer of one oxygen. Existing
mapped parity/CIP validation determines permitted relative configurations from
the input geometry; cooling adds no new R/S, syn/anti or facial population rule.
E substrates, Z substrates, meso cases and relevant enantiomeric alternatives
retain their prior graph behavior. Unknown geometry stays unassigned, and
distant physical configurations are independently checked even where CIP
letters change. An arbitrary conformer never establishes a stereochemical
outcome.

### Why other peracids are not automatically approved

There is primary evidence for cooled chemistry with other peracids. For
example, [the checked styrene-oxide preparation using perbenzoic acid](https://www.orgsyn.org/demo.aspx?prep=CV1P0494),
DOI 10.15227/orgsyn.008.0102, uses 0 °C. A separate
[Organic Syntheses preparation, Note 2](https://www.orgsyn.org/demo.aspx?prep=CV6P0312),
DOI 10.15227/orgsyn.051.0011, reports cooled peracetic-acid preparation of
trans-butene oxide, with an acetate neutralizer and subsequent warming.
Neither is silently treated as the newly reviewed actual-mCPBA profile.
Reagent formulation, medium, buffering, warm-up and epoxide stability deserve
their own scoped validation before a future extension.

## Confidence, UI and stale-result behavior

- The existing version-1 cooling metadata separates `supported-model`,
  `conditions-unresolved` and `unvalidated-pathway`. The new profile carries
  its source URLs and explicit mild-cooled temperature scope.
- Every other pathway now receives its own limitation explanation (including
  separate primary/secondary oxidation messages), rather than only the same
  generic cooling warning. Original stronger endpoint/activation reasons stay
  visible. Missing medium or wrong reagent is not blamed on temperature.
- Affirmative frontend wording requires an exact reviewed model/pathway pair,
  matching backend/evidence/cooling permissions, no missing requirements and
  no unresolved condition issues. Unknown or contradictory profile metadata
  cannot create a confident prompt.
- Any condition change immediately clears the viewer, diagrams, mechanism,
  atom/measurement selections and old calculator results before rematching.
  Existing abort/revision checks prevent late responses restoring stale
  structures. Run requests independently re-resolve the current pair and
  conditions; an old option ID is not permission.
- UI/UX Pro Max informed clear feedback and recovery wording only. No layout,
  stylesheet, navigation, new control or design-system change was made.
- Arithmetic stays browser-local and theoretical. One actual peracid per
  selected C=C produces one epoxide and one actual acid coproduct; alternative
  site/face quantities must not be summed as predicted yields.

## Verification and benchmark preservation

Separate versioned suites:

- `tests/test_cooling_profiles_v1.py`: **56 passing tests**, covering every
  rule type through 25 model fixtures, 14 positive mCPBA structure fixtures,
  independent products/CIP/coordinates, acid and oxygen/proton provenance,
  four concerted electron moves, identity/isomer negatives, conditions,
  authenticated APIs and stale IDs.
- `tests/cooling-profiles-v1.test.mjs`: **21 passing tests**, including the
  actual production lifecycle functions and a late-response invalidation case.
- Existing cooling/bromination/epoxidation focused checks: **148 passing**.
  Only old peracetic-acid cooling expectations were updated narrowly: it
  remains blocked, now for the precise reagent-profile reason instead of a
  blanket unvalidated-temperature reason.
- Full regression verification: **2,029 Python + 2,011 JavaScript = 4,040
  passing tests**, preserving the 3,963-test baseline and adding 77 tests.
- TypeScript and the production build pass. Existing dependency-directive
  and bundle-size warnings remain; no new build failure.
- Scoped whitespace checks pass. Hash comparison confirms every pre-existing
  `*_rule.py`, the frozen audit script and versioned reaction-condition
  benchmark file remain byte-identical. The reaction engine's only change is
  internal peroxyacid identity metadata, not a new transformation rule.
- The unchanged 347-case audit retains identical IDs, actual products,
  per-case results, statuses, pathway summaries, variants and supplementary
  results. Only the production source hash changes. Totals remain **155 fully
  supported, 90 unsupported, 38 correctly rejected, 63 partially supported and
  one pre-existing incorrect-result classification**. No frozen case is
  inflated or fixed by changing expectations.

Browser verification uses isolated localhost services and the real existing
PubChem input workflow. Cooled actual mCPBA generates the epoxide in Compare
mode with the acid present in the 2D equation. The existing single concerted
mechanism displays all four moves. The calculator preserves 1:1 molar
accounting and a theoretical-amount warning. Selecting water immediately
removes the old 3D result and calculation; the rebuilt option is conditional
2D only with an epoxide-opening/medium explanation. Returning to dry restores
qualified output without changing the selected cooling value.

### Browser completion appendix

- Existing PubChem search resolved actual mCPBA; no test-only molecule was
  injected into the browser or curated collection.
- Cooled ethene/mCPBA generated the mapped epoxide in Compare. The 2D equation
  retained the actual acid coproduct, and the existing mechanism showed all
  four electron moves with explicit proton relocation.
- An arithmetic fixture with 1 mmol of each reactant gave the formal 1 mmol
  epoxide bound (0.044053 g), explicitly labeled theoretical, not actual yield.
  This was an arithmetic QA fixture, not an experimental recipe.
- Switching to water cleared the displayed conformer and that old calculation
  immediately. The rematched 2D-only option identified `solvent` and possible
  epoxide opening, not an unvalidated-temperature claim. Dry restored 3D.
- The existing cooled ethene/Br₂ workflow was independently repeated in the
  final browser build and still generated mapped 1,2-dibromoethane.
- At a 320px viewport the document width was 320px; cooling and activation
  controls remained available through the existing Inspector. The existing
  internally scrollable 2D diagram behavior was preserved.
- Final Python rerun after the last source-precision wording correction:
  2,029/2,029 pass. The final frozen audit comparison again has no differences
  outside its expected production-source hash.

Saved browser proof:

- `history/cooling-v1-mcpba-3d-2026-10-24.png`
- `history/cooling-v1-mcpba-mechanism-2026-10-24.png`
- `history/cooling-v1-mcpba-water-blocked-2026-10-24.png`
- `history/cooling-v1-mcpba-mobile-2026-10-24.png`
- `history/cooling-v1-bromination-regression-2026-10-24.png`

Temporary localhost QA services and the QA tab were stopped after verification.
The user's pre-existing preview was not interrupted. Restart that local
chemistry service before trying the new backend profile there.

## Remaining work — recommendation only

1. Consider a separately documented perbenzoic/peracetic extension, validating
   formulation, buffering/warm-up and epoxide stability before approval.
2. Independently review a cooled Cl₂ profile; do not transfer Br₂ confidence.
3. Then consider a narrow cooled dihydroxylation profile with explicit Os and
   aqueous release. No implicit work-up completion.
4. Catalyst-dependent hydrogenation and SN/E temperature/competition models
   need their own evidence; retain their current 2D limitations meanwhile.
5. Numeric temperatures, dynamic kinetics, ionic crystal/solution geometry,
   selective oxidation endpoints and experimental mixtures remain separate
   future capabilities, not dropdown-driven predictions.

**Stop here:** no further cooling profile was implemented. No GitHub push,
merge, Render deployment or frozen-beta update. Existing user edits were
preserved; temporary QA services do not replace the user's local preview.
