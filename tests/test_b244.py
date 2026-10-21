# test_b244: 수익 기록 창 수수료 버튼(판매/분배 0·3·5%) — 1인 판매만, 2인+ 분배 둘 다, 기록 값 = P(1-s)(1-d)/(N-d)
# MBT_SHOTDIR=폴더 → 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',3)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
FIND="b=>[...document.querySelectorAll(`[data-drop^=\"${b}|\"]`)].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))"
def opn(pg,boss):
    k=pg.evaluate(FIND,boss); pg.click(f'[data-drop="{k}"]'); pg.wait_for_selector('#revModal'); return k
def party_mode(pg):  # 분배 모드 선택 창이 뜨면 '분배'
    pg.wait_for_timeout(300)
    if pg.locator('[data-bb="s"]').count(): pg.click('[data-bb="s"]')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for theme in (['dark','light'] if CHECK else ['dark']):
      for vw,vh in ([(1280,900),(390,844)] if CHECK else [(1280,900)]):
        ST['theme']=theme
        pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
        tag=f'{theme} {vw}'
        k=opn(pg,'seren'); pg.fill('#rvAmt','10')
        if SD and vw==1280 and theme=='dark': pg.locator('#revModal .modal').screenshot(path=f'{SD}/'+('fee_after_solo.png' if CHECK else 'fee_before.png'))
        if not CHECK: pg.close(); continue
        check(f'solo: 판매 수수료 줄만 {tag}', pg.locator('[data-frow="s"]').count()==1 and pg.locator('[data-frow="d"]').count()==0)
        check(f'solo: 라벨 {tag}', '판매 수수료 :' in pg.inner_text('[data-frow="s"]'))
        check(f'solo: 기본 0% {tag}', pg.locator('[data-fee="s"].on').inner_text()=='0%')
        g=pg.evaluate("()=>{const a=document.querySelector('.rvin').getBoundingClientRect(),f=document.querySelector('.rvfee').getBoundingClientRect(),o=document.querySelector('.rvok').getBoundingClientRect(),m=document.querySelector('#revModal .modal').getBoundingClientRect();return {order:a.bottom<=f.top+1&&f.bottom<=o.top+1,fit:f.left>=m.left-1&&f.right<=m.right+1,ov:document.documentElement.scrollWidth>innerWidth}}")
        check(f'solo: 입력칸과 기록하기 사이, 창 안 {tag}', g['order'] and g['fit'] and not g['ov'], g)
        pg.click('[data-fee="s"][data-v="3"]')
        check(f'solo: 미리보기 9.7억 {tag}', '9.7억' in pg.inner_text('#rvPrev'), pg.inner_text('#rvPrev'))
        pg.click('.rvok'); pg.wait_for_timeout(300)
        r=pg.evaluate("k=>S.characters[0].drev[k]",k)
        check(f'solo: 기록 = Q = 9.7억 {tag}', r and r['m']==970000000 and r['p']==1, r)
        pg.evaluate("()=>{try{endCelebrate()}catch(e){}}"); pg.wait_for_timeout(200)
        # 3인 분배
        kk=pg.evaluate(FIND,'kaling'); pg.click(f'[data-drop="{kk}"]'); party_mode(pg); pg.wait_for_selector('#revModal')
        check(f'party: 두 줄 {tag}', pg.locator('[data-frow="s"]').count()==1 and pg.locator('[data-frow="d"]').count()==1 and '분배 수수료 :' in pg.inner_text('[data-frow="d"]'))
        check(f'party: 판매 3% 기억 {tag}', pg.locator('[data-fee="s"].on').inner_text()=='3%')
        pg.fill('#rvAmt','10'); pg.click('[data-fee="d"][data-v="3"]')
        if SD and vw==1280 and theme=='dark': pg.locator('#revModal .modal').screenshot(path=f'{SD}/fee_after_party.png')
        check(f'party: 미리보기 3.168억 {tag}', '3.168억' in pg.inner_text('#rvPrev'), pg.inner_text('#rvPrev'))
        pg.click('.rvok'); pg.wait_for_timeout(300)
        r=pg.evaluate("k=>S.characters[0].drev[k]",kk); exp=round(1e9*0.97*0.97/(3-0.03))
        check(f'party: 기록 = Q(1-d)/(N-d) {tag}', r and r['m']==exp and r['p']==3 and r['fd']==3, (r,exp))
        pg.close()
    if CHECK:
      pg=b.new_page(); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(500)
      f=pg.evaluate("[revNet(1e9,1,0,0),revNet(1e9,1,5,5),revNet(1e9,2,0,0),revNet(1e9,3,3,3),revNet(1e9,2,5,5)]")
      check('formula', abs(f[0]-1e9)<1 and abs(f[1]-9.5e8)<1 and abs(f[2]-5e8)<1 and abs(f[3]-316801346.80)<1 and abs(f[4]-1e9*.95*.95/1.95)<1, f)
      # 분배자 x = 받는 사람 y(1-d), 합 = Q
      q=9.7e8; n=3; d=.03; x=f[3]; y=x/(1-d); check('formula consistent', abs(x+(n-1)*y-q)<1)
      pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
