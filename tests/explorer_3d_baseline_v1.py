"""Offline frozen baseline: PubChem responses are not assumed available."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from rdkit import Chem
from server.chemistry_server import analyze_molfile
from server.pubchem_service import _is_ionic_assembly

cases = json.loads((Path(__file__).parent / 'explorer_3d_benchmark_v1.json').read_text())
totals = defaultdict(Counter)
for case in cases:
    molecule = Chem.MolFromSmiles(case['smiles'])
    if molecule is None:
        result = 'invalid-input'
    elif _is_ionic_assembly(molecule):
        result = 'information-only'
    else:
        try:
            output = analyze_molfile(Chem.MolToMolBlock(molecule))
            if output['representation'] == '3d':
                rebuilt = Chem.MolFromMolBlock(output['molfile'], removeHs=True)
                identity = rebuilt is not None and Chem.MolToSmiles(rebuilt, isomericSmiles=True) == Chem.MolToSmiles(molecule, isomericSmiles=True)
                result = '3d-identity-pass' if identity else '3d-identity-fail'
            elif case.get('cid') == 24817:
                result = 'idealized-reference-existing'
            else:
                result = '2d-only'
        except Exception:
            result = 'invalid-input'
    totals[case['category']][result] += 1
    print(case['id'], result)
print('category totals:', json.dumps(totals, sort_keys=True))
