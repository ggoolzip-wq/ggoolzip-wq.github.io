# test_b308 (t542~t549): 서버 저장은 값이 바뀔 때만 (같은 메소 반복 = 0회) + 전부 켠 상태 CPU 측정 (해상도별 1초당 처리 ms·메인 스레드 %)
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:500] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copy(os.path.join(ROOT,'tests','fixtures','b285','map_v07.jpg'),os.path.join(site,'shot.jpg'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  S.characters=[{id:'c0',name:'트딕이',level:285,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; S.meso={}; save(); render();
  window._gc=0; const g0=gdChanged; gdChanged=function(){ window._gc++; }; }"""
PERF="""async ([w,h,sec])=>{ const A=window.AR; await arOcrLoad(); const im=new Image(); im.src='shot.jpg'; await im.decode();
  const cv=document.createElement('canvas'); cv.width=w; cv.height=h; const g=cv.getContext('2d'); let run=1; g.drawImage(im,0,0,w,h); const v=cv; /* 캔버스를 그대로 화면 소스로 (테스트 영상 재생 비용 제외) */ A.cfg.on=true; A.det.cid='c0';
  const W={ms:0,d:0,by:{}}; const wrap=(o,n,lab)=>{ const f=o[n]; if(typeof f!=='function') return; o[n]=function(...a){ if(W.d){ return f.apply(this,a); } W.d=1; const t=performance.now(); try{ const r=f.apply(this,a); return r; } finally{ const d=performance.now()-t; W.d=0; if(W.on){ W.ms+=d; W.by[lab]=(W.by[lab]||0)+d; } } }; };
  for(const n of ['arFrame','arNameWatch','arMapWatch','arBoxStep','arLogFrame','arMesoTick','arBannerWatch','arAirWatch','arItemStep','arBoxScore','arNcc','arBoxGrab','arCrop','arMapHash','arOcr','arMatch']) wrap(window,n,n);
  const P=CanvasRenderingContext2D.prototype, gid=P.getImageData; P.getImageData=function(...a){ if(W.d||!W.on) return gid.apply(this,a); const t=performance.now(); try{ return gid.apply(this,a); } finally{ const d=performance.now()-t; W.ms+=d; W.by.getImageData=(W.by.getImageData||0)+d; } };
  arStart(v); await new Promise(r=>setTimeout(r,2500)); W.on=1; let lag=0, last=performance.now(); const hb=setInterval(()=>{ const n=performance.now(); lag+=Math.max(0,n-last-10); last=n; },10); /* 메인 스레드가 막힌 시간 */ const keep=setInterval(()=>{ A.mapSt={boss:'slime',diff:'normal',kind:'r',name:'고요한 제단',t:Date.now()}; },300); /* 보상 맵 = 상자 0.2초 */
  let busy=0; const mk=window.__mark=[]; const t0=performance.now(); await new Promise(r=>setTimeout(r,sec*1000)); const el=performance.now()-t0;
  W.on=0; clearInterval(hb); clearInterval(keep); run=0; arDisconnect(); const by={}; for(const k in W.by) by[k]=Math.round(W.by[k]/sec); return {el:Math.round(el), lag_ms_per_s:Math.round(lag/el*1000), lag_pct:+(lag/el*100).toFixed(1), ms_per_s:Math.round(W.ms/sec), pct:+(W.ms/el*100).toFixed(1), by, box:A.boxLast}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    r=pg.evaluate("""()=>{ const o={}; window._gc=0; saveMeso('c0',100,5); o.first=window._gc; for(let i=0;i<10;i++) saveMeso('c0',100,5); o.same=window._gc-o.first;
      saveMeso('c0',101,5); o.chg=window._gc-o.first-o.same; const g1=window._gc; for(let i=0;i<5;i++) saveMeso('c0',101,null); o.invOnly=window._gc-g1;
      const g2=window._gc; ARX.clr={boss:'slime',diff:'normal',mapT:Date.now()-60000,reads:[],t0:Date.now()-60000}; try{ arClrFinish('slime','normal',Date.now()); }catch(e){ o.ce=String(e); } o.clear=window._gc-g2; return o; }""")
    print('CALLS',r)
    check('서버 저장 호출: 같은 메소 10번 읽기 → 0회, 값 바뀜 → 1회', r['first']==1 and r['same']==0 and r['chg']==1 and r['invOnly']==0, r)
    cdp=pg.context.new_cdp_session(pg); cdp.send('Performance.enable')
    res={}
    for nm,(w,h) in {'1366x768':(1366,768),'1920x1080':(1920,1080),'2560x1440':(2560,1440)}.items():
      m0={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
      o=pg.evaluate(PERF,[w,h,10])
      m1={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
      # 측정 구간에는 시작 2.5초도 포함 → 전체 시간으로 나눔
      res[nm]={'el':o['el'],'blocked_ms_per_s':o['lag_ms_per_s'],'blocked_pct':o['lag_pct'],'ms_per_s':o['ms_per_s'],'main_pct':o['pct'],'by':o['by'],'renderer_task_ms_per_s(테스트 영상 그리기 포함)':round((m1['TaskDuration']-m0['TaskDuration'])*1000/12.5)}
      print('PERF',nm,res[nm])
    json.dump(res,open(os.path.join(OUT,'b308_perf.json'),'w'),ensure_ascii=False)
    check('측정 완료 (3 해상도)', len(res)==3, res)
    b.close()
finally:
  srv.terminate()
errs=[e for e in errs if 'postMessage' not in e] # 끊은 뒤 OCR 워커 늦은 응답 (기존부터, 무해)
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
