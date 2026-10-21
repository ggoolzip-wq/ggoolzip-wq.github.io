import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8977=_tutil.free_port()
# b219: 지운 부계정(goneAccs)에 묶여 숨겨진 캐릭터 → 같은 부계정 키를 다시 등록하면 그 캐릭터(id·기록)가 다시 연결돼 보임
import os, sys, json, subprocess, time, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM, KA, ACC
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8977
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def wait_list(pg): pg.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); pg.wait_for_timeout(200)
def wait_sync(pg): pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(250)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1366,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle); ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d:d.accept())
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(400)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','본계정'); pg.fill('#newAccKey',KM); pg.press('#newAccKey','Enter'); wait_list(pg)
    pg.check('#impList .imp-item:has-text("단풍용사") input'); pg.click('#impOk'); wait_sync(pg)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); wait_list(pg)
    pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','부계정'); pg.fill('#newAccKey',KA); pg.click('#newAccBtn'); wait_list(pg)
    pg.check('#impList .imp-item:has-text("부계정비숍") input'); pg.click('#impOk'); wait_sync(pg)
    sub=pg.evaluate("S.characters.find(c=>c.name==='부계정비숍')"); sid=sub['id']
    pg.evaluate("id=>{const c=S.characters.find(x=>x.id===id); c.weekly={lucid:true}; save();}",sid)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); wait_list(pg)
    pg.click('#accList .accrow:has(.acclbl[value="부계정"]) [data-accdel]'); pg.wait_for_timeout(400)
    check('setup: sub slot deleted → its character hidden (goneAccs)', pg.evaluate("id=>!charShown(S.characters.find(c=>c.id===id))&&(S.settings.goneAccs||[]).length===1",sid))
    pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','부계정'); pg.fill('#newAccKey',KA); pg.click('#newAccBtn'); wait_list(pg); pg.wait_for_timeout(500)
    r=pg.evaluate("id=>{const c=S.characters.find(x=>x.id===id); return {shown:charShown(c),weekly:c.weekly,acc:accById(c.accId)?.label,gone:(S.settings.goneAccs||[]).length,n:S.characters.filter(x=>x.name==='부계정비숍').length}}",sid)
    check('b219: re-add same sub key → same character (same id, records kept) shown again, no duplicate', r['shown'] and r['weekly'].get('lucid') and r['acc']=='부계정' and r['gone']==0 and r['n']==1, r)
    check('JS 오류 없음', not errs, errs)
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
