import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 썬데이 메이플 카드 (소식 카드 아래, 1/3 : 2/3, 머리글 '☀ 썬데이', 맨 아래 혜택 한 줄) — 모의 feed.json + 모의 이미지
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil, datetime
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM, KA
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    path=os.path.join(OUT,name); loc.screenshot(path=path,**kw)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL='http://localhost:8787/index.html'
KST=datetime.timezone(datetime.timedelta(hours=9)); now=datetime.datetime.now(KST)
iso=lambda d: d.replace(microsecond=0).isoformat()
def ch(id,name,lv,job,ocid,acc,main=False):
    return {'id':id,'name':name,'level':lv,'job':job,'world':'스카니아','ocid':ocid,'accId':acc,'isMain':main,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main','a1',True),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1','a1')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM}],'autoSync':False,'lastSync':int(time.time()*1000)}}
IMG='https://lwi.nexon.com/maplestory/2026/1009_board/SUNDAYTEST.png'
SUN={'id':1399,'title':'스페셜 썬데이 메이플','url':'https://maplestory.nexon.com/News/Event/1399','image':IMG,'benefit':'미라클 타임 · 몬스터파크 경험치 +250%',
     'start':iso(now+datetime.timedelta(days=2)),'end':iso(now+datetime.timedelta(days=2,hours=23,minutes=59))}
def mkfeed(sun):
    f={'version':1,'updatedAt':iso(now),'sources':{k:{'label':k,'ok':True,'checkedAt':iso(now),'lastOkAt':iso(now),'error':''} for k in ['saryo','patch','test','mabbak']},
       'items':{'saryo':[],'patch':[{'id':f'update:{800+i}','title':f'클라이언트 1.2.{400+i} 업데이트 안내','url':'https://maplestory.nexon.com/news/update/1','date':iso(now-datetime.timedelta(days=30-i))} for i in range(12,0,-1)],'test':[],'mabbak':[]}}
    if sun: f['sunday']=sun
    return f
