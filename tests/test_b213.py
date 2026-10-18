# b213: 위 탭 바꾸면 페이지(+ 탭 안 스크롤 칸) 맨 위로, 바로(애니메이션 없음) · 다른 탭에서 캐릭터 클릭 → 이번 주 보스 + 맨 위
#       보스 탭에서 캐릭터 클릭·다시 그리기 = 스크롤 그대로 · 예시 화면도 같음
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8971'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
SMOOTH='html,body,*{scroll-behavior:smooth!important}'
def down(pg):
    pg.evaluate("window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'})"); pg.wait_for_timeout(150); return pg.evaluate("scrollY")
def cclick(pg,i):   # 실제 클릭처럼(마우스) — playwright click 은 먼저 요소로 스크롤해 버려서 좌표 클릭
    r=pg.evaluate("i=>{const e=document.querySelector(`#charList .char[data-id=\"${i}\"] .cname, #charList .char[data-id=\"${i}\"]`);const r=e.getBoundingClientRect();return [r.left+Math.min(30,r.width/2),r.top+r.height/2,r.top>=0&&r.bottom<=innerHeight]}",i)
    if not r[2]: pg.evaluate("i=>document.querySelector(`#charList .char[data-id=\"${i}\"]`).click()",i)
    else: pg.mouse.click(r[0],r[1])
