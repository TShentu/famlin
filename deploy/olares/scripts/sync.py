#!/usr/bin/env python3
"""Sync explicitly named source files to the independent Famlin Dev instance."""
import argparse
import hashlib
import json
import uuid
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--namespace', default='famlindev-hzfystt')
p.add_argument('--watch', action='store_true', help='Watch the named files and sync changes')
p.add_argument('files', nargs='+', help='Source paths relative to the repository root')
args = p.parse_args()
paths = []
for name in args.files:
    path = (root / name).resolve()
    relative = path.relative_to(root)
    if not path.is_file() or relative.parts[0] not in ('web', 'backend', 'packages', 'deploy'):
        p.error('Only existing project source files may be synced: ' + name)
    if any(part.startswith('.') or part == 'node_modules' for part in relative.parts):
        p.error('Hidden files and dependencies must not be synced: ' + name)
    paths.append((path, relative.as_posix()))
stamps = {}
while True:
    for path, relative in paths:
        stamp = path.stat().st_mtime_ns
        if stamps.get(relative) == stamp:
            continue
        staged = relative + '.sync-' + uuid.uuid4().hex
        subprocess.run(['olares-cli', 'files', 'upload', str(path),
                        'drive/Home/Documents/FamlinDev/source/' + staged], check=True)
        pods = json.loads(subprocess.check_output(
            ['olares-cli', 'cluster', 'pod', 'list', '-n', args.namespace, '-o', 'json']))
        matches = [item for item in pods['items']
                   if item['metadata'].get('labels', {}).get('app') == 'famlindev'
                   and not item['metadata'].get('deletionTimestamp')
                   and item.get('status', {}).get('phase') == 'Running']
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one running Famlin Dev pod')
        target = args.namespace + '/' + matches[0]['metadata']['name'] + '/famlindev'
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        # Idempotent if the exec connection retries; verify before atomic replacement.
        script = ("const f=require('fs'),c=require('crypto');const [a,b,h]=process.argv.slice(1);"
                  "if(f.existsSync(a)){if(c.createHash('sha256').update(f.readFileSync(a)).digest('hex')!==h)throw Error('Checksum mismatch');f.renameSync(a,b)}"
                  "if(c.createHash('sha256').update(f.readFileSync(b)).digest('hex')!==h)throw Error('Sync verification failed');console.log('Synced '+b)")
        subprocess.run(['olares-cli', 'cluster', 'container', 'exec', target, '--', 'node', '-e',
                        script, '/workspace/source/' + staged, '/workspace/source/' + relative, checksum], check=True)
        stamps[relative] = stamp
    if not args.watch:
        break
    time.sleep(1)
