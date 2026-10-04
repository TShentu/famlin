#!/usr/bin/env python3
"""Generate a static download site from a locally signed APK. Requires qrcode[pil]."""
import argparse
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import qrcode

p = argparse.ArgumentParser()
p.add_argument('--apk', type=Path, required=True)
p.add_argument('--package-info', type=Path, required=True)
p.add_argument('--source-commit', required=True)
p.add_argument('--base-url', required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--notes', default='家庭自托管版本，支持连接自己的 Famlin 服务器。')
args = p.parse_args()
url = urlparse(args.base_url)
if url.scheme != 'https' or not url.netloc or url.query or url.fragment:
    p.error('--base-url must be a public HTTPS URL without a query or fragment')
if not re.fullmatch(r'[0-9a-f]{40}', args.source_commit):
    p.error('--source-commit must be a full Git commit SHA')
base = args.base_url.rstrip('/')
info = args.package_info.read_text()
package = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", info)
minimum = re.search(r"sdkVersion:'(\d+)'", info)
if not package or package[1] != 'cn.olares.hzfystt.famlin' or not minimum:
    p.error('Unexpected APK package metadata')
version, code = package[3], int(package[2])
if not re.fullmatch(r'[0-9A-Za-z._+-]+', version):
    p.error('Invalid version name')
digest = hashlib.sha256(args.apk.read_bytes()).hexdigest()
filename = f'famlin-{version}-{code}-{digest[:12]}.apk'
out = args.output
out.mkdir(parents=True, exist_ok=True)
shutil.copyfile(args.apk, out / filename)
size = args.apk.stat().st_size
metadata = dict(schemaVersion=1, packageName=package[1], versionName=version,
                versionCode=code, minSdk=int(minimum[1]), size=size, sha256=digest,
                apkUrl=f'{base}/{filename}', downloadPage=base+'/',
                sourceCommit=args.source_commit, releaseNotes=args.notes,
                publishedAt=datetime.now(timezone.utc).isoformat(), mandatory=False)
(out/'latest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
(out/'SHA256SUMS').write_text(f'{digest}  {filename}\n')
shutil.copyfile(Path(__file__).resolve().parents[3]/'LICENSE', out/'LICENSE.txt')
qrcode.make(base+'/').save(out/'install-qr.png')
e = html.escape
document = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>安装 Famlin · 家庭相册</title>
<style>
:root{font-family:system-ui,-apple-system,"PingFang SC",sans-serif;color:#143d42;background:#f0f7f5;line-height:1.7}*{box-sizing:border-box}body{margin:0;padding:40px 20px}main{max-width:780px;margin:auto}.brand{font-size:18px;font-weight:750;color:#177867;letter-spacing:.03em}.card{margin-top:24px;padding:40px;background:#fff;border:1px solid #dcebe5;border-radius:28px;box-shadow:0 14px 60px #154f3c08}.hero{display:grid;grid-template-columns:1fr 180px;gap:28px;align-items:center}.eyebrow{font-size:13px;color:#618079;margin:0}h1{font-size:34px;line-height:1.3;letter-spacing:-.03em;margin:12px 0}h2{font-size:18px;margin:0 0 16px}.sub{color:#5c7474;margin:12px 0 24px}.download{display:inline-block;background:#146f5a;color:white;text-decoration:none;font-weight:650;padding:13px 25px;border-radius:13px}.meta{font-size:13px;color:#648080;margin:12px 0}.qr{text-align:center;font-size:12px;color:#648080}.qr img{width:180px;height:180px;display:block}.divider{border:0;border-top:1px solid #e5eeea;margin:30px 0}ol{padding-left:23px;margin:0}li{padding:5px 0;color:#45615f}.note{background:#f0f7f5;padding:14px 18px;border-radius:12px;font-size:14px}.wechat{display:none;background:#fff0d5;color:#78541f;padding:16px;border-radius:12px;margin-bottom:20px}details{font-size:12px;color:#648080;margin-top:24px}code{word-break:break-all}footer{font-size:12px;color:#77918c;margin:22px 0;text-align:center}a{color:#146f5a}@media(max-width:600px){body{padding:24px 16px}.card{padding:26px 22px}.hero{grid-template-columns:1fr}.qr{display:none}h1{font-size:29px}.download{display:block;text-align:center}}
</style></head><body><main><div class="brand">Famlin / 家庭相册</div><section class="card">
<div class="wechat" id="wechat">请点右上角「⋯」，选择「在浏览器中打开」，再下载安装。</div>
<div class="hero"><div><p class="eyebrow">把生活里的小事，留给最亲的人</p><h1>家人的日常，<br>在这里相聚。</h1><p class="sub">安装安卓客户端，连接家庭自己的相册。<br>照片、视频和成长点滴，一起慢慢收藏。</p>
<a class="download" href="APK_URL" download>下载 Android 安装包</a><p class="meta">版本 <a href="https://github.com/TShentu/famlin/commit/COMMIT"><code>SHORT_SHA</code></a> · SIZE MB · Android MINANDROID 及以上</p></div>
<div class="qr"><img src="install-qr.png" alt="安卓手机扫描二维码打开安装页" width="180" height="180">安卓手机扫码安装</div></div>
<hr class="divider"><h2>三步开始使用</h2><ol><li>点击上方按钮，下载完成后打开 APK 文件。</li><li>按手机提示允许此浏览器安装应用，再确认安装。</li><li>打开 Famlin，填写家人提供的服务器地址并登录，或使用家庭邀请链接。</li></ol>
<p class="note">这是家庭自托管版本。以后的新版本也会在此页面提供，直接覆盖安装即可，无需先卸载。</p>
<h2>本次更新</h2><p class="sub">NOTES</p><details><summary>版本与文件校验信息</summary><p>包名：<code>cn.olares.hzfystt.famlin</code><br>构建编号：CODE<br>SHA-256：<code>DIGEST</code><br>源代码提交：<code>COMMIT</code></p><a href="latest.json">版本信息</a> · <a href="SHA256SUMS">校验文件</a></details>
</section><footer><a href="https://github.com/TShentu/famlin">Famlin 开源项目</a> · <a href="LICENSE.txt">MIT 许可</a><br>此页面仅分发安装包，不存储家庭照片</footer></main><script>if(/MicroMessenger/i.test(navigator.userAgent))document.getElementById('wechat').style.display='block';</script></body></html>'''
for key, value in dict(APK_URL=filename, SHORT_SHA=args.source_commit[:7], SIZE=f'{size/1024/1024:.1f}',
                       MINANDROID={'24':'7.0'}.get(minimum[1], 'API '+minimum[1]), NOTES=args.notes, CODE=str(code), DIGEST=digest,
                       COMMIT=args.source_commit).items():
    document = document.replace(key, e(value))
(out/'index.html').write_text(document)
print(json.dumps(metadata, ensure_ascii=False, indent=2))
