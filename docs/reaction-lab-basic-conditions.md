# Reaction Lab: Base / Basic Conditions

The `base` selector identifies the already selected hydroxide reactant in the existing supported SN2, E2 and ester-saponification models. It does not add a molecule, change solvent, supply a base catalyst, establish pH, predict selectivity or expand structural or cooling eligibility. Hydroxide must be selected as an actual reactant. In SN2 it is the consumed nucleophile, in E2 it accepts a proton in the formal net reaction, and in saponification it is a consumed reagent that leads to the carboxylate. Existing salt handling and 2D-only ionic-product policy remain unchanged. [SN2](https://openstax.org/books/organic-chemistry/pages/11-2-the-sn2-reaction), [E2](https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect), [saponification](https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters).

## Review of all 24 existing rule types

“Not validated” means this implementation does not model that base-selected combination; it does not assert chemical impossibility. Conditions and reagents for the existing models remain authoritative.

| Rule type | Base selection in the present model |
| --- | --- |
| SN2 | Supported only with the actual, structurally validated hydroxide reactant; hydroxide is the nucleophile. |
| E2 | Supported only with actual hydroxide and a validated elimination site; hydroxide is a consumed proton acceptor. |
| Ester saponification | Supported only with actual hydroxide and a validated ester site; hydroxide is consumed and the carboxylate remains charged. |
| SN1, E1 | Not validated as base-selected models; current supported water solvolysis/elimination is not changed to hydroxide chemistry. |
| Hydrogenation, carbonyl hydrogenation | Base-selected catalyst/medium interaction not validated; actual H2 and the existing metal-specific models remain required. |
| Hydration, hydrohalogenation | Base is not a substitute for the required acid activation or actual HX. |
| Bromination, chlorination, epoxidation, alkene dihydroxylation | Base-selected capture, catalyst and product compatibility is not validated by existing neutral/oxidant-specific models. |
| Alcohol oxidation, aldehyde oxidation | Added basic conditions do not establish the current oxidant formulation, aldehyde stopping point or neutral-acid work-up. |
| Esterification, ester hydrolysis | Basic conditions do not replace the acid/water model or silently change it into saponification. |
| Alcohol dehydration, alcohol substitution | Basic conditions do not replace acid activation or HX; no base-catalyzed alcohol transformation is added. |
| Alkyne hydrogenation, alkyne partial hydrogenation | Base does not replace actual H2, an active metal or a selective Lindlar catalyst. |
| Alkyne halogenation, alkyne hydrohalogenation | Base-selected chemistry is not validated for the existing X2 or ionic HX stage models. |
| Polymerization model | Base is not the modeled radical initiator. |

The unsupported selections remain conditional 2D where the existing structure matcher can produce a net diagram; the backend blocks asserted 3D. This conservative policy does not imply all base chemistry is unsupported outside the specific current models.
