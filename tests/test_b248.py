# test_b248: 수수료 = 결과 글자만 — 전체 수정 창/수익 기록 팝업 모두 오른쪽 칸(판매가)은 그대로, 왼쪽 작은 글자 = 수수료 반영 m. 저장 = a(판매가)+fs/fd+m
# MBT_SHOTDIR=폴더 → 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR'); PFX='before' if not CHECK else 'after'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
def state(theme):
    C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',3)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    return {'version':5,'theme':theme,'activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
FIND="b=>[...document.querySelectorAll(`[data-drop^=\"${b}|\"]`)].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))"
# 세렌 1인 10억(a 있음), 카링 3인 분배 10억(a 없음 = 예전 기록 → revGrossOf 역산)
SEED="""([ks,kk,party])=>{const c=S.characters[0]; c.drops={[ks]:1}; c.drev={[ks]:{m:1e9,a:10,p:1,i:ks.split('|')[1]}};
 if(party){ c.drops[kk]=1; c.dmode={[kk]:'s'}; c.drev[kk]={m:Math.round(1e9/3),p:3,i:kk.split('|')[1]}; } save(); render(); }"""
val=lambda pg,k:pg.evaluate("k=>{const r=S.characters[0].drev;const i=revAllRows(S.characters[0]).findIndex(x=>x.key===k);return [document.querySelector(`[data-ra=\"${i}\"]`)?.value,document.querySelector(`[data-ram=\"${i}\"]`)?.textContent]}",k)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for theme in (['dark','light'] if CHECK else ['dark']):
      for vw,vh in ([(1280,900),(390,844)] if CHECK else [(1280,900)]):
       for party in [True,False]:
        tag=f'{theme} {vw} {"party" if party else "solo"}'; shot=SD and vw==1280 and theme=='dark'; sx="party" if party else "solo"
        pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",state(theme)); pg.reload(); pg.wait_for_timeout(800)
        ks=pg.evaluate(FIND,'seren'); kk=pg.evaluate(FIND,'kaling')
        pg.evaluate(SEED,[ks,kk,party]); pg.wait_for_timeout(200)
        # ---- 전체 수정 창
        pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
        if CHECK:
            check(f'처음 칸 = 판매가 {tag}', val(pg,ks)[0]=='10' and (not party or val(pg,kk)[0]=='10'), (val(pg,ks),party and val(pg,kk)))
        pg.click('[data-rafee="s"][data-v="3"]')
        if party: pg.click('[data-rafee="d"][data-v="3"]')
        if shot: pg.locator('#revAllModal .modal').screenshot(path=f'{SD}/{PFX}_editall_{sx}.png')
        if CHECK:
            vs,vk=val(pg,ks),(val(pg,kk) if party else None)
            check(f'수수료 후 칸 그대로 {tag}', vs[0]=='10' and (not party or vk[0]=='10'), (vs,vk))
            check(f'왼쪽 결과 글자 {tag}', vs[1]==pg.evaluate("()=>meso(970000000)") and (not party or vk[1]==pg.evaluate("()=>meso(Math.round(revNet(revGross(Math.round(1e9/3),3,0,0),3,3,3)))")), (vs,vk))
            pg.click('[data-rab="ok"]'); pg.wait_for_timeout(300)
            r=pg.evaluate("()=>S.characters[0].drev"); saved=pg.evaluate("()=>JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0].drev")
            check(f'solo 저장 {tag}', r[ks]=={'m':970000000,'a':10,'p':1,'i':ks.split('|')[1],'fs':3,'fd':0}, r[ks])
            if party: check(f'party 저장 a=10 {tag}', abs(r[kk]['m']-316801347)<=1 and abs(r[kk]['a']-10)<1e-4 and r[kk]['fs']==3 and r[kk]['fd']==3 and r[kk]['p']==3, r[kk])
            check(f'로컬 저장 {tag}', saved==r)
            # 재열기 = 칸 10, 강조 3%, 칸 20 입력 → 결과 글자 갱신, 저장 a=20
            pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
            check(f'재열기 칸 10·3% {tag}', val(pg,ks)[0]=='10' and pg.locator('[data-rafee="s"].on').inner_text()=='3%')
            i=pg.evaluate("k=>revAllRows(S.characters[0]).findIndex(x=>x.key===k)",ks); pg.fill(f'[data-ra="{i}"]','20')
            check(f'입력 → 결과 글자 {tag}', val(pg,ks)[1]==pg.evaluate("()=>meso(19.4e8)"), val(pg,ks))
            pg.click('[data-rab="ok"]'); pg.wait_for_timeout(300)
            r=pg.evaluate("()=>S.characters[0].drev"); check(f'20억 3% 저장 {tag}', r[ks]['m']==1940000000 and r[ks]['a']==20 and r[ks]['fs']==3, r[ks])
        else: pg.keyboard.press('Escape')
        # ---- 수익을 기록할까요? 팝업
        pg.evaluate("()=>localStorage.removeItem('mapleBossTracker.revFee')")
        k=kk if party else ks; bid='kaling' if party else 'seren'
        pg.evaluate("([k,b])=>askRev(S.characters[0],findBoss(b),k,k.split('|')[1],null)",[k,bid]); pg.wait_for_selector('#revModal')
        pg.fill('#rvAmt','10'); pg.click('[data-fee="s"][data-v="3"]')
        if party: pg.click('[data-fee="d"][data-v="3"]')
        if shot: pg.locator('#revModal .modal').screenshot(path=f'{SD}/{PFX}_popup_{sx}.png')
        if CHECK:
            exp=316801347 if party else 970000000
            check(f'팝업 칸 그대로 {tag}', pg.input_value('#rvAmt')=='10')
            rt=pg.inner_text('#rvRam'); check(f'팝업 결과 글자 {tag}', rt==pg.evaluate(f"()=>meso({exp})"), rt)
            g=pg.evaluate("()=>{const a=document.querySelector('#rvRam').getBoundingClientRect(),i=document.querySelector('#rvAmt').getBoundingClientRect(),m=document.querySelector('#revModal .modal').getBoundingClientRect();return {left:a.right<=i.left+1,row:Math.abs((a.top+a.bottom)/2-(i.top+i.bottom)/2)<12,fit:a.left>=m.left-1,ov:document.documentElement.scrollWidth>innerWidth}}")
            check(f'팝업 글자 왼쪽·같은 줄 {tag}', g['left'] and g['row'] and g['fit'] and not g['ov'], g)
            pg.click('[data-fee="s"][data-v="5"]'); rt2=pg.inner_text('#rvRam')
            check(f'팝업 수수료 바꾸면 글자 갱신 {tag}', rt2!=rt and pg.input_value('#rvAmt')=='10', rt2)
            pg.click('[data-fee="s"][data-v="3"]'); pg.click('[data-rv="ok"]'); pg.wait_for_timeout(300)
            r=pg.evaluate("()=>S.characters[0].drev")[k]
            check(f'팝업 저장 {tag}', r['m']==exp and r['a']==10 and r['fs']==3 and r['fd']==(3 if party else 0), r)
        pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
