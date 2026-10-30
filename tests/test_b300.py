# test_b300 (t504u·t522u): 현재 보스는 맵 이름이 아니라 18개 보스 원본 보상 상자(WZ) 감지로 정함. 상자 전엔 어떤 아이템도 기록 안 함.
#   난이도는 상자로 구분 불가(난이도별 몹은 같은 그림 링크) → 같은 보스의 보상 맵 이름에서 보조로 읽음.
#   데미안 마깃안 오기록 재현: 데미안 하드 보상 맵인데 상자 전(v15 #9) → 마깃안 기록 안 됨, 상자 보임(v15 #100) → 데미안으로 정하고 기록됨.
#   실제 영상 프레임 10장: 각 보스 상자 → 감지, 다른 보스 템플릿은 안 맞음.
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b300')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n+'.jpg'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
 window._T=1e7; Date.now=()=>window._T; ARX.cfg.on=true; ARX.stream=null;
 window._img=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0); return cv; };
 return 1; }"""
OWN=[('v08_0030','seren'),('v02_0030','jinhilla'),('v03_0120','dunkel'),('v05_0030','dusk'),('v10_0120','will'),('v09_0150','kaling'),('v07_0120','bellona'),('v18_0030','lucid'),('v15_0100','damien'),('v01_0036','adversary'),('v20_0012','lotus'),('v04_0130','kalos'),('v06_0162','slime')]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    n=pg.evaluate("Object.keys(AR_BOX).filter(k=>!AR_BOX[k].boss).length"); check('보상 상자 원본 템플릿 18종 (WZ)',n==18 and pg.evaluate("Object.values(AR_BOX).filter(v=>!v.boss).every(v=>v.src==='wz'&&v.id)"),n)
    # 데미안 재현: 맵 이름(데미안 하드)만으론 보스 안 정함 → 상자 보여야 데미안으로 정하고 기록
    r=pg.evaluate("""async([a,c])=>{ ARX.det={cid:'c0',boss:'',diff:'',src:''}; ARX.box=null; ARX.mapDet={boss:'damien',diff:'hard',src:'보상 맵',t:Date.now()}; const key='damien|eye', d0=()=>+(dropMap(S.characters[0],'weekly')[key]||0);
      const cv=await _img(a); ARX.boxScanT=0; await arBoxStep(cv,true); const s0=ARX.boxLast, b0=ARX.det.boss; arRecord('eye',.9,'공중'); const r0=d0(), ok0=arBoxOk();
      window._T+=1000; const cv2=await _img(c); await arBoxStep(cv2,true); const s1=ARX.boxLast, ok1=arBoxOk(), det={...ARX.det}; arRecord('eye',.9,'공중'); const r1=d0();
      return {s0,b0,r0,ok0,s1,ok1,det,r1,log:ARX.log.slice(-3)}; }""",[u('v15_0009'),u('v15_0100')])
    check('데미안: 상자 전(#9) → 보스 미정·마깃안 기록 안 함',r['r0']==0 and not r['ok0'] and not r['b0'],r)
    check('데미안: 상자 보임(#100) → 상자로 데미안 정함 + 난이도는 맵 이름(하드) + 마깃안 기록',r['ok1'] and r['det']['boss']=='damien' and r['det']['diff']=='hard' and r['det']['src']=='보상 상자' and r['r1']==1,r)
    r=pg.evaluate("""()=>{ arDetectBoss; ARX.mapDet=null; const b={boss:'kalos',diff:'normal',src:'보상 맵'}; /* 다른 보스 보상 맵 → 상자 해제 */ if(ARX.box&&ARX.box.boss!==b.boss){ } return [ARX.box&&ARX.box.boss, arBoxOk()]; }""")
    check('상자 감지 상태 유지 (데미안)',r==['damien',True],r)
    r=pg.evaluate("""()=>{ window._T+=181000; return [arBoxOk(), ARX.det.boss]; }""")
    check('상자 유지 시간(180초) 지나면 보스 해제',r==[False,''],r)
    r=pg.evaluate("""async(u)=>{ ARX.box=null; ARX.det={cid:'c0',boss:'',diff:'',src:''}; const cv=await _img(u); await arBoxStep(cv,true); return [ARX.det.boss,ARX.det.diff,ARX.det.diffSrc,ARX.box&&ARX.box.key]; }""",u('v20_0012'))
    check('스우(하드) 상자 → 스우, 맵 정보 없으면 난이도는 캐릭터 설정',r[0]=='lotus' and r[1]=='' and r[2]=='캐릭터 설정',r)
    r=pg.evaluate("""()=>{ ARX.cfg.boxGate=false; ARX.box=null; ARX.det={cid:'c0',boss:'blackmage',diff:'hard',src:'보상 맵'}; const k=arBoxOk(); ARX.cfg.boxGate=true; return k; }""")
    check('boxGate=false → 예전처럼 보상 맵만으로 기록',r is True)
    for f,bo in OWN:
      sc=pg.evaluate("""async([u,k])=>{ const cv=await _img(u); const o={}; for(const x of Object.keys(AR_BOX)) o[x]=+(await arBoxScore(cv,x)).toFixed(3); return o; }""",[u(f),bo])
      thr=pg.evaluate("k=>AR_BOX[k].thr",bo); oth=[k for k,v in sc.items() if k!=bo and v>=pg.evaluate("k=>AR_BOX[k].thr",k)]
      if bo=='lotus': bo='lotus_v'; thr=pg.evaluate("k=>AR_BOX[k].thr",bo); oth=[k for k in oth if k!='lotus_v']
      check(f'{f} {bo} 상자 감지 ({sc[bo]} ≥ {thr})',sc[bo]>=thr,sc)
      check(f'{f} 다른 보스 상자로 오인 안 함',not oth,oth)
    r=pg.evaluate("""async(u)=>{ ARX.det={cid:'c0',boss:'',diff:'',src:''}; ARX.box=null; let n=0; const o=window.arItemStep; window.arItemStep=async()=>{n++; return [];}; window.arOcr=async()=>''; ARX.lastOcr=Date.now(); ARX.detT=Date.now(); const cv=await _img(u); await arFrame2(cv,false); window.arItemStep=o; return n; }""",u('v15_0009'))
    check('상자 전엔 아이템 찾기(arItemStep) 안 함',r==0,r)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
