"""Rendering-only regressions: labels, halos, lone pairs and fragment packing."""
import math
import re
import unittest
import xml.etree.ElementTree as ET

from rdkit import Chem

from server import chemistry_server as service
from server.reaction_diagrams import _lone_pairs, _molecule_svg, _species


def drawing(smiles, width=380, height=230, site=False):
    item, _ = _species("spacing-fixture", {"name": "Spacing fixture", "smiles": smiles}, 1)
    if site:
        item["siteMaps"] = {atom.GetAtomMapNum() for atom in item["mol"].GetAtoms()}
    before = Chem.MolToSmiles(item["mol"])
    source = _molecule_svg(item, [], "reactants", 0, set(), width, height)
    assert Chem.MolToSmiles(item["mol"]) == before, "Rendering must not mutate its input graph"
    return item, ET.fromstring("<svg>" + source + "</svg>")


def annotations(root):
    """Read the emitted SVG geometry independently of layout implementation."""
    result = []

    def visit(parent, tx=0., ty=0.):
        pending = []
        for node in parent:
            if node.get("class") == "lewis-electron":
                pending.append((float(node.get("cx")) + tx, float(node.get("cy")) + ty))
            elif node.get("class") == "atom-target":
                glow = next(n for n in node if n.get("class") == "atom-glow")
                hit = next(n for n in node if n.get("class") == "atom-hit")
                result.append({"map": int(node.get("data-atom-map")), "element": node.get("data-element"),
                               "x": float(glow.get("cx")) + tx, "y": float(glow.get("cy")) + ty,
                               "rx": float(glow.get("rx")), "ry": float(glow.get("ry")),
                               "dots": pending, "hit": hit, "node": node})
                pending = []
            elif node.tag.rsplit("}", 1)[-1] == "g":
                offset = re.fullmatch(r"translate\(([-\d.]+) ([-\d.]+)\)", node.get("transform", ""))
                visit(node, tx + (float(offset[1]) if offset else 0), ty + (float(offset[2]) if offset else 0))
    visit(root)
    return result


