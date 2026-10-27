# Reaction Lab tool placement — 2026-10-08

The layout and chemistry engine are unchanged. Tools now appear where their
context belongs:

- Standalone solution calculations live on **Calculators → Solutions**, not in
  a second embedded calculator in Reaction Lab. Explorer's existing calculator
  remains available.
- Each resolved Reaction Lab molecule has a compact **Use in Calculators**
  shortcut. It transfers the exact compound/structure to Solutions and saves
  the reaction draft before navigation. Ambiguous or unrecognized inputs do not
  offer a shortcut. Full salt masses are preserved; unreviewed masses require
  manual entry. Formula matches never substitute a compound or its mass.
- Alkyne addition equivalents and finite chain length stay in Reaction Lab,
  beside matching pathways. They are hidden until the structural matcher returns
  a relevant pathway. Alkyne halogenation/hydrohalogenation shows equivalents
  only; polymerization shows chain length only. Hydrogenation and unrelated
  reactions show neither. Input changes hide stale controls immediately.
- Functional-group/stereochemistry inspection stays optional and collapsed in
  Reaction Lab. Reaction-specific amounts stay beside the selected equation.

The shared calculator transfer format also supports Reaction Lab sources; the
Calculators compound selector no longer mislabels these as coming from Explorer.
Storage failures provide a short manual-entry fallback without silently
transferring another compound.

Verification: 194 Python and 360 JavaScript tests pass (554 total), including
seven new transfer/contextual-control checks. TypeScript, production build and
whitespace checks pass. No chemistry rules, hosting or publication were changed.
