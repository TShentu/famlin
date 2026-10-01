# Famlin Dev on Olares

This is an independent development application (`famlindev`) with its own PostgreSQL database, generated signing key and uploads. It does not depend on the retired Studio app.

## Architecture

The chart reuses the Node 22 / ffmpeg runtime in the pinned upstream image. It mounts `Home/Documents/FamlinDev` at `/workspace`, extracts an uploaded source archive once, and installs development dependencies into the persistent source tree. npm downloads are cached. Subsequent starts reuse dependencies unless a lockfile changes.

The currently tested runtime is pulled through NJU's GHCR cache with the exact upstream digest. This does not alter the production Famlin chart's original GHCR address.

- `source/`: editable checkout contents, including dependencies
- `uploads/`: development media, isolated from production
- `source.tgz`: initial source snapshot; never re-extracted over an existing checkout
- `npm-cache/`: persistent npm cache

Vite listens on 5174 behind the private Olares entrance and proxies `/api`, `/uploads` and `/admin` to the backend. Web changes use WSS HMR on port 443. Backend changes trigger nodemon; committed migrations are applied on backend restart. The admin UI is watch-built; refresh `/admin/` to see admin changes. Shared API client TypeScript is also watched. No demo account or seed data is created.

## Install

From the repository root, archive the checkout excluding `.git`, `node_modules`, `mobile` and `docs` (on macOS set `COPYFILE_DISABLE=1` to omit AppleDouble metadata). Upload it as `drive/Home/Documents/FamlinDev/source.tgz` before installing the chart. The initial npm install can take several minutes. Database configuration is injected by Olares. Create your development administrator at `/admin/`.

```sh
olares-cli chart lint deploy/olares/famlindev
olares-cli chart package deploy/olares/famlindev
olares-cli market upload famlindev-0.1.0.tgz
olares-cli market install famlindev -s upload --version 0.1.0 --watch
```

## Change code without rebuilding an image

Edit directly in Files, or sync specific local files:

```sh
python3 deploy/olares/scripts/sync.py web/src/i18n/locales/zh.json
python3 deploy/olares/scripts/sync.py --watch web/src/components/NewPostModal.tsx web/src/i18n/locales/zh.json
```

The sync command stages files under unique names, verifies SHA-256 and atomically replaces explicitly named source files through cluster exec. This avoids Files collision renaming. Cluster exec access and existing destination parents are required. It never deletes remote files or copies credentials. No container restart is needed for web component or translation edits. Refresh after changing i18n initialization if Vite performs a full page reload.

Dependency/lockfile changes require a development-app restart to rerun `npm ci`; runtime/system library changes require a new base image. This environment is for development, not a replacement for immutable production releases. Keep the entrance private: Vite serves source code.

The chart's Vite allowed-host suffix currently targets `hzfystt.olares.cn`; update it for a different Olares account. Source and runtime paths are intentionally scoped to this dedicated instance.
