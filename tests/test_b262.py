# test_b262: 찬란한 흉성(하드) 환상의 에테르넬 방어구 상자(b_star) = 기록 안 하는 정보 아이콘 칩(칼로스·카링·대적자 상자와 같음, 에리온 칩 옆, 이름 말풍선, 클릭 기록 없음). 지난 기록 표시 유지.
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
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
BS={'star':'hard','kaling':'hard'}
C={'id':'c0','name':'zetking','level':295,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
H=[{'week':'2026-10-15','total':1,'perChar':[{'id':'c0','name':'zetking','meso':0,'bosses':[],'items':{'star|b_star':1},'revs':{'star|b_star':{'m':900000000,'a':9,'p':1,'i':'b_star'}}}]}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':H,'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
def clip(pg,sel,name,up=60):
    if not SD: return
    os.makedirs(SD,exist_ok=True); x,y,w,h=pg.locator(sel).first.evaluate("e=>{const r=(e.closest('.boss,.bcard,.brow')||e.parentElement.parentElement).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-up),'width':min(1600,w+20),'height':min(700,h+up+20)})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    sel='.drop.ibox[aria-label*="환상의"]' if not NOCHK or pg.locator('.drop.ibox[aria-label*="환상의"]').count() else '.drop[data-drop="star|b_star"]'
    pg.locator(sel).first.scroll_into_view_if_needed(); pg.mouse.move(5,5); pg.wait_for_timeout(200); clip(pg,sel,'star_drops',10)
    pg.locator(sel).first.hover(); pg.wait_for_timeout(400); clip(pg,sel,'star_tip')
    if NOCHK: b.close(); raise SystemExit
    r=pg.evaluate("""()=>{const f=BOSSES.find(b=>b.id==='star'), all=BOSSES.flatMap(b=>b.diffs.flatMap(d=>dropsFor(b,d)));
      return {inDrops:all.includes('b_star'), ib:f.diffs.map(d=>[d,infoBoxFor(f,d)]), rev:revItems().includes('b_star')}}""")
    check('b_star 은 DROPS 에 없음(기록 안 함)', not r['inDrops'], r)
    check('흉성 하드에만 정보 칩', r['ib']==[['normal',[]],['hard',['b_star']]], r['ib'])
    check('아이템 시세 목록에 없음', not r['rev'])
    q=pg.evaluate("""()=>{const d=document.querySelector('.drop.ibox[aria-label*="환상의"]'); if(!d) return null; const ch=[...d.parentElement.children], i=ch.indexOf(d), k=document.querySelector('.drop.ibox[aria-label*="흉수"]');
      return {tip:d.getAttribute('data-tip'),drop:d.hasAttribute('data-drop'),img:!!d.querySelector('img'),prev:ch[i-1]?.className||'',cls:d.className,kcls:k&&k.className,txt:d.textContent.trim()}}""")
    check('정보 칩 = 이미지 아이콘만, data-drop 없음, 카링 칩과 같은 클래스', q and q['img'] and not q['drop'] and q['cls']==q['kcls'] and not q['txt'], q)
    check('에리온 칩 바로 옆', q and 'erion' in q['prev'], q)
    check('data-tip = 환상의 에테르넬 방어구 상자', q and q['tip']=='환상의 에테르넬 방어구 상자', q)
    t=pg.evaluate("()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?t.textContent:null}")
    check('hover 말풍선 = 이름', t and '환상의 에테르넬 방어구 상자' in t, t)
    n0=pg.evaluate("JSON.stringify([S.characters[0].drops,S.characters[0].drev||{}])"); pg.click(sel); pg.wait_for_timeout(400)
    check('클릭해도 기록 안 됨·기록 창 없음', pg.evaluate("JSON.stringify([S.characters[0].drops,S.characters[0].drev||{}])")==n0 and not pg.locator('#revModal').count())
    h=pg.evaluate("()=>{const p=S.history[0].perChar[0];return itemsInline(p.items,{revs:p.revs,byBoss:true})}")
    check('지난 기록 b_star 표시 유지', '환상의' in h, h[:200])
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
