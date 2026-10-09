import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 설정 탭 제거 + '+ 추가' 통합 모달 + 동기화 버튼(캐릭터 카드 제목 옆)/☁ 메뉴
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, sys
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM, KA, ACC
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL='http://localhost:8787/index.html'
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
    check('empty modal: key form focused, list hidden', pg.is_hidden('#impSec') and pg.evaluate("document.activeElement.id")=='newAccKey')
    pg.fill('#newAccLabel','본계정'); pg.fill('#newAccKey',KM); pg.press('#newAccKey','Enter'); wait_list(pg)
    n1=pg.locator('#impList .imp-item').count()
    check('after adding key, its characters listed', n1==len(ACC[KM]) and '본계정' in pg.inner_text('#impTitle'), (n1,pg.inner_text('#impMsg')))
    check('key masked', pg.inner_text('#accList .kmask')=='live_••••MAIN', pg.inner_text('#accList .kmask'))
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
    pg.fill('#newAccLabel','부계정'); pg.fill('#newAccKey',KA); pg.click('#newAccBtn'); wait_list(pg)
    rows=pg.eval_on_selector_all('#accList .accrow','e=>e.map(x=>[x.querySelector(".acclbl").value,x.classList.contains("on")])')
    check('2 accounts listed, new one selected', rows==[['본계정',False],['부계정',True]], rows)
    check('부계정 chars listed', pg.locator('#impList .imp-item').count()==len(ACC[KA]))
    pg.check('#impList .imp-item:has-text("부계정비숍") input')
    pg.wait_for_timeout(200); pg.locator('#importModal .modal').screenshot(path=''+OUT+'/add_modal.png')
    pg.click(f'#accList .accrow:has(.acclbl[value="본계정"]) [data-acctest]'); wait_list(pg)
    check('switch account → its list, added ones disabled', pg.locator('#impList .imp-item.dis').count()==3 and '본계정' in pg.inner_text('#impTitle'), (pg.locator('#impList .imp-item.dis').count(), pg.inner_text('#impTitle'), pg.inner_text('#impMsg')[:80]))
    pg.click(f'#accList .accrow:has(.acclbl[value="부계정"]) [data-acctest]'); wait_list(pg)
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
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100); check('Esc closes modal', not pg.is_visible('#importModal'))
    # re-add 부계정 for screenshots
    pg.evaluate(f"S.settings.accounts.push({{id:'a2',label:'부계정',key:'{KA}'}}); S.characters.forEach(c=>{{if(c.name==='부계정비숍') c.accId='a2'}}); save(); render();")
    # 5) main screen: 12/12 overlay on main
    pg.evaluate("""(()=>{const c=S.characters.find(c=>c.name==='단풍용사'); const wk=BOSSES.filter(b=>b.type==='weekly'); let n=Object.keys(c.weekly).length;
      for(const b of wk.slice().reverse()){ if(n>=12) break; if(!c.weekly[b.id]){ c.bosses[b.id]=c.bosses[b.id]||{enabled:true,diff:b.diffs[b.diffs.length-1],party:1}; c.bosses[b.id].enabled=true; c.weekly[b.id]=true; n++; } }
      S.activeId=c.id; save(); render(); })()""")
    pg.wait_for_timeout(300); check('overlay on 12/12 char', pg.query_selector('.char:has-text("단풍용사") .dov') is not None)
    pg.evaluate("window.scrollTo(0,0);document.querySelector('#toast').classList.remove('show')"); pg.wait_for_timeout(300)
    pg.screenshot(path=''+OUT+'/main.png')
    # 6) ☁ menu (show signed-in look)
    pg.evaluate("gdMeta.on=true; gdMeta.lastSave=Date.now()-90e3; gdMeta.lastLoad=Date.now()-3600e3; gdMeta.base=S.updatedAt; gd.state='on'; gdRender();")
    pg.click('#gBtn'); pg.wait_for_selector('#gMenu:not([hidden])')
    txt=pg.inner_text('#gMenu')
    check('cloud menu: status, logout, key note, no wipe', all(w in txt for w in ['동기화됨','로그아웃','API 키도 함께 저장돼요']) and '지우기' not in txt and pg.query_selector('#gdWipe') is None, txt[:200])
    pg.screenshot(path=''+OUT+'/cloud_menu.png')
    pg.mouse.click(600,600); pg.wait_for_timeout(100); check('outside click closes menu', pg.is_hidden('#gMenu'))
    # 7) mobile
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.wait_for_timeout(600)
    check('mobile header fits', not m.evaluate('document.documentElement.scrollWidth>innerWidth'), m.evaluate("[...document.querySelectorAll('header *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>e.id||e.className)"))
    m.click('#gBtn'); m.wait_for_timeout(100); m.screenshot(path=OUT+'/shot13_mobile_menu.png'); m.click('#gMenuClose')
    m.click('#addCharBtn'); m.wait_for_timeout(500); check('mobile modal no overflow', not m.evaluate('document.documentElement.scrollWidth>innerWidth')); m.screenshot(path=OUT+'/shot13_mobile_add.png')
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
