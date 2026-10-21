import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8876=_tutil.free_port()
# zosu-ui: '수익을 기록할까요?' [취소하기] = 그 아이템 선택을 되돌림 (기록·축하 없음, 상태 = 누르기 전과 같음)
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8876)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',2)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
SIG="JSON.stringify(['drops','dmode','outs','drev','mdrops','mdmode','mouts','mdrev'].map(k=>{const v=S.characters[0][k];return v&&Object.keys(v).length?v:null}))"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    first=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))")
    kit=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|\"]')].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))")
    ring=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|r_\"]')].map(e=>e.dataset.drop)[0]")
    cbox=pg.evaluate("[...document.querySelectorAll('[data-drop$=\"|chaosbox\"]')].map(e=>e.dataset.drop)[0]")
    def cancel_case(name,open_fn,key):
        s0=pg.evaluate(SIG); g0=pg.evaluate("document.querySelectorAll('[data-drop].got').length")
        open_fn(); pg.wait_for_selector('#revModal')
        bt=pg.evaluate("(()=>{const o=document.querySelector('.rvno'),k=document.querySelector('.rvok'),c=document.querySelector('.rvcancel'),l=document.querySelector('.rvleft');if(!c)return null;const a=o.getBoundingClientRect(),b=k.getBoundingClientRect(),z=c.getBoundingClientRect(),L=l.getBoundingClientRect();return {t:c.innerText,next:Math.abs(a.top-b.top)<4&&b.right<=a.left+1&&z.top>=a.bottom-1&&Math.abs((z.left+z.right)/2-(L.left+L.right)/2)<3}})()")  # zosu-testfix: b181 — [기록하기][기록 없이 저장] 아래 가운데 [취소]
        check(f'{name}: (b181) 기록 없이 저장 줄 아래 가운데 취소', bt and bt['t']=='취소' and bt['next'], bt)
        pg.click('.rvcancel'); pg.wait_for_timeout(400)
        s1=pg.evaluate(SIG); g1=pg.evaluate("document.querySelectorAll('[data-drop].got').length")
        saved=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0]")
        check(f'{name}: 창 닫힘·축하 없음·선택 되돌림(저장 상태도)', pg.locator('#revModal').count()==0 and pg.locator('#congrats.show').count()==0 and s1==s0 and g1==g0 and not (saved.get('drops') or {}).get(key) and not (saved.get('drev') or {}).get(key), (s0,s1,g0,g1))
    cancel_case('1인', lambda: pg.click(f'[data-drop="{first}"]'), first)
    cancel_case('2인 분배', lambda: (pg.click(f'[data-drop="{kit}"]'), pg.wait_for_selector('#bbModal'), pg.click('#bbModal [data-bb=s]')), kit)
    cancel_case('반지 상자 리4', lambda: (pg.click(f'[data-drop="{ring}"]'), pg.wait_for_selector('#ringModal.show'), pg.click('#ringModal [data-ring=r4]')), ring)
    if cbox:
        cancel_case('칠흑 상자', lambda: (pg.click(f'[data-drop="{cbox}"]'), pg.wait_for_selector('#chaosModal'), pg.click('#chaosModal [data-cbpick]:not([data-cbpick=""])'), pg.wait_for_selector('#bbModal'), pg.click('#bbModal [data-bb=w]')), cbox)
    # 취소 뒤 다시 누르면 정상 기록
    pg.click(f'[data-drop="{first}"]'); pg.wait_for_selector('#revModal'); pg.fill('#rvAmt','1'); pg.click('.rvok'); pg.wait_for_timeout(300)
    check('취소 뒤 다시 누르면 정상 기록·축하', pg.evaluate(f"S.characters[0].drev['{first}'].m")==100000000 and pg.locator('#congrats.show').count()==1)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally: srv.kill()
print('FAILS:',fails); sys.exit(1 if fails else 0)
