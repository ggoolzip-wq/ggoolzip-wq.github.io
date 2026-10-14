# b110: 모든 가운데 창 — 바깥(배경) 클릭 = [취소]와 같음 (저장 없이 닫고, 대기 상태도 취소처럼 되돌림)
import os, sys, time, subprocess, json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8898'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',2)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
SIG="JSON.stringify([S.characters[0].drops,S.characters[0].dropOut||{},S.characters[0].drev||{},S.characters[0].dmode||{}])"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    s0=pg.evaluate(SIG)
    bg=lambda: (pg.mouse.click(4,4), pg.wait_for_timeout(250))
    seren=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))")
    kal=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|\"]')].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))")
    ring=pg.evaluate("[...document.querySelectorAll('[data-drop*=\"|r_\"]')].map(e=>e.dataset.drop)[0]")
    cbox=pg.evaluate("[...document.querySelectorAll('[data-drop$=\"|chaosbox\"]')].map(e=>e.dataset.drop)[0]")
    # 수익 기록 창: 바깥 = 취소 = 체크 되돌림
    pg.click(f'[data-drop="{seren}"]'); pg.wait_for_selector('#revModal'); pg.fill('#rvAmt','3'); bg()
    check('수익 기록 창: 바깥 클릭 → 닫힘·체크 되돌림·기록 없음·축하 없음·저장 대기 없음', pg.locator('#revModal').count()==0 and pg.evaluate(SIG)==s0 and pg.locator('#congrats.show').count()==0 and pg.evaluate('!pend'), pg.evaluate(SIG))
    # 블빵/분배 창
    pg.click(f'[data-drop="{kal}"]'); pg.wait_for_selector('#bbModal'); bg()
    check('블빵/분배 창: 바깥 → 취소', pg.locator('#bbModal').count()==0 and pg.evaluate(SIG)==s0 and pg.evaluate('!pend'))
    # 반지 상자 창
    if ring:
        pg.click(f'[data-drop="{ring}"]'); pg.wait_for_selector('#ringModal.show'); bg()
        check('반지 상자 창: 바깥 → 취소', pg.locator('#ringModal.show').count()==0 and pg.evaluate(SIG)==s0 and pg.evaluate('!pend'))
    if cbox:
        pg.click(f'[data-drop="{cbox}"]'); pg.wait_for_selector('#chaosModal'); bg()
        check('칠흑 상자 창: 바깥 → 취소', pg.locator('#chaosModal').count()==0 and pg.evaluate(SIG)==s0 and pg.evaluate('!pend'))
    # 수익 기록 전체 수정 창
    pg.click(f'[data-drop="{seren}"]'); pg.wait_for_selector('#revModal'); pg.fill('#rvAmt','2'); pg.click('.rvok'); pg.wait_for_timeout(300); pg.evaluate('endCelebrate()'); pg.click('#pendSave'); pg.wait_for_timeout(300)
    s1=pg.evaluate(SIG)
    pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal'); pg.locator('.rarow input').first.fill('9'); bg()
    check('수익 기록 전체 수정 창: 바깥 → 저장 없이 닫힘', pg.locator('#revAllModal').count()==0 and pg.evaluate(SIG)==s1)
    # 캐릭터 편집·추가·드라이브 창
    for nm,op,sel in [('캐릭터 편집 창',"openCharModal('c0')",'#charModal.show'),('캐릭터 추가 창',"document.querySelector('#addCharBtn').click()",'#importModal.show'),('드라이브 창',"document.querySelector('#driveModal').classList.add('show')",'#driveModal.show')]:
        pg.evaluate(op); pg.wait_for_timeout(300); was=pg.locator(sel).count()==1; bg()
        check(f'{nm}: 바깥 → 닫힘', was and pg.locator(sel).count()==0 and pg.evaluate(SIG)==s1)
    b.close()
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs); sys.exit(1 if (fails or errs) else 0)
