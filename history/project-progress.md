# Capstone progress

## 2026-09-19 — Step 1 baseline and direction

- Local project: `/Users/rc/Documents/Capstone project`.
- GitHub repository: `ryanchen2010-eng/capstone-project`.
- Website: Wix Site 1 only; publishing still requires Ryan's go-ahead.
- Local branch: `codex/step-1-baseline`.
- Pre-consolidation backup: commit `84ff533`, including the local Builder and
  an exact snapshot of the existing Wix Explorer embed.
- Consolidated all six Wix molecule property records and search aliases into
  `src/molecules.ts`; retained the existing PubChem SDF files and identifiers.
- Added local Explorer search, full property fields, everyday uses, source links,
  and checks against stale model responses. The current interface shows matching
  molecule cards; matching the Wix suggestion-only interaction is still pending.
- Preserved the Builder periodic-table selection and thin bond styling.
- Baseline checks: 13 tests passed, TypeScript passed, and Vite production build
  passed on 2026-09-18. Builder tests are source checks; full browser verification
  remains pending.
- Local Explorer opened successfully on 2026-09-19 and reported Water ready.
- Known Builder limits: single bonds only, simple fixed neutral-valence limits,
  flat coordinates, and formula hydrogens that are not drawn in the preview.
- Thermal property conditions and molecular forms need a fuller content review
  before release.
- Ryan ruled out MolView integration. The planned Builder tools are Ketcher,
  RDKit, and 3Dmol.js. No Ketcher/RDKit integration has been implemented yet.
- Next chemistry milestone: draw ethanol, validate its molecular graph, calculate
  formula/mass, and generate a real 3D conformer.

The Step 1 baseline was uploaded to Ryan's GitHub branch
`codex/step-1-baseline` on 2026-09-19. The Wix draft was preserved and has not
yet been updated with these local changes.

## 2026-09-24 — Step 2 Builder drawing to 3D

- Replaced the custom flat-coordinate Builder canvas with Ketcher's 2D chemical
  editor. Its atom toolbar includes a periodic table.
- Added a local RDKit HTTP service. It accepts a Molfile from Ketcher, checks
  for a single supported neutral molecule and chemical valence, adds hydrogens,
  generates a 3D conformer, and minimizes it with MMFF94 or UFF.
- Kept 3Dmol.js for the rotatable 3D result and added formula, mass, atom/bond
  counts, a structure check, and the force-field method to the result panel.
- Added an ethanol example to exercise the full workflow.
- Verified ethanol in the browser: C2H6O, 46.069 g/mol, 9 atoms, 8 bonds,
  MMFF94, and a visible 3D model. Python checks cover invalid valence,
  disconnected fragments, and charged inputs.
- Current service runs locally at 127.0.0.1:8000 and has not been deployed or
  added to Wix. The Builder is still limited to the element and molecule scope
  listed in README.md; it does not calculate all possible geometries or prove
  a global energy minimum.

## 2026-09-24 — Step 2 Builder testing pass

- Drew ethene with a double bond and benzene with an aromatic ring in the
  browser. Both generated the expected formula and visible 3D model: C2H4
  (6 atoms, 5 bonds) and C6H6 (12 atoms, 12 bonds).
- Drew a carbon with five single bonds. The Builder correctly rejected it;
  its technical RDKit message was replaced with a plain-language instruction
  to remove or change a bond.
- Added automated double-bond and ring checks. All 6 chemistry tests and all
  10 Explorer catalog tests pass; TypeScript and the production build pass.
- Work remains local on `codex/step-2-builder`; it is not on Wix or GitHub yet.

## 2026-09-24 — Step 3 Reaction Lab first version

- Added a separate `/reaction-lab.html` page with two searchable molecule
  inputs, four curated example pairs, matching reaction selection, conditions,
  a balanced equation, and an interactive 3D main-product preview.
- The reviewed examples are ethene + hydrogen → ethane; ethene + bromine →
  1,2-dibromoethane; ethene + water → ethanol; and ethanoic acid + ethanol →
  ethyl ethanoate + water. Source links point to OpenStax Organic Chemistry.
- The local RDKit endpoint validates the selected pair, checks atom balance
  (including byproducts), and generates the product structure. Unknown pairs
  are explicitly outside the collection rather than labeled impossible.
- Browser-tested esterification and hydrogenation end to end, formula input,
  and an unsupported pair. All 9 Python and 10 catalog tests, TypeScript, and
  the Vite production build pass.
- Work is saved locally on `codex/step-3-reaction-lab`; no Wix publication or
  GitHub upload has been done for this step.

## 2026-09-24 — SN2 examples added to Reaction Lab

- Added bromomethane, chloromethane, and hydroxide ion as selectable reactants.
- The page now shows the requested example, CH3Br + OH⁻ → CH3OH + Br⁻,
  and a chloromethane + hydroxide comparison. Both use textbook-backed SN2
  explanations and list the departing halide ion separately from the 3D
  methanol product.
- The server checks total formal charge as well as atoms for every curated
  reaction. Reaction Lab can use these reviewed ionic reactants while Builder
  remains limited to neutral drawings.
- Browser-tested both SN2 paths, the requested bromomethane equation and 3D
  methanol model, plus searches using CH₃Br and OH⁻. All 11 chemistry tests,
  10 Explorer tests, TypeScript, and the production build pass. Work remains
  local; it has not been uploaded to GitHub or published to Wix.

## 2026-09-24 — Two-input compound entry and Builder handoff

- Reaction Lab now accepts reviewed reactants by name or correctly capitalized
  chemical formula. Unicode subscript digits and ion minus signs also work.
- Added dimethyl ether to expose the shared C2H6O formula with ethanol. Users
  must choose the intended structure; the Lab never silently picks an isomer.
- A validated Builder drawing can be sent to either Reaction Lab reactant box.
  The other input is retained within the browser tab. Drawings are matched by
  canonical molecular structure, not formula alone. An unfamiliar drawing is
  reported as outside the reviewed collection.
- Browser-tested formula ambiguity, CH3Br + OH- SN2 product, and Builder's
  ethanol handoff. All 12 Python tests and 13 JavaScript tests passed;
  TypeScript and production build passed. Work remains local, not on Wix or
  GitHub.

## 2026-09-24 — Multi-pathway reaction-rule foundation

- Added solvent, temperature, and catalyst controls to Reaction Lab. The new
  matching endpoint compares selected structures and conditions, then shows
  multiple supported pathways with an educational condition assessment.
- Added narrow structure-derived SN2 and E2 rules for simple acyclic alkyl
  halides, plus SN1 and E1 examples for a tertiary halide in water. Existing
  addition and esterification examples use the same matching interface.
- Reviewed pairs now include bromoethane + hydroxide (SN2/E2) and
  2-chloro-2-methylpropane + water (SN1/E1). E1 correctly treats water as the
  solvent rather than a stoichiometric reactant. Every displayed product is
  checked for atom and formal-charge balance and given a 3D conformer.
- Rules deliberately avoid unsupported regioisomer/stereoisomer decisions,
  carbocation rearrangements, and rate/yield claims. Drawn molecules still
  must match the reviewed reactant collection; arbitrary reaction prediction
  remains out of scope.
- Browser-tested SN1, E1, E2, and an existing addition path; automated
  chemistry and entry checks pass. This work is local only, not on Wix or
  GitHub.

## 2026-09-25 — Builder drawings checked against supported reaction rules

- Builder now sends the validated drawing's canonical structure and formula to
  either Reaction Lab input. Unlisted drawings are retained within the tab and
  checked by structure rather than rejected for lacking a catalog name.
- The server validates each custom structure on match and run, then applies
  only the existing narrow alkyl-halide SN1/SN2/E1/E2 teaching rules. Products
  outside the small naming map receive a generic label plus exact SMILES.
- Drawn 1-bromopropane + hydroxide is covered (SN2 1-propanol structure and E2
  propene); unsupported structures remain explicitly unsupported, not claimed
  unreactive. No general reaction predictor, regioisomer selection, or
  stereochemistry was added.
- Browser-tested drawing 1-bromopropane in Ketcher, generating its 3D model,
  transferring it to Reaction Lab, matching SN2/E2 with hydroxide, and showing
  the balanced SN2 product (CCCO). The transferred structure survives reload.
  All 18 Python chemistry tests and 13 JavaScript tests pass; TypeScript and
  the production build pass.
- Work remains local; nothing was published to Wix or GitHub.

## 2026-09-25 — Automatic alkene additions from new drawings

- Added structure-based recognition of small, acyclic hydrocarbons containing
  exactly one C=C bond (two to six carbons), even if the drawing is absent from
  the preset reactant list. Listed H2 offers metal-catalyzed hydrogenation;
  listed Br2 offers bromine addition in a dry medium.
- Products are built from the drawn bond, sanitized, checked for atom and
  charge balance, and rendered in 3D. The Lab shows exact product SMILES and
  labels unnamed products by class. The preview does not assign stereo or
  claim a yield; rings, multiple double bonds, alkynes, heteroatom-containing
  alkenes, and specified stereochemistry remain outside this automatic rule.
- Browser-tested drawn propene through Builder into Reaction Lab: H2 gave
  balanced propane connectivity (CCC) and Br2 gave balanced
  1,2-dibromopropane connectivity (CC(Br)CBr). Added a warning when an extra
  catalyst is selected for a pathway that does not evaluate it.
- All 20 Python chemistry tests and 13 JavaScript tests pass; the production
  build succeeds. Work remains local, not published to Wix or GitHub.

## 2026-09-25 — Explorer search beyond six featured molecules

- Kept the six reviewed Explorer molecules as featured examples, but removed
  them as the search limit. A submitted full name or correctly capitalized
  formula now searches PubChem through the local chemistry service.
- Same-formula structures appear as separate choices, with bracketed SMILES
  notation showing their different atom connections. C2H6O returns ethanol
  [CCO] and dimethyl ether [COC]; isotope-labelled, charged, and disconnected
  records are excluded from this introductory list.
- PubChem results load a 3D structure when available. Small supported molecules
  can use an RDKit-generated 3D fallback if PubChem has no 3D record. The six
  existing entries keep their curated teaching notes; new results show formula,
  mass, and source while unreviewed properties remain clearly labelled.
- Browser-checked C2H6O isomer selection and an unlisted acetone search with
  a working 3D model. All 23 Python and 14 JavaScript tests pass, and the
  production build succeeds. This remains local and is not on Wix or GitHub.

## 2026-09-25 — PubChem reactants in both Reaction Lab boxes

- Added a PubChem search action beside each reactant input. Exact names and
  correctly capitalized formulas resolve to connected, neutral structures;
  same-formula isomers remain separate bracketed-SMILES choices.
- Known PubChem structures reuse the reviewed reaction IDs. Other supported
  structures enter the existing narrow RDKit rules; PubChem supplies structure
  identity, not reaction predictions. Unsupported pairs say no current rule
  matches, without asserting that no reaction is possible.
- Selected structures and conditions survive a reload within the browser tab.
  The existing Builder handoff and example buttons still work.
- Browser-tested PubChem propene + listed hydrogen through a balanced 3D
  hydrogenation product; C2H6O with ethanoic acid offers esterification only
  for ethanol, not dimethyl ether. The second input's PubChem search and the
  selected-isomer reload were also checked in the browser. All 24 Python and
  16 JavaScript tests, TypeScript, and the production build pass. Work remains
  local and is not on Wix or GitHub.