def tabclick(pg,t):
    pg.click(f'#tabs [data-tab="{t}"]'); return pg.evaluate("scrollY")   # 클릭 바로 뒤 = 이미 0 (애니메이션 없음)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(vp):
        ctx=b.new_context(viewport=vp,locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return ctx,pg
    ctx,pg=mk({'width':1400,'height':600})
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week")
    wkm=lambda k: pg.evaluate("([w,k])=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7*k+1);return t.toISOString().slice(0,10)}",[wk,k])
    E_=lambda d:{'enabled':True,'diff':d,'party':1}
    CH=[{'id':f'c{i}','name':f'테스트{i}','level':280+i,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':E_('hard'),'will':E_('hard'),'dusk':E_('chaos'),'dunkel':E_('hard'),'jinhilla':E_('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i in range(1,4)]
    HI=[{'week':wkm(k),'total':(10+k)*100000000,'crys':(8+k)*100000000,'isale':0,'cleared':30,'perChar':[]} for k in range(8,0,-1)]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':HI,'monthHistory':[],'characters':CH,'startWeek':wkm(8),'settings':{'accounts':[]}}
    pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
    pg.add_style_tag(content=SMOOTH)
    seq=['total','loot','guild','live','boss']; res=[]
    for t in seq:
        y0=down(pg); y1=tabclick(pg,t); pg.wait_for_timeout(300); res.append((t,y0,y1,pg.evaluate("scrollY")))
    check('실제: 탭 바꿀 때마다 맨 위로 (스크롤 smooth CSS 있어도 바로 0)', all(r[1]>0 and r[2]==0 and r[3]==0 for r in res if r[0]!='live') and all(r[3]==0 for r in res), res)
    # 탭 안 스크롤 칸(.rcol 등): 보스 탭 오른쪽 칸 내리고 → 다른 탭 → 보스 = 0
    pg.evaluate("(()=>{const r=document.querySelector('#view .rcol');if(r){r.style.maxHeight='120px';r.style.height='120px';r.scrollTop=60;}})()")
    r0=pg.evaluate("document.querySelector('#view .rcol')?.scrollTop"); tabclick(pg,'total'); pg.wait_for_timeout(200)
    inner=pg.evaluate("[...document.querySelectorAll('#view *')].filter(e=>e.scrollTop>0).length")
    check('탭 안 스크롤 칸도 맨 위', inner==0, (r0,inner))
    # 다른 탭(수익 분석)에서 왼쪽 캐릭터 클릭 → 이번 주 보스 + 맨 위
    y0=down(pg); cclick(pg,'c2'); y1=pg.evaluate("scrollY"); pg.wait_for_timeout(300)
    st=pg.evaluate("[tab,S.activeId,scrollY]")
    check('다른 탭에서 캐릭터 클릭 → 이번 주 보스, 맨 위', y0>0 and y1==0 and st==['boss','c2',0], (y0,y1,st))
    # 보스 탭에서 캐릭터 클릭 = 스크롤 그대로 (b189)
    y0=down(pg); cclick(pg,'c3'); pg.wait_for_timeout(300); y1=pg.evaluate("scrollY")
    check('보스 탭에서 캐릭터 클릭 = 스크롤 그대로', y0>0 and abs(y1-y0)<2 and pg.evaluate("S.activeId")=='c3', (y0,y1))
    # 같은 탭 다시 그리기·동기화 render = 스크롤 그대로
    pg.click('#tabs [data-tab="total"]'); y0=down(pg); pg.evaluate("render(); renderTabView()"); pg.wait_for_timeout(300); y1=pg.evaluate("scrollY")
    check('다시 그리기(render) = 스크롤 그대로', y0>0 and abs(y1-y0)<2, (y0,y1))
    # 지금 탭 다시 누름 = 탭 안 바뀜 → 그대로
    y2=tabclick(pg,'total'); pg.wait_for_timeout(200)
    check('지금 탭 다시 누름 = 그대로(탭 바뀐 게 아님)', abs(pg.evaluate("scrollY")-y0)<2, (y0,y2))
    # b213: 이번 주 보스 — 누를 수 없는 칩 = 원래 색, 모멘텀 큐브 바로 다음 / 반지 상자 줄 = 숫자 칸 맞춤 + 리4·컨4 아이콘
    pg.evaluate("()=>{const c=S.characters.find(x=>x.id==='c3');c.bosses.lucid={enabled:true,diff:'hard',party:1};c.bosses.seren={enabled:true,diff:'hard',party:1};c.weekly={lucid:true,seren:true,will:true};c.drops={'seren|r_black':5,'lucid|r_life':2,'will|r_white':2};c.dropOut={'seren|r_black':['r4','x','x','c4','x'],'lucid|r_life':['gl','x'],'will|r_white':['c4','x']};S.activeId='c3';tab='boss';syncTabs();save();render()}"); pg.wait_for_timeout(500)
    d=pg.evaluate("""(()=>{const out=[];document.querySelectorAll('.drops').forEach(w=>{const ch=[...w.children];const off=ch.map((e,i)=>e.classList.contains('off')?i:-1).filter(i=>i>=0);if(!off.length)return;
      const lastInfo=Math.max(-1,...ch.map((e,i)=>e.classList.contains('erda')&&!e.classList.contains('off')?i:-1)), firstClick=ch.findIndex(e=>e.dataset.drop);
      out.push({ok:off[0]===lastInfo+1&&off.every((v,j)=>v===off[0]+j)&&(firstClick<0||firstClick>off[off.length-1]),memc:!!w.querySelector('.memc')});});
      const o=document.querySelector('.drop.off'),cs=getComputedStyle(o),im=o.querySelector('img'),mc=document.querySelector('.drop.memc').getBoundingClientRect(),ob=o.getBoundingClientRect();
      return {rows:out,op:cs.opacity,f:cs.filter,imf:im?getComputedStyle(im).filter+'|'+getComputedStyle(im).opacity:'',cur:cs.cursor,txt:o.innerText.trim(),cnt:!!o.querySelector('.ecnt,.dn'),tip:o.dataset.tip||'',size:[Math.round(ob.width),Math.round(ob.height),Math.round(mc.width),Math.round(mc.height)],bs:cs.borderStyle,drop:o.dataset.drop||null}})()""")
    check('누를 수 없는 칩 = 모멘텀 큐브(정보 아이콘) 바로 다음, 누르는 칩보다 앞', d['rows'] and all(r['ok'] for r in d['rows']) and any(r['memc'] for r in d['rows']), d['rows'])
    check('누를 수 없는 칩 = 원래 색 + b214: 정보 아이콘처럼 아이콘만(이름·개수 없음), 같은 크기, 말풍선 = 이름, 클릭 없음', d['op']=='1' and d['f']=='none' and d['imf']=='none|1' and d['cur']=='default' and d['drop'] is None and d['txt']=='' and not d['cnt'] and d['tip'] and d['size'][:2]==d['size'][2:] and d['bs']=='dashed', d)
    o0=pg.locator('.drop.off').first; o0.scroll_into_view_if_needed(); before=pg.evaluate("JSON.stringify(S.characters)"); o0.hover(); pg.wait_for_timeout(300)
    tp=pg.evaluate("(()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?t.innerText:''})()"); o0.click(); pg.wait_for_timeout(300)
    check('b214: 누를 수 없는 아이콘 hover = 이름 말풍선, 클릭 = 아무 변화 없음', tp==d['tip'] and pg.evaluate("JSON.stringify(S.characters)")==before and pg.locator('.modal-bg.show').count()==0, (tp,d['tip']))
    r=pg.evaluate("""(()=>{const R=document.querySelector('.revpanel .rp-ring'),S_=document.querySelector('.revpanel .rp-sale .rpn'),o=R.querySelector('.rpouts');const ims=[...o.querySelectorAll('.rpo')].map(p=>[p.querySelector('img')?.src.match(/ring_\\w+|data:/)?.[0]||(p.querySelector('img')?'img':''),p.innerText.trim(),p.querySelector('img')?.getBoundingClientRect().height,parseFloat(getComputedStyle(p.querySelector('.tsmn')).fontSize)]);
      return {txt:R.innerText.replace(/\\s+/g,' '),right:[o.getBoundingClientRect().right,S_.getBoundingClientRect().right],fit:R.scrollWidth<=R.clientWidth+1,h:R.getBoundingClientRect().height,ims}})()""")
    ims=r['ims']; tips=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-ring .rpo')].map(e=>e.dataset.tip||'')"); r4=[x for x,t in zip(ims,tips) if t.startswith('리스트레인트')]; c4=[x for x,t in zip(ims,tips) if t.startswith('컨티뉴어스')]; gl=[x for x,t in zip(ims,tips) if t.startswith('생명의 연마석')]; other=[x for x in ims if x[1].startswith('꽝')]
    check('반지 상자 결과 = 위 줄 숫자처럼 오른쪽 끝 맞춤, 한 줄, 안 잘림', abs(r['right'][0]-r['right'][1])<1.5 and r['fit'] and r['h']<24, r)
    check('b214: 리4·컨4·연마석 = 아이콘 + xN(글자 없음, 말풍선 = 이름), 꽝 = 글자 꽝 xN', r4 and c4 and gl and all(x[0] and x[1]==('x1' if x is r4[0] or x is gl[0] else 'x2') and abs(x[2]-x[3])<1.5 for x in (r4[0],c4[0],gl[0])) and other and other[0][1]=='꽝 x5' and not other[0][0] and r['txt'].startswith('반지 상자 x9'), (ims,tips,r['txt']))
    fs=pg.evaluate("document.querySelector('.revpanel .rp-ring .rpouts').style.fontSize")
    check('b214: 네 가지 다 있어도 줄이지 않고 원래 크기', fs=='', fs)
    # 모바일
    pg.set_viewport_size({'width':390,'height':700}); pg.wait_for_timeout(400)
    y0=down(pg); y1=tabclick(pg,'loot'); pg.wait_for_timeout(300)
    check('390px: 탭 바꾸면 맨 위', y0>0 and y1==0 and pg.evaluate("scrollY")==0, (y0,y1))
    ctx.close()
    # 예시 화면(로그인 전)
    ctx,pg=mk({'width':1400,'height':600})
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500); pg.add_style_tag(content=SMOOTH)
    check('예시 화면 켜짐', pg.evaluate("!!document.querySelector('.demotop,.dmbanner')"))
    res=[]
    for t in ['total','loot','boss']:
        y0=down(pg); y1=tabclick(pg,t); pg.wait_for_timeout(300); res.append((t,y0,y1))
    check('예시: 탭 바꾸면 맨 위', all(r[1]>0 and r[2]==0 for r in res), res)
    ids=pg.evaluate("[...document.querySelectorAll('#charList .char[data-id]')].map(e=>e.dataset.id)")
    pg.click('#tabs [data-tab="loot"]'); y0=down(pg); cclick(pg,ids[1]); y1=pg.evaluate("scrollY"); pg.wait_for_timeout(300)
    check('예시: 다른 탭에서 캐릭터 클릭 → 이번 주 보스, 맨 위', y0>0 and y1==0 and pg.evaluate("tab")=='boss', (y0,y1))
    y0=down(pg); cclick(pg,ids[0]); pg.wait_for_timeout(300); y1=pg.evaluate("scrollY")
    check('예시: 보스 탭에서 캐릭터 클릭 = 스크롤 그대로', y0>0 and abs(y1-y0)<2, (y0,y1))
    ctx.close(); b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
