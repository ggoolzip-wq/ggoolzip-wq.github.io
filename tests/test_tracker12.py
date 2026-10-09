import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 주간 보스 12/12 완료 덮개 (1줄: ★ 이번 주 보스 완료, 2줄: (!) 검마 격파 필요)
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
FIT="""(()=>{const out={};document.querySelectorAll('#charList .char').forEach(c=>{const d=c.querySelector('.dov');if(!d)return;const cr=c.getBoundingClientRect(),ok=d.querySelector('.dov-ok').getBoundingClientRect(),w=d.querySelector('.dov-warn');
 const inside=r=>r.left>=cr.left-0.5&&r.right<=cr.right+0.5&&r.top>=cr.top-0.5&&r.bottom<=cr.bottom+0.5;const t=d.querySelector('.dov-t');
 const o={okIn:inside(ok),ok1line:ok.height<24,noOvf:t.scrollWidth<=t.clientWidth+1&&d.scrollHeight<=d.clientHeight+1,okCx:Math.abs((ok.left+ok.right)/2-(cr.left+cr.right)/2)<3};
 if(w){const wr=w.getBoundingClientRect();o.wIn=inside(wr);o.below=wr.top>=ok.bottom-1;o.w1line=wr.height<22;o.wCx=Math.abs((wr.left+wr.right)/2-(cr.left+cr.right)/2)<3;}
 out[c.dataset.id]=o;});return out;})()"""
