# test_b243: 득템 축하 창 아이콘 뒤에 에픽 빛줄기(.cg-beam, 투명 animated WebP) — 아이콘 가운데, 아이콘이 위, 화면 안 넘침
# MBT_SHOTDIR=폴더 → 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR'); PFX='after' if CHECK else 'before'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
GEO="""()=>{const b=document.querySelector('#congrats .cg-beam'), i=document.querySelector('#congrats .cg-ico img'); if(!b||!i) return null;
 const r=b.getBoundingClientRect(), q=i.getBoundingClientRect(), cs=getComputedStyle(b);
 return {bx:r.left+r.width/2, ix:q.left+q.width/2, by:r.top+r.height*0.8, iy:q.top+q.height/2, w:r.width, bz:+cs.zIndex, iz:+getComputedStyle(i).zIndex, bg:cs.backgroundImage.slice(0,30), ov:document.documentElement.scrollWidth>innerWidth, vw:innerWidth};}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for vw,vh,tag in [(1280,900,''),(390,844,'-mobile')]:
      pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
      pg.evaluate("()=>{celebrate('x','lcm',null); clearTimeout(celebrate._t);}"); pg.wait_for_timeout(700)
      if SD: pg.screenshot(path=f'{SD}/{PFX}{tag}.png')
      if CHECK:
        g=pg.evaluate(GEO)
        check(f'beam exists {vw}', g is not None)
        if g:
          check(f'beam centered x {vw}', abs(g['bx']-g['ix'])<3, g)
          check(f'beam source at icon y {vw}', abs(g['by']-g['iy'])<6, g)
          check(f'icon above beam {vw}', g['iz']>g['bz'], g)
          check(f'beam is webp {vw}', 'data:image/webp' in g['bg'], g['bg'])
          check(f'beam width sane {vw}', 150<=g['w']<=min(360,vw), g['w'])
          check(f'no overflow {vw}', not g['ov'])
      pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
