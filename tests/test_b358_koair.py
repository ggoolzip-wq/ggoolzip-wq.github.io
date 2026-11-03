# test_b358 (t659): 미트라의 분노 상자가 공중에서 돌 때 인식 못 함 — 결정·큐브 외 아이템 공중 검사를
#   대략 찾기 20도·크기 1개 + 정밀 단계 ±10도 보정(aref) + 후보 24개로 바꿈 (프레임별 4/26 → 11/26, 293 → 131ms)
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b358')
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
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
 ARX.cfg.worker=false; ARX.wk=null; window._rec=[]; window.arRecord=function(k,s,via){ window._rec.push([k,via]); };
 window._opts=[]; const MR=window.arMatchRun; window.arMatchRun=function(G,keys,pxs,opt){ window._opts.push({keys,pxs,angles:(opt.angles||[]).length,aref:opt.aref||0,vmax:opt.vmax||0}); return MR.apply(this,arguments); };
 window._frame=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d',{willReadFrequently:true}); g.fillStyle='#000'; g.fillRect(0,0,1920,1080); g.drawImage(im,0,0); return cv; };
 window._scan=async(u,boss,diff)=>{ ARX.det={boss,diff,cid:'c0'}; const cv=await _frame(u), r=ARX.cfg.airBand, y=Math.round(r.y*1080), h=Math.round(r.h*1080);
   const hs=await arAirScan({img:cv.getContext('2d').getImageData(0,y,1920,h)},1080,0,y,ARX.cfg.airThr); return hs.filter(h=>h.ok).map(h=>[h.k,+h.score.toFixed(3),Math.round(h.x+h.w/2),Math.round(h.y+h.h/2)]); };
 return 1; }"""
OLD="()=>Object.assign(ARX.cfg,{airKoStep:10,airKoRef:0,airKoScales:[],airKoVmax:8})"
GT={'m0980':(577,411),'m0983':(563,421),'m1010':(462,491)}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    c=pg.evaluate("({s:ARX.cfg.airKoStep,r:ARX.cfg.airKoRef,sc:ARX.cfg.airKoScales,v:ARX.cfg.airKoVmax,e:arAirK('airKeyThr','eye',ARX.cfg.airThr),a:arAirAngles().length,a20:arAirAngles(20).length})")
    check('기본값 airKoStep 20 / airKoRef 10 / airKoScales [1] / airKoVmax 24',c['s']==20 and c['r']==10 and c['sc']==[1] and c['v']==24,c)
    check('arAirAngles(step): 기본 36개, 20도 18개',c['a']==36 and c['a20']==18,c)
    check('eye 공중 기준 .8 유지 (b353)',c['e']==.8,c)
    H={}
    for n in ['m0980','m0983','m1010','m1100']:
      H[n]=pg.evaluate("([u])=>_scan(u,'seren','hard')",[u(n)]); print(n,H[n])
    o=pg.evaluate("window._opts"); ko=[x for x in o if 'mitra' in x['keys']]
    check('결정·큐브 외 키 검사: 크기 1개·18각도·aref 10·후보 24',ko and all(len(x['pxs'])==1 and x['angles']==18 and x['aref']==10 and x['vmax']==24 for x in ko),ko[:2])
    def near(h,g): return any(x[0]=='mitra' and abs(x[2]-g[0])<60 and abs(x[3]-g[1])<60 for x in h)
    for n in ['m0980','m0983','m1010']: check(f'공중 회전 중 미트라 상자 인식 {n}',near(H[n],GT[n]),H[n])
    bad=[(n,x) for n in H for x in H[n] if not (n in GT and x[0]=='mitra' and abs(x[2]-GT[n][0])<60 and abs(x[3]-GT[n][1])<60)]
    check('오검출 0 (다른 위치·다른 키 없음, 착지 뒤 m1100 공중 0)',not bad,bad)
    pg.evaluate(OLD)
    h=[pg.evaluate("([u])=>_scan(u,'seren','hard')",[u(n)]) for n in ['m0983','m1010']]
    check('예전 설정(10도×2크기, 후보 8)은 두 프레임 놓침 (b358 원인)',not near(h[0],GT['m0983']) and not near(h[1],GT['m1010']),h)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
