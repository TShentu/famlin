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

`scripts/worker.py` is designed to run on a trusted, continuously available publisher. The `famlindevops` Olares chart runs this publisher on hzfystt. Signing files and state live in the app-private `Data/famlindevops` directory, separate from the public APK folder. It needs Python 3.9+, `qrcode[pil]`, Java 17 and the Android apksigner JAR. The existing certificate was retained. A checksum-pinned Java 17 runtime and a private Python environment are bootstrapped once in persistent app data. It reads public GitHub data; it does not need a personal GitHub token or Olares credentials.

It accepts only an exact commit that passed both the Android pipeline and the full repository CI on the configured branch. It verifies artifact hashes, package name, versionCode and the existing certificate fingerprint, signs privately, uploads the immutable APK, and verifies an anonymous full download. It then applies verified runtime files, waits for server health, and promotes the download page and metadata. A deployment failure restores modified source and the previous download page. `failed.json` prevents repeatedly applying a failing candidate; investigate before removing it to retry.

The keystore, password file and worker state must be outside the public download directory. Preserve the existing certificate; changing it prevents users from installing an update over their existing application.

## Source reload

Runtime source is mounted at `/workspace/source`. Vite and the backend watchers observe atomic file replacements. Files removed from a previous deployment manifest are removed; unmanaged files, uploads, credentials and `node_modules` are never managed by this mechanism. Changed lockfiles or supervisor scripts signal `/workspace/devops-restart`; the supervisor exits, Kubernetes restarts the Dev container, and the existing bootstrap installs the changed dependencies. This does not require an application image build.

New or changed database migrations deliberately stop automatic deployment. Review/apply those separately; a source rollback cannot reverse a database migration safely.

## Network requirement

The owner explicitly authorized the entire Dev entrance to be Public on 2026-10-04. Native clients connect directly and Famlin still checks its application accounts/tokens. This exposes the development frontend/source routes too; use only this independent development instance. The production Famlin entrance is unchanged.

## Verification

```sh
node web/scripts/check-zh.mjs
(cd mobile && npx tsc --noEmit && npm run lint && npm test -- --runInBand)
python3 -m unittest discover -s deploy/devops/scripts -p 'test_*.py'
```

Current local results: 433 mobile locale keys, 82 mobile tests, and 4 deployment integrity/rollback tests. Android device results and final deployment provenance must be recorded after the actual pipeline finishes; a successful Metro or APK build alone is not a launch test.

## Publisher chart updates

Run `python3 deploy/devops/scripts/prepare-chart.py`, lint/package the chart, then upgrade `famlindevops` through Olares Market. The chart code checksum rolls the publisher when its code changes. Keep a secure backup of the original signing directory; deleting the publisher app data would otherwise remove its signing copy. Check the private status entrance for the current phase, published commit, or failed candidate.
