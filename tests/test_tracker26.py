# 보스 현황: 보스·난이도는 넥슨 스케줄러 API로만 (⚙ 보스 선택/난이도 제거), 파티 인원·드롭 기록은 유지 (2026-10-10)
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8799
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def B(d,p=1): return {'enabled':True,'diff':d,'party':p}
c1={'id':'c1','name':'단풍용사','level':287,'job':'히어로','world':'스카니아','ocid':'ocid-main','accId':'a1','isMain':True,'image':'',
    'bosses':{'lotus':B('hard',2),'will':B('hard',3),'kaling':B('normal',1)},'weekly':{'kaling':True},'monthly':{},'auto':{},'drops':{'lotus|h_ear':1},'sync':{}}
c2={'id':'c2','name':'수동캐','level':200,'job':'비숍','world':'스카니아','ocid':'','accId':'','isMain':False,'image':'','bosses':{'lucid':B('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','characters':[c1,c2],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':''}],'lastSync':int(time.time()*1000)}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(500)
    check("tab renamed '보스 현황'", pg.inner_text('[data-tab="boss"]')=='보스 현황')
    check('no ⚙ 보스 선택/난이도 button, no difficulty selector', pg.locator('#editModeBtn').count()==0 and pg.locator('[data-setdiff]').count()==0 and '보스 선택' not in pg.inner_text('#view'))
    check('party selector + drop chips kept', pg.locator('[data-party="lotus"]').count()==1 and pg.locator('.boss .drop').count()>0)
    # 스케줄러 응답: 루시드(하드) 완료, 윌(노말) 등록만, 카링(노말) 등록, 로터스는 목록에 없음
    d={'date':pg.evaluate("S.period.week")+'T00:00+09:00','weekly_boss_clear_count':1,'weekly_boss_clear_limit_count':14,'boss_contents':[
       {'content_name':'루시드','difficulty':'하드','cycle':'weekly','registration_flag':'true','complete_flag':'true'},
       {'content_name':'윌','difficulty':'노말','cycle':'weekly','registration_flag':'true','complete_flag':'false'},
       {'content_name':'카링','difficulty':'노말','cycle':'weekly','registration_flag':'true','complete_flag':'false'}]}
    pg.evaluate("d=>{applyScheduler(S.characters[0],d);save();render()}",d); pg.wait_for_timeout(200)
    bs=pg.evaluate("S.characters[0].bosses")
    check('registered bosses enabled with API difficulty, party kept', bs['will']['enabled'] and bs['will']['diff']=='normal' and bs['will']['party']==3 and bs['lucid']['enabled'] and bs['lucid']['diff']=='hard', bs)
    check('boss not in scheduler (lotus) turned off, its party/drops kept', not bs['lotus']['enabled'] and bs['lotus']['party']==2 and pg.evaluate("S.characters[0].drops['lotus|h_ear']")==1, bs['lotus'])
    check('already-checked boss this week (kaling) stays on', bs['kaling']['enabled'] and pg.evaluate("S.characters[0].weekly.kaling"))
    names=pg.eval_on_selector_all('.boss .bn',"e=>e.map(x=>x.textContent.trim().split(' ')[0])")
    check('boss list = scheduler bosses', set(names)=={'루시드','윌','카링'}, names)
    pth=os.path.join(OUT,'boss_status_api.png'); pg.locator('.bosslay .grid>.card').nth(1).screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    pg.click('.char[data-id="c2"]'); pg.wait_for_timeout(200)
    check('manual (no API) character: keeps saved bosses, read-only', pg.locator('.boss').count()==1 and pg.locator('#editModeBtn').count()==0)
    pg.evaluate("S.characters[1].bosses.lucid.enabled=false;save();render()"); pg.wait_for_timeout(100)
    check('manual char with no bosses → explains API needed', 'API' in pg.inner_text('.boss-list'), pg.inner_text('.boss-list'))
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails)
