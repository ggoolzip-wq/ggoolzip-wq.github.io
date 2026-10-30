# test_b305 (t537): 보스 확정 = 맵 이름+보상 상자 동시. 맵 이름 그대로면 상자 없어도(시간 지나도) 유지, 한 글자라도 바뀌면 즉시 중단, OCR 흔들림엔 유지
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
  r=pg.evaluate("""()=>{ const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d');
    const draw=t=>{ g.fillStyle='#202830'; g.fillRect(0,0,1920,1080); const R=arR('map',cv); g.fillStyle='#fff'; g.font='bold 20px "Gothic A1",sans-serif'; g.textBaseline='middle'; g.fillText(t,R.x*1920+4,(R.y+R.h/2)*1080); };
    const boss=BOSSES[0].id, now=Date.now(), o={}; ARX.lock=null; ARX.box=null; ARX.det.boss=''; ARX.det.diff='';
    draw('검은 마법사 보상 맵'); ARX.mapText='검은 마법사 보상 맵'; ARX.mapDet=null; o.noMap=arLockTry(cv,boss,now);
    ARX.mapDet={boss,diff:'',t:now}; ARX.det.boss=boss; ARX.box={boss,key:'k',t:now}; o.lock=arLockTry(cv,boss,now)&&!!ARX.lock;
    ARX.box.t=now-3600e3; o.okOld=arBoxOk(); o.same=arLockCheck(cv,'검은 마법사 보상 맵');
    o.jit=arLockCheck(cv,'검은 마법자 보상 맵'); o.jitBoss=ARX.det.boss===boss; o.blank=arLockCheck(cv,''); o.still=!!ARX.lock;
    draw('검은 마법사 보상 맴'); o.dist=arHashDist(arMapHash(cv),ARX.lock.hash); o.px=[...ARX.lock.hash].reduce((a,b)=>a+b,0); o.R=arR('map',cv); o.chg=arLockCheck(cv,'검은 마법사 보상 맴'); o.after=[ARX.det.boss,!!ARX.lock,!!ARX.box,arBoxOk()];
    ARX.det.boss=boss; ARX.box={boss,key:'k',t:now-3600e3}; o.noLockOld=arBoxOk(); ARX.det.boss=''; ARX.box=null; return o; }""")
  check('맵 이름 안 보이면 상자만으로 확정 안 함',r['noMap'] is False,r)
  check('맵 이름+상자 동시 → 확정',r['lock'] is True,r)
  check('확정 후 상자 1시간 지나도 기록 유지',r['okOld'] is True and r['same']=='keep',r)
  check('OCR 한 글자 흔들림(픽셀 그대로)엔 유지',r['jit']=='jitter' and r['jitBoss'] and r['blank']=='keep' and r['still'],r)
  check('맵 이름 한 글자 바뀜 → 즉시 중단',r['chg']=='stop' and r['after']==['',False,False,False],r)
  check('확정 없으면 기존처럼 상자 시간 만료',r['noLockOld'] is False,r)
  check('페이지 오류 없음',not errs,errs)
  b.close()
finally: srv.kill()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
