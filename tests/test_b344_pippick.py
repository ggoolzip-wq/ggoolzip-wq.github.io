# test_b344 (t648): PIP 수익 기록 칸에서 반지 상자·칠흑 장신구 상자 고르기 (페이지 창과 같은 선택지·같은 저장 함수). PIP 닫히면 원래 창. MBT_SHOTDIR 에 pip_ring.png / pip_pitched.png
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
SALE="()=>{ const d=document.getElementById('fakePip').contentDocument; const e=d.querySelector('.ar-pipsale'); return e?{t:e.innerText,v:e.querySelector('.ar-psamt')?.value,rows:e.querySelectorAll('.rvfrow').length,after:e.previousElementSibling&&e.previousElementSibling.className}:null; }"
PD="(s)=>document.getElementById('fakePip').contentDocument.querySelector(s)"
def clk(pg,sel): pg.evaluate("s=>document.getElementById('fakePip').contentDocument.querySelector(s).click()",sel); pg.wait_for_timeout(150)
def typ(pg,v): pg.evaluate("v=>{ const i=document.getElementById('fakePip').contentDocument.querySelector('.ar-psamt'); i.value=v; i.dispatchEvent(new Event('input',{bubbles:true})); }",v)
def shot(pg,n):
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=n,clip={'x':f['x']-10,'y':0,'width':f['width']+20,'height':f['y']+f['height']+10})
def shot2(pg,a,b,out):
    from PIL import Image
    A,B=Image.open(a),Image.open(b); C=Image.new('RGB',(A.width+B.width+20,max(A.height,B.height)),(0,0,0)); C.paste(A,(0,0)); C.paste(B,(A.width+20,0)); C.save(out)
