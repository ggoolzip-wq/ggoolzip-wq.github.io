# b94: 지운 부계정 키 / 역할 없는 예전 사용자 키로 대표 칸 로그인 → 승인 대기 (wrangler dev 로컬 D1, approval=True)
import os, sys, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('FAILS: []'); sys.exit(0)
NP, WP = 8895, 8894
def req(m,path,body=None,tok=None):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=15) as res: return res.status, json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP,approval=True)
K=lambda x:f'live_KEY_{x}_0123456789abcdef'
try:
    s,a=req('POST','/api/login',{'key':K('A')}); check('first user pending', a.get('status')=='pending', a)
    UA=dev.sql('SELECT id FROM users')[0]['id']; dev.sql(f"INSERT INTO meta (k,v) VALUES ('admin_user','{UA}')")
    s,a=req('POST','/api/login',{'key':K('A')}); TA=a.get('token'); check('admin login ok', s==200 and a['admin'], a)
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('F'),'label':'F'}]},tok=TA); check('add alt F', s==200, r)
    s,r=req('POST','/api/login',{'key':K('F')}); check('alt key in main box while registered → sub_key 403', s==403, (s,r))
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[]},tok=TA); check('remove alt F', s==200 and len(r['accounts'])==1, r)
    s,r=req('POST','/api/login',{'key':K('F')}); check('removed alt key → pending new user (not admin)', s==200 and r.get('status')=='pending' and not r.get('token'), r)
    # stale mapping left by old code: map acc-G to admin without main role
    s,_=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('G'),'label':'G'}]},tok=TA)
    dev.sql("DELETE FROM keyreg"); dev.sql(f"DELETE FROM acct_role WHERE role='sub'")
    s,r=req('POST','/api/login',{'key':K('G')}); check('stale alt mapping → pending, not admin session', r.get('status')=='pending' and not r.get('admin'), r)
    check('stale mapping removed from admin', len(dev.sql(f"SELECT 1 FROM accounts WHERE user_id='{UA}'"))==1)
    # legacy user (pre-b68): no approval row, no roles
    s,_=req('POST','/api/login',{'key':K('H')}); UH=dev.sql("SELECT user_id FROM approval WHERE status='pending' ORDER BY requested_at DESC LIMIT 1")[0]['user_id']
    dev.sql(f"DELETE FROM approval WHERE user_id='{UH}'"); dev.sql(f"DELETE FROM acct_role WHERE user_id='{UH}'")
    s,r=req('POST','/api/login',{'key':K('H')}); check('legacy no-role user → pending', r.get('status')=='pending', r)
    s,r=req('POST','/api/login',{'key':K('A')}); check('admin still ok', s==200 and r['admin'], r)
finally:
    dev.stop(); ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
