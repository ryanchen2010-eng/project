"""Deterministic offline generator audit; does not call PubChem or NIST."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from rdkit import Chem
from server.chemistry_server import BUILDER_3D_ELEMENTS
from server.explorer_rdkit_geometry import generate_fallback
from server.pubchem_service import _is_ionic_assembly

base = Path(__file__).parent
cases = json.loads((base / 'explorer_3d_benchmark_v1.json').read_text()) + json.loads((base / 'explorer_3d_benchmark_v2.json').read_text())
totals = defaultdict(Counter)
for case in cases:
    mol = Chem.MolFromSmiles(case['smiles'])
    if mol is None:
        result = 'invalid-input'
    elif _is_ionic_assembly(mol):
        result = 'information-only'
    else:
        output = generate_fallback(mol, BUILDER_3D_ELEMENTS)
        result = 'rdkit-validated' if output else 'generator-unavailable'
    totals[case['category']][result] += 1
    print(f"{case['id']}: {result}")
print('TOTALS', json.dumps(totals, sort_keys=True))
