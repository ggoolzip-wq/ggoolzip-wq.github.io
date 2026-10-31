# test_b319 (t574/t575): 상태바 닉네임 = 목록 이름과 정확히 같을 때만 그 캐릭터, 아니면 '-' (근사 매칭으로 다른 캐릭터 고르지 않음)
# 재현: 붐하우스로 접속(목록에 붐하우스 없음/있음) → 예전엔 자모 유사도·느슨 비교로 '트딕이' 가 뜸. 해상도 프로필 5개로 합성한 상태바 + 실제 OCR.
import os, sys, tempfile, shutil, subprocess, json
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
SETUP="""async(names)=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name)=>({id,name,level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=names.map((n,i)=>C('c'+i,n)); S.activeId='c0'; window.AR.cfg.cid='c0'; save&&save(); render();
  if(!window._im){ const im=new Image(); im.src='fx/v07_1080.jpg'; await im.decode(); window._im=im; await arOcrLoad(); } }"""
# 프로필: [게임 W,H, UI 배율]
PROFS=[(1366,768,1),(1920,1080,1),(1920,1080,1.40625),(2560,1440,1.875),(2560,1440,2)]
CASE="""async ([W,H,s,name,prev])=>{ const A=window.AR, im=window._im; const cv=document.createElement('canvas'); cv.width=W; cv.height=H; const g=cv.getContext('2d');
  g.drawImage(im,0,0,W,H); g.fillStyle='#10141a'; g.fillRect(0,H*1028/1080,W*392/1920,H); const bw=384*s, bh=28*s, dy=H-46*s; g.drawImage(im,0,1034,384,28,0,dy,bw,bh);
  g.fillStyle='#1b2026'; g.fillRect(56*s,dy+2*s,150*s,bh-3*s); g.fillStyle='#f2f2f2'; g.font=`${Math.round(16*s)}px "Gothic A1","Noto Sans CJK KR",sans-serif`; g.textBaseline='middle'; g.fillText(name,61*s,dy+bh/2+1*s);
  A.bbox=arBBox(cv); A.bbKey='t'+W+'x'+H+s+name; A.geo=null; A.prof=null; await arProfDetect(cv).catch(()=>{});
  A.det.cid=prev; A.cidT=Date.now()-5000; A.nChgT=Date.now()-1000; A.nameOk=false; A.video=cv; if(!A.stream){ const c=document.createElement('canvas'); c.width=c.height=8; A.stream=c.captureStream(1); }
  const reads=[]; let cid=null;
  A.nOther=[]; for(const k of [3,4,2,3,4,2,3,4,2]){ const t=await arOcr(arCrop(cv,W,H,arR('name',cv),arSc(H,k,cv)),150,1); arNameRes(t); reads.push([t.replace(/\\n/g,' ').trim(),A.det.cid,A.nameRead||'']); }
  arPanelPaint(); const e=document.querySelector('#arPanel .ar-cchar .ar-b'); const tg=arTarget();
  const c2=document.createElement('canvas'); const r=arR('name',cv); c2.width=Math.round(r.w*W); c2.height=Math.round(r.h*H); c2.getContext('2d').drawImage(cv,r.x*W,r.y*H,r.w*W,r.h*H,0,0,c2.width,c2.height);
  return {reads,cid:A.det.cid,tgt:tg?tg.c.name:'',html:e?e.innerText:'',img:c2.toDataURL()}; }"""
