"""Video map-name additions preserve OCR, difficulty and shared-map box gates."""
import sys,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate("""()=>{const check=(v,s)=>{if(!v)throw Error(s)};
  const loaded=arMapTplLoad();check(AR_MAPTPL_MORE.length===19&&loaded.filter(t=>t.extra).length===19,'15+4(b409) actual templates built/loaded');
  for(const n of AR_MAPTPL_NEAR)check(arMapTplMin({text:n+' <하드>',extra:false})===.95&&arMapTplMin({text:n+' <하드>',extra:true})===.95,'near-name guard '+n);
  const original=[arMapTplImg,arMapTplBands,arMapTplLoad,arMapTplScore];let L=[];arMapTplImg=()=>({v:[],W:2,H:2});arMapTplBands=()=>[{}];arMapTplLoad=()=>L;arMapTplScore=(I,B,T)=>T.score;
  const T=(text,score,extra)=>({text,score,extra,boss:'will'}),cv=document.createElement('canvas');cv.width=1920;cv.height=1080;
  try{L=[T('바스러지는 빛 <하드>',.899,true)];check(!arMapTplMatch(cv),'new below .90 rejected');L[0].score=.901;check(arMapTplMatch(cv),'new >=.90 accepted');
  L=[T('욕망의 제단 <하드>',.949,false)];check(!arMapTplMatch(cv),'legacy near-name below .95 rejected');L[0].score=.951;check(arMapTplMatch(cv),'near >=.95 accepted');
  L=[T('바스러지는 빛 <하드>',.801,false)];check(arMapTplMatch(cv),'legacy non-near threshold unchanged');L=[T('바스러지는 빛 <하드>',.96,true),T('다른 이름 <하드>',.93,true)];check(!arMapTplMatch(cv),'rival margin retained');
  }finally{[arMapTplImg,arMapTplBands,arMapTplLoad,arMapTplScore]=original;}
  ARX.mapSt=ARX.mapPend=ARX.rew=ARX.rwl=ARX.lock=ARX.box=ARX.mapDet=null;ARX.det={cid:'',boss:'',diff:''};ARX.runDiff={boss:'will',diff:'hard'};ARX.mprev=null;ARX.mOcrT=0;ARX.mapBusy=false;
  const match=arMapTplMatch;arMapTplMatch=()=>({text:'바스러지는 빛 <하드>',boss:'will',sc:.999});try{arMapWatch(cv);check(ARX.mapSt?.boss==='will'&&!ARX.rew&&!ARX.rwl&&!ARX.det.boss,'shared map still requires box');}finally{arMapTplMatch=match;}
  ARX.mapSt=ARX.mapPend=ARX.rew=ARX.rwl=ARX.lock=ARX.box=ARX.mapDet=null;ARX.det={cid:'',boss:'',diff:''};ARX.runDiff=null;ARX.mprev=null;ARX.mOcrT=0;ARX.mapBusy=false;
  const ocr=arOcrLoad;ARX.ocr=null;arOcrLoad=()=>Promise.resolve();arMapTplMatch=()=>({text:'고요해진 함선 <하드>',boss:'lotus',sc:.999});try{arMapWatch(cv);check(!ARX.det.diff,'template cannot supply hard difficulty');ARX.video=document.createElement('video');ARX.stream={getVideoTracks:()=>[]};check(arCandidates0(true).length===0,'unknown difficulty cannot search all item tables');}finally{arMapTplMatch=match;arOcrLoad=ocr;}
  return true;}""");assert r;b.close();print('PASS b404: 15 templates; .90/.95 and rival margin; OCR/difficulty/shared-map guards retained')
finally:srv.terminate()
