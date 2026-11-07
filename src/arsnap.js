/* b366 (t674): 라이브 화면 공유 프레임을 Worker 에서 받기 — 메인 스레드에서 drawImage(video) 를 0.1초마다 6~8번(이름·맵·검은화면·에픽빔 버퍼…) 하면
   매번 영상 프레임 변환(1080p 한 번 15~40ms)이 메인 스레드에서 일어나 사이트 전체가 끊김(측정: 메인 스레드 98% 바쁨).
   → MediaStreamTrackProcessor(복제 트랙) 의 VideoFrame 을 Worker 로 넘겨 OffscreenCanvas 에 그린 뒤 ImageBitmap 을 0.1초마다 보내 줌.
   분석 함수들은 이 비트맵에서 잘라 씀(자르기 0.05ms). 지원 안 하는 브라우저·시작 전엔 그대로 video. */
function OwnedCaptureWorkerMain(){
 let reader=null,fr=null,stopped=false,ms=100,clipH=720,clipFps=30,enabled=true,paused=false;
 let bitmapCanvas=null,bg=null,clipCanvas=null,cg=null,lastBitmap=-Infinity;
 let nextId=0,clipOK=null,loopStarted=false,clipTimer=null,stopPromise=null;
 const pending=new Set();
 function ready(ok,error){if(clipOK!==ok||error){clipOK=ok;postMessage(error?{clipReady:ok,clipError:String(error)}:{clipReady:ok});}}
 function closeSource(){if(fr){fr.close();fr=null;}}
 function clearClipTimer(){if(clipTimer!==null){clearInterval(clipTimer);clipTimer=null;}}
 function captureClip(){
  if(stopped||!fr||!enabled||paused||clipOK===false||pending.size>=2)return;
  let owned=null;
  try{const t0=performance.now(),w=fr.displayWidth,h=fr.displayHeight,ch=Math.min(clipH,h),cw=Math.max(1,Math.round(w*ch/h));
   if(!clipCanvas||clipCanvas.width!==cw||clipCanvas.height!==ch){clipCanvas=new OffscreenCanvas(cw,ch);cg=clipCanvas.getContext('2d');}
   // Explicit owned pixel copy from latest source; never emit a source clone.
   cg.drawImage(fr,0,0,w,h,0,0,cw,ch);
   const at=Date.now(),id=++nextId;owned=new VideoFrame(clipCanvas,{timestamp:Math.round(at*1000)});
   pending.add(id);try{postMessage({clip:owned,at,id,dt:performance.now()-t0},[owned]);owned=null;}catch(e){pending.delete(id);throw e;}
   ready(true);
  }catch(e){if(owned)owned.close();ready(false,e&&e.message||e);clearClipTimer();}
 }
 function startClipTimer(){clearClipTimer();if(loopStarted&&!stopped&&enabled&&!paused&&clipOK!==false)clipTimer=setInterval(captureClip,Math.max(1,Math.round(1000/clipFps)));}
 function stop(){
  if(stopPromise)return stopPromise;
  stopped=true;clearClipTimer(); // Must precede asynchronous reader cancellation.
  stopPromise=(async()=>{try{if(reader)await reader.cancel();}finally{closeSource();pending.clear();if(reader){try{reader.releaseLock();}catch(_){}reader=null;}bitmapCanvas=bg=clipCanvas=cg=null;postMessage({stopped:true,outstanding:pending.size,sourceClosed:fr===null,clipTimerCleared:clipTimer===null});}})();
  return stopPromise;
 }
 function configure(d){
  let restart=false;
  if(Number.isFinite(d.ms)&&d.ms>0)ms=d.ms;
  if(Number.isFinite(d.clipH)&&d.clipH>=1)clipH=Math.floor(d.clipH);
  if(Number.isFinite(d.clipFps)&&d.clipFps>0){const fps=Math.min(240,d.clipFps);restart=restart||fps!==clipFps;clipFps=fps;}
  if(typeof d.clipEnabled==='boolean'){restart=restart||enabled!==d.clipEnabled;enabled=d.clipEnabled;}
  if(typeof d.clipPause==='boolean'){restart=restart||paused!==d.clipPause;paused=d.clipPause;}
  if(restart)startClipTimer();
 }
 async function pump(rs){
  if(loopStarted)throw Error('Only one input stream is supported');loopStarted=true;
  reader=rs.getReader();if(typeof VideoFrame!=='function')ready(false);startClipTimer();
  try{while(!stopped){const item=await reader.read();if(item.done)break;if(stopped){item.value.close();break;}closeSource();fr=item.value;
   const now=performance.now(),w=fr.displayWidth,h=fr.displayHeight;
   // Bitmap errors are stream/bitmap errors, never downgraded to clip fallback.
   if(now-lastBitmap>=Math.max(0,ms-8)){
    lastBitmap=now;const t0=performance.now();if(!bitmapCanvas||bitmapCanvas.width!==w||bitmapCanvas.height!==h){bitmapCanvas=new OffscreenCanvas(w,h);bg=bitmapCanvas.getContext('2d');}
    bg.drawImage(fr,0,0,w,h);const bm=bitmapCanvas.transferToImageBitmap();
    const opaque=/^(?:I420|I422|I444|NV12|RGBX|BGRX)$/.test(fr.format||'');
    try{postMessage({bm,ts:fr.timestamp,opaque,dt:performance.now()-t0},[bm]);}catch(e){bm.close();throw e;}
   }
  }}catch(e){postMessage({bitmapError:String(e&&e.message||e)});}
  finally{if(!stopped)await stop();}
 }
 onmessage=e=>{const d=e.data||{};configure(d);if(Number.isSafeInteger(d.ack))pending.delete(d.ack);if(d.stop){stop().catch(e=>postMessage({stopError:String(e)}));return;}if(d.rs)pump(d.rs).catch(e=>postMessage({bitmapError:String(e)}));};
}

