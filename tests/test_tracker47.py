# b62 task 8: '수익을 기록할까요?' 창 (득템 축하 직전), 분배 ÷인원, 블빵패배/반지 꽝 제외, 판매 수익 카드, 이번 주 수익 분홍 줄
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8847/index.html'
SHOT='/workspace/maple-boss-tracker'; os.makedirs(SHOT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8847','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',2)},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    first=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].map(e=>e.dataset.drop).find(k=>!/\\|(r_|chaosbox)/.test(k))")
    kitems=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|\"]')].map(e=>e.dataset.drop).filter(k=>!/\\|(r_|chaosbox)/.test(k))")
    ring=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|r_\"]')].map(e=>e.dataset.drop)[0]")
    D="k=>S.characters[0].drev&&S.characters[0].drev[k]||null"
    # 1) 1인
    pg.click(f'[data-drop="{first}"]'); pg.wait_for_selector('#revModal')
    t=pg.inner_text('#revModal .rvh')
    check('1인: 축하 전에 창, 제목 앞 아이템 아이콘', pg.locator('#congrats.show').count()==0 and '수익을 기록할까요?' in t and pg.locator('#revModal .rvh .rvico img, #revModal .rvh .rvico .ric').count()>=1, t)
    g=pg.evaluate("(()=>{const e=document.querySelector('#rvGuide'),h=document.querySelector('.rvh');return {t:e.innerText,fs:parseFloat(getComputedStyle(e).fontSize),hfs:parseFloat(getComputedStyle(h).fontSize),below:e.getBoundingClientRect().top>=h.getBoundingClientRect().bottom-1}})()")
    check("제목 아래 작은 안내 문구 '이 아이템의 경매장 최저가 시세를 적어주세요.'", g['t']=='이 아이템의 경매장 최저가 시세를 적어주세요.' and g['fs']<g['hfs']*0.8 and g['below'], g)
    lay=pg.evaluate("""(()=>{const r=s=>document.querySelector(s).getBoundingClientRect(); const i=r('#rvAmt'),u=r('.rvin span'),ok=r('.rvok'),no=r('.rvno'),l=r('.rvleft');
      return {sameLine:Math.abs((i.top+i.bottom)/2-(u.top+u.bottom)/2)<4, okBelow:no.top>=i.bottom-1, okCenter:(c=>Math.abs((no.left+c.right)/2-(l.left+l.right)/2)<3)(r('.rvcancel')), noRight:ok.left>=l.right-1,
        okBg:getComputedStyle(document.querySelector('.rvok')).backgroundColor, unit:document.querySelector('.rvin span').innerText, okTxt:document.querySelector('.rvok').innerText, noTxt:document.querySelector('.rvno').innerText}})()""")
    check('레이아웃: 입력+억 메소 한 줄, 주황 기록하기+취소하기 아래 가운데, 오른쪽 아니오', lay['sameLine'] and lay['okBelow'] and lay['okCenter'] and lay['noRight'] and lay['okBg']=='rgb(255, 138, 31)' and lay['unit']=='억 메소' and lay['okTxt']=='기록하기' and lay['noTxt']=='기록 없이 저장', lay)
    pg.screenshot(path=f'{SHOT}/oct12b_revmodal.png')
    pg.click('.rvok'); pg.wait_for_timeout(100)
    check('빈 값 → 오류, 창 유지', pg.locator('#revModal').count()==1 and '금액' in pg.inner_text('#rvErr'))
    pg.fill('#rvAmt','2.5'); pg.click('.rvok'); pg.wait_for_timeout(300)
    r=pg.evaluate(D,first)
    check('1인 2.5억 → 250,000,000 전부 저장 + 축하', r and r['m']==250000000 and r['p']==1 and pg.locator('#revModal').count()==0 and pg.locator('#congrats.show').count()==1, r)
    pg.evaluate('endCelebrate()')
    # 2) 2인 분배
    pg.click(f'[data-drop="{kitems[0]}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=s]'); pg.wait_for_selector('#revModal')
    check('분배: 창에 2인 분배 안내', '2인 분배' in pg.inner_text('#revModal'))
    pg.fill('#rvAmt','3'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    r=pg.evaluate(D,kitems[0]); check('2인 분배 3억 → ÷2 = 150,000,000', r and r['m']==150000000 and r['p']==2, r)
    pg.evaluate('endCelebrate()')
    pg.click(f'[data-drop="{kitems[0]}"]'); pg.wait_for_timeout(200)
    check('획득 취소 → 수익 기록도 삭제', pg.evaluate(D,kitems[0]) is None)
    # 3) 블빵승리 전부
    pg.click(f'[data-drop="{kitems[0]}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=w]'); pg.wait_for_selector('#revModal')
    check('블빵승리: 분배 안내 없음', '분배' not in pg.inner_text('#revModal'))
    pg.fill('#rvAmt','3'); pg.click('.rvok'); pg.wait_for_timeout(300)
    r=pg.evaluate(D,kitems[0]); check('블빵승리 3억 → 300,000,000 전부', r and r['m']==300000000 and r['p']==1, r)
    pg.evaluate('endCelebrate()')
    # 4) 블빵패배 → 창 없음
    pg.click(f'[data-drop="{kitems[1]}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=l]'); pg.wait_for_timeout(300)
    check('블빵패배 → 수익 창·축하 없음', pg.locator('#revModal').count()==0 and pg.locator('#congrats.show').count()==0 and pg.evaluate(D,kitems[1]) is None)
    # 5) 반지 꽝 → 창 없음
    pg.click(f'[data-drop="{ring}"]'); pg.wait_for_selector('#ringModal.show'); pg.click('#ringModal [data-ring=x]'); pg.wait_for_timeout(300)
    check('반지 상자 꽝 → 수익 창 없음', pg.locator('#revModal').count()==0 and pg.evaluate(D,ring) is None)
    # 6) 아니오 / Esc → 기록 없이 축하
    pg.click(f'[data-drop="{kitems[1]}"]'); pg.wait_for_timeout(200)  # 패배 취소
    pg.click(f'[data-drop="{kitems[1]}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=s]'); pg.wait_for_selector('#revModal'); pg.click('.rvno'); pg.wait_for_timeout(300)
    check('아니오 → 기록 없이 축하', pg.evaluate(D,kitems[1]) is None and pg.locator('#congrats.show').count()==1 and pg.evaluate(f"S.characters[0].drops['{kitems[1]}']===1"))
    pg.evaluate('endCelebrate()')
    if len(kitems)>2:
        pg.click(f'[data-drop="{kitems[2]}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=s]'); pg.wait_for_selector('#revModal'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        check('Esc → 기록 없이 축하', pg.evaluate(D,kitems[2]) is None and pg.locator('#congrats.show').count()==1 and pg.locator('#revModal').count()==0)
        pg.evaluate('endCelebrate()')
    # 저장 후 이번 주 수익 분홍 줄
    pg.click('#pendSave'); pg.wait_for_timeout(400)
    st=pg.evaluate("""(()=>{const e=[...document.querySelectorAll('.dlrev')]; if(!e.length) return null; const p=getComputedStyle(e[0].parentElement).fontSize, cs=getComputedStyle(e[0]);
       return {n:e.length, color:cs.color, fs:parseFloat(cs.fontSize), pfs:parseFloat(p), txt:e.map(x=>x.innerText), below:e[0].getBoundingClientRect().top>=e[0].parentElement.firstElementChild.getBoundingClientRect().bottom-1}})()""")
    check('이번 주 수익: 아이템 아래 분홍(#ff4fa3) 금액, 1pt 작게', st and st['n']>=2 and st['color']=='rgb(255, 79, 163)' and abs(st['pfs']-st['fs']-4/3)<0.15 and st['below'], st)
    pg.evaluate("document.querySelector('.dlrev')?.closest('.card,section,aside')?.scrollIntoView()"); pg.wait_for_timeout(200)
    pg.screenshot(path=f'{SHOT}/oct12b_revpink.png')
    # 득템 분석: 판매 수익 카드
    pg.click('[data-tab=loot]'); pg.wait_for_selector('#salesCard')
    sc=pg.inner_text('#salesCard'); tot=pg.evaluate("totalData().sales"); s=sum(v['m'] for v in tot.values())
    check('득템 분석: 아이템 판매 수익 카드 (합계 5.5억, 항목별)', '아이템 판매 누적 수익' in sc and s==550000000 and pg.locator('#salesCard .slist > *').count()==2, (sc,tot))
    pg.locator('#salesCard').screenshot(path=f'{SHOT}/oct12b_salescard.png')
    # 동기화 필드 / 기록 이전
    check('동기화: drev 는 S 에 저장되어 contentSig 에 포함', pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0].drev!=null"))
    ws=pg.evaluate("weekSummary(S.period.week).perChar"); revs=[pc.get('revs') for pc in ws if pc.get('revs')]
    check('주간 기록(perChar.revs)에 남음', revs and sum(v['m'] for v in revs[0].values())==550000000, revs)
    # 라이트 테마 + 모바일 화면
    pg.evaluate("render()")  # b67: 라이트 테마 없음 (다크 전용)
    pg.wait_for_timeout(600); pg.click('[data-tab=boss]'); pg.wait_for_timeout(300)
    pg.evaluate(f"(()=>{{const c=S.characters[0],b=findBoss('kaling'); askRev(c,b,'{kitems[0]}','{kitems[0].split('|')[1]}',null)}})()"); pg.wait_for_selector('#revModal')
    pg.screenshot(path=f'{SHOT}/oct12b_revmodal_light.png'); pg.click('.rvno')
    m=b.new_page(viewport={'width':390,'height':844},locale='ko-KR'); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); m.reload(); m.wait_for_timeout(800)
    m.evaluate(f"(()=>{{const c=S.characters[0],b=findBoss('kaling'); askRev(c,b,'{kitems[0]}','{kitems[0].split('|')[1]}',null)}})()"); m.wait_for_selector('#revModal')
    mb=m.evaluate("(()=>{const r=document.querySelector('.rvbox').getBoundingClientRect();return [r.left,r.right,innerWidth, document.documentElement.scrollWidth]})()")
    check('모바일: 창이 화면 안', mb[0]>=0 and mb[1]<=mb[2] and mb[3]<=mb[2], mb)
    m.screenshot(path=f'{SHOT}/oct12b_revmodal_mobile.png')
    b.close()
finally:
    srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
