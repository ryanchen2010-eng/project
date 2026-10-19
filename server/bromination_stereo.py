"""Local, map-referenced anti Br2 stereo; no sampled conformer decides products.

The two faces are alternatives, not predicted populations. E/Z supplies the
relationship of exact substituents; an ordinary small monocycle supplies its
two ring references. Unknown alkene geometry is never guessed.
"""
from rdkit import Chem
if __package__:
    from . import stereochemistry as stereo
else:
    import stereochemistry as stereo


def references(substrate, ends):
    bond = substrate.GetBondBetweenAtoms(*ends)
    # Explicit H is required; maps are identities, never CIP priorities.
    refs = [[n.GetAtomMapNum() for n in substrate.GetAtomWithIdx(i).GetNeighbors() if n.GetIdx() not in ends] for i in ends]
    if any(len(r) != 2 for r in refs):
        raise ValueError("Anti addition requires the actual two substituents at each explicit-H alkene end.")
    refs = [sorted(r) for r in refs]
    if bond.GetStereo() in stereo.DOUBLE_STEREO:
        neighbors, trans = stereo._double_signature(bond)
        return refs, not trans, "specified mapped alkene geometry"
    if bond.IsInRing():
        rings = [r for r in substrate.GetRingInfo().AtomRings() if set(ends) <= set(r)]
        if len(rings) == 1 and 5 <= len(rings[0]) <= 7:
            ring_refs = [[n.GetAtomMapNum() for n in substrate.GetAtomWithIdx(i).GetNeighbors()
                          if n.GetIdx() in rings[0] and n.GetIdx() not in ends][0] for i in ends]
            same = True ^ (refs[0][0] != ring_refs[0]) ^ (refs[1][0] != ring_refs[1])
            return refs, same, "cis ring paths in an isolated 5–7-membered carbocycle"
    return refs, None, "starting alkene geometry unspecified"


def local_centers(product, maps):
    copy = Chem.Mol(product)
    for atom in copy.GetAtoms(): atom.SetAtomMapNum(0)
    Chem.AssignStereochemistry(copy, cleanIt=True, force=True)
    return {product.GetAtomWithIdx(info.centeredOn).GetAtomMapNum() for info in Chem.FindPotentialStereo(copy)
            if info.type == Chem.StereoType.Atom_Tetrahedral and product.GetAtomWithIdx(info.centeredOn).GetAtomMapNum() in maps}


def normalized_tag(atom, order):
    actual = [n.GetAtomMapNum() for n in atom.GetNeighbors()]
    if len(actual) != 4 or set(actual) != set(order) or atom.GetChiralTag() not in stereo.TETRAHEDRAL:
        raise ValueError("The newly formed bromination tetrahedron is missing or invalid.")
    permutation = [order.index(m) for m in actual]
    odd = sum(permutation[i] > permutation[j] for i in range(4) for j in range(i + 1, 4)) % 2
    return bool(atom.GetChiralTag() == Chem.ChiralType.CHI_TETRAHEDRAL_CW) ^ bool(odd)


def set_tag(atom, order, value):
    atom.SetChiralTag(Chem.ChiralType.CHI_TETRAHEDRAL_CW)
    if normalized_tag(atom, order) != value: atom.InvertChirality()


def specification(substrate, product, p):
    ends = [next(a.GetIdx() for a in substrate.GetAtoms() if a.GetAtomMapNum() == m) for m in p["alkene"]]
    refs, same, basis = references(substrate, ends)
    centers = local_centers(product, p["alkene"])
    assigned = bool(centers) and (same is not None or len(centers) == 1)
    return refs, same, basis, centers, assigned


def apply(substrate, editor, p, face):
    refs, same, _, centers, assigned = specification(substrate, editor, p)
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    for i, number in enumerate(p["alkene"]):
        atom = atoms[number]
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        if assigned and number in centers:
            # In the exact order [other C, ref0, ref1, entering Br], opposite
            # Br faces give equal tetrahedral parity iff refs are same-side.
            value = bool(face) if i == 0 else bool(face) ^ (same is False)
            set_tag(atom, [p["alkene"][1-i], *refs[i], p["bromines"][i]], value)


def validate(substrate, product, p, face):
    refs, same, _, centers, assigned = specification(substrate, product, p)
    atoms = {a.GetAtomMapNum(): a for a in product.GetAtoms()}
    clean = stereo._checked_stereo(product)
    checked = {a.GetAtomMapNum(): a for a in clean.GetAtoms()}
    parities = []
    for i, number in enumerate(p["alkene"]):
        tag = atoms[number].GetChiralTag()
        if assigned and number in centers:
            expected = bool(face) if i == 0 else bool(face) ^ (same is False)
            order = [p["alkene"][1-i], *refs[i], p["bromines"][i]]
            if normalized_tag(checked[number], order) != expected:
                raise ValueError("The product disagrees with the selected opposite-face bromination alternative.")
            parities.append(normalized_tag(checked[number], order))
        elif tag != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("Bromination cannot invent stereo from unknown starting geometry or at a non-stereogenic center.")
    if len(parities) == 2 and (parities[0] == parities[1]) != same:
        raise ValueError("The local mapped relative configurations are syn, not the validated anti relationship.")


def projected_product(product, p):
    """For the unchanged spectator validator, mask ONLY independently checked
    newly formed tags at the two actual sp2-to-sp3 reaction atoms. Full local
    stereo is separately validated before AND after mapped serialization.
    No spectator stereo, bond, map or charge is masked.
    """
    copy = Chem.Mol(product)
    for atom in copy.GetAtoms():
        if atom.GetAtomMapNum() in p["alkene"]:
            atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    return copy
