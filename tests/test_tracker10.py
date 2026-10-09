import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, subprocess, os, time, urllib.request, re
errs=[]; BASE='http://localhost:8787/index.html'
env=dict(os.environ, PORT='8787', MBT_FIXTURE_DIR=ROOT+'/tests/fixtures/mock')
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
INIT="""
window.__MBT_GCID='test-client.apps.googleusercontent.com';
window.__g={req:0,revoked:0,prompts:[]};
window.google={accounts:{oauth2:{
  initTokenClient(cfg){ return {requestAccessToken(o){ __g.req++; __g.prompts.push(o&&o.prompt); const f=localStorage.getItem('__gfail');
    setTimeout(()=>{ if(f==='access_denied') cfg.callback({error:f}); else if(f) cfg.error_callback({type:f}); else cfg.callback({access_token:'tok'+__g.req,expires_in:3599,scope:'https://www.googleapis.com/auth/drive.appdata'}); },30); }}; },
  hasGrantedAllScopes(r,s){ return (r.scope||'').includes(s); },
  revoke(t,cb){ __g.revoked++; cb&&cb(); } }}};
"""
class Drive:
    def __init__(s): s.file=None; s.log=[]
    def seed(s,data,upd,keys=False):
        s.file={'id':'F1','appProperties':{'updatedAt':str(upd),'characters':str(len(data['characters']))},'content':{'app':'maple-boss-tracker','format':1,'savedAt':upd,'updatedAt':upd,'characters':len(data['characters']),'withKeys':keys,'data':data}}
    def handle(s,route,req):
        h={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization,content-type','Access-Control-Allow-Methods':'GET,POST,PATCH,OPTIONS'}
        if req.method=='OPTIONS': return route.fulfill(status=204,headers=h)
        u=req.url; s.log.append((req.method,u.split('?')[0].replace('https://www.googleapis.com','')))
        auth=req.headers.get('authorization','')
        if not auth.startswith('Bearer tok'): return route.fulfill(status=401,headers=h,json={'error':{'message':'no auth'}})
        def ok(j): route.fulfill(status=200,headers={**h,'Content-Type':'application/json'},body=json.dumps(j))
        if req.method=='GET' and '/drive/v3/files?' in u:
            assert 'spaces=appDataFolder' in u
            return ok({'files':[{'id':s.file['id'],'appProperties':s.file['appProperties']}] if s.file else []})
        m=re.search(r'/drive/v3/files/([^?]+)\?(.*)',u)
        if req.method=='GET' and m:
            if not s.file or s.file['id']!=m.group(1): return route.fulfill(status=404,headers=h,json={'error':{'message':'File not found'}})
            if 'alt=media' in m.group(2): return ok(s.file['content'])
            return ok({'id':s.file['id'],'appProperties':s.file['appProperties']})
        if '/upload/drive/v3/files' in u:
            ct=req.headers['content-type']; bd=ct.split('boundary=')[1]
            parts=[p for p in req.post_data.split('--'+bd) if p.strip() and p.strip()!='--']
            meta=json.loads(parts[0].split('\r\n\r\n',1)[1].strip()); body=json.loads(parts[1].split('\r\n\r\n',1)[1].strip())
            if req.method=='POST':
                assert meta.get('parents')==['appDataFolder'] and meta['name']=='maple-boss-tracker.json', meta
                s.file={'id':'F2','appProperties':meta['appProperties'],'content':body}
            else:
                s.file['appProperties']=meta['appProperties']; s.file['content']=body
            return ok({'id':s.file['id']})
        route.fulfill(status=500,headers=h,body='unexpected')
    def uploads(s): return [l for l in s.log if 'upload' in l[1]]
def char(i,name): return {'id':'c'+str(i),'name':name,'level':270+i,'job':'히어로','world':'스카니아','isMain':i==1,'ocid':'','bosses':{'lotus':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
def state(names,upd,key=''):
    return {'version':5,'activeId':'c1','characters':[char(i+1,n) for i,n in enumerate(names)],'history':[],'monthHistory':[],'worldOrder':[],'updatedAt':upd,
            'settings':{'weeklyLimit':12,'monthlyLimit':1,'prices':{},'accounts':[{'id':'a1','label':'본계정','key':key}],'apiMode':'direct','autoSync':False,'autoEnable':True,'lastSync':0}}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def newpage(drive,local=None,meta=None,gcid=True,w=1280):
        ctx=b.new_context(viewport={'width':w,'height':900},locale='ko-KR',accept_downloads=True)
        if gcid: ctx.add_init_script(INIT)
        ctx.route('https://www.googleapis.com/**',drive.handle)
        ctx.route('https://accounts.google.com/**',lambda r,q: r.fulfill(status=200,body='/* blocked in test */'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
        pg.on('dialog',lambda d:d.accept())
        pg.goto(BASE); pg.wait_for_timeout(150)
        if local is not None or meta is not None:
            if local is not None: pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(local))
            if meta is not None: pg.evaluate("s=>localStorage.setItem('mapleBossTracker.gdrive',s)",json.dumps(meta))
            pg.reload(); pg.wait_for_timeout(300)
        return ctx,pg
    gbtn=lambda pg: pg.inner_text('#gBtn')
    def login(pg): pg.click('#gBtn'); pg.wait_for_selector('#gMenu #gdLogin'); pg.click('#gMenu #gdLogin')
    def menu(pg): pg.click('#gBtn') if pg.is_hidden('#gMenu') else None; pg.wait_for_timeout(100)
    names=lambda pg: pg.evaluate("S.characters.map(c=>c.name)")
    # 1. both empty + debounce
    d=Drive(); ctx,pg=newpage(d)
    print('E0 header btn:',gbtn(pg),'| visible:',pg.is_visible('#gBtn'))
    login(pg); pg.wait_for_timeout(500)
    print('E1 both-empty → state:',pg.evaluate('gd.state'),'| msg:',pg.evaluate('gd.msg'),'| uploads:',len(d.uploads()),'| prompts:',pg.evaluate('__g.prompts'))
    for i in range(3):
        pg.evaluate(f"()=>{{S.characters.push({json.dumps(char(i+1,'캐릭'+str(i)))}); save();}}"); pg.wait_for_timeout(1000)
    print('E2 after 3 changes over ~3s: uploads',len(d.uploads()),'| btn:',gbtn(pg))
    pg.wait_for_timeout(3000); print('E2 at ~6s: uploads',len(d.uploads()),'| drive chars:',d.file and d.file['content']['characters'])
    pg.wait_for_timeout(2500); print('E2 at ~8.5s (debounced, single upload):',len(d.uploads()),'method',d.uploads()[0][0],'| btn:',gbtn(pg))
    ctx.close()
    # 2. drive-only
    d=Drive(); d.seed(state(['드라이브캐1','드라이브캐2'],1760000000000),1760000000000); ctx,pg=newpage(d)
    login(pg); pg.wait_for_timeout(600)
    print('D1 drive-only → loaded:',names(pg),'| state',pg.evaluate('gd.state'),'| updatedAt kept:',pg.evaluate('S.updatedAt')==1760000000000,'| modal:',pg.is_visible('#driveModal'))
    pg.wait_for_timeout(5600); print('D1 uploads after load (no needless writes expected ≤1):',len(d.uploads()))
    ctx.close()
    # 3. local-only, keys excluded by default, then opt-in
    d=Drive(); loc=state(['로컬캐'],1760000500000,key='live_SECRETKEY'); ctx,pg=newpage(d,local=loc)
    login(pg); pg.wait_for_timeout(600)
    acc=d.file['content']['data']['settings']['accounts']
    print('L1 local-only → created:',d.uploads()[0][0],'| drive chars:',[c['name'] for c in d.file['content']['data']['characters']],'| accounts:',acc,'| key saved to drive (expected True):', 'live_SECRETKEY' in json.dumps(d.file['content']))
    menu(pg)
    print('L2 menu status:',pg.inner_text('#gdStatus').replace('\n',' | ')[:160])
    print('L3 no checkbox:',pg.query_selector('#sDriveKeys') is None,'| note:',pg.inner_text('#gMenu').count('API 키도 함께 저장돼요'),'| withKeys:',d.file['content']['withKeys'])
    print('L4 no JSON export/import UI, no connection-mode select, no settings tab:', pg.query_selector('#exportBtn') is None and pg.query_selector('#importFile') is None and pg.query_selector('#sMode') is None and pg.query_selector('[data-tab="settings"]') is None)
    pg.screenshot(path=OUT+'/shot10_menu.png'); pg.click('#gMenuClose')
    pg.evaluate("()=>{S.settings.accounts[0].key='live_NEWKEY'; save();}"); pg.wait_for_timeout(5800)
    print('L5 key edit → autosaved to drive:', 'live_NEWKEY' in json.dumps(d.file['content']))
    pg.screenshot(path=OUT+'/shot10_settings.png')
    # 3b. reload in same tab session: auto-load without new consent
    req0=pg.evaluate('__g.req')
    newer=json.loads(json.dumps(d.file['content'])); newer['data']['characters'][0]['name']='PC방에서수정'; newer['updatedAt']=newer['data']['updatedAt']=int(time.time()*1000)+5000
    d.file['content']=newer; d.file['appProperties']['updatedAt']=str(newer['updatedAt'])
    pg.reload(); pg.wait_for_timeout(800)
    print('R1 reopen (token in session) → requests:',pg.evaluate('__g.req'),'| names:',names(pg),'| state:',pg.evaluate('gd.state'),'| modal:',pg.is_visible('#driveModal'))
    # 3c. local-only change since last sync → auto push on reopen
    pg.evaluate("()=>{S.characters[0].level=299; save();}"); up0=len(d.uploads()); pg.reload(); pg.wait_for_timeout(800)
    print('R2 reopen with local unsaved change → pushed:',len(d.uploads())>up0,'| drive level:',d.file['content']['data']['characters'][0]['level'])
    # 3d. page hide flush
    up0=len(d.uploads()); pg.evaluate("()=>{S.characters[0].level=300; save(); Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange'));}"); pg.wait_for_timeout(500)
    print('H1 hide → immediate upload:',len(d.uploads())-up0,'| drive level:',d.file['content']['data']['characters'][0]['level'])
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false})")
    # 3e. other PC saved meanwhile (different field) → auto-merged without asking (2026-10-10)
    other=json.loads(json.dumps(d.file['content'])); other['updatedAt']=int(time.time()*1000)+9000; other['data']['characters'][0]['name']='다른PC'
    d.file['content']=other; d.file['appProperties']['updatedAt']=str(other['updatedAt'])
    pg.evaluate("()=>{S.characters[0].level=301; save();}"); pg.wait_for_timeout(5800)
    dc0=d.file['content']['data']['characters'][0]
    print('C0 concurrent edit (other field) → modal:',pg.is_visible('#driveModal'),'| state',pg.evaluate('gd.state'),'| merged drive:',dc0['name'],dc0['level'],'| local:',names(pg),pg.evaluate('S.characters[0].level'))
    # 3e2. genuine conflict (same field on both) → one prompt; 나중에 → header reopens
    other=json.loads(json.dumps(d.file['content'])); other['updatedAt']=int(time.time()*1000)+19000; other['data']['characters'][0]['name']='다른PC2'
    d.file['content']=other; d.file['appProperties']['updatedAt']=str(other['updatedAt'])
    pg.evaluate("()=>{S.characters[0].name='이PC이름'; save();}"); pg.wait_for_timeout(5800)
    print('C1 same-field conflict → modal:',pg.is_visible('#driveModal'),'| state',pg.evaluate('gd.state'),'| drive not overwritten:',d.file['content']['data']['characters'][0]['name']=='다른PC2')
    pg.click('#gdClose'); print('C1 later → btn:',gbtn(pg)); pg.click('#gBtn'); print('C1 header reopens modal:',pg.is_visible('#driveModal')); pg.click('#gdUseDrive'); pg.wait_for_timeout(500)
    print('C1 use drive → names',names(pg),'| state',pg.evaluate('gd.state'),'| level kept:',pg.evaluate('S.characters[0].level'))
    # 3f. wipe
    print('W0 no wipe button:', pg.query_selector('#gdWipe') is None and '지우기' not in pg.inner_text('#gMenu') if not pg.is_hidden('#gMenu') else pg.query_selector('#gdWipe') is None)
    rv=pg.evaluate('__g.revoked'); menu(pg); pg.click('#gMenu #gdLogout'); pg.wait_for_timeout(1500)
    print('W1 logout → local chars kept:',names(pg),'| meta:',pg.evaluate("localStorage.getItem('mapleBossTracker.gdrive')"),'| drive kept:',d.file['content']['data']['characters'][0]['name'],'| btn:',gbtn(pg))
    ctx.close()
    # 3g. PC방 upgrade: drive saved by old version (no keys), this PC has the key, same data → next connect saves keys
    d=Drive(); base=1760000000000; dat=state(['PC방캐'],base); d.seed(json.loads(json.dumps(dat)),base)
    d.file['content']['withKeys']=False
    loc=state(['PC방캐'],base,key='live_PCBANG'); loc['settings']['driveKeys']=False
    ctx,pg=newpage(d,local=loc,meta={'on':True,'base':base,'fileId':'F1'}); pg.wait_for_timeout(800)
    print('K3 old-version drive w/o keys → saved with keys:', 'live_PCBANG' in json.dumps(d.file['content']), '| withKeys:', d.file['content']['withKeys'], '| old flag removed:', pg.evaluate("S.settings.driveKeys===undefined"))
    ctx.close()
    # 3h. new PC: empty local, drive has keys → restored
    d=Drive(); dat=state(['집캐'],base,key='live_HOMEKEY'); d.seed(dat,base,keys=True)
    ctx,pg=newpage(d); login(pg); pg.wait_for_timeout(600)
    print('K4 new PC → key restored:', pg.evaluate("accounts().map(a=>a.key)"))
    menu(pg); pg.click('#gMenu #gdLogout'); pg.wait_for_timeout(1500)
    print('K5 logout → local data kept, state off:', 'live_HOMEKEY' in (pg.evaluate("localStorage.getItem('mapleBossTracker.v1')") or ''), pg.evaluate('gd.state'), '| drive keeps key:', 'live_HOMEKEY' in json.dumps(d.file['content']))
    ctx.close()
    # 3i. same data, drive has key, this PC lacks it → pulled
    d=Drive(); dat=state(['A'],base,key='live_DRV'); d.seed(dat,base,keys=True)
    ctx,pg=newpage(d,local=state(['A'],base),meta={'on':True,'base':base,'fileId':'F1'}); pg.wait_for_timeout(800)
    print('K6 key only in drive → pulled to this PC:', pg.evaluate("accounts().map(a=>a.key)"))
    ctx.close()
    # 4. conflict first link, both choices
    for choice in ['gdUseDrive','gdUseLocal']:
        d=Drive(); d.seed(state(['드라1','드라2','드라3'],1760000000000),1760000000000)
        ctx,pg=newpage(d,local=state(['이PC1'],1760000900000))
        login(pg); pg.wait_for_selector('#driveModal.show',timeout=5000)
        txt=pg.inner_text('#gdBody').replace('\n',' | ')
        if choice=='gdUseDrive': print('K1 conflict modal:',txt[:330]); pg.screenshot(path=''+OUT+'/drive_conflict.png')
        pg.click('#'+choice); pg.wait_for_timeout(500)
        print('K2',choice,'→ local:',names(pg),'| drive:',[c['name'] for c in d.file['content']['data']['characters']],'| state:',pg.evaluate('gd.state'))
        ctx.close()
    # 5. reopen without session token + popup blocked → reconnect, then click works
    d=Drive(); d.seed(state(['A'],1760000000000),1760000000000)
    ctx,pg=newpage(d,local=state(['A'],1760000000000),meta={'on':True,'base':1760000000000,'fileId':'F1'})
    pg.evaluate("localStorage.setItem('__gfail','popup_failed_to_open'); sessionStorage.removeItem('mapleBossTracker.gtoken')"); pg.reload(); pg.wait_for_timeout(600)
    print('P1 auto re-auth blocked → state',pg.evaluate('gd.state'),'| btn:',gbtn(pg),'| prompt used:',pg.evaluate('__g.prompts'))
    pg.evaluate("localStorage.removeItem('__gfail')"); login(pg); pg.wait_for_timeout(500)
    print('P2 one click → state',pg.evaluate('gd.state'),'| btn:',gbtn(pg))
    ctx.close()
    # 5b. login errors show Korean help (interactive)
    for f in ['access_denied','popup_closed','popup_failed_to_open']:
        d=Drive(); ctx,pg=newpage(d)
        pg.evaluate(f"localStorage.setItem('__gfail','{f}')"); login(pg); pg.wait_for_timeout(400)
        print('X',f,'→ btn:',gbtn(pg),'| modal:',pg.is_visible('#driveModal'),'|',pg.inner_text('#gdBody').replace('\n',' ')[:170])
        if f=='access_denied': pg.screenshot(path=''+OUT+'/drive_help.png')
        pg.evaluate("localStorage.removeItem('__gfail')"); pg.click('#driveModal #gdLogin'); pg.wait_for_timeout(400)
        print('X',f,'retry →',pg.evaluate('gd.state'),'| modal closed:',not pg.is_visible('#driveModal'))
        ctx.close()
    # 6. 401 → token refresh retry
    d=Drive(); d.seed(state(['A'],1760000000000),1760000000000)
    ctx,pg=newpage(d,local=state(['A'],1760000000000),meta={'on':True,'base':1760000000000,'fileId':'F1'})
    pg.wait_for_timeout(400); pg.evaluate("()=>{gd.token='expired-token'; gd.exp=Date.now()+3600e3; S.characters[0].level=250; save();}"); pg.wait_for_timeout(5800)
    print('T1 401 → re-token + saved:',d.file['content']['data']['characters'][0]['level']==250,'| state',pg.evaluate('gd.state'))
    ctx.close()
    # 7. no client id / file:// / mobile
    d=Drive(); ctx,pg=newpage(d,gcid=False); menu(pg)
    print('N1 (client id now built in) gcid:',pg.evaluate('gcid()')[:12]); print('N1 real GIS (blocked in test) → header visible:',pg.is_visible('#gBtn'),'| card:',pg.inner_text('#gdStatus').replace('\n',' ')[:80])
    ctx.close()
    ctx=b.new_context(); ctx.add_init_script(INIT); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+ROOT+'/index.html'); pg.click('#gBtn'); pg.wait_for_timeout(100)
    print('N2 file:// → header visible:',pg.is_visible('#gBtn'),'| btn:',gbtn(pg),'| menu:',pg.inner_text('#gMenu .impmsg b')); ctx.close()
    d=Drive(); d.seed(state(['드라1'],1760000000000),1760000000000); ctx,pg=newpage(d,local=state(['이PC1'],1760000900000),w=375)
    login(pg); pg.wait_for_selector('#driveModal.show'); print('M1 mobile overflow:',pg.evaluate('document.documentElement.scrollWidth>innerWidth')); pg.screenshot(path=OUT+'/shot10_mobile.png'); ctx.close()
    b.close()
srv.terminate()
print('ERRORS:',errs)
