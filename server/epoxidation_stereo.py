"""Same-face oxygen transfer, independent of halogen anti-addition chemistry.

Only mapped reference/permutation helpers are reused. One O becomes a neighbor
of both carbons. No conformer, CIP letter swap or face population chooses tags.
"""
from rdkit import Chem
if __package__:
    from .bromination_stereo import specification, normalized_tag, set_tag, projected_product
    from . import stereochemistry as stereo
else:
    from bromination_stereo import specification, normalized_tag, set_tag, projected_product
    import stereochemistry as stereo


def apply(substrate, editor, p, face):
    refs, same, _, centers, assigned = specification(substrate, editor, p)
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    for i, number in enumerate(p["alkene"]):
        atom = atoms[number]
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        if assigned and number in centers:
            # For [other C, ref0, ref1, O], SAME oxygen face requires
            # opposite parity iff ref0 groups were on the same side.
            value = bool(face) if i == 0 else bool(face) ^ (same is True)
            set_tag(atom, [p["alkene"][1-i], *refs[i], p["transferredOxygen"]], value)


def validate(substrate, product, p, face):
    refs, same, _, centers, assigned = specification(substrate, product, p)
    atoms = {a.GetAtomMapNum(): a for a in product.GetAtoms()}
    checked = {a.GetAtomMapNum(): a for a in stereo._checked_stereo(product).GetAtoms()}
    parities = []
    for i, number in enumerate(p["alkene"]):
        if assigned and number in centers:
            expected = bool(face) if i == 0 else bool(face) ^ (same is True)
            parity = normalized_tag(checked[number], [p["alkene"][1-i], *refs[i], p["transferredOxygen"]])
            if parity != expected:
                raise ValueError("Epoxide configuration disagrees with the selected same-face oxygen-transfer alternative.")
            parities.append(parity)
        elif atoms[number].GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("Epoxidation cannot invent geometry at an unknown or non-stereogenic center.")
    if len(parities) == 2 and (parities[0] != parities[1]) != same:
        raise ValueError("The epoxide does not retain the mapped alkene substituent relationship.")
