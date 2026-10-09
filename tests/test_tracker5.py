import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, urllib.parse, random
URL='file://'+ROOT+'/index.html'
errs=[]; calls=[]
def ch(o,n,w,j,l): return {'ocid':o,'character_name':n,'world_name':w,'character_class':j,'character_level':l}
random.seed(3)
JOBS=['히어로','팔라딘','비숍','신궁','나이트로드','아델','카인','라라','호영','제논']
WORLDS=['스카니아','베라','루나','엘리시움','크로아']
BIG=[ch(f'ocid-big{i}',f'창고캐{i:02d}',WORLDS[i%5],JOBS[i%10],[10,33,101,140,199,200,220,250,265,290][i%10]) for i in range(64)]
LIST={
 'live_mock_MULTI':{'account_list':[
    {'account_id':'A1','character_list':[ch('o1','본캐히어로','스카니아','히어로',285),ch('o2','저렙법사','스카니아','아크메이지(썬,콜)',150),ch('o3','루나아델','루나','아델',262)]},
    {'account_id':'A2','character_list':[ch('o4','두번째계정비숍','베라','비숍',271),ch('o1','본캐히어로','스카니아','히어로',285),ch('o5','레벨문자열','베라','카인','230')]},
    {'account_id':'A3','character_list':[]},
    {'account_id':'A4'}]},
 'live_mock_BIG':{'account_list':[{'account_id':'B','character_list':BIG}]},
 'test_mock_EMPTY':{'account_list':[]},
 'live_mock_NOLIST':{},
}
ERR={'live_mock_403':(403,{'error':{'name':'OPENAPI00002','message':'Forbidden'}}),
     'live_mock_429':(429,{'error':{'name':'OPENAPI00007','message':'Too Many Requests'}}),
     'live_mock_003':(400,{'error':{'name':'OPENAPI00003','message':'Please input valid id'}}),
     'live_mock_500':(500,'<html>Internal error</html>')}
def handle(route):
    u=urllib.parse.urlparse(route.request.url); q=dict(urllib.parse.parse_qsl(u.query)); p=u.path
    k=route.request.headers.get('x-nxopen-api-key'); calls.append((p.rsplit('/',1)[-1],k))
    if '/static/' in p: return route.fulfill(status=404,body='')
    if k in ERR:
        st,body=ERR[k]
        return route.fulfill(status=st,json=body) if isinstance(body,dict) else route.fulfill(status=st,body=body,content_type='text/html')
    if k not in LIST: return route.fulfill(status=400,json={'error':{'name':'OPENAPI00005','message':'The apikey is not valid.'}})
    if p.endswith('/character/list'): return route.fulfill(json=LIST[k])
    allc={c['ocid']:c for a in LIST[k].get('account_list',[]) for c in a.get('character_list',[])}
    if p.endswith('/character/basic'):
        c=allc[q['ocid']]; return route.fulfill(json={'date':'2026-10-08T00:00+09:00',**{x:c[x] for x in ('character_name','world_name','character_class')},'character_level':int(c['character_level']),'character_exp_rate':'12.345','character_exp':1})
    if p.endswith('/scheduler/character-state'):
        # clear_flag only (no complete_flag) to verify fallback
        return route.fulfill(json={'date':'2026-10-09T00:00+09:00','boss_contents':[{'content_name':'스우','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','clear_flag':'true'},
            {'content_name':'데미안','difficulty':'normal','cycle':'bossWeekly','registration_flag':'true','clear_flag':'false'}],'weekly_boss_clear_count':1,'weekly_boss_clear_limit_count':12})
    return route.fulfill(status=400,json={'error':{'name':'OPENAPI00006','message':'invalid path'}})

def setkey(pg,accid,key):
    pg.evaluate("([id,k])=>{const a=accById(id); a.key=k; a.status=null; delete listCache[id]; save(); openImport(id);}",[accid,key])
    pg.wait_for_selector('#importModal.show'); pg.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); pg.wait_for_timeout(150)
