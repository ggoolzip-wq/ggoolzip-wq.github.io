import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8991=_tutil.free_port()
# b208: 시세 '- 메소' 아이템 = 관리자 손 입력 — maple.ai.kr 에 유효한 값이 있을 때만 바뀜 · 짝 없는 이름 기록 · 이름 후보로 새 아이템 맞춤 · 시세 등록 창 '시세 정보 없음'
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8991)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b208_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'blackmage':B('extreme'),'zakum':B('chaos')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
   'drops':{'lucid|whisper':1,'lucid|g_faith':1,'kaling|oath':1},'drev':{'lucid|whisper':{'m':500000000,'a':5,'p':1,'i':'whisper'},'kaling|oath':{'m':900000000,'a':9,'p':1,'i':'oath'}}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
MAI={'date':'2026-10-17','got':['lcm','tc','eye','belt','book','terror','cfe','sos','genesis','mitra','whisper','oath','bliss','spirit','legacy','papmark','g_life','g_faith','ring_r4','ring_c4','h_face','h_eye','h_belt','b_sjm']}
SRV={'prices':{'whisper':{'p':6200000000,'t':1760000000000},'h_face':{'p':6199000000,'t':1760000000000}},'puts':[],'pub':0,'nx':[]}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR')
    H={'Access-Control-Allow-Origin':'*'}
    def api(r):
        u=r.request.url
        if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'admin':True,'user':'u0','accounts':[]}))
        if u.endswith('/api/prices'): SRV['pub']+=1; return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/prices' in u:
            if r.request.method=='PUT': d=json.loads(r.request.post_data)['prices']; SRV['puts'].append(d); SRV['prices'].update(d)
            return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices'],'mai':MAI}))
        if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'users':[]}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body='{}')
    def nxapi(r):  # /maplestory/v1/id: 첫 호출 429(초당), 두 번째 200
        SRV['nx'].append(time.time())
        if 'tst429' in r.request.url and len([1 for _ in SRV['nx']])==1: return r.fulfill(status=429,content_type='application/json',headers=H,body=json.dumps({'error':{'name':'OPENAPI00007','message':'rate'}}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'ocid':'x1'}))
    ctx.route('http://127.0.0.1:9997/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else nxapi(r) if 'tst429' in r.request.url else r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9997');localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}")
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';save();render()}",ST); pg.wait_for_timeout(300)
    pg.evaluate("admPriceLoad()"); pg.wait_for_timeout(500)
    check('관리자 시세 받을 때 가장 새 시세 날짜에 받은 키(mai.got) 기억', pg.evaluate("admMaiGot&&admMaiGot.size")==len(MAI['got']) and pg.evaluate("admMaiDate")=='2026-10-17')
    pg.evaluate("openMkt()"); pg.wait_for_timeout(300)
    R=pg.evaluate("""[...document.querySelectorAll('#mktModal .rarow')].map(r=>{const n=r.querySelector('.raname'),x=r.querySelector('.mkno'),inp=r.querySelector('.rain');const xr=x&&x.getBoundingClientRect(),ir=inp.getBoundingClientRect();
      return {k:r.querySelector('[data-mk]').getAttribute('aria-label'),no:!!x,txt:x&&x.textContent,col:x&&getComputedStyle(x).color,fam:x&&getComputedStyle(x).fontFamily,nameFam:getComputedStyle(n).fontFamily,
        left:x?Math.round(ir.left-xr.right):null,clip:n.scrollWidth>n.clientWidth+1,h:Math.round(r.getBoundingClientRect().height),one:x?xr.height<24:true}})""")
    no=[x['k'].split(' 시세')[0] for x in R if x['no']]
    check("'시세 정보 없음' = 최신 날짜에 값 못 받은 아이템만(오만의 원죄·귀고리·포켓·펜던트(b252)·소울 에테르 1~4)", sorted(no)==sorted(['오만의 원죄','익셉셔널 해머 (귀고리)','익셉셔널 해머 (포켓)','익셉셔널 해머 (펜던트)','1단계 소울 에테르','2단계 소울 에테르','3단계 소울 에테르','4단계 소울 에테르']), no)
    bad=[x for x in R if x['no'] and not (x['txt']=='시세 정보 없음' and x['col'] in ('rgb(255, 107, 107)',) and 0<=x['left']<=12 and x['one'] and x['fam']==x['nameFam'])]
    check('빨간 글씨·메소 칸 바로 왼쪽·한 줄·이름과 같은 글꼴', not bad, bad[:2])
    check('이름 안 잘림·줄 높이 같음', not [x for x in R if x['clip']] and len({x['h'] for x in R})==1, ([x['k'] for x in R if x['clip']],{x['h'] for x in R}))
    shot(pg.locator('#mktModal .modal'),'mkt_dark')
    pg.evaluate("document.querySelector('#mktModal')?.remove(); document.documentElement.dataset.theme='light'; openMkt()"); pg.wait_for_timeout(300)
    c=pg.evaluate("getComputedStyle(document.querySelector('#mktModal .mkno')).color")
    check('라이트 모드 빨간색 진하게', c=='rgb(211, 47, 47)', c)
    shot(pg.locator('#mktModal .modal'),'mkt_light')
    b.close()
finally: srv.terminate()

