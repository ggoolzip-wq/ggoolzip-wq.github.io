# test_b250: 스케줄러 응답의 '등록 안 한 다른 난이도'(registration_flag false) 줄 때문에 등록된 주간 보스가 꺼지던 버그
#  (목 리셋 뒤 12개 → 몇 개, 동기화마다 켜짐/꺼짐 번갈아). 같은 보스의 어떤 난이도든 true 면 켜짐 유지. 진짜 해제(모든 난이도 false)는 b242 대로 끔.
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
# 실제 응답 모양(2026-10-22): 보스마다 모든 난이도 줄, 등록한 난이도만 true
REG=[('스우','extreme'),('가디언 엔젤 슬라임','chaos'),('윌','hard'),('더스크','chaos'),('진 힐라','hard'),('듄켈','hard'),('선택받은 세렌','hard'),('감시자 칼로스','normal'),('카링','easy'),('최초의 대적자','normal'),('찬란한 흉성','normal'),('벨로나','easy')]
ALL={'스우':['normal','hard','extreme'],'가디언 엔젤 슬라임':['normal','chaos'],'윌':['easy','normal','hard'],'더스크':['normal','chaos'],'진 힐라':['normal','hard'],'듄켈':['normal','hard'],'선택받은 세렌':['normal','hard','extreme'],'감시자 칼로스':['easy','normal','chaos','extreme'],'카링':['easy','normal','hard','extreme'],'최초의 대적자':['easy','normal','hard','extreme'],'찬란한 흉성':['normal','hard'],'벨로나':['easy','normal','hard'],'림보':['normal','hard','extreme'],'발드릭스':['normal','hard','extreme']}
def resp(date,reg=REG,done=()):
    rows=[{'content_name':n,'difficulty':d,'cycle':'bossWeekly','registration_flag':'true' if (n,d) in reg else 'false','complete_flag':'true' if (n,d) in done else 'false'} for n,ds in ALL.items() for d in ds]
    rows.append({'content_name':'검은 마법사','difficulty':'hard','cycle':'bossMonthly','registration_flag':'true','complete_flag':'true'})
    return {'date':date+'T00:00+09:00','boss_contents':rows,'weekly_boss_clear_count':len(done),'weekly_boss_clear_limit_count':12}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
CNT="()=>{const c=S.characters[0];return {on:BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).length,shown:BOSSES.filter(b=>b.type==='weekly'&&bossOn(c,b)).length,next:c.bossNext?Object.keys(c.bossNext):[]}}"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    wk=pg.evaluate("()=>S.period.week")
    ap=lambda r:pg.evaluate("r=>{applyScheduler(S.characters[0],r); render();}",r)
    for i in range(1,4):
        ap(resp(wk)); r=pg.evaluate(CNT); check(f'이번 주 응답 {i}번째 동기화 → 12개 켜짐·표시, 대기 없음', r['on']==12 and r['shown']==12 and not r['next'], r)
    check('화면 주간 보스 탭 0/12', '0/12' in pg.inner_text('body').replace(' ',''), '')
    # 잡은 보스 2개(다른 난이도 false 줄 있음) → '빼기' 대기 안 생김, 12개 그대로
    ap(resp(wk,done=[('스우','extreme'),('윌','hard')])); r=pg.evaluate(CNT)
    check('잡은 보스: 다른 난이도 false 줄로 빼기 대기 안 생김', r['on']==12 and not r['next'] and pg.evaluate("()=>!!S.characters[0].weekly.lotus&&!!S.characters[0].weekly.will"), r)
    # 진짜 해제: 안 잡은 벨로나를 스케줄러에서 빼고 림보 노말 등록 → 벨로나 끔, 림보 켬 (b242)
    reg2=[x for x in REG if x[0]!='벨로나']+[('림보','normal')]
    ap(resp(wk,reg=reg2,done=[('스우','extreme'),('윌','hard')])); r=pg.evaluate(CNT); e=pg.evaluate("()=>{const c=S.characters[0];return [c.bosses.bellona?.enabled,c.bosses.limbo?.enabled]}")
    check('진짜 해제(모든 난이도 false) = 끔, 새 등록 = 켬', e==[False,True] and r['on']==12, (e,r))
    # 잡은 보스 진짜 해제 → 이번 주 유지 + 대기(b242)
    reg3=[x for x in reg2 if x[0]!='윌']
    ap(resp(wk,reg=reg3,done=[('스우','extreme'),('윌','hard')])); r=pg.evaluate(CNT)
    check('잡은 보스 해제 = 이번 주 유지 + 대기', pg.evaluate("()=>S.characters[0].bosses.will.enabled") and 'will' in r['next'], r)
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
