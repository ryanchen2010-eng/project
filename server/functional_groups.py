"""Inspect actual molecular graphs; group recognition is not reaction approval."""
from html import escape
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

if __package__:
    from .reaction_diagrams import _species, _molecule_svg
    from .reaction_information import group_reactions
    from .stereochemistry import inspect_stereochemistry, e2_geometry_sites
else:
    from reaction_diagrams import _species, _molecule_svg
    from reaction_information import group_reactions
    from stereochemistry import inspect_stereochemistry, e2_geometry_sites

# Inspection is deliberately broader than eligibility (e.g. aromatic amines,
# phenyl esters and alkyl fluoride). Maps address the exact inspected graph.
PATTERNS = {
    "alkene": "[C;!a]=[C;!a]",
    "alkyne": "[C]#[C]",
    "alcohol": "[C;X4]-[O;H1;+0]",
    "aldehyde": "[C;H1,H2](=[O])-[#6,#1]",
    "ketone": "[#6]-[C](=[O])-[#6]",
    "carboxylic acid": "[C](=[O])-[O;H1;+0]",
    "ester": "[#6,#1]-[C](=[O])-[O;H0;+0]-[#6]",
    "amine": "[N;X3;+0;!a;!$(N-C=O);!$(N-S);!$(N-P)]",
    "amide": "[C](=[O])-[N]",
    "haloalkane": "[C;X4]-[F,Cl,Br,I]",
    "peroxyacid": "[C](=[O])-[O;H0;+0]-[O;H1;+0]",
}
QUERIES = {name: Chem.MolFromSmarts(pattern) for name, pattern in PATTERNS.items()}


def detect_groups(molecule):
    groups = []
    for name, query in QUERIES.items():
        # Formaldehyde has no carbon substituent in a hydrogen-suppressed graph.
        matches = list(molecule.GetSubstructMatches(query, uniquify=True))
        if name == "aldehyde":
            matches.extend(molecule.GetSubstructMatches(Chem.MolFromSmarts("[C;H2]=[O]")))
        for match in matches:
            if name == "amine":
                neighbors = list(molecule.GetAtomWithIdx(match[0]).GetNeighbors())
                if not any(a.GetAtomicNum() == 6 for a in neighbors) or any(a.GetAtomicNum() not in {1, 6} for a in neighbors):
                    continue
            if name == "carboxylic acid" and any(a.GetIdx() not in match and a.GetAtomicNum() not in {1, 6}
                    for a in molecule.GetAtomWithIdx(match[0]).GetNeighbors()):
                continue
            # Include group atoms, not generic scaffold anchors.
            indices = match[1:] if name == "ester" else match[1:3] if name == "ketone" else match[:2] if name == "aldehyde" else match
            maps = sorted({molecule.GetAtomWithIdx(i).GetAtomMapNum() for i in indices})
            if any(g["type"] == name and g["atomMaps"] == maps for g in groups):
                continue
            groups.append({"id": name.replace(" ", "-") + "-" + "-".join(map(str, maps)), "type": name,
                           "label": name.capitalize(), "atomMaps": maps, "reactions": group_reactions(name)})
    for ring in molecule.GetRingInfo().AtomRings():
        if all(molecule.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
            maps = sorted(molecule.GetAtomWithIdx(i).GetAtomMapNum() for i in ring)
            groups.append({"id": "aromatic-ring-" + "-".join(map(str, maps)), "type": "aromatic ring",
                           "label": "Aromatic ring", "atomMaps": maps, "reactions": []})
    return groups


def inspect_structure(reference, catalog, include_3d=False, analyze=None):
    if not isinstance(include_3d, bool):
        raise ValueError("include3D must be true or false.")
    if isinstance(reference, str) and reference in catalog:
        entry = catalog[reference]
    elif isinstance(reference, dict) and isinstance(reference.get("smiles"), str):
        entry = {"name": str(reference.get("name") or "Selected molecule")[:120], "smiles": reference["smiles"]}
    else:
        raise ValueError("Select an exact molecule structure to inspect.")
    if not entry["smiles"] or len(entry["smiles"]) > 4000:
        raise ValueError("This structure is empty or too large to inspect.")
    molecule = Chem.MolFromSmiles(entry["smiles"])
    if molecule is None or not molecule.GetNumAtoms() or any(a.HasQuery() for a in molecule.GetAtoms()):
        raise ValueError("This structure could not be read.")
    if molecule.GetNumAtoms() > 80 or Chem.AddHs(molecule).GetNumAtoms() > 80:
        raise ValueError("Group inspection supports at most 80 atoms including hydrogens.")
    item, _ = _species("inspection", entry, 1)
    explicit = item["mol"]
    groups = detect_groups(explicit)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 300" role="img" '
           'aria-label="' + escape(entry["name"] + " functional groups", quote=True) + '">' +
           _molecule_svg(item, [], "reactants", 0, set(), 480, 300) + '</svg>')
    payload = {"name": entry["name"], "formula": rdMolDescriptors.CalcMolFormula(molecule),
               "groups": groups, "svg": svg, "stereochemistry": inspect_stereochemistry(explicit),
               "note": "Group-level suggestions only. A reaction also needs a supported partner, site and conditions."}
    if include_3d and analyze:
        payload["model"] = analyze(Chem.MolToMolBlock(explicit))
        if payload["model"].get("representation") == "3d":
            conformer = Chem.MolFromMolBlock(payload["model"]["molfile"], removeHs=False)
            payload["e2Geometry"] = e2_geometry_sites(conformer)
    return payload