def imp(pg): return {'msg':pg.inner_text('#impMsg').replace('\n',' | ')[:400],'cls':pg.get_attribute('#impMsg','class'),'items':pg.locator('#impList .imp-item').count(),'count':pg.inner_text('#impCount')}
def close(pg): pg.click('#impClose'); pg.wait_for_timeout(100)
def addkey(pg,key):
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.fill('#newAccKey',key); pg.click('#newAccBtn')
    pg.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); pg.wait_for_timeout(150)

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)))
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(200)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); print('T0 empty modal: impSec hidden', pg.is_hidden('#impSec'), '|', pg.inner_text('#accList')[:60])
    pg.fill('#newAccKey','live_mock_MULTI'); pg.click('#newAccBtn'); pg.wait_for_function("!document.querySelector('#impMsg .spin')",timeout=15000); pg.wait_for_timeout(150)
    aid=pg.evaluate("S.settings.accounts[0].id")
    # 1. multi account_list
    r=imp(pg); print('T1 multi:',r)
    print('T1b names:', pg.eval_on_selector_all('#impList .imp-item b','e=>e.map(x=>x.textContent)'), '| impMin value:', repr(pg.input_value('#impMin')))
    pg.screenshot(path=OUT+'/shot5_import_multi.png')
    close(pg)
    # 2. big list, all levels visible by default; filter works
    setkey(pg,aid,'live_mock_BIG'); r=imp(pg); print('T2 big:',r, '| lowest level shown:', pg.eval_on_selector_all('#impList .imp-item .muted','e=>e.map(x=>x.textContent).filter(t=>t.startsWith("Lv.")).at(-1)'))
    pg.fill('#impMin','200'); pg.wait_for_timeout(50); print('T2b min200:', pg.inner_text('#impCount'), pg.locator('#impList .imp-item').count())
    pg.fill('#impMin',''); pg.fill('#impQ','창고캐0'); pg.wait_for_timeout(50); print('T2c search:', pg.inner_text('#impCount'))
    pg.fill('#impQ','없는이름'); pg.wait_for_timeout(50); print('T2d no-match:', pg.inner_text('#impList')); pg.click('#impClear'); print('T2e cleared:', pg.inner_text('#impCount'))
    pg.click('#impAll'); pg.click('#impOk'); pg.wait_for_function("!syncing",timeout=60000); print('T2f imported:', pg.evaluate("S.characters.length"))
    pg.evaluate("S.characters=[];save();render()")
    # 3. empty
    setkey(pg,aid,'test_mock_EMPTY'); print('T3 empty:',imp(pg)); pg.screenshot(path=OUT+'/shot5_import_empty.png'); close(pg)
    setkey(pg,aid,'live_mock_NOLIST'); print('T3b no account_list:',imp(pg)); close(pg)
    pg.click('#addCharBtn'); pg.wait_for_timeout(300); print('T3c account row:', pg.inner_text('#accList .accrow .accst')); close(pg)
    # 4. errors
    for k in ['live_mock_403','live_mock_429','live_mock_003','live_mock_500','live_bad_key_xxx']:
        setkey(pg,aid,k); r=imp(pg); print('T4',k,r['cls'],'|',r['msg']); 
        if k=='live_bad_key_xxx': pg.screenshot(path=OUT+'/shot5_import_error.png')
        close(pg)
    pg.click('#addCharBtn'); pg.wait_for_timeout(300); print('T4b account row status:', pg.inner_text('#accList .accrow .accst'), '| title:', pg.get_attribute('#accList .accrow .warnc','title')); close(pg)
    # 4c. '캐릭터 목록' button on the account row
    pg.evaluate("([id])=>{accById(id).key='live_mock_MULTI'; accById(id).status=null; save();}",[aid]); pg.click('#addCharBtn'); pg.click(f'[data-acctest="{aid}"]'); pg.wait_for_selector('#importModal.show'); pg.wait_for_function("!document.querySelector('#impMsg .spin')"); pg.wait_for_timeout(200)
    print('T4c test button (key typed, no blur):', imp(pg)['items'], '| list calls so far for MULTI:', sum(1 for c in calls if c==('list','live_mock_MULTI')))
    close(pg)
    # 5. character modal picker
    pg.click('#addCharBtn'); pg.evaluate('closeImport();openCharModal()'); pg.wait_for_timeout(400)
    print('T5 pick visible:', pg.is_visible('#fPickWrap'), pg.locator('#fPick .pick-item').count(), '| acc label:', pg.inner_text('#fPickAcc'))
    pg.fill('#fName','두번'); pg.wait_for_timeout(50); print('T5b filter:', pg.eval_on_selector_all('#fPick .pick-item b','e=>e.map(x=>x.textContent)'))
    pg.fill('#fName',''); pg.click('#fPick .pick-item:has-text("저렙법사")'); pg.wait_for_timeout(300)
    print('T5c filled:', pg.input_value('#fName'), pg.input_value('#fJob'), pg.input_value('#fLevel'), pg.input_value('#fWorld'), '|', pg.inner_text('#fLookupMsg'))
    pg.screenshot(path=OUT+'/shot5_charmodal.png')
    pg.click('#fSave'); pg.wait_for_timeout(100)
    c=pg.evaluate("S.characters[0]"); print('T5d saved:', c['name'], c['ocid'], c['accId']==aid, c.get('exp'))
    pg.click('#syncBtn'); pg.wait_for_function("!syncing"); pg.wait_for_timeout(100)
    c=pg.evaluate("S.characters[0]"); print('T6 clear_flag scheduler → weekly:', c['weekly'], '| sync ok:', c['sync'].get('ok'))
    pg.click('#addCharBtn'); pg.evaluate('closeImport();openCharModal()'); pg.wait_for_timeout(300); print('T5e dup disabled:', pg.locator('#fPick .pick-item:disabled').count()); pg.click('#fCancel')
    # 7. picker error in char modal
    setkey(pg,aid,'live_mock_429'); close(pg)
    pg.click('#addCharBtn'); pg.evaluate('closeImport();openCharModal()'); pg.wait_for_timeout(500); print('T7 char modal error:', pg.inner_text('#fPick').replace('\n',' | ')[:200]); pg.click('#fCancel')
    # 8. unit: applyScheduler accepts boolean & complete_flag
    print('T8 flags:', pg.evaluate("[flagOn('true'),flagOn(true),flagOn('TRUE'),flagOn('false'),flagOn(undefined)]"))
    # 9. LIVE call with dummy key (no mock)
    live=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); lp=live.new_page(); lp.on('pageerror',lambda e:errs.append('live:'+str(e)))
    lp.goto(URL); lp.evaluate("localStorage.clear()"); lp.reload(); lp.wait_for_timeout(200)
    addkey(lp,'test_dummy_key_for_error_check'); print('T9 LIVE dummy key:', imp(lp)); lp.screenshot(path=OUT+'/shot5_live_error.png')
    b.close()
print('ERRORS:',errs)
