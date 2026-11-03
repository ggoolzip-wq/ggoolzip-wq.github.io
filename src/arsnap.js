/* b366 (t674): 라이브 화면 공유 프레임을 Worker 에서 받기 — 메인 스레드에서 drawImage(video) 를 0.1초마다 6~8번(이름·맵·검은화면·에픽빔 버퍼…) 하면
   매번 영상 프레임 변환(1080p 한 번 15~40ms)이 메인 스레드에서 일어나 사이트 전체가 끊김(측정: 메인 스레드 98% 바쁨).
   → MediaStreamTrackProcessor(복제 트랙) 의 VideoFrame 을 Worker 로 넘겨 OffscreenCanvas 에 그린 뒤 ImageBitmap 을 0.1초마다 보내 줌.
   분석 함수들은 이 비트맵에서 잘라 씀(자르기 0.05ms). 지원 안 하는 브라우저·시작 전엔 그대로 video. */
const ARS={on:false,bm:null,old:[],w:null,tr:null,s:null,n:0,ms:0,err:''};
function arSnapStop(){ try{ ARS.w&&ARS.w.terminate(); }catch(e){} try{ ARS.tr&&ARS.tr.stop(); }catch(e){} ARS.w=null; ARS.tr=null; ARS.s=null; ARS.on=false; ARS.old.forEach(b=>{ try{ b.close(); }catch(e){} }); ARS.old=[]; ARS.bm=null; }
function arSnapStart(st){ arSnapStop(); ARS.s=st; ARS.n=0; if(typeof ARX!=='undefined'&&ARX.cfg&&ARX.cfg.snap===false) return; if(typeof MediaStreamTrackProcessor!=='function'||typeof OffscreenCanvas==='undefined'||typeof Worker==='undefined') return;
  const t=st&&st.getVideoTracks&&st.getVideoTracks()[0]; if(!t) return;
  try{ const code=`let fr=null,ms=100,lt=0,oc=null,g=null,busy=false;
const snap=()=>{ if(!fr||busy) return; busy=true; const t0=performance.now(), w=fr.displayWidth, h=fr.displayHeight; if(!oc||oc.width!==w||oc.height!==h){ oc=new OffscreenCanvas(w,h); g=oc.getContext('2d'); } g.drawImage(fr,0,0); const ts=fr.timestamp; const bm=oc.transferToImageBitmap(); postMessage({bm,ts,dt:performance.now()-t0},[bm]); busy=false; };
onmessage=async e=>{ const d=e.data; if(d.ms) ms=d.ms; if(d.rs){ const rd=d.rs.getReader(); for(;;){ const {value,done}=await rd.read(); if(done) break; if(fr) fr.close(); fr=value; const n=performance.now(); if(n-lt>=ms-8){ lt=n; snap(); } } } };`;
    const tr=t.clone(), pr=new MediaStreamTrackProcessor({track:tr}), w=new Worker(URL.createObjectURL(new Blob([code],{type:'text/javascript'})));
    w.onmessage=e=>{ const {bm,dt}=e.data; if(ARS.s!==st){ bm.close(); return; } bm.videoWidth=bm.width; bm.videoHeight=bm.height; bm.readyState=4; bm.currentTime=(ARX.video&&ARX.video.currentTime)||0; bm.arSnap=1;
      ARS.bm=bm; /* 지난 비트맵은 닫지 않음: 상자·해상도 판정이 await 사이에 같은 화면을 계속 그림(닫으면 조용히 실패) → GC 가 회수 */ ARS.t=performance.now(); ARS.n++; ARS.ms=dt; ARS.on=true; };
    w.onerror=e=>{ ARS.err=String(e.message||e); arSnapStop(); };
    w.postMessage({rs:pr.readable,ms:100},[pr.readable]); ARS.w=w; ARS.tr=tr; }
  catch(e){ ARS.err=String(e); arSnapStop(); ARS.s=st; } }
/* 분석에 쓸 화면: 최신 Worker 비트맵(0.6초 안 — 멈추면 video), 없으면 video */
function arSrc(){ const v=ARX.video; if(!v) return v; const st=ARX.stream||null; if(st!==ARS.s){ if(st) arSnapStart(st); else arSnapStop(); }
  const b=ARS.bm; return b&&ARS.on&&ARS.n>0&&performance.now()-ARS.t<600&&(v.videoWidth?b.width===v.videoWidth:true)?b:v; }
