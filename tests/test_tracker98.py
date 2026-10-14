# b134: 접속 안 한 캐릭터(지난 주 스케줄러 응답)도 등록 복구 + 다음 목요일에 다시 안 꺼지게
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8915'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b134_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1,e=True:{'enabled':e,'diff':d,'party':p}
def ch(i,name,bs): return {'id':i,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'o'+i,'bosses':bs,'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
C1=ch('c1','접속캐',{'lucid':B('hard'),'will':B('hard',1,False)})
C2=ch('c2','미접속캐',{'lotus':B('hard',2,False),'will':B('normal',3,False),'dusk':B('chaos',1,False)})
C3=ch('c3','기록없는캐',{'lucid':B('easy',1,False)})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':900},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(400)
    wk=pg.evaluate("S.period.week"); prev=pg.evaluate("w=>{const t=new Date(w+'T00:00:00+09:00');t.setDate(t.getDate()-7);return t.toISOString().slice(0,10)}",wk)
    pg.evaluate("w=>{const t=new Date(w+'T12:00:00Z');return 0}",wk)
    H={'week':prev,'total':1,'cleared':4,'perChar':[
       {'id':'c1','name':'접속캐','meso':1,'count':2,'bosses':['루시드(하드)','윌(하드)']},
       {'id':'c2','name':'미접속캐','meso':1,'count':2,'bosses':['스우(하드)/2인','더스크(카오스)']}]}
    ST={'version':5,'theme':'dark','activeId':'c2','worldOrder':[],'history':[H],'monthHistory':[],'characters':[C1,C2,C3],
        'period':pg.evaluate("({...S.period})"),'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    # before 화면: 예전 빌드에선 그대로 꺼진 상태
    pg.reload(); pg.wait_for_timeout(800)
    shot(pg.locator('.boss-list, .bosslay, #view').first,'offline_char')
    if not NOCHK:
        bs=pg.evaluate("Object.fromEntries(S.characters.map(c=>[c.id,Object.fromEntries(Object.entries(c.bosses).map(([k,v])=>[k,[!!v.enabled,v.diff,v.party]]))]))")
        check('미접속캐: 지난 주 기록의 스우(하드)·더스크(카오스) 다시 켬, 파티 유지', bs['c2']['lotus']==[True,'hard',2] and bs['c2']['dusk']==[True,'chaos',1], bs['c2'])
        check('지난 주 기록에 없는 보스(미접속캐 윌)는 지어내지 않음 — 꺼진 그대로', bs['c2']['will'][0] is False, bs['c2'])
        check('접속캐: 기록의 윌(하드) 복구', bs['c1']['will']==[True,'hard',1], bs['c1'])
        check('지난 주 기록 없는 캐릭터는 그대로', bs['c3']['lucid'][0] is False, bs['c3'])
        check('1번만: c.b134 표시', pg.evaluate("S.characters.every(c=>c.b134===1)"))
        # 다시 끈 뒤 새로고침 → 다시 켜지지 않음
        pg.evaluate("()=>{S.characters[1].bosses.dusk.enabled=false;save()}"); pg.reload(); pg.wait_for_timeout(600)
        check('한 번 복구 후엔 다시 안 건드림', pg.evaluate("S.characters[1].bosses.dusk.enabled===false"))
        # 지난 주 응답(미접속) + 등록 표시 없음 → 등록 끄지 않음 (다음 목요일 대비)
        pg.evaluate("""prev=>{applyScheduler(S.characters[1],{date:prev+'T00:00+09:00',boss_contents:[
          {content_name:'윌',difficulty:'노말',cycle:'bossWeekly',registration_flag:'false',complete_flag:'true'}]});save()}""",prev)
        check('stale 응답: 등록 그대로(스우 켜짐 유지)', pg.evaluate("S.characters[1].bosses.lotus.enabled===true"))
        pg.evaluate("""w=>{applyScheduler(S.characters[1],{date:w+'T00:00+09:00',boss_contents:[
          {content_name:'윌',difficulty:'노말',cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]});save()}""",wk)
        check('b136 이번 주 응답: 윌 켬, 스우 등록 유지(안 끔)', pg.evaluate("S.characters[1].bosses.lotus.enabled && S.characters[1].bosses.will.enabled"))
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
