# b390: 운영처럼 epic_tomb 없는 기존 D1(b389 schema.sql) 위에 새 worker 를 띄우면 ensureSchema 가 표·색인을 만들고(멱등) 기존 클립은 그대로 — 로컬 wrangler/D1 만
import os, sys, json, subprocess, tempfile, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); sys.exit(0)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old=subprocess.run(['git','show','86019cb:server/schema.sql'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
check('기준 schema 에 epic_tomb 없음','epic_tomb' not in old)
d=tempfile.mkdtemp(prefix='cfdev'); f=os.path.join(d,'old.sql'); open(f,'w').write(old)
env=dict(os.environ,PATH=cf_dev.NODE_BIN+':'+os.environ.get('PATH',''),CI='1'); w=os.path.join(cf_dev.SERVER,'node_modules','.bin','wrangler')
subprocess.run([w,'d1','execute','ggoolzip-sync','--local','--persist-to',d,'--file='+f],cwd=cf_dev.SERVER,env=env,check=True,capture_output=True)
subprocess.run([w,'d1','execute','ggoolzip-sync','--local','--persist-to',d,'--command',"INSERT INTO epic_clips (id,user_id,acct_hash,t0,meta,r2key,size,created_at) VALUES ('ec1790000000000','u','h',1790000000000,'{}','clips/h/ec1790000000000.ecb',1,1)"],cwd=cf_dev.SERVER,env=env,check=True,capture_output=True)
NP,WP=_tutil.free_port(),_tutil.free_port(); K='live_KEY_M390_0123456789abcdef'; MN.start(NP); MN.KEYS[K]=['acc-b390-M']
t=open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read(); R2B='\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n'
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b390m-%d.toml'%os.getpid()); open(cfg,'w').write(t.replace(R2B,'\n').replace('[vars]',R2B.strip()+'\n\n[vars]',1))
def req(m,path,body=None,tok=None):
    h={'Origin':'https://bossmaple.pages.dev','Content-Type':'application/json',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: return res.status,json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code,e.read()[:200]
dev=None
try:
    dev=cf_dev.Dev(WP,NP,persist=d,args=('-c',cfg))
    tok=req('POST','/api/login',{'key':K})[1]['token']
    s,b=req('GET','/api/epic/deleted',tok=tok); check('첫 요청 → epic_tomb 자동 생성, 빈 이력',s==200 and b['items']==[] and b['complete'] is True,(s,b))
    tabs={r['name'] for r in dev.sql("SELECT name FROM sqlite_master WHERE type IN ('table','index')")}
    check('표·색인 생성',{'epic_tomb','epic_tomb_user','epic_tomb_at','epic_r2key'}<=tabs,tabs)
    check('기존 클립 행 그대로',dev.sql("SELECT COUNT(*) n FROM epic_clips")[0]['n']==1)
    dev.stop(); dev=cf_dev.Dev(WP,NP,persist=d,args=('-c',cfg))
    s,b=req('GET','/api/epic/deleted',tok=tok); check('다시 띄워도(멱등 DDL) 정상',s==200,(s,b))
    r=subprocess.run([w,'d1','execute','ggoolzip-sync','--local','--persist-to',d,'--file=schema.sql'],cwd=cf_dev.SERVER,env=env,capture_output=True,text=True)
    check('새 schema.sql 재실행도 멱등(IF NOT EXISTS)',r.returncode==0,r.stderr[-300:])
finally:
    if dev: dev.stop()
    try: os.remove(cfg)
    except Exception: pass
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
