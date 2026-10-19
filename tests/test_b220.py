# b220: 자동(cron) 시세 갱신 뒤에도 시세 등록 창 '시세 정보 없음' — [최저가 갱신] 과 똑같은 상태 (서버 maiInfo 하나)
import os, sys, json, time, subprocess, urllib.request, shutil, tempfile
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8974'
SHOT=os.environ.get('MBT_SHOTDIR'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
# maple.ai.kr 2026-10-18 표의 이름들(값은 아무거나) — 실제 페이지 요청 없음
ITEMS={n:{'main':v} for n,v in {"루컨마":12.22,"마깃안":27.77,"몽벨":39,"거공":42.89,"고근":49.89,"커포":13.7,"언더컨트롤":199.6,"창뱃":190.56,"블랙하트(스카)":12.5,"리4":36.56,"컨4":25.56,"자석펫":168.33,"연마석(스카)":8.94,"신마석(스카)":30.33,"영달포":9.3,"익셉셔널 눈장":234.56,"익셉셔널 벨트":63.86,"익셉셔널 얼장":61.3,"익셉셔널 훈장":800,"도미":8.3,"블빈마":0.95,"데브팬":0.0289,"파풀마":1.8,"솔 에르다 조각":0.0599,"에스텔라":0.0045,"트왈마":0.005,"가엔링":0.02,"미트라":10.32,"마도서":39.43,"에테르넬 모자":0.18,"에테르넬 상의":0.2,"에테르넬 하의":0.22,"에테르넬 견장":0.2,"에테르넬 신발":18.99,"에테르넬 장갑":18.07,"에테르넬 망토":19.02,"근원의 속삭임":577,"죽음의 맹세":715,"불멸의 유산":700,"황홀한 악몽":607,"굶주리는 핏빛 원혼":743}.items()}

# ---- Worker (node, 모의 fetch·D1): cron 이 받은 뒤 /api/admin/prices 의 mai == [최저가 갱신](/api/admin/maple-prices) 의 mai ----
tmp=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'server','worker.js'),os.path.join(tmp,'w.mjs'))
js=r"""
const W=await import(process.argv[2]); const ITEMS=JSON.parse(process.argv[3]); const meta={}; let page={etag:'"a"',body:''}, nf=0;
const DB={prepare(sql){const st={sql,args:[],bind(...a){st.args=a;return st;},async first(){const k=st.args[0];return k in meta?{v:meta[k]}:null;},
  async run(){let k,v; const m=sql.match(/VALUES \('(\w+)',\?\)/); if(m){k=m[1];v=st.args[0];} else {[k,v]=st.args;} meta[k]=v; return {};}};return st;}, async batch(L){for(const s of L) await s.run();}};
globalThis.fetch=async(u,o)=>{ nf++; if(o.headers['If-None-Match']===page.etag) return new Response(null,{status:304}); return new Response(page.body,{status:200,headers:{ETag:page.etag}}); };
const mk=(d,it)=>'<script>self.__next_f.push([1,"x:{\\"data\\":[{\\"date\\":\\"'+d+'\\",\\"items\\":'+JSON.stringify(it).replace(/"/g,'\\"')+'}]}"])</script>';
const env={DB}; const K=(d,hm)=>Date.parse(d+'T'+hm+':00+09:00');
meta.admin_prices=JSON.stringify({sin:{p:111e8,t:K('2026-10-17','21:00')},se1:{p:2e8,t:K('2026-10-17','21:00')},se2:{p:3e8,t:K('2026-10-17','21:00')},se3:{p:4e8,t:K('2026-10-17','21:00')},se4:{p:5e8,t:K('2026-10-17','21:00')},h_ear:{p:55e8,t:K('2026-10-17','21:00')}});
page.etag='"b"'; page.body=mk('2026-10-18',ITEMS);
const o={}; o.cron=await W.maiCron(env,K('2026-10-18','16:00'));
const cv=JSON.parse(meta.mai_cache); o.auto=W.maiInfo(cv); o.prices=JSON.parse(meta.admin_prices); o.um=JSON.parse(meta.mai_unmatched);
const x=await W.maiRefresh(env,K('2026-10-18','16:10'),'admin'); o.manualStatus=x.status; o.manual=W.maiInfo(x.cv); o.mapped=Object.keys(W.maiMap(x.cv.items,0)).sort();
o.src=String(await (await import('fs')).promises.readFile(process.argv[2],'utf8'));
o.nf=nf; console.log(JSON.stringify({...o,src:undefined,hasMaiInMaple:/mai: maiInfo\(cv\)/.test(o.src),getUses:/const mi = maiInfo\(cv\)/.test(o.src)}));
"""
open(os.path.join(tmp,'t.mjs'),'w').write(js)
O=json.loads(subprocess.check_output(['node',os.path.join(tmp,'t.mjs'),os.path.join(tmp,'w.mjs'),json.dumps(ITEMS,ensure_ascii=False)]).decode().strip().splitlines()[-1])
HAND=['h_ear','se1','se2','se3','se4','sin']
check('cron 새 날짜 받음', O['cron']=='new', O['cron'])
check('자동(cron) mai == 수동([최저가 갱신]) mai (같은 날짜·같은 got)', O['auto']['date']==O['manual']['date']=='2026-10-18' and sorted(O['auto']['got'])==sorted(O['manual']['got'])==O['mapped'], (O['auto'],O['manual']))
check('got 에 없는 키 = 손 입력 아이템(오만의 원죄·소울 에테르 1~4·귀고리)뿐', sorted(set(O['um']['missing']))==HAND and not (set(HAND)&set(O['auto']['got'])), O['um']['missing'])
check('손 입력 값 보존(cron 이 안 덮음)', all(O['prices'][k]['p']>0 and O['prices'][k]['t']==1792238400000 for k in HAND), {k:O['prices'][k] for k in HAND})
check('짝 없는 18개 = 사이트가 기록하지 않는 아이템(여명 회색 칩·에테르넬 방어구·훈장 등) — 짝 버그 아님', len(O['um']['names'])==18 and '데브팬' in O['um']['names'], O['um']['names'])
check('두 GET 이 같은 maiInfo 사용', O['hasMaiInMaple'] and O['getUses'])
check('maple.ai.kr 요청 = 모의 2번(cron 1·수동 1, 304)', O['nf']==2 and O['manualStatus']=='same', O['nf'])
MAI={k:O['auto'][k] for k in ('date','got')}

