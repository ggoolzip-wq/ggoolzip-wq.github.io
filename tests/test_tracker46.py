# b62: 대표 키 하나로 어느 PC 에서든 부계정·예비 키 전부 복원 / 부계정·예비 키 로그인 차단(빨간 글) / 강제 로그아웃(예전 세션) 후 데이터 유지 / 소식 읽음 동기화
# 브라우저 여러 대 + wrangler dev(로컬 D1) + 넥슨 모의 서버
import os, sys, json, subprocess, time, urllib.request, shutil, hashlib, datetime
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
PORT, WP, NP = 8797, 8778, 8779
API=f'http://127.0.0.1:{WP}'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
KA,KF,KG='live_KEY_A_0123456789abcdef','live_KEY_F_0123456789abcdef','live_KEY_G_0123456789abcdef'
BKA,BKG='live_BK_A_0123456789abcdefg','live_BK_G_0123456789abcdefg'
def ch(id,name,acc):
    return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':'','accId':acc,'isMain':id=='c1','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','단풍용사','a1'),ch('c2','부캐F','a2'),ch('c3','부캐G','a3')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KA}],'lastSync':int(time.time()*1000)}}
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))); iso=lambda d:d.isoformat(timespec='seconds')
src=lambda l:{'label':l,'ok':True,'checkedAt':iso(now),'lastOkAt':iso(now),'error':''}
FEED={'version':1,'updatedAt':iso(now),'sources':{k:src(k) for k in ('saryo','patch','test','mabbak')},
  'items':{'saryo':[{'id':f'notice:{900000+i}','title':f'사료 글 {i}','url':f'https://maplestory.nexon.com/News/Notice/{900000+i}','date':iso(now-datetime.timedelta(days=i))} for i in range(1,4)],'patch':[],'test':[],'mabbak':[]}}
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
def mkctx(b):
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort()); ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(FEED)))
    ctx.route('https://maplestory.nexon.com/**',lambda r:r.fulfill(status=200,body='ok'))
    pg=ctx.new_page(); pg.on('dialog',lambda d:d.accept()); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'net::' not in m.text else None)
    return ctx,pg
st=lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
def wait_on(pg,t=15000): pg.wait_for_function("gd.state==='on'&&!gd.busy&&!gd.timer",timeout=t); pg.wait_for_timeout(200); pg.evaluate("closeImport()")
def invite(pg): pass  # b67: 초대 비밀번호 폐지 (호환용 빈 함수)
def login(pg,key):  # b67: 캐릭터 추가 창의 '본계정 API 키 등록'으로 로그인
    if not pg.evaluate("document.querySelector('#importModal').classList.contains('show')"): pg.evaluate("openAdd()")
    pg.wait_for_selector('#svMainKey'); pg.fill('#svMainKey',key); pg.click('#svMainBtn')
def fresh(b):
    c,p=mkctx(b); p.goto(URL); p.evaluate("api=>{localStorage.clear();localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',api)}",API); p.reload(); p.wait_for_timeout(400); return c,p
