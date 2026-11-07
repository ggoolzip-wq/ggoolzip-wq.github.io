"""Essential lossless brightest-frame + static celebration regression."""
import sys,subprocess,json
from pathlib import Path
from PIL import Image,ImageStat
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];assert 'epicbeam_static.png' in (ROOT/'tools/pages_dist.sh').read_text();png=Image.open(ROOT/'epicbeam_static.png').convert('RGBA');assert png.size==(716,428)
source=Path('/workspace/epic_beam_user.gif')
if source.exists():
 im=Image.open(source);means=[];frames=[]
 for i in range(im.n_frames):
  im.seek(i);f=im.convert('RGBA');frames.append(f.copy());bg=Image.new('RGBA',f.size,'black');bg.alpha_composite(f);means.append(ImageStat.Stat(bg.convert('L')).mean[0])
 k=max(range(len(means)),key=means.__getitem__);assert k==6 and png.tobytes()==frames[k].tobytes();print('PASS brightest frame #6 (7th), 716x428, pixel-exact lossless PNG')
PORT=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1280,'height':900});errs=[];requests=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('request',lambda r:requests.append(r.url));pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_function('typeof celebrate==="function"')
  assert pg.evaluate("typeof beamPrep==='undefined'&&typeof beamDraw==='undefined'&&typeof beamPlay==='undefined'&&typeof beamBake==='undefined'")
  pg.evaluate("celebrate(null,'r_white',findBoss('kaling'))");pg.wait_for_function("document.querySelector('#congrats.show .cg-beam')?.naturalWidth===716")
  pg.wait_for_timeout(550)
  info=pg.locator('.cg-beam').evaluate("e=>({tag:e.tagName,w:e.naturalWidth,h:e.naturalHeight,src:e.currentSrc,pos:getComputedStyle(e).position,animation:getComputedStyle(e).animationName,animations:e.getAnimations().length})")
  assert info['tag']=='IMG' and info['w']==716 and info['h']==428 and info['pos']=='absolute' and info['animation']=='none' and info['animations']==0,info
  assert pg.locator('#congrats canvas').count()==0
  pg.screenshot(path='/workspace/maple-boss-tracker/b396_celebration.png')
  pg.wait_for_timeout(250);assert pg.locator('.cg-beam').evaluate('(e)=>e.currentSrc')==info['src']
  assert not any('epicbeam_s720' in u or 'epicbeam_sprite' in u for u in requests),requests
  assert not errs,errs
  pg.evaluate('endCelebrate()');assert pg.locator('#congrats.show').count()==0
  b.close();print('PASS static IMG, no beam canvas/animation/sprite requests, alignment, close, JS errors=0')
finally:srv.terminate()
print('ALL PASS b396')
