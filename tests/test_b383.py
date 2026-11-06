# b383 (t425): 에픽빔 ECB1 실제 총 용량 예산 초과 시 중앙 크롭·WebP 품질·fps 순 낮춤, 기존 JPEG ECB1 호환
import os,sys,tempfile,shutil,base64
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or '/workspace/b382';os.makedirs(OUT,exist_ok=True)
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']:shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr','fonts']:shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site)
fails=[];errs=[]
def check(n,c,d=''):
 print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
 if not c:fails.append(n)
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL9WQAAAABJRU5ErkJggg=='
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
  pg=b.new_page(viewport={'width':1440,'height':1000},locale='ko-KR',timezone_id='Asia/Seoul');pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:print('CONSOLE',m.text) if m.text.startswith('DBG') else None)
  # 네트워크가 아니라 <img> 망가질 때 한 글자 이니셜이 보이게: 실제 같은 CSS 가로 고정
  pg.route('**/testavatar',lambda r:r.abort())
  pg.goto(f'http://127.0.0.1:{PORT}/index.html');pg.evaluate('localStorage.clear()');pg.reload();pg.wait_for_timeout(700)
  # 실제 사용자 사례 상태(더스크 카오스 전투 맵 + 상자 추정 상태)
  r=pg.evaluate("""()=>{ const now=Date.now(); ARX.det={boss:'dusk',diff:'chaos',cid:'c0'}; ARX.mapSt={boss:'dusk',kind:'b',t:now}; ARX.rew={boss:'dusk'}; return {ctx:ecCtx(now),battle:arRewMap(now)?.kind,state:arBossState()}; }""")
  check('전투 맵 60초 + ARX.rew 상태라도 에픽빔 저장 게이트 닫힘',r['ctx'] is None and r['battle']=='b',r)
  r=pg.evaluate("""()=>{ const now=Date.now(); ARX.mapSt={boss:'dusk',kind:'r',t:now}; const ok=ecCtx(now); ARX.mapSt.t=now-9000; return {ok,old:ecCtx(now)}; }""")
  check('실제 보상 맵 + 8초 내 = 저장 허용 / 오래되면 닫힘',r['ok']['boss']=='dusk' and r['old'] is None,r)
  check('저장 소스 8fps·최대 540p WebP·용량 제한·감지 240p 분리', pg.evaluate("EC.cfg.fps===8&&EC.cfg.H===540&&EC.cfg.H0===240&&EC.cfg.q===.75&&EC.cfg.maxBytes===800000"))
  pg.evaluate("""async()=>{const src=document.createElement('canvas');src.width=1920;src.height=1080;src.videoWidth=1920;src.videoHeight=1080;src.currentTime=1; const g=src.getContext('2d');g.fillStyle='#263b65';g.fillRect(0,0,1920,1080);for(let i=0;i<100;i++){g.fillStyle=`hsl(${i*37%360} 80% 55%)`;g.fillText('선명한 글자',i%10*150,(i/10|0)*70+50);}ARX.testSrc=src;ARX.video=src;clearInterval(EC.timer); /* 10fps 구버전 */EC.cfg.fps=10;EC.cfg.H0=240;EC.cfg.H=240;EC.cfg.q=.72;const oldtick=()=>{const now=Date.now().toString(); /* 실제 구버전 JPEG 크기 대표 프레임도 직접 인코딩 */return new Promise(ok=>{const c=document.createElement('canvas');c.width=427;c.height=240;c.getContext('2d').drawImage(src,0,0,427,240);c.toBlob(b=>ok(b),'image/jpeg',.72);});};window.oldblob=await oldtick();ARX.stream=null;ARX.video=src;ecTick();EC.buf=[];EC.h=[];EC.log=[];EC.cur=null;EC.cfg.maxBytes=800000;EC.cfg.fps=8;EC.cfg.H=540;EC.cfg.q=.75;ARX.det={boss:'dusk',diff:'chaos'};ecTick();window.newblob=await EC.buf[0].p;window.capture=[EC.cv.width,EC.cv.height,newblob.type,newblob.size,oldblob.size];}""")
  cap=pg.evaluate('capture'); print('캡처 크기',cap); 
  check('같은 입력 실제 캡처: 540p 원본 그대로 WebP',cap[:3]==[960,540,'image/webp'],cap)
  packed=pg.evaluate("async()=>{const F={ts:[0],vt:[1],f:[newblob]};return ecUnpack(await (await ecPack(F)).arrayBuffer()).f[0].type}")
  check('WebP ECB1 왕복',packed=='image/webp',packed)
  # 캐릭터 이미지 URL 이 유효해도 lazy 이미지가 사라져서 동그라미만 남던 부분
  pg.evaluate("""()=>{ S.characters=[{id:'c0',name:'란별자',image:'https://open.api.nexon.com/testavatar',bosses:{},weekly:{},monthly:{},drops:{},auto:{},sync:{}}]; const m={id:'t1',t0:Date.now(),boss:'star',diff:'normal',item:'se2',cid:'c0',start:-1000,end:2900,up:1,poster:null}; document.querySelector('#view').innerHTML='<div class="card ecwrap"><div class="ecgrid" style="grid-template-columns:320px">'+ecCard(m)+'</div></div>'; }""")
  pg.wait_for_timeout(500)
  check('초상화 로드 실패해도 빈 원이 아닌 닉네임 이니셜',pg.locator('.eccard .ecav .ecfb').count()==1, pg.locator('.ecl4').inner_text())
  pg.locator('.ecwrap').screenshot(path=os.path.join(OUT,'epic_avatar_after.png'))
  # 캘린더: 과거 카오스 더스크 일정·오늘 이후 일정. 배지(선홍 문구)는 그대로
  pg.evaluate("""()=>{ const now=new Date(),p=n=>String(n).padStart(2,'0'),id=d=>`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;const y=new Date(now-864e5),t=new Date(+now+864e5);S.calNotes={};S.calNotes[id(y)]={b:{'past':{cid:'c0',n:'란별자',slot:'dusk',boss:'dusk',d:'chaos',p:2,h:22,mi:0,at:1}}};S.calNotes[id(t)]={b:{'future':{cid:'c0',n:'란별자',slot:'dusk',boss:'dusk',d:'chaos',p:2,h:22,mi:0,at:1}}};calMon=id(now).slice(0,7);calSel='M:'+calMon;tab='cal';renderCal();}""")
  col=pg.evaluate("""()=>{let p=document.querySelector('.calc.past.cbB'),f=document.querySelector('.calc.cbB:not(.past)');return {pb:getComputedStyle(p).borderColor,pt:getComputedStyle(p.querySelector('.calbb')).color,fb:getComputedStyle(f).borderColor,pc:p.className}}""")
  print('캘린더 색',col)
  check('지난 보스 일정 테두리 원상복구 + 미래는 선홍',col['pb']!='rgb(255, 59, 107)' and col['fb']=='rgb(255, 59, 107)',col)
  check('지난 보스 일정 개수 선홍 문구 유지',col['pt']=='rgb(255, 59, 107)',col)
  pg.locator('.calgrid').screenshot(path=os.path.join(OUT,'calendar_after.png'))
  check('페이지 오류 없음',not errs,errs);b.close()
finally:srv.terminate()
print('RESULT','FAIL' if fails else 'OK',fails);sys.exit(1 if fails else 0)
