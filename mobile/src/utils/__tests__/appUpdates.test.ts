import Constants from 'expo-constants';
import { Alert, Linking, Platform } from 'react-native';
import { checkForAppUpdate, parseRelease, UPDATE_ORIGIN } from '../appUpdates';

jest.mock('@/i18n', () => ({ __esModule: true, default: { t: (key: string) => key } }));
const release = { schemaVersion: 1, packageName: 'cn.olares.hzfystt.famlin', versionCode: 99,
  minSdk: 24, sourceCommit: 'a'.repeat(40), apkUrl: `${UPDATE_ORIGIN}/famlin-0.7.0-99-abc.apk` };

describe('APK release validation', () => {
  it('accepts the distribution manifest', () => expect(parseRelease(release)).toEqual(release));
  it.each([
    { packageName: 'another.app' }, { versionCode: '99' }, { versionCode: -1 },
    { schemaVersion: 2 }, { sourceCommit: 'invalid' }, { minSdk: null },
    { apkUrl: 'https://evil.example/file.apk' }, { apkUrl: `${UPDATE_ORIGIN}/file.html` },
    { apkUrl: `${UPDATE_ORIGIN}/famlin.apk?redirect=evil` },
  ])('rejects invalid metadata %j', (change) => expect(() => parseRelease({ ...release, ...change })).toThrow());
});

describe('update checks', () => {
  beforeEach(() => {
    Object.defineProperty(Platform, 'OS', { configurable: true, value: 'android' });
    Object.defineProperty(Platform, 'Version', { configurable: true, value: 35 });
    Constants.expoConfig = { name: 'test', slug: 'test', extra: { selfHosted: true }, android: { versionCode: 98 } };
    globalThis.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => release });
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined);
  });
  afterEach(() => jest.restoreAllMocks());

  it('prompts and opens the exact APK only when the download button is pressed', async () => {
    await checkForAppUpdate(true);
    expect(Linking.openURL).not.toHaveBeenCalled();
    const buttons = jest.mocked(Alert.alert).mock.calls[0][2]!;
    buttons[1].onPress!();
    expect(Linking.openURL).toHaveBeenCalledWith(release.apkUrl);
  });
  it.each([99, 100])('does not offer equal or older builds (installed %i)', async (versionCode) => {
    Constants.expoConfig!.android!.versionCode = versionCode;
    await checkForAppUpdate(true);
    expect(Alert.alert).toHaveBeenCalledWith('updates.title', 'updates.current');
  });
  it('reports network errors for manual checks', async () => {
    jest.mocked(fetch).mockRejectedValue(new Error('offline'));
    await checkForAppUpdate(true);
    expect(Alert.alert).toHaveBeenCalledWith('updates.title', 'updates.failed');
  });
  it('does not offer an incompatible APK', async () => {
    Object.defineProperty(Platform, 'Version', { configurable: true, value: 23 });
    await checkForAppUpdate(true);
    expect(Alert.alert).toHaveBeenCalledWith('updates.title', 'updates.incompatible');
  });
  it('does not check updates in upstream builds', async () => {
    Constants.expoConfig!.extra = {};
    await checkForAppUpdate(true);
    expect(fetch).not.toHaveBeenCalled();
  });
  it('suppresses repeated automatic checks', async () => {
    await checkForAppUpdate(true);
    jest.mocked(fetch).mockClear();
    await checkForAppUpdate();
    expect(fetch).not.toHaveBeenCalled();
  });
});
