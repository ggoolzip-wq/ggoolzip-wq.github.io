# b388: 진단 메타(dg)가 실제 업로드 경로(X-Epic-Meta → 서버 parse·8192자 검사 → D1 meta → 목록 GET)에서 그대로 보존되는지 — wrangler dev 로컬 R2/D1 + 넥슨 모의 서버(운영 버킷·D1·계정 안 건드림)
import os, sys, json, subprocess, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN, _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP'); sys.exit(0)
# 실제 ecDiagOut/ecMetaOut 소스로 최악 크기 메타 생성 (lg 40개 최대 자릿수, 긴 닉네임·아이템, ecLink 의 recT 포함)
gen=r'''
const fs=require('fs'),vm=require('vm');const s=fs.readFileSync(process.argv[1],'utf8');
const pick=n=>{const i=s.indexOf('function '+n+'(');let d=0,j=s.indexOf('{',i);for(;j<s.length;j++){if(s[j]=='{')d++;else if(s[j]=='}'){d--;if(!d)break;}}return s.slice(i,j+1);};
const ctx={document:{documentElement:{dataset:{build:'b388'}}},JSON,Math};vm.createContext(ctx);
vm.runInContext(pick('ecDiagOut')+';'+s.match(/const ecMetaOut=[^;]*;[^;]*;\s*};/)[0]+';this.o=ecDiagOut;this.mo=ecMetaOut;',ctx);
const lg=Array.from({length:40},(_,i)=>[-1499+i*37,0.999,0.999,254.9]);
const dg=ctx.o({det:1999,src:'video',bmAge:599,sn:123456789,vw:3840,vh:2160,lg,kind:'shift',hitT:-999,commit:1999,map:{k:'rq',b:'blackmage',d:'extreme',age:7999},boss:'blackmage'},{n:120,gap:999,first:-1000,last:2999});
const big=ctx.o({lg:Array.from({length:400},(_,i)=>[i,0.123,0.456,78.9])},{n:120,gap:33,first:-1000,last:2966});
const m={id:'ec1794040000000',t0:1794040000000,vt0:123456.789012,boss:'blackmage',diff:'extreme',item:'x'.repeat(80),cid:'c'.repeat(60),cname:'가'.repeat(40),sc:0.999,w:1280,h:720,fps:30,codec:'vp9',n:120,start:-1000,end:3000,vts:[123455.789012,123459.789012],poster:null,pi:0,up:0,bytes:799999,format:'webm',dg,recT:1794040001234};
process.stdout.write(JSON.stringify({meta:ctx.mo(m),dgLen:JSON.stringify(dg).length,bigLen:JSON.stringify(big).length,bigKeys:Object.keys(big)}));'''
J=json.loads(subprocess.run(['node','-e',gen,os.path.join(ROOT,'src','epicclip.js')],capture_output=True,text=True,check=True).stdout)
meta=J['meta']; full=len(json.dumps(meta,ensure_ascii=False,separators=(',',':')))
print('sizes dg',J['dgLen'],'full meta JSON chars',full,'header bytes',len(urllib.parse.quote(json.dumps(meta,ensure_ascii=False,separators=(',',':')))),'oversize→',J['bigLen'],J['bigKeys'])
check('최악 dg ≤1600자 (잘림 없이 lg 40개 유지)',J['dgLen']<=1600 and len(meta['dg']['lg'])==40,J['dgLen'])
check('과대 dg 는 1600자 이하로 축소',J['bigLen']<=1600,J['bigLen'])
check('최악 전체 메타 JSON < 8192 (서버 검사 기준 JSON.stringify 길이)',full<8192,full)
NP,WP=_tutil.free_port(),_tutil.free_port(); K='live_KEY_D388_0123456789abcdef'
MN.start(NP); MN.KEYS[K]=['acc-b388-D']
t=open(os.path.join(cf_dev.SERVER,'wrangler.toml')).read(); R2B='\n[[r2_buckets]]\nbinding = "EPIC"\nbucket_name = "bossmaple-epic"\n'
cfg=os.path.join(cf_dev.SERVER,'.wrangler-b388-%d.toml'%os.getpid()); open(cfg,'w').write(t.replace(R2B,'\n').replace('[vars]',R2B.strip()+'\n\n[vars]',1))
def req(m,path,body=None,tok=None,raw=None,hdr=None):
    h={'Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {}),**(hdr or {})}
    h['Content-Type']='application/octet-stream' if raw is not None else 'application/json'
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=raw if raw is not None else (json.dumps(body).encode() if body is not None else None),method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=30) as res: return res.status,json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code,e.read()[:300]
dev=None
try:
    dev=cf_dev.Dev(WP,NP,args=('-c',cfg))
    s,a=req('POST','/api/login',{'key':K}); tok=a.get('token'); check('모의 로그인',s==200 and tok,s)
    hv=urllib.parse.quote(json.dumps(meta,ensure_ascii=False))
    s,b=req('POST','/api/epic/clip?id='+meta['id'],raw=b'\x1aE\xdf\xa3'+os.urandom(4000),tok=tok,hdr={'X-Epic-Meta':hv}); check('최악 크기 메타 업로드 200',s==200,(s,b))
    s,L=req('GET','/api/epic/clips?page=0&per=12',tok=tok); it=[x for x in (L.get('items') or []) if x['id']==meta['id']] if s==200 else []
    check('목록 GET 에 dg 그대로 보존(deep equal)',len(it)==1 and it[0].get('dg')==meta['dg'],it[0].get('dg') if it else (s,L))
    check('기존 필드 보존(boss/diff/item/cname/n/w/h/fps/format/recT)',it and all(it[0].get(k)==meta[k] for k in ('boss','diff','item','cname','n','w','h','fps','format','recT')),it[:1])
    over=dict(meta); over['pad']='z'*8200
    s,b=req('POST','/api/epic/clip?id=ec1794040000001',raw=b'\x1aE\xdf\xa3'+os.urandom(100),tok=tok,hdr={'X-Epic-Meta':urllib.parse.quote(json.dumps(over))}); check('대조: 8192 넘는 메타는 기존대로 400 bad_meta',s==400,(s,b))
finally:
    if dev: dev.stop()
    try: os.remove(cfg)
    except Exception: pass
print('RESULT','OK' if not fails else 'FAIL '+','.join(fails)); sys.exit(1 if fails else 0)
