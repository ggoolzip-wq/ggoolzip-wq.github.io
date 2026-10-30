# test_b304 (t536): 드라이브/서버 동기화(1분마다 pull)가 다른 기기의 선택 캐릭터(activeId)로 바꾸지 않음 — 선택·테마는 이 PC 값
import os,sys,subprocess,tempfile,shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
P=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(P),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
from playwright.sync_api import sync_playwright
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox']); pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('https://**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{P}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
  pg.evaluate("""()=>{ const mk=(id,name)=>({id,name,level:285,job:'',world:'스카니아',ocid:'o'+id,accId:'',isMain:id==='c0',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
   S.characters=[mk('c0','본캐'),mk('c1','부캐')]; S.activeId='c1'; save(); render(); }""")
  for mode in ['drive','server']:
    r=pg.evaluate("""async mode=>{ S.activeId='c1'; save(); render(); const bk=backupData(true); const data=JSON.parse(JSON.stringify(bk)); data.activeId='c0'; data.characters[1].name='부캐'+mode;
      const remote={updatedAt:Date.now()+5000,withKeys:true,data}; const was=window.gdWrite; window.gdWrite=async()=>{}; window.gdBaseData=()=>bk;
      const m=mode==='server'?gdServerWins(gdPrep(bk),gdPrep(data)):gdMerge(gdPrep(bk),gdPrep(bk),gdPrep(data),{base:true,prefer:'l',conf:[]});
      gdLoad(m); window.gdWrite=was; return {id:S.activeId, name:S.characters[1].name, shown:document.querySelector('#charList .char.active, #charList .char.on, #charList .char.sel')?.dataset.id||null}; }""",mode)
    check(f'[{mode}] 다른 기기 activeId(c0)가 와도 선택 캐릭터 c1 유지 + 다른 변경(이름)은 반영',r['id']=='c1' and r['name']=='부캐'+mode and r['shown'] in ('c1',None),r)
  r=pg.evaluate("""()=>{ S.activeId='c1'; save(); const d=JSON.parse(JSON.stringify(backupData(true))); d.activeId='c0'; const w=window.gdPush; window.gdPush=()=>{}; gdApply({updatedAt:Date.now(),withKeys:true,data:d},null); window.gdPush=w; return S.activeId; }""")
  check('드라이브 데이터 통째로 불러와도 선택 유지',r=='c1',r)
  check('페이지 오류 없음',not errs,errs)
  b.close()
finally: srv.kill()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