# ---- Worker 쪽 (node, 모의 fetch·D1) ----
import shutil, tempfile
tmp=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'server','worker.js'),os.path.join(tmp,'w.mjs'))
js=r"""
const W=await import(process.argv[2]); const meta={}; let page={etag:'"a"',body:''};
const DB={prepare(sql){const st={sql,args:[],bind(...a){st.args=a;return st;},async first(){const k=st.args[0];return k in meta?{v:meta[k]}:null;},
  async run(){let k,v; const m=sql.match(/VALUES \('(\w+)',\?\)/); if(m){k=m[1];v=st.args[0];} else {[k,v]=st.args;} meta[k]=v; return {};}};return st;}, async batch(L){for(const s of L) await s.run();}};
globalThis.fetch=async(u,o)=>{ if(o.headers['If-None-Match']===page.etag) return new Response(null,{status:304}); return new Response(page.body,{status:200,headers:{ETag:page.etag}}); };
const mk=(d,it)=>'<script>self.__next_f.push([1,"x:{\\"data\\":[{\\"date\\":\\"'+d+'\\",\\"items\\":'+JSON.stringify(it).replace(/"/g,'\\"')+'}]}"])</script>';
const env={DB}; const K=(d,hm)=>Date.parse(d+'T'+hm+':00+09:00'); const P=()=>JSON.parse(meta.admin_prices||'{}'), U=()=>JSON.parse(meta.mai_unmatched||'null');
const o={};
// 관리자 손 입력: 오만의 원죄(sin)·소울 에테르(se1)·귀고리(h_ear, 짝 있음)·마깃안(eye, 짝 있음)
meta.admin_prices=JSON.stringify({sin:{p:111e8,t:K('2026-10-17','21:00')},se1:{p:2e8,t:K('2026-10-17','21:00')},h_ear:{p:55e8,t:K('2026-10-17','21:00')},eye:{p:30e8,t:K('2026-10-17','21:00')}});
// 10-18: 마깃안 값 0, 귀고리 null, 근원의 속삭임 정상, 새 이름 '신비한 반지' (짝 없음)
page.etag='"b"'; page.body=mk('2026-10-18',{'마깃안':{main:0},'익셉셔널 귀고리':{main:null},'근원의 속삭임':{main:60},'신비한 반지':{main:3}});
o.r1=[await W.maiCron(env,K('2026-10-18','15:30')),P(),U()];
// 같은 날 관리자가 손으로 고침(PUT 흉내: 더 새 t) → 그날 다음 회차·다음 날 304 에도 안 되돌아감
const p=P(); p.eye={p:31e8,t:K('2026-10-18','16:05')}; meta.admin_prices=JSON.stringify(p);
o.r2=[await W.maiCron(env,K('2026-10-18','16:30')),await W.maiCron(env,K('2026-10-19','00:00')),P().eye];
// 10-19: 페이지에 '오만의 원죄'·'소울 에테르 1단계'·마깃안 값이 생김 → 그때만 바뀜, 귀고리는 여전히 없음 → 손 입력 그대로
page.etag='"c"'; page.body=mk('2026-10-19',{'마깃안':{main:28.5},'오만의 원죄':{main:150},'소울 에테르 1단계':{main:2.5},'신비한 반지':{main:3},'근원의 속삭임':{main:61}});
o.r3=[await W.maiCron(env,K('2026-10-19','14:00')),P(),U()];
console.log(JSON.stringify(o));
"""
open(os.path.join(tmp,'t.mjs'),'w').write(js)
O=json.loads(subprocess.check_output(['node',os.path.join(tmp,'t.mjs'),os.path.join(tmp,'w.mjs')]).decode().strip().splitlines()[-1])
st,P1,U1=O['r1']; K1=1792234620000
check('10-18 새 날짜: 값 0(마깃안)·null(귀고리) = 손 입력 그대로(안 덮음·안 지움), 정상 값만 갱신', st=='new' and P1['eye']['p']==30e8 and P1['h_ear']['p']==55e8 and P1['sin']['p']==111e8 and P1['se1']['p']==2e8 and P1['whisper']['p']==60e8, P1)
check('짝 없는 새 이름 기록(meta.mai_unmatched: names·처음 본 날짜·못 받은 키)', U1 and U1['names']==['신비한 반지'] and U1['first']=={'신비한 반지':'2026-10-18'} and 'eye' in U1['missing'] and 'h_ear' in U1['missing'] and 'whisper' not in U1['missing'], U1)
check('관리자 손 저장 뒤 cron(같은 날·다음 날 304) = 안 되돌림', O['r2'][0]=='done_today' and O['r2'][1]=='same' and O['r2'][2]['p']==31e8, O['r2'])
st,P3,U3=O['r3']
check("10-19 페이지에 '오만의 원죄'·'소울 에테르 1단계' 생김 → 이름으로 맞춰 그때만 바뀜, 귀고리는 그대로", st=='new' and P3['sin']['p']==150e8 and P3['se1']['p']==2.5e8 and P3['eye']['p']==28.5e8 and P3['h_ear']['p']==55e8, P3)
check('처음 본 날짜는 유지', U3['first']=={'신비한 반지':'2026-10-18'} and 'sin' not in U3['missing'], U3)
check('app.js 에 짝 복사본 없음(MAI_CODE·maiMap 함수)', 'const MAI_CODE' not in open(os.path.join(ROOT,'src','app.js'),encoding='utf-8').read() and 'function maiMap' not in open(os.path.join(ROOT,'src','app.js'),encoding='utf-8').read())
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
