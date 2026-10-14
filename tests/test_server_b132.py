# b132: 가입 승인 스위치 APPROVAL_REQUIRED — 0 = 끔(누구나 바로 사용), 1 = 켬 (wrangler dev 로컬 D1)
import os, sys, json, re, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('FAILS: []'); sys.exit(0)
NP, WP = 8787, 8786
def req(m,path,body=None,tok=None):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=15) as res: return res.status, json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')
ms=MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
for x in 'PRN': MN.KEYS[K(x)]=[f'acc-b132-{x}']
dev=cf_dev.Dev(WP,NP,approval=True)
try:
    toml=open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'server','wrangler.toml')).read()
    check('운영 wrangler.toml: APPROVAL_REQUIRED = "0" (지금 승인 끔)', re.search(r'^APPROVAL_REQUIRED = "0"', toml, re.M) is not None)
    s,a=req('POST','/api/login',{'key':K('A')}); UA=dev.sql('SELECT id FROM users')[0]['id']
    dev.sql(f"DELETE FROM approval WHERE user_id='{UA}'"); dev.sql(f"INSERT INTO meta (k,v) VALUES ('admin_user','{UA}')")
    s,a=req('POST','/api/login',{'key':K('A')}); TA=a.get('token'); check('관리자 로그인', s==200 and a.get('admin') and TA, a)
    s,p=req('POST','/api/login',{'key':K('P')}); UP=dev.sql("SELECT user_id FROM approval WHERE status='pending'")[0]['user_id']
    check('켬: 새 키 → 승인 대기 (토큰 없음)', p.get('status')=='pending' and not p.get('token') and UP!=UA, p)
    s,r=req('POST','/api/login',{'key':K('R')}); UR=[x['user_id'] for x in dev.sql("SELECT user_id FROM approval WHERE status='pending'") if x['user_id']!=UP][0]
    s,d=req('POST','/api/admin/decide',{'user':UR,'action':'reject'},tok=TA); check('켬: R 거절', s==200 and d.get('status')=='rejected' and d.get('user')==UR, (s,d,UR))
    check('켬: P는 여전히 pending', dev.sql(f"SELECT status FROM approval WHERE user_id='{UP}'")[0]['status']=='pending')
    D=dev.dir; dev.stop(); dev=cf_dev.Dev(WP,NP,approval=True,extra={'APPROVAL_REQUIRED':'0'},persist=D)
    s,n=req('POST','/api/login',{'key':K('N')}); UN=dev.sql("SELECT user_id FROM accounts ORDER BY created_at DESC LIMIT 1")[0]['user_id']
    check('끔: 새 키 → 바로 ok + 토큰', s==200 and n.get('status')=='ok' and bool(n.get('token')), n)
    check('끔: 새 사용자에 approval 행 없음', not dev.sql(f"SELECT 1 FROM approval WHERE user_id='{UN}'"), UN)
    s,b=req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'characters':[]}},tok=n.get('token')); check('끔: 새 사용자 저장 가능', s==200, (s,b))
    s,p=req('POST','/api/login',{'key':K('P')}); TP=p.get('token')
    check('끔: 예전 대기 사용자도 바로 ok (approval 행은 그대로 pending)', s==200 and p.get('status')=='ok' and TP and dev.sql(f"SELECT status FROM approval WHERE user_id='{UP}'")[0]['status']=='pending', p)
    s,b=req('GET','/api/me',tok=TP); check('끔: 대기 사용자 세션 사용 가능', s==200, (s,b))
    s,r=req('POST','/api/login',{'key':K('R')}); check('끔: 거절(rejected)은 그대로 403', s==403 and r.get('error')=='rejected', (s,r))
    D=dev.dir; dev.stop(); dev=cf_dev.Dev(WP,NP,approval=True,persist=D)
    s,b=req('GET','/api/me',tok=TP); check('다시 켬: 대기 사용자 세션 → 403 pending', s==403 and b.get('error')=='pending', (s,b))
    s,p=req('POST','/api/login',{'key':K('P')}); check('다시 켬: 대기 사용자 로그인 → pending', p.get('status')=='pending' and not p.get('token'), p)
    s,n=req('POST','/api/login',{'key':K('N')}); check('다시 켬: 끔 동안 가입한 사용자는 승인 행 없음 = 승인됨', n.get('status')=='ok', n)
finally:
    try: dev.stop()
    except Exception: pass
    ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
