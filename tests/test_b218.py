# b218: API 키 등록 직후 1번 자동 동기화 — 본계정 키 등록(다시 등록 포함) · 부계정 키 추가(연결된 캐릭터 있을 때) · 중복/3초 안 건너뜀 · 새 사용자(캐릭터 0)는 안 함
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
PORT, WP, NP = 8961, 8962, 8963
API=f'http://127.0.0.1:{WP}'; URL=f'http://localhost:{PORT}/index.html'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
WRAP="()=>{ window.__sc=0; const o=window.syncAll; window.syncAll=function(...a){ window.__sc++; return o.apply(this,a); }; }"
sc=lambda pg: pg.evaluate("window.__sc")
def idle(pg): pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(300)
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    c1,p1=mkctx(b); fresh(p1); p1.evaluate(WRAP)
    check('demo: no auto sync on the landing', sc(p1)==0 and p1.locator('#view>.demotop').count()==1)
    login(p1,KA); wait_on(p1); p1.wait_for_timeout(800)
    check('new user (0 characters) → no sync yet (doImport syncs after picking)', sc(p1)==0, sc(p1))
    # 캐릭터: 본캐(본계정 키) + 부캐(키 없는 부계정 칸, ocid o-acc-F)
    p1.evaluate("""()=>{ const A=accounts()[0]; S.settings.accounts.push({id:'aF',label:'부계정'}); const mk=(id,nm,acc,o,main)=>({id,name:nm,level:280,job:'히어로',world:'스카니아',ocid:o,accId:acc,isMain:main,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
      S.characters.push(mk('c1','본캐A',A.id,'o-acc-A',true), mk('c2','부캐F','aF','o-acc-F',false)); save(); render(); svSaveNow(); }"""); wait_on(p1)
    # 본계정 키 삭제 → 처음 화면 → 같은 키 다시 등록 → 자동 동기화 1번
    p1.evaluate("openAdd()"); p1.wait_for_selector('#accList .accrow'); p1.locator('#accList .accrow').nth(0).locator('[data-accdel]').click()
    p1.wait_for_function("!svTok()",timeout=10000); p1.wait_for_timeout(800)
    p1.reload(); p1.wait_for_timeout(600); p1.evaluate(WRAP)
    login(p1,KA); wait_on(p1); p1.wait_for_timeout(500)
    n1=sc(p1)
    check('re-register main key → characters restored + 1 auto sync', n1==1 and p1.evaluate("S.characters.filter(charShown).length")==1, (n1,p1.evaluate("S.characters.map(c=>[c.name,charShown(c)])")))
    p1.screenshot(path=SHOT+'/after_reregister_sync_running.png'); idle(p1)
    check('sync finished → lastSync set', p1.evaluate("Date.now()-(+S.settings.lastSync||0)<60000"), p1.evaluate("S.settings.lastSync"))
    p1.evaluate("keySync(); keySync()"); p1.wait_for_timeout(300)
    check('within 3s of last sync / while syncing → no duplicate', sc(p1)==1, sc(p1))
    p1.screenshot(path=SHOT+'/after_reregister_synced.png')
    # 부계정 키 추가 → 부캐 다시 연결 → 1번 동기화
    p1.wait_for_timeout(3200)
    p1.evaluate("openAdd()"); p1.wait_for_selector('#accAddOpen'); p1.evaluate("accAddShow(true)"); p1.fill('#newAccLabel','부계정'); p1.fill('#newAccKey',KF); p1.click('#newAccBtn')
    p1.wait_for_function("accounts().some(a=>a.key==='%s')"%KF,timeout=15000); p1.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); p1.wait_for_timeout(600)
    check('add sub key with linked character → 부캐 shown + 1 more auto sync', sc(p1)==2 and p1.evaluate("S.characters.filter(charShown).length")==2, (sc(p1),p1.evaluate("S.characters.map(c=>[c.name,charShown(c)])")))
    idle(p1); p1.evaluate("closeImport()"); p1.screenshot(path=SHOT+'/after_sub_key_sync.png')
    # b222: 새로 들어올 때·새로고침(F5)·뒤로/앞으로 모두 1번 (3초 안 중복은 건너뜀)
    NX=[]; p1.on('request',lambda r: NX.append(r.url) if 'open.api.nexon.com' in r.url and '/character/list' not in r.url else None)
    nav=lambda: p1.evaluate("performance.getEntriesByType('navigation')[0].type")
    def one_sync(tag,want):
        p1.wait_for_timeout(300); p1.wait_for_function("!syncing",timeout=30000); p1.wait_for_timeout(500)
        basic=[u for u in NX if '/character/basic' in u]
        check(f'{tag} → one auto sync (≤1 basic call per shown character)', len(NX)>0 and nav()==want and 0<len(basic)<=2, (len(NX),len(basic),nav()))
    p1.wait_for_timeout(3200); NX.clear(); p1.reload(); one_sync('b222: F5 reload (logged in)','reload')
    NX.clear(); p1.reload(); p1.wait_for_timeout(2000)
    check('b222: reload again within 3s of last sync → skipped (no duplicate)', len(NX)==0 and nav()=='reload', (len(NX),nav()))
    p1.wait_for_timeout(3200); NX.clear(); p1.goto(URL); one_sync('fresh entry (navigate)','navigate')
    p1.screenshot(path=SHOT+'/fresh_entry_synced.png')
    p1.wait_for_timeout(3200); p1.goto('about:blank'); NX.clear(); p1.go_back(); p1.wait_for_timeout(300); p1.wait_for_function("!syncing",timeout=30000); p1.wait_for_timeout(500)
    bf=p1.evaluate("performance.getEntriesByType('navigation')[0]?.type")
    check('b222: back/forward → one auto sync (reload 처럼)', len([u for u in NX if '/character/basic' in u])>0 and bf=='back_forward', (len(NX),bf))
    # bfcache 복원(pageshow persisted)도 같은 규칙: 3초 지났으면 1번, 동기화 중이면 건너뜀
    p1.wait_for_timeout(3200); NX.clear()
    p1.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); p1.wait_for_timeout(50)
    n_a=p1.evaluate("syncing||Date.now()-(+localStorage.getItem(LOAD_SYNC_KEY)||0)<1000"); p1.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); p1.wait_for_function("!syncing",timeout=30000)
    basic=[u for u in NX if '/character/basic' in u]
    check('b222: bfcache restore → one sync, second pageshow (syncing/within 3s) skipped', n_a and 0<len(basic)<=2, (n_a,len(basic)))
    tip=p1.evaluate("document.querySelector('#syncBtn,[data-act=sync],.syncbtn')?.title||''")
    check('b222: sync button tooltip mentions reload', '새로고침할 때' in tip and '제외' not in tip, tip)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