## 2026-09-25 — Broader compound handling across the three tools

- Explorer search no longer discards every charged or multi-part PubChem record.
  Formula matching compares element counts instead of element order, so a
  search such as NaOH can match PubChem's HNaO record. Formula searches still
  filter isotope variants and disconnected neutral mixtures; search results
  remain bounded and source-labelled. Name lookup prefers an exact PubChem
  title when a synonym initially resolves to a different related record.
- Explorer now uses a PubChem 2D depiction when a usable 3D structure cannot
  be obtained. Tested cisplatin and sodium hydroxide in the browser; both
  display their identified PubChem records and 2D depictions. Water still
  displays in 3D. This is a fallback, not a fabricated 3D geometry.
- Reaction Lab recognizes the class of simple Li, Na, K, Rb, and Cs hydroxide
  salts as OH⁻ sources for its existing supported ionic reaction equations.
  It labels the omitted spectator cation. Tested sodium hydroxide with
  bromomethane in the browser. Other salts and complexes remain outside the
  Lab's current structural rules unless individually supported.
- Builder now parses a wider range of periodic-table drawings. It attempts
  3D only for eligible neutral, connected covalent structures with supported
  optimization parameters; salts, charges, metal complexes, and failed
  geometry calculations retain a 2D-only result with a reason. Invalid valence
  still fails validation. The 2D-only drawing can be passed to Reaction Lab,
  where the Lab may report that no reaction rule covers it.
- Browser-tested Builder ethanol as a 3D result and a separately placed sodium
  atom as a 2D-only result. Corrected RDKit's inferred NaH formula from a bare
  periodic-table Na drawing so it reports Na instead.
- All 31 Python and 16 JavaScript tests pass; TypeScript, production build, and
  `git diff --check` pass. Work remains local, not published to Wix or GitHub.

## 2026-09-25 — Cross-page chemistry test pass

- Added a permanent 22-compound Explorer-result → Builder → Reaction Lab matrix,
  spanning ordinary molecules, isomers, alkenes, alkyl halides, salts, an ion,
  a metal complex, and an unsupported secondary substrate. The matrix checks
  source/formula identity, 3D versus 2D-only classification, reaction-rule
  scope, and atom/charge balance for every offered pathway.
- Checked 11 live PubChem name/formula queries and five live 3D/2D availability
  cases. Browser-tested formula ambiguity, sodium chloride's loaded 2D image,
  potassium hydroxide's SN2 interpretation, unsupported sodium chloride, a
  successful Builder ethanol → Lab esterification with 3D product, and a
  2D-only sodium Builder handoff rejected by the Lab's narrow rules.
- Fixed a formula-search filter that admitted an unrelated disconnected neutral
  mixture merely because one fragment had internal formal charges. Explorer
  now labels charged connected records separately, and Lab copy accurately
  describes Builder's 2D-only handling of charged drawings.
- Detailed outcomes and limits are in
  `history/cross-page-chemistry-audit-2026-09-25.md`. All 32 Python and 17
  JavaScript tests pass; TypeScript, production build, and `git diff --check`
  pass. Nothing was published to Wix or uploaded to GitHub.

## 2026-09-25 — Home page and four-page navigation

- Added a Home page at `/` with clear entry points to Explore Molecules,
  Molecule Builder, and Reaction Lab. It explains the prototype's chemistry
  and 3D-model limitations without presenting the illustration as a live model.
- Moved the existing Explorer entry point to `/explore.html` and connected all
  four pages through consistent navigation. Updated the Vite build and README
  for the new routes.
- Added navigation tests and checked the Home page on desktop and mobile. The
  mobile layout has no horizontal overflow, and Home → Explorer → Home works
  in the browser. The Explorer water model still loads in 3D.
- The site remains local; it has not been published to Wix or GitHub.

## 2026-09-26 — One-command local launcher

- Added `start-local.command` for macOS. One run starts the RDKit chemistry
  service and Vite website, waits for both to respond, and opens Home in the
  default browser. Control-C stops only the two processes it started.
- The launcher reuses already-running local services, checks for unrelated
  processes on ports 8000/5173, and reports missing Python, Node, or Vite
  dependencies instead of failing silently. Updated the README instructions.
- Verified startup, the already-running path, and cleanup after Control-C;
  neither local port remained in use after stopping. This remains a local
  preview, not a Wix publication or GitHub upload.

## 2026-09-28 — Shared compound catalog and cross-page workflow

- Added one source of identity (`src/shared-molecules.json`) for 18 featured
  compounds used by both Explorer and Reaction Lab. Explorer retains its six
  fully reviewed property panels and adds twelve common compounds with clearly
  labelled unreviewed properties. Ionic sodium chloride and sodium hydroxide
  use PubChem's 2D fallback when a molecular 3D model is unavailable.
- Added Explorer buttons to send the selected structure—not just its formula—
  to either Reaction Lab input. The Lab keeps the selected structure distinct
  from same-formula isomers and still requires the user to choose a supported
  reaction pathway. Listed sodium hydroxide is interpreted as hydroxide plus
  an omitted sodium spectator in the simplified ionic equation.
- The Lab now recognizes listed propene for supported hydrogenation and bromine
  addition; unsupported pairs still do not produce invented reactions. Builder
  now saves the current drawing in the browser tab and restores it when
  returning from another page; no more example drawings were added.
- Browser-tested Builder drawing restoration, Explorer propene → Reaction Lab
  handoff, competing SN2/E2 choices, listed sodium hydroxide interpretation,
  and a balanced 3D propane product from propene + hydrogen. Verified 33 Python
  and 20 JavaScript tests, TypeScript checking, and a production build. All changes remain local;
  nothing was published to Wix or uploaded to GitHub.

## 2026-09-28 — Seven-family Reaction Lab library

- Replaced the small example-chip row with a filterable Organic Reaction
  Library spanning addition, elimination, substitution, oxidation, reduction,
  condensation, and hydrolysis. A loaded pair still requires the user to choose
  a supported pathway. Choosing one now previews the proposed net equation
  before the 3D calculation.
- Added three reviewed, atom- and charge-balanced teaching examples: ethyl
  ethanoate + water → ethanoic acid + ethanol (acid-catalyzed hydrolysis),
  2-propanol + sodium hypochlorite → acetone + sodium chloride + water
  (simplified oxidation), and acetone + hydrogen → 2-propanol (reduction).
  The oxidation card and result warn that the net equation is not a procedure
  and does not capture other possible products.
- Added 2-propanol and ethyl ethanoate to the shared Explorer/Lab compound
  catalog, bringing it to 20. Sodium hypochlorite remains a Lab-only reagent.
- Verified all 34 Python and 20 JavaScript tests, TypeScript checking, and a
  production build. Browser-tested family filtering, each new pair, net
  equations, atom balance, and 3D products. The site remains local and was
  not published to Wix or GitHub.

## 2026-09-29 — Shorter pages and Reaction Lab guide

- Shortened visible copy on Home, Explorer, Builder, and Reaction Lab. Search
  tips, drawing guidance, extra molecule properties, and detailed reaction
  interpretation now open on demand without removing them.
- Added a compact, expandable Reaction guide describing all seven supported
  families and their current mechanisms (including SN1, SN2, E1, and E2).
  Kept the Lab's educational-warning label visible.
- Verified 34 Python and 21 JavaScript tests, TypeScript checking, and a
  production build. Browser-checked Home, Explorer, Builder, and the collapsed
  and expanded Reaction guide. These changes remain local; nothing was
  published to Wix or GitHub.

## 2026-09-29 — Explorer layout correction

- Decoupled the Explorer's 3D stage height from the sample-molecule list. The
  list now scrolls within its own area while the viewer and property panel keep
  a stable size. Stacked the Explorer header navigation on narrower screens.
- Browser-checked desktop and mobile layouts and scrolling through the full
  compound list. The production build passed; the fix remains local.

## 2026-09-29 — GitHub backup

- Uploaded the current website source to Ryan's `ryanchen2010-eng/capstone-project`
  repository on branch `codex/capstone-site-2026-09-29`.
- Opened draft pull request #1 for review. The repository is public, but the
  website is still an unfinished local prototype: the pull request was not
  merged, and nothing was published to Wix.

## 2026-09-30 — GitHub merge and visual Reaction Lab

- The earlier GitHub pull request #1 was subsequently merged into `main` at
  `a6142c67563978111ea672b93059ca395c8c3cb3`. The local working branch still has
  the ongoing project edits; nothing has been deployed to Wix.
- Selecting a supported reaction now immediately shows a 2D reactants → products
  diagram. Broken, formed, and changed-order bonds have slim red, blue, and gold
  highlights. Reacting hydrogens and all net byproducts are included; E1 water
  remains the medium, and alkali hydroxides keep their simplified ionic equation.
- All 17 existing pathways and the supported unlisted drawing rules have verified
  atom-preserving net bond changes. Products are checked against their exact
  structures before highlighting; future unsupported mappings get plain diagrams
  without guessed changes. These diagrams do not show a full curved-arrow mechanism.
- Added a 2D reaction / 3D product switch. 3D is generated on request and retained
  when switching views. Reactant/condition/pathway changes clear stale previews
  and cancel prior requests. Longer facts and conditions remain collapsed.
- Verified 52 Python tests, 21 JavaScript tests, TypeScript, and a production build.
  Browser-checked SN2, rapid SN2 → E2 switching, addition, 2D/3D retention, input
  reset, and responsive desktop/mobile diagrams. New changes remain local, not
  uploaded to GitHub or published to Wix.

## 2026-09-30 — Lewis-style diagrams and linked atom inspection

- Reaction Lab now draws explicit carbon and hydrogen labels, formal charges,
  thin bonds, and supported lone-pair dots. It uses each compound's actual graph,
  not a copy of the reference picture. Net bond-change colors remain intact.
- Added Compare mode: desktop shows 2D reactants/products beside the 3D main
  product; phones stack them without horizontal page overflow. Each mapped atom
  is an accessible 2D target. Hover links both views, click/tap pins an atom,
  Enter/Space selects a focused atom, and Clear atom/Escape clears it.
- Preserved exact atom IDs, including individual hydrogens, through reaction
  transformations and 3D embedding. Highlights never guess by element or atom
  order. Atoms appearing only in byproducts are labelled outside the main-product
  3D view. Incomplete mappings disable linkage instead of marking a wrong atom.
- Added purple 2D outlines and a 3D halo/label. A 3D pick reveals the matching
  product atom inside the diagram scroll area, without jumping the page. Changing
  pathways cancels queued picks, invalidates old click callbacks, and clears halos.
- Browser-verified methanol's 3D oxygen → both 2D occurrences, distinct ethanol
  carbons, byproduct exclusion, Escape, pathway resets, a larger ester product,
  and the 390px mobile layout. Regression tests cover bidirectional hover and
  interaction lifecycle. Verified 55 Python and 40 JavaScript tests, TypeScript,
  and a production build (existing Builder bundle-size warnings remain).
- Limits: diagrams show net reaction changes, not full curved-arrow mechanisms
  or stereochemical predictions. Lone-pair dots are conservative electron counts,
  not 3D electron geometry; unsupported/aromatic assignments are not guessed.
  Changes remain local, not uploaded to GitHub or published to Wix.

