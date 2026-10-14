# b118: 득템왕·보스 득템왕 점수 (흑옥 0.1, 백옥 0.2, 생명 0.4, 아이템 1)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8907'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b118_{TAG}_{name}.png'))
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
    pg.evaluate("()=>{const c=S.characters[0];c.bosses={blackmage:{enabled:true,diff:'extreme',party:1},star:{enabled:true,diff:'normal',party:1},kaling:{enabled:true,diff:'normal',party:1},lucid:{enabled:true,diff:'hard',party:1},zakum:{enabled:true,diff:'chaos',party:1},dusk:{enabled:true,diff:'chaos',party:1}};c.weekly={star:true,kaling:true,lucid:true,zakum:true,dusk:true};c.monthly={blackmage:S.period.week};c.mdate={blackmage:'2026-10-08'};save();render()}"); pg.wait_for_timeout(400)
    if SHOT:
        try: pg.locator('.revpanel .rp-char').first.screenshot(path=os.path.join(SHOT,f'b118_{TAG}_bossorder.png'))
        except Exception as e: print('shot skip',str(e)[:80])
    if not NOCHK:
        ob=pg.evaluate("(()=>{const inv={};for(const k in BOSS_ICONS)inv[BOSS_ICONS[k]]=k;return [...document.querySelector('.revpanel .rp-char').querySelectorAll('.rp-boss img')].map(i=>inv[i.getAttribute('src')]||'?')})()")
        check('이번 주 수익 보스 아이콘 = 보스 드랍 표 순서, 검마 맨 오른쪽', ob==['zakum','lucid','dusk','kaling','star','blackmage'], ob)
    T=pg.evaluate("""()=>{ const P=ik=>ik; const T={chars:[
      {id:'c1',name:'테스트캐',week:0,month:0,items:{'lucid|r_black':3,'lucid|r_white':1,'lucid|r_life':1},outs:{'lucid|r_black':['r4','x','x'],'lucid|r_life':['gl']}},
      {id:'n:가',name:'가캐',week:0,month:0,items:{'lucid|whisper':1,'lucid|r_black':5},outs:{}},
      {id:'n:나',name:'나캐',week:0,month:0,items:{'lucid|g_faith':2},outs:{}},
      {id:'n:다',name:'다캐',week:0,month:0,items:{'lucid|r_white':1},outs:{}}],
      byBoss:{'lucid|하드':{slot:'lucid',dl:'하드',items:{r_black:7},cnt:7,sc:7},'kaling|노말':{slot:'kaling',dl:'노말',items:{oath:1},cnt:1,sc:10},'dusk|카오스':{slot:'dusk',dl:'카오스',items:{r_life:3,r_white:1},cnt:4,sc:14},'zakum|카오스':{slot:'zakum',dl:'카오스',items:{r_white:1},cnt:1,sc:2}}};
      const d=document.createElement('div'); d.id='b118box'; d.style.cssText='position:fixed;left:0;top:0;z-index:99999;width:1400px;background:#111;padding:8px'; d.innerHTML=kingHtml(T,'loot')+bossLootKingHtml(T); document.body.appendChild(d);
      return {sc:typeof lootSc10==='undefined'?[]:[lootSc10({'a|r_black':3},{},()=>true),lootSc10({'a|r_black':1,'a|r_white':1,'a|r_life':1,'a|oath':2},{},()=>true)].map(fmtSc)} }""")
    pg.wait_for_timeout(300); shot(pg.locator('#b118box'),'kings')
    if not NOCHK:
        check('점수 소수 오차 없음 (0.3점 / 2.7점)', T['sc']==['0.3점','2.7점'], T)
        sub=pg.evaluate("[...document.querySelectorAll('#b118box .kingsub')].map(e=>e.textContent)")
        check('제목 밑 설명 2곳', sub==['(흑옥 0.1점, 백옥 0.2점, 생명 0.4점, 아이템 1점)']*2, sub)
        lk=pg.evaluate("[...document.querySelectorAll('#b118box #lootKing tbody tr')].map(r=>[r.querySelector('.rknm b').textContent,r.querySelector('.sc').textContent,r.querySelector('.sc').className])")
        gl=pg.evaluate("[...document.querySelectorAll('#b118box #lootKing tbody tr')].map(r=>[r.querySelector('.rknm b').textContent,[...r.querySelectorAll('.loot .ln')].map(e=>e.textContent.trim())])")
        t1=[x for x in gl if x[0]=='테스트캐'][0][1]
        check('b122 득템왕: 생명 상자에서 나온 생명의 연마석은 칸 없음, 생명 상자는 있음', '생명의 연마석' not in t1 and '생명의 보스 반지 상자' in t1, t1)
        hh=pg.evaluate("[...document.querySelectorAll('#b118box thead tr')].map(r=>[...r.children].map(e=>e.textContent))")
        check('점수 열: 캐릭터/보스 바로 옆, 득템 횟수 열 없음', hh==[['순위','캐릭터','점수','누적 획득 아이템'],['순위','보스','점수','득템 목록']], hh)
        nm=pg.evaluate("[...document.querySelectorAll('#b118box .rkname')].map(e=>e.textContent)")
        check('이름 옆 (N점)·(N회) 없음', not any('점)' in x or '회)' in x for x in nm), nm)
        check('득템왕 점수순 (b120 반상 포함: 나 2, 테스트 1.9 = 상자 0.9 + 리4 1 (b122: 생명 상자 연마석은 0점), 가 1.5, 다 0.2)', [x[0] for x in lk]==['나캐','테스트캐','가캐','다캐'] and [x[1] for x in lk]==['2점','1.9점','1.5점','0.2점'], lk)
        col=pg.evaluate("[...document.querySelectorAll('#b118box .sc')].map(e=>getComputedStyle(e).color)")
        check('점수 색 금·은·동·흰', col[:4]==['rgb(255, 213, 74)','rgb(217, 222, 230)','rgb(217, 146, 90)','rgb(255, 255, 255)'], col)
        bk=pg.evaluate("[...document.querySelectorAll('#b118box #bossLootKing tbody tr')].map(r=>[r.querySelector('.bdn').textContent,r.querySelector('.sc').textContent])")
        check('보스 득템왕 점수순 (더스크 1.4, 카링 1, 루시드 0.7, 자쿰 0.2)', [x[1] for x in bk]==['1.4점','1점','0.7점','0.2점'], bk)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
