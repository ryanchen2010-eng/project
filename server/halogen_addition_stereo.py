"""Halogen-independent opposite-face parity, not a halogen chemistry policy.

Reuse the already validated mapped reference/parity helpers without changing
the Br2 API or behavior. Callers validate their own reagent and environment.
The element is never inferred from this module or from map ordering.
"""
if __package__:
    from .bromination_stereo import references, local_centers, normalized_tag, set_tag, specification, projected_product, stereo
else:
    from bromination_stereo import references, local_centers, normalized_tag, set_tag, specification, projected_product, stereo
from rdkit import Chem


def apply(substrate, editor, p, face, *, incoming_key):
    refs, same, _, centers, assigned = specification(substrate, editor, p)
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    for i, number in enumerate(p["alkene"]):
        atom = atoms[number]
        atom.SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
        if assigned and number in centers:
            # In the exact order [other C, ref0, ref1, entering halogen], opposite
            # halogen faces give equal tetrahedral parity iff refs are same-side.
            value = bool(face) if i == 0 else bool(face) ^ (same is False)
            set_tag(atom, [p["alkene"][1-i], *refs[i], p[incoming_key][i]], value)


def validate(substrate, product, p, face, *, incoming_key):
    refs, same, _, centers, assigned = specification(substrate, product, p)
    atoms = {a.GetAtomMapNum(): a for a in product.GetAtoms()}
    clean = stereo._checked_stereo(product)
    checked = {a.GetAtomMapNum(): a for a in clean.GetAtoms()}
    parities = []
    for i, number in enumerate(p["alkene"]):
        tag = atoms[number].GetChiralTag()
        if assigned and number in centers:
            expected = bool(face) if i == 0 else bool(face) ^ (same is False)
            order = [p["alkene"][1-i], *refs[i], p[incoming_key][i]]
            if normalized_tag(checked[number], order) != expected:
                raise ValueError("The product disagrees with the selected opposite-face halogen-addition alternative.")
            parities.append(normalized_tag(checked[number], order))
        elif tag != Chem.ChiralType.CHI_UNSPECIFIED:
            raise ValueError("Halogen addition cannot invent stereo from unknown starting geometry or at a non-stereogenic center.")
    if len(parities) == 2 and (parities[0] == parities[1]) != same:
        raise ValueError("The local mapped relative configurations are syn, not the validated anti relationship.")