import base64
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400)
    try: pg.click('#arGuide [data-arg="x"]',timeout=1500)
    except Exception: pass
    # 1) 순수 함수: 비슷한 글자로 읽혀도 다른 캐릭터 안 고름
    pg.evaluate(SETUP,['트딕이','팬더데이','린벨자','Drcancel'])
    nm=pg.evaluate("()=>['Lv.285 붐하우스','Lv.285 붐하우스뇨','7.689 드티니','17.208 드특니','Lv.285 트딕','Lv.285 트딕이','Lv.289 팬더데이','Lv.285 Drcancel','Lv.285 drcance1','Lv.285 부하우스','Lv.285 트딕이다'].map(t=>{const c=arDetectChar(t);return c?S.characters.find(x=>x.id===c).name:''})")
    print('pure',nm)
    check('정확히 같은 이름만 캐릭터 (붐하우스·드티니·드특니·트딕·부하우스·트딕이다 → 없음)', nm==['','','','','','트딕이','팬더데이','Drcancel','Drcancel','',''], nm)
    ok_t=[]
    for listed in [False,True]:
      names=['트딕이','팬더데이','린벨자']+(['붐하우스'] if listed else [])
      pg.evaluate(SETUP,names)
      for W,H,s in PROFS:
        for prev in ['','c0']:
          r=pg.evaluate(CASE,[W,H,s,'붐하우스',prev]); tag=f"{W}x{H}@{s} 목록{'O' if listed else 'X'} 이전={'트딕이' if prev else '-'}"
          if prev=='' and not listed: open(os.path.join(OUT,f'b319_bar_{W}_{s}.png'),'wb').write(base64.b64decode(r['img'].split(',')[1]))
          print(tag,r['reads'],r['cid'],r['tgt'],repr(r['html']))
          import difflib
          readable=sum(1 for x in r['reads'] if len(x[2])>=3)>=2
          if prev=='':
            check(f'{tag}: 붐하우스 화면 → 트딕이로 절대 안 바뀜', all(x[1]!='c0' for x in r['reads']) and r['tgt']!='트딕이', r['reads'])
          elif readable:
            check(f'{tag}: 다른 닉네임이 읽히면 트딕이 → 붐하우스/"-"', r['tgt']!='트딕이' and '트딕이' not in r['html'], r['reads'])
          else:
            print('  (이 합성 해상도는 이름이 전혀 안 읽힘 → 지금 캐릭터 유지가 정상)'); check(f'{tag}: 못 읽음 → 지금 캐릭터 유지(t576)', r['tgt']=='트딕이', r['reads'])
          if listed: check(f'{tag}: 목록에 있으면 붐하우스 또는 "-" (다른 캐릭터 아님)', r['tgt'] in ('붐하우스',''), r['reads'])
          elif prev=='' or readable: check(f'{tag}: 목록에 없으면 기록 대상 없음 · 캐릭터 \"-\"', r['cid']=='' and r['tgt']=='', r)
      for W,H,s in PROFS:
        r=pg.evaluate(CASE,[W,H,s,'트딕이','']); print('tdk',W,s,r['reads'])
        check(f'{W}x{H}@{s}: 트딕이 화면 → 트딕이 또는 "-" (붐하우스 등 다른 캐릭터 아님)', r['tgt'] in ('트딕이',''), r['reads']); ok_t.append(r['tgt']=='트딕이')
    check('정확히 읽힌 프로필에선 실제로 트딕이로 잡힘', any(ok_t), ok_t)
    # t576: 이름 OCR 1회 비용 (CPU 부하 추정용)
    ms=pg.evaluate("""async()=>{ const im=window._im, cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; cv.getContext('2d').drawImage(im,0,0); const out=[];
      for(let i=0;i<20;i++){ const t0=performance.now(); await arOcr(arCrop(cv,1920,1080,arR('name',cv),arSc(1080,[3,4,2][i%3],cv)),150,1); out.push(performance.now()-t0); } out.sort((a,b)=>a-b); return [out[10],out.reduce((a,b)=>a+b)/out.length]; }""")
    print('NAME_OCR_MS median=%.0f avg=%.0f'%tuple(ms)); check('이름 OCR 1회가 0.2초 틱 안에 끝남(대략)', ms[0]<400, ms)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails,'ERRORS:',[])
sys.exit(1 if fails else 0)
