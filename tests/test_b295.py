# test_b295: 해상도·창 모드 — UI '최적 비율' 정수 배율(1080p 이하 1배, 1440p·2732x1536·4K 2배), 게임 화면(창 제목줄·검은 테두리) 찾기,
#            UI 영역(이름·맵·로그·배너)을 화면 모서리 + UI px × 배율로, 바닥 아이콘은 게임 높이 비율, 배너 아이콘 46px × 배율.
#            합성 화면: 실제 v07 1080p 프레임 → 월드는 해상도에 맞게 늘이고, UI 조각(이름·미니맵 제목)은 원래 px × 배율로 모서리에 붙임.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b295'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""async()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name)=>({id,name,level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','트딕이'),C('c1','팬더데이')]; S.activeId='c1'; save&&save(); render();
  const im=new Image(); im.src='fx/v07_1080.jpg'; await im.decode(); window._im=im; await arOcrLoad(); }"""
# mode: full = 스트림 = 게임 / win = 창 캡처(제목줄 31 + 테두리 8) / box = 더 큰 화면 가운데 검은 테두리
CASE="""async ([W,H,s,mode,CW,CH])=>{ const A=window.AR, im=window._im; let ox=0,oy=0,sw=W,sh=H;
  if(mode==='win'){ sw=W+16; sh=H+39; ox=8; oy=31; } if(mode==='box'){ sw=CW; sh=CH; ox=Math.round((CW-W)/2); oy=Math.round((CH-H)/2); }
  const cv=document.createElement('canvas'); cv.width=sw; cv.height=sh; const g=cv.getContext('2d'); g.fillStyle='#000'; g.fillRect(0,0,sw,sh);
  if(mode==='win'){ g.fillStyle='#3a3a3a'; g.fillRect(0,0,sw,sh); g.fillStyle='#ddd'; g.font='14px sans-serif'; g.fillText('MapleStory',30,20); }
  g.drawImage(im,ox,oy,W,H); g.imageSmoothingEnabled=false;
  const P=[[0,1034,384,28,'bl'],[0,0,384,86,'tl'],[1306,594,614,356,'br']]; let nameBox=null;
  for(const [x,y,w,h,a] of P){ const dx=a==='br'?ox+W-w*s:ox, dy=a==='tl'?oy:oy+H-(1080-y)*s; g.drawImage(im,x,y,w,h,dx,dy,w*s,h*s); if(a==='bl') nameBox=[dx,dy,w*s,h*s]; }
  A.bbox=arBBox(cv); A.bbKey='t'+sw+'x'+sh+mode; A.geo=null; const G=arGeom(sw,sh);
  const px=(r)=>[r.x*sw,r.y*sh,r.w*sw,r.h*sh].map(Math.round); const n=px(arR('name',cv));
  const iou=(a,b)=>{ const x0=Math.max(a[0],b[0]),y0=Math.max(a[1],b[1]),x1=Math.min(a[0]+a[2],b[0]+b[2]),y1=Math.min(a[1]+a[3],b[1]+b[3]); const i=Math.max(0,x1-x0)*Math.max(0,y1-y0); return i/(a[2]*a[3]+b[2]*b[3]-i); };
  let nt='',cid='',mt='',boss=null; for(const k of [3,4,2]){ nt=await arOcr(arCrop(cv,sw,sh,arR('name',cv),arSc(sh,k,cv))); cid=arDetectChar(nt); if(cid) break; }
  mt=await arOcr(arCrop(cv,sw,sh,arR('map',cv),arSc(sh,3,cv))); boss=arDetectBoss(mt);
  const out={sw,sh,G:{x:G.gx,y:G.gy,w:G.gw,h:G.gh,s:G.s},iou:+iou(n,nameBox).toFixed(2),nt,cid,mt,boss:boss&&boss.boss,ban:arIconPx(sh,'banner',cv),gp:arGroundPx(arGH(cv,sh))[1],log:px(arR('log',cv))};
  if(window._shot){ const c2=document.createElement('canvas'); c2.width=960; c2.height=Math.round(960*sh/sw); const q=c2.getContext('2d'); q.drawImage(cv,0,0,c2.width,c2.height); q.lineWidth=2;
    for(const [k,col] of [['log','#ff6bd0'],['banner','#ffe066'],['map','#5ec8ff'],['name','#7dff9a'],['item','#ffb347']]){ const r=arR(k,cv); q.strokeStyle=col; q.strokeRect(r.x*c2.width,r.y*c2.height,r.w*c2.width,r.h*c2.height); } out.img=c2.toDataURL('image/png'); }
  return out; }"""
CASES=[(1366,768,1,'full'),(1280,720,1,'full'),(1600,900,1,'full'),(1920,1080,1,'full'),(1920,1080,1,'win'),(1280,720,1,'win'),(1366,768,1,'box',1920,1080),(1600,900,1,'box',1920,1080),
       (2560,1440,2,'full'),(2560,1440,2,'win'),(2732,1536,2,'full'),(3840,2160,2,'full'),(2560,1440,2,'box',3440,1440)]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    d=pg.evaluate("()=>['name','map','log','banner'].map(k=>{ const a=arR(k,{width:1920,height:1080}), b=AR_DEF[k]; return Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y),Math.abs(a.w-b.w),Math.abs(a.h-b.h)); })")
    check('1920x1080 = 예전 화면 비율 영역 그대로 (회귀 없음)', max(d)<.002, d)
    check('배율 규칙: 1080p 이하 1, 1440p·1536·2160 2, 사용자 지정 우선', pg.evaluate("[arUiScale(1366,768),arUiScale(1920,1080),arUiScale(1920,1200),arUiScale(2560,1440),arUiScale(2732,1536),arUiScale(3840,2160)].join()")=='1,1,1,2,2,2' and pg.evaluate("(()=>{ window.AR.cfg.uiScale=3; const r=arUiScale(1920,1080); window.AR.cfg.uiScale=0; return r; })()")==3)
    for c in CASES:
        W,H,s,mode=c[:4]; CW,CH=(c[4],c[5]) if len(c)>4 else (0,0)
        pg.evaluate("v=>{window._shot=v}", (W,H,mode) in [(2560,1440,'win'),(1366,768,'box'),(1280,720,'full')])
        r=pg.evaluate(CASE,[W,H,s,mode,CW,CH]); tag=f'{W}x{H} {mode}'
        if r.get('img'):
            import base64; open(os.path.join(OUT,f'b295_{W}x{H}_{mode}.png'),'wb').write(base64.b64decode(r.pop('img').split(',')[1]))
        print('CASE',tag,r)
        ex={'full':(0,0),'win':(8,31),'box':((CW-W)//2,(CH-H)//2)}[mode]
        check(f'{tag}: 게임 화면 {W}x{H} @({ex[0]},{ex[1]}) · UI {s}배', (r['G']['w'],r['G']['h'],r['G']['s'])==(W,H,s) and abs(r['G']['x']-ex[0])<=2 and abs(r['G']['y']-ex[1])<=2, r['G'])
        check(f'{tag}: 이름 영역 = 상태바 이름 자리 (모서리 + UI px×배율)', r['iou']>=.85, r['iou'])
        check(f'{tag}: 이름 OCR → 트딕이', r['cid']=='c0', r['nt'])
        check(f'{tag}: 맵 OCR → 보스 인식', bool(r['boss']), r['mt'])
        check(f'{tag}: 배너 아이콘 46×배율 · 바닥 아이콘 71×게임높이/1080', r['ban']==46*s and abs(r['gp']-round(71*H/1080))<=1, (r['ban'],r['gp']))
        check(f'{tag}: 로그 영역 오른쪽 아래 붙음', abs(r['log'][0]+r['log'][2]-(ex[0]+W))<=2 and abs(r['log'][1]-(ex[1]+H-486*s))<=2, r['log'])
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