## 2026-09-30 — Expanded Explorer descriptions

- Left Reaction Lab's Lewis-style/linked-atom work unchanged. Explorer now has
  a Chemical behaviour section below its description, with six readable cards:
  flammability, reactivity, toxicity, acidity/basicity, oxidation/corrosion, and
  heat of combustion. Its existing 3D viewer keeps a stable size.
- Added original, sourced qualitative notes and a richer overview for all 20
  featured compound CIDs. References include ILO/WHO chemical safety cards,
  NOAA, USGS, PubChem, ATSDR, and chemistry education sources. An expandable
  guide explains the six terms separately from compound-specific claims.
- Isomers retain their own notes through exact-CID lookup. Unreviewed PubChem
  compounds show a clear unknown notice and a direct source, not guessed
  flammability, toxicity, pH, or combustion energies. pH is explained as a
  solution property; energy notes are qualitative, not numerical thermochemistry.
- Browser-checked Water → Methane → Ethanol notes, the glossary, and a live
  Aspirin search with its unreviewed fallback and working 3D view. Verified a
  single-column card layout with no page overflow at 390px. The 3D stage stayed
  560px on desktop and 420px on mobile; expanding the desktop guide did not
  change the stage height. Saved `history/explorer-descriptions-preview-2026-09-30.jpg`.
- Verified 48 JavaScript and 55 Python tests, TypeScript, production build, and
  whitespace checks. Existing Builder bundle-size warnings remain. This remains
  local work; nothing was uploaded to GitHub or published to Wix.

## 2026-10-01 — Private Wix import preparation

- Ryan authorized importing current progress into Wix My Site 1 as a private
  trial. Confirmed Site 1 still has the old Explorer and offers page-password
  access. Opened its password setup for Ryan to enter/save himself; no password
  was entered by the assistant and nothing was published or replaced.
- Prepared a host-neutral Docker package and a separate private Flask/Gunicorn
  gateway. The website and every chemistry API require the app's own session;
  a Wix page password alone does not protect the external service.
- Added guarded startup, secure partitioned cookies, origin/body checks,
  protected compressed assets, process-local request/job limits, minimal health
  status, and redacted RDKit diagnostics. Local development remains unchanged.
- Verified 130 tests (51 JavaScript, 79 Python), TypeScript, frontend build,
  compressed-asset integrity, and Gunicorn factory configuration using synthetic
  credentials only. Actual Linux Docker build and HTTPS/Wix iframe behavior are
  not verified yet.
- Render's free tier was proposed; hosting selection is awaiting Ryan's answer.
  No hosting account/service, repository permission, payment, GitHub upload,
  or public launch was performed. See `history/wix-private-trial-2026-10-01.md`
  and `docs/private-wix-trial.md` for exact status and handoff requirements.

## 2026-10-01 — Compact Explorer information

- Ryan chose to keep running locally for now and revisit Render hosting when
  ready. Wix and the private deployment package were left unchanged.
- Combined physical facts and chemical behaviour into one always-visible
  Molecule information panel. Removed the separate More properties section;
  definitions, references, and the teaching disclaimer remain in a small
  optional Definitions and sources disclosure.
- Shortened all 20 featured compound profiles to a one-sentence overview,
  brief everyday uses, and concise values. Added a flexible 13-property
  registry, including reviewed state, appearance, water solubility, density,
  functional groups, hydrogen bonding, and stability where appropriate.
  Extra rows appear only when that exact compound has reviewed data.
- Missing values use Not available or Not reviewed; truly inapplicable values
  can use N/A. Kept units, essential conditions, ionic lattice descriptions,
  sublimation, and decomposition rather than hiding them as missing data.
  Combustion behaviour is qualitative, not an invented heat-of-combustion value.
- Browser-checked Water, carbon dioxide's phase values, optional sources,
  unreviewed Aspirin from PubChem, and Aspirin transfer into Reaction Lab.
  Verified no horizontal overflow at 1366px desktop and 390px mobile, with
  stable 560px and 420px viewer stages respectively. Saved
  `history/compact-explorer-preview-2026-10-01.jpg`.
- Verified 139 automated tests (60 JavaScript, 79 Python), TypeScript checking,
  the production build, and whitespace checks. Existing Builder bundle-size
  warnings remain. Builder and Reaction Lab code were not changed for this
  step; no GitHub upload, Wix publication, or Render deployment was performed.

## 2026-10-01 — Ionic Explorer results are information-only

- Removed sodium chloride and sodium hydroxide from Explorer's default sample
  list, leaving 18 molecular samples. Kept both records and their reviewed
  information in the complete 20-compound shared catalog and explicit searches;
  Reaction Lab's data and examples were not removed.
- Ionic search results now show a short notice and the information panel, with
  no 3D/2D diagram or empty viewer area. They do not request structure or
  depiction files. Ordinary molecular results retain their existing viewers.
- Added PubChem search metadata based on oppositely charged separate fragments,
  not a name or the mere presence of formal charges/metals. Connected zwitterions,
  individual ions, and neutral metal-complex records are not automatically
  classified as salts. Backend search acceptance and structure endpoints remain
  unchanged.
- Browser-verified NaCl, NaOH, an unlisted potassium chloride search, clearing
  the search back to 18 samples, and restoring Water's 3D viewer. Ionic layouts
  have no horizontal overflow at desktop and 390px mobile widths. Saved
  `history/ionic-explorer-preview-2026-10-01.jpg`.
- Verified 152 tests (72 JavaScript, 80 Python), TypeScript, the production
  build, and whitespace checks. Lifecycle tests cover absent/broken viewer
  cleanup, no ionic diagram requests, stale 3D/2D responses, and re-enabled
  selection buttons. Existing Builder bundle-size warnings remain. Changes
  remain local; nothing was uploaded, deployed, or published.

## 2026-10-03 — Reaction calculator

- Added a collapsed Reaction calculator inside Reaction Lab's result panel.
  After selecting a supported pathway, users can enter consumed-reactant amounts
  in g, mg, mol, or mmol to find the limiting reactant, theoretical main-product
  yield, and excess amounts. A second mode accepts a target product amount and
  calculates stoichiometric minimum reactant requirements.
- Added structure-derived molar masses, exact input-slot correspondence, unit
  coefficients, and a reusable atom/charge balance gate to the existing reaction
  metadata. All 17 current equations and supported generated pathways are
  covered without a 3D calculation. This is not a general equation balancer or
  an actual-yield predictor.
- Full NaOH/KOH/etc salt masses are retained even when the net equation omits
  the spectator cation. E1 excludes water when it is only the medium. Catalyst
  quantities and practical excesses are not calculated; pure reagents and 100%
  conversion are assumed. Reversible-reaction limitations and the OpenStax
  method reference remain in a collapsed Assumptions and method section.
- Changing a pathway, calculation mode, input, or unit clears old results;
  switching pathways also clears quantities. Invalid targets and unbalanced
  metadata do not produce a calculated result. Names and notes use safe text.
- Browser-verified NaOH SN2 amounts and target calculations, zero-target error
  reset, E1 solvent exclusion with mmol, and a common esterification calculation.
  The 320px mobile layout has no horizontal page overflow. Saved
  `history/reaction-calculator-preview-2026-10-03.jpg`.
- Verified 192 automated tests (98 JavaScript, 94 Python), TypeScript, the
  frontend production build, and whitespace checks. Existing third-party
  Builder bundle warnings remain. Work is local; no GitHub upload, ngrok setup,
  Wix publication, or Render deployment was performed. Feature 2 is awaiting
  Ryan's description.

## 2026-10-06 — Bond and geometry measurements

- Added one shared, collapsed Measure 3D tool to Explorer, Builder, and Reaction
  Lab's main-product viewer. Distance uses two atoms in Å; angle uses three
  atoms with the middle atom at the vertex; signed torsion uses four atoms
  around the middle bond and is reported in degrees.
- Atoms can be selected directly in 3D or through a keyboard-friendly atom
  list. Numbered highlights, dashed lines, an ordered selection, clear/reset,
  and mode controls keep the UI compact. Normal rotation/zoom and Reaction
  Lab's linked atom inspector remain available; Off restores ordinary pinning.
- Values use the exact displayed model coordinates, not experimental geometry.
  Non-bonded sequences are labelled, undefined geometry is rejected, and ionic
  information-only or 2D-only results have no controls. Molecule, drawing,
  pathway, stale-response, and error transitions clear old selections and
  only remove the measurement tool's own overlays.
- Browser-verified water O–H distance (0.969 Å) and H–O–H angle (104.0°), ethanol
  distance and signed torsion, keyboard selection, model replacement, and
  rotation. Builder's generated ethanol C–C distance was 1.515 Å. Reaction Lab
  measurements worked via actual 3D clicks in Compare; normal atom linking
  resumed in Off, and changing to E2 removed the old measurements.
- All three pages had no horizontal page overflow at 320px. Saved
  `history/bond-measurements-preview-2026-10-06.jpg`. A separate numerical check
  compared 384 distance/angle/torsion results with RDKit to 1e-8 tolerance.
- Verified 229 automated tests (135 JavaScript, 94 Python), TypeScript, the
  production build, and whitespace checks. Existing third-party Builder
  bundle-size warnings remain. Work remains local; no GitHub upload, ngrok
  setup, Wix publication, or Render deployment was performed.

## 2026-10-06 — Solution calculator

- Added the same compact, collapsed Solution calculator to Explorer and Reaction
  Lab. Its three modes find molarity, required pure-solute mass, or the stock
  aliquot and dilution factor for a target concentration and final volume.
  No new page, chemistry endpoint, or third-party integration was needed.
- Explorer uses the selected compound's strict g/mol property, including ionic
  information-only results. Reaction Lab lets users select Molecule 1, Molecule
  2, or manual entry inside the drawer, independently of reaction matching.
  Automatic mass reuse requires exact catalog identity and structure; it never
  uses formula alone or replaces a full salt with its active ion's mass.
- Supports g/mg/mol/mmol, L/mL/µL, and mol/L/mmol/L/µmol/L. Missing molar mass
  can be entered manually and does not block mole inputs or dilution. Manual
  overrides are labelled. Compound, mode, input, and unit changes invalidate
  old results. Invalid values, impossible concentration increases by dilution,
  overflow, and underflow produce short errors instead of misleading output.
- Final volume always means the whole solution. Dilution reports the stock
  aliquot and final total separately, not an exact added-solvent amount.
  Collapsed assumptions explain pure-solute and exact-form requirements,
  formula-unit molarity for salts, lack of solubility/suitability checking, and
  the OpenStax molarity/dilution reference.
- Browser-verified NaCl concentration (5.8443 g in 100 mL → 1 mol/L), NaCl mass
  (250 mL at 100 mmol/L → 1.4611 g), and dilution (1 mol/L stock → 100 mmol/L
  in 250 mL gives a 25 mL stock aliquot). Checked invalid dilution targets,
  mmol inputs without mass, NaOH's full mass, manual overrides, compound
  resets, and manual µL-scale dilution in Reaction Lab without a pathway.
- Both calculator layouts have no horizontal page overflow at 320px. Saved
  `history/solution-calculator-preview-2026-10-06.jpg`. Work remains local;
  nothing was uploaded to GitHub, exposed through ngrok, deployed, or published.
