# Phase 3A — Alkene hydration

Completed October 14, 2026. This increment improves the existing **acid-catalyzed alkene + water** pathway only. No new family, layout redesign, Calculator change, curated example additions, publication or Phase 3B implementation.

## 1. Implementation

Added a dedicated [hydration_rule.py](</Users/rc/Documents/Capstone project/server/hydration_rule.py>) consumer of the shared reaction-site compatibility architecture. It identifies the selected C=C and OH-capture carbon, screens the substrate's other groups, declares four exact mapped net edits and validates them independently.

Hydration no longer shares the old hydrohalogenation/halogenation matcher. Those pathways keep their original eligibility, orientation and product behavior. The core molecular-graph, stereo, product-edit validators, other reaction-rule modules, mechanism renderer and 2D renderer were not weakened or rewritten. Shared compatibility serialization gains only optional consumed-double-bond metadata.

The public workflow exposes each validated site/orientation through matching, 2D preview and acid-enabled 3D generation. The exact same mapped graph supplies products, highlighting, atom inspection and theoretical reaction amounts.

## 2. Newly supported and retained structures

New fixed-benchmark support:

- **2-Hexene:** separately selectable hexan-2-ol and hexan-3-ol net options.
- **E-3-hexene and Z-3-hexene:** selected E/Z is consumed on hydration, without assigning new alcohol configuration.
- **Styrene:** narrowly screened benzylic capture gives unsigned 1-phenylethanol connectivity.
- **Specified 4-methylhex-1-ene:** the distant physical configuration is retained and its CIP descriptor recalculated.

Additional independent tests outside the benchmark demonstrate screened remote primary/secondary alcohols, ordinary saturated ethers and multiple remote alcohol groups. For example, `C=CCCCCCCCO` gives `CC(O)CCCCCCCO` in the conditional net model; `C=CCCCCCCCOC` keeps its remote ether bonds. These are deliberately well-separated structures, not blanket permission for alkenols or ethers.

Previously working simple, long and branched terminal alkenes and symmetric internal alkenes remain supported. Ordinary selected **single 5–8-membered carbocyclic rings** are now explicitly screened and tested, including cyclopentene through cyclooctene and a methyl-substituted cyclic alkene. Some cyclic cases already worked before this increment; they are retained support, not all new coverage gains.

Widely separated isolated double bonds remain distinct selected-site options, even when graph symmetry gives the same constitutional product. Unselected valid E/Z is preserved. Multiple options are **not** a prediction of selective partial hydration or product distribution.

## 3. Orientation and competing chemistry

The ordinary substitution-based Markovnikov model gives propene → propan-2-ol. Full-graph symmetry collapses equivalent orientations. Equal, inequivalent internal ends instead expose both validated constitutional capture options. A narrow phenyl-conjugated branch uses benzylic stabilization; unvalidated competing stabilization patterns are rejected.

