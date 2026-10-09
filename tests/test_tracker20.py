# 구글 로그인 창이 자동으로 뜨지 않는지 (2026-10-10 'PC방에서 자꾸 로그인하라고 함' 회귀 테스트)
# 규칙: 로그인 팝업(requestAccessToken)은 사용자가 직접 누른 동작에서만, 그 동작당 최대 1번.
#       페이지 열기·탭 복귀(gdPull)·1분 타이머·자동 저장은 남은 토큰(1시간, sessionStorage)만 사용 → 없으면 [☁ 다시 연결] 표시만.
import os, sys, json, time, subprocess, urllib.request, importlib.util
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('t10h', os.path.join(here,'test_tracker10.py'))
src=open(spec.origin,encoding='utf-8').read()
head=src.split('with sync_playwright() as p:')[0].replace("srv=subprocess.Popen","srv=None and subprocess.Popen").replace("for _ in range(50):","for _ in range(0):")
ns={'__file__':spec.origin}; exec(compile(head,spec.origin,'exec'),ns)
Drive, INIT, state = ns['Drive'], ns['INIT'], ns['state']
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(here); PORT=8798; BASE=f'http://localhost:{PORT}/index.html'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
fails=[]; errs=[]
def check(name,cond,info=''):
    print(('PASS ' if cond else 'FAIL ')+name+(' — '+str(info) if info!='' else '')); (None if cond else fails.append(name))
T0=1760000000000
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def page(d,tok=None):
        ctx=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); ctx.add_init_script(INIT)
        ctx.route('https://www.googleapis.com/**',d.handle); ctx.route('https://accounts.google.com/**',lambda r,q: r.fulfill(status=200,body='/* blocked */'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda x:x.accept())
        pg.goto(BASE); pg.wait_for_timeout(150)
        pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(state(['A'],T0)))
        pg.evaluate("s=>localStorage.setItem('mapleBossTracker.gdrive',s)",json.dumps({'on':True,'base':T0,'rU':T0,'fileId':'F1'}))
        if tok: pg.evaluate("t=>sessionStorage.setItem('mapleBossTracker.gtoken',JSON.stringify({t:t,e:Date.now()+3500e3}))",tok)
        pg.reload(); pg.wait_for_timeout(700); return ctx,pg
    req=lambda pg: pg.evaluate('__g.req')
    def hide_show(pg):
        pg.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));}"); pg.wait_for_timeout(200)
        pg.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'));}"); pg.wait_for_timeout(600)

    # 1) 새 탭/브라우저(토큰 없음)로 열기 → 팝업 0, [☁ 다시 연결]
    d=Drive(); d.seed(state(['A'],T0),T0); ctx,pg=page(d)
    check('open without token → no login popup', req(pg)==0, req(pg))
    check('open without token → header shows 다시 연결', pg.evaluate('gd.state')=='reconnect' and '다시 연결' in pg.inner_text('#gBtn'), pg.inner_text('#gBtn'))
    hide_show(pg); pg.evaluate("gdPull(true)"); pg.wait_for_timeout(300)
    check('tab return / gdPull without token → still no popup', req(pg)==0, req(pg))
    pg.evaluate("()=>{S.characters[0].level=281; save();}"); pg.wait_for_timeout(5800)
    check('edit while logged out → no popup, kept locally', req(pg)==0 and pg.evaluate('S.characters[0].level')==281 and d.file['content']['data']['characters'][0]['level']!=281)
    pg.click('#gBtn'); pg.wait_for_timeout(800)
    check('one click on [☁ 다시 연결] → exactly one popup, synced, edit saved to drive', req(pg)==1 and pg.evaluate('gd.state')=='on' and d.file['content']['data']['characters'][0]['level']==281, (req(pg),pg.evaluate('gd.state')))
    pg.reload(); pg.wait_for_timeout(700)
    check('reload within the hour → token reused, no popup', req(pg)==0 and pg.evaluate('gd.state')=='on', (req(pg),pg.evaluate('gd.state')))
    ctx.close()

    # 2) 토큰이 남아 있음 → 열기·복귀·저장 모두 팝업 0
    d=Drive(); d.seed(state(['A'],T0),T0); ctx,pg=page(d,tok='tokS')
    check('open with valid token → connected silently', req(pg)==0 and pg.evaluate('gd.state')=='on', pg.evaluate('gd.state'))
    for i in range(3): hide_show(pg)
    pg.evaluate("()=>{S.characters[0].level=282; save();}"); pg.wait_for_timeout(5800)
    check('tab returns + autosave with valid token → saved, no popup', req(pg)==0 and d.file['content']['data']['characters'][0]['level']==282)

    # 3) 1시간 지나 토큰 만료 → 복귀·1분 확인·자동 저장에서 팝업 0, 헤더 안내
    pg.evaluate("gd.exp=Date.now()-1000"); hide_show(pg); pg.evaluate("gdPull(true)"); pg.wait_for_timeout(300)
    check('expired token: tab return / pull → no popup', req(pg)==0, req(pg))
    pg.evaluate("()=>{S.characters[0].level=283; save();}"); pg.wait_for_timeout(5800)
    check('expired token: autosave → no popup, header 다시 연결', req(pg)==0 and pg.evaluate('gd.state')=='reconnect', (req(pg),pg.evaluate('gd.state'),pg.evaluate('gd.msg')))
    pg.evaluate("()=>{S.characters[0].level=284; save();}"); pg.wait_for_timeout(5800)
    check('further edits while reconnect → still no popup', req(pg)==0)
    pg.click('#gBtn'); pg.wait_for_timeout(800)
    check('click → one popup, latest edit saved', req(pg)==1 and d.file['content']['data']['characters'][0]['level']==284 and pg.evaluate('gd.state')=='on', (req(pg),d.file['content']['data']['characters'][0]['level']))
    ctx.close()

    # 4) 토큰이 서버에서 거부(401) → 자동 저장은 팝업 없이 다시 연결 표시
    d=Drive(); d.seed(state(['A'],T0),T0); ctx,pg=page(d,tok='badtoken')
    check('revoked token on open → no popup, reconnect', req(pg)==0 and pg.evaluate('gd.state')=='reconnect', (req(pg),pg.evaluate('gd.state')))
    ctx.close()

    # 5) 직접 누르는 '지금 저장'은 토큰이 없을 때 한 번 로그인 창 허용
    d=Drive(); d.seed(state(['A'],T0),T0); ctx,pg=page(d,tok='tokS')
    pg.evaluate("gd.exp=Date.now()-1000; S.characters[0].level=290; S.updatedAt=Date.now();")
    pg.evaluate("()=>gdPush({manual:true})"); pg.wait_for_timeout(800)
    check("manual save with expired token → one popup, saved", req(pg)==1 and d.file['content']['data']['characters'][0]['level']==290, req(pg))
    ctx.close()

    # 6) 팝업이 막히거나 닫혀도 자동으로 다시 시도하지 않음
    d=Drive(); d.seed(state(['A'],T0),T0); ctx,pg=page(d)
    pg.evaluate("localStorage.setItem('__gfail','popup_closed')"); pg.click('#gBtn'); pg.wait_for_timeout(500)
    if pg.is_visible('#driveModal'): pg.click('#gdClose2')
    n=req(pg); hide_show(pg); pg.wait_for_timeout(300); pg.evaluate("()=>{S.characters[0].level=291; save();}"); pg.wait_for_timeout(5800)
    check('after closed popup → no automatic retries', n==1 and req(pg)==1, (n,req(pg)))
    ctx.close()
    b.close()
srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
