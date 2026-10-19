# Molecule Playground

The local Home page at `/` introduces the four tools and their calculation
limits. Explorer is at `/explore.html`, Builder at `/builder.html`, and Reaction
Lab at `/reaction-lab.html`. The fifth page, Calculators, is at `/calculators.html`.

A small 3Dmol.js-powered app for exploring compounds. The Explorer starts with
20 featured compounds (six with fully reviewed teaching properties), then searches PubChem by full name or molecular formula
for more records, including ionic salts and metal compounds. Results with the
same formula appear as separate choices with their atom connections in bracketed
SMILES notation. The reviewed examples retain their explanations and properties;
other PubChem results show their source, formula, mass, and a 3D model when a
usable structure exists. Otherwise, they show PubChem's 2D depiction rather
than inventing 3D coordinates. Multi-part and formally charged results are
labelled separately; unreviewed properties are clearly labelled.

Explorer's description area also has sourced chemical-behaviour notes for all
20 featured compounds: flammability, reactivity, toxicity, acidity/basicity,
oxidation/corrosion, and heat of combustion. These are qualitative teaching
notes, not safety data sheets or numerical thermochemistry records. Longer
definitions open in an optional guide. Notes are selected by the exact PubChem
CID, never by formula, so isomers keep their own explanations. Unreviewed search
results retain their structure description and show an explicit unknown notice
with a PubChem reference instead of guessed chemical properties. Solution pH,
exposure-dependent toxicity, and compounds that are not ordinary fuels are
described in context rather than assigned misleading universal values.

The separate Molecule Builder at `/builder.html` uses Ketcher to draw a 2D
skeletal structure. Its structure check sends the exported Molfile to a local
RDKit service. RDKit checks the graph and valence. For eligible neutral,
connected covalent structures, it adds hydrogens, embeds a 3D conformer, and
minimizes it with MMFF94 or UFF; 3Dmol.js displays the result. Charged,
multi-part, metal, and other structures outside that geometry method remain
2D-only with an explanation instead of a misleading 3D model. The Builder
includes an ethanol example and Ketcher's periodic-table picker. Its drawing
is saved in the current browser tab and restored after visiting another page;
no new example drawings were added.

