# b390: 클라이언트 명시 삭제 전파 — 완전한 삭제 이력(complete)만 IDB(meta+frames) 제거, 실패/오프라인/로그인 없음/예전 서버/일부 페이지 실패는 보존, 오래된 캐시 재업로드 거부. 로컬 wrangler+모의 넥슨.
# (b354 도우미 재사용) b354: 에픽빔 클립 서버 저장(사이트 쪽) — wrangler dev(로컬 R2·D1) + 넥슨 모의 서버 + 브라우저 두 개(PC A·PC B)
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
MN.start(NP); MN.KEYS[K('EA')]=['acc-b390c-A']; MN.KEYS[K('EA2')]=['acc-b390c-A']
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b390c-%d.toml'%os.getpid())
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
has=lambda pg,id: pg.evaluate("async id=>{const L=await ecList();return [!!L.find(x=>x.id===id),!!(await ecFrames(id))]}",id)
def sync(pg): pg.evaluate("async()=>{ while(ECC.busy) await new Promise(r=>setTimeout(r,50)); ECC.last=Date.now(); await ecSync(); while(ECC.busy) await new Promise(r=>setTimeout(r,50)); }")
def login(pg,k): pg.evaluate(f"svLogin('{K(k)}')"); pg.wait_for_function("()=>localStorage.getItem('mapleBossTracker.svToken')",timeout=15000); until(pg,"()=>!ECC.busy&&ECC.st==='ok'",None,20)
dev=None
try:
  dev=cf_dev.Dev(WP,NP,args=('-c',cfg))
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctxA,A=newpc(b); A.evaluate(SETUP); item=A.evaluate("()=>dropsFor(BOSSES.find(x=>x.id==='lucid'),'hard').find(k=>ITEM_ICONS[k])")
    t0=int(time.time()*1000)-7200e3
    i1,i2,i3=[A.evaluate(MK,[t0+k*60000,20+k*40,item]) for k in range(3)]
    login(A,'EA'); sync(A)
    check('PC A 3개 업로드',A.evaluate("ecList().then(L=>L.filter(x=>x.up===1).length)")==3 and dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==3)
    ctxB,B=newpc(b); B.evaluate(SETUP)
    ctxB.set_offline(True); x1=B.evaluate(MK,[t0+30*60000,300,item]); ctxB.set_offline(False)
    B.route(API+'/api/epic/clip?**',lambda r:r.fulfill(status=429,content_type='application/json',body='{"error":"too_many"}'))  # B 의 업로드만 잠시 429 로 미뤄 x1 을 미업로드로 유지(목록 동기화는 계속)
    login(B,'EA2'); sync(B)
    check('PC B: 서버 목록 3개 받음 + 미업로드 x1',sorted(B.evaluate("ecList().then(L=>L.map(x=>x.id))"))==sorted([i1,i2,i3,x1]) and B.evaluate(f"ecList().then(L=>L.find(x=>x.id==='{x1}').up)")==0)
    B.evaluate(f"id=>ecFetch({{id,format:'ecb'}}).catch(()=>0)",i1); B.evaluate("async id=>{const m=(await ecList()).find(x=>x.id===id);await ecFetch(m);}",i1)
    check('PC B: i1 영상 캐시',has(B,i1)==[True,True])
    S0=B.evaluate("JSON.stringify(S)")
    # PC A 에서 i1 명시 삭제
    r=A.evaluate("id=>ecDeleteClip(id)",i1)
    check('PC A ecDeleteClip → ok, 이 PC 사본 제거',r.get('ok') and r.get('deleted')==1 and has(A,i1)==[False,False],r)
    check('서버 행 삭제·이력 기록',dev.sql(f"SELECT COUNT(*) n FROM epic_clips WHERE id='{i1}'")[0]['n']==0 and dev.sql(f"SELECT COUNT(*) n FROM epic_tomb WHERE id='{i1}'")[0]['n']>=1)
    # 실패 경로: 아무것도 지우지 않음
    B.route(API+'/api/epic/deleted**',lambda r:r.fulfill(status=500,content_type='application/json',body='{"error":"x"}')); sync(B)
    check('이력 500 → B 에서 지우지 않음',has(B,i1)==[True,True]); B.unroute(API+'/api/epic/deleted**')
    pgN=[0]
    def part(r):
        pgN[0]+=1
        if pgN[0]==1: r.fulfill(status=200,content_type='application/json',body=json.dumps({'items':[{'id':i1,'at':1}],'next':{'after':1,'aid':i1},'complete':False}))
        else: r.fulfill(status=500,content_type='application/json',body='{"error":"x"}')
    B.route(API+'/api/epic/deleted**',part); sync(B)
    check('이력 일부 페이지 실패(complete 아님) → 지우지 않음',has(B,i1)==[True,True] and pgN[0]>=2,pgN); B.unroute(API+'/api/epic/deleted**')
    B.route(API+'/api/epic/deleted**',lambda r:r.fulfill(status=404,content_type='application/json',body='{"error":"not_found"}')); sync(B)
    check('예전 서버(이력 API 없음 404) → 지우지 않고 동기화 계속(ok)',has(B,i1)==[True,True] and B.evaluate("ECC.st")=='ok'); B.unroute(API+'/api/epic/deleted**')
    tok=B.evaluate("localStorage.getItem('mapleBossTracker.svToken')"); B.evaluate("localStorage.removeItem('mapleBossTracker.svToken')"); sync(B)
    check('로그인 없음 → 지우지 않음(nolog)',has(B,i1)==[True,True] and B.evaluate("ECC.st")=='nolog',B.evaluate("ECC.st")); B.evaluate(f"localStorage.setItem('mapleBossTracker.svToken','{tok}')")
    ctxB.set_offline(True); sync(B); check('오프라인 → 지우지 않음(net)',has(B,i1)==[True,True] and B.evaluate("ECC.st")=='net',B.evaluate("ECC.st")); ctxB.set_offline(False)  # online 이벤트 → 정상 동기화
    # 정상 동기화 → 명시 id 만 제거
    sync(B)
    check('정상 이력 → B 의 i1 meta+frames 제거',has(B,i1)==[False,False])
    check('i2·i3(서버 목록)·x1(미업로드) 보존',all(B.evaluate("id=>ecList().then(L=>!!L.find(x=>x.id===id))",i) for i in (i2,i3,x1)) and B.evaluate(f"ecList().then(L=>L.find(x=>x.id==='{x1}').up)")==0)
    check('일반 S(보스 기록 등) 그대로',B.evaluate("JSON.stringify(S)")==S0)
    B.unroute(API+'/api/epic/clip?**'); sync(B)
    check('x1 은 이후 정상 업로드',B.evaluate(f"ecList().then(L=>L.find(x=>x.id==='{x1}').up)")==1 and dev.sql(f"SELECT COUNT(*) n FROM epic_clips WHERE id='{x1}'")[0]['n']==1)
    # 오래된 캐시 PC C: 로그인 → 이력이 먼저 지워 재업로드 없음
    ctxC,C=newpc(b); C.evaluate(SETUP); C.evaluate(MK,[t0,20,item]); check('PC C: i1 의 오래된 미업로드 사본',has(C,i1)==[True,True])
    login(C,'EA'); sync(C)
    check('PC C 로그인 → 이력으로 i1 제거, 서버 부활 없음',has(C,i1)==[False,False] and dev.sql(f"SELECT COUNT(*) n FROM epic_clips WHERE id='{i1}'")[0]['n']==0)
    # PC D: 이력 조회 실패 중에도 업로드는 410 으로 거부 → 다시 올리지 않음, 지우지도 않음 → 이력 성공 때 제거
    ctxD,D=newpc(b); D.evaluate(SETUP); D.evaluate(MK,[t0,20,item])
    D.route(API+'/api/epic/deleted**',lambda r:r.fulfill(status=500,content_type='application/json',body='{}'))
    login(D,'EA2'); sync(D)
    m=D.evaluate(f"ecList().then(L=>L.find(x=>x.id==='{i1}'))")
    check('PC D: 410 → up=-1·gone, 사본 보존(재시도 안 함), 서버 부활 없음',m and m.get('up')==-1 and m.get('gone')==1 and has(D,i1)==[True,True] and dev.sql(f"SELECT COUNT(*) n FROM epic_clips WHERE id='{i1}'")[0]['n']==0,m and {k:m.get(k) for k in ('up','gone')})
    D.unroute(API+'/api/epic/deleted**'); sync(D); check('PC D: 이력 성공 → i1 제거',has(D,i1)==[False,False])
    r=A.evaluate("id=>ecDeleteClip(id)",'ec1700000000000'); check('없는 id 삭제 → ok:false 404, 로컬 변화 없음',r.get('ok') is False and r.get('status')==404,r)
    r=A.evaluate("id=>ecDeleteClip(id)",'bad'); check('잘못된 id → 요청 안 함 ok:false',r.get('ok') is False and r.get('status')==400,r)
    A.route(API+'/api/epic/clip/**',lambda r:r.fulfill(status=500,content_type='application/json',body='{}') if r.request.method=='DELETE' else r.continue_())
    r=A.evaluate("id=>ecDeleteClip(id)",i2); check('서버 DELETE 실패 → 로컬 i2 보존',r.get('ok') is False and has(A,i2)[0],r); A.unroute(API+'/api/epic/clip/**')
    check('개인 4개 id 하드코딩 없음',not any(x in open(os.path.join(ROOT,'src','epicclip.js'),encoding='utf-8').read() for x in ['ec1794033431494','ec1794032772754','ec1793884892169','ec1793858562894']))
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
  if dev: dev.stop()
  try: os.remove(cfg)
  except Exception: pass
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
