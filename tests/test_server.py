# 동기화 서버(server/worker.js) — wrangler dev(로컬 D1) + 넥슨 모의 서버로 API 테스트
import os, sys, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed (cd server && npm install)'); print('FAILS: []'); sys.exit(0)
NP, WP = 8771, 8770
ORIGIN='https://ggoolzip-wq.github.io'
def req(method,path,body=None,tok=None,origin=ORIGIN,raw=None):
    h={'Content-Type':'application/json'}
    if origin: h['Origin']=origin
    if tok: h['Authorization']='Bearer '+tok
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=data,method=method,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=15) as res: return res.status, json.loads(res.read() or b'null'), dict(res.headers)
    except urllib.error.HTTPError as e:
        b=e.read(); return e.code, (json.loads(b) if b else None), dict(e.headers)
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
    KA,KB,KAC,KD,KE='live_KEY_A_0123456789abcdef','live_KEY_B_0123456789abcdef','live_KEY_AC_0123456789abcde','live_KEY_D_0123456789abcdef','live_KEY_E_0123456789abcdef'
    # CORS
    s,_,h=req('GET','/api/health'); check('health + CORS for github.io', s==200 and h.get('Access-Control-Allow-Origin')==ORIGIN, h)
    s,_,h=req('GET','/api/health',origin='http://localhost:8787'); check('CORS allows localhost (tests)', h.get('Access-Control-Allow-Origin')=='http://localhost:8787', h)
    s,b,h=req('GET','/api/health',origin='https://evil.example'); check('other origin rejected (403, no ACAO)', s==403 and 'Access-Control-Allow-Origin' not in h, (s,h))
    # 초대 비밀번호 (기기당 한 번)
    s,b,_=req('POST','/api/login',{'key':KA}); check('login without invite device → 403 need_invite', s==403 and b['error']=='need_invite', b)
    s,b,_=req('POST','/api/invite',{'pass':'wrong'}); check('wrong invite password → 403 bad_invite', s==403 and b['error']=='bad_invite', b)
    s,b,_=req('POST','/api/invite',{'pass':'test invite 7'}); check('invite password is case-sensitive', s==403, b)
    s,b,_=req('POST','/api/invite',{'pass':'  '+cf_dev.TEST_PASS+' '}); DEV=b.get('device',''); check('correct invite (spaces trimmed) → device ticket', s==200 and len(DEV)>=40, b)
    rows=json.dumps(dev.sql("SELECT * FROM devices")); check('device ticket stored only as hash', DEV not in rows and cf_dev.TEST_PASS not in rows)
    s,b,_=req('POST','/api/login',{'key':KA,'device':'x'*43}); check('fake device ticket → need_invite', s==403 and b['error']=='need_invite', b)
    # 로그인
    s,b,_=req('POST','/api/login',{'device':DEV,'key':'live_WRONG_0123456789abcdef'}); check('invalid key → 401 invalid_key', s==401 and b['error']=='invalid_key', b)
    s,b,_=req('POST','/api/login',{'device':DEV,'key':'short'}); check('malformed key → 400', s==400 and b['error']=='bad_key', b)
    s,b,_=req('POST','/api/login',{'device':DEV,'key':'live_RATE_0123456789abcdef'}); check('Nexon 429 → 429', s==429 and b['error']=='nexon_rate', b)
    s,a1,_=req('POST','/api/login',{'device':DEV,'key':KA,'label':'PC방'}); check('login A → token, new user, rev 0', s==200 and a1['newUser'] and len(a1['token'])>=40 and a1['rev']==0 and len(a1['accounts'])==1, a1)
    TA=a1['token']
    check('Nexon called with the key header on the list endpoint', ('/maplestory/v1/character/list',KA) in MN.SEEN)
    s,b,_=req('GET','/api/state',tok=TA); check('empty state → rev 0, data null', s==200 and b['rev']==0 and b['data'] is None, b)
    s,b,_=req('GET','/api/state'); check('no token → 401', s==401 and b['error']=='no_session', b)
    s,b,_=req('GET','/api/state',tok='x'*43); check('bad token → 401', s==401, b)
    # 저장 (키는 서버에서 제거)
    st={'version':5,'characters':[{'id':'c1','name':'단풍용사'}],'settings':{'apiKey':KA,'accounts':[{'id':'a1','label':'본계정','key':KA,'ah':a1['accounts'][0]}]},'updatedAt':111}
    s,b,_=req('PUT','/api/state',{'baseRev':0,'updatedAt':111,'data':st},tok=TA); check('first save → rev 1', s==200 and b['rev']==1, b)
    s,b,_=req('GET','/api/state',tok=TA); check('read back, keys stripped server-side, ah kept', b['rev']==1 and b['updatedAt']==111 and b['data']['characters'][0]['name']=='단풍용사' and 'key' not in b['data']['settings']['accounts'][0] and 'apiKey' not in b['data']['settings'] and b['data']['settings']['accounts'][0]['ah']==a1['accounts'][0], b)
    rows=dev.sql("SELECT data FROM state UNION ALL SELECT data FROM state_history")
    check('raw API key never stored in D1 (state + history)', rows and not any(KA in r['data'] for r in rows), len(rows))
    allrows=json.dumps(dev.sql("SELECT * FROM accounts"))+json.dumps(dev.sql("SELECT * FROM sessions"))+json.dumps(dev.sql("SELECT * FROM users"))
    check('no raw key / account_id / token in accounts·sessions·users tables', KA not in allrows and 'acc-A' not in allrows and TA not in allrows)
    s,b,_=req('GET','/api/state/meta',tok=TA); check('meta has rev/updatedAt, no data', b=={'rev':1,'updatedAt':111,'savedAt':b['savedAt']} and 'data' not in b, b)
    # 다른 기기 (같은 키 → 같은 데이터)
    s,a2,_=req('POST','/api/login',{'device':DEV,'key':KA}); TA2=a2['token']; check('2nd device same key → same user, not new, rev 1', not a2['newUser'] and a2['user']==a1['user'] and a2['rev']==1, a2)
    s,b,_=req('PUT','/api/state',{'baseRev':1,'updatedAt':222,'data':{**st,'updatedAt':222}},tok=TA2); check('device 2 saves rev 2', s==200 and b['rev']==2, b)
    s,b,_=req('PUT','/api/state',{'baseRev':1,'updatedAt':333,'data':st},tok=TA); check('device 1 stale baseRev → 409 with current state', s==409 and b['error']=='conflict' and b['rev']==2 and b['updatedAt']==222 and b['data'] is not None, b)
    s,b,_=req('PUT','/api/state',{'baseRev':0,'updatedAt':333,'data':st},tok=TA); check('baseRev 0 when state exists → 409', s==409, s)
    s,b,_=req('PUT','/api/state',{'baseRev':2,'updatedAt':333,'data':{'nope':1}},tok=TA); check('invalid state rejected', s==400 and b['error']=='bad_state', b)
    s,b,_=req('PUT','/api/state',raw=b'{"baseRev":2,"data":{"characters":[],"x":"'+b'a'*1900000+b'"}}',tok=TA); check('too large → 413', s==413, s)
    # 다른 사용자는 서로 분리
    s,bb,_=req('POST','/api/login',{'device':DEV,'key':KB}); TB=bb['token']; check('user B: new user, different id', bb['newUser'] and bb['user']!=a1['user'], bb)
    s,b,_=req('GET','/api/state',tok=TB); check('user B cannot see A data', b['rev']==0 and b['data'] is None, b)
    s,b,_=req('PUT','/api/state',{'baseRev':0,'updatedAt':5,'data':{'characters':[{'id':'b1','name':'B캐릭'}]}},tok=TB); s,b,_=req('GET','/api/state',tok=TA)
    check('A data unchanged by B save', b['data']['characters'][0]['name']=='단풍용사' and b['rev']==2, b)
    # 같은 사람의 다른 넥슨 계정 연결
    s,b,_=req('POST','/api/link',{'device':DEV,'key':KD},tok=TA); check('link key D to A', s==200 and len(b['all'])==2, b)
    s,d,_=req('POST','/api/login',{'device':DEV,'key':KD}); check('login with D → A data', d['user']==a1['user'] and d['rev']==2, d)
    s,b,_=req('POST','/api/link',{'device':DEV,'key':KB},tok=TA); check('link B (owned by another user) → 409', s==409 and b['error']=='linked_elsewhere', b)
    s,ac,_=req('POST','/api/login',{'device':DEV,'key':KAC}); check('key with accounts A+C → A data, C auto-linked', ac['user']==a1['user'] and len(ac['accounts'])==2, ac)
    s,me,_=req('GET','/api/me',tok=TA); check('me: 3 linked accounts, ≥4 sessions', len(me['accounts'])==3 and me['sessions']>=4 and me['rev']==2, me)
    # 부계정 키 금고: 대표 키(A)로 암호화 보관 → 다른 기기에서 대표 키만으로 로그인하면 되돌아옴
    KF,KG='live_KEY_F_0123456789abcdef','live_KEY_G_0123456789abcdef'
    s,b,_=req('PUT','/api/subkeys',{'main':KB,'subs':[{'key':KF,'label':'부1'}]},tok=TA); check('subkeys with a main key not of this data → 403', s==403 and b['error']=='not_main', b)
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KB,'label':'x'}]},tok=TA); check('sub key owned by another user → 409', s==409 and b['error']=='linked_elsewhere', b)
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KF,'label':'부1'},{'key':KG,'label':'부2'},{'key':KA,'label':'dup main'}]},tok=TA)
    check('store 2 sub keys (main key skipped) → ah returned, linked', s==200 and [x['label'] for x in b['subs']]==['부1','부2'] and len(b['accounts'])==5, b)
    vrows=json.dumps(dev.sql("SELECT * FROM keyvault")); dump=vrows+json.dumps(dev.sql("SELECT data FROM state"))+json.dumps(dev.sql("SELECT * FROM accounts"))
    check('vault holds only ciphertext (no raw main/sub keys)', '"ct"' in vrows and all(k not in dump for k in (KA,KF,KG)) and '부1' not in vrows)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KA}); check('new device, main key only → sub keys come back', v['vault']=='open' and sorted(x['key'] for x in v['subKeys'])==sorted([KF,KG]) and {x['label'] for x in v['subKeys']}=={'부1','부2'} and all(x['ah'] for x in v['subKeys']), v)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KF}); check('login with a sub key → same data, vault locked, no keys', v['user']==a1['user'] and v['vault']=='locked' and v['subKeys']==[], v)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KAC}); check('different key (also on acc-A) cannot open vault', v['vault']=='locked' and v['subKeys']==[], v)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KB}); check('other user: vault none', v['vault']=='none' and v['subKeys']==[], v)
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KG,'label':'부2'}]},tok=TA); s,v,_=req('POST','/api/login',{'device':DEV,'key':KA})
    check('removing a sub key updates the vault', [x['key'] for x in v['subKeys']]==[KG], v)
    # 예비 키 (같은 넥슨 계정만, 금고에 함께 암호화)
    BKA,BKG='live_BK_A_0123456789abcdefg','live_BK_G_0123456789abcdefg'
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'mainBk':KF,'subs':[{'key':KG,'label':'부2'}]},tok=TA); check('backup key of another account → 400 backup_mismatch', s==400 and b['error']=='backup_mismatch', b)
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KG,'label':'부2','bk':BKA}]},tok=TA); check('sub backup of wrong account → 400', s==400 and b['error']=='backup_mismatch' and '부2' in b['message'], b)
    s,b,_=req('PUT','/api/subkeys',{'main':KA,'mainBk':BKA,'subs':[{'key':KG,'label':'부2','bk':BKG}]},tok=TA); check('backup keys of same accounts stored', s==200, b)
    vr=json.dumps(dev.sql("SELECT * FROM keyvault")); check('vault ciphertext only (no backup keys)', BKA not in vr and BKG not in vr)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KA}); check('login with main → backup keys come back', v['mainBk']==BKA and [x.get('bk') for x in v['subKeys']]==[BKG], v)
    s,v,_=req('POST','/api/login',{'device':DEV,'key':KF}); check('sub-key login → no backup keys', v['mainBk']=='' and v['subKeys']==[], v)
    # 로그아웃
    s,b,_=req('POST','/api/logout',tok=TA2); s2,b2,_=req('GET','/api/state',tok=TA2); s3,_,_=req('GET','/api/state',tok=TA)
    check('logout kills only that session', s==200 and s2==401 and s3==200, (s,s2,s3))
    s,b,_=req('POST','/api/logout-all',tok=TA); s2,_,_=req('GET','/api/state',tok=TA); check('logout-all kills all sessions', s==200 and b['removed']>=3 and s2==401, b)
    # 계정 삭제
    s,e,_=req('POST','/api/login',{'device':DEV,'key':KE}); TE=e['token']; req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'characters':[]}},tok=TE)
    s,b,_=req('DELETE','/api/account',tok=TE); s2,_,_=req('GET','/api/state',tok=TE); s3,e2,_=req('POST','/api/login',{'device':DEV,'key':KE})
    check('delete account → data + sessions gone, next login = new user', s==200 and s2==401 and e2['newUser'] and e2['rev']==0, (s,s2,e2))
    # 기록 보관 10개
    s,x,_=req('POST','/api/login',{'device':DEV,'key':KB}); tb=x['token']; rev=x['rev']
    for i in range(12):
        s,b,_=req('PUT','/api/state',{'baseRev':rev,'updatedAt':100+i,'data':{'characters':[],'i':i}},tok=tb); rev=b['rev']
    n=dev.sql(f"SELECT COUNT(*) AS n FROM state_history h JOIN accounts a ON a.user_id=h.user_id WHERE a.acct_hash='{x['accounts'][0]}'")[0]['n']
    check('history keeps last 10 revisions', n==10, n)
    # 세션별 읽기 제한 (90회/분) — 다른 세션은 영향 없음
    s,x2,_=req('POST','/api/login',{'device':DEV,'key':KD}); t1=x2['token']; s,x3,_=req('POST','/api/login',{'device':DEV,'key':KD}); t2=x3['token']
    codes=[req('GET','/api/state/meta',tok=t1)[0] for _ in range(95)]
    s9,b9,h9=req('GET','/api/state/meta',tok=t1); s10,_,_=req('GET','/api/state/meta',tok=t2)
    check('per-session read limit → 429 + Retry-After; other session still OK', codes.count(200)==90 and s9==429 and b9['error']=='too_many' and h9.get('Retry-After') and s10==200, (codes.count(200),s9,h9.get('Retry-After'),s10))
    # 저장 제한 (세션 20회/분)
    rv=req('GET','/api/state/meta',tok=t2)[1]['rev']; wc=[]
    for i in range(22):
        s,b,_=req('PUT','/api/state',{'baseRev':rv,'updatedAt':i,'data':{'characters':[]}},tok=t2); wc.append(s); rv=b.get('rev',rv)
    check('per-session write limit (20/min) → 429', wc.count(200)==20 and wc[-1]==429, wc)
    # 초대 비밀번호 시도 제한 (IP별 10회/10분)
    ic=[req('POST','/api/invite',{'pass':'nope'})[0] for _ in range(10)]
    check('invite attempts rate-limited → 429', 429 in ic and req('POST','/api/invite',{'pass':cf_dev.TEST_PASS})[0]==429, ic)
    # 로그인 시도 제한 (30회/10분)
    codes=[req('POST','/api/login',{'device':DEV,'key':'live_WRONG_0123456789abcdef'})[0] for _ in range(30)]
    check('login rate limit → 429 too_many', 429 in codes and req('POST','/api/login',{'device':DEV,'key':KA})[1]['error']=='too_many', codes[-5:])
    # SITE_PASS_HASH 없음 → 로그인 전부 거부 (fail closed)
    dev.stop(); dev=cf_dev.Dev(WP,NP,no_pass=True)
    s1,b1,_=req('POST','/api/invite',{'pass':cf_dev.TEST_PASS}); s2,b2,_=req('POST','/api/login',{'key':KA,'device':DEV})
    check('no SITE_PASS_HASH → invite/login refused (503 not_configured)', s1==503 and s2==503 and b2['error']=='not_configured', (s1,s2))
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
