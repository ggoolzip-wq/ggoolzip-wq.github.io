# b136: 캐릭터 동기화가 등록을 지우던 버그 — 스케줄러 등록 목록 기준, 클리어 여부로 절대 안 끔
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8962'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b184_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
# b184: 🔄 동기화 속도 — 키 1개·캐릭터 N명 모의 넥슨 API, 4건/1.1초 제한 유지 확인
N=int(os.environ.get('MBT_SYNC_N','12')); NOW=int(os.environ.get('MBT_SYNC_NOWEEK','3'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1100},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    T=[]
    def api(r):
        u=r.request.url; T.append((time.time(),u))
        if 'character/list' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'account_list':[{'account_id':'x','character_list':[{'ocid':f'o{i}','character_name':f'캐릭{i}','world_name':'스카니아','character_class':'히어로','character_level':280} for i in range(N)]}]}))
        if 'scheduler/character-state' in u:
            i=int(u.split('ocid=o')[1].split('&')[0]); rows=[{'content_name':'검은 마법사','difficulty':'hard','cycle':'bossMonthly','registration_flag':'true','clear_flag':'false'}] if i<NOW else [{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','clear_flag':'true'}]
            return r.fulfill(status=200,content_type='application/json',body=json.dumps({'date':None,'boss_contents':rows}))
        if 'character/basic' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'character_level':280,'character_exp_rate':'50.0','character_exp':1}))
        if 'item-equipment' in u: return r.fulfill(status=200,content_type='application/json',body='{"item_equipment":[]}')
        return r.fulfill(status=400,content_type='application/json',body='{"error":{"name":"OPENAPI00004","message":"x"}}')
    ctx.route('https://open.api.nexon.com/**',api)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    CH=[{'id':f'c{i}','name':f'캐릭{i}','level':280,'job':'히어로','world':'스카니아','image':'','ocid':f'o{i}','accId':'a1','b134':1,'bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(N)]
    ST={'version':5,'theme':'dark','activeId':'c0','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,'period':pg.evaluate("({...S.period})"),'settings':{'accounts':[{'id':'a1','label':'계정1','key':'test_dummy_key'}]}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("(()=>{const f=window.fetch;window.fetch=function(u,...r){ if(String(u).includes('open.api.nexon.com')) (window.__fx||(window.__fx=[])).push(Date.now()); return f.call(this,u,...r); };})()")
    def run(label):
        T.clear(); pg.evaluate('window.__fx=[]'); t0=time.time(); pg.evaluate("async()=>{await syncAll()}"); dt=time.time()-t0
        st=pg.evaluate("document.querySelector('#syncLbl,.synclbl')?.innerText||''")
        pg.evaluate("async()=>{ if(typeof syncBg!=='undefined'&&syncBg) await syncBg; }"); pg.wait_for_timeout(300)
        ts=[x/1000 for x in pg.evaluate('window.__fx||[]')]; pg.evaluate('window.__fx=[]'); mx=max([sum(1 for y in ts if x<=y<x+1.095) for x in ts] or [0])
        print(f'{label}: 완료까지 {dt:.2f}s · 호출 {len(T)}건 · 1.1초 창 최대 {mx}건 · 표시 {st!r}')
        return dt,len(T),mx
    a=run('1회차(첫 🔄)'); bb=run('2회차(바로 다시 🔄)')
    check('1.1초 창 안 호출 ≤ 4건 (429 보호 유지)', a[2]<=4 and bb[2]<=4, (a,bb))
    if os.environ.get('MBT_SYNC_GOAL')!='0': check('🔄 완료 표시 3초 안', a[0]<3 and bb[0]<3.3, (a,bb))
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
