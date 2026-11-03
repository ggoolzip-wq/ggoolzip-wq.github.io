# b354: 에픽빔 클립 서버 저장(사이트 쪽) — wrangler dev(로컬 R2·D1) + 넥슨 모의 서버 + 브라우저 두 개(PC A·PC B)
# PC A: 넥슨 키 로그인 → 클립 자동 업로드(☁) · 오프라인이면 대기(⏳) → 다시 연결(online)되면 올림 · ECB1 묶음 왕복
# PC B: 같은 넥슨 계정의 다른 키로 로그인 → 서버 클립 목록(12개씩) → 미리보기·영상 받아 재생, IndexedDB 캐시
# R2 꺼짐(503 r2_off) → '이 PC 에만 저장' 표시, 클립은 그대로(지우지 않음)
# 스크린샷: MBT_SHOTDIR(기본 tests/out) 에 epic_cloud_A.png, epic_cloud_B.png, epic_cloud_modal.png, epic_cloud_off.png
import os, sys, tempfile, shutil, subprocess, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil, cf_dev, mock_nexon_list as MN
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('RESULT OK 0'); sys.exit(0)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
NP, WP = _tutil.free_port(), _tutil.free_port()
K=lambda x:f'live_KEY_{x}_0123456789abcdef'
MN.start(NP); MN.KEYS[K('EA')]=['acc-b354c-A']; MN.KEYS[K('EA2')]=['acc-b354c-A']
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b354c-%d.toml'%os.getpid())
open(cfg,'w').write(open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read().replace('\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n','\n').replace('[vars]','[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n\n[vars]',1))
API=f'http://127.0.0.1:{WP}'
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]}; const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}});
  S.characters=[mk('c0','트딕이')]; S.activeId='c0'; save(); render(); }"""
MK="""async([t0,hue,item])=>{ const c=document.createElement('canvas'); c.width=426; c.height=240; const g=c.getContext('2d'); const f=[],ts=[],vt=[];
  for(let i=0;i<40;i++){ g.fillStyle=`hsl(${hue},60%,${15+i}%)`; g.fillRect(0,0,426,240); g.fillStyle='#fff'; g.font='bold 40px sans-serif'; g.fillText('EPIC '+i,120+i*2,140); g.fillRect(200,0,26+i,240);
    f.push(await new Promise(r=>c.toBlob(r,'image/jpeg',.72))); ts.push(-1000+i*100); vt.push(1+i*.1); }
  const id='ec'+t0; const m={id,t0,vt0:2,boss:'lucid',diff:'hard',item,cid:'c0',cname:'트딕이',sc:.9,w:426,h:240,n:40,start:-1000,end:2900,vts:[1,4.9],poster:f[13],pi:13,up:0,bytes:f.reduce((s,b)=>s+b.size,0)};
  await ecTx(['meta','frames'],'readwrite',t=>{ t.objectStore('meta').put(m); t.objectStore('frames').put({id,ts,vt,f}); }); return id; }"""
def newpc(b):
    ctx=b.new_context(viewport={'width':1600,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul')
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d:d.accept())
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate(f"localStorage.clear(); localStorage.setItem('mapleBossTracker.syncApi','{API}')"); pg.reload(); pg.wait_for_timeout(800)
    return ctx,pg
def until(pg,js,arg=None,t=20):
    e=time.time()+t
    while time.time()<e:
        if pg.evaluate(js,arg): return True
        pg.wait_for_timeout(250)
    return False
up=lambda pg,id: pg.evaluate("id=>ecList().then(L=>(L.find(x=>x.id===id)||{}).up)",id)
dev=None
try:
  dev=cf_dev.Dev(WP,NP,args=('-c',cfg))
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctxA,A=newpc(b); A.evaluate(SETUP)
    item=A.evaluate("()=>dropsFor(BOSSES.find(x=>x.id==='lucid'),'hard').find(k=>ITEM_ICONS[k])")
    check('클립 창 -1초 ~ +3초 (b354)',A.evaluate("[EC.cfg.pre,EC.cfg.post]")==[1000,3000])
    t0=int(time.time()*1000)-3600e3
    id1=A.evaluate(MK,[t0,20,item])
    A.evaluate("ecSync()"); A.wait_for_timeout(600)
    check('로그인 전: 업로드 안 함(nolog, ⏳)',up(A,id1)==0 and A.evaluate("ECC.st")=='nolog',(up(A,id1),A.evaluate("ECC.st")))
    A.evaluate(f"svLogin('{K('EA')}')")
    A.wait_for_function("()=>localStorage.getItem('mapleBossTracker.svToken')",timeout=15000)
    until(A,"id=>ecList().then(L=>(L.find(x=>x.id===id)||{}).up===1)",id1)
    check('로그인 → 자동 업로드(☁)',up(A,id1)==1 and A.evaluate("ECC.st")=='ok',A.evaluate("ECC.st"))
    rows=dev.sql('SELECT id,boss,item,cname,size,acct_hash FROM epic_clips')
    check('D1 메타(보스·아이템·캐릭터)+크기',len(rows)==1 and rows[0]['boss']=='lucid' and rows[0]['item']==item and rows[0]['cname']=='트딕이' and 0<rows[0]['size']<2*1024*1024,rows)
    rt=A.evaluate("async id=>{ const F=await ecFrames(id), b=await ecPack(F), U=ecUnpack(await b.arrayBuffer()); const a=await F.f[5].arrayBuffer(), c=await U.f[5].arrayBuffer(); return [U.f.length, U.ts[0], a.byteLength===c.byteLength, b.size] }",id1)
    check('ECB1 묶음 왕복(프레임·시각 그대로)',rt[0]==40 and rt[1]==-1000 and rt[2],rt)
    # 오프라인 → 대기 → online 이벤트로 올림
    ctxA.set_offline(True)
    id2=A.evaluate(MK,[t0+600000,200,item]); A.evaluate("ecSync()"); A.wait_for_timeout(800)
    check('오프라인: 이 PC 에 보관·대기(net)',up(A,id2)==0 and A.evaluate("ECC.st")=='net',(up(A,id2),A.evaluate("ECC.st")))
    ctxA.set_offline(False)
    until(A,"id=>ecList().then(L=>(L.find(x=>x.id===id)||{}).up===1)",id2)
    check('다시 연결(online) → 대기 클립 올림',up(A,id2)==1)
    for i in range(1,12): A.evaluate(MK,[t0-i*3600000,(i*30)%360,item])
    A.evaluate("ECC.last=0; ecSync()"); until(A,"()=>ecList().then(L=>!ECC.busy&&L.every(x=>x.up===1))",None,30)
    check('13개 모두 서버에',dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==13)
    A.locator('#tabs [data-tab=epic]').click(); A.wait_for_timeout(800)
    check('PC A: 서버 저장 문구 없음(b356)·카드 ☁ 배지',A.locator('.eccloud').count()==0 and A.evaluate("!document.querySelector('#view').textContent.includes('다른 PC 에서도')") and A.locator('.ecup.on').count()==12,A.evaluate("document.querySelector('.eccloud')?.textContent"))
    A.screenshot(path=os.path.join(OUT,'epic_cloud_A.png'))
    # PC B: 같은 넥슨 계정 다른 키, 빈 IndexedDB
    ctxB,B=newpc(b); B.evaluate(SETUP)
    check('PC B 처음엔 클립 없음',B.evaluate("ecList().then(L=>L.length)")==0)
    B.evaluate(f"svLogin('{K('EA2')}')"); B.wait_for_function("()=>localStorage.getItem('mapleBossTracker.svToken')",timeout=15000)
    B.locator('#tabs [data-tab=epic]').click(); 
    B.wait_for_function("()=>document.querySelectorAll('.ecgrid .ecthumb img').length===12",timeout=30000)
    check('PC B: 서버 목록 13개(1쪽 12 + 2쪽 1)·미리보기 받음',B.evaluate("ecList().then(L=>L.length)")==13 and B.locator('.ecpg .ecpb').count()==2)
    first=B.evaluate("document.querySelector('.ecgrid .eccard .ectl').textContent")
    check('PC B 카드에 보스·아이템·캐릭터',('루시드' in first) and ('트딕이' in first) and B.evaluate("k=>ITEMS[k].n",item) in first,first)
    B.screenshot(path=os.path.join(OUT,'epic_cloud_B.png'))
    B.locator('[data-ecpg="1"]').click(); B.wait_for_timeout(300); B.locator('.eccard').first.click()
    B.wait_for_selector('#ecModal canvas',timeout=15000); B.wait_for_timeout(1200)
    f1=B.evaluate("document.getElementById('ecModal')._f"); B.wait_for_timeout(900); f2=B.evaluate("document.getElementById('ecModal')._f")
    check('PC B: 서버에서 받은 영상 재생(캐시 안 된 2쪽 클립)',f1 is not None and f1!=f2,(f1,f2))
    B.screenshot(path=os.path.join(OUT,'epic_cloud_modal.png')); B.keyboard.press('Escape')
    check('PC B: 받은 영상 IndexedDB 캐시',B.evaluate("ecList().then(async L=>{ let n=0; for(const m of L) if(await ecFrames(m.id)) n++; return n; })")==13)
    # R2 꺼짐(지금 운영 상태) → 이 PC 에만, 지우지 않음
    A.route(API+'/api/epic/**',lambda r:r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'r2_off','message':'off'})))
    id3=A.evaluate(MK,[t0+1200000,90,item]); A.evaluate("ECC.last=0; ecSync()"); A.wait_for_timeout(1000)
    check('R2 꺼짐: 503 → off, 클립은 이 PC 에(⏳)',A.evaluate("ECC.st")=='off' and up(A,id3)==0 and A.evaluate("ecList().then(L=>L.length)")==14)
    A.evaluate("EC.page=0; renderEpic()"); A.wait_for_timeout(500)
    check('R2 꺼짐 표시',A.locator('.eccloud.off').count()==1,A.evaluate("document.querySelector('.eccloud')?.textContent"))
    A.screenshot(path=os.path.join(OUT,'epic_cloud_off.png'))
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
  if dev: dev.stop()
  try: os.remove(cfg)
  except Exception: pass
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
