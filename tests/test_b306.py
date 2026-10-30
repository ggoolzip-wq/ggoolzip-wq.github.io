# test_b306 (t538/t539): 보스 맵 표(대기/전투/보상)로 보스·난이도 판별, 전투 맵 진입 = 클리어 시간 시작, 대기 맵 = 버림
import os,sys,subprocess,tempfile,shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
P=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(P),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
from playwright.sync_api import sync_playwright
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox']); pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('https://**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{P}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
  r=pg.evaluate("""()=>{ const D=t=>{ const b=arDetectBMap(t); return b?[b.boss,b.diff,b.kind]:null; }, o={}; ARX.runDiff=null;
    o.a=D('고요한 제단 <노멀>'); o.b=D('라무라무 계곡 : 고요한 제단 <노말>'); o.c=D('라무라무 신전 <카오스>'); o.d=D('라무라무 신전'); o.e=D('가디언 엔젤 슬라임의 제단 <노멀>');
    o.f=D('공허의 눈 앞 <카오스>'); o.g=D('공허의 눈 <카오스>'); o.h=D('검은 바다：환영이 벗겨진 폐허'); o.i=D('헤네시스'); ARX.runDiff=null; o.j=D('솔라툼 골짜기：솔라툼의 유산');
    ARX.clr=null; ARX.clrHold=false; const n=Date.now(); arMapHit(arDetectBoss('고요한 제단 <노멀>'),n); o.rewNoStart=!ARX.clr;
    arMapState('라무라무 신전 <노멀>',n); o.start=ARX.clr&&ARX.clr.mapT===n&&ARX.clr.boss==='slime'&&ARX.clr.diff==='normal';
    arMapState('가디언 엔젤 슬라임의 제단 <노멀>',n+5); o.waitDrop=!ARX.clr; return o; }""")
  check("스크린샷 문구 '고요한 제단 <노멀>' → 슬라임 노멀 보상 맵",r['a']==['slime','normal','r'],r)
  check("지역명·'<노말>' OCR 변형도",r['b']==['slime','normal','r'],r)
  check('전투 맵 <카오스>, 꺾쇠 없으면 같은 판 마지막 난이도 유지',r['c']==['slime','chaos','b'] and r['d']==['slime','chaos','b'],r)
  check('대기 맵 구분 (슬라임 제단, 공허의 눈 앞 vs 공허의 눈)',r['e']==['slime','normal','w'] and r['f']==['dusk','chaos','w'] and r['g'][0]=='dusk' and 'r' in r['g'][2],r)
  check('표기 없는 흉성 2페이즈·벨로나 보상맵, 일반 맵은 없음',r['h'] and r['h'][:1]==['star'] and r['h'][2]=='b' and r['j'] and r['j'][0]=='bellona' and r['i'] is None,r)
  check('클리어 시간: 보상 맵만으론 시작 안 함, 전투 맵 진입=시작, 대기 맵이면 버림',r['rewNoStart'] and r['start'] and r['waitDrop'],r)
  check('페이지 오류 없음',not errs,errs)
  b.close()
finally: srv.kill()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
