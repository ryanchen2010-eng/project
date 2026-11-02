# Reaction Lab: pathway reasoning and mapped mechanisms

Local implementation, October 7, 2026. The existing two-panel layout, structural reaction engine, selected-site options, linked atom inspection, measurements and calculators are retained. No publication or GitHub push.

## 1. New reasoning rules

`server/reaction_reasoning.py` reads molecular graphs and validated selected conditions. Factors include functional group/site, substrate class, leaving group, sterics, carbocation support, beta H, nucleophile/base, geometry limitations, reagent roles, oxidation stage, solvent, temperature and catalyst.

Each option has a collapsed **Why This Pathway?** list. **Strong match**, **Possible**, **Unfavorable** and **Unsupported** describe fit within the implemented model, not percentages, rates or predicted conversion. Missing required settings, unmodeled extra catalysts and secondary SN2 are cautious; profile mismatches are unfavorable but do not prove impossibility. E2 remains Possible even when its illustrative condition profile fits because anti-periplanar feasibility is unverified.

The comparison panel copies those exact factor records; no separate scoring table or LLM is involved. It can render any number of supplied candidates, including four columns. The current OH/water reagent scope ordinarily provides **SN2/E2** or **SN1/E1**, not all four for an arbitrary pair. It does not manufacture unsupported choices for comparison.

## 2. Implemented mechanisms

`server/reaction_mechanisms.py` uses the engine's global map IDs and selected mapped net products. Every step preserves atoms, elements and net charge, sanitizes its state, and checks electron endpoints. The final main product must exactly agree with the selected net product.

| Type | Elementary steps | Actual intermediates |
| --- | --- | --- |
| SN2 | One concerted nucleophilic attack / C–O formation / C–X cleavage | None |
| E2 | One concerted base attack at the selected beta H / C=C formation / C–X cleavage | None |
| SN1 | Ionization; water capture; explicit solvent-water proton transfer | Carbocation, then oxonium |
| E1 | Ionization; coupled beta-H removal and C=C formation | Carbocation |

E1 has **two**, not three artificial elementary steps: proton removal and pi-bond formation are coupled in the second step. The carbocation is explicitly an **Intermediate**, never a transition state.

`src/pathway-insights.ts` renders step controls, exact role IDs, intermediate/product-state Lewis depictions, electron source/destination buttons and a qualitative barrier/intermediate sequence. Orange source/teal destination/purple shared endpoints are independent of existing hover/pin and amber site markers. Actual retained product atoms are highlighted in 3D; absent leaving groups, solvent or coproduct atoms receive no guessed 3D location.

## 3. Mechanism limitations

- Curved-arrow geometry is not implemented; exact electron endpoints and highlighting are implemented.
- Intermediate depictions are 2D only. The existing 3D view remains the **final main product**, not a carbocation or transition-state geometry.
- SN1/E1 use explicit solvent water for proton removal and depict released acid as hydronium/halide. Existing net equations may display HX. Mechanism-only solvent does not alter net stoichiometric/calculator quantities.
- No inversion, racemization, E/Z assignment, rearrangement, conformational/anti-periplanar validation, rate or numerical activation energy.
- Energy metadata is qualitative topology only. Ionization is the textbook assumed rate-limiting step for the supported SN1/E1 model, not an experimentally determined barrier.

## 4. Oxidation changes

The conditions form adds **Oxidation stage** without changing the layout. First stage supports methyl/primary alcohol → aldehyde connectivity and secondary alcohol → ketone. Tertiary alcohols remain excluded.

An actual aldehyde + supported alkali hypochlorite now has an **Aldehyde oxidation** rule only when **Further oxidation** and **Water · polar protic** are explicitly selected. A mapped formyl H moves to introduced oxidant oxygen, the acid OH forms, and full spectator chloride is retained. The displayed acid is the neutral **reporting structure**, not a prediction of solution protonation or isolated product. An ordinary ketone does not match. Choosing Further oxidation on a primary alcohol does not skip directly to acid.

This is a balanced net-stage model, not an aldehyde oxidation mechanism, universal oxidant selector or laboratory procedure. Reagent/conditions, other reactive groups and solution chemistry affect actual outcomes. No household-chemical mixing instructions are provided.

Further oxidation remains labeled **Possible** even when the stage/medium fit: the tool does not validate a reagent/pH/catalyst protocol or exclude halogenation. The primary hypochlorite reference below uses a specific catalytic system; it does not establish that every uncatalyzed aldehyde/bleach mixture gives a clean acid product.

## 5. Verification

Added **18 Python tests** and **8 JavaScript tests**, keeping the original 450 checks. Coverage includes deterministic/name-independent facts, exact comparison reuse, primary/secondary/tertiary SN2, beta-H requirement and both 2-bromobutane E2 products, mapped carbocation/oxonium charges, explicit proton transfer, coupled E1 elimination, no invented other-family mechanisms, oxidation stages, multiple aldehydes, full salt mass, mapped/3D product reuse, stale condition rejection, safe DOM text, four-column rendering, exact 3D correspondence, independent highlight cleanup and page integration.

Full count: **476 checks (140 Python + 336 JavaScript)**, plus TypeScript, production build and whitespace validation. Live browser verification covers the four mechanisms, exact mapped source/destination selection, reaction-condition invalidation, staged oxidation and responsive containment.

## 6. Remaining chemistry boundaries

All previous [structural-engine boundaries](reaction-engine-coverage.md) remain. No unrestricted reaction prediction, quantitative selectivity, mixtures, enzyme catalysis or organometallic mechanisms. **Acid + amine is still not automatically amidated**; activation/dehydration and acid–base salt formation need separate future models. Mechanisms for addition, reduction, esterification, hydrolysis and oxidation are not added by this extension, even though their net pathways remain usable.

## Primary references

- [OpenStax SN2](https://openstax.org/books/organic-chemistry/pages/11-2-the-sn2-reaction), [SN1](https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction).
- [OpenStax E2](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect), [E1](https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions).
- [OpenStax alcohol oxidation](https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols), [aldehyde/ketone oxidation](https://openstax.org/books/organic-chemistry/pages/19-3-oxidation-of-aldehydes-and-ketones).
- [ACS: catalytic hypochlorite oxidation of alcohols and aldehydes](https://pubs.acs.org/doi/abs/10.1021/jo0612574). Used for oxidant context and limitations, not a claimed uncatalyzed protocol.
