# test_b243: 득템 축하 창 아이콘 뒤에 에픽 빛줄기(.cg-beam, 투명 animated WebP) — 아이콘 가운데, 아이콘이 위, 화면 안 넘침
# b244: 2배(576x343, 모바일 460x274) + 페더(마스크), 프레임 69ms(2200ms 창에서 약 2번)
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
 return {bx:r.left+r.width/2, ix:q.left+q.width/2, by:r.top+r.height*0.6845, iy:q.top+q.height/2, w:r.width, bz:+cs.zIndex, iz:+getComputedStyle(i).zIndex, bg:cs.backgroundImage, mask:(cs.maskImage||cs.webkitMaskImage||''), h:r.height, b64:cs.backgroundImage.slice(cs.backgroundImage.indexOf('base64,')+7,-2), ov:document.documentElement.scrollWidth>innerWidth, vw:innerWidth};}"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for vw,vh,tag in [(1280,900,''),(390,844,'_mobile')]:
      pg=b.new_page(viewport={'width':vw,'height':vh},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
      pg.evaluate("()=>{celebrate('x','lcm',null); clearTimeout(celebrate._t);}"); pg.wait_for_timeout(700)
      if SD: pg.screenshot(path=f'{SD}/beam_{PFX}{tag}.png')
      if CHECK:
        g=pg.evaluate(GEO)
        check(f'beam exists {vw}', g is not None)
        if g:
          check(f'beam centered x {vw}', abs(g['bx']-g['ix'])<3, g)
          check(f'beam source at icon y {vw}', abs(g['by']-g['iy'])<6, g)
          check(f'icon above beam {vw}', g['iz']>g['bz'], g)
          check(f'beam is webp {vw}', 'epicbeam.webp' in g['bg'], g['bg'])
          W=576 if vw>480 else 460
          check(f'beam 2x size {vw}', abs(g['w']-W)<2 and abs(g['h']-W*343/576)<3, (g['w'],g['h']))
          check(f'beam feathered mask {vw}', 'radial-gradient' in g['mask'], g['mask'])
          import base64, struct
          raw=open(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','epicbeam.webp'),'rb').read(); ds=[]; i=12
          while i<len(raw)-8:
            n,sz=raw[i:i+4],struct.unpack('<I',raw[i+4:i+8])[0]
            if n==b'ANMF': ds.append(int.from_bytes(raw[i+8+12:i+8+15],'little'))
            i+=8+sz+(sz&1)
          check(f'beam 16 frames x 69ms (2 loops/2.2s) {vw}', len(ds)==16 and set(ds)=={69}, ds[:3])
          check(f'beam asset small {vw}', len(raw)<1600000, len(raw))
          check(f'no overflow {vw}', not g['ov'])
      pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
