# b108: 🔄 옆 '새로고침 중입니다..' → 초록 '새로고침 완료! HH:mm'(KST) · 페이지 열 때 동기화도 · 일부 실패 주황 · 전체 실패 빨강 · 줄바꿈/잘림 없음(1280·1920·375·320)
# MBT_ROOT=다른 빌드(변경 전 화면), MBT_SHOTDIR=스크린샷 폴더, MBT_TAG=파일 이름 접두(before/after), MBT_NOCHECK=1 이면 검사 생략(변경 전 촬영용)
import os, sys, time, subprocess, re, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mock_nexon import handle, KM
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8894'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(pg,name):
    if SHOT: pg.locator('aside .card').first.screenshot(path=os.path.join(SHOT,f'b108_{TAG}_{name}.png'))
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
def ch(i,n,o): return {'id':f'c{i}','name':n,'level':280,'job':'히어로','world':'스카니아','ocid':o,'accId':'a1','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch(0,'단풍용사','ocid-main'),ch(1,'불독메이지','ocid-alt1')],
    'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM,'main':True}],'lastSync':0}}
mode={'fail':False}
def route(r):
    if mode['fail']: return r.fulfill(status=400,content_type='application/json',body='{"error":{"name":"OPENAPI00005","message":"bad"}}')
    return handle(r)
LBL="(()=>{const e=document.querySelector('#syncDone');if(!e)return null;const r=e.getBoundingClientRect(),c=e.closest('.card').getBoundingClientRect(),h=e.closest('h2');return {t:e.innerText,c:getComputedStyle(e).color,next:document.querySelector('#syncBtn').nextElementSibling===e,oneLine:r.height<22,inCard:r.right<=c.right+0.5&&r.left>=c.left,clip:e.scrollWidth>e.clientWidth+1,hH:h.getBoundingClientRect().height}})()"
def kst_hm(): return (dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=9)).strftime('%H:%M')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for (w,h) in [(1280,800),(1920,1080),(375,812),(320,640)]:
        pg=b.new_page(viewport={'width':w,'height':h}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/open.api.nexon.com/**',route); pg.route('**/feed.json*',lambda r:r.fulfill(status=404,body='')); pg.route('https://accounts.google.com/**',lambda r:r.abort())
        mode['fail']=False
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST)
        pg.reload(); pg.wait_for_function("typeof syncing!=='undefined'&&!syncing",timeout=30000); pg.wait_for_timeout(300)
        f=pg.evaluate(LBL)
        if w==1280: check('페이지 열 때 동기화 → 초록 새로고침 완료! HH:mm', bool(f) and f['t'] in ('새로고침 완료! '+kst_hm(),) or (f and re.fullmatch(r'새로고침 완료! \d\d:\d\d',f['t'])), f)
        # 동기화 중: 넥슨 호출을 느리게 (키별 1.5초에 1건)
        pg.evaluate("CONFIG.API_RATE_N=1;CONFIG.API_RATE_WIN_MS=1500;CONFIG.API_DELAY_MS=1500")
        pg.evaluate("void syncAll()"); pg.wait_for_timeout(250); f=pg.evaluate(LBL)
        check(f'{w}: 동기화 중 "새로고침 중입니다.." 한 줄·카드 안·안 잘림', bool(f) and f['t']=='새로고침 중입니다..' and f['next'] and f['oneLine'] and f['inCard'] and not f['clip'], f)
        shot(pg,f'{w}_during')
        pg.wait_for_function("!syncing",timeout=60000); pg.wait_for_timeout(200); f=pg.evaluate(LBL)
        check(f'{w}: 완료 "새로고침 완료! HH:mm" 초록·한 줄·카드 안·안 잘림·제목 한 줄', bool(f) and re.fullmatch(r'새로고침 완료! \d\d:\d\d',f['t']) and f['c']=='rgb(74, 222, 128)' and f['oneLine'] and f['inCard'] and not f['clip'] and f['hH']<40, f)
        shot(pg,f'{w}_done')
        if w==1280:
            pg.evaluate("CONFIG.API_RATE_N=5;CONFIG.API_RATE_WIN_MS=1100")
            mode['fail']=True; pg.evaluate("toastHide()"); pg.evaluate("syncAll()"); pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(200); f=pg.evaluate(LBL)
            check('계정 키 오류 → 주황 "일부 실패 HH:mm" + 알림(toast) 그대로', bool(f) and re.fullmatch(r'일부 실패 \d\d:\d\d',f['t']) and f['c']=='rgb(245, 165, 36)' and pg.evaluate("document.querySelector('#toast').classList.contains('show')"), f)
            shot(pg,'1280_partfail')
            pg.route('**/open.api.nexon.com/**',lambda r:r.abort()); pg.evaluate("for(const k in listCache) delete listCache[k]; void syncAll()"); pg.wait_for_function("!syncing",timeout=30000); f=pg.evaluate(LBL)
            check('네트워크 오류 → 빨강 "새로고침 실패 HH:mm"', bool(f) and re.fullmatch(r'새로고침 실패 \d\d:\d\d',f['t']) and f['c']=='rgb(248, 113, 113)', f)
        pg.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs); sys.exit(1 if (fails or errs) and not NOCHK else 0)
