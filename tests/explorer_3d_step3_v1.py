"""Replay the frozen offline baseline through the Explorer-specific generator."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from rdkit import Chem
from server.chemistry_server import BUILDER_3D_ELEMENTS
from server.explorer_rdkit_geometry import generate_fallback
from server.pubchem_service import _is_ionic_assembly

cases = json.loads((Path(__file__).parent / 'explorer_3d_benchmark_v1.json').read_text())
totals = defaultdict(Counter)
for case in cases:
    mol = Chem.MolFromSmiles(case['smiles'])
    if mol is None:
        result = 'invalid-input'
    elif _is_ionic_assembly(mol):
        result = 'information-only'
    else:
        output = generate_fallback(mol, BUILDER_3D_ELEMENTS)
        result = '3d-validated' if output else ('idealized-reference-existing' if case.get('cid') == 24817 else '2d-only')
    totals[case['category']][result] += 1
    print(case['id'], result)
print('category totals:', json.dumps(totals, sort_keys=True))
