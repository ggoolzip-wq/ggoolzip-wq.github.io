# b412 (t489): 지나지 않은 날짜의 파티 보스 일정 = 빨간 테두리, 지난 날짜는 강조 없음.
# 가짜 일정은 로컬 페이지에만 주입. 계정 저장/서버 변경 없음.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']:
    src=os.path.join(ROOT,d)
    if os.path.isdir(src): shutil.copytree(src,os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{
  const t=dayId(Date.now());
  const add=(id,days)=>{const [Y,M,D]=id.split('-').map(Number);const dt=new Date(Date.UTC(Y,M-1,D+days));const p=n=>String(n).padStart(2,'0');return `${dt.getUTCFullYear()}-${p(dt.getUTCMonth()+1)}-${p(dt.getUTCDate())}`;};
  const past=add(t,-2), fut=add(t,3), memo=add(t,1);
  const boss=()=>({cids:['c0'],ns:['테스트'],slot:'lucid',boss:'lucid',d:'hard',p:2,h:20,mi:0,at:1});
  S.characters=[{id:'c0',name:'테스트',level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}}];
  S.activeId='c0';
  S.calNotes={[past]:{b:{x:boss()}},[t]:{b:{x:boss()}},[fut]:{b:{x:boss()}},[memo]:{m:{a:{t:'메모',at:1}}}};
  calMon=t.slice(0,7); calSel=null; calDef=1; tab='cal'; save(); renderCal();
  return {past,today:t,future:fut,memo};
}"""
MEAS="""(ids)=>{
  const one=el=>{const c=getComputedStyle(el);return {cls:el.className,border:c.borderTopColor,shadow:c.boxShadow,w:c.borderTopWidth};};
  const out={};
  for(const [k,id] of Object.entries(ids)){const el=document.querySelector(`[data-calday="${id}"]`); out[k]=el?one(el):null;}
  return out;
}"""
RED={'dark':'rgb(255, 59, 107)','light':'rgb(224, 20, 76)'}
MEMO={'dark':'rgb(62, 224, 138)','light':'rgb(15, 157, 88)'}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for th in ('dark','light'):
      pg=b.new_page(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark' if th=='dark' else 'light',timezone_id='Asia/Seoul')
      pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
      pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(700)
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'")
      ids=pg.evaluate(SETUP); pg.wait_for_timeout(300)
      m=pg.evaluate(MEAS, ids)
      check(th+' 미래 파티 일정 칸에 cbB 클래스', 'cbB' in (m['future'] or {}).get('cls',''), m['future'])
      check(th+' 미래 파티 일정 = 빨간 테두리', (m['future'] or {}).get('border')==RED[th], m['future'])
      check(th+' 오늘 파티 일정 칸에 today cbB', 'today' in (m['today'] or {}).get('cls','') and 'cbB' in (m['today'] or {}).get('cls',''), m['today'])
      check(th+' 오늘 파티 일정 = 빨간 테두리(날짜 숫자는 오늘 분홍 유지)', (m['today'] or {}).get('border')==RED[th], m['today'])
      check(th+' 지난 파티 일정 = 빨간 테두리 없음', (m['past'] or {}).get('border') not in (RED[th], MEMO[th]) and 'past' in (m['past'] or {}).get('cls',''), m['past'])
      check(th+' 미래 메모만 = 초록 테두리(기존 동작 유지)', (m['memo'] or {}).get('border')==MEMO[th], m['memo'])
      pg.locator('.calgrid').screenshot(path=os.path.join(OUT,f'b412_{th}_grid.png'))
      pg.close()
    check('페이지 오류 없음', not errs, errs)
    # 빌드 마커
    pg=b.new_page(); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(200)
    build=pg.evaluate("document.documentElement.dataset.build")
    check('dataset.build=b412', build=='b412', build)
    pg.close(); b.close()
finally:
  srv.terminate(); shutil.rmtree(site, ignore_errors=True)
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
