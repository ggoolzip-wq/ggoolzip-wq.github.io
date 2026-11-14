"""b426 (t558u): 칼로스 전투 '격전의 마천루'가 '력전의 마천루'로 읽혀도 대기 맵 '마천루'가 아니라 전투 맵. 대기 맵은 그대로."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  D=lambda s: pg.evaluate("t=>{ARX.runDiff=null;ARX.mapSt=null;const d=arDetectBMap(t); return d?[d.boss,d.diff,d.kind]:null}",s)
  for t,e,n in [('즈로테           이\n력전의 마천루 <노멀>',['kalos','normal','b'],'v03 력전의 마천루 → 전투'),
                ('격전더 마천루 <노멀:',['kalos','normal','b'],'격전더 마천루 → 전투'),
                ('격전의 마천루 <노멀>',['kalos','normal','b'],'정확한 전투 그대로'),
                ('카로데 카로데 마천루 노멀:',['kalos','normal','br'],'보상 카로데 카로데 마천루'),
                ('(2) _ㅜ\n 카로테\n| 마천루',['kalos','','w'],'대기 맵(꼬리 없음) 그대로'),
                ('카로테：마천루',['kalos','','w'],'대기 맵 카로테：마천루 그대로'),
                ('카로테마천루',['kalos','','w'],'대기 맵 한 줄 그대로'),
                ('어둠의 신전 <하드>',['blackmage','hard','b'],'다른 보스 그대로')]:
    r=D(t); check(n,r==e,r)
  b.close()
finally: srv.terminate()
print('PASS b426' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
