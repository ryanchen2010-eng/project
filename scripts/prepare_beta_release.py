"""Freeze an allowlisted local source release; never commit, push or deploy.

Run from any directory: .venv/bin/python scripts/prepare_beta_release.py
Each release name is write-once. Secrets, Git metadata, tests, history and local
environments are not release inputs. The manifest describes dirty source too;
a HEAD commit alone cannot identify this project's current uncommitted work.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = ('Dockerfile', '.dockerignore', 'render.yaml', 'package.json', 'pnpm-lock.yaml',
              'pnpm-workspace.yaml', 'tsconfig.json', 'vite.config.ts', 'index.html',
              'explore.html', 'builder.html', 'reaction-lab.html', 'calculators.html')
FORBIDDEN = re.compile(r'(^\.|\.(?:pem|key|p12|pfx|pyc)$|secret|credential)', re.I)
TOKEN = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}')


def source_files(root=ROOT):
    files = [root / p for p in ROOT_FILES]
    files += sorted((root / 'server').glob('*.py'))
    files += [root / 'server' / p for p in ('requirements.txt', 'requirements-production.txt')]
    files += [root / 'scripts/compress-dist.mjs']
    for folder in ('src', 'public'):
        for p in sorted((root / folder).rglob('*')):
            relative = p.relative_to(root)
            if p.is_symlink():
                raise ValueError(f'Release source must not contain symlinks: {relative}')
            if any(FORBIDDEN.search(part) for part in relative.parts[1:]):
                raise ValueError(f'Unexpected hidden/credential file in runtime sources: {relative}')
            if p.is_file():
                files.append(p)
    for p in files:
        if p.is_symlink() or not p.is_file():
            raise ValueError(f'Missing or unsafe release input: {p.relative_to(root)}')
        if TOKEN.search(p.read_bytes()):
            raise ValueError(f'Potential credential in release input: {p.relative_to(root)}')
    return sorted(set(files))


def freeze(name, root=ROOT):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,79}', name):
        raise ValueError('Use a short lowercase release name, not a path.')
    # Read immutable bytes once, before writing anything into releases/.
    content = {str(p.relative_to(root)): p.read_bytes() for p in source_files(root)}
    hashes = {p: hashlib.sha256(data).hexdigest() for p, data in content.items()}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True))
    directory = root / 'releases' / name
    directory.mkdir(parents=True, exist_ok=False)
    archive = directory / f'{name}-source.tar.gz'
    with tarfile.open(archive, 'w:gz') as bundle:
        for path, data in content.items():
            info = tarfile.TarInfo(f'{name}/{path}')
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            bundle.addfile(info, io.BytesIO(data))
    manifest = {'schemaVersion': 1, 'release': name, 'baseCommit': head, 'dirtySource': dirty,
                'archive': archive.name, 'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'files': hashes, 'autoDeploy': False, 'published': False,
                'note': 'Local candidate only. Review and authorize the exact release before any upload, push or deployment.'}
    with (directory / 'manifest.json').open('x') as output:
        json.dump(manifest, output, indent=2); output.write('\n')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='molecule-playground-beta-v1')
    args = parser.parse_args()
    print(freeze(args.name))
