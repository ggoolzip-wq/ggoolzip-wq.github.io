# test_b388 (t459): 에픽빔 오기록 재현용 진단 메타(dg) — 감지 판단·저장 구간은 그대로, 저장 메타에 점수 흐름·분석 화면 출처·보상 맵 상태·원본 프레임 간격만 추가, 서버 메타 8KB 한도 안.
import os, sys, tempfile, shutil, subprocess, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:600] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copy(os.path.join(ROOT,'tests','fixtures','b352','beam720.webm'),site)
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
PLAY="""async(src)=>{ const v=document.createElement('video'); v.muted=true; v.src=src; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;width:320px'; document.body.appendChild(v); await v.play(); ARX.testSrc=v; window._v=v; return true; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1400,'height':900},locale='ko-KR',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate("ARX.video=null")
    cfg0=pg.evaluate("JSON.stringify(EC.cfg)")
    check('감지 설정: 기존 문턱·빈도·게이트 + b391 모션 설정',json.loads(cfg0)=={"fps":30,"H0":240,"H":720,"q":.5,"maxBytes":800000,"th":.66,"strong":.8,"minMean":12,"hits":2,"mo":True,"moWin":1200,"moEarly":5,"moPkLo":4,"moPkHi":8,"moLate":9,"moRLo":.4,"moRHi":2.5,"moDecay":.75,"moDup":.5,"moMinDt":150,"pre":1000,"post":3000,"linkBefore":30000,"linkAfter":90000,"cool":12000,"gate":True,"rewardOnly":True,"pil":False,"shift":True,"sx":10,"sy":4,"sTh":.77,"sN":2,"pendMs":2000,"pilTh":.88,"pilWid":5,"per":12},cfg0)
    pg.evaluate("()=>{ ARX.det={cid:'',boss:'lucid',diff:'hard',src:''}; ARX.mapSt={boss:'lucid',kind:'r',diff:'hard',t:Date.now()}; setInterval(()=>{ if(ARX.mapSt) ARX.mapSt.t=Date.now(); },1000); }")
    pg.evaluate(PLAY,'beam720.webm'); t0=time.time()
    while time.time()-t0<35 and not pg.evaluate("EC.saved"): pg.wait_for_timeout(200)
    L=pg.evaluate("ecList().then(L=>L.map(m=>({...m,poster:!!m.poster})))")
    check('클립 1개 저장',len(L)==1,L)
    m=L[0]; dg=m.get('dg') or {}; print('dg',json.dumps(dg)[:1800])
    check('첫 감지 프레임 = 에픽빔 시작(6.0초) 직후(기존과 같음)',6.0<=m['vt0']<=6.6,m['vt0'])
    check('dg 기본 필드',dg.get('kind')=='motion' and isinstance(dg.get('mo'),dict) and len(dg['mo'].get('k',[]))==3 and dg.get('v')==1 and dg.get('build')==pg.evaluate('document.documentElement.dataset.build')=='b391' and dg.get('src') in ('bm','video') and isinstance(dg.get('lg'),list) and len(dg['lg'])>=5,dg)
    check('감지/저장 시각 순서: hitT≤0≤det≤commit',dg.get('hitT') is not None and dg['hitT']<=0<=dg['det']<=dg['commit']<=2100,(dg.get('hitT'),dg.get('det'),dg.get('commit')))
    check('점수 흐름에 문턱 통과 점수 포함',any(x[1]>=.66 or x[2]>=.77 for x in dg['lg']),dg['lg'][-8:])
    check('보상 맵 상태 기록',dg.get('map',{}).get('k')=='r' and dg['map']['b']=='lucid' and 0<=dg['map']['age']<1500 and dg.get('boss')=='lucid',dg.get('map'))
    check('원본 프레임 수·간격',dg.get('fr',{}).get('n',0)>=96 and 0<dg['fr']['gap']<1000 and dg['fr']['first']>=-1000 and dg['fr']['last']<3000,dg.get('fr'))
    out=pg.evaluate("id=>ecList().then(L=>JSON.stringify(ecMetaOut(L.find(x=>x.id===id))).length)",m['id'])
    check('dg ≤1600자, 서버 메타 8192 한도 안',len(json.dumps(dg,separators=(',',':')))<=1600 and out<8192,(len(json.dumps(dg,separators=(',',':'))),out))
    big=pg.evaluate("()=>{ const o=ecDiagOut({lg:Array.from({length:400},(_,i)=>[i,0.123,0.456,78.9])},{n:120,gap:33,first:-1000,last:2966}); return [JSON.stringify(o).length,o.fr.n]; }")
    check('진단 과대 시 잘라 1600자 이하 유지',big[0]<=1600 and big[1]==120,big)
    check('JS 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
