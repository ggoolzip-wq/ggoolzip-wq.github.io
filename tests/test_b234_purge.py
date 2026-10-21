# test_b234_purge (b234): API 키가 빠진 계정 30일 → 기록 삭제 (본계정 포함). 30일 전엔 숨김·보존, 다시 넣으면 복귀, 지나면 캐릭터·지난 기록·빠뜨린 보스메소 삭제
# MBT_SHOT=경로 → 삭제 후 결정석 분석 탭 스크린샷
import os, sys, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=9341
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
E=100000000; DAY=86400000; NOW=int(time.time()*1000)
def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{'swoo|x':1},'drev':{'swoo|x':{'m':E,'a':1,'p':1,'i':'x'}},'sync':{}}
def pc(id,name,m): return {'id':id,'name':name,'meso':m,'count':1,'bosses':['스우(하드)'],'bvals':[m],'items':{}}
H=[{'week':'2026-09-28','perChar':[pc('c1','본캐',5*E),pc('h1','부계캐',9*E),pc('h2','지운캐',7*E)]},{'week':'2026-10-05','perChar':[pc('h2','지운캐',3*E)]}]
for h in H: h.update(total=sum(p['meso'] for p in h['perChar']),cleared=len(h['perChar']),crystals=len(h['perChar']),items=0)
ST={'version':5,'theme':'dark','activeId':'h2','startWeek':'2026-09-28','history':H,
 'monthHistory':[{'month':'2026-09','total':8*E,'cleared':2,'perChar':[pc('c1','본캐',E),pc('h2','지운캐',7*E)]}],
 'missW':[{'week':'2026-09-28','date':'2026.10.01','n':4,'meso':16*E,'list':[{'id':'c1','name':'본캐','n':1,'meso':E},{'id':'h1','name':'부계캐','n':1,'meso':5*E},{'id':'h2','name':'지운캐','n':1,'meso':7*E},{'name':'지운캐','n':1,'meso':3*E}]},
          {'week':'2026-10-05','date':'2026.10.08','n':1,'meso':2*E,'list':[{'name':'지운캐','n':1,'meso':2*E}]}],
 'missM':[{'month':'2026-09','date':'2026.10.01','n':1,'meso':7*E,'list':[{'id':'h2','name':'지운캐','n':1,'meso':7*E}]}],'worldOrder':[],
 'characters':[ch('c1','본캐','a1'),ch('h1','부계캐','a2'),ch('h2','지운캐','a3')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'test_main_0123456789abcdef','main':True},{'id':'a2','label':'부','key':''}],'goneAccs':['a3'],
   'keyGoneAt':{'a2':NOW-10*DAY,'a3':NOW-31*DAY}}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1600},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog',lambda d:d.accept())
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900)
    g=lambda js: pg.evaluate(js)
    # 1) 불러올 때: a3(31일 지남) 삭제, a2(10일) 숨김·보존
    check('31일 지난 계정 캐릭터 삭제(드롭·판매 포함)', g("S.characters.map(c=>c.id)")==['c1','h1'], g("S.characters.map(c=>c.id)"))
    check('주간 기록 perChar 에서 삭제·합계 다시 계산', g("S.history.map(h=>[h.week,h.total,h.cleared,h.crystals,h.perChar.map(p=>p.id)])")==[['2026-09-28',14*E,2,2,['c1','h1']]], g("S.history.map(h=>[h.week,h.total,h.perChar.map(p=>p.id)])"))
    check('지운캐만 있던 주 기록은 없어짐', len(g("S.history"))==1)
    check('월간 기록 삭제·합계', g("S.monthHistory.map(h=>[h.total,h.perChar.map(p=>p.id)])")==[[E,['c1']]], g("S.monthHistory"))
    check('빠뜨린 보스메소(주간): id·이름만 줄 모두 삭제, n·meso 다시 계산', g("S.missW.map(r=>[r.week,r.n,r.meso,r.list.map(x=>x.name)])")==[['2026-09-28',2,6*E,['본캐','부계캐']]], g("S.missW"))
    check('빠뜨린 보스메소(월간): 그 달 기록이 남아 있으면 0으로(백필이 다시 만들지 않게)', g("S.missM.map(r=>[r.n,r.meso,r.list.length])")==[[0,0,0]], g("S.missM"))
    check('예약·goneAccs 정리, 숨은 a2 는 보존(10일)', g("[Object.keys(S.settings.keyGoneAt||{}),S.settings.goneAccs]")==[['a2'],[]], g("[S.settings.keyGoneAt,S.settings.goneAccs]"))
    check('activeId 정리', g("S.activeId")=='c1', g("S.activeId"))
    check('저장소에도 반영(localStorage)', g("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters.length")==2)
    check('숨은 h1: 화면 합계엔 없음·저장 기록엔 있음', g("totalData().grand")==g("totalData().grand") and g("S.history[0].perChar.some(p=>p.id==='h1')") and not g("activeIds().has('h1')"))
    # 2) 30일 전(29일째) = 그대로, 다시 넣으면 복귀
    check('29일째: 삭제 안 됨', (g("keyGoneTick(Date.now()+19*864e5)"), g("S.characters.some(c=>c.id==='h1')"))[1])
    g("accById('a2').key='test_alt_0123456789abcdef'; keyGoneTick(); render()")
    check('30일 안에 키 다시 등록 → 예약 취소·기록 복귀', not g("S.settings.keyGoneAt") and g("activeIds().has('h1')") and g("totalData().chars.some(o=>o.name==='부계캐')"), g("S.settings.keyGoneAt"))
    check('복귀 후 100일 지나도 키 있는 계정은 안 지움', (g("keyGoneTick(Date.now()+100*864e5)"), g("S.characters.length"))[1]==2)
    # 3) 가짜 시계: 키 삭제 버튼(부계정) → 30일 정각-1ms 보존, 30일 지나면 삭제, 다시 넣으면 새로 시작
    g("tab='settings'; try{openImport()}catch(e){} render(); renderAccList()")
    btn=pg.locator('[data-accdel="a2"]')
    if btn.count(): btn.first.click(force=True)
    else: g("document.body.insertAdjacentHTML('beforeend','<button id=\"x234\" data-accdel=\"a2\">x</button>'); document.getElementById('x234').click()")
    pg.wait_for_timeout(200)
    t0=g("S.settings.keyGoneAt&&S.settings.keyGoneAt.a2")
    check('키 삭제 버튼 → 삭제 시각 기록', bool(t0) and abs(t0-int(time.time()*1000))<60000, g("S.settings.keyGoneAt"))
    g(f"keyGoneTick({t0}+30*864e5-1)")
    check('30일 - 1ms: 보존', g("S.characters.some(c=>c.id==='h1')"))
    g(f"keyGoneTick({t0}+30*864e5)")
    check('30일 지남: 부계정 캐릭터·기록 삭제', not g("S.characters.some(c=>c.id==='h1')") and not g("S.history.some(h=>h.perChar.some(p=>p.id==='h1'))") and not g("S.missW.some(r=>r.list.some(x=>x.name==='부계캐'))"), g("[S.characters.map(c=>c.id),S.history]"))
    check('한 번 더 돌려도 그대로(idempotent)', (g(f"keyGoneTick({t0}+60*864e5)"), g("[S.characters.length,S.history[0].total]"))[1]==[1,5*E], g("[S.characters.length,S.history[0].total]"))
    # 4) 본계정(서버 아닌 모드): 대표 키 삭제 → 30일 뒤 본계정 캐릭터·기록 삭제
    g("render()"); g("document.body.insertAdjacentHTML('beforeend','<button id=\"y234\" data-accdel=\"a1\">x</button>'); document.getElementById('y234').click()"); pg.wait_for_timeout(200)
    t1=g("S.settings.keyGoneAt&&S.settings.keyGoneAt.a1")
    check('본계정 키 삭제 → 삭제 시각 기록, 데이터 보존', bool(t1) and g("S.characters.length")==1 and g("!accById('a1').key"), g("S.settings"))
    g(f"keyGoneTick({t1}+31*864e5); save(); render()")
    check('본계정 30일 지남: 기록 전부 삭제', g("[S.characters.length,S.history.length,S.monthHistory.length,(S.missW||[]).length]")==[0,0,0,0], g("[S.characters,S.history,S.missW]"))
    if os.environ.get('MBT_SHOT'): g("tab='total'; render()"); pg.wait_for_timeout(300); pg.screenshot(path=os.environ['MBT_SHOT'],full_page=False)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
