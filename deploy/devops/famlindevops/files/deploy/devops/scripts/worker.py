#!/usr/bin/env python3
"""Pull only tested candidates; sign, verify, deploy source, then promote downloads.

Runs on a trusted publisher, never on pull-request runners. Signing files and
state must be outside DOWNLOAD_ROOT. No GitHub or Olares credential is needed.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

from source import atomic, read_bundle, apply, accept, rollback

REPO = 'TShentu/famlin'
PUBLIC = 'https://c89009ed.hzfystt.olares.cn'
SERVER = 'https://762e7148.hzfystt.olares.cn'
CERT = '2235d7b2444d8ea6a30158487d62d261f8074858ddfde061f0954d818769d9e3'
SCRIPTS = Path(__file__).resolve().parent


def request(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Famlin-DevOps', 'Accept': 'application/vnd.github+json' if url.startswith('https://api.github.com/') else '*/*'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def api(path):
    return json.loads(request(f'https://api.github.com/repos/{REPO}/{path}'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def candidate(branch):
    # Check BOTH the APK/emulator pipeline and the full monorepo CI at the exact SHA.
    builds = api(f'actions/workflows/android-selfhost.yml/runs?branch={branch}&status=success&per_page=10')['workflow_runs']
    checks = api(f'actions/workflows/ci.yml/runs?branch={branch}&status=success&per_page=20')['workflow_runs']
    checked = {r['head_sha'] for r in checks if r['conclusion'] == 'success' and r['head_repository']['full_name'] == REPO}
    for run in builds:
        if run['head_sha'] in checked and run['head_repository']['full_name'] == REPO:
            try:
                release = api(f'releases/tags/dev-build-{run["run_number"]}')
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    continue  # A superseded build intentionally has no release.
                raise
            if release['draft'] or release['target_commitish'] != run['head_sha']:
                raise ValueError('Release is not bound to the tested source commit')
            return run, release
    return None


def health(url, restart_marker, timeout=180):
    until = time.monotonic() + timeout
    # Watchers need time to observe all atomic writes and finish rebuilding.
    time.sleep(10)
    while time.monotonic() < until:
        try:
            if not restart_marker.exists() and isinstance(json.loads(request(url + '/api/auth/setup-status'))['needsSetup'], bool):
                return
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError('Updated server did not become healthy')


def execute(args):
    state = Path(args.state).resolve()
    downloads = Path(args.downloads).resolve()
    runtime = Path(args.source).resolve()
    state.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)
    for private in [state, Path(args.keystore).resolve(), Path(args.password_file).resolve()]:
        if private == downloads or downloads in private.parents:
            raise ValueError('Private state/signing material must never be under the public download root')
    restart = runtime.parent / 'devops-restart'
    if (state/'pending.json').exists():
        rollback(runtime, state)
        atomic(restart, b'rollback\n')
        raise RuntimeError('Recovered interrupted source deployment; waiting for restart')
    found = candidate(args.branch)
    if not found:
        return
    run, release = found
    code, commit = run['run_number'], run['head_sha']
    published = json.loads(request(PUBLIC + '/latest.json'))
    if code <= published['versionCode']:
        return
    failure = state/'failed.json'
    if failure.exists() and json.loads(failure.read_text())['sourceCommit'] == commit:
        return  # Explicitly remove failed.json to retry an inspected failure.
    stage = state / f'build-{code}'
    stage.mkdir(exist_ok=True)
    expected = {'checksums.txt', 'famlin-family-unsigned.apk', 'server-source.tgz', 'package-info.txt', 'source-commit.txt'}
    assets = {a['name']: a for a in release['assets']}
    for name in expected:
        url = assets[name]['browser_download_url']
        if not url.startswith(f'https://github.com/{REPO}/releases/download/dev-build-{code}/'):
            raise ValueError('Unexpected artifact URL')
        data = request(url)
        if len(data) != assets[name]['size']:
            raise ValueError('Incomplete asset')
        atomic(stage/name, data)
    checksums = {}
    for line in (stage/'checksums.txt').read_text().splitlines():
        sha, name = line.split(maxsplit=1)
        checksums[name.strip()] = sha
    for name in expected - {'checksums.txt'}:
        if digest((stage/name).read_bytes()) != checksums[name]:
            raise ValueError(f'Artifact checksum mismatch: {name}')
    if (stage/'source-commit.txt').read_text().strip() != commit:
        raise ValueError('Artifact source mismatch')
    manifest, files = read_bundle((stage/'server-source.tgz').read_bytes(), commit)
    info = (stage/'package-info.txt').read_text()
    match = re.search(r"package: name='cn.olares.hzfystt.famlin' versionCode='(\d+)'", info)
    if not match or int(match[1]) != code:
        raise ValueError('Package/version mismatch')
    signer = [args.java, '-jar', args.apksigner]
    signed = stage/'signed.apk'
    subprocess.run(signer + ['sign', '--ks', args.keystore, '--ks-type', 'PKCS12', '--ks-key-alias', 'famlin', '--ks-pass', 'file:' + args.password_file, '--out', str(signed), str(stage/'famlin-family-unsigned.apk')], check=True)
    report = subprocess.check_output(signer + ['verify', '--verbose', '--print-certs', str(signed)], text=True)
    if CERT not in report.lower():
        raise ValueError('Signing certificate changed: cannot safely update installed apps')
    subprocess.run([sys.executable, str(SCRIPTS.parents[1]/'downloads/scripts/prepare-release.py'),
                    '--apk', str(signed), '--package-info', str(stage/'package-info.txt'), '--source-commit', commit,
                    '--base-url', PUBLIC, '--output', str(stage/'site'),
                    '--notes', '新增完整简体中文界面，可在登录页和个人设置中切换英语、荷兰语和中文。预填家庭开发服务器地址。'], check=True, stdout=subprocess.DEVNULL)
    site = stage/'site'
    metadata = json.loads((site/'latest.json').read_text())
    apk = metadata['apkUrl'].rsplit('/', 1)[1]
    if (downloads/apk).exists() and digest((downloads/apk).read_bytes()) != metadata['sha256']:
        raise ValueError('Immutable APK filename collision')
    atomic(downloads/apk, (site/apk).read_bytes())
    if digest(request(metadata['apkUrl'])) != metadata['sha256']:
        raise ValueError('Public APK download verification failed')
    promoted = ['LICENSE.txt', 'install-qr.png', 'SHA256SUMS', 'index.html', 'latest.json']
    previous_site = {name: (downloads/name).read_bytes() if (downloads/name).exists() else None for name in promoted}
    try:
        result = apply(runtime, state, manifest, files)
        if result['restart']:
            atomic(restart, commit.encode())
        health(args.health_url, restart)
        # The APK is already verified; now promote the installation page and metadata.
        for name in promoted:
            atomic(downloads/name, (site/name).read_bytes())
        if json.loads(request(PUBLIC + '/latest.json'))['sourceCommit'] != commit:
            raise ValueError('Public metadata verification failed')
        accept(state, manifest)
        atomic(state/'published.json', json.dumps({**result, 'versionCode': code, 'runUrl': run['html_url']}).encode())
        print(f'Published Android {code} and server {commit}', flush=True)
    except Exception:
        for name, content in previous_site.items():
            if content is None:
                (downloads/name).unlink(missing_ok=True)
            else:
                atomic(downloads/name, content)
        rollback(runtime, state)
        atomic(restart, b'rollback\n')
        atomic(failure, json.dumps({'sourceCommit': commit, 'versionCode': code}).encode())
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['state', 'downloads', 'source', 'java', 'apksigner', 'keystore', 'password-file']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--branch', default='main')
    parser.add_argument('--health-url', default=SERVER)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    while True:
        try:
            execute(args)
        except Exception as error:
            # Avoid dumping HTTP response bodies or subprocess environments.
            print(f'Deployment failed: {type(error).__name__}: {error}', file=sys.stderr, flush=True)
            if args.once:
                raise SystemExit(1)
        if args.once:
            break
        time.sleep(300)
