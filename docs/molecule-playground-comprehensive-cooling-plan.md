# Molecule Playground — Comprehensive Cooling System Development Plan

24 October 2026 · Planning document v1 · Awaiting approval

**This document proposes future work. It does not implement or approve additional cooled chemistry.** Production code, existing tests, prior reports, the frozen benchmark, the website layout and Render are unchanged by this planning phase.

## 1. Executive summary

Cooling should become a reaction-specific condition system, not a universal permission switch. All 24 reaction-rule types should recognize the selected temperature and explain their status. That does **not** require all 24 to generate cooled products or 3D structures.

The current implementation provides a sound starting point: two bounded models, fail-closed generation, independent product validation, conditional previews and stale-result protection. The approved models are:

- `cooled-alkene-bromination-v1`: actual Br₂ under the existing screened, non-capturing model.
- `cooled-peroxyacid-epoxidation-v1`: actual mCPBA, not any peracid or formula-equivalent reagent.

The main development need is a versioned profile architecture that can expand without duplicating chemistry decisions across backend checks and frontend wording. Each additional profile then needs its own evidence review, condition contract, independent product checks and public-workflow verification.

Recommended order:

1. Consolidate the **two existing profiles without changing behavior**.
2. Validate a narrowly scoped, actual-perbenzoic-acid epoxidation profile using directly accessible checked evidence.
3. Complete the source/formulation review for cooled Os/H₂O₂ dihydroxylation, the strongest identified candidate for a **third reaction type**.
4. Investigate chlorination, substitution and reduction profiles in separately approved increments.
5. Keep unresolved endpoints, ionic 3D limitations and different reagent systems explicitly excluded.

No phase should promise reaction rates, complete conversion, experimental yields, site selectivity or stereoisomer ratios. A theoretical conformer is a representation of an eligible molecular product, **not a temperature simulation or proof that a reaction occurs**.

## 2. Current implementation assessment

### 2.1 Reviewed baseline

This plan was checked against the actual local source and [the existing cooling report](reaction-lab-cooling-compatibility-v1.md), not just earlier chat descriptions.

The last completed implementation report records **4,040 passing tests: 2,029 Python and 2,011 JavaScript**, with TypeScript, production build and browser verification passing. Those are recorded baseline results; this planning phase does not claim a fresh regression run.

The frozen 347-case audit currently records 155 fully supported, 90 unsupported, 38 correctly rejected, 63 partially supported and one pre-existing incorrect-result classification. Its inputs contain no cooled cases. These counts cannot measure cooled-profile coverage. Existing benchmark defects and condition-aware measurements must remain separate.

### 2.2 What is already strong

- Reagent identity comes from validated molecular structure. The mCPBA check is not based on its name or formula.
- Cooling cannot override failed substrate, reagent, medium, endpoint, mapping, charge or stereochemistry validation.
- Match, diagram and run operations reassess current inputs. An earlier option ID does not authorize generation under new conditions.
- Conditional 2D net transformations are distinguished from eligible theoretical 3D products.
- Existing UI changes invalidate diagrams, viewers, mechanisms, selections, measurements and calculator results; late responses are ignored.
- The current profiles retain existing product transformations and atom provenance.
- Detailed epoxidation mechanisms exist; a complete bromonium mechanism does not. Cooling does not change that distinction.

### 2.3 Architectural gaps to address before expansion

| Verified code area | Current behavior | Planning implication |
| --- | --- | --- |
| `server/chemistry_server.py`, `CONDITION_VALUES`, `_conditions()` | Temperature is unset, `cooled`, `ambient` or `heated`; unknown fields fail closed. | A numeric temperature or new profile field cannot simply be sent today. Any future schema change needs explicit validation and migration. |
| `server/reaction_conditions.py`, `assess_cooling_support()` | Explicit branches for the two reviewed profiles. | Replace duplication with a small versioned registry, retaining their exact existing behavior. |
| `cooling_confidence()` and `chemistry_server._assessment()` | Idempotent confidence overlay preserves stronger blockers. | Keep one authoritative evaluation contract; do not drop a stronger reason while adding a temperature message. |
| `reaction_conditions.alkyne_input_evidence()` | A separate guard currently accepts only unset/ambient temperature. | A future alkyne profile needs a profile-scoped integration here too. Globally removing the guard is unsafe. |
| `chemistry_server._base_assessment()` | Six legacy types return primarily state/note rather than the modern explicit permission/factor contract. | Add cooled-only normalization for hydrogenation, carbonyl hydrogenation, esterification, ester hydrolysis, saponification and polymerization before expansion. Preserve non-cooled behavior. |
| `src/reaction-conditions.ts` | Positive cooling wording explicitly recognizes the two reviewed model/pathway pairs and consistent backend permissions. | A backend-only expansion would leave inconsistent UI feedback. Use a versioned reviewed contract, not an independently growing frontend chemistry switch. |
| `server/reaction_condition_guidance.py` | Guidance currently targets Lindlar and alcohol oxidation, not cooling profiles. | Add prospective cooling guidance only after a profile is reviewed. Guidance must never itself authorize a product. |
| `server/reaction_compatibility.py` | Existing connected/neutral/closed-shell, element, size, site and stereo restrictions remain. | Temperature approval must not bypass these limits or extend structural scope. |

Existing mCPBA evidence is anchored to mild cooling and a specific solvent precedent. Its documented initial/hold temperature and addition upper limit are **not** a validated continuous operating window. Similarly, the current “dry” selector does not experimentally validate every dry solvent. The future architecture should make these bounded assumptions clearer without retroactively claiming broader evidence.

## 3. Complete 24-reaction compatibility matrix

### Classification and evidence key

- **S — Supported:** an existing bounded cooled model is implemented.
- **P — Potential:** a cooled profile may be supportable; it is not approved yet.
- **I — Current-profile incompatible:** an explicit existing temperature, formulation or endpoint boundary prevents cooled confidence. This does not assert universal chemical impossibility.
- **O — Outside current scope:** temperature evidence alone cannot resolve the endpoint, output or mechanism limitation.

Evidence labels: **D** = directly inspected primary reaction-stage evidence; **L** = limited primary evidence, such as indexed experimental text, an abstract or kinetics without validated product scope; **Iƒ** = mechanistic/modeling inference; **U** = no adequately matching cooled primary profile established in this review. E-number references are detailed in Section 4.

All proposed substrate classes mean **only structures already accepted by that pathway's site/compatibility rules**. They do not enable excluded rings, competing groups or stereochemistry. “Could allow 3D” always means after all current product and geometry checks, not guaranteed embedding.

