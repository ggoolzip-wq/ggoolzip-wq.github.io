"""Essential inline guide / connect-stop / existing PiP card lifecycle regression."""
import sys,subprocess,ast
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];PORT=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
module=ast.parse((ROOT/'tests/test_b376_pipmin.py').read_text());FAKE=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign) and any(getattr(t,'id','')=='FAKE' for t in n.targets))
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page(viewport={'width':1440,'height':1000});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(f'http://127.0.0.1:{PORT}/');pg.wait_for_function('typeof renderAuto==="function"');pg.click('[data-tab="auto"]');pg.wait_for_selector('#arGuideInline');pg.evaluate("()=>{S.settings.accounts=[{id:'fixture'}];tab='auto';renderAuto();}")
  assert pg.locator('#arGuide').count()==0 and pg.locator('#arGuideInline .ar-gimg img').count()==2
  assert pg.locator('#arPanel .ar-cchar,#arPanel .ar-clive,#arPanel video,#arPanel canvas.ar-prev').count()==0
  assert not pg.locator('#arPanel .ar-cboss').is_visible()
  assert pg.locator('.ar-maple-connect').inner_text()=='메이플 연결'
  assert pg.locator('.ar-maple-connect').bounding_box()['y']>=pg.locator('.ar-crec').bounding_box()['y']
  pg.screenshot(path='/workspace/maple-boss-tracker/b397_auto_inline.png',full_page=True)
  pg.evaluate(FAKE)
  pg.evaluate('''()=>{window.__calls=0;window.__stopped=false;arConnect=()=>{__calls++;const tr={readyState:'live',stop(){__stopped=true;this.readyState='ended'},getSettings(){return {width:1280,height:720}}};ARX.stream={getVideoTracks:()=>[tr],getTracks:()=>[tr]};ARX.video=document.createElement('video');arPanelPaint();};}''')
  pg.click('.ar-maple-connect');assert pg.evaluate('__calls')==1 and pg.locator('.ar-maple-connect').inner_text()=='메이플 연결 해제'
  assert pg.evaluate('arPipOpen(arPipCard())')
  assert pg.evaluate("!!ARX.pip.win.document.querySelector('.ar-cboss .ar-b')")
  pg.evaluate('arPipSetMin(true)') if pg.evaluate('typeof arPipSetMin==="function"') else None
  pg.evaluate('renderAuto(); arPipClose()');assert not pg.locator('#arPanel .ar-cboss').is_visible()
  pg.click('.ar-maple-connect');assert pg.evaluate('__stopped') and pg.locator('.ar-maple-connect').inner_text()=='메이플 연결'
  pg.evaluate("S.settings.accounts=[]");pg.click('.ar-maple-connect');assert pg.evaluate('__calls')==2;pg.click('.ar-maple-connect')
  assert not errs,errs
  b.close();print('ALL PASS b397: inline guide/no popup, removed page sections, bottom connect/stop uses existing handler, PiP open/re-render/return remains hidden, track stops, JS errors=0')
finally:srv.terminate()
