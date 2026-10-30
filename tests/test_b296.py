# test_b296: (1) 자동 기록 탭 상태 줄 = '● 연결됨' 만 (fps·놓친 프레임 디버그 줄 없음)
#            (2) 이름 감시 장시간(가상 시계 15분): 캐릭터 3번 바꿈 · OCR 못 읽는 구간 11분 · OCR 멈춤(응답 없음) 여러 번
#                → 멈춰도 시간 초과로 풀리고 워커 새로 띄움 · 상태바가 그대로면 마지막 이름 유지(인식 중… 안 뜸) · 바뀌면 다시 인식
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
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name,lv)=>({id,name,level:lv,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','트딕이',285),C('c1','팬더데이',285),C('c2','터래플',289)]; S.activeId='c0'; save&&save(); render(); }"""
SIM="""async ()=>{ const A=window.AR; A.cfg.on=false; A.cfg.ocrTimeout=300;
  const NM={c0:'Lv.285 트딕이',c1:'Lv.285 팬더데이',c2:'Lv.289 터래플'}; let T=1e9, cur='c0', mode='ok', calls=0, hangs=0, made=0, maxBusy=0, busySince=0;
  const realNow=Date.now; Date.now=()=>T;
  const mk=()=>{ made++; return {recognize:()=>{ calls++; if(mode==='hang'||(mode==='hang3'&&calls%3===0)){ hangs++; return new Promise(()=>{}); }
      return Promise.resolve({data:{text:mode==='junk'?'':NM[cur]}}); }, terminate:()=>{}}; };
  window.Tesseract={createWorker:async()=>mk()}; A.ocrP=null; A.ocr=null; await arOcrLoad();
  const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'), n=A.cfg.name;
  const paint=()=>{ g.fillStyle='#223'; g.fillRect(0,0,1920,1080); g.fillStyle='#fff'; g.font='bold 22px sans-serif'; g.fillText(NM[cur]+' '+cur.repeat(8),n.x*1920+6,n.y*1080+n.h*1080*.8); };
  A.det.cid=''; A.cidT=0; A.nprev=null; A.nameOk=false; A.nameBusy=false; A.nTimer=1; paint();
  const log=[]; const at={}; const t0=T;
  const ev=[[0,()=>{}],[60,()=>{mode='junk';}],[400,()=>{mode='hang';}],[430,()=>{mode='junk';}],[720,()=>{mode='ok';}],[760,()=>{cur='c1';paint();mode='hang3';}],[820,()=>{mode='hang';}],[835,()=>{mode='ok';cur='c2';paint();}],[880,()=>{mode='hang3';}]];
  let ei=0; for(let s=0;s<=900*5;s++){ const sec=s/5; while(ei<ev.length&&ev[ei][0]<=sec){ ev[ei][1](); ei++; }
    arNameWatch(cv); if(A.nameBusy){ if(!busySince) busySince=T; maxBusy=Math.max(maxBusy,T-busySince); } else busySince=0;
    await new Promise(r=>setTimeout(r,mode.startsWith('hang')?2:0)); T+=200;
    if(s%5===0) log.push([sec,A.det.cid]); }
  for(const q of [59,399,429,719,759,775,834,850,900]) at[q]=(log.filter(l=>l[0]<=q).pop()||[])[1];
  const lost=log.filter(l=>l[0]>=2&&!l[1]).length;
  const firstC1=(log.find(l=>l[0]>=760&&l[1]==='c1')||[])[0], firstC2=(log.find(l=>l[0]>=835&&l[1]==='c2')||[])[0];
  A.video={}; arPanel(true); const card=document.querySelector('#arPanel .ar-cchar')?.textContent||'', sbar=document.querySelector('#arPanel .ar-sbar')?.textContent||'';
  A.video=null; Date.now=realNow; A.nTimer=0; return {at,lost,firstC1,firstC2,calls,hangs,made,ocrHang:A.ocrHang||0,maxBusy,card,sbar}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    r=pg.evaluate(SIM); print('SIM',r)
    a=r['at']
    check('처음 트딕이 인식', a['59']=='c0', a)
    check('OCR 못 읽는 11분(상태바 그대로) 동안 트딕이 유지 — 10분 지나도 안 비움', a['399']=='c0' and a['429']=='c0' and a['719']=='c0' and a['759']=='c0', a)
    check('15분 동안 이름이 빈 적 없음(인식 중… 안 뜸)', r['lost']==0, r['lost'])
    check('OCR 멈춤 → 시간 초과로 풀리고 워커 새로 띄움', r['ocrHang']>=2 and r['made']>=3 and r['maxBusy']<=8200, (r['ocrHang'],r['made'],r['maxBusy']))
    check('멈춤 섞여도 캐릭터 바꾸면 다시 인식(팬더데이 2초 안)', r['firstC1'] is not None and r['firstC1']-760<=2, r['firstC1'])
    check('멈춤 끝나고 바꾼 캐릭터(터래플) 3초 안 · 끝까지 유지', r['firstC2'] is not None and r['firstC2']-835<=3 and a['900']=='c2', (r['firstC2'],a['900']))
    check('캐릭터 카드 = 터래플 (인식 중… 아님)', '터래플' in r['card'] and '인식 중' not in r['card'], r['card'][:120])
    check("상태 줄 = '● 연결됨' 만 (fps·놓친 프레임 없음)", ('연결됨' in r['sbar'] or '끊김' in r['sbar']) and 'fps' not in r['sbar'] and '놓친' not in r['sbar'] and 'full-rate' not in r['sbar'], r['sbar'][:200])
    pg.evaluate("()=>{ const A=window.AR; A.det.cid='c0'; A.det.boss='slime'; A.det.diff='chaos'; A.runRec=[{k:'r_white',b:'가디언 엔젤 슬라임',c:'트딕이',t:'18:40'}]; document.querySelector('#tabs [data-tab=auto]').click(); }")
    pg.wait_for_timeout(400); pg.evaluate("()=>{ document.getElementById('arGuide')?.remove(); }")
    u=pg.evaluate("""()=>{ const P=document.querySelector('#arPanel'); const T=P.innerText; return {T, h2:[...P.querySelectorAll('.ar-c h2')].map(h=>h.textContent.trim()), dimg:!!P.querySelector('.ar-cboss .dimg img'), boss:P.querySelector('.ar-cboss .ar-b').innerText, setVis:!!P.querySelector('.ar-cset')?.offsetParent}; }""")
    print('UI',u['h2'],u['boss'],u['dimg'])
    check("'현재 보스' · '현재까지 기록' 제목", '현재 보스' in u['h2'] and '현재까지 기록' in u['h2'] and '인식 보스' not in u['h2'] and '이번 판 기록' not in u['h2'], u['h2'])
    u2=pg.evaluate("()=>{const e=document.querySelector('#arPanel .ar-bline');const n=e.querySelector('.ar-bn');return {nfull:n.scrollWidth<=n.clientWidth+1,ic:!!e.querySelector('.bicon'),one:e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().height<60}}")
    check('현재 보스 = 보스 아이콘 + 이름 + 난이도 1줄(긴 이름 자동 축소)', u2['ic'] and u2['one'] and u2['nfull'], u2)
    check('현재 보스 = 보스 이름 + 난이도 아이콘(드랍표와 같은 dimg) 만 · 맵 이름/아이템 인식 중 없음', '가디언 엔젤 슬라임' in u['boss'] and u['dimg'] and '라무라무' not in u['boss'] and '아이템 인식' not in u['boss'] and '맵 OCR' not in u['boss'], u['boss'])
    check("'수동 선택 · 조정 · 디버그' · '어디에도 보내지 않아요' 안 보임", not u['setVis'] and '수동 선택' not in u['T'] and '어디에도 보내지' not in u['T'], u['T'][-200:])
    pg.wait_for_timeout(300)
    sd=pg.evaluate("()=>{const n=document.querySelector('#arPanel .ar-bn');return n.scrollWidth<=n.clientWidth+1&&n.getBoundingClientRect().right<=document.querySelector('#arPanel .ar-bline').getBoundingClientRect().right+1}")
    check('스크린샷 시점에도 긴 보스 이름 안 잘림', sd, sd)
    pg.screenshot(path=os.path.join(OUT,'b296_panel_dark.png'))
    pg.evaluate("()=>{ document.documentElement.dataset.theme='light'; }"); pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(OUT,'b296_panel_light.png'))
    # b297ui: 고정 영역 · 드래그 UI 없음 · 영역 보기 라벨
    pg.evaluate("()=>{ document.documentElement.dataset.theme='dark'; localStorage.setItem('mbt_autorec',JSON.stringify({log:{x:.1,y:.1,w:.1,h:.1}})); }")
    r=pg.evaluate("""()=>{ const T=document.querySelector('#arPanel').innerText; const btn=document.querySelector('#arPanel .ar-roib'); const before=btn.textContent; btn.click();
      return {before, after:document.querySelector('#arPanel .ar-roib').textContent, drag:/드래그/.test(document.querySelector('#arPanel').innerText), regs:!!document.querySelector('#arPanel .ar-regs button'), log:JSON.stringify(window.AR.cfg.log)} }""")
    check("'영역 보기' → '영역 숨기기' 그대로, '영역: … 화면에서 드래그' UI 없음", r['before']=='영역 보기' and r['after']=='영역 숨기기' and not r['drag'] and not r['regs'], r)
    pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(OUT,'b297_roi_dark.png'))
    pg.evaluate("()=>{ document.documentElement.dataset.theme='light'; }"); pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(OUT,'b297_roi_light.png'))
    pg.evaluate("()=>document.querySelector('#arPanel .ar-roib').click()")
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
