import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 레이아웃: 캐릭터 목록 8명 + 안쪽 스크롤 · '초기화까지' 카드 = 오른쪽 열 맨 아래(화면 안) · 사이드바 소식 카드 위로 · 캐릭터 정렬(기본순/보스 미완료순)
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def save_shot(pg,name,**kw):
    path=os.path.join(OUT,name); pg.screenshot(path=path,**kw)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
PORT=8799
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
W12=['zakum','pierre','vonbon','queen','vellum','magnus','papulatus','lotus','damien','slime','lucid','will']
def ch(i,done,world='스카니아'):
    bs={k:{'enabled':True,'diff':'chaos' if k in('zakum','pierre','vonbon','queen','vellum','papulatus') else ('hard' if k in('magnus','lotus','damien','lucid','will') else 'normal'),'party':1} for k in W12}
    return {'id':f'c{i}','name':f'캐릭{i:02d}','level':260+i,'job':'히어로','world':world,'ocid':'','accId':'','isMain':i==1,'image':'',
            'bosses':bs,'weekly':{k:True for k in W12} if done else {'zakum':True},'monthly':{},'auto':{},'sync':{},'drops':{}}
DONE={1,3,6,7,10}
CH=[ch(i,i in DONE) for i in range(1,12)]+[ch(12,False,'루나'),ch(13,True,'루나'),ch(14,False,'챌린저스2'),ch(15,False,'테스트월드')]
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':CH,
  'settings':{'accounts':[],'autoSync':False,'lastSync':int(time.time()*1000)}}
