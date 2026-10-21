# b234: 본계정(대표) 키 삭제 → /api/keygone 이 삭제 시각 기록 + 세션 끝. 30일 안에 다시 로그인/다른 기기 사용 = 취소, 지나면 cron(keyGoneCron)이 사용자 데이터 전부 삭제
# wrangler dev(로컬 D1, --test-scheduled) — 운영 D1 은 건드리지 않음. 포트 = _tutil.free_port()
import os, sys, json, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('FAILS: []'); sys.exit(0)
NP, WP = _tutil.free_port(), _tutil.free_port()
DAY=86400000
def req(m,path,body=None,tok=None,raw=False):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: b=res.read(); return res.status, (b if raw else json.loads(b or b'null'))
    except urllib.error.HTTPError as e:
        b=e.read()
        try: return e.code, json.loads(b or b'null')
        except Exception: return e.code, b
ms=MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
for x in ['M','O','R','S']: MN.KEYS[K(x)]=[f'acc-b234-{x}']
dev=cf_dev.Dev(WP,NP,args=('--test-scheduled',))
def cron(): s,b=req('GET','/__scheduled?cron=*+*+*+*+*',raw=True); time.sleep(1.5); return s
def uid(x): return dev.sql(f"SELECT a.user_id FROM accounts a WHERE a.acct_hash IN (SELECT acct_hash FROM accounts) ORDER BY created_at")
def login(x): return req('POST','/api/login',{'key':K(x)})
try:
    T={}; U={}
    for x in 'MORS':
        s,a=login(x); T[x]=a.get('token'); check(f'{x} 로그인', s==200 and T[x], a)
        req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'characters':[{'id':'c'+x,'name':'캐'+x}],'history':[{'week':'2026-09-28','total':5}]}},tok=T[x])
        U[x]=dev.sql(f"SELECT user_id FROM sessions ORDER BY created_at DESC LIMIT 1")[0]['user_id']
    check('users.key_gone_at 열 있음', any(c['name']=='key_gone_at' for c in dev.sql("PRAGMA table_info(users)")))
    s,b=req('POST','/api/keygone',tok=T['M']); check('M 본계정 키 삭제 → /api/keygone 200', s==200 and b.get('purgeAfterDays')==30, (s,b))
    kg=dev.sql(f"SELECT key_gone_at FROM users WHERE id='{U['M']}'")[0]['key_gone_at']
    check('삭제 시각 기록', kg and abs(kg-time.time()*1000)<120000, kg)
    s,b=req('GET','/api/me',tok=T['M']); check('그 세션은 끝남(401)', s==401, s)
    s,b=req('POST','/api/keygone'); check('로그인 없이 keygone → 401', s==401, s)
    # R: 삭제 후 30일 안에 다시 로그인 = 취소
    req('POST','/api/keygone',tok=T['R']); s,a=login('R')
    check('R 다시 로그인 → 예약 취소(NULL)·데이터 그대로', dev.sql(f"SELECT key_gone_at FROM users WHERE id='{U['R']}'")[0]['key_gone_at'] is None and a.get('rev',0)>=1, a)
    # S: 다른 기기 세션이 아직 쓰임 = 취소
    s,a2=login('S'); T2=a2.get('token'); req('POST','/api/keygone',tok=T['S'])
    s,b=req('GET','/api/me',tok=T2); check('S 다른 기기 세션 사용 → 예약 취소', s==200 and dev.sql(f"SELECT key_gone_at FROM users WHERE id='{U['S']}'")[0]['key_gone_at'] is None, (s,b))
    # 30일 전: cron 이 지우지 않음
    dev.sql("DELETE FROM meta WHERE k='keygone_cron'"); cron()
    check('30일 전 cron: M 데이터 그대로', len(dev.sql(f"SELECT 1 FROM state WHERE user_id='{U['M']}'"))==1)
    check('cron 1시간 제한 기록(meta)', len(dev.sql("SELECT 1 FROM meta WHERE k='keygone_cron'"))==1)
    # 31일 전으로 당김(가짜 시각) — 1시간 제한 안이면 건너뜀
    dev.sql(f"UPDATE users SET key_gone_at=key_gone_at-{31*DAY} WHERE id='{U['M']}'"); cron()
    check('1시간 안 다시 실행 = 건너뜀(아직 안 지움)', len(dev.sql(f"SELECT 1 FROM users WHERE id='{U['M']}'"))==1)
    dev.sql("DELETE FROM meta WHERE k='keygone_cron'"); cron()
    left={t:len(dev.sql(f"SELECT 1 FROM {t} WHERE user_id='{U['M']}'")) for t in ['state','state_history','sessions','accounts','acct_role','keyreg','keyvault2']}
    check('30일 지남: M 사용자·데이터·계정 연결 전부 삭제', not dev.sql(f"SELECT 1 FROM users WHERE id='{U['M']}'") and not any(left.values()), left)
    for x in 'ORS': check(f'키 있는 {x} 데이터 그대로', len(dev.sql(f"SELECT 1 FROM state WHERE user_id='{U[x]}'"))==1 and len(dev.sql(f"SELECT 1 FROM users WHERE id='{U[x]}'"))==1)
    dev.sql("DELETE FROM meta WHERE k='keygone_cron'"); cron()
    check('다시 실행해도 문제없음(idempotent)', all(len(dev.sql(f"SELECT 1 FROM users WHERE id='{U[x]}'"))==1 for x in 'ORS'))
    s,a=login('M'); s2,st=req('GET','/api/state',tok=a.get('token'))
    check('삭제 뒤 같은 키로 다시 등록 = 새로 시작(예전 기록 없음)', s==200 and a.get('newUser') and a.get('rev')==0, (a,st))
finally:
    try: dev.stop()
    except Exception: pass
    ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
