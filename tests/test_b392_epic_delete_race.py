# b392: 삭제·업로드 동시성(인터리빙) 회귀 — 테스트 전용 진입점(tests/fixtures/b392/race_entry.js, X-Epic-Test-Hold 헤더로 R2 put 앞/뒤 지연)으로 순서를 고정. 운영 worker.js 에는 지연 코드 없음. 로컬 wrangler R2/D1 + 모의 넥슨만.
#  R1 검사 통과 → (R2 put 전) 멈춘 업로드 / R2 put 후 멈춘 업로드가 DELETE 뒤에 DB 쓰기 → 410, 행·R2 부활 없음, 다른 계정 같은 id 보존
#  R2 경쟁 중복 업로드 → 행 1개 · R3 경쟁 중복 DELETE → 실제 삭제 1번만 deleted 1 · R4 거부 업로드의 R2 정리 실패 표시(r2_done=0) → 다음 DELETE 재시도
import os, sys, re, json, time, threading, subprocess, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); sys.exit(0)
NP,WP=_tutil.free_port(),_tutil.free_port()
def req(m,path,body=None,tok=None,raw=None,hdr=None,want_raw=False):
    h={'Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {}),**(hdr or {})}
    h['Content-Type']='application/octet-stream' if raw is not None else 'application/json'
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None),method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=60) as res: b=res.read(); return res.status,(b if want_raw else json.loads(b or b'null'))
    except urllib.error.HTTPError as e:
        b=e.read()
        try: return e.code,json.loads(b or b'null')
        except Exception: return e.code,b
MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
MN.KEYS[K('P')]=['acc-b390r-P']; MN.KEYS[K('P2')]=['acc-b390r-P']; MN.KEYS[K('Q')]=['acc-b390r-Q']
t=open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read(); R2B='\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n'
check('운영 worker.js·wrangler.toml 에 테스트 지연 코드 없음',all(x not in t+open(os.path.join(cf_dev.SERVER,'worker.js'),encoding='utf-8').read() for x in ('EPIC_TEST_HOLD','X-Epic-Test','epicTestHold')))
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b390r-%d.toml'%os.getpid()); ENTRY=os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'fixtures','b392','race_entry.js'),cf_dev.SERVER)
t2=re.sub(r'(?m)^main\s*=.*$','main = "'+ENTRY+'"',t); assert t2!=t
open(cfg,'w').write(t2.replace(R2B,'\n').replace('[vars]',R2B.strip()+'\n\n[vars]',1))
meta=lambda i:urllib.parse.quote(json.dumps({'id':i,'t0':int(i[2:]),'boss':'dusk','diff':'chaos','n':120,'w':1280,'h':720,'format':'webm'}))
def up(i,tok,blob,hold=None): return req('POST','/api/epic/clip?id='+i,raw=blob,tok=tok,hdr={'X-Epic-Meta':meta(i),**({'X-Epic-Test-Hold':hold} if hold else {})})
def bg(fn,*a):
    out={}
    def run(): t=time.time(); out['r']=fn(*a); out['dt']=time.time()-t
    th=threading.Thread(target=run); th.start(); return th,out