- Verified 277 automated tests (183 JavaScript, 94 Python), TypeScript checking,
  the production build, and whitespace checks. Existing third-party Builder
  bundle-size warnings remain. Numerical, panel-lifecycle, identity-sharing,
  invalid-input, and extreme-value display regressions are covered.

## 2026-10-07 — Chemistry Calculator Menu

- Added the fifth page, Calculators, with six topics and a desktop left menu /
  compact mobile selector. Home and every tool link to it. Included it in Vite
  production inputs, the Docker allowlist/COPY, and authenticated return routes.
  Existing Explorer and Reaction Lab calculators remain in place.
- Moles/particles supports kg/g/mg/µg, mol/mmol/µmol and entity counts, using the
  SI Avogadro constant. Molecules, atomic species and ionic formula units are
  distinguished. Explorer's Open in Calculators transfers exact identity,
  structure and full compound mass; same-formula isomers are never substituted.
  Solutions reuses the original concentration, solute-mass and dilution panel.
- Reaction amounts uses the existing server's 17 reviewed, balanced equations
  and the shared limiting-reactant/target-amount arithmetic. Choice labels include
  actual reactant/product names. Invalid metadata is rejected; unavailable
  catalog shows a retry while other arithmetic remains local and usable.
- General equilibrium offers K/Q, Q/K direction and a bounded one-reaction
  extent solve, with explicit coefficients/phases/concentrations/charges and
  optional fixed spectator rows. Pure phases have activity 1 and are assumed
  present. The user confirms the balanced equation; names do not verify it.
- Acid/base models include strong and weak monoprotic acid/base, acid or base
  conjugate buffers, and one neutral polyprotic family with up to three steps.
  Full water equilibrium, family mass and charge balance are solved together.
  Solubility supports one two-ion salt with common ions and Qsp comparisons;
  supersaturated mixtures cannot produce a dissolution-only amount calculation.
- Advanced tools require user-entered K/pK and, for pH, Kw. Ideal or fixed
  supplied activity coefficients use a 1 mol/L concentration standard state.
  Entered mode requires coefficients for every dissolved family/ion/spectator
  species. Temperature edits wipe constants and coefficients; K↔pK changes wipe
  the numeric constant. No lookup, correction model or temperature extrapolation.
- All edits clear stale outputs; zero inputs remain exact zeros. Undefined
  expressions, unsupported ranges and nonconvergence fail explicitly. Tests and
  independent audits verify positivity, material/equilibrium/charge residuals,
  including subnormal charge and overflowing-scale failures. Model assumptions,
  limits, formulas and primary references stay collapsed and are also documented
  in docs/calculator-models.md. No rates, actual-yield, accuracy or safety claims.
- Browser checks verified full NaCl particle counts, NaOH solution concentration,
  supported SN2 yield, A⇌B from 1/0 to 0.5/0.5 at K=1, the acetate buffer at
  pH 4.74488, and common-ion AgCl-type solubility in ideal and entered-γ modes.
  Missing spectator γ blocks output. Temperature changes require new constants.
  Dimethyl ether transfers as that exact isomer, not ethanol; Enter submits the
  mole calculation. All six topic layouts have one visible tool and no page
  overflow at 320px. Temporary viewport override was restored.
- Verified 414 automated tests (319 JavaScript, 95 Python), TypeScript, the
  production build and whitespace checks. Existing third-party Builder warnings
  remain. Saved history/calculator-menu-preview-2026-10-07.png. Work is local;
  no GitHub upload, public tunnel, Wix/Render deployment or publication occurred.

## 2026-10-07 — Reaction bond highlight spacing

- Changed the shared reaction diagram renderer to color the bond strokes that
  RDKit trims around atom labels. Red, blue and amber highlights no longer use
  filled strips extending through the atom centers and letters.
- Added a regression check for all 17 reviewed pathways: colored bond paths are
  open strokes with endpoints clear of the atom centers. All 22 diagram and
  reaction preview checks pass; whitespace checks pass.
- Restarted the local preview and visually checked ethanoic acid + ethanol,
  including the formed O–H bond in water. Saved the screenshot in
  history/reaction-bond-label-spacing-2026-10-07.png.

## 2026-10-07 — Smoother linked atom inspection

- Coalesced 2D and 3D mouse hover updates into one animation frame, using the
  newest pointer position without repeatedly cancelling the queued frame.
  Brief atom-edge misses have a 70 ms grace period. Leaving, rotating, zooming,
  clearing and keyboard input cancel pending hover work immediately.
- Reuse each inspected atom's halo and label for the current model; hide them
  when inactive and dispose them when the diagram/model changes. Label creation
  skips intermediate viewer draws. Cached atom/target indexes replace repeated
  searches, and an unchanged atom no longer triggers diagram layout/scrolling.
- Reserved two lines for atom status to reduce layout changes during inspection.
  Pinning, exact atom correspondence and shared measurement clicks remain usable.
- All 57 targeted interaction, measurement and lifecycle checks, TypeScript,
  production build and whitespace checks pass. The build retains its existing
  third-party Builder bundle warnings.
- Browser checks verified both directions of atom selection, returning to a
  previously inspected oxygen, rotation with a selected atom, and a C1–C2
  distance of 1.498 Å. Saved history/smooth-atom-inspection-2026-10-07.png.
  The changes are local and the preview remains running.

## 2026-10-07 — Structural reaction engine generalization

- Recorded the before-refactor audit and all 17 existing pathways before edits.
  Added reusable graph detectors and a selected-site, explicit-H transformation
  engine. Removed example-pair shortcuts, the tiny organic-molecule caps and
  duplicated first-match product generation in the diagram renderer.
- Generalized alkene hydrogenation, Br2/Cl2 addition, supported hydration/HX
  orientations, alcohol oxidation stages, aldehyde/ketone reduction,
  acid/alcohol esterification, ordinary ester hydrolysis and bounded SN1/SN2/E1/E2.
  Multiple functional groups and distinct beta-elimination products are separate
  choices, not a guessed preferred product. All original products remain.
- Products are sanitized and checked for atom/map conservation, net charge,
  unexpected radicals/H, duplicate bonds and valid fragments before display.
  Reactant provenance and bond changes feed the same mapped 2D/3D graphs.
  Original supplied atom maps are retained in provenance. Amber site markers
  stay separate from purple hover/pin inspection and shared measurements.
- Kept the existing layout and sample drawings. Added only reagent identities,
  site labels/markers and concise support/failure explanations. Primary-alcohol
  aldehydes are explicitly oxidation stages, not guaranteed isolated products.
  Acid–amine amidation and further aldehyde oxidation remain unsupported.
- Added 26 multi-molecule structural coverage tests and a site-overlay lifecycle
  test; updated obsolete rejection expectations while retaining strict old-product
  regressions. All 450 checks (122 Python, 328 JavaScript), TypeScript, production
  build and whitespace checks pass. Full details: docs/reaction-engine-coverage.md.
- Browser verified a non-preset PubChem propanoic acid/methanol esterification,
  exact oxygen mapping, both independently selected 1,5-hexadiene sites and
  selected carbon 6 in both views. Saved the structural-reaction-engine screenshot.
  Work remains local; no GitHub push, publication or hosting change.

## 2026-10-07 — Pathway reasoning, comparison and mapped mechanisms

- Recovered saved task context after a connection/compaction error; no saved
  project files were lost. Finished the pending extension without replacing
  the structural engine or redesigning the two-panel layout.
- Added deterministic graph/condition factors underneath each pathway and a
  comparison panel generated from those same factors. Qualitative labels only:
  Strong match, Possible, Unfavorable or Unsupported; no percentages or winner.
- Added reusable mapped elementary steps for SN2, E2, SN1 and E1. Each chosen
  elimination product uses its actual beta H. Carbocation/oxonium states are
  intermediates, not transition states. SN1 includes explicit solvent-water
  deprotonation; E1 couples H removal and pi formation in its second step.
- Added step controls, Lewis-state diagrams and electron source/destination
  highlights, independent of existing hover/pin, selected sites and measurements.
  Only actual retained final-product atoms are highlighted in 3D; intermediates
  remain 2D. Energy topology is qualitative, with no calculated activation energy.
- Added an explicit oxidation-stage setting and aqueous further aldehyde-to-acid
  reporting rule. No direct primary-alcohol-to-acid shortcut; ketones/tertiary
  alcohols do not acquire this rule. Protocol, pH/protonation, side reactions and
  isolated products remain unpredicted. Amidation remains unsupported.
- Added 26 focused checks (18 Python, 8 JavaScript). All 476 checks pass (140
  Python, 336 JavaScript), including the original 450, plus TypeScript, production
  build and whitespace checks. Browser verified all four mechanisms, exact
  electron endpoints, condition invalidation, a PubChem ethanal oxidation and
  320px layout containment. Wide tables/state diagrams scroll within panels.
- Full report: docs/reaction-pathway-insights.md. Preview artifact:
  history/reaction-pathway-insights-2026-10-07.png. Everything remains local;
  the preview is running, with no GitHub push or publication.

## 2026-10-07 — Functional groups, epoxidation and progressive information

- Began the next incremental slice of the long-term beginner/university/live
  teaching tool direction. Preserved layout, working structural rules, mapped
  mechanisms and calculators. No accounts or classroom management.
- Added a modular peroxyacid epoxidation rule for isolated hydrocarbon C=C
  sites, actual acid coproducts and explicit atom/map/charge validation.
  Multi-site options are separate; defined stereochemistry and unsupported
  selectivity are rejected. No epoxidation mechanism/stereochemical prediction.
- Added automatic independent functional-group detection and a collapsed
  inspection panel for both resolved inputs. Group selection highlights exact
  2D/3D reactant atoms. 3D is requested explicitly; changing groups reuses the
  model. Changing inputs clears stale state and aborts old responses.
- Centralized mechanism information and implemented-group suggestions. Added
  Basic / Explanation / Mechanism / Advanced depths and multiple classification
  labels. Mechanism depth reuses existing mapped SN/E steps; unavailable
  mechanisms are labelled, not fabricated.
- Added 31 checks (19 Python, 12 JavaScript). All 507 tests pass (159 Python,
  348 JavaScript), including all 476 prior checks; TypeScript, production build
  and whitespace checks pass. Browser verified epoxidation and reactant group
  3D, existing mechanism reuse, 320px containment and the desktop layout.
- Full report: docs/reaction-lab-expansion.md. Scope still excludes full
  presentation controls, stereochemical outcomes, universal reaction discovery
  and acid–amine amidation. Recommended next chemistry step: distinguish
  acid–amine salt formation from validated amidation conditions.
- Everything remains local; no GitHub push, publication or hosting change.
  Saved history/reaction-functional-groups-2026-10-07.png and
  history/reaction-epoxidation-information-2026-10-07.png. The updated local
  preview remains running at http://127.0.0.1:5173/reaction-lab.html.

## 2026-10-07 — Deeper mapped mechanisms, stereo foundation and structural rules

- Preserved the existing Reaction Lab layout and all working tools. Extended
  the SN2/E2/SN1/E1 mechanism data with both before/after states, explicit bond
  changes and proton transfers. Electron source bonds must exist before the
  step, and mechanism products must match the selected stereochemical identity.
  Highlighted states are used; automatic curved-arrow routing is not implemented.
