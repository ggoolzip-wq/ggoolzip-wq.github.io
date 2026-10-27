# test_b280: 득템왕 누적 획득 아이템 — 1~3위도 글씨 크기 같음(확대 없음), 반짝임은 유지
import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_PB280=_tutil.free_port()
# b55: 득템왕 (N회) 정렬·색, 반짝임, 보스왕, 에픽빔왕, 상자깡, 못 가진 아이템, 요약 카드 (base b52:) 메소왕·득템왕(순위·메달·10개씩 페이지), 시드링 획득 타율 위치, 블빵 승률·이긴/진 아이템, 빠뜨린 보스메소 ! 아이콘
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL=('http://localhost:'+str(_PB280)+'/index.html')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',str(_PB280),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
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
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900); pg.evaluate("(()=>{const v=document.querySelector('#view');const o=render;window.render=function(){renderLoot();const l=v.innerHTML;o.apply(this,arguments);v.insertAdjacentHTML('beforeend',l)};render()})()")
    pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    pg.locator('#lootKing').scroll_into_view_if_needed(); pg.wait_for_timeout(1600)
    FS="""()=>[...document.querySelectorAll('#lootKing tbody tr:not(.rkpad)')].map(r=>{ const c=r.children[3]; if(!c) return null; const t=[...c.querySelectorAll('.loot, .loot *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.data.trim())&&!e.closest('.ptx,.lx,.lxn')); return {rk:r.className, fs:[...new Set(t.map(e=>getComputedStyle(e).fontSize))], tf:[...new Set([...c.querySelectorAll('*')].map(e=>getComputedStyle(e).transform).filter(x=>x!=='none'))], h:Math.round(c.querySelector('.loot')?.getBoundingClientRect().height||0)}; }).filter(x=>x&&x.fs.length)"""
    R=pg.evaluate(FS); allfs=set(f for r in R for f in r['fs'])
    check('득템왕 누적 획득 아이템: 모든 순위 글씨 크기 하나 (1~3위 확대 없음)', len(allfs)==1 and len(R)>=3, R)
    check('확대 transform 없음', all(not r['tf'] for r in R), R)
    pg.hover('#lootKing tr.rk1 .loots .loot'); pg.wait_for_timeout(400); H=pg.evaluate(FS)
    check('마우스 올려도 크기 그대로', set(f for r in H for f in r['fs'])==allfs and all(not r['tf'] for r in H), H)
    check('1~3위 반짝임은 그대로', pg.evaluate("getComputedStyle(document.querySelector('#lootKing tr.rk1 .loots .spk'),'::before').animationName")=='spkd1')
    if os.environ.get('MBT_SHOTDIR'): pg.mouse.move(5,5); pg.wait_for_timeout(300); pg.locator('#lootKing').screenshot(path=os.path.join(os.environ['MBT_SHOTDIR'],os.environ.get('MBT_SHOT','after')+'_lootking.png'))
    b.close()
finally: srv.terminate()
check('JS 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
