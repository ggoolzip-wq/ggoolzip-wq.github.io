# b66: 입장 화면(초대 비밀번호·대표 키) + github.io 첫 화면(empty)에 NEXON Open API 표기
import os, sys, json, time, subprocess, shutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR') or '/workspace/maple-boss-tracker'
os.makedirs(SHOTDIR, exist_ok=True)
PORT=8850
ATTRIB='Data based on NEXON Open API'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def vis_in_vp(pg, sel):
    return pg.evaluate("""sel=>{
      const e=document.querySelector(sel); if(!e) return {ok:false,why:'missing'};
      const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
      const ok=r.width>0&&r.height>0&&r.top>=0&&r.bottom<=innerHeight+0.5&&r.left>=-1&&r.right<=innerWidth+1
        && cs.visibility!=='hidden'&&cs.display!=='none'&&parseFloat(cs.opacity||'1')>0;
      return {ok, top:r.top, bottom:r.bottom, h:innerHeight, color:cs.color, text:e.textContent.trim(), fs:cs.fontSize, ta:cs.textAlign};
    }""", sel)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.7)
API='https://fake-sync-b66.example'
def fake(route):
    u=route.request.url
    if u.endswith('/api/invite'):
        return route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},
                            body=json.dumps({'device':'dev-ticket-b66-'+('x'*40)}))
    route.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    # --- server gate: invite ---
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(API+'/**',fake); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("a=>{localStorage.clear();localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12');localStorage.setItem('mapleBossTracker.syncApi',a)}",API)
    pg.reload(); pg.wait_for_selector('#svGate #svInvite'); pg.wait_for_timeout(200)
    v=vis_in_vp(pg,'#svGate .svgattrib')
    check('invite@1280x800: attrib visible no scroll', v['ok'] and v['text']==ATTRIB, v)
    check('invite: muted/small/centered', v['ok'] and v['ta']=='center' and float(v['fs'].replace('px',''))<=14, v)
    pg.screenshot(path=os.path.join(OUT,'oct12d_attrib_pass.png'), full_page=False)
    shutil.copy(os.path.join(OUT,'oct12d_attrib_pass.png'), os.path.join(SHOTDIR,'oct12d_attrib_pass.png'))
    # light theme invite
    pg.evaluate("S.theme='light'; applyTheme(); svGate()"); pg.wait_for_timeout(150)
    vl=vis_in_vp(pg,'#svGate .svgattrib')
    check('invite light: attrib visible + muted brown', vl['ok'] and vl['text']==ATTRIB and vl['color']=='rgb(138, 119, 101)', vl)
    pg.evaluate("S.theme='dark'; applyTheme(); svGate()"); pg.wait_for_timeout(100)
    # mobile invite
    pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(100)
    vm=vis_in_vp(pg,'#svGate .svgattrib')
    check('invite mobile: attrib in viewport', vm['ok'] and vm['text']==ATTRIB, vm)
    # --- key step ---
    pg.set_viewport_size({'width':1280,'height':800})
    pg.fill('#svGate #svInvite','ok'); pg.click('#svGate #svInviteBtn'); pg.wait_for_selector('#svGate #svKey'); pg.wait_for_timeout(200)
    vk=vis_in_vp(pg,'#svGate .svgattrib')
    check('key@1280x800: attrib visible no scroll', vk['ok'] and vk['text']==ATTRIB, vk)
    pg.screenshot(path=os.path.join(OUT,'oct12d_attrib_key.png'), full_page=False)
    shutil.copy(os.path.join(OUT,'oct12d_attrib_key.png'), os.path.join(SHOTDIR,'oct12d_attrib_key.png'))
    pg.evaluate("S.theme='light'; applyTheme(); svGate()"); pg.wait_for_timeout(150)
    vkl=vis_in_vp(pg,'#svGate .svgattrib')
    check('key light: attrib visible', vkl['ok'] and vkl['text']==ATTRIB, vkl)
    pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(100)
    vkm=vis_in_vp(pg,'#svGate .svgattrib')
    check('key mobile: attrib in viewport', vkm['ok'] and vkm['text']==ATTRIB, vkm)
    # --- github.io equivalent: no syncApi → empty first-run (no gate) ---
    pg2=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR')
    pg2.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg2.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    pg2.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg2.evaluate("localStorage.clear(); localStorage.setItem('mapleBossTracker.keyReset','b64-2026-10-12')")
    pg2.reload(); pg2.wait_for_timeout(500)
    check('github.io mode: no gate', pg2.locator('#svGate').count()==0)
    ea=pg2.inner_text('.empty-attrib') if pg2.locator('.empty-attrib').count() else ''
    ft=pg2.inner_text('.foot')
    check('empty first-run has attrib + site footer has attrib', ea==ATTRIB and ATTRIB in ft, (ea, ft[:120]))
    ve=vis_in_vp(pg2,'.empty-attrib')
    check('empty attrib visible at 1280x800', ve['ok'], ve)
    check('no page errors', not errs, errs[:3])
    print('SHOT', os.path.join(SHOTDIR,'oct12d_attrib_pass.png'))
    print('SHOT', os.path.join(SHOTDIR,'oct12d_attrib_key.png'))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