- Added reusable potential-center detection, accurate CIP R/S assignment, E/Z
  detection, common-H/H cis/trans descriptions, neighbor-order-aware SN2
  inversion, and signed E2 beta-H torsions from actual supplied 3D conformers.
  Maps do not affect CIP priorities. Unknown stereo remains unassigned.
  Inspection/Advanced panels expose reports without claiming selectivity.
- Added generalized alcohol dehydration/substitution, ester saponification,
  alkyne hydrogenation/halogenation/hydrohalogenation, catalytic net alkene
  dihydroxylation, and a finite 2/4/6-monomer polymerization model. Retained and
  multi-molecule-tested the already implemented aldehyde-to-acid oxidation.
  New rules use structural sites, not example identities. Repeated reagents
  now aggregate into correct calculator coefficients; model variants have
  distinct IDs and parameters are separate from atom indices.
- Saponification produces a real carboxylate and alcohol, with no invented
  neutral acid work-up; its charged main product remains 2D-only. Polymerization
  models consumed benzoyl peroxide, explicit phenyl end groups and two CO2,
  not bulk polymers or experimentally predicted distributions. Amidation
  remains deferred; ordinary acid + amine never becomes an automatic amide.
- Added 40 checks (35 Python, 5 JavaScript). All 547 tests pass (194 Python,
  353 JavaScript), plus TypeScript, production build and whitespace checks.
  Tests include multiple structures per family, exact maps/charges, both SN2
  enantiomers, priority-changing inversion, E/Z bounds, torsion failures and
  input/model invalidation. Existing regression checks remain green.
- Browser verified the SN1 proton-transfer before/after states, valid 2D charged
  saponification, a rendered finite oligomer, and alkyne hydrogenation with
  1 mol propyne + 2 mol H2 giving 1 mol propane in the amount calculator.
  Bromoethane inspection reported mapped anti/gauche beta-H torsions from its
  actual conformer. At 320px, wide mechanism states stay inside keyboard-focusable
  scrolling panels without page-wide overflow. No browser errors observed.
- Full scope, sources and limitations: docs/reaction-chemistry-depth.md.
  Saved history/reaction-mechanism-depth-2026-10-07.png. Recommended next step:
  conformer-aware E2 stereoproducts and explicit syn-addition outcomes using
  this foundation. Nothing was pushed or published. Local preview remains
  running at http://127.0.0.1:5173/reaction-lab.html.

## 2026-10-08 — Move standalone calculations out of Reaction Lab

- Removed the embedded solution calculator and its compound selector from
  Reaction Lab. Standalone concentration/mass/dilution calculations remain on
  Calculators → Solutions. Explorer's existing calculator is unchanged.
- Added compact Use in Calculators shortcuts under resolved reactants. Transfers
  preserve exact identities/structures and full salt masses, save the reaction
  draft, and open the Solutions topic. Ambiguous formulas never select an isomer
  or borrow a mass. Unknown masses stay manual; blocked storage shows a fallback.
- Moved alkyne/chain controls beside matching pathway options. Equivalents appear
  only for matched alkyne halogenation/hydrohalogenation, chain length only for
  polymerization. Unrelated reactions show neither; edits hide stale controls.
  Functional-group inspection stays collapsed/optional; the reaction-dependent
  amount calculator stays beside the selected equation. No layout redesign or
  chemistry-rule changes.
- Added seven checks; all 554 tests pass (194 Python, 360 JavaScript), plus
  TypeScript, production build and whitespace checks. Updated old embedding
  assertions to test the new cross-page route and preserved Explorer behavior.
- Browser verified contextual one/two-equivalent product changes, separate chain
  controls, a sodium hydroxide transfer with full 39.997 g/mol mass, a 1 mol/L
  arithmetic result, and restoration of the original reactant draft on return.
  Existing SN2 mapped 2D/3D product generation still works; no browser errors.
- Report: docs/reaction-lab-tool-placement.md. Saved Reaction Lab placement and
  solution-transfer screenshots dated 2026-10-08. Changes remain local; no
  GitHub push, publication or hosting change.

## 2026-10-09 — Phase 2 initial increment: reaction-site-compatible hydrogenation

- Added reusable per-pathway site/group compatibility and exact mapped-bond edit
  contracts. Applied them only to existing alkene hydrogenation; no new family,
  page layout change or automatic expansion of other pathways. Distance alone
  never permits an unvalidated group to be treated as inert.
- Screened remote saturated alcohol groups and distant specified configurations
  now survive the selected isolated C=C reduction. Unselected bonds, individual
  atom charges and applicable tetrahedral/alkene configurations are checked
  through serialization. CIP priority changes do not falsely imply inversion.
  Unsupported competition or stereogenicity loss gives a specific rejection.
- Kept the Phase 1 ester pathways and their stereo validator behavior intact.
  Conjugation, aromatic/catalyst-sensitive environments, unvalidated spectators,
  small-ring/size limits and newly unassigned stereochemistry remain bounded.
- All 616 tests pass (232 Python + 384 JavaScript), including 22 new Python and
  eight new JavaScript checks. Production build and whitespace checks pass.
- Same 347-case audit: hydrogenation 9/14 (64.3%) → 11/14 (78.6%); only remote OH
  and remote specified center rows improve. All other pathway statuses and all
  38 negative controls are unchanged. Ester scores remain 90.0%/90.9%.
- Browser verified remote alcohol 2D/3D atom linking, two isolated alkene sites,
  and precise allylic-alcohol rejection. Preview refreshed and left running;
  temporary browser test tab closed. No GitHub push/publication/deployment.
- Full report: docs/reaction-lab-hydrogenation-phase2.md; preserved Phase 1
  baseline and separate Phase 2 JSON/evidence. Recommended next consumer is
  existing carbonyl hydrogenation with its own validated policy; not started.

## 2026-10-11 — Phase 2 increment: site-compatible carbonyl hydrogenation

- Applied the shared compatibility system only to the existing aldehyde/ketone
  H₂ reduction. Screened alcohol/ether spectators and distant specified centers
  retain exact mapped bonds/configurations. The selected C=O alone becomes C–OH;
  one actual H₂ supplies C–H/O–H. No layout change or new reaction family.
- Added carbonyl-specific competition checks, exact edit/serialization contracts,
  pre-canonicalization unsupported-stereo checks and precise public explanations.
  Potential hydroxy-carbonyl cyclization, nearby carbonyls, catalyst-sensitive
  ethers/alcohols and unvalidated groups fail closed. Aromatic/multi-carbonyl net
  options remain bounded; new alcohol stereocenters are not invented.
- Newly supported remote enantiomers and combined specified-center plus screened
  alcohol/ether substrates. Existing ordinary oxygen-containing cases now receive
  explicit validation, not a claim that they were all previously unsupported.
- All 648 tests pass (256 Python + 392 JavaScript), including 24 new Python and
  eight new JavaScript checks. All previous 616 are preserved. Production build
  and whitespace checks pass; existing dependency/chunk warnings remain.
- Same 347-case audit: carbonyl 6/11 (54.5%) → 7/11 (63.6%); only A115 remote
  specified center improves. All 335 non-carbonyl case statuses and 38 negative
  controls are unchanged. Zero incorrect results or failed previews, 206 options.
- Browser verified 3-methoxypropanal oxygen correspondence, (3S)-3-methylpentanal
  retained S/linked carbon, and levulinic acid's specific unvalidated-acid rejection.
  Preview refreshed to final code and left running; temporary browser tab closed.
- Report: docs/reaction-lab-carbonyl-phase2.md; separate final JSON and screenshots.
  No GitHub push/publication/deployment. Recommended next is existing alcohol
  oxidation with its own competition/local-stereo-loss policy; not implemented.

## 2026-10-13 — Phase 2B checklist revalidation

- Confirmed the October 11 carbonyl increment already fulfills the Phase 2B
  request. Audited source hashes are unchanged; no chemistry reimplementation,
  duplicate tests, new reaction family or layout change was needed.
- Fresh verification: all 648 tests pass (256 Python + 392 JavaScript), including
  the 32 carbonyl tests added above the original 616. TypeScript, production build
  and whitespace checks pass; existing dependency/chunk warnings remain.
- Reran all 347 completeness cases: observations match the saved carbonyl results.
  Carbonyl remains 7/11 (63.6%), versus Phase 2A baseline 6/11 (54.5%). Only A115
  improves against that baseline; all unrelated statuses and 38 negatives remain
  unchanged. Matrix inputs/expectations were not changed to improve the score.
- Report now explicitly labels this increment Phase 2B. Phase 2C alcohol oxidation
  is recommended but not started. No GitHub push, publication or deployment.

## 2026-10-13 — Phase 2C: site-compatible alcohol oxidation

- Added an oxidation-specific compatibility consumer for the existing actual
  alkali-metal hypochlorite reagent. Only primary/secondary C–OH sites with C–H
  oxidize; tertiary OH is not an ordinary carbonyl-forming site. First-stage
  aldehyde reporting and the separate further-oxidation pathway remain distinct.
- Screened ethers and separated alcohols, distant specified configurations and
  individually selected OH sites use exact mapped bond/charge/H-transfer checks.
  Only a checked reactive alcohol stereocenter becomes planar; unrelated stereo
  loss or charge changes cannot inherit a global permission. Competing or
  unvalidated environments give precise reasons and fail closed.
- All 686 tests pass (284 Python + 402 JavaScript), including 28 new Python and
  10 new JavaScript tests above 648. Updated two obsolete alcohol-rejection guards
  to retain coverage of the separate aldehyde restriction; no product/conservation
  assertions were weakened. TypeScript/build/whitespace pass; old warnings remain.
- Same 347-case audit: alcohol oxidation 8/12 (66.7%) → 9/12 (75.0%); only A086
  remote center improves. All 333 non-alcohol statuses and all 38 negatives are
  unchanged. Zero incorrect results/failed previews; 207 public site options.
- Browser verified the real Builder hand-off, carbonyl + salt/water equation,
  retained mapped S center and linked carbon 3 in 2D/3D. PubChem lookup was
  unavailable during the attempt; exact Builder input verified the public workflow.
- Report: docs/reaction-lab-alcohol-phase2c.md; separate JSON and browser evidence.
  No layout/frontend/Calculator changes, no new family, push or deployment.
  Recommend existing SN2 compatibility next; Phase 2D not started.

## 2026-10-13 — Phase 2D: site-compatible hydroxide SN2

- Added an SN2-specific spectator/site policy, exact C–X/C–O and charge contracts,
  and independent physical inversion with distant stereo retention. Existing
  methyl/primary/selected secondary/benzylic scope remains bounded; no new
  nucleophile or leaving-group family, layout/frontend or Calculator change.
- Screened remote OH/ethers and multiple eligible sites; small OH ring-closure,
  nearby ether, unvalidated competing groups, tertiary/allylic/ring-bound/
  neopentyl and unsupported stereo cases fail with precise reasons. One old
  unvalidated geminal-trihalide chemistry fixture now tests priority-changing
  inversion at the utility level and asserts public rejection.
- SN2 mechanism remains one concerted electron-movement step and now passes
  the same inversion/edit validator. SN1/E1/E2 rules were not expanded.
- All 732 tests pass (316 Python + 416 JavaScript), adding 32 Python and 14
  JavaScript checks above 686. TypeScript/build/whitespace pass; old warnings remain.
- Same 347-case audit: SN2 8/15 (53.3%) → 10/15 (66.7%); only A156 methoxy-benzyl
  and A160 remote ether improve. All 328 non-SN2 statuses and 38 negatives unchanged.
  Zero incorrect results/failed previews; 209 public site options.
