import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8899=_tutil.free_port()
# b111: 득템 분석(리4컨4·블빵 상위%, 총 득템에 리4·컨4, 칠흑 상자 말풍선, 똥캐 TOP5, 보스 득템왕 반지 상자 결과, 강한 보스 순 정렬, 총 아이템 획득량 반상·리4·컨4),
# 길드 탭 취소/추가 위치, 일퀘 현황 탭 복원. MBT_ROOT/MBT_SHOTDIR/MBT_TAG/MBT_NOCHECK (변경 전 빌드 촬영용)
import os, sys, time, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8899)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.scroll_into_view_if_needed(); loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b111')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(i,name): return {'id':f'c{i}','name':name,'level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
NAMES=['일번','이번','삼번','사번','오번','육번','칠번']
CH=[ch(i,n) for i,n in enumerate(NAMES)]
P0={'id':'c0','name':'일번','meso':1,'bosses':['유피테르(하드)','카링(하드)','스우(익스트림)','자쿰(카오스)'],
    'items':{'jupiter|chaosbox':3,'kaling|r_black':2,'kaling|r_white#3':1,'jupiter|g_faith':1,'lotus|r_red':1,'zakum|r_black':1,'kaling|oath#3w':6,'kaling|se1#3l':4},
    'outcomes':{'jupiter|chaosbox':['cb:belt','cb:belt','cb:eye'],'kaling|r_black':['r4','x'],'kaling|r_white#3':['c4'],'lotus|r_red':['c4'],'zakum|r_black':['x']}}
