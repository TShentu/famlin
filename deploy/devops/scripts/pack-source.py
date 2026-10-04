#!/usr/bin/env python3
"""Create a manifest-verified runtime bundle from a Git commit."""
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import PurePosixPath


def allowed(name):
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('..', 'node_modules') or x.startswith('.') for x in p.parts):
        return False
    return name in ('package.json', 'package-lock.json') or name.startswith((
        'web/', 'backend/', 'packages/api-client/', 'deploy/olares/scripts/'))


def pack(commit, output):
    commit = subprocess.check_output(['git', 'rev-parse', f'{commit}^{{commit}}'], text=True).strip()
    manifest = {'sourceCommit': commit, 'files': {}}
    with tarfile.open(output, 'w:gz') as bundle:
        names = subprocess.check_output(['git', 'ls-tree', '-rz', commit]).split(b'\0')
        for entry in filter(None, names):
            info, raw_name = entry.split(b'\t', 1)
            mode, kind, object_id = info.split()
            name = raw_name.decode()
            if not allowed(name):
                continue
            if kind != b'blob' or mode not in (b'100644', b'100755'):
                raise ValueError(f'Unexpected runtime file type: {name}')
            data = subprocess.check_output(['git', 'cat-file', 'blob', object_id.decode()])
            manifest['files'][name] = hashlib.sha256(data).hexdigest()
            item = tarfile.TarInfo('source/' + name)
            item.size = len(data)
            item.mode = int(mode, 8) & 0o777
            bundle.addfile(item, io.BytesIO(data))
        data = (json.dumps(manifest, sort_keys=True) + '\n').encode()
        item = tarfile.TarInfo('manifest.json')
        item.size = len(data)
        bundle.addfile(item, io.BytesIO(data))
    print(f'Packaged {len(manifest["files"])} files at {commit}')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--commit', default='HEAD')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    pack(a.commit, a.output)
