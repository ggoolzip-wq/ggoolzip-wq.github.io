# test_b288: (1) 화면 공유 연결 핫픽스 — 헤더 버튼 한 번에 getDisplayMedia, frameRate 거절 시 재시도, 끊긴 스트림 정리 후 재연결, 실패 이유 표시, Worker 실패 → 메인 스레드
#            (2) 모양 같은 아이콘(해머·링 상자 등) 색 단계 — 모든 짝 구분 (흐림·가림·밝기)  (3) 템플릿 = 기록 가능한 드롭 표 아이템
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR'); PROBE=os.environ.get('PROBE')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SCENE="""()=>{ const cv=window._scene||(window._scene=document.createElement('canvas')); cv.width=1280; cv.height=720; const g=cv.getContext('2d'); g.fillStyle='#2b3a55'; g.fillRect(0,0,1280,720);
  g.fillStyle='rgba(0,0,0,.6)'; g.fillRect(0,0,256,32); g.fillStyle='#fff'; g.font='bold 15px sans-serif'; g.fillText('레헬른 악몽의 시계탑 <하드>',8,22); return 1; }"""
STUB="""(mode)=>{ window._gdm=[]; navigator.mediaDevices.getDisplayMedia=function(c){ window._gdm.push(JSON.stringify(c)); window._gdmSync=!window._afterAwait;
  if(mode==='overc'&&c.video&&c.video.frameRate) return Promise.reject(Object.assign(new Error('fr'),{name:'OverconstrainedError'}));
  if(mode==='deny') return Promise.reject(Object.assign(new Error('Permission denied'),{name:'NotAllowedError'}));
  return Promise.resolve(window._scene.captureStream(4)); }; }"""
VAR="""async ([k,mode,grp])=>{ window.arCandidates=()=>grp.map(x=>({k:x,b:'t',info:false}));
  const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); const gr=g.createLinearGradient(0,0,0,1080); gr.addColorStop(0,'#33405a'); gr.addColorStop(1,'#5a4a32'); g.fillStyle=gr; g.fillRect(0,0,1920,1080);
  for(let i=0;i<60;i++){ g.fillStyle=`hsl(${i*47%360},25%,${25+i%20}%)`; g.fillRect((i*131)%1920,(i*71)%640,80,24); } g.fillStyle='#6b5a3a'; g.fillRect(0,880,1920,40);
  const im=new Image(); im.src=ITEM_ICONS[k]; await im.decode(); const c2=document.createElement('canvas'); c2.width=c2.height=71; const g2=c2.getContext('2d');
  g2.filter=mode==='blur'?'blur(1px)':mode==='dark'?'brightness(0.8)':mode==='bright'?'brightness(1.2)':'none'; g2.drawImage(im,0,0,71,71); g2.filter='none';
  if(mode==='occ'){ g2.fillStyle='#222'; g2.fillRect(0,50,30,21); }
  g.drawImage(c2,930,809); const h=await arItemScan(cv); return h.map(x=>[x.k,+x.score.toFixed(3),x.amb||null,(x.vd||[]).map(v=>[v[0],+(+v[1]).toFixed(1)])]); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SCENE)
    pg.evaluate("""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
      S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render(); }""")
    # 1) 연결
    pg.evaluate(STUB,'ok'); pg.click('#tabs [data-tab=auto]'); pg.wait_for_selector('#arGuide [data-arg=ok]'); pg.click('#arGuide [data-arg=ok]')
    pg.wait_for_function("window.AR.stream&&window.AR.video",timeout=15000); pg.wait_for_timeout(2500)
    st=pg.evaluate("({gdm:window._gdm,sync:window._gdmSync,panel:!!document.querySelector('#arPanel'),txt:document.querySelector('#arPanel')?.innerText||''})")
    check('헤더 버튼 한 번 → getDisplayMedia 1번 (클릭 처리 안에서 바로)', len(st['gdm'])==1 and st['sync'], st['gdm'])
    check('frameRate 는 ideal (exact 아님)', 'ideal' in st['gdm'][0] and 'exact' not in st['gdm'][0], st['gdm'])
    check('패널: 연결됨 + 분석 fps 표시', '연결됨' in st['txt'] and '분석' in st['txt'] and 'fps' in st['txt'], st['txt'][:300])
    if SD: os.makedirs(SD,exist_ok=True); pg.screenshot(path=os.path.join(SD,'connected.png'))
    # 끊긴 스트림 (트랙 ended 이벤트 없이 멈춤) → 다시 누르면 새로 연결
    pg.evaluate("()=>{ const t=window.AR.stream.getVideoTracks()[0]; t.removeEventListener('ended',arDisconnect); t.stop(); }")
    pg.evaluate(STUB,'ok'); pg.evaluate("arPanel(false)") if pg.evaluate("typeof arPanel")=='function' else None
    pg.click('#tabs [data-tab=auto]'); pg.wait_for_selector('#arGuide [data-arg=ok]'); pg.click('#arGuide [data-arg=ok]'); pg.wait_for_timeout(800)
    s2=pg.evaluate("({n:window._gdm.length,live:window.AR.stream?.getVideoTracks()[0]?.readyState})")
    check('끊긴 스트림이 남아 있어도 → 다시 연결 (예전: 패널만 열리고 아무 일 없음)', s2['n']==1 and s2['live']=='live', s2)
    pg.evaluate("arDisconnect()")
    # frameRate 거절 → 제약 없이 재시도
    pg.evaluate(STUB,'overc'); pg.click('#tabs [data-tab=auto]'); pg.wait_for_selector('#arGuide [data-arg=ok]'); pg.click('#arGuide [data-arg=ok]'); pg.wait_for_function("window.AR.stream&&window.AR.video",timeout=10000)
    g=pg.evaluate("window._gdm"); check('frameRate 거절(OverconstrainedError) → {video:true} 로 재시도해 연결', len(g)==2 and 'frameRate' not in g[1], g)
    pg.evaluate("arDisconnect()")
    # 거부 → 이유 표시
    pg.evaluate(STUB,'deny'); pg.click('#tabs [data-tab=auto]'); pg.wait_for_selector('#arGuide [data-arg=ok]'); pg.click('#arGuide [data-arg=ok]'); pg.wait_for_timeout(500)
    t=pg.evaluate("document.querySelector('#arPanel')?.innerText||''")
    check('공유 취소·차단 → 패널에 이유 표시 (조용히 실패 안 함)', '화면 공유' in t and ('취소' in t or '막혀' in t), t[:300])
    check('지원 안 하는 브라우저 문구', pg.evaluate("()=>{ const o=navigator.mediaDevices.getDisplayMedia; navigator.mediaDevices.getDisplayMedia=undefined; arConnect(); const r=window.AR.connErr; navigator.mediaDevices.getDisplayMedia=o; return r; }").find('지원')>=0)
    # Worker 실패 → 메인 스레드
    pg.evaluate("()=>{ window.AR.det={cid:'c0',boss:'lucid',diff:'hard',src:'t'}; }")
    r=pg.evaluate("""async()=>{ const RW=window.Worker; window.Worker=function(){ throw new Error('worker blocked'); }; window.AR.wk=undefined; window.AR.wkOff=null;
      const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); g.fillStyle='#345'; g.fillRect(0,0,1920,1080); const im=new Image(); im.src=ITEM_ICONS.belt; await im.decode(); g.drawImage(im,930,809,71,71);
      const h=await arItemScan(cv); window.Worker=RW; return {k:h.map(x=>x.k), wk:window.AR.wk||null}; }""")
    check('Worker 생성 실패 → 메인 스레드로 같은 결과 (몽환의 벨트)', 'belt' in r['k'] and not r['wk'], r)
    r=pg.evaluate("""async()=>{ window.AR.wk=undefined; window.AR.wkOff=null; window.AR.wkFail=0; const w=arWorker(); if(!w) return {skip:1}; w.postMessage=function(){}; /* 답이 안 옴 */
      const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); g.fillStyle='#345'; g.fillRect(0,0,1920,1080); const im=new Image(); im.src=ITEM_ICONS.belt; await im.decode(); g.drawImage(im,930,809,71,71);
      const t=performance.now(); await arItemScan(cv); await arItemScan(cv); const h=await arItemScan(cv); return {k:h.map(x=>x.k), off:!!window.AR.wkOff, ms:performance.now()-t}; }""")
    check('Worker 가 답을 안 줌 → 시간 초과 2번이면 Worker 끄고 메인 스레드로', r.get('off') and 'belt' in r.get('k',[]), r)
    # 3) 템플릿 = 기록 가능한 아이템
    q=pg.evaluate("""()=>{ const rec=new Set(); for(const b of BOSSES) for(const d of b.diffs||[]) for(const k of dropsFor(b,d)) if(ITEM_ICONS[k]) rec.add(k);
      const cand=new Set(); const D=window.AR.det; for(const b of BOSSES) for(const d of b.diffs||[]){ window.AR.det={boss:b.id,diff:d,cid:'c0',src:'t'}; for(const c of arCandidates(true)) cand.add(c.k); } window.AR.det=D;
      return {rec:[...rec].sort(), cand:[...cand].sort(), arr:arRecordable().size, bad:[...cand].filter(k=>/^(ab_|ar_)/.test(k)||/_f$/.test(k))}; }""")
    check('찾는 아이템 = 대시보드 드롭 표에서 기록 가능한 아이템 (그 외 템플릿 없음)', q['rec']==q['cand'] and q['arr']==len(q['rec']), [x for x in q['cand'] if x not in q['rec']]+[x for x in q['rec'] if x not in q['cand']])
    check('앱솔·아케인 상자·에테르넬 조각 템플릿 없음', q['bad']==[], q['bad'])
    # 2) 색 단계
    groups=pg.evaluate("AR_VAR.map(g=>g.filter(k=>ITEM_ICONS[k]&&arRecordable().has(k))).filter(g=>g.length>1)")
    if PROBE: print('GROUPS',groups)
    bad=[]; ambig=[]; miss=[]; n=0
    for grp in groups:
        for k in grp:
            for mode in ['plain','blur','occ','dark','bright']:
                h=pg.evaluate(VAR,[k,mode,grp]); n+=1
                if PROBE: print(k,mode,h)
                top=h[0] if h else None
                if not top: miss.append((k,mode)); continue
                if top[2]:
                    if k not in top[2]: bad.append((k,mode,top))
                    else: ambig.append((k,mode))
                elif top[0]!=k: bad.append((k,mode,top))
    check(f'닮은 아이콘 묶음 {len(groups)}개 · {n}경우: 다른 아이콘으로 자동 기록 0번', not bad, bad)
    check('못 찾음(가림 등) ≤ 10% — 못 찾으면 기록 안 함일 뿐 틀린 기록은 아님', len(miss)<=n*0.1, miss)
    check('또렷한 아이콘(흐림·가림·밝기 포함)은 대부분 자동 구분 (애매해서 직접 고르기 ≤ 10%)', len(ambig)<=n*0.1, ambig)
    # 직접 고르기 칩
    pg.evaluate("""()=>{ const A=window.AR; A.det={cid:'c0',boss:'lucid',diff:'hard',src:'t'}; A.amb=[]; window.arCandidates=()=>[{k:'belt',b:'lucid',info:false},{k:'h_belt',b:'lucid',info:false}]; arPanel(true); arPick({k:'belt',score:.9,amb:['belt','h_belt']},'바닥'); }""")
    chips=pg.evaluate("[...document.querySelectorAll('#arPanel [data-ar^=\"pick:\"]')].map(b=>b.dataset.ar)")
    check('애매하면 자동 기록 대신 직접 고르기 버튼 2개', len(chips)==2, chips)
    nb=pg.evaluate("()=>{ const A=window.AR; A.det={cid:'c0',boss:'',diff:'',src:''}; A.recent={}; const n0=JSON.stringify(S.characters[0].drops); arPick({k:'legacy',score:.9},'배너 순간'); return [n0==JSON.stringify(S.characters[0].drops), A.cfg.banner.y>=.145]; }")
    check('보스 확인 전엔 자동 기록 안 함 (타이머 상자 → 불멸의 유산 오인식 막음) · 배너 영역은 타이머 아래부터', nb==[True,True], nb)
    if errs: print('ERRS',errs)
    check('페이지 오류 없음', not [e for e in errs if 'worker blocked' not in e], errs)
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
