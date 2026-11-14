"""b430 (pt573u): w03 백옥·w01 연마석이 실행마다 잡혔다 놓쳤다 하던 것 — 일반 구조로 고침.
① 배너(획득 알림) 아이콘 크기: t562 WZ 아이콘 교체 때 56px×배율이 됐지만 실제 화면은 41px×배율(1366 실영상 w03 백옥 .78, n4·v02 흑옥 .85) → 56px에선 .31로 배너 칸이 사실상 꺼져 있었음.
② 바닥 칸도 실제 드롭 그림(dropsprites) 사용 — 연마석은 바닥에 잠깐 놓일 때 인벤 아이콘과 모양이 달라 바닥 칸이 못 봤음.
③ 공중 약한 맞춤(색 차이 airSad~airSad2): 다른 시각 2번 + 움직임 있을 때만 추적 기록. 한 장·제자리는 기록 안 함."""
import sys,subprocess,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
T=Path(__file__).parent/'fixtures'
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=str(Path(__file__).parent.parent),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
BAN="""async ([img,px])=>{ const im=new Image(); im.src='data:image/png;base64,'+img; await im.decode(); const bmp=await createImageBitmap(im);
 const r=await arMatchRun({bmp},['r_white'],[px],{thr:.3}); let b=0; for(const h of r.hits||[]) b=Math.max(b,h.score); return +b.toFixed(3); }"""
GND="""async ([img])=>{ const im=new Image(); im.src='data:image/jpeg;base64,'+img; await im.decode(); const pxs=arGroundPx(720), o=d=>({multi:true,tiles:true,sad:ARX.cfg.groundSad,thr:.3,f:Math.max(2,Math.round(pxs[1]/9)),angles:[0],sq:[1],pxs,drop:d});
 const out=[]; for(const d of [true,false]){ const bmp=await createImageBitmap(im); const r=await arMatchRun({bmp},['g_life'],pxs,o(d)); const h=(r.hits||[]).sort((a,b)=>b.score-a.score)[0]; out.push(h?[+h.score.toFixed(3),+(h.sad||0).toFixed(1)]:null); } return out; }"""
SOFT="""()=>{ const on=ARX.cfg.on; ARX.cfg.on=false; const t0=1e6, H=(x,y,sad)=>({k:'r_white',x,y,w:56,h:56,score:.76,sad,air:true});
 const mk=h=>(h.ok=h.sad<=ARX.cfg.airSad,h.soft=!h.ok&&arAirSoft(h),h); const run=seq=>{ ARX.tracks=[]; let n=0; for(const [h,t] of seq){ const H2=mk(h); if(H2.ok||H2.soft) n+=arTrack([H2],720,t).length; } return n; };
 const r={moving:run([[H(600,300,43),t0],[H(612,240,44),t0+170]]), single:run([[H(600,300,43),t0]]), still:run([[H(600,300,43),t0],[H(601,300,43),t0+170]]), toohigh:run([[H(600,300,49),t0],[H(612,240,49),t0+170]])};
 ARX.cfg.on=on; return r; }"""
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');pg.wait_for_timeout(800)
  ip=pg.evaluate("()=>[arIconPx(776,'banner',{videoWidth:1376,videoHeight:776}),arIconPx(1080,'banner',{videoWidth:1920,videoHeight:1080})]")
  check('배너 아이콘 크기 = 41px × UI배율 (1366·1920 최적 = 41)',ip==[41,41],ip)
  img=base64.b64encode((T/'b430'/'w03_banner.png').read_bytes()).decode()
  s41=pg.evaluate(BAN,[img,41]); s56=pg.evaluate(BAN,[img,56])
  check('w03 백옥 획득 배너: 41px .73 이상 (배너 기준 .7)',s41>=.73,s41)
  check('w03 백옥 획득 배너: 예전 56px는 .5 아래 (꺼져 있던 원인)',s56<.5,s56)
  g=pg.evaluate(GND,[base64.b64encode((T/'b429'/'w01_ground.jpg').read_bytes()).decode()])
  check('w01 바닥 연마석: 바닥 칸 드롭 그림 = groundThr 이상·groundSad 이하',g[0] and g[0][0]>=pg.evaluate('ARX.cfg.groundThr') and g[0][1]<=pg.evaluate('ARX.cfg.groundSad'),g)
  check('w01 바닥 연마석: 인벤 아이콘으론 groundThr 아래 (못 보던 원인)',g[1] is None or g[1][0]<pg.evaluate('ARX.cfg.groundThr'),g)
  check('바닥 칸이 드롭 그림을 씀 (arItemScan drop)',pg.evaluate("()=>/drop:ARX\\.cfg\\.groundDropSpr!==false/.test(arItemScan.toString())"),'')
  s=pg.evaluate(SOFT)
  check('약한 맞춤: 2번+움직임 → 1건, 한 장·제자리·색차 46 초과 → 0건',s=={'moving':1,'single':0,'still':0,'toohigh':0},s)
  check('빌드 b430 이상',pg.evaluate("document.documentElement.dataset.build||document.body.dataset.build||''")>='b430',pg.evaluate("document.documentElement.dataset.build||document.body.dataset.build||''"))
  b.close()
finally: srv.terminate()
print('PASS b430' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
