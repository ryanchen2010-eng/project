# Hosted beta smoke test — 2026-10-20

## Outcome and scope

**Passed the representative live-browser smoke test; no blocking failure observed.** Website: https://molecule-playground-beta-v1.onrender.com/. The user signed in privately before testing. The deployed dependency-patch commit is `1f5a9a579e8d4bd7312932555060ccbbc926e480` (verified during the preceding startup check).

Tests used the authenticated Chrome session, actual page controls, rendered structures, public application workflows and the hosted chemistry service. This was not a rerun of all reaction pathways, the 347-case benchmark or the entire automated regression suite. Finite smoke-test success is not a claim of universal chemistry correctness.

## Checks and observed results

| Area | Test | Observed result |
| --- | --- | --- |
| Home/authentication | Navigate through all five pages and refresh Home | Pages load while remaining signed in; no login loop |
| Explorer | Default water model | Visible 3D water; information panel populated |
| Explorer measurement | O1 to H2 using atom list | 0.969 Å, labeled displayed-model geometry rather than experimental measurement |
| PubChem | Search acetophenone, outside the 18 Explorer samples | One exact structure; C8H8O, 120.15 g/mol, 3D ready; unreviewed properties identified as such |
| Explorer reset | Change compounds after measurement | Selection and old result clear; measurement mode returns to Off |
| Ionic handling | Search sodium chloride | Information-only state explicitly says no 3D diagram; full formula mass 58.443 g/mol; no fake discrete molecular model |
| Cross-page identity | Explorer → Open in Calculators | Sodium chloride identity, full mass and ionic formula-unit entity carried across |
| Moles | 58.443 g NaCl | 1 mol; 6.02214e+23 formula units at displayed precision |
| Stale calculation | Change input after mole calculation | Old answer disappears immediately |
| Solutions | 5.8443 g NaCl, final volume 100 mL | 0.1 mol and 1 mol/L; solubility is not claimed |
| Equilibrium | Default symbolic 1:1 dissolved A ⇌ B, concentrations 0.25 and 0.5 mol/L, user balance confirmation | Q = 2; ideal, temperature and standard state shown |
| Undefined quotient | Set reactant concentration to zero | Explicit zero-denominator/undefined finite quotient explanation, not an invented finite value |
| Acid/base | Strong monoprotic acid, 0.001 mol/L, entered Kw = 1e-14 at 25 °C | pH 3, pOH 11; H+ 0.001 mol/L, OH− 1e-11 mol/L; spectator included |
| Temperature invalidation | Change acid/base temperature to 30 °C | Kw and old result clear |
| Solubility | Generic 1:1 salt, charges +1/−1, Ksp = 1e-10, no initial common ions | Additional dissolved salt 0.00001 mol/L; each ion 0.00001 mol/L |
| Builder | Draw cyclohexane using Ketcher's ring tool, not the app ethanol example | Hosted validation and 3D generation succeed: C6H12, 84.162 g/mol, 18 atoms and 18 bonds including H, Passed, MMFF94 |
| Builder transfer | Use drawn structure as molecule 1 | Reaction Lab receives `Drawn structure · C6H12` |
| Negative reaction | Drawn cyclohexane + hydrogen | No supported pathway; no fabricated product; wording does not claim chemical impossibility |
| SN2 sample | Bromomethane + hydroxide in the model conditions | Correct displayed methanol + bromide net equation, visible 2D and 3D product, explicit condensed-vs-molecular-formula explanation |
| Mapped atom interaction | Select carbon in 2D, then oxygen directly in the 3D canvas | Corresponding reactant/product atoms selected in 2D; matching 3D halo/label; atom identity text updates in both directions |
| SN2 mechanism | Open Mapped mechanism | One concerted step; atoms 1–6 forming, 1–2 breaking; lone-pair and leaving-group electron moves; no inserted carbocation |
| Reaction calculator | 94.939 g bromomethane + 34.014 g hydroxide | Bromomethane limiting, 1 mol/32.042 g theoretical methanol, 1 mol/17.007 g hydroxide remaining |
| Input reset | Change reaction example after generating SN2 | Previous product, selection and amounts removed |
| Guided oxidation gate | Load 2-propanol/NaOCl example with generic water and incomplete settings | Conditional 2D only; 3D and Compare disabled; missing model fields identified |
| Guided replacement | Review proposed medium/temperature/activation/stage replacements and confirm | Fields update to the bounded profile; confidence becomes theoretical 3D, not guaranteed experimental outcome |
| Guided oxidation run | Request 3D with condition-complete bounded profile | Acetone ready as a conditional net-model structure; mapping includes salt and water; qualifications remain visible |
| Generalized chemistry | Import 1-bromopentane from PubChem; pair with hydroxide in polar aprotic model | SN2 and E2 options exposed separately; SN2 generates C5H12O + bromide and a 3D product; no exact pathway ratio claimed |
| Mobile page width | All five pages, 320 × 800 CSS viewport | Document and body widths 320; no page-level horizontal overflow in inspected states |
| Mobile tools | Mobile topic selector → Reaction amounts; choose catalog hydrogenation | Selector works; supported reaction catalog loads |
| Mobile calculation | 28.054 g ethene + 4.032 g H2 | Ethene limiting, 30.07 g/1 mol theoretical ethane, 2.016 g/1 mol H2 remaining; width still 320 |
| Browser diagnostics | Captured warning/error log review | No site-origin warning/error entries in the captured log; unrelated Grammarly extension warnings excluded |

