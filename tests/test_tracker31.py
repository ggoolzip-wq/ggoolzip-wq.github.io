# 테섭 예정 결정석 가격 표시 (로컬 데모: 모든 가격 10% 인하 테섭 글) — 실서버 가격은 그대로
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    pth=os.path.join(OUT,name); loc.screenshot(path=pth,**kw); SHOTDIR and shutil.copy(pth,SHOTDIR)
PORT=8831
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
live=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8'))
demo=json.loads(json.dumps(live)); demo['checkedAt']='2099-01-01'
demo['upcoming']={'source':{'url':'https://maplestory.nexon.com/Testworld/News/Update/999','title':'[데모] 테스트 서버 업데이트 안내','date':'2026-10-10'},
  'rows':[{'boss':r['boss'],'old':r['new'],'new':int(r['new']*0.9)} for r in live['rows']],'detectedAt':'2026-10-10T09:00:00+09:00'}
def B(d): return {'enabled':True,'diff':d,'party':1}
c1={'id':'c1','name':'단풍용사','level':285,'job':'히어로','world':'스카니아','ocid':'o1','accId':'','isMain':True,'image':'','bosses':{'seren':B('hard'),'kaling':B('normal'),'lotus':B('hard'),'blackmage':B('hard'),'limbo':B('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{'at':1}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/prices.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(demo)))
    pg.goto(URL)
    ST={'version':5,'theme':'dark','activeId':'c1','characters':[c1],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[],'lastSync':int(time.time()*1000)}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(800)
    k=pg.evaluate("priceKey(findBoss('seren'),'hard')"); livev=pg.evaluate("price(findBoss('seren'),'hard')")
    seren=[r for r in live['rows'] if r['boss'].startswith('선택받은 세렌') and '하드' in r['boss']][0]['new']
    check('live price unchanged (from main patch)', livev==seren, (livev,seren))
    ups=pg.locator('.pricecard .pc-up').count()
    check('every price row shows 테섭 예정 → N', ups>=20 and '테섭 예정 → ' in pg.inner_text('.pricecard'), ups)
    row=pg.inner_text(".pricecard .pc-row:has-text('선택받은 세렌')")
    check('example row: current + 테섭 예정 (−10%)', '테섭 예정' in row, row)
    check('foot names the 테섭 source', '테섭 예정 가격' in pg.inner_text('.pc-foot'))
    pg.locator('.pricecard').screenshot(path='/workspace/shots/b38_demo_price.png')
    ex=pg.inner_text('.expinc')
    check('예상 결정석 수익: current + 테섭 예정 value', '테섭 예정 → ' in ex, ex)
    pg.locator('#view .card').first.screenshot(path='/workspace/shots/b38_demo_expinc.png')
    # 생명 반지 상자 → '생명의 연마석' 결과
    pg.evaluate("localStorage.removeItem('x')"); pg.click('[data-drop="limbo|r_life"]'); pg.wait_for_selector('#ringModal.show')
    opts=pg.eval_on_selector_all('#ringModal [data-ring]',"e=>e.filter(x=>!x.hidden).map(x=>x.dataset.ring)")
    check('life box modal has 생명의 연마석 option with icon', opts==['r4','c4','gl','x'] and pg.locator('#ringModal [data-ring=gl] img').count()==1, opts)
    pg.screenshot(path='/workspace/shots/b38_life_modal.png')
    pg.click('#ringModal [data-ring=gl]'); pg.wait_for_timeout(300)
    check('gl → burst with 연마석 icon', pg.evaluate("[...document.querySelectorAll('#iconBurst img')].length>=30&&[...document.querySelectorAll('#iconBurst img')].every(i=>i.getAttribute('src')===ITEM_ICONS.g_life)") and '생명의 연마석' in pg.inner_text('#congrats'))
    pg.evaluate("endCelebrate()")
    bw=pg.evaluate("parseFloat(getComputedStyle(document.createElement('div')).width)||0")
    check('recorded like ring outcome', pg.evaluate("S.characters[0].dropOut['limbo|r_life']")==['gl'])
    pg.click('#pendSave'); pg.wait_for_timeout(200); pg.click('[data-tab="total"]'); pg.wait_for_timeout(300)
    rows=pg.eval_on_selector_all('.bossloot .blrow','e=>e.map(x=>x.innerText.split(String.fromCharCode(10)).join(" "))'); tot=pg.inner_text('.itemtot')
    check('수익 분석: boss row + 총 아이템 획득량 include 생명의 연마석', any(r.startswith('림보') and '생명의 연마석 x1' in r for r in rows) and '생명의 연마석 x1' in tot.replace('\n',' ') and '생명의 보스 반지 상자 x1' in tot.replace('\n',' '), (rows,tot))
    vt=pg.inner_text('#view'); check('수익 분석: no Drive storage sentence, no stray punctuation', '드라이브' not in vt and '기록).' in vt and '. .' not in vt)
    check('시드링 summary lists 연마석 outcome', '생명의 연마석' in pg.inner_text('.ringsum'))
    pg.click('[data-drop="kaling|chaosbox"]') if False else None
    pg.click('[data-tab="boss"]'); pg.wait_for_timeout(150)
    pg.click('[data-drop="seren|mitra"]'); pg.wait_for_timeout(150)
    sz=pg.evaluate("(i=>i?i.getBoundingClientRect().width>0&&getComputedStyle(i).width:null)(document.querySelector('#iconBurst img'))")
    check('burst icons 1.3x larger (42px)', sz=='42px', sz)
    pg.click('[data-drop="seren|mitra"]'); pg.wait_for_timeout(100); pg.evaluate("endCelebrate()")
    # 예정 없음 → 표시 없음
    pg.unroute('**/prices.json*'); pg.route('**/prices.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(live)))
    pg.evaluate("localStorage.removeItem(PRICES_CACHE_KEY)"); pg.reload(); pg.wait_for_timeout(800)
    check('no upcoming → no marks', pg.locator('.pc-up').count()==0 and pg.locator('.exp-up').count()==0)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
