# test_b283: 게임 화면 연결 → 자동 기록 (합성 화면: 미니맵 '하드 루시드' · 이름 · 몽환의 벨트 아이콘). getDisplayMedia 는 canvas.captureStream 으로 대신.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SD=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data')); shutil.copytree(os.path.join(ROOT,'ocr'),os.path.join(site,'ocr'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ S.characters=[
  {id:'c0',name:'제트루',level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:{lucid:{enabled:true,diff:'hard',party:1},will:{enabled:true,diff:'hard',party:1}},weekly:{lucid:true},monthly:{},auto:{},drops:{},sync:{}},
  {id:'c1',name:'부캐둘',level:270,job:'비숍',world:'스카니아',ocid:'',accId:'',isMain:false,image:'',bosses:{lucid:{enabled:true,diff:'hard',party:1}},weekly:{},monthly:{},auto:{},drops:{},sync:{}}];
  S.activeId='c1'; save&&save(); render(); }"""
SCENE="""async ([map,name,item,show])=>{ const cv=window._scene||(window._scene=document.createElement('canvas')); cv.width=1280; cv.height=720; const g=cv.getContext('2d');
  const gr=g.createLinearGradient(0,0,0,720); gr.addColorStop(0,'#2b3a55'); gr.addColorStop(1,'#4a3a2a'); g.fillStyle=gr; g.fillRect(0,0,1280,720);
  g.fillStyle='#6b5a3a'; g.fillRect(0,560,1280,30); for(let i=0;i<40;i++){ g.fillStyle=`hsl(${i*37%360},30%,35%)`; g.fillRect((i*97)%1280,(i*53)%500+40,60,20); }
  g.fillStyle='rgba(0,0,0,.6)'; g.fillRect(0,0,256,32); g.fillStyle='#fff'; g.font='bold 15px NanumGothic'; g.fillText(map,8,22);
  g.fillStyle='rgba(0,0,0,.7)'; g.fillRect(0,688,256,20); g.fillStyle='#fff'; g.font='bold 14px NanumGothic'; g.fillText(name?'Lv.280 '+name:'',8,703); /* b284: 실제 화면처럼 왼쪽 아래 상태바 */
  if(show){ const im=new Image(); im.src=ITEM_ICONS[item]; await im.decode(); g.drawImage(im,612,513,47,47); } /* b287: 실제 바닥 아이콘 크기(1080p 71px → 720p 47px) */
  window.AR.testSrc=cv; return 1; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    reqs=[]; big=[]; pg.on('request',lambda r:(reqs.append(r.url), (r.post_data_buffer and len(r.post_data_buffer)>20000 and big.append(r.url))))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1000)
    check('연결 전 OCR 안 불러옴', not any('/ocr/' in u for u in reqs), [u for u in reqs if 'ocr' in u])
    check('b294: 헤더 버튼 없음 → 자동 기록 탭', pg.locator('#arBtn').count()==0 and pg.locator('#tabs [data-tab=auto]').count()==1)
    if SD: os.makedirs(SD,exist_ok=True); pg.locator('#tabs').screenshot(path=os.path.join(SD,'button.png'))
    pg.evaluate(SETUP)
    pg.evaluate(SCENE,['레헬른 악몽의 시계탑 <하드>','제트루','belt',False])
    pg.evaluate("navigator.mediaDevices.getDisplayMedia=async()=>{ setInterval(()=>{ const g=window._scene.getContext('2d'); g.fillStyle='rgba(0,0,0,.02)'; g.fillRect(0,0,1,1); },100); return window._scene.captureStream(4); }")
    pg.click('#tabs [data-tab=auto]'); pg.wait_for_selector('#arGuide [data-arg=ok]'); pg.click('#arGuide [data-arg=ok]')  # b288: 헤더 버튼 한 번에 연결
    try: pg.wait_for_function("window.AR.stream&&window.AR.ocr",timeout=60000)
    except Exception:
        print("DBG",pg.evaluate("({s:!!window.AR.stream,e:window.AR.ocrErr,o:!!window.AR.ocr,T:typeof Tesseract})"),errs,[u for u in reqs if "ocr" in u]); raise
    pg.evaluate("window.AR.lastOcr=0"); 
    try: pg.wait_for_function("window.AR.det.boss",timeout=30000)
    except Exception:
        print("DBG2",pg.evaluate("({m:window.AR.mapText,n:window.AR.nameText,b:window.AR.busy,vw:window.AR.video&&window.AR.video.videoWidth,l:window.AR.lastOcr})"),errs); raise
    pg.wait_for_timeout(500)
    d=pg.evaluate("({det:window.AR.det,map:window.AR.mapText,name:window.AR.nameText})")
    check('맵 이름 OCR → 루시드 하드', d['det']['boss']=='lucid' and d['det']['diff']=='hard', d)
    check('이름 OCR → 제트루(c0)', d['det']['cid']=='c0', d)
    check('아이콘 없으면 기록 없음', not pg.evaluate("Object.keys(S.characters[0].drops).length"))
    pg.evaluate(SCENE,['레헬른 악몽의 시계탑 <하드>','제트루','belt',True])
    try: pg.wait_for_function("S.characters[0].drops['lucid|belt']",timeout=15000)
    except Exception: print('DBG',pg.evaluate("JSON.stringify({sc:window.AR.scores,f:window.AR.found,det:window.AR.det,cand:(window.arCandidates?arCandidates().map(c=>c.k||c):null)})")[:600])
    st=pg.evaluate("({d0:S.characters[0].drops,d1:S.characters[1].drops,act:S.activeId,t:document.querySelector('#arToast')?.textContent,sc:window.AR.lastScore})")
    check('몽환의 벨트 → 제트루·루시드 자동 기록 (같은 저장 키)', st['d0'].get('lucid|belt')==1 and not st['d1'] and st['act']=='c0', st)
    check('토스트', '자동 기록: 몽환의 벨트 · 루시드' in (st['t'] or ''), st['t'])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)  # (가격 창이 뜨면 닫기)
    if SD: pg.screenshot(path=os.path.join(SD,'connected_toast.png'))
    pg.wait_for_timeout(1500); check('중복 기록 안 됨(계속 보여도 1번)', pg.evaluate("S.characters[0].drops['lucid|belt']")==1)
    pg.click('#arToast .ar-undo'); pg.wait_for_timeout(300)
    check('취소 = 기록 지움', not pg.evaluate("S.characters[0].drops['lucid|belt']"))
    pg.wait_for_timeout(1500); check('취소 뒤 중복막기 시간 안엔 다시 안 기록', not pg.evaluate("S.characters[0].drops['lucid|belt']"))
    check('다른 아이콘(윌 마도서)은 루시드 맵에선 후보 아님', 'book' not in [k for k,_ in pg.evaluate("window.AR.lastScore")])
    ext=[u for u in reqs if u.startswith('http') and '127.0.0.1' not in u and not any(h in u for h in ('fonts.googleapis','fonts.gstatic','accounts.google.com','ggoolzip-sync.bossmaple.workers.dev','nexon'))]
    check('프레임을 밖으로 안 보냄(큰 업로드·새 외부 요청 없음, OCR은 ./ocr 자체 호스팅)', not big and not ext and not any(('tesseract' in u or 'traineddata' in u) and '127.0.0.1' not in u for u in reqs), (big,ext))
    pg.click('#arPanel [data-ar=stop]'); check('연결 종료', not pg.evaluate("!!window.AR.stream"))
    check('JS 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
