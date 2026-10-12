# b104(예전 b93): 관리자 전용 시세 — 관리자 창 '최저가 갱신' → (1~4.5초 무작위 대기) → Worker /api/admin/maple-prices(maple.ai.kr) 1번 → 우리 아이템으로 맞춤 → /api/admin/prices,
#      '수익을 기록할까요?' 금액 자동 채움(수정 가능) + '최저가 측정 시간 - YYYY-MM-DD HH:mm'(KST). 페이지에 없는 아이템은 그대로. 관리자가 아니면 없음. (Worker 는 가짜 응답)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8893
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':'a1','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','테스트캐')],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
T0=int(time.mktime(time.strptime('2026-10-12 18:05','%Y-%m-%d %H:%M'))*1000)  # 박스 = KST
SHOT=os.environ.get('SHOT_DIR'); BEFORE=os.environ.get('BEFORE')=='1'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(ext,admin=True):
        ctx=b.new_context(viewport={'width':900,'height':900},device_scale_factor=2)
        saved={'prices':{}, 'puts':0, 'mai':[]}
        def api(r):
            u=r.request.url
            if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'admin':admin,'user':'u0','accounts':[]}))
            if '/api/admin/prices' in u:
                if r.request.method=='PUT': saved['puts']+=1; saved['prices'].update(json.loads(r.request.post_data)['prices'])
                return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'prices':saved['prices']}))
            if '/api/admin/maple-prices' in u: saved['mai'].append(time.time()); return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'date':'2026-10-12','fetchedAt':T0,'items':{'마깃안':{'main':29.28},'데브팬':{'main':0.0889},'리4':{'main':39},'파풀마':{'main':1.9},'자석펫':{'main':166}}}))
            if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'users':[]}))
            return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body='{}')
        ctx.route('http://127.0.0.1:9999/**',lambda r: r.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("([s,a])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s)); localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9999'); localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43)); localStorage.setItem('mapleBossTracker.svAdmin',a?'1':'0')}",[ST,admin]); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("a=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin',a?'1':'0')}",admin)
        return ctx,pg,saved
    ask=lambda pg,ik: (pg.evaluate("ik=>{document.querySelector('#revModal')?.remove(); window.__c=window.__c||{id:'cx',name:'테스트캐',bosses:{},weekly:{},monthly:{},drops:{}}; askRev(window.__c,findBoss('lucid'),'lucid|'+ik.replace(/^cb:/,''),ik,()=>{});}",ik), pg.wait_for_timeout(150))
    ctx,pg,saved=mk(True)
    if BEFORE:
        ask(pg,'eye'); pg.locator('#revModal .modal').screenshot(path=f'{SHOT}/oct12z_b104_before_revmodal.png'); pg.evaluate("document.querySelector('#revModal').remove()")
        pg.evaluate("admUsers=[];admErr='';document.querySelector('#adminModal').classList.add('show');renderAdmin()"); pg.wait_for_timeout(200)
        pg.locator('#adminModal .modal').screenshot(path=f'{SHOT}/oct12z_b104_before_admin.png')
    else:
        pg.evaluate("openAdmin()"); pg.wait_for_timeout(300)
        btn=pg.locator('#admPriceBtn'); check("admin window has '최저가 갱신' button", btn.count()==1 and '최저가 갱신' in btn.inner_text())
        if SHOT: pg.locator('#adminModal .modal').screenshot(path=f'{SHOT}/oct12z_b104_after_admin.png')
        t0=time.time(); btn.click(); pg.wait_for_timeout(300)
        check('busy message while waiting', 'maple.ai.kr' in pg.inner_text('#admPrice'), pg.inner_text('#admPrice'))
        pg.wait_for_function("!admPriceBusy",timeout=10000)
        check('human-like: request ≥1s after click (random 1.2~4.5s), exactly 1 request', len(saved['mai'])==1 and 1.0<=saved['mai'][0]-t0<=5.0, [round(x-t0,2) for x in saved['mai']])
        check('results saved to Worker (PUT /api/admin/prices)', saved['puts']>=1 and saved['prices'].get('eye',{}).get('p')==2928000000, saved)
        check('status shown in admin window (3 mapped; 데브팬·자석펫 not in map)', '3개 갱신' in pg.inner_text('#admPrice') and '2026-10-12' in pg.inner_text('#admPrice'), pg.inner_text('#admPrice'))
        check('only mapped drop items saved (eye·papmark·ring_r4)', sorted(saved['prices'])==['eye','papmark','ring_r4'], saved['prices'])
        check('source note 출처: maple.ai.kr', '출처: maple.ai.kr' in pg.inner_text('#admPrice'))
        pg.evaluate("document.querySelector('#adminModal').classList.remove('show')")
        ask(pg,'eye')
        check('eye prefilled 29.28 (억)', pg.input_value('#rvAmt')=='29.28', pg.input_value('#rvAmt'))
        g=pg.inner_text('#rvGuide'); check("hint exactly '최저가 측정 시간 - 2026-10-12 18:05'", g.strip()=='최저가 측정 시간 - 2026-10-12 18:05', g)
        if SHOT: pg.locator('#revModal .modal').screenshot(path=f'{SHOT}/oct12z_b104_after_revmodal.png')
        pg.fill('#rvAmt','30'); pg.click('[data-rv=ok]'); pg.wait_for_timeout(200)
        check('editable: saved edited 30', pg.evaluate("window.__c.drev['lucid|eye'].a")==30)
        ask(pg,'papmark'); check('papmark 1.9', pg.input_value('#rvAmt')=='1.9', pg.input_value('#rvAmt'))
        ask(pg,'daybreak'); check('unmapped item (데브팬) → unchanged', pg.input_value('#rvAmt')=='')
        ask(pg,'cb:eye'); check('chaos box result eye prefilled', pg.input_value('#rvAmt')=='29.28')
        ask(pg,'ring:r4'); check('ring box result 리스트레인트 링 4레벨 prefilled 39', pg.input_value('#rvAmt')=='39', pg.input_value('#rvAmt'))
        ask(pg,'belt'); check('item not on page → unchanged (empty + original guide)', pg.input_value('#rvAmt')=='' and '최저가 측정' not in pg.inner_text('#rvGuide'))
        check('no extension code left in page', not pg.evaluate("typeof extVer!=='undefined'") and 'bossmaple-ext' not in open(os.path.join(ROOT,'index.html'),encoding='utf-8').read())
        ctx.close()
        ctx,pg,saved=mk(True,admin=False)
        pg.evaluate("localStorage.setItem('mapleBossTracker.admPrices',JSON.stringify({eye:{p:2928000000,t:%d}}))"%T0); ask(pg,'eye')
        check('non-admin: no prefill', pg.input_value('#rvAmt')=='' and '최저가 측정' not in pg.inner_text('#rvGuide'))
        ctx.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
