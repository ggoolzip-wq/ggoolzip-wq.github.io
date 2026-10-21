import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8994=_tutil.free_port()
# b229: 득템 분석 — '주별 득템 캐릭터 정리' 새 표(판매 수익과 득템왕 사이, 한 쪽 = 한 주, 최신 주 기본) · 득템왕 제목 = 1위 초상화 · 판매 수익 제목 = 금액 1위 아이템 · 실제 + 예시
import os, sys, time, subprocess, urllib.request, json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8994)
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
INFO="""()=>{const q=s=>document.querySelector(s), wl=q('#weekLoot'); if(!wl) return null; const R=wl.getBoundingClientRect();
 return {order:[...document.querySelectorAll('#view .grid>.card')].map(c=>c.id).slice(1,4), now:wl.querySelector('.wlnow')?.textContent,
  rows:[...wl.querySelectorAll('.wlpage.on .wlrow')].map(r=>r.innerText.replace(/\\s+/g,' ').trim()), empty:wl.querySelector('.wlpage.on .wlempty')?.textContent||null,
  pages:wl.querySelectorAll('.wlpage').length, h:Math.round(R.height), ico:wl.querySelector('h2 .wlico img')?.getAttribute('src')||'',
  wrap:[...wl.querySelectorAll('.wlb b,.loot,.wlnow')].filter(e=>e.getClientRects().length>1||e.scrollWidth>e.clientWidth+0.5).length,
  out:[...wl.querySelectorAll('*')].filter(e=>e.getClientRects().length&&e.getBoundingClientRect().right>R.right+0.5).length,
  older:wl.querySelector('[data-wlpg="1"]')?.disabled, newer:wl.querySelector('[data-wlpg="-1"]')?.disabled,
  lk:!!q('#lootKing h2 .avatar'), lkName:q('#lootKing h2 .avatar')?.textContent||'', sIco:q('#salesCard h2 img')?.getAttribute('src')||''}; }"""
