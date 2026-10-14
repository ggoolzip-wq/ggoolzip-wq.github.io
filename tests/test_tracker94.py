# b126: 이번 주 수익 아이템 줄 — 보스 이름 앞 bossPic (주보 게이지 밑 아이콘과 같은 크기)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8911'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b126')}_{TAG}"+f'_{name}.png'))
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
    pg.evaluate("()=>{const c=S.characters[0];c.bosses.seren={enabled:true,diff:'hard',party:1};c.weekly.seren=true;c.drops['seren|r_black']=3;c.drops['seren|r_white']=3;c.drops['lucid|r_life']=1;c.outcomes=c.outcomes||{};save();render()}"); pg.wait_for_timeout(300)
    pg.evaluate("()=>{const c=S.characters[0];c.dropOut={'seren|r_black':['r4','x','x'],'seren|r_white':['c4','gl']};c.drev['seren|r_black']={m:100000000,a:1,p:1,i:'ring:r4'};c.drev['seren|r_white']={m:250000000,a:2.5,p:1,i:'ring:c4'};save();render()}"); pg.wait_for_timeout(300)
    pg.set_viewport_size({'width':1600,'height':2400}); pg.wait_for_timeout(300)
    shot(pg.locator('.revpanel'),'revpanel')
    shot(pg.locator('.revpanel .rp-items').first,'rp_items')
    if not NOCHK:
        R=pg.evaluate("""(()=>{const box=e=>{const r=e.getBoundingClientRect();return [Math.round(r.width),Math.round(r.height)]};
          const g=document.querySelector('.revpanel .rp-boss .bpic'), gb=g&&g.querySelector('.dbadge');
          const L=[...document.querySelectorAll('.revpanel .rp-items .dl:not(.dli)')].map(d=>{const b=d.querySelector('.dlb'),p=b&&b.querySelector('.bpic'),i=p&&p.querySelector('img.bicon'),bd=p&&p.querySelector('.dbadge');
            return {t:b?b.innerText.trim():'',pic:!!p,first:!!b&&b.firstElementChild===p,src:i?i.getAttribute('src'):null,sz:i?box(i):null,bd:bd?box(bd):null,d:bd?bd.className:''}});
          return {gauge:g?box(g.querySelector('.bicon')):null,gb:gb?box(gb):null,L,icons:Object.fromEntries(['lucid','kaling','seren'].map(k=>[k,BOSS_ICONS[k]]))}})()""")
        L=R['L']
        check('모든 아이템 줄에 보스 아이콘이 이름 앞에', len(L)>=3 and all(x['pic'] and x['first'] for x in L), L)
        check('주보 게이지 밑 아이콘과 같은 크기 (아이콘·배지)', R['gauge'] and all(x['sz']==R['gauge'] and x['bd']==R['gb'] for x in L), (R['gauge'],R['gb'],[(x['sz'],x['bd']) for x in L]))
        okSrc=all(any(x['src']==v for v in R['icons'].values()) for x in L if x['t'].startswith(('루시드','카링','선택받은')))
        check('bossIcon() 의 v4 아이콘 사용 + 난이도 배지', okSrc and all('db-' in x['d'] for x in L), [(x['t'],x['d']) for x in L])
    if not NOCHK:
        ov=pg.evaluate("""(()=>{const bad=[];const R=e=>e.getBoundingClientRect();
          const pics=[...document.querySelectorAll('.revpanel .rp-items .bpic')];
          const others=[...document.querySelectorAll('.revpanel .rp-items .dlrev, .revpanel .rp-items .dlt, .revpanel .rp-items .dlb')];
          for(const p of pics){ for(const part of [p.querySelector('.bicon'),p.querySelector('.dbadge')]){ if(!part) continue; const a=R(part);
            for(const o of others){ if(o.contains(p)||o.closest('.dl')===p.closest('.dl')&&!o.classList.contains('dlrev')) continue; const b=R(o);
              if(a.left<b.right-1&&a.right>b.left+1&&a.top<b.bottom-1&&a.bottom>b.top+1) bad.push([part.className,o.className,o.innerText.slice(0,20)]); } } }
          return bad})()""")
        check('b128 보스 아이콘·배지가 아래 금액 줄·다른 줄과 안 겹침', not ov, ov[:5])
    if not NOCHK:
        G=pg.evaluate("""[...document.querySelectorAll('.revpanel .rp-items .dl.dlg')].map(g=>{const R=e=>e.getBoundingClientRect();const it=[...g.querySelectorAll('.dli')],rv=g.querySelector(':scope>.dlcol>.dlrev');const last=it[it.length-1];
          return {b:g.querySelector('.dlb').innerText.replace(/\\s+/g,' ').trim(),n:it.length,pics:g.querySelectorAll('.bpic').length,stack:it.every((e,i)=>!i||R(e).top>=R(it[i-1]).bottom-1)&&it.every(e=>Math.abs(R(e).left-R(it[0]).left)<1),
            rev:rv?rv.innerText:'',under:rv?(R(rv).top>=R(last).bottom-1&&Math.abs(R(rv).left-R(last).left)<4):null,revLast:rv?g.querySelector('.dlcol').lastElementChild===rv:null}})""")
        names=[x['b'] for x in G]
        check('b131 같은 보스·난이도는 1묶음 (보스 아이콘 1번)', len(names)==len(set(names)) and all(x['pics']==1 for x in G), G)
        lu=[x for x in G if x['b'].startswith('루시드')]; se=[x for x in G if x['b'].startswith('선택받은')]
        check('b131 루시드 3개·세렌 2개 아이템이 세로로', lu and lu[0]['n']==3 and se and se[0]['n']==2 and all(x['stack'] for x in G), G)
        check('b131 합친 금액 1번, 마지막 아이템 바로 밑 (세렌 1억+2.5억=3.5억)', se[0]['rev'].startswith('3억 5,000만') and se[0]['under'] and se[0]['revLast'] and all(x['under'] in (None,True) for x in G), G)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
