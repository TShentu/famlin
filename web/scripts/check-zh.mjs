import fs from 'node:fs';
import assert from 'node:assert/strict';
import { URL } from 'node:url';
import { log } from 'node:console';
function flatten(object, prefix = '') {
  return Object.fromEntries(Object.entries(object).flatMap(([key, value]) =>
    typeof value === 'object' ? Object.entries(flatten(value, `${prefix}${key}.`)) : [[prefix + key, value]]));
}
for (const [name, path] of [
  ['web', '../src/i18n/locales/'],
  ['admin', '../../backend/admin/src/i18n/locales/'],
  ['server', '../../backend/src/i18n/locales/'],
]) {
  const base = new URL(path, import.meta.url);
  const en = flatten(JSON.parse(fs.readFileSync(new URL('en.json', base), 'utf8')));
  for (const language of ['nl', 'zh']) {
    const translated = flatten(JSON.parse(fs.readFileSync(new URL(`${language}.json`, base), 'utf8')));
    assert.deepEqual(Object.keys(translated).sort(), Object.keys(en).sort(), `${name}/${language}: translation keys must match English`);
    for (const key of Object.keys(en)) {
      assert.ok(translated[key].trim(), `${name}/${language}/${key}`);
      assert.deepEqual([...translated[key].matchAll(/{{.*?}}/g)].map(m => m[0]).sort(),
        [...en[key].matchAll(/{{.*?}}/g)].map(m => m[0]).sort(), `Interpolation mismatch: ${name}/${language}/${key}`);
    }
    log(`${name}/${language}: ${Object.keys(translated).length} keys and interpolation placeholders verified`);
  }
}
