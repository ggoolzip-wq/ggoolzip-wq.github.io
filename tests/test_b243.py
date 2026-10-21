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
 return {bx:r.left+r.width/2, ix:q.left+q.width/2, by:r.top+r.height*0.6819, iy:q.top+q.height/2, w:b.offsetWidth, bz:+cs.zIndex, iz:+getComputedStyle(i).zIndex, bg:b.tagName+' '+(typeof BEAM!=='undefined'?BEAM.src:''), cw:b.width, mask:(cs.maskImage||cs.webkitMaskImage||''), h:b.offsetHeight, b64:cs.backgroundImage.slice(cs.backgroundImage.indexOf('base64,')+7,-2), ov:document.documentElement.scrollWidth>innerWidth, vw:innerWidth};}"""
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
          check(f'beam is canvas sprite (2x res) {vw}', g['bg']=='CANVAS epicbeam_sprite.webp' and g['cw']==1152, g['bg'])
          W=576 if vw>480 else 460
          check(f'beam 2x size {vw}', abs(g['w']-W)<2 and abs(g['h']-W*344/576)<3, (g['w'],g['h']))
          check(f'beam feathered mask {vw}', 'radial-gradient' in g['mask'], g['mask'])
          raw=open(os.path.join(os.path.dirname(__file__),'..','epicbeam_sprite.webp'),'rb').read()
          m=pg.evaluate("()=>({...BEAM, nw:beamImg.naturalWidth, nh:beamImg.naturalHeight})")
          check(f'beam 16 frames x 69ms sprite {vw}', m['n']==16 and m['ms']==69 and m['nw']==1152*4 and m['nh']==689*4, m)
          check(f'beam asset < 4MB {vw}', len(raw)<4000000, len(raw))
          check(f'no overflow {vw}', not g['ov'])
      if CHECK:
        # b246: 창이 열리는 순간 항상 0번 프레임부터 (두 번째 열 때도)
        for k in range(2):
          f0=pg.evaluate("()=>{endCelebrate(); celebrate('x','lcm',null); clearTimeout(celebrate._t); return celebrate.beamFrame;}")
          check(f'beam frame 0 at open #{k+1} {vw}', f0==0, f0)
          pg.wait_for_timeout(500); f1=pg.evaluate("celebrate.beamFrame")
          check(f'beam advances #{k+1} {vw}', 4<=f1<=10, f1)
          px=pg.evaluate("()=>{const c=document.querySelector('#congrats .cg-beam'),d=c.getContext('2d').getImageData(0,0,1152,689).data;let n=0;for(let i=3;i<d.length;i+=4000)n+=d[i]>0;return n}")
          check(f'beam canvas painted #{k+1} {vw}', px>20, px)
      pg.close()
    if CHECK:
      pg=b.new_page(reduced_motion='reduce'); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(500)
      d=pg.evaluate("()=>{celebrate('x','lcm',null); clearTimeout(celebrate._t); return [celebrate.beamFrame, getComputedStyle(document.querySelector('#congrats .cg-beam')).display]}")
      check('reduced motion: no beam', d==[-1,'none'], d); pg.close()
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