def ico(pg,k): return pg.evaluate("k=>{const d=document.createElement('div'); d.innerHTML=lootIco(k); return d.querySelector('img')?.getAttribute('src')||''}",k)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    def mk(w):
        ctx=b.new_context(viewport={'width':w,'height':1000},locale='ko-KR'); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); return ctx,pg
    ctx,pg=mk(1600); pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    E=lambda d:{'enabled':True,'diff':d,'party':1}
    BS={'lotus':E('hard'),'seren':E('hard'),'limbo':E('normal'),'blackmage':E('hard')}
    ch=[{'id':f'c{i}','name':n,'level':285,'job':'히어로','world':'스카니아','image':'','bosses':dict(BS),'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,n in [(1,'원모본캐'),(2,'원모부캐'),(3,'빈손캐릭')]]
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':ch,'settings':{'accounts':[]},'startWeek':'2026-10-01'}
    pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",[ST]); pg.reload(); pg.wait_for_timeout(1000)
    pg.evaluate("""()=>{ const wk=S.period.week; const P=(id,name,items,outcomes,revs)=>({id,name,meso:1e9,count:1,bosses:['스우(하드)'],bvals:[1e9],items,outcomes,...(revs?{revs}:{})});
      S.startWeek='2026-10-01';
      S.history=[{week:'2026-10-01',weeklyOnly:true,total:2e9,cleared:2,perChar:[P('c1','원모본캐',{'lotus|eye':1,'seren|r_white':2},{'seren|r_white':['c4','x']}),P('c2','원모부캐',{'limbo|r_life':1},{'limbo|r_life':['gl']})]},
                 {week:'2026-10-08',weeklyOnly:true,total:2e9,cleared:2,perChar:[P('c1','원모본캐',{'seren|chaosbox':1,'lotus|r_black':3},{'seren|chaosbox':['cb:eye'],'lotus|r_black':['x','x','x']},{'seren|chaosbox':{m:5e9,a:50,p:1,i:'cb:eye'}}),P('c3','빈손캐릭',{'lotus|r_black':1},{'lotus|r_black':['x']})]}];
      const c=S.characters[0]; c.weekly={limbo:true}; c.drops={'limbo|r_life':1,'limbo|se3':2}; c.dropOut={'limbo|r_life':['r4']}; c.drev={'limbo|r_life':{m:1.5e9,a:15,p:1,i:'ring:r4'}};
      c.monthly={blackmage:wk}; c.mdrops={'blackmage|genesis':1};
      const d=S.characters[1]; d.weekly={lotus:true}; d.drops={'lotus|eye':1}; save(); }""")
    pg.click('[data-tab=loot]'); pg.wait_for_timeout(700)
    I=pg.evaluate(INFO)
    check('실제: 표 순서 = 판매 수익 → 주별 득템 → 득템왕', I and I['order']==['salesCard','weekLoot','lootKing'], I and I['order'])
    check('실제: 최신 주 기본 + 라벨(날짜 · N주차 (이번 주))', I['now'].endswith('3주차 (이번 주)') and ' ~ ' in I['now'] and I['newer'] and not I['older'] and I['pages']==3, (I['now'],I['pages']))
    check('실제 이번 주: 검마(이번 주) 창세 + 반지 결과 리4 + 에테르 x2, 부캐 안대 / 빈손 캐릭 없음', len(I['rows'])==2 and all(x in I['rows'][0] for x in ['원모본캐','창세의 뱃지 x1','리스트레인트 링 4레벨 x1','소울 에테르 x2']) and '생명의 보스 반지 상자' not in I['rows'][0] and '원모부캐' in I['rows'][1] and '마력이 깃든 안대 x1' in I['rows'][1], I['rows'])
    check('실제: 제목 아이콘 = 이번 주 가장 많이 얻은 아이템(에테르 x2)', I['ico'] and I['ico']==ico(pg,'se3'), I['ico'][-30:])
    check('득템왕 제목 = 1위 캐릭터 초상화', I['lk'] and I['lkName']=='원', I['lkName'])
    check('판매 수익 제목 = 금액 1위(안대 50억 > 리4 15억)', I['sIco']==ico(pg,'eye'), I['sIco'][-30:])
    h0=I['h']; sy=pg.evaluate('scrollY')
    pg.click('#weekLoot [data-wlpg="1"]'); pg.wait_for_timeout(150); I=pg.evaluate(INFO)
    check('2쪽 = 지난 주: 칠흑 상자 고른 안대, 꽝 상자·꽝만 얻은 캐릭터 없음', I['now'].startswith('10/8 ~ 10/14') and len(I['rows'])==1 and '원모본캐' in I['rows'][0] and '빈손캐릭' not in ' '.join(I['rows']) and '흑옥' not in I['rows'][0] and not I['newer'], (I['now'],I['rows']))
    check('쪽 넘겨도 표 높이·스크롤 그대로', I['h']==h0 and pg.evaluate('scrollY')==sy, (h0,I['h']))
    pg.click('#weekLoot [data-wlpg="1"]'); pg.wait_for_timeout(150); I=pg.evaluate(INFO)
    check('3쪽: 컨4·생명의 연마석(꽝 제외), 제목 아이콘 바뀜, 더 지난 주 없음', I['now'].startswith('10/1 ~ 10/7') and '컨티뉴어스 링 4레벨 x1' in I['rows'][0] and '생명의 연마석 x1' in I['rows'][1] and I['older'] and I['ico']==ico(pg,'eye'), (I['rows'],I['ico'][-20:]))
    for w in (1280,390):
        pg.set_viewport_size({'width':w,'height':900}); pg.wait_for_timeout(250); I=pg.evaluate(INFO)
        check(f'실제 {w}: 줄바꿈·잘림·넘침 없음', I['wrap']==0 and I['out']==0, (I['wrap'],I['out']))
    pg.evaluate("()=>{S.history=[{week:'2026-10-08',weeklyOnly:true,total:0,cleared:0,perChar:[]}];S.characters.forEach(c=>{c.drops={};c.mdrops={};c.drev={};});WL_PAGE=0;render()}"); pg.wait_for_timeout(300)
    pg.click('#weekLoot [data-wlpg="1"]'); pg.wait_for_timeout(150); I=pg.evaluate(INFO)
    check('빈 주 = 짧은 안내', I['empty']=='이 주에 얻은 아이템이 없어요.' and not I['rows'], I['empty'])
    ctx.close()
    for w in (1600,390):
        ctx,pg=mk(w); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1300)
        pg.click('[data-tab=loot]'); pg.wait_for_timeout(700); I=pg.evaluate(INFO)
        check(f'예시 {w}: 새 표·순서·여러 주·이번 주 줄 있음', I and I['order']==['salesCard','weekLoot','lootKing'] and I['pages']>=3 and len(I['rows'])>=1 and I['lk'], I)
        check(f'예시 {w}: 줄바꿈·잘림·넘침 없음', I['wrap']==0 and I['out']==0, (I['wrap'],I['out']))
        n0=I['now']; pg.click('#weekLoot [data-wlpg="1"]'); pg.wait_for_timeout(150); I2=pg.evaluate(INFO)
        check(f'예시 {w}: 쪽 넘기기 동작(예시 화면에서 막히지 않음)', I2['now']!=n0 and I2['h']==I['h'] and (I2['rows'] or I2['empty']), (n0,I2['now']))
        ctx.close()
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); fails.append('exception')
finally:
    srv.kill()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
