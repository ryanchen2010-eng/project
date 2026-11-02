# Product names and condition prompts — local increment, 2026-10-20

## Implemented

### Generated names

`server/product_naming.py` provides local, display-only structural names for a bounded set of unbranched C1–C10 molecules: alkanes, one C=C or C≡C, simple alcohols/diols, aldehydes/ketones, terminal carboxylic acids and supported halogen substitution. Examples verified independently include Pentan-1-ol, Pent-1-ene, Pentan-2-one, Pentanal and Pentanoic acid.

- Existing exact-identity/catalog names take precedence.
- Already specified R/S and E/Z are independently recalculated after removing atom maps from a copied graph. No conformation is used to invent stereochemistry. Propene bromination alternatives now have distinct `(2R)-1,2-dibromopropane` and `(2S)-1,2-dibromopropane` labels.
- Branching, rings, aromaticity, isotopes, ions, enhanced/exotic stereo and unimplemented combinations return no guessed systematic name. The reaction retains its class label; Reaction Lab options show the exact isomeric SMILES as a wrapping structural identifier.
- The existing explicitly qualified **Partially hydrogenated product** label is retained; its SMILES distinguishes the structure without discarding the partial-conversion qualification.
- Main-product names propagate from the generated reaction through equations, mapped diagrams, 3D responses and calculator product labels. Eligible simple coproducts receive the same bounded naming treatment.
- No network naming lookup, formula-based identity substitution or new naming dependency was added.

Naming references: [IUPAC Blue Book P-1](https://iupac.qmul.ac.uk/BlueBook/P1.html) and [P-9 stereochemical descriptors](https://iupac.qmul.ac.uk/BlueBook/P9.html). This implementation is deliberately not an unrestricted IUPAC/PIN naming engine.

### Condition prompts

- The existing Guided conditions panel now shows a short, visible checklist of missing choices and proposed replacements before the collapsed review details.
- The next action is explicit: open **Review supported settings**, review, and apply. Nothing is automatically applied; existing replacement confirmation and backend revalidation are unchanged.
- Reaction options show friendly missing-field names and explain that options refresh automatically.
- Missing comparison information is distinguished from chemically required activation. Unimplemented selective-aldehyde profiles explicitly state that changing dropdowns cannot enable 3D.
- Non-applicable/qualified guides do not acquire misleading apply controls or checklists.
- Complex structural identifiers and all new wording use `textContent`, not injected HTML. Long SMILES wrap inside existing cards.

No page redesign, new reaction family, relaxed condition gate, new reagent model, changed selectivity, atom-map edits or calculator arithmetic changes.

## Verification

- Python: **1,895 passed** (234.548 seconds); naming tests also rerun against the final helper.
- JavaScript: **1,888 passed** (29.368 seconds).
- Combined: **3,783 passed**, including **17 new tests** (10 Python and 7 JavaScript) plus the preserved 3,766-test baseline.
- TypeScript + Vite production build: **passed** (29.00 seconds); existing dependency directives and bundle-size warnings remain.
- Whitespace: **passed**.
- Fixed 347-case audit: **zero changed classifications** versus the beta baseline. Totals remain 155 Fully supported, 63 Partially supported, 90 Unsupported, 38 Correctly rejected and 1 pre-existing Incorrect result. The latter was not introduced or addressed in this display-only increment. Benchmark inputs/expectations were not edited.
- Public-workflow tests verify match/run/diagram/calculator name consistency, exact catalog-name precedence, stereochemical distinctions, map/identity/permission preservation and safe naming fallback.
- Local browser: PubChem-imported 1-bromopentane exposes **Pentan-1-ol** and **Pent-1-ene** options. SN2 generates the same correctly named 2D/3D structure. Secondary oxidation checklist stays visible, 3D remains blocked until explicit reviewed application, and the original bounded model becomes available after revalidation.
- Mobile: visible condition checklist at 320 × 800; document width remains 320. Temporary viewport reset afterward.

Evidence: `product-names-preview.png`, `product-condition-prompts-preview.png`, `product-condition-prompts-mobile.png`.

## Scope and preservation

Runtime changes versus the deployed dependency-patch snapshot are limited to:

- `server/reaction_engine.py`
- `src/reaction-conditions.ts`
- `src/guided-reaction-conditions.ts`
- `src/reaction-lab.ts`
- new `server/product_naming.py`

No other runtime files changed and none were removed. The two previously frozen release archives are unchanged. The original Git index hash is still `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`.

**Local only:** no commit, push, new release freeze or Render deployment was performed. The online beta continues to run the previously approved version. A separately reviewed update is required to publish this increment.
