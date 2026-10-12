# b102: 부계정 삭제 = 칸 통째로 지움(캐릭터만 숨김) / 관리자 창 즉시(캐시·낙관적·실패 시 되돌림)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _legacy
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8899; API='http://127.0.0.1:9996'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(i,acc): return {'id':i,'name':'캐'+i,'level':280,'job':'히어로','world':'스카니아','ocid':'','accId':acc,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','a1'),ch('c2','a2'),ch('c3','a3')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':_legacy.LEGACY_KEY,'main':True},{'id':'a2','label':'부계정1','key':_legacy.LEGACY_KEY+'x','ah':'a'*64},{'id':'a3','label':'부계정2','key':_legacy.LEGACY_KEY+'y'}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1300,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route(API+'/**',lambda r:r.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.wait_for_timeout(300)
    # 2) 캐릭터가 있으면 헤더 버튼 보임 + 부계정 삭제
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("confirm=()=>true; const el=document.createElement('button'); el.dataset.accdel='a2'; document.body.appendChild(el); el.click(); el.remove()"); pg.wait_for_timeout(200)
    s=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
    check('alt delete: account slot removed entirely (no key/ah/label left)', [x['id'] for x in s['settings']['accounts']]==['a1','a3'] and 'a'*64 not in json.dumps(s), s['settings']['accounts'])
    check('alt delete: id kept only in goneAccs, character record kept but hidden', s['settings'].get('goneAccs')==['a2'] and any(c['id']=='c2' for c in s['characters']) and pg.evaluate("vchars().map(c=>c.id)")==['c1','c3'])
    # 4) 관리자 창: 캐시로 즉시, 낙관적 반영, 실패 시 되돌림
    USERS=[{'id':'u0','status':'ok','admin':True,'name':'관리','alts':[]},{'id':'p1','status':'pending','name':'대기1','alts':[]},{'id':'p2','status':'pending','name':'대기2','alts':[]},{'id':'u3','status':'ok','name':'유저3','alts':[]}]
    pg.evaluate("""u=>{ window.__u=u; window.__fail=false; window.__slow=800; confirm=()=>true;
      svFetch=async(path,o)=>{ await new Promise(r=>setTimeout(r,window.__slow)); if(path.startsWith('/api/admin/users')) return {users:window.__u,prices:{}}; if(path==='/api/admin/decide'){ if(window.__fail) throw new Error('서버 오류'); return {ok:true}; } return {}; };
      sessionStorage.setItem('mapleBossTracker.admUsers',JSON.stringify(u)); admUsers=null; }""",USERS)
    t0=time.time(); pg.evaluate("void openAdmin()"); n=pg.evaluate("document.querySelectorAll('#admBody .admrow').length"); dt=(time.time()-t0)*1000
    check('open: list drawn instantly from cache (before 800ms server reply)', n==4, (n,round(dt)))
    pg.wait_for_timeout(900)
    t0=time.time(); pg.evaluate("void admDecide('p1','reject')"); n=pg.evaluate("document.querySelectorAll('#admBody [data-admuser=p1]').length")
    check('reject: row gone immediately (optimistic)', n==0, n)
    pg.wait_for_timeout(900); check('reject: stays gone after server ok', pg.locator('#admBody [data-admuser=p1]').count()==0)
    pg.evaluate("window.__fail=true; void admDecide('p2','approve')"); check('approve: moved to 사용 중 immediately', pg.evaluate("admUsers.find(x=>x.id==='p2').status")=='ok')
    pg.wait_for_timeout(1000)
    check('failure: rolled back + error toast', pg.evaluate("admUsers.find(x=>x.id==='p2').status")=='pending' and '되돌렸' in pg.inner_text('#toast'), pg.inner_text('#toast'))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
