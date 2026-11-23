# test_b436 (t586u): 모양 점수 상한 — 이지 대적자 영상(d01) 배너 띠 실제 프레임에서 불멸의 유산이 색 치우침만으로 .85~.87 → 하드/익스트림 후보면 오기록.
#  수정 후: 같은 프레임 오탐 0, 진짜 아이콘(불멸의 유산·색 치우침 큰 아이콘들)을 같은 프레임에 합성하면 그대로 찾음.
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
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b436'),os.path.join(site,'fx'))
FX=sorted(os.listdir(os.path.join(ROOT,'tests','fixtures','b436')))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RUN="""async (FX)=>{ const ld=u=>new Promise(r=>{ const i=new Image(); i.onload=()=>r(i); i.src=u; }); const o={old:[],neu:[],pos:[]};
  const keys=[...new Set([...dropsFor(findBoss('adversary'),'hard'),...dropsFor(findBoss('adversary'),'extreme')])].filter(k=>ITEM_ICONS[k]); o.keys=keys; o.tol=ARX.cfg.shapeTol;
  const imgOf=async (f,draw)=>{ const bg=await ld('/fx/'+f); const c=document.createElement('canvas'); c.width=bg.width; c.height=bg.height; const g=c.getContext('2d'); g.drawImage(bg,0,0); if(draw){ await draw(g); const j=await ld(c.toDataURL('image/jpeg',.7)); g.drawImage(j,0,0); } return g.getImageData(0,0,c.width,c.height); };
  const tol0=ARX.cfg.shapeTol;
  for(const f of FX){ const img=await imgOf(f); ARX.cfg.shapeTol=null; const a=await arMatchRun({img},keys,[41],{thr:ARX.cfg.bannerThr}); ARX.cfg.shapeTol=tol0; const b=await arMatchRun({img},keys,[41],{thr:ARX.cfg.bannerThr});
    o.old.push([f,(a.hits||[]).map(h=>[h.k,+h.score.toFixed(3)])]); o.neu.push([f,(b.hits||[]).map(h=>[h.k,+h.score.toFixed(3),h.shp]),(b.scores||[]).find(s=>s[0]==='legacy')]); }
  for(const K of ['legacy','bliss','belt','book','whisper','sos','g_life','se1']){ const ic=await ld(ITEM_ICONS[K]); for(const f of FX.slice(0,4)) for(const br of [.8,1,1.2]){ const x=380, y=70;
    const img=await imgOf(f,g=>{ g.filter=`brightness(${br})`; g.drawImage(ic,x,y,Math.round(ic.width*41/40),Math.round(ic.height*41/40)); g.filter='none'; });
    const r=await arMatchRun({img},[K],[41],{thr:ARX.cfg.bannerThr}); const h=(r.hits||[])[0]; ARX.cfg.shapeTol=null; const r0=await arMatchRun({img},[K],[41],{thr:ARX.cfg.bannerThr}); ARX.cfg.shapeTol=tol0; const h0=(r0.hits||[])[0];
    o.pos.push([K,f,br,h?h.k:null,h?+h.score.toFixed(3):null,h?h.shp:null,h?Math.abs(h.x-x)<6&&Math.abs(h.y-y)<6:false,h0?+h0.score.toFixed(3):null]); } }
  return o; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    o=pg.evaluate(RUN,FX); print(json.dumps({k:o[k] for k in ('keys','tol','old','neu')},ensure_ascii=False))
    check('shapeTol 기본 .2', o['tol']==0.2, o['tol'])
    check('수정 전(모양 상한 없음): 실제 d01 배너 프레임에서 불멸의 유산 오탐 재현(8장 모두 ≥.7)', all(any(h[0]=='legacy' for h in x[1]) for x in o['old']), o['old'])
    check('수정 후: 같은 8장 오탐 0', all(not x[1] for x in o['neu']), o['neu'])
    bad=[x for x in o['pos'] if x[7] is not None and not (x[3]==x[0] and x[6])]
    check('진짜 아이콘 합성(불멸의 유산·색 치우침 큰 bliss/belt/book/whisper/sos·g_life·se1 × 4장 × 밝기 3): 수정 전에 찾던 것은 수정 후에도 전부 같은 자리에서 찾음', not bad, bad[:6])
    print('수정 전에도 못 찾은 합성(문턱 미만):', [x[:3]+[x[7]] for x in o['pos'] if x[7] is None])
    lg=[x for x in o['pos'] if x[0]=='legacy']; check('불멸의 유산 진짜 아이콘 점수 ≥ .85 (모양 상한에 안 걸림)', all(x[4] and x[4]>=.85 for x in lg), lg)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
