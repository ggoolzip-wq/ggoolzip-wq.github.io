# b198: 검색 등록 준비 — meta description·canonical·og, robots.txt·sitemap.xml 실제 파일, 숨은 소개 글(화면 변화 없음)
import os, sys, time, subprocess, urllib.request, re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8981'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
H=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read(); head=H[:H.index('</head>')]
U='https://bossmaple.pages.dev/'
check('meta description (한국어)', re.search(r'<meta name="description" content="[^"]*메이플스토리[^"]*보스',head) is not None)
check('canonical = bossmaple.pages.dev', f'<link rel="canonical" href="{U}">' in head)
for k,v in (('og:title','메보기'),('og:description','메이플'),('og:url',U),('og:image',U+'og.png')):
    check(k, re.search(rf'<meta property="{k}" content="[^"]*{re.escape(v)}',head) is not None)
check('b199 소유 확인 태그(구글·네이버)', '<meta name="google-site-verification" content="1vcb6ZmBor2M4xfKsBwcPVDYSjOmd3zo4ZzM9A7lA4E" />' in head and '<meta name="naver-site-verification" content="a7d0315262c0c08150e38a3a696a4d0f54fae152" />' in head)
rb=open(os.path.join(ROOT,'robots.txt')).read()
check('robots.txt Allow / + Sitemap', 'Allow: /' in rb and 'Sitemap: '+U+'sitemap.xml' in rb and 'Disallow: /\n' not in rb, rb)
sm=open(os.path.join(ROOT,'sitemap.xml')).read()
check('sitemap.xml 대표 주소', f'<loc>{U}</loc>' in sm and 'sitemaps.org/schemas/sitemap/0.9' in sm)
ds=open(os.path.join(ROOT,'tools/pages_dist.sh')).read()
check('Cloudflare Pages 배포에 robots·sitemap·og 포함', all(f in ds for f in ('robots.txt','sitemap.xml','og.png')))
check('og.png 있음', os.path.getsize(os.path.join(ROOT,'og.png'))>10000)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':900},locale='ko-KR')
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    r=pg.evaluate("(()=>{const s=document.getElementById('seoIntro'),b=s.getBoundingClientRect(),h=document.querySelector('header').getBoundingClientRect();return {w:b.width,h:b.height,pos:getComputedStyle(s).position,txt:s.textContent.includes('주간 보스'),htop:h.top,h1:document.querySelectorAll('h1').length}})()")
    check('숨은 소개 글: 1px·absolute(화면·레이아웃 그대로), 크롤러용 글 있음', r['w']<=1 and r['h']<=1 and r['pos']=='absolute' and r['txt'] and r['htop']==0, r)
    check('JS 오류 없음', not errs, errs)
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
