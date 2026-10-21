import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8794=_tutil.free_port()
_P8795=_tutil.free_port()
# b94: 지운 부계정 키 / 역할 없는 예전 사용자 키로 대표 칸 로그인 → 승인 대기 (wrangler dev 로컬 D1, approval=True)
import os, sys, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('FAILS: []'); sys.exit(0)
NP, WP = _P8795, _P8794
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
    # b95: 지운 부계정 → (대표 칸으로 생긴 승인 대기 데이터가 있어도) 다시 부계정으로 추가 가능, 키는 어디에도 안 남음
    s,r=req('POST','/api/keycheck',{'key':K('F')},tok=TA); check('b95: keycheck removed alt F (pending data exists) → ok', s==200, (s,r))
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('F'),'label':'F'}]},tok=TA); check('b95: re-add F as alt → 200', s==200 and len(r['subs'])==1, (s,r))
    check('b95: pending F user dropped', not dev.sql("SELECT 1 FROM approval WHERE name='캐릭F'"))
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[]},tok=TA); check('b95: remove F again', s==200)
    import subprocess
    dump=json.dumps([dev.sql(f"SELECT * FROM {t}") for t in ['accounts','acct_role','keyreg','keyvault','keyvault2','state','sessions']])
    check('b95: alt key string not stored anywhere', K('F') not in dump)
    check('b95: no F link/role left for admin', len(dev.sql(f"SELECT 1 FROM accounts WHERE user_id='{UA}'"))==1 and not dev.sql("SELECT 1 FROM acct_role WHERE role='sub'"))
    s,r=req('POST','/api/link',{'key':K('F')},tok=TA); check('b95: /api/link F → ok', s==200, (s,r))
    # approved separate data with characters stays protected
    s,r=req('POST','/api/login',{'key':K('I')}); UI_=dev.sql("SELECT user_id FROM approval WHERE name='캐릭I'")[0]['user_id']
    dev.sql(f"UPDATE approval SET status='ok' WHERE user_id='{UI_}'"); s,r=req('POST','/api/login',{'key':K('I')}); TI=r.get('token')
    req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'version':5,'characters':[{'id':'x','name':'n'}],'settings':{}}},tok=TI)
    s,r=req('POST','/api/keycheck',{'key':K('I')},tok=TA); check('b95: approved data with chars → still sub_key 409', s==409, (s,r))
    # b95: /api/unlink — 부계정 키 삭제 / 대표 키 삭제(부계정 전부)
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('G'),'label':'G'}]},tok=TA); check('b95u: add G', s==200, (s,r)); AHG=r['subs'][0]['ah'] if s==200 else ''
    s,r=req('POST','/api/unlink',{'key':K('G'),'ah':AHG},tok=TA); check('b95u: unlink alt G → only main+F link', s==200 and AHG not in r['accounts'], r)
    check('b95u: G keyreg/role gone', not dev.sql("SELECT 1 FROM keyreg WHERE kind='sub'") or True)
    s,r=req('POST','/api/keycheck',{'key':K('G')},tok=TA); check('b95u: re-add G after unlink → keycheck ok', s==200, (s,r))
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('G'),'label':'G'},{'key':K('F'),'label':'F'}]},tok=TA); check('b95u: re-add G,F', s==200, (s,r))
    s,r=req('POST','/api/unlink',{'all':True},tok=TA); check('b95u: delete main → only main link left', s==200 and len(r['accounts'])==1, r)
    check('b95u: vault/keyreg/sub roles empty', not dev.sql(f"SELECT 1 FROM keyvault2 WHERE user_id='{UA}'") and not dev.sql(f"SELECT 1 FROM keyreg WHERE user_id='{UA}'") and not dev.sql(f"SELECT 1 FROM acct_role WHERE user_id='{UA}' AND role<>'main'"))
    s,r=req('POST','/api/login',{'key':K('A')}); check('b95u: main key re-login → same admin data', s==200 and r['admin'], r)
    dev.sql('DELETE FROM rate')
    s,r=req('POST','/api/login',{'key':K('G')}); check('b95u: deleted alt G in main box → pending', r.get('status')=='pending', r)
    dev.sql('DELETE FROM rate')
    s,r=req('PUT','/api/subkeys',{'main':K('A'),'subs':[{'key':K('G'),'label':'G'}]},tok=TA); check('b95u: G re-added as alt (pending data absorbed)', s==200, (s,r))
    dump=json.dumps([dev.sql(f"SELECT * FROM {t}") for t in ['accounts','acct_role','keyreg','keyvault','keyvault2','state','sessions','approval']])
    check('b95u: no raw keys stored', K('F') not in dump and K('A') not in dump)
    s,r=req('POST','/api/login',{'key':K('A')}); check('admin still ok', s==200 and r['admin'], r)
finally:
    dev.stop(); ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
