# b210: 로그인 전 = 위 탭(이번 주 보스·수익 분석·득템 분석·길드 현황)마다 예시 화면 (실시간 결정석·공용 시세로 계산, 저장·동기화·넥슨·서버 쓰기 없음)
#       + 작은 API 키 칸·예시 띠, 랜딩 소개·가격 카드 없음(숨김 SEO 글·푸터 NEXON 표기 유지), '이번 주 수익 총합' 제목, 로그인(캐릭터 0명) = 예전 빈 화면
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8979'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b210_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
H={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'}
PR={'prices':{'g_life':{'p':900000000,'t':1760000000000},'ring:r4':{'p':3600000000,'t':1760000000000},'ring:c4':{'p':2500000000,'t':1760000000000}}}
reqs=[]
def api(r):
    reqs.append((r.request.method,r.request.url))
    if r.request.method=='OPTIONS': return r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST'})
    if r.request.url.endswith('/api/prices'): return r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps(PR))
    return r.fulfill(status=401,headers=H,content_type='application/json',body='{"error":"no_session"}')
TXT='예시 화면입니다 · API키를 넣으면 내 캐릭터로 보여요'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR')
    nexon=[]; ctx.route('https://open.api.nexon.com/**',lambda r:(nexon.append(r.request.url),r.abort()))
    ctx.route('http://127.0.0.1:9996/**',api)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9996');localStorage.setItem('mapleBossTracker.tab','loot')"); pg.reload(); pg.wait_for_timeout(2500)
    r=pg.evaluate("""(()=>{const v=document.getElementById('view'),t=v.querySelector(':scope>.demotop'),k=t&&t.querySelector('.dmkey');return {tab, on:document.body.classList.contains('demo'), top:!!t, ban:t&&t.querySelector('.dmbanner').innerText.replace(/\\s+/g,' ').trim(),
      close:!!document.querySelector('[data-demo-close],.dmclose'), keyH:k&&k.getBoundingClientRect().height, keyTxt:k&&k.innerText, btn:!!(k&&k.querySelector('#importAccBtn')),
      seoland:!!v.querySelector('.seoland,.landprices,.landing'), entry:v.innerText.includes('예시 화면 둘러보기'), seo:!!document.getElementById('seoIntro')&&document.getElementById('seoIntro').innerText.includes('메보기'),
      foot:(document.querySelector('.foot')||{}).textContent, chars:document.querySelectorAll('#charList .char[data-id]').length, act:document.querySelector('#tabs [data-tab].on,#tabs [data-tab].active')?.dataset.tab}})()""")
    check('로그인 전 처음 = 이번 주 보스 예시(탭 켜짐, 저장된 탭 무시)', r['tab']=='boss' and r['on'] and r['top'] and r['chars']==4, r)
    check("예시 띠 문구 그대로 · '예시 닫기' 없음", r['ban'] and r['ban'].endswith(TXT) and not r['close'], r['ban'])
    check("작은 API 키 칸(한 줄, 네온 버튼, 'Data based on' 줄 없음)", r['btn'] and r['keyH']<64 and 'Data based' not in (r['keyTxt'] or ''), (r['keyH'],r['keyTxt']))
    check('랜딩 소개 카드·가격 카드·둘러보기 카드 없음 / 숨김 SEO 글 유지 / 푸터 NEXON 표기 유지', not r['seoland'] and not r['entry'] and r['seo'] and 'Data based on NEXON Open API' in (r['foot'] or ''), r)
    h=pg.evaluate("(()=>{const h=document.querySelector('.revpanel h2');return h&&{t:h.innerText.trim(),one:h.scrollWidth<=h.clientWidth+1&&h.getBoundingClientRect().height<34}})()")
    check("카드 제목 '이번 주 수익 총합' 한 줄", h and h['t'].endswith('이번 주 수익 총합') and h['one'], h)
    shot(pg.locator('.revpanel'),'demo_revpanel')
    # 값 = 실시간 가격으로 계산
    v=pg.evaluate("""(()=>{let o={}; demoRun(()=>{ o.bad=[]; for(const c of S.characters){ for(const [id,cfg] of Object.entries(c.bosses)){ const b=findBoss(id); if(price(b,cfg.diff)!==PRICE_CONFIG[priceKey(b,cfg.diff)]) o.bad.push(id); }
        for(const [k,x] of Object.entries(c.drev||{})){ const ip=itemPrices()[priceId(x.i)]; if(!ip||x.m!==Math.round(ip.p/x.p)) o.bad.push(k); } }
      for(const h of S.history) for(const pc of h.perChar) for(const [k,x] of Object.entries(pc.revs||{})){ const ip=itemPrices()[priceId(x.i)]; if(!ip||x.m!==Math.round(ip.p/x.p)) o.bad.push(k); }
      o.bm=S.characters.filter(c=>c.bosses.blackmage).map(c=>curParty(c,'blackmage')); o.hist=S.history.length; o.ids=S.characters.map(c=>c.id); },[]); o.realN=S.characters.length; return o;})()""")
    check('예시 결정석 = 지금 가격표 · 판매 = 공용 시세(/api/prices) ÷ 분배 · 검마 솔로', not v['bad'] and v['bm'] and all(x==1 for x in v['bm']) and v['hist']>=3 and v['realN']==0, v)
    PR['prices']['g_life']['p']=1200000000
    pg.evaluate("itemPriceLoad&&itemPriceLoad()"); pg.wait_for_timeout(2500)
    g=pg.evaluate("(()=>{let o=[]; demoRun(()=>{ for(const c of S.characters) for(const x of Object.values(c.drev||{})) if(x.i==='g_life') o.push(x.m*x.p); for(const h of S.history) for(const pc of h.perChar) for(const x of Object.values(pc.revs||{})) if(x.i==='g_life') o.push(x.m*x.p); },[]); return o;})()")
    check('시세가 바뀌면 예시도 새 시세로 다시 계산', g and all(abs(x-1200000000)<10 for x in g), g)
    for t,need in (('total','누적 수입'),('loot','누적 득템'),('guild','지하 수로')):
        pg.click(f'#tabs [data-tab={t}]'); pg.wait_for_timeout(900)
        s=pg.evaluate("(()=>({top:!!document.querySelector('#view>.demotop'),txt:document.getElementById('view').innerText}))()")
        check(f'{t} 탭 클릭 → 예시 화면', s['top'] and need in s['txt'] and TXT in s['txt'], s['txt'][:120])
    pg.click('#tabs [data-tab=live]'); pg.wait_for_timeout(700)
    s=pg.evaluate("({top:!!document.querySelector('#view>.demotop'),demo:document.body.classList.contains('demo'),chars:document.querySelectorAll('#charList .char[data-id]').length})")
    check('신창섭 라이브 = 예시 없음(그대로)', not s['top'] and not s['demo'] and s['chars']==0, s)
    pg.click('#tabs [data-tab=boss]'); pg.wait_for_timeout(700)
    # 예시 캐릭터 클릭 = 예시 안에서 바뀜, 체크 버튼 눌러도 아무 변화 없음
    pg.click('#charList .char[data-id=demo3]'); pg.wait_for_timeout(500)
    a=pg.evaluate("document.querySelector('#view .charinfo, #view .bosslay')?.innerText.includes('데모아크')")
    before=pg.evaluate("document.getElementById('view').innerText.length")
    for sel in ('.bossrow .chk, .brow input[type=checkbox], [data-check]','.dropchip, [data-drop]'):
        el=pg.query_selector(sel)
        if el:
            try: el.click(timeout=1500)
            except Exception: pass
    pg.wait_for_timeout(500)
    check('예시 캐릭터 클릭 = 예시 안에서 바뀜', a, a)
    pg.wait_for_timeout(1500)
    st=pg.evaluate("(()=>{const s=JSON.parse(localStorage.getItem('mapleBossTracker.v1')||'null');return {n:s?(s.characters||[]).length:0,demo:s?JSON.stringify(s).includes('예시히어로'):false}})()")
    w=[x for x in reqs if x[0] not in ('GET','OPTIONS')]
    check('예시는 저장 안 함 · 넥슨 호출 0 · 서버 쓰기 요청 0', st['n']==0 and not st['demo'] and not nexon and not w, (st,nexon[:2],w[:3]))
    pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(600)
    m=pg.evaluate("(()=>{const h=document.querySelector('.revpanel h2'),k=document.querySelector('#view .dmkey'),bn=document.querySelector('#view .dmbanner b');return {h:h.scrollWidth<=h.clientWidth+1&&h.getBoundingClientRect().height<34,k:k.scrollWidth<=k.clientWidth+1,bn:bn.scrollWidth<=bn.clientWidth+1&&bn.getBoundingClientRect().right<=innerWidth,over:document.documentElement.scrollWidth<=innerWidth+1}})()")
    check('휴대폰(390px): 제목·키 칸·예시 띠 안 잘림, 가로 넘침 없음', all(m.values()), m)
    ctx.close()
    # 로그인(서버 토큰 있음) + 캐릭터 0명 = 예전 빈 화면, 예시 없음
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    ctx.route('http://127.0.0.1:9996/**',lambda r:r.fulfill(status=200,headers=H,content_type='application/json',body='{}'))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:None)
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear();localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9996');localStorage.setItem('mapleBossTracker.svToken','t-test')"); pg.reload(); pg.wait_for_timeout(1500)
    s=pg.evaluate("({top:!!document.querySelector('#view>.demotop'),demo:document.body.classList.contains('demo'),empty:!!document.querySelector('#view .card.empty'),chars:document.querySelectorAll('#charList .char[data-id]').length})")
    check('로그인했는데 캐릭터 0명 = 예전 빈 화면(예시 없음)', not s['top'] and not s['demo'] and s['empty'] and s['chars']==0, s)
    ctx.close()
    # 로컬 테스트 데이터(실제 캐릭터) = 예시 없음, 카드 제목 바뀜
    ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(300)
    E=lambda d:{'enabled':True,'diff':d,'party':1}
    C={'id':'c1','name':'테스트캐','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':E('hard'),'will':E('hard'),'blackmage':E('hard')},'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    pg.evaluate("c=>{const s={...S,characters:[c],activeId:'c1'};localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','boss')}",C); pg.reload(); pg.wait_for_timeout(1200)
    s=pg.evaluate("({top:!!document.querySelector('#view>.demotop'),demo:document.body.classList.contains('demo'),h:document.querySelector('.revpanel h2')?.innerText.trim(),name:document.querySelector('#charList .char[data-id]')?.innerText})")
    check("내 캐릭터 있으면 예시 없음 · 제목 '이번 주 수익 총합'", not s['top'] and not s['demo'] and s['h'].endswith('이번 주 수익 총합') and '테스트캐' in s['name'], s)
    shot(pg.locator('.revpanel'),'local_revpanel')
    ctx.close(); b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