| # | Existing rule type / current cooling class | Documented cooled feasibility | Required or proposed bounded conditions | Pathway/product effects and current engine fit | Theoretical 3D and missing validation |
| --- | --- | --- | --- | --- | --- |
| 1 | **Hydrogenation — P** | U for an actual matching cold H₂/current-metal profile. Other catalyst literature is not transferable. | Existing eligible alkene + actual H₂; identify the actual metal formulation/support and compatible medium before qualifying a cold model. | Current net C=C reduction is representable. Catalyst activity, other reducible groups and one-site selectivity are not established by cooling. | Could allow selected neutral products after catalyst/substrate evidence, formulation metadata and legacy-assessment normalization. |
| 2 | **Bromination — S, bounded** | D: checked cyclic and primary acyclic precedents, E01–E02. | Actual Br₂; current screened alkene; existing dry/non-capturing assumption and no added activation; retain existing exclusions. | Dibromide graph and validated anti-related outcomes already represented. Source-specific medium/additive details limit generalization; cold does not eliminate competing chemistry. | Already permitted within v1. Preserve exact Br maps, stereo alternatives and non-capturing restrictions. Do not claim a full bromonium mechanism. |
| 3 | **Chlorination — P** | L: low-temperature literature exists, but exact matching substrate/medium/product scope is not yet verified, E09–E10. | Actual Cl₂; initially simple eligible hydrocarbon alkenes; independently documented non-nucleophilic medium and initiation/light boundaries. | Existing dichloride and validated anti structures are representable. Radical substitution, capture and rearrangement cannot be dismissed because no initiator was added. | Candidate only after full primary-source review and independent Cl₂ stereo/product verification. Br₂ permission is not evidence. |
| 4 | **Hydration — P** | U for a sufficiently specified cooled acid/water profile matching the current direct alcohol endpoint. | Eligible screened alkene + actual water + required acid; document acid identity/activity, water availability, medium and reaction-stage temperature. | Existing H/OH addition is representable. Cold acid addition that produces an alkyl sulfate followed by hydrolysis/warming is not automatically the current model. | Could allow unrearranged supported products only after capture/rearrangement/cyclization and stage-history validation. No cold syn/anti claim. |
| 5 | **Hydrohalogenation — P; oxygen subprofile I** | U for a qualified cold ionic HCl/HBr/HI profile in current scope. | Actual HX, separately reviewed by identity/formulation; compatible non-capturing ionic medium; no unsupported radical activation. Existing remote-O HCl qualification remains ambient-only. | Existing regioisomer alternatives are representable. Radical, capture and rearranged products are not interchangeable with ionic Markovnikov addition. | Candidate simple substrates only after direct ionic evidence. Do not transfer approval between HX reagents or extend the oxygen-spectator profile automatically. |
| 6 | **Epoxidation — S for mCPBA; other peracids P** | D/L for current mCPBA, E03–E04; D for actual perbenzoic acid at 0 °C, E05; staged peracetic precedent E06. | Current v1: exact mCPBA, screened alkene, dry-compatible assumption, no added activation. Proposed next profile: actual perbenzoic acid with documented medium/thermal scope. | Existing epoxide + actual acid coproduct and same-face transfer fit. Peracetic formulation includes additional controls/warming and needs separate modeling review. | mCPBA already eligible. Perbenzoic candidate requires identity-specific contract and broader independent fixtures. No transfer from source temperature to facial selectivity. |
| 7 | **SN2 — P** | L: aqueous methyl-halide/base-dependent kinetics at 287 K, E13; not a near-zero preparative scope. | Actual hydroxide and a specified supported medium; begin with eligible methyl/low-hindrance sites. Assess base activity and other substitution/elimination sites. | Existing concerted substitution/inversion fits. A cooler kinetic measurement does not qualify all alkyl halides or polar-aprotic media. | Could allow after product/formulation evidence; preserve physical inversion, recomputed CIP and distant centers. Do not impose a universal cold cutoff. |
| 8 | **SN1 — P** | L: lower-temperature tertiary-chloride/water solvolysis literature, E14. | Actual water and documented aqueous formulation; start with screened tertiary carbocation sites, not ordinary primary/methyl centers. | Existing ionization, water capture and deprotonation fit. Product competition, rearrangement and cyclization still need screening. | Candidate after full-source/product review. No retained reacting-center configuration or exact racemization ratio. |
| 9 | **E2 — P, lower priority** | U for a directly validated cold hydroxide/alkyl-halide product profile in this review. | Actual hydroxide; supported medium/base conditions; validated acyclic α/β site and β-H/anti requirements. | Current concerted elimination fits. Heated is a reference, not proof that low-temperature E2 is impossible; SN2 competition remains unresolved. | Do not approve yet. Need cold alkene-product evidence, base/formulation and geometry review; no new E/Z prediction. |
| 10 | **E1 — P, lower priority** | U for direct cold elimination-product evidence. SN1 kinetics alone are insufficient. | Actual water/aqueous model; supported carbocation, β-H and site; independently documented elimination outcome. | Current stepwise elimination fits, but ionization does not establish an alkene rather than substitution. | Do not approve from SN1 alone. Preserve planar intermediate, unspecified new E/Z and no SN1/E1 ratios. |
| 11 | **Alcohol oxidation — primary O; secondary I** | D: external cooling in existing secondary NaOCl/AcOH source maintains approximately ambient internal temperatures, E15. Cold selective primary oxidation E16 uses a different reagent system. | Current secondary actual NaOCl/acetic-acid named profile remains ambient. Current primary NaOCl model has no qualified aldehyde-stopping profile at any temperature. | Secondary ketone net graph fits but a genuinely colder profile is unvalidated. Primary aldehyde confidence cannot be created by changing temperature. | Secondary requires independent cold formulation/endpoint evidence. Primary stays blocked; adding TEMPO/KBr/buffer is separate chemistry, not this plan's temperature extension. |
| 12 | **Aldehyde oxidation — I** | U for a cold current-hypochlorite profile with validated reporting/speciation. | Actual supported hypochlorite, aqueous further-oxidation model; validate pH, acid/carboxylate endpoint and any distinct work-up. | Net further oxidation exists, but a neutral-acid reporting graph is not proof of solution speciation or an acid work-up. | Keep current boundary. Temperature evidence cannot resolve ionic geometry or missing work-up information. |
| 13 | **Carbonyl hydrogenation — P** | U for a matching cooled actual H₂/current-metal C=O profile. | Existing screened aldehyde/ketone + H₂; actual catalyst formulation and compatible solvent; competing reductions reviewed separately from alkene hydrogenation. | Selected C=O → alcohol fits. Catalyst selectivity and new-center configuration are not predicted. | Candidate after matched cold evidence; preserve remote stereo and leave newly formed centers unassigned unless already validated otherwise. |
| 14 | **Esterification — P** | Iƒ/U: plausible net chemistry, but no adequately matching cooled primary profile established here. | Existing acid + alcohol, documented acid catalysis/medium, cold reaction stage rather than cold catalyst addition before heating. | Current ester/water graph fits. Equilibrium composition, reaction time and conversion are outside the model. | Candidate after direct evidence and legacy-condition normalization; no claim that cooling produces a specified amount experimentally. |
| 15 | **Ester hydrolysis — P** | U for a bounded cold acid/water profile matching existing scope. | Actual water + acid/aqueous model; retain ordinary ester, approved lactone/aryl and site/stereo limits; validate each proposed substrate class. | Existing acid/alcohol or lactone-opening connectivity fits. Do not infer completion, neutralization or universal ring compatibility. | Could allow eligible neutral products after independent evidence and mapping checks. Acid work-up must remain distinct from basic hydrolysis. |
| 16 | **Alcohol dehydration — I** | D: existing sulfuric-acid precedent heats the reaction; its cooled receiver is not a cooled reaction, E17. | Current actual H₂SO₄/acid model requires heating. No low-temperature replacement reagent is proposed. | Existing alkene graph is not evidence for cold dehydration; substitution/ether formation may compete. | Remain unsupported under current cooled profile. A different dehydrating reagent would require separate chemistry approval. |
| 17 | **Alcohol substitution — I; narrow research candidate** | L: historical cold tert-butanol/HCl lead cited by checked procedure, E18; original experiment not yet reviewed. | Current methyl/primary HX profile requires heating; secondary/tertiary profile is ambient. Investigate actual HCl/tertiary alcohol only if original evidence is obtained. | Existing haloalkane graph fits selected cases. Elimination, ionization, rearrangement and stereo remain independent questions. | No present cooled permission. Do not generalize a tertiary HCl lead to primary alcohols or HBr/HI. |
| 18 | **Ester saponification — P chemistry; O for present 3D** | Iƒ/research lead: cold alkaline ester hydrolysis is plausible, but no fully reviewed profile is admitted here. | Actual hydroxide/aqueous model and existing ester-site restrictions; product is hydroxy carboxylate where applicable, not neutral acid. | Ring opening/ester cleavage and ionic net accounting fit. A separate acid work-up is not part of the selected reaction. | A future cold net-model review could improve 2D confidence. Charged carboxylate 3D remains outside current output policy; no silent protonation. |
| 19 | **Alkyne hydrogenation — P** | U for a matching cold full-reduction profile; specialized cold Pd work E12 is not generic-metal evidence. | Actual two H₂ + independently documented current active-metal formulation; existing eligible isolated alkyne and competing-site limits. | C≡C → C–C and two-equivalent net accounting fit. Partial reduction/isomerization/other sites remain risks. | Candidate after actual alkane endpoint and catalyst evidence; profile-scoped alkyne temperature integration required. |
| 20 | **Alkyne partial hydrogenation — P** | D for existing Lindlar chemistry but not a cold reaction stage, E08. | Actual H₂ + Lindlar; one-equivalent net endpoint; current isolated eligible alkyne, medium and competing-group limits. | Existing syn/cis/Z product model fits. The source warns uptake continues; cooling does not establish automatic stopping. | Need actual cooled Lindlar evidence and endpoint limits. Terminal products receive no invented E/Z; no substitution of another Pd formulation. |
| 21 | **Alkyne halogenation — P, reagent/stage-specific** | U for fully reviewed cold profiles matching current one-/two-stage endpoints. | Actual Br₂ or Cl₂, separately; explicit one or two equivalents; validated non-capturing medium and no unsupported initiation/capture. | Dihaloalkene and tetrahaloalkane graphs exist. First-stage chlorine stereo, additional unsaturation and nucleophilic groups remain independent limits. | Investigate Br₂ stages separately. Do not enable first-stage Cl₂ 3D while its existing stereo confidence is unresolved. |
| 22 | **Alkyne hydrohalogenation — I** | L: genuine 0 °C HBr evidence found is explicitly homolytic, E11, not current ionic chemistry. | Current qualified ionic profile requires ambient/dry/explicit stage; retain HCl formulation, internal E/Z, two-HI, remote-O and multi-site limitations. | Existing vinyl/geminal products fit only qualified scopes. A radical cold product is not evidence for ionic orientation/stereo. | No present cold extension. Need direct ionic reagent-specific product evidence; both thermal gates and original blockers must remain authoritative. |
| 23 | **Alkene dihydroxylation — P, priority candidate** | L: primary experimental text reports actual H₂O₂/OsO₄ in tert-butanol at 0 °C with identified glycol, E07. Full formulation verification remains a gate. | Actual current H₂O₂/Os system; named compatible medium/formulation and confirmed aqueous release. Initially avoid new-stereocenter scope unless independently validated. | Existing syn diol net model may fit. Overoxidation, medium and release assumptions must be checked; Os/NMO is a different system. | Could become a third supported type after evidence/representation review. Source's non-stereogenic example does not validate all E/Z-derived stereo products. |
| 24 | **Polymerization model — O** | U for the present finite BPO model under cooling. Other cold initiation systems are not substitutes. | Existing actual BPO, radical activation and finite 2/4/6-unit model; no new redox, amine or photoinitiator. | Finite connectivity is not initiation/propagation/termination, kinetics or bulk polymer prediction. | Remain unsupported for a cooled outcome claim. Temperature validation alone cannot supply the missing initiation/endpoint model. |