The separate Reaction Lab at `/reaction-lab.html` has two molecule inputs.
Type a listed compound name (case-insensitive) or formula (element capitals
matter), search PubChem beside either box for an unlisted molecule, or send a
valid Builder drawing to either box. A selected Explorer compound can also be
sent directly to either box. Both pages read the same
`src/shared-molecules.json` identities. A shared formula such as C2H6O asks the
user to choose ethanol [CCO] or dimethyl ether [COC] instead of silently
selecting one structure. Search terms go to PubChem; selected structures and
conditions are retained within the current browser tab.
The Lab now compares supported pathways with selected solvent, temperature,
and catalyst settings. Its filterable example library covers seven teaching
families: addition, elimination, substitution, oxidation, reduction,
condensation, and hydrolysis. Reviewed examples include ester hydrolysis,
2-propanol oxidation, acetone hydrogenation, alkene additions, and
esterification. Hydrogenation can be classified as both addition and reduction.
A collapsed Reaction guide on the Lab page briefly explains every supported
reaction type; longer interpretation and limits remain available on demand.
Selecting a pathway now opens a 2D reactants-to-products diagram, including
byproducts. Red highlights show broken bonds, blue shows formed bonds, and gold
shows bond-order changes. Lewis-style drawings have explicit C/H labels, formal
charges, and supported lone-pair dots, with thin bonds. The highlights use
atom-preserving graph edits verified against every expected product. All 17
current pathways and the supported drawn-structure rules are covered. Future
unsupported transformations show plain structures without guessed highlights.
These are net changes, not step-by-step curved-arrow mechanisms or stereochemical
predictions. Lone-pair dots represent electron counts, not their 3D orientation;
unsupported/aromatic electron assignments are omitted rather than guessed.
Choose **Compare** to see the 2D reaction beside the main product's 3D model.
Hover either view to highlight the exact same atom in both, including its mapped
reactant position. Click/tap to pin a selection, or focus a 2D atom and press
Enter/Space. **Clear atom** or Escape clears it. Byproduct-only atoms are clearly
labelled as outside the main-product 3D view. Atom IDs are preserved through
reaction edits and 3D embedding; incomplete correspondence disables linking.
3D is generated on request and retained when switching views. Detailed product
facts and conditions stay collapsed. On phones, Compare stacks the views and
the diagram scrolls internally without widening the page. Picking a 3D atom
reveals its 2D counterpart within that diagram, without moving the page.
A small structural-rule set also covers SN1, SN2, E1, and E2 on simple alkyl
halides.
Bromoethane + hydroxide shows SN2 and E2 as competing pathways;
2-chloro-2-methylpropane + water shows SN1 and E1. Water is treated as a
solvent rather than a consumed reactant in the E1 equation. Conditions are
teaching profiles, not predictions of rate, yield, or a unique mechanism.
The local RDKit service checks atom and charge balance, validates each
product structure, and generates its 3D coordinates. Chemistry source links and
limitations are shown for each option. An unlisted pair is unsupported,
not proven unreactive.
The hypochlorite oxidation is a simplified net equation, not a procedure;
actual mixtures and side reactions are not predicted.
Valid Builder drawings outside the named collection are also checked by
structure against the narrow alkyl-halide SN1/SN2/E1/E2 rules when paired with
listed hydroxide or water. For example, drawn 1-bromopropane + hydroxide shows
an SN2 alcohol and an E2 alkene option; their exact product SMILES is shown.
Small acyclic hydrocarbon drawings with one C=C bond (up to six carbons) are
also recognized without a preset name. Paired with listed hydrogen or bromine,
they offer hydrogenation or bromine addition respectively. For example, drawn
1-butene yields the butane or 1,2-dibromobutane connectivity. Propene is now
in the shared catalog and has the same supported addition pathways. These reactions
need the stated metal catalyst or dry medium; the preview does not assign
stereochemistry or predict yields. PubChem identifies searched reactants, not
reactions; the existing reviewed and structural rules decide what the Lab can
show. No PubChem naming lookup is used for generated products yet, so unlisted
products may have generic names alongside exact SMILES. Other valid searched
or drawn structures can still have no supported pathway. The rule set excludes
regioisomer choices, reaction stereochemistry, carbocation rearrangements, and
product ratios.

### Reaction calculator

After choosing a supported pathway, open **Reaction calculator** in the result
panel. **Amounts → yield** accepts g, mg, mol, or mmol for each consumed
reactant and shows the limiting reactant, main-product theoretical yield, and
remaining reactant amounts. **Target → amounts** calculates the stoichiometric
minimum needed for a selected product amount. A new pathway clears previous
amounts and results; the calculator does not require generating a 3D model.

The service supplies structure-derived molar masses and verified atom/charge
balance for all 17 current equations and the supported generated pathways.
Their current coefficients are all one; this is not a general equation
balancer. Water is excluded where it is only the E1 medium, and catalyst
quantities are not calculated. NaOH and other supported alkali hydroxides use
the full salt mass, not the mass of OH⁻. Values assume pure reagent amounts,
100% conversion into the selected pathway, and no product losses. They do not
predict actual yields, equilibrium conversion, reaction mixtures, solution
concentrations, or laboratory procedures. The method reference and assumptions
are available in a collapsed disclosure.

### 3D measurements

Explorer, Builder, and Reaction Lab share a compact **Measure 3D** disclosure
below each usable 3D model. Choose distance (2 atoms), angle (3 atoms, with the
second atom at the vertex), or signed torsion (4 atoms, around atoms 2–3).
Click atoms in order or open **Choose atoms by list** for keyboard selection.
Numbered highlights and dashed lines identify the selection; distances use Å
and angles use degrees. **Clear selection** removes it; **Off** restores normal
atom clicks. Reaction Lab's linked atom hover remains available.