PER=[P0]+[{'id':f'c{i}','name':NAMES[i],'meso':1,'bosses':['자쿰(카오스)'],'items':({'zakum|se1':i} if i else {})} for i in range(1,7)]
hist=[{'week':'2026-10-01','weeklyOnly':True,'total':7,'cleared':7,'perChar':PER}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':CH,'history':hist,'monthHistory':[],'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','loot')}",ST); pg.reload(); pg.wait_for_timeout(900)
    pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    if not NOCHK:
        sz=pg.evaluate('''(()=>{const r=s=>[...new Set([...document.querySelectorAll(s)].map(e=>{const b=e.getBoundingClientRect();return Math.round(b.width)+'x'+Math.round(b.height)}))];return [r('#lootKing .rkav'),r('#bossLootKing .rkico > *'),r('#lootKing .loot img, #lootKing .loot .ric'),r('#bossLootKing .blkchip img, #bossLootKing .blkchip .ric')]})()''')
        check('b122 보스 득템왕 보스 초상화 = 득템왕 캐릭터 초상화, 득템 목록 아이콘 = 득템왕 아이템 아이콘', sz[0]==sz[1] and sz[2]==sz[3] and len(sz[0])==1 and len(sz[2])==1, sz)
    shot(pg.locator('#lootTop'),'loot_top')
    if NOCHK:  # 변경 전 빌드: 같은 카드 촬영만
        for sel,nm in (('#lootKing','lootking_tip'),('#bossLootKing','bossking'),('#epicCard','epic_tip'),('.itemtot','itemtot'),('.bossloot','bossloot'),('#missItems','missing')): shot(pg.locator(sel).first,nm)
    else: shot(pg.locator('.bossloot').first,'bossloot'); shot(pg.locator('#missItems'),'missing')
    if not NOCHK:
        # 1) 상위% 계산 (사용자 예시: 3인 10판 6승 → 상위 7.7%)
        check('pbTail: 3인 10판 6승 = 상위 7.7%', pg.evaluate("topPct(pbTail(Array(10).fill(1/3),6))")=='상위 7.7%', pg.evaluate("pbTail(Array(10).fill(1/3),6)"))
        t=pg.evaluate("[...['#ltTotal','#ltRing','#ltBbang']].map(s=>document.querySelector(s).innerText.replace(/\\s+/g,' '))")
        # 블빵: 3인 6승 4패 → 7.7%
        check("블빵 카드: '블빵 상위' + 상위 7.7% + '3인 (6승 4패)' (b120 이름)", t[2]=='블빵 상위 상위 7.7% 3인 (6승 4패)', t[2])
        # 반상(녹옥·홍옥 제외): 흑옥 3(결과 기록 3: r4,x,x) 5% · 백옥 1(c4) 10% → P(X>=2)
        exp=pg.evaluate("pbTail([.05,.05,.05,.1],2)")
        ps=[.05,.05,.05,.1]
        import itertools
        pp=sum((lambda r:__import__('math').prod(ps[i] if r[i] else 1-ps[i] for i in range(4)))(r) for r in itertools.product([0,1],repeat=4) if sum(r)>=2)*100
        check('리4컨4 상위% = 포아송 이항(흑옥 3·백옥 1, 성공 2) — 파이썬 계산과 같음', abs(exp-pp)<1e-9 and t[1]==f"반상 상위 상위 {round(pp,1)}% 반상 누적 4회, 녹·홍옥 반상 제외", (t[1],pp))
        # 총 득템: chaosbox 3 + 흑옥 3 + 백옥 1 + 신념 1 + 홍옥 제외 + oath 6(블빵승리) (se1 패배 제외) + 리4·컨4 3(흑옥 r4, 백옥 c4, 홍옥 c4) = 17
        check('총 득템: 반지 상자 자체는 전부 제외(b182b, 흑옥3·백옥1 빠짐), 상자 리4·컨4는 더함, 블빵패배 제외 = 34개 (다른 캐릭터 소울 에테르 21 포함)', '34개' in t[0], t[0])
        check('b182b 총 득템 = 반지 상자 뺀 개수 (lootSummary.items 에 상자 수 없음)', pg.evaluate("(()=>{const T=totalData();let r=0;T.items.forEach(([a,I])=>{const {it,mode}=parseIK(a);if(mode!=='l'&&isRing(it))r+=I.n;});return lootSummary(T).items})()")==34)
        # 2) 득템왕: 칠흑 상자 = 상자 하나 + 말풍선
        lk=pg.evaluate("(()=>{const r=[...document.querySelectorAll('#lootKing tbody tr')].find(r=>r.innerText.includes('일번'));return [r.innerText.replace(/\\s+/g,' '),r.querySelectorAll('[data-tiphtml]').length]})()")
        check('득템왕: 칠흑 장신구 상자 ×3 (장신구 칩 대신), 상자 - 벨트 표기 없음', '혼돈의 칠흑 장신구 상자' in lk[0] and ' - ' not in lk[0] and lk[1]==1, lk)
        check('득템왕: 리4·컨4 반지 아이콘 칩 (분배 무관)', pg.evaluate("(()=>{const r=[...document.querySelectorAll('#lootKing tbody tr')].find(r=>r.innerText.includes('일번'));const t=r.innerText.replace(/\\s+/g,' ');return /리스트레인트 링 4레벨 x1/.test(t)&&/컨티뉴어스 링 4레벨 x2/.test(t)&&r.querySelectorAll('.loot img.ric, .loot .ric').length>=2})()"))
        el=pg.locator('#lootKing [data-tiphtml]').first; el.hover(); pg.wait_for_timeout(250)
        tip=pg.inner_text('#mbtTip'); ti=pg.locator('#mbtTip .ttr img').count()
        check('득템왕 말풍선: 장신구별 아이콘·개수 (벨트 2, 안대 1)', '혼돈의 칠흑 장신구 상자' in tip and ti==2 and '×2' in tip.replace('x','×'), (tip,ti))
        shot(pg.locator('#lootKing'),'lootking_tip')
        pg.mouse.move(1,1)
        # 3) 똥캐 TOP5 → b212 TOP3
        ids=pg.evaluate("[...document.querySelectorAll('#view .card[id]')].map(c=>c.id)")
        check('똥캐 TOP5 = 득템왕과 보스 득템왕 사이', ids.index('lootKing')+1==ids.index('poopKing')==ids.index('bossLootKing')-1, ids)
        pr=pg.evaluate("[...document.querySelectorAll('#poopKing tbody tr')].map(r=>[r.cells[0].innerText.trim(),r.querySelector('.rknm b').innerText.trim(),r.cells[2].innerText.trim(),r.querySelectorAll('.poopav .poop').length,r.querySelectorAll('.fly').length])")
        check('똥캐 TOP3(b212): 제목 + 득템 적은 순 1~3위만 (이번1·삼번2·사번3)', 'TOP3' in pg.inner_text('#poopKing h2') and [x[1] for x in pr]==['이번','삼번','사번'] and [x[2] for x in pr]==['1회','2회','3회'], pr)
        check('똥캐: 3명 모두 초상화 위 똥 + 날파리 4(b115), 1위 = 💩 (왕관 없음), 메달 색 없음', all(x[3]==1 and x[4]==4 for x in pr) and '💩' in pr[0][0] and pg.locator('#poopKing .crown:not(:has-text("💩"))').count()==0 and pg.locator('#poopKing [class*=md-]').count()==0, pr)
        check('똥캐: 제목 아이콘 = 1위 초상화 + 똥', pg.locator('#poopKing h2 .poopav .avatar').count()==1 and pg.locator('#poopKing h2 .poop').count()==1)
        shot(pg.locator('#poopKing'),'poop')
        # 4) 보스 득템왕: 칠흑 상자 + 반지 상자 결과
        bk=pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr')].map(r=>r.innerText.replace(/\\s+/g,' '))")
        check("보스 득템왕: 반지 상자 = 아이콘 + 'N개 - 리4 a개 - 컨4 b개 - 꽝 c개'", any('2개 - 리4 1개 - 컨4 0개 - 꽝 1개' in x for x in bk), bk)
        check('보스 득템왕: 칠흑 상자 하나 + 말풍선', pg.locator('#bossLootKing [data-tiphtml]').count()==1 and any('혼돈의 칠흑 장신구 상자' in x for x in bk), bk)
        check('보스 득템왕: 보스 아이콘 크게 (≥32px)', pg.evaluate("(()=>{const i=document.querySelector('#bossLootKing .rkico img, #bossLootKing .rkico .bicon');return i?i.getBoundingClientRect().width:0})()")>=32)
        shot(pg.locator('#bossLootKing'),'bossking')
        # 5) 에픽빔왕: 칠흑 상자 말풍선 (모든 캐릭터)
        pg.locator('#epicCard [data-tiphtml]').first.hover(); pg.wait_for_timeout(250)
        check('에픽빔왕 칠흑 상자 말풍선: 장신구 목록', '몽환의 벨트' in pg.inner_text('#mbtTip') and pg.locator('#mbtTip .ttr img').count()==2, pg.inner_text('#mbtTip'))
        shot(pg.locator('#epicCard'),'epic_tip'); pg.mouse.move(1,1)
        # 6) 정렬: 강한 보스 먼저
        so=pg.evaluate("[bossStr('jupiter','hard'),bossStr('star','hard'),bossStr('star','normal'),bossStr('lotus','extreme'),bossStr('kaling','hard'),bossStr('seren','extreme'),bossStr('blackmage','extreme'),bossStr('dunkel','hard'),bossStr('lucid','hard'),bossStr('lotus','hard'),bossStr('zakum','chaos')]")
        check('강함 순서: 유피테르 > … 흉성(노말) > 스우(익스트림) > 카링 … > 검마 > 아케인 > 그 밖', so==sorted(so) and len(set(so))==len(so), so)
        bl=pg.evaluate("[...document.querySelectorAll('.bossloot .blrow .blb b')].map(e=>e.innerText)")
        check('보스 별 누적 획득 아이템: 강한 보스 먼저 (유피테르 → 스우(익스트림, 흉성 노말 아래) → 카링 → 자쿰)', bl==['유피테르','스우','카링','자쿰'], bl)
        mi=pg.evaluate("missingItems(totalData()).map(o=>bossStr(o.list[0].b,o.list[0].d))")
        check('못 가진 아이템: 강한 보스 먼저, 첫 줄 = 유피테르', mi==sorted(mi) and pg.evaluate("missingItems(totalData())[0].list[0].b.id")=='jupiter', mi[:5])
        # 7) 총 아이템 획득량 (b120: 요약 줄 삭제, 리4·컨4 = 일반 칩)
        OUT4=pg.evaluate("({r4:OUT_NAME.r4,c4:OUT_NAME.c4})")
        it=pg.evaluate("[...document.querySelectorAll('.itemtot .loot')].map(e=>e.innerText.replace(/\\s+/g,' ').trim())")
        r4=[x for x in it if x.startswith(OUT4['r4'])]; c4=[x for x in it if x.startswith(OUT4['c4'])]
        order=pg.evaluate("[...document.querySelectorAll('.itemtot .loot')].map(e=>e.querySelector('.ln').textContent)")
        check('b120 총 아이템 획득량: 위 요약 줄 없음, 리4 x1 · 컨4 x2 = 다른 아이템과 같은 칩, 아이템 순서', pg.locator('#itRingSum').count()==0 and r4==[OUT4['r4']+' x1'] and c4==[OUT4['c4']+' x2'], (it,order))
        names=pg.evaluate("[...document.querySelectorAll('.itemtot .loot')].map(e=>e.innerText.replace(/\\s+/g,' ').trim())")
        win=[x for x in names if '블빵승리' in x]; los=[i for i,x in enumerate(names) if '블빵패배' in x]
        check('b122 총 아이템 획득량: 블빵승리는 같은 아이템과 합침, 블빵패배는 따로 맨 뒤', not win and los and los==list(range(len(names)-len(los),len(names))) and len([x for x in names if x.startswith('1단계 소울 에테르 x')])==1, names)
        shot(pg.locator('.itemtot'),'itemtot')
    # 8) 길드 탭 버튼 위치 · 일퀘 탭 (모의 넥슨 API)
    ctx=b.new_context(viewport={'width':1366,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    pg2=ctx.new_page(); pg2.on('pageerror',lambda e:errs.append(str(e)))
    PRE={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
      'characters':[dict(ch(1,'단풍용사'),ocid='ocid-main',accId='a1',level=287)],
      'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM}],'lastSync':int(time.time()*1000),'guilds':[]}}
    pg2.goto(f'http://127.0.0.1:{PORT}/index.html'); pg2.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','guild')}",PRE); pg2.reload(); pg2.wait_for_timeout(1500)
    pg2.wait_for_timeout(300); pg2.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    tabs=pg2.eval_on_selector_all('#tabs button',"e=>e.map(x=>x.dataset.tab)")
    check('b119: 일퀘 현황 탭 없음, 길드 현황 있음', 'daily' not in tabs and 'guild' in tabs, tabs)
    if pg2.locator('#guildAdd').count():
        pg2.click('#guildAdd'); pg2.wait_for_timeout(600)
        g=pg2.evaluate("(()=>{const h=document.querySelector('#guildCard h2'),a=h.querySelector('#guildAdd'),x=h.querySelector('#guildCancel'),o=h.querySelector('#guildOk');return [!!x,!!o,x&&o&&x.getBoundingClientRect().right<=o.getBoundingClientRect().left+1&&o.getBoundingClientRect().right<=a.getBoundingClientRect().left+1,document.querySelectorAll('#guildCard .suropick-b').length,x?getComputedStyle(x).backgroundColor:'']})()")
        check('길드 추가: 취소·추가가 제목 줄 버튼 왼쪽 (아래 줄 없음), 취소 = 색 없음', g[0] and g[1] and g[2] and g[3]==0 and g[4] in ('rgba(0, 0, 0, 0)','transparent'), g)
        shot(pg2.locator('#guildCard'),'guild_add')
        pg2.click('#suroAdd'); pg2.wait_for_timeout(300)
        s2=pg2.evaluate("(()=>{const h=document.querySelector('#suroCard h2'),a=h.querySelector('#suroAdd'),x=h.querySelector('#suroCancel'),o=h.querySelector('#suroOk');return [!!x&&!!o&&x.getBoundingClientRect().right<=o.getBoundingClientRect().left+1&&o.getBoundingClientRect().right<=a.getBoundingClientRect().left+1,document.querySelectorAll('#suroCard .suropick-b').length]})()")
        check('캐릭터 추가(수로): 취소·추가 = 버튼 왼쪽', s2[0] and s2[1]==0, s2)
        shot(pg2.locator('#suroCard'),'suro_add')
        pg2.click('#suroCancel'); pg2.wait_for_timeout(200); check('수로 취소 → 닫힘', pg2.locator('#suroCancel').count()==0)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs[:3]); sys.exit(1 if fails or errs else 0)
