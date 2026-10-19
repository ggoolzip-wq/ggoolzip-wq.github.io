import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8921=_tutil.free_port()
# b137: 실제 넥슨 응답 — 목 리셋 후 미접속 캐릭터는 오늘 응답에 주간 보스 행이 없음 → 지난 날짜 등록 목록으로 라인업
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8921)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b137_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
FX=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'fixture_sched_b137.json')))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1800},locale='ko-KR',color_scheme='dark')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    hits=[]; W={}
    def nx(r):
        u=r.request.url
        if 'character/list' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'account_list':[{'account_id':'x','character_list':[{'ocid':'o1','character_name':'미접속캐','world_name':'스카니아','character_class':'히어로','character_level':285}]}]}))
        if 'scheduler/character-state' in u:
            hits.append(u)
            if '&date=' not in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps(FX['today_offline']).replace('__W__',W['w']))
            dt=u.split('&date=')[1][:10]
            if dt==W['y']: return r.fulfill(status=400,content_type='application/json',body='{"error":{"name":"OPENAPI00009","message":"Please wait until the data is ready"}}')
            x=json.loads(json.dumps(FX['prev_full']).replace('__P__',dt))
            for row in x['boss_contents']:
                if row['content_name']=='듄켈' and row['difficulty']=='hard': row['complete_flag']='true'  # 지난 주 클리어 → 이번 주 클리어로 치면 안 됨
            return r.fulfill(status=200,content_type='application/json',body=json.dumps(x))
        return r.abort()
    ctx.route('https://open.api.nexon.com/**',nx)
    # zosu-testfix: 금요일 KST 로 고정 — 어제(목, 리셋일) 400 → 그제(수) = 지난 주 응답. 예전엔 월~수에 돌리면 그제가 이번 주라 듄켈 클리어가 이번 주로 맞게 잡혀 실패(요일 의존)
    import datetime as _dt; ctx.clock.install(time=_dt.datetime(2026,10,16,12,0,tzinfo=_dt.timezone(_dt.timedelta(hours=9))))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    W['w']=pg.evaluate("S.period.week"); W['y']=pg.evaluate("dayId(Date.now()-864e5)")
    C={'id':'c1','name':'미접속캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'o1','b134':1,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'period':pg.evaluate("({...S.period})"),
        'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    pg.reload(); pg.wait_for_timeout(700)
    pg.evaluate("syncAll({full:true})"); pg.wait_for_timeout(2500)
    on=pg.evaluate("Object.entries(S.characters[0].bosses).filter(([k,v])=>v.enabled).map(([k,v])=>k+':'+v.diff).sort()")
    exp=sorted(['blackmage:hard','lotus:extreme','dusk:chaos','jinhilla:hard','dunkel:hard','seren:extreme','kalos:chaos','kaling:hard','limbo:hard','baldrix:hard','adversary:hard','star:hard','bellona:hard'])
    check('오늘 응답에 주간 행 없음(실제 응답 모양) → 지난 날짜 스케줄러 등록 목록으로 라인업 채움', on==exp, on)
    check('어제 데이터 준비 중(OPENAPI00009)이면 그 전날로', sum('&date=' in h for h in hits)==2, [h.split('?')[1].replace('ocid=o1','') for h in hits])
    check('지난 날짜 응답의 클리어는 이번 주 클리어로 안 침 (듄켈)', pg.evaluate("!S.characters[0].weekly.dunkel"))
    check('검마 이번 달 클리어는 오늘 응답대로', pg.evaluate("!!S.characters[0].monthly.blackmage"))
    check('동기화 상태 날짜 = 오늘 응답', pg.evaluate("S.characters[0].sync.date")==W['w'], pg.evaluate("S.characters[0].sync"))
    pg.evaluate("render()"); pg.wait_for_timeout(300)
    names=pg.evaluate("[...document.querySelectorAll('.boss-list .bn')].map(e=>e.innerText.split('\\n')[0])")
    check('라인업 화면에 등록 보스 표시', len(names)>=12, names)
    el=pg.locator('.boss-list').first
    shot(el if el.count() else pg.locator('#view'),'sync_lineup_mock')
    # 주간 행이 있는 (접속한) 캐릭터는 추가 호출 없음
    hits.clear(); FX['today_offline']=json.loads(json.dumps(FX['prev_full']).replace('__P__','__W__'))
    pg.evaluate("()=>{listCache={};}") if False else None
    pg.evaluate("syncAll({full:true})"); pg.wait_for_timeout(2000)
    check('주간 행이 있는 응답이면 지난 날짜 조회 안 함', hits and not any('&date=' in h for h in hits), hits)
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
