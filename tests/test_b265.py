# test_b265: 마빡도로시 — 제목에 '포탈' 이 있는 글은 수집 안 함(update_feed.src_mabbak) + 기존 feed.json 에서 제거 + 화면(feedItems)에서도 숨김. 다른 탭은 그대로.
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
import os, sys, json, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
FIX=json.load(open(os.path.join(ROOT,'tests','fixture_b265_feed.json'),encoding='utf-8'))
if not NOCHK:
    sys.path.insert(0, os.path.join(ROOT,'scripts')); import update_feed as F
    check('mabbak_skip', [F.mabbak_skip(t) for t in ['요약 포탈','요약 정리','',None]]==[True,False,False,False])
    F.INVEN_BOARDS=['5974']; F.time.sleep=lambda s:None
    F.http_get=lambda url,**k:(200,'inven '+'x'*6000)
    F.inven_rows=lambda s:[('u1','',11),('u2','',12),('u3','',13)]
    T={'u1':'오늘 요약 포탈','u2':'보스 정리','u3':'테섭포탈모음'}
    F.inven_post=lambda u:(T[u],'2026-10-26T00:00:00+09:00')
    wm={'inven:5974':10}; new=F.src_mabbak({},wm,False,0)
    check('수집기: 포탈 글 건너뜀', [x['title'] for x in new]==['보스 정리'], new)
    check('수집기: 건너뛴 글도 워터마크 넘김(다시 안 받음)', wm['inven:5974']==13, wm)
    live=json.load(open(os.path.join(ROOT,'feed.json'),encoding='utf-8'))['items']
    check('feed.json 마빡도로시에 포탈 없음', not [x for x in live.get('mabbak',[]) if '포탈' in x['title']])


    s=open(os.path.join(ROOT,'scripts','update_feed.py'),encoding='utf-8').read()
    check('main() 에서 기존 포탈 글 제거 코드', 'items["mabbak"] = [x for x in items["mabbak"] if not mabbak_skip' in s)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(FIX)))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_selector('#feedCard [data-ftab="mabbak"]',timeout=15000)
    pg.click('#feedCard [data-ftab="mabbak"]'); pg.wait_for_timeout(500)
    if SD:
        os.makedirs(SD,exist_ok=True); pg.locator('#feedCard').scroll_into_view_if_needed(); pg.mouse.move(5,5); pg.wait_for_timeout(200)
        pg.locator('#feedCard').screenshot(path=os.path.join(SD,f'{PFX}_mabbak_tab.png'))
    if not NOCHK:
        r=pg.evaluate("()=>[feedItems('mabbak').map(x=>x.title),feedItems('test').length,feedItems('saryo').length,document.querySelector('#feedCard').innerText]")
        n0=len(FIX['items']['mabbak']); nP=sum('포탈' in x['title'] for x in FIX['items']['mabbak'])
        check('화면: 마빡도로시 포탈 글 숨김', len(r[0])==n0-nP and not any('포탈' in t for t in r[0]) and '포탈' not in r[3], r[0])
        check('다른 탭 그대로', r[1]==len(FIX['items']['test']) and r[2]==len(FIX['items']['saryo']), r[1:3])
        pg.evaluate("feedSrvApply({items:{mabbak:[{id:'inven:x:1',title:'서버 포탈 글',date:'2026-10-26'}]}})")
        check('서버(feed.srv) 글도 숨김', not any('포탈' in x for x in pg.evaluate("feedItems('mabbak').map(x=>x.title)")))
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
