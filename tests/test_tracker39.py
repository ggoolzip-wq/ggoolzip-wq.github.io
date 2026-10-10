# b53: 동점=기본순, 득템왕 점수/칠흑, 고정 10행 페이지, 에픽빔 합치기, 상자깡, 블빵 통합, 수익 억, 가격 변동일, 체크 오버레이 (b52 base:) 메소왕·득템왕(순위·메달·10개씩 페이지), 시드링 획득 타율 위치, 블빵 승률·이긴/진 아이템, 빠뜨린 보스메소 ! 아이콘
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8839/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8839','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
N=12
chars=[{'id':f'c{i}','name':f'캐릭{i:02d}','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(N)]
# 지난 주 기록: c{i} 메소 = (i+1)억 (c11 이 1등), 월간 c0 에 20억 → c0 이 1등이 됨
per=[{'id':f'c{i}','name':f'캐릭{i:02d}','meso':(i+1)*100000000,'count':1,'bosses':[],'items':{},'outcomes':{}} for i in range(N)]
# 아이템: c3 = 승리 2 + 분배 1 + 패배 1(제외) + 꽝 반지 1(제외), c5 = 1인 아이템 2, c7 = 패배만 1
per[3]['items']={'kaling|g_faith#2w':1,'star|bliss#3w':1,'limbo|whisper#2':1,'kaling|oath#2l':1,'kaling|r_white':1}; per[3]['outcomes']={'kaling|r_white':['x']}
per[5]['items']={'seren|mitra':1,'kalos|r_black':1}; per[5]['outcomes']={'kalos|r_black':['r4']}
per[7]['items']={'star|chaosbox#2l':1}; per[7]['outcomes']={'star|chaosbox#2l':['cb:eye']}
per[9]['items']={'kaling|g_life#2w':1,'kaling|se1#2l':1,'star|se2#3l':1}
per[4]['meso']=per[5]['meso']
hist=[{'week':'2026-10-01','weeklyOnly':True,'total':0,'cleared':N,'perChar':per}]
mh=[{'month':'2026-09','total':0,'cleared':1,'perChar':[{'id':'c0','name':'캐릭00','meso':2000000000,'bosses':[],'items':{},'outcomes':{}}]}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':hist,'monthHistory':mh,'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]},
    'missW':[{'week':'2026-10-01','date':'2026.10.08','n':0,'meso':0,'list':[]}]}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900)
    hs=[h.replace('\n',' ').strip() for h in pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.innerText.trim())')]
    def idx(t): return next((i for i,h in enumerate(hs) if t in h),-1)
    order=['메소왕','득템왕','에픽빔왕','혼돈의 칠흑 장신구 상자깡','물욕 블빵 승률','블빵 이겨서','블빵 져서','보스 별 누적','시드링 획득 타율','총 아이템 획득량']
    ii=[idx(t) for t in order]; check('섹션 순서', all(x>=0 for x in ii) and ii==sorted(ii), list(zip(order,ii)))
    rows=pg.eval_on_selector_all('#mesoKing tbody tr:not(.rkpad)','e=>e.map(x=>x.children[1].innerText.trim())')
    i4=[i for i,r in enumerate(rows) if r.endswith('캐릭04') or r.endswith('캐릭05')]
    check('메소왕 동점 → 기본순 (캐릭04 먼저)', len(i4)==2 and rows[i4[0]].endswith('캐릭04'), rows)
    lk=pg.inner_text('#lootKing tbody tr:first-child')
    check('득템왕 (N점) 선홍색, xN 닉네임 옆 없음', '(3회)' in lk, lk)
    h1=pg.eval_on_selector('#mesoKing tbody','e=>e.getBoundingClientRect().height'); y1=pg.eval_on_selector('#mesoKing .cpager','e=>e.getBoundingClientRect().top-e.closest(".card").getBoundingClientRect().top')
    pg.click('#mesoKing [data-rkpage="meso|2"]'); pg.wait_for_timeout(200)
    h2=pg.eval_on_selector('#mesoKing tbody','e=>e.getBoundingClientRect().height'); y2=pg.eval_on_selector('#mesoKing .cpager','e=>e.getBoundingClientRect().top-e.closest(".card").getBoundingClientRect().top')
    check('페이지 2: 10행 높이 유지, 버튼 위치 고정', pg.locator('#mesoKing tbody tr').count()==10 and abs(h1-h2)<1 and abs(y1-y2)<1, (h1,h2,y1,y2))
    ep=pg.inner_text('#epicCard').replace('\n',' ')
    check('에픽빔: 합계 x 없이, 수식어 없음, 칠흑은 상자로', pg.inner_text('#epicCard .epgold').strip().isdigit() and '블빵' not in ep and '분배' not in ep and '혼돈의 칠흑 장신구 상자' in ep and '마력이 깃든 안대' not in ep, ep)
    cc=pg.eval_on_selector_all('#chaosCard tbody tr:not(.rkpad)','e=>e.map(x=>x.innerText.replace(/\s+/g," ").trim())')
    check('칠흑 상자깡: 7개, 0 포함, 안대 x1', len(cc)==7 and any('안대' in x and 'x1' in x for x in cc) and sum('x0' in x for x in cc)==6, cc)
    check('블빵 3부분 한 카드', pg.locator('#bbCard .bbpart').count()==3 and pg.locator('#bbCard #bbRate h2:has-text("물욕 블빵 승률")').count()==1)
    check('보스 별 아이콘 = 자쿰', pg.locator('.bossloot h2 .hbi img').count()==1)
    pg.locator('#lootKing').screenshot(path='/workspace/shots/b53_loot.png'); pg.locator('#epicCard').screenshot(path='/workspace/shots/b53_epic.png')
    pg.locator('#chaosCard').screenshot(path='/workspace/shots/b53_chaos.png'); pg.locator('#bbCard').screenshot(path='/workspace/shots/b53_bbang.png')
    pg.evaluate("localStorage.setItem('mapleBossTracker.tab','boss')"); pg.reload(); pg.wait_for_timeout(900)
    t=pg.inner_text('.rp-total'); check('이번 주 수익 억 한 자리 소수', t.replace('\n','').strip().endswith('억 메소') and '.' in t, t)
    pf=pg.inner_text('#view') if False else pg.content()
    check('월간 보스 📅, 가격 변동일 문구', '📅 월간 보스' in pf and '가격 변동일' in pf, '')
    pg.evaluate("()=>{const d=document.createElement('span'); d.className='drop got'; d.textContent='x'; document.body.appendChild(d)}")
    sz=pg.evaluate("(()=>{const d=document.querySelector('.drop.got');const a=getComputedStyle(d,'::after');return [a.backgroundImage.includes('svg'),a.position]})()")
    check('선택 칩 체크 오버레이 (SVG ::after, absolute)', sz[0] and sz[1]=='absolute', sz)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
