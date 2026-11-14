"""b427 (t561u): 카링 <이지> 오독(큰 공백 뒤 잡글, :011[:, -미1:, <미자, <미>) → 이지. 다른 난이도·보스 그대로."""
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
  for t,e,n in [('도위권 빛을 되찾은 사계 <011>     월 이\n| 기', ['kaling', 'easy', 'r'], 'w07 <011> 뒤 큰 공백 잡글'), ('도원경 빛을 되찾은 사계 <미자:       0”', ['kaling', 'easy', 'r'], '<미자:'), ('도원경 빛을 되찾은 사계 <미>            -따', ['kaling', 'easy', 'r'], '<미>'), ('도퀸권 죽음을 두른 나계 :011[:              티', ['kaling', 'easy', 'b'], '전투 :011[:'), ('도원권 죽음을 두른 나계 -미1:             11', ['kaling', 'easy', 'b'], '전투 -미1:'), ('도원견 폭음을 두른 사계 ~미디:          니니', ['kaling', 'easy', 'b'], '전투 ~미디:'), ('도원경 빛을 되찾은 사계 01            ,', ['kaling', '', 'r'], '여는 기호 없는 01은 난이도 안 정함'), ('도원경 빛을 되찾은 사계 <노멀>', ['kaling', 'normal', 'r'], '노멀 그대로'), ('도원경 빛을 되찾은 사계 <하드>', ['kaling', 'hard', 'r'], '하드 그대로'), ('카로테：마천루', ['kalos', '', 'w'], '칼로스 대기 맵 그대로'), ('격전의 마천루 <노멀>', ['kalos', 'normal', 'b'], '칼로스 전투 그대로'), ('어둠의 신전 <하드>', ['blackmage', 'hard', 'b'], '검은 마법사 그대로'), ('욕망의 제단 :하드-', ['jinhilla', 'hard', 'br'], '진힐라 그대로'), ('공허의 눈 <카오스>', ['dusk', 'chaos', 'br'], '더스크(이지 없음) 그대로')]:
    r=D(t); check(n,r==e,r)
  b.close()
finally: srv.terminate()
print('PASS b427' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