These are measurements of the displayed conformer's coordinates, not experimental
values or averages over conformations. Any atom pair can be measured, so a
non-bonded selection is labelled rather than called a bond. Undefined angles
and torsions show a short error instead of a number. Changing the molecule,
drawing, or reaction clears old measurements. Ionic information-only results,
2D-only structures, and models with fewer than two atoms have no measurement
controls. Reaction Lab measures the main product only, not the reaction diagram
or byproducts.

### Solution calculator

Explorer's **Solution calculator** below compound information reuses the exact
selected compound's molar mass. Standalone calculations live on
**Calculators → Solutions**. Reaction Lab offers a compact **Use in Calculators**
shortcut under each resolved molecule, carrying its exact identity and saving
the reaction draft. It works without a supported reaction or a 3D model,
including ionic salts; ambiguous formulas require an explicit structure choice.

- **Find concentration:** enter pure solute amount and total solution volume.
- **Find solute mass:** enter target molarity and final solution volume.
- **Dilute a stock:** enter stock and target concentrations plus final volume
  to calculate the stock aliquot and dilution factor.

Amounts support g, mg, mol, and mmol; volumes support L, mL, and µL;
concentrations support mol/L, mmol/L, and µmol/L. Molar mass is editable and
required only for mass conversions. Exact compound identity controls automatic
mass reuse; a shared formula never substitutes one compound for another.
Missing values require manual mass entry, but mole inputs and dilution still
work. Changing the compound, mode, input, or unit clears outdated results.

