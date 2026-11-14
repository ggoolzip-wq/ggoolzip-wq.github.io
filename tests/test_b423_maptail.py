"""b423 (t555u): '<하드>'가 ':하드-'로 읽힌 진힐라 맵 줄 — 끝 난이도 조각을 이름에서 빼고 인식. 오인 방지 유지."""
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
  t='고 통디 미궁 혹망의 제단 :하드-'
  check('v02 실제 OCR(7.3초 줄) → 진힐라 하드 보상', D(t)==['jinhilla','hard','br'], D(t))
  check('기존 꺾쇠 줄 그대로', D('고통의 미궁 : 욕망의 제단 <하드>')==['jinhilla','hard','br'], D('고통의 미궁 : 욕망의 제단 <하드>'))
  check('난이도 조각만 있는 줄은 맵 아님', D(':하드-') is None, D(':하드-'))
  check('난이도 꼬리 없는 자모 3개 틀린 이름은 미인식(문턱 .8)', D('고통되 미궁 혹망의 페단') is None, D('고통되 미궁 혹망의 페단'))
  check('b425: 꼬리 있는 자모 3개(.77) 진힐라 줄은 인식', D('고통되 미궁 혹망의 페단 :하드-')==['jinhilla','hard','br'], D('고통되 미궁 혹망의 페단 :하드-'))
  check('듄켈 b420 꼴 유지', D('메 가까운 끗 하드')==['dunkel','hard','br'], D('메 가까운 끗 하드'))
  r=pg.evaluate("""()=>{ ARX.rew=null; ARX.rwl=null; ARX.lock=null; ARX.runDiff=null; ARX.mapPend=null;
    ARX.mapSt={boss:'adversary',kind:'b',diff:'normal',name:'전설로거듭나는운명',t:Date.now()}; ARX.mOcrT=12345;
    const L='픔명의 전장 의지가 증명된 파리 <노멸>'; arMapState(L,Date.now()); const a=[ARX.mapSt.kind,ARX.mOcrT];
    arMapState(L,Date.now()); const b=ARX.mapSt.kind;
    ARX.mapPend=null; ARX.mapSt={boss:'will',kind:'w',diff:'hard',name:'거울에비친빛의신좌',t:Date.now()}; ARX.mOcrT=777;
    arMapState('에스페라 회절의 회랑 <하드>',Date.now()); const c=[ARX.mapSt.kind,ARX.mOcrT];
    return {a,b,c}; }""")
  check('v01 대적자 비슷한 보상 읽기 1번째: 상태 유지 + 확인 읽기 바로(mOcrT=0)', r['a']==['b',0], r)
  check('2번째 같은 읽기에 보상 맵 확정(2번 확인 규칙 유지)', r['b']=='r', r)
  check('보상 아닌 바뀜(대기→전투)은 기존 3초 주기 그대로', r['c'][1]==777 and r['c'][0]=='w', r)
  b.close()
finally: srv.terminate()
print('PASS b423' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
