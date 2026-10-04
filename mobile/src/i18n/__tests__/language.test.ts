import i18n, { initI18nLanguage } from '../index';
import { getLanguage } from '@/utils/storage';
import { getLocales } from 'expo-localization';

jest.mock('@/utils/storage', () => ({ getLanguage: jest.fn() }));
jest.mock('expo-localization', () => ({ getLocales: jest.fn() }));

beforeEach(() => {
  jest.mocked(getLanguage).mockResolvedValue(null);
  jest.mocked(getLocales).mockReturnValue([{ languageCode: 'zh', languageTag: 'zh-CN' }] as unknown as ReturnType<typeof getLocales>);
});

test('Chinese devices start in Chinese and interpolate counts', async () => {
  await initI18nLanguage();
  expect(i18n.language).toBe('zh');
  expect(i18n.t('login.continueButton')).toBe('继续');
  expect(i18n.t('relativeTime.minutesAgo', { count: 2 })).toBe('2 分钟前');
});

test('persisted selection takes precedence over device language', async () => {
  jest.mocked(getLanguage).mockResolvedValue('nl');
  await initI18nLanguage();
  expect(i18n.language).toBe('nl');
});

test('unsupported saved and device languages fall back to English', async () => {
  jest.mocked(getLanguage).mockResolvedValue('invalid');
  jest.mocked(getLocales).mockReturnValue([{ languageCode: 'de' }] as unknown as ReturnType<typeof getLocales>);
  await initI18nLanguage();
  expect(i18n.language).toBe('en');
});
