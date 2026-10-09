import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')  # 지정하면 feed_card.png 를 그 폴더에도 저장
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 소식 피드 카드 (모의 feed.json)
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil, datetime
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM, KA
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(loc_or_pg,name,**kw):
    path=os.path.join(OUT,name); loc_or_pg.screenshot(path=path,**kw)
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
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main','a1',True),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1','a1'),
                ch('c3','신궁짱',265,'신궁','ocid-alt2','a1'),ch('c4','부계정비숍',268,'비숍','ocid-b1','a2')],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM},{'id':'a2','label':'부계정','key':KA}],'autoSync':False,'lastSync':int(time.time()*1000)}}
def src(label,ok=True,err=''):
    return {'label':label,'ok':ok,'checkedAt':iso(now),'lastOkAt':iso(now-datetime.timedelta(hours=0 if ok else 5)),'error':err}
FEED_={'version':1,'updatedAt':iso(now),
 'sources':{'saryo':src('사료감지'),'patch':src('패치내역'),'test':src('테섭'),'mabbak':src('마빡도로시',False,'5974: HTTPError 403')},
 'items':{
  'saryo':[{'id':'notice:900002','title':'(추가) 리워드 드롭 관련 오류 안내 — 메이플 운영자 NPC 에서 사과의 마음 수령','url':'https://maplestory.nexon.com/News/Notice/Notice/900002','date':iso(now-datetime.timedelta(days=1)),'end':iso(now+datetime.timedelta(days=12)),'src':'notice'},
           {'id':'notice:900001','title':'지난 점검 연장 보상 안내','url':'https://maplestory.nexon.com/News/Notice/Notice/900001','date':iso(now-datetime.timedelta(days=20)),'end':iso(now-datetime.timedelta(days=6)),'src':'notice'}],
  'patch':[{'id':f'update:{800+i}','title':f'클라이언트 1.2.{400+i} 업데이트 안내','url':f'https://maplestory.nexon.com/news/update/{800+i}','date':iso(now-datetime.timedelta(days=30-i))} for i in range(14,0,-1)]
          +[{'id':'minor:900020','title':'[패치완료] 10/8(수) ver1.2.419 마이너(6) 패치(16:40 적용)','url':'https://maplestory.nexon.com/News/Notice/Notice/900020','date':iso(now-datetime.timedelta(days=1)),'src':'minor'},
            {'id':'minor:900010','title':'[패치완료] 9/25(목) ver1.2.419 마이너패치(15:10 적용)','url':'https://maplestory.nexon.com/News/Notice/Notice/900010','date':iso(now-datetime.timedelta(days=17,hours=12)),'src':'minor'}],
  'test':[{'id':f'test:{150+i}','title':f'클라이언트 1.2.{150+i} 릴리즈(이벤트, 컨텐츠, 개선사항 및 오류 수정) 아주 긴 제목 테스트','url':f'https://maplestory.nexon.com/Testworld/News/Update/{150+i}','date':iso(now-datetime.timedelta(days=60-i))} for i in range(49,0,-1)],
  'mabbak':[{'id':'inven:5974:7258005','title':'10월 테섭(라방) 일정 / 2026 한글날 이벤트 요약','url':'https://www.inven.co.kr/board/maple/5974/7258005','date':'2025-09-30T02:36:00+09:00','board':'5974'}]}}
FEED=FEED_; FEED['items']['patch'].sort(key=lambda x:x['date'],reverse=True)  # update_feed.py 와 같이 날짜순
feed_hits=[]
def feed_route(route):
    feed_hits.append(route.request.url)
    route.fulfill(status=200,content_type='application/json',body=json.dumps(FEED,ensure_ascii=False))
