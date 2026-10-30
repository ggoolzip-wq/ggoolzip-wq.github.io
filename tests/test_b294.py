# test_b294: 상태바 이름 빠른 인식 (실제 영상 v07·v10 트딕이 — 이름 칸 가렸다가 보이면 1초 안), 느슨한 이름 비교,
#            '보스 득템 자동 기록' 탭(길드 현황 자리) · 헤더 🎮 버튼 없음 · 안내 창 → 확인 클릭에서 바로 getDisplayMedia · 이미 연결이면 다시 안 물음 · 1080p 스크롤 없음
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b294'),os.path.join(site,'fx'))
shutil.copy(os.path.join(ROOT,'tests','fixtures','b285','map_v07.jpg'),os.path.join(site,'fx','shot.jpg'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name,lv)=>({id,name,level:lv,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','트딕이',285),C('c1','팬더데이',285),C('c2','터래플',289)]; S.activeId='c1'; save&&save(); render(); }"""
# 이름 칸을 reveal ms 동안 검게 가린 캔버스 스트림 → arStart. 직전 캐릭터(c1)가 잡혀 있는 상태에서 트딕이로 바뀌는 시간
RUN="""async ([clip,reveal])=>{ const A=window.AR; A.cfg.on=false; await arOcrLoad();
  const v=document.createElement('video'); v.muted=true; v.src='fx/'+clip+'.mp4'; v.loop=true; await v.play();
  const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'), n=A.cfg.name; let t0=performance.now(), tShow=0;
  const draw=()=>{ g.drawImage(v,0,0,1920,1080); if(performance.now()-t0<reveal){ g.fillStyle='#000'; g.fillRect(n.x*1920,n.y*1080,n.w*1920,n.h*1080); } else if(!tShow) tShow=performance.now(); if(A._run) requestAnimationFrame(draw); }; A._run=1; draw();
  const v2=document.createElement('video'); v2.muted=true; v2.srcObject=cv.captureStream(30); await v2.play(); A.det.cid='c1'; A.cidT=Date.now(); arStart(v2);
  let ms=-1; while(performance.now()-t0<reveal+8000){ await new Promise(r=>setTimeout(r,20)); if(tShow&&A.det.cid==='c0'){ ms=Math.round(performance.now()-tShow); break; } }
  A._run=0; arDisconnect(); v.pause(); return {ms,name:A.nameText}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    nm=pg.evaluate("()=>['7.689 드티니','17.208 드특니','17.209 드닉니','Lv.289 터래플','Lv.285 팬더데이','Lv.200 가나다'].map(arDetectChar)")
    check('이름 비교: 거센소리·ㅇ↔ㄴ 헷갈린 OCR(드티니) → 트딕이 · 다른 캐릭터 그대로 · 모르는 이름 없음', nm[0]=='c0' and nm[2]=='c0' and nm[3]=='c2' and nm[4]=='c1' and nm[5]=='', nm)
    T={}
    for c in ['v07','v10']:
        best=None
        for k in range(2):
            r=pg.evaluate(RUN,[c,2500]); print('TIME',c,r)
            if r['ms']>=0 and (best is None or r['ms']<best): best=r['ms']
            if best is not None and best<=1200: break
        T[c]=best
    check('실제 영상: 상태바 이름이 보이고 1.2초 안에 트딕이로 바뀜 (예전 7~9초)', all(v is not None and v<=1200 for v in T.values()), T)
    # UI
    check('헤더 🎮 게임 화면 연결 버튼 없음 · 길드 현황 탭 없음', pg.evaluate("!document.getElementById('arBtn')&&![...document.querySelectorAll('#tabs button')].some(b=>b.textContent.includes('길드'))"))
    tabs=pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.dataset.tab)")
    check('탭 순서: 득템 분석 다음(길드 자리)에 보스 득템 자동 기록', tabs==['boss','total','loot','auto','live'], tabs)
    pg.evaluate("""()=>{ window._gdm=0; window._gdmSync=null; navigator.mediaDevices.getDisplayMedia=function(){ window._gdm++; window._gdmSync=!!(navigator.userActivation&&navigator.userActivation.isActive); const c=document.createElement('canvas'); c.width=1920; c.height=1080; const g=c.getContext('2d'); const im=new Image(); im.src='fx/shot.jpg'; im.onload=()=>{ const f=()=>{ g.drawImage(im,0,0,1920,1080); requestAnimationFrame(f); }; f(); }; return Promise.resolve(c.captureStream(30)); }; }""")
    pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400)
    g=pg.evaluate("(()=>{ const m=document.getElementById('arGuide'), t=document.querySelector('#tabs [data-tab=auto]').getBoundingClientRect(), r=m&&m.getBoundingClientRect(); return {vis:!!m&&!m.hidden, below:r&&r.top>=t.bottom&&r.top-t.bottom<30, w:r&&r.width, txt:m&&m.textContent, imgs:m?[...m.querySelectorAll('img')].map(i=>i.naturalWidth):[], gdm:window._gdm}; })()")
    check('탭 클릭 → 탭 바로 아래 안내 창 (아직 화면 선택 안 물음) · 예시 이미지 2장', g['vis'] and g['below'] and g['gdm']==0 and '파티 목록' in g['txt'] and '인벤토리' in g['txt'] and len(g['imgs'])==2 and all(w>0 for w in g['imgs']), g)
    pg.screenshot(path=os.path.join(OUT,'b294_guide.png'))
    pg.click('#arGuide [data-arg="x"]'); pg.wait_for_timeout(200)
    check('닫기 → 연결 안 함', pg.evaluate("window._gdm===0&&!window.AR.stream"))
    pg.click('#arPanel [data-ar="guide"]'); pg.wait_for_timeout(300); pg.click('#arGuide [data-arg="ok"]'); pg.wait_for_timeout(1500)
    st=pg.evaluate("({n:window._gdm, sync:window._gdmSync, live:!!window.AR.stream, txt:document.querySelector('#arPanel .ar-sbar').textContent})")
    check('확인 클릭 안에서 바로 getDisplayMedia 1번 → 연결됨', st['n']==1 and st['sync'] and st['live'] and '연결됨' in st['txt'], st)
    pg.click('#tabs [data-tab="boss"]'); pg.wait_for_timeout(300); pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(500)
    check('이미 연결이면 탭 다시 눌러도 안내·화면 선택 안 물음', pg.evaluate("window._gdm===1&&(!document.getElementById('arGuide')||document.getElementById('arGuide').hidden)"))
    pg.evaluate("""()=>{ const A=window.AR; A.det={cid:'c0',boss:'bellona',diff:'easy',src:'보상 맵'}; A.nameMs=420; A.runRec=[{k:'r_white',b:'벨로나',c:'트딕이',t:'16:50'}]; A.cfg.roi=true; arPanelPaint(); }""")
    pg.wait_for_timeout(1200)
    d=pg.evaluate("""(()=>{ const se=document.scrollingElement; const q=s=>document.querySelector(s); return {scroll:se.scrollHeight-se.clientHeight, cards:[...document.querySelectorAll('#arPanel .ar-c h2')].map(h=>h.textContent.trim()), name:q('#arPanel .ar-cchar').textContent, boss:q('#arPanel .ar-cboss').textContent, rec:q('#arPanel .ar-crec').textContent, vid:q('#arPanel .ar-vid').videoWidth, fps:q('#arPanel .ar-sbar').textContent}; })()""")
    check('대시보드: 캐릭터·보스·라이브·이번 판 카드 · 상태 줄 · 1080p 스크롤 없음', d['scroll']<=1 and '트딕이' in d['name'] and '벨로나' in d['boss'] and '백옥' in d['rec'] and d['vid']>0 and '연결됨' in d['fps'] and '분석 fps' not in d['fps'], d)
    pg.screenshot(path=os.path.join(OUT,'b294_tab_dark.png'))
    pg.evaluate("toggleTheme()"); pg.wait_for_timeout(400); pg.screenshot(path=os.path.join(OUT,'b294_tab_light.png'))
    pg.click('#arPanel [data-ar="stop"]'); pg.wait_for_timeout(300)
    check('연결 끊기 → 끊김', pg.evaluate("!window.AR.stream&&document.querySelector('#arPanel .ar-sbar').textContent.includes('끊김')"))
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
