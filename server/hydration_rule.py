"""Bounded acid/water capture of a selected alkene, not a selectivity predictor.

Ordinary isolated alkenes and narrowly screened phenyl-conjugated sites use
substitution/resonance orientation. Equal, inequivalent ends are alternatives,
not an arbitrary major product. Only the chosen pi geometry is consumed.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/8-4-hydration-of-alkenes-addition-of-h2o-by-oxymercuration"
REARRANGEMENT_SOURCE = "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"


def input_stereo_issue(smiles, normalized):
    """Detect directional annotations erased before canonical input matching.

    The unsanitized copy is used ONLY to inspect requested bond directions;
    it never supplies chemistry, eligibility or a product. Keep the normal
    sanitized molecule as the sole structural source of truth.
    """
    if "/" not in smiles and "\\" not in smiles:
        return None
    parser = Chem.SmilesParserParams()
    parser.sanitize = False; parser.removeHs = False
    raw = Chem.MolFromSmiles(smiles, parser)
    if raw is None:
        return "Hydration cannot validate the supplied directional alkene annotation."
    raw_heavy = {a.GetIdx(): i for i, a in enumerate(a for a in raw.GetAtoms() if a.GetAtomicNum() != 1)}
    heavy = [a.GetIdx() for a in normalized.GetAtoms() if a.GetAtomicNum() != 1]
    directions = {Chem.BondDir.ENDUPRIGHT, Chem.BondDir.ENDDOWNRIGHT}
    for bond in raw.GetBonds():
        if bond.GetBondType() != Chem.BondType.DOUBLE or bond.GetBeginAtom().GetAtomicNum() != 6 or bond.GetEndAtom().GetAtomicNum() != 6:
            continue
        if any(b.GetBondDir() in directions for a in (bond.GetBeginAtom(), bond.GetEndAtom()) for b in a.GetBonds()):
            ends = [heavy[raw_heavy[i]] for i in (bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())]
            checked = normalized.GetBondBetweenAtoms(*ends)
            if checked is None or checked.GetStereo() == Chem.BondStereo.STEREONONE:
                return "Hydration cannot preserve an incomplete/unsupported directional C=C annotation through input normalization (including unvalidated small-ring geometry). Supply validated E/Z or omit unsupported directions; no geometry is silently assumed."
    return None


def _phenyl_neighbor(molecule, index):
    atom = molecule.GetAtomWithIdx(index)
    aromatic = [n for n in graph.carbon_neighbors(atom) if n.GetIsAromatic()]
    if len(aromatic) != 1:
        return None
    neighbor = aromatic[0]
    rings = [r for r in molecule.GetRingInfo().AtomRings() if neighbor.GetIdx() in r]
    if (len(rings) != 1 or len(rings[0]) != 6
            or any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 or not molecule.GetAtomWithIdx(i).GetIsAromatic() for i in rings[0])):
        return None
    return neighbor.GetIdx()


def orientation(molecule, ends):
    """Return justified capture centers and a qualitative basis, never ratios."""
    aromatic = [_phenyl_neighbor(molecule, i) is not None for i in ends]
    degrees = [graph.substitution_degree(molecule.GetAtomWithIdx(i)) for i in ends]
    if any(aromatic):
        if sum(aromatic) != 1 or degrees[1 - aromatic.index(True)] >= 3:
            return [], "Benzylic versus multiply stabilized carbocation preferences are not validated for this alkene."
        return [ends[aromatic.index(True)]], "bounded benzylic resonance orientation"
    if degrees[0] != degrees[1]:
        return [ends[0] if degrees[0] > degrees[1] else ends[1]], "bounded Markovnikov substitution orientation"
    copy = Chem.RemoveHs(Chem.Mol(molecule))
    # Atom maps are bookkeeping, not chemically distinct substituents.
    for atom in copy.GetAtoms():
        atom.SetAtomMapNum(0)
    # In this engine explicit Hs are appended after the heavy graph. Match
    # heavy indices explicitly instead of assuming RemoveHs retains any H index.
    heavy = [a.GetIdx() for a in molecule.GetAtoms() if a.GetAtomicNum() != 1]
    ranks = Chem.CanonicalRankAtoms(copy, breakTies=False, includeChirality=True)
    if ranks[heavy.index(ends[0])] == ranks[heavy.index(ends[1])]:
        return [ends[0]], "equivalent ends under full-graph symmetry"
    return list(ends), "regioselectivity unresolved: separate constitutional capture alternatives"


def _ring_issue(molecule, ends):
    bond = molecule.GetBondBetweenAtoms(*ends)
    rings = molecule.GetRingInfo().AtomRings()
    if bond.IsInRing():
        shared = [r for r in rings if set(ends) <= set(r)]
        if len(shared) != 1 or not 5 <= len(shared[0]) <= 8:
            return "Selected cyclic hydration is limited to one 5–8-membered carbocyclic ring; small/large/fused/bridged ring cations need separate validation."
        ring = shared[0]
        if any(sum(i in r for r in rings) != 1 or molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in ring):
            return "Fused, bridged or heterocyclic hydration sites need additional cation/ring-migration validation."
    elif any(molecule.GetAtomWithIdx(i).IsInRing() for i in ends):
        return "Exocyclic/ring-bound alkene hydration may involve ring migration; this scope does not assume an unrearranged product."
    return None


def site_check(molecule, ends):
    if tuple(ends) not in graph.find_alkenes(molecule) and tuple(reversed(ends)) not in graph.find_alkenes(molecule):
        return "Hydration requires a selected non-aromatic C=C, not a saturated or aromatic bond."
    ring_issue = _ring_issue(molecule, ends)
    if ring_issue:
        return ring_issue
    for i in ends:
        for neighbor in molecule.GetAtomWithIdx(i).GetNeighbors():
            j = neighbor.GetIdx()
            if j in ends:
                continue
            if neighbor.GetAtomicNum() not in {1, 6}:
                return "Direct heteroatom-substituted alkenes/enol ethers need a separate acid/oxocarbenium hydration model."
            if neighbor.GetIsAromatic():
                if _phenyl_neighbor(molecule, i) != j:
                    return "Only a single screened carbocyclic phenyl neighbor is validated for benzylic hydration."
            elif any(b.GetBondType() != Chem.BondType.SINGLE for b in neighbor.GetBonds()):
                return "Conjugated/cumulated alkenes and adjacent unsaturated groups have unvalidated competing protonation/capture sites."
    targets, basis = orientation(molecule, ends)
    if not targets:
        return basis
    # Screen every plausible capture center, not just a conveniently safe one.
    for target in targets:
        for neighbor in graph.carbon_neighbors(molecule.GetAtomWithIdx(target)):
            j = neighbor.GetIdx()
            if j in ends or neighbor.GetIsAromatic():
                continue
            same_ring = molecule.GetBondBetweenAtoms(*ends).IsInRing() and any({target, j} <= set(r) for r in molecule.GetRingInfo().AtomRings())
            if neighbor.IsInRing() and not same_ring:
                return "Adjacent cyclic carbon can undergo ring migration/expansion; unrearranged hydration is not validated."
            if graph.substitution_degree(neighbor) >= 3:
                return "Adjacent branched/quaternary carbon creates a hydride/alkyl-shift risk; no rearranged hydration product or guaranteed unrearranged outcome is assigned."
            if any(n.GetIsAromatic() for n in graph.carbon_neighbors(neighbor)):
                return "A neighboring carbon could give a benzylic cation after a shift; this competing hydration rearrangement is unvalidated."
    return None


def _oxygen_issue(molecule, oxygen, ends):
    targets, _ = orientation(molecule, ends)
    for target in targets:
        path = Chem.GetShortestPath(molecule, oxygen, target)
        if len(path) <= 2:
            return "Direct oxygen/carbocation participation is not a remote spectator environment."
        if len(path) <= 6:
            return f"Possible {len(path)}-membered intramolecular oxygen capture between O atom {oxygen + 1} and C atom {target + 1} competes with water hydration; cyclization is not predicted by this model."
    return None


def group_check(molecule, ends, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alkene":
        if set(indices) == set(ends):
            return "reactive", "validated", "Water's net H/OH fragments add to this selected C=C under required acid catalysis."
        issue = site_check(molecule, tuple(indices))
        if issue:
            return "rejected", "competition", "Another alkene has an unvalidated acid-reactive environment: " + issue
        targets, _ = orientation(molecule, ends)
        for target in targets:
            for other in indices:
                size = len(Chem.GetShortestPath(molecule, target, other))
                if size <= 6:
                    return "rejected", "competition", f"A second C=C permits a potential {size}-membered intramolecular carbon capture/cyclization from the selected cation; selective one-site water capture is unresolved."
        return "alternative-site", "bounded", "This sufficiently separated screened C=C is another independent net site; further hydration, migration, larger-ring capture and selective one-site conversion are not predicted."
    if kind in {"alcohol", "ether"}:
        oxygens = [i for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8]
        if len(oxygens) != 1:
            return "rejected", "unvalidated", "This oxygen environment is not a screened ordinary alcohol/ether."
        oxygen = oxygens[0]
        carbons = [n for n in molecule.GetAtomWithIdx(oxygen).GetNeighbors() if n.GetAtomicNum() == 6]
        if (not carbons or any(c.GetIsAromatic() or c.GetHybridization() != Chem.HybridizationType.SP3
                or graph.substitution_degree(c) >= 3 or graph.is_allylic_or_benzylic(c)
                or sum(n.GetAtomicNum() == 8 for n in c.GetNeighbors()) != 1 for c in carbons)):
            return "rejected", "competition", "Acid-sensitive allylic/benzylic/tertiary, aryl, enol, acetal or related oxygen groups are not validated hydration spectators."
        # Each alkene is potentially protonated under acid; distance from just
        # the selected site cannot excuse a short capture path at another site.
        for alkene in graph.find_alkenes(molecule):
            issue = _oxygen_issue(molecule, oxygen, alkene)
            if issue:
                return "rejected", "competition", issue
        return "preserved", "bounded", "Screened saturated remote C–O/O–H bonds are retained only in this net edit. Acid strength, ether cleavage/dehydration, intermolecular and larger-ring capture are not predicted."
    if kind == "aromatic ring":
        ring = set(indices)
        phenyl = {_phenyl_neighbor(molecule, i) for i in ends}
        if any(i in ring for i in phenyl if i is not None):
            return "preserved", "bounded", "The screened phenyl ring supports a benzylic capture orientation and stays unchanged in this bounded net option; polymerization/acid-specific selectivity are not predicted."
        return "rejected", "unvalidated", "Remote aromatic acid chemistry/intramolecular capture is not screened by this hydration policy."
    return "rejected", "competition", f"Additional {kind} protonation, hydrolysis or competing chemistry has no validated acid-hydration spectator policy; distance alone does not establish inertness."


def additional_check(molecule, ends):
    for atom in molecule.GetAtoms():
        if atom.GetChiralTag() in stereo.TETRAHEDRAL:
            distance = min(len(Chem.GetShortestPath(molecule, atom.GetIdx(), i)) - 1 if atom.GetIdx() != i else 0 for i in ends)
            if distance < 2:
                yield "near-site-stereo", "unvalidated", "A specified center at/adjacent to this alkene needs separate acid/stereochemical compatibility validation; no configuration is silently removed.", [atom.GetIdx()]


POLICY = compatibility.SitePolicy("acid-catalyzed alkene hydration", frozenset({"C", "H", "O"}),
                                  site_check, group_check, additional_check, added_atoms=3)


def assess(molecule, site):
    report = compatibility.assess_site(molecule, site[:2], POLICY)
    targets, basis = orientation(molecule, site[:2]) if len(site) >= 2 and all(type(i) is int and 0 <= i < molecule.GetNumAtoms() for i in site[:2]) else ([], "invalid site")
    if len(site) != 3 or site[2] not in targets:
        report["rejections"].append({"code": "invalid-orientation", "category": "structural", "message": "The selected OH carbon is not a supported hydration orientation.", "atomIndices": []})
        report["eligible"] = False
    report["orientationBasis"] = basis
    report["orientationCount"] = len(targets)
    return report


def sites(molecule):
    return [(*ends, target) for ends in graph.find_alkenes(molecule) for target in (orientation(molecule, ends)[0] or [ends[0]])]


def participants(substrate, reagent, site):
    atoms = list(reagent.GetAtoms())
    oxygen = [a for a in atoms if a.GetAtomicNum() == 8]
    hs = sorted((a.GetAtomMapNum() for a in atoms if a.GetAtomicNum() == 1))
    if (len(atoms) != 3 or len(oxygen) != 1 or len(hs) != 2 or reagent.GetNumBonds() != 2
            or any(a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in atoms)
            or any(b.GetBondType() != Chem.BondType.SINGLE or 8 not in {b.GetBeginAtom().GetAtomicNum(), b.GetEndAtom().GetAtomicNum()} for b in reagent.GetBonds())):
        raise ValueError("Hydration consumes one actual neutral water molecule; acid is a regenerated catalyst, not an atom source in the net equation.")
    first, second, target = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    return {"alkene": [first, second], "oxygenCarbon": target, "hydrogenCarbon": second if target == first else first,
            "oxygen": oxygen[0].GetAtomMapNum(), "hydrogen": hs[0], "hydroxylHydrogen": hs[1]}


def edit_contract(substrate, reagent, site):
    p = participants(substrate, reagent, site)
    return [{"atomMaps": p["alkene"], "before": 2.0, "after": 1.0},
            {"atomMaps": [p["oxygen"], p["hydrogen"]], "before": 1.0, "after": None},
            {"atomMaps": [p["hydrogenCarbon"], p["hydrogen"]], "before": None, "after": 1.0},
            {"atomMaps": [p["oxygenCarbon"], p["oxygen"]], "before": None, "after": 1.0}]


def edit(editor, substrate, reagent, site):
    # Apply this exact contract rather than duplicate water-H selection logic.
    indices = {a.GetAtomMapNum(): a.GetIdx() for a in editor.GetAtoms()}
    for change in edit_contract(substrate, reagent, site):
        left, right = (indices[m] for m in change["atomMaps"])
        if change["after"] is None:
            editor.RemoveBond(left, right)
        elif change["before"] is None:
            editor.AddBond(left, right, Chem.BondType.SINGLE)
        else:
            bond = editor.GetBondBetweenAtoms(left, right)
            bond.SetBondType(Chem.BondType.SINGLE)
            bond.SetStereo(Chem.BondStereo.STEREONONE)
    # Direction flags adjacent to consumed E/Z must not leak into the single
    # bond serialization. Other double-bond geometry is checked independently.
    Chem.SetDoubleBondNeighborDirections(editor)


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    edits = edit_contract(substrate, reagent, site)
    compatibility.validate_edit_contract(before, after, edits, consumed_double_bonds=[edits[0]["atomMaps"]], expected_fragments=1)