class OwnedCaptureHost {
 constructor(workerMain,{onBitmap,onClip,onError=()=>{},expectedSize=()=>null}={}){
  if(typeof workerMain!=='function'||typeof onBitmap!=='function'||typeof onClip!=='function')throw new TypeError('workerMain, onBitmap and onClip must be functions');
  this.workerMain=workerMain;this.onBitmap=onBitmap;this.onClip=onClip;this.onError=onError;this.expectedSize=expectedSize;
  this.worker=null;this.track=null;this.stream=null;this.url=null;this.generation=0;this.config={};this.clipN=0;this.clipError='';this.ready=false;this.width=0;this.height=0;this.lastClip=0;
 }
 _clear(){this.ready=false;this.lastClip=0;this.width=0;this.height=0;}
 _revoke(url){if(url){URL.revokeObjectURL(url);if(this.url===url)this.url=null;}}
 _report(error){try{this.onError(error instanceof Error?error:new Error(String(error)));}catch(_){}}
 _clipFailure(error){this._clear();this.clipError=String(error&&error.message||error);this._report(error);}
 start(stream){
  this.stop();const generation=this.generation;this.clipN=0;this.clipError='';
  let worker=null,track=null,url=null;
  try{
   if(typeof Worker!=='function'||typeof MediaStreamTrackProcessor!=='function'||typeof OffscreenCanvas==='undefined')throw new Error('Capture Worker APIs unavailable');
   const original=stream&&stream.getVideoTracks()[0];if(!original)throw new Error('Video track required');
   track=original.clone();this.track=track;this.stream=stream;
   const processor=new MediaStreamTrackProcessor({track});
   url=URL.createObjectURL(new Blob(['('+this.workerMain.toString()+')()'],{type:'text/javascript'}));this.url=url;
   worker=new Worker(url);this.worker=worker;this.config={clipEnabled:false,clipPause:false,clipH:720,clipFps:30};
   worker.onmessage=e=>{this._revoke(url);this._dispatch(e.data||{},worker,generation);};
   worker.onerror=e=>{this._revoke(url);if(this.worker!==worker||generation!==this.generation)return;this.stop();this._report(e.message||e);};
   worker.postMessage({rs:processor.readable,ms:100,clipEnabled:false},[processor.readable]);return this;
  }catch(error){this._revoke(url);if(worker)worker.terminate();if(track)track.stop();this.stop();throw error;}
 }
 configure(patch){
  const changed={};for(const key of ['clipEnabled','clipPause','clipH','clipFps'])if(Object.prototype.hasOwnProperty.call(patch,key)&&!Object.is(this.config[key],patch[key])){this.config[key]=patch[key];changed[key]=patch[key];}
  if(this.config.clipEnabled===false||this.config.clipPause===true)this._clear();
  if(this.worker&&Object.keys(changed).length)this.worker.postMessage(changed);
 }
 _dispatch(d,originalWorker,generation){
  const current=this.worker===originalWorker&&this.generation===generation;
  if(d.clip){
   const frame=d.clip;let owns=false;
   try{
    if(!current||!this.config.clipEnabled||this.config.clipPause||!Number.isFinite(d.at)||Math.abs(Date.now()-d.at)>600)return;
    const w=frame.displayWidth,h=frame.displayHeight,expected=this.expectedSize();
    if(expected&&(expected.w!==w||expected.h!==h))return;
    owns=this.onClip(frame,d.at)===true;
    if(owns&&this.worker===originalWorker&&this.generation===generation&&this.config.clipEnabled&&!this.config.clipPause){this.ready=true;this.lastClip=performance.now();this.width=w;this.height=h;this.clipN++;}
   }catch(error){if(current)this._clipFailure(error);}
   finally{if(!owns)try{frame.close();}catch(_){}try{originalWorker.postMessage({ack:d.id});}catch(_){}}
  }
  if(d.bm){
   if(!current){d.bm.close();return;}
   try{this.onBitmap(d.bm,d.dt,d.opaque);}catch(error){try{d.bm.close();}catch(_){}this.stop();this._report(error);return;}
  }
  if(!current)return;
  if(d.clipReady===false){this._clear();if(d.clipError){this.clipError=String(d.clipError);this._report(d.clipError);}}
  if(d.bitmapError){this.stop();this._report(d.bitmapError);}
  if(d.stopped)this._clear();
 }
 fresh(w,h,maxAge=300){return !!(this.ready&&this.worker&&this.lastClip>0&&performance.now()-this.lastClip<maxAge&&this.width===w&&this.height===h);}
 stop(){
  this.generation++;const worker=this.worker,track=this.track,url=this.url;
  this.worker=null;this.track=null;this.stream=null;this.url=null;this.config={};this._clear();
  this._revoke(url);if(worker)try{worker.terminate();}catch(_){}if(track)try{track.stop();}catch(_){}
 }
}
const ARS={on:false,bm:null,old:[],w:null,tr:null,s:null,n:0,ms:0,err:'',clip:null};
function arSnapStop(){ try{ ARS.clip&&ARS.clip.stop(); }catch(e){} ARS.clip=null; try{ ARS.w&&ARS.w.terminate(); }catch(e){} try{ ARS.tr&&ARS.tr.stop(); }catch(e){} ARS.w=null; ARS.tr=null; ARS.s=null; ARS.on=false; ARS.old.forEach(b=>{ try{ b.close(); }catch(e){} }); ARS.old=[]; ARS.bm=null; }
function arSnapClipCfg(){const h=ARS.clip;if(!h||typeof EC==='undefined')return;try{h.configure({clipEnabled:!!(window.VideoEncoder&&window.VideoFrame&&window.ECWebM),clipPause:!!ECV.busy,clipH:EC.cfg.H,clipFps:EC.cfg.fps});}catch(e){ARS.err=String(e);}}
function arSnapStart(st){ arSnapStop(); ARS.s=st; ARS.n=0; if(typeof ARX!=='undefined'&&ARX.cfg&&ARX.cfg.snap===false) return; if(typeof MediaStreamTrackProcessor!=='function'||typeof OffscreenCanvas==='undefined'||typeof Worker==='undefined') return;
  const t=st&&st.getVideoTracks&&st.getVideoTracks()[0]; if(!t) return;
  try{ const h=new OwnedCaptureHost(OwnedCaptureWorkerMain,{
    expectedSize:()=>{const v=ARX.video,H=Math.min(EC.cfg.H,v&&v.videoHeight||0);return {w:Math.round(H*(v&&v.videoWidth||0)/(v&&v.videoHeight||1)),h:H};},
    onBitmap:(bm,dt,opaque)=>{if(ARS.s!==st){bm.close();return;}bm.videoWidth=bm.width;bm.videoHeight=bm.height;bm.readyState=4;bm.currentTime=(ARX.video&&ARX.video.currentTime)||0;bm.arSnap=1;bm.arOpaque=opaque===true;ARS.bm=bm;ARS.t=performance.now();ARS.n++;ARS.ms=dt;ARS.on=true;},
    onClip:(frame,at)=>ecVPush(at,frame),
    onError:e=>{ARS.err=String(e.message||e);if(!h.worker)arSnapStop();}
  });ARS.clip=h;h.start(st);ARS.w=h.worker;ARS.tr=h.track;arSnapClipCfg();}
  catch(e){ ARS.err=String(e); arSnapStop(); ARS.s=st; } }
/* 분석에 쓸 화면: 최신 Worker 비트맵(0.6초 안 — 멈추면 video), 없으면 video */
function arSrc(){ const v=ARX.video; if(!v) return v; const st=ARX.stream||null; if(st!==ARS.s){ if(st) arSnapStart(st); else arSnapStop(); }
  const b=ARS.bm; return b&&ARS.on&&ARS.n>0&&performance.now()-ARS.t<600&&(v.videoWidth?b.width===v.videoWidth:true)?b:v; }
