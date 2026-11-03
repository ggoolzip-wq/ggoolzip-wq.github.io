# test_b347 (t651): PIP 위치 안내 없앰 + 창 높이 최소화 (상태 칸·득템 목록·수익 칸·반지 고르기 유지). MBT_SHOTDIR 에 pip_idle.png, pip_sale.png
#  headless 에 documentPictureInPicture 없음 → iframe 창 흉내(resizeTo = iframe 크기 바꿈)
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
FAKE="""()=>{ Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:0;outline:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; Object.defineProperty(w,'outerWidth',{get:()=>w.innerWidth}); Object.defineProperty(w,'outerHeight',{get:()=>w.innerHeight}); w.resizeTo=(x,y)=>{ window.__rz=(window.__rz||0)+1; f.style.width=x+'px'; f.style.height=y+'px'; }; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}}); }"""
STUB="""()=>{ window.arBoxOk=()=>true; window.arTarget=()=>({c:S.characters[0]}); window.arToast=()=>{}; window.arCandidates=()=>[{k:window.__k,b:findBoss(window.AR.det.boss)}]; }"""
REC="""([b,k])=>arSessAdd(k,findBoss(b).name,S.characters[0].name)"""
def shot(pg,n):
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=n,clip={'x':f['x']-10,'y':f['y']-10,'width':f['width']+20,'height':f['height']+20})
# PIP 안 내용이 창 안에 다 보이는지 (스크롤 없이, 목록만 자체 스크롤)
FIT="""()=>{ const d=document.getElementById('fakePip').contentDocument, w=d.defaultView; return {sh:d.documentElement.scrollHeight, ih:w.innerHeight, iw:w.innerWidth, sw:d.documentElement.scrollWidth}; }"""
VIS="""s=>{ const d=document.getElementById('fakePip').contentDocument, e=d.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return {h:r.height,b:r.bottom,ih:d.defaultView.innerHeight,show:getComputedStyle(e).display!=='none'&&r.height>0}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate(FAKE); pg.evaluate("()=>{ window.__mv=null; }"); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(500)
    m=pg.evaluate("()=>[window.AR.pip.minW,window.AR.pip.minH]"); print('SIZE',m)
    check('최소 높이 ≤ 320 (b346 630 → 짧게, b349 캐릭터 줄 포함)',m[1]<=320,m)
    check('폭 ≥ 320',m[0]>=320,m)
    check('위치 안내 없음',pg.evaluate("()=>!document.getElementById('fakePip').contentDocument.querySelector('.ar-piphint')"))
    check('arPipHint 함수 없음',pg.evaluate("()=>typeof arPipHint==='undefined'"))
    check('위치 계산은 그대로(ARX.pipPos)',pg.evaluate("()=>!!window.AR.pipPos&&typeof window.AR.pipPos.x==='number'"))
    for i,k in enumerate(['eye','belt','h_pocket']*4): pg.evaluate(REC,['lucid',k])
    pg.wait_for_timeout(200)
    f=pg.evaluate(FIT); check('평소: 창 안에 다 들어감(스크롤 없음)',f['sh']<=f['ih']+1,f)
    l=pg.evaluate(VIS,'.ar-prl'); check('득템 목록 작은 영역에서 스크롤',l and l['h']<=200 and pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-prl'); return e.scrollHeight>e.clientHeight; }"),l)
    check('상태 칸 보임',(pg.evaluate(VIS,'.ar-cboss') or {}).get('show'))
    shot(pg,os.path.join(OUT,'pip_idle.png'))
    pg.evaluate("()=>{ window.__k='eye'; arRecord('eye',.9,'t'); }"); pg.wait_for_timeout(300)
    s=pg.evaluate(VIS,'.ar-pipsale'); f=pg.evaluate(FIT)
    check('수익 칸: 창 안에 다 들어감',s and s['show'] and s['b']<=s['ih']+1 and f['sh']<=f['ih']+1,(s,f))
    check('수익 칸 열리면 목록 칸 숨김(자리 대신 씀)',not (pg.evaluate(VIS,'.ar-piprec') or {}).get('show'))
    check('수익 칸 요소 그대로',pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-pipsale'); return !!(e.querySelector('.rvico img')&&e.querySelector('.ar-psn')&&e.querySelector('.ar-psamt')&&e.querySelector('[data-fee=s]')&&e.querySelector('[data-ps=ok]')&&e.querySelector('[data-ps=no]')); }"))
    shot(pg,os.path.join(OUT,'pip_sale.png'))
    pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('[data-ps=no]').click()"); pg.wait_for_timeout(200)
    check('수익 칸 닫히면 목록 다시 보임',(pg.evaluate(VIS,'.ar-piprec') or {}).get('show') and pg.evaluate(VIS,'.ar-pipsale') is None)
    # 2인(분배 수수료 줄 추가) + 반지 고르기도 창 안
    pg.evaluate("()=>{ S.characters[0].bosses[findBoss('will').id].party=2; save(); }"); pg.evaluate(REW,'will'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.__k='belt'; arRecord('belt',.9,'t'); }"); pg.wait_for_timeout(300)
    o=pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-pipsale'); return [e.scrollHeight,e.clientHeight]; }"); print('2P',o); check('2인 수익 칸 스크롤 없이 다 보임',o[0]<=o[1]+1,o)
    s=pg.evaluate(VIS,'.ar-pipsale'); f=pg.evaluate(FIT); check('2인 수익 칸도 창 안',s and s['b']<=s['ih']+1 and f['sh']<=f['ih']+1,(s,f))
    pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('[data-ps=no]').click()"); pg.wait_for_timeout(200)
    pg.evaluate("()=>{ const c=S.characters[0], b=findBoss('lucid'); ARX.saleQ=[{cid:c.id,bid:b.id,key:'x',ik:'chaosbox',pick:'cb',u:'cb@1'}]; arPipSale(); }"); pg.wait_for_timeout(200)
    s=pg.evaluate(VIS,'.ar-pipsale'); f=pg.evaluate(FIT); o=pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-pipsale'); return [e.scrollHeight,e.clientHeight]; }"); print('CB',o)
    check('칠흑 상자 고르기도 창 안(넘치면 그 칸만 스크롤)',s and s['b']<=s['ih']+1 and f['sh']<=f['ih']+1,(s,f))
    shot(pg,'/tmp/pip_cb.png')
    pg.evaluate("()=>arDisconnect()"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
