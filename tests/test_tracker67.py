import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8887=_tutil.free_port()
# b91: 관리자 창 '사용 중' — 부계정은 본계정 아래 접힘(▽/△), 부계정은 강퇴 없음, '등록 날짜 : YYYY-MM-DD'(KST), 10명씩 쪽은 본계정 기준 (모의 목록)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8887
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
T=lambda s: int(time.mktime(time.strptime(s,'%Y-%m-%d %H:%M'))*1000)  # 박스 시간대 = KST
def U(i,name,alts=(),admin=False,reg='2026-10-01 10:00',join='2026-09-20 10:00'):
    return {'id':f'u{i}','status':'ok','admin':admin,'name':name,'world':'스카니아','level':280,'chars':3,'size':2048,'lastLogin':T('2026-10-12 09:00'),'syncAt':(0 if i==2 else T('2026-10-13 21:07')),'regAt':(T(reg) if reg else 0),'joinAt':(T(join) if join else 0),
            'alts':[{'label':l,'name':n,'world':'스카니아','level':270,'chars':1,'regAt':(T(r) if r else 0)} for l,n,r in alts]}
USERS=[U(0,'관리자캐',admin=True,reg='2026-10-10 08:00'),U(1,'본캐하나',[('부계정1','부캐가','2026-10-11 23:30'),('부계정2','부캐나',None)],reg='2026-10-10 23:59')]+[U(i,f'유저{i}',reg=(None if i==3 else '2026-10-01 10:00'),join=(None if i==4 else '2026-09-20 10:00')) for i in range(2,13)]+[{'id':'p1','status':'pending','name':'대기캐','world':'루나','level':260,'requestedAt':T('2026-10-12 08:00')}]
SHOT=os.environ.get('SHOT'); STRICT=not SHOT or 'after' in SHOT
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':900,'height':1000},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.wait_for_timeout(600)
    pg.evaluate("u=>{admUsers=u; admErr=''; admPage=1; document.querySelector('#adminModal').classList.add('show'); renderAdmin();}",USERS); pg.wait_for_timeout(200)
    if SHOT and not STRICT: pg.locator('#adminModal .modal').first.screenshot(path=SHOT)
    if STRICT:
      sec=lambda: pg.evaluate("[...document.querySelectorAll('#admBody .admsec')][1]")
      r1="#admBody [data-admuser='u1']"
      check('page 1 = 10 main accounts (alts not counted)', pg.evaluate("document.querySelectorAll('#admBody .admsec:nth-of-type(2) .admrow:not(.admalt)').length")==10 and pg.locator('[data-admpage]').count()==2)
      check('alts collapsed by default', pg.evaluate(f"document.querySelectorAll(\"{r1} ~ .admalts .admalt\").length")==2 and not pg.is_visible('.admalt'))
      tg=pg.locator(f"{r1} [data-admalt]"); check('toggle ▽ next to main with alts', tg.count()==1 and '▽' in tg.inner_text(), tg.count())
      check('no toggle for user without alts', pg.locator("[data-admuser='u2'] [data-admalt]").count()==0)
      check('b237: main row = 가입·등록 both (KST)', '가입 : 2026-09-20 · 등록 : 2026-10-10' in pg.inner_text(r1), pg.inner_text(r1))
      check('b237: no key reg → 등록 : - (no fallback to 가입)', '가입 : 2026-09-20 · 등록 : -' in pg.inner_text("[data-admuser='u3']"), pg.inner_text("[data-admuser='u3']"))
      check('b237: no joinAt → 가입 : -', '가입 : - · 등록 : 2026-10-01' in pg.inner_text("[data-admuser='u4']"), pg.inner_text("[data-admuser='u4']"))
      check('b229: 최근 갱신 = syncAt (KST), 마지막 로그인 없음', '최근 갱신 10/13 21:07' in pg.inner_text(r1) and '마지막 로그인' not in pg.inner_text('#admBody'), pg.inner_text(r1))
      check('b229: no sync recorded → 최근 갱신 -', '최근 갱신 -' in pg.inner_text("[data-admuser='u2']"), pg.inner_text("[data-admuser='u2']"))
      if os.environ.get('B225_SHOT'): pg.locator('#adminModal .modal').first.screenshot(path=os.environ['B225_SHOT'])
      check('main kick button present', pg.locator(f"{r1} [data-adm=kick]").count()==1)
      tg.click(); pg.wait_for_timeout(150)
      alts=pg.locator('.admalt:visible'); t=' | '.join(alts.all_inner_texts())
      check('expanded: △, 2 alts visible', '△' in tg.inner_text() and alts.count()==2, t)
      check('alt reg dates (KST, 23:30 stays 10-11) and - for unknown', '등록 날짜 : 2026-10-11' in t and '등록 날짜 : -' in t, t)
      check('alts have no 강퇴', pg.locator('.admalt [data-adm]').count()==0)
      check('alt shows label + rep char', '부계정1' in t and '부캐가' in t, t)
      if SHOT: pg.locator('#adminModal .modal').first.screenshot(path=SHOT)
      tg.click(); pg.wait_for_timeout(150); check('collapse again ▽', '▽' in tg.inner_text() and not pg.is_visible('.admalt'))
      pg.click("[data-admpage='2']"); pg.wait_for_timeout(150)
      check('page 2 has remaining 3 mains', pg.evaluate("document.querySelectorAll('#admBody .admsec:nth-of-type(2) .admrow:not(.admalt)').length")==3)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
