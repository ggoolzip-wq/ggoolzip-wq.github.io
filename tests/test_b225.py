import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8986=_tutil.free_port()
_P8987=_tutil.free_port()
_P8988=_tutil.free_port()
# b229(b225 고침): 관리자 창 '최근 갱신' = 마지막으로 캐릭터 동기화가 끝난 시각 (users.sync_click) — 🔄·키 등록·들어올 때·F5 자동 동기화 모두 적음, 10초 안 중복은 그대로
import os, sys, json, subprocess, time, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
SHOT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out')
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
T=open(os.path.join(ROOT,'tests','test_b216.py'),encoding='utf-8').read(); exec(T[T.index("KA,KF="):T.index("if not cf_dev")])
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
PORT, WP, NP = _P8986, _P8987, _P8988
API=f'http://127.0.0.1:{WP}'; URL=f'http://localhost:{PORT}/index.html'
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def idle(pg): pg.wait_for_timeout(300); pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(400)
sc=lambda: dev.sql("SELECT sync_click FROM users")[0]['sync_click']
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    c1,p1=mkctx(b); CL=[]; p1.on('request',lambda r: CL.append(r.url) if '/api/sync-click' in r.url else None)
    fresh(p1); login(p1,KA); wait_on(p1)
    p1.evaluate("""()=>{ const A=accounts()[0]; const mk=(id,nm,acc,o,main)=>({id,name:nm,level:280,job:'히어로',world:'스카니아',ocid:o,accId:acc,isMain:main,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
      S.characters.push(mk('c1','본캐A',A.id,'o-acc-A',true)); save(); render(); svSaveNow(); }"""); wait_on(p1)
    n0=len(CL); v0=sc()
    p1.wait_for_timeout(3200); t0=int(time.time()*1000); p1.reload(); idle(p1)   # 새로고침 자동 동기화
    v1=sc(); check('F5 auto sync → /api/sync-click, sync_click = now', len(CL)>n0 and v1 and abs(v1-t0)<8000, (len(CL),v1,t0))
    p1.wait_for_timeout(3200); n1=len(CL); p1.goto(URL); idle(p1)  # 새로 들어올 때 자동 동기화 (10초 안 → 요청은 가도 값 그대로)
    check('fresh entry auto sync → request, within 10s no rewrite', len(CL)>n1 and sc()==v1, (len(CL),sc(),v1))
    p1.wait_for_timeout(10500); t2=int(time.time()*1000); p1.evaluate("keySync()"); idle(p1)
    v2=sc(); check('key-registration sync after 10s → sync_click updated', v2 and v2>v1 and abs(v2-t2)<8000, (v2,v1))
    p1.wait_for_timeout(10500); t3=int(time.time()*1000); n3=len(CL); p1.click('#syncBtn'); idle(p1)
    v3=sc(); check('🔄 button sync → updated', len(CL)>n3 and v3>v2 and abs(v3-t3)<8000, (v3,v2))
    p1.evaluate("S.settings.accounts.length"); n4=len(CL); p1.evaluate("syncing=true"); p1.click('#syncBtn'); p1.wait_for_timeout(400); p1.evaluate("syncing=false")
    check('click while already syncing → no request (no finished sync)', len(CL)==n4, len(CL)-n4)
    v1=v3
    # 관리자로 지정 → 관리자 창
    uid=dev.sql("SELECT id FROM users")[0]['id']; dev.sql(f"INSERT OR REPLACE INTO meta (k,v) VALUES ('admin_user','{uid}')")
    p1.evaluate("openAdmin()"); p1.wait_for_function("admUsers&&admUsers.length&&!document.querySelector('#admBody .muted')?.textContent.includes('불러오는 중')",timeout=10000); p1.wait_for_timeout(300)
    row=p1.inner_text(f"#admBody [data-admuser='{uid}']"); want=p1.evaluate(f"hm({v1})")
    check('admin row: 최근 갱신 = last sync time (KST M/D HH:MM)', f'최근 갱신 : {want}' in row and '최근 로그인' not in row and '마지막 로그인' not in row, (row,want))
    check('API sends syncAt', p1.evaluate("admUsers[0].syncAt")==v1)
    w=p1.evaluate(f"(()=>{{const e=document.querySelector(\"#admBody [data-admuser='{uid}'] .admwho .tiny\"); return [e.scrollWidth<=e.clientWidth+1, e.getClientRects().length, Math.round(e.getBoundingClientRect().height)]}})()")
    check('info line one line, not clipped', w[0] and w[2]<24, w)
    os.makedirs('/workspace/b229',exist_ok=True); p1.locator('#adminModal .modal').first.screenshot(path='/workspace/b229/admin_recent_sync.png')
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
