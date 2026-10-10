# b46: 빠뜨린 보스메소(주간/월간) 기록·백필·중복 없음 · 아이템 항목 줄바꿈 단위 · 일퀘 탭 삭제 · 넓힌 오른쪽 열/결정석 글자 키움
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8835/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8835','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
def ch(i,n,weekly,monthly,drops={},out={}):
    return {'id':f'c{i}','name':n,'level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'',
      'bosses':{'seren':B('extreme'),'kalos':B('chaos',2),'blackmage':B('extreme')},'weekly':weekly,'monthly':monthly,'auto':{},'drops':drops,'dropOut':out,'sync':{}}
# 고정 시계: 2026-10-15 10:00 KST (목요일 초기화 직후)
CLOCK="""(()=>{const T=Date.parse('2026-10-15T10:00:00+09:00');const R=Date;const d=T-R.now();class D extends R{constructor(...a){a.length?super(...a):super(R.now()+d)} static now(){return R.now()+d}};window.Date=D;})()"""
chars=[ch(0,'zetking',{'seren':True},{},{'kalos|r_white':1},{'kalos|r_white':['x']}), ch(1,'다잡음',{'seren':True,'kalos':True},{'blackmage':True})]
hist=[{'week':'2026-09-24','weeklyOnly':True,'total':0,'cleared':1,'perChar':[{'id':'c0','name':'zetking','count':1,'bosses':['선택받은 세렌(익스트림)']},{'id':'c1','name':'다잡음','count':2,'bosses':['선택받은 세렌(익스트림)','감시자 칼로스(카오스)/2인']}]}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':hist,'monthHistory':[],'worldOrder':[],'startWeek':'2026-09-24',
    'period':{'week':'2026-10-08','day':'2026-10-14','month':'2026-09'},'settings':{'accounts':[]},'dq':{'off':{}}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(CLOCK); pg.goto(URL)
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','daily')}",ST); pg.reload(); pg.wait_for_timeout(900)
    check('일퀘 탭 없음 + 저장된 daily 탭 → 보스 현황', pg.locator('[data-tab=daily]').count()==0 and pg.evaluate('tab')=='boss' and '일퀘' not in pg.inner_text('header'))
    W=pg.evaluate('S.missW'); M=pg.evaluate('S.missM')
    w=[x for x in W if x['week']=='2026-10-08']
    check('지난 주(10/8~) 기록: zetking 1개(칼로스 카오스 2인), 다잡음 없음, 날짜 2026.10.15', len(w)==1 and w[0]['date']=='2026.10.15' and w[0]['n']==1 and [x['name'] for x in w[0]['list']]==['zetking'] and w[0]['meso']>0, w)
    bf=[x for x in W if x['week']=='2026-09-24']
    check('안 열었던 주는 저장된 주간 기록으로 백필 (근사)', len(bf)==1 and bf[0].get('approx') and bf[0]['date']=='2026.10.01' and bf[0]['list'][0]['name']=='zetking' and len(bf[0]['list'])==1, bf)
    check('월간(9월) 기록: 검마 못 잡은 zetking만, 날짜 2026.10.01', len(M)==1 and M[0]['month']=='2026-09' and M[0]['date']=='2026.10.01' and [x['name'] for x in M[0]['list']]==['zetking'], M)
    check('저장됨(localStorage)', len(json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))['missW'])==2)
    pg.reload(); pg.wait_for_timeout(700); pg.evaluate('checkResets();checkResets()')
    check('중복 없음 (기간당 1개)', len(pg.evaluate('S.missW'))==2 and len(pg.evaluate('S.missM'))==1)
    # 아이템 항목: 줄 중간에서 끊기지 않음 (이번 주 수익 패널) — 이번 주에도 획득 기록이 있게
    pg.evaluate("S.characters[0].drops={'kalos|r_white':1};S.characters[0].dropOut={'kalos|r_white':['x']};save();render()")
    pg.wait_for_timeout(300)
    for vw,vh in ((1920,1080),(1280,800),(1200,800)):
      pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(400)
      r=pg.evaluate("""(()=>{const l=[...document.querySelectorAll('.rcol .dl')];return l.map(e=>{const rs=[...e.getClientRects()];const ts=[...e.querySelectorAll('img,b,span')].map(x=>Math.round(x.getBoundingClientRect().top+x.getBoundingClientRect().height/2));return {t:e.innerText.replace(/\\s+/g,' '),rows:new Set(ts.map(t=>Math.round(t/6))).size,h:Math.round(e.getBoundingClientRect().height)}})})()""")
      check(f'{vw}: 반지 상자 항목이 한 줄 덩어리 (꽝이 다음 줄로 안 떨어짐)', r and all(x['h']<=26 for x in r), r)
      lay=pg.evaluate("(()=>{const m=document.querySelector('main').getBoundingClientRect();const cut=[...document.querySelectorAll('.pricecard .pc-nm')].filter(n=>n.scrollWidth>n.clientWidth+0.5).length;const fs=parseFloat(getComputedStyle(document.querySelector('.pc-row')).fontSize);return {l:Math.round(m.left),r:Math.round(innerWidth-m.right),cut,fs,rcol:document.querySelector('.rcol').getBoundingClientRect().width,hs:document.documentElement.scrollWidth>innerWidth}})()")
      check(f'{vw}: 결정석 가격 안 잘림, 글자 키움, 가운데, 가로 스크롤 없음', lay['cut']==0 and abs(lay['l']-lay['r'])<=1 and not lay['hs'] and (vw<1300 or lay['fs']>=12), lay)
      if vw in (1920,1280): pg.screenshot(path=f'/workspace/shots/b46_layout_{vw}.png')
      if vw==1920: pg.locator('.revpanel').screenshot(path='/workspace/shots/b46_items.png')
    pg.set_viewport_size({'width':1920,'height':1080})
    pg.click('[data-tab=total]'); pg.wait_for_timeout(500)
    hs=pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.innerText.trim())')
    iw=next(i for i,h in enumerate(hs) if '빠뜨린 보스메소는? (주간 Ver)' in h); it=next(i for i,h in enumerate(hs) if '총 아이템 획득량' in h); il=next(i for i,h in enumerate(hs) if '전체 주 목록' in h)
    check('순서: 총 아이템 획득량 < 주간 Ver < 월간 Ver < 전체 주 목록', it<iw<il and '(월간 Ver)' in hs[iw+1] and pg.locator('.missic').count()==2, hs)
    pts=pg.locator('.misschart').first.locator('.mpt'); check('주간 그래프 점 2개 + 날짜 라벨', pts.count()==2 and '2026.10.15' in pg.inner_text('.misschart'))
    pts.last.locator('circle').nth(1).hover(force=True); pg.wait_for_timeout(300); tip=pg.inner_text('#mbtTip')
    check('툴팁: 닉네임·개수·손해 메소·합계', 'zetking: 1개' in tip and '합계: 1개' in tip, tip)
    pg.locator('.misschart').first.scroll_into_view_if_needed(); pg.screenshot(path='/workspace/shots/b46_miss.png')
    pg.evaluate("S.missW=[{week:'2026-10-08',date:'2026.10.15',n:0,meso:0,list:[]}];S.missM=[];render()"); pg.wait_for_timeout(300)
    pg.locator('.misschart .mpt circle').nth(1).hover(force=True); pg.wait_for_timeout(300)
    check('모두 잡으면 손해 없음 / 비면 아직 기록이 없어요', '손해 없음' in pg.inner_text('#mbtTip') and '아직 기록이 없어요' in pg.inner_text('#view'))
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
