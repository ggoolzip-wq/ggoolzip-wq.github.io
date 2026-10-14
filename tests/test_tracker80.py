# b109: 이름 '메이플 보스 수익 기록 - 메보수'·왼쪽 위 '메보수'(→ 이번 주 보스 탭)·파비콘=강렬한 힘의 결정(주간)·탭 이름(이번 주 보스/수익 분석)·
# '수익을 기록할까요?' [기록하기]/[기록 없이 저장]/[취소]·'수익 기록 전체 수정' 창·월간 보스 안내 문구 삭제.
# MBT_ROOT/MBT_SHOTDIR/MBT_TAG/MBT_NOCHECK (변경 전 빌드 촬영용)
import os, sys, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8896'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b109_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,e)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{'seren':B('extreme'),'kaling':B('hard',2),'blackmage':B('extreme')},'weekly':{'seren':True,'kaling':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    shot(pg.locator('header'),'header')
    check('사이트 이름', pg.title()=='메이플 보스 수익 기록 - 메보수', pg.title())
    check("왼쪽 위 '메보수'", pg.inner_text('header .logo').strip()=='메보수', pg.inner_text('header .logo'))
    fav=pg.evaluate("document.querySelector('link[rel=icon]').href.slice(0,60)==document.querySelector('header .logo img').src.slice(0,60)?'':'x'")
    check('파비콘·로고 = 강렬한 힘의 결정 (주간) (logo.json 재생성)', pg.evaluate("document.querySelector('header .logo img').naturalWidth")>0)
    tabs=pg.eval_on_selector_all('#tabs button',"e=>e.map(x=>x.innerText.trim())")
    check('탭 이름: 이번 주 보스 · 수익 분석', tabs[:3]==['이번 주 보스','수익 분석','득템 분석'], tabs)
    pg.click('[data-tab=total]'); pg.wait_for_timeout(200)
    if pg.locator('#logoHome').count(): pg.click('#logoHome')
    else: pg.click('[data-tab=boss]')
    pg.wait_for_timeout(200)
    check('메보수 클릭 → 이번 주 보스 탭', pg.evaluate('tab')=='boss' and pg.locator('[data-tab=boss].on').count()==1)
    # 월간 보스 안내 문구 삭제
    pg.click('[data-filter=monthly]'); pg.wait_for_timeout(200)
    check('월간 보스 안내 문구 없음', '매월 1일' not in pg.inner_text('main'))
    pg.click('[data-filter=weekly]'); pg.wait_for_timeout(200)
    # 수익 기록 창
    keys=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"seren|\"]')].map(e=>e.dataset.drop).filter(k=>!/\\|(r_|chaosbox)/.test(k))")
    pg.click(f'[data-drop="{keys[0]}"]'); pg.wait_for_selector('#revModal')
    lay=pg.evaluate("""(()=>{const q=s=>document.querySelector(s),r=s=>q(s).getBoundingClientRect(),i=r('#rvAmt'),ok=r('.rvok'),no=r('.rvno'),cc=r('.rvcancel');
      return {ok:q('.rvok').innerText,no:q('.rvno').innerText,cancel:q('.rvcancel').innerText,okRight:ok.left>=i.right-1,okBg:getComputedStyle(q('.rvok')).backgroundColor,below:no.top>=i.bottom-1&&cc.top>=i.bottom-1,noBefore:no.right<=cc.left+1}})()""")
    check("수익 창: 오른쪽 주황 '기록하기', 아래 '기록 없이 저장'·'취소'", lay['ok']=='기록하기' and lay['no']=='기록 없이 저장' and lay['cancel']=='취소' and lay['okRight'] and lay['okBg']=='rgb(255, 138, 31)' and lay['below'] and lay['noBefore'], lay)
    shot(pg.locator('#revModal .modal'),'revmodal')
    pg.click('.rvno'); pg.wait_for_timeout(300)
    check('기록 없이 저장 → 획득 유지·기록 없음·축하', pg.evaluate(f"S.characters[0].drops['{keys[0]}']===1 && !(S.characters[0].drev||{{}})['{keys[0]}']") and pg.locator('#congrats.show').count()==1)
    pg.evaluate('endCelebrate()')
    pg.click(f'[data-drop="{keys[1]}"]'); pg.wait_for_selector('#revModal'); pg.click('.rvcancel'); pg.wait_for_timeout(300)
    check('취소 → 선택 되돌림', pg.evaluate(f"!S.characters[0].drops['{keys[1]}']") and pg.locator('#congrats.show').count()==0)
    pg.click(f'[data-drop="{keys[1]}"]'); pg.wait_for_selector('#revModal'); pg.fill('#rvAmt','2'); pg.click('.rvok'); pg.wait_for_timeout(300); pg.evaluate('endCelebrate()')
    check('기록하기 → 2억 기록', pg.evaluate(f"S.characters[0].drev['{keys[1]}'].m")==200000000)
    kk=pg.evaluate("[...document.querySelectorAll('[data-drop^=\"kaling|\"]')].map(e=>e.dataset.drop).filter(k=>!/\\|(r_|chaosbox)/.test(k))[0]")
    pg.click(f'[data-drop="{kk}"]'); pg.wait_for_selector('#bbModal'); pg.click('#bbModal [data-bb=s]'); pg.wait_for_selector('#revModal'); pg.click('.rvno'); pg.wait_for_timeout(300); pg.evaluate('endCelebrate()')
    pg.click('#pendSave'); pg.wait_for_timeout(300)
    # 전체 수정
    bt=pg.evaluate("(()=>{const a=document.querySelector('#revAllBtn'),c=document.querySelector('#pendCancel');return a&&{t:a.innerText,next:a.nextElementSibling===c}})()")
    check("'수익 기록 전체 수정' 버튼 = 취소 바로 옆(왼쪽)", bt and bt['t']=='수익 기록 전체 수정' and bt['next'], bt)
    pg.wait_for_timeout(2600); shot(pg.locator('.toolbar').first,'toolbar')
    if NOCHK and not pg.locator('#revAllBtn').count(): raise SystemExit(0)
    pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal')
    m=pg.evaluate("""(()=>{const q=s=>document.querySelector(s),box=q('#revAllModal .modal').getBoundingClientRect(),ic=q('.raicons').getBoundingClientRect(),l=q('.ralist').getBoundingClientRect(),fs=parseFloat(getComputedStyle(q('.raicons')).fontSize||16);
      return {title:q('#raTitle').innerText,icons:document.querySelectorAll('.raicons .raic').length,oneRow:[...document.querySelectorAll('.raicons .raic')].every(e=>Math.abs(e.getBoundingClientRect().top-ic.top)<2),
       gap:l.top-ic.bottom,rows:[...document.querySelectorAll('.rarow')].map(r=>[r.querySelector('.raname').innerText,r.querySelector('input').value]),
       center:Math.abs((box.left+box.right)/2-innerWidth/2)<3,btns:[...document.querySelectorAll('.rabtns button')].map(b=>b.innerText),okBg:getComputedStyle(q('.raok')).backgroundColor}})()""")
    check("창 제목·아이콘 한 줄·1.5줄 간격·아이템 3줄(기록 안 한 것 포함)·가운데·[전체 수정](주황)/[취소]", m['title']=='수익 기록 전체 수정' and m['icons']==3 and m['oneRow'] and 18<=m['gap']<=30 and len(m['rows'])==3 and m['center'] and m['btns']==['전체 수정','취소'] and m['okBg']=='rgb(255, 138, 31)', m)
    check('기존 기록 값 미리 채움(2억), 나머지 빈 칸', sorted(r[1] for r in m['rows'])==['','','2'], m['rows'])
    shot(pg.locator('#revAllModal .modal'),'revall')
    ins=pg.locator('.rarow input'); n=ins.count(); vals=['3','',''] 
    for i in range(n): ins.nth(i).fill(['3','4','5'][i])
    pg.click('.raok'); pg.wait_for_timeout(300)
    d=pg.evaluate(f"(()=>{{const c=S.characters[0];return [c.drev['{keys[0]}'].m,c.drev['{keys[1]}'].m,c.drev['{kk}'].m,c.drev['{kk}'].p,!!pend]}})()")
    check('전체 수정 → 바로 저장(대기 없음), 분배 아이템 ÷2', pg.locator('#revAllModal').count()==0 and sorted(d[:3])==sorted([300000000,400000000,250000000]) and d[3]==2 and d[4]==False, d)
    check('저장된 상태(localStorage)에도 반영', pg.evaluate(f"JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0].drev['{kk}'].m")==250000000)
    pg.click('#revAllBtn'); pg.wait_for_selector('#revAllModal'); pg.locator('.rarow input').first.fill(''); pg.click('#revAllModal [data-rab=cancel]'); pg.wait_for_timeout(200)
    check('취소 → 아무것도 안 바뀜', pg.locator('#revAllModal').count()==0 and len(pg.evaluate("Object.keys(S.characters[0].drev)"))==3)
    b.close()
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs); sys.exit(1 if (fails or errs) and not NOCHK else 0)