STATE={'feed':mkfeed(SUN)}
SVG='<svg xmlns="http://www.w3.org/2000/svg" width="876" height="3692"><rect width="876" height="3692" fill="#ffe27a"/><circle cx="438" cy="400" r="250" fill="#f5c518"/><text x="438" y="1200" font-size="120" text-anchor="middle">SUNDAY</text></svg>'
def img_route(r): r.fulfill(status=200,content_type='image/svg+xml',body=SVG)
CARDS="(()=>{const f=document.querySelector('#feedCard').getBoundingClientRect(),s=document.querySelector('#sunCard'),r=s.getBoundingClientRect(),im=s.querySelector('img'),bn=s.querySelector('.sunben');return {fh:f.height,fbot:f.bottom,sh:r.height,stop:r.top,sbot:r.bottom,sdisp:getComputedStyle(s).display,ih:innerHeight,doc:document.scrollingElement.scrollHeight,sw:document.scrollingElement.scrollWidth,ben:bn?{bot:bn.getBoundingClientRect().bottom,last:bn===s.querySelector('.sunbody').lastElementChild,ws:getComputedStyle(bn).whiteSpace}:null,img:im?{fit:getComputedStyle(im).objectFit,nw:im.naturalWidth,h:im.getBoundingClientRect().height,bot:im.getBoundingClientRect().bottom}:null}})()"
NOSIDE="(()=>{const a=document.querySelector('#feedCard'),b=document.querySelector('#sunCard');a.style.display='none';const bd=b.style.display;b.style.display='none';const h=document.scrollingElement.scrollHeight;a.style.display='';b.style.display=bd;return h})()"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(STATE['feed'],ensure_ascii=False)))
    ctx.route('https://lwi.nexon.com/**',img_route)
    ctx.route(lambda u: 'maplestory.nexon.com' in u, lambda r:r.fulfill(status=200,content_type='text/html',body='<p>ok</p>'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'gsi' not in m.text else None)
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload()
    pg.wait_for_selector('#sunCard img'); pg.wait_for_function("document.querySelector('#sunCard img').complete"); pg.wait_for_timeout(300)
    pos=pg.evaluate("(()=>{const f=document.querySelector('#feedCard'),s=document.querySelector('#sunCard');return {inAside:!!s.closest('aside.side-sticky'),after:f.nextElementSibling===s,below:s.getBoundingClientRect().top>=f.getBoundingClientRect().bottom}})()")
    check('sun card right below feed card in left sidebar', all(pos.values()), pos)
    hd=pg.evaluate("(()=>{const t=document.querySelector('#sunCard .ftabs .ftab');const sv=t.querySelector('svg.sunico');return {txt:t.textContent.trim(),on:t.classList.contains('on'),svgFirst:t.firstElementChild===sv,color:sv?getComputedStyle(sv).color:'',w:sv?sv.getBoundingClientRect().width:0}})()")
    check("tab-style header '썬데이' with yellow sun icon before text", hd['txt']=='썬데이' and hd['on'] and hd['svgFirst'] and hd['color']=='rgb(245, 197, 24)' and 12<=hd['w']<=18, hd)
    lk=pg.evaluate("(()=>{const a=document.querySelector('#sunCard a.sunimg');return {href:a.href,tgt:a.target,rel:a.rel,src:a.querySelector('img').getAttribute('src')}})()")
    check('image links to the event post (new tab) and uses feed image URL', lk['href']==SUN['url'] and lk['tgt']=='_blank' and 'noopener' in lk['rel'] and lk['src']==IMG, lk)
    cap=pg.inner_text('#sunCard .suncap'); check('caption: title + date', '스페셜 썬데이 메이플' in cap and '.' in cap, cap)
    ben=pg.inner_text('#sunCard .sunben'); check('benefit line at the bottom shows benefit text', '미라클 타임' in ben, ben)
    for vw,vh in [(1280,800),(1920,1080)]:
        pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(300)
        for t in ['boss','summary','daily']:
            pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(250); pg.evaluate('feedFit()')
            c=pg.evaluate(CARDS); h0=pg.evaluate(NOSIDE)
            ratio=c['fh']/(c['fh']+c['sh'])
            check(f'{vw}x{vh} {t}: feed ≈1/3 (or its 2-row minimum), sun the rest', c['sdisp']!='none' and (0.28<=ratio<=0.40 or (ratio>0.40 and c['fh']<=133)), (round(ratio,3),c['fh'],c['sh']))
            if vw==1920: check(f'{vw}x{vh} {t}: ratio ≈1/3 exactly', 0.30<=ratio<=0.37, round(ratio,3))
            check(f'{vw}x{vh} {t}: no extra page height, both cards inside viewport', c['doc']<=max(h0,c['ih']) and c['sbot']<=c['ih'], (c['doc'],h0,c['sbot'],c['ih']))
            check(f'{vw}x{vh} {t}: image contained, benefit line last & inside card', c['img'] and c['img']['fit']=='contain' and c['img']['nw']>0 and c['img']['h']<=c['sh'] and c['ben'] and c['ben']['last'] and c['ben']['ws']=='nowrap' and c['ben']['bot']<=c['sbot'] and c['img']['bot']<=c['ben']['bot'], c)
            check(f'{vw}x{vh} {t}: feed card shows ≥2 rows', pg.evaluate('feed.per')>=2, pg.evaluate('feed.per'))
            pg.evaluate('scrollTo(0,document.scrollingElement.scrollHeight)'); pg.wait_for_timeout(80)
            bb=pg.evaluate("document.querySelector('#sunCard').getBoundingClientRect().bottom"); check(f'{vw}x{vh} {t}: sun card inside viewport when scrolled', bb<=vh, bb); pg.evaluate('scrollTo(0,0)')
        pg.click('[data-tab=boss]'); pg.wait_for_timeout(200); pg.mouse.move(vw-10,vh-10)
        shot(pg,f'sun_{vw}x{vh}.png'); shot(pg.locator('#sunCard'),f'sun_card_{vw}.png')
    pg.set_viewport_size({'width':1280,'height':560}); pg.wait_for_timeout(300); pg.evaluate('feedFit()')
    c=pg.evaluate(CARDS); h0=pg.evaluate(NOSIDE)
    check('short window: page not taller (sun hidden if no room)', c['doc']<=max(h0,c['ih']) or c['sdisp']=='none', (c,h0))
    for vw,vh in [(390,844),(320,640)]:
        pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(300)
        c=pg.evaluate(CARDS); sw0=pg.evaluate("(()=>{const b=document.querySelector('#sunCard');b.style.display='none';const w=document.scrollingElement.scrollWidth;b.style.display='';return w})()")
        c['sw']=c['sw']-max(0,sw0-vw)  # 320px 헤더 넘침(기존 알려진 현상)은 빼고
        check(f'mobile {vw}: sun card below feed, no horizontal overflow, image 100..520px, benefit shown', c['stop']>=c['fbot'] and c['sdisp']!='none' and c['sw']<=vw and 100<=c['img']['h']<=520 and c['ben'] and c['ben']['bot']<=c['sbot'], c)
    pg.locator('#sunCard').scroll_into_view_if_needed(); shot(pg.locator('#sunCard'),'sun_card_mobile.png')
    pg.set_viewport_size({'width':1280,'height':800})
    STATE['feed']=mkfeed(dict(SUN,benefit='')); pg.evaluate('feedLoad()'); pg.wait_for_timeout(400)
    check('no benefit text → falls back to post title', pg.inner_text('#sunCard .sunben').endswith('스페셜 썬데이 메이플'), pg.inner_text('#sunCard .sunben'))
    STATE['feed']=mkfeed(None); pg.evaluate('feedLoad()'); pg.wait_for_timeout(400)
    em=pg.locator('#sunCard .sunempty'); check('no sunday → tidy placeholder with sun icon', em.count()==1 and '썬데이 메이플' in em.inner_text() and pg.locator('#sunCard .sunempty svg.sunico').count()==1 and pg.locator('#sunCard img').count()==0)
    shot(pg.locator('#sunCard'),'sun_card_empty.png')
    STATE['feed']=mkfeed(dict(SUN,id=1400,title='썬데이 메이플',url='https://maplestory.nexon.com/News/Event/1400')); pg.evaluate('feedLoad()'); pg.wait_for_timeout(400)
    check('new sunday post replaces card', pg.get_attribute('#sunCard a.sunimg','href').endswith('/1400'))
    pg.evaluate("window.__im=document.querySelector('#sunCard img')"); pg.evaluate('feedLoad()'); pg.wait_for_timeout(300)
    check('same data → image element kept (no reload)', pg.evaluate("window.__im===document.querySelector('#sunCard img')"))
    pg.close(); b.close()
finally:
    srv.terminate()
print('ERRORS',errs)
if errs: fails.append('js errors')
print('FAILS',fails); sys.exit(1 if fails else 0)
