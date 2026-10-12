# b93: 관리자 전용 경매장 최저가 — 관리자 창 '최저가 갱신'(확장 postMessage 다리), 확장 없으면 설치 안내, 결과 → /api/admin/prices,
#      '수익을 기록할까요?' 금액 자동 채움(수정 가능) + '최저가 측정 시간 - YYYY-MM-DD HH:mm'(KST). 관리자가 아니면 없음. (가짜 확장 = 페이지에 넣은 content script 흉내)
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
FAKE_EXT="""(()=>{ const post=m=>window.postMessage({src:'bossmaple-ext',...m},location.origin); window.__extReq=[];
 window.addEventListener('message',e=>{ const m=e.data; if(!m||m.src!=='bossmaple-page') return; if(m.type==='ping') post({type:'hello',version:'1.0.0'});
  if(m.type==='refresh'){ window.__extReq.push(m.items); setTimeout(()=>post({type:'prices',reqId:m.reqId,ok:true,results:[{item:'eye',lowestPrice:2928000000,time:%d},{item:'daybreak',lowestPrice:8890000,time:%d}],skipped:[],posts:2,remaining:98,stop:''}),50); } });
 post({type:'hello',version:'1.0.0'}); })()""" % (T0,T0)
SHOT=os.environ.get('SHOT_DIR'); BEFORE=os.environ.get('BEFORE')=='1'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(ext,admin=True):
        ctx=b.new_context(viewport={'width':900,'height':900},device_scale_factor=2)
        saved={'prices':{}, 'puts':0}
        def api(r):
            u=r.request.url
            if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'admin':admin,'user':'u0','accounts':[]}))
            if '/api/admin/prices' in u:
                if r.request.method=='PUT': saved['puts']+=1; saved['prices'].update(json.loads(r.request.post_data)['prices'])
                return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'prices':saved['prices']}))
            if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({'users':[]}))
            return r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body='{}')
        ctx.route('http://127.0.0.1:9999/**',lambda r: r.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        if ext: ctx.add_init_script(FAKE_EXT)
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("([s,a])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s)); localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9999'); localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43)); localStorage.setItem('mapleBossTracker.svAdmin',a?'1':'0')}",[ST,admin]); pg.reload(); pg.wait_for_timeout(900)
        pg.evaluate("a=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin',a?'1':'0')}",admin)
        return ctx,pg,saved
    ask=lambda pg,ik: (pg.evaluate("ik=>{document.querySelector('#revModal')?.remove(); window.__c=window.__c||{id:'cx',name:'테스트캐',bosses:{},weekly:{},monthly:{},drops:{}}; askRev(window.__c,findBoss('lucid'),'lucid|'+ik.replace(/^cb:/,''),ik,()=>{});}",ik), pg.wait_for_timeout(150))
    ctx,pg,saved=mk(True)
    if BEFORE:
        ask(pg,'eye'); pg.locator('#revModal .modal').screenshot(path=f'{SHOT}/oct12z_b93_before_revmodal.png'); pg.evaluate("document.querySelector('#revModal').remove()")
        pg.evaluate("admUsers=[];admErr='';document.querySelector('#adminModal').classList.add('show');renderAdmin()"); pg.wait_for_timeout(200)
        pg.locator('#adminModal .modal').screenshot(path=f'{SHOT}/oct12z_b93_before_admin.png')
    else:
        pg.evaluate("openAdmin()"); pg.wait_for_timeout(300)
        btn=pg.locator('#admPriceBtn'); check("admin window has '최저가 갱신' button", btn.count()==1 and '최저가 갱신' in btn.inner_text())
        if SHOT: pg.locator('#adminModal .modal').screenshot(path=f'{SHOT}/oct12z_b93_after_admin.png')
        btn.click(); pg.wait_for_timeout(500)
        req=pg.evaluate("window.__extReq")
        names=[x['name'] for x in (req[0] if req else [])]; keys=[x['key'] for x in (req[0] if req else [])]
        check('items sent to extension: sellable only', '마력이 깃든 안대' in names and 'chaosbox' not in keys and 'cfs' not in keys and not any(k.startswith('e_') or k.startswith('r_') or k.startswith('se') for k in keys), keys)
        check('results saved to Worker (PUT /api/admin/prices)', saved['puts']>=1 and saved['prices'].get('eye',{}).get('p')==2928000000, saved)
        check('status shown in admin window', '2개' in pg.inner_text('#admPrice'), pg.inner_text('#admPrice'))
        pg.evaluate("document.querySelector('#adminModal').classList.remove('show')")
        ask(pg,'eye')
        check('eye prefilled 29.28 (억)', pg.input_value('#rvAmt')=='29.28', pg.input_value('#rvAmt'))
        g=pg.inner_text('#rvGuide'); check("hint exactly '최저가 측정 시간 - 2026-10-12 18:05'", g.strip()=='최저가 측정 시간 - 2026-10-12 18:05', g)
        if SHOT: pg.locator('#revModal .modal').screenshot(path=f'{SHOT}/oct12z_b93_after_revmodal.png')
        pg.fill('#rvAmt','30'); pg.click('[data-rv=ok]'); pg.wait_for_timeout(200)
        check('editable: saved edited 30', pg.evaluate("window.__c.drev['lucid|eye'].a")==30)
        ask(pg,'daybreak'); check('small price 0.0889', pg.input_value('#rvAmt')=='0.0889', pg.input_value('#rvAmt'))
        ask(pg,'cb:eye'); check('chaos box result eye prefilled', pg.input_value('#rvAmt')=='29.28')
        ask(pg,'cfs'); check('no price → empty + original guide', pg.input_value('#rvAmt')=='' and '최저가 측정' not in pg.inner_text('#rvGuide'))
        ctx.close()
        ctx,pg,saved=mk(False)
        pg.evaluate("openAdmin()"); pg.wait_for_timeout(300); pg.click('#admPriceBtn'); pg.wait_for_timeout(1700)
        t=pg.inner_text('#admPrice'); check("no extension → '크롬 확장을 먼저 설치해주세요' + steps", '크롬 확장을 먼저 설치해주세요' in t and 'chrome://extensions' in t, t)
        if SHOT: pg.locator('#adminModal .modal').screenshot(path=f'{SHOT}/oct12z_b93_after_admin_noext.png')
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
