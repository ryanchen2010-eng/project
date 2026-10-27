# Reaction Lab — Ester Phase 1 completion report

Completed locally on October 9, 2026. Only the existing **Ester hydrolysis** and
**Ester saponification** pathways were expanded. No new reaction family, page
layout redesign, publication, or Phase 2 work was performed.

## 1. Changes implemented

- The ester detector now recognizes O–aryl carboxylic esters as well as ordinary
  O–alkyl esters, with explicit single-bond and oxygen-connectivity checks.
  Carbonates, anhydrides, amides, ethers and enol esters do not become false
  carboxylic-ester matches.
- Both public pathways use a shared, selected-site scope validator. Lactone
  opening is limited to **isolated, saturated five- and six-membered rings**
  containing one ring oxygen. Ring substitution is permitted within the existing
  C/H/O substrate scope; fused, bridged, spiro and other unvalidated topologies
  are not enabled.
- Existing mapped acyl–O edits now reach the public matcher for validated
  lactones and carbocyclic aryl esters. Their topology is checked again during
  transformation rather than trusting the initial detector.
- New product postconditions require exactly the intended two broken and two
  formed bonds, the proton supplied by the actual reagent, unchanged unselected
  bonds, correct carbonyl and alkoxy connectivity, correct acid/carboxylate
  protonation, and the correct number of product components. Existing valence,
  element, isotope, unique-map, total-charge, radical and size checks remain.
- Hydrolysis uses the aqueous-acid pathway and reports neutral acid. Base
  hydrolysis consumes one OH⁻ equivalent per chosen site and reports carboxylate.
  A lactone yields **one connected hydroxy acid or hydroxy carboxylate**, not two
  invented fragments. An ordinary aryl ester gives acid/carboxylate plus phenol.
- Saponification does not include acid work-up. Choosing an acid catalyst while
  hydroxide is the reactant flags unaligned/unevaluated conditions and does not
  protonate the product. Excess-base deprotonation of phenol or other OH groups
  is not inferred. The separation between saponification and subsequent acid
  work-up follows the [ester chemistry reference](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters).
- Specified tetrahedral and alkene configurations are retained only when their
  mapped neighbor correspondence and physical parity pass validation, including
  coproducts and mapped-SMILES serialization. CIP letters are recomputed rather
  than blindly copied. New assignments, loss or inversion fail closed.
- Enhanced/relative stereo groups and unsupported non-tetrahedral or ambiguous
  bond stereo are rejected before input canonicalization can erase them.
- Phenol is named correctly. Existing guide, information and diagram summaries
  now distinguish connected lactone opening and phenolic coproducts. The overall
  layout and example collection remain unchanged.

## 2. Previously unsupported examples that now work

| Input | Acid hydrolysis | Basic saponification |
| --- | --- | --- |
| γ-Butyrolactone | 4-Hydroxybutanoic acid, one connected product | 4-Hydroxybutanoate, charge −1, one connected product |
| δ-Valerolactone | 5-Hydroxypentanoic acid | 5-Hydroxypentanoate, charge −1 |
| Supported methyl-substituted γ-lactones | Corresponding connected hydroxy acids | Corresponding connected hydroxy carboxylates |
| Phenyl acetate | Ethanoic acid + phenol | Ethanoate + phenol |
| Tested cresyl/methoxyphenyl/naphthyl esters and phenyl benzoate | Actual acid + corresponding phenol | Actual carboxylate + corresponding phenol |
| Tested esters with specified, unchanged tetrahedral centers or C=C geometry | Mapped configurations retained in actual acid/alcohol products | Mapped configurations retained in actual carboxylate/alcohol products |

The inputs are identified by their structures, not by membership in a preset
list. Existing branched, cyclic-alkoxy and aromatic-acyl cases remain working.
Asymmetric diesters and di-aryl esters produce independently selectable,
**one-site** options; the unselected ester remains intact. This is not automatic
complete hydrolysis of every ester group.

## 3. Structural cases still unsupported

- Smaller/strained rings, lactone rings of seven or more members, and fused,
  bridged, spiro, unsaturated or additional-heteroatom lactone ring paths.
- Heteroaryl and enol ester extensions, enhanced/relative stereo, non-tetrahedral
  stereo, and cases in which mapped configuration cannot be retained and checked.
- Substrates outside the existing neutral, closed-shell, non-isotopic C/H/O
  oxygen-chemistry scope, including the audit's remote-amine ester. Existing
  general small-ring and product size limits also remain.
- Separate acid work-up, excess-base protonation-state modeling, full elementary
  ester mechanisms, equilibrium composition, competing pathways, epimerization,
  reaction rates, practical yields and isolated stereochemical outcomes.

These are implementation boundaries, not statements that the excluded real
molecules cannot undergo hydrolysis. Acid–amine amidation remains untouched.

