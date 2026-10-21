# test_tracker103 (zosu-apikey): 키 삭제된 계정(키 없음·settings.goneAccs) 캐릭터는 모든 합계·순위·표·차트·길드 수로에서 제외, 키 다시 넣으면 복귀
# MBT_ROOT=폴더 → 그 폴더의 index.html 검사(스크린샷용), MBT_SHOT=경로 → 결정석 분석 탭 스크린샷 저장, MBT_NOCHECK=1 → 판정 생략
import os, sys, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8946
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
MISS=[{'week':'2026-09-28','date':'2026.10.01','n':4,'meso':58*E,'list':[{'name':'보이는캐','n':1,'meso':E},{'name':'키없는캐','n':2,'meso':50*E},{'id':'h2','name':'삭제계정캐','n':1,'meso':7*E}]}]
for h in H: h.update(total=sum(p['meso'] for p in h['perChar']),cleared=0,crystals=0,items=0)
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-28','history':H,'monthHistory':[{'month':'2026-09','total':77*E,'cleared':2,'perChar':[pc('c1','보이는캐',[('검은 마법사(하드)',E)]),pc('h1','키없는캐',[('검은 마법사(익스트림)',76*E)])]}],'missW':MISS,'worldOrder':[],
 'characters':[ch('c1','보이는캐','a1'),ch('c2','보이는둘','a1'),ch('c3','보이는셋','a1'),ch('h1','키없는캐','a2'),ch('h2','삭제계정캐','a3')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'test_crystal_0123456789abcdef','main':True},{'id':'a2','label':'부','key':''}],'goneAccs':['a3'],'suroChars':['c1','h1','h2']}}

HID=['키없는캐','삭제계정캐']
def vis_text(pg): return pg.evaluate("document.querySelector('#view').innerText+' '+[...document.querySelectorAll('#view [data-tip],#view [title]')].map(e=>(e.dataset.tip||'')+e.title).join(' ')")
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1600},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900)
    pg.evaluate("tab='total'; render()"); pg.wait_for_timeout(300)
    if os.environ.get('MBT_SHOT'):
        el=pg.locator('.misschart').first
        if el.count(): el.scroll_into_view_if_needed()
        pg.wait_for_timeout(200); pg.screenshot(path=os.environ['MBT_SHOT'],full_page=True)
        mc=pg.locator('.card:has(.misschart)').first  # 빠뜨린 보스메소 카드만 따로 (…-miss.png)
        if mc.count(): mc.screenshot(path=os.environ['MBT_SHOT'].replace('.png','-miss.png'))
    if not os.environ.get('MBT_NOCHECK'):
        t=vis_text(pg)
        check('결정석 분석 탭: 숨은 캐릭터 이름 없음(메소왕·보스왕·빠뜨린 보스메소)', not any(h in t for h in HID), [h for h in HID if h in t])
        g=pg.evaluate("totalData().grand")
        check('총 합계 = 보이는 캐릭터만 (주간 13억 + 월간 1억)', g==14*E, g)
        mk=pg.evaluate("totalData().chars.map(o=>o.name)")
        check('메소왕 순위: 보이는 3명만', sorted(mk)==sorted(['보이는캐','보이는둘','보이는셋']), mk)
        bk=pg.evaluate("bossKills(totalData()).map(o=>o.b.name)")
        check('결정석 보스왕: 카링 없음', '카링' not in bk, bk)
        ms=pg.evaluate("(S.missW||[]).map(r=>activeMiss(r)).map(r=>[r.n,r.meso,r.list.map(x=>x.name)])")
        check('빠뜨린 보스메소(주간): 숨은 캐릭터 제외·합계 다시 계산', ms==[[1,E,['보이는캐']]], ms)
        raw=pg.evaluate("S.missW[0].list.length")
        check('저장된 빠뜨린 보스메소 기록은 그대로(3명)', raw==3, raw)
        cr=pg.evaluate("Object.keys(charRecords())")
        check('캐릭터 별 기록(charRecords): 숨은 캐릭터 없음', 'h1' not in cr and 'h2' not in cr, cr)
        ac=pg.evaluate("[activeChars().map(c=>c.id), [...activeIds()], activeRecords(S.history[0]).total]")
        check('헬퍼 activeChars/activeIds/activeRecords', ac[0]==['c1','c2','c3'] and sorted(ac[1])==['c1','c2','c3'] and ac[2]==13*E, ac)
        rv=pg.evaluate("(()=>{ const c=S.characters.find(x=>x.id==='h1'); c.bosses.will={enabled:true,diff:'hard',party:1}; c.weekly.will=true; save(); return allRevenue(activeChars()).per.map(p=>p.c.id); })()")
        check('이번 주 수익(수익 패널): 숨은 캐릭터 제외', 'h1' not in rv, rv)
        pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300); t=vis_text(pg)
        check('득템 분석 탭: 숨은 캐릭터 이름 없음', not any(h in t for h in HID), [h for h in HID if h in t])
        pg.evaluate("tab='boss'; render()"); pg.wait_for_timeout(300); t=pg.evaluate("document.body.innerText")
        check('보스 탭·사이드바: 숨은 캐릭터 없음', not any(h in t for h in HID), [h for h in HID if h in t])
        sc=pg.evaluate("suroChars().map(c=>c.name)")
        check('길드 현황 수로(★ 본캐 목록): 보이는 캐릭터만', sc==['보이는캐'], sc)
        pg.evaluate("tab='guild'; render()"); pg.wait_for_timeout(500); t=vis_text(pg)
        check('길드 현황 탭: 숨은 캐릭터 이름 없음', not any(h in t for h in HID), [h for h in HID if h in t])
        adm=pg.evaluate("(()=>{ admUsers=[{id:'u1',status:'ok',name:'관리자본캐',chars:3,alts:[]}]; admErr=''; document.querySelector('#adminModal').classList.add('show'); renderAdmin(); return document.querySelector('#admBody').innerText; })()")
        check('관리자 창: 로컬 캐릭터 데이터 안 씀(숨은 이름 없음)', '관리자본캐' in adm and not any(h in adm for h in HID), adm[:200])
        pg.evaluate("document.querySelector('#adminModal').classList.remove('show')")
        pg.evaluate("accounts()[1].key='test_apikey2_0123456789abcdef'; save(); tab='total'; render()"); pg.wait_for_timeout(300)
        g2=pg.evaluate("totalData().grand"); ms2=pg.evaluate("(S.missW||[]).map(r=>activeMiss(r))[0].list.map(x=>x.name)"); sc2=pg.evaluate("suroChars().map(c=>c.name)")
        check('키 다시 넣으면 복귀: 합계·빠뜨린 보스메소·수로', g2>=14*E+99*E+76*E and '키없는캐' in ms2 and '삭제계정캐' not in ms2 and sc2==['보이는캐','키없는캐'], [g2,ms2,sc2])
        mn=pg.evaluate("(()=>{ const c=S.characters.find(x=>x.id==='h2'); c.bosses.will={enabled:true,diff:'hard',party:1}; return missNow('w').list.map(x=>x.id); })()")
        check('missNow 는 id 와 함께 저장(숨은 캐릭터도 저장, 화면에서 거름)', 'h2' in mn, mn)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e)); fails.append('exception')
finally: srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