keyset=lambda s: sorted(x for a in s['settings']['accounts'] for x in (a.get('key'),a.get('bk')) if x)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # ---- 기기 A: 대표 키 로그인 → (+추가 창처럼) 부계정 2개·예비 키 2개를 저장 버튼 없이 등록 ----
    ca,pa=mkctx(b); pa.goto(URL)
    pa.evaluate("([p,api])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p));localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',api)}",[PRESET,API]); pa.reload(); pa.wait_for_timeout(400)
    invite(pa); login(pa,KA); wait_on(pa)
    pa.evaluate("([KF,KG,BKA,BKG])=>{const ac=accounts();ac[0].bk=BKA;ac[0].bkLabel='본계정 예비';S.settings.accounts=[...ac,{id:'a2',label:'부계정F',key:KF},{id:'a3',label:'부계정G',key:KG,bk:BKG,bkLabel:'G 예비'}];save();render()}",[KF,KG,BKA,BKG])
    pa.wait_for_function("localStorage.getItem('mapleBossTracker.svSubSig')===svSubSig()",timeout=15000)
    check('A: 키만 바꿔도 (저장 버튼 없이) 2초 뒤 서버 금고에 보관', True)
    reg=dev.sql("SELECT kind FROM keyreg"); check('A: 서버 등록부 = 부계정 2 + 예비 2 (해시만)', sorted(r['kind'] for r in reg)==['bk','bk','sub','sub'], reg)
    dump=json.dumps(dev.sql("SELECT * FROM keyvault2"))+json.dumps(dev.sql("SELECT * FROM keyreg"))+json.dumps(dev.sql("SELECT data FROM state"))
    check('A: 서버 어디에도 키 원본 없음', not any(k in dump for k in (KA,KF,KG,BKA,BKG)))
    # 소식 읽음: A 에서 글 2개 클릭
    pa.wait_for_selector('#feedCard a[data-fid="notice:900001"] .fnew')
    for fid in ('notice:900001','notice:900002'):
        pa.evaluate("f=>{const a=document.querySelector(`#feedCard a[data-fid=\"${f}\"]`);a.addEventListener('click',e=>e.preventDefault(),{once:true});a.click()}",fid)
    pa.wait_for_timeout(2500)
    seen=dev.sql("SELECT ids FROM seen"); check('A: 읽은 글이 서버에 저장', seen and set(json.loads(seen[0]['ids']))>={'notice:900001','notice:900002'}, seen)
    # ---- 새 기기 B: 대표 키만 → 키 전부 + 데이터 + 읽음 ----
    cb,pb=fresh(b); invite(pb); login(pb,KA); wait_on(pb); pb.wait_for_timeout(800)
    sb=st(pb); check('B(새 PC): 대표 키 로그인 → 부계정·예비 키 전부 그대로', keyset(sb)==sorted([KA,KF,KG,BKA,BKG]), keyset(sb))
    check('B: 계정 이름·예비 키 이름도 그대로', {a['label'] for a in sb['settings']['accounts']}>={'본계정','부계정F','부계정G'} and {a.get('bkLabel') for a in sb['settings']['accounts']}>={'본계정 예비','G 예비'} and any(a.get('bk')==BKG for a in sb['settings']['accounts']), [(a['label'],a.get('bkLabel')) for a in sb['settings']['accounts']])
    check('B: 캐릭터 데이터도 그대로', [c['name'] for c in sb['characters']]==['단풍용사','부캐F','부캐G'], [c['name'] for c in sb['characters']])
    pb.wait_for_function("feedSeen.has('notice:900001')",timeout=10000)
    nb=pb.evaluate("[['notice:900001','notice:900002','notice:900003'].map(f=>!feedSeen.has(f)),feedUnseen('saryo'),[...document.querySelectorAll('#feedCard a[data-fid] ')].map(a=>[a.dataset.fid,!!a.querySelector('.fnew')])]")
    check('B: A 에서 읽은 글은 N 없음, 안 읽은 글만 N (안 읽은 수 1)', nb[0]==[False,False,True] and nb[1]==1 and all(n==(f=='notice:900003') for f,n in nb[2]), nb)
    # ---- 새 기기 C: 부계정 키 / 예비 키 → 빨간 글, 로그인 안 됨 ----
    cc,pc=fresh(b); invite(pc)
    for k,nm in ((KF,'부계정 키'),(BKG,'부계정 예비 키'),(BKA,'본계정 예비 키')):
        login(pc,k); pc.wait_for_selector('#svMainSt .keyrej',timeout=10000); pc.wait_for_timeout(200)
        t=pc.inner_text('#svMainSt .keyrej'); col=pc.evaluate("getComputedStyle(document.querySelector('#svMainSt .keyrej')).color")
        check(f'C: {nm} 로그인 → 빨간 \'이미 등록된 부계정 API입니다.\' + 로그인 안 됨', t.strip()=='이미 등록된 부계정 API입니다.' and col=='rgb(255, 90, 90)' and not pc.evaluate("localStorage.getItem('mapleBossTracker.svToken')") and pc.locator('#svMainSec').count()==1, (t,col))
    # ---- 강제 로그아웃: A 의 세션·기기 표를 기준 시각 이전으로 → 다시 열면 입장 화면, 비밀번호부터 ----
    pa.evaluate("()=>{S.characters[0].name='단풍용사2';save();}")  # 저장 안 한 변경(이 PC 에만)
    ep=int(dev.sql("SELECT v FROM meta WHERE k='auth_epoch_b62'")[0]['v'])
    tok=pa.evaluate("localStorage.getItem('mapleBossTracker.svToken')")
    dev.sql(f"UPDATE sessions SET created_at={ep-1000} WHERE token_hash='{hashlib.sha256(tok.encode()).hexdigest()}'")
    before=dev.sql("SELECT rev FROM state")[0]['rev']
    pa.reload(); pa.wait_for_function("!localStorage.getItem('mapleBossTracker.svToken')",timeout=15000); pa.wait_for_timeout(300)
    check('예전 세션: 새로고침하면 (입장 화면 없이) 로그아웃 상태 + 다시 로그인 안내', pa.locator('#svGate').count()==0 and '다시 로그인' in pa.evaluate("gd.svErr") and pa.inner_text('#gBtn').strip() in ('☁ 로그인','☁ 다시 로그인'), (pa.evaluate("gd.svErr"),pa.inner_text('#gBtn')))
    sa=st(pa); check('예전 세션: 이 PC 데이터·키는 지우지 않음', sa['characters'][0]['name']=='단풍용사2' and keyset(sa)==sorted([KA,KF,KG,BKA,BKG]), keyset(sa))
    check('예전 세션: 서버 데이터 그대로', dev.sql("SELECT rev FROM state")[0]['rev']==before)
    pa.click('#gBtn'); pa.wait_for_selector('#svMainSec .keyrej.soft',timeout=5000)
    check('☁ 로그인 → 캐릭터 추가 창에 본계정 키 칸만 + 다시 로그인 안내', '다시 로그인' in pa.inner_text('#svMainSt') and not pa.is_visible('#accList'))
    login(pa,KA); wait_on(pa); pa.wait_for_timeout(500)
    sa=st(pa); check('다시 로그인: 묻지 않고 합침, 저장 안 했던 변경 유지, 키 그대로', not pa.evaluate("document.querySelector('#driveModal').classList.contains('show')") and sa['characters'][0]['name']=='단풍용사2' and keyset(sa)==sorted([KA,KF,KG,BKA,BKG]), (sa['characters'][0]['name'],keyset(sa)))
    srvd=json.loads(dev.sql("SELECT data FROM state")[0]['data']); check('다시 로그인 후 서버에도 반영(데이터 손실 없음)', [c['name'] for c in srvd['characters']]==['단풍용사2','부캐F','부캐G'], [c['name'] for c in srvd['characters']])
    # ---- 또 다른 새 기기 D: 강제 로그아웃 뒤에도 대표 키 → 전부 복원 ----
    cd,pd=fresh(b); invite(pd); login(pd,KA); wait_on(pd); pd.wait_for_timeout(500)
    sd=st(pd); check('D(새 PC): 키 전부 + 최신 데이터', keyset(sd)==sorted([KA,KF,KG,BKA,BKG]) and sd['characters'][0]['name']=='단풍용사2', keyset(sd))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
