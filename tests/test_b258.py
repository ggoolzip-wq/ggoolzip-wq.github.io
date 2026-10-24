# test_b258: 에리온의 조각 · 칼로스/대적자/카링 방어구 상자 · 앱솔랩스/아케인셰이드 상자 정보 칩 = 여명 장신구(off) 칩과 같은 말풍선(#mbtTip, 아이템 이름)
# MBT_ROOT = 다른 빌드(변경 전 사진용, 검사 생략은 MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = 파일 이름 앞말(before/after)
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
BS={'kaling':'hard','kalos':'extreme','adversary':'hard','lotus':'hard','lucid':'hard','seren':'hard'}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
def tip(pg,sel):
    pg.mouse.move(5,5); pg.wait_for_timeout(150); el=pg.locator(sel).first; el.scroll_into_view_if_needed(); el.hover(); pg.wait_for_timeout(350)
    return pg.evaluate("()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?{txt:t.textContent,cls:t.className,cs:getComputedStyle(t).backgroundColor+'|'+getComputedStyle(t).borderRadius}:null}")
def shot(pg,sel,name):
    if not SD: return
    os.makedirs(SD,exist_ok=True); bx=pg.locator(sel).first.evaluate("e=>{const r=(e.closest('.boss,.bcard,section,.card')||e.parentElement).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    x,y,w,h=bx; pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-60),'width':min(1600,w+20),'height':h+80})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    q=pg.evaluate("()=>[...document.querySelectorAll('.drop.erion,.drop.ibox')].map(x=>({c:x.className,tip:x.getAttribute('data-tip'),al:x.getAttribute('aria-label')}))")
    er=[x for x in q if 'erion' in x['c']]; ib=[x for x in q if 'ibox' in x['c']]
    check('에리온 칩 data-tip = 에리온의 조각', er and all(x['tip']=='에리온의 조각' for x in er), er)
    check('상자 칩 data-tip = 아이템 이름(aria-label 앞부분)', ib and all(x['tip'] and x['al'].startswith(x['tip']) for x in ib), ib)
    names={x['tip'] for x in ib}
    check('칼로스·대적자·카링·앱솔·아케인 상자 이름', all(any(n in (t or '') for t in names) for n in ['의지의 에테르넬','고대의 에테르넬','흉수의 에테르넬','앱솔랩스 무기','아케인셰이드 방어구']), names)
    dawn=tip(pg,'.drop.off[data-tip]')
    check('기준: 여명 장신구 칩 말풍선', dawn and dawn['txt'], dawn)
    if SD: pg.locator('.drop.erion').first.scroll_into_view_if_needed(); shot(pg,'.drop.erion','droptable_1600')
    t=tip(pg,'.drop.erion'); check('에리온 칩 hover = 같은 말풍선', t and t['txt']=='에리온의 조각' and t['cs']==(dawn or {}).get('cs'), t)
    shot(pg,'.drop.erion','tip_erion')
    t=tip(pg,'.drop.ibox[aria-label*="흉수"]'); check('카링 상자 칩 hover = 이름 말풍선', t and '흉수의 에테르넬 방어구 상자' in t['txt'] and t['cs']==(dawn or {}).get('cs'), t)
    shot(pg,'.drop.ibox[aria-label*="흉수"]','tip_kaling_box')
    t=tip(pg,'.drop.ibox[aria-label*="앱솔랩스"]'); check('앱솔랩스 상자 칩 hover', t and '앱솔랩스' in t['txt'], t)
    t=tip(pg,'.drop.ibox[aria-label*="아케인셰이드"]'); check('아케인셰이드 상자 칩 hover', t and '아케인셰이드' in t['txt'], t)
    n0=pg.evaluate("JSON.stringify(S.characters[0].drops||{})"); pg.click('.drop.erion'); pg.click('.drop.ibox'); pg.wait_for_timeout(300)
    check('클릭해도 기록 안 됨', pg.evaluate("JSON.stringify(S.characters[0].drops||{})")==n0)
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'{len(fails)} FAIL'); sys.exit(1 if fails else 0)
