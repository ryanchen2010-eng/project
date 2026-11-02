# Thermochemistry scientific accuracy audit

## Independently checked examples

| Mode | Inputs | Independently worked result |
| --- | --- | --- |
| Specific heat | 100 g; 4.184 J/(g K); 20 to 30 °C | q = 4,184 J |
| Heat capacity | 2 kJ/K; 300 K to 20 °C | ΔT = −6.85 K; q = −13.7 kJ |
| Reaction ΔH° | H₂(g) + Cl₂(g) → 2 HCl(g), ΔHf° HCl = −92.3 kJ/mol, elements 0 | −184.6 kJ per reaction as written; reverse +184.6 kJ. [OpenStax](https://openstax.org/books/chemistry-2e/pages/5-3-enthalpy) |
| Reaction ΔS° | Illustrative values: 2 reactant × 10, product × 50 J/(mol K) | +30 J/(mol reaction K); this is an arithmetic fixture, not a database claim |
| Gibbs | ΔH = 10 kJ/mol; ΔS = 100 J/(mol K); T = 300 K | ΔG = 10 − 300 × 0.1 = −20 kJ/mol; illustrative inputs |

Desktop and 320px browser checks cover mixed K/°C, g/kg and J/kJ conversions, negative and zero temperature changes, below absolute zero, missing data, zero ΔH, and stale-result clearing. Fractional and invalid coefficients and nonfinite values have unit tests. ΔH = 0 is classified neither exothermic nor endothermic. A separate check rejects unknown species sides. Output formatting rounds to at most seven significant digits; it does not infer measurement precision or uncertainties, and the user is told to apply them independently.

Standard-state and actual-condition results are not interchangeable: ΔG° alone does not determine direction under arbitrary concentrations or pressures. The calculator does not calculate reaction quotient, verify equation balance, retrieve data, or adjust ΔH/ΔS for temperature or phase changes. Refer to [OpenStax on Gibbs free energy](https://openstax.org/books/chemistry-2e/pages/16-4-free-energy).

Within these defined models and disclosed limitations, the calculator is suitable to mark complete for the current scope; this is not a claim of universal thermodynamic prediction.
