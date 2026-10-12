import _legacy
import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# b95: 계정 키 삭제 → 키만 지움(칸·캐릭터 연결 유지, 숨김), 대표 키 삭제 → 부계정 키도 전부, 같은 키 다시 넣으면 다시 보임
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, sys
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM, KA, ACC
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen(['python3','-m','http.server','8899','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8899/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL='http://localhost:8899/index.html'
def wait_list(pg): pg.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); pg.wait_for_timeout(200)
def wait_sync(pg): pg.wait_for_function("!syncing",timeout=30000); pg.wait_for_timeout(250)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1366,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'gsi' not in m.text else None)
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(400)
    check('no settings tab, no API side card', pg.query_selector('[data-tab="settings"]') is None and pg.query_selector('#apiSide') is None)
    check('sync button hidden without key', pg.is_hidden('#syncBtn'))
    # 1) + 추가 → 빈 상태 → 본계정 키 추가 → 목록 → 전체 선택 추가
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show')
    pg.wait_for_timeout(200); fe=pg.evaluate("document.activeElement.id"); check('empty modal: key form focused, list hidden', pg.is_hidden('#impSec') and fe in ('newAccKey','newAccLabel'), fe)  # b72: 이름 칸이 먼저(필수)
    pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','본계정'); pg.fill('#newAccKey',KM); pg.press('#newAccKey','Enter'); wait_list(pg)
    n1=pg.locator('#impList .imp-item').count()
    check('after adding key, its characters listed', n1==len(ACC[KM]) and '본계정' in pg.inner_text('#impTitle'), (n1,pg.inner_text('#impMsg')))
    check('key not shown, 등록 완료 with green check', pg.locator('#accList .kmask').count()==0 and '등록 완료' in pg.inner_text('#accList') and 'live_' not in pg.inner_text('#accList'), pg.inner_text('#accList'))
    pg.fill('#impQ','메이지'); pg.wait_for_timeout(80); check('search filters', pg.locator('#impList .imp-item').count()==1); pg.fill('#impQ',''); pg.wait_for_timeout(80)
    for nm in ['단풍용사','불독메이지','신궁짱']: pg.check(f'#impList .imp-item:has-text("{nm}") input')
    pg.click('#impOk'); wait_sync(pg)
    check('3 chars added, modal closed', pg.evaluate('S.characters.length')==3 and not pg.is_visible('#importModal'))
    check('sync button (character card header, 2026-10-10): icon only, aria-label, last time in title', pg.inner_text('#syncBtn').strip()=='' and '지금 동기화' in pg.get_attribute('#syncBtn','aria-label') and '마지막 동기화:' in pg.get_attribute('#syncBtn','title') and pg.query_selector('#syncBtn svg.rot') is not None and pg.query_selector('header #syncBtn') is None, (pg.inner_text('#syncBtn'),pg.get_attribute('#syncBtn','title')))
    # spin while syncing
    pg.evaluate("syncing=true; renderHeaderSync()"); check('icon spins while syncing', pg.evaluate("getComputedStyle(document.querySelector('#syncBtn .rot')).animationName")=='sbspin' and pg.is_disabled('#syncBtn'))
    pg.evaluate("syncing=false; renderHeaderSync()")
    # 2) 두 번째 계정
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); wait_list(pg)
    pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','부계정'); pg.fill('#newAccKey',KA); pg.click('#newAccBtn'); wait_list(pg)
    rows=pg.eval_on_selector_all('#accList .accrow','e=>e.map(x=>[x.querySelector(".acclbl").value,x.classList.contains("on")])')
    check('2 accounts listed, new one selected', rows==[['본계정',False],['부계정',True]], rows)
    check('부계정 chars listed', pg.locator('#impList .imp-item').count()==len(ACC[KA]))
    pg.check('#impList .imp-item:has-text("부계정비숍") input')
    pg.wait_for_timeout(200); pg.locator('#importModal .modal').screenshot(path=''+OUT+'/add_modal.png')
    pg.click(f'#accList .accrow:has(.acclbl[value="본계정"]) .accst'); wait_list(pg)
    check('switch account → its list, added ones disabled', pg.locator('#impList .imp-item.dis').count()==3 and '본계정' in pg.inner_text('#impTitle'), (pg.locator('#impList .imp-item.dis').count(), pg.inner_text('#impTitle'), pg.inner_text('#impMsg')[:80]))
    pg.click(f'#accList .accrow:has(.acclbl[value="부계정"]) .accst'); wait_list(pg)
    pg.check('#impList .imp-item:has-text("부계정비숍") input'); pg.click('#impOk'); wait_sync(pg)
    check('4 chars', pg.evaluate('S.characters.length')==4)
    # 3) 이름으로 직접 추가 + 편집
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.evaluate('closeImport();openCharModal()'); pg.wait_for_selector('#charModal.show')
    check('manual add opens char modal', not pg.is_visible('#importModal')); pg.click('#fCancel')
    pg.click('.char:has-text("신궁짱") [data-edit]'); pg.wait_for_selector('#charModal.show'); check('edit still works', pg.input_value('#fName')=='신궁짱'); pg.click('#fCancel')
    # 4) 삭제
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); wait_list(pg)
    pg.once('dialog',lambda d:d.accept()); pg.click('#accList .accrow:has(.acclbl[value="부계정"]) [data-accdel]'); pg.wait_for_timeout(300)
    check('account deleted, chars kept', pg.locator('#accList .accrow').count()==1 and pg.evaluate('S.characters.length')==4, (pg.locator('#accList .accrow').count(), pg.evaluate('S.characters.length')))
    st=pg.evaluate("JSON.stringify(S)")
    check('b95: alt slot kept keyless, chars hidden not unassigned', pg.evaluate("S.settings.accounts.some(a=>a.label==='부계정'&&!a.key)") and pg.evaluate("S.characters.filter(c=>c.accId&&!charShown(c)).length")>0, pg.evaluate("S.settings.accounts.map(a=>[a.label,!!a.key])"))
    check('b95: deleted key not in state/localStorage', KA not in st and all(KA not in (pg.evaluate(f"localStorage.getItem(localStorage.key({i}))") or '') for i in range(pg.evaluate('localStorage.length'))))
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12z_approval_after_altdel.png')
    pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel','부계정'); pg.fill('#newAccKey',KA); pg.click('#newAccBtn'); wait_list(pg); pg.wait_for_timeout(500)
    check('b95: re-add same alt key → same slot, chars visible again', pg.evaluate("S.settings.accounts.filter(a=>a.label==='부계정').length")==1 and pg.evaluate("S.characters.every(c=>charShown(c))"), pg.evaluate("S.settings.accounts.map(a=>[a.label,!!a.key])"))
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12z_approval_after_readd.png')
    pg.once('dialog',lambda d:d.accept()); pg.click('#accList .accrow:has(.acclbl[value="본계정"]) [data-accdel]'); pg.wait_for_timeout(300)
    check('b95: main delete → all keys gone, slots kept, all linked chars hidden', pg.evaluate("S.settings.accounts.every(a=>!a.key&&!a.bk)") and pg.evaluate("S.characters.filter(c=>c.accId).every(c=>!charShown(c))") and len(pg.evaluate("S.settings.accounts"))==2, pg.evaluate("S.settings.accounts.map(a=>[a.label,!!a.key,!!a.main])"))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails else 0)