This is an **initial water-capture net model**, not a claim that the unrearranged alcohol is the guaranteed experimental product. Acid activation, carbocation capture and catalyst regeneration follow the introductory acid/water discussion in [OpenStax 8.4](https://openstax.org/books/organic-chemistry/pages/8-4-hydration-of-alkenes-addition-of-h2o-by-oxymercuration). The oxymercuration section on that page is not implemented here; no mercury reagent or different hydration family was added.

Adjacent branched/quaternary shift risks, neighboring ring migration and potential benzylic shifts are excluded. The ordinary 3-methyl-1-butene rearrangement example illustrates why simple substitution counting is insufficient. [Carbocation rearrangement reference](https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements).

Remote oxygen groups are screened for saturated ordinary environments, acid-sensitive cleavage/dehydration and short intramolecular capture. Potential 3–6-membered O/pi closure paths are excluded. Acid-mediated intramolecular alcohol capture is documented chemistry, but the tool does not predict its products or transfer a particular published catalyst/solvent protocol to every input. [Primary hydroalkoxylation study](https://link.springer.com/article/10.1007/s00706-024-03214-3), [ether-cleavage reference](https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage).

**Safety correction:** 1,7-octadiene is no longer accepted as an uncomplicated selected-site hydration. Its second C=C creates a possible short intramolecular carbon-capture route, so competing cyclization remains unresolved. This is a conservative structural-risk inference, not an assertion that cyclization must occur or dominates. Acid cyclization has been investigated experimentally for other acyclic dienes; that evidence does not establish the product distribution of this exact substrate. [Primary diene-cyclization study](https://authors.library.caltech.edu/records/f1dcg-j9d20).

Distance/ring-size bounds are model screening choices, not universal published selectivity laws. Longer-range migration, larger-ring/intermolecular capture, isomerization, polymerization, further hydration and equilibrium composition are not predicted. No major/minor percentages, yields or rates are generated.

## 4. Required activation and existing controls

| Input conditions | Assessment and action |
| --- | --- |
| Acid absent, unspecified or None added | **Acid activation required.** Conditional 2D is inspectable; 3D/run/compare are disabled and the run API returns 422. |
| Other catalyst selected | **Not evaluated.** It is not treated as acid activation or automatically called chemically unfavorable. |
| Actual water + Acid; aqueous or no extra medium specified | Supported acid/water **net** conditions. 3D can be generated; unspecified acid strength, water activity and kinetics are not inferred. |
| Acid + Dry | Conflicting water/medium settings cannot be evaluated; conditional 2D only. |
| Acid + Ethanol/polar-aprotic medium | Solvent capture or acid/water compatibility is unvalidated; conditional 2D only. |

Temperature selectors do not imply universal room-temperature conversion or predict heating effects quantitatively. Structural availability remains distinct from condition assessment. Missing required acid is not labeled merely a difference from a preset.

The existing controls consume this assessment; no controls or page panels were added or rearranged. Changing conditions clears stale selection/products. Supported theoretical reaction calculations remain available with explicit activation/equilibrium/selectivity qualifications, not as actual yields.

## 5. Atom mapping and stereochemistry safeguards

- Selected C=C changes from order 2 to 1; one actual water O–H bond is broken in the net mapping; C–H and C–O form at the declared endpoints. The other water H stays on O.
- Exactly one water equivalent is consumed. Acid is regenerated and is excluded from the net equation and required-amount arithmetic. Hydrogen identities are **net bookkeeping**, not an isotope/proton-exchange history involving the catalyst.
- Unique atom identities, charges, every unaffected bond, valence, explicit hydrogen counts, connected product and the 80-explicit-atom bound remain enforced.
- Distant specified tetrahedral configurations are independently retained by mapped physical parity and checked after serialization. CIP is recalculated rather than copied. Coordinates of generated 3D conformers are independently checked for the specified distant centers.
- Only the selected valid E/Z disappears; unselected E/Z is checked. Newly formed or initially unspecified centers remain unsigned. No syn/anti outcome or enantiomeric ratio is assigned by an ordinary acid model or a single conformer.
- An input-only hydration guard preserves a warning when directional alkene annotations would be erased during normalization, including unvalidated small-ring or incomplete terminal notation. These hydration options fail closed, including when canonicalization would otherwise match a preset. The unsanitized copy is used only to inspect input directions and never supplies chemistry/products; other pathways keep their old input behavior.

Hydration remains a mapped **net** visualization; a step-by-step carbocation/oxonium hydration mechanism is not implemented or advertised as complete. Existing SN1/SN2/E1/E2 mechanisms remain intact.

## 6. Unchanged 347-case benchmark

The original matrix, expectations, scoring and script are unchanged. Script SHA-256: `1304ec753e0c7986ade09e324cc1f420572e46c8e5ecc8ef3979bdd669c75b55`.

**Hydration: 6/14 (42.9%) → 10/14 (71.4%).** Five cases gain support; one previous permissive result is conservatively excluded.

| Case | Change | Reason |
| --- | --- | --- |
| A066: 2-hexene | Unsupported → fully supported | Both constitutional capture alternatives are selectable. |
| A067/A068: E/Z-3-hexene | Unsupported → fully supported | Valid selected alkene geometry is consumed without invented alcohol configuration. |
| A069: styrene | Unsupported → fully supported | Narrowly screened benzylic capture orientation. |
| A072: remote specified center | Unsupported → fully supported | Mapped distant retention and independent CIP. |
| A074: 1,7-octadiene | Fully supported → unsupported | Short intramolecular pi-capture/cyclization risk; no selective hydration assumption. |

Remaining applicable benchmark exclusions:

- **A070, 4-penten-1-ol:** potential five-membered intramolecular oxygen capture.
- **A071, remote fluoroalkene:** F is outside this hydration policy's validated spectator set, not declared unreactive throughout the website.
- **A073, 1-triacontene:** hydrated product exceeds 80 explicit atoms.
- **A074, 1,7-octadiene:** unresolved competing cyclization as above.

All **332 non-hydration rows** retain their previous statuses, products, option counts, preview/geometry outcomes and mechanism-step counts. Overall: **169 fully supported, 124 unsupported, 16 partial, 38 correctly rejected**. No audit-flagged incorrect result or failed preview. Some pooled rejection notes can now mention the separately evaluated hydration policy.

This percentage is fixed tested-case workflow coverage, not comprehensive chemistry, experimental selectivity or complete mechanism support. Existing benchmark stereo-grading caveats are not repaired by changing its expectations.

## 7. Verification

**1,051 tests pass: 529 Python + 522 JavaScript, no failures or skips.** Added **53 Python + 22 JavaScript = 75 tests**. All 976 previous test methods remain. Six existing methods update intentionally superseded hydration activation, ambiguous-orientation or capability expectations; none were deleted to obtain a passing count.

New checks cover independently supplied products, orientations, terminal/internal/branched/cyclic structures, remote OH/ethers, specified centers, E/Z consumption/retention, multiple sites, unassigned new centers, rearrangements/cyclization, unsupported groups/elements/input annotations and size limits. Deliberately tampered bond, hydrogen-map and stereo products fail the exact validators.

Four real authenticated HTTP tests exercise matching, both 2-hexene products, conditional diagrams, missing-acid 422 responses, eligible 3D atom links and forged/rejected selections without a listening socket or deployment. Sixteen real public fixtures exercise the unchanged browser-local amount calculator in both input orders, with independent elemental-weight sums, limiting amounts, theoretical mass and required amounts. Acid never becomes a consumed third reactant.

The previous four-pathway public diagnostic also passes: **48 substrates, 192 matching calls, 48 condition checks, five reagent controls, 125 verified options, zero failures**. Elementary mechanisms, conservation, mapped changes, physical stereo and exact 2D/3D correspondence remain checked.

TypeScript `--noEmit`, production build and `git diff --check` pass. Existing third-party directive and large Builder-bundle warnings remain. Hashes confirm HTML/CSS, Calculators, curated molecules/public data, fixed benchmark and unrelated rule/graph/stereo/rendering modules remain unchanged.

Browser verification used the existing propene/water inputs: absent acid showed conditional 2D with disabled 3D controls; selecting Acid reset the result and enabled linked 2D/3D 2-propanol. The local preview was refreshed with final code. Nothing was pushed or published.

[Saved audit, diagnostics and source hashes](</Users/rc/Documents/Capstone project/docs/reaction-lab-hydration-phase3a-results.json>).

![Verified acid-enabled propene hydration comparison](</Users/rc/Documents/Capstone project/docs/reaction-lab-phase3a-preview.jpg>)

## 8. Remaining scope and next recommendation

Unvalidated conjugated/cumulated or directly heteroatom-substituted alkenes, complex/fused/bridged/exocyclic reaction rings, general aromatic acid chemistry, near-site specified centers, rearrangement/cyclization-prone structures and unsupported acid-sensitive groups remain excluded with reasons. Larger-ring/intermolecular and longer-range chemistry is not established by distance alone. No real experimental conversion, distribution or stereochemical mixture is predicted.

Recommend a **separately requested existing hydrohalogenation compatibility increment** next: adopt selected-site architecture while independently validating HX-specific orientation, rearrangement and spectator chemistry. It must not blindly inherit hydration's acid/water permissions.

**Phase 3A stops here. No Phase 3B or other pathway implementation was started.**
