# b200: 헤더 세로 가운데 — 로고 아이콘 중심선에 로고 글자·관리자·로그아웃·테마 버튼 (다크/라이트, 넓은/좁은 화면), 좁은 화면에서도 한 줄
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8983'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
M="""(()=>{const g=document.getElementById('gBtn');g.hidden=false;g.textContent='로그아웃';
 if(!document.getElementById('svAdminHdr')){const a=document.createElement('button');a.id='svAdminHdr';a.className='hbtn admhdr';a.textContent='👑 관리자';g.parentNode.insertBefore(a,g);}
 const c=e=>{const r=e.getBoundingClientRect();return +(r.top+r.height/2).toFixed(2)};
 return {icon:c(document.querySelector('#logoHome img')),text:(e=>c(e)-new DOMMatrix(getComputedStyle(e).transform).m42)(document.querySelector('#logoHome .logo-g')),shift:new DOMMatrix(getComputedStyle(document.querySelector('#logoHome .logo-g')).transform).m42,admin:c(document.getElementById('svAdminHdr')),logout:c(g),theme:c(document.getElementById('themeBtn')),over:document.documentElement.scrollWidth>innerWidth}})()"""
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for th in ('dark','light'):
      for w in (1400,390):
        ctx=b.new_context(viewport={'width':w,'height':800},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("t=>{localStorage.setItem('mapleBossTracker.v1',JSON.stringify({version:5,theme:t,characters:[],settings:{}}))}",th); pg.reload(); pg.wait_for_timeout(700)
        r=pg.evaluate(M); v=[r[k] for k in ('icon','text','admin','logout','theme')]
        check(f'{th} {w}px 세로 중심 1px 안 (로고 글자 = 잉크 보정 전 상자)', max(v)-min(v)<=1, r)
        check(f'{th} {w}px 로고 글자 잉크 보정 1~1.5px 아래로', 1<=r['shift']<=1.5, r)
        check(f'{th} {w}px 가로 넘침 없음', not r['over'], r)
        ctx.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
