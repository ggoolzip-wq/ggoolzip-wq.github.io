# test_b287: (1) 사용자 확인 보스 맵 표 — 리멘만 읽히면 듄켈, 소울 조각이 검은 마법사면 검은 마법사 / 맵 이름 > 지역 이름 / 힐라(일간) ≠ 진 힐라
#            (2) 바닥 아이템 (파티 격파는 자동 줍기 안 됨): 실제 화면 — 앱솔 무기·방어구 상자, 흉성 단편 조각 / 닮은 바닥(벨로나 조각) 오인식 없음
#            (3) 추적·중복: 같은 자리 다시 보여도 1번, 배너로 이미 센 건 바닥에서 다시 안 셈  (4) Worker 결과 = 메인 스레드 결과, 분석 fps 표시
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b287'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""(o)=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
  const A=window.AR; A.recent={}; A.recentVia={}; A.logPrev=[]; A.log=[]; A.tracks=[]; A.hits={}; A.det={cid:'c0',boss:o.boss||'',diff:o.diff||'',src:'t'}; A.detT=Date.now(); A.cidT=Date.now(); A.cfg.on=true; if(o.worker===false){ A.wk=null; } }"""
SCAN="""async f=>{ const im=new Image(); im.src='fx/'+f; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0); window._cv=cv;
  const h=await arItemScan(cv); return h.map(x=>[x.k,+x.score.toFixed(3),x.x+x.w/2|0,x.y+x.h/2|0]); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    # 1) 맵 표
    D=lambda t: pg.evaluate("t=>{ const r=arDetectBoss(t); return r&&[r.boss,r.diff,r.src]; }",t)
    cases=[('해방된 나무 정상 <노멀>','limbo','normal'),('탈라하트 폭풍이 사그라든 여명 <하드>','baldrix','hard'),('기어드락 적막한 용광로 <노멀>','jupiter','normal'),('검은 바다 잠든 환상 <노멀>','star','normal'),
           ('레헬른 악몽의 시계탑 <하드>','lucid','hard'),('존재하지 않는 공간 <익스트림>','blackmage','extreme'),
           ('도원경 빛을 되찾은 사계 <이지>','kaling','easy'),('고통의 미궁 욕망의 제단 <하드>','jinhilla','hard'),('리멘 끝에 가까운 곳 <하드>','dunkel','hard')]
    for t,bid,df in cases:
        r=D(t); check(f"맵 '{t}' → {bid} {df}", r and r[0]==bid and (not df or r[1]==df) and r[2]=='보상 맵', r)
    for t in ['리멘 <하드>','어둠의 왕좌','카로테 격전의 마천루']:
        r=D(t); check(f"b291: 보상 맵 아님 '{t}' → 무시", r is None, r)
    pg.evaluate(SETUP,{}); pg.evaluate("()=>{ window.AR.det.boss=''; arLogStep('소비 아이템을 얻었습니다 (힐라의 소울 조각)'); }")
    check("'(힐라의 소울 조각)'(일간 하드 힐라) → 진 힐라로 안 바꿈", pg.evaluate("window.AR.det.boss")!='jinhilla', pg.evaluate("window.AR.det"))
    pg.evaluate(SETUP,{}); pg.evaluate("()=>{ window.AR.det.boss=''; arLogStep('소비 아이템을 얻었습니다 (진 힐라의 소울 조각)'); }")
    check("b291: 소울 조각으로 보스 안 정함", pg.evaluate("window.AR.det.boss")=='', pg.evaluate("window.AR.det"))
    wk=pg.evaluate("BOSSES.filter(b=>/힐라/.test(b.name)).map(b=>[b.id,b.name,b.type,b.diffs])")
    check('주간·월간 보스 목록의 힐라는 진 힐라 노멀·하드뿐 (하드 힐라는 일간)', wk==[['jinhilla','진 힐라','weekly',['normal','hard']]], wk)
    # 2) 바닥 아이템
    pg.evaluate(SETUP,{'boss':'lotus','diff':'hard'}); h=pg.evaluate(SCAN,'s04.jpg'); ks=sorted(x[0] for x in h)
    check('b288 s04 바닥: 앱솔 상자(기록 안 되는 아이템)는 아예 안 찾음 → 결과 없음', ks==[], h)
    check('Worker 로 돌았음', pg.evaluate("!!window.AR.wk"))
    pg.evaluate(SETUP,{'boss':'lotus','diff':'hard','worker':False}); h2=pg.evaluate(SCAN,'s04.jpg')
    check('메인 스레드(Worker 없음) 결과도 같음', sorted(x[0] for x in h2)==ks, h2)
    pg.evaluate("()=>{ window.AR.wk=undefined; }")
    pg.evaluate(SETUP,{'boss':'star','diff':'normal'}); h=pg.evaluate(SCAN,'s11.jpg')
    check('b288 s11 바닥: 에테르넬 단편 조각(정보용)도 안 찾음', h==[], h)
    pg.evaluate(SETUP,{'boss':'bellona','diff':'normal'}); h=pg.evaluate(SCAN,'s13.jpg')
    check('s13: 닮은 바닥 무늬(벨로나 조각 모양) 오인식 없음', h==[], h)
    # 3) 추적·중복
    pg.evaluate(SETUP,{'boss':'lotus','diff':'extreme'})
    n=pg.evaluate("""()=>{ const H=[{k:'tc',score:.86,x:190,y:740,w:67,h:67}]; const t=Date.now(); arTrack(H,1080,t); arTrack([{...H[0],x:194}],1080,t+500); arTrack([{...H[0],x:196}],1080,t+1000);
       return window.AR.log.filter(l=>l.includes(ITEMS.tc.n)).length; }""")
    check('같은 자리 바닥 아이템 3번 보여도 1번만', n==1, pg.evaluate("window.AR.log"))
    pg.evaluate(SETUP,{'boss':'adversary','diff':'normal'})
    lg=pg.evaluate("""()=>{ arRecord('r_white',.8,'배너 순간'); const t=Date.now(); const H=[{k:'r_white',score:.8,x:900,y:850,w:71,h:71}]; arTrack(H,1080,t); arTrack(H,1080,t+400); return window.AR.log; }""")
    check('배너로 센 아이템은 바닥에서 다시 안 셈', len([l for l in lg if '자동 기록' in l])==1, lg)
    # 4) 패널: 분석 fps · 놓친 프레임 · 미리보기 끄기
    pg.evaluate("()=>{ window.AR.pf={t0:performance.now()-2000,frames:120,watched:118,missed:2,bannerMs:30,banners:3,items:2,iskip:1,last:null}; window.AR.video={}; arPanel(true); }")
    txt=pg.inner_text('#arPanel .ar-perf'); check("패널에 '분석 fps · 놓친 프레임' 표시", '분석 fps' in txt and '놓친 프레임' in txt and '2' in txt, txt)
    check('미리보기 끄기 체크박스', pg.locator('#arPanel input[name=prevOn]').count()==1)
    pg.locator('#arPanel input[name=prevOn]').uncheck(); check('미리보기 끄면 미리보기 캔버스 없음', pg.locator('#arPanel .ar-prev').count()==0 and pg.evaluate("window.AR.cfg.prev")==0)
    pg.evaluate("()=>{ window.AR.video=null; }")
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
