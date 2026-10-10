# b52: 메소왕·득템왕(순위·메달·10개씩 페이지), 시드링 획득 타율 위치, 블빵 승률·이긴/진 아이템, 빠뜨린 보스메소 ! 아이콘
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8838/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8838','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
N=12
chars=[{'id':f'c{i}','name':f'캐릭{i:02d}','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(N)]
# 지난 주 기록: c{i} 메소 = (i+1)억 (c11 이 1등), 월간 c0 에 20억 → c0 이 1등이 됨
per=[{'id':f'c{i}','name':f'캐릭{i:02d}','meso':(i+1)*100000000,'count':1,'bosses':[],'items':{},'outcomes':{}} for i in range(N)]
# 아이템: c3 = 승리 2 + 분배 1 + 패배 1(제외) + 꽝 반지 1(제외), c5 = 1인 아이템 2, c7 = 패배만 1
per[3]['items']={'kaling|g_faith#2w':1,'star|bliss#3w':1,'limbo|whisper#2':1,'kaling|oath#2l':1,'kaling|r_white':1}; per[3]['outcomes']={'kaling|r_white':['x']}
per[5]['items']={'seren|mitra':1,'kalos|r_black':1}; per[5]['outcomes']={'kalos|r_black':['r4']}
per[7]['items']={'star|chaosbox#2l':1}; per[7]['outcomes']={'star|chaosbox#2l':['cb:eye']}
per[9]['items']={'kaling|g_life#2w':1,'kaling|se1#2l':1,'star|se2#3l':1}
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
    order=['메소왕','득템왕','에픽빔 본 횟수','블빵 승률','블빵 이겨서 얻은 아이템들','블빵 져서 잃은 아이템들','보스 별 누적 획득 아이템','시드링 획득 타율','총 아이템 획득량']
    ii=[idx(t) for t in order]
    check('섹션 순서 (메소왕→득템왕→에픽빔→블빵 승률→이긴→진→보스별→시드링 획득 타율→총 아이템)', all(x>=0 for x in ii) and ii==sorted(ii) and ii[-2]+1==ii[-1] and '캐릭터별 누적' not in ' '.join(hs), list(zip(order,ii)))
    check("시드링: '대박 확률' 없음", '대박 확률' not in pg.inner_text('#view'))
    rows=pg.eval_on_selector_all('#mesoKing tbody tr','e=>e.map(x=>[...x.children].map(td=>td.innerText.replace(/\\s+/g," ").trim()))')
    check('메소왕: 열 + 누적 합계 내림차순, 10개', pg.eval_on_selector_all('#mesoKing th','e=>e.map(x=>x.innerText)')==['순위','캐릭터','누적 주간 보스메소량','누적 월간 보스메소량','누적 합계'] and len(rows)==10 and rows[0][1].endswith('캐릭00') and rows[1][1].endswith('캐릭11') and rows[2][1].endswith('캐릭10') and rows[9][1].endswith('캐릭03'), rows[:3])
    md=pg.evaluate("""[1,2,3,4].map(r=>{const tr=document.querySelector('#mesoKing tbody tr.rk'+r);const n=tr.querySelector('.rkname'),k=tr.querySelector('.rkno');return {cls:tr.className,crownNo:!!k.querySelector('.crown'),crownNm:!!n.querySelector('.crown'),av:!!n.querySelector('.avatar'),col:getComputedStyle(n.querySelector('b')).color,glow:getComputedStyle(k).textShadow!=='none'}})""")
    check('1등: 순위·닉네임 왕관 + 초상화 + 금색 빛', md[0]['crownNo'] and md[0]['crownNm'] and md[0]['av'] and md[0]['col']=='rgb(255, 213, 74)' and md[0]['glow'], md[0])
    check('2등: 초상화 + 은색 빛 (왕관 없음)', md[1]['av'] and not md[1]['crownNo'] and md[1]['col']=='rgb(230, 235, 242)' and md[1]['glow'], md[1])
    check('3등: 초상화 + 동색 빛', md[2]['av'] and md[2]['col']=='rgb(227, 160, 106)' and md[2]['glow'], md[2])
    check('4등: 초상화·빛 없음', not md[3]['av'] and not md[3]['glow'] and not md[3]['crownNo'], md[3])
    pg.locator('#mesoKing').screenshot(path='/workspace/shots/b52_meso.png')
    btn=pg.eval_on_selector_all('#mesoKing .cpg','e=>e.map(x=>[x.innerText,x.classList.contains("on")])')
    check('메소왕 페이지 버튼 1 2 (캐릭터 목록과 같은 모양)', btn==[['1',True],['2',False]], btn)
    pg.click('#mesoKing [data-rkpage="meso|2"]'); pg.wait_for_timeout(200)
    r2=pg.eval_on_selector_all('#mesoKing tbody tr','e=>e.map(x=>x.children[0].innerText.trim()+" "+x.children[1].innerText.trim())')
    check('2쪽 = 11~12위', r2==['11 캐릭02','12 캐릭01'], r2)
    lk=pg.eval_on_selector_all('#lootKing tbody tr','e=>e.map(x=>x.children[1].innerText.replace(/\\s+/g," ").trim())')
    check('득템왕: 승리·분배·1인만 셈, 패배·꽝 제외 (c3=3, c5=2, c9=1, c7 없음)', [x.split(' x')[0].split()[-1] for x in lk]==['캐릭03','캐릭05','캐릭09'] and lk[0].endswith('x3') and lk[1].endswith('x2'), lk)
    ch=pg.inner_text('#lootKing'); check('득템왕 아이템 칩 xN (리4 결과로, 꽝/패배 없음)', '리스트레인트 링 4레벨' in ch and '죽음의 맹세' not in ch and '꽝' not in ch and pg.locator('#lootKing h2 img').count()==1, ch)
    pg.locator('#lootKing').screenshot(path='/workspace/shots/b52_loot.png')
    st=pg.evaluate("bbangStats(totalData())")
    rr=pg.eval_on_selector_all('#bbRate tr','e=>e.map(x=>x.innerText.replace(/\\s+/g," ").trim())')
    # 2인: w g_faith, g_life / l oath, chaosbox, se1 → 2승 3패 = 40.0% ; 3인: w bliss / l se2 → 1승 1패 = 50.0%
    check('블빵 승률: 인원별 %, N승 M패, 기록 없는 인원 숨김', rr==['2인 40.0% 2승 3패','3인 50.0% 1승 1패'], (rr,st))
    sp=pg.evaluate("(()=>{const a=document.querySelector('#bbRate .bk-a'),b=document.querySelector('#bbRate .bk-b');return [getComputedStyle(a).clipPath,getComputedStyle(b).clipPath,getComputedStyle(b).filter]})()")
    check('승률 아이콘: 대각선 반반 (왼쪽 위 원색, 오른쪽 아래 흑백)', 'polygon' in sp[0] and 'polygon' in sp[1] and 'grayscale' in sp[2], sp)
    w=pg.inner_text('#bbWon'); l=pg.inner_text('#bbLost')
    check('이긴 아이템: 블빵승리만', '신념의 연마석' in w and '황홀한 악몽' in w and '생명의 연마석' in w and '근원의 속삭임' not in w and '죽음의 맹세' not in w, w)
    check('진 아이템: 블빵패배만 (흑백 블링크)', '죽음의 맹세' in l and '마력이 깃든 안대' in l and '신념의 연마석' not in l and pg.locator('#bbLost .blk.gray').count()==1, l)
    pg.locator('#bbRate').screenshot(path='/workspace/shots/b52_bbang.png')
    mi=pg.evaluate("[...document.querySelectorAll('.missic')].map(e=>{const s=getComputedStyle(e);return [s.color,s.backgroundColor,s.borderRadius,s.fontWeight]})")
    check("빠뜨린 보스메소 '!': 주간 노랑 / 월간 빨강, 배경·원 없음, 굵게", len(mi)==2 and mi[0][0]=='rgb(242, 201, 76)' and mi[1][0]=='rgb(255, 77, 77)' and all(x[1]=='rgba(0, 0, 0, 0)' and int(x[3])>=800 for x in mi), mi)
    pg.locator('.missic').first.scroll_into_view_if_needed(); pg.screenshot(path='/workspace/shots/b52_miss.png')
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
