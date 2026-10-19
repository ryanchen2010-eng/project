"""Atom-mapped elementary-step models for the supported OH/water SN/E rules.

No name recognition and no invented stable concerted intermediate. Solvent
water is explicit for proton transfers; it is not added to net stoichiometry.
"""
from rdkit import Chem
if __package__:
    from .stereochemistry import invert_sn2
    from . import sn2_rule, e2_rule, sn1_rule, e1_rule
    from .reaction_diagrams import (_species, _combine, _index, _remove, _add, _order, _charge,
                                   _finish, _identity, _changes, _molecule_svg)
else:
    from stereochemistry import invert_sn2
    import sn2_rule, e2_rule, sn1_rule, e1_rule
    from reaction_diagrams import (_species, _combine, _index, _remove, _add, _order, _charge,
                                  _finish, _identity, _changes, _molecule_svg)


def endpoint(kind, *maps):
    return {"type": kind, "atomMaps": list(maps)}


def electron_move(identifier, source, destination, description):
    return {"id": identifier, "source": source, "destination": destination, "description": description}


def validate_step(before, after):
    Chem.SanitizeMol(after)
    def atoms(mol):
        return {a.GetAtomMapNum(): (a.GetAtomicNum(), a.GetIsotope()) for a in mol.GetAtoms()}
    if (atoms(before) != atoms(after) or len(atoms(after)) != after.GetNumAtoms()
            or sum(a.GetFormalCharge() for a in before.GetAtoms()) != sum(a.GetFormalCharge() for a in after.GetAtoms())
            or any(a.GetNumRadicalElectrons() or a.GetNumImplicitHs() for a in after.GetAtoms())):
        raise ValueError("Invalid mapped intermediate; no mechanism may be displayed.")


