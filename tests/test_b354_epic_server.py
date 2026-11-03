# b354: 에픽빔 클립 서버 저장 (R2 + D1) — wrangler dev 로컬 R2/D1 (운영 버킷·D1 건드리지 않음)
# 같은 넥슨 계정(acct_hash) 기준으로 보임 · 2MB 제한 · 인증 · 12개 페이지 · 30일 미동기화 삭제(cron)·계정 삭제에도 클립 유지 · R2 없으면 503 r2_off
import os, sys, json, time, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); print('FAILS: []'); sys.exit(0)
NP, WP, WP2 = _tutil.free_port(), _tutil.free_port(), _tutil.free_port()
DAY=86400000; PORT=[WP]
def req(m,path,body=None,tok=None,raw=None,hdr=None,want_raw=False):
    h={'Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {}),**(hdr or {})}
    data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if raw is None: h['Content-Type']='application/json'
    else: h['Content-Type']='application/octet-stream'
    r=urllib.request.Request(f'http://127.0.0.1:{PORT[0]}{path}',data=data,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: b=res.read(); return res.status, (b if want_raw else json.loads(b or b'null'))
    except urllib.error.HTTPError as e:
        b=e.read()
        try: return e.code, json.loads(b or b'null')
        except Exception: return e.code, b
MN.start(NP); K=lambda x:f'live_KEY_{x}_0123456789abcdef'
for x in ['P','Q']: MN.KEYS[K(x)]=[f'acc-b354-{x}']
MN.KEYS[K('P2')]=['acc-b354-P']   # 같은 넥슨 계정의 다른 키 (다른 PC)
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b354-%d.toml'%os.getpid())
t=open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read()
R2B='\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n'
cfg0=cfg.replace('.toml','-nor2.toml'); open(cfg0,'w').write(t.replace(R2B,'\n'))
open(cfg,'w').write(t.replace('\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n','\n').replace('[vars]','[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n\n[vars]',1))
def meta(i,**k): return urllib.parse.quote(json.dumps({'id':i,'t0':int(i[2:]),'boss':'검은 마법사','diff':'익스트림','item':'창세의 뱃지','cid':'c1','cname':'단풍용사','n':40,'w':426,'h':240,**k},ensure_ascii=False))
dev=None; dev2=None
try:
    dev=cf_dev.Dev(WP,NP,args=('-c',cfg,'--test-scheduled'))
    s,a=req('POST','/api/login',{'key':K('P')}); TP=a.get('token'); check('P 로그인', s==200 and TP, s)
    s,a=req('POST','/api/login',{'key':K('Q')}); TQ=a.get('token')
    blob=b'ECB1'+os.urandom(50000)
    s,b=req('POST','/api/epic/clip?id=ec1762000000000',raw=blob,hdr={'X-Epic-Meta':meta('ec1762000000000')})
    check('인증 없이 업로드 → 401', s==401, (s,b))
    s,b=req('POST','/api/epic/clip?id=ec1762000000000',raw=blob,tok=TP,hdr={'X-Epic-Meta':meta('ec1762000000000')})
    check('업로드 → 200 size', s==200 and b.get('size')==len(blob), (s,b))
    s,b=req('POST','/api/epic/clip?id=ec1762000000000',raw=blob,tok=TP,hdr={'X-Epic-Meta':meta('ec1762000000000')})
    check('같은 클립 다시 → dup (중복 저장 안 함)', s==200 and b.get('dup'), (s,b))
    s,b=req('POST','/api/epic/clip?id=ec1762000000001',raw=b'x'*(2*1024*1024+10),tok=TP,hdr={'X-Epic-Meta':meta('ec1762000000001')})
    check('2MB 넘음 → 413', s==413, (s,b))
    s,b=req('POST','/api/epic/clip?id=../../etc',raw=blob,tok=TP,hdr={'X-Epic-Meta':meta('ec1762000000002')})
    check('잘못된 id → 400', s==400, (s,b))
    s,b=req('POST','/api/epic/clip?id=ec1762000000003',raw=blob,tok=TP,hdr={'X-Epic-Meta':'%%%'})
    check('잘못된 메타 → 400', s==400, (s,b))
    for i in range(1,26):
        r_=req('POST',f'/api/epic/clip?id=ec17620000{i:05d}00',raw=b'ECB1'+bytes([i])*100,tok=TP,hdr={'X-Epic-Meta':meta(f'ec17620000{i:05d}00')})
        if r_[0]!=200: print('up',i,r_)
    s,b=req('GET','/api/epic/clips?page=0&per=12',tok=TP)
    check('목록 1쪽: total 26, 12개, 최신순, 메타 그대로', s==200 and b['total']==26 and len(b['items'])==12 and b['items'][0]['id']=='ec17620000'+'00025'+'00' and b['items'][0]['boss']=='검은 마법사', (s,b and {k:b[k] for k in ('total','page')}))
    s,b2=req('GET','/api/epic/clips?page=2&per=12',tok=TP); check('3쪽 = 2개', len(b2['items'])==2, b2.get('items'))
    ids=[x['id'] for p in range(3) for x in req('GET',f'/api/epic/clips?page={p}&per=12',tok=TP)[1]['items']]
    check('페이지 겹침·빠짐 없음', len(set(ids))==26, len(set(ids)))
    s,b=req('GET','/api/epic/clips',tok=TQ); check('다른 넥슨 계정(Q)은 못 봄', s==200 and b['total']==0, b)
    s,b=req('GET','/api/epic/clip/ec1762000000000',tok=TQ); check('Q 가 P 클립 받기 → 404', s==404, s)
    s,raw=req('GET','/api/epic/clip/ec1762000000000',tok=TP,want_raw=True); check('P 클립 받기 = 올린 바이트 그대로', s==200 and raw==blob, (s,len(raw) if isinstance(raw,bytes) else raw))
    s,a=req('POST','/api/login',{'key':K('P2')}); TP2=a.get('token')
    s,b=req('GET','/api/epic/clips?per=12',tok=TP2); check('다른 PC·같은 넥슨 계정의 다른 키로 로그인 → 26개 보임', b.get('total')==26, b.get('total'))
    rows=json.dumps(dev.sql('SELECT * FROM epic_clips'))
    check('D1 에 키·토큰 원본 없음', K('P') not in rows and TP not in rows)
    # 자동 삭제 없음: 30일 미동기화 cron 으로 사용자가 지워져도 클립은 그대로 → 같은 키로 새로 가입하면 다시 보임
    uP=dev.sql("SELECT user_id FROM epic_clips LIMIT 1")[0]['user_id']
    dev.sql(f"UPDATE users SET last_sync_at=last_sync_at-{31*DAY} WHERE id='{uP}'"); dev.sql("DELETE FROM meta WHERE k='syncgone_cron'")
    req('GET','/__scheduled?cron=*+*+*+*+*',want_raw=True); time.sleep(2)
    check('cron 이 P 사용자 삭제', len(dev.sql(f"SELECT 1 FROM users WHERE id='{uP}'"))==0)
    check('cron 뒤에도 클립 메타 26개 그대로', dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==26)
    s,a=req('POST','/api/login',{'key':K('P')}); TP3=a.get('token')
    s,b=req('GET','/api/epic/clips',tok=TP3); check('같은 키로 다시 가입(새 user_id) → 클립 26개 다시 보임', a.get('newUser') and b.get('total')==26, (a.get('newUser'),b.get('total')))
    s,raw=req('GET','/api/epic/clip/ec1762000000000',tok=TP3,want_raw=True); check('R2 파일도 그대로', s==200 and raw==blob)
    s,b=req('DELETE','/api/account',tok=TP3)
    check('계정 삭제(직접)해도 클립 메타 유지(자동 삭제 없음)', dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==26)
    s,b=req('OPTIONS','/api/epic/clip?id=ec1',hdr={'Access-Control-Request-Method':'PUT','Access-Control-Request-Headers':'x-epic-meta'},want_raw=True)
    check('CORS 사전요청이 X-Epic-Meta 허용', s==204)
    dev.stop()
    # R2 바인딩 뺀 설정(b355 부터 운영은 켜짐) → 503 r2_off
    PORT[0]=WP2; dev2=cf_dev.Dev(WP2,NP,args=('-c',cfg0))
    s,a=req('POST','/api/login',{'key':K('Q')}); s,b=req('GET','/api/epic/clips',tok=a.get('token'))
    check('R2 없으면 503 r2_off', s==503 and b.get('error')=='r2_off', (s,b))
finally:
    for d in (dev,dev2):
        if d: d.stop()
    try: os.remove(cfg); os.remove(cfg0)
    except Exception: pass
print('FAILS:',fails); sys.exit(1 if fails else 0)
