import hmac
import uuid
import re
import hashlib
import http.server
import json
import os
import subprocess
import tarfile
import threading
import time
import urllib.request
from pathlib import Path

state = Path('/state')
state.mkdir(exist_ok=True)
status = {'phase': 'waiting-for-private-signing-files'}
class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/candidates':
            self.send_error(404)
            return
        key = state/'deploy-token'
        if not key.exists() or not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+key.read_text().strip()).encode()):
            self.close_connection = True
            self.send_error(401, 'Publisher authentication required')
            return
        checksum = self.headers.get('X-Content-SHA256', '')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = 0
        if not 0 < length <= 200_000_000 or not re.fullmatch(r'[0-9a-f]{64}', checksum):
            self.send_error(400, 'Invalid delivery size or checksum')
            return
        inbox = state/'inbox'
        inbox.mkdir(exist_ok=True)
        temp = inbox/(uuid.uuid4().hex+'.partial')
        try:
            self.connection.settimeout(60)
            digest = hashlib.sha256()
            with temp.open('wb') as f:
                while length:
                    chunk = self.rfile.read(min(1024*1024, length))
                    if not chunk:
                        raise ValueError('Incomplete delivery')
                    f.write(chunk)
                    digest.update(chunk)
                    length -= len(chunk)
                f.flush()
                os.fsync(f.fileno())
            if not hmac.compare_digest(digest.hexdigest(), checksum):
                raise ValueError('Delivery checksum mismatch')
            temp.replace(temp.with_suffix('.tgz'))
            self.send_response(202)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"queued":true}')
        except Exception:
            temp.unlink(missing_ok=True)
            self.send_error(400, 'Invalid delivery')
    def do_GET(self):
        if self.path == '/candidates':
            key = state/'deploy-token'
            if not key.exists() or not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+key.read_text().strip()).encode()):
                self.send_error(401, 'Publisher authentication required')
                return
        data = dict(status)
        for name in ['published.json', 'failed.json']:
            path = state/name
            if path.exists():
                data[name] = json.loads(path.read_text())
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_args):
        pass
threading.Thread(target=http.server.ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever, daemon=True).start()
while not all((state/name).exists() for name in ['release.p12', 'password', 'apksigner.jar', 'deploy-token']):
    time.sleep(5)
status['phase'] = 'preparing-toolchain'
java = state/'jdk-17.0.20.1+1-jre/bin/java'
if not java.exists():
    archive = state/'jre.tgz'
    url = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.20.1%2B1/OpenJDK17U-jre_x64_linux_hotspot_17.0.20.1_1.tar.gz'
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != '0b2b640e3046b64c8ec504de0ab9d91bb5610182bda21fad454681ce54d45a62':
        raise RuntimeError('Java archive checksum mismatch')
    archive.write_bytes(data)
    with tarfile.open(archive) as tar:
        tar.extractall(state, filter='data')
venv = state/'venv'
if not (venv/'ready').exists():
    subprocess.run(['python3', '-m', 'venv', str(venv)], check=True)
    subprocess.run([str(venv/'bin/pip'), 'install', 'qrcode[pil]==8.2', 'pillow==11.3.0'], check=True)
    (venv/'ready').write_text('ready')
status['phase'] = 'waiting-for-tested-candidates'
args = [str(venv/'bin/python'), '/opt/famlin/deploy/devops/scripts/worker.py', '--state', '/state', '--source', '/workspace/source', '--downloads', '/downloads', '--java', str(java), '--apksigner', '/state/apksigner.jar', '--keystore', '/state/release.p12', '--password-file', '/state/password', '--branch', os.environ['RELEASE_BRANCH']]
raise SystemExit(subprocess.call(args))
