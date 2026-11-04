# test_b372 (t688): 캘린더 년/월 제목 클릭 → 년·월 선택 팝오버 (이동·Esc·바깥 클릭).
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SD=os.environ.get('B372_SHOTDIR') or OUT
TI="document.querySelector('.calti').textContent"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1300,'height':900},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("()=>{ S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}}]; S.activeId='c0'; S.calNotes={'2023-05-02':{m:{a:{t:'옛 메모',at:1}},b:{}}}; save(); render(); }")
    pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    cy=pg.evaluate("new Date().getFullYear()"); cm=pg.evaluate("new Date().getMonth()+1")
    check('제목 = 이번 달', pg.evaluate(TI)==f'{cy}년 {cm}월', pg.evaluate(TI))
    cur=pg.evaluate("getComputedStyle(document.querySelector('.calti')).cursor"); check('제목 클릭 가능(pointer)', cur=='pointer', cur)
    pg.hover('.calti'); bg=pg.evaluate("getComputedStyle(document.querySelector('.calti')).backgroundColor"); check('호버 표시', bg not in ('rgba(0, 0, 0, 0)','transparent'), bg)
    pg.click('.calti'); pg.wait_for_timeout(100)
    o=pg.evaluate("({y:document.querySelector('[data-calyv]').textContent,m:[...document.querySelectorAll('[data-calym2]')].map(e=>e.textContent),on:document.querySelector('[data-calym2].on')?.dataset.calym2,neon:document.querySelectorAll('#calYP .neonBtn').length})")
    check('팝오버: 연도 + 1~12월(네온), 지금 달 표시', o['y']==f'{cy}년' and o['m']==[f'{i}월' for i in range(1,13)] and o['on']==str(cm) and o['neon']==14, o)
    bx=pg.locator('.calhd').bounding_box(); pb=pg.locator('#calYP').bounding_box()
    pg.screenshot(path=os.path.join(SD,'ympicker.png'),clip={'x':bx['x']-10,'y':bx['y']-10,'width':max(bx['width'],320)+20,'height':pb['y']+pb['height']-bx['y']+20})
    pg.click('[data-calyy="1"]'); check('다음 해(현재+1)', pg.locator('[data-calyv]').text_content()==f'{cy+1}년' and pg.locator('[data-calyy="1"]').is_disabled())
    for _ in range(cy+1-2023): pg.click('[data-calyy="-1"]')
    check('데이터 있는 해(2023)까지 내려감, 그 아래는 막힘', pg.locator('[data-calyv]').text_content()=='2023년' and pg.locator('[data-calyy="-1"]').is_disabled())
    pg.click('[data-calym2="5"]'); pg.wait_for_timeout(100)
    check('월 고르면 그 달로 이동 + 닫힘', pg.evaluate(TI)=='2023년 5월' and pg.locator('#calYP').count()==0, pg.evaluate(TI))
    check('그 달 칸에 메모 표시', pg.locator('[data-calday="2023-05-02"].cbM').count()==1)
    pg.click('.calti'); pg.keyboard.press('Escape'); pg.wait_for_timeout(80); check('Esc 닫힘', pg.locator('#calYP').count()==0)
    pg.click('.calti'); pg.mouse.click(5,880); pg.wait_for_timeout(80); check('바깥 클릭 닫힘', pg.locator('#calYP').count()==0 and pg.evaluate(TI)=='2023년 5월')
    pg.click('.calti'); pg.click('.calti'); check('제목 다시 클릭 = 닫힘', pg.locator('#calYP').count()==0)
    pg.evaluate("document.documentElement.dataset.theme='light'"); pg.click('.calti'); pg.wait_for_timeout(80)
    lb=pg.evaluate("getComputedStyle(document.querySelector('#calYP')).backgroundColor"); check('라이트 테마 팝오버 흰 배경', lb=='rgb(255, 255, 255)', lb)
    bx=pg.locator('.calhd').bounding_box(); pb=pg.locator('#calYP').bounding_box()
    pg.screenshot(path=os.path.join(SD,'ympicker_light.png'),clip={'x':bx['x']-10,'y':bx['y']-10,'width':max(bx['width'],320)+20,'height':pb['y']+pb['height']-bx['y']+20})
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
