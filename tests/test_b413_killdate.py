# b413 (t492): 동기화를 나중에 해도 주간 보스 처치를 잡은 날로 귀속.
# 수요일 처치 → 목요일(주 리셋 후) 동기화 시 지난주 목요일이 아니라 수요일에 합산.
# 가짜 스케줄러 응답만 사용. 실제 계정·서버 데이터 변경 없음.
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

BOOT="""()=>{
  rateGate=async()=>{};
  const row=(name,diff,cycle,reg,done)=>({content_name:name,difficulty:diff,cycle,list_order_no:1,registration_flag:String(!!reg),complete_flag:String(!!done)});
  const pack=(date,lucidDone,hasWeekly,bmDone)=>{
    const rows=[];
    if(hasWeekly){ rows.push(row('루시드','hard','bossWeekly',true,lucidDone)); rows.push(row('윌','hard','bossWeekly',true,false)); }
    rows.push(row('검은 마법사','hard','bossMonthly',true,!!bmDone));
    return {date:date+'T00:00+09:00',boss_contents:rows,weekly_boss_clear_count:lucidDone?1:0,weekly_boss_clear_limit_count:12,character_level:285,world_name:'스카니아',character_class:'히어로'};
  };
  const TODAY=dayId(), WEEK=weekId(), PREV=dayAdd(WEEK,-7), WED=dayAdd(WEEK,-1), TUE=dayAdd(WEEK,-2);
  window.__days={TODAY,WEEK,PREV,WED,TUE};
  window.__pay={'TODAY':pack(TODAY,false,false,true)};
  for(let k=1;k<=7;k++){ const d=dayAdd(WEEK,-k); window.__pay[d]=pack(d,d>=WED,true,true); }
  window.__pay[TUE]=pack(TUE,false,true,true);
  for(let k=3;k<=7;k++){ const d=dayAdd(WEEK,-k); window.__pay[d]=pack(d,false,true,true); }
  window.__calls=[];
  nx=async(path,params,key)=>{
    window.__calls.push({path,date:params&&params.date||null});
    if(String(path).includes('character-state')){
      if(params&&params.date===TODAY){ const e=new Error('OPENAPI00004'); e.code='OPENAPI00004'; throw e; }
      const p=window.__pay[params&&params.date||'TODAY'];
      if(!p){ const e=new Error('OPENAPI00009'); e.code='OPENAPI00009'; throw e; }
      return JSON.parse(JSON.stringify(p));
    }
    return {};
  };
  const c={id:'c0',name:'테스트',job:'히어로',world:'스카니아',level:285,ocid:'oc1',accId:'a1',image:'',
    bosses:{lucid:{enabled:true,diff:'hard',party:1},will:{enabled:true,diff:'hard',party:1},blackmage:{enabled:true,diff:'hard',party:1}},
    weekly:{},monthly:{blackmage:WEEK},mdate:{blackmage:TODAY},auto:{},wat:{},drops:{},drev:{},mdrops:{},mdrev:{},sync:{}};
  S.characters=[c]; S.activeId='c0'; S.history=[]; S.missW=[]; S.monthHistory=[];
  S.period={week:WEEK,day:TODAY,month:monthId()};
  S.settings=S.settings||defaultSettings(); S.settings.accounts=[{id:'a1',label:'테스트',key:'test-key'}];
  try{ localStorage.removeItem('mapleBossTracker.cal'); }catch(e){}
  if(typeof schedDateCache==='object'){ for(const k of Object.keys(schedDateCache)) delete schedDateCache[k]; }
  if(typeof schedCatchAt==='object'){ for(const k of Object.keys(schedCatchAt)) delete schedCatchAt[k]; }
  if(typeof lbCache==='object'){ for(const k of Object.keys(lbCache)) delete lbCache[k]; }
  return window.__days;
}"""

def shot(pg,name):
    try: pg.locator('#calView, .calgrid, [data-tab="cal"], body').first.screenshot(path=os.path.join(OUT,name))
    except Exception:
        pg.screenshot(path=os.path.join(OUT,name))

