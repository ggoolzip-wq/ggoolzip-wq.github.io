# b55: 득템왕 (N회) 정렬·색, 반짝임, 보스왕, 에픽빔왕, 상자깡, 못 가진 아이템, 요약 카드 (base b52:) 메소왕·득템왕(순위·메달·10개씩 페이지), 시드링 획득 타율 위치, 블빵 승률·이긴/진 아이템, 빠뜨린 보스메소 ! 아이콘
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8841/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8841','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
N=12
chars=[{'id':f'c{i}','name':f'캐릭{i:02d}','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(N)]
# 지난 주 기록: c{i} 메소 = (i+1)억 (c11 이 1등), 월간 c0 에 20억 → c0 이 1등이 됨
per=[{'id':f'c{i}','name':f'캐릭{i:02d}','meso':(i+1)*100000000,'count':1,'bosses':[],'items':{},'outcomes':{}} for i in range(N)]
# 아이템: c3 = 승리 2 + 분배 1 + 패배 1(제외) + 꽝 반지 1(제외), c5 = 1인 아이템 2, c7 = 패배만 1
per[3]['items']={'kaling|g_faith#2w':1,'star|bliss#3w':1,'limbo|whisper#2':1,'kaling|oath#2l':1,'kaling|r_white':1}; per[3]['outcomes']={'kaling|r_white':['x']}
per[5]['items']={'seren|mitra':1,'kalos|r_black':1}; per[5]['outcomes']={'kalos|r_black':['r4']}
per[7]['items']={'star|chaosbox#2l':1}; per[7]['outcomes']={'star|chaosbox#2l':['cb:eye']}
per[9]['items']={'kaling|g_life#2w':1,'kaling|se1#2l':1,'star|se2#3l':1}
per[0]['bosses']=['스우(하드)','루시드(하드)/2인']; per[0]['bvals']=[100,50]
per[1]['bosses']=['스우(하드)','루시드(하드)']; per[1]['bvals']=[100,100]
per[2]['bosses']=['루시드(하드)','윌(하드)']; per[2]['bvals']=[100,7]
per[5]['outcomes']['kalos|r_black']=['gl']
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
    idx=lambda t: next((i for i,h in enumerate(hs) if h.endswith(t) or h==t),-1)
    o=[idx(t) for t in ['메소왕','득템왕','보스왕','에픽빔왕','혼돈의 칠흑 장신구 상자깡','내가 가지지 못한 아이템 목록']]
    check('순서: 메소왕→득템왕→보스왕→에픽빔왕→상자깡→못 가진 아이템, 득템왕 제목 괄호 없음', all(x>=0 for x in o) and o==sorted(o), (o,hs))
    al=pg.evaluate("""(()=>{const n=document.querySelector('#lootKing tr.rk1 .rkname b:not(.rkcnt)'),c=document.querySelector('#lootKing tr.rk1 .rkcnt');const a=n.getBoundingClientRect(),b=c.getBoundingClientRect();return [c.innerText,getComputedStyle(n).color,getComputedStyle(c).color,getComputedStyle(n).fontSize,getComputedStyle(c).fontSize,a.bottom,b.bottom,a.top,b.top]})()""")
    check('득템왕 (N회): 닉네임과 같은 색·크기, 같은 줄(세로 정렬)', al[0]=='(3회)' and al[1]==al[2] and al[3]==al[4] and abs(al[5]-al[6])<1 and abs(al[7]-al[8])<1 and pg.locator('#lootKing .score').count()==0, al)
    pl=pg.evaluate("getComputedStyle(document.querySelector('#lootKing tr.rk4 .rkcnt')).color==getComputedStyle(document.querySelector('#lootKing tr.rk4 .rkname b')).color") if pg.locator('#lootKing tr.rk4').count() else True
    check('4위 이하 (N회)도 닉네임과 같은 색', pl)
    sp=pg.evaluate("['#mesoKing','#lootKing','#bossKing','#epicCard'].map(t=>{const e=document.querySelector(t+' tr.rk1 .spk');return e?getComputedStyle(e,'::before').content:''})")
    check('1~3위 반짝임 (메소왕·득템왕·보스왕·에픽빔왕)', all('✦' in x for x in sp), sp)
    bk=pg.eval_on_selector_all('#bossKing tbody tr:not(.rkpad)','e=>e.map(x=>[...x.children].map(t=>t.innerText.replace(/\s+/g," ").trim()))')
    check('보스왕: 횟수 내림차순, 동점은 비싼 보스 먼저, 메소 합(파티 나눔 적용)', [r[1] for r in bk]==['루시드 (하드)','스우 (하드)','윌 (하드)'] and bk[0][2]=='3회' and bk[0][3]==pg.evaluate("meso(250)") and bk[1][2]=='2회', bk)
    dc=pg.evaluate("[getComputedStyle(document.querySelector('#bossKing .dlv-hard')).color,getComputedStyle(document.querySelector('#bossKing .bdn')).color]")
    check('난이도 하드 빨강·보스 이름 흰색, 1~3위 보스 아이콘', dc==['rgb(255, 77, 77)','rgb(255, 255, 255)'] and pg.locator('#bossKing tr.rk1 .rkico img').count()==1 and pg.locator('#bossKing h2 img').count()==1, dc)
    ep=pg.inner_text('#epicCard')
    check('에픽빔왕: 제목 숫자 없음, 누적 횟수 줄, 반지 상자·상자 결과 제외', pg.inner_text('#epicCard h2').strip()=='에픽빔왕' and pg.locator('#epicCard .epgold').count()==1 and '반지 상자' not in ep and ep.count('생명의 연마석')==1 and '리스트레인트' not in ep, (pg.inner_text('#epicCard h2'),ep[:300]))
    er=pg.eval_on_selector_all('#epicCard tbody tr:not(.rkpad)','e=>e.map(x=>x.children[1].innerText.trim())')
    check('에픽빔 동점 → 아이템 우선순위 (광휘 먼저)', er[0] in ('황홀한 악몽','근원의 속삭임','죽음의 맹세'), er)
    cc=pg.eval_on_selector_all('#chaosCard tbody tr:not(.rkpad)','e=>e.map(x=>x.children[1].innerText.trim()+"|"+x.children[2].innerText.trim())')
    check('상자깡: 순위 표 7행, 0 포함, 동점 우선순위(루컨마·커포 뒤)', len(cc)==7 and cc[0].endswith('x1') and cc[-1].split('|')[0] in ('루즈 컨트롤 머신 마크','커맨더 포스 이어링'), cc)
    mi=pg.eval_on_selector_all('#missItems tbody tr:not(.rkpad)','e=>e.map(x=>x.innerText.replace(/\s+/g," ").trim())')
    allm=pg.evaluate("missingItems(totalData()).map(o=>ITEMS[o.k].n+'@'+o.b.name)")
    check('못 가진 아이템: 4단계 소울 에테르(유피테르) 있음, 얻은 신념·생명 연마석(상자 결과) 없음', any(x.startswith('4단계 소울 에테르@유피테르') for x in allm) and not any(x.split('@')[0] in ('신념의 연마석','생명의 연마석') for x in allm), allm)
    check('못 가진 아이템: 광휘 먼저, 10줄 고정, 흑백 제목 아이콘', len(mi)<=10 and pg.locator('#missItems tbody tr').count()==10 and pg.locator('#missItems h2 .gray').count()==1 and ('창세' in allm[0] or pg.evaluate("ITEMS[missingItems(totalData())[0].k].set")=='광휘'), allm[:3])
    sm=pg.inner_text('#view .card >> nth=0')
    check('요약: 억 1자리, 주/월 평균 원 단위, 종 없음', '월 평균' in sm and '종' not in sm and '억' in sm and '개월' not in sm, sm)
    for n,sel in [('loot','#lootKing'),('boss','#bossKing'),('epic','#epicCard'),('miss','#missItems'),('summary','#view .card >> nth=0')]: pg.locator(sel).screenshot(path=f'/workspace/shots/b55_{n}.png')
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
