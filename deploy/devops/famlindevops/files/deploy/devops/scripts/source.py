"""Verified runtime-source transactions; uploads, secrets and dependencies are excluded."""
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path, PurePosixPath


def allowed(name):
    p = PurePosixPath(name)
    return (str(p) == name and not p.is_absolute() and all(x not in ('..', 'node_modules') and not x.startswith('.') for x in p.parts)
            and (name in ('package.json', 'package-lock.json') or name.startswith((
                'web/', 'backend/', 'packages/api-client/', 'deploy/olares/scripts/'))))


def read_bundle(data, expected_commit):
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        total = 0
        for item in archive:
            total += item.size
            if not item.isfile() or item.size > 20_000_000 or total > 150_000_000:
                raise ValueError('Invalid or oversized source entry')
            if item.name != 'manifest.json' and not (item.name.startswith('source/') and allowed(item.name[7:])):
                raise ValueError(f'Forbidden source path: {item.name}')
            if item.name in files:
                raise ValueError('Duplicate source entry')
            files[item.name] = archive.extractfile(item).read()
    manifest = json.loads(files.pop('manifest.json'))
    if manifest['sourceCommit'] != expected_commit:
        raise ValueError('Source commit mismatch')
    files = {name[7:]: data for name, data in files.items()}
    if {name: hashlib.sha256(data).hexdigest() for name, data in files.items()} != manifest['files']:
        raise ValueError('Source manifest checksum mismatch')
    return manifest, files


def destination(root, name):
    if not allowed(name):
        raise ValueError(f'Forbidden runtime path: {name}')
    path = root / name
    parents = [root.joinpath(*PurePosixPath(name).parts[:i]) for i in range(1, len(PurePosixPath(name).parts) + 1)]
    if root.is_symlink() or any(p.is_symlink() for p in parents):
        raise ValueError(f'Symlink in runtime path: {name}')
    return path


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.devops-tmp')
    with temp.open('wb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def apply(root, state_dir, manifest, files):
    root, state_dir = Path(root), Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    previous = json.loads((state_dir/'source.json').read_text()) if (state_dir/'source.json').exists() else {'files': {}}
    names = set(previous['files']) | set(files)
    changes = {}
    for name in sorted(names):
        path = destination(root, name)
        old = path.read_bytes() if path.exists() else None
        new = files.get(name)
        if old != new:
            if name.startswith('backend/prisma/migrations/'):
                raise ValueError('Database migrations require a separate reviewed deployment')
            changes[name] = old
    journal = {name: old is not None for name, old in changes.items()}
    backup = state_dir/'rollback'
    for name, old in changes.items():
        if old is not None:
            atomic(backup/name, old)
    atomic(state_dir/'pending.json', json.dumps(journal).encode())
    for name in changes:
        path = destination(root, name)
        if name in files:
            atomic(path, files[name])
        else:
            path.unlink(missing_ok=True)
    restart = any(name.endswith(('package.json', 'package-lock.json')) or name.startswith('deploy/olares/scripts/') for name in changes)
    return {'changed': len(changes), 'restart': restart, 'commit': manifest['sourceCommit']}


def rollback(root, state_dir):
    root, state_dir = Path(root), Path(state_dir)
    journal = state_dir/'pending.json'
    if not journal.exists():
        return
    for name, existed in json.loads(journal.read_text()).items():
        path = destination(root, name)
        if existed:
            atomic(path, (state_dir/'rollback'/name).read_bytes())
        else:
            path.unlink(missing_ok=True)
    journal.unlink()


def accept(state_dir, manifest):
    state_dir = Path(state_dir)
    atomic(state_dir/'source.json', json.dumps(manifest).encode())
    (state_dir/'pending.json').unlink(missing_ok=True)
