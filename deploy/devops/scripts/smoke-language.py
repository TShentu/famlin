#!/usr/bin/env python3
"""Exercise real Android UI language selection and persistence with adb."""
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def adb(*args):
    return subprocess.check_output(['adb', *args])


def screen(name):
    adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml')
    adb('pull', '/sdcard/window.xml', f'smoke/{name}.xml')
    Path(f'smoke/{name}.png').write_bytes(adb('exec-out', 'screencap', '-p'))
    return ET.parse(f'smoke/{name}.xml').getroot()


def tap(text):
    root = screen('before-language')
    node = next(n for n in root.iter('node') if n.get('text') == text)
    x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds')))
    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
    time.sleep(2)


for language, expected in [('简体中文', '继续'), ('Nederlands', 'Doorgaan'), ('English', 'Continue'), ('简体中文', '继续')]:
    tap(language)
    root = screen('language-' + language)
    texts = [n.get('text', '') for n in root.iter('node')]
    assert expected in texts, texts
    assert any('762e7148.hzfystt.olares.cn' in t for t in texts), texts
adb('shell', 'am', 'force-stop', 'cn.olares.hzfystt.famlin')
adb('shell', 'am', 'start', '-W', '-n', 'cn.olares.hzfystt.famlin/.MainActivity')
time.sleep(5)
assert any(n.get('text') == '继续' for n in screen('zh-restart').iter('node'))
print('English/Dutch/Chinese switching, Dev server default and persistence passed on Android.')