CARD="(()=>{const c=document.querySelector('#feedCard'),r=c.getBoundingClientRect();return {top:r.top,bottom:r.bottom,h:r.height,per:feed.per,rows:c.querySelectorAll('.flist li').length,sh:document.scrollingElement.scrollHeight,ih:innerHeight,inner:c.querySelector('.fbody').scrollHeight-c.querySelector('.fbody').clientHeight}})()"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':800},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort()); ctx.route('**/feed.json*',feed_route)
    ctx.route(lambda u: 'maplestory.nexon.com' in u or 'inven.co.kr' in u, lambda r:r.fulfill(status=200,content_type='text/html',body='<p>ok</p>'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'gsi' not in m.text else None)
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); feed_hits.clear(); pg.reload()
    pg.wait_for_selector('#feedCard .flist li'); pg.wait_for_timeout(300)
    check('feed.json fetched once, cache-busted', len(feed_hits)==1 and '?t=' in feed_hits[0], feed_hits)
    # 1) 위치: 왼쪽 사이드바, 캐릭터 카드 바로 아래 ('초기화까지' 카드는 2026-10-10 오른쪽 열로 이동)
    pos=pg.evaluate("(()=>{const f=document.querySelector('#feedCard'),r=document.querySelector('#charList').closest('.card');return {inAside:!!f.closest('aside.side-sticky'),after:r.nextElementSibling===f,below:f.getBoundingClientRect().top>=r.getBoundingClientRect().bottom,left:f.getBoundingClientRect().left<400}})()")
    check('card in left sidebar right below the character card (reset card moved to right column 2026-10-10)', all(pos.values()), pos)
    tabs=pg.eval_on_selector_all('#feedCard .ftab',"e=>e.map(x=>[x.dataset.ftab,x.childNodes[0].textContent,(x.querySelector('.fcnt')||{}).textContent||''])")
    check('4 tabs with unseen counts', tabs==[['saryo','사료감지','2'],['patch','패치내역','16'],['test','테섭','49'],['mabbak','마빡도로시','1']], tabs)
    check('tabs fit on one line', pg.evaluate("(()=>{const t=[...document.querySelectorAll('#feedCard .ftab')].map(e=>e.getBoundingClientRect().top);return Math.max(...t)-Math.min(...t)<1 && document.querySelector('#feedCard .ftabs').scrollWidth<=document.querySelector('#feedCard .ftabs').clientWidth})()"))
    # 2) 사료: N 배지, 기한, 만료 흐리게
    it=pg.eval_on_selector_all('#feedCard .fit',"e=>e.map(x=>({n:!!x.querySelector('.fnew'),exp:x.classList.contains('exp'),op:getComputedStyle(x).opacity,end:(x.querySelector('.fend')||{}).textContent,dt:x.querySelector('.fdt').textContent,tgt:x.target,rel:x.rel,ell:getComputedStyle(x.querySelector('.ftt')).textOverflow,ws:getComputedStyle(x.querySelector('.ftt')).whiteSpace,h:x.getBoundingClientRect().height}))")
    print(it)
    check('saryo items: N badges, ~end date, expired dimmed', len(it)==2 and all(x['n'] for x in it) and not it[0]['exp'] and it[0]['op']=='1' and it[1]['exp'] and float(it[1]['op'])<0.6 and all(x['end'].startswith('~') for x in it), it)
    check('one-line ellipsis title, date, opens new tab', all(x['ell']=='ellipsis' and x['ws']=='nowrap' and x['tgt']=='_blank' and 'noopener' in x['rel'] and len(x['dt'])>=5 and x['h']<=31 for x in it), it)
    check('no feed error note on healthy tab', pg.locator('#feedCard .fnote').count()==0)
    pg.mouse.move(700,500); pg.wait_for_timeout(100)
    shot(pg,'feed_card.png'); shot(pg.locator('#feedCard'),'feed_card_saryo.png')
    for t in ['patch','test','mabbak']:
        pg.click(f'[data-ftab={t}]'); pg.mouse.move(700,500); pg.wait_for_timeout(60); shot(pg.locator('#feedCard'),f'feed_card_{t}.png')
    pg.click('[data-ftab=patch]'); pg.wait_for_timeout(60)
    first=pg.inner_text('#feedCard .fit .ftt >> nth=0'); ids=pg.evaluate("feedItems('patch').map(x=>x.id)")
    check('patch tab: newest minor patch shown first', first.startswith('[패치완료] 10/8(수)'), first)
    check('patch tab: minor patches merged among updates by date', ids[0]=='minor:900020' and ids[1:4]==['update:814','update:813','minor:900010'], ids[:5])
    pg.click('[data-ftab=saryo]')
    # 3) 클릭 → 읽음
    with ctx.expect_page() as np: pg.click('#feedCard .fit >> nth=0')
    newp=np.value; newp.wait_for_load_state(); check('item opens its URL in a new tab', newp.url.endswith('/900002'), newp.url); newp.close()
    pg.wait_for_timeout(150)
    check('clicked item loses N, tab count 2→1', pg.locator('#feedCard .fit >> nth=0').locator('.fnew').count()==0 and pg.inner_text('[data-ftab=saryo] .fcnt')=='1')
    # 4) 페이지 맞춤 + 쪽 넘김
    c=pg.evaluate(CARD); print('1280x800',c)
    pg.evaluate("document.querySelector('#feedCard').style.display='none'"); sh0=pg.evaluate('document.scrollingElement.scrollHeight'); pg.evaluate("document.querySelector('#feedCard').style.display=''")
    check('1280x800: card fits viewport, no inner scroll, page not longer because of it', c['bottom']<=c['ih'] and c['inner']<=0 and c['sh']<=max(sh0,c['ih']), (c,sh0))
    per=c['per']; check('rows per page fits card (2..20)', 2<=per<=20, per)
    pg.click('[data-ftab=test]'); pg.wait_for_timeout(100)
    pages=-(-49//per)
    pgr=lambda: pg.eval_on_selector_all('#feedCard .fpg',"e=>e.map(x=>(x.classList.contains('fnav')?(x.disabled?'x':'')+x.textContent:x.textContent)+(x.classList.contains('on')?'*':''))")
    r=pgr(); print(r)
    check('test tab: first page full, 5 page numbers + prev/next', pg.locator('#feedCard .flist li').count()==per and r==['x‹','1*','2','3','4','5','›'], r)
    pg.click('#feedCard .fpg.fnav >> nth=1'); pg.click('#feedCard .fpg.fnav >> nth=1'); pg.click('#feedCard .fpg.fnav >> nth=1'); pg.wait_for_timeout(50)
    r=pgr(); check('next ×3 → page 4, window 2–6', r==['‹','2','3','4*','5','6','›'], r)
    first=pg.inner_text('#feedCard .fit .ftt >> nth=0'); check('page 4 shows the right items', first.startswith(f'클라이언트 1.2.{150+49-3*per} '), first)
    pg.click(f'#feedCard [data-fpage="{pages}"]') if pg.locator(f'#feedCard [data-fpage="{pages}"]').count() else None
    pg.evaluate(f"feed.page={pages};renderFeed()"); r=pgr(); check('last page: next disabled', r[-1]=='x›' and pg.locator('#feedCard .flist li').count()==49-(pages-1)*per, r)
    tt=pg.evaluate("(()=>{const e=document.querySelector('#feedCard .ftt');return e.scrollWidth>e.clientWidth})()"); check('long title truncated', tt)
    pg.click('[data-ftab=patch]'); r=pgr(); check('switching tab resets to page 1', '1*' in r and pg.evaluate('feed.page')==1, r)
    if -(-16//per)<=5: check('≤5 pages → no prev/next'  # 패치 16개가 5쪽 이하일 때만 (2026-10-10: 오른쪽 열 높이 고정으로 내용이 짧은 모의 화면에서는 소식 카드가 최소 2줄이 될 수 있음)
         , not any('‹' in x or '›' in x for x in r), r)
    pg.click('[data-ftab=test]'); check('back to test tab → page 1 again', pg.evaluate('feed.page')==1)
    # 5) 수집 실패 표시
    pg.click('[data-ftab=mabbak]'); note=pg.locator('#feedCard .fnote')
    check('failed source → subtle note with error tooltip', note.count()==1 and '수집 실패' in note.inner_text() and note.get_attribute('title')=='5974: HTTPError 403', note.count() and note.inner_text())
    check('old-year date shows yy.mm.dd', pg.inner_text('#feedCard .fdt')=='25.09.30', pg.inner_text('#feedCard .fdt'))
    c=pg.evaluate(CARD); check('note does not cause inner overflow', c['inner']<=0, c)
    # 6) 읽음 유지 (reload)
    pg.reload(); pg.wait_for_selector('#feedCard .flist li'); pg.wait_for_timeout(200)
    check('seen state persists across reload', pg.inner_text('[data-ftab=saryo] .fcnt')=='1' and pg.locator('#feedCard .fit >> nth=0').locator('.fnew').count()==0)
    # 7) 모든 탭에서 카드 때문에 스크롤 안 생김 (1280x800, 1920x1080)
    for vw,vh in [(1280,800),(1920,1080)]:
        pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(200)
        for t in ['boss','summary','history','total','daily','guild']:
            pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(250)
            c=pg.evaluate(CARD)
            pg.evaluate("document.querySelector('#feedCard').style.display='none'"); sh0=pg.evaluate('document.scrollingElement.scrollHeight')
            pg.evaluate("document.querySelector('#feedCard').style.display=''"); pg.evaluate('feedFit()')
            check(f'{vw}x{vh} {t}: card adds no page height, fits viewport, no inner scroll', c['sh']<=max(sh0,c['ih']) and c['bottom']<=c['ih'] and c['inner']<=0, (c,sh0))
            pg.evaluate('scrollTo(0,document.scrollingElement.scrollHeight)'); pg.wait_for_timeout(80)
            bb=pg.evaluate("document.querySelector('#feedCard').getBoundingClientRect().bottom")
            check(f'{vw}x{vh} {t}: card stays inside viewport when scrolled', bb<=vh, bb); pg.evaluate('scrollTo(0,0)')
        print(vw,vh,'per',pg.evaluate('feed.per'))
    pg.click('[data-tab=history]'); pg.wait_for_timeout(200)
    SIDE="(()=>{const s=document.querySelector('#sunCard');return document.querySelector('#feedCard').getBoundingClientRect().height+(s&&getComputedStyle(s).display!=='none'?s.getBoundingClientRect().height:0)})()"
    big=pg.evaluate(SIDE); pg.set_viewport_size({'width':1280,'height':800}); pg.wait_for_timeout(250); small=pg.evaluate(SIDE); pg.set_viewport_size({'width':1920,'height':1080}); pg.wait_for_timeout(250)
    # 썬데이 카드가 생긴 뒤로는 소식 줄 수 대신 왼쪽 아래(소식+썬데이) 전체 높이로 비교 (1920 에서는 썬데이가 2/3 를 차지)
    check('1920x1080 gives the bottom-left cards more room than 1280x800', big>small and pg.evaluate('feed.per')>=2, (big,small,pg.evaluate('feed.per'),per))
    # 8) 모바일: 본문 아래 자연스러운 흐름
    for vw,vh in [(390,844),(320,640)]:
        pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(250)
        m=pg.evaluate("(()=>{const f=document.querySelector('#feedCard').getBoundingClientRect(),v=document.querySelector('#view').getBoundingClientRect(),cl=document.querySelector('#charList').getBoundingClientRect();return {after:f.top>=v.bottom,charsFirst:cl.top<v.top,h:document.querySelector('#feedCard').style.height,per:feed.per,w:f.width,right:f.right,iw:innerWidth,inner:document.querySelector('#feedCard .fbody').scrollHeight-document.querySelector('#feedCard .fbody').clientHeight}})()")
        check(f'mobile {vw}: feed below content, chars still first, natural height, 6 rows, no overflow', m['after'] and m['charsFirst'] and m['h']=='' and m['per']==6 and m['right']<=m['iw'] and m['inner']<=0, m)
    shot(pg.locator('#feedCard'),'feed_card_mobile.png')
    # 9) 5분마다 다시 읽기
    n0=len(feed_hits); pg.evaluate('feedLoad()'); pg.wait_for_timeout(200); check('feedLoad refetches', len(feed_hits)==n0+1)
    pg.close(); b.close()
finally:
    srv.terminate()
print('ERRORS',errs)
if errs: fails.append('js errors')
print('FAILS',fails); sys.exit(1 if fails else 0)
