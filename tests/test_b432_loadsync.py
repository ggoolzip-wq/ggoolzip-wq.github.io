import _tutil  # 빈 포트·서버 정리·운영 Worker 차단
_P=_tutil.free_port()
# b432 (t578): 페이지 열 때(새로고침) 캐릭터 동기화가 '일부 캐릭터만' 안 되던 것.
# 원인: 열 때 syncAll 과 서버 불러오기(gdConnect → 다른 기기 변경이면 서버 값으로 S 통째 교체)가 동시에 돌아,
#  교체 뒤 처리된 캐릭터는 버려진 옛 객체에 쓰이고, 뒤 작업(레벨·EXP·이미지·훈장)은 '지워진 캐릭터'로 보고 전부 건너뜀.
# 시나리오: A 서버 모드 + 다른 기기가 서버에 저장(가장 흔함) · B 서버 바뀜 없음 · C 로컬 · D 넥슨 429 연속(재시도) · E 동기화 중 1분 확인(gdPull)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P)
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; OUT=os.environ.get('MBT_OUT')
fails=[]; errs=[]; R={}
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
N=int(os.environ.get('MBT_SYNC_N','12')); SV='https://sv.mock'
def run(b,name,sv=False,changed=True,q429=None,pull_mid=False,delay=0.3):
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    cnt={}; hits={'state':0,'put':0}; TS=[]
    def nx(r):
        u=r.request.url; TS.append(time.time())
        if 'character/list' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'account_list':[{'account_id':'x','character_list':[{'ocid':f'o{i}','character_name':f'캐릭{i}','world_name':'스카니아','character_class':'히어로','character_level':281} for i in range(N)]}]}))
        k=('s' if 'scheduler' in u else 'b' if 'basic' in u else 'e' if 'equipment' in u else '?')+u.split('ocid=')[-1].split('&')[0]
        cnt[k]=cnt.get(k,0)+1
        if q429 and k in q429 and cnt[k]<=q429[k]: return r.fulfill(status=429,content_type='application/json',body='{"error":{"name":"OPENAPI00007","message":"Too Many Requests"}}')
        if 'scheduler/character-state' in u:
            if 'date=' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'date':u.split('date=')[1][:10],'boss_contents':[{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','complete_flag':'false'}]}))
            return r.fulfill(status=200,content_type='application/json',body=json.dumps({'date':None,'boss_contents':[{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','complete_flag':'true'}]}))
        if 'character/basic' in u: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'character_level':281,'character_exp_rate':'77.7','character_exp':5,'character_image':'https://img.mock/new.png','world_name':'스카니아','character_class':'히어로'}))
        if 'item-equipment' in u: return r.fulfill(status=200,content_type='application/json',body='{"item_equipment":[]}')
        return r.fulfill(status=400,content_type='application/json',body='{"error":{"name":"OPENAPI00004","message":"x"}}')
    ctx.route('https://open.api.nexon.com/**',nx)
    ctx.route('https://img.mock/**',lambda r:r.fulfill(status=200,content_type='image/png',body=b''))
    ctx.add_init_script("(()=>{const f=window.fetch;window.__fx=[];window.fetch=function(u,...r){ if(String(u).includes('open.api.nexon.com')) window.__fx.push(performance.timeOrigin+performance.now()); return f.call(this,u,...r); };})()")
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(name+': '+str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(300)
    per=pg.evaluate("({...S.period})")
    old=time.time()*1000-2*3600e3
    CH=[{'id':f'c{i}','name':f'캐릭{i}','level':280,'job':'히어로','world':'스카니아','image':'https://img.mock/old.png','ocid':f'o{i}','accId':'a1','b134':1,'bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{'imgAt':old},'exp':{'rate':10.0,'exp':1,'level':280,'at':old},'medal':{'v':2,'bad':False,'where':[],'at':old}} for i in range(N)]
    ST={'version':5,'theme':'dark','activeId':'c0','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,'period':per,'updatedAt':1000,'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_dummy_key_x','main':True}],'lastSync':old}}
    srvData=json.loads(json.dumps(ST)); srvData['settings']['accounts']=[{'id':'a1','label':'본계정','main':True}]
    base=json.loads(json.dumps(srvData))
    if changed: srvData['calNotes']={'2026-11-15':{'m':{'x1':{'t':'다른 PC 메모','at':1}}}}
    st={'rev':2 if changed else 1,'upd':2000 if changed else 1000,'data':srvData}
    def svr(r):
        u=r.request.url; m=r.request.method; os.environ.get('MBT_DBG') and print('SV',m,u[len(SV):])
        H={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}
        if m=='OPTIONS': return r.fulfill(status=204,headers=H)
        if u.endswith('/api/state/meta'): return r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({'rev':st['rev'],'updatedAt':st['upd'],'savedAt':1}))
        if u.endswith('/api/state') and m=='GET':
            hits['state']+=1; time.sleep(delay)
            return r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({'rev':st['rev'],'updatedAt':st['upd'],'savedAt':1,'data':st['data']}))
        if u.endswith('/api/state') and m=='PUT':
            hits['put']+=1; bd=json.loads(r.request.post_data or '{}')
            if int(bd.get('baseRev',0))!=st['rev']: return r.fulfill(status=409,headers=H,content_type='application/json',body=json.dumps({'error':'conflict','message':'x','rev':st['rev'],'updatedAt':st['upd'],'savedAt':1,'data':st['data']}))
            st['rev']+=1; st['upd']=bd.get('updatedAt',0); st['data']=bd.get('data')
            return r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({'rev':st['rev'],'savedAt':2,'updatedAt':st['upd']}))
        if '/api/seen' in u: return r.fulfill(status=200,headers=H,content_type='application/json',body='{"ids":[]}')
        return r.fulfill(status=200,headers=H,content_type='application/json',body='{}')
    if sv: ctx.route(SV+'/**',svr)
    init={'mapleBossTracker.v1':json.dumps(ST),'mapleBossTracker.loadSyncAt':str(int(old))}
    if sv: init.update({'mapleBossTracker.syncApi':SV,'mapleBossTracker.svToken':'t'*43,'mapleBossTracker.svmeta':json.dumps({'on':True,'base':1000,'rU':1000,'rev':1}),'mapleBossTracker.svbase':json.dumps(base),'mapleBossTracker.svUser':'u1','mapleBossTracker.keyReset':'b64-2026-10-12'})
    pg.evaluate("o=>{localStorage.clear();for(const k in o) localStorage.setItem(k,o[k]);}",init)
    t0=time.time(); pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    if pull_mid:  # 동기화 도중 다른 기기 저장 + 1분 확인(gdPull) 이 도는 경우
        pg.wait_for_timeout(1200); st['rev']+=1; st['upd']+=1; st['data']=json.loads(json.dumps(st['data'])); st['data']['calNotes']={'2026-11-16':{'m':{'x2':{'t':'또 다른 메모','at':2}}}}
        pg.evaluate("()=>{ try{ gd.pulledAt=0; }catch(e){} gdPull(true); }")
    try: pg.wait_for_function("()=>typeof syncing!=='undefined'&&!syncing&&!syncBg&&(+S.settings.lastSync||0)>Date.now()-60e3",timeout=20000)
    except Exception as ex: print('wait fail',name,pg.evaluate("()=>({syncing,bg:!!syncBg,last:S.settings.lastSync,now:Date.now(),api:hasApi(),acc:JSON.stringify(S.settings.accounts).replace(/live_[^\"]*/g,'K'),n:S.characters.length,gd:gd.state,msg:gd.msg})"))
    pg.wait_for_timeout(2500)
    pg.wait_for_function("()=>!syncing&&!syncBg",timeout=60000); pg.wait_for_timeout(300)
    res=pg.evaluate("""()=>S.characters.map(c=>({id:c.id,weekly:!!c.weekly?.lucid,level:c.level,exp:c.exp?.rate,img:c.image,ok:c.sync?.ok}))""")
    notes=pg.evaluate("()=>Object.keys(S.calNotes||{}).sort()"); srvNotes=sorted((st['data'] or {}).get('calNotes',{}).keys()) if sv else []
    FX=[x/1000 for x in pg.evaluate('window.__fx||[]')]; mx=max([sum(1 for y in FX if x<=y<x+1.095) for x in FX] or [0])
    lbl=pg.evaluate("document.querySelector('#syncLbl,.synclbl')?.innerText||''")
    stale=(['(캐릭터 0명)'] if not res else [])+[x['id'] for x in res if not (x['weekly'] and x['level']==281 and x['exp']==77.7 and x['img'].endswith('new.png'))]
    print(f'[{name}] {time.time()-t0:.1f}s 미갱신 {len(stale)}/{N} {stale} 표시={lbl!r} 서버GET={hits["state"]} PUT={hits["put"]}')
    print(f'   메모(다른 기기) 이 PC={notes} 서버={srvNotes} · 넥슨 호출 {len(TS)}건 · 1.1초 최대 {mx}건')
    R[name]={'notes':notes,'srvNotes':srvNotes,'mx':mx,'ncalls':len(TS),'stale':stale,'n':N,'label':lbl,'rows':res,'calls':cnt}
    ctx.close(); return stale
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ONLY=os.environ.get('MBT_ONLY')
    if ONLY:
        run(b,ONLY,**json.loads(os.environ.get('MBT_KW','{}'))); b.close(); raise SystemExit(0)
    a=run(b,'A_서버_다른기기저장',sv=True,changed=True)
    a2=run(b,'A2_서버_다른기기저장_느린응답',sv=True,changed=True,delay=2.0)
    bb=run(b,'B_서버_변경없음',sv=True,changed=False)
    c=run(b,'C_로컬',sv=False)
    d=run(b,'D_429연속',sv=False,q429={'so1':2,'so2':2,'bo3':2,'bo4':2,'eo5':2})
    e=run(b,'E_동기화중_1분확인',sv=True,changed=False,pull_mid=True)
    for k,v in R.items():
        check(f'{k}: 모든 캐릭터 갱신(보스 클리어·레벨·EXP·이미지)', not v['stale'], v['stale'])
        check(f'{k}: 넥슨 호출 1.1초 창 ≤ 5건(넥슨 초당 한도 이내; rateGate 예약 4건 + fetch 시각 흔들림, b431도 429 때 5)', v['mx']<=5, v['mx'])
    check('A: 다른 기기 메모 이 PC·서버 모두 유지', R['A_서버_다른기기저장']['notes']==['2026-11-15'] and R['A_서버_다른기기저장']['srvNotes']==['2026-11-15'], R['A_서버_다른기기저장'])
    check('E: 동기화 중 다른 기기 메모도 서버에 유지(409 병합)', '2026-11-16' in R['E_동기화중_1분확인']['srvNotes'], R['E_동기화중_1분확인']['srvNotes'])
    b.close()
finally: srv.terminate()
if OUT: json.dump(R,open(OUT,'w'),ensure_ascii=False)
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
