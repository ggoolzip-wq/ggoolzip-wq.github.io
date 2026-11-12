# b414 (t494): 처치일 보정이 끝난 뒤에만 동기화 완료. 실계정과 같은 지난주 기록(perChar.bosses+id, wats 없음)도
# 다음 동기화에서 합계를 유지한 채 처음 완료된 날로 옮김. 가짜 스케줄러만 사용, 실제 계정·서버 변경 없음.
import os, sys, json, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:500] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']:
    src=os.path.join(ROOT,d)
    if os.path.isdir(src): shutil.copytree(src,os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

BOOT=r"""()=>{
  rateGate=async()=>{};
  window.__syncLabels=[];
  const _sl=syncLabel; syncLabel=(st)=>{ window.__syncLabels.push({st, at:Date.now(),
    hasWats:!!((((S.history||[]).find(h=>h.week===window.__days?.PREV)||{}).perChar||[])[0]||{}).wats,
    wed:null}); return _sl(st); };
  const row=(name,diff,cycle,reg,done)=>({content_name:name,difficulty:diff,cycle,list_order_no:1,registration_flag:String(!!reg),complete_flag:String(!!done)});
  const pack=(date,lucidDone,hasWeekly)=>({
    date:date+'T00:00+09:00',
    boss_contents: hasWeekly
      ? [row('루시드','hard','bossWeekly',true,lucidDone),row('윌','hard','bossWeekly',true,false)]
      : [row('검은 마법사','hard','bossMonthly',true,false)],
    weekly_boss_clear_count:lucidDone?1:0, weekly_boss_clear_limit_count:12
  });
  const TODAY=dayId(), WEEK=weekId(), PREV=dayAdd(WEEK,-7), WED=dayAdd(WEEK,-1), TUE=dayAdd(WEEK,-2);
  window.__days={TODAY,WEEK,PREV,WED,TUE};
  window.__pay={'TODAY':pack(TODAY,false,false)};
  for(let k=1;k<=7;k++){ const d=dayAdd(WEEK,-k); window.__pay[d]=pack(d,d===WED,true); }
  nx=async(path,params,key)=>{
    if(String(path).includes('character-state')){
      if(params&&params.date===TODAY){ const e=new Error('OPENAPI00004'); e.code='OPENAPI00004'; throw e; }
      const p=window.__pay[params&&params.date||'TODAY'];
      if(!p){ const e=new Error('OPENAPI00009'); e.code='OPENAPI00009'; throw e; }
      return JSON.parse(JSON.stringify(p));
    }
    if(String(path).includes('/character/list')) return {account_list:[]};
    return {};
  };
  const val=Math.floor(price(findBoss('lucid'),'hard'));
  window.__val=val;
  const c={id:'c0',name:'테스트',job:'히어로',world:'스카니아',level:285,ocid:'oc1',accId:'a1',image:'',
    bosses:{lucid:{enabled:true,diff:'hard',party:1},will:{enabled:true,diff:'hard',party:1}},
    weekly:{},monthly:{},auto:{},wat:{},drops:{},drev:{},sync:{}};
  S.characters=[c]; S.activeId='c0'; S.monthHistory=[]; S.missW=[];
  S.period={week:WEEK,day:TODAY,month:monthId()};
  S.settings=S.settings||defaultSettings(); S.settings.accounts=[{id:'a1',label:'테스트',key:'test-key'}];
  // 실계정과 같은 형태: 지난주 기록에 perChar.id·bosses·bvals 는 있고 wats 는 없음 → 캘린더는 목요일 합산
  S.history=[{week:PREV,weeklyOnly:true,total:val,cleared:1,crystals:1,items:0,
    perChar:[{id:'c0',name:'테스트',job:'히어로',world:'스카니아',meso:val,count:1,bosses:['루시드(하드)'],bvals:[val],items:{},outcomes:{}}]}];
  try{ localStorage.removeItem('mapleBossTracker.cal'); }catch(e){}
  if(typeof schedDateCache==='object') for(const k of Object.keys(schedDateCache)) delete schedDateCache[k];
  if(typeof schedCatchAt==='object') for(const k of Object.keys(schedCatchAt)) delete schedCatchAt[k];
  if(typeof lbCache==='object') for(const k of Object.keys(lbCache)) delete lbCache[k];
  calTick(); tab='cal'; calMon=PREV.slice(0,7); calSel=PREV; calDef=1; render();
  return {TODAY,WEEK,PREV,WED,TUE,val};
}"""

try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul')
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(800)
    days=pg.evaluate(BOOT)
    print('DAYS',json.dumps(days,ensure_ascii=False))
    before=pg.evaluate("""()=>{
      const R=calRecs(calLoad()), D=window.__days;
      return {thu:R.filter(r=>r.day===D.PREV&&r.id==='c0').reduce((s,r)=>s+r.m,0),
              wed:R.filter(r=>r.day===D.WED&&r.id==='c0').reduce((s,r)=>s+r.m,0),
              wats:(((S.history.find(h=>h.week===D.PREV)||{}).perChar||[])[0]||{}).wats||null};
    }""")
    print('BEFORE',before)
    check('보정 전: 지난주 기록에 wats 없고 목요일 합산', before.get('thu',0)>0 and before.get('wed',0)==0 and not before.get('wats'), before)
    try: pg.locator('.calgrid').screenshot(path=os.path.join(OUT,'b414_before.png'))
    except Exception: pg.screenshot(path=os.path.join(OUT,'b414_before.png'))

    after=pg.evaluate("""async ()=>{
      window.__syncLabels=[];
      await syncAll({silent:true});
      calTick(); tab='cal'; calMon=window.__days.PREV.slice(0,7); calSel=window.__days.WED; render();
      const R=calRecs(calLoad()), D=window.__days;
      const h=(S.history||[]).find(x=>x.week===D.PREV);
      const pc=(h.perChar||[]).find(x=>x.id==='c0');
      const labels=window.__syncLabels.map(x=>({st:x.st,hasWats:x.hasWats}));
      return {labels,
        thu:R.filter(r=>r.day===D.PREV&&r.id==='c0').reduce((s,r)=>s+r.m,0),
        wed:R.filter(r=>r.day===D.WED&&r.id==='c0').reduce((s,r)=>s+r.m,0),
        today:R.filter(r=>r.day===D.TODAY&&r.id==='c0'&&String(r.bs||'').startsWith('루시드(')).reduce((s,r)=>s+r.m,0),
        total:h&&h.total, count:pc&&pc.count, lucidN:(pc.bosses||[]).filter(t=>String(t).startsWith('루시드(')).length,
        wats:pc&&pc.wats, thisWeek:!!S.characters[0].weekly.lucid, lastSync:S.settings.lastSync};
    }""")
    print('AFTER',json.dumps(after,ensure_ascii=False,default=str)[:2000])
    ok_labels=[x for x in (after.get('labels') or []) if x.get('st') in ('ok','part')]
    check('완료 표시 시점에 이미 wats 가 있음', ok_labels and all(x.get('hasWats') for x in ok_labels), after.get('labels'))
    check('보정 후: 수요일로 이동, 목요일·오늘은 0', after.get('wed',0)>0 and after.get('thu',0)==0 and after.get('today',0)==0, after)
    check('합계·보스 수 유지, 이번 주 미포함', after.get('total')==days['val'] and after.get('lucidN')==1 and after.get('thisWeek') is False, after)
    try: pg.locator('.calgrid').screenshot(path=os.path.join(OUT,'b414_after.png'))
    except Exception: pg.screenshot(path=os.path.join(OUT,'b414_after.png'))

    again=pg.evaluate("""async ()=>{
      const D=window.__days, before=((S.history.find(h=>h.week===D.PREV)||{}).total);
      await syncAll({silent:true});
      const h=S.history.find(x=>x.week===D.PREV);
      const pc=(h.perChar||[]).find(x=>x.id==='c0');
      const R=calRecs(calLoad());
      return {before,after:h.total,n:(pc.bosses||[]).length,wed:R.filter(r=>r.day===D.WED&&r.id==='c0').reduce((s,r)=>s+r.m,0),thisWeek:!!S.characters[0].weekly.lucid};
    }""")
    print('AGAIN',again)
    check('재동기화해도 합계·수요일 유지, 이중 계산 없음', again.get('before')==again.get('after') and again.get('n')==1 and again.get('wed',0)>0 and again.get('thisWeek') is False, again)

    build=pg.evaluate("document.documentElement.dataset.build")
    check('dataset.build=b414', build=='b414', build)
    check('페이지 오류 없음', not errs, errs)
    pg.close(); b.close()
finally:
  srv.terminate(); shutil.rmtree(site, ignore_errors=True)
print('RESULT','FAIL' if fails else 'OK',len(fails))
sys.exit(1 if fails else 0)
