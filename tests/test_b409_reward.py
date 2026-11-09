"""b409 (t692): 콜더쇼츠 ㅋ 읽기·1920 기본 비율 맵 이름 그림 4장·그림 재대조."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate("""()=>{const check=(v,s)=>{if(!v)throw Error(s)};
  const C=(id,name)=>({id,name,bosses:{},weekly:{},monthly:{},drops:{}}), H=['골더쇼츠','폴더쇼츠','골더쇼즈','골더쇼츠','필더쇼츠','골더쇼츠'];
  S.characters=[C('a','콜더쇼츠'),C('b','림강훈망')];ARX.nHist=H.slice();ARX.nLead=H.map(()=>false);check(arNameVote2().cid==='a','ㅋ name accepted from ㄱ reads when no pair');
  S.characters=[C('a','콜더쇼츠'),C('c','골더쇼츠')];ARX.nHist=H.slice();ARX.nLead=H.map(()=>false);check(arNameVote2().cid!=='a','ㅋ name not accepted when ㄱ pair is listed');
  S.characters=[C('a','콜더쇼츠')];ARX.nHist=['골더','골더','골더'];check(arNameVote2().cid==='','short reads unrelated');
  S.characters=[C('t','트딕이')];ARX.nHist=['드딕이','드딕이','드딕이','드딕이'];ARX.nLead=[false,false,false,false];check(arNameVote2().cid==='','ㅌ rule unchanged (needs aspirated read)');
  const L=arMapTplLoad().filter(t=>t.extra);check(AR_MAPTPL_MORE.length===19&&L.length===19,'4 b409 templates');for(const n of ['의지가 증명된 자리 <이지>','고요해진 함선 <하드>','악몽의 시계탑 <하드>'])check(L.some(t=>t.text===n),'template '+n);
  const cv=document.createElement('canvas');cv.width=1920;cv.height=1080;const M=arMapTplMatch,G=arMapGot;let got=[];arMapGot=t=>got.push(t);
  try{ ARX.mapBusy=true;ARX.mOcrT=Date.now();ARX.mapOk=false;ARX.mChgT=Date.now();ARX.mtRetryT=0;ARX.mprev=null;arMapTplMatch=()=>({text:'의지가 증명된 자리 <이지>',boss:'adversary',sc:.99});arMapWatch(cv);check(got.length===1&&ARX.mapSrc==='템플릿','template checked while OCR busy');
   arMapWatch(cv);check(got.length===1,'retry throttled 0.2s');
   ARX.mapBusy=false;ARX.mapOk=true;ARX.mOcrT=Date.now();ARX.mtNear=false;ARX.mtRetryT=0;arMapWatch(cv);check(got.length===1,'no extra work when settled and not near');
  }finally{arMapTplMatch=M;arMapGot=G;ARX.mapBusy=false;}
  return true;}""");assert r;b.close();print('PASS b409: ㅋ/ㄱ name vote with pair guard; 4 map templates; template retry while OCR busy, throttled')
finally:srv.terminate()
