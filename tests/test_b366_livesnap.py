# test_b366 (t674): 라이브 인식 중 사이트 끊김 + 득템 축하 연출 렉
# 1) 라이브 프레임은 Worker 비트맵(arSrc) — 0.1초 타이머들이 메인 스레드에서 drawImage(video) 안 함, 끊으면 복제 트랙 정지, 미지원 브라우저는 video 폴백
# 2) 에픽빔 에셋 2880x1720(<1.6MB)·로드 때 미리 디코딩 안 함 3) 느린 프레임이면 연출 품질 자동 낮춤(CGQ)
import os, sys, subprocess, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
raw=open(os.path.join(ROOT,'epicbeam_s720.webp'),'rb').read()
check('에픽빔 에셋 < 1.6MB', len(raw)<1600000, len(raw))
try:
    from PIL import Image; im=Image.open(os.path.join(ROOT,'epicbeam_s720.webp')); check('에셋 2880x1720 RGBA', im.size==(2880,1720) and im.mode=='RGBA', (im.size,im.mode))
except ImportError: pass
check('배포 목록에 새 에셋', 'epicbeam_s720.webp' in open(os.path.join(ROOT,'tools','pages_dist.sh')).read())
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
LIVE="""async()=>{ const st=await navigator.mediaDevices.getUserMedia({video:{width:1280,height:720}}); const v=document.createElement('video'); v.muted=true; v.srcObject=st; await v.play();
 arStart(v); ARX.stream=st; arSrc(); for(let i=0;i<60&&ARS.n<2;i++) await new Promise(r=>setTimeout(r,100)); const W=[]; const od=CanvasRenderingContext2D.prototype.drawImage; window.__od=od;
 CanvasRenderingContext2D.prototype.drawImage=function(s,...a){ if(s instanceof HTMLVideoElement){ const k=(new Error().stack||'').match(/arNameWatch|arMapWatch|arFrame|arBoxStep|arLogFrame/); if(k) W.push(k[0]); } return od.call(this,s,...a); };
 await new Promise(r=>setTimeout(r,2500)); const s=arSrc(); const o={n:ARS.n,snap:!!(s&&s.arSnap),w:s&&s.width,vw:v.videoWidth,vd:W.length,who:[...new Set(W)],err:ARS.err};
 const tr=ARS.tr; arDisconnect(); o.stopped=!ARS.tr&&(!tr||tr.readyState==='ended'); o.orig=st.getVideoTracks()[0].readyState; CanvasRenderingContext2D.prototype.drawImage=od; return o; }"""
FB="""async()=>{ delete window.MediaStreamTrackProcessor; window.MediaStreamTrackProcessor=undefined; const st=await navigator.mediaDevices.getUserMedia({video:true}); const v=document.createElement('video'); v.muted=true; v.srcObject=st; await v.play();
 arStart(v); ARX.stream=st; await new Promise(r=>setTimeout(r,800)); const s=arSrc(); const o={isVideo:s===v,n:ARS.n}; arDisconnect(); return o; }"""
CG="""async()=>{ CGQ.set(0); let on=true; const hog=()=>{ const t=performance.now(); while(performance.now()-t<45){} if(on) requestAnimationFrame(hog); }; requestAnimationFrame(hog);
 celebrate(null,'r_white',BOSSES[0]); await new Promise(r=>setTimeout(r,1500)); on=false; const o={lv:CGQ.lv,hist:CGQ.hist.at(-1).slice(0,14),ls:localStorage.getItem('cgq')}; endCelebrate(); return o; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--headless=new','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
    pg=b.new_page(viewport={'width':1600,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    check('페이지 로드 때 큰 빔 이미지 미리 디코딩 안 함', pg.evaluate("!beamImg.src"), pg.evaluate("beamImg.src"))
    pg.wait_for_function("beamBake.fr&&beamBake.fr.length===16",timeout=20000)
    check('구운 프레임 576x344(dpr1)', pg.evaluate("beamBake.fr[0].width===576&&beamBake.fr[0].height===344"))
    o=pg.evaluate(LIVE); print(o)
    check('Worker 비트맵 받음', o['n']>=5 and o['snap'] and o['w']==o['vw'], o)
    check('0.1초 타이머들이 drawImage(video) 안 함', o['vd']==0, o['who'])
    check('끊으면 복제 트랙 정지·Worker 종료', o['stopped'], o)
    f=pg.evaluate(FB); check('MediaStreamTrackProcessor 없으면 video 그대로', f['isVideo'] and f['n']==0, f)
    c=pg.evaluate(CG); print(c)
    check('느린 첫 프레임 → 연출 품질 자동 낮춤(저장됨)', c['lv']>=1 and c['ls']==str(c['lv']) and any(x<0 for x in c['hist']), c)
    pg.evaluate("CGQ.set(0)")
    bx=pg.evaluate("""async()=>{ const k=Object.keys(AR_BOX)[0], T8=await arBoxTpl(k,8), T4=await arBoxTpl(k,4); const mk=(w,h,sd)=>{ const d=new Uint8ClampedArray(w*h*4); let r=sd; for(let i=0;i<d.length;i++){ r=(r*1103515245+12345)>>>0; d[i]=(r>>>16)&255; } return {d,w,h}; };
      const G8=mk(240,120,7), G4=mk(480,240,7); const put=(G,T,x0,y0)=>{ for(let j=0;j<T.n;j++){ const p=((y0+T.oy[j])*G.w+x0+T.ox[j])*4; for(let c=0;c<3;c++) G.d[p+c]=128+T.t[j*3+c]*.8; } }; put(G8,T8,50,30); put(G4,T4,100,60); const b=arBoxScoreSync(G8,G4,T8,T4,k); const w=arBoxW(); AR_BXW.sent.add(k); w.postMessage({k,tp:{T8,T4,P8:arBoxParts(T8),P4:arBoxParts(T4)}});
      const a=await new Promise(res=>{ const id=++AR_BXW.id; AR_BXW.cb.set(id,res); w.postMessage({id,k,G8:{d:G8.d.slice(),w:G8.w,h:G8.h},G4:{d:G4.d.slice(),w:G4.w,h:G4.h},thr:AR_BOX[k].thr,part:true,pen:AR_BOX_PART_PEN}); }); return {a,b,w:!!w}; }""")
    check('상자 NCC Worker = 메인 계산과 같은 점수', bx['w'] and bx['a']==bx['b'] and bx['a']>.9, bx)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally: srv.terminate()
print('RESULT', 'FAIL' if fails else 'PASS', len(fails)); sys.exit(1 if fails else 0)