- Browser verified Builder hand-off for a remote ether with two specified centers:
  reacting carbon 10 S → R, distant carbon 3 S → S, linked carbon 10 in 2D/3D,
  and both electron movements in one concerted SN2 step. Saved three evidence
  images; no warning/error console entries. Temporary verification tab closed.
- Report: docs/reaction-lab-sn2-phase2d.md; separate JSON. No push/publication/
  deployment or subsequent increment. Recommend separately validated E2 next;
  it has not been implemented.

## 2026-10-13 — Phase 2E: site-compatible hydroxide E2

- Added an E2-specific spectator/site policy, exact four-bond and two-charge
  contracts, actual beta-H maps and independently selectable alpha/beta sites.
  Screened remote OH/ethers and distant configurations now pass; rings, allylic,
  beta heteroatoms, small OH cyclization and unvalidated groups still fail closed.
- Only alpha/beta tetrahedra may become planar. Two specified local centers with
  one beta H determine a bounded anti E/Z relationship; unsigned alternatives
  remain unassigned. Distant parity is checked through mapped serialization.
- Supplied non-anti geometry can rotate to a kinematic acyclic anti candidate;
  this is not energy/clash/transition-state validation or proof of conversion.
  E2 mechanism retains all three concerted electron moves and uses the same validator.
- All 794 tests pass (352 Python + 442 JavaScript), adding 36 Python and 26 JS.
  Three old E2-exclusion/capability assertions updated without deleting tests or
  weakening SN2 product/inversion checks. TypeScript/build/whitespace pass.
- Source atom-map labels cannot split symmetry-equivalent beta sites; exact
  source/reaction identities remain. Local preview restarted with final code.
- Same 347-case audit: E2 4/13 (30.8%) → 7/13 (53.8%); A188/A190/A205 improve.
  All 333 non-E2 statuses and 38 negatives unchanged. Zero audit-flagged incorrect
  results/failed previews; 215 public options. Report flags pre-existing A190
  reversed-chain stereo expectation error; benchmark untouched, new strict
  tests validate the correctly retained configuration separately.
- Browser verified two E2 options, remote atom 3 S → S, C=C 10–12 Z, exact
  keyboard-linked beta atom 12 in 2D/3D and concerted H34/base43/Br11 movements.
  Dense SVG mouse targeting remains an existing UI limitation; no layout redesign.
- Final restarted browser preview also verified the existing propene E2 example,
  one symmetry-distinct site, water/Br− and exact linked carbon 2; no console errors.
- Report: docs/reaction-lab-e2-phase2e.md; separate JSON and four evidence images.
  No new family/reagent/examples, frontend/Calculator change, push or deployment.
  Recommend separate SN1 compatibility next; not started. Local preview running.

## 2026-10-13 — Phase 2F: site-compatible water SN1

- Added a water/carbocation-specific compatibility policy for screened tertiary/
  benzylic sites, distant ordinary OH/ethers, specified distant/reacting centers,
  multiple independent sites and a narrow symmetric CH2/CH2 allyl net model.
  Ordinary methyl/primary/secondary aliphatic, unequal allylic, ring-bound,
  shift-prone, small oxygen-capture and acid-sensitive cases remain excluded.
- Exact SN1-stage permissions validate ionization (+C/−X, planar C), water capture
  (+oxonium), and separate solvent-water deprotonation (hydronium + halide).
  Simplified net HX reports acid equivalents; the reaction calculator retains one
  net water equivalent with explicit solvent/model limits. No new nucleophile.
- Reacting-center configuration is lost and stays unassigned; distant mapped
  physical parity is retained and CIP independently reassigned. An independent
  remote-Cl example retains its physical center while its CIP letter changes R→S.
  Enhanced/relative stereo is rejected before canonicalization; no 50:50 ratio.
- All 847 tests pass (395 Python + 452 JS), adding 43 Python + 10 JS above 794.
  Two old exclusion/capability assertions updated for validated SN1 scope without
  removing tests. TypeScript/build/whitespace pass; existing build warnings remain.
- Same 347-case benchmark: SN1 4/11 (36.4%) → 5/11 (45.5%), only A179 improves.
  A177's ether remains excluded due to a potential five-membered capture path.
  All 335 non-SN1 scores and 38 negatives unchanged; no incorrect/failed-preview
  audit cases; 216 public options. Original matrix untouched, including prior
  separate E2 A190 stereo-expectation defect.
- Browser checked independent Builder handoff, exact linked product carbon 13,
  13 S→unassigned / distant 3 S→S, water O50 and separate deprotonation O53/H51.
  Three mechanism states work; no console warnings/errors. Dense large net 2D
  diagrams remain an existing rendering limitation, not redesigned in this phase.
- Report: docs/reaction-lab-sn1-phase2f.md; separate JSON and evidence screenshots.
  No new family, curated examples, frontend/layout/Calculator edits, push or deploy.
  Recommend separately validated E1 next; Phase 2G has not begun. Local preview
  restarted with final code; temporary verification tabs closed.
- Final existing tert-butyl chloride/water example rechecked after restart: SN1
  and unchanged E1 both offered, tert-butanol 3D and exact carbon 2 correspondence
  work, no browser warnings/errors. Fourth evidence screenshot saved.

## 2026-10-14 — Phase 2G: site-compatible water E1

- Added an independent E1 site/cation/beta-H/spectator policy. Screened distant
  OH/ethers and specified centers now work; saturated Me/Me and Me/Et secondary
  arms and narrowly H-free-central-pi allylic systems have conditional net support.
  Arbitrary primary/secondary, ring, rearrangement/capture and unvalidated
  functional groups remain excluded. No new reagent family or visible examples.
- Exact two-stage permissions validate +C/−X ionization before solvent beta-H
  removal/C=C formation/hydronium. Only reacting tetrahedra become planar; distant
  mapped physical parity is retained and CIP independently reassigned. E/Z and
  ratios remain unassigned; no E2 anti permissions leak into E1.
- Same-C–X beta equivalents are deduplicated without letting source map labels
  split symmetric positions. Distinct C–X identities stay selectable. Net HX is
  acid-equivalent reporting; water stays excluded from simplified net calculator
  arithmetic, not falsely limiting when its quantity is missing/zero.
- All 914 tests pass (438 Python + 476 JS), adding 43 Python + 24 JS above 847.
  Three old test methods update newly validated E1 scope/capability expectations
  without deleting tests. TypeScript/build/whitespace pass; old warnings remain.
- Fixed 347-case benchmark unchanged: E1 3/9 (33.3%) → 5/9 (55.6%), A199/A207
  improve. All 337 non-E1 scores and 38 negatives unchanged; no audit-flagged
  incorrect results or failed previews; 220 public site options.
- Separately reported original benchmark limits: A199 reversed terminal-SMILES
  parity expects R instead of retained S (independent strict tests validate S);
  A207 lacks an E/Z scoring flag, so “fully supported” there is not complete
  stereo resolution. A196 remains partial E/Z; A197's nearby ether is rejected.
- Browser checked independent Builder handoff for two-center benzylic substrate:
  E1 alongside unchanged SN1, exact linked beta atom 6, alpha 7 planar, distant
  atom 3 S→S, C=C 6–7 unassigned; ionization then O34/beta-H26 electron movements.
  No console warnings/errors; saved three screenshots. Local final-code preview
  running. Existing dense all-H 2D rendering not redesigned.
- Report: docs/reaction-lab-e1-phase2g.md; separate audit JSON. SN1/SN2/E2 rule
  module and frontend hashes match Phase 2F; Calculators/layout unchanged. No
  push, publication, deployment or next reaction increment. Recommend separately
  validated alkene hydration next; not started.
- Final restarted preview also verified the original tert-butyl chloride/water
  pair: unchanged SN1 alongside E1, C4H8 + HCl net reporting, linked beta carbon
  1, separate ionization and later elimination with explicit non-E2 clarification.
  Fourth screenshot saved; no browser warnings/errors; temporary test tab closed.

## 2026-10-14 — Phase 2H reaction consistency fixes

- Shared bounded SN1/E1 alkyl-cation assessment; screened isopropyl/sec-butyl
  now have independently verified water-capture options as well as E1. General
  allylic capture remains excluded with a resonance-product scope explanation.
- Four-pathway condition statuses distinguish match, reference difference,
  incomplete settings, evidenced SN2 protic solvation and unevaluated conditions.
  Eligibility remains separate; no rates, activation requirements or ratios invented.
- Primary-site SN2 permits a screened distant ordinary tertiary halide to remain
  mapped; tertiary SN2, nearby/product-OH closure and unsupported spectators remain
  excluded. Correct direct-O versus 3–6-membered closure wording; 422 reasons
  retained as safe text in existing UI controls.
- 976 tests pass (476 Python + 500 JS): 38 Python + 24 JS added. Original methods
  retained; existing intentional scope/label expectations updated, none deleted.
  Public review checks: 48 substrates / 192 matches / 125 options, no failures.
- Unchanged 347-case audit: only A182 sec-butyl SN1 improves, 5/11 → 6/11 (54.5%).
  All 346 other product sets, option counts and statuses unchanged; all 38 negatives
  rejected, no flagged incorrect results or failed previews. SN2/E1/E2 scores stable.
- TypeScript/build/whitespace pass; old build warnings remain. HTML/CSS, Calculators,
  molecular data and curated examples unchanged. Browser confirmed secondary SN1/E1,
  Reference differs badge, 3D 2-propanol and linked carbon 2; screenshot saved.
- Report: docs/reaction-lab-consistency-phase2h.md; results JSON with source hashes.
  Local preview started for verification. No publication, push or hydration work.
  Ready for a separately requested, independently validated hydration increment.

## 2026-10-14 — Phase 3A: site-compatible acid-catalyzed alkene hydration

- Added a hydration-specific shared-compatibility consumer: exact selected C=C,
  H/OH water maps, four net bond edits, spectator screening, strict unchanged-bond,
  charge, serialized-stereo and size checks. Other addition rules remain separate.
- New internal regio alternatives, valid E/Z consumption, screened styrene and
  distant specified configurations; independent tests cover remote ordinary OH/
  ethers and widely separated sites. New centers/syn/anti/ratios remain unsigned.
- Acid is required activation, not a reference mismatch. Conditional 2D stays
  inspectable; missing/unsupported activation or medium blocks 3D and returns 422.
  Acid is regenerated; one actual water equivalent enters theoretical arithmetic.
- Input direction guard rejects hydration annotations erased during normalization,
  including unsupported ring/terminal notation; no unsanitized chemistry is used.
- Fixed 347-case benchmark unchanged: hydration 6/14 (42.9%) → 10/14 (71.4%).
  A066/A067/A068/A069/A072 gain support; A074 1,7-octadiene is conservatively
  excluded for competing short pi-capture/cyclization. All 332 other pathway rows
  retain statuses/products/options/preview/geometry/mechanism counts; no incorrect
  audit result. Remaining A070/A071/A073 exclusions retain specific explanations.
- 1,051 tests pass (529 Python + 522 JS), 75 new. All 976 original methods retained;
  six old hydration activation/scope/capability assertions intentionally updated.
  Authenticated HTTP, exact 2D/3D maps, 16 arithmetic fixtures, specified-center 3D
  CIP and the prior 192-match/125-option four-pathway diagnostics pass.
