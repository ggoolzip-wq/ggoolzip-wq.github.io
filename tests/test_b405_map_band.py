"""Bright game background must not hide a narrow map title. No threshold weakening."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');pg.evaluate('''()=>{const ck=(x,s)=>{if(!x)throw Error(s)};const W=491,H=129,v=new Uint8Array(W*H);for(let y=0;y<H;y++)for(let x=300;x<W;x++)v[y*W+x]=220;for(let y=90;y<105;y++)for(let x=20;x<180;x++)v[y*W+x]=220;const I={v,W,H},B=arMapTplBands(I);ck(I.narrowBand&&B.some(b=>b.y0===90&&b.y1===104),'narrow title recovered');ck(arMapTplBands({v:new Uint8Array(W*H).fill(220),W,H}).length===0,'white screen not title');const Q={v:v.slice(),W,H};for(let y=0;y<H;y++)Q.v.fill(0,y*W+300,(y+1)*W);ck(arMapTplBands(Q).length===1&&!Q.narrowBand,'normal path unchanged');
 ARX.mapSt={boss:'dunkel',kind:'br',diff:''};ARX.runDiff=null;ARX.det={cid:'',boss:'',diff:''};ARX.rew=ARX.rwl=ARX.lock=ARX.box=null;
 const cv=document.createElement('canvas');cv.width=1920;cv.height=1080;const hint={text:'끝에 가까운 곳 <이지>',boss:'dunkel',sc:.999};
 ck(!arMapTplDiff('울메 가까운 끗 하드',hint,cv),'brackets required');ck(!arMapTplDiff('<미지>',hint,cv),'fuzzy tag not promoted');ck(!arMapTplDiff('<하드>',{...hint,sc:.949},cv),'strict visual check required');ck(!arMapTplDiff('<이지>',hint,cv),'unsupported boss difficulty rejected');ck(!ARX.runDiff&&!ARX.det.diff,'template label supplied no difficulty');ck(arMapTplDiff('울메 가까운 끗 <하드>',hint,cv),'independent actual tag accepted');ck(ARX.mapSt.diff==='hard'&&ARX.runDiff.diff==='hard','actual hard overrides template easy label');ck(!ARX.det.boss&&!ARX.rew&&!ARX.rwl,'shared map still requires box');ck(!ARX.tplNoDiff,'guard reset');}''');b.close()
 print('PASS b405: narrow bands only on failure; white/normal safety; independent exact OCR tag; .95/shared-map guards')
finally:srv.terminate()
