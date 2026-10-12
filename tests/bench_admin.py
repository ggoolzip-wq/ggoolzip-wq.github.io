# 관리자 창 속도 측정 (wrangler dev 로컬 D1): 사용자 N명 + 상태 데이터 → GET /api/admin/users, POST decide reject
import os, sys, json, time, urllib.request, urllib.error, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
NP, WP, N = 8906, 8905, int(os.environ.get('N','40'))
def req(m,path,body=None,tok=None):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    t=time.perf_counter()
    try:
        with urllib.request.urlopen(r,timeout=60) as res: out=(res.status, json.loads(res.read() or b'null'))
    except urllib.error.HTTPError as e: out=(e.code, json.loads(e.read() or b'null'))
    return out+((time.perf_counter()-t)*1000,)
MN.KEYS['live_ADMIN_0123456789abcdef']=['acc-ADM']
for i in range(N): MN.KEYS[f'live_U{i:03d}_0123456789abcdef']=[f'acc-U{i}']
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
    s,a,_=req('POST','/api/login',{'key':'live_ADMIN_0123456789abcdef'}); TA=a['token']; UA=dev.sql('SELECT id FROM users')[0]['id']
    dev.sql(f"INSERT INTO meta (k,v) VALUES ('admin_user','{UA}')")
    ch=lambda i,lv: {'id':f'c{i}','name':f'캐릭{i}','level':lv,'world':'스카니아','accId':'a1','bosses':{},'drops':{}}
    for i in range(N):
        dev.sql("DELETE FROM rate")
        s,b,_=req('POST','/api/login',{'key':f'live_U{i:03d}_0123456789abcdef'})
        if b and b.get('token'): req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':{'version':5,'characters':[ch(j,200+j) for j in range(12)],'settings':{'accounts':[{'id':'a1','label':'본계정','main':True}]}}},tok=b['token'])
    dev.sql("INSERT INTO approval (user_id,status,requested_at) SELECT id,'pending',1 FROM users WHERE id<>'"+UA+"' ORDER BY created_at DESC LIMIT 5 ON CONFLICT(user_id) DO UPDATE SET status='pending'")
    T=[req('GET','/api/admin/users',tok=TA)[2] for _ in range(5)]
    s,u,_=req('GET','/api/admin/users',tok=TA); print('users',len(u['users']),'payload bytes',len(json.dumps(u,ensure_ascii=False).encode()))
    pend=[x['id'] for x in u['users'] if x['status']=='pending']
    R=[req('POST','/api/admin/decide',{'user':p,'action':'reject'},tok=TA)[2] for p in pend[:3]]
    print(f'GET users median {statistics.median(T):.0f}ms (all {[round(x) for x in T]}) ; reject median {statistics.median(R):.0f}ms {[round(x) for x in R]}')
finally:
    dev.stop(); ms.shutdown()
