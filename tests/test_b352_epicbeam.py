# test_b352 (t657): 에픽빔 기록지 — 합성 영상(게임 화면 + 사용자 GIF 에픽빔, 6.0초)으로 감지·-1~+3초 클립(b354)·IndexedDB·자동 기록 연결, 흰 섬광 오감지 없음, 4x3 그리드·페이지·모달.
# 스크린샷: MBT_SHOTDIR(기본 tests/out) 에 tabs.png, epic_grid.png, epic_modal.png
import os, sys, tempfile, shutil, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
for f in ['beam_synth.webm','flash_synth.webm']: shutil.copy(os.path.join(ROOT,'tests','fixtures','b352',f),site)
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]}; const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}});
  S.characters=[mk('c0','트딕이'),mk('c1','지운캐')]; S.activeId='c0'; save(); render(); }"""
PLAY="""async(src)=>{ const v=document.createElement('video'); v.muted=true; v.src=src; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;width:320px'; document.body.appendChild(v); await v.play(); ARX.testSrc=v; window._v=v; return true; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1600,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    # 탭: 캘린더 바로 뒤, 아이콘, Paperlogy
    order=pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.dataset.tab)")
    check('탭 순서: 캘린더 바로 뒤 에픽빔 기록지',order[order.index('cal')+1]=='epic',order)
    ic=pg.evaluate("()=>{const b=document.querySelector('#tabs [data-tab=epic]'),i=b.querySelector('img.ecico'),r=i.getBoundingClientRect();return [b.textContent.trim(),i.src.startsWith('data:image/png'),Math.round(r.width),i.complete&&i.naturalWidth,getComputedStyle(b).fontFamily]}")
    check('탭 아이콘(GIF 프레임) 16px + 글자 + Paperlogy',ic[0]=='에픽빔 기록지' and ic[1] and ic[2]==16 and ic[3]==40 and 'Paperlogy' in ic[4],ic)
    pg.locator('nav.tabs').screenshot(path=os.path.join(OUT,'tabs.png'))
    # 게이트: 보상 맵이 아니면 감지해도 저장 안 함
    check('보스·보상 맵 아니면 ecCtx=null',pg.evaluate("()=>{ ARX.det={cid:'c0',boss:'lucid',diff:'hard',src:''}; ARX.rew=null; ARX.mapSt=null; return ecCtx(Date.now())===null; }"))
    item=pg.evaluate("()=>{ const b=BOSSES.find(x=>x.id==='lucid'); return dropsFor(b,'hard').find(k=>ITEM_ICONS[k]); }")
    pg.evaluate("()=>{ ARX.det={cid:'c0',boss:'lucid',diff:'hard',src:''}; ARX.rew={boss:'lucid'}; }")
    # 흰 섬광(같은 밝기 곡선, 광선 모양 없음) → 저장 없음
    pg.evaluate(PLAY,'flash_synth.webm'); pg.wait_for_timeout(9500)
    mx=pg.evaluate("Math.max(0,...EC.log.map(x=>x.sc))")
    check('흰 섬광 영상: 감지 안 함',not pg.evaluate("EC.cur||EC.saved"),pg.evaluate("[EC.saved,EC.last]"))
    pg.evaluate("()=>{ _v.pause(); _v.remove(); ARX.testSrc=null; EC.h=[]; EC.log=[]; EC.buf=[]; }"); pg.wait_for_timeout(300)
    # 에픽빔 영상
    pg.evaluate(PLAY,'beam_synth.webm')
    t0=time.time()
    while time.time()-t0<9 and pg.evaluate("_v.currentTime")<8.0: pg.wait_for_timeout(100)
    pg.evaluate("([k])=>arSessAdd(k,'루시드','트딕이')",[item])   # 에픽빔 뒤 2초쯤 자동 기록 (감싼 arSessAdd)
    while time.time()-t0<22 and not pg.evaluate("EC.saved"): pg.wait_for_timeout(200)
    pg.wait_for_timeout(600)
    L=pg.evaluate("ecList().then(L=>L.map(m=>({...m,poster:!!m.poster})))")
    check('에픽빔 감지 → 클립 1개 저장',len(L)==1,L)
    if L:
      m=L[0]; print('meta',{k:m[k] for k in ('vt0','vts','n','start','end','sc','item','cid','boss','diff','bytes')})
      check('첫 감지 프레임 = 에픽빔 시작(6.0초) 직후',6.0<=m['vt0']<=6.6,m['vt0'])
      check('클립 시작 = 첫 감지 -1초 (b354)',abs(m['vts'][0]-(m['vt0']-1))<=0.25 and -1000<=m['start']<=-850,(m['vts'],m['start']))
      check('클립 끝 = +3초(총 4초, b354)',abs(m['vts'][1]-(m['vt0']+3))<=0.3 and 2700<=m['end']<3000,(m['vts'],m['end']))
      check('약 10fps 프레임',33<=m['n']<=41,m['n'])
      check('서버 로그인 없음 → 올릴 예정(up:0)·이 PC 저장',m.get('up')==0 and pg.evaluate("ECC.st")=='nolog',(m.get('up'),pg.evaluate("ECC.st")))
      check('자동 기록 아이템 연결(보스·난이도·아이템·캐릭터)',m['item']==item and m['boss']=='lucid' and m['diff']=='hard' and m['cid']=='c0',m)
      fr=pg.evaluate("ecFrames(ecList.length?'':'').then?0:0")
      ff=pg.evaluate("async(id)=>{ const F=await ecFrames(id); return [F.f.length, F.f.every(b=>b instanceof Blob&&b.type==='image/jpeg')] }",m['id'])
      check('IndexedDB 에 JPEG 프레임 저장',ff[0]==m['n'] and ff[1],ff)
    pg.evaluate("()=>{ _v.pause(); ARX.testSrc=null; }")
    # 그리드·페이지: 같은 프레임으로 14개 더 (총 15)
    pg.evaluate("""async()=>{ const [m]=await ecList(), F=await ecFrames(m.id); const its=dropsFor(BOSSES.find(x=>x.id==='will'),'hard').filter(k=>ITEM_ICONS[k]);
      for(let i=1;i<=14;i++){ const id='ec'+(m.t0-i*3600e3); await ecTx(['meta','frames'],'readwrite',t=>{ t.objectStore('meta').put({...m,id,t0:m.t0-i*3600e3,boss:i%2?'will':'lucid',diff:i%3?'hard':'normal',item:i%2?its[i%its.length]:m.item,cid:i%2?'c1':'c0',cname:''}); t.objectStore('frames').put({...F,id}); }); } }""")
    pg.locator('#tabs [data-tab=epic]').click(); pg.wait_for_timeout(700)
    cards=pg.evaluate("[...document.querySelectorAll('.ecgrid .eccard')].map(c=>{const r=c.getBoundingClientRect();return [Math.round(r.left),Math.round(r.top)]})")
    xs=sorted(set(c[0] for c in cards)); ys=sorted(set(c[1] for c in cards))
    check('1페이지 12개 = 4열 x 3행',len(cards)==12 and len(xs)==4 and len(ys)==3,cards)
    lines=pg.evaluate("()=>{const c=document.querySelector('.eccard .ectl');return [...c.children].map(d=>[d.className,d.textContent.trim(),d.querySelectorAll('img,.bicon,.avatar').length])}")
    import re
    check('제목 4줄',len(lines)==4,lines)
    check('1줄 날짜·시간(KST)',re.fullmatch(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}',lines[0][1]) is not None,lines[0])
    check('2줄 보스 아이콘·이름(난이도)',lines[1][2]>=1 and lines[1][1]=='루시드 (하드)',lines[1])
    check('3줄 아이템 아이콘·이름',lines[2][2]>=1 and lines[2][1]==pg.evaluate("k=>ITEMS[k].n",item),lines[2])
    check('4줄 캐릭터 초상화·닉네임',lines[3][2]>=1 and lines[3][1].endswith('트딕이'),lines[3])
    pgs=pg.evaluate("[...document.querySelectorAll('.ecpg .ecpb')].map(b=>b.textContent+(b.classList.contains('on')?'*':''))")
    check('번호 페이지 1*,2',pgs==['1*','2'],pgs)
    pg.screenshot(path=os.path.join(OUT,'epic_grid.png'),full_page=False)
    pg.locator('[data-ecpg="1"]').click(); pg.wait_for_timeout(400)
    check('2페이지 3개',pg.locator('.ecgrid .eccard').count()==3 and pg.evaluate("document.querySelector('.ecpb.on').textContent")=='2')
    pg.locator('[data-ecpg="0"]').click(); pg.wait_for_timeout(400)
    pg.locator('.eccard').first.click(); pg.wait_for_timeout(1500)
    mo=pg.evaluate("()=>{const o=document.getElementById('ecModal'),bx=o.querySelector('.ecbox').getBoundingClientRect(),cv=o.querySelector('canvas'),d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;let s=0;for(let i=0;i<d.length;i+=40)s+=d[i];return {cx:bx.left+bx.width/2,cy:bx.top+bx.height/2,w:bx.width,vw:innerWidth,vh:innerHeight,lum:s/(d.length/40),f:o._f}}")
    check('모달 화면 가운데 크게',abs(mo['cx']-800)<4 and abs(mo['cy']-550)<40 and mo['w']>=1000,mo)
    check('모달 영상 그려짐',mo['lum']>20,mo)
    f1=mo['f']; pg.wait_for_timeout(1500); f2=pg.evaluate("document.getElementById('ecModal')._f")
    check('모달 영상 재생(프레임 진행)',f2!=f1,(f1,f2))
    pg.wait_for_function("()=>{const t=document.querySelector('#ecModal .ectime');return t&&parseFloat(t.textContent)>=0.0&&parseFloat(t.textContent)<0.4}",timeout=15000)
    pg.screenshot(path=os.path.join(OUT,'epic_modal.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('Esc 로 닫힘',pg.locator('#ecModal').count()==0)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
