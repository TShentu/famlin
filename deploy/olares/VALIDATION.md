# Development validation — 2026-10-01

- Independent `famlindev` installed on Olares 1.12.7 (amd64). Separate PostgreSQL database, signing key and `Home/Documents/FamlinDev/uploads`.
- Existing pinned upstream runtime reused; no application image was built for these changes.
- Initial source snapshot started in English. Browser connected to Vite through the private HTTPS entrance and WSS.
- Synced Chinese locale and login language selector while that tab remained open. Vite logged a hot update to LoginPage.tsx and the selector appeared automatically.
- Selected 简体中文, then synced another Chinese subtitle change. The open page automatically displayed “记录生活，让家人更亲近”. No image rebuild or container restart was needed for either UI change. Changes to i18n resources can trigger Vite's automatic page reload; React component changes use HMR.
- All 281 user-web English keys have Chinese counterparts with matching interpolation placeholders. Admin UI and backend error messages remain in their upstream languages.
- TypeScript and Vite build passed in the development container after localization.
- Files upload auto-renames collisions on this device. The sync helper now stages unique names and uses checksum-verified atomic replacement in the development container.
- Backend watching uses nodemon polling for the Files host mount; admin changes are watch-built and require browser refresh.

The environment is intentionally private and has not been seeded with production users or media. Use `/admin/` for initial development-account setup. Source includes the file-selection snapshot fix, but an end-to-end video upload with that fix is not part of this hot-update validation.
