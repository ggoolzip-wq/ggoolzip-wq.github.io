"""Black-mage occlusion path: strict band plus full shape at the same position."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate("""()=>{const orig=arNcc,G={d:[],w:10,h:10},T={},A={},B={};let band=.95,full=.59,checked=false;
  arNcc=(d,w,h,t,x0,x1,y0,y1)=>{if(t===T){if(x0!==2||x1!==2||y0!==2||y1!==2)throw Error('full guard must use band location');checked=true;return [[full,2,2]];}return t===A?[[.95,1,1]]:[[band,2,2]];};
  try{if(arBoxBlackmage(G,G,T,A,B)!==0||!checked)throw Error('weak full shape accepted');full=.61;const ok=arBoxBlackmage(G,G,T,A,B);if(Math.abs(ok-.8)>1e-9)throw Error('strict pair rejected');band=.899;if(arBoxBlackmage(G,G,T,A,B)!==0)throw Error('weak band accepted');return true;}finally{arNcc=orig;}}""");assert r;b.close();print('PASS b403: band >=.90 and same-position full >=.60, weak band/full rejected')
finally:srv.terminate()