ORDER="[...document.querySelectorAll('#charList .char[data-id]')].map(e=>e.dataset.id)"
GEOM="""(()=>{const r=e=>e?e.getBoundingClientRect():null, de=document.scrollingElement;
  const rs=r(document.querySelector('.resetcard')), cl=document.querySelector('#charList'), fc=r(document.querySelector('#feedCard'));
  const chs=[...cl.querySelectorAll('.char[data-id]')], L=r(cl);
  const vis=chs.filter(c=>{const x=r(c);return x.top>=L.top-1&&x.bottom<=L.bottom+1}).length;
  return {ih:innerHeight, docH:de.scrollHeight, reset:rs?{top:rs.top,bot:rs.bottom,txt:document.querySelector('#resetInfo').innerText}:null,
    inRcol:!!document.querySelector('.rcol>.resetcard:last-child'), sideReset:!!document.querySelector('.side-sticky #resetInfo'),
    listScroll:cl.scrollHeight>cl.clientHeight+2, vis, n:chs.length, feedTop:fc?fc.top:null, listBot:r(cl.closest('.card')).bottom,
    sideBot:Math.max(...[...document.querySelectorAll('.side-sticky>.card')].filter(e=>getComputedStyle(e).display!=='none').map(e=>r(e).bottom))}})()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for vw,vh in [(1280,800),(1920,1080)]:
      ctx=b.new_context(viewport={'width':vw,'height':vh},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
      ctx.route('https://accounts.google.com/**',lambda r:r.abort()); ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
      pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload()
      pg.wait_for_selector('.resetcard #resetInfo b'); pg.wait_for_timeout(400)
      g=pg.evaluate(GEOM); tag=f'{vw}x{vh}'
      check(f'{tag}: reset card is last in right column, not in sidebar', g['inRcol'] and not g['sideReset'] and '초기화까지' in g['reset']['txt'], g['reset'])
      check(f'{tag}: reset card fully inside viewport at top', g['reset']['bot']<=g['ih'] and g['reset']['top']>=0, (g['reset'],g['ih']))
      check(f'{tag}: char list shows up to 8 rows (8 when it fits), scrolls internally', g['n']==11 and (g['vis']==8 if vh>=1000 else 4<=g['vis']<=8) and g['listScroll'], (g['n'],g['vis']))
      check(f'{tag}: feed card directly below character card', g['feedTop'] is not None and 0<=g['feedTop']-g['listBot']<=14, (g['feedTop'],g['listBot']))
      check(f'{tag}: sidebar fits in viewport', g['sideBot']<=g['ih']+1, (g['sideBot'],g['ih']))
      save_shot(pg,f'shot19_layout_{tag}.png')
      pg.evaluate("scrollTo(0,document.scrollingElement.scrollHeight)"); pg.wait_for_timeout(300); g2=pg.evaluate(GEOM)
      check(f'{tag}: reset card still inside viewport after page scroll', g2['reset']['bot']<=g2['ih'] and g2['reset']['top']>=0, g2['reset'])
      pg.evaluate("scrollTo(0,0)")
      # page scrolling: wheel over char list scrolls list not page
      xy=pg.evaluate("(()=>{const r=document.querySelector('#charList').getBoundingClientRect();return [r.left+r.width/2,r.top+60]})()"); pg.mouse.move(xy[0],xy[1]); pg.mouse.wheel(0,400); pg.wait_for_timeout(300)
      st=pg.evaluate("[document.querySelector('#charList').scrollTop, scrollY]")
      check(f'{tag}: wheel over list scrolls the list', st[0]>0, st)
      pg.evaluate("document.querySelector('#charList').scrollTop=0")
      if vw==1280:
        base=pg.evaluate(ORDER)
        check('default order', base==[f'c{i}' for i in range(1,12)], base)
        ctl=pg.evaluate("(()=>{const s=document.querySelector('.charsort'),w=s.closest('#worldTabs');return {inWorld:!!w,txt:w&&w.innerText,on:document.querySelector('.sortlink.on').dataset.csort,deco:getComputedStyle(document.querySelector('.sortlink')).textDecorationLine,fw:[...document.querySelectorAll('.sortlink')].map(e=>getComputedStyle(e).fontWeight)}})()")
        check('sort control next to world tabs', ctl['inWorld'] and '스카니아' in ctl['txt'] and '기본순' in ctl['txt'], ctl)
        check('link style underline, active bold', ctl['deco']=='underline' and ctl['on']=='base' and int(ctl['fw'][0])>int(ctl['fw'][1]), ctl)
        pg.hover('[data-csort="undone"]'); pg.wait_for_timeout(100)
        col=pg.evaluate("getComputedStyle(document.querySelector('[data-csort=\"undone\"]')).color")
        check('dark hover orange', col=='rgb(255, 154, 60)', col)
        pg.click('[data-csort="undone"]'); pg.wait_for_timeout(200)
        o=pg.evaluate(ORDER); exp=[f'c{i}' for i in range(1,12) if i not in DONE]+[f'c{i}' for i in sorted(DONE)]
        check('보스 미완료순 = stable partition', o==exp, o)
        saved=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters.map(c=>c.id)")
        check('saved default order unchanged', saved[:11]==base, saved)
        check('mode remembered in localStorage', pg.evaluate("localStorage.getItem('mapleBossTracker.charSort')")=='undone')
        check('reorder locked in sorted view', pg.evaluate("[...document.querySelectorAll('#charList [data-move]')].every(b=>b.disabled) && document.querySelector('#charList .char').getAttribute('draggable')==='false'"))
        pg.evaluate("document.querySelector('#charList').scrollTop=0"); g3=pg.evaluate(GEOM); check('sorted view same rows + scroll', g3['vis']==g['vis'] and g3['listScroll'], g3['vis'])
        pg.evaluate("document.querySelector('#charList').scrollTop=0")
        save_shot(pg,'shot19_sort_undone.png',clip={'x':0,'y':0,'width':360,'height':g3['listBot']+10})
        pg.reload(); pg.wait_for_selector('.sortlink.on'); pg.wait_for_timeout(200)
        check('mode persists after reload', pg.evaluate(ORDER)==exp and pg.evaluate("document.querySelector('.sortlink.on').dataset.csort")=='undone')
        # 완료 상태가 바뀌면 순서도 바뀜: c2 를 완료로
        pg.click('.char[data-id="c2"]'); pg.wait_for_timeout(100)
        for k in W12:
            if pg.evaluate("k=>{const c=activeChar();return !!(c.bosses[k]&&c.bosses[k].enabled)&&!c.weekly[k]}",k): pg.evaluate("(k=>{const e=document.createElement('i');e.dataset.check=k;document.querySelector('#view').appendChild(e);e.click();e.remove()})",k); pg.wait_for_timeout(30)
        o2=pg.evaluate(ORDER)
        check('newly done char moves to done group (stable)', o2==[x for x in exp if x!='c2'][:5]+['c1','c2','c3','c6','c7','c10'] , o2)
        pg.click('[data-csort="base"]'); pg.wait_for_timeout(150)
        check('기본순 restores saved order', pg.evaluate(ORDER)==base)
        pg.click('#themeBtn'); pg.wait_for_timeout(150); pg.hover('[data-csort="undone"]'); pg.wait_for_timeout(100)
        col=pg.evaluate("getComputedStyle(document.querySelector('[data-csort=\"undone\"]')).color")
        check('light hover deep orange', col=='rgb(201, 90, 0)', col)
        save_shot(pg,'shot19_layout_light.png')
      if vw==1920:
        wt=pg.evaluate("""(()=>{const tabs=[...document.querySelectorAll('#worldTabs .wtab')];return {names:tabs.map(t=>t.dataset.world),txt:document.querySelector('#worldTabs .wtablist').textContent.replace(/\\s+/g,' ').trim(),
          icons:tabs.map(t=>{const i=t.querySelector('img.wico');return i?[i.naturalWidth,i.complete]:null}),on:tabs.filter(t=>t.classList.contains('on')).map(t=>t.dataset.world),
          onStyle:(t=>[getComputedStyle(t).color,getComputedStyle(t).fontWeight,getComputedStyle(t).textDecorationLine])(document.querySelector('.wtab.on')),
          offDeco:getComputedStyle(tabs[1]).textDecorationLine}})()""")
        check('world tabs: one per world, ㅣ separators, counts', wt['names']==['스카니아','루나','챌린저스2','테스트월드'] and wt['txt'].count('ㅣ')==3 and '스카니아 (11)' in wt['txt'] and '루나 (2)' in wt['txt'], wt['txt'])
        check('official world icons (스카니아/루나/챌린저스2), none for unknown world', wt['icons'][0] and wt['icons'][0][0]==14 and wt['icons'][1] and wt['icons'][2] and wt['icons'][2][0]==13 and wt['icons'][3] is None, wt['icons'])
        check('active tab bold orange underlined (dark)', wt['on']==['스카니아'] and wt['onStyle'][0]=='rgb(255, 154, 60)' and int(wt['onStyle'][1])>=700 and wt['onStyle'][2]=='underline' and wt['offDeco']=='underline', wt)
        pg.click('.wtab[data-world="루나"]'); pg.wait_for_timeout(150)
        ids=pg.evaluate(ORDER)
        check('click 루나 → only 루나 chars', ids==['c12','c13'], ids)
        check('tab selection remembered', pg.evaluate("localStorage.getItem('mapleBossTracker.worldTab')")=='루나')
        pg.click('[data-csort="undone"]'); pg.wait_for_timeout(100)
        check('sort applies within selected world', pg.evaluate(ORDER)==['c12','c13'])
        pg.evaluate("S.characters.find(c=>c.id==='c12').weekly=Object.fromEntries(%s.map(k=>[k,true]));S.characters.find(c=>c.id==='c13').weekly={zakum:true};save();render()" % json.dumps(W12)); pg.wait_for_timeout(100)
        check('미완료순 within 루나 (c13 first)', pg.evaluate(ORDER)==['c13','c12'], pg.evaluate(ORDER))
        pg.click('[data-csort="base"]')
        save_shot(pg,'shot19_worldtabs_luna.png',clip={'x':0,'y':0,'width':480,'height':420})
        pg.reload(); pg.wait_for_selector('.wtab.on'); pg.wait_for_timeout(200)
        check('selected tab persists after reload', pg.evaluate("document.querySelector('.wtab.on').dataset.world")=='루나' and pg.evaluate(ORDER)==['c12','c13'])
        pg.drag_and_drop('.wtab[data-world="루나"]', '.wtab[data-world="스카니아"]', target_position={'x':2,'y':5}); pg.wait_for_timeout(200)
        wo=pg.evaluate("[...document.querySelectorAll('#worldTabs .wtab')].map(t=>t.dataset.world)")
        check('drag tab reorders worlds (saved)', wo[:2]==['루나','스카니아'] and pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).worldOrder.slice(0,2)")==['루나','스카니아'], wo)
        # 다른 화면에서 다른 월드 캐릭터 선택 → 그 월드 탭으로
        pg.evaluate("S.activeId='c3';save();render()"); pg.wait_for_timeout(100)
        check('selecting char from other world switches tab', pg.evaluate("document.querySelector('.wtab.on').dataset.world")=='스카니아')
        pg.click('.wtab[data-world="스카니아"]')
      ctx.close()
    # mobile sanity
    ctx=b.new_context(viewport={'width':375,'height':760},locale='ko-KR',is_mobile=True,has_touch=True); ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload(); pg.wait_for_timeout(500)
    m=pg.evaluate("({sw:document.scrollingElement.scrollWidth,iw:innerWidth,reset:!!document.querySelector('.rcol .resetcard #resetInfo b'),vis:document.querySelector('#charList').classList.contains('scroll')})")
    check('mobile: no horizontal overflow, reset card present, list scrolls', m['sw']<=m['iw']+1 and m['reset'] and m['vis'], m)
    save_shot(pg,'shot19_mobile.png',full_page=True)
    b.close()
finally:
    srv.terminate()
check('no page errors', not errs, errs)
print('FAILS',fails); print('ERRORS',errs)
sys.exit(1 if fails or errs else 0)
