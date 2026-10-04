# Famlin Dev delivery

Targets are deliberately fixed to this family installation:

- Source: `TShentu/famlin`; development branch `codex/devops-zh` until reviewed.
- APK page: https://c89009ed.hzfystt.olares.cn/
- Server: https://762e7148.hzfystt.olares.cn/
- Android package: `cn.olares.hzfystt.famlin`, same signing certificate as build 2.

## Candidate pipeline

`android-selfhost.yml` builds the Android APK without release keys, includes ARM and x86_64 libraries, and bundles the exact matching Git source for the server. It tests locale parity, TypeScript, lint, unit tests, then installs a disposable-signed copy in Android 15. The emulator verifies English/Dutch/Chinese switching, the preset server address, and Chinese persistence after restarting the app. The disposable signature is never distributed.

Only passing candidates become `dev-build-N` prereleases. Those APK assets are **unsigned and not installable**. Users install from the Olares page. The GitHub workflow run number remains the increasing Android versionCode; do not reset it or rename the workflow without accounting for published versionCodes.

## Trusted publisher

`scripts/worker.py` is designed to run on a trusted, continuously available publisher. Deployment of that worker and its private key location must be configured before the loop is automatic. It needs Python 3.9+, `qrcode[pil]`, Java 17 and the Android apksigner JAR. It reads public GitHub data; it does not need a personal GitHub token or Olares credentials.

It accepts only an exact commit that passed both the Android pipeline and the full repository CI on the configured branch. It verifies artifact hashes, package name, versionCode and the existing certificate fingerprint, signs privately, uploads the immutable APK, and verifies an anonymous full download. It then applies verified runtime files, waits for server health, and promotes the download page and metadata. A deployment failure restores modified source and the previous download page. `failed.json` prevents repeatedly applying a failing candidate; investigate before removing it to retry.

The keystore, password file and worker state must be outside the public download directory. Preserve the existing certificate; changing it prevents users from installing an update over their existing application.

## Source reload

Runtime source is mounted at `/workspace/source`. Vite and the backend watchers observe atomic file replacements. Files removed from a previous deployment manifest are removed; unmanaged files, uploads, credentials and `node_modules` are never managed by this mechanism. Changed lockfiles or supervisor scripts signal `/workspace/devops-restart`; the supervisor exits, Kubernetes restarts the Dev container, and the existing bootstrap installs the changed dependencies. This does not require an application image build.

New or changed database migrations deliberately stop automatic deployment. Review/apply those separately; a source rollback cannot reverse a database migration safely.

## Network requirement

The current Dev entrance uses Olares authentication. A native client cannot use a browser's Olares session automatically. Member API/media paths therefore need an explicitly approved policy allowing Famlin's own authentication, or the client needs an independently verified LarePass access route. Do not make the Vite source server or admin routes anonymous to solve this.

## Verification

```sh
node web/scripts/check-zh.mjs
(cd mobile && npx tsc --noEmit && npm run lint && npm test -- --runInBand)
python3 -m unittest discover -s deploy/devops/scripts -p 'test_*.py'
```

Current local results: 433 mobile locale keys, 82 mobile tests, and 4 deployment integrity/rollback tests. Android device results and final deployment provenance must be recorded after the actual pipeline finishes; a successful Metro or APK build alone is not a launch test.
