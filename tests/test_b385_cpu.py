"""b385: no discarded encoder, exact shift scores, bounded ownership, restart clocks."""
import functools,http.server,os,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(ROOT)));threading.Thread(target=srv.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME','/usr/bin/google-chrome'),args=['--no-sandbox'])
  pg=b.new_page();pg.goto(f'http://127.0.0.1:{srv.server_port}/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""()=>{clearInterval(EC.timer);
   function ref(D){const C=EC.cfg;let best=0;const a=new Float32Array(576),b=new Float32Array(576);for(const T of EC_TPL)for(let dy=-C.sy;dy<=C.sy;dy++)for(let dx=-C.sx;dx<=C.sx;dx++){if(!dx&&!dy)continue;let n=0;for(let y=Math.max(0,dy);y<18+Math.min(0,dy);y++)for(let x=Math.max(0,dx);x<32+Math.min(0,dx);x++){a[n]=D[y*32+x];b[n]=T[(y-dy)*32+x-dx];n++;}best=Math.max(best,ecNcc(a.subarray(0,n),b.subarray(0,n)));}return best;}
   let seed=385,err=0;const rnd=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
   const inputs=[new Float32Array(576),new Float32Array(576).fill(100),...EC_TPL.map(t=>Float32Array.from(t))];for(let j=0;j<24;j++)inputs.push(Float32Array.from({length:576},()=>rnd()*255));
   for(const D of inputs)err=Math.max(err,Math.abs(ref(D)-ecNccShift(D)));
   const cv=document.createElement('canvas');cv.width=1280;cv.height=720;cv.getContext('2d').fillRect(0,0,1280,720);ARX.testSrc=cv;let blobs=0;const orig=HTMLCanvasElement.prototype.toBlob;HTMLCanvasElement.prototype.toBlob=function(...a){blobs++;return orig.apply(this,a)};
   for(let i=0;i<5;i++)ecTick();const nativeBlobs=blobs,nativeRing=ECV.frames.length;const ve=window.VideoEncoder;window.VideoEncoder=undefined;ecTick();const legacyBlobs=blobs-nativeBlobs;window.VideoEncoder=ve;
   EC.cur=null;const now=Date.now();ECV.frames.unshift({t:now-2500,f:new VideoFrame(EC.cv,{timestamp:0})});EC.pend={t:now-1800};ecVPush(now);const pendingKept=ECV.frames[0].t===now-2500;EC.pend=null;
   ARX.testSrc=null;ecTick();const released=ECV.frames.length===0&&EC.buf.length===0;
   return{err,nativeBlobs,nativeRing,legacyBlobs,released,pendingKept};}""")
  assert r['err']<1e-9,r
  assert r['nativeBlobs']==0 and r['nativeRing']==5,r
  assert r['legacyBlobs']==1 and r['released'] and r['pendingKept'],r
  print('PASS exact NCC (32 deterministic inputs), WebM zero WebP work, legacy fallback, release:',r)
  r=pg.evaluate("""()=>{
   function ref(I,T,x0,x1,y0,y1){let best=-1,bx=0,by=0;for(let y=Math.max(0,y0);y<=Math.min(I.h-T.h,y1);y++)for(let x=Math.max(0,x0);x<=Math.min(I.w-T.w,x1);x++){let s=0,q=0,st=0;for(let j=0;j<T.h;j++){const ro=(y+j)*I.w+x,to=j*T.w;for(let i=0;i<T.w;i++){const v=I.a[ro+i];s+=v;q+=v*v;st+=v*T.t[to+i];}}const vi=q-s*s/T.n,den=Math.sqrt(Math.max(0,vi)*T.tt),sc=den>1e-6?st/den:0;if(sc>best){best=sc;bx=x;by=y;}}return {sc:best,x:bx,y:by};}
   let err=0,seed=385;const rnd=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
   for(let j=0;j<20;j++){const I={w:80,h:40,a:Float32Array.from({length:3200},()=>rnd()*255)},t=Float32Array.from({length:99},()=>rnd()*255),m=t.reduce((a,b)=>a+b)/99;t.forEach((v,i)=>t[i]=v-m);const T={w:11,h:9,n:99,t,tt:t.reduce((a,b)=>a+b*b,0)};const old=ref(I,T,0,80,0,40),now=arBmNcc(I,T,0,80,0,40);if(old.x!==now.x||old.y!==now.y)throw Error('peak changed');err=Math.max(err,Math.abs(old.sc-now.sc));}
   return err;}""")
  assert r<1e-9,r
  print('PASS message/meso summed-area NCC equivalent on 20 deterministic images',r)
  # Timer regression uses the real arStart but disables unrelated OCR/DOM work.
  r=pg.evaluate("""()=>{arOcrLoad=()=>{};arWorker=()=>{};arBtnPaint=()=>{};arPanel=()=>{};const v=document.createElement('video');v.requestVideoFrameCallback=()=>{};arStart(v);const first=AR_TK.f.size;arStart(v);const second=AR_TK.f.size;arDisconnect();return {first,second,end:AR_TK.f.size};}""")
  assert r['first']==r['second'] and r['end']==0,r
  print('PASS repeated start has one timer set; disconnect clears all',r)
  b.close()
finally:srv.shutdown()
print('RESULT OK')
