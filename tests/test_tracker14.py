import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')  # 지정하면 tab_daily.png / tab_daily_hover.png / tab_guild.png 를 그 폴더에도 저장
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 일퀘 현황 · 길드 현황 탭 (스케줄러 / 길드 랭킹 모의 응답)
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil
sys.argv=[sys.argv[0]]
import mock_nexon
from mock_nexon import handle, KM, KA, CALLS, GUILD_EMPTY
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
IMG='https://open.api.nexon.com/static/maplestory/character/look/mock-'
def ch(id,name,lv,job,ocid,acc,main=False,img=''):
    return {'id':id,'name':name,'level':lv,'job':job,'world':'스카니아','ocid':ocid,'accId':acc,'isMain':main,'image':(IMG+img) if img else '',
            'bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main','a1',True,'main'),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1','a1',False,'alt1'),
                ch('c3','신궁짱',265,'신궁','ocid-alt2','a1',False,'alt2'),ch('c4','부계정비숍',268,'비숍','ocid-b1','a2',False,'b1'),
                ch('c5','수동캐릭',250,'아델','','',False)],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM},{'id':'a2','label':'부계정','key':KA}],'autoSync':True,'autoEnable':True,'lastSync':int(time.time()*1000)}}
sched_calls=lambda: [q.get('ocid') for p,q in CALLS if p.endswith('/scheduler/character-state')]
guild_calls=lambda: [(q.get('date'),q.get('ranking_type')) for p,q in CALLS if p.endswith('/ranking/guild')]
def wait_idle(pg): pg.wait_for_function("!dqBusy && !guildBusy && !syncing",timeout=20000); pg.wait_for_timeout(200)
CELLS="(id)=>[...document.querySelectorAll(`.dqc[data-dqchar=${id}] .dqi`)].map(e=>[e.dataset.dqi,[...e.classList].find(c=>c.startsWith('s-')),e.querySelector('.dqs').textContent.trim(),!!e.querySelector('.dqov')])"
OVFD="[document.documentElement.scrollWidth,...[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&!e.closest('header')).slice(0,5).map(e=>e.tagName+'.'+e.className+':'+Math.round(e.getBoundingClientRect().right))]"
NOOVF="[...document.querySelectorAll('main *')].every(e=>{const r=e.getBoundingClientRect();return r.left>=-1&&r.right<=innerWidth+1})"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1366,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'gsi' not in m.text else None)
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload(); pg.wait_for_timeout(500)
    today=pg.evaluate('dayId()'); yday=pg.evaluate('dayId(Date.now()-864e5)')
    # 1) 탭 바: 총 수익 → ㅡ 구분선 → 일퀘 현황 → 길드 현황
    tabs=pg.eval_on_selector_all('#tabs > *',"e=>e.map(x=>x.tagName==='SPAN'?'|'+x.className:x.textContent.trim())")
    check('tab order with divider', tabs==['보스 현황','수익 분석','|tabsep','길드 현황'], tabs)
    sep=pg.evaluate("(()=>{const r=document.querySelector('#tabs .tabsep').getBoundingClientRect(),t=document.querySelector('[data-tab=total]').getBoundingClientRect();return {w:r.width,h:r.height,mid:Math.abs((r.top+r.bottom)/2-(t.top+t.bottom)/2)}})()")
    check('divider is a short horizontal line, vertically centered', 8<=sep['w']<=20 and 1<=sep['h']<=3 and sep['mid']<6, sep)
    check('no API calls before opening tabs', not sched_calls() and not guild_calls(), CALLS)
    n1=len(sched_calls())
    # 5) 길드 현황
    pg.click('[data-tab=guild]'); pg.wait_for_selector('.gtile'); wait_idle(pg)
    gc=guild_calls(); print('guild calls',gc)
    ready=pg.evaluate("(()=>{const k=kst();return k.getUTCHours()*60+k.getUTCMinutes()>=570})()"); exp=today if ready else yday
    check('guild ranking called for type 2 and 1 with date', sorted(gc)==sorted([(exp,'2'),(exp,'1')]), gc)
    tiles=pg.eval_on_selector_all('.gtile','e=>e.map(x=>x.innerText.replace(/\\s+/g," ").trim())'); print(tiles)
    check('지하 수로 tile', '지하 수로' in tiles[0] and '137,591' in tiles[0] and '532위' in tiles[0], tiles)
    check('플래그 레이스 tile', '플래그 레이스' in tiles[1] and '4,000' in tiles[1] and '523위' in tiles[1], tiles)
    gt=pg.inner_text('.gcard'); check('guild level/master/date shown', 'Lv.30' in gt and '터래플' in gt and f'기준 {exp}' in gt and '봉사활동' in gt and '스카니아' in gt, gt)
    rows=pg.eval_on_selector_all('.grow-r','e=>e.map(x=>x.innerText.replace(/\\s+/g," ").trim())'); print(rows)
    check('main characters only, with 지하 수로 score from scheduler', len(rows)==1 and '단풍용사' in rows[0] and '23,513' in rows[0] and '플래그' not in rows[0], rows)
    check('guild tab: one scheduler call for main only', len(sched_calls())==n1+1, sched_calls()[n1:])
    pg.mouse.move(5,5); shot(pg,'tab_guild.png')
    # 랭킹 미준비 → 어제로 대체
    GUILD_EMPTY.add(today); g0=len(guild_calls())
    pg.evaluate("guildC=null; refreshGuild(true)"); wait_idle(pg)
    gt=pg.inner_text('.gcard'); check('fallback to yesterday when today empty', f'기준 {yday}' in gt and '어제' in gt and '137,591' in gt, (gt,guild_calls()[g0:]))
    GUILD_EMPTY.add(yday); pg.evaluate("refreshGuild(true)"); wait_idle(pg)
    gt=pg.inner_text('.gcard'); check('both empty → message, keeps last data', '찾지 못했습니다' in gt and '137,591' in gt, gt)
    GUILD_EMPTY.clear()
    # 본캐가 여러 명이어도 모두 표시 (현재 UI는 1명) / 없으면 안내
    pg.evaluate("S.characters.forEach(c=>c.isMain=false); renderGuild()"); check('no main → hint', '본캐로 지정된 캐릭터가 없습니다' in pg.inner_text('#view'))
    pg.evaluate("S.characters[0].isMain=true; save(); renderGuild()")
    gr=pg.inner_text('#view .card:nth-child(2)')
    check('본캐 지하 수로 row: only 지하 수로 score (no 플래그 / 주간 미션)', '지하 수로' in gr and '플래그' not in gr and '주간 미션' not in gr, gr)
    pth=os.path.join(OUT,'guild_suro_only.png'); pg.locator('#view').screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    pg.click('[data-tab=guild]'); pg.wait_for_timeout(150)
    # 6) 사이드바 캐릭터 클릭 → 보스 체크로 이동, 기존 탭 정상
    pg.click('#charList .char[data-id=c2]'); pg.wait_for_timeout(150); check('sidebar click → boss tab', pg.evaluate('tab')=='boss' and pg.evaluate('S.activeId')=='c2')
    for t in ['total','boss']: pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(80)
    check('existing tabs still render', pg.query_selector('#view .card') is not None)
    # 7) 모바일 375 / 320
    for w in (375,320):
        pg.set_viewport_size({'width':w,'height':800})
        pg.click('[data-tab=guild]'); wait_idle(pg); pg.wait_for_timeout(150)
        check(f'{w}px guild: no horizontal overflow', pg.evaluate(NOOVF), pg.evaluate(OVFD))
        if w==375: shot(pg,'tab_guild_mobile.png',full_page=True)
    # 8) 라이트 테마도 깨지지 않음
    pg.set_viewport_size({'width':1366,'height':900}); pg.click('#themeBtn'); pg.click('[data-tab=guild]'); wait_idle(pg)
    check('light theme renders', pg.evaluate("document.documentElement.dataset.theme")=='light' and pg.locator('.gtile').count()>=1)
    check('일퀘 현황 탭 없음', pg.locator('[data-tab=daily]').count()==0 and not pg.evaluate("typeof renderDaily!=='undefined'"))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
