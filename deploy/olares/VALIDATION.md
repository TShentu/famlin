# Development validation — 2026-10-01

- Independent `famlindev` installed on Olares 1.12.7 (amd64). Separate PostgreSQL database, signing key and `Home/Documents/FamlinDev/uploads`.
- Existing pinned upstream runtime reused; no application image was built for these changes.
- Initial source snapshot started in English. Browser connected to Vite through the private HTTPS entrance and WSS.
- Synced Chinese locale and login language selector while that tab remained open. Vite logged a hot update to LoginPage.tsx and the selector appeared automatically.
- Selected 简体中文, then synced another Chinese subtitle change. The open page automatically displayed “记录生活，让家人更亲近”. No image rebuild or container restart was needed for either UI change. Changes to i18n resources can trigger Vite's automatic page reload; React component changes use HMR.
- All locale catalogs have matching English/Dutch/Chinese keys and interpolation placeholders: web 281, admin 359, server 144. The checker imports Node URL/console explicitly and passes ESLint.
- TypeScript and Vite build passed in the development container after localization.
- Files upload auto-renames collisions on this device. The sync helper now stages unique names and uses checksum-verified atomic replacement in the development container.
- Backend watching uses nodemon polling for the Files host mount; admin changes are watch-built and require browser refresh.

The environment is intentionally private and has not been seeded with production users or media. Use `/admin/` for initial development-account setup. Source includes the file-selection snapshot fix, but an end-to-end video upload with that fix is not part of this hot-update validation.

## Admin and server localization

- Browser verified English, Nederlands and 简体中文 dashboard switching, Chinese server settings, and all three server-default language options. The existing server default was preserved.
- UI language persists across reloads; the HTML language follows the selection. Login and first-time setup expose the same selector.
- Web/admin API requests send the selected Accept-Language. Unauthenticated read-only requests returned localized 401 errors for en, nl and zh-CN.
- Admin and web TypeScript/Vite builds and server TypeScript checks passed. Admin ESLint has no errors when excluding macOS AppleDouble metadata (`--ignore-pattern "**/._*"`); existing upstream warnings remain.
- Sync tolerates concurrent repeated exec calls: a missing staging file is accepted only when the destination checksum matches.

## Pre-merge CI review — 2026-10-01

- Source lint uses `--max-warnings 0` for web, API client, backend, admin and mobile. Replaced loose types, corrected dependencies and stale callbacks, and documented local exceptions for native imperative handles and external-input/loading effects rather than disabling rules globally.
- Web: 111 tests; API client: 57 tests; mobile: 79 tests. Mobile tests now await asynchronous rendering/mutations, avoid native fetch initialization during teardown and disable test cache GC timers.
- Updated Docker build Actions to their Node 24 releases, exported the CI build with `load`, migrated Vite/Docusaurus configuration and split React/i18n vendor bundles.
- Backend, admin and mobile dependency audits have no known vulnerabilities after compatible updates. The mobile xcode UUID override preserves its v4 API and passes Expo's dependency alignment check.
- Documentation dependencies were reduced from 32 audit findings to six high-severity findings, all stemming from Postman's pinned `@faker-js/faker` 5.5.3 dependency. This is a build-only toolchain that processes repository-owned OpenAPI input and is not included in the application image. The current Postman package still requires the old Faker API/locale paths; forcing a modern major version is not a compatible fix. The user explicitly accepted this residual risk before merge.
- Retained upstream deprecation notices include Expo/Jest's legacy transitive packages, Postman's old Faker, and Prisma/pg's concurrent-client-query notice. Expected error-path test logs are not CI failures. These were not globally silenced.