- TypeScript, build and whitespace pass; existing dependency/bundle warnings remain.
  HTML/CSS, Calculators, curated data, benchmark and other rule modules unchanged.
  Browser confirms missing-acid gate and acid-enabled linked propene → 2-propanol.
- Report: docs/reaction-lab-hydration-phase3a.md; audit/results JSON and screenshot.
  Final local preview refreshed. No push/deployment/publication or Phase 3B work.
  Recommend separately validated existing hydrohalogenation compatibility next.

## 2026-10-14 — Phase 3B: site-compatible ionic alkene hydrohalogenation

- Added an HX-specific shared-compatibility consumer for actual HCl/HBr/HI,
  validated Markovnikov/benzylic orientation, internal alternatives, bounded rings,
  distant configurations and independent C=C sites. Exact H/X maps and four net
  bond edits are enforced by existing unweakened product/stereo validators.
- Screened oxygen retention is conditional ambient HCl only. HBr/HI OH/ether
  substitution/cleavage, acid-labile groups, short O/pi capture, shifts and
  unvalidated ring environments remain excluded. Distance does not prove inertness.
- HX is consumed, not regenerated acid. Radical initiation produces no ionic
  option; solvent capture/extra activation/absent ambient-HCl oxygen conditions
  permit only qualified 2D previews and return 422 on 3D run. No new controls.
- New centers remain unsigned; selected valid E/Z is consumed, unselected
  geometry and distant physical parity retained. CIP is independently reassigned,
  including a test where physical retention changes S to R. 3D is not a ratio.
- Graph-equivalent multi-site duplicates are grouped only after full chirality-
  aware automorphism proof; independent sites/regio products remain selectable.
- Fixed 347-case audit: hydrohalogenation 8/16 (50.0%) → 12/16 (75.0%). A051,
  A052/A053, A054 and A057 gain support; A059 1,7-octadiene is newly excluded for
  short pi-capture/cyclization risk, not claimed chemically impossible. All 330
  other rows are identical; no incorrect audit chemistry appeared.
- All 1,195 tests pass (594 Python + 601 JS), 144 new; all 1,051 original methods
  retained. Three old HX-scope assertions intentionally updated, none removed.
  Six authenticated HTTP tests, 72 independent arithmetic fixtures, exact 2D/3D
  maps, 3D distant-center CIP and prior 192-match/125-option diagnostics pass.
- TypeScript, production build and whitespace pass; previous bundle warnings
  remain. HTML/CSS, Calculators, curated data, benchmark and unrelated rules
  unchanged. Browser verifies HBr product/linking and radical reset/rejection.
- Report: docs/reaction-lab-hydrohalogenation-phase3b.md; results JSON and preview.
  Local preview refreshed; no push/deployment/publication. Net visualization only:
  full ionic HX mechanism is not advertised as implemented. Stop after Phase 3B;
  recommend separately validated existing alkene halogenation next.

## 2026-10-14 — Phase 3C: site-compatible alkene bromination

- Added Br2-specific compatibility and local anti-stereo utilities. Selected C=C,
  actual Br–Br, four exact bond edits, reagent maps, unchanged bonds/stereo,
  charge/atom conservation and one-to-one stoichiometry are validated.
- E/Z and bounded small-ring geometry determine opposite-face structures without
  random conformer predictions. E-2-butene meso, Z-2-butene R,R/S,S and small-ring
  trans Br/Br expectations independently pass. Unknown internal geometry stays
  unsigned. Distant physical stereo/CIP retained; no ratios or generic trans claim.
- Separate R/S options and source labels use the existing UI. Equivalent meso/
  symmetric site representations are grouped; distinct sites/alternatives remain.
- Screened remote OH/ethers and terminal styrenes supported. Nearby O/pi capture,
  activated groups, conjugation and unvalidated rings/benzylic stereo fail closed.
  HBr/HI or chlorination permissions were not imported or expanded.
- Neutral non-nucleophilic Br2 model distinguished from water/alcohol capture,
  unknown aprotic solvents, extra activation/heat and radical substitution.
  Conditional 2D remains inspectable where appropriate; blocked runs return 422.
- Fixed audit: bromination 6/14 (42.9%) → 9/14 (64.3%). E/Z, styrene and remote
  stereo gain support; A029 1,7-octadiene newly excluded for competing capture.
  A020 remains partial because original benchmark lacks independent stereo
  expectations, although new ring stereo tests pass. All 331 other rows identical.
- 1,299 tests pass (652 Python + 647 JS), 104 new. All 1,195 original methods
  retained; eight old bromination expectations intentionally updated, none deleted.
  Five authenticated HTTP tests, 42 amount fixtures, actual 3D map/CIP checks and
  prior 192-match/125-option four-pathway diagnostics pass.
- TypeScript/build/whitespace pass; existing bundle warnings remain. Layout,
  Calculators, curated data, benchmark and unrelated rules/validators unchanged.
  Browser verifies R/S cards, medium gate/reset, wedges and Br11 linked 2D/3D.
- Report: docs/reaction-lab-bromination-phase3c.md; results JSON and screenshot.
  Net visualization only; full bromonium mechanism remains unsupported. Local
  preview refreshed; no push/deployment/publication. Stop after bromination;
  recommend separately validated existing chlorination next, not started.

## 2026-10-14 — Phase 3D: site-compatible alkene chlorination

- Added Cl2-specific compatibility, exact neutral Cl–Cl provenance and four net
  edits through existing strict validation. Reused only element-independent
  mapped anti-reference/parity helpers; bromination rule/stereo remain unchanged.
- E/Z-dependent meso/enantiomer alternatives, bounded cyclic trans Cl/Cl, distant
  physical configurations/CIP and unselected E/Z are independently checked.
  Unknown internal geometry remains unsigned; no generic anti=trans claim.
- Terminal styrenes, distant stereo and widely separated sites now work. Remote
  OH/ether compatibility is not independently established for Cl2 and fails
  closed; nearby O/pi capture, internal aryl sites and unvalidated groups remain
  excluded. 1,7-octadiene newly rejected for unresolved cyclization risk.
- Dedicated neutral non-nucleophilic conditions distinguish water/alcohol
  capture, unknown medium, added activation/heat and radical pathways. Qualified
  2D remains inspectable where appropriate; unsupported runs return 422 and
  condition changes clear stale products. No layout/control/Calculator changes.
- Fixed 347-case audit: chlorination 6/14 (42.9%) -> 9/14 (64.3%). E/Z-3-hexene,
  styrene and distant-chiral case gain support, minus 1,7-octadiene restriction.
  Cycloheptene remains partial under unchanged benchmark stereo scoring, despite
  separate verified cyclic tests. All 332 non-chlorination rows identical.
- 1,405 tests pass (720 Python + 685 JS), 106 new. All 1,299 original tests remain;
  only two old Cl2 expectation methods updated. Eight authenticated HTTP tests,
  34 amount fixtures, exact 2D/3D maps/configurations and prior 192-match/125-option
  four-pathway diagnostics pass. Br differential: 45 match contexts and 46 full
  diagram payloads have identical before/after hashes.
- TypeScript/build/whitespace pass; previous bundle warnings remain. Layout,
  curated data, benchmark, Calculators and unrelated rules/validators unchanged.
  Browser verified chlorine linking, R/S options and water reset/3D gate. Local
  preview refreshed; no commit, push or publication.
- Report: docs/reaction-lab-chlorination-phase3d.md; results JSON and JPG preview.
  Net visualization only; full chloronium mechanism not claimed. Stop after 3D;
  recommend a separately requested existing epoxidation review, not started.

## 2026-10-14 — Phase 3E: site-compatible peroxyacid epoxidation

- Expanded existing epoxidation using its own site/group/reagent policy. Added
  same-face geometry from mapped alkene references; no halogen anti permissions
  imported. Remote screened OH/ethers, aryl-adjacent alkenes, distant stereo and
  isolated multiple sites supported. Common peroxyacids and mCPBA retained.
- Corrected formal concerted acid atom roles: terminal O enters the epoxide,
  original carbonyl O accepts peracid H, proximal O becomes acid C=O. Eight exact
  edits and both fragments pass unchanged strict conservation/stereo validation.
- One concerted mechanism step with four formal electron-pair moves; explicit
  proton transfer, no invented stable intermediate or computed timing/energies.
  Existing mechanism panel and 2D/3D correspondence reused without layout changes.
- Independently verified E/trans and Z/cis epoxides, meso/enantiomer alternatives,
  cyclic cis-fused structures and distant physical retention/CIP reassignment.
  Unknown geometry stays unsigned; no face/site ratios or experimental yields.
- Nearby oxygen/directing/opening risks, acid-labile/competing groups and unusual
  ring environments remain excluded. Cyclooctene/exocyclic/fused selected sites
  and competing peracid substituents newly fail closed. A narrow raw peracid
  stereo guard prevents silent normalization loss. These are model limits, not
  claims those structures cannot react.
- Fixed 347-case audit: 5/11 (45.5%) -> 9/11 (81.8%); styrene, E/Z and distant
  stereo gain support. Cyclic row remains partial under unchanged scoring;
  nearby OH remains unsupported. All 334 non-epoxidation rows identical. Isolated
  1,7-octadiene remains supported; equivalent-site identities independently tested.
- 1,572 tests pass (799 Python + 773 JS), 167 new. All 1,405 originals remain;
  nine epoxidation expectation methods intentionally updated, none removed.
  Nine HTTP tests, 84 amount fixtures and strict tampering checks pass. Before/
  after Br2/Cl2/water/HBr comparison: 120 matches, 104 diagrams, identical hash.
  Earlier 192-match/125-option SN/E diagnostic passes with no failures.
- TypeScript/build/whitespace pass; previous third-party/bundle warnings remain.
  Layout, frontend, Calculators, curated data, benchmark and unrelated rule/
  validator files unchanged. Browser verified O14 linking, concerted controls and
  water gating. Local preview refreshed; no commit, push or publication.
- Report: docs/reaction-lab-epoxidation-phase3e.md; results JSON and JPG preview.
  Stop after 3E. Recommend separately requested existing dihydroxylation review;
  not started.

## 2026-10-15 — Phase 3F: alkene dihydroxylation only

- Replaced the old hydrocarbon/unsigned diol gate with a dedicated Os/H2O2
  selected-site compatibility policy and strict four-change mapped net contract.
  Screened remote OH/ethers, styrene, E/Z, isolated 5–7-membered rings, distant
  specified centers and separated reaction sites now have validated net scope.
- Verified syn E-2-butene RR/SS, Z-2-butene meso RS, unequal E/Z alternatives,
  cis cyclic diols, retained physical configurations and independently changed
  CIP descriptors. Unknown internal geometry stays unsigned; no facial ratios.
- Kept H2O2 as formal net O/H inventory, not elementary catalyst/proton
  provenance. No mapped osmium cycle, osmate/workup mechanism, NMO, KMnO4,
  cleavage or new reagent family. Exact explicit-species conservation retained.
- Added a small conditional workup assumption selector inside the existing
  pathway settings. Unconfirmed release or missing Os activation blocks 3D/run
  but keeps conditional 2D. It does not certify a full experimental protocol.