# ---- 페이지: 버튼 안 누르고 자동 갱신 상태만으로 '시세 정보 없음' ----
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'blackmage':B('extreme'),'jupiter':B('hard')},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{},'drev':{}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
SRV={'prices':{'whisper':{'p':577e8,'t':1792306848939},'sin':{'p':111e8,'t':1792238400000}},'mai':MAI,'getp':0,'maple':0}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR')
    H={'Access-Control-Allow-Origin':'*'}
    def api(r):
        u=r.request.url; J=lambda o: r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps(o))
        if u.endswith('/api/me'): return J({'admin':True,'user':'u0','accounts':[]})
        if u.endswith('/api/prices'): return J({'prices':SRV['prices']})
        if '/api/admin/maple-prices' in u: SRV['maple']+=1; return J({'date':'2026-10-18','mapped':{k:{'p':1e8,'t':1} for k in SRV['mai']['got']},'missing':HAND,'mai':SRV['mai'],'cached':True})
        if '/api/admin/prices' in u:
            if r.request.method=='GET': SRV['getp']+=1
            return J({'prices':SRV['prices'],'mai':SRV['mai']})
        if '/api/admin/users' in u: return J({'users':[],'prices':SRV['prices']})
        return J({})
    ctx.route('http://127.0.0.1:9997/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    ctx.route('https://maple.ai.kr/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9997');localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}")
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';save();render()}",ST); pg.wait_for_timeout(200)
    # 시작 때처럼: 공용 시세를 막 받은 직후(60초 안)에 로그인 확인 → 예전엔 admPriceLoad 건너뜀
    pg.evaluate("()=>{admMaiGot=null; localStorage.removeItem('mapleBossTracker.admMai'); itemPriceLoad._at=Date.now(); gdMeta.on=true;}")
    g0=SRV['getp']; pg.evaluate("svAdminCheck()"); pg.wait_for_timeout(600)
    check('로그인 확인 때 공용 시세 60초 제한과 상관없이 관리자 시세·mai 받음', SRV['getp']>g0 and pg.evaluate("admMaiGot&&admMaiGot.size")==len(MAI['got']), (SRV['getp'],g0))
    check('mai 를 이 기기에 보관', json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.admMai')"))['date']=='2026-10-18')
    def miss():
        return sorted(r for r in pg.evaluate("[...document.querySelectorAll('#mktModal .rarow')].filter(r=>r.querySelector('.mkno')).map(r=>r.dataset.pid)"))
    # 메모리에 아무것도 없는 상태(새 탭·버튼 안 누름)로 창 열기 → 열 때 받아서 칠함
    pg.evaluate("()=>{admMaiGot=null; localStorage.removeItem('mapleBossTracker.admMai');}")
    g0=SRV['getp']; pg.evaluate("openMkt()"); pg.wait_for_timeout(600)
    auto_miss=miss()
    check('창 열 때 서버 mai 받음', SRV['getp']>g0)
    rows=pg.evaluate("[...document.querySelectorAll('#mktModal .rarow')].map(r=>r.dataset.pid)")
    exp=sorted(k for k in rows if k not in MAI['got'])
    check("자동 갱신만으로 '시세 정보 없음' 표시 (손 입력 아이템)", auto_miss==exp and set(auto_miss)<=set(HAND) and 'sin' in auto_miss, (auto_miss,exp))
    R=pg.evaluate("[...document.querySelectorAll('#mktModal .mkno')].map(x=>{const inp=x.nextElementSibling;return {t:x.textContent,c:getComputedStyle(x).color,next:inp&&inp.classList.contains('rain')}})")
    check('빨간 글씨·메소 칸 바로 왼쪽', R and all(x['t']=='시세 정보 없음' and x['c']=='rgb(255, 107, 107)' and x['next'] for x in R), R[:2])
    check('입력값은 그대로(손 입력 오만의 원죄 111억)', pg.evaluate("document.querySelector('#mktModal .rarow[data-pid=sin] input').value")=='111')
    if SHOT: pg.locator('#mktModal .modal').screenshot(path=os.path.join(SHOT,'b220_mkt_after_cron.png'))
    # 다음 날 cron 이 소울 에테르 1 을 새로 받음 → 열려 있는 창도 다시 받으면 바로 지워짐 / 캐시는 즉시 그려짐
    SRV['mai']={'date':'2026-10-19','got':MAI['got']+['se1']}
    pg.evaluate("admPriceLoad()"); pg.wait_for_timeout(500)
    check('열린 창 제자리 갱신(se1 표시 사라짐)', 'se1' not in miss() and 'sin' in miss(), miss())
    pg.evaluate("document.querySelector('#mktModal')?.remove()")
    SRV['mai']=MAI
    # 수동 [최저가 갱신] 길 → 같은 표시
    pg.evaluate("admPriceRun()"); pg.wait_for_function("!admPriceBusy",timeout=5000); pg.evaluate("openMkt()"); pg.wait_for_timeout(500)
    check('수동 [최저가 갱신] 뒤 표시 == 자동 갱신 뒤 표시', miss()==auto_miss, (miss(),auto_miss))
    pg.evaluate("document.querySelector('#mktModal')?.remove(); document.documentElement.dataset.theme='light'; openMkt()"); pg.wait_for_timeout(500)
    if SHOT: pg.locator('#mktModal .modal').screenshot(path=os.path.join(SHOT,'b220_mkt_after_cron_light.png'))
    check('빌드 표시 b220 이상', int(pg.evaluate("document.documentElement.dataset.build")[1:])>=220)
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