dev=None
try:
    dev=cf_dev.Dev(WP,NP,args=('-c',cfg))
    env=dict(os.environ,PATH=cf_dev.NODE_BIN+':'+os.environ.get('PATH',''),CI='1'); w=os.path.join(cf_dev.SERVER,'node_modules','.bin','wrangler')
    def r2has(key):
        r=subprocess.run([w,'r2','object','get','bossmaple-epic/'+key,'--local','--persist-to',dev.dir,'-c',cfg,'--pipe'],cwd=cf_dev.SERVER,env=env,capture_output=True)
        return r.returncode==0 and len(r.stdout)>0
    def tkey(i):
        ah=dev.sql("SELECT acct_hash FROM epic_tomb WHERE id='%s' LIMIT 1"%i)[0]['acct_hash']; return 'clips/%s/%s.ecb'%(ah[:16],i)
    rows=lambda i:dev.sql(f"SELECT acct_hash,r2key FROM epic_clips WHERE id='{i}'")
    TP=req('POST','/api/login',{'key':K('P')})[1]['token']; TP2=req('POST','/api/login',{'key':K('P2')})[1]['token']; TQ=req('POST','/api/login',{'key':K('Q')})[1]['token']
    for tk in (TP,TP2,TQ): req('GET','/api/epic/clips?per=1',tok=tk) # 예열(첫 요청 지연이 순서를 흐리지 않게)
    # Q 계정의 같은 id (보호 대상)
    for i in ('ec1794100000001','ec1794100000002'): check('Q 같은 id 업로드 '+i,up(i,TQ,b'\x1aE\xdf\xa3Q'+os.urandom(800))[0]==200)
    qkey={i:rows(i)[0]['r2key'] for i in ('ec1794100000001','ec1794100000002')}
    # R1a: P2 업로드가 검사 통과 후 R2 put 전에 멈춤 → P 업로드·DELETE 완료 → P2 가 put + DB 쓰기 시도
    X='ec1794100000001'; th,o=bg(up,X,TP2,b'\x1aE\xdf\xa3late'+os.urandom(900),'4000,0'); time.sleep(1.5)
    s,_=up(X,TP,b'\x1aE\xdf\xa3first'+os.urandom(900)); pk=[r['r2key'] for r in rows(X) if r['r2key']!=qkey[X]]
    check('R1a: P 업로드 200 (P2 는 멈춤 중)',s==200 and len(pk)==1,(s,rows(X)))
    s,b=req('DELETE','/api/epic/clip/'+X,tok=TP); check('R1a: P DELETE 200 deleted 1',s==200 and b['deleted']==1,(s,b))
    th.join(); s,b=o['r']
    check('R1a: P2 는 사전 검사를 통과한 뒤 지연 지점에서 멈췄음(≥3.5s)',o['dt']>=3.5,o['dt'])
    check('R1a: 늦은 P2 업로드 → 410 (원자적 SQL 가드)',s==410 and b.get('error')=='deleted',(s,b))
    check('R1a: P 범위 행 부활 없음, Q 행만 남음',[r['r2key'] for r in rows(X)]==[qkey[X]],rows(X))
    check('R1a: 늦은 put 이 만든 R2 객체 정리됨',not r2has(pk[0]))
    check('R1a: Q 의 R2 객체·다운로드 그대로',r2has(qkey[X]) and req('GET','/api/epic/clip/'+X,tok=TQ,want_raw=True)[0]==200)
    check('R1a: P 목록·다운로드에 없음',req('GET','/api/epic/clip/'+X,tok=TP,want_raw=True)[0]==404 and X not in [x['id'] for x in req('GET','/api/epic/clips?per=48',tok=TP)[1]['items']])
    check('R1a: 정리 완료 표시 r2_done=1',all(r['r2_done']==1 for r in dev.sql(f"SELECT r2_done FROM epic_tomb WHERE id='{X}'")),dev.sql(f"SELECT * FROM epic_tomb WHERE id='{X}'"))
    # R1b: P2 가 R2 put 까지 한 뒤 DB 쓰기 전에 멈춤
    Y='ec1794100000002'; th,o=bg(up,Y,TP2,b'\x1aE\xdf\xa3late2'+os.urandom(900),'0,4000'); time.sleep(1.5)
    s,_=up(Y,TP,b'\x1aE\xdf\xa3first2'+os.urandom(900)); s2,b2=req('DELETE','/api/epic/clip/'+Y,tok=TP); th.join(); s,b=o['r']; check('R1b: P2 R2 put 뒤 멈췄음(≥3.5s)',o['dt']>=3.5,o['dt'])
    pk2=tkey(Y)
    check('R1b: DELETE 200 → 늦은 DB 쓰기 410',s2==200 and b2['deleted']==1 and s==410,(s2,b2,s,b))
    check('R1b: P 행 없음, Q 행·객체 그대로',[r['r2key'] for r in rows(Y)]==[qkey[Y]] and r2has(qkey[Y]) and not r2has(pk2),rows(Y))
    # R2: 경쟁 중복 업로드(같은 계정 두 PC 동시) → 행 1개, 하나는 dup
    Z='ec1794100000003'; th,o=bg(up,Z,TP2,b'\x1aE\xdf\xa3z'+os.urandom(700),'0,1500'); time.sleep(0.5); s1,b1=up(Z,TP,b'\x1aE\xdf\xa3z'+os.urandom(700)); th.join(); s2,b2=o['r']
    check('R2: 동시 중복 업로드 둘 다 200, 하나 dup, 행 1개',s1==200 and s2==200 and (b1.get('dup') or b2.get('dup')) and len(rows(Z))==1,(b1,b2,rows(Z)))
    zk=rows(Z)[0]['r2key']; check('R2: 객체 존재·다운로드 200',r2has(zk) and req('GET','/api/epic/clip/'+Z,tok=TP,want_raw=True)[0]==200)
    # R3: 경쟁 중복 DELETE
    res=[None,None]; ths=[threading.Thread(target=lambda k=k:res.__setitem__(k,req('DELETE','/api/epic/clip/'+Z,tok=[TP,TP2][k]))) for k in (0,1)]
    [x.start() for x in ths]; [x.join() for x in ths]
    dl=[r[1].get('deleted') for r in res]
    check('R3: 동시 중복 DELETE 둘 다 200, 실제 삭제 합계 1, already 1개 이상',all(r[0]==200 for r in res) and sum(dl)==1 and any(r[1].get('already') for r in res),res)
    check('R3: 행·객체 없음, 재업로드 410',not rows(Z) and not r2has(zk) and up(Z,TP,b'\x1aE\xdf\xa3z'+os.urandom(10))[0]==410)
    # R4: 거부된 늦은 업로드의 R2 정리 실패 상황(객체 남음·r2_done=0) → 다음 DELETE 가 정리, 다른 계정 참조는 안 지움
    V='ec1794100000004'; check('R4 준비',up(V,TP,b'\x1aE\xdf\xa3v'+os.urandom(500))[0]==200 and req('DELETE','/api/epic/clip/'+V,tok=TP)[0]==200)
    vk=tkey(V)
    subprocess.run([w,'r2','object','put','bossmaple-epic/'+vk,'--local','--persist-to',dev.dir,'-c',cfg,'--pipe'],input=b'orphan',cwd=cf_dev.SERVER,env=env,capture_output=True)
    dev.sql(f"UPDATE epic_tomb SET r2_done=0, r2key='{vk}' WHERE id='{V}'")
    check('R4: 고아 객체 재현',r2has(vk))
    s,b=req('DELETE','/api/epic/clip/'+V,tok=TP); check('R4: 재 DELETE → already, r2 deleted 1, 객체 없음',s==200 and b['already'] and b['r2']['deleted']==1 and not r2has(vk),(s,b))
    check('끝: Q 의 두 클립 행·객체 그대로',all(rows(i) and r2has(qkey[i]) for i in qkey))
finally:
    if dev: dev.stop()
    try: os.remove(cfg)
    except Exception: pass
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
