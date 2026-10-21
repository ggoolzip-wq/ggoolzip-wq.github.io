import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8985=_tutil.free_port()
# b206 (원래 b187 틀): 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8985)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b206')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)

try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1400},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week")
    wkm=lambda k: pg.evaluate("([w,k])=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7*k+1);return t.toISOString().slice(0,10)}",[wk,k])
    E=lambda d:{'enabled':True,'diff':d,'party':1}
    BS={'lucid':E('hard'),'will':E('hard'),'dusk':E('chaos'),'blackmage':E('hard')}
    C1={'id':'c1','name':'캐릭A','level':280,'job':'히어로','world':'스카니아','image':'','bosses':BS,'weekly':{'lucid':True},'monthly':{},'auto':{},'drops':{},'sync':{}}
    C2={'id':'c2','name':'캐릭B','level':270,'job':'비숍','world':'스카니아','image':'','bosses':dict(BS),'weekly':{'lucid':True,'will':True,'dusk':True},'monthly':{'blackmage':wk},'auto':{},'drops':{},'sync':{}}
    C3={'id':'c3','name':'숨김캐','level':270,'job':'비숍','world':'스카니아','image':'','accId':'a9','bosses':dict(BS),'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    H=[{'week':wkm(k),'total':(3+k)*100000000,'crys':(3+k)*80000000,'isale':(3+k)*20000000,'cleared':3,'perChar':[]} for k in (3,2,1)]
    MW=[{'week':wkm(k),'date':wkm(k),'meso':k*150000000,'n':k,'list':[{'name':'캐릭A','n':k,'meso':k*150000000}]} for k in (3,2,1)]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':H,'monthHistory':[],'missW':MW,'missM':MW[:2],'characters':[C1,C2,C3],'startWeek':wkm(3),'period':pg.evaluate("({...S.period})"),'settings':{'accounts':[{'id':'a9','label':'키없음','key':''}]}}
    def go(t):
        pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab',t)}",[ST,t]); pg.reload(); pg.wait_for_timeout(1000)
        pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()"); pg.wait_for_timeout(600)
    # 4: 수익을 기록할까요? — 가격 확인 / 출처 링크
    go('boss')
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify({whisper:{p:55500000000,t:Date.parse('2026-10-17T09:30:00Z')},genesis:{p:18299000000,t:Date.parse('2026-10-17T09:30:00Z')}}))}")
    pg.evaluate("askRev(S.characters[0],findBoss('lucid'),'lucid|whisper','whisper',()=>{})"); pg.wait_for_timeout(250)
    r=pg.evaluate("""(()=>{const m=document.querySelector('#revModal'),g=m.querySelector('#rvGuide').innerText,s=m.querySelector('.rvsrc'),a=s&&s.querySelector('a');return {g,s:s&&s.innerText,href:a&&a.href,tg:a&&a.target,rel:a&&a.rel,old:m.innerText.includes('최저가 측정')}})()""")
    check('수익을 기록할까요? 가격 확인 : 날짜 + 출처 : 링크(새 탭)', r['g'].startswith('가격 확인 : 2026-10-17 18:30') and r['s'] and r['s'].startswith('출처 : ') and r['href']=='https://maple.ai.kr/blog/item-price-tracker-2026' and r['tg']=='_blank' and 'noopener' in r['rel'] and not r['old'], r)
    shot(pg.locator('#revModal .modal'),'rev_dialog')
    pg.evaluate("document.querySelector('#revModal')?.remove()")
    # 3: 아이템 가격 표 (로그인 상태)
    pg.evaluate("()=>{pcKind='item';repaintPrices();}"); pg.wait_for_timeout(200)
    r=pg.evaluate("""(()=>{const c=document.querySelector('.rcol .pricecard');const d=[...c.querySelectorAll('.pc-date')].map(x=>x.innerText.trim());const a=c.querySelector('.pc-src a');
      const rows=[...c.querySelectorAll('.pc-date,.pc-src')].every(x=>x.scrollWidth<=x.clientWidth+1&&x.getBoundingClientRect().height<24);
      return {d,href:a&&a.href,tg:a&&a.target,fam:a&&getComputedStyle(c.querySelector('.pc-src')).fontFamily.split(',')[0],nowrap:rows}})()""")
    check('아이템 가격 표: 가격 확인 : 날짜, 아래 출처 : 링크(새 탭), 한 줄', r['d'][0].startswith('가격 확인 : 2026-10-17') and r['d'][1].startswith('출처 : ') and r['href']=='https://maple.ai.kr/blog/item-price-tracker-2026' and r['tg']=='_blank' and r['nowrap'], r)
    shot(pg.locator('.rcol .pricecard'),'item_price')
    pg.evaluate("()=>{pcKind='cry';repaintPrices();}")
    # 1: 체크한 아이템 없음 → 확인 하나
    pg.evaluate("()=>{S.activeId='c1';render();}"); pg.wait_for_timeout(200)
    before=pg.evaluate("JSON.stringify(S)")
    pg.evaluate("openRevAll()"); pg.wait_for_timeout(250)
    r=pg.evaluate("[...document.querySelectorAll('#revAllModal .rabtns button')].map(b=>b.innerText.trim())")
    check('전체 수정 창: 체크한 아이템 없음 → [확인] 버튼 하나', r==['확인'], r)
    shot(pg.locator('#revAllModal .modal'),'revall_empty')
    pg.click('#revAllModal [data-rab]'); pg.wait_for_timeout(200)
    check('[확인] = 닫기만, 아무 변화 없음', pg.locator('#revAllModal').count()==0 and pg.evaluate("JSON.stringify(S)")==before)
    # 체크한 아이템 있으면 그대로
    pg.evaluate("()=>{const c=S.characters[0];c.drops={'lucid|whisper':1};render();}"); pg.wait_for_timeout(150)
    pg.evaluate("openRevAll()"); pg.wait_for_timeout(200)
    r=pg.evaluate("[...document.querySelectorAll('#revAllModal .rabtns button')].map(b=>b.innerText.trim())")
    check('체크한 아이템 있으면 [전체 수정][취소] 그대로', r==['전체 수정','취소'], r)
    pg.evaluate("document.querySelector('#revAllModal')?.remove()")
    # 2: 다른 탭에서 왼쪽 캐릭터 클릭 → 이번 주 보스 탭 + 그 캐릭터
    for t in ('total','loot','guild','live'):
        pg.locator(f'#tabs [data-tab={t}]').click(); pg.wait_for_timeout(300)
        tgt='c2' if pg.evaluate("S.activeId")=='c1' else 'c1'
        pg.locator(f'#charList .char[data-id={tgt}]').click(); pg.wait_for_timeout(350)
        r=pg.evaluate("[tab,S.activeId,localStorage.getItem('mapleBossTracker.tab'),document.querySelector('#tabs [data-tab=boss]').classList.contains('on'),!!document.querySelector('#view .bosslay .boss-list'),document.querySelector('#view .bosslay h2')?.innerText||'']")
        check(f'{t} 탭에서 캐릭터 클릭 → 이번 주 보스 탭·그 캐릭터 보스 목록', r[0]=='boss' and r[1]==tgt and r[2]=='boss' and r[3] and r[4] and ('캐릭A' if tgt=='c1' else '캐릭B') in r[5], r)
        if t=='loot':
            pg.wait_for_timeout(600); shot(pg.locator('body'),'char_from_loot')
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
