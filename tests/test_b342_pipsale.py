# test_b342 (t646): PIP 열린 상태 자동 기록 → 모달 대신 PIP 아래 수익 기록 칸 (askRev [기록하기] 와 같은 저장). 1인=판매 수수료만, 2인+=판매+분배·자동 분배, 여러 개 줄 세움. MBT_SHOTDIR 에 pip_record.png
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
PIPTXT="()=>{ const d=document.getElementById('fakePip')?.contentDocument; const e=d&&d.querySelector('.ar-piprec'); return e?e.innerText:null; }"
SALE="()=>{ const d=document.getElementById('fakePip').contentDocument; const e=d.querySelector('.ar-pipsale'); return e?{t:e.innerText,v:e.querySelector('.ar-psamt').value,rows:e.querySelectorAll('.rvfrow').length,after:e.previousElementSibling&&e.previousElementSibling.className}:null; }"
PD="(s)=>document.getElementById('fakePip').contentDocument.querySelector(s)"
def clk(pg,sel): pg.evaluate("s=>document.getElementById('fakePip').contentDocument.querySelector(s).click()",sel); pg.wait_for_timeout(150)
def typ(pg,v): pg.evaluate("v=>{ const i=document.getElementById('fakePip').contentDocument.querySelector('.ar-psamt'); i.value=v; i.dispatchEvent(new Event('input',{bubbles:true})); }",v)
def shot(pg,n):
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=n,clip={'x':f['x']-10,'y':0,'width':f['width']+20,'height':f['y']+f['height']+10})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(400)
    check('기록 전엔 수익 칸 없음',pg.evaluate(SALE) is None)
    # 1인
    pg.evaluate("()=>{ window.__k='eye'; arRecord('eye',.9,'t'); }"); pg.wait_for_timeout(300)
    k1=pg.evaluate("()=>findBoss('lucid').id+'|eye'"); x=pg.evaluate(SALE)
    check('1인: 모달 없이 PIP 칸',x and not pg.evaluate("!!document.querySelector('#revModal,#bbModal')"),x)
    check('1인: 득템 목록 아래',x and 'ar-piprec' in (x['after'] or ''),x)
    check('1인: 아이콘·이름·기록하기/기록하지 않기',x and '마력이 깃든 안대' in x['t'] and '기록하기' in x['t'] and '기록하지 않기' in x['t'] and pg.evaluate(PD,'.ar-pipsale .rvico img') is not None,x)
    ap=pg.evaluate("()=>{ const a=admPriceOf('eye'); return a?String(Math.round(a.p/1e4)/1e4):''; }")
    check('1인: 최저가 = admPriceOf 미리 채움',x and x['v']==ap,(x and x['v'],ap))
    check('1인: 판매 수수료만',x and x['rows']==1 and '분배 수수료' not in x['t'],x)
    check('득템 저장됨 (아직 수익 없음)',pg.evaluate("k=>S.characters[0].drops[k]===1&&!S.characters[0].drev?.[k]",k1))
    typ(pg,'12.5'); clk(pg,'.ar-pipsale [data-fee=s][data-v="5"]'); pg.wait_for_timeout(150)
    shot(pg,'/tmp/pr1.png')
    clk(pg,'.ar-pipsale [data-ps=ok]')
    r=pg.evaluate("k=>S.characters[0].drev?.[k]",k1); want=pg.evaluate("()=>Math.round(revNet(12.5e8,1,5,0))")
    check('1인 기록하기 = askRev 저장 형식',r=={'m':want,'a':12.5,'p':1,'i':'eye','fs':5,'fd':0},r)
    check('수수료 기억(revFeeSet)',pg.evaluate("()=>revFeeGet().s")==5)
    check('기록 후 칸 사라짐',pg.evaluate(SALE) is None)
    # 2인 + 줄 세우기
    pg.evaluate("()=>{ S.characters[0].bosses[findBoss('will').id].party=2; save(); }"); pg.evaluate(REW,'will'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.admPriceOf=ik=>ik==='belt'?{p:3.2e8,t:Date.now()}:null; }")
    pg.evaluate("()=>{ window.__k='belt'; arRecord('belt',.9,'t'); window.__k='h_pocket'; arRecord('h_pocket',.9,'t'); }"); pg.wait_for_timeout(300)
    kb,kp=pg.evaluate("()=>[findBoss('will').id+'|belt',findBoss('will').id+'|h_pocket']")
    x=pg.evaluate(SALE)
    check('2인: 판매+분배 수수료',x and x['rows']==2 and '2인 분배' in x['t'],x)
    check('2인: 대기 2개, 하나씩',x and '대기 2개' in x['t'] and pg.evaluate("window.AR.saleQ.length")==2,x)
    check('2인: 최저가 미리 채움(admPriceOf)',x and x['v']=='3.2',x and x['v'])
    check('2인: 자동 분배 s',pg.evaluate("k=>S.characters[0].dmode?.[k]",kb)=='s')
    typ(pg,'4'); clk(pg,'.ar-pipsale [data-fee=d][data-v="3"]')
    pg.evaluate("()=>{ window.AR.pip&&arPipRec(); }"); check('다시 그려도 입력값 유지',pg.evaluate(SALE)['v']=='4')
    shot(pg,'/tmp/pr2.png')
    clk(pg,'.ar-pipsale [data-ps=ok]')
    r=pg.evaluate("k=>S.characters[0].drev?.[k]",kb); want=pg.evaluate("()=>Math.round(revNet(4e8,2,5,3))")
    check('2인 기록하기 = 분배 저장',r=={'m':want,'a':4,'p':2,'i':'belt','fs':5,'fd':3},r)
    x=pg.evaluate(SALE); check('다음 아이템 표시',x and x['t'].count('대기')==0 and pg.evaluate("window.AR.saleQ[0].ik")=='h_pocket',x)
    clk(pg,'.ar-pipsale [data-ps=no]')
    check('기록하지 않기 = 득템만',pg.evaluate("k=>S.characters[0].drops[k]===1&&!S.characters[0].drev?.[k]",kp) and pg.evaluate(SALE) is None)
    pg.evaluate("()=>arDisconnect()")
    b.close()
  from PIL import Image
  A,B=Image.open('/tmp/pr1.png'),Image.open('/tmp/pr2.png'); C=Image.new('RGB',(A.width+B.width+20,max(A.height,B.height)),(0,0,0)); C.paste(A,(0,0)); C.paste(B,(A.width+20,0)); C.save(os.path.join(OUT,'pip_record.png'))
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
