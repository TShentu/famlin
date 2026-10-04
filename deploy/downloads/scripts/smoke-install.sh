#!/usr/bin/env bash
set -euo pipefail
mkdir -p smoke
trap 'adb logcat -d > smoke/logcat.txt || true' EXIT
adb install -r smoke/app.apk | tee smoke/install.txt
adb shell am start -W -n cn.olares.hzfystt.famlin/.MainActivity | tee smoke/launch.txt
sleep 15
adb shell pidof cn.olares.hzfystt.famlin > smoke/pid.txt
adb shell uiautomator dump /sdcard/window.xml
adb pull /sdcard/window.xml smoke/window.xml
adb exec-out screencap -p > smoke/screen.png
python3 - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as ET
root = ET.parse('smoke/window.xml').getroot()
texts = [n.get('text', '') for n in root.iter('node')]
Path('smoke/screen-text.txt').write_text('\n'.join(texts))
assert any('server' in t.lower() or '服务器' in t for t in texts), texts
assert 'Success' in Path('smoke/install.txt').read_text()
print('Hosted, locally signed APK installed and rendered the server login screen.')
PY
