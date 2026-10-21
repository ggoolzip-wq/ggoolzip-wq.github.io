# test_b247: 수익 기록 전체 수정 — 수수료 전체 적용(판매/분배 0·3·5%), 전부 1인이면 판매만, 원래 판매가에서 b244 식으로 다시 계산
# MBT_SHOTDIR=폴더 → 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess, json
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
def state(theme,party):
    C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',3)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    return {'version':5,'theme':theme,'activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
FIND="b=>[...document.querySelectorAll(`[data-drop^=\"${b}|\"]`)].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))"
# 기록 심기: 세렌 1인 10억(수수료 0, 예전 형식: fs 없음), 카링 3인 분배 10억 → 내 몫 = 10억/3 (예전 형식)
SEED="""([ks,kk,party])=>{const c=S.characters[0]; c.drops={[ks]:1}; c.drev={[ks]:{m:1e9,a:10,p:1,i:ks.split('|')[1]}};
 if(party){ c.drops[kk]=1; c.dmode={[kk]:'s'}; c.drev[kk]={m:Math.round(1e9/3),a:10,p:3,i:kk.split('|')[1]}; } save(); render(); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for theme in (['dark','light'] if CHECK else ['dark']):
      for vw,vh in ([(1280,900),(390,844)] if CHECK else [(1280,900)]):
       for party in ([True,False] if CHECK else [True]):
        tag=f'{theme} {vw} {"party" if party else "solo"}'; shot=SD and vw==1280 and theme=='dark'
        pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",state(theme,party)); pg.reload(); pg.wait_for_timeout(800)
        ks=pg.evaluate(FIND,'seren'); kk=pg.evaluate(FIND,'kaling')
        pg.evaluate(SEED,[ks,kk,party]); pg.wait_for_timeout(200)
        pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
        if shot and not CHECK: pg.locator('#revAllModal .modal').screenshot(path=f'{SD}/editall_before.png'); pg.close(); continue
        if not CHECK: pg.close(); continue
        if shot and party: pg.locator('#revAllModal .modal').screenshot(path=f'{SD}/editall_before.png')
        ns=pg.locator('[data-rafrow="s"]').count(); nd=pg.locator('[data-rafrow="d"]').count()
        check(f'줄 수 {tag}', ns==1 and nd==(1 if party else 0), (ns,nd))
        check(f'라벨 {tag}', '판매 수수료 :' in pg.inner_text('[data-rafrow="s"]') and (not party or '분배 수수료 :' in pg.inner_text('[data-rafrow="d"]')))
        check(f'현재 공통값 0% 표시 {tag}', pg.locator('[data-rafee="s"].on').inner_text()=='0%')
        g=pg.evaluate("()=>{const f=document.querySelector('.rafee').getBoundingClientRect(),g=document.querySelector('.ragrp').getBoundingClientRect(),m=document.querySelector('#revAllModal .modal').getBoundingClientRect();return {above:f.bottom<=g.top+1,fit:f.left>=m.left-1&&f.right<=m.right+1,ov:document.documentElement.scrollWidth>innerWidth}}")
        check(f'맨 위 보스 바로 위, 창 안 {tag}', g['above'] and g['fit'] and not g['ov'], g)
        pg.click('[data-rafee="s"][data-v="3"]')
        if party: pg.click('[data-rafee="d"][data-v="3"]')
        check(f'선택 강조 {tag}', pg.locator('[data-rafee="s"].on').inner_text()=='3%' and (not party or pg.locator('[data-rafee="d"].on').inner_text()=='3%'))
        if shot: pg.locator('#revAllModal .modal').screenshot(path=f'{SD}/editall_after_{"party" if party else "solo"}.png')
        pg.click('[data-rab="ok"]'); pg.wait_for_timeout(300)
        r=pg.evaluate("()=>S.characters[0].drev"); saved=pg.evaluate("()=>JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0].drev")
        check(f'solo 10억 3% = 9.7억 {tag}', r[ks]['m']==970000000 and r[ks]['fs']==3 and r[ks]['fd']==0, r[ks])
        if party: check(f'3인 3%/3% = 316,801,347 {tag}', r[kk]['m']==316801347 and r[kk]['fs']==3 and r[kk]['fd']==3 and r[kk]['p']==3, r[kk])
        check(f'로컬 저장 {tag}', saved==r)
        # 다시 열기 → 공통값 3% 강조, 0% 다시 적용 → 원래 값
        pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
        check(f'재열기 3% 강조 {tag}', pg.locator('[data-rafee="s"].on').inner_text()=='3%')
        pg.click('[data-rafee="s"][data-v="0"]')
        if party: pg.click('[data-rafee="d"][data-v="0"]')
        pg.click('[data-rab="ok"]'); pg.wait_for_timeout(300)
        r=pg.evaluate("()=>S.characters[0].drev")
        check(f'0% 복원 solo {tag}', r[ks]['m']==1000000000, r[ks])
        if party: check(f'0% 복원 party {tag}', abs(r[kk]['m']-1e9/3)<=1, r[kk])
        pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
