"""Repeatable b384/b385 Chromium CPU benchmark; no user credentials or live API.
Usage: CHROME=/usr/bin/google-chrome python3 tests/bench_b385_cpu.py --html /workspace/b385/baseline.html --out /workspace/b385/before.json
CPU is SUM Chromium process CPU seconds / wall second, NOT the user's machine percent.
"""
import argparse, functools, http.server, json, os, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--html',default=str(ROOT/'index.html'));a.add_argument('--out',required=True);a.add_argument('--video',default=str(ROOT/'tests/fixtures/b352/beam720.webm'));a.add_argument('--seconds',type=float,default=12);a.add_argument('--modes',default='epic,auto');args=a.parse_args()
class Handler(http.server.SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path.split('?')[0]=='/bench_video.webm':
   data=Path(args.video).read_bytes();self.send_response(200);self.send_header('Content-type','video/webm');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  elif self.path.split('?')[0]=='/bench.html':
   data=Path(args.html).read_bytes();self.send_response(200);self.send_header('Content-type','text/html');self.end_headers();self.wfile.write(data)
  else: super().do_GET()
 def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=srv.serve_forever,daemon=True).start()
results={}
with sync_playwright() as p:
 for mode in args.modes.split(','):
  b=p.chromium.launch(executable_path=os.environ.get('CHROME','/usr/bin/google-chrome'),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
  pg=b.new_page(viewport={'width':1280,'height':900});pg.route('https://open.api.nexon.com/**',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{srv.server_port}/bench.html');pg.wait_for_timeout(1500)
  pg.evaluate("""async(mode)=>{window.BEN={blob:0,parts:{}};const blob=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(...a){BEN.blob++;return blob.apply(this,a)};
   for(const n of ['ecTick','ecGrid','ecNccShift','arFrame','arNameWatch','arMapWatch','arBoxStep','arLogFrame']){const f=window[n];if(typeof f==='function')window[n]=function(...a){const t=performance.now();try{return f.apply(this,a)}finally{const r=BEN.parts[n]||(BEN.parts[n]={calls:0,ms:0});r.calls++;r.ms+=performance.now()-t}}}
   const v=document.createElement('video');v.muted=true;v.loop=true;v.src='/bench_video.webm';document.body.append(v);await v.play();window._benchV=v;
   if(mode==='auto'||mode==='reward'||mode==='ocr'){
    if(mode!=='auto'){
     const bosses={};for(const x of BOSSES)bosses[x.id]={enabled:true,party:1,diff:x.diffs.includes('hard')?'hard':x.diffs[0]};
     S.characters=[{id:'bench',name:'트딕이',bosses,weekly:{},monthly:{},drops:{},auto:{},sync:{}}];S.activeId='bench';
     ARX.stream=v.captureStream();
    }
    arStart(v);
    if(mode!=='auto'){
     const state=()=>{ARX.det={cid:'bench',boss:'lucid',diff:'hard',src:'benchmark'};ARX.mapSt={boss:'lucid',kind:'r',t:Date.now(),diff:'hard'};};state();setInterval(state,100);EC.cool=Date.now()+1e9;
     if(mode==='ocr'){clearInterval(EC.timer);ECV.frames.forEach(x=>x.f.close());ECV.frames=[];}
    }
   }else ARX.testSrc=v;
  }""",mode)
  pg.wait_for_timeout(3000)
  if mode=='encode':
   pg.evaluate("EC.cur={t0:Date.now()+1000};EC.cfg.post=100000;EC.cool=Date.now()+1e9")
   pg.wait_for_timeout(4300)
   pg.evaluate("clearInterval(EC.timer);_benchV.pause();EC.cur=null")
  bc=b.new_browser_cdp_session();cd=pg.context.new_cdp_session(pg);cd.send('Performance.enable');cd.send('Profiler.enable');cd.send('Profiler.start')
  def cpu():return sum(x['cpuTime'] for x in bc.send('SystemInfo.getProcessInfo')['processInfo'])
  def metrics():return {x['name']:x['value'] for x in cd.send('Performance.getMetrics')['metrics']}
  pg.evaluate('BEN.blob=0;BEN.parts={}');c0=cpu();m0=metrics();t=time.monotonic()
  if mode=='encode':
   pg.evaluate("async()=>{const t=ECV.frames[0].t+1000;await ecVMake({t0:t,vt0:1,sc:1,boss:'lucid',diff:'hard',w:1280,h:720});}")
  else: pg.wait_for_timeout(args.seconds*1000)
  wall=time.monotonic()-t;c1=cpu();m1=metrics()
  profile=cd.send('Profiler.stop')['profile'];counts={};nodes={n['id']:n['callFrame']['functionName'] or '(anonymous)' for n in profile['nodes']}
  for n,dt in zip(profile.get('samples',[]),profile.get('timeDeltas',[])):counts[nodes.get(n,'?')]=counts.get(nodes.get(n,'?'),0)+dt
  r=pg.evaluate("({blobs:BEN.blob,parts:BEN.parts,ocr:!!ARX.ocr,ocrError:ARX.ocrErr,boxWorker:!!AR_BXW.w,snapFrames:ARS.n,videoError:ECV.videoError,ring:ECV.frames.length,saved:EC.saved})");r.update(wall=wall,cpuSeconds=c1-c0,cpuPerWall=(c1-c0)/wall,mainTaskSeconds=m1.get('TaskDuration',0)-m0.get('TaskDuration',0),hotSamplesMs=sorted(((n,round(v/1000,1)) for n,v in counts.items()),key=lambda x:-x[1])[:18]);results[mode]=r;print(mode,json.dumps(r),flush=True);b.close()
srv.shutdown();Path(args.out).write_text(json.dumps(results,indent=2))
