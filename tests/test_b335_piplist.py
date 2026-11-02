# test_b335 (t639): PIP 창 '보상 맵 인식' 칸 아래 이번 라이브 득템 목록 — 실시간, 라이브 다시 시작하면 비움, 중간에 열어도 전체. MBT_SHOTDIR 에 pip_list.png
#  headless 에 documentPictureInPicture 없음 → iframe 창으로 requestWindow 흉내. MBT_SHOTDIR 에 button.png / pip.png
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }"""
REW="""b=>{ const A=window.AR; A.det.boss=b; A.det.diff='hard'; A.rew={boss:b,diff:'hard',hash:null}; arLivePaint(); }"""
FAKE="""()=>{ Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}}); }"""
STUB="""()=>{ window.arBoxOk=()=>true; window.arTarget=()=>({c:S.characters[0]}); window.arToast=()=>{}; window.arCandidates=()=>[{k:window.__k,b:findBoss(AR.det.boss)}]; }"""
REC="""([b,k])=>arSessAdd(k,findBoss(b).name,S.characters[0].name)"""
PIPTXT="()=>{ const d=document.getElementById('fakePip')?.contentDocument; const e=d&&d.querySelector('.ar-piprec'); return e?e.innerText:null; }"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid')
    pg.evaluate(REC,['lucid','eye']); pg.evaluate(REC,['will','belt'])
    check('기록이 세션 목록에 쌓임',pg.evaluate("window.AR.sessRec.length")==2,pg.evaluate("window.AR.sessRec"))
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(400)
    t=pg.evaluate(PIPTXT)
    check('PIP 중간에 열어도 전체 목록',t is not None and '2개' in t and '마력이 깃든 안대' in t and '몽환의 벨트' in t and '트딕이' in t,t)
    order=pg.evaluate("()=>{ const d=document.getElementById('fakePip').contentDocument; const a=d.querySelector('.ar-cboss'), r=d.querySelector('.ar-piprec'); return !!(a.compareDocumentPosition(r)&Node.DOCUMENT_POSITION_FOLLOWING); }")
    check('보상 맵 인식 칸 아래',order)
    check('시각·아이콘',pg.evaluate("()=>{ const li=document.getElementById('fakePip').contentDocument.querySelector('.ar-prl li'); return /\\d\\d:\\d\\d:\\d\\d/.test(li.innerText)&&!!li.querySelector('img'); }"))
    pg.evaluate(REC,['seren','book']); pg.wait_for_timeout(150); t=pg.evaluate(PIPTXT)
    check('실시간 추가(최신이 위)','3개' in t and t.index('저주받은 마도서')<t.index('마력이 깃든 안대'),t)
    pg.screenshot(path=os.path.join(OUT,'pip_list.png'),clip={'x':1000,'y':0,'width':600,'height':560})
    pg.evaluate("()=>{ arDisconnect(); arStart(document.createElement('video')); }"); pg.evaluate("()=>arPipRec()"); pg.wait_for_timeout(150); t=pg.evaluate(PIPTXT)
    check('라이브 다시 시작하면 비움',t is not None and '0개' in t and '아직 기록된' in t,t)
    pg.evaluate("()=>arDisconnect()")
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
