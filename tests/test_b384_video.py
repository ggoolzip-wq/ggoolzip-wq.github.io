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
for f in ['beam_synth.webm','flash_synth.webm','beam720.webm']: shutil.copy(os.path.join(ROOT,'tests','fixtures','b352',f),site)
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]}; const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}});
  S.characters=[mk('c0','트딕이'),mk('c1','지운캐')]; S.activeId='c0'; save(); render(); }"""
PLAY="""async(src)=>{ const v=document.createElement('video'); v.muted=true; v.src=src; v.playsInline=true; v.style.cssText='position:fixed;left:-9999px;width:320px'; document.body.appendChild(v); await v.play(); ARX.testSrc=v; window._v=v; return true; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1600,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP);pg.evaluate("ARX.video=null")
    # 탭: 캘린더 바로 뒤, 아이콘, Paperlogy
    order=pg.evaluate("[...document.querySelectorAll('#tabs button')].map(b=>b.dataset.tab)")
    check('탭 순서: 캘린더 바로 뒤 에픽빔 기록지',order[order.index('cal')+1]=='epic',order)
    ic=pg.evaluate("()=>{const b=document.querySelector('#tabs [data-tab=epic]'),i=b.querySelector('img.ecico'),r=i.getBoundingClientRect();return [b.textContent.trim(),i.src.startsWith('data:image/png'),Math.round(r.width),i.complete&&i.naturalWidth,getComputedStyle(b).fontFamily]}")
    check('탭 아이콘(GIF 프레임) 16px + 글자 + Paperlogy',ic[0]=='에픽빔 기록지' and ic[1] and ic[2]==16 and ic[3]==40 and 'Paperlogy' in ic[4],ic)
    pg.locator('nav.tabs').screenshot(path=os.path.join(OUT,'tabs.png'))
    # 게이트: 보상 맵이 아니면 감지해도 저장 안 함
    check('보스·보상 맵 아니면 ecCtx=null',pg.evaluate("()=>{ ARX.det={cid:'c0',boss:'lucid',diff:'hard',src:''}; ARX.rew=null; ARX.mapSt=null; return ecCtx(Date.now())===null; }"))
    item=pg.evaluate("()=>{ const b=BOSSES.find(x=>x.id==='lucid'); return dropsFor(b,'hard').find(k=>ITEM_ICONS[k]); }")
    pg.evaluate("()=>{ ARX.det={cid:'c0',boss:'lucid',diff:'hard',src:''}; ARX.rew={boss:'lucid'}; ARX.mapSt={boss:'lucid',kind:'r',t:Date.now()}; setInterval(()=>{ if(ARX.mapSt) ARX.mapSt.t=Date.now(); },1000); }")
    pg.evaluate(PLAY,'beam720.webm')
    t0=time.time()
    while time.time()-t0<9 and pg.evaluate("_v.currentTime")<8.0: pg.wait_for_timeout(100)
    pg.evaluate("([k])=>arSessAdd(k,'루시드','트딕이')",[item])
    while time.time()-t0<35 and not pg.evaluate("EC.saved"): pg.wait_for_timeout(200)
    check('720p VP9 저장 실패 없음',not pg.evaluate("ECV.videoError"),pg.evaluate("ECV.videoError"))
    L=pg.evaluate("ecList().then(L=>L.map(m=>({...m,poster:!!m.poster})))")
    check('에픽빔 감지 → 클립 1개 저장',len(L)==1,L)
    if L:
      m=L[0]; print('meta',{k:m[k] for k in ('vt0','vts','n','start','end','sc','item','cid','boss','diff','bytes')})
      check('첫 감지 프레임 = 에픽빔 시작(6.0초) 직후',6.0<=m['vt0']<=6.6,m['vt0'])
      check('클립 시작 = 첫 감지 -1초 (b354)',abs(m['vts'][0]-(m['vt0']-1))<=0.25 and -1000<=m['start']<=-850,(m['vts'],m['start']))
      check('클립 끝 = +3초(총 4초, b354)',abs(m['vts'][1]-(m['vt0']+3))<=0.3 and 2700<=m['end']<=3034,(m['vts'],m['end']))
      check('30fps 목표 실제 프레임 ≥96',96<=m['n'],m['n'])
      check('b384 실제 WebM ≤800,000B',m['bytes']<=800000 and m['bytes']>0,m['bytes'])
      check('native 720p 업스케일 없음',m['w']==1280 and m['h']==720 and m['fps']==30 and m['format']=='webm',m)
      check('서버 로그인 없음 → 올릴 예정(up:0)·이 PC 저장',m.get('up')==0 and pg.evaluate("ECC.st")=='nolog',(m.get('up'),pg.evaluate("ECC.st")))
      check('자동 기록 아이템 연결(보스·난이도·아이템·캐릭터)',m['item']==item and m['boss']=='lucid' and m['diff']=='hard' and m['cid']=='c0',m)
      blob=pg.evaluate("async(id)=>{const F=await ecFrames(id);return [...new Uint8Array(await F.video.arrayBuffer())]}",m['id'])
      import pathlib,base64
      pd=pathlib.Path('/workspace/b384');pd.mkdir(exist_ok=True);(pd/'clip.webm').write_bytes(bytes(blob))
      both=pg.evaluate("""async()=>{const src=document.createElement('canvas');src.width=1280;src.height=720;const g=src.getContext('2d');_v.currentTime=6.6;await new Promise(r=>_v.onseeked=r);g.drawImage(_v,0,0,1280,720);const old=await new Promise(r=>{const c=document.createElement('canvas');c.width=427;c.height=240;c.getContext('2d').drawImage(_v,0,0,427,240);c.toBlob(r,'image/jpeg',.72)});return {vt:_v.currentTime,old:[...new Uint8Array(await old.arrayBuffer())]};}""")
      (pd/'clip_video_time.txt').write_text(str(both['vt']));(pd/'old_reference.jpg').write_bytes(bytes(both['old']))
    if m['item']!=item: raise RuntimeError('linked clip disappeared')
    oldid=pg.evaluate("""async()=>{const id='ec'+(Date.now()-30*86400000),cv=document.createElement('canvas');cv.width=768;cv.height=432;const g=cv.getContext('2d');g.fillStyle='#3c284c';g.fillRect(0,0,768,432);g.fillStyle='white';g.font='40px sans-serif';g.fillText('old legacy clip',160,220);const f=[],ts=[];for(let i=0;i<32;i++){f.push(await new Promise(r=>cv.toBlob(r,'image/jpeg',.8)));ts.push(-1000+i*125);}await ecTx(['meta','frames'],'readwrite',t=>{t.objectStore('meta').put({id,t0:+id.slice(2),boss:'lucid',diff:'hard',w:768,h:432,n:32,start:-1000,end:3000,pi:0,poster:f[0],up:0});t.objectStore('frames').put({id,ts,vt:[],f});});await ecOpen(id);return id;}""")
    pg.wait_for_timeout(500)
    check('예전 JPEG/WebP ECB1 캔버스 재생',pg.locator('#ecModal canvas').count()==1 and pg.evaluate("document.getElementById('ecModal')._f") is not None)
    pg.keyboard.press('Escape');pg.wait_for_timeout(200);pg.evaluate("ecClose()")
    pg.evaluate("()=>{ _v.pause(); ARX.testSrc=null; }")
    # 그리드·페이지: 같은 WebM 으로 14개 더 (총 15)
    if not L: raise RuntimeError('clip missing')
    pg.evaluate("""async()=>{ const L=await ecList();window.origClip=L.find(x=>x.format==='webm'); const m=origClip, F=await ecFrames(m.id); const its=dropsFor(BOSSES.find(x=>x.id==='will'),'hard').filter(k=>ITEM_ICONS[k]);
      for(let i=2;i<=15;i++){ const id='ec'+(m.t0-i*3600e3); await ecTx(['meta','frames'],'readwrite',t=>{ t.objectStore('meta').put({...m,id,t0:m.t0-i*3600e3,boss:i%2?'will':'lucid',diff:i%3?'hard':'normal',item:i%2?its[i%its.length]:m.item,cid:i%2?'c1':'c0',cname:''}); t.objectStore('frames').put({...F,id}); }); } }""")
    pg.locator('#tabs [data-tab=epic]').click(); pg.wait_for_timeout(700)
    cards=pg.evaluate("[...document.querySelectorAll('.ecgrid .eccard')].map(c=>{const r=c.getBoundingClientRect();return [Math.round(r.left),Math.round(r.top)]})")
    xs=sorted(set(c[0] for c in cards)); ys=sorted(set(c[1] for c in cards))
    check('1페이지 12개 = 4열 x 3행',len(cards)==12 and len(xs)==4 and len(ys)==3,cards)
    lines=pg.evaluate("()=>{const c=document.querySelector('.eccard .ectl');return [...c.children].map(d=>[d.className,d.textContent.trim(),d.querySelectorAll('img,.bicon,.avatar').length])}")
    import re
    check('제목 4줄',len(lines)==4,lines)
    check('1줄 날짜·시간(KST)',re.fullmatch(r'\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}',lines[0][1]) is not None,lines[0])
    check('2줄 보스 아이콘·이름(난이도)',lines[1][2]>=1 and lines[1][1].startswith('루시드 '),lines[1])
    check('3줄 아이템 아이콘·이름',lines[2][2]>=1 and lines[2][1]==pg.evaluate("k=>ITEMS[k].n",item),lines[2])
    check('4줄 캐릭터 초상화·닉네임',lines[3][2]>=1 and lines[3][1].endswith('트딕이'),lines[3])
    pgs=pg.evaluate("[...document.querySelectorAll('.ecpg .ecpb')].map(b=>b.textContent+(b.classList.contains('on')?'*':''))")
    check('번호 페이지 1*,2',pgs==['1*','2'],pgs)
    pg.screenshot(path=os.path.join(OUT,'epic_grid.png'),full_page=False)
    pg.locator('[data-ecpg="1"]').click(); pg.wait_for_timeout(400)
    check('2페이지 4개(예전 1+신규 15)',pg.locator('.ecgrid .eccard').count()==4 and pg.evaluate("document.querySelector('.ecpb.on').textContent")=='2')
    pg.locator('[data-ecpg="0"]').click(); pg.wait_for_timeout(400)
    pg.evaluate("()=>ecOpen(origClip.id)"); pg.wait_for_timeout(1500)
    mo=pg.evaluate("()=>{const o=document.getElementById('ecModal'),bx=o.querySelector('.ecbox').getBoundingClientRect(),v=o.querySelector('video');return {cx:bx.left+bx.width/2,cy:bx.top+bx.height/2,w:bx.width,vw:innerWidth,vh:innerHeight,ready:v.readyState,f:v.currentTime};}")
    check('모달 화면 가운데 크게',abs(mo['cx']-800)<4 and abs(mo['cy']-550)<40 and mo['w']>=1000,mo)
    check('모달 WebM 실제 decode',mo['ready']>=2,mo)
    f1=mo['f']; pg.wait_for_timeout(1500); f2=pg.evaluate("document.querySelector('#ecModal video').currentTime")
    check('모달 영상 재생(프레임 진행)',f2!=f1,(f1,f2))
    pg.screenshot(path=os.path.join(OUT,'epic_modal.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    check('Esc 로 닫힘',pg.locator('#ecModal').count()==0)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
