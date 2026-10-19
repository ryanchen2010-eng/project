"""Selected-site ionic HCl/HBr/HI addition, not an experimental predictor.

HX supplies BOTH atoms and is consumed. HBr/HI oxygen-substitution/cleavage
risks are not imported from hydration's water model. HCl alone has a narrow
ambient neutral-reporting spectator scope; protonation/inertness is not claimed.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/7-8-orientation-of-electrophilic-additions-markovnikovs-rule"
HALOGENS = frozenset({"Cl", "Br", "I"})


def hx_element(reagent):
    """Validate the actual graph, with either explicit or implicit hydrogen."""
    molecule = Chem.AddHs(reagent)
    atoms = list(molecule.GetAtoms())
    x = [a for a in atoms if a.GetSymbol() in HALOGENS]
    if (len(atoms) != 2 or len(x) != 1 or sum(a.GetAtomicNum() == 1 for a in atoms) != 1
            or molecule.GetNumBonds() != 1 or molecule.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in atoms)):
        raise ValueError("Ionic alkene hydrohalogenation needs actual neutral H–Cl, H–Br or H–I. HF, free halide, halogen X2, isotopic/radical and multi-part reagent graphs are not enabled.")
    return x[0].GetSymbol()


def phenyl_anchor(molecule, index):
    attached = [a for a in graph.carbon_neighbors(molecule.GetAtomWithIdx(index)) if a.GetIsAromatic()]
    if len(attached) != 1:
        return None
    rings = [r for r in molecule.GetRingInfo().AtomRings() if attached[0].GetIdx() in r]
    if len(rings) == 1 and len(rings[0]) == 6 and all(molecule.GetAtomWithIdx(i).GetAtomicNum() == 6 and molecule.GetAtomWithIdx(i).GetIsAromatic() for i in rings[0]):
        return attached[0].GetIdx()
    return None


def orientation(molecule, ends):
    """Bounded cation basis; equal inequivalent ends are not a guessed winner."""
    if len(ends) != 2 or len(set(ends)) != 2 or any(type(i) is not int or not 0 <= i < molecule.GetNumAtoms() for i in ends):
        return [], "invalid alkene site"
    degree = [graph.substitution_degree(molecule.GetAtomWithIdx(i)) for i in ends]
    resonant = [i for i in ends if phenyl_anchor(molecule, i) is not None]
    if resonant:
        if len(resonant) != 1 or graph.substitution_degree(molecule.GetAtomWithIdx(next(i for i in ends if i not in resonant))) >= 3:
            return [], "Competing benzylic/multiply stabilized cation orientations require an independently validated preference model."
        return resonant, "screened benzylic resonance capture"
    if degree[0] != degree[1]:
        return [ends[degree.index(max(degree))]], "bounded Markovnikov cation substitution"
    copy = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in copy.GetAtoms(): atom.SetAtomMapNum(0)
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    rank = Chem.CanonicalRankAtoms(copy, breakTies=False, includeChirality=True)
    if rank[heavy.index(ends[0])] == rank[heavy.index(ends[1])]:
        return [ends[0]], "equivalent full-graph orientations"
    return list(ends), "unresolved regioselectivity: separate constitutional HX capture options"


def local_issue(molecule, ends):
    if tuple(ends) not in graph.find_alkenes(molecule) and tuple(reversed(ends)) not in graph.find_alkenes(molecule):
        return "Select a non-aromatic C=C for ionic HX addition."
    bond, rings = molecule.GetBondBetweenAtoms(*ends), molecule.GetRingInfo().AtomRings()
    if bond.IsInRing():
        selected = [r for r in rings if set(ends) <= set(r)]
        if (len(selected) != 1 or not 5 <= len(selected[0]) <= 8
                or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or sum(i in r for r in rings) != 1 for i in selected[0])):
            return "Ionic cyclic HX addition is validated only for a selected isolated 5–8-membered carbocycle; small/large, fused, bridged and heterocyclic cation environments remain unvalidated."
    elif any(molecule.GetAtomWithIdx(i).IsInRing() for i in ends):
        return "Exocyclic/ring-bound HX sites need separate ring-cation/migration and geometry validation; no rearranged product is generated."
    for index in ends:
        for neighbor in molecule.GetAtomWithIdx(index).GetNeighbors():
            if neighbor.GetIdx() in ends: continue
            if neighbor.GetAtomicNum() not in {1, 6}:
                return "Direct heteroatom-substituted/enol-ether alkenes require a different oxocarbenium/protonation model."
            if neighbor.GetIsAromatic():
                if phenyl_anchor(molecule, index) != neighbor.GetIdx():
                    return "Only one isolated carbocyclic phenyl attachment is screened for benzylic HX capture."
            elif any(b.GetBondType() != Chem.BondType.SINGLE for b in neighbor.GetBonds()):
                return "Conjugated, cumulated or adjacent unsaturated environments have competing HX addition sites not covered by this isolated-cation model."
    targets, basis = orientation(molecule, ends)
    if not targets: return basis
    for target in targets:
        for neighbor in graph.carbon_neighbors(molecule.GetAtomWithIdx(target)):
            j = neighbor.GetIdx()
            if j in ends or neighbor.GetIsAromatic(): continue
            within_ring = bond.IsInRing() and any({target, j} <= set(r) for r in rings)
            if neighbor.IsInRing() and not within_ring:
                return "Adjacent ring migration/expansion may compete; the unrearranged HX capture is not validated."
            if graph.substitution_degree(neighbor) >= 3:
                return "Adjacent branched/quaternary carbon introduces hydride/alkyl-shift risk; unsupported rearranged and guaranteed unrearranged HX products are not assigned."
            if any(a.GetIsAromatic() for a in graph.carbon_neighbors(neighbor)):
                return "A neighboring shift can create a benzylic cation; this rearrangement competes with the proposed HX capture."
    return None


def oxygen_capture_issue(molecule, oxygen):
    for ends in graph.find_alkenes(molecule):
        targets, _ = orientation(molecule, ends)
        for target in targets:
            size = len(Chem.GetShortestPath(molecule, oxygen, target))
            if size <= 6:
                return f"Potential {size}-membered intramolecular oxygen capture from O atom {oxygen + 1} to C atom {target + 1} competes with halide capture; ionic HX cyclization/neighboring participation is unresolved."
    return None


def group_check(molecule, ends, group, symbol):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(ends):
            return "reactive", "validated", f"One actual H{symbol} supplies H and {symbol} to this selected C=C in the ionic net model."
        issue = local_issue(molecule, tuple(indices))
        if issue: return "rejected", "competition", "Another acid-reactive alkene is not screened: " + issue
        targets, _ = orientation(molecule, ends)
        for target in targets:
            for carbon in indices:
                size = len(Chem.GetShortestPath(molecule, target, carbon))
                if size <= 6:
                    return "rejected", "competition", f"A second C=C permits a potential {size}-membered intramolecular carbon capture/cyclization; one-site ionic HX addition is unresolved, not chemically impossible."
        return "alternative-site", "bounded", "Another screened isolated C=C is an independent net site. Further HX addition, migration, larger-ring/intermolecular capture and selective mono-conversion are not predicted."
    if kind in {"alcohol", "ether"}:
        if symbol != "Cl":
            return "rejected", "competition", f"H{symbol} can cause additional alcohol substitution or ether C–O cleavage. A preserve-only oxygen spectator model is not validated for H{symbol}, regardless of distance."
        os = [i for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8]
        if len(os) != 1: return "rejected", "unvalidated", "This oxygen group is not a screened HCl spectator."
        oxygen = os[0]
        carbons = [a for a in molecule.GetAtomWithIdx(oxygen).GetNeighbors() if a.GetAtomicNum() == 6]
        if (not carbons or any(a.GetIsAromatic() or a.GetHybridization() != Chem.HybridizationType.SP3
                or graph.substitution_degree(a) >= (2 if kind == "alcohol" else 3)
                or graph.is_allylic_or_benzylic(a) or sum(n.GetAtomicNum() == 8 for n in a.GetNeighbors()) != 1 for a in carbons)):
            return "rejected", "competition", "Only unactivated primary alcohols and ordinary primary/secondary dialkyl ethers have a bounded ambient-HCl reporting scope. Secondary/tertiary alcohols, acid-labile tertiary/allylic/benzylic ethers, aryl/enol and acetal environments remain excluded."
        issue = oxygen_capture_issue(molecule, oxygen)
        if issue: return "rejected", "competition", issue
        return "preserved", "bounded", "Only in the explicitly ambient, no-added-activation HCl net model are these screened remote bonds retained in a neutral reporting form. Oxygen protonation, eventual alcohol substitution, cleavage under other acids, large-ring/intermolecular capture and experimental selectivity are not established."
    if kind == "aromatic ring":
        if any(phenyl_anchor(molecule, i) in indices for i in ends):
            return "preserved", "bounded", "One screened phenyl ring stabilizes benzylic capture and stays unchanged in the net option. Polymerization and acid-specific experimental outcomes are not predicted."
        return "rejected", "unvalidated", "Additional aromatic electrophilic/intramolecular chemistry is not screened for this ionic HX policy."
    if kind == "peroxide":
        return "rejected", "competition", "Peroxide-containing substrates may introduce radical HBr chemistry; no anti-Markovnikov or other radical HX model is implemented."
    return "rejected", "competition", f"Additional {kind} protonation, addition, hydrolysis or substitution has no validated H{symbol} spectator policy. Distance alone does not establish inertness."


def extra_check(molecule, ends):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in ends)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "A specified at/adjacent alkene stereocenter needs separate ionic-HX stereochemical/epimerization validation; no configuration is discarded.", [atom.GetIdx()]


def assess(molecule, reagent, site):
    symbol = hx_element(reagent)
    policy = compatibility.SitePolicy(f"ionic H{symbol} alkene addition", frozenset({"C", "H", "O"}),
                                      local_issue, lambda m, s, g: group_check(m, s, g, symbol), extra_check, added_atoms=2)
    report = compatibility.assess_site(molecule, site[:2], policy)
    targets, basis = orientation(molecule, site[:2])
    if len(site) != 3 or type(site[2]) is not int or site[2] not in targets:
        report["rejections"].append({"code": "invalid-orientation", "category": "structural", "message": "Choose a validated HX capture carbon on the actual selected C=C.", "atomIndices": []})
        report["eligible"] = False
    report.update(hydrogenHalide="H" + symbol, orientationBasis=basis, orientationCount=len(targets))
    return report


def sites(molecule):
    return [(*ends, target) for ends in graph.find_alkenes(molecule) for target in (orientation(molecule, ends)[0] or [ends[0]])]


def context_issue(conditions):
    if conditions.get("catalyst") == "radical":
        return "Radical initiation is outside the ionic HCl/HBr/HI model. Peroxide-initiated anti-Markovnikov HBr requires a separate validated radical mechanism; no ionic or radical product is generated for these conditions."
    return None


def participants(substrate, reagent, site):
    symbol = hx_element(reagent)
    # The mapping/edit API, unlike matching, requires explicit H and atom maps.
    if reagent.GetNumAtoms() != 2:
        raise ValueError("The HX edit needs its actual explicit mapped hydrogen and halogen.")
    first, second, target = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    h = next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetAtomicNum() == 1)
    x = next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetSymbol() == symbol)
    return {"alkene": [first, second], "halogenCarbon": target, "hydrogenCarbon": second if target == first else first,
            "hydrogen": h, "halogen": x, "halogenElement": symbol}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkene"], "before": 2.0, "after": 1.0},
            {"atomMaps": [p["hydrogen"], p["halogen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["hydrogenCarbon"], p["hydrogen"]], "before": None, "after": 1.0},
            {"atomMaps": [p["halogenCarbon"], p["halogen"]], "before": None, "after": 1.0}]


def edit(editor, substrate, reagent, site):
    indices = {a.GetAtomMapNum(): a.GetIdx() for a in editor.GetAtoms()}
    for change in edit_contract(substrate, reagent, site):
        i, j = [indices[m] for m in change["atomMaps"]]
        if change["after"] is None: editor.RemoveBond(i, j)
        elif change["before"] is None: editor.AddBond(i, j, Chem.BondType.SINGLE)
        else:
            bond = editor.GetBondBetweenAtoms(i, j)
            bond.SetBondType(Chem.BondType.SINGLE); bond.SetStereo(Chem.BondStereo.STEREONONE)
    Chem.SetDoubleBondNeighborDirections(editor)


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, reagent, site)
    if not report["eligible"]: raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagent, site)
    compatibility.validate_edit_contract(before, after, edits, consumed_double_bonds=[edits[0]["atomMaps"]], expected_fragments=1)


def equivalent_sites(molecule, first, second):
    """Deduplicate only proven full-graph automorphisms, not identical formulas.

    Bounded matches may miss an equivalence and retain an extra option; they
    never justify merging sites from a guessed atom-rank/constitutional match.
    """
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    work = Chem.RemoveHs(Chem.Mol(molecule))
    for atom in work.GetAtoms(): atom.SetAtomMapNum(0)
    a, b = [tuple(heavy.index(i) for i in site) for site in (first, second)]
    for mapping in work.GetSubstructMatches(work, uniquify=False, useChirality=True, maxMatches=512):
        if {mapping[a[0]], mapping[a[1]]} == set(b[:2]) and mapping[a[2]] == b[2]:
            return True
    return False
