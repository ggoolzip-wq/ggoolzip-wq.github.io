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
if os.path.exists(os.path.join(SRC, 'worldicons.json')):  # 공식 월드 아이콘 (tools/build_worlds.py)
    s = s.replace('/*__WORLD_ICONS__*/{}', json.dumps(js('worldicons.json'), separators=(',', ':'), ensure_ascii=False))
css = rd('style_v1.css').replace('</style>', rd('extra.css') + '</style>')
LOGO = js("logo.json")  # b109: 강렬한 힘의 결정 (주간) item 4001928 (assets/ringicons/4001928.png) — 예전 주황버섯
head = ('<!DOCTYPE html>\n<html lang="ko" data-theme="dark">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>메보기 - 메이플 보스 수익·결정석 기록 사이트</title>\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{LOGO["s32"]}">\n'
        f'<link rel="icon" type="image/png" sizes="16x16" href="{LOGO["s16"]}">\n'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
        # b198: 검색 등록(구글 서치 콘솔·네이버 서치어드바이저) 준비 — 대표 주소 = bossmaple.pages.dev (github.io 도 canonical 은 여기로). 소유 확인 태그는 아직 없음
        '<meta name="description" content="메이플스토리 보스 수익 계산과 주간 보스 기록을 한 번에. 캐릭터별 주간 보스·검은 마법사 결정석 수익, 최신 결정석 가격표(패치 노트 자동 반영), 반지 상자·득템 기록과 주간 메소 그래프를 무료로 제공합니다.">\n'
        '<meta name="google-site-verification" content="1vcb6ZmBor2M4xfKsBwcPVDYSjOmd3zo4ZzM9A7lA4E" />\n<meta name="naver-site-verification" content="a7d0315262c0c08150e38a3a696a4d0f54fae152" />\n'  # b199: 서치 콘솔·서치어드바이저 소유 확인
        '<link rel="canonical" href="https://bossmaple.pages.dev/">\n'
        '<meta property="og:type" content="website">\n<meta property="og:site_name" content="메보기">\n<meta property="og:locale" content="ko_KR">\n'
        '<meta property="og:title" content="메보기 - 메이플 보스 수익·결정석 기록 사이트">\n<meta property="og:description" content="메이플스토리 보스 수익 계산과 주간 보스 기록을 한 번에. 캐릭터별 주간 보스·검은 마법사 결정석 수익, 최신 결정석 가격표(패치 노트 자동 반영), 반지 상자·득템 기록과 주간 메소 그래프를 무료로 제공합니다.">\n'
        '<meta property="og:url" content="https://bossmaple.pages.dev/">\n<meta property="og:image" content="https://bossmaple.pages.dev/og.png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="메보기 - 메이플 보스 수익·결정석 기록 사이트">\n<meta name="twitter:description" content="메이플스토리 보스 수익 계산과 주간 보스 기록을 한 번에. 캐릭터별 주간 보스·검은 마법사 결정석 수익, 최신 결정석 가격표(패치 노트 자동 반영), 반지 상자·득템 기록과 주간 메소 그래프를 무료로 제공합니다.">\n<meta name="twitter:image" content="https://bossmaple.pages.dev/og.png">\n')
body = rd('body.html').replace('__LOGO64__', LOGO['s64'])
open(OUT, 'w', encoding='utf-8').write(head + css + '\n' + body + '\n<script>\n' + s + '</script>\n</body>\n</html>\n')
print('built', OUT, os.path.getsize(OUT), 'bytes')
