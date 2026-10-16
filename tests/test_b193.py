# b193: Worker 1분 공지 감시 → 결정석 가격표 파싱(prParse, nexon_prices.parse_post 와 같은 결과) + 사이트가 feed.prices 를 prices.json 위에 덮음
import os, sys, json, time, subprocess, urllib.request, re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8966'
sys.path.insert(0,os.path.join(ROOT,'scripts')); import nexon_prices
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
FX=os.path.join(ROOT,'tests','fixtures','update_813.html')
js=r"""const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');const pick=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b));
const f=new Function(src.match(/const unent = [^\n]*\n/)[0]+pick('const PR_MIN_ROWS','const kstIso')+'return prParse;')();
console.log(JSON.stringify(f(fs.readFileSync(process.argv[2],'utf8'))));"""
out=json.loads(subprocess.check_output(['node','-e',js,os.path.join(ROOT,'server','worker.js'),FX]))
py=nexon_prices.parse_post(open(FX,encoding='utf-8').read())
k=lambda L:[(r['boss'],r.get('old'),r['new'],r.get('effective')) for r in L]
check('Worker prParse = 파이썬 parse_post (46줄·적용일 같음)', len(out['rows'])>=20 and k(out['rows'])==k(py['rows']), (len(out['rows']),len(py['rows'])))
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1100},locale='ko-KR')
    PJ=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8'))
    rows=[dict(r) for r in PJ['rows']]; rows[0]['new']=rows[0]['new']+11111
    SP={'id':99999,'source':{'url':'https://maplestory.nexon.com/News/Update/99999','title':'테스트 공지','date':'2026.10.17'},'rows':rows,'notes':[],'checkedAt':'2099-01-01T00:00:00+09:00','changedAt':'2026-10-17'}
    LIVE={'at':0,'list':[],'feed':{'items':{'saryo':[],'patch':[]},'sunday':None,'chk':{},'prices':SP}}
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('**/api/live*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(LIVE)))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(1500)
    pg.evaluate("liveFetch()"); pg.wait_for_timeout(800)
    r=pg.evaluate("(r=>{const m=parseBossLabel(r.boss);return [PRICE_CONFIG[priceKey(m.b,m.d)],officialInfo.checkedAt,officialInfo.source.url]})(arguments[0])",rows[0]) if False else pg.evaluate("r=>{const m=parseBossLabel(r.boss);return [PRICE_CONFIG[priceKey(m.b,m.d)],officialInfo.checkedAt,officialInfo.source.url]}",rows[0])
    check('새 공지 id → Worker 가격으로 바뀜 + 마지막 확인 갱신', r[0]==rows[0]['new'] and r[1].startswith('2099') and r[2].endswith('/99999'), r)
    SP2=dict(SP,id=1,rows=[dict(x,new=1) for x in PJ['rows']],checkedAt='2099-02-01T00:00:00+09:00'); LIVE['feed']['prices']=SP2
    pg.evaluate("localStorage.removeItem('mapleBossTracker.srvPrices'); srvPrSig=''; liveFetch()"); pg.wait_for_timeout(800)
    r=pg.evaluate("r=>{const m=parseBossLabel(r.boss);return [PRICE_CONFIG[priceKey(m.b,m.d)],officialInfo.checkedAt]}",PJ['rows'][0])
    check('옛 공지 id → 줄은 prices.json 그대로, 마지막 확인만 늦은 쪽', r[0]==PJ['rows'][0]['new'] and r[1].startswith('2099-02'), r)
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
