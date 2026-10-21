import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8875=_tutil.free_port()
# zosu-ui: ① 로그인 전 첫 화면 오른쪽 위 로그인 버튼 없음(로그인 뒤 헤더 그대로) ② '+ 추가' 본계정 키 칸 아래 'API 발급 : 링크' 한 줄 (가짜 서버, 넥슨 호출 없음)
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8875)
URL_API='https://openapi.nexon.com/ko/my-application/create-app/'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
API='https://fake-sync-zosu.example'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':800},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(API+'/**',lambda r:r.fulfill(status=404,headers={'Access-Control-Allow-Origin':'*'},body='{}')); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("a=>{localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi',a)}",API); pg.reload(); pg.wait_for_timeout(800)
    check('로그인 전: 오른쪽 위 로그인 버튼 안 보임', pg.is_hidden('#gBtn'), pg.evaluate("document.querySelector('#gBtn').textContent"))
    check("로그인 전: 가운데 '캐릭터 추가' 길은 그대로", pg.is_visible('#addCharBtn') or pg.locator('text=캐릭터 추가').count()>0)
    pg.click('#addCharBtn'); pg.wait_for_selector('#svMainSec #svMainKey')
    a=pg.evaluate("""(()=>{const s=document.querySelector('#svMainSec'),l=s.querySelector('.svmapi'),k=s.querySelector('#svMainKey'),x=l&&l.querySelector('a');
      return l&&{t:l.innerText.trim(),n:s.querySelectorAll('.svmapi').length,href:x&&x.href,tg:x&&x.target,rel:x&&x.rel,below:l.getBoundingClientRect().top>=k.getBoundingClientRect().bottom-1,fs:parseFloat(getComputedStyle(l).fontSize),ph:k.placeholder,lines:Math.round(l.getBoundingClientRect().height/parseFloat(getComputedStyle(l).lineHeight))}})()""")
    check("본계정 키 칸 아래 'API 발급 : 링크' 한 줄, 새 탭", a and a['n']==1 and a['t'].startswith('API 발급 : ') and a['href']==URL_API and a['tg']=='_blank' and 'noopener' in a['rel'] and a['below'] and a['fs']<13 and a['ph']=='API키 입력' and a['lines']==1, a)
    # 로그인 뒤: 헤더 버튼(로그아웃) 그대로 보임
    pg.evaluate("()=>{ localStorage.setItem(SV_TOKEN_KEY,'fake'); gdMeta.on=true; gd.state='on'; gdRender(); }")
    v=pg.evaluate("(()=>{const b=document.querySelector('#gBtn');return {h:b.hidden,t:b.textContent}})()")
    check('로그인 뒤: 헤더 로그아웃 버튼 그대로', not v['h'] and v['t']=='로그아웃', v)
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally: srv.kill()
print('FAILS:',fails); sys.exit(1 if fails else 0)
