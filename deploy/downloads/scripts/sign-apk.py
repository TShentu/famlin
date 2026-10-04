#!/usr/bin/env python3
"""Sign locally; pass passwords by file, never through command arguments or logs."""
import argparse
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--java', required=True)
p.add_argument('--apksigner', required=True)
p.add_argument('--keystore', required=True)
p.add_argument('--password-file', required=True)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
base = [a.java, '-jar', a.apksigner]
subprocess.run(base+['sign', '--ks', a.keystore, '--ks-type', 'PKCS12',
    '--ks-key-alias', 'famlin', '--ks-pass', 'file:'+a.password_file,
    '--out', a.output, a.input], check=True)
subprocess.run(base+['verify', '--verbose', '--print-certs', a.output], check=True)
