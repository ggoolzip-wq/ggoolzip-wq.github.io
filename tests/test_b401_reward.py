"""Targeted regression: black-mage reward latch + no-boss capture candidate fence."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate('''()=>{const name='리멘 존재하지 않는 공간 <하드>';const T=arDetectBMap(name);if(!T.kind.includes('r')||T.boss!=='blackmage')return false;ARX.det={boss:'blackmage',diff:'hard'};ARX.rwl={boss:'blackmage',names:AR_BMAP.filter(x=>x[1]==='blackmage'&&x[2].includes('r')).map(x=>x[0]),diff:0};for(let i=0;i<8;i++)arRwlCheck(name+'\\n무관한 이펙트 잡음');if(!ARX.rwl)return false;arRwlCheck('리멘 거인의 심장');arRwlCheck('리멘 거인의 심장');if(!ARX.rwl)return false;arRwlCheck('헤네시스 마을');arRwlCheck('헤네시스 마을');if(ARX.rwl)return false;const v=document.createElement('video');ARX.video=v;ARX.stream={getVideoTracks:()=>[]};ARX.det={cid:'',boss:'',diff:''};if(arCandidates0(true).length)return false;return true;}''');assert r;print('PASS b401: blackmage fight/reward name + noise retains latch, unrelated map clears after 2, live unknown boss has 0 candidates');b.close()
finally:srv.terminate()
