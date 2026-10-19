"""Map-aware stereochemistry foundations, not a stereochemical reaction oracle.

Labels require specified stereo. Geometry checks describe ONE supplied 3D
conformer; they neither search conformers nor predict experimental selectivity.
"""
import math
from rdkit import Chem
from rdkit.Chem import rdCIPLabeler


def inspect_stereochemistry(molecule):
    work = Chem.Mol(molecule)
    maps = [a.GetAtomMapNum() for a in work.GetAtoms()]
    # Reaction identity numbers must never become substituent priorities.
    for atom in work.GetAtoms():
        atom.SetAtomMapNum(0)
    Chem.AssignStereochemistry(work, cleanIt=True, force=True)
    rdCIPLabeler.AssignCIPLabels(work, maxRecursiveIterations=100000)
    centers, alkenes = [], []
    for info in Chem.FindPotentialStereo(work):
        specified = info.specified == Chem.StereoSpecified.Specified
        if info.type == Chem.StereoType.Atom_Tetrahedral:
            atom = work.GetAtomWithIdx(info.centeredOn)
            centers.append({"atomIndex": atom.GetIdx(), "atomMap": maps[atom.GetIdx()],
                            "element": atom.GetSymbol(), "specified": specified,
                            "assignment": atom.GetProp("_CIPCode") if specified and atom.HasProp("_CIPCode") else None})
        elif info.type == Chem.StereoType.Bond_Double:
            bond = work.GetBondWithIdx(info.centeredOn)
            assignment = bond.GetProp("_CIPCode") if specified and bond.HasProp("_CIPCode") else None
            ends = [bond.GetBeginAtom(), bond.GetEndAtom()]
            # H/H is a common reference only when each end has exactly one H.
            h_counts = [a.GetTotalNumHs() + sum(n.GetAtomicNum() == 1 for n in a.GetNeighbors()) for a in ends]
            ordinary_h = not any(a.GetIsotope() for a in work.GetAtoms() if a.GetAtomicNum() == 1)
            common_h = h_counts == [1, 1] and ordinary_h
            alkenes.append({"bondIndex": bond.GetIdx(), "atomMaps": [maps[a.GetIdx()] for a in ends],
                           "specified": specified, "assignment": assignment,
                           "cisTrans": {"E": "trans", "Z": "cis"}.get(assignment) if common_h else None,
                           "cisTransReference": "hydrogen on each alkene carbon" if common_h else None})
    return {"version": 1, "chiralCenters": centers, "alkenes": alkenes,
            "note": "Unspecified centers/alkenes remain unassigned. Cis/trans is reported only for a common H/H reference; ring-relative and non-tetrahedral stereo are outside this initial model."}


TETRAHEDRAL = {Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW}
DOUBLE_STEREO = {Chem.BondStereo.STEREOE, Chem.BondStereo.STEREOZ,
                 Chem.BondStereo.STEREOCIS, Chem.BondStereo.STEREOTRANS}


def stereo_scope_issue(molecule, context="the selected reaction"):
    if molecule.GetStereoGroups():
        return f"Enhanced/relative stereo groups are not supported by {context}; specify absolute configurations."
    if any(a.GetChiralTag() not in TETRAHEDRAL | {Chem.ChiralType.CHI_UNSPECIFIED} for a in molecule.GetAtoms()):
        return f"Non-tetrahedral stereochemistry is not supported by {context}."
    if any(b.GetStereo() not in DOUBLE_STEREO | {Chem.BondStereo.STEREONONE}
           or b.GetBondDir() in {Chem.BondDir.UNKNOWN, Chem.BondDir.EITHERDOUBLE} for b in molecule.GetBonds()):
        return f"Ambiguous or nonstandard bond stereochemistry is not supported by {context}."
    return None



def _checked_stereo(molecule):
    work = Chem.Mol(molecule)
    maps = [a.GetAtomMapNum() for a in work.GetAtoms()]
    for atom in work.GetAtoms():
        atom.SetAtomMapNum(0)
    Chem.AssignStereochemistry(work, cleanIt=True, force=True)
    for atom, number in zip(work.GetAtoms(), maps):
        atom.SetAtomMapNum(number)
    return work