class DiagramAnnotationSpacingTests(unittest.TestCase):
    def test_selection_and_electrons_have_visible_clearance(self):
        for smiles in ("O", "[OH-]", "[Br-]", "CBr", "CO", "CC(=O)O", "CC(=O)OCC", "O=C=O", "N"):
            with self.subTest(smiles=smiles):
                item, root = drawing(smiles, site=True)
                records = annotations(root)
                self.assertEqual(len(records), item["mol"].GetNumAtoms())
                by_map = {a.GetAtomMapNum(): a for a in item["mol"].GetAtoms()}
                for atom in records:
                    self.assertEqual(len(atom["dots"]), 2 * (_lone_pairs(by_map[atom["map"]]) or 0))
                    for dx, dy in atom["dots"]:
                        # Sample the actual ellipse perimeter, including the
                        # widest keyboard-focus stroke, not just axis radii.
                        distance = min(math.hypot(dx - atom["x"] - atom["rx"] * math.cos(i * math.pi / 180),
                                                  dy - atom["y"] - atom["ry"] * math.sin(i * math.pi / 180))
                                       for i in range(360))
                        self.assertGreater(distance - 1.8 - 1.5, 4)

    def test_electrons_avoid_other_atom_highlights_in_reported_ester_example(self):
        for smiles in ("CC(=O)O", "CCO", "CC(=O)OCC", "O"):
            with self.subTest(smiles=smiles):
                _, root = drawing(smiles, site=True)
                records = annotations(root)
                for atom in records:
                    for dx, dy in atom["dots"]:
                        for other in records:
                            if atom is other:
                                continue
                            self.assertGreater(((dx - other["x"]) / (other["rx"] + 3)) ** 2
                                               + ((dy - other["y"]) / (other["ry"] + 3)) ** 2, 1)

    def test_bromide_pairs_and_highlight_are_centered_on_br_not_the_charge(self):
        _, root = drawing("[Br-]")
        atom = annotations(root)[0]
        paths = [n for n in root if n.tag == "path" and n.get("class") == "atom-0"]
        # RDKit emits B, r, then the small charge stroke in this fixture.
        coordinates = [list(map(float, re.findall(r"-?\d+(?:\.\d+)?", n.get("d")))) for n in paths[:2]]
        xs = [x for values in coordinates for x in values[::2]]
        ys = [y for values in coordinates for y in values[1::2]]
        self.assertAlmostEqual(atom["x"], (min(xs) + max(xs)) / 2, delta=.02)
        self.assertAlmostEqual(atom["y"], (min(ys) + max(ys)) / 2, delta=.02)
        self.assertEqual(len(atom["dots"]), 8)
        self.assertAlmostEqual(sum(x for x, _ in atom["dots"]) / 8, atom["x"], delta=.02)
        self.assertAlmostEqual(sum(y for _, y in atom["dots"]) / 8, atom["y"], delta=.02)

    def test_site_and_selection_use_the_same_label_aware_boundary(self):
        for smiles in ("O", "[OH-]", "CBr", "[Br-]", "[Cl-]", "[NH4+]", "[Na+]", "[Fe+2]", "[2H]O[2H]"):
            with self.subTest(smiles=smiles):
                _, root = drawing(smiles, site=True)
                sites = [n for n in root if n.get("class") == "reaction-site"]
                targets = annotations(root)
                self.assertEqual(len(sites), len(targets))
                for site, target in zip(sites, targets):
                    glow = next(n for n in target["node"] if n.get("class") == "atom-glow")
                    for key in ("cx", "cy", "rx", "ry"):
                        self.assertEqual(site.get(key), glow.get(key))
                    self.assertEqual(target["hit"].get("r"), "17")
                    self.assertEqual(target["hit"].get("fill"), "transparent")
                    self.assertEqual(target["hit"].get("pointer-events"), "all")

    def test_charge_glyph_is_inside_highlight_not_crossed_by_its_outline(self):
        for smiles in ("[Br-]", "[Cl-]", "[OH-]", "[NH4+]", "[Na+]", "[Fe+2]", "[2H]O[2H]"):
            with self.subTest(smiles=smiles):
                _, root = drawing(smiles)
                for atom in annotations(root):
                    atom_index = int(atom["map"]) - 1
                    for path in root:
                        if path.tag != "path" or path.get("class") != f"atom-{atom_index}":
                            continue
                        values = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))))
                        for x, y in zip(values[::2], values[1::2]):
                            self.assertLess(((x - atom["x"]) / atom["rx"]) ** 2
                                            + ((y - atom["y"]) / atom["ry"]) ** 2, .74)

    def test_disconnected_mechanism_species_have_distinct_annotation_space(self):
        item, root = drawing("CBr.[OH-]", width=560)
        records = annotations(root)
        self.assertEqual({a["map"] for a in records}, {a.GetAtomMapNum() for a in item["mol"].GetAtoms()})
        self.assertEqual(len([n for n in root if n.tag == "text" and n.text == "+"]), 1)
        b = next(a for a in records if a["element"] == "Br")
        o = next(a for a in records if a["element"] == "O")
        self.assertGreater(o["x"] - o["rx"] - b["x"] - b["rx"], 24)
        self.assertGreater(min(math.hypot(x - ox, y - oy) for x, y in b["dots"] for ox, oy in o["dots"]), 10)

    def test_rendering_preserves_charges_maps_isotopes_and_configurations(self):
        for smiles in ("CBr.[OH-]", "[Br-].CO", "[Na+].[Cl-]", "[2H]O[2H]", "C[C@H](O)CCCBr", "C/C=C/CO",
                       "[Na+].[Na+].[Cl-].[Cl-].O"):
            with self.subTest(smiles=smiles):
                item, root = drawing(smiles, width=560)
                self.assertEqual(len(annotations(root)), item["mol"].GetNumAtoms())
                self.assertEqual({n["map"] for n in annotations(root)}, {a.GetAtomMapNum() for a in item["mol"].GetAtoms()})

    def test_electron_pairs_are_not_clipped_in_representative_views(self):
        for width, height in ((374, 230), (480, 300), (560, 230)):
            for smiles in ("O", "[OH-]", "[Br-]", "CBr", "CC(=O)O", "CC(=O)OCC"):
                with self.subTest(size=(width, height), smiles=smiles):
                    _, root = drawing(smiles, width, height)
                    for atom in annotations(root):
                        for x, y in atom["dots"]:
                            self.assertGreaterEqual(x, 4)
                            self.assertLessEqual(x, width - 4)
                            self.assertGreaterEqual(y, 4)
                            self.assertLessEqual(y, height - 4)

    def test_actual_public_sn2_mechanism_keeps_graph_and_lone_pair_bookkeeping(self):
        result = service.reaction_diagram("sn2-bromomethane", "bromomethane", "hydroxide", {"solvent": "polar-aprotic"})
        mechanism = result["mechanism"]
        self.assertEqual(len(mechanism["steps"]), 1)
        step = mechanism["steps"][0]
        self.assertTrue(step["concerted"])
        for state in (step["beforeState"], step["state"]):
            root = ET.fromstring(state["svg"])
            self.assertEqual(len(annotations(root)), len(state["atoms"]))
            self.assertFalse(any(set(b["atomMaps"]) == {2, 6} for b in state["bonds"]))
        before = annotations(ET.fromstring(step["beforeState"]["svg"]))
        after = annotations(ET.fromstring(step["state"]["svg"]))
        pairs = lambda records, symbol: len(next(a["dots"] for a in records if a["element"] == symbol)) // 2
        self.assertEqual((pairs(before, "Br"), pairs(after, "Br")), (3, 4))
        self.assertEqual((pairs(before, "O"), pairs(after, "O")), (3, 2))


if __name__ == "__main__":
    unittest.main()
