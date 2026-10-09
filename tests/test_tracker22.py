# 페이지 열 때 자동 동기화(3초 간격) · 예전 15분 자동 동기화 제거 · 🔄 아이콘 버튼(캐릭터 카드 제목 옆) (2026-10-10)
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    path=os.path.join(OUT,name); loc.screenshot(path=path)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
PORT=8795
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def ch(id,name,lv,job,ocid,main=False):
    return {'id':id,'name':name,'level':lv,'job':job,'world':'스카니아','ocid':ocid,'accId':'a1','isMain':main,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main',True),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM}],'autoSync':True,'autoEnable':True,'lastSync':0}}
calls=[]; popups=[]
def counted(route):
    if '/maplestory/v1/' in route.request.url: calls.append(route.request.url)  # 캐릭터 이미지(static)는 API 호출량 아님
    return handle(route)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',counted)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort()); ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('popup',lambda pp: popups.append(pp.url))
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET)
    calls.clear(); pg.reload(); pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(300)
    n1=len(calls); check('page load → Nexon sync runs once (lastSync set)', n1>0 and pg.evaluate("S.settings.lastSync")>0, n1)
    check('old autoSync setting removed on load (migration)', pg.evaluate("'autoSync' in S.settings")==False and 'autoSync' not in pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    check('no periodic auto-sync code left', pg.evaluate("typeof autoDue==='undefined' && !('AUTO_SYNC_MIN' in CONFIG)"))
    calls.clear(); pg.reload(); pg.wait_for_timeout(800)
    check('reload within 3s → skipped (no API calls)', len(calls)==0, calls)
    pg.wait_for_timeout(3200); calls.clear(); pg.reload(); pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(300)
    check('reload after 3s → sync again', len(calls)>0, len(calls))
    # 동기화 도중 새로고침 → 시작 시각 기록으로 건너뜀
    pg.evaluate("S.settings.lastSync=0; save(); localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))"); calls.clear(); pg.reload(); pg.wait_for_timeout(800)
    check('reload right after a load-sync start (sync interrupted) → skipped', len(calls)==0, len(calls))
    check('never opened a Google login popup', not popups and not pg.evaluate("gd.ia"), popups)
    # 🔄 버튼: 캐릭터 카드 제목 옆, 아이콘만
    pg.wait_for_timeout(3200); pg.reload(); pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(200)
    info=pg.evaluate("""(()=>{const b=document.querySelector('#syncBtn'),h=b.closest('h2');const r=b.getBoundingClientRect(),t=h.firstChild;
      const rg=document.createRange(); rg.selectNodeContents(t); const tr=rg.getBoundingClientRect();
      return {inCard:!!b.closest('aside .card'),title:t.textContent.trim(),gap:r.left-tr.right,text:b.textContent.trim(),aria:b.getAttribute('aria-label'),tt:b.title,w:r.width,h:r.height,round:getComputedStyle(b).borderRadius,inHeader:!!b.closest('header')}})()""")
    check('sync button: in character card header right after 캐릭터, icon-only, round, aria-label+title', info['inCard'] and info['title']=='캐릭터' and 0<=info['gap']<=14 and info['text']=='' and '지금 동기화' in info['aria'] and '페이지를 열거나 새로고침할 때 자동' in info['tt'] and not info['inHeader'] and abs(info['w']-info['h'])<1, info)
    calls.clear(); pg.click('#syncBtn'); pg.wait_for_timeout(50)
    check('click → spins + disabled while syncing', pg.evaluate("syncing && document.querySelector('#syncBtn').classList.contains('busy') && getComputedStyle(document.querySelector('#syncBtn .rot')).animationName==='sbspin'"))
    pg.wait_for_function("!syncing",timeout=30000); check('manual click syncs', len(calls)>0)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(300)
    check('+ 추가 modal: 15-min auto-sync checkbox gone', pg.locator('#sAuto').count()==0 and pg.locator('#sAutoEnable').count()==0)
    pg.keyboard.press('Escape'); pg.evaluate("document.querySelector('#toast').classList.remove('show')"); pg.wait_for_timeout(200)
    shot(pg.locator('aside .card').first,'sidebar_header.png')
    # ☁ 다시 연결은 헤더에 그대로
    pg.evaluate("gdMeta.on=true; gd.state='reconnect'; gd.msg=GD_NEED_LOGIN; gdRender()")
    check('[☁ 다시 연결] still in header', '다시 연결' in pg.inner_text('header #gBtn'), pg.inner_text('header #gBtn'))
    # 모바일
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.wait_for_timeout(600)
    mi=m.evaluate("""(()=>{const b=document.querySelector('#syncBtn'),r=b.getBoundingClientRect(),a=document.querySelector('#addCharBtn').getBoundingClientRect();return {vis:r.width>0,w:r.width,right:r.right,iw:innerWidth,sameRow:Math.abs((r.top+r.bottom)/2-(a.top+a.bottom)/2)<6,over:document.documentElement.scrollWidth>innerWidth}})()""")
    check('mobile: sync icon visible, ≥32px, same row as + 추가, no overflow', mi['vis'] and mi['w']>=32 and mi['sameRow'] and not mi['over'], mi)
    shot(m.locator('aside .card').first,'sidebar_header_mobile.png')
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
