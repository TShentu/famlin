import fs from 'node:fs';
import assert from 'node:assert/strict';
const base = new URL('../src/i18n/locales/', import.meta.url);
function flatten(object, prefix = '') {
  return Object.fromEntries(Object.entries(object).flatMap(([key, value]) =>
    typeof value === 'object' ? Object.entries(flatten(value, `${prefix}${key}.`)) : [[prefix + key, value]]));
}
const en = flatten(JSON.parse(fs.readFileSync(new URL('en.json', base), 'utf8')));
const zh = flatten(JSON.parse(fs.readFileSync(new URL('zh.json', base), 'utf8')));
assert.deepEqual(Object.keys(zh).sort(), Object.keys(en).sort(), 'Chinese translation keys must match English');
for (const key of Object.keys(en)) {
  assert.ok(zh[key].trim(), key);
  assert.deepEqual([...zh[key].matchAll(/{{.*?}}/g)].map(m => m[0]).sort(),
    [...en[key].matchAll(/{{.*?}}/g)].map(m => m[0]).sort(), `Interpolation mismatch: ${key}`);
}
console.log(`Chinese: ${Object.keys(zh).length} keys and interpolation placeholders verified`);
