# b49: 블빵승리/패배/분배 (2인 이상), 생명 반지 '셋 다', 축하 이모지
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8837/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8837','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',2)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
EMO=['😚','😙','😊','😘','🥳']
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    rev0=pg.evaluate("charRevenue(S.characters[0]).meso")
    first=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].map(e=>e.dataset.drop).find(k=>!/^seren\\|r_/.test(k))")
    pg.click(f'[data-drop="{first}"]'); pg.wait_for_timeout(200)
    t=pg.inner_text('#congrats') if pg.locator('#congrats.show').count() else ''
    check('1인: 고르기 창 없이 바로 기록 + 축하 + 이모지 1개', pg.locator('#bbModal').count()==0 and pg.evaluate(f"S.characters[0].drops['{first}']===1") and '축하드립니다!' in t and sum(t.count(e) for e in EMO)==1, t)
    pg.evaluate('endCelebrate()')
    pg.click('[data-drop="kaling|g_faith"]'); pg.wait_for_selector('#bbModal')
    opts=pg.eval_on_selector_all('#bbModal [data-bb]','e=>e.map(x=>[x.dataset.bb,x.innerText.trim(),!!x.querySelector("img")])')
    gray=pg.evaluate("getComputedStyle(document.querySelector('#bbModal [data-bb=l] img')).filter")
    check('2인: 블빵승리/블빵패배/분배/취소, 블링크 아이콘(패배는 흑백), 메소 아이콘', [o[1] for o in opts]==['블빵승리','블빵패배','분배','취소'] and all(o[2] for o in opts[:3]) and 'grayscale' in gray, (opts,gray))
    check('b50: 제목 대신 큰 아이템 아이콘 + 이름만', pg.inner_text('#bbModal .bbname')=='신념의 연마석' and '파티' not in pg.inner_text('#bbModal') and pg.evaluate("document.querySelector('#bbModal .bbico img').getBoundingClientRect().width")>=60)
    r=pg.evaluate("(()=>{const m=document.querySelector('#bbModal .modal').getBoundingClientRect();return [Math.round(m.left+m.width/2-innerWidth/2),Math.round(m.top+m.height/2-innerHeight/2)]})()")
    check('창이 가운데', abs(r[0])<=2 and abs(r[1])<=2, r)
    pg.evaluate("document.querySelector('#iconBurst')?.remove()"); pg.locator('#bbModal .modal').screenshot(path='/workspace/shots/b49_modal.png')
    pg.click('#bbModal [data-bb=""]'); pg.wait_for_timeout(150)
    check('취소 → 기록 안 함, 취소/저장 비활성', not pg.evaluate("S.characters[0].drops['kaling|g_faith']") and pg.locator('#bbModal').count()==0)
    pg.click('[data-drop="kaling|g_faith"]'); pg.click('#bbModal [data-bb=w]'); pg.wait_for_timeout(200)
    t=pg.inner_text('#congrats')
    check('블빵승리 → 기록(w) + 축하', pg.evaluate("S.characters[0].drops['kaling|g_faith']===1&&S.characters[0].dmode['kaling|g_faith']==='w'") and pg.locator('#congrats.show').count()==1 and sum(t.count(e) for e in EMO)==1, t)
    pg.evaluate("endCelebrate(); document.querySelector('#iconBurst')?.remove()")
    # 생명 반지 상자: 결과 → 3지선다 → 블빵패배 (축하 없음)
    pg.click('[data-drop="kaling|r_life"]'); pg.wait_for_selector('#ringModal.show')
    xt=pg.inner_text('#ringModal [data-ring=x]'); check("생명 반지 상자: '셋 다 못 먹었어요'", '셋 다 못 먹었어요' in xt, xt)
    pg.click('#ringModal [data-ring=r4]'); pg.wait_for_selector('#bbModal')
    check('b50: 반지 상자 → 고른 결과(리4) 아이콘·이름', pg.inner_text('#bbModal .bbname')=='리스트레인트 링 4레벨', pg.inner_text('#bbModal .bbname'))
    pg.evaluate("document.querySelector('#iconBurst')?.remove()"); pg.locator('#bbModal .modal').screenshot(path='/workspace/shots/b50_modal.png')
    pg.click('#bbModal [data-bb=l]'); pg.wait_for_timeout(200)
    check('반지: 결과 고른 뒤 블빵패배 → 기록(l)·결과 r4, 축하·불꽃 없음', pg.evaluate("S.characters[0].dmode['kaling|r_life']==='l'&&S.characters[0].dropOut['kaling|r_life'][0]==='r4'") and pg.locator('#congrats.show').count()==0 and pg.locator('#iconBurst').count()==0)
    pg.evaluate("openRing('kaling|r_white')"); xt2=pg.inner_text('#ringModal [data-ring=x]'); pg.evaluate('closeRing()')
    check("다른 반지 상자는 '둘 다'", '둘 다 못 먹었어요' in xt2, xt2)
    # 칠흑: 장신구 → 3지선다 → 분배
    pg.click('[data-drop="kaling|chaosbox"]'); pg.wait_for_selector('#chaosModal'); pg.click('#chaosModal [data-cbpick=eye]'); pg.wait_for_selector('#bbModal'); check('b50: 칠흑 → 고른 장신구 이름', pg.inner_text('#bbModal .bbname')=='마력이 깃든 안대', pg.inner_text('#bbModal .bbname')); pg.click('#bbModal [data-bb=s]'); pg.wait_for_timeout(200)
    check('칠흑: 장신구 고른 뒤 분배 → 기록(s) + 축하', pg.evaluate("S.characters[0].dmode['kaling|chaosbox']==='s'&&S.characters[0].dropOut['kaling|chaosbox'][0]==='cb:eye'") and pg.locator('#congrats.show').count()==1)
    pg.evaluate('endCelebrate()')
    check('결정석 수익은 그대로 (1/n)', pg.evaluate("charRevenue(S.characters[0]).meso")==rev0, rev0)
    pg.click('#pendSave'); pg.wait_for_timeout(300)
    check('저장 → 선택이 저장 데이터에 남음', json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))['characters'][0]['dmode']=={'kaling|g_faith':'w','kaling|r_life':'l','kaling|chaosbox':'s'})
    rp=pg.inner_text('.revpanel'); cw=pg.evaluate("getComputedStyle(document.querySelector('.revpanel .ptx-w')).color"); cl=pg.evaluate("getComputedStyle(document.querySelector('.revpanel .ptx-l')).color")
    check('이번 주 수익: (2인 블빵승리) 하늘색 / (2인 블빵패배) 회색 / (2인 분배)', '(2인 블빵승리)' in rp and '(2인 블빵패배)' in rp and '(2인 분배)' in rp and cw=='rgb(127, 211, 255)' and cl=='rgb(138, 143, 152)', (cw,cl))
    hs=pg.evaluate("[...document.querySelectorAll('.revpanel .dl, .ringouts .dl')].map(e=>{const P=e.parentElement.closest('.rp-items,.ringouts').getBoundingClientRect(),R=e.getBoundingClientRect();return [e.innerText.replace(/\\s+/g,' '),Math.round(R.height),R.right<=P.right+1]})")
    check('b50: 모든 항목(칠흑·블빵 포함)이 한 줄 덩어리, 칸 밖으로 안 나감', hs and all(h<=26 and ok for _,h,ok in hs), hs)
    pg.evaluate("endCelebrate(); document.querySelector('#iconBurst')?.remove()"); pg.locator('.revpanel').screenshot(path='/workspace/shots/b49_income.png')
    pg.click('[data-tab=total]'); pg.wait_for_timeout(500)
    tot=pg.inner_text('.itemtot'); bl=pg.inner_text('.bossloot')
    check('수익 분석 총 아이템 획득량: 승리/패배 따로', '(블빵승리)' in tot and '(블빵패배)' in tot and pg.locator('.itemtot .loot.md-w').count()>=1 and pg.locator('.itemtot .loot.md-l').count()>=1, tot)
    ring=pg.evaluate("totalData().ring"); check('패배한 반지 상자의 결과는 내 시드링(리4) 집계에서 제외', ring['r4']==0, ring)
    check('캐릭터별 표에도 (2인 블빵승리)/(2인 블빵패배)', '(2인 블빵승리)' in pg.inner_text('#view') and '(2인 블빵패배)' in pg.inner_text('#view'))
    pg.evaluate("endCelebrate(); document.querySelector('#iconBurst')?.remove()"); pg.locator('.bossloot').screenshot(path='/workspace/shots/b49_total.png')
    # 예전 기록(선택 없음)은 그대로 (n인 분배)
    pg.evaluate("delete S.characters[0].dmode; save(); render()"); pg.click('[data-tab=boss]'); pg.wait_for_timeout(300)
    rp=pg.inner_text('.revpanel'); check('선택 없는 예전 기록 → (2인 분배)', '블빵' not in rp and '(2인 분배)' in rp, rp)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
