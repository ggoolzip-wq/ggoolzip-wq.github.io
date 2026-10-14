# b133: 목요일 주간 리셋 직후 스케줄러 동기화가 보스 등록을 지우던 버그
#  - stale 완료(지난 주 date + complete)만 보고 registration 을 무시하던 경로
#  - boss_contents 에 매칭되는 주간 보스가 0개일 때 전부 끄던 경로
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8914'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b133_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'o1',
   'bosses':{'lotus':B('hard',2),'will':B('hard',3),'kaling':B('normal'),'lucid':B('hard')},
   'weekly':{'lotus':True,'will':True},'monthly':{},'auto':{'lotus':True,'will':True},'drops':{'lotus|h_ear':1},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],
    'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':900},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    pg.reload(); pg.wait_for_timeout(800)
    # 이번 주 시작을 강제로 지난주 금요일처럼 보이게 한 뒤, 오늘(새 주)로 리셋
    prev=pg.evaluate("""()=>{const cur=S.period.week; const t=new Date(cur+'T00:00:00+09:00'); t.setDate(t.getDate()-7); const y=t.getFullYear(),m=String(t.getMonth()+1).padStart(2,'0'),d=String(t.getDate()).padStart(2,'0');
      S.period.week=y+'-'+m+'-'+d; S.characters[0].weekly={lotus:true,will:true}; save(); return S.period.week}""")
    shot(pg.locator('.boss-list, .bosslay, #view').first,'before_reset')
    pg.evaluate("()=>{checkResets(); render()}"); pg.wait_for_timeout(300)
    weekly0=pg.evaluate("S.characters[0].weekly")
    check('리셋 후 주간 클리어만 비움 (등록 bosses 는 유지)', weekly0=={} and pg.evaluate("['lotus','will','kaling','lucid'].every(id=>S.characters[0].bosses[id].enabled)"), weekly0)
    # 넥슨이 아직 지난주 date + complete 로 주는 경우 (목 직후 흔한 응답)
    d=pg.evaluate("""prev=>({date:prev+'T00:00+09:00',weekly_boss_clear_count:2,weekly_boss_clear_limit_count:14,boss_contents:[
      {content_name:'스우',difficulty:'하드',cycle:'bossWeekly',registration_flag:'true',complete_flag:'true'},
      {content_name:'윌',difficulty:'하드',cycle:'bossWeekly',registration_flag:'true',complete_flag:'true'},
      {content_name:'카링',difficulty:'노말',cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'},
      {content_name:'루시드',difficulty:'하드',cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]})""",prev)
    pg.evaluate("d=>{applyScheduler(S.characters[0],d);save();render()}",d); pg.wait_for_timeout(300)
    shot(pg.locator('.boss-list, .bosslay, #view').first,'after_stale_sync')
    bs=pg.evaluate("Object.fromEntries(Object.entries(S.characters[0].bosses).map(([k,v])=>[k,{enabled:!!v.enabled,diff:v.diff,party:v.party}]))")
    wk=pg.evaluate("S.characters[0].weekly")
    check('stale 완료+등록: 등록 유지, 이번 주 클리어로 안 침', all(bs[k]['enabled'] for k in ('lotus','will','kaling','lucid')) and wk=={} and bs['lotus']['party']==2, (bs,wk))
    # 매칭 0개인 boss_contents(일일만) → 등록을 지우면 안 됨
    pg.evaluate("""()=>{S.characters[0].bosses.zakum={enabled:true,diff:'chaos',party:1}; applyScheduler(S.characters[0],{date:S.period.week+'T00:00+09:00',boss_contents:[
      {content_name:'몬스터파크',difficulty:'',cycle:'daily',registration_flag:'true',complete_flag:'false'}]}); save()}""")
    check('일일만 있는 응답: 주간 등록을 끄지 않음', pg.evaluate("S.characters[0].bosses.zakum.enabled && S.characters[0].bosses.lotus.enabled"))
    # 스케줄러에 없는 보스만 끔 (기존 규칙)
    pg.evaluate("""()=>{applyScheduler(S.characters[0],{date:S.period.week+'T00:00+09:00',boss_contents:[
      {content_name:'루시드',difficulty:'하드',cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]}); save()}""")
    check('b136: 목록에 없는 등록도 유지(동기화는 안 끔)', pg.evaluate("S.characters[0].bosses.lotus.enabled && S.characters[0].bosses.lucid.enabled && S.characters[0].bosses.lotus.party===2"))
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
