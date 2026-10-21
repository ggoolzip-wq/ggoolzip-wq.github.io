import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8917=_tutil.free_port()
# b136: 캐릭터 동기화가 등록을 지우던 버그 — 스케줄러 등록 목록 기준, 클리어 여부로 절대 안 끔
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P8917)
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b136_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1,e=True:{'enabled':e,'diff':d,'party':p}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    resp={}
    hits=[]
    def sched(r):
        hits.append(r.request.url[:90])
        if 'scheduler/character-state' in r.request.url: return r.fulfill(status=200,content_type='application/json',body=json.dumps(resp))
        if 'character/list' in r.request.url: return r.fulfill(status=200,content_type='application/json',body=json.dumps({'account_list':[{'account_id':'x','character_list':[{'ocid':'o1','character_name':'동기화캐','world_name':'스카니아','character_class':'히어로','character_level':280}]}]}))
        if '/id?' in r.request.url: return r.fulfill(status=200,content_type='application/json',body='{"ocid":"o1"}')
        return r.abort()
    ctx.route('https://open.api.nexon.com/**',sched)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week")
    C={'id':'c1','name':'동기화캐','level':280,'job':'히어로','world':'스카니아','image':'','ocid':'o1','b134':1,
       'bosses':{'lucid':B('hard'),'will':B('hard',2),'dusk':B('chaos'),'kaling':B('normal'),'blackmage':B('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'period':pg.evaluate("({...S.period})"),'settings':{}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    pg.reload(); pg.wait_for_timeout(700)
    on=lambda: pg.evaluate("Object.entries(S.characters[0].bosses).filter(([k,v])=>v.enabled).map(([k])=>k).sort()")
    def apply(rows):
        return pg.evaluate("rows=>{applyScheduler(S.characters[0],{date:S.period.week+'T00:00+09:00',boss_contents:rows});save();render();return 1}",rows)
    # 1) 실제 응답처럼 clear_flag 만 (registration_flag 없음) + 이번 달 검마 클리어 → 예전엔 주간 전부 꺼짐
    apply([{'content_name':'검은 마법사','difficulty':'hard','cycle':'bossMonthly','clear_flag':'true'},
           {'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','clear_flag':'false'}])
    check('registration_flag 없는 응답 + 월간 클리어: 주간 등록 하나도 안 꺼짐', on()==['blackmage','dusk','kaling','lucid','will'], on())
    # 2) 리셋 직후: 등록 true 인데 클리어 false 전부 → 다 보임
    apply([{'content_name':n,'difficulty':d,'cycle':'bossWeekly','registration_flag':'true','clear_flag':'false'} for n,d in [('루시드','hard'),('윌','hard'),('더스크','chaos'),('카링','normal'),('스우','hard')]])
    check('등록 true·클리어 false: 전부 주간 라인업에 (새로 등록된 스우도 켜짐)', on()==['blackmage','dusk','kaling','lotus','lucid','will'], on())
    check('파티 인원 유지 (윌 2인)', pg.evaluate("S.characters[0].bosses.will.party")==2)
    # 3) 스케줄러가 registration_flag:"false" 여도 / 응답에 없어도 동기화는 등록을 끄지 않음 (사용자: 등록은 리셋·동기화로 절대 안 지움)
    apply([{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','clear_flag':'false'},
           {'content_name':'카링','difficulty':'normal','cycle':'bossWeekly','registration_flag':'false','clear_flag':'false'}])
    # b242: 이번 주 응답에서 명시적 registration_flag 'false' + 안 잡은 주간 보스 = 스케줄러에서 뺀 것 → 꺼짐(교체 바로 적용). 응답에 없는 보스는 여전히 유지
    check('b242: 등록 false(안 잡음)는 꺼짐, 응답에 없음은 유지', on()==['blackmage','dusk','lotus','lucid','will'], on())
    # 4) 등록 false 만 잔뜩 (리셋 직후 이상 응답) → 아무것도 안 끔
    apply([{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'false','clear_flag':'false'}])
    check('주간 등록 true 가 하나도 없는 응답은 끄는 근거 아님', 'lucid' in on(), on())
    # 5) 이번 주 체크한 보스는 등록 false 라도 유지
    pg.evaluate("S.characters[0].weekly.dusk=true")
    apply([{'content_name':'루시드','difficulty':'hard','cycle':'bossWeekly','registration_flag':'true','clear_flag':'false'},
           {'content_name':'더스크','difficulty':'chaos','cycle':'bossWeekly','registration_flag':'false','clear_flag':'false'}])
    check('이번 주 체크한 더스크는 유지', 'dusk' in on(), on())
    # 6) 진짜 버튼: 🔄 동기화 (mock 응답) 후 라인업 스크린샷
    pg.evaluate("()=>{S.settings.accounts=[{id:'a1',label:'본계정',key:'live_K1_0123456789abcdefgh',main:true}];S.characters[0].accId='a1';S.characters[0].weekly={};save();render()}")
    resp.update({'date':wk+'T00:00+09:00','character_name':'동기화캐','boss_contents':[{'content_name':n,'difficulty':d,'cycle':'bossWeekly','registration_flag':'true','clear_flag':c} for n,d,c in [('루시드','hard','true'),('윌','hard','false'),('더스크','chaos','false'),('스우','hard','false')]]+[{'content_name':'검은 마법사','difficulty':'hard','cycle':'bossMonthly','registration_flag':'true','clear_flag':'true'}],'weekly_boss_clear_count':1,'weekly_boss_clear_limit_count':12})
    pg.evaluate("syncAll({full:true})"); pg.wait_for_timeout(2500)
    o=on(); check('동기화 후: 등록된 보스 전부 라인업 (클리어 루시드 + 미클리어 윌·더스크·스우)', all(x in o for x in ['lucid','will','dusk','lotus']) and pg.evaluate("!!S.characters[0].weekly.lucid && !S.characters[0].weekly.will"), o)
    el=pg.locator('.boss-list').first
    if el.count(): shot(el,'sync_lineup')
    else: shot(pg.locator('#view'),'sync_lineup')
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
