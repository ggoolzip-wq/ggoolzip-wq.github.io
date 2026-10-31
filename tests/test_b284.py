# test_b284: 실제 게임 화면 13장(찬란한 흉성 노멀 · 스우 익스트림, 보상 상자 개봉) → 맵/난이도 · 상태바 캐릭터 · 획득 로그(1순위) · 배너 아이콘 인식 + 쌓이는 로그 줄 한 번씩 세기
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR'); PROBE=os.environ.get('PROBE')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b284'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const C=(id,name,lv,bosses)=>({id,name,level:lv,job:'',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses,weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','터래플',289,{lotus:{enabled:true,diff:'extreme',party:1},star:{enabled:true,diff:'normal',party:1}}), C('c1','2터래플',285,{lotus:{enabled:true,diff:'extreme',party:1},star:{enabled:true,diff:'normal',party:1}}), C('c2','제트루',280,{lucid:{enabled:true,diff:'hard',party:1}})];
  S.activeId='c2'; save&&save(); render(); }"""
LOAD="""async (f)=>{ const im=new Image(); im.src='fx/'+f; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0); window.AR.testSrc=cv; window._fx=cv; return [cv.width,cv.height]; }"""
RUN="""async ()=>{ const A=window.AR; A.logPrev=[]; A.recent={}; A.det={cid:'',boss:'',diff:'',src:''}; A.hits={}; const cfgOn=A.cfg.on; A.cfg.on=false;
  await arFrame(window._fx,true); const lg=await arLogFrame(window._fx); A.cfg.on=cfgOn;
  return {map:A.mapText,name:A.nameText,det:A.det,log:A.logText,logItems:(lg||[]).map(x=>x.k+'x'+x.n),found:A.found,sc:A.lastScore}; }"""
# 정답 (사람이 화면 보고 적음)
STAR=('star','normal'); LOTUS=('lotus','extreme')
TRUTH={'s01':STAR,'s02':STAR,'s03':STAR,'s11':STAR}
for i in [4,5,6,7,8,9,10,12,13]: TRUTH['s%02d'%i]=LOTUS
CHAR={**{'s%02d'%i:'c1' for i in range(1,10)},**{'s%02d'%i:'c0' for i in range(10,14)}}  # Lv.285 2터래플 / Lv.289 터래플
BANNER_AB={'s07','s08','s13'}   # 가운데 배너 '앱솔랩스 방어구 상자를 획득했습니다.'
rows=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("ARX.cfg.boxGate=false")  # t522: 이 테스트는 아이템 인식만 봄 — 보상 상자 게이트는 test_b300
    pg.evaluate(SETUP)
    pg.evaluate("arOcrLoad()")
    pg.wait_for_function("window.AR.ocr||window.AR.ocrErr",timeout=60000)
    for n in sorted(TRUTH):
        wh=pg.evaluate(LOAD,n+'.jpg'); r=pg.evaluate(RUN)
        if PROBE: print(n,wh,json.dumps(r,ensure_ascii=False)[:900])
        bd=(r['det']['boss'],r['det']['diff']); ban=any(f[0]=='ab_a' and f[1]=='banner' for f in r['found'] or [])
        rows.append((n,bd==TRUTH[n],r['det']['cid'] in (CHAR[n],''),not any(f[0] in ('ab_a','ab_w') for f in r['found'] or []),'ab_a' in ' '.join(r['logItems']),r['map'],r['name']))
    print('ROWS',json.dumps(rows,ensure_ascii=False))
    ok=lambda i:sum(1 for r in rows if r[i])
    check('맵 → 보스·난이도 13장 모두', ok(1)==13, [r[0] for r in rows if not r[1]])
    check('상태바 → 2터래플/터래플 또는 없음 13장 (t574: 흐린 OCR 이면 없음 · 다른 캐릭터 절대 아님, 파티원 이름표 무시)', ok(2)==13, [r[0] for r in rows if not r[2]])
    check('b288 기록 가능 아이템만: 앱솔 상자 배너는 13장 어디서도 안 찾음', ok(3)==13, [r[0] for r in rows if not r[3]])
    check('b288: 로그의 앱솔랩스 방어구.. 줄도 무시', not any(r[4] for r in rows), [r[0] for r in rows if r[4]])
    # 빠르게 쌓이는 로그 (솔로 자동 줍기, 0.1초마다 갱신) — 줄마다 정확히 한 번
    sim=pg.evaluate("""()=>{ const A=window.AR; A.logPrev=[]; A.counted=[]; A.recent={}; A.det={cid:'c1',boss:'lotus',diff:'extreme',src:'t'};
      const a=ITEMS.tc.n.slice(0,6)+'..', b=ITEMS[dropsFor(BOSSES.find(x=>x.id==='lotus'),'extreme').find(k=>k!=='tc'&&ITEMS[k].n.slice(0,3)!==ITEMS.tc.n.slice(0,3))].n.slice(0,6)+'..'; window._ab=[a,b];
      const L=[a+' 아이템을 1 개 얻었습니다. ( 장비 )',b+' 아이템을 1 개 얻었습니다. ( 장비 )','튜링된 시간의.. 아이템을 7 개 얻었습니다. ( 기타 )',a+' 아이템을 1 개 얻었습니다. ( 장비 )'];
      const frames=[[L[0]],[L[0]],[L[0],L[1]],[L[0],L[1],L[2]],[L[0],L[1],L[2]],[L[1],L[2]],[L[1],L[2],L[3]],[L[2],L[3]],[L[2].replace('7','7 '),L[3]],[L[3]],[]];
      const per=frames.map(f=>arLogStep(f.join('\\n')).map(x=>x.k+'x'+x.n));
      return {per,tot:A.counted.map(x=>x.k), q:arLogItem(window._ab[1]+' 아이템을 3 개 얻었습니다.'), qa:arLogItem('앱솔랩스 무기 .. 아이템을 3 개 얻었습니다.')}; }""")
    print('SIM',sim)
    check('쌓이는 로그: 새 줄만 1번씩 (A 2번 · B 1번, 반복 프레임·OCR 흔들림 무시)', len(sim['tot'])==3 and sim['tot'].count('tc')==2, sim)
    check('N개 수량 읽기', (sim['q'] or {}).get('n')==3 and sim['q']['k']!='tc' and not sim['qa'], sim)
    # 기록 경로: 드롭 아이템 로그 줄 → changeDrop, 정보 칩(상자)은 기록 안 함, 배너+로그 겹쳐도 1번
    rec=pg.evaluate("""()=>{ const A=window.AR; A.cfg.on=true; A.logPrev=[]; A.recent={}; A.det={cid:'c1',boss:'lotus',diff:'extreme',src:'t'};
      arLogStep('앱솔랩스 방어구.. 아이템을 1 개 얻었습니다. ( 소비 )'); const n=ITEMS.tc.n.slice(0,6);
      arLogStep(n+'.. 아이템을 1 개 얻었습니다. ( 장비 )'); arLogStep(n+'.. 아이템을 1 개 얻었습니다. ( 장비 )\\n'+n+'.. 아이템을 1 개 얻었습니다. ( 장비 )');
      return {d1:S.characters[1].drops, d0:S.characters[0].drops, act:S.activeId, info:A.infoSeen||[]}; }""")
    print('REC',rec)
    check('로그 줄 → 2터래플 스우(익스) 드롭 기록 1번 (같은 아이템 연속은 중복막기)', rec['d1'].get('lotus|tc')==1 and not rec['d0'] and rec['act']=='c1', rec)
    check('b288: 앱솔랩스 상자는 정보 칩도 기록도 없음', not any('ab_' in x for x in rec['info']) and 'lotus|ab_a' not in rec['d1'], rec)
    if SD:
        os.makedirs(SD,exist_ok=True); pg.evaluate(LOAD,'s07.jpg'); pg.evaluate("window.AR.cfg.on=false"); pg.evaluate(RUN); pg.evaluate("arPanel(true); document.querySelector('#arPanel details').open=true; arPanelPaint(); document.querySelector('#arPanel details').open=true")
        pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(SD,'after_panel_s07.png'))
    check('JS 오류 없음', not errs, errs)
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
