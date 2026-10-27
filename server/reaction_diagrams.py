"""RDKit net-reaction diagrams with verified, rule-based atom correspondence.

The transformations here mirror Reaction Lab's reviewed rules. They are net
bond changes, not curved-arrow mechanisms or stereochemical predictions. No
formula matching or maximum-common-substructure mapping is used for highlights.
"""

from __future__ import annotations

from html import escape
from math import atan2, cos, hypot, pi, sin, sqrt
import re
from typing import Any
import xml.etree.ElementTree as ET

from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D


COLORS = {
    "broken": "#c14d58",
    "formed": "#2875b8",
    "order": "#b87916",
}
LABELS = {"broken": "Bond broken", "formed": "Bond formed", "order": "Bond order changed"}
VALENCE_ELECTRONS = {"H": 1, "B": 3, "C": 4, "N": 5, "O": 6, "F": 7,
                     "Si": 4, "P": 5, "S": 6, "Cl": 7, "Br": 7, "I": 7}


def _mol(smiles: str) -> Chem.Mol:
    if not isinstance(smiles, str) or not smiles or len(smiles) > 2048:
        raise ValueError("A reaction diagram needs a valid structure.")
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None or not 0 < molecule.GetNumAtoms() <= 80:
        raise ValueError("A reaction diagram needs a valid structure of at most 80 atoms.")
    return molecule


def _identity(molecule: Chem.Mol) -> str:
    copy = Chem.Mol(molecule)
    for atom in copy.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.RemoveHs(copy), canonical=True)


def _species(identifier: str, source: dict[str, Any], next_map: int) -> tuple[dict[str, Any], int]:
    if not isinstance(source, dict) or not isinstance(source.get("name"), str):
        raise ValueError("A reaction diagram needs named structures.")
    mol = Chem.AddHs(_mol(source.get("smiles")))
    for atom in mol.GetAtoms():
        if atom.GetAtomMapNum():
            # Different reactants may reuse source map numbers; keep provenance
            # alongside the reaction's unique IDs rather than dropping it.
            atom.SetIntProp("sourceAtomMap", atom.GetAtomMapNum())
        atom.SetAtomMapNum(next_map)
        next_map += 1
    return {"id": identifier, "name": source["name"][:100], "mol": mol}, next_map


def _combine(items: list[dict[str, Any]]) -> Chem.Mol:
    result = Chem.Mol(items[0]["mol"])
    for item in items[1:]:
        result = Chem.CombineMols(result, item["mol"])
    return result


def _index(molecule: Chem.Mol, atom_map: int) -> int:
    return next(atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomMapNum() == atom_map)


def _maps(molecule: Chem.Mol, symbol: str) -> list[int]:
    return [atom.GetAtomMapNum() for atom in molecule.GetAtoms() if atom.GetSymbol() == symbol]


def _hydrogens(molecule: Chem.Mol, atom_map: int) -> list[int]:
    return [atom.GetAtomMapNum() for atom in molecule.GetAtomWithIdx(_index(molecule, atom_map)).GetNeighbors()
            if atom.GetSymbol() == "H"]


def _remove(editor: Chem.RWMol, first: int, second: int) -> None:
    editor.RemoveBond(_index(editor, first), _index(editor, second))


def _add(editor: Chem.RWMol, first: int, second: int, order: int = 1) -> None:
    editor.AddBond(_index(editor, first), _index(editor, second),
                   Chem.BondType.DOUBLE if order == 2 else Chem.BondType.SINGLE)


def _order(editor: Chem.RWMol, first: int, second: int, order: int) -> None:
    bond = editor.GetBondBetweenAtoms(_index(editor, first), _index(editor, second))
    if bond is None:
        raise ValueError("A reaction rule did not find its changing bond.")
    bond.SetBondType(Chem.BondType.DOUBLE if order == 2 else Chem.BondType.SINGLE)


