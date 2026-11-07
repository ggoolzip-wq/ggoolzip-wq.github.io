# b390: 에픽빔 클립 단일 삭제 API + 삭제 이력(tombstone) — wrangler dev 로컬 R2/D1 + 넥슨 모의 서버 (운영 버킷·D1·실계정 안 건드림, 실 키 사용 없음)
# 범위(사용자·연결 계정)·존재 비노출·다른 계정 같은 id 보존·공유 R2 보존·R2 재시도·중복/없는 id·재업로드(부활) 거부·이력 페이지·기존 목록/다운로드 호환
import os, sys, json, time, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); sys.exit(0)
NP, WP = _tutil.free_port(), _tutil.free_port()
def req(m,path,body=None,tok=None,raw=None,hdr=None,want_raw=False):
    h={'Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {}),**(hdr or {})}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h['Content-Type']='application/octet-stream' if raw is not None else 'application/json'
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=data,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: b=res.read(); return res.status,(b if want_raw else json.loads(b or b'null'))
    except urllib.error.HTTPError as e:
        b=e.read()
        try: return e.code,json.loads(b or b'null')
        except Exception: return e.code,b
MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
MN.KEYS[K('P')]=['acc-b390-P']; MN.KEYS[K('P2')]=['acc-b390-P']; MN.KEYS[K('Q')]=['acc-b390-Q']
t=open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read(); R2B='\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n'
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b390-%d.toml'%os.getpid()); open(cfg,'w').write(t.replace(R2B,'\n').replace('[vars]',R2B.strip()+'\n\n[vars]',1))
def meta(i,**k): return urllib.parse.quote(json.dumps({'id':i,'t0':int(i[2:]),'boss':'dusk','diff':'chaos','item':'','cid':'c1','cname':'테스트','n':120,'w':1280,'h':720,'format':'webm',**k},ensure_ascii=False))
def up(i,tok,blob): return req('POST','/api/epic/clip?id='+i,raw=blob,tok=tok,hdr={'X-Epic-Meta':meta(i)})
ids=lambda tok:[x['id'] for x in req('GET','/api/epic/clips?per=48',tok=tok)[1]['items']]
dev=None
try:
    dev=cf_dev.Dev(WP,NP,args=('-c',cfg))
    TP=req('POST','/api/login',{'key':K('P')})[1]['token']; TQ=req('POST','/api/login',{'key':K('Q')})[1]['token']; TP2=req('POST','/api/login',{'key':K('P2')})[1]['token']
    A,B,C='ec1794033431494','ec1793879339857','ec1794032772754'   # fixture id 만 사용 (실서버 호출 아님)
    bA,bB,bC,bQ=b'\x1aE\xdf\xa3'+os.urandom(3000),b'\x1aE\xdf\xa3'+os.urandom(3000),b'ECB1'+os.urandom(2000),b'\x1aE\xdf\xa3'+os.urandom(2500)
    check('업로드 P:A,B,C / Q:같은 id A',all(up(i,tok,b)[0]==200 for i,tok,b in [(A,TP,bA),(B,TP,bB),(C,TP,bC),(A,TQ,bQ)]))
    s,b=req('DELETE','/api/epic/clip/'+A); check('인증 없이 DELETE → 401',s==401,(s,b))
    s,b=req('DELETE','/api/epic/clip/'+B,tok=TQ); check('Q 가 P 전용 B 삭제 → 404 no_clip(존재 비노출)',s==404 and b.get('error')=='no_clip',(s,b))
    check('B 는 P 에 그대로',B in ids(TP))
    s,b=req('DELETE','/api/epic/clip/ec1700000000000',tok=TP); check('없는 id → 404 no_clip',s==404 and b.get('error')=='no_clip',(s,b))
    s,b=req('DELETE','/api/epic/clip/../x',tok=TP); check('잘못된 id 형식 → 404 not_found(정규식 그대로)',s==404 and b.get('error')=='not_found',(s,b))
    s,b=req('DELETE','/api/account/x',tok=TP); check('계정 전체 삭제 경로는 안 씀(별도 주소 없음)',s==404,(s,b))
    s,b=req('DELETE','/api/epic/clip/'+A,tok=TP)
    check('P 가 A 삭제 → 200 deleted 1, R2 1개 삭제',s==200 and b.get('ok') and b.get('id')==A and b.get('deleted')==1 and not b.get('already') and b['r2']=={'deleted':1,'kept':0,'failed':0},(s,b))
    check('P 목록에서 A 사라짐, B·C 유지',A not in ids(TP) and B in ids(TP) and C in ids(TP),ids(TP))
    s,_=req('GET','/api/epic/clip/'+A,tok=TP,want_raw=True); check('P 가 A 받기 → 404',s==404,s)
    s,raw=req('GET','/api/epic/clip/'+A,tok=TQ,want_raw=True); check('다른 계정 Q 의 같은 id A 는 행·R2 그대로',s==200 and raw==bQ and A in ids(TQ),(s,))
    s,raw=req('GET','/api/epic/clip/'+B,tok=TP,want_raw=True); check('기존 다운로드 호환(B 바이트 그대로)',s==200 and raw==bB)
    s,b=req('DELETE','/api/epic/clip/'+A,tok=TP); check('같은 id 다시 DELETE → 200 already, deleted 0',s==200 and b.get('already') is True and b.get('deleted')==0,(s,b))
    s,b=up(A,TP,bA); check('P 가 오래된 캐시로 A 재업로드 → 410 deleted(부활 거부)',s==410 and b.get('error')=='deleted',(s,b))
    s,b=up(A,TP2,bA); check('같은 넥슨 계정 다른 PC(P2)도 A 재업로드 → 410',s==410,(s,b))
    check('재업로드 거부 뒤에도 P 목록에 A 없음',A not in ids(TP))
    s,b=req('GET','/api/epic/deleted',tok=TP)
    check('P 삭제 이력 = [A], id·at 만(키·닉네임·계정해시 없음), complete',s==200 and [x['id'] for x in b['items']]==[A] and all(set(x)=={'id','at'} for x in b['items']) and b['complete'] is True,(s,b))
    check('P2(같은 계정) 이력도 A',[x['id'] for x in req('GET','/api/epic/deleted',tok=TP2)[1]['items']]==[A])
    s,b=req('GET','/api/epic/deleted',tok=TQ); check('Q 이력에는 P 의 삭제 안 보임',s==200 and b['items']==[] and b['complete'] is True,(s,b))
    s,b=up(A,TQ,bQ); check('Q 는 자기 A 그대로(dup), 410 아님',s==200 and b.get('dup'),(s,b))
    raw_tomb=json.dumps(dev.sql('SELECT * FROM epic_tomb')); check('이력 D1 에 키·토큰 원본·닉네임 없음',K('P') not in raw_tomb and TP not in raw_tomb and '테스트' not in raw_tomb)
    # 공유 R2: 다른 사용자 행이 같은 r2key 를 가리키면 남김
    rk=dev.sql(f"SELECT r2key FROM epic_clips WHERE id='{C}'")[0]['r2key']; qa=dev.sql(f"SELECT user_id,acct_hash FROM epic_clips WHERE id='{A}'")[0]
    dev.sql(f"INSERT INTO epic_clips (id,user_id,acct_hash,t0,meta,r2key,size,created_at) VALUES ('{C}','{qa['user_id']}','{qa['acct_hash']}',{C[2:]},'{{}}','{rk}',{len(bC)},1)")
    s,b=req('DELETE','/api/epic/clip/'+C,tok=TP); check('공유 R2 객체 → P 행만 삭제, R2 kept 1',s==200 and b.get('deleted')==1 and b['r2']=={'deleted':0,'kept':1,'failed':0},(s,b))
    s,raw=req('GET','/api/epic/clip/'+C,tok=TQ,want_raw=True); check('다른 계정이 참조하는 R2 객체 그대로 받음',s==200 and raw==bC,s)
    # R2 정리 실패 뒤 재시도: r2_done=0 으로 남은 키를 다음 DELETE 때 다시 지움
    s,_=up('ec1794000000001',TP,b'ECB1'+os.urandom(500)); rk2=dev.sql("SELECT r2key FROM epic_clips WHERE id='ec1794000000001'")[0]['r2key']
    pa=dev.sql("SELECT user_id,acct_hash FROM epic_clips WHERE id='ec1794000000001'")[0]
    dev.sql(f"DELETE FROM epic_clips WHERE id='ec1794000000001'"); dev.sql(f"INSERT INTO epic_tomb (acct_hash,id,user_id,deleted_at,r2key,r2_done) VALUES ('{pa['acct_hash']}','ec1794000000001','{pa['user_id']}',{int(time.time()*1000)},'{rk2}',0)")
    s,b=req('DELETE','/api/epic/clip/ec1794000000001',tok=TP); check('R2 실패로 남은 객체 → 재 DELETE 때 정리(already, r2 deleted 1)',s==200 and b.get('already') and b['r2']['deleted']==1,(s,b))
    check('재시도 후 r2_done=1',dev.sql("SELECT r2_done FROM epic_tomb WHERE id='ec1794000000001'")[0]['r2_done']==1)
    # 이력 페이지: 같은 deleted_at 여러 개도 빠짐·겹침 없음
    at=int(time.time()*1000)+5000
    for i in range(7): dev.sql(f"INSERT INTO epic_tomb (acct_hash,id,user_id,deleted_at,r2key,r2_done) VALUES ('{pa['acct_hash']}','ec17950000000{i:02d}','{pa['user_id']}',{at},NULL,1)")
    got=[]; after=0; aid=''
    for _ in range(10):
        s,b=req('GET',f'/api/epic/deleted?after={after}&aid={aid}&limit=3',tok=TP); got+= [x['id'] for x in b['items']]
        if b['complete']: break
        after,aid=b['next']['after'],b['next']['aid']
    check('이력 3개씩 페이지: 같은 시각 7개 포함 전부, 중복 없음',len(got)==len(set(got))==10 and b['complete'],got)
    s,b=req('GET','/api/epic/deleted?aid=../x',tok=TP); check('이력 커서 id 검증 → 400',s==400,(s,b))
    s,b=up('ec1794000000002',TP,b'ECB1'+os.urandom(300)); check('삭제 안 한 새 id 업로드는 기존대로 200',s==200 and b.get('ok'),(s,b))
    s,b=req('GET','/api/epic/clips?page=0&per=12',tok=TP); check('기존 목록 형식(total/page/per/items) 유지',s==200 and set(b)=={'total','page','per','items'} and b['total']==2,(s,b))
    s,b=req('OPTIONS','/api/epic/clip/'+B,hdr={'Access-Control-Request-Method':'DELETE'},want_raw=True); check('CORS 사전요청 DELETE 허용',s==204,s)
finally:
    if dev: dev.stop()
    try: os.remove(cfg)
    except Exception: pass
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