def molecule_record(mol, name, kind):
    item = {"name": name, "mol": mol}
    drawing = _molecule_svg(item, [], "mechanism state", 0, set(), 560, 230)
    return {"kind": kind, "name": name, "mappedSmiles": Chem.MolToSmiles(mol),
            "atoms": [{"mapId": a.GetAtomMapNum(), "element": a.GetSymbol(), "formalCharge": a.GetFormalCharge()}
                      for a in mol.GetAtoms()],
            "bonds": [{"atomMaps": [b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()],
                       "order": b.GetBondTypeAsDouble()} for b in mol.GetBonds()],
            "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 230" role="img" aria-label="' + name + '">' + drawing + '</svg>'}


def build_mechanism(reaction, catalog):
    mechanism = reaction["mechanism"]
    if mechanism == "Epoxidation":
        if __package__:
            from .epoxidation_mechanism import build
        else:
            from epoxidation_mechanism import build
        return build(reaction, catalog)
    if mechanism not in {"SN1", "SN2", "E1", "E2"}:
        return None
    inputs, next_map = [], 1
    for identifier in reaction["equationReactants"]:
        item, next_map = _species(identifier, catalog[identifier], next_map); inputs.append(item)
    substrate = inputs[0]["mol"]
    site = reaction["site"]["substrateAtoms"]
    carbon, leaving = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]]
    params = Chem.SmilesParserParams(); params.removeHs = False
    outputs = [{"mol": Chem.MolFromSmiles(smiles, params)} for smiles in reaction["mappedProducts"]]
    initial = _combine(inputs)
    net_changes = _changes(inputs, outputs)
    roles = {"electrophilic-carbon" if mechanism.startswith("SN") else "alpha-carbon": carbon, "leaving-group": leaving}
    solvent_species = []
    if mechanism in {"SN1", "E1"}:
        solvent, next_map = _species("mechanism-solvent-water", {"name": "Solvent water", "smiles": "O"}, next_map)
        initial = Chem.CombineMols(initial, solvent["mol"])
        base = next(a.GetAtomMapNum() for a in solvent["mol"].GetAtoms() if a.GetSymbol() == "O")
        solvent_species = [{"role": "proton-transfer solvent", "atomMaps": [a.GetAtomMapNum() for a in solvent["mol"].GetAtoms()],
                            "note": "Explicit water for the mechanism only; not an extra consumed net-equation reactant."}]
    else:
        base = next(a.GetAtomMapNum() for a in inputs[1]["mol"].GetAtoms() if a.GetSymbol() == "O")
    if mechanism in {"SN1", "SN2"}:
        nucleophile = next(a.GetAtomMapNum() for a in inputs[1]["mol"].GetAtoms() if a.GetSymbol() == "O")
        roles["nucleophile"] = nucleophile
    if mechanism in {"E1", "E2"}:
        beta = substrate.GetAtomWithIdx(site[2]).GetAtomMapNum()
        transfer = next(c for c in net_changes if c["kind"] == "broken" and beta in c["atomMaps"] and "H" in c["atoms"])
        beta_h = next(m for m in transfer["atomMaps"] if m != beta)
        roles.update({"base": base, "beta-carbon": beta, "beta-hydrogen": beta_h})
    steps, state = [], Chem.Mol(initial)
    def step(title, description, editor, moves, intermediate_name=None):
        nonlocal state
        after = _finish(editor)
        validate_step(state, after)
        if mechanism == "SN1":
            stage = {"Ionization": "ionization", "Nucleophilic capture": "capture", "Proton transfer": "deprotonation"}.get(title)
            if stage is None:
                raise ValueError("An SN1 mechanism must keep its distinct ionization/capture/deprotonation stages.")
            sn1_rule.validate(state, after, substrate, inputs[1]["mol"], site, stage, solvent["mol"])
        elif mechanism == "E1":
            stage = {"Ionization": "ionization", "Elimination": "elimination"}.get(title)
            if stage is None: raise ValueError("E1 must retain separate ionization and beta-H elimination stages.")
            e1_rule.validate(state, after, substrate, site, stage, solvent["mol"])
        changes = _changes([{"mol": state}], [{"mol": after}])
        known = {a.GetAtomMapNum() for a in state.GetAtoms()}
        if any(not set(e["atomMaps"]) <= known for move in moves for e in (move["source"], move["destination"])):
            raise ValueError("Mechanism references an absent atom.")
        for move in moves:
            source = move["source"]
            if source["type"] == "bond" and (len(source["atomMaps"]) != 2 or state.GetBondBetweenAtoms(*[_index(state, m) for m in source["atomMaps"]]) is None):
                raise ValueError("An electron source bond must exist before the step.")
        record = molecule_record(after, intermediate_name or "Mechanism products", "Intermediate" if intermediate_name else "Product state")
        steps.append({"id": f"{mechanism.lower()}-step-{len(steps) + 1}", "title": title, "description": description,
                      "concerted": mechanism in {"SN2", "E2"} or title == "Elimination",
                      "electronMoves": moves, "beforeState": molecule_record(state, "Before this step", "Starting state"),
                      "protonTransfers": [c for c in changes if "H" in c["atoms"] and c["kind"] in {"formed", "broken"}],
                      "bondsFormed": [c for c in changes if c["kind"] == "formed"],
                      "bondsBroken": [c for c in changes if c["kind"] == "broken"],
                      "bondOrderChanges": [c for c in changes if c["kind"] == "order"],
                      "intermediate": record if intermediate_name else None, "state": record})
        state = after
    departure = electron_move("departure", endpoint("bond", carbon, leaving), endpoint("atom", leaving), "The C–leaving-group electron pair goes to the leaving group.")
    if mechanism in {"SN1", "E1"}:
        editor = Chem.RWMol(state); _remove(editor, carbon, leaving); _charge(editor, carbon, 1); _charge(editor, leaving, -1)
        if mechanism == "SN1":
            sn1_rule.unassign_reacting_center(editor, carbon)
        elif mechanism == "E1":
            e1_rule.apply_stereo(editor, e1_rule.participants(substrate, site, "ionization", solvent["mol"]))
        step("Ionization", "Heterolytic leaving-group departure forms the mapped carbocation. This is an intermediate, not a transition state." +
             (" The reacting center is planar/unassigned; a benzylic/allylic drawing is one formal resonance contributor, not a localized charge-density prediction." if mechanism in {"SN1", "E1"} else ""), editor, [departure], "Carbocation intermediate")
    if mechanism == "SN2":
        editor = Chem.RWMol(state); _remove(editor, carbon, leaving); _add(editor, carbon, nucleophile)
        _charge(editor, nucleophile, 0); _charge(editor, leaving, -1)
        invert_sn2(state, editor, carbon, leaving, nucleophile)
        step("Concerted substitution", "Backside nucleophilic attack, C–O formation and C–halogen cleavage occur in one elementary step; no stable carbocation is inserted.", editor,
             [electron_move("attack", endpoint("lone-pair", nucleophile), endpoint("atom", carbon), "The nucleophile's electron pair forms the C–O bond."), departure])
    elif mechanism == "E2":
        editor = Chem.RWMol(state); _remove(editor, carbon, leaving); _remove(editor, beta, beta_h)
        _order(editor, carbon, beta, 2); _add(editor, base, beta_h); _charge(editor, base, 0); _charge(editor, leaving, -1)
        e2_rule.apply_stereo(initial, editor, e2_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
        step("Concerted elimination", "Base removes the actual selected beta H while its C–H electrons form C=C and the leaving group departs. All three electron moves occur together.", editor,
             [electron_move("base-attack", endpoint("lone-pair", base), endpoint("atom", beta_h), "Base electron pair accepts the beta proton."),
              electron_move("pi-formation", endpoint("bond", beta, beta_h), endpoint("bond", beta, carbon), "Beta C–H electrons form the new pi bond."), departure])
    elif mechanism == "SN1":
        editor = Chem.RWMol(state); _add(editor, carbon, nucleophile); _charge(editor, carbon, 0); _charge(editor, nucleophile, 1)
        sn1_rule.unassign_reacting_center(editor, carbon)
        step("Nucleophilic capture", "Water attacks the carbocation to give a protonated alcohol (oxonium intermediate). No face-specific configuration or racemization ratio is assigned.", editor,
             [electron_move("attack", endpoint("lone-pair", nucleophile), endpoint("atom", carbon), "Water oxygen donates an electron pair to the carbocation.")], "Oxonium intermediate")
        transfer = next(c for c in net_changes if c["kind"] == "broken" and nucleophile in c["atomMaps"] and "H" in c["atoms"])
        proton = next(m for m in transfer["atomMaps"] if m != nucleophile)
        roles.update({"proton-transfer-base": base, "transferred-proton": proton})
        editor = Chem.RWMol(state); _remove(editor, nucleophile, proton); _add(editor, base, proton)
        _charge(editor, nucleophile, 0); _charge(editor, base, 1)
        step("Proton transfer", "A separate solvent water removes the oxonium proton. The alcohol is neutral and hydronium carries the released acid in water.", editor,
             [electron_move("proton-acceptance", endpoint("lone-pair", base), endpoint("atom", proton), "Solvent water accepts the proton."),
              electron_move("deprotonation", endpoint("bond", nucleophile, proton), endpoint("atom", nucleophile), "The O–H electron pair remains on the alcohol oxygen.")])
    else:
        editor = Chem.RWMol(state); _remove(editor, beta, beta_h); _order(editor, carbon, beta, 2)
        _add(editor, base, beta_h); _charge(editor, carbon, 0); _charge(editor, base, 1)
        e1_rule.apply_stereo(editor, e1_rule.participants(substrate, site, "elimination", solvent["mol"]))
        step("Elimination", "Water removes the selected beta proton and the C–H electrons form C=C in the same elementary step. These coupled events are not separated into a fictitious stable intermediate. This second step follows the separate ionization/carbocation step; leaving-group cleavage is not concerted with it as in E2.", editor,
             [electron_move("base-attack", endpoint("lone-pair", base), endpoint("atom", beta_h), "Solvent water accepts the beta proton."),
              electron_move("pi-formation", endpoint("bond", beta, beta_h), endpoint("bond", beta, carbon), "Beta C–H electrons form the pi bond and neutralize the carbocation.")])
    if mechanism == "SN2":
        sn2_rule.validate(initial, state, inputs[0]["mol"], inputs[1]["mol"], site)
    elif mechanism == "E2":
        e2_rule.validate(initial, state, inputs[0]["mol"], inputs[1]["mol"], site)
    actual_main = next(f for f in Chem.GetMolFrags(state, asMols=True) if any(a.GetAtomMapNum() == carbon for a in f.GetAtoms()))
    expected_main = outputs[0]["mol"]
    def signature(mol):
        return ({a.GetAtomMapNum(): (a.GetAtomicNum(), a.GetFormalCharge()) for a in mol.GetAtoms()},
                {tuple(sorted((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum()))): b.GetBondTypeAsDouble() for b in mol.GetBonds()})
    if signature(actual_main) != signature(expected_main) or _identity(actual_main) != _identity(expected_main):
        raise ValueError("Mechanism and selected net product do not agree.")
    intermediates = [s["intermediate"] for s in steps if s["intermediate"]]
    return {"version": 1, "type": mechanism, "siteId": reaction["site"]["siteId"], "roles": roles,
            "steps": steps, "solventSpecies": solvent_species,
            "energyProfile": {"qualitative": True, "stepCount": len(steps), "rateDeterminingStep": 1,
                              "intermediates": len(intermediates), "activationEnergies": None,
                              "note": "Textbook elementary-step topology; ionization is the assumed limiting step for SN1/E1. No barriers, energies, kinetics or relative rates are calculated."},
            "limitations": ["No curved-arrow geometry or transition-state calculation. Electron moves identify exact mapped endpoints.",
                            "SN1 loses only the reacting-center configuration at its planar carbocation. Water capture is unassigned; distant mapped configurations are checked. No exact racemization ratio, rearrangements or facial preference is predicted." if mechanism == "SN1" else
                            "E1 ionization precedes beta-H loss: alpha becomes planar first, beta only on alkene formation. New E/Z is unassigned; distant mapped configurations are checked. No E2 anti geometry, major-product or stereoisomer ratio is assumed." if mechanism == "E1" else
                            "SN2 inverts a specified tetrahedral center; unspecified configurations remain unspecified. No SN1 racemization ratio, rearrangements or conformer search." if mechanism != "E2" else "Only validated local anti-E2 relationships receive E/Z; unsigned centers remain unsigned. No product ratios or energy-based conformer search.",
                            "3D remains the final main product; charged intermediates are 2D structures only."] +
                           (["Net HX represents acid released; aqueous mechanism shows hydronium plus halide. Solvent water is explicit only in the mechanism."] if mechanism in {"SN1", "E1"} else []) +
                           (["E2 uses the selected mapped beta H in one concerted step. Acyclic anti rotation is kinematic only; rings, energy accessibility and product ratios are not validated."] if mechanism == "E2" else [])}
