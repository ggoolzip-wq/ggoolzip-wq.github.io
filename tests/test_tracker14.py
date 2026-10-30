import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8875=_tutil.free_port()
import _legacy
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
srv=_tutil.Popen(['python3','-m','http.server',str(_P8875),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(('http://127.0.0.1:'+str(_P8875)+'/index.html'),timeout=1); break
    except Exception: time.sleep(0.1)
URL=('http://localhost:'+str(_P8875)+'/index.html')
IMG='https://open.api.nexon.com/static/maplestory/character/look/mock-'
def ch(id,name,lv,job,ocid,acc,main=False,img=''):
    return {'id':id,'name':name,'level':lv,'job':job,'world':'스카니아','ocid':ocid,'accId':acc,'isMain':main,'image':(IMG+img) if img else '',
            'bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main','a1',True,'main'),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1','a1',False,'alt1'),
                ch('c3','신궁짱',265,'신궁','ocid-alt2','a1',False,'alt2'),ch('c4','부계정비숍',268,'비숍','ocid-b1','a2',False,'b1'),
                ch('c5','수동캐릭',250,'아델','','',False)],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM},{'id':'a2','label':'부계정','key':KA}],'autoSync':True,'autoEnable':True,'lastSync':int(time.time()*1000),'guilds':[{'world':'스카니아','name':'봉사활동'}]}}  # b85: 고정 길드 대신 선택한 길드
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
    # 1) 탭 바: 총 수익 → ㅡ 구분선 → 길드 현황 (b119: 일퀘 현황 삭제)
    tabs=pg.eval_on_selector_all('#tabs > *',"e=>e.map(x=>x.tagName==='SPAN'?'|'+x.className:x.textContent.trim())")
    check('tab order with divider', tabs==['이번 주 보스','수익 분석','득템 분석','|tabsep','보스 득템 자동 기록','|tabsep','신창섭 라이브LIVE'], tabs)
    sep=pg.evaluate("(()=>{const r=document.querySelector('#tabs .tabsep').getBoundingClientRect(),t=document.querySelector('[data-tab=total]').getBoundingClientRect();return {w:r.width,h:r.height,mid:Math.abs((r.top+r.bottom)/2-(t.top+t.bottom)/2)}})()")
    check('divider is a short horizontal line, vertically centered', 8<=sep['w']<=20 and 1<=sep['h']<=3 and sep['mid']<6, sep)
    check('no API calls before opening tabs', not sched_calls() and not guild_calls(), CALLS)
    n1=len(sched_calls())
    # 5) b294: 길드 현황 탭 삭제 → 그 자리에 '보스 득템 자동 기록'
    check('b294: 길드 탭 없음', pg.locator('[data-tab=guild]').count()==0 and pg.locator('[data-tab=auto]').count()==1)
    check('b294: 길드 API 안 부름', not guild_calls(), guild_calls())
    # 6) 사이드바 캐릭터 클릭 → 보스 체크로 이동, 기존 탭 정상
    pg.click('#charList .char[data-id=c2]'); pg.wait_for_timeout(150); check('sidebar click → boss tab', pg.evaluate('tab')=='boss' and pg.evaluate('S.activeId')=='c2')
    for t in ['total','boss']: pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(80)
    check('existing tabs still render', pg.query_selector('#view .card') is not None)
    # 7) 모바일 375 / 320
    for w in (375,320):
        pg.set_viewport_size({'width':w,'height':800})
        pg.click('[data-tab=auto]'); pg.wait_for_timeout(400)
        check(f'{w}px auto: no horizontal overflow', pg.evaluate(NOOVF), pg.evaluate(OVFD))
        if w==375: shot(pg,'tab_auto_mobile.png',full_page=True)
    # 8) 라이트 테마도 깨지지 않음
    pg.set_viewport_size({'width':1366,'height':900}); pg.click('[data-tab=auto]'); pg.wait_for_timeout(300)
    check('b182: default dark + header theme toggle', pg.evaluate("document.documentElement.dataset.theme")=='dark' and pg.locator('header #themeBtn').count()==1)
    check('b119: 일퀘 현황 탭 삭제', pg.locator('[data-tab=daily]').count()==0 and pg.evaluate("typeof renderDaily==='undefined'"))
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
