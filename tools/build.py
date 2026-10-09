#!/usr/bin/env python3
"""index.html 빌드: src(app.js, body.html, style_v1.css, extra.css, icons.json, itemicons.json, logo.json) → 한 파일 index.html

사용법:  python3 tools/build.py            (저장소 루트에서: src/ → index.html)
         python3 build.py [소스폴더] [출력파일]
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    SRC = sys.argv[1]
elif os.path.exists(os.path.join(HERE, 'app.js')):          # 작업 PC(박스) 배치: 소스와 build.py 가 같은 폴더
    SRC = HERE
else:                                                        # 저장소 배치: tools/build.py + src/
    SRC = os.path.join(os.path.dirname(HERE), 'src')
if len(sys.argv) > 2:
    OUT = sys.argv[2]
elif SRC == HERE and os.path.isdir('/workspace/maple-boss-tracker'):
    OUT = '/workspace/maple-boss-tracker/index.html'
else:
    OUT = os.path.join(os.path.dirname(os.path.abspath(SRC)), 'index.html')
rd = lambda n: open(os.path.join(SRC, n), encoding='utf-8').read()
js = lambda n: json.load(open(os.path.join(SRC, n), encoding='utf-8'))
s = rd('app.js')
s = s.replace('/*__BOSS_ICONS__*/{}', json.dumps(js('icons.json'), separators=(',', ':')))
s = s.replace('/*__ITEM_ICONS__*/{}', json.dumps(js('itemicons.json'), separators=(',', ':')))
css = rd('style_v1.css').replace('</style>', rd('extra.css') + '</style>')
LOGO = js('logo.json')  # 주황버섯 (mob 1210102, maplestory.io KMS 389 mob icon)
head = ('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>보스 캐릭터 관리</title>\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{LOGO["s32"]}">\n'
        f'<link rel="icon" type="image/png" sizes="16x16" href="{LOGO["s16"]}">\n'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n')
body = rd('body.html').replace('__LOGO64__', LOGO['s64'])
open(OUT, 'w', encoding='utf-8').write(head + css + '\n' + body + '\n<script>\n' + s + '</script>\n</body>\n</html>\n')
print('built', OUT, os.path.getsize(OUT), 'bytes')
