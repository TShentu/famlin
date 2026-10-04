import Constants from 'expo-constants';
import { Alert, Linking, Platform } from 'react-native';
import i18n from '@/i18n';

export const UPDATE_ORIGIN = 'https://c89009ed.hzfystt.olares.cn';
export type ApkRelease = { versionCode: number; sourceCommit: string; apkUrl: string; minSdk: number };

export function parseRelease(value: unknown): ApkRelease {
  const r = value as Record<string, unknown> | null;
  if (!r || r.schemaVersion !== 1 || r.packageName !== 'cn.olares.hzfystt.famlin' ||
      !Number.isSafeInteger(r.versionCode) || Number(r.versionCode) < 1 ||
      !Number.isSafeInteger(r.minSdk) || Number(r.minSdk) < 1 ||
      typeof r.sourceCommit !== 'string' || !/^[0-9a-f]{40}$/.test(r.sourceCommit) ||
      typeof r.apkUrl !== 'string') throw new Error('Invalid APK release');
  const url = new URL(r.apkUrl);
  if (url.origin !== UPDATE_ORIGIN || url.username || url.password || url.search || url.hash ||
      !/^\/famlin-[a-zA-Z0-9._+-]+\.apk$/.test(url.pathname)) throw new Error('Invalid APK URL');
  return r as ApkRelease;
}

export function updatesEnabled() {
  return Platform.OS === 'android' && Constants.expoConfig?.extra?.selfHosted === true;
}

let busy = false;
let lastCheck = 0;
let lastPrompted = 0;
const CHECK_INTERVAL = 6 * 60 * 60 * 1000;

/** Automatic errors stay silent; manual checks always provide feedback. */
export async function checkForAppUpdate(manual = false) {
  if (!updatesEnabled() || busy || (!manual && Date.now() - lastCheck < CHECK_INTERVAL)) return;
  const installed = Constants.expoConfig?.android?.versionCode;
  if (!Number.isSafeInteger(installed)) return;
  busy = true;
  lastCheck = Date.now();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${UPDATE_ORIGIN}/latest.json?t=${Date.now()}`, {
      signal: controller.signal,
      headers: { 'Cache-Control': 'no-cache' },
    });
    if (!response.ok) throw new Error('Release request failed');
    const release = parseRelease(await response.json());
    if (release.versionCode <= installed!) {
      if (manual) Alert.alert(i18n.t('updates.title'), i18n.t('updates.current'));
      return;
    }
    if (Number(Platform.Version) < release.minSdk) {
      if (manual) Alert.alert(i18n.t('updates.title'), i18n.t('updates.incompatible'));
      return;
    }
    if (!manual && lastPrompted === release.versionCode) return;
    lastPrompted = release.versionCode;
    Alert.alert(i18n.t('updates.available'), i18n.t('updates.message', { commit: release.sourceCommit.slice(0, 7) }), [
      { text: i18n.t('updates.later'), style: 'cancel' },
      { text: i18n.t('updates.download'), onPress: () => {
        void Linking.openURL(release.apkUrl).catch(() => {
          Alert.alert(i18n.t('updates.title'), i18n.t('updates.openFailed'));
        });
      } },
    ]);
  } catch {
    if (manual) Alert.alert(i18n.t('updates.title'), i18n.t('updates.failed'));
  } finally {
    clearTimeout(timeout);
    busy = false;
  }
}