These are local arithmetic calculations, not solvent choices, hazard checks,
or laboratory procedures. Final volume is the whole solution, not added solvent;
dilution does not assume additive volumes. The tool does not check solubility,
purity, hydrated forms, density, or temperature. Ionic-salt concentration counts
formula units. The collapsed method section cites the
[OpenStax molarity and dilution reference](https://openstax.org/books/chemistry-2e/pages/3-3-molarity).

### Calculator menu

**Calculators** is a separate page with six topics: moles/particles, solutions,
verified reaction amounts, one-reaction equilibrium, acids/bases/buffers, and
one-salt solubility. Desktop has a left topic menu; mobile has a compact topic
selector. Explorer's **Open in Calculators** transfers exact compound identity
and full molar mass to the mole and solution tools. Formula matches never choose
an isomer, ion, salt or hydrate on the user's behalf. Manual values remain possible.
Explorer and Reaction Lab keep their existing calculators.

Arithmetic runs browser-locally. Only the verified reaction catalog needs the
chemistry service. Advanced tools require entered constants (K or pK), including
Kw for pH. Temperature changes clear constants and activity coefficients; the
tools do not look them up or correct them automatically. Ideal and fixed entered
activity coefficients use a consistent 1 mol/L concentration standard state.
Missing coefficients, undefined expressions, unsupported models and failed
balances produce errors, not approximate-looking answers. These are practical
calculators, not a universal reaction predictor or a safety assessment.

See [calculator model limits and reference checks](docs/calculator-models.md).

## Agreed direction

- Five local pages: Home, Molecule Explorer, Molecule Builder, Reaction Lab, and Calculators.
- Use Wix Site 1 as the website shell.
- Keep 3Dmol.js for displaying 3D structures.
- The Builder uses Ketcher, a Python RDKit service, and 3Dmol.js.
- MolView integration is excluded from the plan (Ryan's decision, 2026-09-19).
- Start Reaction Lab with a small reviewed reaction library; expand it only
  after reviewing the examples and interface with users.

The Builder chemistry endpoint parses drawings of up to 80 atoms and rejects
invalid valence or unreadable structures. Its 3D method covers eligible neutral,
connected covalent structures using H, B, C, N, O, F, Si, P, S, Cl, Ge, As,
Se, Br, Sb, Te, or I when a supported force field succeeds. This produces one
candidate conformer, not proof of a global energy minimum or every electron
rule. Other parsed drawings can still be shown and transferred as 2D-only;
Reaction Lab supports only its own reviewed or structural reaction rules.
In those rules, LiOH, NaOH, KOH, RbOH, and CsOH can supply OH⁻ for a simplified
ionic equation, with the omitted counterion identified. This does not make
arbitrary salts or metal complexes valid reaction inputs.

The RDKit endpoint currently runs on this computer only, so deploying the
Builder and Reaction Lab on Wix requires a hosted chemistry service. PubChem
search in both Explorer and Reaction Lab, plus the Explorer's 3D/2D proxy,
also use that local service and need a hosted endpoint before they work on
Wix. Searches are capped at 20 distinct returned structures and are not an
exhaustive PubChem browser; formula searches exclude isotope variants and
disconnected neutral mixtures.

The latest local Explorer has not yet replaced the Wix Site 1 draft embed.
The preserved Wix embed is in
`history/snapshots/wix-site-1-explorer-2026-09-18.html`.

## Private Wix trial (deployment preparation)

The online trial is **not deployed yet**. Keep using Wix **My Site 1** only.
The website is embedded as one hosted app, preserving Home, Explorer, Builder,
Reaction Lab, internal navigation, and shared molecule transfers.

`Dockerfile` builds the locked frontend and packages it with RDKit and a separate
Flask/Gunicorn gateway. This is not the old loopback-only development server.
The gateway protects both the built website and every chemistry/PubChem API.
It fails closed without configured credentials and an HTTPS public origin.
Only a minimal `/healthz` and the login page are publicly accessible. Assets
are precompressed during the build to reduce the large Builder download.

The hosting account, costs, HTTPS URL, and online access checks still need to be
completed before replacing the Wix embed. Render's free tier is a proposed
trial option, not an account or service that has already been created.
See [private deployment instructions](docs/private-wix-trial.md).

Wix's page password alone does not protect the external app or API. Browser
restrictions on embedded sessions must be tested; do not remove authentication
to make an iframe load. If embedded login is blocked, use the protected app in
its own tab until the integration is resolved.

## Checks

```bash
node --test tests/*.test.mjs
.venv/bin/python -m unittest discover -s tests
pnpm build
```

For the private gateway's synthetic authentication and routing tests, install
the optional production dependencies in the project virtual environment first:

```bash
.venv/bin/python -m pip install -r server/requirements-production.txt
.venv/bin/python -m unittest discover -s tests -p 'test_production_app.py'
```

The Explorer description suite checks all 20 compound identities, all six
property categories, sourced references, exact-CID lookup, unknown-compound
fallback, safe text rendering, and replacement of stale descriptions.
The atom-inspector suite checks exact correspondence, bidirectional hover,
pin/clear, keyboard/touch handling, stale callback cancellation, and internal
scrolling. The diagram/API suites verify mapped atom identities, supported lone
pairs, charges, and the exact emitted 3D atom order across all existing pathways.
The baseline and entry suites check molecule file identities, formulas, bonds,
data fields, search behavior, case-sensitive formulas, ambiguous isomer lookup,
and PubChem-to-reactant selection.
The PubChem suite checks formula isomers, salt/metal records, exclusion of
isotope-labelled and disconnected neutral mixtures (including mixtures whose
individual fragments contain offsetting atom charges), name lookup, depiction
validation, and input bounds without network calls. A 22-compound cross-page
matrix checks PubChem-result parsing, Builder classification, and Reaction Lab
scope/balance together. The RDKit suite checks
ethanol's formula and 3D coordinates, 2D-only Builder limits, alkali hydroxide
handling, condition-aware pathway matches, balanced products, invalid valence,
and unsupported structures. See `history/cross-page-chemistry-audit-2026-09-25.md`
for the test matrix and `history/project-progress.md`
for completed work and remaining checks.

## Featured compounds

The six fully reviewed entries remain water, methane, carbon dioxide, ethanol,
glucose, and caffeine. The shared catalog adds oxygen, ammonia, hydrogen
peroxide, methanol, ethane, propene, acetone, ethanoic acid, dimethyl ether,
bromomethane, 2-propanol, ethyl ethanoate, sodium chloride, and sodium hydroxide.
The additional entries have verified identities, molar masses, and sourced
chemical-behaviour notes; other unreviewed physical/geometry properties remain
labelled as such. Sodium chloride and sodium hydroxide are ionic compounds;
Explorer uses a 2D depiction when a meaningful molecular 3D conformer is
unavailable. Appearance in Reaction Lab does not imply that a reaction rule
exists for every pair. The user still selects a supported pathway explicitly.

The bundled SDF structures are sourced from PubChem's PUG REST service using
the compound identifiers documented in `src/shared-molecules.json` and the download
script below.

## Run locally

After the first-time setup below, open `start-local.command` in Finder or run
`./start-local.command` from this folder. It starts both local services and
opens Home in your default browser. Keep its Terminal window open while using
the site; press Control-C to stop both services. If the services are already
running, the launcher simply opens the site. It will not replace an unrelated
process using either port.

First-time setup, if `.venv` or `node_modules` is missing:

```bash
pnpm install
python3 -m venv .venv
.venv/bin/python -m pip install -r server/requirements.txt
```

Run `./start-local.command`, then use `http://127.0.0.1:5173/` for Home,
`http://127.0.0.1:5173/explore.html` for Explorer,
`http://127.0.0.1:5173/builder.html` for Builder, or
`http://127.0.0.1:5173/reaction-lab.html` for Reaction Lab. The launcher uses
Node from the terminal PATH or, on this Mac, Codex's bundled Node runtime.

Do not open the HTML files directly from Finder: the tools' JavaScript modules,
3Dmol.js, and bundled molecule files must be served over HTTP.

## Refresh molecule structures

```bash
mkdir -p public/molecules
curl -L --fail -o public/molecules/water.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/SDF?record_type=3d'
curl -L --fail -o public/molecules/methane.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/297/SDF?record_type=3d'
curl -L --fail -o public/molecules/carbon-dioxide.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/280/SDF?record_type=3d'
curl -L --fail -o public/molecules/ethanol.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/702/SDF?record_type=3d'
curl -L --fail -o public/molecules/glucose.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/5793/SDF?record_type=3d'
curl -L --fail -o public/molecules/caffeine.sdf 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2519/SDF?record_type=3d'
```

3Dmol.js is loaded from its hosted browser script and integrated through its
`createViewer` API. The same viewer can be embedded in Wix using an HTML
embed and a public GitHub/jsDelivr SDF URL.

## Public jsDelivr molecule URLs

- [Water](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/water.sdf)
- [Methane](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/methane.sdf)
- [Carbon dioxide](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/carbon-dioxide.sdf)
- [Ethanol](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/ethanol.sdf)
- [Glucose](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/glucose.sdf)
- [Caffeine](https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/caffeine.sdf)

Use one of those URLs in a Wix HTML embed. This starter snippet loads water:

```html
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
<div id="molecule-viewer" style="height:420px; width:100%;"></div>
<script>
  const viewer = $3Dmol.createViewer("molecule-viewer", { backgroundColor: "#f5f3ee" });
  fetch("https://cdn.jsdelivr.net/gh/ryanchen2010-eng/capstone-project@main/public/molecules/water.sdf")
    .then((response) => response.text())
    .then((sdf) => {
      viewer.addModel(sdf, "sdf");
      viewer.setStyle({}, { stick: { colorscheme: "Jmol" }, sphere: { scale: 0.25 } });
      viewer.zoomTo();
      viewer.render();
    });
</script>
```
