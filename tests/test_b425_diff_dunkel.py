"""b425 (t557u): 벨로나 '<이지>' 오독(미디·미지) 난이도, 듄켈 전투 '을메 기까운 꽂' 맵 인식. 오인 방지 유지."""
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
  for t,e,n in [('터주받은 테네마 신전 <미디-',['bellona','easy','b'],'v07 전투 <미디- → 이지'),
                ('글라톰 글파기 솔라톰의 유븐 "미지:',['bellona','easy','r'],'v07 보상 "미지: → 이지'),
                ('솔라툼 골짜기 : 솔라툼의 유산 <하드>',['bellona','hard','r'],'정확한 하드 그대로'),
                ('을메 기까운 꽂 <하드:',['dunkel','hard','br'],'v04 전투 을메 기까운 꽂'),
                ('플매 기까운 끗 <하드:',['dunkel','hard','br'],'v04 플매 기까운 끗'),
                ('을메 기까운 꽂',None,'난이도 꼬리 없으면 그대로 미인식'),
                ('어둠의 신전 <하드>',['blackmage','hard','b'],'정확한 다른 맵 그대로'),
                ('을메 기까운 핌 <하드>',None,'가운데만 같고 자모 4개 틀리면(.6) 미인식')]:
    r=D(t); check(n,r==e,r)
  r=pg.evaluate("()=>arTagDiff('공허의 눈 <미디>',findBoss('dusk'))"); check('이지 없는 보스(더스크)에는 이지 안 붙임',r=='',r)
  b.close()
finally: srv.terminate()
print('PASS b425' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