def _tetra_signature(atom):
    neighbors = [a.GetAtomMapNum() for a in atom.GetNeighbors()]
    if atom.GetDegree() != 4 or len(set(neighbors)) != 4:
        raise ValueError("Stereo retention requires four explicit, uniquely mapped neighbors.")
    parity = sum(neighbors[i] > neighbors[j] for i in range(4) for j in range(i + 1, 4)) % 2
    orientation = (atom.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(parity)
    bonds = frozenset((b.GetOtherAtom(atom).GetAtomMapNum(), b.GetBondType()) for b in atom.GetBonds())
    return bonds, orientation


def _double_signature(bond):
    refs = list(bond.GetStereoAtoms())
    if len(refs) != 2 or bond.GetBondType() != Chem.BondType.DOUBLE:
        raise ValueError("Specified alkene reference atoms are missing.")
    endpoints = [bond.GetBeginAtom(), bond.GetEndAtom()]
    orientation = bond.GetStereo() in {Chem.BondStereo.STEREOE, Chem.BondStereo.STEREOTRANS}
    neighbors = {}
    for atom, other, ref in zip(endpoints, reversed(endpoints), refs):
        group = sorted(n.GetAtomMapNum() for n in atom.GetNeighbors() if n.GetIdx() != other.GetIdx())
        reference = bond.GetOwningMol().GetAtomWithIdx(ref).GetAtomMapNum()
        if len(group) != 2 or reference not in group:
            raise ValueError("Specified alkene neighbor correspondence failed.")
        orientation ^= reference != group[0]
        neighbors[atom.GetAtomMapNum()] = tuple(group)
    return neighbors, orientation


def validate_retained_stereo(before, after, *, consumed_double_bonds=(), consumed_tetrahedral_centers=(),
                            inverted_substitutions=(), eliminations=(), solvolyses=(), e1_eliminations=(), context="The selected net edit"):
    """Compare physical configurations using atom maps, not R/S or E/Z letters.

CIP priorities can change even when configuration is retained. This check also
rejects any lost or newly invented specified stereo, including in coproducts.
Explicit hydroxide SN2 substitutions independently compare inversion after
relabelling the leaving neighbor, without making R/S letters the validator.
SN1 configuration loss is scoped to an explicitly validated ionization,
unsigned water capture or proton transfer; it is not distant-stereo permission.
E1 has separate ionization and beta-H loss permissions; it does not inherit
the anti-periplanar E/Z relationship of a concerted hydroxide E2 edit.
"""
    for molecule in (before, after):
        issue = stereo_scope_issue(molecule, context)
        if issue:
            raise ValueError(issue)
    consumed = {frozenset(pair) for pair in consumed_double_bonds}
    consumed_tetrahedral_centers = tuple(consumed_tetrahedral_centers)
    lost_centers = set(consumed_tetrahedral_centers)
    if len(lost_centers) != len(consumed_tetrahedral_centers) or any(type(m) is not int or m <= 0 for m in lost_centers):
        raise ValueError("Consumed tetrahedral centers require distinct positive atom maps.")
    checked_before, checked_after = _checked_stereo(before), _checked_stereo(after)
    original_atoms = {a.GetAtomMapNum(): a for a in before.GetAtoms()}
    product_atoms = {a.GetAtomMapNum(): a for a in after.GetAtoms()}
    checked_original = {a.GetAtomMapNum(): a for a in checked_before.GetAtoms()}
    checked_product = {a.GetAtomMapNum(): a for a in checked_after.GetAtoms()}
    solvolysed_centers = set()
    for substitution in solvolyses:
        center, leaving, incoming, hydrogen = (substitution[k] for k in ("center", "leaving", "incoming", "hydrogen"))
        stage = substitution["stage"]
        if (stage not in {"net", "ionization", "capture", "deprotonation"}
                or len({center, leaving, incoming, hydrogen}) != 4
                or any(type(m) is not int or m <= 0 or m not in original_atoms or m not in product_atoms for m in (center, leaving, incoming, hydrogen))
                or center in solvolysed_centers or center in lost_centers):
            raise ValueError("SN1 configuration loss requires one exact, uniquely declared water-solvolysis site and stage.")
        old, new = original_atoms[center], product_atoms[center]
        old_neighbors = {a.GetAtomMapNum() for a in old.GetNeighbors()}
        new_neighbors = {a.GetAtomMapNum() for a in new.GetNeighbors()}
        if (old.GetAtomicNum() != 6 or new.GetAtomicNum() != 6
                or original_atoms[leaving].GetSymbol() not in {"Cl", "Br", "I"}
                or original_atoms[incoming].GetAtomicNum() != 8 or original_atoms[hydrogen].GetAtomicNum() != 1
                or new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                or any(b.GetBondType() != Chem.BondType.SINGLE for atom in (old, new) for b in atom.GetBonds())):
            raise ValueError("The SN1 reacting carbon must remain unassigned in its validated ionization/capture edit.")
        if stage in {"net", "ionization"}:
            if (old.GetDegree() != 4 or old.GetHybridization() != Chem.HybridizationType.SP3
                    or old.GetFormalCharge() or leaving not in old_neighbors or incoming in old_neighbors):
                raise ValueError("SN1 configuration loss must start at the actual neutral tetrahedral C–halogen site.")
            if old.GetChiralTag() in TETRAHEDRAL and checked_original[center].GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("Invalid specified SN1 source configuration cannot be silently erased.")
        elif old.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("An SN1 carbocation/capture state cannot regain a specified reacting configuration.")
        if stage == "ionization":
            valid = (new_neighbors == old_neighbors - {leaving} and new.GetDegree() == 3
                     and new.GetHybridization() == Chem.HybridizationType.SP2 and new.GetFormalCharge() == 1
                     and product_atoms[leaving].GetFormalCharge() == -1)
        elif stage == "net":
            valid = (new_neighbors == (old_neighbors - {leaving}) | {incoming}
                     and new.GetDegree() == 4 and new.GetHybridization() == Chem.HybridizationType.SP3 and not new.GetFormalCharge())
        elif stage == "capture":
            valid = (old.GetDegree() == 3 and old.GetHybridization() == Chem.HybridizationType.SP2 and old.GetFormalCharge() == 1
                     and new_neighbors == old_neighbors | {incoming} and new.GetDegree() == 4
                     and new.GetHybridization() == Chem.HybridizationType.SP3 and not new.GetFormalCharge()
                     and product_atoms[incoming].GetFormalCharge() == 1)
        else:
            valid = (old_neighbors == new_neighbors and old.GetDegree() == new.GetDegree() == 4
                     and old.GetHybridization() == new.GetHybridization() == Chem.HybridizationType.SP3
                     and not old.GetFormalCharge() and not new.GetFormalCharge())
        if not valid:
            raise ValueError("SN1 configuration loss/unsigned capture did not follow the actual planar carbocation pathway.")
        solvolysed_centers.add(center)
    e1_centers, e1_formed = set(), set()
    for elimination in e1_eliminations:
        alpha, beta, hydrogen, leaving = (elimination[k] for k in ("alpha", "beta", "hydrogen", "leaving"))
        numbers = (alpha, beta, hydrogen, leaving); stage = elimination["stage"]
        if (stage not in {"net", "ionization", "elimination"} or len(set(numbers)) != 4
                or any(type(m) is not int or m <= 0 or m not in original_atoms or m not in product_atoms for m in numbers)
                or (e1_centers | lost_centers | solvolysed_centers).intersection((alpha, beta))):
            raise ValueError("E1 needs distinct exact mapped alpha/beta atoms and a uniquely declared elementary stage.")
        old, new = original_atoms[alpha], product_atoms[alpha]
        old_b, new_b = original_atoms[beta], product_atoms[beta]
        old_neighbors = {a.GetAtomMapNum() for a in old.GetNeighbors()}
        new_neighbors = {a.GetAtomMapNum() for a in new.GetNeighbors()}
        old_beta_neighbors = {a.GetAtomMapNum() for a in old_b.GetNeighbors()}
        new_beta_neighbors = {a.GetAtomMapNum() for a in new_b.GetNeighbors()}
        old_bond = before.GetBondBetweenAtoms(old.GetIdx(), old_b.GetIdx())
        new_bond = after.GetBondBetweenAtoms(new.GetIdx(), new_b.GetIdx())
        if (any(a.GetAtomicNum() != 6 for a in (old, new, old_b, new_b))
                or original_atoms[leaving].GetSymbol() not in {"Cl", "Br", "I"} or original_atoms[hydrogen].GetAtomicNum() != 1
                or old_b.GetDegree() != 4 or old_b.GetHybridization() != Chem.HybridizationType.SP3
                or old_b.GetFormalCharge() or hydrogen not in old_beta_neighbors
                or any(b.GetBondType() != Chem.BondType.SINGLE for b in old_b.GetBonds())
                or new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED or new.GetDegree() != 3
                or new.GetHybridization() != Chem.HybridizationType.SP2 or old_bond is None or old_bond.IsInRing()
                or old_bond.GetBondType() != Chem.BondType.SINGLE or new_bond is None):
            raise ValueError("E1 permission must follow an actual saturated beta-H and an unassigned planar reacting carbon.")
        if stage in {"net", "ionization"}:
            if (old.GetDegree() != 4 or old.GetHybridization() != Chem.HybridizationType.SP3 or old.GetFormalCharge()
                    or leaving not in old_neighbors or new_neighbors != old_neighbors - {leaving} or original_atoms[leaving].GetFormalCharge()
                    or any(b.GetBondType() != Chem.BondType.SINGLE for b in old.GetBonds())):
                raise ValueError("E1 ionization/net edit must start at the actual neutral tetrahedral C–X bond.")
            if old.GetChiralTag() in TETRAHEDRAL and checked_original[alpha].GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("Invalid source E1 tetrahedral configuration cannot be erased.")
        elif (old.GetDegree() != 3 or old.GetHybridization() != Chem.HybridizationType.SP2 or old.GetFormalCharge() != 1
              or old.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED or old_neighbors != new_neighbors
              or leaving in old_neighbors or original_atoms[leaving].GetFormalCharge() != -1):
            raise ValueError("E1 elimination must start from the unassigned positive carbocation, not a concerted E2 state.")
        if stage == "ionization":
            if (new.GetFormalCharge() != 1 or product_atoms[leaving].GetFormalCharge() != -1
                    or new_bond.GetBondType() != Chem.BondType.SINGLE or old_beta_neighbors != new_beta_neighbors):
                raise ValueError("E1 ionization must leave beta C–H/C–C intact and form the positive cation/halide.")
            e1_centers.add(alpha)
        else:
            if (new.GetFormalCharge() or new_b.GetFormalCharge() or new_b.GetDegree() != 3
                    or product_atoms[leaving].GetFormalCharge() != (0 if stage == "net" else -1)
                    or new_b.GetHybridization() != Chem.HybridizationType.SP2
                    or new_b.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                    or new_beta_neighbors != old_beta_neighbors - {hydrogen}
                    or new_bond.GetBondType() != Chem.BondType.DOUBLE or new_bond.GetStereo() != Chem.BondStereo.STEREONONE):
                raise ValueError("E1 beta-H loss must give the exact neutral unsigned alkene; E2 anti geometry cannot invent E/Z.")
            if old_b.GetChiralTag() in TETRAHEDRAL and checked_original[beta].GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("Invalid E1 beta configuration cannot be silently erased.")
            e1_centers.update((alpha, beta)); e1_formed.add(frozenset((alpha, beta)))
    eliminated_centers, formed_alkenes = set(), set(e1_formed)
    for elimination in eliminations:
        alpha, beta, hydrogen, leaving = (elimination[k] for k in ("alpha", "beta", "hydrogen", "leaving"))
        numbers = (alpha, beta, hydrogen, leaving)
        if (len(set(numbers)) != 4 or any(type(m) is not int or m <= 0 or m not in original_atoms or m not in product_atoms for m in numbers)
                or eliminated_centers.intersection((alpha, beta)) or lost_centers.intersection((alpha, beta)) or solvolysed_centers.intersection((alpha, beta)) or e1_centers.intersection((alpha, beta))):
            raise ValueError("E2 stereo consumption requires distinct, uniquely declared mapped reaction atoms.")
        for center, removed, element in ((alpha, leaving, {17, 35, 53}), (beta, hydrogen, {1})):
            old, new = original_atoms[center], product_atoms[center]
            old_neighbors = {a.GetAtomMapNum() for a in old.GetNeighbors()}
            new_neighbors = {a.GetAtomMapNum() for a in new.GetNeighbors()}
            if (old.GetAtomicNum() != 6 or new.GetAtomicNum() != 6 or old.GetDegree() != 4 or new.GetDegree() != 3
                    or old.GetHybridization() != Chem.HybridizationType.SP3 or new.GetHybridization() != Chem.HybridizationType.SP2
                    or old_neighbors - new_neighbors != {removed} or new_neighbors - old_neighbors
                    or original_atoms[removed].GetAtomicNum() not in element
                    or new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                    or any(b.GetBondType() != Chem.BondType.SINGLE for b in old.GetBonds())):
                raise ValueError("Only the actual C–H/C–halogen elimination centers may become unassigned planar alkene carbons.")
            if old.GetChiralTag() in TETRAHEDRAL and checked_original[center].GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("Invalid specified stereo at an E2 reacting center cannot be silently discarded.")
        old_bond = before.GetBondBetweenAtoms(original_atoms[alpha].GetIdx(), original_atoms[beta].GetIdx())
        new_bond = after.GetBondBetweenAtoms(product_atoms[alpha].GetIdx(), product_atoms[beta].GetIdx())
        if old_bond is None or old_bond.GetBondType() != Chem.BondType.SINGLE or old_bond.IsInRing() or new_bond is None or new_bond.GetBondType() != Chem.BondType.DOUBLE:
            raise ValueError("An E2 stereo permission needs its actual acyclic single-to-double C–C edit.")
        expected = e2_anti_stereo(before, elimination)
        if expected:
            refs = expected["referenceMaps"]
            if new_bond.GetStereo() not in DOUBLE_STEREO:
                raise ValueError("The specified local anti-E2 relationship was lost from the new alkene.")
            required_orientation = expected["sameSide"]
            # Compare physical sides of exact mapped references, not E/Z labels.
            neighbors, trans = _double_signature(new_bond)
            actual_trans = trans ^ (refs[0] != neighbors[alpha][0]) ^ (refs[1] != neighbors[beta][0])
            if actual_trans == required_orientation:
                raise ValueError("The new alkene disagrees with the specified local anti-E2 geometry.")
        elif new_bond.GetStereo() != Chem.BondStereo.STEREONONE:
            raise ValueError("E2 cannot invent E/Z from incompletely specified local configurations.")
        eliminated_centers.update((alpha, beta)); formed_alkenes.add(frozenset((alpha, beta)))
    inverted_centers = set()
    for substitution in inverted_substitutions:
        center, leaving, incoming = (substitution[k] for k in ("center", "leaving", "incoming"))
        if (any(type(m) is not int or m <= 0 or m not in original_atoms or m not in product_atoms for m in (center, leaving, incoming))
                or len({center, leaving, incoming}) != 3 or center in inverted_centers or center in lost_centers or center in eliminated_centers or center in solvolysed_centers or center in e1_centers):
            raise ValueError("SN2 inversion requires distinct, uniquely declared positive atom maps.")
        inverted_centers.add(center)
        old, new = checked_original[center], checked_product[center]
        if (old.GetAtomicNum() != 6 or new.GetAtomicNum() != 6 or old.GetDegree() != 4 or new.GetDegree() != 4
                or any(b.GetBondType() != Chem.BondType.SINGLE for atom in (old, new) for b in atom.GetBonds())
                or original_atoms[leaving].GetSymbol() not in {"Cl", "Br", "I"}
                or original_atoms[incoming].GetAtomicNum() != 8):
            raise ValueError("This inversion contract requires an ordinary tetrahedral C–halogen to C–O substitution.")
        old_neighbors = [a.GetAtomMapNum() for a in old.GetNeighbors()]
        desired = [incoming if m == leaving else m for m in old_neighbors]
        actual = [a.GetAtomMapNum() for a in new.GetNeighbors()]
        if leaving not in old_neighbors or incoming in old_neighbors or set(desired) != set(actual):
            raise ValueError("SN2 inversion neighbor replacement did not match the mapped leaving group and nucleophile.")
        original_tag = original_atoms[center].GetChiralTag()
        if original_tag in TETRAHEDRAL:
            if old.GetChiralTag() not in TETRAHEDRAL or new.GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("The reacting SN2 center has invalid or no-longer-stereogenic specified stereo; this case is not silently erased.")
            parity = sum(desired[i] > desired[j] for i in range(4) for j in range(i + 1, 4)) % 2
            old_orientation_with_replacement = (old.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(parity)
            if _tetra_signature(new)[1] == old_orientation_with_replacement:
                raise ValueError("SN2 must invert the mapped physical configuration, not retain it or merely change a CIP letter.")
            if product_atoms[center].GetChiralTag() not in TETRAHEDRAL:
                raise ValueError("The specified reacting SN2 configuration was lost.")
        elif new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED or product_atoms[center].GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("SN2 cannot invent a specified configuration at an unsigned reacting center.")
    for number in lost_centers:
        old, new = original_atoms.get(number), product_atoms.get(number)
        if (old is None or new is None or old.GetAtomicNum() != 6 or new.GetAtomicNum() != 6
                or old.GetChiralTag() not in TETRAHEDRAL or old.GetDegree() != 4
                or old.GetHybridization() != Chem.HybridizationType.SP3
                or new.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED or new.GetDegree() != 3
                or new.GetHybridization() != Chem.HybridizationType.SP2):
            raise ValueError("Only a specified alcohol carbon that becomes an unassigned planar carbonyl may consume its tetrahedral configuration.")
        old_neighbors = {a.GetAtomMapNum(): a for a in old.GetNeighbors()}
        new_neighbors = {a.GetAtomMapNum(): a for a in new.GetNeighbors()}
        removed = old_neighbors.keys() - new_neighbors.keys()
        carbonyls = [b for b in new.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(new).GetAtomicNum() == 8]
        if (len(removed) != 1 or any(old_neighbors[m].GetAtomicNum() != 1 for m in removed)
                or new_neighbors.keys() - old_neighbors.keys() or len(carbonyls) != 1
                or any(b.GetBondType() != Chem.BondType.SINGLE for b in old.GetBonds())):
            raise ValueError("Consumed alcohol-center stereo must follow the actual C–H loss and C–O-to-C=O edit.")
        oxygen = carbonyls[0].GetOtherAtom(new).GetAtomMapNum()
        if (oxygen not in old_neighbors or old_neighbors[oxygen].GetDegree() != 2
                or sum(n.GetAtomicNum() == 1 for n in old_neighbors[oxygen].GetNeighbors()) != 1
                or product_atoms[oxygen].GetDegree() != 1):
            raise ValueError("A consumed alcohol center must retain its original oxygen.")
    def signatures(original, checked):
        tetra, double = {}, {}
        for atom, clean in zip(original.GetAtoms(), checked.GetAtoms()):
            if atom.GetAtomMapNum() in inverted_centers | eliminated_centers | solvolysed_centers | e1_centers:
                continue  # Independently checked mapped neighbor replacement/inversion.
            if atom.GetChiralTag() in TETRAHEDRAL:
                if clean.GetChiralTag() not in TETRAHEDRAL:
                    raise ValueError(f"Specified tetrahedral configuration at atom map {atom.GetAtomMapNum()} is no longer retainable (invalid or no longer stereogenic); it is not silently discarded.")
                if atom.GetAtomMapNum() in lost_centers:
                    continue  # Only the separately checked reactive alcohol center.
                tetra[atom.GetAtomMapNum()] = _tetra_signature(clean)
        for bond in checked.GetBonds():
            key = frozenset((bond.GetBeginAtom().GetAtomMapNum(), bond.GetEndAtom().GetAtomMapNum()))
            if key in consumed | formed_alkenes:
                continue  # Only the explicitly authorized reactive C=C may lose E/Z.
            original_bond = original.GetBondWithIdx(bond.GetIdx())
            if original_bond.GetStereo() in DOUBLE_STEREO and bond.GetStereo() not in DOUBLE_STEREO:
                raise ValueError("A specified alkene configuration was invalid or lost.")
            if original_bond.GetStereo() in DOUBLE_STEREO and _double_signature(original_bond) != _double_signature(bond):
                raise ValueError("Contradictory alkene stereo tags and bond directions cannot be retained.")
            if bond.GetStereo() in DOUBLE_STEREO:
                key = frozenset((bond.GetBeginAtom().GetAtomMapNum(), bond.GetEndAtom().GetAtomMapNum()))
                double[key] = _double_signature(bond)
        return tetra, double
    if signatures(before, checked_before) != signatures(after, checked_after):
        raise ValueError(f"{context} did not retain the specified mapped configurations.")


def e2_anti_stereo(before, elimination):
    """Bounded local anti-E2 relationship, independent of an embedded conformer.

Only two specified tetrahedral reacting centers with one actual beta H determine
a unique alkene relationship here. Ideal tetrahedral coordinates encode their
mapped parity and an anti H/X arrangement, NOT an energetic transition state.
Unsigned/CH2/CH3 sites do not gain a stereochemical prediction.
"""
    from rdkit.Geometry import Point3D
    atoms = {a.GetAtomMapNum(): a for a in _checked_stereo(before).GetAtoms()}
    alpha, beta, hydrogen, leaving = (elimination[k] for k in ("alpha", "beta", "hydrogen", "leaving"))
    a, b = atoms[alpha], atoms[beta]
    if any(atom.GetChiralTag() not in TETRAHEDRAL for atom in (a, b)):
        return None
    if sum(n.GetAtomicNum() == 1 for n in b.GetNeighbors()) != 1:
        return None
    refs = [[n.GetAtomMapNum() for n in atom.GetNeighbors() if n.GetAtomMapNum() not in removed]
            for atom, removed in ((a, {beta, leaving}), (b, {alpha, hydrogen}))]
    if any(len(pair) != 2 for pair in refs) or a.IsInRing() or b.IsInRing():
        raise ValueError("This local anti-E2 stereo model requires two ordinary acyclic tetrahedra.")
    refs = [sorted(pair) for pair in refs]
    work = Chem.Mol(before); work.RemoveAllConformers()
    conf = Chem.Conformer(work.GetNumAtoms()); conf.Set3D(True)
    # Only the two local tetrahedra are used. No remote conformer is inferred.
    indexed = {x.GetAtomMapNum(): x.GetIdx() for x in work.GetAtoms()}
    positions = {alpha: (0, 0, 0), beta: (1, 0, 0), leaving: (-1/3, -math.sqrt(8)/3, 0),
                 hydrogen: (4/3, math.sqrt(8)/3, 0)}
    for r, origin, x, y in ((refs[0], 0, -1/3, math.sqrt(2)/3), (refs[1], 1, 1/3, -math.sqrt(2)/3)):
        positions[r[0]] = (origin + x, y, math.sqrt(6)/3)
        positions[r[1]] = (origin + x, y, -math.sqrt(6)/3)
    for number, point in positions.items():
        conf.SetAtomPosition(indexed[number], Point3D(*point))
    work.AddConformer(conf)
    for center, pair in ((alpha, refs[0]), (beta, refs[1])):
        measured = Chem.Mol(work)
        Chem.AssignAtomChiralTagsFromStructure(measured, replaceExistingTags=True)
        if _tetra_signature(measured.GetAtomWithIdx(indexed[center]))[1] != _tetra_signature(atoms[center])[1]:
            p, q = pair
            point_p, point_q = conf.GetAtomPosition(indexed[p]), conf.GetAtomPosition(indexed[q])
            work.GetConformer().SetAtomPosition(indexed[p], point_q)
            work.GetConformer().SetAtomPosition(indexed[q], point_p)
    measured = Chem.Mol(work); Chem.AssignAtomChiralTagsFromStructure(measured, replaceExistingTags=True)
    if any(_tetra_signature(measured.GetAtomWithIdx(indexed[c]))[1] != _tetra_signature(atoms[c])[1] for c in (alpha, beta)):
        raise ValueError("The local anti-E2 construction did not retain both source configurations.")
    zs = [work.GetConformer().GetAtomPosition(indexed[pair[0]]).z for pair in refs]
    return {"referenceMaps": [pair[0] for pair in refs], "sameSide": zs[0] * zs[1] > 0,
            "basis": "both specified local tetrahedra and a unique beta H in the acyclic anti model"}


def invert_sn2(before, editor, carbon_map, leaving_map, incoming_map):
    """Invert physical tetrahedral configuration, accounting for neighbor order.

R/S can stay the same when replacing the leaving group changes CIP priorities.
Never implement inversion by merely exchanging the letters R and S.
"""
    original = next(a for a in before.GetAtoms() if a.GetAtomMapNum() == carbon_map)
    current = next(a for a in editor.GetAtoms() if a.GetAtomMapNum() == carbon_map)
    tag = original.GetChiralTag()
    if tag == Chem.ChiralType.CHI_UNSPECIFIED:
        return False
    if tag not in {Chem.ChiralType.CHI_TETRAHEDRAL_CW, Chem.ChiralType.CHI_TETRAHEDRAL_CCW} or original.GetDegree() != 4 or current.GetDegree() != 4:
        raise ValueError("SN2 inversion needs an explicit four-neighbor tetrahedral center.")
    desired = [incoming_map if a.GetAtomMapNum() == leaving_map else a.GetAtomMapNum() for a in original.GetNeighbors()]
    actual = [a.GetAtomMapNum() for a in current.GetNeighbors()]
    if leaving_map not in [a.GetAtomMapNum() for a in original.GetNeighbors()] or set(desired) != set(actual):
        raise ValueError("SN2 neighbor correspondence failed.")
    order = [desired.index(m) for m in actual]
    odd = sum(order[i] > order[j] for i in range(4) for j in range(i + 1, 4)) % 2
    current.SetChiralTag(tag)
    if odd:
        current.InvertChirality()  # preserve configuration after atom replacement
    current.InvertChirality()      # then perform backside inversion
    return True


def anti_periplanar(molecule, hydrogen_map, beta_map, alpha_map, leaving_map, tolerance=15):
    """Measure H–Cβ–Cα–X torsion of an explicit, supplied 3D conformer."""
    if not math.isfinite(tolerance) or not 0 <= tolerance <= 30:
        raise ValueError("Anti-periplanar tolerance must be between 0 and 30 degrees.")
    maps = [hydrogen_map, beta_map, alpha_map, leaving_map]
    indexed = {a.GetAtomMapNum(): a for a in molecule.GetAtoms()}
    if len(set(maps)) != 4 or any(m not in indexed for m in maps):
        raise ValueError("Select four distinct, mapped atoms.")
    atoms = [indexed[m] for m in maps]
    if [a.GetSymbol() for a in atoms[:3]] != ["H", "C", "C"] or atoms[3].GetSymbol() not in {"F", "Cl", "Br", "I"}:
        raise ValueError("Select a beta H, beta C, alpha C and halogen leaving group.")
    bonds = [molecule.GetBondBetweenAtoms(atoms[i].GetIdx(), atoms[i + 1].GetIdx()) for i in range(3)]
    if any(b is None or b.GetBondType() != Chem.BondType.SINGLE for b in bonds):
        raise ValueError("The selected atoms do not form a single-bond H–Cβ–Cα–X chain.")
    if not molecule.GetNumConformers() or not molecule.GetConformer().Is3D():
        raise ValueError("An actual 3D conformer is required, not a 2D drawing.")
    points = [tuple(molecule.GetConformer().GetAtomPosition(a.GetIdx())) for a in atoms]
    if any(not math.isfinite(v) for p in points for v in p):
        raise ValueError("Non-finite coordinates cannot be measured.")
    def sub(a, b): return tuple(x - y for x, y in zip(a, b))
    def dot(a, b): return sum(x * y for x, y in zip(a, b))
    def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    axis = sub(points[2], points[1]); length = math.sqrt(dot(axis, axis))
    if length < 1e-9:
        raise ValueError("Degenerate torsion geometry.")
    axis = tuple(x / length for x in axis)
    a, b = sub(points[0], points[1]), sub(points[3], points[2])
    v = sub(a, tuple(dot(a, axis) * x for x in axis)); w = sub(b, tuple(dot(b, axis) * x for x in axis))
    if dot(v, v) < 1e-12 or dot(w, w) < 1e-12:
        raise ValueError("Collinear atoms do not define a torsion.")
    angle = math.degrees(math.atan2(dot(cross(axis, v), w), dot(v, w)))
    return {"atomMaps": maps, "dihedralDegrees": round(angle, 3), "toleranceDegrees": tolerance,
            "antiPeriplanar": 180 - abs(angle) <= tolerance,
            "note": "One supplied conformer only; not a conformer search, E/Z prediction or reaction-rate claim."}


def e2_geometry_sites(molecule):
    """Enumerate actual beta-H torsions in a provided conformer, not eligibility."""
    results = []
    for leaving in molecule.GetAtoms():
        if leaving.GetSymbol() not in {"Cl", "Br", "I"}: continue
        for alpha in leaving.GetNeighbors():
            if alpha.GetSymbol() != "C" or alpha.GetHybridization() != Chem.HybridizationType.SP3: continue
            for beta in alpha.GetNeighbors():
                if beta.GetSymbol() != "C" or beta.GetHybridization() != Chem.HybridizationType.SP3: continue
                for hydrogen in beta.GetNeighbors():
                    if hydrogen.GetSymbol() != "H": continue
                    try:
                        results.append(anti_periplanar(molecule, *[a.GetAtomMapNum() for a in (hydrogen, beta, alpha, leaving)]))
                    except ValueError:
                        continue
    return results
