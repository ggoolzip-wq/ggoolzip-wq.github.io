# b60: 메소 단위, 홍옥 비활성, 이번 주 주간 보스 수익(+검마), 월간 클리어 날짜, 탭 이름/분리, 누적 수입, 득템 분석
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8844/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8844','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
ch={'id':'c0','name':'캐릭00','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'',
    'bosses':{'kaling':{'enabled':True,'diff':'hard','party':1},'blackmage':{'enabled':True,'diff':'hard','party':1},'lotus':{'enabled':True,'diff':'normal','party':1}},'weekly':{'kaling':True},'monthly':{},'auto':{},'sync':{},'drops':{}}
per=[{'id':'c0','name':'캐릭00','meso':100000000,'count':2,'bosses':['카링(하드)'],'bvals':[100000000],
      'items':{'kaling|g_faith':1,'kaling|se1':1,'kaling|r_black':1,'kaling|r_white':1,'lotus|r_green':1,'lotus|r_red':1,'kaling|g_life#2w':1,'kaling|oath#2l':1},
      'outcomes':{'kaling|r_black':['r4'],'kaling|r_white':['x'],'lotus|r_green':['x'],'lotus|r_red':['c4']}}]
hist=[{'week':'2026-10-01','weeklyOnly':True,'total':100000000,'cleared':1,'perChar':per}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':[ch],'history':hist,'monthHistory':[],'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    def load(tab,st=ST):
        pg.goto(URL); pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab',t)}",[st,tab]); pg.reload(); pg.wait_for_timeout(900)
    load('boss')
    m=pg.evaluate("[meso(0),meso(5000),meso(150000000),meso(60000)]")
    check('A: meso() 단위 메소', m==['0 메소','5,000 메소','1억 5,000만 메소','6만 메소'], m)
    pr=pg.evaluate("[...document.querySelectorAll('.pricecard .pc-row b')].every(e=>/메소/.test(e.innerText))")
    check('A: 가격 카드 금액 전부 메소', pr)
    pg.evaluate("()=>{S.characters[0].bosses.lotus.diff='normal';render()}")
    off=pg.evaluate("(()=>{const e=Object.entries(RING_DROPS.r_red)[0],b=findBoss(e[0]),d=e[1][0];return [dropsFor(b,d).includes('r_red'),dropsOff(b,d).includes('r_red'),missingItems(totalData()).some(o=>o.k==='r_red'),b.id+d]})()")
    check('B: 홍옥 반지 상자 회색 비활성(맨 끝) + 못 가진 목록 제외', off[0]==False and off[1]==True and off[2]==False, off)
    # C/D
    pg.evaluate("()=>{const c=S.characters[0];c.monthly.blackmage=S.period.week;c.mdate={blackmage:'2026-10-08'};save();render()}"); pg.wait_for_timeout(300)
    st=pg.inner_text('.stats.s3'); r=pg.evaluate("[cRev(S.characters[0]).meso,price(findBoss('blackmage'),'hard'),meso(cRev(S.characters[0]).meso+price(findBoss('blackmage'),'hard'))]")
    check('C: (이 캐릭터) 제거 + 주간 수익에 이번 주 검마 합산', '(이 캐릭터)' not in st and r[2] in st, (st[:120],r))
    check('D: 이번 달 월간 보스 옆 (10/8)', '이번 달 월간 보스 (10/8)' in st.replace('\n',' '), st[:200])
    pg.evaluate("()=>{const c=S.characters[0];delete c.mdate;save();render()}"); pg.wait_for_timeout(200)
    check('D: 날짜 없는 기존 기록은 날짜 표시 안 함', '(10/8)' not in pg.inner_text('.stats.s3') and pg.evaluate("S.characters[0].mdate!==undefined||true"))
    pg.evaluate("()=>{const c=S.characters[0];c.monthly={};c.mdate={};save();render()}")
    pg.evaluate("()=>{const e=document.createElement('button');e.dataset.check='blackmage';e.style.display='none';document.body.appendChild(e);e.click();e.remove()}"); pg.wait_for_timeout(300)
    md=pg.evaluate("S.characters[0].mdate&&S.characters[0].mdate.blackmage")
    import re
    check('D: 체크하면 오늘(KST) 날짜 저장', bool(md) and re.match(r'\d{4}-\d\d-\d\d$',md), md)
    # E/F/G
    names=pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.innerText)")
    check('E: 탭 이름 결정석 분석 · 득템 분석(바로 옆)', names[:3]==['보스 현황','결정석 분석','득템 분석'], names)
    load('total')
    hs=[h.replace('\n',' ').strip() for h in pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.innerText.trim())')]
    check('F/G: 결정석 분석 카드 구성', hs[0].startswith('누적 수입') and any('주별 누적 결정석 메소'==h.replace('📈','').strip() for h in hs) and any(h.endswith('메소왕') for h in hs) and any(h.endswith('결정석 보스왕') for h in hs) and any('빠뜨린' in h for h in hs) and any('전체 주 목록' in h for h in hs) and not any(('득템왕' in h or '에픽빔왕' in h or '시드링' in h or '블빵' in h or '가지지' in h) for h in hs), hs)
    ks=pg.eval_on_selector_all('#view .card:first-child .stat .k','e=>e.map(x=>x.innerText.trim())')
    check('F: 3칸(총 수익/주보 누적 메소량/검마 누적 메소량), 획득 아이템 누적 없음', len(ks)==3 and ks[1]=='주보 누적 메소량' and ks[2]=='검마 누적 메소량' and '획득 아이템 누적' not in pg.inner_text('#view'), ks)
    # H
    load('loot')
    hs=[h.replace('\n',' ').strip() for h in pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.innerText.trim())')]
    check('H: 득템 분석 구성(누적 득템 맨 위 + 옮겨진 카드)', hs[0]=='누적 득템' and any(h.endswith('득템왕') for h in hs) and any('에픽빔왕' in h for h in hs) and any('시드링' in h for h in hs) and any('블빵 승률' in h for h in hs) and any('가지지' in h for h in hs) and not any('메소왕' in h for h in hs), hs)
    L=pg.evaluate("(()=>{const g=id=>document.querySelector(id).innerText.replace(/\\s+/g,' ');return [g('#ltTotal'),g('#ltRing'),g('#ltBbang'),document.querySelectorAll('#lootTop .stat .hbi img, #lootTop .stat .hbi .ric, #lootTop .stat .blk .ric').length]})()")
    # 총 득템: kaling g_faith,se1,r_black,r_white,g_life#2w = 5 (녹옥·홍옥 제외, 블빵패배 oath 제외)
    check('H: 총 득템 5개 + 제외 문구', '5개' in L[0] and '녹옥, 홍옥 반지 상자 제외' in L[0], L)
    check('H: 반상 누적 2회(흑옥·백옥) + 타율 + 제외 문구', '2회' in L[1] and '리4컨4 타율' in L[1] and '녹옥, 홍옥 반지 상자 제외' in L[1], L[1])
    rt=pg.evaluate("(()=>{const t=document.querySelector('#ltRing').innerText;const m=/타율 ([\\d.]+)%/.exec(t);return m?+m[1]:null})()")
    # r_black lv4 .2*12.5%=2.5% r4 → expected r4 .025, c4 .025; r_white 5%+5% → total .125; actual r4 1 → 1/0.15
    check('H: 타율 = 실제 ÷ 기댓값', rt is not None and abs(rt-round(100/0.15,1))<0.2, rt)
    check('H: 누적 블빵 승리 횟수 1회만', '1회' in L[2] and L[2].replace('누적 블빵 승리 횟수','').strip()=='1회', L[2])
    check('H: 3칸 아이콘', L[3]>=3, L)
    check('JS 오류 없음', not errs, errs)
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
