import { useTranslation } from 'react-i18next';
import { LANGUAGE_NAMES, SUPPORTED_LANGUAGES, storeLanguage, type SupportedLanguage } from '../i18n';

export function LanguageSelector() {
  const { t, i18n } = useTranslation();
  return (
    <label>
      {t('layout.language')}
      <select aria-label={t('layout.language')} value={i18n.resolvedLanguage ?? i18n.language}
        onChange={(event) => {
          const language = event.target.value as SupportedLanguage;
          storeLanguage(language);
          void i18n.changeLanguage(language);
        }}>
        {SUPPORTED_LANGUAGES.map(language => (
          <option key={language} value={language}>{LANGUAGE_NAMES[language]}</option>
        ))}
      </select>
    </label>
  );
}
