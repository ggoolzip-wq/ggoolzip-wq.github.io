# test_b329_maptpl (t627): 맵 이름 이미지 템플릿 (닉네임 음절 방식처럼)
#  - 템플릿 없는 보상 맵: 처음엔 OCR(느림) → 이름 인정 + 같은 보스 상자 확정이 2번(깨끗한 같은 그림) 모이면 localStorage 'arMapTpl' 저장
#  - 다음 등장부터 템플릿으로 즉시 확정(OCR 없음), 새로고침 후에도 유지 / 다른 맵·다른 보스 상자·한 번만 확인은 저장·매칭 안 함
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']:
    if os.path.isdir(os.path.join(ROOT,d)): shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
LOAD="""async ([a,b])=>{ const L=async s=>{ const im=new Image(); im.src=s; await im.decode(); return im; }; window.__S=await L(a); window.__D=await L(b); AR_MAPTPL.length=0; ARX.mtT=null; ARX.mtPend={}; return true; }"""
LEARN="""([im,txt,boss,now])=>{ const I=arMapTplImg(window[im]); const B=arMapTplBands(I); ARX.rwl=boss?{boss}:null; ARX.lock=null; const r=arMapTplLearn(I,B,txt,now); ARX.rwl=null; return r; }"""
M="""im=>{ const r=arMapTplMatch(window[im]); return r&&[r.text,r.boss,r.sc,r.ms]; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.removeItem('arMapTpl')"); pg.reload(); pg.wait_for_timeout(800)
    bi=pg.evaluate("""async ([a,b,c])=>{ const L=async s=>{ const im=new Image(); im.src=s; await im.decode(); return im; }; const o=[]; for(const s of [a,b,c]){ const r=arMapTplMatch(await L(s)); o.push(r&&r.text); } return o; }""",[u('b329/v2_seren.jpg'),u('b328/v5_dunkel.jpg'),u('b328/v3_jinhilla.jpg')])
    check('기본 템플릿(영상에서 학습): 세렌·듄켈·진힐라 정확',bi==['왕궁 메인홀 <하드>','끝에 가까운 곳 <하드>','욕망의 제단 <하드>'],bi)
    pg.evaluate(LOAD,[u('b329/v2_seren.jpg'),u('b328/v5_dunkel.jpg')])
    check('템플릿 없음 → 매칭 없음(OCR 경로)',pg.evaluate(M,'__S') is None)
    O="""async im=>{ const s=window[im]; const t0=performance.now(); const t=await arOcr(arMapCrop(s,s.width,s.height,arR('map',s)),150,1); return [t,performance.now()-t0]; }"""
    ocr=pg.evaluate(O,'__S'); txt=ocr[0]; print('OCR',ocr)
    check('상자 확정 없으면 저장 안 함',pg.evaluate(LEARN,['__S',txt,'',1000]) is False and pg.evaluate(LEARN,['__S',txt,'',3000]) is False)
    check('다른 보스 상자면 저장 안 함',pg.evaluate(LEARN,['__S',txt,'dunkel',4000]) is False and pg.evaluate(LEARN,['__S',txt,'dunkel',6000]) is False)
    check('비보상/엉뚱한 글자면 저장 안 함',pg.evaluate(LEARN,['__S','아무 글자 없음','seren',7000]) is False)
    pg.evaluate("ARX.mtPend={}")
    a=pg.evaluate(LEARN,['__S',txt,'seren',10000]); a2=pg.evaluate(LEARN,['__S',txt,'seren',10200])
    check('1번째 확인(및 0.5초 안 반복)만으론 저장 안 함',a is False and a2 is False,[a,a2])
    check('같은 깨끗한 그림 2번째 확인 → 저장',pg.evaluate(LEARN,['__S',txt,'seren',11000]) is True)
    st=pg.evaluate("JSON.parse(localStorage.getItem('arMapTpl')||'[]').map(x=>[x.text,x.boss,x.w,x.h])"); check('저장 이름 = 표의 정식 이름(오독 글자 아님)',st and st[0][0]=='왕궁 메인홀 <하드>' and st[0][1]=='seren',st)
    r=pg.evaluate(M,'__S'); check(f'다음 등장 → 템플릿 즉시 확정 (OCR {ocr[1]:.0f}ms → 템플릿 {r and r[3]:.1f}ms)',r and r[0]=='왕궁 메인홀 <하드>' and r[3]<ocr[1] and r[3]<60,r)
    d=pg.evaluate("t=>{const d=arDetectBMap(t); return d&&[d.boss,d.diff,d.kind.includes('r')]}",r[0]); check('정식 이름 → 세렌 하드 보상 맵',d==['seren','hard',True],d)
    check('다른 맵(듄켈) 화면은 세렌 템플릿과 안 맞음',pg.evaluate(M,'__D') is None,pg.evaluate("ARX.mtSc"))
    # 실제 arMapWatch 경로: 템플릿이면 OCR 없이 동기로 맵 상태까지
    w=pg.evaluate("""()=>{ ARX.mapSt=null; ARX.mapPend=null; ARX.mapOk=false; ARX.mChgT=Date.now(); ARX.mOcrT=0; ARX.mapBusy=false; ARX.mprev=null; ARX.mapText=''; const t0=performance.now(); arMapWatch(window.__S); return [ARX.mapSrc,ARX.mapText,ARX.mapBusy,performance.now()-t0]; }""")
    check('arMapWatch: 템플릿으로 즉시(OCR 안 부름)',w[0]=='템플릿' and w[1]=='왕궁 메인홀 <하드>' and w[2] is False,w)
    pg.reload(); pg.wait_for_timeout(800); pg.evaluate(LOAD,[u('b329/v2_seren.jpg'),u('b328/v5_dunkel.jpg')])
    r=pg.evaluate(M,'__S'); check('새로고침 후에도 저장 템플릿으로 즉시',r and r[0]=='왕궁 메인홀 <하드>',r)
    # 두 번째 맵(듄켈) 도 같은 방식 → 서로 헷갈리지 않음
    t2=pg.evaluate(O,'__D')[0]; pg.evaluate(LEARN,['__D',t2,'dunkel',1000]); ok=pg.evaluate(LEARN,['__D',t2,'dunkel',2000])
    check('두 번째 새 맵(듄켈)도 2번 확인 후 저장',ok is True,t2)
    check('듄켈 → 듄켈, 세렌 → 세렌',(pg.evaluate(M,'__D') or [''])[0]=='끝에 가까운 곳 <하드>' and (pg.evaluate(M,'__S') or [''])[0]=='왕궁 메인홀 <하드>',[pg.evaluate(M,'__D'),pg.evaluate(M,'__S')])
    check('cfg.mapTpl=false 면 끔',pg.evaluate("()=>{ ARX.cfg.mapTpl=false; const r=arMapTplMatch(window.__S); ARX.cfg.mapTpl=undefined; return r; }") is None)
    rm=pg.evaluate("""()=>{ const n=Date.now(), o=ARX.mapSt; const r=[]; for(const [k,d] of [['b',20000],['b',70000],['r',5000],['r',9000],['w',1000]]){ ARX.mapSt={boss:'lucid',kind:k,t:n-d}; r.push(!!arRewMap(n)); } ARX.mapSt=o; return r; }""")
    check('t630: 전투 맵(60초)에서도 그 보스 상자 찾음, 보상 맵 8초, 대기 맵 안 함',rm==[True,False,True,False,False],rm)
    pg.evaluate("localStorage.removeItem('arMapTpl')")
    b.close()
finally:
    srv.kill(); shutil.rmtree(site,ignore_errors=True)
check('페이지 오류 없음',not errs,errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
