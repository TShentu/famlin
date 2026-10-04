#!/usr/bin/env python3
"""Copy only public publisher code into the Olares chart (never signing material)."""
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[3]
files = root/'deploy/devops/famlindevops/files'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--verify', action='store_true')
args = parser.parse_args()
for name in ['deploy/devops/scripts/worker.py', 'deploy/devops/scripts/source.py', 'deploy/downloads/scripts/prepare-release.py', 'LICENSE']:
    source, target = root/name, files/name
    if args.verify:
        if not target.exists() or target.read_bytes() != source.read_bytes():
            raise SystemExit('Chart copy out of date: ' + name)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
