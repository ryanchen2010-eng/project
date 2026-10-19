"""Additional bounded graph rules. Site selection never uses molecule names.

Net pathways only: no guessed rearrangements, product ratios or kinetics.
Polymerization is a finite benzoyl-peroxide initiated, combination-terminated
oligomer model with explicit end groups and CO2, not a bulk-polymer prediction.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph
    from . import ester_rules, alkyne_partial_hydrogenation_rule, alkyne_halogenation_rule, alcohol_dehydration_rule, alcohol_substitution_rule
    from .reaction_diagrams import _remove, _add, _order, _charge, _hydrogens
else:
    import molecular_graph as graph
    import ester_rules, alkyne_partial_hydrogenation_rule, alkyne_halogenation_rule, alcohol_dehydration_rule, alcohol_substitution_rule
    from reaction_diagrams import _remove, _add, _order, _charge, _hydrogens

SOURCES = {
    "alcohol": "https://openstax.org/books/organic-chemistry/pages/17-6-reactions-of-alcohols",
    "ester": "https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters",
    "alkyne": "https://openstax.org/books/organic-chemistry/pages/9-3-reactions-of-alkynes-addition-of-hx-and-x2",
    "reduction": "https://openstax.org/books/organic-chemistry/pages/9-5-reduction-of-alkynes",
    "diol": "https://pubmed.ncbi.nlm.nih.gov/23113538/",
    "polymer": "https://openstax.org/books/organic-chemistry/pages/8-10-radical-additions-to-alkenes-chain-growth-polymers",
}
BPO = Chem.MolFromSmiles("O=C(OOC(=O)c1ccccc1)c1ccccc1")
MECHANISMS = {"Alcohol dehydration", "Alcohol substitution", "Ester saponification", "Alkyne hydrogenation",
              "Alkyne partial hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation", "Alkene dihydroxylation", "Polymerization model"}


def reagent_role(mol):
    if mol.GetNumAtoms() == 2 and mol.GetNumBonds() == 1 and all(
            a.GetSymbol() == "O" and not a.GetFormalCharge() and graph.attached_hydrogens(a) == 1 for a in mol.GetAtoms()):
        return "hydrogen-peroxide"
    if mol.GetNumAtoms() == 5 and mol.HasSubstructMatch(Chem.MolFromSmarts("[S](=[O])(=[O])([O;H1])[O;H1]")):
        return "sulfuric-acid"
    if mol.GetNumAtoms() == BPO.GetNumAtoms() and mol.HasSubstructMatch(BPO) and BPO.HasSubstructMatch(mol):
        return "benzoyl-peroxide"
    return None


def candidates(substrate, reagent, role, conditions, plan, notes):
    hydrocarbon = all(a.GetSymbol() in {"C", "H"} for a in substrate.GetAtoms())
    if role == "hydroxide" and all(a.GetSymbol() in {"C", "H", "O"} for a in substrate.GetAtoms()):
        for site in graph.find_esters(substrate):
            issue = ester_rules.site_issue(substrate, site)
            if issue:
                notes.append(issue); continue
            cyclic = substrate.GetBondBetweenAtoms(site[0], site[2]).IsInRing()
            plan("Ester saponification", "Hydrolysis", site, {"solvent": "aqueous-protic"},
                 "Hydroxide opens the selected lactone acyl–O bond to give one connected hydroxy carboxylate. No neutral acid work-up is assumed." if cyclic else
                 "Hydroxide cleaves the selected ester acyl–O bond into carboxylate and alcohol or phenol. No neutral acid work-up is assumed.", SOURCES["ester"],
                 "One OH⁻ equivalent per selected ester site. The charged carboxylate is displayed in 2D; spectators are excluded from the net ionic equation. Excess-base deprotonation of other OH groups and a separate acid work-up are not modeled.")
    if hydrocarbon and role in {"hydrogen", "halogen", "hydrogen-halide"}:
        for ends in graph.find_alkynes(substrate):
            if substrate.GetBondBetweenAtoms(*ends).IsInRing() or any(
                    b.GetBondTypeAsDouble() > 1 and b.GetOtherAtomIdx(i) not in ends
                    for i in ends for b in substrate.GetAtomWithIdx(i).GetBonds()) or any(
                    b.GetBondTypeAsDouble() > 1 for i in ends for n in substrate.GetAtomWithIdx(i).GetNeighbors()
                    if n.GetIdx() not in ends for b in n.GetBonds()):
                notes.append("Ring/conjugated alkynes need additional selectivity rules."); continue
            if role == "hydrogen":
                continue  # Complete and partial reduction have independent site policies.
            elif role == "halogen":
                continue  # Independent electrophilic X2 site/condition policy.
            else:
                continue  # Independent alkyne-specific ionic HX site policy.
    if hydrocarbon and role == "benzoyl-peroxide":
        alkene_sites = graph.find_alkenes(substrate)
        if len(alkene_sites) == 1 and not substrate.GetRingInfo().NumRings():
            ends = alkene_sites[0]
            terminal = [i for i in ends if graph.attached_hydrogens(substrate.GetAtomWithIdx(i)) == 2]
            if terminal and graph.isolated_alkene(substrate, ends):
                tail = terminal[0]; head = ends[1] if tail == ends[0] else ends[0]
                units = int(conditions.get("polymerUnits") or "4")
                if units in {2, 4, 6}:
                    plan("Polymerization model", "Polymerization", (tail, head, units), {"catalyst": "radical", "temperature": "heated", "polymerUnits": str(units)},
                         f"Finite {units}-monomer model: benzoyl peroxide initiates two chains; head-to-tail propagation and head-to-head combination termination give a phenyl-ended oligomer plus two CO₂ molecules.", SOURCES["polymer"],
                         "A bounded connectivity demonstration, not a bulk polymer, molecular-weight distribution, tacticity or predicted experimental product. Initiator is consumed, not a catalyst.")


def equation_ids(mechanism, substrate_id, reagent_id, site):
    if mechanism == "Alcohol dehydration": return [substrate_id]
    if mechanism == "Alkyne hydrogenation": return [substrate_id, reagent_id, reagent_id]
    if mechanism in {"Alkyne halogenation", "Alkyne hydrohalogenation"}:
        return [substrate_id] + [reagent_id] * site[-1]
    if mechanism == "Polymerization model": return [substrate_id] * site[2] + [reagent_id]
    return None


def edit(mechanism, editor, combined, inputs, site):
    if mechanism not in MECHANISMS:
        return False
    substrate = inputs[0]["mol"]
    maps = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]]
    carbon, second = maps
    reagent = inputs[-1]["mol"] if len(inputs) > 1 else None
    def atom(symbol): return next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetSymbol() == symbol)
    if mechanism == "Alcohol dehydration":
        alcohol_dehydration_rule.edit(editor, substrate, site)
    elif mechanism == "Alcohol substitution":
        alcohol_substitution_rule.edit(editor, substrate, reagent, site)
    elif mechanism == "Ester saponification":
        old_o = substrate.GetAtomWithIdx(site[2]).GetAtomMapNum(); new_o = atom("O"); h = _hydrogens(combined, new_o)[0]
        _remove(editor, carbon, old_o); _remove(editor, new_o, h); _add(editor, carbon, new_o); _add(editor, old_o, h)
        _charge(editor, new_o, -1)
    elif mechanism in {"Alkyne hydrogenation", "Alkyne partial hydrogenation", "Alkyne halogenation"}:
        equivalents = len(inputs) - 1; _order(editor, carbon, second, 3 - equivalents)
        for item in inputs[1:]:
            introduced = [a.GetAtomMapNum() for a in item["mol"].GetAtoms()]
            _remove(editor, *introduced)
            _add(editor, carbon, introduced[0]); _add(editor, second, introduced[1])
        if mechanism == "Alkyne partial hydrogenation":
            alkyne_partial_hydrogenation_rule.assign_syn_geometry(editor, substrate, site)
        elif mechanism == "Alkyne halogenation":
            alkyne_halogenation_rule.assign_geometry(editor, substrate, [item["mol"] for item in inputs[1:]], site,
                                                    anti_model=inputs[0].get("alkyneHalogenAntiModel", False))
    elif mechanism == "Alkyne hydrohalogenation":
        target = substrate.GetAtomWithIdx(site[2]).GetAtomMapNum(); other = second if target == carbon else carbon
        _order(editor, carbon, second, 3 - (len(inputs) - 1))
        editor.GetBondBetweenAtoms(site[0], site[1]).SetStereo(Chem.BondStereo.STEREONONE)
        for item in inputs[1:]:
            x = next(a.GetAtomMapNum() for a in item["mol"].GetAtoms() if a.GetSymbol() != "H"); h = _hydrogens(combined, x)[0]
            _remove(editor, x, h); _add(editor, target, x); _add(editor, other, h)
    elif mechanism == "Alkene dihydroxylation":
        return False  # Independently validated site/syn policy in its own module.
    elif mechanism == "Polymerization model":
        units = [(item["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum(), item["mol"].GetAtomWithIdx(site[1]).GetAtomMapNum()) for item in inputs[:-1]]
        peroxide = next(b for b in reagent.GetBonds() if b.GetBeginAtom().GetSymbol() == b.GetEndAtom().GetSymbol() == "O")
        oxygens = [peroxide.GetBeginAtom(), peroxide.GetEndAtom()]
        _remove(editor, *[a.GetAtomMapNum() for a in oxygens]); initiator_anchors = []
        for oxygen in oxygens:
            acyl = next(n for n in oxygen.GetNeighbors() if n.GetSymbol() == "C")
            phenyl = next(n for n in acyl.GetNeighbors() if n.GetSymbol() == "C")
            _remove(editor, acyl.GetAtomMapNum(), phenyl.GetAtomMapNum())
            _order(editor, acyl.GetAtomMapNum(), oxygen.GetAtomMapNum(), 2)
            initiator_anchors.append(phenyl.GetAtomMapNum())
        for tail, head in units: _order(editor, tail, head, 1)
        split = len(units) // 2
        for anchor, chain in zip(initiator_anchors, (units[:split], units[split:])):
            _add(editor, anchor, chain[0][0])
            for first, next_unit in zip(chain, chain[1:]): _add(editor, first[1], next_unit[0])
        _add(editor, units[split - 1][1], units[-1][1])
    else:
        return False
    return True
