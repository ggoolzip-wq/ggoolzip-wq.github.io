"""Exact input bitmaps of m09 false eye hits; real-icon composites retain detail."""
import sys,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
cases=json.loads((Path(__file__).parent/'fixtures/b405_eye_false.json').read_text())
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate('''async E=>{const out=[];for(const e of E){const im=new Image();im.src=e.url;await im.decode();const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;const g=cv.getContext('2d');g.drawImage(im,0,0);const F={d:g.getImageData(0,0,cv.width,cv.height).data,w:cv.width,h:cv.height},px=e.rect[2],A=await arTemplates(['eye'],px),T=arXcache(A.eye,px,0,1,1).Tf;out.push(arEyeDetail(F,T,e.rect[0],e.rect[1]));}let positives=0;for(const px of [56,84]){const A=await arTemplates(['eye'],px);for(const a of [0,30,90,180]){const T=arXcache(A.eye,px,a,1,1).Tf;for(const brightness of [1,.75,.6]){const d=Float32Array.from(T.d,(v,i)=>i%4===3?v:v*brightness);if(!arEyeDetail({d,w:T.w,h:T.h},T,0,0))throw Error('real-icon detail rejected '+px+'/'+a+'/'+brightness);positives++;}}}if(out.some(Boolean))throw Error('false-eye bitmap accepted '+out);return {negativeRejected:out.length,iconCompositesAccepted:positives};}''',cases);print('PASS b405 eye:',r);b.close()
finally:srv.terminate()