OPTS="()=>[...document.getElementById('fakePip').contentDocument.querySelectorAll('.ar-pipsale [data-pk]')].map(b=>[b.dataset.pk,b.innerText.trim(),!!b.querySelector('img')])"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.admPriceOf=ik=>ik==='ring:r4'?{p:25e8,t:Date.now()}:ik==='cb:eye'?{p:7.5e8,t:Date.now()}:null; }")
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(400)
    MOD="()=>!!document.querySelector('#ringModal.show,#chaosModal,#revModal,#bbModal')"
    # 1인 반지 상자
    pg.evaluate("()=>{ window.__k='r_white'; arRecord('r_white',.9,'t'); }"); pg.wait_for_timeout(300)
    kr=pg.evaluate("()=>findBoss('lucid').id+'|r_white'")
    o=pg.evaluate(OPTS); check('반지: 페이지 창 없이 PIP 고르기',not pg.evaluate(MOD) and [x[0] for x in o]==['r4','c4','x'],o)
    check('반지: 고르기 전엔 저장 안 함',pg.evaluate("k=>!S.characters[0].drops[k]",kr))
    pg.wait_for_timeout(100); shot(pg,'/tmp/r1.png')
    clk(pg,'.ar-pipsale [data-pk=r4]'); x=pg.evaluate(SALE)
    check('반지: 결과 저장 = chooseRing (outMap r4)',pg.evaluate("k=>S.characters[0].drops[k]===1&&JSON.stringify(S.characters[0].dropOut[k])",kr)=='["r4"]')
    check('반지: 가격 칸 (이름·미리 채움·판매 수수료만)',x and '리스트레인트 링 4레벨' in x['t'] and x['v']=='25' and x['rows']==1,x)
    clk(pg,'.ar-pipsale [data-fee=s][data-v="3"]'); shot(pg,'/tmp/r2.png'); clk(pg,'.ar-pipsale [data-ps=ok]')
    r=pg.evaluate("k=>S.characters[0].drev?.[k]",kr); want=pg.evaluate("()=>Math.round(revNet(25e8,1,3,0))")
    check('반지 기록하기 = askRev 형식',r=={'m':want,'a':25,'p':1,'i':'ring:r4','fs':3,'fd':0},r)
    shot2(pg,'/tmp/r1.png','/tmp/r2.png',os.path.join(OUT,'pip_ring.png'))
    # 2인 칠흑 상자
    pg.evaluate("()=>{ S.characters[0].bosses[findBoss('will').id].party=2; save(); }"); pg.evaluate(REW,'will'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.__k='chaosbox'; arRecord('chaosbox',.9,'t'); }"); pg.wait_for_timeout(300)
    kc=pg.evaluate("()=>findBoss('will').id+'|chaosbox'"); o=pg.evaluate(OPTS)
    check('칠흑: CHAOS_PICK 아이콘 목록',not pg.evaluate(MOD) and [x[0] for x in o]==pg.evaluate("CHAOS_PICK") and all(x[2] for x in o),o)
    shot(pg,'/tmp/c1.png'); clk(pg,'.ar-pipsale [data-pk=eye]'); x=pg.evaluate(SALE)
    check('칠흑: 결과 저장 = chaosApply + 자동 분배',pg.evaluate("k=>{ const c=S.characters[0]; return c.drops[k]===1&&JSON.stringify(c.dropOut[k])==='[\"cb:eye\"]'&&c.dmode[k]==='s'; }",kc))
    check('칠흑: 2인 판매+분배, 미리 채움',x and x['rows']==2 and x['v']=='7.5' and '마력이 깃든 안대' in x['t'],x)
    clk(pg,'.ar-pipsale [data-fee=d][data-v="5"]'); shot(pg,'/tmp/c2.png'); clk(pg,'.ar-pipsale [data-ps=ok]')
    r=pg.evaluate("k=>S.characters[0].drev?.[k]",kc); want=pg.evaluate("()=>{ const f=revFeeGet(); return [Math.round(revNet(7.5e8,2,f.s,5)),f.s]; }")
    check('칠흑 기록하기 = 분배 저장',r=={'m':want[0],'a':7.5,'p':2,'i':'cb:eye','fs':want[1],'fd':5},r)
    shot2(pg,'/tmp/c1.png','/tmp/c2.png',os.path.join(OUT,'pip_pitched.png'))
    # 생명 반지 꽝 + 고르기 전 기록하지 않기 + 줄 세우기
    pg.evaluate("()=>{ window.__k='r_life'; arRecord('r_life',.9,'t'); window.__k='r_red'; arRecord('r_red',.9,'t'); }"); pg.wait_for_timeout(300)
    kl,kd=pg.evaluate("()=>[findBoss('will').id+'|r_life',findBoss('will').id+'|r_red']"); o=pg.evaluate(OPTS); x=pg.evaluate(SALE)
    check('생명 반지: 연마석 포함 4개, 대기 2개',[y[0] for y in o]==['r4','c4','gl','x'] and '셋 다 못 먹었어요' in o[3][1] and '대기 2개' in x['t'],(o,x and x['t']))
    clk(pg,'.ar-pipsale [data-pk=x]')
    check('꽝 = 수익 없이 기록 (mode n)',pg.evaluate("k=>{ const c=S.characters[0]; return c.drops[k]===1&&c.dmode[k]==='n'&&!c.drev?.[k]; }",kl))
    clk(pg,'.ar-pipsale [data-ps=skip]')
    check('고르기 전 기록하지 않기 = 아무것도 안 남김',pg.evaluate("k=>!S.characters[0].drops[k]&&!S.characters[0].dropOut?.[k]",kd) and pg.evaluate(SALE) is None)
    # PIP 닫힘 → 원래 창
    pg.evaluate("()=>{ document.getElementById('fakePip').contentWindow.close(); }"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ window.AR.recent={}; window.__k='r_white'; arRecord('r_white',.9,'t'); }"); pg.wait_for_timeout(300)
    check('PIP 닫히면 원래 반지 창',pg.evaluate("!!document.querySelector('#ringModal.show')"))
    pg.evaluate("()=>arDisconnect()")
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
