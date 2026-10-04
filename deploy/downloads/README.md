# Famlin Android distribution on Olares

Phase 1 provides a self-hosted HTTPS download page, a QR code, signed APKs and machine-readable release metadata. It does **not** yet implement an in-app update checker or silent installation.

## Deployment

- Target identity: `hzfystt@olares.cn`
- App: `famlindownloads`; namespace: `famlindownloads-hzfystt`
- Public entrance: https://c89009ed.hzfystt.olares.cn/
- Files: `drive/Home/Documents/FamlinDownloads/`
- Nginx mounts only that dedicated directory read-only. There is no public upload endpoint, directory listing, account database or photo storage.
- HTTPS is terminated by Olares. Nginx supports Range requests; APK filenames contain version, build number and checksum and can be cached. The page, QR and `latest.json` revalidate on each visit.
- Architecture was checked live on 2026-10-04: amd64. The reused `beclab/aboveos-nginx:1.27.0` manifest supports amd64 and arm64. The application runs as UID/GID 1000.

Deploy using `olares-cli chart lint`, `chart package`, `market upload`, then `market install -s upload`. For chart changes, increase both chart versions and use `market upgrade`. Updating downloadable content does not require an app upgrade.

## Android build and signing

`.github/workflows/android-selfhost.yml` builds a release APK on GitHub Actions, without Expo accounts or upstream store credentials. Run it on the desired source branch after it is available as a workflow; the initial development branch also triggers builds on relevant pushes.

The self-hosted build sets `FAMLIN_SELF_HOSTED=1`:

- Package: `cn.olares.hzfystt.famlin` (separate from the upstream Google Play application).
- Name: `Famlin 家庭相册`.
- `FAMLIN_BUILD_NUMBER` becomes the integer Android versionCode. CI uses the workflow run number; keep this number strictly increasing when migrating workflows.
- The upstream author's EAS project and Firebase configuration are omitted. Expo/FCM remote push is not configured for this family build. This does not prevent server login, photo viewing or uploads.
- The artifact is **unsigned**; it cannot be installed until the publisher signs it locally.

Release private keys and passwords must remain outside the repository and the public download directory. A persistent PKCS12 keystore (alias `famlin`) is used for all releases. Back it up securely: losing it prevents normal updates to the installed application. No signing secrets were uploaded to GitHub.

Download the build artifact, then run:

```sh
python3 deploy/downloads/scripts/sign-apk.py \
  --java /path/to/java \
  --apksigner /path/to/build-tools/lib/apksigner.jar \
  --keystore /private/path/release.p12 \
  --password-file /private/path/password \
  --input /path/to/famlin-family-unsigned.apk \
  --output /path/to/famlin-family.apk
```

## Prepare and publish a release

Install `qrcode[pil]==8.2` in a local virtual environment. The following command generates a site directory containing the signed APK, installation page, QR code, `latest.json`, and SHA256SUMS:

```sh
python deploy/downloads/scripts/prepare-release.py \
  --apk /path/to/famlin-family.apk \
  --package-info /path/to/artifact/package-info.txt \
  --source-commit FULL_GIT_COMMIT \
  --base-url https://c89009ed.hzfystt.olares.cn \
  --output /path/to/release-site
```

Before publishing, verify the signature with `apksigner verify`, and check the versionCode is greater than the published one. Upload the immutable, uniquely named APK **first**, then verify a complete unauthenticated HTTPS download has the expected SHA-256. Promote `latest.json` and the HTML page only after verification. Do not overwrite a published APK filename with new bytes.

Use Olares Files for uploads. Its backend may rename collisions, so never assume uploading `latest.json` overwrites it: explicitly use `files edit` for existing text metadata (requires a terminal/editor). The serving container has a read-only data mount. Do not delete and reinstall the service to publish an APK.

The QR code points to the permanent **page URL**, so printed/shared QR codes survive future versions. No third-party QR service is used. Only installation artifacts belong in this directory; never upload the signing directory, source archives, credentials or family photos.

## Validation

Verify anonymous HTTPS access, MIME type, Content-Disposition, file size, full-download checksum, HTTP Range (206), QR decoding back to the page URL, and signature validity. A successful build alone is not a device installation test. Record actual emulator/phone testing separately.

## Phase 2

Add a small client updater consuming `latest.json`: compare versionCode, show release notes, download the APK, validate size/hash, and hand off to Android's package installer. Keep this HTTPS endpoint stable and maintain the same package and signing key. An updater cannot silently replace packages on arbitrary personal phones. Native feature changes still require an APK even if JavaScript OTA updates are introduced later.
