# b54: 축하 = 보스 아이콘 + 축하드립니다! (이모지 없음), 결정석 가격 '내가 잡는 보스만 보기' (테섭 예정 모의 포함)
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8840/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8840','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
def ch(i,b):
    return {'id':f'c{i}','name':f'캐릭{i}','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':i==0,'image':'','bosses':b,'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
B0={'lotus':{'enabled':True,'diff':'hard','party':1},'lucid':{'enabled':True,'diff':'hard','party':1},'blackmage':{'enabled':True,'diff':'hard','party':1}}
B1={'lotus':{'enabled':True,'diff':'extreme','party':1},'lucid':{'enabled':True,'diff':'hard','party':1},'zakum':{'enabled':False,'diff':'chaos','party':1}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[ch(0,B0),ch(1,B1)],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",ST); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("celebrate(null,'g_faith',findBoss('kaling'))"); pg.wait_for_timeout(300)
    check('축하: 보스 아이콘이 글자 앞, 이모지·🎉 없음', pg.locator('#congrats .cg-big .cg-boss img').count()==1 and pg.locator('#congrats .cg-emo').count()==0 and pg.evaluate("document.querySelector('.cg-big').firstElementChild.className")=='cg-boss')
    pg.evaluate("document.querySelector('#iconBurst')?.remove()"); pg.locator('#congrats .cg-in').screenshot(path='/workspace/shots/b54_celebrate.png'); pg.evaluate("endCelebrate()")
    full=pg.locator('.pricecard .pc-row').count()
    pg.click('.pc-mine >> text=내가 잡는 보스만 보기'); pg.wait_for_timeout(200)
    nm=pg.eval_on_selector_all('.pricecard .pc-row .pc-nm','e=>e.map(x=>x.innerText.replace(/\\s+/g," "))')
    check('라벨 클릭으로 켜짐: 스우 하드·익스트림 따로, 루시드 하드 1번, 검마 하드, 꺼진 자쿰 없음', sorted(nm)==sorted(['스우 하드','스우 익스트림','루시드 하드','검은 마법사 하드']), nm)
    check('localStorage 기억', pg.evaluate("localStorage.getItem('mapleBossTracker.pcMine')")=='1')
    over=pg.evaluate("[...document.querySelectorAll('.pricecard .pc-nm')].some(n=>n.scrollWidth>n.clientWidth+0.5)")
    check('잘림 없음', not over)
    pg.locator('.pricecard').screenshot(path='/workspace/shots/b54_mine.png')
    pg.reload(); pg.wait_for_timeout(1200)
    check('새로고침 후에도 켜져 있음', pg.is_checked('#pcMine') and pg.locator('.pricecard .pc-row').count()==4)
    # 테섭 예정 모의 (저장 안 함)
    pg.evaluate("officialInfo.upcoming={lotus_extreme:999000000, zakum_chaos:1}; document.querySelector('.pricecard').outerHTML=priceCard(); fitPriceCard()")
    check('테섭 예정 + 필터: 스우 익스트림 예정 표시, 자쿰 숨김', pg.locator('.pricecard .pc-row.has-up').count()==1 and '자쿰' not in pg.inner_text('.pricecard .pc-list') and pg.locator('.pc-tabs').count()==1)
    pg.locator('.pricecard').screenshot(path='/workspace/shots/b54_upcoming.png')
    pg.click('[data-pctab=after]'); pg.wait_for_timeout(200)
    check('패치 후 탭에서도 토글 유지·동작', pg.is_checked('#pcMine') and pg.locator('.pa-row').count()==2)
    pg.click('[data-pctab=price]'); pg.click('#pcMine'); pg.wait_for_timeout(200)
    check('체크박스 클릭으로 끄면 전체 목록', pg.locator('.pricecard .pc-row').count()==full and pg.evaluate("localStorage.getItem('mapleBossTracker.pcMine')")=='0', full)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