def _charge(editor: Chem.RWMol, atom_map: int, value: int) -> None:
    editor.GetAtomWithIdx(_index(editor, atom_map)).SetFormalCharge(value)


def _finish(editor: Chem.RWMol) -> Chem.Mol:
    result = editor.GetMol()
    Chem.SanitizeMol(result)
    return result


def _split_like_expected(molecule: Chem.Mol, expected: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Assign whole product fragments by identity, including multi-part salts."""
    fragments = list(Chem.GetMolFrags(molecule, asMols=True))
    products = []
    for item in expected:
        assembled = None
        for expected_fragment in Chem.GetMolFrags(_mol(item["smiles"]), asMols=True):
            wanted = _identity(expected_fragment)
            match = next((index for index, fragment in enumerate(fragments)
                          if _identity(fragment) == wanted), None)
            if match is None:
                return None
            fragment = fragments.pop(match)
            assembled = fragment if assembled is None else Chem.CombineMols(assembled, fragment)
        products.append({"name": item["name"], "mol": assembled})
    return products if not fragments else None




def _bond_map(items: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    result = {}
    for item in items:
        for bond in item["mol"].GetBonds():
            atoms = (bond.GetBeginAtom(), bond.GetEndAtom())
            maps = tuple(sorted(atom.GetAtomMapNum() for atom in atoms))
            ordered = sorted(atoms, key=lambda atom: atom.GetAtomMapNum())
            result[maps] = {"order": bond.GetBondTypeAsDouble(), "symbols": [atom.GetSymbol() for atom in ordered]}
    return result


def _changes(inputs: list[dict[str, Any]], outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before, after = _bond_map(inputs), _bond_map(outputs)
    changes = []
    for maps in sorted(before.keys() | after.keys()):
        previous, current = before.get(maps), after.get(maps)
        if previous == current:
            continue
        kind = "formed" if previous is None else "broken" if current is None else "order"
        symbols = (current or previous)["symbols"]
        changes.append({"kind": kind, "atomMaps": list(maps), "atoms": symbols,
                        "before": previous["order"] if previous else None,
                        "after": current["order"] if current else None,
                        "label": f"{'–'.join(symbols)} {LABELS[kind].lower()}"})
    return changes


def _lone_pairs(atom: Chem.Atom) -> int | None:
    """Count pairs only for readable, closed-shell main-group Lewis atoms.

    This is electron bookkeeping, not a prediction of orbital orientation.
    Aromatic atoms, radicals, and atoms coordinated to metals are deliberately
    omitted rather than receiving guessed dots.
    """
    symbol = atom.GetSymbol()
    if symbol not in VALENCE_ELECTRONS or atom.GetIsAromatic() or atom.GetNumRadicalElectrons():
        return None
    if any(neighbor.GetSymbol() not in VALENCE_ELECTRONS for neighbor in atom.GetNeighbors()):
        return None
    bonds = list(atom.GetBonds())
    if any(bond.GetIsAromatic() or bond.GetBondType() not in
           (Chem.BondType.SINGLE, Chem.BondType.DOUBLE, Chem.BondType.TRIPLE) for bond in bonds):
        return None
    nonbonding = VALENCE_ELECTRONS[symbol] - atom.GetFormalCharge() - sum(bond.GetBondTypeAsDouble() for bond in bonds)
    if nonbonding < 0 or nonbonding > 8 or nonbonding % 2:
        return None
    return int(nonbonding / 2)


def _rgb(color: str) -> tuple[float, float, float]:
    return tuple(int(color[position:position + 2], 16) / 255 for position in (1, 3, 5))


def _atom_metadata(item: dict[str, Any], side: str, species_index: int,
                   product_maps: set[int]) -> list[dict[str, Any]]:
    names = Chem.GetPeriodicTable()
    return [{"mapId": atom.GetAtomMapNum(), "element": atom.GetSymbol(),
             "label": f"{names.GetElementName(atom.GetAtomicNum())} {atom.GetAtomMapNum()}",
             "side": side, "speciesIndex": species_index, "speciesName": item["name"],
             "atomIndex": atom.GetIdx(), "formalCharge": atom.GetFormalCharge(),
             "lonePairs": _lone_pairs(atom), "linkedTo3D": atom.GetAtomMapNum() in product_maps}
            for atom in item["mol"].GetAtoms()]


def _label_layout(drawing: str, molecule: Chem.Mol,
                  coordinates: dict[int, tuple[float, float]]) -> dict[int, dict[str, Any]]:
    """Measure RDKit's actual glyph outlines, not the charged label's atom anchor.

    The capital/lowercase element glyphs are taller than the superscript charge
    and isotope glyphs. Keep their center as the annotation anchor, but reserve
    space for *all* label outlines. Bond endpoints and molecular coordinates are
    deliberately untouched. A bounded fallback also supports non-path fonts.
    """
    paths: dict[int, list[list[tuple[float, float]]]] = {}
    for node in ET.fromstring(f'<svg>{drawing}</svg>'):
        match = re.fullmatch(r"atom-(\d+)", node.get("class", ""))
        data = node.get("d", "")
        if node.tag != "path" or not match or not data:
            continue
        # RDKit emits absolute M/L/Q/C outlines. Control points conservatively
        # bound the curves. Never interpret arc flags / relative paths as xy.
        commands = re.findall(r"[A-DF-Za-df-z]", data)
        if any(command not in {"M", "L", "Q", "C", "Z"} for command in commands):
            continue
        numbers = list(map(float, re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?", data)))
        if numbers and len(numbers) % 2 == 0:
            paths.setdefault(int(match[1]), []).append(list(zip(numbers[::2], numbers[1::2])))
    result = {}
    for atom in molecule.GetAtoms():
        index = atom.GetIdx()
        glyphs = paths.get(index, [])
        if glyphs:
            element_glyphs = sorted(glyphs, key=lambda points:
                                    max(y for _, y in points) - min(y for _, y in points),
                                    reverse=True)[:len(atom.GetSymbol())]
            base = [point for points in element_glyphs for point in points]
            cx = (min(x for x, _ in base) + max(x for x, _ in base)) / 2
            cy = (min(y for _, y in base) + max(y for _, y in base)) / 2
            points = [point for glyph in glyphs for point in glyph]
        else:
            cx, cy = coordinates[index]
            points = [(cx - 7 * len(atom.GetSymbol()), cy - 9),
                      (cx + 7 * len(atom.GetSymbol()), cy + 9)]
        rx = max(15., max(abs(x - cx) for x, _ in points) + 5)
        ry = max(15., max(abs(y - cy) for _, y in points) + 5)
        # Reserve clearance at corners as well as at the four axis extrema.
        scale = max(1., max(sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
                             for x, y in points) / .85)
        result[index] = {"cx": cx, "cy": cy, "rx": rx * scale, "ry": ry * scale,
                         "bounds": (min(x for x, _ in points), min(y for _, y in points),
                                    max(x for x, _ in points), max(y for _, y in points))}
    return result


def _electron_positions(atom: Chem.Atom, labels: dict[int, dict[str, Any]],
                        bonds: list[tuple[tuple[float, float], tuple[float, float]]],
                        placed: list[tuple[float, float]], width: int, height: int) -> list[tuple[float, float]]:
    count = _lone_pairs(atom)
    if not count:
        return []
    label = labels[atom.GetIdx()]
    x, y = label["cx"], label["cy"]
    occupied = [atan2(labels[n.GetIdx()]["cy"] - y, labels[n.GetIdx()]["cx"] - x)
                for n in atom.GetNeighbors()]
    choices = [index * pi / 12 for index in range(24)]
    selected = []
    dots: list[tuple[float, float]] = []

    def segment_distance(point, segment):
        (ax, ay), (bx, by) = segment
        dx, dy = bx - ax, by - ay
        t = max(0., min(1., ((point[0] - ax) * dx + (point[1] - ay) * dy) / (dx * dx + dy * dy))) if dx or dy else 0.
        return hypot(point[0] - ax - t * dx, point[1] - ay - t * dy)

    for _ in range(count):
        candidates = []
        for extra in (0, 4, 8, 12):
            for angle in choices:
                px = x + (label["rx"] + 10 + extra) * cos(angle)
                py = y + (label["ry"] + 10 + extra) * sin(angle)
                pair = [(px - offset * sin(angle), py + offset * cos(angle)) for offset in (-3.2, 3.2)]
                collisions = 0
                for dx, dy in pair:
                    collisions += int(not (4 <= dx <= width - 4 and 4 <= dy <= height - 4))
                    for index, other in labels.items():
                        if index == atom.GetIdx():
                            continue
                        collisions += int(((dx - other["cx"]) / (other["rx"] + 4)) ** 2
                                          + ((dy - other["cy"]) / (other["ry"] + 4)) ** 2 < 1)
                    collisions += sum(segment_distance((dx, dy), bond) < 4 for bond in bonds)
                    collisions += sum(hypot(dx - ox, dy - oy) < 7.6 for ox, oy in placed + dots)
                clearance = min((abs((angle - direction + pi) % (2 * pi) - pi)
                                 for direction in occupied + selected), default=pi)
                candidates.append(((collisions, extra, -clearance), angle, pair))
            if any(candidate[0][0] == 0 for candidate in candidates):
                break
        _, angle, pair = min(candidates, key=lambda candidate: candidate[0])
        selected.append(angle)
        choices.remove(angle)
        dots.extend(pair)
    return dots


def _molecule_svg(item: dict[str, Any], changes: list[dict[str, Any]], side: str,
                  species_index: int, product_maps: set[int], width: int, height: int) -> str:
    # Keep every H explicit. The same mapped graph also supplies the 3D
    # Molfile, so symmetric atoms never depend on a guessed element ordering.
    molecule = Chem.Mol(item["mol"])
    fragment_indexes: list[tuple[int, ...]] = []
    fragments = Chem.GetMolFrags(molecule, asMols=True, sanitizeFrags=False,
                                 fragsMolAtomMapping=fragment_indexes)
    if 1 < len(fragments) <= 4:
        # Disconnected mechanism species must not share RDKit's tight packing:
        # that packing knows about glyphs, but not our Lewis dots / halos.
        # Keep RDKit's normal packing for larger assemblies rather than making
        # an unbounded row with negative / unusably small cell widths.
        gap = 24
        cell = (width - gap * (len(fragments) - 1)) / len(fragments)
        pieces = []
        for number, (fragment, indexes) in enumerate(zip(fragments, fragment_indexes)):
            fragment_item = {**item, "mol": fragment}
            content = _molecule_svg(fragment_item, changes, side, species_index, product_maps,
                                    max(1, int(cell)), height)
            content = re.sub(r"\batom-(\d+)\b", lambda match: f"atom-{indexes[int(match[1])]}", content)
            pieces.append(f'<g transform="translate({number * (cell + gap):.2f} 0)">{content}</g>')
            if number:
                pieces.append(f'<text x="{number * (cell + gap) - gap / 2:.2f}" y="{height / 2 + 5:.2f}" '
                              'text-anchor="middle" fill="#50665c" font-size="18" font-family="sans-serif">+</text>')
        return "".join(pieces)
    highlights = {}
    for change in changes:
        if side == "reactants" and change["kind"] == "formed" or side == "products" and change["kind"] == "broken":
            continue
        indexes = {atom.GetAtomMapNum(): atom.GetIdx() for atom in molecule.GetAtoms()}
        if not all(atom_map in indexes for atom_map in change["atomMaps"]):
            continue
        bond = molecule.GetBondBetweenAtoms(*(indexes[atom_map] for atom_map in change["atomMaps"]))
        if bond is not None:
            highlights[bond.GetIdx()] = _rgb(COLORS[change["kind"]])
    original_maps = {atom.GetIdx(): atom.GetAtomMapNum() for atom in molecule.GetAtoms()}
    for atom in molecule.GetAtoms():
        atom.SetAtomMapNum(0)
    rdDepictor.Compute2DCoords(molecule)
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 1.25
    options.highlightBondWidthMultiplier = 3
    # Color the label-trimmed bond strokes instead of drawing a continuous
    # highlight underneath (and through the open parts of) atom letters.
    options.continuousHighlight = False
    options.fixedFontSize = 24
    options.padding = 0.16
    options.useBWAtomPalette()
    for atom in molecule.GetAtoms():
        # RDKit normally hides skeletal carbons. A Lewis-style drawing has an
        # actual label and hit target for every carbon, including terminal C.
        if atom.GetSymbol() == "C":
            charge = atom.GetFormalCharge()
            suffix = "" if charge == 0 else f'<sup>{abs(charge) if abs(charge) != 1 else ""}{"+" if charge > 0 else "−"}</sup>'
            options.atomLabels[atom.GetIdx()] = "C" + suffix
    drawer.DrawMolecule(molecule, highlightAtoms=[], highlightBonds=list(highlights), highlightBondColors=highlights)
    coordinates = {atom.GetIdx(): (drawer.GetDrawCoords(atom.GetIdx()).x, drawer.GetDrawCoords(atom.GetIdx()).y)
                   for atom in molecule.GetAtoms()}
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    drawing = svg[svg.index(">", svg.index("<svg")) + 1:svg.rindex("</svg>")]
    labels = _label_layout(drawing, molecule, coordinates)
    bonds = [(coordinates[b.GetBeginAtomIdx()], coordinates[b.GetEndAtomIdx()]) for b in molecule.GetBonds()]
    electrons = {}
    placed: list[tuple[float, float]] = []
    for atom in sorted(molecule.GetAtoms(), key=lambda atom: -(_lone_pairs(atom) or 0)):
        positions = _electron_positions(atom, labels, bonds, placed, width, height)
        electrons[atom.GetIdx()] = positions
        placed.extend(positions)
    overlay = []
    metadata = _atom_metadata(item, side, species_index, product_maps)
    for atom, details in zip(molecule.GetAtoms(), metadata):
        measured = labels[atom.GetIdx()]
        x, y, rx, ry = (measured[key] for key in ("cx", "cy", "rx", "ry"))
        map_id = original_maps[atom.GetIdx()]
        label = f'{details["label"]}, {item["name"]}, {side}'
        overlay.extend(f'<circle class="lewis-electron" cx="{dx:.2f}" cy="{dy:.2f}" r="1.8" fill="#172c24"/>'
                       for dx, dy in electrons[atom.GetIdx()])
        if map_id in item.get("siteMaps", set()):
            overlay.append(f'<ellipse class="reaction-site" cx="{x:.2f}" cy="{y:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                           'fill="none" stroke="#b87916" stroke-width="2" stroke-dasharray="3 2" pointer-events="none"/>')
        overlay.append(f'<g class="atom-target" data-atom-map="{map_id}" data-element="{atom.GetSymbol()}" '
                       f'data-side="{side}" data-species-index="{species_index}" tabindex="0" role="button" '
                       f'aria-label="{escape(label, quote=True)}">'
                       f'<ellipse class="atom-glow" cx="{x:.2f}" cy="{y:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                       'fill="#ffe5a0" fill-opacity="0.45" stroke="#b87916" stroke-width="2" '
                       'pointer-events="none" opacity="0"/>'
                       f'<circle class="atom-hit" cx="{x:.2f}" cy="{y:.2f}" r="17" '
                       'fill="transparent" pointer-events="all"/>'
                       '</g>')
    return drawing + "".join(overlay)


def _svg(inputs: list[dict[str, Any]], outputs: list[dict[str, Any]], changes: list[dict[str, Any]]) -> str:
    # Stacked rows preserve readable structures in the narrow result panel.
    # The frontend can horizontally scroll the image on a small phone screen.
    width = 800
    height = 660
    product_maps = {atom.GetAtomMapNum() for atom in outputs[0]["mol"].GetAtoms()}
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Reactant and product structures with net bond changes">',
              '<text x="400" y="20" text-anchor="middle" fill="#50665c" font-size="15" font-family="sans-serif">REACTANTS</text>',
              '<text x="400" y="356" text-anchor="middle" fill="#50665c" font-size="15" font-family="sans-serif">PRODUCTS</text>',
              '<path d="M400 310 V334 M393 327 L400 334 L407 327" fill="none" stroke="#315a49" stroke-width="2"/>']
    for side, items, y, name_y in (("reactants", inputs, 28, 279), ("products", outputs, 368, 619)):
        cell = 780 // len(items)
        for index, item in enumerate(items):
            x = 10 + index * cell
            chunks.append(f'<g transform="translate({x} {y})">{_molecule_svg(item, changes, side, index, product_maps, cell - 16, 230)}</g>')
            # Names are readable outside atom labels. Long names wrap into two
            # short lines rather than overflowing a neighboring compound.
            words = item["name"].split()
            lines = [""]
            for word in words:
                if len(lines[-1]) + len(word) + 1 > max(14, cell // 8):
                    lines.append(word)
                else:
                    lines[-1] = (lines[-1] + " " + word).strip()
            lines = lines[:2]
            for line_index, line in enumerate(lines):
                chunks.append(f'<text x="{x + (cell - 16) / 2}" y="{name_y + line_index * 18}" text-anchor="middle" fill="#263c32" font-size="14" font-family="sans-serif">{escape(line)}</text>')
            if index < len(items) - 1:
                chunks.append(f'<text x="{x + cell - 8}" y="{y + 115}" text-anchor="middle" fill="#50665c" font-size="21" font-family="sans-serif">+</text>')
    chunks.append("</svg>")
    return "".join(chunks)


def _reaction_species(reaction: dict[str, Any], reactant_catalog: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Build the single deterministic mapped graph used by both 2D and 3D.

    Pass ``{**REACTANTS, **custom}`` after input resolution. The raw reaction must
    include productSmiles and byproduct smiles. equationReactants is respected,
    so a selected solvent is not incorrectly shown as consumed in the equation.
    """
    if not isinstance(reaction, dict) or not isinstance(reactant_catalog, dict):
        raise ValueError("A reaction diagram needs a reaction and reactant catalog.")
    identifiers = reaction.get("equationReactants", reaction.get("reactants"))
    if not isinstance(identifiers, (tuple, list)) or not 1 <= len(identifiers) <= 7:
        raise ValueError("A reaction diagram needs one to seven bounded equation species.")
    inputs, next_map = [], 1
    for identifier in identifiers:
        if not isinstance(identifier, str) or identifier not in reactant_catalog:
            raise ValueError("The reaction diagram reactant was not found.")
        item, next_map = _species(identifier, reactant_catalog[identifier], next_map)
        inputs.append(item)
    byproducts = reaction.get("byproducts", [])
    if not isinstance(byproducts, list) or len(byproducts) > 3:
        raise ValueError("The reaction diagram product list is invalid.")
    expected = [{"name": reaction.get("productName"), "smiles": reaction.get("productSmiles")}, *byproducts]
    plain_outputs = []
    for index, item in enumerate(expected):
        # Fallback products get unique identities disjoint from all reactants.
        # They can still link to their own exact 3D graph, but never imply an
        # unverified atom correspondence through the reaction.
        species, next_map = _species(f"product-{index}", item, next_map)
        plain_outputs.append(species)
    mechanism = reaction.get("mechanism")
    mapped = None
    if "mappedProducts" in reaction:
        # Use the engine's selected-site transformation, not another first-match
        # detector. Keep every explicit H and map when parsing mapped products.
        params = Chem.SmilesParserParams()
        params.removeHs = False
        supplied = [Chem.MolFromSmiles(smiles, params) for smiles in reaction["mappedProducts"]]
        if not supplied or any(mol is None for mol in supplied):
            raise ValueError("This structural case is not currently supported.")
        combined = _combine([{"mol": mol} for mol in supplied])
        mapped = _split_like_expected(combined, expected)
        before = {a.GetAtomMapNum(): a.GetAtomicNum() for item in inputs for a in item["mol"].GetAtoms()}
        after = {a.GetAtomMapNum(): a.GetAtomicNum() for mol in supplied for a in mol.GetAtoms()}
        if (mapped is None or before != after or len(after) != combined.GetNumAtoms()
                or sum(a.GetFormalCharge() for item in inputs for a in item["mol"].GetAtoms())
                != sum(a.GetFormalCharge() for a in combined.GetAtoms())):
            raise ValueError("This structural case is not currently supported: mapped products failed validation.")
    outputs = mapped or plain_outputs
    site_maps = set(reaction.get("site", {}).get("atomMaps", []))
    for item in inputs + outputs:
        item["siteMaps"] = site_maps
    changes = _changes(inputs, outputs) if mapped else []
    return inputs, outputs, changes, bool(mapped)


def mapped_product_molecule(reaction: dict[str, Any], reactant_catalog: dict[str, dict[str, Any]]) -> Chem.Mol:
    """Main product with explicit H and the exact identities of its 2D atoms."""
    _, outputs, _, _ = _reaction_species(reaction, reactant_catalog)
    return Chem.Mol(outputs[0]["mol"])


def build_reaction_diagram(reaction: dict[str, Any], reactant_catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """JSON-ready Lewis-style diagram with verified net bond correspondence."""
    inputs, outputs, changes, mapped = _reaction_species(reaction, reactant_catalog)
    identifiers = reaction.get("equationReactants", reaction.get("reactants"))
    mechanism = reaction.get("mechanism")
    summaries = {
        "SN2": "OH replaces the leaving group to form an alcohol.",
        "SN1": "The leaving group is replaced by OH through a carbocation pathway.",
        "E2": "A beta hydrogen and the leaving group are lost as C=C forms.",
        "E1": "The leaving group departs, then loss of a beta hydrogen forms C=C.",
        "Hydrogenation": "Hydrogen adds across C=C, changing it to a single bond.",
        "Epoxidation": "Peroxyacid oxygen adds across C=C to form an epoxide; a carboxylic acid is also formed.",
        "Bromination": "One bromine adds to each carbon as C=C becomes a single bond.",
        "Chlorination": "One chlorine adds to each carbon at the selected C=C.",
        "Hydrohalogenation": "H and halogen add across the selected C=C in the supported orientation.",
        "Hydration": "H and OH add across the carbon–carbon double bond.",
        "Esterification": "An acid and alcohol form an ester and water.",
        "Ester hydrolysis": "Acid hydrolysis gives acid and alcohol/phenol; lactone opening gives one connected hydroxy acid.",
        "Alcohol oxidation": "The alcohol becomes a carbonyl; hypochlorite becomes chloride.",
        "Aldehyde oxidation": "The aldehyde becomes a carboxylic acid reporting structure; hypochlorite becomes chloride.",
        "Carbonyl hydrogenation": "Hydrogen adds across C=O to form an alcohol.",
        "Alcohol dehydration": "OH and a beta hydrogen form water as the selected C=C forms.",
        "Alcohol substitution": "HX replaces activated alcohol OH with halogen; water forms.",
        "Ester saponification": "Hydroxide gives carboxylate and alcohol/phenol; lactone opening gives one connected hydroxy carboxylate. No acid work-up.",
        "Alkyne hydrogenation": "Two H₂ equivalents add four H and saturate the selected C≡C to C–C; other sites are not assumed selectively inert.",
        "Alkyne partial hydrogenation": "One H₂/Lindlar changes the selected C≡C into C=C; internal products are cis/Z, terminal E/Z is not applicable.",
        "Alkyne halogenation": "One actual X₂ gives a vicinal dihaloalkene; two give a 1,1,2,2-tetrahaloalkane. Br₂ anti geometry is a qualified net model; Cl₂ first-stage E/Z is unsigned. No experimental endpoint is predicted.",
        "Alkyne hydrohalogenation": "One actual HX gives a vinyl halide; two give a geminal dihalide. Internal orientations are separate net alternatives without ratios; no universal anti/trans or E/Z outcome is assigned.",
        "Alkene dihydroxylation": "A bounded Os/H2O2 net model adds syn OH groups. Configurations are assigned only from validated geometry; unknown internal geometry remains unassigned.",
        "Polymerization model": "Finite combination-terminated oligomer model; no bulk-polymer outcome predicted.",
    }
    medium = [{"name": reactant_catalog[identifier]["name"],
               "role": "acid catalyst" if mechanism == "Alcohol dehydration" else "medium"}
              for identifier in reaction.get("reactants", [])
              if identifier not in identifiers and identifier in reactant_catalog]
    def public_species(item: dict[str, Any]) -> dict[str, str]:
        return {"name": item["name"], "smiles": _identity(item["mol"]),
                "formula": rdMolDescriptors.CalcMolFormula(item["mol"])}
    summary = summaries.get(mechanism, "Reactants form the displayed products.") if mapped else "Reactant and product structures are shown without verified bond-change highlighting."
    product_maps = {atom.GetAtomMapNum() for atom in outputs[0]["mol"].GetAtoms()}
    atoms = [metadata for side, species in (("reactants", inputs), ("products", outputs))
             for index, item in enumerate(species)
             for metadata in _atom_metadata(item, side, index, product_maps)]
    origins = {a.GetAtomMapNum(): {"reactantId": item["id"], "atomIndex": a.GetIdx(), "element": a.GetSymbol(),
                                  **({"originalAtomMap": a.GetIntProp("sourceAtomMap")} if a.HasProp("sourceAtomMap") else {})}
               for item in inputs for a in item["mol"].GetAtoms()}
    return {"svg": _svg(inputs, outputs, changes), "summary": summary, "site": reaction.get("site"),
            "atomMap": [{"mapId": a.GetAtomMapNum(), **origins.get(a.GetAtomMapNum(), {}),
                         "productIndex": i, "productAtomIndex": a.GetIdx()}
                        for i, item in enumerate(outputs) for a in item["mol"].GetAtoms()],
            "bondsFormed": [c for c in changes if c["kind"] == "formed"],
            "bondsBroken": [c for c in changes if c["kind"] == "broken"],
            "bondOrderChanges": [c for c in changes if c["kind"] == "order"],
            "highlightsAvailable": mapped, "changes": changes, "atoms": atoms,
            "legend": [{"kind": kind, "label": LABELS[kind], "color": COLORS[kind]}
                       for kind in COLORS if any(change["kind"] == kind for change in changes)],
            "reactants": [public_species(item) for item in inputs],
            "products": [public_species(item) for item in outputs], "medium": medium,
            "note": ("Net bond changes; all H are explicit. Dots show supported lone pairs, not their 3D orientation. Validated distant configurations are retained; the selected alkene E/Z is consumed and new centers remain unassigned. No complete mapped stepwise mechanism is implemented for this pathway. A 3D conformer is not a stereochemical outcome prediction."
                     if mechanism in {"Hydration", "Hydrohalogenation"} else
                     "Net bond changes; all H are explicit. Dots show supported lone pairs, not their 3D orientation. This net view omits intermediate steps and stereochemistry; supported steps appear separately in Mapped mechanism.") if mapped else
                    "Structures shown; bond-change highlighting is unavailable for this pathway."}
