# test_b349 (t655): PIP 맨 위 현재 캐릭터 한 줄(아바타·이름·Lv/직업·월드 / 인식 중·미인식), 실시간 갱신, 스크롤 없음. 원본 b347 틀
# (b347 t651): PIP 위치 안내 없앰 + 창 높이 최소화 (상태 칸·득템 목록·수익 칸·반지 고르기 유지). MBT_SHOTDIR 에 pip_idle.png, pip_sale.png
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
    PC="()=>{ const d=document.getElementById('fakePip').contentDocument, e=d.querySelector('.ar-pipchar'), c=d.querySelector('.ar-cboss'); if(!e) return null; const r=e.getBoundingClientRect(); return {t:e.textContent,h:r.height,b:r.bottom,cb:c.getBoundingClientRect().top,img:!!e.querySelector('img,.avatar,[class*=av]')}; }"
    m=pg.evaluate("()=>[window.AR.pip.minW,window.AR.pip.minH]"); check('PIP 크기 320×318 (b347 286 + 캐릭터 줄 32)',m==[320,318],m)
    pg.evaluate("()=>{ ARX.det.cid=''; arLivePaint(); }"); pg.wait_for_timeout(300); r=pg.evaluate(PC); print(r)
    check('캐릭터 줄이 보상 맵 인식 칸 위',r and r['b']<=r['cb']+1 and r['h']>=20,r)
    check('미인식 표시',r and '미인식' in r['t'],r)
    pg.evaluate("()=>{ ARX.det.cid='c0'; }"); pg.wait_for_timeout(500); r=pg.evaluate(PC); print(r)
    check('실시간: 인식되면 이름·Lv·월드 표시(따로 그리기 호출 없이)',r and '트딕이' in r['t'] and 'Lv.285' in r['t'] and '스카니아' in r['t'],r)
    check('아바타 있음',r and r['img'],r)
    for k in ['eye','belt','h_pocket']*4: pg.evaluate(REC,['lucid',k])
    pg.wait_for_timeout(200); f=pg.evaluate(FIT); check('창 안에 다 들어감(스크롤 없음)',f['sh']<=f['ih']+1 and f['sw']<=f['iw']+1,f)
    shot(pg,os.path.join(OUT,'pip_char.png'))
    pg.evaluate("()=>{ S.characters[0].bosses[findBoss('will').id].party=2; save(); }"); pg.evaluate(REW,'will'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.__k='belt'; arRecord('belt',.9,'t'); }"); pg.wait_for_timeout(300)
    s2=pg.evaluate(VIS,'.ar-pipsale'); f=pg.evaluate(FIT); o=pg.evaluate("()=>{ const e=document.getElementById('fakePip').contentDocument.querySelector('.ar-pipsale'); return [e.scrollHeight,e.clientHeight]; }")
    check('2인 수익 칸도 스크롤 없이 창 안',s2 and s2['b']<=s2['ih']+1 and f['sh']<=f['ih']+1 and o[0]<=o[1]+1,(s2,f,o))
    shot(pg,os.path.join(OUT,'pip_char_sale.png'))
    pg.evaluate("()=>arDisconnect()"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
