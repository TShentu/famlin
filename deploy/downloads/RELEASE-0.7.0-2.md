# First hosted release — 2026-10-04

- Public installation page: https://c89009ed.hzfystt.olares.cn/
- APK: https://c89009ed.hzfystt.olares.cn/famlin-0.7.0-2-250d9c327cae.apk
- Metadata: https://c89009ed.hzfystt.olares.cn/latest.json
- Source: `20776379c7dea02fbe33aa857eb8a5003ee928af`
- Build: https://github.com/TShentu/famlin/actions/runs/37176162050
- Package: `cn.olares.hzfystt.famlin`, version `0.7.0`, versionCode `2`
- Minimum Android: 7.0 / API 24; ABIs: arm64-v8a and armeabi-v7a
- Signed APK: 55,130,943 bytes
- SHA-256: `250d9c327caef0b98f14d5fc3939b2bc3b65942733cbbbbfcfddb0d753f63b47`
- Signing certificate SHA-256: `2235d7b2444d8ea6a30158487d62d261f8074858ddfde061f0954d818769d9e3`

Validation completed:

- Release build succeeded; original unsigned artifact checksum verified.
- Local apksigner verification passed using APK Signature Schemes v2 and v3.
- Full anonymous HTTPS download matched the signed file's size and SHA-256.
- APK response has Android package MIME type and attachment disposition.
- Byte-range request returned HTTP 206 and the requested 1,024 bytes.
- Public metadata exactly matched local metadata.
- Downloaded QR decoded to the permanent installation page URL.
- Download page rendered correctly at a narrow mobile viewport.
- GitHub's independent runner downloaded the public APK and verified its checksum.

Installation test: https://github.com/TShentu/famlin/actions/runs/37178194152

- Android 15 Google APIs x86_64 emulator accepted the signed APK (`adb install`: `Success`).
- The overall launch test failed. SoLoader searched `base.apk!/lib/x86_64` and could not load `libreactnative.so`; this APK contains arm64-v8a and armeabi-v7a libraries, both verified present. ARM translation in this emulator did not provide a successful application launch.
- Physical ARM-device launch and authenticated photo operations have **not** been verified. Do not represent the failed launch test as a passing device test. A native ARM device is the next validation target; an APK built with x86_64 libraries would enable this specific emulator workflow.

This release does not include an in-app update checker or configured Expo/FCM remote push. The distribution page does not contain family media. Keep the existing signing key for future APK updates, and increment versionCode.
