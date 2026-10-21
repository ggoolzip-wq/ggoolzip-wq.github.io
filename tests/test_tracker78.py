import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8886=_tutil.free_port()
# zosu-crystal: 결정석 보스왕 = 누적 메소 내림차순, 동점은 난이도(익스트림>하드=카오스>노말>이지), 키 삭제된 계정 캐릭터 제외
# MBT_ROOT=폴더 → 그 폴더의 index.html 검사(스크린샷용), MBT_SHOT=경로 → #bossKing 스크린샷 저장, MBT_NOCHECK=1 → 판정 생략
import os, sys, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8886
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
def pc(id,name,bl): return {'id':id,'name':name,'meso':sum(v for _,v in bl),'count':len(bl),'bosses':[t for t,_ in bl],'bvals':[v for _,v in bl],'items':{}}
E=100000000
H=[{'week':'2026-09-28','perChar':[
    pc('c1','보이는캐',[('윌(하드)',5*E),('스우(하드)',E),('루시드(이지)',E),('스우(익스트림)',E)]),
    pc('c2','보이는둘',[('스우(하드)',E),('루시드(노말)',E),('벨룸(카오스)',E)]),
    pc('c3','보이는셋',[('스우(하드)',E),('루시드(하드)',E)]),
    pc('h1','키없는캐',[('카링(익스트림)',99*E)]),
    pc('h2','삭제계정캐',[('카링(하드)',88*E)])]}]
for h in H: h.update(total=sum(p['meso'] for p in h['perChar']),cleared=0,crystals=0,items=0)
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-28','history':H,'monthHistory':[],'worldOrder':[],
 'characters':[ch('c1','보이는캐','a1'),ch('c2','보이는둘','a1'),ch('c3','보이는셋','a1'),ch('h1','키없는캐','a2'),ch('h2','삭제계정캐','a3')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'test_crystal_0123456789abcdef','main':True},{'id':'a2','label':'부','key':''}],'goneAccs':['a3']}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900)
    pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
    pg.evaluate("tab='total'; render()"); pg.wait_for_timeout(300)
    rows=pg.eval_on_selector_all('#bossKing tbody tr:not(.rkpad)','e=>e.map(x=>[...x.children].map(t=>t.innerText.replace(/\\s+/g," ").trim()))')
    print('ROWS',rows)
    if os.environ.get('MBT_SHOT'): pg.locator('#bossKing').screenshot(path=os.environ['MBT_SHOT'])
    if not os.environ.get('MBT_NOCHECK'):
        names=[r[1] for r in rows]
        check('누적 메소 내림차순: 윌(하드) 5억(1회) > 스우(하드) 3억(3회)', names[:2]==['윌 (하드)','스우 (하드)'] and rows[0][2]=='1회' and rows[1][2]=='3회', names)
        check('동점(1억): 익스트림 > 하드=카오스 > 노말 > 이지', names[2]=='스우 (익스트림)' and set(names[3:5])=={'루시드 (하드)','벨룸 (카오스)'} and names[5:]==['루시드 (노말)','루시드 (이지)'], names)
        ms=pg.evaluate("bossKills(totalData()).map(o=>o.meso)")
        check('메소 값 내림차순(전체)', all(ms[i]>=ms[i+1] for i in range(len(ms)-1)) and ms[0]==5*E, ms)
        check('키 없는 계정·키 삭제된 계정 캐릭터 제외(카링 없음)', not any('카링' in n for n in names) and len(names)==7, names)
        # 저장된 기록에서 직접 불러도(totalData 필터를 거치지 않아도) 제외
        raw=pg.evaluate("bossKills({weeks:S.history,months:[]}).map(o=>o.b.name)")
        check('bossKills 자체도 숨은 캐릭터 제외', '카링' not in raw and len(raw)==7, raw)
        pg.evaluate("accounts()[1].key='test_crystal2_0123456789abcdef'; save(); render()"); pg.wait_for_timeout(200)
        n2=pg.eval_on_selector_all('#bossKing tbody tr:not(.rkpad)','e=>e.map(x=>x.children[1].innerText.replace(/\\s+/g," ").trim())')
        check('키 다시 넣으면 그 계정 보스 복귀(1위), 삭제 계정은 계속 제외', n2[0]=='카링 (익스트림)' and '카링 (하드)' not in n2, n2)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e)); fails.append('exception')
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