- Fixed benchmark untouched: original 4/11 full -> strict 0/11 full, ten partial,
  one unsupported positive (NMO). The unchanged inputs omit required workup
  confirmation; this downgrade is intentional and explicitly reported.
  Structural matches rise from 5/11 to 10/11. Separate confirmed-workup replay:
  9/11 full, cyclic case still partial under the fixed stereo-scoring criterion.
  All 335 unrelated rows identical. Exclusive totals reconcile: 179 full +
  25 partial + 105 unsupported + 38 correctly rejected = 347. Variant summaries
  are nested subsets; 309 positive expectations exclude 38 negative controls
  only from full-support denominators, not from the fixed total.
- 1,704 tests pass: 884 Python + 820 JS, 132 new (77 chemistry, eight HTTP,
  42 public calculator fixtures, five UI checks). All original methods remain;
  obsolete unsigned/E/Z expectations and setting mocks intentionally updated.
  Existing 192-match/125-option SN/E diagnostic has no failures. TypeScript,
  production build and whitespace checks pass; prior bundling warnings remain.
- Browser verified O10 linking through peroxide, diol 2D and 3D. Clearing
  workup removes the prior model. Temporary tab closed; local preview running.
  Overall layout, Calculators, curated molecule collection and other pathways
  preserved. No commit, push, deployment or publication.
- Report: docs/reaction-lab-dihydroxylation-phase3f.md; full fixed-audit/results
  JSON and linked-oxygen JPG proof alongside it. Stop after 3F; a separate
  addition-family consistency review is recommended but has not started.

## 2026-10-15 — Phase 3H: addition-family consistency fixes only

- Implemented the five Phase 3G priorities: separate condition evidence/output
  permissions, explicit diol solvent uncertainty, visible transferable calculator
  assumptions, accurate net/mechanism labels, and grouped hydration choices.
- New versioned grouped option view preserves every legacy mapped site ID.
  Equivalent hydration sites appear once; site/face alternatives are not counted
  as different mechanisms. No chemistry scope or 3D/workup gate was relaxed.
- Added a separate 48-case/66-option diagnostic with independent stereo, mapping,
  provenance and site checks. Conditional 2D success is distinct from blocked 3D.
- All 1,704 original tests untouched; 96 new checks give 1,800 passing tests
  (953 Python + 847 JS). TypeScript, build and whitespace pass. Existing public
  192-match/125-option diagnostic also passes. No layout/CSS or curated examples
  changed; no new reactions or reagent families.
- Fixed 347-case benchmark and every result row unchanged. Diol strict 0/11;
  separate confirmed-workup replay 9/11. Never substituted the replay score.
- Report: docs/reaction-lab-addition-phase3h.md; machine results and PNG proof.
  Local preview refreshed. No commit, push, deployment or publication. Stop here.

## 2026-10-15 — Phase 4A: existing Lindlar alkyne partial hydrogenation

- Added a dedicated shared-compatibility consumer for isolated acyclic terminal
  and internal alkynes, screened remote OH/ethers, distant configurations and
  independent well-separated C≡C sites. Internal products have validated net
  cis/Z geometry; terminal products have no invented E/Z. Actual H2 maps and
  exact spectator bond/configuration retention are checked through serialization.
- Grouped equivalent presentation choices preserve all addressable site IDs.
  Missing/incorrect selective activation retains conditional 2D but blocks 3D;
  solvent/pressure/stopping and over-reduction remain explicitly unvalidated.
  Visible Calculator context retained; arithmetic unchanged; no surface mechanism.
- Fixed benchmark untouched: partial reduction 4/10 (40%) → 8/10 (80%). Four
  newly supported target rows; all 336 unrelated product/status/workflow results
  unchanged, five pair-wide notes-only corrections documented. Six-addition
  diagnostic is exactly unchanged. No new families or curated examples.
- Added 145 tests (93 Python, 52 JS): 1,945 pass (1,046 Python + 899 JS).
  One obsolete internal-alkyne negative expectation strengthened to require cis/Z
  plus missing-catalyst blocking; other original tests/fixtures unchanged.
  Separate 52-case/33-option diagnostic, authenticated public workflow, 2D/3D,
  independent CIP/coordinate checks and calculators pass. TypeScript/build and
  whitespace pass. No layout/CSS, container config or other reaction-rule changes.
- Report: docs/reaction-lab-alkyne-partial-hydrogenation-phase4a.md; machine JSON
  and linked cis-alkene preview saved. Local preview refreshed. No commit, push,
  deployment or publication. Phase 4A complete; no next pathway started.

## 2026-10-15 — Phase 4B: complete alkyne hydrogenation only

- Added a dedicated active-metal full-reduction compatibility consumer: selected
  C≡C → C–C, two actual H2/four mapped H, screened remote saturated OH/ethers and
  distant physical stereo retention. No E/Z or new local centers; no invented
  catalyst surface/ionic/radical mechanism or experimental completion.
- Existing Pd/Pt selector required; Lindlar remains partial-only. Missing or
  incompatible settings retain conditional 2D, not a full 3D outcome. Exact H2
  supply/pressure and protocol remain unknown. Calculator caveats carry context;
  all arithmetic unchanged. Other unsaturations are not assumed inert.
- Equivalent multi-alkyne site choices group with addressable original IDs.
  Selected-site equations remain 2D bookkeeping only: unresolved competing
  reduction blocks selective 3D; no all-sites product is invented.
- Fixed 347-case benchmark unchanged: full reduction 6/10 (60%) → 7/10 (70%).
  A262/A264 newly full; A265 deliberately full → partial for the selective 3D
  safeguard. All 336 unrelated product/status/workflow results unchanged; three
  pair-wide notes-only corrections documented. Partial stays 8/10, with its
  rule/tests untouched and diagnostic identical except pair-wide reasons.
- All 1,945 original tests unchanged; 149 new tests (94 Python/55 JS) give
  2,094 passing (1,140 Python + 954 JS). Six authenticated public tests, separate
  52-case/32-option diagnostic, exact 2D/3D/stereo/provenance and calculators pass.
  Six-addition diagnostic exactly unchanged. TypeScript/build/whitespace pass.
- No layout/CSS, curated examples, other chemistry-rule modules, shared stereo
  validators, Calculator arithmetic or container/build configuration changed.
  Report: docs/reaction-lab-alkyne-complete-hydrogenation-phase4b.md; machine JSON
  and two-H2/linked-OH browser proof saved. Preview refreshed; no commit, push or
  publication. Phase 4B complete; next alkyne halogenation review not started.

## 2026-10-15 — Phase 4C: existing alkyne halogenation only

- Verified both Br2/Cl2 and one/two-equivalent modes pre-existed. Added a
  dedicated site policy, exact actual-X2 edit/provenance contract, screened
  remote saturated O groups and distant physical stereo retention. First-stage
  Br anti geometry is CIP-checked only under explicit compatible-medium net
  settings; incomplete conditions remain unsigned. Cl first-stage E/Z remains
  unsigned/2D-only; no blanket Br stereospecificity permission is inherited.
- Two equivalents give the saturated 1,1,2,2-tetrahalide; no H is added or lost.
  Nearby capture rings, complex rings, conjugation and competing groups remain
  restricted. Equivalent multi-alkyne options group with original mapped IDs;
  all selective one-site multi-alkyne 3D claims are blocked, 2D retained.
- Conditions/evidence and calculator caveats distinguish exact theoretical
  equivalents from actual supply, stopping or complete conversion. Missing
  medium/stage, capture media, radical/extra activation and forcing settings
  cannot assert a 3D endpoint. No complete halonium mechanism is invented.
- Fixed 347-case benchmark unchanged: structural matches 13/21 → 15/21, but
  full-workflow score deliberately 6/21 → 0/21 because every fixed X2 input
  omits the newly enforced compatible-medium setting. A286/A297 gain net
  support; A289–A293/A298 full → partial. First-stage hard-coded unsigned
  scoring remains untouched. Separate dry-medium companion: 12 qualified,
  three conditional-only, six unsupported positives; not a replacement score.
- All 324 unrelated benchmark rows entirely identical. Complete/partial alkyne
  hydrogenation and six-addition diagnostics exactly unchanged. New independent
  X2 diagnostic: 177 cases, 85 diagrams, 44 verified runs, 41 correct gates,
  no failures. Original rules, tests, fixtures, layout, curated data and
  Calculator arithmetic preserved; no prior expectation edited.
- Added 276 tests (115 Python/161 JS): all 2,370 pass (1,255 Python/1,115 JS),
  including all 2,094 originals and seven authenticated public workflow tests.
  Independent physical parity/CIP/coordinate representation, exact 2D/3D links,
  calculations, TypeScript, production build and whitespace pass.
- Browser proof: existing propyne example, linked Br8 and correct two-X2
  limiting amount; changing to Cl first stage clears results and blocks 3D.
  Report, machine comparison/hashes and preview saved in docs. No commit,
  publication or layout change. Phase 4C complete; Phase 4D not started.

## 2026-10-16 — Phase 4D: existing alkyne hydrohalogenation only

- Replaced the legacy whole-substrate HX restriction with a dedicated site
  compatibility consumer. Existing HCl/HBr/HI and one/two-equivalent modes
  retain actual H/X provenance, strict bond edits, atom/charge conservation
  and distant physical configuration with independent CIP reassignment.
- Terminal Markovnikov products, symmetric choices and both unsymmetric
  internal orientations are validated. First-stage internal E/Z remains
  unsigned/2D-only; saturated geminal products have no residual E/Z. Screened
  remote oxygen and multiple alkyne sites retain conditional 2D equations,
  not claims of inert spectators or experimental one-site selectivity.
- Reagent-specific conditions gate 3D independently: HBr bounded endpoints,
  terminal one-HI only, HCl/two-HI conditional-only. Explicit stage, dry
  compatible-medium assumption and ambient settings are required; capture,
  radical, extra activation and unknown conditions cannot reuse permissions.
  No complete vinyl-cation/alkene mechanism or radical products are invented.
- Fixed 347-case audit unchanged: HX structural matches 11/21 -> 15/21;
  strict full workflow 10/21 -> 0/21 because fixed inputs omit required medium
  and temperature. Separate entered-condition replay: 11 qualified cases,
  four conditional-only, six unsupported. A304 has a frozen shifted-double-
  bond expectation defect; literal Incorrect-result status disclosed, not
  rescored. Engine retains the original selected bond and correct products.
- All 324 unrelated audit rows entirely identical, including A322 outside the
  23-row HX bucket. Partial/complete hydrogenation, X2 and six alkene-addition
  diagnostic vectors exactly unchanged. New HX diagnostic: 291 cases,
  153 diagrams, 31 verified runs, 122 correct 3D gates, zero failures.
- Added 459 tests (161 Python/298 JS): 2,829 pass (1,416 Python/1,413 JS),
  including seven authenticated route tests. All 2,370 old tests retained;
  one obsolete blanket internal-alkyne rejection expectation transparently
  updated to verify both correct orientations and incomplete-condition gate.
  TypeScript/build/whitespace pass; existing large-chunk warnings remain.
- Browser checked existing propyne example, linked Br8, two-HX limiting
  calculation, stale-result clearing and radical 2D-only gate. Report,
  machine evidence/hashes and screenshot saved in docs. Layout, examples,
  Calculator arithmetic and other reaction modules unchanged. No commit,
  publication or subsequent combined review. Phase 4D complete; stop here.