Charged carboxylates remain intentionally 2D-only. Neutral supported acids are
eligible for the existing validated 3D generator. The net 2D drawing does not
render a full stereochemical mechanism; specified configurations remain in the
structural identities and information data. A 3D conformer of an unspecified
stereostructure is a representative shape, not a predicted stereochemical outcome.

## 4. Unexpected chemistry results

No incorrect connectivity, coproduct, net charge, atom-mapping or balance results
were found in the final regression checks or completeness matrix. All previews
and runs in the matrix completed without exceptions.

A retention test deliberately changes the CIP label from R to S because
hydrolysis changes the relative priorities of two ester-containing side chains.
The mapped physical configuration remains unchanged; this is **not inversion**.
Another check distinguishes interpretation of an unspecified 3D conformer from
an assigned stereochemical product; the authoritative net product remains
unassigned. Neither observation was hidden by relaxing validation.

## 5. Audit comparison against the preserved baseline

The original 347-case matrix, input structures, conditions, independent
expectations and scoring definitions were retained. Only supplementary wording
and source-hash coverage in the runner were updated. The baseline report and
baseline JSON were not overwritten.

| Pathway | Baseline fully supported | Phase 1 fully supported | Change |
| --- | --- | --- | --- |
| Ester hydrolysis | 6/10 — 60.0% | 9/10 — 90.0% | +30.0 percentage points |
| Ester saponification | 7/11 — 63.6% | 10/11 — 90.9% | +27.3 percentage points |

Exactly six case statuses changed, all Unsupported → Fully supported:

- A136/A147: phenyl acetate, acid/base respectively.
- A137/A148: γ-butyrolactone, acid/base respectively.
- A139/A150: ester with a remote specified stereocenter, acid/base respectively.

Both remaining positive ester failures are the remote-amine input. All 324 rows
outside these two pathways have unchanged coverage status. All 38 negative
controls still pass. Across the whole matrix, fully supported positives rose
from 146 to 152 of 309; partial remains 16 and unsupported fell from 147 to 141.
There are zero incorrect-result rows and zero preview failures. The rerun checks
203 generated options through match → diagram → run, including exact main-product
2D/3D atom correspondence wherever 3D is eligible.

These percentages describe this bounded matrix, not universal chemistry coverage,
experimental success probabilities, or complete mechanism support.

- Baseline: [audit report](reaction-lab-completeness-audit.md) and
  [baseline JSON](reaction-lab-completeness-audit-results.json).
- Rerun: [Phase 1 JSON](reaction-lab-ester-phase1-results.json), including the
  production source hashes and each unchanged matrix case's outcome.

## 6. Regression, production and public-workflow verification

**All 586 tests pass: 210 Python + 376 JavaScript.** This includes 16 new Python
tests and 16 new JavaScript tests, with numerous molecular and input-order
subcases. The two old blanket lactone-rejection fixtures were replaced by still
unsupported larger-ring controls; all other assertions remain enforced. The
existing information-capability expectation was updated for validated ester
stereo retention only.

New tests cover lactones, aryl esters, branched esters, diesters, false ester
groups, scope boundaries, incorrect reagent/structure controls, absolute stereo
retention and CIP changes, unsupported stereo input, corrupted configuration,
unselected-bond mutations, failed validation, atom/charge conservation, real
authenticated production HTTP match/diagram/run routes, 3D eligibility and exact
atom links, full NaOH/KOH masses and reversed input order.

The actual browser reaction calculator consumes public ester match metadata in
JavaScript tests for limiting reactants, theoretical yield and required amounts.
The selected full-salt mass is used, never just the hydroxide fragment's mass.

The production build passes (`tsc` followed by `vite build`, the package build
script's exact commands). Existing dependency `use client` and large-chunk
warnings remain; they are not Phase 1 build failures. `git diff --check` passes.

Browser verification used an isolated tab and the public **Search PubChem**
controls to find γ-butyrolactone and phenyl acetate, select acid/base pathways,
inspect equations and 2D products, generate neutral 3D products, and verify linked
atom selection. Charged lactone products correctly report no neutral 3D model.
The real calculator also verified 86.09 g lactone + 19.9985 g NaOH: NaOH limiting,
0.5 mol/51.548 g theoretical carboxylate yield, 0.5 mol lactone remaining.

Preview evidence:

- [Lactone acid opening, linked 2D/3D](reaction-lab-ester-phase1-lactone.png).
- [Lactone base opening and calculation](reaction-lab-ester-phase1-saponification.png).
- [Phenyl acetate acid hydrolysis and linked atom selection](reaction-lab-ester-phase1-aryl.png).

The local preview was refreshed for the final code. Nothing was pushed or
published, and Phase 2 was not started.