try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul')
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(800)
    days=pg.evaluate(BOOT)
    print('DAYS',json.dumps(days,ensure_ascii=False))
    check('오늘은 KST 목요일(주 시작일)', days.get('TODAY')==days.get('WEEK') and days.get('TODAY')=='2026-11-12', days)
    check('어제=수요일 2026-11-11, 지난주 시작=2026-11-05', days.get('WED')=='2026-11-11' and days.get('PREV')=='2026-11-05', days)

    # --- A: 목 리셋 뒤 늦은 동기화, 지난주 기록에 루시드가 없음 ---
    a=pg.evaluate("""async ()=>{
      const a=accOf(S.characters[0]);
      const n=await schedApply(S.characters[0],a);
      calTick(); tab='cal'; calMon=(window.__days.PREV||'').slice(0,7); calSel=window.__days.WED; calDef=1; render();
      const h=(S.history||[]).find(x=>x.week===window.__days.PREV)||null;
      const pc=h&&(h.perChar||[]).find(x=>x.id==='c0');
      const R=calRecs(calLoad());
      const lucidDays=R.filter(r=>r.id==='c0'&&String(r.bs||'').startsWith('루시드(')).map(r=>({day:r.day,m:r.m,ap:!!r.ap}));
      const thu=R.filter(r=>r.day===window.__days.PREV&&r.id==='c0').reduce((s,r)=>s+r.m,0);
      const wed=R.filter(r=>r.day===window.__days.WED&&r.id==='c0').reduce((s,r)=>s+r.m,0);
      const today=R.filter(r=>r.day===window.__days.TODAY&&r.id==='c0'&&String(r.bs||'').startsWith('루시드(')).reduce((s,r)=>s+r.m,0);
      return {n, weekly:S.characters[0].weekly, wat:S.characters[0].wat||{},
        histWeek:h&&h.week, bosses:pc&&pc.bosses, bvals:pc&&pc.bvals, wats:pc&&pc.wats,
        total:h&&h.total, cleared:h&&h.cleared, lucidDays, thu, wed, todayLucid:today,
        thisWeekLucid:!!S.characters[0].weekly.lucid,
        calls:window.__calls.filter(x=>String(x.path).includes('character-state')).map(x=>x.date),
        monthly:S.characters[0].monthly, mdrev:S.characters[0].mdrev||{}, drev:S.characters[0].drev||{}};
    }""")
    print('A',json.dumps(a,ensure_ascii=False,default=str)[:2000])
    check('A 이번 주 weekly.lucid 는 켜지지 않음(지난주 처치)', a.get('thisWeekLucid') is False, a.get('weekly'))
    check('A 지난주 기록에 루시드가 추가됨', bool(a.get('bosses') and any(str(x).startswith('루시드(') for x in a['bosses'])), a.get('bosses'))
    wats=a.get('wats') or {}
    wed_ts=wats.get('lucid')
    wed_day=None
    if wed_ts:
        # evaluate dayId in page
        wed_day=pg.evaluate('t=>dayId(t)', wed_ts)
    check('A 처치일이 수요일 2026-11-11', wed_day==days['WED'], {'wats':wats,'day':wed_day})
    check('A 캘린더 수요일에 루시드 수익', a.get('wed',0)>0, a.get('wed'))
    check('A 캘린더 지난주 목요일에 루시드 수익 없음', a.get('thu',0)==0, a.get('thu'))
    check('A 캘린더 오늘(이번주 목)에 루시드 수익 없음', a.get('todayLucid',0)==0, a.get('todayLucid'))
    check('A 월간 검마·아이템 수익 맵은 그대로(추가 변경 없음)', a.get('monthly',{}).get('blackmage')==days['WEEK'] and a.get('drev')=={} , a)
    # today date must never be requested
    check('A 오늘 date 파라미터 호출 없음', days['TODAY'] not in (a.get('calls') or []), a.get('calls'))
    check('A 일별 조회가 7일을 넘지 않음', len(set(x for x in (a.get('calls') or []) if x))<=7, a.get('calls'))
    pg.wait_for_timeout(400)
    try:
        pg.locator('.calgrid').screenshot(path=os.path.join(OUT,'b413_after_wed_clear.png'))
    except Exception as e:
        pg.screenshot(path=os.path.join(OUT,'b413_after_wed_clear.png'))
        print('grid shot fallback', e)

    # --- B: 이미 지난주 기록에 날짜 없이 들어 있음(목요일 합산) → 날짜만 수요일로 ---
    bres=pg.evaluate("""async ()=>{
      for(const k of Object.keys(schedDateCache||{})) delete schedDateCache[k];
      for(const k of Object.keys(schedCatchAt||{})) delete schedCatchAt[k];
      for(const k of Object.keys(lbCache||{})) delete lbCache[k];
      window.__calls=[];
      const PREV=window.__days.PREV, WED=window.__days.WED, val=Math.floor(price(findBoss('lucid'),'hard'));
      S.history=[{week:PREV,weeklyOnly:true,total:val,cleared:1,crystals:1,items:0,perChar:[{id:'c0',name:'테스트',job:'히어로',world:'스카니아',meso:val,count:1,bosses:['루시드(하드)'],bvals:[val],items:{},outcomes:{}}]}];
      S.characters[0].weekly={}; S.characters[0].wat={};
      try{ localStorage.removeItem('mapleBossTracker.cal'); }catch(e){}
      calTick();
      const before=calRecs(calLoad());
      const beforeThu=before.filter(r=>r.day===PREV&&r.id==='c0').reduce((s,r)=>s+r.m,0);
      const beforeWed=before.filter(r=>r.day===WED&&r.id==='c0').reduce((s,r)=>s+r.m,0);
      await schedApply(S.characters[0],accOf(S.characters[0]));
      calTick(); tab='cal'; calMon=PREV.slice(0,7); calSel=WED; render();
      const h=(S.history||[]).find(x=>x.week===PREV);
      const pc=h&&(h.perChar||[]).find(x=>x.id==='c0');
      const after=calRecs(calLoad());
      return {beforeThu,beforeWed,afterThu:after.filter(r=>r.day===PREV&&r.id==='c0').reduce((s,r)=>s+r.m,0),
        afterWed:after.filter(r=>r.day===WED&&r.id==='c0').reduce((s,r)=>s+r.m,0),
        bosses:pc&&pc.bosses, count:pc&&pc.count, total:h&&h.total, wats:pc&&pc.wats,
        thisWeekLucid:!!S.characters[0].weekly.lucid, lucidCount:(pc&&pc.bosses||[]).filter(t=>String(t).startsWith('루시드(')).length};
    }""")
    print('B',json.dumps(bres,ensure_ascii=False,default=str)[:2000])
    check('B 수정 전: 날짜 없는 지난주 처치는 목요일에 합산', bres.get('beforeThu',0)>0 and bres.get('beforeWed',0)==0, bres)
    check('B 수정 후: 수요일로 옮겨지고 목요일 합계는 0', bres.get('afterWed',0)>0 and bres.get('afterThu',0)==0, bres)
    check('B 합계·보스 수는 그대로(이중 계산 없음)', bres.get('lucidCount')==1 and bres.get('count')==1, bres)
    check('B 이번 주에는 안 들어감', bres.get('thisWeekLucid') is False, bres)
    try:
        pg.locator('.calgrid').screenshot(path=os.path.join(OUT,'b413_moved_from_thu_to_wed.png'))
    except Exception:
        pg.screenshot(path=os.path.join(OUT,'b413_moved_from_thu_to_wed.png'))

    # --- C: 같은 주 안에서 늦게 동기화(수요일에 동기화, 월요일 처치) ---
    cres=pg.evaluate("""async ()=>{
      for(const k of Object.keys(schedDateCache||{})) delete schedDateCache[k];
      for(const k of Object.keys(schedCatchAt||{})) delete schedCatchAt[k];
      for(const k of Object.keys(lbCache||{})) delete lbCache[k];
      const WEEK=window.__days.PREV, MON=dayAdd(WEEK,4), TUE=dayAdd(WEEK,5), WED=window.__days.WED; // 주 목=PREV, 월=+4
      window.__pay['TODAY']=window.__pay[WED]||window.__pay['TODAY'];
      // force mid-week period
      const keepPeriod={...S.period}; S.period={week:WEEK,day:WED,month:keepPeriod.month};
      const realToday=dayId();
      // schedClearDays only, because today is actually Thursday in the real clock
      const map=await schedClearDays(S.characters[0],accOf(S.characters[0]),['lucid'],WED,WEEK);
      S.period=keepPeriod;
      return {map, MON, TUE, WED, WEEK, lucidDay:map.lucid};
    }""")
    print('C',json.dumps(cres,ensure_ascii=False,default=str)[:2000])
    # In our pay: WED complete, TUE incomplete → first complete day is WED.
    # Wait, I wanted Monday kill. Need MON complete, Sunday not.
    # Recheck: I set pay[d>=WED] complete then overwrote TUE and k=3..7 as incomplete.
    # So only WED is complete in last week. schedClearDays(end=WED, start=PREV) → walk TUE (not done) → lucidDay=WED.
    # That's "complete as of Wednesday, not complete Tuesday" = Wednesday kill. Good mid-week dating test:
    # If someone synced on Wednesday for a Wednesday kill, day=Wednesday not week-start Thursday.
    check('C 일별 조회로 처음 완료일이 수요일(화요일은 미완료)', cres.get('lucidDay')==days['WED'], cres)
    check('C 주 시작 목요일로 떨어지지 않음', cres.get('lucidDay')!=days['PREV'], cres)

    # more precise Mon-kill walk: mark Mon-Wed complete, Sun incomplete
    dres=pg.evaluate("""async ()=>{
      for(const k of Object.keys(schedDateCache||{})) delete schedDateCache[k];
      const WEEK=window.__days.PREV, MON=dayAdd(WEEK,4), SUN=dayAdd(WEEK,3), WED=window.__days.WED;
      const row=(name,diff,cycle,reg,done)=>({content_name:name,difficulty:diff,cycle,list_order_no:1,registration_flag:String(!!reg),complete_flag:String(!!done)});
      const pack=(date,done)=>({date:date+'T00:00+09:00',boss_contents:[row('루시드','hard','bossWeekly',true,done),row('윌','hard','bossWeekly',true,false),row('검은 마법사','hard','bossMonthly',true,true)],weekly_boss_clear_count:done?1:0,weekly_boss_clear_limit_count:12});
      for(let k=0;k<=6;k++){ const d=dayAdd(WEEK,k); window.__pay[d]=pack(d,d>=MON&&d<=WED); }
      const map=await schedClearDays(S.characters[0],accOf(S.characters[0]),['lucid'],WED,WEEK);
      return {map,MON,SUN,WED,WEEK};
    }""")
    print('D',json.dumps(dres,ensure_ascii=False,default=str)[:2000])
    check('D 월요일 처치·수요일 조회 = 월요일로 귀속', dres.get('map',{}).get('lucid')==dres.get('MON'), dres)

    # --- E: 다시 동기화해도 이중 합산 없음 ---
    eres=pg.evaluate("""async ()=>{
      for(const k of Object.keys(schedCatchAt||{})) delete schedCatchAt[k];
      for(const k of Object.keys(schedDateCache||{})) delete schedDateCache[k];
      for(const k of Object.keys(lbCache||{})) delete lbCache[k];
      window.__pay['TODAY']={date:window.__days.TODAY+'T00:00+09:00',boss_contents:[{content_name:'검은 마법사',difficulty:'hard',cycle:'bossMonthly',list_order_no:52,registration_flag:'true',complete_flag:'true'}],weekly_boss_clear_count:0,weekly_boss_clear_limit_count:12};
      // restore wed-only complete in last week
      const WEEK=window.__days.WEEK, WED=window.__days.WED, PREV=window.__days.PREV;
      const row=(name,diff,cycle,reg,done)=>({content_name:name,difficulty:diff,cycle,list_order_no:1,registration_flag:String(!!reg),complete_flag:String(!!done)});
      const pack=(date,done)=>({date:date+'T00:00+09:00',boss_contents:[row('루시드','hard','bossWeekly',true,done),row('윌','hard','bossWeekly',true,false),row('검은 마법사','hard','bossMonthly',true,true)],weekly_boss_clear_count:done?1:0,weekly_boss_clear_limit_count:12});
      for(let k=1;k<=7;k++){ const d=dayAdd(WEEK,-k); window.__pay[d]=pack(d,d===WED); }
      const before=(S.history.find(h=>h.week===PREV)||{}).total;
      const beforeN=((S.history.find(h=>h.week===PREV)||{}).perChar||[]).find(p=>p.id==='c0')?.bosses?.length;
      await schedApply(S.characters[0],accOf(S.characters[0]));
      const h=S.history.find(x=>x.week===PREV);
      const pc=(h.perChar||[]).find(x=>x.id==='c0');
      return {before,after:h.total,beforeN,afterN:(pc.bosses||[]).length,lucidN:(pc.bosses||[]).filter(t=>String(t).startsWith('루시드(')).length,thisWeek:!!S.characters[0].weekly.lucid};
    }""")
    print('E',json.dumps(eres,ensure_ascii=False,default=str)[:2000])
    check('E 재동기화해도 지난주 합계·보스 수 불변', eres.get('before')==eres.get('after') and eres.get('beforeN')==eres.get('afterN') and eres.get('lucidN')==1, eres)
    check('E 재동기화해도 이번 주에 안 들어감', eres.get('thisWeek') is False, eres)

    build=pg.evaluate("document.documentElement.dataset.build")
    check('dataset.build>=b413', (lambda b: b and b.startswith('b') and int(b[1:] or 0)>=413)(build), build)
    check('페이지 오류 없음', not errs, errs)
    pg.close(); b.close()
finally:
  srv.terminate(); shutil.rmtree(site, ignore_errors=True)
print('RESULT','FAIL' if fails else 'OK',len(fails))
sys.exit(1 if fails else 0)
