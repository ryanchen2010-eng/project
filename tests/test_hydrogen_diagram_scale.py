"""H₂ should not stretch to the width of a reaction-diagram cell."""
import math
import re
import unittest

from server import chemistry_server as service


class HydrogenDiagramScaleTests(unittest.TestCase):
    def test_hydrogen_bond_is_comparable_to_neighboring_bonds(self):
        conditions = {'catalyst': 'metal'}
        reaction = next(r for r in service.match_reactions('ethene', 'hydrogen', conditions)['reactions'] if r['mechanism'] == 'Hydrogenation')
        diagram = service.reaction_diagram(reaction['id'], 'ethene', 'hydrogen', conditions)
        targets = re.findall(r'data-atom-map="(\d+)"[^>]*>\s*<ellipse[^>]*cx="([\d.]+)" cy="([\d.]+)', diagram['svg'])
        coords = {int(atom): (float(x), float(y)) for atom, x, y in targets[:8]}
        def distance(a, b):
            return math.dist(coords[a], coords[b])
        self.assertEqual(set(coords), set(range(1, 9)))
        self.assertGreater(distance(7, 8), 35)
        self.assertLess(distance(7, 8), 1.5 * distance(1, 2))
        self.assertEqual(len([a for a in diagram['atoms'] if a['side'] == 'reactants']), 8)
        self.assertTrue(any(item['kind'] == 'broken' for item in diagram['legend']))


if __name__ == '__main__':
    unittest.main()
