# test_b234_purge (b234 → b235): 🔄 캐릭터 동기화 버튼을 30일 동안 안 누른 계정 → 기록 삭제 (본계정 포함). 키 삭제·로그아웃은 타이머와 무관.
# 키 없는 캐릭터는 합계에서 제외(기록 보존), 같은 넥슨 계정 새 키 → 다시 연결·기록 그대로. 본계정 줄 = '로그아웃' 버튼.
# MBT_SHOT=경로 → 삭제 후 결정석 분석 탭 · MBT_SHOTBTN=경로 → API 키 목록(본계정 로그아웃 버튼) · MBT_ROOT=다른 빌드(변경 전 사진용)
import os, sys, subprocess, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
E=100000000; DAY=86400000; NOW=int(time.time()*1000)
def ch(id,name,acc,ocid=None): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'ocid':ocid,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{'swoo|x':1},'drev':{'swoo|x':{'m':E,'a':1,'p':1,'i':'x'}},'sync':{}}
def pc(id,name,m): return {'id':id,'name':name,'meso':m,'count':1,'bosses':['스우(하드)'],'bvals':[m],'items':{}}
H=[{'week':'2026-09-28','perChar':[pc('c1','본캐',5*E),pc('h1','부계캐',9*E),pc('h2','지운캐',7*E)]},{'week':'2026-10-05','perChar':[pc('h2','지운캐',3*E)]}]
for h in H: h.update(total=sum(p['meso'] for p in h['perChar']),cleared=len(h['perChar']),crystals=len(h['perChar']),items=0)
ST={'version':5,'theme':'dark','activeId':'h2','startWeek':'2026-09-28','history':H,
 'monthHistory':[{'month':'2026-09','total':8*E,'cleared':2,'perChar':[pc('c1','본캐',E),pc('h2','지운캐',7*E)]}],
 'missW':[{'week':'2026-09-28','date':'2026.10.01','n':4,'meso':16*E,'list':[{'id':'c1','name':'본캐','n':1,'meso':E},{'id':'h1','name':'부계캐','n':1,'meso':5*E},{'id':'h2','name':'지운캐','n':1,'meso':7*E},{'name':'지운캐','n':1,'meso':3*E}]},
          {'week':'2026-10-05','date':'2026.10.08','n':1,'meso':2*E,'list':[{'name':'지운캐','n':1,'meso':2*E}]}],
 'missM':[{'month':'2026-09','date':'2026.10.01','n':1,'meso':7*E,'list':[{'id':'h2','name':'지운캐','n':1,'meso':7*E}]}],'worldOrder':[],
 'characters':[ch('c1','본캐','a1'),ch('h1','부계캐','a2','oc-h1'),ch('h2','지운캐','a3'),ch('k1','키부캐','a4')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'test_main_0123456789abcdef','main':True},{'id':'a2','label':'부','key':''},{'id':'a4','label':'부2','key':'test_alt4_0123456789abcdef'}],'goneAccs':['a3'],
   'keyGoneAt':{'a2':NOW-40*DAY},'syncAt':{'a1':NOW-5*DAY,'a3':NOW-31*DAY,'a4':NOW-2*DAY}}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1600},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    dlg=[]; pg.on('dialog',lambda d:(dlg.append(d.message),d.accept()))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900)
    g=lambda js: pg.evaluate(js)
    if os.environ.get('MBT_SHOTBTN'):
        g("try{openImport()}catch(e){} renderAccList()"); pg.wait_for_timeout(400)
        el=pg.locator('#accList'); el.screenshot(path=os.environ['MBT_SHOTBTN'])
        if os.environ.get('MBT_ROOT'): b.close(); srv.terminate(); print('SHOT only'); sys.exit(0)
        g("$('#importModal').classList.remove('show')")
    # 1) 불러올 때: a3(동기화 31일 전) 삭제, a2(키 삭제 40일 전이지만 동기화 기록 없음 → 지금부터) 보존, b234 keyGoneAt 버림
    check('31일 동기화 안 한 계정 캐릭터 삭제(드롭·판매 포함)', g("S.characters.map(c=>c.id)")==['c1','h1','k1'], g("S.characters.map(c=>c.id)"))
    check('주간 기록 perChar 에서 삭제·합계 다시 계산', g("S.history.map(h=>[h.week,h.total,h.cleared,h.crystals,h.perChar.map(p=>p.id)])")==[['2026-09-28',14*E,2,2,['c1','h1']]], g("S.history.map(h=>[h.week,h.total,h.perChar.map(p=>p.id)])"))
    check('월간 기록 삭제·합계', g("S.monthHistory.map(h=>[h.total,h.perChar.map(p=>p.id)])")==[[E,['c1']]], g("S.monthHistory"))
    check('빠뜨린 보스메소(주간) 삭제·다시 계산', g("S.missW.map(r=>[r.week,r.n,r.meso,r.list.map(x=>x.name)])")==[['2026-09-28',2,6*E,['본캐','부계캐']]], g("S.missW"))
    check('빠뜨린 보스메소(월간) 0 줄 유지', g("S.missM.map(r=>[r.n,r.meso,r.list.length])")==[[0,0,0]], g("S.missM"))
    check('b234 keyGoneAt 제거, 키 삭제 시각은 타이머 아님', g("S.settings.keyGoneAt")==None and g("S.characters.some(c=>c.id==='h1')"))
    a2=g("S.settings.syncAt.a2"); check('기록 없던 칸 = 지금부터 셈(바로 안 지움)', a2 and abs(a2-int(time.time()*1000))<60000, g("S.settings.syncAt"))
    check('a3 타이머·goneAccs 정리, activeId 정리', 'a3' not in g("S.settings.syncAt") and g("S.settings.goneAccs")==[] and g("S.activeId")=='c1', g("[S.settings.syncAt,S.settings.goneAccs,S.activeId]"))
    check('키 없는 h1: 화면 합계엔 없음·저장 기록엔 있음', g("S.history[0].perChar.some(p=>p.id==='h1')") and not g("activeIds().has('h1')") and not g("totalData().chars.some(o=>o.name==='부계캐')"))
    # 2) 🔄 버튼 = 키 있는 모든 칸 타이머 리셋 (키 없는 a2 는 리셋 안 됨)
    g("S.settings.syncAt.a1=Date.now()-29*864e5; S.settings.syncAt.a4=Date.now()-29*864e5; S.settings.syncAt.a2=Date.now()-29*864e5; render()")
    # b236: 끝난 syncAll 마다(자동 동기화 포함) = 리셋. 넥슨 호출은 가짜(성공)
    g("window.__sp=0; const of=svFetch; svFetch=(u,o)=>{ if(u==='/api/sync-press') window.__sp++; return of(u,o); }; listAccount=async()=>[]; assignFromList=()=>0; schedApply=async()=>0; fetchBasic=async()=>{}; fetchMedal=async()=>{}; schedLookback=async()=>0; S.characters.forEach(c=>c.ocid=c.ocid||('oc-'+c.id))")
    g("syncAll({silent:true})"); pg.wait_for_function("!syncing",timeout=10000); pg.wait_for_timeout(200)
    sa=g("S.settings.syncAt"); t=int(time.time()*1000)
    check('자동 동기화(silent) 끝 → 본계정·키 있는 부계정 = 지금', abs(sa['a1']-t)<60000 and abs(sa['a4']-t)<60000, sa)
    g("S.settings.syncAt.a1=Date.now()-29*864e5; accById('a4').status=null; listAccount=async a=>{ if(a.id==='a4') throw new Error('x'); return []; }; Object.keys(listCache).forEach(k=>delete listCache[k])"); 
    g("S.characters.find(c=>c.id==='k1').ocid=null; syncAll({silent:true})"); pg.wait_for_function("!syncing",timeout=10000); pg.wait_for_timeout(200)
    sa2=g("S.settings.syncAt"); check('오류 난 계정은 리셋 안 됨, 성공 계정은 리셋', abs(sa2['a1']-t)<60000 and sa2['a4']==sa['a4'], sa2)
    g("S.characters.find(c=>c.id==='k1').ocid='oc-k1'; listAccount=async()=>[]")
    check('키 없는 칸은 🔄 로 리셋 안 됨', t-sa['a2']>28*DAY, sa)
    # 3) 새 키(같은 넥슨 캐릭터 ocid)를 30일 안에 등록 → 다시 연결·기록 그대로·합계 복귀
    g("accForget([accById('a2')]); const n={id:'a9',label:'새키',key:'test_new_0123456789abcdef'}; accounts().push(n); keyRelink(n,[{ocid:'oc-h1'}]); render()")
    check('새 키 → h1 다시 연결·타이머 이어감', g("S.characters.find(c=>c.id==='h1').accId")=='a9' and g("S.settings.syncAt.a9")==sa['a2'], g("[S.characters.find(c=>c.id==='h1'),S.settings.syncAt]"))
    check('다시 연결 → 합계에 다시 포함·기록 그대로', g("activeIds().has('h1')") and g("totalData().chars.some(o=>o.name==='부계캐')") and g("S.history[0].perChar.some(p=>p.id==='h1')"))
    # 4) 부계정 키 삭제 = 타이머 시작/변경 없음, 30일-1ms 보존·30일 삭제
    g("S.settings.syncAt.a9=Date.now(); renderAccList()")
    g("document.body.insertAdjacentHTML('beforeend','<button id=\"x235\" data-accdel=\"a9\">x</button>'); document.getElementById('x235').click()"); pg.wait_for_timeout(200)
    t0=g("S.settings.syncAt.a9")
    check('부계정 키 삭제 확인창: 30일 삭제 문구 없음', dlg and '30일' not in dlg[-1] and '삭제할까요' in dlg[-1], dlg[-1:] )
    check('부계정 키 삭제 → 기록 숨김, 타이머 그대로', not g("activeIds().has('h1')") and g("S.characters.some(c=>c.id==='h1')") and not g("S.settings.keyGoneAt"))
    g(f"S.settings.syncAt.a1={t0}+30*864e5; S.settings.syncAt.a4={t0}+30*864e5; syncGoneTick({t0}+30*864e5-1)"); check('30일 - 1ms: 보존', g("S.characters.some(c=>c.id==='h1')"))
    g(f"S.settings.syncAt.a1={t0}+30*864e5; S.settings.syncAt.a4={t0}+30*864e5; syncGoneTick({t0}+30*864e5)")
    check('30일 동기화 안 함: 부계정 캐릭터·기록 삭제', not g("S.characters.some(c=>c.id==='h1')") and not g("S.history.some(h=>h.perChar.some(p=>p.id==='h1'))"), g("S.characters.map(c=>c.id)"))
    ids=(g(f"syncGoneTick({t0}+30*864e5+1)"), g("S.characters.map(c=>c.id)"))[1]; check('idempotent', ids==['c1','k1'], ids)
    # 5) 본계정 줄 = 로그아웃 버튼 (삭제 문구 없음), 누르면 타이머 그대로·데이터 보존
    g("try{openImport()}catch(e){} renderAccList()"); pg.wait_for_timeout(200)
    lb=g("(document.querySelector('[data-accdel=\"a1\"]')||{}).textContent"); cl=g("(document.querySelector('[data-accdel=\"a1\"]')||{}).className")
    check('본계정 버튼 = 로그아웃(ghost)', lb=='로그아웃' and 'danger' not in cl and 'ghost' in cl, (lb,cl))
    check('부계정 버튼 = 삭제 그대로', g("(document.querySelector('[data-accdel=\"a4\"]')||{}).textContent")=='삭제')
    if os.environ.get('MBT_SHOTBTN'): pg.locator('#accList').screenshot(path=os.environ['MBT_SHOTBTN'])
    before=g("JSON.stringify(S.settings.syncAt)")
    pg.locator('[data-accdel="a1"]').first.click(force=True); pg.wait_for_timeout(200)
    check('로그아웃 확인창: 로그아웃·부계정 함께, 삭제 문구 없음', '로그아웃' in dlg[-1] and '부계정' in dlg[-1] and '삭제' not in dlg[-1], dlg[-1])
    check('본계정 로그아웃 → 타이머 그대로·keyGoneAt 없음·기록 보존', g("JSON.stringify(S.settings.syncAt)")==before and not g("S.settings.keyGoneAt") and g("S.characters.length")==2 and not g("accById('a1').key"), [g("JSON.stringify(S.settings.syncAt)"),before,g("S.characters.length")])
    # 6) 본계정(서버 아닌 모드): 30일 동기화 안 하면 본계정 캐릭터·기록 삭제
    g(f"syncGoneTick(S.settings.syncAt.a1+31*864e5); save(); render()")
    check('본계정 30일 지남: 기록 전부 삭제', g("[S.characters.length,S.history.length,S.monthHistory.length,(S.missW||[]).length]")==[0,0,0,0], g("[S.characters,S.history,S.missW]"))
    if os.environ.get('MBT_SHOT'): g("$('#importModal').classList.remove('show'); tab='total'; render()"); pg.wait_for_timeout(300); pg.screenshot(path=os.environ['MBT_SHOT'],full_page=False)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
