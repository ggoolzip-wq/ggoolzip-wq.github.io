# b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8885
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}

def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
def pc(id,items,bosses): return {'id':id,'name':id,'meso':1,'count':1,'bosses':bosses,'bvals':[1]*len(bosses),'items':{k:1 for k in items}}
P1=pc('c1',['lucid|eye','lucid|belt','lucid|book','kalos|g_faith','jupiter|g_life','zakum|r_black'],['루시드(하드)','감시자 칼로스(카오스)','유피테르(하드)','자쿰(카오스)'])
P2=pc('c1',['blackmage|genesis','blackmage|mitra','jupiter|g_faith','jupiter|lcm'],['검은 마법사(익스트림)','유피테르(하드)'])
P3=pc('c2',['zakum|eye','zakum|belt','zakum|book','zakum|terror','zakum|sos'],['자쿰(카오스)'])
H=[{'week':'2026-09-28','perChar':[P1,P3]}]; M=[{'month':'2026-09','perChar':[P2]}]
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-28','history':H,'monthHistory':M,'worldOrder':[],'characters':[ch('c1','보이는캐','a1'),ch('c2','숨는캐','a2')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1280,390):
        pg=b.new_page(viewport={'width':w,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
        pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
        if w==1280:
            ids=pg.evaluate("[...document.querySelectorAll('#view .card[id]')].map(c=>c.id)")
            check('order: 득템왕 → 똥캐 TOP3 → 보스 득템왕 → 에픽빔왕 (b111)', 'bossLootKing' in ids and ids.index('lootKing')+1==ids.index('poopKing') and ids.index('poopKing')+1==ids.index('bossLootKing') and ids[ids.index('bossLootKing')+1]=='epicCard', ids)
            rows=pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr:not(.rkpad)')].map(r=>[r.cells[1].innerText.trim(),r.cells[2].innerText.trim(),r.querySelectorAll('.blkchip').length,(r.querySelector('[class*=rg-]')||{}).className||''])")
            check('rows(점수): 루시드 3, 유피테르 3, 검마 2, 칼로스 1 (자쿰 흑옥 상자 1개 = 0.1점; hidden char zakum x5 excluded)', [x[1] for x in rows]==['3점','3점','2점','1점','0.1점'] and '루시드' in rows[0][0]+rows[1][0] and '유피테르' in rows[0][0]+rows[1][0] and '검은 마법사' in rows[2][0], rows)
            check('difficulty shown', '(하드)' in rows[0][0] and '(익스트림)' in rows[2][0], rows)
            check('top3 region colors: 유피테르 gr2, 루시드 arc, 검마 bm', sorted([rows[0][3],rows[1][3]])==['spk rg-arc','spk rg-gr2'] and rows[2][3]=='spk rg-bm' and rows[3][3]=='', rows)
            check('title icon = rank-1 boss portrait', pg.evaluate("document.querySelector('#bossLootKing h2 .hbi').innerHTML===bossIcon(findBoss((()=>{const t=document.querySelector('#bossLootKing tbody tr').cells[1].innerText; return t.includes('유피테르')?'jupiter':'lucid'})()))"))
            pg.locator('#bossLootKing').screenshot(path='/workspace/maple-boss-tracker/oct12u_b83_test_card.png')
        one=pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr:not(.rkpad)')].every(r=>r.getBoundingClientRect().height<=64)"); print(w,pg.evaluate("[...document.querySelectorAll('#bossLootKing tbody tr:not(.rkpad)')].map(r=>r.getBoundingClientRect().height)"), pg.evaluate("(()=>{const c=document.querySelector('#bossLootKing');return [c.scrollWidth,c.clientWidth,document.documentElement.scrollWidth]})()"))
        hs=pg.evaluate("(()=>{const c=document.querySelector('#bossLootKing'); return c.scrollWidth>c.clientWidth+1||[...c.querySelectorAll('*')].some(e=>e.getBoundingClientRect().right>c.getBoundingClientRect().right+1)})()"); print('wide:',pg.evaluate("[...document.querySelectorAll('#view *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,5).map(e=>e.tagName+'.'+e.className+'#'+e.id+':'+(e.closest('.card')||{}).id)"))
        check(f'{w}px: one line rows, no horizontal scroll', one and not hs, (one,hs))
        if w==390: print('CW',pg.evaluate("[...document.querySelectorAll('#bossLootKing th')].map(t=>t.offsetWidth+':'+getComputedStyle(t).width)+'|'+getComputedStyle(document.querySelector('#bossLootKing .rkico')).display+'|'+getComputedStyle(document.querySelector('#bossLootKing .blktbl')).tableLayout"))
        if w==390: pg.locator('#bossLootKing').screenshot(path='/workspace/maple-boss-tracker/oct12u_b83_test_card_390.png')
        pg.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
