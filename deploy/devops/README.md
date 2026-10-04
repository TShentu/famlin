# Famlin Dev delivery

Targets are deliberately fixed to this family installation:

- Source: `TShentu/famlin`; automatic delivery from `main` only.
- APK page: https://c89009ed.hzfystt.olares.cn/
- Server: https://762e7148.hzfystt.olares.cn/
- Android package: `cn.olares.hzfystt.famlin`, same signing certificate as build 2.

## Candidate pipeline

`android-selfhost.yml` builds the Android APK without release keys, includes ARM and x86_64 libraries, and bundles the exact matching Git source for the server. It tests locale parity, TypeScript, lint, unit tests, then installs a disposable-signed copy in Android 15. The emulator verifies English/Dutch/Chinese switching, the preset server address, and Chinese persistence after restarting the app. The disposable signature is never distributed.

Only candidates passing both Android smoke tests and the full repository CI are pushed over HTTPS to the Olares publisher. A dedicated repository secret authorizes this upload; it has no GitHub API permissions and is not the Android signing key. The Actions job waits for the publisher to confirm the source commit was deployed before succeeding. Users install the signed APK from the Olares page. The GitHub workflow run number remains the increasing Android versionCode; do not reset it or rename the workflow without accounting for published versionCodes.

## Trusted publisher

`scripts/worker.py` is designed to run on a trusted, continuously available publisher. The `famlindevops` Olares chart runs this publisher on hzfystt. Signing files and state live in the app-private `Data/famlindevops` directory, separate from the public APK folder. It needs Python 3.9+, `qrcode[pil]`, Java 17 and the Android apksigner JAR. The existing certificate was retained. A checksum-pinned Java 17 runtime and a private Python environment are bootstrapped once in persistent app data. It receives authenticated build bundles from Actions rather than polling GitHub, because direct GitHub TLS from this Olares instance is unreliable. It needs neither a personal GitHub token nor Olares credentials.

The Actions upload job checks both pipelines at the exact commit. The receiver requires the dedicated upload credential, verifies payload size/hash, and accepts only this repository and main (the development branch override is used only during initial validation). It verifies artifact hashes, package name, versionCode and the existing certificate fingerprint, signs privately, uploads the immutable APK, and verifies an anonymous full download. It then applies verified runtime files, waits for server health, and promotes the download page and metadata. A deployment failure restores modified source and the previous download page. `failed.json` prevents repeatedly applying a failing candidate; investigate before removing it to retry.

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

Validated: 433 mobile locale keys, 82 mobile tests, and 8 deployment integrity/rollback/transfer tests. Android 15 emulator runs verify all three language options, Chinese persistence after restart, and connection to the actual Dev API. Physical ARM devices have not been tested. The authenticated publisher status and public `latest.json` record the deployed commit and build number.

## Publisher chart updates

Run `python3 deploy/devops/scripts/prepare-chart.py`, lint/package the chart, then upgrade `famlindevops` through Olares Market. The chart code checksum rolls the publisher when its code changes. Keep a secure backup of the original signing directory; deleting the publisher app data would otherwise remove its signing copy. Check the private status entrance for the current phase, published commit, or failed candidate.

## Upload credential

`FAMLIN_DEPLOY_TOKEN` in repository Actions secrets must match the private `/state/deploy-token` file. Only `/candidates` bypasses the publisher entrance’s Olares login, and the application requires this bearer credential for both upload and status polling. The status homepage remains private. Do not place this token in the public APK directory or source repository. Rotate the two copies together if needed.

## Dependency review (2026-10-04)

The final review updated `@fastify/busboy` from 3.2.0 to 3.2.2 and `http-cache-semantics` from 4.2.0 to 4.3.0. Backend `npm audit --omit=dev` reports zero vulnerabilities. The following upstream toolchain advisories still have no published patched version at review time:

- [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm): `braces` deeply nested pattern denial of service. Transitive through file watchers/build/test tools (including Dev nodemon), not imported by Famlin application source. This setup uses repository-controlled glob patterns; do not accept glob patterns from users or run untrusted repositories in the publisher.
- [GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv): `node-forge` RSA signature validation. Present through Expo CLI code-signing tooling; Android publication uses Java apksigner, not this package. Expo OTA updates are not configured in this delivery flow.
- The previously accepted Postman/Faker documentation-generator advisory remains. Documentation generation uses repository-controlled input and does not run in the app image.

Audit totals include dependent packages, so one advisory can report many affected packages. These residual alerts are not fixed or suppressed; review their upstream patches separately.

Delivery uses 1 MiB chunks over up to 16 parallel authenticated connections, verifies the assembled SHA-256, and queues only the complete bundle. The Android workflow accepts an optional `candidate_run` when manually dispatched to retry delivery of an existing APK without recompiling. Both successful APK/smoke jobs and matching repository CI are verified again; the publisher still enforces its allowed branch and increasing versionCode.
