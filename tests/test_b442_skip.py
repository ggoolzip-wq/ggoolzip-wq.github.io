"""b442 (t708u): 자쿰·피에르·반반·블러디퀸·벨룸·매그너스·파풀라투스 7종은 보상 맵 자동 인식에서 제외 (인식기만, 보스 목록·드롭표는 그대로)."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
SK=['zakum','pierre','vonbon','queen','vellum','magnus','papulatus']
T="""(SK)=>{ const r={};
 r.inBosses=SK.every(id=>!!findBoss(id)); r.drops=SK.filter(id=>{ const b=findBoss(id); return b&&b.diffs.some(d=>dropsFor(b,d).length); }).length;
 const mk=en=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:en(b.id),party:1,diff:b.diffs[b.diffs.length-1]}; return {id:'c0',name:'시험',level:280,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},mdate:{},auto:{},drops:{},sync:{}}; };
 S.characters=[mk(id=>SK.includes(id))]; S.activeId='c0'; ARX.det={cid:'c0',boss:'',diff:'',src:''}; ARX.cfg.boss='';
 const lv=window.arLive; window.arLive=()=>false;
 r.candSkipOnly=arCandidates0(true).map(c=>c.k);
 S.characters=[mk(id=>SK.includes(id)||id==='jinhilla')]; r.candWithJin=[...new Set(arCandidates0(true).map(c=>c.b.id))];
 ARX.cfg.boss='zakum'; r.targetManual=arTarget()?.b?.id||''; ARX.cfg.boss='';
 ARX.cfg.mapAlias={[arNorm('엘나스 산 정상')]:{boss:'zakum',diff:''},[arNorm('욕망의 제단 시험')]:{boss:'jinhilla',diff:''}};
 r.aliasZakum=arDetectBoss('엘나스 산 정상 <카오스>'); r.aliasJin=arDetectBoss('욕망의 제단 시험 <하드>')?.boss||''; ARX.cfg.mapAlias={};
 ARX.det={cid:'c0',boss:'magnus',diff:'hard',src:''}; const before=JSON.stringify(S.characters[0].drops); const ok=window.arBoxOk; window.arBoxOk=()=>true; arRecord('tc',.9,'시험'); window.arBoxOk=ok; r.recMagnus=JSON.stringify(S.characters[0].drops)===before;
 window.arLive=lv; return r; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');pg.evaluate('localStorage.clear()');pg.reload();pg.wait_for_timeout(800)
  r=pg.evaluate(T,SK)
  check('7종은 보스 목록(다른 기능)에 그대로 있음',r['inBosses'],r)
  check('7종만 켠 캐릭터 → 인식 후보 0개',r['candSkipOnly']==[],r)
  check('진힐라 같이 켜면 후보는 진힐라만',r['candWithJin']==['jinhilla'],r)
  check('수동 보스 저장값이 자쿰이면 인식 대상 없음',r['targetManual']=='',r)
  check('맵 등록 별칭: 자쿰 → 인식 안 함, 진힐라 → 인식',r['aliasZakum'] is None and r['aliasJin']=='jinhilla',r)
  check('매그너스로 잡혀 있어도 득템 기록 안 함',r['recMagnus'],r)
  check('빌드 b442 이상',pg.evaluate("document.documentElement.dataset.build")>='b442',pg.evaluate("document.documentElement.dataset.build"))
  check('페이지 오류 없음',not errs,errs)
  b.close()
finally: srv.terminate()
print('FAILS',bad); sys.exit(1 if bad else 0)
