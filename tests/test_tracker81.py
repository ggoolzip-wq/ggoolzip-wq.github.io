# b110: 아이템 판매값을 수익에 더함 — 판 캐릭터에만, 준 보스 종류대로(주간 보스 → 주간, 검은 마법사 → 월간). 이번 주 수익 두 줄, 캐릭터 정보,
# 누적 수입(총/주보/검마), 주간 메소 그래프, 메소왕(누적 주간/월간 메소량), 보스 메소왕(누적 결정석·누적 아이템 판매값·누적 메소량), 전체 주 목록, 문구 2개 삭제.
# MBT_ROOT/MBT_SHOTDIR/MBT_TAG/MBT_NOCHECK
import os, sys, time, subprocess, re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8897'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b110_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,e)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
def ch(i,n,**k): return {'id':i,'name':n,'level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i=='c1','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{},**k}
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]},
    'characters':[ch('c1','판매왕',bosses={'lucid':B('hard')},weekly={'lucid':True},drops={'lucid|mitra':1},drev={'lucid|mitra':{'m':100000000,'a':1,'p':1,'i':'mitra'}}),
                  ch('c2','검마잡이',bosses={'blackmage':B('hard')})]}
SETUP="""()=>{ const cur=S.period.week, prev=dayId(weekStartMs(Date.parse(cur+'T12:00:00+09:00')-7*864e5)), mon=S.period.month;
  S.startWeek=prev;
  S.history=[{week:prev,weeklyOnly:true,total:300000000,cleared:2,crystals:2,items:1,perChar:[
    {id:'c1',name:'판매왕',meso:100000000,count:1,bosses:['루시드(하드)'],bvals:[100000000],items:{'lucid|eye':1},outcomes:{},revs:{'lucid|eye':{m:50000000,a:0.5,p:1,i:'eye'}}},
    {id:'c2',name:'검마잡이',meso:200000000,count:1,bosses:['루시드(하드)'],bvals:[200000000],items:{},outcomes:{}}]}];
  S.monthHistory=[{month:'2026-09',total:500000000,cleared:1,perChar:[{id:'c1',name:'판매왕',meso:500000000,bosses:['검은 마법사(하드)'],bvals:[500000000],mweeks:[prev],items:{'blackmage|genesis':1},outcomes:{},revs:{'blackmage|genesis':{m:3000000000,a:30,p:1,i:'genesis'}}}]}];
  const c2=S.characters[1]; c2.monthly={blackmage:cur}; c2.mdrops={'blackmage|genesis':1}; c2.mdrev={'blackmage|genesis':{m:200000000,a:2,p:1,i:'genesis'}};
  save(); render(); return {cur,prev}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    W=pg.evaluate(SETUP); pg.wait_for_timeout(300)
    if NOCHK:  # 변경 전 빌드 촬영만
        shot(pg.locator('.revpanel'),'revpanel'); pg.click('[data-tab=total]'); pg.wait_for_timeout(400)
        shot(pg.locator('#view .card').first,'total_top'); shot(pg.locator('#mesoKing'),'mesoking'); shot(pg.locator('#bossKing'),'bossking'); raise SystemExit(0)
    lc=pg.evaluate("price(findBoss('lucid'),'hard')"); bm=pg.evaluate("price(findBoss('blackmage'),'hard')")
    # 이번 주 수익
    cry=lc+bm; sale=100000000+200000000
    rt=pg.inner_text('.rp-total').replace('\n',''); l1=pg.inner_text('.rp-cry'); l2=pg.inner_text('.rp-sale')
    check('이번 주 수익 = 결정석 합 + 아이템 판매값', rt.startswith(f"{(cry+sale)/1e8:.2f}억"), (rt,cry+sale))
    check("b176 결정석 줄: 주보 결정석 N개 금액 / 검마 결정석 M개 금액 따로", re.sub(r'\s+',' ',l1).strip()==f"주보 결정석 1개 +{lc:,}" and re.sub(r'\s+',' ',pg.inner_text('.rp-cm')).strip()==f"검마 결정석 1개 {bm:,}" and pg.locator('.rp-cry img').count()==2, l1)
    check("둘째 줄 (b121) '이번주 획득 아이템 N개 … 판매금액(오른쪽)'", re.sub(r'\s+',' ',l2).strip()==f"이번주 획득 아이템 1개 +{sale:,}", l2)
    pcs=pg.evaluate("[...document.querySelectorAll('.rp-char')].map(r=>[r.dataset.id,r.querySelector('b').innerText])")
    check('캐릭터별 메소에 그 캐릭터 판매값만', dict(pcs)=={'c1':pg.evaluate(f"meso({lc+100000000})"),'c2':pg.evaluate(f"meso({bm+200000000})")}, pcs)
    ci=pg.evaluate("(()=>{const e=[...document.querySelectorAll('.stat')].find(s=>s.querySelector('.k')?.innerText.trim()==='이번 주 주간 보스 수익');return e&&e.querySelector('.v').innerText})()")
    check('캐릭터 정보 이번 주 주간 보스 수익 + 판매값', ci==pg.evaluate(f"meso({lc+100000000})"), ci)
    shot(pg.locator('.revpanel'),'revpanel')
    # 수익 분석
    pg.click('[data-tab=total]'); pg.wait_for_timeout(400)
    T=pg.evaluate("(()=>{const T=totalData();return {w:T.wTotal,m:T.mTotal,g:T.grand}})()")
    ew=300000000+50000000+lc+100000000; em=500000000+3000000000+bm+200000000
    check('주보 누적 = 주간 결정석 + 주간 보스 아이템(검마 아이템 제외)', T['w']==ew, (T,ew))
    check('검마 누적 = 월간 결정석 + 검은 마법사 아이템만', T['m']==em, (T,em))
    check('총 수익 = 둘의 합', T['g']==ew+em, T)
    main=pg.inner_text('#view')
    check("'수익은 결정석 판매 금액만…' 문구 없음", '결정석 판매 금액만' not in main)
    check("맨 아래 '결정석 가격은 공식 패치 노트 기준으로 자동 갱신됩니다.' 없음, NEXON 표기 유지", '자동 갱신됩니다' not in pg.inner_text('.foot') and 'NEXON Open API' in pg.inner_text('.foot'), pg.inner_text('.foot'))
    hs=pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.innerText.trim())')
    check("그래프 제목 '주간 메소 그래프'", any(h.endswith('주간 메소 그래프') for h in hs), hs)
    tips=pg.evaluate("[...document.querySelectorAll('.linechart .lpt')].map(g=>g.dataset.tip)")
    check('주간 메소 그래프: 지난 주 = 주간(3.5억) + 그 주에 잡은 검마 결정석·아이템(35억)', len(tips)==2 and pg.evaluate(f"meso({350000000+3500000000})") in tips[0], tips)
    mk=pg.evaluate("[...document.querySelectorAll('#mesoKing th')].map(x=>x.innerText)"); mr=pg.evaluate("[...document.querySelectorAll('#mesoKing tbody tr')].map(r=>[...r.cells].map(c=>c.innerText.trim()))")
    check("메소왕 열 '누적 주간 메소량'·'누적 월간 메소량'", mk==['순위','캐릭터','누적 주간 메소량','누적 월간 메소량','누적 합계'], mk)
    c1w=100000000+50000000+lc+100000000; c1m=500000000+3000000000
    check('메소왕: 판 캐릭터에만 더함', mr[0][1].endswith('판매왕') and mr[0][2]==pg.evaluate(f"meso({c1w})") and mr[0][3]==pg.evaluate(f"meso({c1m})"), mr)
    bh=pg.evaluate("[...document.querySelectorAll('#bossKing th')].map(x=>x.innerText)"); br=pg.evaluate("[...document.querySelectorAll('#bossKing tbody tr')].map(r=>[...r.cells].map(c=>c.innerText.trim()))")
    check("보스 메소왕 제목·열 순서", '보스 메소왕' in pg.inner_text('#bossKing h2') and bh==['순위','보스','처치 당한 횟수','누적 결정석','누적 아이템 판매값','누적 메소량'], bh)
    rows={r[1]:r for r in br}
    bmr=next((r for k,r in rows.items() if k.startswith('검은 마법사')),None); lr=next((r for k,r in rows.items() if k.startswith('루시드')),None)
    M=lambda v: pg.evaluate(f"meso({v})")
    check('검은 마법사 행: 결정석·아이템·합 (아이템은 그 보스 것만)', bmr and bmr[3]==M(500000000+bm) and bmr[4]==M(3000000000+200000000) and bmr[5]==M(500000000+bm+3200000000), bmr)
    check('루시드 행: 결정석·아이템(눈·미트라)·합', lr and lr[3]==M(300000000+lc) and lr[4]==M(150000000) and lr[5]==M(300000000+lc+150000000), lr)
    check('보스 메소왕 정렬 = 누적 메소량 내림차순', br[0][1].startswith('검은 마법사'), br)
    wl=pg.evaluate("[...document.querySelectorAll('#view table')].pop().innerText")
    check('전체 주 목록 주간 수익에 아이템 판매값 + 그 주 검마 결정석·판매(b115)', M(lc+100000000+bm+200000000) in wl and M(350000000+500000000+3000000000) in wl, wl[:300])
    shot(pg.locator('#view .card').first,'total_top'); shot(pg.locator('#mesoKing'),'mesoking'); shot(pg.locator('#bossKing'),'bossking')
    b.close()
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs); sys.exit(1 if (fails or errs) and not NOCHK else 0)
