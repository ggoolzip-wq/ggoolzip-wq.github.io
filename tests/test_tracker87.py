# b115: t51 9건 — 연마석 순서·그래프 말풍선·메소왕 말풍선·난이도 네모·주 목록 검마·날파리·고화질 초상화+테두리·호출 한도 해제·이번 주 수익 보스 아이콘
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8903'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b115_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'blackmage':B('extreme'),'zakum':B('chaos')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
   'drops':{'lucid|whisper':1,'lucid|g_faith':1,'kaling|oath':1},'drev':{'lucid|whisper':{'m':500000000,'a':5,'p':1,'i':'whisper'},'kaling|oath':{'m':900000000,'a':9,'p':1,'i':'oath'}}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
SRV={'prices':{'whisper':{'p':6200000000,'t':1760000000000},'h_face':{'p':6199000000,'t':1760000000000}},'puts':[],'pub':0,'nx':[]}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR')
    H={'Access-Control-Allow-Origin':'*'}
    def api(r):
        u=r.request.url
        if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'admin':True,'user':'u0','accounts':[]}))
        if u.endswith('/api/prices'): SRV['pub']+=1; return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/prices' in u:
            if r.request.method=='PUT': d=json.loads(r.request.post_data)['prices']; SRV['puts'].append(d); SRV['prices'].update(d)
            return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'users':[]}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body='{}')
    def nxapi(r):  # /maplestory/v1/id: 첫 호출 429(초당), 두 번째 200
        SRV['nx'].append(time.time())
        if 'tst429' in r.request.url and len([1 for _ in SRV['nx']])==1: return r.fulfill(status=429,content_type='application/json',headers=H,body=json.dumps({'error':{'name':'OPENAPI00007','message':'rate'}}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'ocid':'x1'}))
    ctx.route('http://127.0.0.1:9998/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else nxapi(r) if 'tst429' in r.request.url else r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9998');localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}")
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';const c=S.characters[0];c.bosses.blackmage={enabled:true,diff:'extreme',party:1};c.monthly={blackmage:S.period.week};c.mdate={blackmage:'2026-10-08'};c.mdrops={'blackmage|genesis':1};c.mdrev={'blackmage|genesis':{m:3000000000,a:30,p:1,i:'genesis'}};save();render()}",ST); pg.wait_for_timeout(400)
    shot(pg.locator('.revpanel'),'revpanel'); shot(pg.locator('.pricecard'),'pricecard'); shot(pg.locator('.boss').first,'bossrow')
    pg.evaluate("openRevAll()"); pg.wait_for_timeout(300); shot(pg.locator('#revAllModal .modal'),'revall'); pg.evaluate("document.querySelector('#revAllModal')?.remove()")
    if not NOCHK:
        ord_=pg.evaluate("revItems().map(priceId)"); fi,li=ord_.index('g_faith'),ord_.index('g_life')
        check('1 신념의 연마석 = 생명의 연마석 바로 위', li==fi+1, ord_)
        rb=pg.eval_on_selector_all('.revpanel .rp-boss .bpic',"e=>e.map(x=>[x.querySelector('img')?.getAttribute('src')===BOSS_ICONS[BOSSES.find(b=>x.innerHTML.includes(BOSS_ICONS[b.id]))?.id],x.querySelector('.dbadge')?.dataset.d,x.classList.contains('bfr')])")
        check('9 이번 주 수익: 잡은 보스 아이콘 + 난이도, 테두리 없음', len(rb)==3 and sorted(x[1] for x in rb)==['EX','H','N'] and not any(x[2] for x in rb), rb)
        h=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-boss')].map(e=>e.getBoundingClientRect().height)")
        pg.evaluate("()=>{const c=JSON.parse(JSON.stringify(S.characters[0]));c.id='c2';c.name='둘째캐';c.weekly={lucid:true};c.monthly={};c.drev={};c.mdrev={};c.drops={};c.mdrops={};const c3=JSON.parse(JSON.stringify(c));c3.id='c3';c3.name='셋째';c3.weekly={};S.characters.unshift(c3,c);save();render()}"); pg.wait_for_timeout(300)
        rk=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-char')].map(e=>[e.querySelector('.rp-rk')?.textContent.trim(),e.querySelector('.rp-nm b, .rp-nm .spk, .rp-nm span')?.textContent,!!e.querySelector('.rkno.md-gold'),e.querySelector('.rp-top').getBoundingClientRect().height])")
        check('이번 주 수익: 수익 높은 순 + 순위(1위 메달), 0 = -', [x[0][-1:] for x in rk]==['1','2','-'] and rk[0][1]=='테스트캐' and rk[0][2] and all(x[3]<30 for x in rk), rk)
        shot(pg.locator('.revpanel'),'revpanel_rank')
        cl=pg.evaluate("[...document.querySelectorAll('.revpanel .rp-char')].map(e=>[...e.querySelectorAll('.rp-cl:not(.rp-left)')].map(x=>x.textContent.split(' ')[0]+' '+x.textContent.split(' ')[1]+'|'+!!x.querySelector('img,.ric,svg')))")
        check('결정석 줄: 주간/검마 (기록 있을 때만, 아이콘)', cl[0][:2]==['주간 결정석|true','검마 결정석|true'] and cl[1]==['주간 결정석|true'] and cl[2]==[], cl)
        check('월간 ✓ 없음', '월간 ✓' not in pg.inner_text('.revpanel'))
        check('9 아이콘 1줄', h and all(x<30 for x in h), h)
        pc=pg.evaluate("[...document.querySelectorAll('.pricecard .pc-row .bpic')].slice(0,3).map(x=>[x.classList.contains('bfr'),!!x.querySelector('.dbadge')])")
        check('9 결정석 가격표: 테두리 없음 + 난이도', pc and all((not a) and b for a,b in pc), pc)
        ra=pg.evaluate("[...document.querySelectorAll('.boss .bn .bpic')].map(x=>x.classList.contains('bfr')&&!!x.querySelector('.dbadge'))")
        check('4·7 보스 목록: 테두리 + 난이도', ra and all(ra), ra)
        nat=pg.evaluate("Promise.all(BOSSES.map(b=>new Promise(r=>{const i=new Image();i.onload=()=>r(i.naturalWidth);i.onerror=()=>r(0);i.src=BOSS_ICONS[b.id]}))).then(a=>Math.min(...a))")
        check('7 초상화 ≥100px (b116: 스케줄러 아이콘 최근접 4배)', nat>=100, nat)
        q=pg.evaluate("""async()=>{ const k=S.settings.accounts[0].key; try{await nxRaw('/maplestory/v1/id',{character_name:'tst429'},k);}catch(e){} quotaBump(k,true); const a=quotaOf(k).over; await nxRaw('/maplestory/v1/id',{character_name:'tst429'},k); render(); return [a,quotaOf(k).over,document.querySelector('.quota')?.textContent||''] }""")
        check('8 성공하면 호출 한도 도달 해제 → 남은 호출 표시', q[0] and not q[1] and '한도 도달' not in q[2], q)
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(500)
    if not NOCHK:
        tip=pg.evaluate("[...document.querySelectorAll('.linechart .lpt')].pop()?.dataset.tip||''")
        check('2 그래프 말풍선(b191 4줄): 주간 결정석/검마 결정석/아이템 판매', '\n주간 결정석 : ' in tip and '\n검마 결정석 : ' in tip and '\n아이템 판매 : ' in tip and '누적' not in tip and '44.00억' in tip.split('아이템 판매 : ')[1].split('\n')[0], tip)
        mw=pg.evaluate("(()=>{const T=totalData();const w=T.weeks[T.weeks.length-1];return [(w.total||0)+((monthlyByWeek(T)[w.week]||{}).meso||0), meso((w.total||0)+((monthlyByWeek(T)[w.week]||{}).meso||0))]})()")
        row=pg.evaluate("[...document.querySelectorAll('.card')].find(c=>c.querySelector('h2')?.textContent.includes('전체 주 목록'))?.querySelector('tbody tr td:nth-child(4)')?.textContent")
        check('5 전체 주 목록: 검마 결정석 + 검마 판매 포함', row==mw[1] and mw[0]>pg.evaluate("totalData().weeks.slice(-1)[0].total"), (row,mw))
    bk=pg.locator('#bossKing'); bk.scroll_into_view_if_needed()
    sale=pg.locator('#bossKing .bksale').first
    if sale.count():
        sale.hover(); pg.wait_for_timeout(400); shot(pg.locator('#tip, .tip, [class*=tip].show').first,'bosskingtip')
    shot(bk,'bossking')
    if not NOCHK:
        th=pg.evaluate("document.querySelector('#bossKing .bksale')?.dataset.tiphtml||''")
        check('3 메소왕 말풍선: 초상화+난이도 / 보스 이름 (난이도) / 아이템 몇 개, 얼마', 'dbadge' in th and 'bkt-h' in th and '개, ' in th and '(' in th, th[:200])
    pg.click('[data-tab="loot"]'); pg.wait_for_timeout(500); shot(pg.locator('#bossLootKing'),'lootking'); shot(pg.locator('#poopKing'),'poop')
    if not NOCHK:
        lk=pg.evaluate("[...document.querySelectorAll('#bossLootKing .rkico .bpic')].map(x=>x.classList.contains('bfr')&&!!x.querySelector('.dbadge'))")
        check('4·7 득템왕: 테두리 + 난이도', lk and all(lk), lk)
        bg=pg.evaluate("[...document.querySelectorAll('.bpic .dbadge')].filter(d=>d.getBoundingClientRect().width).map(d=>getComputedStyle(d).backgroundColor)")
        check('난이도 네모 색 보임(투명 아님)', bg and 'rgba(0, 0, 0, 0)' not in bg, bg[:6])
        fl=pg.evaluate("[...document.querySelectorAll('#poopKing tbody .poopav .fly')].map(f=>[f.getBoundingClientRect().width,parseFloat(getComputedStyle(f).animationDuration)])")
        check('6 날파리: 초상화 쪽 4마리·작게·빠르게', len(fl)>=4 and all(w<=8 and d<=1.85 for w,d in fl) and pg.evaluate("document.querySelectorAll('#poopKing .rknm .fly').length")==0, fl[:4])
    if not NOCHK:
        for tab in ('boss','total','loot'):
            pg.click(f'[data-tab="{tab}"]'); pg.wait_for_timeout(400)
            bad=pg.evaluate("""()=>{ const out=[]; document.querySelectorAll('.dbadge').forEach(d=>{ const r=d.getBoundingClientRect(); if(!r.width) return; const p=d.closest('.bpic,.rabi')||d.parentElement, q=p.getBoundingClientRect();
              if(false) { out.push('outside:'+(p.className||'')+':'+d.textContent+':'+Math.round(r.left-q.left)+','+Math.round(r.top-q.top)+','+Math.round(r.right-q.right)); return; }
              for(let e=d.parentElement;e&&e!==document.body;e=e.parentElement){ const cs=getComputedStyle(e); if(cs.overflowX==='hidden'||cs.overflowY==='hidden'||cs.overflowX==='clip'||cs.overflowY==='clip'){ const b=e.getBoundingClientRect(); if(r.left<b.left-0.5||r.top<b.top-0.5||r.right>b.right+0.5||r.bottom>b.bottom+0.5){ out.push((e.id||e.className)+''); break; } } } }); return out; }""")
            check(f'난이도 네모 전체 보임 ({tab})', not bad, bad[:5])
    if not NOCHK:
        pg.click('[data-tab="boss"]'); pg.wait_for_timeout(300); pg.evaluate("itemPricePut({whisper:{p:6200000000,t:Date.UTC(2026,9,14,5,30)}});repaintPriceCard()"); pg.click('.pricecard [data-pckind=item]'); pg.wait_for_timeout(300)
        dt=pg.evaluate("document.querySelector('.pricecard .pc-date')?.textContent")
        check('아이템 가격 탭 맨 아래: 가격 확인 날짜 (KST, 공용 시세 최신)', dt=='가격 확인 날짜 : 2026-10-14 14:30', dt)
        shot(pg.locator('.pricecard'),'pricecard_items')
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
