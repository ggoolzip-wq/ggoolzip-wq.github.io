# test_b310 (t554/t555): 메소 단일 판독 즉시 확정(신뢰도만, 급증 상한 없음) · 의심 판독은 재확인 · 서버 저장 1분 스로틀(값 바뀔 때만)
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RUN="""async()=>{ const A=window.AR, all={}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; S.meso={};
  let t=1e12; const on=Date.now; Date.now=()=>t; A.det.cid='c0'; A.nameOf=()=>'c0'; let R={v:0,hi:true}; let saves=0; const sm=window.saveMeso; window.saveMeso=(...a)=>{ const r=sm(...a); if(r) saves++; return r; };
  window.arMesoPanel=(s,k)=>k==='inv'; window.arMesoRead=async()=>({t:'',v:R.v,hi:R.hi}); window.arOcr=async()=>'Lv.285 트딕이';
  const cv=document.createElement('canvas'); cv.width=1366; cv.height=768; const inv=()=>{ const o=S.meso[mesoKey(S.characters[0])]; return o?o.inv:null; }, o={};
  R={v:20328294388,hi:true}; o.r1=await arMesoNow(cv); o.s1=inv(); o.n1=saves;
  t+=1000; R={v:20328294388+5e9+123,hi:true}; o.r2=await arMesoNow(cv); o.s2=inv(); o.n2=saves; /* 50억+ 급증: 바로 확정되지만 1분 안이라 보류 */
  o.pend=A.mesoPend&&A.mesoPend.inv;
  for(let i=0;i<30;i++){ t+=1000; R={v:20828294511+i*1000,hi:true}; await arMesoNow(cv); } o.n3=saves;
  t+=31000; arMesoTick(cv,t); o.n4=saves; o.s4=inv();
  t+=1000; R={v:20328294300,hi:false}; o.r5=await arMesoNow(cv); t+=1000; R={v:20328294300,hi:false}; o.r6=await arMesoNow(cv); o.conf6=A.mesoPend&&A.mesoPend.inv;
  t+=1000; R={v:11111111111,hi:false}; o.r7=await arMesoNow(cv); t+=1000; R={v:22222222222,hi:false}; o.r8=await arMesoNow(cv); o.p8=A.mesoPend&&A.mesoPend.inv;
  t+=61000; arMesoFlush(t); o.n9=saves; o.s9=inv(); t+=61000; arMesoFlush(t); R={v:o.s9,hi:true}; await arMesoNow(cv); t+=61000; arMesoFlush(t); o.n10=saves;
  Date.now=on; window.saveMeso=sm; return JSON.parse(JSON.stringify(o)); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    o=pg.evaluate(RUN); print(json.dumps(o,ensure_ascii=False))
    check('신뢰도 높은 판독 1번 → 즉시 확정·저장', o['s1']==20328294388 and o['n1']==1, o)
    check('50억+ 급증도 신뢰도 높으면 확정 (급증 상한 없음), 1분 안이라 보류', o['r2'].get('why') is None and o['pend']==25328294511 and o['n2']==1, o)
    check('사냥 중 1초마다 값이 바뀌어도 1분 안에는 서버 저장 0번', o['n3']==1, o)
    check('1분 지나면 최신 값 1번 저장', o['n4']==2 and o['s4']==20828294511+29000, o)
    check('의심 판독 1번 → 보류, 다음 판독이 같으면 확정', o['r5'].get('why')=='suspect' and o['r6'].get('why2')=='recheck' and o['conf6']==20328294300, o)
    check('의심 판독이 서로 다르면 확정 안 함', o['r7'].get('why')=='suspect' and o['r8'].get('why')=='suspect' and o['p8']==20328294300, o)
    check('값 그대로면 서버 저장 안 함', o['n10']==o['n9']==3, o)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
