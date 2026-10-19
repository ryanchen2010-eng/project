# Reaction Conditions Companion

Run alongside, never instead of, the frozen 347-case audit:

```sh
.venv/bin/python scripts/reaction_conditions_companion.py
.venv/bin/python scripts/reaction_conditions_companion.py --diagnostic
.venv/bin/python scripts/reaction_conditions_companion.py --compare 1.0.0 --version 1.0.0
```

Output is JSON on stdout. Redirect to a **new** result artifact; never replace historical artifacts. Default runs only admitted overlays; `--diagnostic` explicitly applies draft overlays and labels their results unvalidated. The initial scope is 53 original positives plus five controls (58 rows), with all 347 parent identities checksum-bound. The remaining 289 are outside profile review, not certified. Case IDs, actual reagent identities, existing conditions and frozen expectations cannot be replaced by an overlay.

## Evidence gate

Version 1.0.0 is deliberately a draft catalogue: **zero approved profiles**. The 53 positives remain 52 evidence gaps and one unsupported engine model (A255, actual NMO). The original family-specific 0/21, 0/21 and 0/11 strict scores and distinct replay-generation / old-scorer results are historical diagnostics, not new validated coverage.

Admission requires primary evidence with exact location and rationale; explicit independent reviewer/date/assertion-scope sign-off; all ten condition dimensions specified or justified not applicable; and a separate case-specific applicability review covering substrate, sites, competing chemistry and stereochemistry. Unknown fields cannot count as complete. Generation and test passes do not provide approval. This validates recorded evidence completeness; scientific review must still establish that the evidence actually applies.

A separately reviewed product oracle must independently specify all allowed products, byproducts, mapping contract and stereo uncertainty. A304's defect is annotated, not silently fixed. Any corrected companion oracle needs an explicit erratum version and approval; the frozen parent remains untouched.

## Four metrics

All metrics count original positive **cases**, not options/faces/aliases. Each pathway and overall scope reports an explicit denominator:

1. Structural matching: at least one net option from the actual selected reagent model.
2. Condition-complete eligibility: matched case with independently admitted profile **and case applicability**.
3. Fully supported product generation: admitted case whose diagrams, mapping, balance and all 3D options pass, and whose independently reviewed product set agrees.
4. Independently verified chemistry: admitted case agreeing with its independent oracle in the stated scope; a conditional uncertainty-aware 2D set can pass this narrower question without permission to assert a single 3D outcome.

`diagnosticModelGenerationOnly` is a separately named observation, not one of the validated metrics. Controls, policy blocks, oracle defects, generation errors and profile backlog remain individually observable. No metric represents experimental success, safety, conversion, rates or product ratios.

Results identify the engine by a content fingerprint, profiles by manifest version, and independent oracles by their explicit status/erratum version. A reviewed oracle mismatch is reported as `failed-independent-oracle` and a nonzero command exit, not as an unreviewed case. A known frozen-oracle defect remains a separate annotation.

## Versioning

Never overwrite `1.0.0.json`. Add a new semantic-version file, append its SHA-256 pin to `index.json`, retain all parent digests/IDs and historical diagnostics, and document reviewer-approved condition/oracle changes. The loader rejects changed bytes and identities. `--compare OLD --version NEW` reports changed case bindings, profiles and defect annotations without running chemistry. Version pins are reproducibility controls, not cryptographic signatures or substitutes for scientific review.

Profiles for named alternative media/formulations need independent reagent-, stage- and substrate-specific validation. None are admitted by this phase. In particular, NMO evidence cannot certify Os/H2O2; dry does not prove non-nucleophilicity; ambient is not a universal kinetic boundary. Dihydroxylation production behavior is unchanged.
