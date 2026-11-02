"""Research-only xTB pilot; reference geometries are also starting coordinates.

Usage: PYTHONPATH=. .venv/bin/python tests/explorer_xtb_pilot.py
The Fe/Ni source SDFs must be fetched separately from their fixed NIST URLs.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolTransforms
from server.coordination_reference import validate_carbonyl_sdf

ROOT = Path(__file__).resolve().parents[1]
XTB = ROOT / '.xtb-pilot/env/bin/xtb'
CASES = [
    ('water', ROOT/'public/molecules/water-reference.sdf', 'O', 'H', 2, None),
    ('AlCl3', ROOT/'public/molecules/aluminum-trichloride-nist-reference.sdf', 'Al', 'Cl', 3, None),
    ('ZrCl4', ROOT/'public/molecules/zirconium-tetrachloride-gas-reference.sdf', 'Zr', 'Cl', 4, None),
    ('Fe(CO)5', ROOT/'.xtb-pilot/fe-co5.sdf', 'Fe', 'C', 5, 26040),
    ('Ni(CO)4', ROOT/'.xtb-pilot/ni-co4.sdf', 'Ni', 'C', 4, 26039),
]

def angles(conf, center, neighbors):
    return sorted(rdMolTransforms.GetAngleDeg(conf, neighbors[i], center, neighbors[j]) for i in range(len(neighbors)) for j in range(i))

def main():
    for name, path, center_symbol, neighbor_symbol, count, cid in CASES:
        text = path.read_text()
        if cid and not validate_carbonyl_sdf(text, cid):
            raise ValueError(f'{name}: reference identity validation failed')
        mol = Chem.MolFromMolBlock(text.split('$$$$')[0], sanitize=False, removeHs=False)
        center = next(a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == center_symbol)
        neighbors = [a.GetIdx() for a in mol.GetAtomWithIdx(center).GetNeighbors() if a.GetSymbol() == neighbor_symbol]
        if len(neighbors) != count or any(a.GetFormalCharge() for a in mol.GetAtoms()):
            raise ValueError(f'{name}: unexpected reference graph/charge')
        ref = mol.GetConformer()
        with tempfile.TemporaryDirectory(prefix='xtb-geometry-') as work:
            xyz = Path(work)/'input.xyz'
            xyz.write_text(Chem.MolToXYZBlock(mol))
            result = subprocess.run([str(XTB), str(xyz), '--gfn', '2', '--opt', '--chrg', '0', '--uhf', '0'], cwd=work, capture_output=True, text=True, timeout=120, env={**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'})
            output = Path(work)/'xtbopt.xyz'
            if result.returncode or not output.is_file() or 'GEOMETRY OPTIMIZATION CONVERGED' not in result.stdout.upper():
                print(name, 'FAILED', result.returncode, result.stderr[-400:]); continue
            optimized = Chem.MolFromXYZFile(str(output))
            if optimized is None or [a.GetSymbol() for a in optimized.GetAtoms()] != [a.GetSymbol() for a in mol.GetAtoms()]:
                print(name, 'atom identity/order mismatch'); continue
            conf = optimized.GetConformer()
            ds0 = [rdMolTransforms.GetBondLength(ref, center, n) for n in neighbors]
            ds1 = [rdMolTransforms.GetBondLength(conf, center, n) for n in neighbors]
            a0, a1 = angles(ref, center, neighbors), angles(conf, center, neighbors)
            bond_changes = [abs(rdMolTransforms.GetBondLength(ref, b.GetBeginAtomIdx(), b.GetEndAtomIdx()) - rdMolTransforms.GetBondLength(conf, b.GetBeginAtomIdx(), b.GetEndAtomIdx())) for b in mol.GetBonds()]
            print(name, 'charge=0 unpaired=0', 'reference distances', [round(x,3) for x in ds0], 'xtb distances', [round(x,3) for x in ds1], 'max ΔÅ', round(max(abs(x-y) for x,y in zip(ds0,ds1)),3), 'max Δangle°', round(max(abs(x-y) for x,y in zip(a0,a1)),2), 'max mapped-bond ΔÅ', round(max(bond_changes),3))

if __name__ == '__main__': main()