There are exactly 24 rule types above. Primary and secondary alcohol oxidation share type 11 but require separate fixtures, producing at least 25 model-level checks. Profile counts and supported-type counts must be reported separately.

## 4. Scientific evidence and limitations

This is a bounded primary-source review, not an exhaustive literature survey. A missing matched source below means **not established here**, not that the reaction cannot occur. A paper's title, an abstract, a cold bath, a supplier protocol or a generated conformer is insufficient for broad permission.

### 4.1 Existing qualified profiles and the next evidence leads

- **E01 — Br₂/cyclic alkene:** [checked Organic Syntheses preparation](https://www.orgsyn.org/demo.aspx?prep=CV2P0171), DOI 10.15227/orgsyn.012.0026. Direct cooled product precedent, but its historical medium/additives and competing substitution observations prevent treating every dry medium as equivalent.
- **E02 — Br₂/acyclic alkene:** Amrani and Aizenshtat, [primary experimental paper](https://doi.org/10.1016/j.orggeochem.2004.06.019), [author-paper repository copy](https://repository.geologyscience.ru/bitstream/handle/123456789/39625/Amra_04.pdf?sequence=1). Contains a cooled actual-Br₂ alkene preparation with analytical identification. Supports a bounded net-model inference, not universal site or face selectivity.
- **E03 — mCPBA:** Srinivasan et al., [Epoxidation of Olefins at Low Temperature Using m-Chloroperbenzoic Acid](https://doi.org/10.1081/SCC-120004069). Publisher abstract supports low-temperature mCPBA/dichloromethane chemistry without catalyst. Full experimental text was not retrievable; no exact temperatures or substrate table are attributed to the abstract.
- **E04 — mCPBA thermal-stage anchor:** [US7612123B2, Example 4](https://patents.google.com/patent/US7612123B2/en). Primary patent experiment documents near-zero reaction stages, an addition upper bound and an identified epoxide. This is not an independently checked procedure or a validated continuous temperature interval. Subsequent bicarbonate treatment is not the oxidation catalyst.
- **E05 — strongest accessible next peracid profile:** [checked styrene-oxide preparation](https://www.orgsyn.org/demo.aspx?prep=CV1P0494), DOI 10.15227/orgsyn.008.0102. Actual perbenzoic acid/chloroform at 0 °C gives the epoxide. Supports a narrow candidate within existing eligibility; not every aryl alkene or peracid formulation.
- **E06 — peracetic caution:** [checked preparation, Note 2](https://www.orgsyn.org/demo.aspx?prep=CV6P0312), DOI 10.15227/orgsyn.051.0011. Cold peracetic epoxidation includes acetate/formulation control and subsequent warming. Do not collapse that history into the current no-added-activation dry model. Separately, [trans-stilbene oxide](https://www.orgsyn.org/demo.aspx?prep=CV4P0860), DOI 10.15227/orgsyn.038.0083, supports a stereochemical relationship but uses different temperatures; it is not cooled-mCPBA evidence.
- **E07 — strongest new-type lead:** Milas and Sussman, [The Hydroxylation of the Double Bond](https://doi.org/10.1021/ja01298a065), JACS 1936, 58, 1302–1304, [primary-paper scan](https://electronicsandbooks.com/edt/manual/Magazine/J/Journal%20of%20the%20American%20Chemical%20Society%20US/1936%20%20%28vol%20058%29/07%20%20%281067-1320%29/1302-1304.pdf). Indexed experimental text reports 2-methylpropene → 2-methylpropane-1,2-diol with the current oxidant/catalyst pair in cold tert-butanol. This creates no stereocenter. Its reported fractionation does not independently validate the engine's particular aqueous-release assumption. Direct PDF retrieval timed out; check complete experimental pages and that separate release/representation gate before implementation. [Checked Os/NMO dihydroxylation](https://www.orgsyn.org/demo.aspx?prep=CV6P0342), DOI 10.15227/orgsyn.058.0043, instead reacts at room temperature; cold crystallization is not cooled H₂O₂/Os evidence.
- **E08 — Lindlar endpoint caution:** [Lindlar and Dubuis, checked catalyst/test procedure](https://www.orgsyn.org/demo.aspx?prep=CV5P0880), DOI 10.15227/orgsyn.046.0089. Validates selective-catalyst chemistry and the need to stop hydrogen uptake, but not a cooled reaction stage. Heated catalyst preparation is also not the substrate reaction temperature.

### 4.2 Evidence that must not be generalized

- **E09 — cold Cl₂ lead:** Taft, [Substitution vs addition in the low temperature non-activated chlorination of olefins](https://pubmed.ncbi.nlm.nih.gov/18891863/), DOI 10.1021/ja01190a044. Only a primary bibliographic record was accessible. Retrieve the paper before claiming its exact substrate, medium, stereo or product distribution.
- **E10 — Cl₂ competing mechanism:** Poutsma, [primary chlorination study](https://doi.org/10.1021/ja01088a015). Indexed primary text describes substrate-initiated radical chemistry and medium dependence. Full-text retrieval was incomplete. This is a caution against equating “none added” with demonstrated absence of radical chemistry, not an admitted cooling profile.
- **E11 — different alkyne HX mechanism:** [Tetrahedron 2022, 132687](https://www.sciencedirect.com/science/article/abs/pii/S0040402022000734), DOI 10.1016/j.tet.2022.132687, describes cold, air-associated homolytic hydrobromination. It cannot qualify the existing ionic HX model.
- **E12 — different hydrogenation catalyst:** Staiger et al., [cold Pd-nanoparticle study](https://doi.org/10.1002/cctc.202001121). Catalyst/additive/pressure-dependent partial reduction, full reduction and competing outcomes do not validate Lindlar or a generic Pd/Pt selector.
- **E13 — narrow SN2 kinetics:** Baesman and Miller, [primary-author USGS record](https://pubs.usgs.gov/publication/70028000), DOI 10.1007/s10874-005-1904-0. Aqueous methyl-halide kinetics at 287/306 K include pH-dependent base hydrolysis. The cooler point is about 14 °C, not near-zero permission. Buffer/base activity and kinetic measurements do not establish a general preparative product profile. The official record was indexed but direct retrieval returned 403.
- **E14 — narrow SN1 kinetics:** Adams and Sheppard, [tertiary-chloride/water solvolysis study](https://doi.org/10.1039/F19807602114); related [Euranto and Kanerva study](https://doi.org/10.1039/F19837901483). Lower-temperature measurements are a credible research lead. Full experimental/product review is still required; solvolysis rate evidence does not determine SN1/E1 product proportions.
- **E15 — bath versus mixture temperature:** Stevens, Chapman and Weller, [secondary-alcohol oxidation paper](https://doi.org/10.1021/jo01298a066), [primary PDF](https://ursula.chem.yale.edu/~chem220/PROBSETS/PS13spr/PS9-S13-ans/Stevens1980JOC.pdf). External ice cooling maintains internal temperatures of 15–25 °C or 20–25 °C in the cited examples. It does not validate a near-zero secondary-oxidation profile or a selective primary-aldehyde endpoint.
- **E16 — different primary-oxidation formulation:** [checked (S)-(+)-2-methylbutanal preparation](https://www.orgsyn.org/demo.aspx?prep=CV8P0367), DOI 10.15227/orgsyn.069.0212. Cold stages are real, but TEMPO, KBr, buffering and biphasic formulation distinguish it from the current primary NaOCl system. Do not add those unimplemented reagents through a temperature profile.
- **E17 — receiver versus reaction:** [checked cyclohexene preparation](https://www.orgsyn.org/demo.aspx?prep=cv1p0183), DOI 10.15227/orgsyn.005.0033. The sulfuric-acid reaction is heated; the receiver is cooled. It does not support cooled dehydration.
- **E18 — alcohol-substitution historical lead:** [checked tert-butyl chloride preparation](https://www.orgsyn.org/demo.aspx?prep=CV1P0144), DOI 10.15227/orgsyn.008.0050. Its discussion cites an older freezing-mixture/HCl preparation, but the checked procedure itself does not specify that cold reaction. Obtain the original experiment before proposing permission.

### 4.3 Evidence admission gate for every new profile

Record the primary source, exact experimental location, actual structures, relevant reaction-stage temperature, reagent formulation, medium, activation, stage/work-up, identified products, stereo evidence and competing chemistry. Separate what the source demonstrates from the generalized structural inference the software proposes.

Multiple independent structure fixtures are required even when a source reports only one substrate. They check that the implementation generalizes correctly; they do **not** turn those structures into independently proven cold experiments. If the evidence cannot support the proposed class, narrow or defer the profile rather than add hard-coded molecule-name exceptions.

Historical hazardous media are evidence anchors, not recommendations for student laboratory use. No quantities, handling directions or safety assurances need to be added to Reaction Lab.

## 5. Proposed shared cooling architecture

### 5.1 Layered evaluation, not one temperature boolean

Evaluate in this order, retaining all relevant blockers:

1. **Valid inputs and identities:** accepted fields, exact substrate/reagent structures and known profile/version.
2. **Structural eligibility:** selected reactive atoms/bonds and existing spectator/competition/stereo restrictions.
3. **Non-thermal requirements:** actual reagent, catalyst, medium, equivalents, activation, endpoint and work-up.
4. **Thermal-profile compatibility:** does a reviewed profile cover this condition interpretation and chemical scope?
5. **Product validity:** existing connectivity, valence, charge, conservation, mapping and stereochemistry checks.
6. **Output eligibility:** conditional net preview, asserted supported net transformation, theoretical 3D permission and separate geometry availability.
7. **Experimental confidence:** rates, yields, complete conversion, selectivity and laboratory suitability remain unpredicted.

Never temporarily rewrite `cooled` to `ambient` to make an existing assessor pass. Explicit ambient-only models require independently reviewed cooled variants. A legacy reference mismatch must not be mislabeled as a missing chemical activation requirement.

### 5.2 Versioned backend registry

Proposed new module: `server/reaction_temperature_profiles.py`, called by the existing shared assessment layer. This filename is a proposal, not a file created by this plan.

Each reviewed entry should contain:

- Stable model ID, version and reaction-rule type.
- Exact reagent predicate and a reusable existing substrate/site-policy identifier.
- Required/compatible/conflicting medium, catalyst, activation, equivalents, stage and work-up settings.
- Thermal semantics: documented observations, covered qualitative interpretation, stage history, and explicitly unassessed factors.
- Source/evidence records, reviewed applicability and limits of structural generalization.
- Structured reason codes, recovery suggestions and explicit output permissions.

Keep the existing two IDs and v1 serialized metadata compatible during consolidation. Unknown models, versions, contradictory fields and missing reagent metadata fail closed. Provisional research entries must never be executable registry entries.

The registry should not duplicate product rules, implement a new thermodynamic solver or declare arbitrary spectators inert. It should invoke existing pathway checks and add a narrowly scoped condition-confidence decision.

### 5.3 Qualitative setting versus named and numeric profiles

Retain **Cooled / Low Temperature** as a qualitative user choice. It is sufficient only when a reviewed model explicitly defines what the application assumes. It cannot mean a universal range or arbitrary cryogenic conditions.

Prefer **named documented models** before numeric entry. A lone temperature cannot supply solvent identity, catalyst support/poisoning, pressure, concentration, pH, time or warm-up/work-up history. Use existing Guided Conditions/details surfaces to disclose these model assumptions, with user confirmation where a profile must be selected. Do not silently claim the user entered an exact solvent or temperature.

For future numerical support, require a separately approved schema/design decision. Distinguish:

- Bath/setpoint from actual reaction-mixture temperature.
- Initial temperature from addition control, hold temperature, later warming and isolation.
- A published observed point from an independently validated interval.
- User-entered values from model assumptions and reference observations.

Do not infer continuous validity, interpolate rates or set a global cold/ambient boundary. If the evidence requires multiple stages that current controls cannot express, keep the profile conditional until that representation is separately approved. No new numerical control or layout change is part of this plan's execution.

### 5.4 Output and reason contract

Preserve existing fields while proposing structured reasons for:

- Supported bounded model.
- Missing required information.
- Conflicting or incompatible selected profile.
- Unsupported/competing substrate chemistry.
- Unreviewed temperature/formulation scope.
- Unsupported endpoint or ionic output.
- Valid product graph but unavailable geometry.

Reason precedence must remain specific: wrong reagent is not a temperature problem; failed atom balance is not missing conditions; an unreviewed cooled pathway is not chemically impossible.

Backend permission remains authoritative. A future reviewed manifest/version can replace the frontend's duplicated two-model switch, but the frontend must still reject unknown or contradictory responses. Guidance and calculator metadata must not become alternative authorization routes.

## 6. Complete workflow integration

| Surface | Required future behavior | Primary code areas |
| --- | --- | --- |
| Matching and site selection | Retain structural candidates separately from condition readiness. Deduplicate equivalent products without hiding distinct sites or regioisomers. Cold approval does not imply experimental site selectivity. | `server/reaction_engine.py`; `chemistry_server.match_reactions()`; existing `*_rule.py` site checks, unchanged unless separately approved. |
| Product generation | Re-resolve current substrate/reagent/site/profile; retain all original pathway gates, mapping, balance and endpoint checks. Never trust a stale option ID. | `chemistry_server.run_curated_reaction()` and `reaction_conditions.py`. |
| 2D diagrams | Where a net transformation is already eligible for conditional preview, show current condition limitations alongside it. Do not render a rejected product as an asserted supported outcome. | `chemistry_server.reaction_diagram()`; `server/reaction_diagrams.py`; `src/reaction-lab.ts`. |
| Theoretical 3D | Require reviewed profile permission **and** validated product/stereo/maps **and** successful geometry. Main-product-only displays must identify omitted coproducts. | Public run endpoint; `server/addition_contract.py`; `src/reaction-conditions.ts`; existing viewer integration. |
| Stereochemistry | Retain independently validated existing outcomes; preserve distant physical configuration and recompute CIP. Cooling adds no stereochemical rule or conformer-derived certainty. | `server/stereochemistry.py`; existing halogen/epoxide/stereo utilities. These are validation dependencies, not planned rule rewrites. |
| Atom mapping | Keep consumed H/X/O provenance, unchanged atoms and correct equivalent counts; coproduct maps remain in the 2D net equation. | Existing graph/product pipeline and public API serialization. |
| Guided Conditions | Offer only a reviewed prospective model; disclose assumptions and proposed changes; require confirmation; reassess after application. Never silently turn cooling into ambient or remove an incompatible field. | `server/reaction_condition_guidance.py`; `src/guided-reaction-conditions.ts`; existing apply/signature logic. |
| Mechanisms | Apply the same condition status to current mechanism displays. Keep SN1/SN2/E1/E2/epoxidation support honest; a net transformation is not a complete mechanism. | `server/reaction_mechanisms.py`; existing mechanism modules and UI. No new mechanism is required by cooling approval. |
| Calculators | Keep browser-local theoretical stoichiometry; carry selected conditions/profile and invalidate previous outputs on change. Alternative outcomes are not summed as predicted yields. | `addition_contract.py`; existing calculator context and calculation modules. No arithmetic redesign. |
| Feedback and lifecycle | Clear old viewer/diagram/mechanism/selection/measurement/calculation immediately on any condition/profile/reactant change. Ignore late responses; validate restored draft versions. | `src/reaction-lab.ts` condition payload, reset/abort/revision, guided apply and draft restoration. |

### User-facing guidance without layout changes

Use the current condition messages/details/guidance panels. Proposed wording examples, not implemented strings:

- “This cooled model requires actual Br₂ and the reviewed non-capturing medium assumption. Select the missing medium setting to reassess.”
- “Cooling is not yet validated for this reagent formulation. A conditional 2D net transformation is available; 3D is not authorized.”
- “The selected primary-oxidation system does not establish an aldehyde endpoint. Temperature alone cannot resolve this.”
- “The product is a carboxylate; the present ionic-3D restriction still applies. No acid work-up has been assumed.”
- “Theoretical molecular conformer under a bounded condition model—not a temperature simulation or an experimental outcome guarantee.”

Only show an actionable selector instruction when changing that setting can actually resolve the blocker. Otherwise state that evidence/modeling is missing. Preserve specific earlier chemistry reasons.

UI/UX Pro Max informs accessible feedback planning only: announce changing status/errors through existing accessible status regions, use text rather than color alone, and keep recovery guidance adjacent to the condition assessment. No styling, layout or interaction code is changed in this planning phase.

## 7. Numbered implementation roadmap

Every phase below is a **separate approval boundary**. Passing a phase does not authorize starting the next. Each chemistry candidate may finish as “deferred with documented evidence gap.” No phase may relax product rules to obtain a passing count.

The common verification gate in Section 8 applies after **every implementation phase and chemistry subincrement**.

### Phase 1 — Consolidate existing profiles and contracts; no chemistry expansion

1. **Types:** current bromination and mCPBA epoxidation positives; all other types remain negative/conditional.
2. **Profiles:** preserve the two existing v1 IDs and exact eligibility. Introduce the registry, cooled-only legacy normalization and explicit reason/output contract; no new positive profile.
3. **Evidence:** existing report/E01–E04; annotate observations versus modeling assumptions, without enlarging scope.
4. **Code:** proposed `reaction_temperature_profiles.py`; `reaction_conditions.assess_cooling_support()`/`cooling_confidence()`; `chemistry_server._assessment()`/`_base_assessment()`; `addition_contract.py`; `src/reaction-conditions.ts`. Preserve serialized compatibility.
5. **Tests:** exhaustive old/new assessment equivalence, all 24 types/25 models, idempotence, unknown versions/fields, conflicting permissions, API/diagram/run/calculator parity and non-cooled equivalence.
6. **Risks:** accidentally authorizing a legacy pathway, frontend/backend allowlist drift, masking stronger blockers and changing old drafts.
7. **Complete when:** two and only two existing types retain positive cooled eligibility; existing products/statuses remain equivalent; full verification passes. Stop for review.

### Phase 2 — One additional peracid profile with direct checked evidence

1. **Types:** epoxidation only; increases profile coverage, not the supported-type count.
2. **Proposed profile:** `cooled-perbenzoic-epoxidation-v1`, actual perbenzoic acid and the documented cold medium/model; initially a narrow already-eligible substrate class. Do not approve peracetic acid or all peracids.
3. **Evidence:** E05 full procedure plus independent structure/stereo applicability review. Establish whether the source solvent can be represented honestly through a named model in existing guidance. Source/example presence is not permission for every accepted alkene.
4. **Code:** registry predicate, existing peroxyacid identity metadata/assessment, guidance serializer and frontend contract. `epoxidation_rule.py`, stereo and mechanism rules should remain unchanged.
5. **Tests:** exact identity versus mCPBA/other peracids/isomers; multiple independently specified molecules within the approved class; actual benzoic-acid coproduct; oxygen maps, unchanged stereo, mechanism and calculator parity; water/extra activation negatives.
6. **Risks:** solvent assumptions broader than evidence, acid-sensitive epoxide opening and unjustified generalization beyond a single reported substrate.
7. **Complete when:** evidence and representation gates are satisfied, bounded positive/negative public workflow passes and the common gate passes. Otherwise document the remaining gate and stop. Peracetic formulation/warming stays deferred.

### Phase 3 — Validate a third type: bounded Os/H₂O₂ dihydroxylation

1. **Types:** alkene dihydroxylation only.
2. **Proposed profile:** `cooled-osmium-peroxide-diol-v1`, contingent on full review of actual H₂O₂/Os/tert-butanol chemistry and confirmed diol release. Begin without new-stereocenter claims; broaden only when independently justified.
3. **Evidence:** obtain complete E07 experimental pages; check medium, oxidation endpoint, release and competing overoxidation. Obtain additional applicable evidence before generalizing substrate or E/Z stereo scope. E07's glycol example does not settle all stereochemical questions.
4. **Code:** registry, `reaction_conditions.py` dihydroxylation assessment, condition schema/guidance metadata only if needed, public contract/UI status. Inspect `dihydroxylation_rule.py` as a dependency; do not rewrite validated transformations.
5. **Tests:** independently specified eligible simple substrates, actual oxidant/catalyst identity, required release, missing/wrong medium, overoxidation-prone negatives, stereo-boundary cases, O/H mapping, stoichiometry and public API parity.
6. **Risks:** confusing NMO with H₂O₂, false solvent compatibility, promoting an unreleased intermediate to free diol and overgeneralizing syn product certainty.
7. **Complete when:** source/formulation and current-representation gates are resolved; otherwise retain conditional 2D and no cooled 3D. No new reagent system may be smuggled into the profile.

### Phase 4 — Halogen-addition research and separately approved profiles

1. **Types:** alkene chlorination first; alkyne Br₂ first-stage and full-addition models only in later separately approved subincrements. Alkyne Cl₂ remains a separate evidence/stereo decision.
2. **Proposed profiles:** a simple-alkene Cl₂ non-capturing model; separately `cooled-alkyne-bromination-one-v1` and `...-two-v1` if direct evidence qualifies each endpoint. These are candidates, not admitted profiles.
3. **Evidence:** retrieve E09/E10 completely and verify actual cold products, initiation and medium. Locate matched cold Br₂/alkyne studies for each stage. Reject evidence for halohydrins, radical substitution or unresolved first-stage chlorine stereo as dichloride/3D proof.
4. **Code:** registry and respective condition assessors; profile-scoped `alkyne_input_evidence()` change for alkyne increments; addition contract, guidance and frontend status. Preserve `chlorination_rule.py`, `alkyne_halogenation_rule.py` and existing stereo contracts.
5. **Tests:** actual Cl/Br provenance; terminal/internal and validated E/Z/cyclic cases only within approved scope; one/two equivalents; capturing media/radical/remote nucleophile/multiple-site negatives; known unresolved substrates remain blocked.
6. **Risks:** transferring Br₂ evidence to Cl₂, missing radical chemistry, claiming cold prevents cyclization, and passing one thermal gate but failing another.
7. **Complete when:** each individual profile has direct applicable evidence, independent product/stereo oracles and the common gate. Unresolved 1,7-octadiene-like cyclization and first-stage Cl₂ stereo restrictions remain intact.

### Phase 5 — Substitution/elimination condition review, not blanket competition prediction

1. **Types:** SN2 first; then water-based SN1. E1 and E2 remain research/negative controls unless separately validated.
2. **Proposed profiles:** narrow actual-OH methyl/low-hindrance SN2 formulation; narrow actual-water screened tertiary SN1 formulation. No automatic paired E1/E2 permission.
3. **Evidence:** obtain full E13/E14 experimental and product details; distinguish kinetic feasibility from verified substitution endpoints. Require direct cold elimination-product evidence for any E1/E2 proposal.
4. **Code:** registry, `reaction_conditions.py` SN reference/condition assessment, guidance and contract. Inspect `sn1_rule.py`, `sn2_rule.py`, `e1_rule.py`, `e2_rule.py`, `carbocation_compatibility.py` and mechanism/stereo utilities without changing structural chemistry.
5. **Tests:** substrate-class and selected-site independence, actual medium/base activity, inversion/recomputed CIP, planar SN1 center, preserved distant centers, β-H/anti negatives, rearrangement/cyclization and SN1/E1/SN2/E2 consistency.
6. **Risks:** treating rates as product selectivity, approving weakly specified solvent/base conditions, and inferring cooled E1 products from SN1 ionization alone.
7. **Complete when:** each admitted substitution profile has an evidence-backed endpoint, honest competition warnings and full public/mechanism verification. Heated-reference differences alone neither approve nor prohibit elimination.

### Phase 6 — Catalyst-specific reductions, three separate increments

1. **Types:** alkene hydrogenation, Lindlar partial alkyne hydrogenation, complete alkyne hydrogenation; carbonyl hydrogenation only after its own additional review.
2. **Proposed profiles:** actual-H₂/current-metal alkene reduction; actual-H₂/Lindlar partial reduction; actual-two-H₂/current-metal full alkyne reduction; independently qualified carbonyl variant. Admit only the exact catalyst/medium scope supported by evidence.
3. **Evidence:** direct cold experiments using the actual current catalyst formulations and identified endpoints. E08 lacks cold-stage evidence; E12 uses a distinct formulation and cannot fill that gap. Resolve pressure/additive/support facts before naming a model.
4. **Code:** registry, cooled-only legacy adapter for alkene/carbonyl types, alkyne condition/input-evidence gates, guidance and public contracts. Existing hydrogenation rule modules remain validation dependencies.
5. **Tests:** one/two H₂ accounting; correct loss/retention of unsaturation; cis/Z only where already validated; catalyst/formulation negatives; reducible spectators, mixed unsaturation and over-reduction boundaries; mapped H provenance.
6. **Risks:** generic-metal selectors hiding materially different catalysts, cooling presented as guaranteed Lindlar stopping, or selective reduction inferred from a graph transformation.
7. **Complete when:** each independent increment has a matched cold endpoint and expressible conditions. If pressure/catalyst details cannot be represented in current surfaces, defer rather than guess or redesign controls without approval.

### Phase 7 — Acid-mediated addition and alcohol-substitution candidates

1. **Types:** hydration, alkene hydrohalogenation, alkyne hydrohalogenation and alcohol substitution, each separately reviewed.
2. **Proposed profiles:** direct acid/water cooled hydration; reagent-specific ionic HX addition; narrowly evidenced tertiary-alcohol/HCl substitution. No universal HX profile, radical addition or new nucleophile family.
3. **Evidence:** direct cold reaction-stage products, actual acid/HX formulation, water/solvent activity and any warm-up/work-up. Resolve E18's original source. E11 is a different mechanism and cannot qualify ionic alkyne HX.
4. **Code:** registry, corresponding existing condition assessors, alkyne input gate where applicable, guidance/contracts. Preserve hydration, hydrohalogenation, alkyne-HX and alcohol-substitution product rules and current ambient-only subprofiles.
5. **Tests:** independently justified regioisomers, retained distant stereo, consumed E/Z, unassigned new centers, H/X/O provenance, capture/rearrangement/cyclization and wrong-formulation negatives; stale profile/temperature switching.
6. **Risks:** confusing sulfate formation/hydrolysis with direct hydration; ionic/radical conflation; transferring cold tertiary HCl behavior to primary HX substitution; asserting new selectivity.
7. **Complete when:** a profile's existing graph endpoint and entire relevant condition history are supported. Otherwise keep the precise current limitation. Do not change chemistry merely to make the source fit.

### Phase 8 — Ester-family review; preserve oxidation and output boundaries

1. **Types:** esterification, acid ester hydrolysis and saponification as research priorities. Reassess secondary alcohol/aldehyde oxidation evidence only; primary aldehyde stopping, heated dehydration and finite BPO polymerization stay excluded absent separately approved modeling work.
2. **Proposed profiles:** independently documented cold acid-catalyzed esterification/hydrolysis and cold aqueous hydroxide saponification. Saponification approval can improve net/2D confidence without authorizing ionic 3D. No new primary-oxidation or dehydration profile is promised.
3. **Evidence:** matched reaction-stage products, catalyst/pH/formulation and hydrolysis/work-up distinction. Review ordinary/aryl/lactone applicability individually. E15–E17 specifically do not establish the missing cold endpoints.
4. **Code:** registry and cooled-only legacy ester adapters; public confidence/guidance contract. Existing ester, oxidation and dehydration rule modules are inspection/test dependencies, not authorized product-rule changes.
5. **Tests:** ester acid/base distinctions, ring-open connectivity, carboxylate charge, no implicit work-up, unaffected stereo, all mapped coproducts and calculator balance. Oxidation/dehydration/polymerization negatives remain explicit.
6. **Risks:** implying equilibrium completion, neutralizing ionic products for rendering, interpreting an ice bath as near-zero reaction evidence, or importing TEMPO/redox chemistry under a condition label.
7. **Complete when:** admitted profiles fit existing endpoints and outputs. Unresolved chemistry is documented as deferred, with no coverage target requiring a positive result.

### Phase 9 — Consolidated 24-type cooling acceptance review

1. **Types:** all 24, including both alcohol-oxidation models and every admitted profile/version.
2. **Profiles:** none added; freeze the reviewed manifest and accurately classify the rest.
3. **Evidence:** each admitted model has traceable sources, applicability limits and independent expected-product rationale. Rejected candidates retain reasons, not executable permissions.
4. **Code:** no chemistry expansion; inspection of shared evaluator, API serialization, guidance, UI permission and lifecycle integration. Documentation only unless a separately approved defect fix is needed.
5. **Tests:** whole matrix, condition switching/races, public endpoints, geometry failures, stereo/maps, calculators, restored drafts and desktop/mobile browsers.
6. **Risks:** reporting conditional graph matches as fully validated cold chemistry, hiding unsupported models, or conflating supported profiles with supported types.
7. **Complete when:** all types recognize cooling with an accurate reason; each admitted profile passes its contract; benchmark comparison and complete checks pass. Full 24/24 cooled 3D is **not** an acceptance target.

## 8. Testing, measurements and acceptance criteria

### 8.1 Separate versioned cooling suites

Preserve the existing `tests/test_cooling_profiles_v1.py` and `tests/cooling-profiles-v1.test.mjs` as baseline contracts. Proposed future additions are versioned v2 matrix/registry suites plus per-profile fixtures. Record profile versions and independent expected chemistry; do not regenerate expected products from the engine being tested.

The matrix must include every `DEFINITIONS` type and both primary/secondary oxidation models. For each model, exercise missing, supported, incompatible and unreviewed settings rather than one convenient positive sample.

Required test groups:

- **Identity/site:** exact reagent graph; wrong isomer/formula/name; valid and invalid sites; branch/ring/remote-group/multi-site boundaries; current size and element limits.
- **Conditions:** cooled/ambient/heated/unset, actual solvent/catalyst conflicts, stages/equivalents/release, unsupported fields/profile versions, known unrelated selectors marked not applicable.
- **Outputs:** public match/diagram/run agreement; visibly conditional previews; failed conditions never authorize 3D; geometry failure is not a chemistry conclusion.
- **Chemistry:** independent connectivity/charge/valence/atom balance; mapped H/X/O provenance; byproducts and full stoichiometry; no silent acid work-up or removed spectator.
- **Stereo:** existing validated product relationships, reacting-center changes, independently recomputed CIP and retained physical distant configuration; arbitrary coordinates cannot create certainty.
- **Mechanism/calculator:** supported steps and electron moves remain consistent; absent full mechanisms stay absent; theoretical amounts reflect current profile and never imply actual yield.
- **Lifecycle:** immediately invalidate all dependent results on any input/profile/temperature change; test late match/diagram/run responses and restored obsolete drafts.
- **Frontend/backend:** reject contradictory permission flags, unknown reviewed-manifest versions and forged profile IDs. Guidance is advisory; backend independently validates every run.
- **Browser:** existing desktop and mobile layout, keyboard/status announcements, actual reactant selection, profile application, 2D/3D/Compare, mechanisms and calculator reset. No visual redesign.

### 8.2 Required gate after every implementation increment

1. Run all existing Python tests with the project's `.venv` and all JavaScript tests using the established runner. Preserve every prior passing case; the recorded starting floor is **4,040**, then ratchet the baseline upward.
2. Run the focused versioned cooling, public API, mechanism/mapping and calculator suites.
3. Run TypeScript and the production build (`pnpm run build` currently runs `tsc && vite build`); record existing warnings separately from failures.
4. Run browser checks, including temperature transitions and stale-response races, on isolated local services.
5. Run the unchanged `scripts/audit_reaction_lab.py`; compare all 347 IDs, inputs, expected/actual products, per-case statuses and totals. A changed source fingerprint alone is not a benchmark improvement.
6. Run separately documented condition-aware replays and reviewed cooling fixtures. Do not overwrite `benchmarks/reaction-conditions/1.0.0.json` or frozen expectations; use a new pinned version if a future benchmark artifact is approved.
7. Check whitespace and review the diff for unrelated changes, curated-example edits, product-rule changes and local secrets. No push/deployment is part of any phase without separate authority.

An unexpected benchmark change must be investigated before completion. Do not repair expectations to hide an engine defect or apply a known benchmark erratum silently.

### 8.3 Reporting that avoids misleading zero scores

Report these dimensions independently:

| Measurement | What it means |
| --- | --- |
| Structural compatibility | Existing rule/site matcher can represent the candidate transformation. |
| Condition completeness | Required profile information is present and consistent. |
| Reviewed cooled applicability | Evidence-backed model covers that reagent/substrate/condition scope. |
| Supported product generation | Independent expected graph/stereo/mapping agrees with generated output. |
| Theoretical 3D availability | Qualified product plus successful geometry under current output policy. |
| Rejection / unresolved category | Missing information, current-profile conflict, unreviewed evidence, unsupported endpoint, competing chemistry, geometry failure or actual incorrect chemistry. |

Give counts with denominators for **24 types**, **25+ model fixtures** and **reviewed profile cases** separately. Keep the frozen347 strict result and condition-aware replays labeled separately. No cooled rows in the frozen benchmark means it cannot establish cooling success or failure. A charged endpoint or an unreviewed condition is not automatically an incorrect reaction.

## 9. Risks and unresolved questions

1. **Broad selectors conceal formulation.** “Dry,” “metal” and “acid” do not encode actual solvent, support, pH or concentration. Named model assumptions may suffice for a bounded educational net model; cases needing actual user-supplied detail must remain conditional until separately approved inputs exist.
2. **A cold bath is not a measured cold reaction.** Source annotations must distinguish the reacting mixture from addition control, catalyst manufacture, receivers, quenching and crystallization.
3. **Cold changes competition, not just speed.** Existing rules do not predict rates, proportions, extent or thermal histories. Do not claim that a lower temperature suppresses every rearrangement, capture or competing pathway.
4. **Source scope is narrower than graph scope.** Keep evidence for exact experiments distinct from generalized eligibility inference. Multiple software fixtures are necessary but not experimental validation.
5. **Layered gates can drift.** Registry, legacy assessments, alkyne guards, public evidence and frontend wording must agree. Stronger blockers and non-cooled behavior must survive consolidation.
6. **Endpoint/output gaps are not temperature gaps.** Primary-alcohol aldehyde stopping, acid/carboxylate reporting, ionic geometry and finite-polymer initiation need different work. Do not force them into cooling development.
7. **Stereochemical certainty is independent.** A successful conformer is one geometry, not a validated face population, mixture ratio or low-temperature stereochemical mechanism.
8. **Some evidence is not yet fully accessible.** Full-text gates in E07, E09–E10 and E14 remain real work. An abstract or historical citation is a research lead, not approval.
9. **No justified universal numerical range exists.** Named profiles should come first. Numeric input, if later useful, requires its own data semantics, evidence and approval—not cosmetic precision.

## 10. Recommended implementation order and first decision

The roadmap prioritizes correctness and low-risk reuse before breadth:

**Phase 1 → Phase 2 → Phase 3**, then evidence-gated individual increments from Phases 4–8, followed by Phase 9. The later ordering may change when stronger primary evidence is obtained; no unsupported candidate should be promoted merely to follow a schedule.

Perbenzoic epoxidation is the strongest accessible low-risk profile extension, but it remains the same reaction type. Os/H₂O₂ dihydroxylation is the most promising identified route to a third cooled type; it needs full formulation/source and existing-model compatibility review first. Chlorination and hydrogenation must not inherit cooling permission from visually similar pathways.

**Implement Phase 1 first: behavior-preserving registry and confidence-contract consolidation for the two existing profiles.** It addresses duplicated permissions, legacy-assessment gaps and frontend/backend drift before new chemistry increases the risk. Its success criterion is equivalent existing behavior, not more positive reactions.

After that phase is reviewed, approve one bounded chemistry increment at a time. This plan authorizes none of them and stops here for the user's decision.
