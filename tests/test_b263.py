# test_b263: 영롱한 달빛 포션(moon, WZ 2023136) = 익스트림 6보스(세렌·칼로스·대적자·카링·림보·발드릭스) 드롭표 기록 가능 칩. 이름 말풍선, WZ 원본 아이콘, 가격순 정렬, 시세 없음 → 수동 입력.
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
import os, sys, tempfile, shutil, subprocess, base64, io
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
BS={'kaling':'extreme','limbo':'extreme'}
C={'id':'c0','name':'zetking','level':295,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
def clip(pg,sel,name,up=60):
    if not SD: return
    os.makedirs(SD,exist_ok=True); x,y,w,h=pg.locator(sel).first.evaluate("e=>{const r=(e.closest('.boss,.bcard,.brow')||e.parentElement.parentElement).getBoundingClientRect();return [r.x,r.y,r.width,r.height]}")
    pg.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'),clip={'x':max(0,x-10),'y':max(0,y-up),'width':min(1600,w+20),'height':min(700,h+up+20)})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    sel='.drop[data-drop="kaling|moon"]' if not NOCHK or pg.locator('.drop[data-drop="kaling|moon"]').count() else '.drop[data-drop^="kaling|"]'
    pg.locator(sel).first.scroll_into_view_if_needed(); pg.mouse.move(5,5); pg.wait_for_timeout(200); clip(pg,sel,'kaling_drops',10)
    if not NOCHK: pg.locator(sel).first.hover(); pg.wait_for_timeout(400); clip(pg,sel,'kaling_tip')
    if NOCHK: b.close(); raise SystemExit
    r=pg.evaluate("""()=>Object.fromEntries(BOSSES.map(b=>[b.id,b.diffs.filter(d=>dropsFor(b,d).includes('moon'))]))""")
    got={k:v for k,v in r.items() if v}
    check('달빛 포션 = 6보스 익스트림만', got=={k:['extreme'] for k in ['seren','kalos','adversary','kaling','limbo','baldrix']}, got)
    check('ERION b264 값', pg.evaluate("[erionFor(findBoss('kaling'),'extreme'),erionFor(findBoss('bellona'),'hard')]")==[480,90])
    q=pg.evaluate("""()=>{const d=document.querySelector('.drop[data-drop="kaling|moon"]'); if(!d) return null; const im=d.querySelector('img');
      return {tip:d.getAttribute('data-tip'),txt:d.textContent.trim(),role:d.getAttribute('role'),nw:im&&im.naturalWidth,last:d.parentElement.querySelector('.drop[data-drop]:last-of-type')===d}}""")
    check('칩 = 기록 버튼, 이름·말풍선', q and q['role']=='button' and q['tip']=='영롱한 달빛 포션' and '영롱한 달빛 포션' in q['txt'], q)
    check('아이콘 WZ 원본 31px (b296)', q and q['nw']==31, q)
    o=pg.evaluate("""()=>{const b=findBoss('limbo');return [...document.querySelectorAll('.drop[data-drop^="limbo|"]')].map(e=>e.dataset.drop.split('|')[1])}""")
    check('정렬: 가격 없음 → 뒤쪽(반지 상자 앞), 기존 순서 유지', o[-1]=='moon' or o.index('moon')>o.index('whisper'), o)
    t=pg.evaluate("()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?t.textContent:null}")
    check('hover 말풍선 = 이름', t and '영롱한 달빛 포션' in t, t)
    check('시세 목록 포함, 자동 시세 없음', pg.evaluate("[revItems().includes('moon'), !admPriceOf('moon')]")==[True,True])
    pg.click(sel); pg.wait_for_timeout(400)
    check('클릭 → 기록 창, 금액 비어 있음(수동 입력)', pg.locator('#revModal').count()==1 and pg.evaluate("document.getElementById('rvAmt').value")=='', )
    pg.fill('#rvAmt','0.5'); pg.click('#revModal [data-rv="ok"]'); pg.wait_for_timeout(300)
    pg.wait_for_timeout(1200); s=pg.evaluate("()=>({drops:S.characters[0].drops,drev:S.characters[0].drev,err:document.getElementById('rvErr')?.textContent})")
    check('기록 저장 kaling|moon', s['drops'].get('kaling|moon')==1 and s.get('drev',{}).get('kaling|moon',{}).get('m')==50000000, (s['drops'],s.get('drev')))
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
