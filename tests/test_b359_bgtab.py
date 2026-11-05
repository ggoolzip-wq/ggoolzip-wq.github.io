# test_b359 (t672): 화면 공유 연결 + PIP 연 채로 다른 탭(캘린더)으로 가도 인식·기록·PIP 갱신이 계속되는지
#   (1) 인식 시계가 Worker 시계(arTick)  (2) 숨은 video 가 화면 안(2px, opacity .01) — -9999px/opacity 0 아님
#   (3) 캘린더 탭에서도 이름·박스·프레임 루프 rate 유지  (4) 캘린더 탭에서 득템 → 기록되고 PIP 득템 목록·캐릭터 줄 갱신, 닉네임 유지
#   (5) 프레임 콜백이 멈추면(뒤 탭) Worker 시계로 배너·공중 감시 대신 (rvfcT 오래됨 흉내)
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save(); document.querySelector('#tabs [data-tab="auto"]').click();
 navigator.mediaDevices.getDisplayMedia=async()=>{ const c=document.createElement('canvas'); c.width=1366; c.height=768; const g=c.getContext('2d'); let i=0; setInterval(()=>{ g.fillStyle=`hsl(${(i++*7)%360},50%,40%)`; g.fillRect(0,0,1366,768); },33); return c.captureStream(30); };
 Object.defineProperty(window,'documentPictureInPicture',{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:120px;width:${o.width}px;height:${o.height}px;z-index:99999;border:0;outline:2px solid #39f`; document.body.append(f); await new Promise(r=>setTimeout(r,50)); const w=f.contentWindow; w.close=()=>f.remove(); w.moveTo=()=>{}; return w; }}});
 const C=window.__cnt={n:0,f:0,b:0,w:0}; const wrap=(k,key)=>{ const o=window[k]; window[k]=function(){ C[key]++; return o.apply(this,arguments); }; }; wrap('arNameWatch','n'); wrap('arFrame','f'); wrap('arBoxStep','b'); wrap('arBannerWatch','w'); ARX.cfg.rewGate=false; }"""
MEAS="""async(ms)=>{ const C=window.__cnt, a={...C}; await new Promise(r=>setTimeout(r,ms)); const s=ms/1000; return {n:(C.n-a.n)/s,f:(C.f-a.f)/s,b:(C.b-a.b)/s,w:(C.w-a.w)/s}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)+' @ '+(e.stack or '')[:600]))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>arConnect()"); pg.wait_for_timeout(600); pg.evaluate("()=>{ if(!ARX.pip) return arPipOpen(); }"); pg.wait_for_timeout(1500)
    check('PIP 열림',pg.evaluate("()=>!!ARX.pip&&!!document.getElementById('fakePip')"))
    check('인식 시계 = Worker 시계(arTick)',pg.evaluate("()=>[ARX.nTimer,ARX.timer,ARX.boxTimer,ARX.logTimer,ARX.uiTick].every(i=>AR_TK.f.has(i))&&!!AR_TK.w"))
    st=pg.evaluate("()=>{ const v=ARX.video, cs=getComputedStyle(v), r=v.getBoundingClientRect(); return {op:+cs.opacity,disp:cs.display,x:r.x,w:r.width,conn:v.isConnected}; }")
    check('숨은 video 는 화면 안에 그려짐(-9999px·opacity 0·display:none 아님)',st['conn'] and st['disp']!='none' and st['op']>0 and st['x']>=0 and st['w']>0,st)
    A=pg.evaluate(MEAS,2000)
    pg.click('#tabs [data-tab="cal"]'); pg.wait_for_timeout(400)
    check('캘린더 탭으로 옮김(#arPanel 없음)',pg.evaluate("()=>tab==='cal'&&!document.getElementById('arPanel')"))
    Bm=pg.evaluate(MEAS,2000)
    check('캘린더 탭에서도 루프 속도 유지(이름·상자·배너)',Bm['n']>=8 and Bm['b']>=8 and Bm['w']>=5 and Bm['n']>=A['n']*.8,(A,Bm))
    pg.evaluate("()=>{ ARX.det.cid='c0'; ARX.nameOk=true; }"); pg.wait_for_timeout(500)
    ch=pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipchar')?.textContent||''")
    check('캘린더 탭에서도 PIP 캐릭터 줄 갱신(닉네임)','트딕이' in ch and 'Lv.285' not in ch,ch)
    r=pg.evaluate("""async()=>{ const bo=BOSSES.find(b=>b.id==='kaling'); ARX.det.boss='kaling'; ARX.det.diff='easy'; window.arBoxOk=()=>true; ARX.rwl=null; const c=arCandidates(true); const it=(c.find(x=>x.k==='r_white')||c[0])?.k; arRecord(it,.95,'공중'); await new Promise(r=>setTimeout(r,600));
      const d=document.getElementById('fakePip').contentDocument; return {it, n:(ARX.sessRec||[]).length, pip:d.querySelector('.ar-prh')?.textContent||'', tab, cid:ARX.det.cid}; }""")
    check('캘린더 탭에서 득템 기록 → PIP 득템 목록 1개',r['n']==1 and '1개' in r['pip'] and r['tab']=='cal',r)
    pg.wait_for_timeout(1500)
    check('닉네임(캐릭터) 그대로',pg.evaluate("()=>ARX.det.cid")=='c0' and '트딕이' in pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipchar').textContent"))
    pg.screenshot(path=os.path.join(OUT,'b359_cal_pip.png'))
    # 뒤 탭 흉내: 프레임 콜백을 막고(rvfcT 멈춤) Worker 시계 대신 감시
    W=pg.evaluate("""async()=>{ const v=ARX.video; v.requestVideoFrameCallback=()=>0; await new Promise(r=>setTimeout(r,400)); const a=__cnt.w; await new Promise(r=>setTimeout(r,2000)); return (__cnt.w-a)/2; }""")
    check('프레임 콜백 멈춰도 배너·공중 감시 계속(Worker 시계)',W>=4,W)
    pg.wait_for_timeout(1500); pg.evaluate("()=>{ tab='auto'; render(); }"); pg.wait_for_timeout(500)
    check('대시보드 탭으로 돌아오면 패널 정상',pg.evaluate("()=>!!document.querySelector('#arPanel .ar-g')"),pg.evaluate("()=>[tab,document.querySelector('#view').innerHTML.slice(0,300)]"))
    pg.evaluate("()=>arDisconnect()"); pg.wait_for_timeout(200)
    check('끊으면 시계 모두 정리',pg.evaluate("()=>AR_TK.f.size===0"),pg.evaluate("()=>AR_TK.f.size"))
    b.close()
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
errs=[e for e in errs if 'tesseract.min.js' not in e]  # OCR 워커 종료 경쟁(끊을 때) — 이 테스트와 무관
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
