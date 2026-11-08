"""Only confirmed map-name change ends a latched reward session."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate("""()=>{const check=(v,s)=>{if(!v)throw Error(s)};ARX.det={cid:'',boss:'',diff:''};ARX.box=ARX.lock=ARX.rew=ARX.rwl=ARX.mapSt=null;
 arMapState('의지가 증명된 자리 <이지>',Date.now());check(arRewOn()&&arBoxOk()&&!ARX.box&&ARX.det.boss==='adversary','reward starts without box');
 const video=document.createElement('video');ARX.video=video;ARX.stream={getVideoTracks:()=>[]};ARX.det.diff='';check(arCandidates0(true).length===0,'unknown difficulty cannot search all difficulty items');ARX.cfg.rewx=true;check(arCandidates(true).length===0,'extended candidates also need difficulty');ARX.cfg.rewx=false;ARX.det.diff='easy';ARX.mapSt.t=1;check(arRewMap(Date.now()),'no 8s expiry');ARX.rew.pend=1;arRewCheck(null,null);check(arRewOn(),'no 3s unread timeout');
 arRwlCheck('');arRwlCheck('잡음가나다');arRwlCheck('다른잡음라마');check(ARX.rwl,'unrelated OCR noise is not repeated different map');
 arRwlCheck('의지가 증명된 자리');check(ARX.rwl&&ARX.rwl.diff===0,'same map resets other-name confirmation');
 arRwlCheck('헤네시스 마을');check(ARX.rwl,'one different map not enough');arRwlCheck('헤네시스 마을');check(!ARX.rwl&&!ARX.rew&&!ARX.mapSt&&!ARX.det.boss,'two same different names stop and clear stale map');
 arRewardMapStart(arDetectBMap('존재하지 않는 공간 <하드>'),Date.now());check(!ARX.rew,'shared fight/reward map still needs disambiguation');return true;}""");assert r;b.close();print('PASS b402: reward-only map starts without box; age/unread/noise retain; repeated different map stops; shared-map safety retained')
finally:srv.terminate()
