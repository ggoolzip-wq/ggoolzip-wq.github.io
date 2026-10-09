import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 주간 보스 12/12 완료 '완' 도장
from playwright.sync_api import sync_playwright
import json, subprocess, os, time, urllib.request
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
SETUP="""(()=>{
 const wk=BOSSES.filter(b=>b.type==='weekly').slice(-14);
 const mk=(id,name,lv,job,n,main)=>{const c={id,name,level:lv,job,world:'스카니아',isMain:!!main,ocid:'',bosses:{},weekly:{},monthly:{},auto:{},sync:{},drops:{}};
   wk.slice(0,12).forEach(b=>{c.bosses[b.id]={enabled:true,diff:b.diffs[b.diffs.length-1],party:1};}); wk.slice(0,n).forEach(b=>c.weekly[b.id]=true); return c;};
 S.characters=[mk('c1','단풍용사',287,'히어로',12,true),mk('c2','은월달빛',279,'은월',12),mk('c3','아델의칼',271,'아델',11),mk('c4','비숍조아',262,'비숍',3)];
 S.activeId='c1'; save(); render(); })()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR')
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    pg.goto('http://localhost:8787/index.html'); pg.wait_for_timeout(500)
    pg.evaluate(SETUP); pg.wait_for_timeout(300)
    st=lambda: pg.evaluate("[...document.querySelectorAll('#charList .char, .char')].map(e=>[e.dataset.id,!!e.querySelector('.donestamp')])")
    s=dict(st()); check('stamp on 12/12 only', s=={'c1':True,'c2':True,'c3':False,'c4':False}, s)
    box=pg.evaluate("(()=>{const c=document.querySelector('.char[data-id=c1]'),s=c.querySelector('.donestamp'),n=c.querySelector('.nm'),l=c.querySelector('.lv');const r=s.getBoundingClientRect(),cr=c.getBoundingClientRect(),nr=n.getBoundingClientRect(),lr=l.getBoundingClientRect();const ov=(a,b)=>!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom);return {w:r.width,top:r.top-cr.top,left:r.left-cr.left,nm:ov(r,nr),lv:ov(r,lr),txt:s.textContent,tf:getComputedStyle(s).transform}})()")
    check('stamp top-left, small, not covering name/level', box['w']<=30 and box['top']<10 and box['left']<10 and not box['nm'] and not box['lv'] and box['txt']=='완' and box['tf']!='none', box)
    # 11/12로 줄이면 사라짐
    pg.click('.char[data-id=c2]'); pg.wait_for_timeout(200)
    pg.evaluate("(()=>{const c=S.characters.find(c=>c.id==='c2');delete c.weekly[Object.keys(c.weekly)[0]];save();render();})()"); pg.wait_for_timeout(200)
    check('stamp gone below 12', not dict(st())['c2'])
    pg.evaluate("(()=>{const c=S.characters.find(c=>c.id==='c3');const b=BOSSES.filter(b=>b.type==='weekly').slice(-14)[11];c.weekly[b.id]=true;save();render();})()"); pg.wait_for_timeout(200)
    check('stamp appears at 12', dict(st())['c3'])
    pg.click('.char[data-id=c1]'); pg.wait_for_timeout(300)
    pg.screenshot(path=''+OUT+'/price_card.png')
    pg.screenshot(path=OUT+'/stamp_zoom.png',clip={'x':0,'y':80,'width':300,'height':330})
    pg.click('#themeBtn') if pg.query_selector('#themeBtn') else None; pg.wait_for_timeout(200)
    pg.screenshot(path=OUT+'/stamp_dark.png',clip={'x':0,'y':80,'width':300,'height':330})
    # 주간 초기화 후 사라짐
    pg.evaluate("(()=>{S.period.week='2000-01-01';save();})()"); pg.reload(); pg.wait_for_timeout(600)
    check('stamp gone after weekly reset', not any(v for _,v in st()), st())
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append(str(e)))
    m.goto('http://localhost:8787/index.html'); m.wait_for_timeout(400); m.evaluate(SETUP); m.wait_for_timeout(300)
    check('mobile stamp + no overflow', m.query_selector('.char[data-id=c1] .donestamp') is not None and not m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    m.screenshot(path=OUT+'/stamp_mobile.png')
    pg.goto('http://localhost:8787/index.html'); pg.wait_for_timeout(600)
    v=pg.inner_text('body')
    check('no settings tab / API side card / backup / proxy text', pg.query_selector('[data-tab="settings"]') is None and pg.query_selector('#apiSide') is None and pg.query_selector('#exportBtn') is None and not any(w in v for w in ['프록시','JSON','백업','serve.py','연결 방식']), [w for w in ['프록시','JSON','백업','serve.py','연결 방식'] if w in v])
    check('limits fixed 12/1', pg.evaluate('[S.settings.weeklyLimit,S.settings.monthlyLimit]')==[12,1])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
