"""b429 (pt567u·t569): 생명의 연마석 — 인벤 아이콘과 실제 떨어진 그림이 달라(반짝이·후광 23%, 판 1.2배) 공중 점수 0.47~0.58로 못 잡던 것.
실제 영상에서 자른 '드롭 그림' 템플릿(src/dropsprites.json, tools/build_dropsprites.py)으로 공중 검사 → 바닥 0.85·공중 0.70.
신념의 연마석 드롭 그림은 아이콘 두 장 색 차이를 옮겨 만든 것 — 생명/신념 색 구분(arVarDist)이 그대로 맞아야 함."""
import sys,subprocess,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
FX=Path(__file__).parent/'fixtures'/'b429'
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=str(Path(__file__).parent.parent),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
JS="""async ([img,drop])=>{ const im=new Image(); im.src='data:image/jpeg;base64,'+img; await im.decode(); const bmp=await createImageBitmap(im); const px=arGroundPx(720)[1];
 const r=await arMatchRun({bmp},['g_life'],[px],{multi:true,tiles:true,sad:999,thr:.3,f:Math.max(2,Math.round(px/9)),angles:arAirAngles(20),aref:10,vmax:24,kvmax:drop?{g_life:80}:null,sq:[1],lane:'air',drop});
 const h=(r.hits||[])[0]; return h?[h.k,+h.score.toFixed(3),h.x,h.y,(h.vd||[]).map(v=>v[0]+':'+v[1])]:null; }"""
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');pg.wait_for_timeout(800)
  n=pg.evaluate("()=>Object.keys(AR_DROP_SPR)")
  check('드롭 그림 템플릿 g_life·g_faith 들어감',set(n)>={'g_life','g_faith'},n)
  g=base64.b64encode((FX/'w01_ground.jpg').read_bytes()).decode(); a=base64.b64encode((FX/'w01_air.jpg').read_bytes()).decode()
  gd=pg.evaluate(JS,[g,True]); gi=pg.evaluate(JS,[g,False]); ad=pg.evaluate(JS,[a,True])
  check('w01 바닥 연마석: 드롭 그림 0.73 이상 (자리 x 880~930, y 390~430)',gd and gd[0]=='g_life' and gd[1]>=.73 and 880<=gd[2]<=930 and 390<=gd[3]<=430,gd)
  check('w01 바닥 연마석: 예전 아이콘은 0.6 아래 (못 잡던 원인)',gi is None or gi[1]<.6,gi)
  check('w01 공중(돌며 나는) 연마석: 드롭 그림 0.65 이상, 신념보다 생명 색이 가까움',ad and ad[0]=='g_life' and ad[1]>=.65,ad)
  b.close()
finally: srv.terminate()
print('PASS b429' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
