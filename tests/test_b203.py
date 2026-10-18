# b203: 로그인 전 첫 화면 = 빈 카드 + 소개 카드(기능 3줄) + 실제 결정석/아이템 가격 카드(읽기 전용), 제목·설명
import os, sys, time, subprocess, urllib.request, re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8984'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
H=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read(); head=H[:H.index('</head>')]
T='메보기 - 메이플 보스 수익·결정석 기록 사이트'
check('title·og·twitter 제목', f'<title>{T}</title>' in head and f'og:title" content="{T}"' in head and f'twitter:title" content="{T}"' in head)
check('설명 = 보스 수익 계산·주간 보스 기록', re.search(r'<meta name="description" content="메이플스토리 보스 수익 계산과 주간 보스 기록을 한 번에\.[^"]*무료로 제공합니다\.">',head) is not None)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
J="""(()=>{const v=document.getElementById('view'),cards=[...v.querySelectorAll('.landprices .pricecard')];
 const rows=c=>c.querySelectorAll('.pc-row').length, nowrap=[...v.querySelectorAll('.landprices .pc-row')].every(r=>{const n=r.querySelector('.pc-nm');return !n||n.scrollWidth<=n.clientWidth+1}),
 hh=(a=>[Math.min(...a),Math.max(...a)])([...v.querySelectorAll('.landprices .pricecard:first-child .pc-row:not(.has-up)')].map(r=>r.getBoundingClientRect().height));
 return {empty:!!v.querySelector('.card.empty'),intro:!!v.querySelector('.seoland h2'),feat:v.querySelectorAll('.seofeat li').length,n:cards.length,
  kinds:cards.map(c=>c.dataset.land),cry:cards[0]&&rows(cards[0]),item:cards[1]&&rows(cards[1]),mine:!!v.querySelector('.landprices #pcMine'),kindBtn:v.querySelectorAll('.landprices [data-pckind],.landprices [data-pctab]').length,
  plain:!!v.querySelector('.seoprice'),admin:!!v.querySelector('.landprices .admbtn,.landprices [id^=adm]'),nowrap,hh,over:document.documentElement.scrollWidth>innerWidth,
  txt:v.innerText.includes('결정석 가격')&&v.innerText.includes('아이템 가격')}})()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1400,390):
        ctx=b.new_context(viewport={'width':w,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.setItem('mapleBossTracker.gdrive',JSON.stringify({on:true}))"); pg.reload(); pg.wait_for_timeout(1200)  # b210: 로그인 전 = 예시 화면 → 여기선 '연결했는데 캐릭터 0명'(규칙 10)
        r=pg.evaluate(J)
        check(f'{w}px 빈 카드 + 소개(기능 3줄) + 가격 카드 2장(결정석·아이템)', r['empty'] and r['intro'] and r['feat']==3 and r['n']==2 and r['kinds']==['cry','item'] and r['cry']>=30 and r['item']>=10 and r['txt'], r)
        check(f'{w}px 읽기 전용: 내가 잡는 보스만·종류/패치 후 버튼·관리자 없음, 글자 목록 가격표 없음', not r['mine'] and r['kindBtn']==0 and not r['admin'] and not r['plain'], r)
        check(f'{w}px 줄바꿈·잘림·가로 넘침 없음, 줄 높이 같음', r['nowrap'] and r['hh'][1]-r['hh'][0]<=1.5 and not r['over'], r)
        if w==1400:
            for t in ('total','loot','guild'):
                pg.evaluate(f"()=>{{tab='{t}';syncTabs();render();}}"); pg.wait_for_timeout(200)
                check(f'규칙 10: {t} 탭도 같은 첫 화면', pg.evaluate(J)['n']==2)
            pg.evaluate("()=>{tab='boss';syncTabs();render();}")
            pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify({genesis:{p:12300000000,t:Date.now()}}));repaintPriceCard();}"); pg.wait_for_timeout(200)
            r2=pg.evaluate("[...document.querySelectorAll('.landprices .pricecard')].map(c=>c.dataset.land+'|'+(c.querySelector('.pc-row[data-pit=genesis] b')||{}).innerText)")
            check('시세 다시 그려도 두 카드 종류 그대로, 공용 아이템 시세 표시', r2[0].startswith('cry|') and r2[1].startswith('item|') and '123' in r2[1], r2)
        if SHOT: pg.screenshot(path=os.path.join(SHOT,f'b203_landing_{w}.png'),full_page=True)
        ctx.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
