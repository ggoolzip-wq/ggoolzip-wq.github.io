# zosu-testfix (2026-10-19): b184 동기화 뒤 작업(basic·훈장)이 넣을 때의 키를 쓰고, 그 사이 지운 캐릭터·바뀐 키로는 요청하지 않음 (src/app.js bgJob)
import _tutil
import os, sys, json, time, urllib.parse
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL='file://'+ROOT+'/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
K_OLD,K_NEW='live_mock_OLD_0123456789abcdef','live_mock_NEW_0123456789abcdef'
N=8; OC=[f'ocid-bg{i}' for i in range(N)]
calls=[]  # (t, endpoint, key, ocid)
def handle(route):
    u=urllib.parse.urlparse(route.request.url); q=dict(urllib.parse.parse_qsl(u.query)); p=u.path; k=route.request.headers.get('x-nxopen-api-key')
    ep=p.rsplit('/',1)[-1]; calls.append((time.time(),ep,k,q.get('ocid')))
    if '/static/' in p: return route.fulfill(status=404,body='')
    if k not in (K_OLD,K_NEW): return route.fulfill(status=400,json={'error':{'name':'OPENAPI00005','message':'The apikey is not valid.'}})
    if ep=='list': return route.fulfill(json={'account_list':[{'account_id':'A','character_list':[{'ocid':o,'character_name':f'캐릭{i}','world_name':'스카니아','character_class':'히어로','character_level':260} for i,o in enumerate(OC)]}]})
    if q.get('ocid') not in OC: return route.fulfill(status=400,json={'error':{'name':'OPENAPI00003','message':'Please input valid id'}})
    i=OC.index(q['ocid'])
    if ep=='basic': return route.fulfill(json={'date':'2026-10-08T00:00+09:00','character_name':f'캐릭{i}','world_name':'스카니아','character_class':'히어로','character_level':260,'character_exp_rate':'1.0','character_exp':1})
    if ep=='item-equipment': return route.fulfill(json={'preset_no':1,'item_equipment':[]})
    if ep=='character-state': return route.fulfill(json={'date':None,'boss_contents':[{'content_name':'스우','difficulty':'hard','cycle':'bossWeekly','list_order_no':1,'registration_flag':'true','complete_flag':'false'}],'weekly_boss_clear_count':0,'weekly_boss_clear_limit_count':12})
    return route.fulfill(status=400,json={'error':{'name':'OPENAPI00006','message':'invalid path'}})
def state():
    chs=[{'id':f'c{i}','name':f'캐릭{i}','level':260,'job':'히어로','world':'스카니아','ocid':o,'accId':'a1','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,o in enumerate(OC)]
    return {'version':5,'theme':'dark','activeId':'c0','characters':chs,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':K_OLD,'main':True}]}}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    def load():
        pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",state())
        pg.reload(); pg.wait_for_timeout(500); pg.wait_for_function("!syncing&&!syncBg",timeout=30000); calls.clear()
    # A) 대조군: 아무것도 안 바꾸면 뒤 작업이 넣을 때 키(OLD)로 basic·훈장 전부
    load(); pg.evaluate("syncAll({full:true})"); pg.wait_for_function("!syncing",timeout=30000)
    pg.wait_for_function("!syncBg",timeout=60000)
    bg=[c for c in calls if c[1] in ('basic','item-equipment')]
    check('A: 뒤 작업 basic·훈장 = 캐릭터 수×2, 전부 OLD 키', len(bg)==2*N and all(c[2]==K_OLD for c in bg), (len(bg),{c[2][:13] for c in bg}))
    # B) '완료'(syncing=false) 직후 뒤 작업이 남은 동안 캐릭터 6명 삭제 + 키 교체
    load(); pg.evaluate("syncAll({full:true})"); pg.wait_for_function("!syncing",timeout=30000)
    pend=pg.evaluate("!!syncBg"); t0=time.time()
    pg.evaluate(f"()=>{{S.characters=S.characters.slice(0,2); S.settings.accounts[0].key='{K_NEW}'; save(); render();}}")
    pg.wait_for_function("!syncBg",timeout=60000); pg.wait_for_timeout(300)
    after=[c for c in calls if c[0]>t0 and c[1] in ('basic','item-equipment')]
    check('B: 바꿀 때 뒤 작업이 아직 남아 있었음(테스트 전제)', pend)
    check('B: 바뀐(NEW) 키로 뒤 작업 요청 없음', not any(c[2]==K_NEW for c in after), [(c[1],c[2][:13],c[3]) for c in after][:8])
    gone=[c for c in after if c[3] in OC[2:]]; conc=pg.evaluate("SYNC_CONC")
    # 바꾸기 전에 이미 시작해 rateGate 에서 기다리던 요청(최대 SYNC_CONC 개)만 허용. 고치기 전 코드는 남은 작업 전부(지운 캐릭터 12건 안팎)를 새 키로 보냈음
    check('B: 지운 캐릭터(ocid-bg2~7) 새 뒤 작업 없음 (이미 출발한 최대 SYNC_CONC 건만)', len(gone)<=conc and len(after)<=conc, (len(gone),len(after),conc))
    check('JS 오류 없음', not errs, errs)
    b.close()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