fitok=lambda f: all(all(v for v in o.values()) for o in f.values())
SETUP="""(()=>{
 const wk=BOSSES.filter(b=>b.type==='weekly').slice(-14);
 const mk=(id,name,lv,job,n,main,bm)=>{const c={id,name,level:lv,job,world:'스카니아',isMain:!!main,ocid:'',bosses:{},weekly:{},monthly:{},auto:{},sync:{},drops:{}};
   wk.slice(0,12).forEach(b=>{c.bosses[b.id]={enabled:true,diff:b.diffs[b.diffs.length-1],party:1};}); wk.slice(0,n).forEach(b=>c.weekly[b.id]=true);
   if(bm){ c.bosses.blackmage={enabled:true,diff:'hard',party:1}; if(bm==='done') c.monthly.blackmage=S.period.week; } return c;};
 S.characters=[mk('c1','단풍용사',287,'히어로',12,true,'todo'),mk('c2','은월달빛',279,'은월',12),mk('c3','아델의칼',271,'아델',11,false,'todo'),mk('c4','비숍조아',262,'비숍',12,false,'done')];
 S.activeId='c3'; save(); render(); })()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR')
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    pg.goto('http://localhost:8787/index.html'); pg.wait_for_timeout(500)
    pg.evaluate(SETUP); pg.wait_for_timeout(300)
    ov=lambda: dict(pg.evaluate("[...document.querySelectorAll('#charList .char')].map(e=>[e.dataset.id,e.querySelector('.dov')?e.querySelector('.dov').innerText.replace(/\\s+/g,' ').trim():null])"))
    o=ov(); print(o)
    check('no stamp anywhere', pg.query_selector('.donestamp') is None)
    check('c1 12/12 + 검마 selected not cleared → warning variant', o['c1'].replace(' ','')=='★이번주보스완료!검마격파필요', o['c1'])
    check('no old text / parentheses', '격파 안함' not in pg.inner_text('#charList') and '(' not in o['c1'], o['c1'])
    check('warn text exact', pg.evaluate("document.querySelector('.char[data-id=c1] .dov-warn').textContent.trim()")=='!검마 격파 필요')
    check('c2 12/12, 검마 not selected → plain', o['c2']=='★ 이번 주 보스 완료', o['c2'])
    check('c3 11/12 → no overlay', o['c3'] is None)
    check('c4 12/12, 검마 cleared → plain', o['c4']=='★ 이번 주 보스 완료', o['c4'])
    st=pg.evaluate("(()=>{const d=document.querySelector('.char[data-id=c1] .dov'),c=d.parentElement,cs=getComputedStyle(d),w=document.querySelector('.char[data-id=c1] .dov-warn');const r=d.getBoundingClientRect(),cr=c.getBoundingClientRect();return {bg:cs.backgroundColor,pe:cs.pointerEvents,rad:cs.borderRadius,cover:Math.abs(r.width-cr.width)<3&&Math.abs(r.height-cr.height)<3,star:getComputedStyle(document.querySelector('.dov-star')).color,txt:getComputedStyle(document.querySelector('.dov-ok')).color,warn:getComputedStyle(w).color,ex:getComputedStyle(document.querySelector('.dov-ex')).borderTopColor,ok1line:document.querySelector('.char[data-id=c2] .dov-ok').getBoundingClientRect().height<24}})()")
    check('overlay style', st['bg']=='rgba(0, 0, 0, 0.55)' and st['pe']=='none' and st['cover'] and st['star']=='rgb(255, 210, 63)' and st['txt']=='rgb(255, 255, 255)' and st['warn']=='rgb(255, 90, 90)' and st['ok1line'], st)
    f=pg.evaluate(FIT); check('desktop: 2 lines, warning below, centered, inside card', fitok(f) and 'wIn' in f['c1'] and 'wIn' not in f['c2'], f)
    pg.mouse.move(5,5); pg.wait_for_timeout(250)
    pg.locator('#charList').screenshot(path=''+OUT+'/done_overlay.png')
    if os.environ.get('MBT_SHOT'): pg.locator('#charList').screenshot(path=os.environ['MBT_SHOT'])
    pg.hover('.char[data-id=c1] .nm'); pg.wait_for_timeout(250)
    check('hover fades overlay out', pg.evaluate("getComputedStyle(document.querySelector('.char[data-id=c1] .dov')).opacity")=='0' and pg.evaluate("getComputedStyle(document.querySelector('.char[data-id=c2] .dov')).opacity")=='1')
    pg.locator('#charList').screenshot(path=''+OUT+'/done_overlay_hover.png')
    # 클릭·버튼·정렬은 덮개를 통과
    hit=pg.evaluate("(()=>{const c=document.querySelector('.char[data-id=c2]').getBoundingClientRect();const e=document.elementFromPoint(c.x+c.width/2,c.y+c.height/2);return e.closest('.dov')?'dov':e.closest('.char')?.dataset.id})()")
    check('center hit passes through overlay', hit=='c2', hit)
    pg.click('.char[data-id=c2]'); pg.wait_for_timeout(150); check('click selects card', pg.evaluate('S.activeId')=='c2')
    pg.click('.char[data-id=c2] [data-edit]'); pg.wait_for_selector('#charModal.show'); check('✎ works', pg.input_value('#fName')=='은월달빛'); pg.click('#fCancel')
    order=lambda: pg.evaluate("S.characters.map(c=>c.id)")
    pg.click('[data-move="c2|-1"]'); pg.wait_for_timeout(150); check('▲ works', order()[:2]==['c2','c1'], order())
    pg.drag_and_drop('.char[data-id="c4"]', '.char[data-id="c2"]', target_position={'x':40,'y':4}); pg.wait_for_timeout(200)
    check('drag reorder works over overlay', order()[0]=='c4', order())
    # 검마 잡으면 경고 사라짐
    pg.evaluate("(()=>{const c=S.characters.find(c=>c.id==='c1');c.monthly.blackmage=S.period.week;save();render();})()"); pg.wait_for_timeout(150)
    check('warning disappears after 검마 clear', ov()['c1']=='★ 이번 주 보스 완료')
    pg.evaluate("(()=>{const c=S.characters.find(c=>c.id==='c2');delete c.weekly[Object.keys(c.weekly)[0]];save();render();})()"); pg.wait_for_timeout(150)
    check('overlay gone below 12', ov()['c2'] is None)
    pg.click('#themeBtn'); pg.wait_for_timeout(150); pg.locator('#charList').screenshot(path=OUT+'/stamp_dark.png'); pg.click('#themeBtn')
    pg.evaluate("(()=>{S.period.week='2000-01-01';save();})()"); pg.reload(); pg.wait_for_timeout(600)
    check('overlay gone after weekly reset', all(v is None for v in ov().values()), ov())
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append(str(e)))
    m.goto('http://localhost:8787/index.html'); m.wait_for_timeout(400); m.evaluate(SETUP); m.wait_for_timeout(300)
    check('mobile overlay + no overflow', m.query_selector('.char[data-id=c1] .dov') is not None and not m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    f=m.evaluate(FIT); check('mobile: 2 lines fit inside card', fitok(f) and 'wIn' in f['c1'], f)
    m.screenshot(path=OUT+'/stamp_mobile.png')
    m.set_viewport_size({'width':320,'height':700}); m.wait_for_timeout(200)
    f=m.evaluate(FIT); check('320px: 2 lines fit inside card', fitok(f) and not m.evaluate('document.documentElement.scrollWidth>innerWidth'), f)
    m.screenshot(path=OUT+'/stamp_mobile320.png')
    # 터치: 덮개 위 탭이 카드 선택으로 통과
    t=b.new_context(viewport={'width':375,'height':812},has_touch=True,is_mobile=True,locale='ko-KR'); tp=t.new_page(); tp.on('pageerror',lambda e:errs.append(str(e)))
    tp.goto('http://localhost:8787/index.html'); tp.wait_for_timeout(400); tp.evaluate(SETUP); tp.wait_for_timeout(300)
    tp.tap('.char[data-id=c1]'); tp.wait_for_timeout(200); check('touch tap passes through overlay', tp.evaluate('S.activeId')=='c1' and tp.evaluate("getComputedStyle(document.querySelector('.char[data-id=c1] .dov')).opacity")=='1')
    t.close()
    pg.goto('http://localhost:8787/index.html'); pg.wait_for_timeout(600)
    v=pg.inner_text('body')
    check('no settings tab / API side card / backup / proxy text', pg.query_selector('[data-tab="settings"]') is None and pg.query_selector('#apiSide') is None and pg.query_selector('#exportBtn') is None and not any(w in v for w in ['프록시','JSON','백업','serve.py','연결 방식']), [w for w in ['프록시','JSON','백업','serve.py','연결 방식'] if w in v])
    check('limits fixed 12/1', pg.evaluate('[S.settings.weeklyLimit,S.settings.monthlyLimit]')==[12,1])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
