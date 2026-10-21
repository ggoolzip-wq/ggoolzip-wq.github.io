# b234 → b235: 🔄 캐릭터 동기화 버튼(POST /api/sync-press = users.last_sync_at)을 30일 안 누른 사용자 → cron(syncGoneCron)이 데이터 전부 삭제. 관리자 제외.
# 로그인·로그아웃·/api/keygone(예전 페이지)·다른 기기 세션·자동 동기화(/api/sync-click)는 타이머와 무관. 같은 넥슨 계정 새 키 = 같은 사용자(기록 그대로).
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
def req(m,path,body=None,tok=None,raw=False,ip=None):
    h={**({'CF-Connecting-IP':ip} if ip else {}),'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: b=res.read(); return res.status, (b if raw else json.loads(b or b'null'))
    except urllib.error.HTTPError as e:
        b=e.read()
        try: return e.code, json.loads(b or b'null')
        except Exception: return e.code, b
ms=MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
for x in ['M','O','R','S','A']: MN.KEYS[K(x)]=[f'acc-b235-{x}']
MN.KEYS[K('R2')]=['acc-b235-R']  # 같은 넥슨 계정의 새 키
dev=cf_dev.Dev(WP,NP,args=('--test-scheduled',))
def cron(): s,b=req('GET','/__scheduled?cron=*+*+*+*+*',raw=True); time.sleep(1.5); return s
def login(x): return req('POST','/api/login',{'key':K(x)})
ls=lambda u: dev.sql(f"SELECT last_sync_at FROM users WHERE id='{u}'")[0]['last_sync_at']
exists=lambda u: len(dev.sql(f"SELECT 1 FROM users WHERE id='{u}'"))==1
def recron(): dev.sql("DELETE FROM meta WHERE k='syncgone_cron'"); cron()
try:
    T={}; U={}
    for x in 'MORSA':
        s,a=login(x); T[x]=a.get('token'); check(f'{x} 로그인', s==200 and T[x], a)
        req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'characters':[{'id':'c'+x,'name':'캐'+x}],'history':[{'week':'2026-09-28','total':5}]}},tok=T[x])
        U[x]=dev.sql(f"SELECT user_id FROM sessions ORDER BY created_at DESC LIMIT 1")[0]['user_id']
    check('users.last_sync_at 열 있음', any(c['name']=='last_sync_at' for c in dev.sql("PRAGMA table_info(users)")))
    check('새 가입 = last_sync_at 지금', all(ls(U[x]) and abs(ls(U[x])-time.time()*1000)<120000 for x in 'MORSA'))
    dev.sql(f"UPDATE users SET last_sync_at=NULL WHERE id='{U['O']}'")
    dev.sql(f"INSERT OR REPLACE INTO meta (k,v) VALUES ('admin_user','{U['A']}')")
    # 모두 31일 전으로 (O 는 NULL = 배포 전 기존 사용자 흉내)
    dev.sql(f"UPDATE users SET last_sync_at=last_sync_at-{31*DAY} WHERE last_sync_at IS NOT NULL")
    s,b=req('POST','/api/sync-press',tok=T['S']); check('S 🔄 누름 → /api/sync-press 200·last_sync_at 지금', s==200 and b.get('purgeAfterDays')==30 and abs(ls(U['S'])-time.time()*1000)<120000, (s,b))
    s,b=req('POST','/api/sync-press'); check('로그인 없이 sync-press → 401', s==401, s)
    req('POST','/api/sync-click',{},tok=T['M']); check('자동 동기화(sync-click)는 타이머 안 바꿈', time.time()*1000-ls(U['M'])>30*DAY)
    s,a=login('M'); req('GET','/api/me',tok=a.get('token')); req('POST','/api/logout',tok=a.get('token'))
    check('로그인·세션 사용·로그아웃은 타이머 안 바꿈', time.time()*1000-ls(U['M'])>30*DAY)
    s,b=req('POST','/api/keygone',tok=T['M']); check('예전 /api/keygone = 그냥 로그아웃(타이머 무관)', s==200 and time.time()*1000-ls(U['M'])>30*DAY and req('GET','/api/me',tok=T['M'])[0]==401, (s,b))
    # R: 키 삭제 후 같은 넥슨 계정의 새 키로 등록 = 같은 사용자, 기록 그대로 → 🔄 누르면 계속
    s,a=login('R2'); tR=a.get('token'); s2,st=req('GET','/api/state',tok=tR)
    uR2=dev.sql(f"SELECT user_id FROM sessions ORDER BY created_at DESC LIMIT 1")[0]['user_id']
    check('새 키(같은 넥슨 계정) = 같은 사용자·기록 그대로', uR2==U['R'] and not a.get('newUser') and a.get('rev',0)>=1, (a.get('newUser'),a.get('rev')))
    req('POST','/api/sync-press',tok=tR)
    s,_=req('GET','/__scheduled?cron=*+*+*+*+*',raw=True); time.sleep(1.5)
    recron()
    check('O(기존 사용자, 기록 없음) = 지금으로 채워져 안 지움', exists(U['O']) and ls(U['O']) and time.time()*1000-ls(U['O'])<120000, ls(U['O']) if exists(U['O']) else None)
    check('cron 1시간 제한 기록(meta)', len(dev.sql("SELECT 1 FROM meta WHERE k='syncgone_cron'"))==1)
    left={t:len(dev.sql(f"SELECT 1 FROM {t} WHERE user_id='{U['M']}'")) for t in ['state','state_history','sessions','accounts','acct_role','keyreg','keyvault2']}
    check('M 31일 🔄 안 누름: 사용자·데이터·계정 연결 전부 삭제', not exists(U['M']) and not any(left.values()), left)
    for x in 'SR': check(f'{x} 🔄 누름 → 그대로', exists(U[x]) and len(dev.sql(f"SELECT 1 FROM state WHERE user_id='{U[x]}'"))==1)
    check('관리자 A 는 31일 지나도 그대로', exists(U['A']) and len(dev.sql(f"SELECT 1 FROM state WHERE user_id='{U['A']}'"))==1)
    # 1시간 제한
    dev.sql(f"UPDATE users SET last_sync_at=last_sync_at-{31*DAY} WHERE id='{U['S']}'"); cron()
    check('1시간 안 다시 실행 = 건너뜀', exists(U['S']))
    recron(); check('제한 지나면 S 삭제', not exists(U['S']))
    recron(); check('idempotent', exists(U['R']) and exists(U['O']) and exists(U['A']))
    s,a=req('POST','/api/login',{'key':K('M')},ip='10.2.3.5');  # 새 가입 IP 하루 5개 제한 피함 check('삭제 뒤 같은 키로 다시 등록 = 새로 시작', s==200 and a.get('newUser') and a.get('rev')==0, a)
finally:
    try: dev.stop()
    except Exception: pass
    ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
