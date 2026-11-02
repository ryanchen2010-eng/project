"""Research-only independent random starts; fixed seed and conservative checks.
Run PYTHONPATH=. .venv/bin/python tests/explorer_xtb_independent_pilot.py.
"""
import math
import os
import random
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolTransforms
from tests.explorer_xtb_pilot import CASES, XTB, angles, ROOT
from server.coordination_reference import validate_carbonyl_sdf

def unit(rng):
    while True:
        v = [rng.uniform(-1, 1) for _ in range(3)]
        n = math.sqrt(sum(x*x for x in v))
        if 0.01 < n <= 1: return [x/n for x in v]

def starts(mol, center, neighbors, seed):
    # Independent random coordination orientations, not rotations/perturbations
    # of reference coordinates. Approximate initial bond lengths are heuristic.
    rng = random.Random(seed)
    positions = [None] * mol.GetNumAtoms()
    positions[center] = (0., 0., 0.)
    vectors = []
    bond_start = {'O': 1., 'Al': 2.1, 'Zr': 2.3, 'Fe': 1.9, 'Ni': 1.9, 'Cr': 1.9, 'S': 1.6, 'N': 1.0}[mol.GetAtomWithIdx(center).GetSymbol()]
    for n in neighbors:
        for _ in range(1000):
            v = unit(rng)
            if all(sum(a*b for a,b in zip(v, previous)) < 0.68 for previous in vectors): break
        else: raise RuntimeError('Could not generate separated ligands')
        vectors.append(v)
        positions[n] = tuple(bond_start*x for x in v)
        other = [a.GetIdx() for a in mol.GetAtomWithIdx(n).GetNeighbors() if a.GetIdx() != center]
        for index in other:
            if mol.GetAtomWithIdx(index).GetSymbol() != 'O': raise ValueError('Unsupported ligand')
            positions[index] = tuple((bond_start + 1.15)*x for x in v)
    if any(p is None for p in positions): raise ValueError('Unmapped atom in pilot')
    return '\n'.join([str(len(positions)), 'independent random start'] + [f'{atom.GetSymbol()} {p[0]:.8f} {p[1]:.8f} {p[2]:.8f}' for atom,p in zip(mol.GetAtoms(),positions)]) + '\n'

def main():
    extra = [
        ('Cr(CO)6', ROOT/'.xtb-pilot/C13007926.sdf', 'Cr', 'C', 6, 25589),
        ('SF6', ROOT/'public/molecules/sulfur-hexafluoride-nist-reference.sdf', 'S', 'F', 6, None),
        ('SO3', ROOT/'.xtb-pilot/C7446119.sdf', 'S', 'O', 3, None),
        ('NH3', ROOT/'.xtb-pilot/C7664417.sdf', 'N', 'H', 3, None),
    ]
    for name, path, symbol, neighbor_symbol, count, cid in CASES + extra:
        text = path.read_text()
        if cid and not validate_carbonyl_sdf(text, cid): raise ValueError('Bad reference identity')
        mol = Chem.MolFromMolBlock(text.split('$$$$')[0], sanitize=False, removeHs=False, strictParsing=False)
        if mol is None: raise ValueError(f'{name}: reference could not be parsed')
        center = next(a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == symbol)
        neighbors = [a.GetIdx() for a in mol.GetAtomWithIdx(center).GetNeighbors() if a.GetSymbol() == neighbor_symbol]
        if len(neighbors) != count or any(a.GetFormalCharge() for a in mol.GetAtoms()): raise ValueError('Unexpected reference')
        ref = mol.GetConformer()
        ref_dist = sorted(rdMolTransforms.GetBondLength(ref, center, n) for n in neighbors)
        ref_angles = angles(ref, center, neighbors)
        stats = Counter()
        for seed in range(1, 9):
            with tempfile.TemporaryDirectory(prefix='xtb-start-') as work:
                xyz = Path(work)/'input.xyz'
                try: xyz.write_text(starts(mol, center, neighbors, seed))
                except RuntimeError:
                    stats['start_generation_failed'] += 1; continue
                try:
                    p = subprocess.run([str(XTB), str(xyz), '--gfn', '2', '--opt', '--chrg', '0', '--uhf', '0'], cwd=work, capture_output=True, text=True, timeout=120, env={**os.environ, 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1'})
                except subprocess.TimeoutExpired:
                    stats['timeout'] += 1; continue
                output = Path(work)/'xtbopt.xyz'
                if p.returncode or not output.is_file() or 'GEOMETRY OPTIMIZATION CONVERGED' not in p.stdout.upper():
                    stats['not_converged'] += 1; continue
                out = Chem.MolFromXYZFile(str(output))
                if out is None or [a.GetSymbol() for a in out.GetAtoms()] != [a.GetSymbol() for a in mol.GetAtoms()]:
                    stats['identity_failed'] += 1; continue
                conf = out.GetConformer()
                ds = sorted(rdMolTransforms.GetBondLength(conf, center, n) for n in neighbors)
                ans = angles(conf, center, neighbors)
                delta_dist = max(abs(x-y) for x,y in zip(ds, ref_dist))
                delta_angle = max(abs(x-y) for x,y in zip(ans, ref_angles))
                # All original bonds must stay in conservative length bands;
                # xyz lacks bonds, and this does not prove topology or stereo.
                bond_ok = all(0.65 < rdMolTransforms.GetBondLength(conf, b.GetBeginAtomIdx(), b.GetEndAtomIdx()) < (2.65 if symbol == 'Zr' and center in (b.GetBeginAtomIdx(), b.GetEndAtomIdx()) else 2.3) for b in mol.GetBonds())
                if name == 'Fe(CO)5' and seed == 1:
                    others = [(a.GetIdx(), rdMolTransforms.GetBondLength(conf, center, a.GetIdx())) for a in mol.GetAtoms() if a.GetSymbol() == 'O']
                    print('Fe diagnostic: metal-to-oxygen distances', [(i, round(d,3)) for i,d in others], flush=True)
                if cid:
                    clone = Chem.Mol(mol)
                    for i in range(clone.GetNumAtoms()): clone.GetConformer().SetAtomPosition(i, conf.GetAtomPosition(i))
                    validator_ok = validate_carbonyl_sdf(Chem.MolToMolBlock(clone), cid)
                    stats['carbonyl_screen_pass' if validator_ok else 'carbonyl_screen_reject'] += 1
                    if name == 'Fe(CO)5': print('Fe carbonyl geometry-screen:', validator_ok, flush=True)
                passed = delta_dist <= 0.12 and delta_angle <= 8 and bond_ok
                stats['geometry_pass' if passed else 'geometry_mismatch'] += 1
                print(f'{name} seed={seed} max_distance_delta={delta_dist:.3f} max_angle_delta={delta_angle:.2f} bonded_distance_screen={bond_ok} result={"pass" if passed else "mismatch"}', flush=True)
        print(name, 'total', dict(stats), flush=True)

if __name__ == '__main__': main()