## Non-blocking usability observations

1. Generated products can retain generic names such as **Alcohol product** or **Organic product**, even when structure and formula are available. Showing a validated name, or a clearer structural identifier, would help users distinguish products. No naming change made.
2. The curated **Oxidize 2-propanol** card initially selects generic water and leaves several bounded-profile settings missing. The guided review corrects these settings successfully, but an immediate conditional result can confuse first-time users. A clearer example-card hint or reviewed preset could improve usability without weakening the condition gate. No condition rule or curated example changed.
3. Two propene bromination entries in the calculator selector have the same visible generic product wording. This test did not establish whether they represent distinct stereochemical alternatives, so this is a labeling observation, not a confirmed duplicate-chemistry defect.

## Limits and preservation

- No production code, chemistry rules, benchmark, deployment settings, secrets or curated examples modified. Runtime hashes compared with the 107-file dependency-patch snapshot: **zero differences**.
- Original Git index SHA-256 preserved: `2c75388cd6edf8bab2ad85639ead733ade239f5b06e01cdfef875418108cbdde`.
- Test inputs and the drawn cyclohexane used normal session-level application storage; no unrelated stored data was deleted. The browser was returned to Home and the temporary viewport override was reset.
- Not exhaustively checked today: all 24 pathways, every stereochemical edge case, every advanced calculator mode/activity model, every mobile state, touch behavior on a real phone, rapid hover smoothness, long-running/load behavior, cold-start timing, accessibility/screen-reader conformance and session expiry.
- Prior local dependency-patch verification was 3,766 automated tests plus TypeScript/production build. Those were not rerun during this browser-only test.

## Evidence

- `beta-test-explorer-2026-10-20.png`
- `beta-test-builder-2026-10-20.png`
- `beta-test-reaction-compare-2026-10-20.png` — mapped carbon visibly linked in 2D and 3D
- `beta-test-mobile-home-2026-10-20.png`
- `beta-test-mobile-calculator-2026-10-20.png`

## Recommendation

Proceed with a small password-protected friend beta. Share the website URL and trial password privately, never the session secret. Collect specific reproducible inputs, selected pathway/conditions, expected behavior and actual result. Address confirmed defects in a new reviewed increment rather than modifying the frozen release silently.
