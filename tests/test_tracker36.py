# b48: 예비 API 키 — 이름 칸, 같은 넥슨 계정만, 429/OPENAPI00007 이면 예비 키로 다시 + 오늘 하루 예비 키, 남은 호출(추정) 표시
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8836/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8836','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
KA,BKA,KX='live_MAIN_A_0123456789abcdef','live_BACK_A_0123456789abcdef','live_OTHER_X_0123456789abcde'
ACC={KA:'acc-A',BKA:'acc-A',KX:'acc-X'}; RATE={'on':False}; CALLS=[]
def handle(route):
    u=route.request.url; k=route.request.headers.get('x-nxopen-api-key',''); CALLS.append((u.split('/v1/')[1].split('?')[0],k))
    if RATE['on'] and k==KA: return route.fulfill(status=429,json={'error':{'name':'OPENAPI00007','message':'rate'}})
    if '/character/list' in u: return route.fulfill(json={'account_list':[{'account_id':ACC.get(k,'?'),'character_list':[{'ocid':'o1','character_name':'림강혼망','world_name':'스카니아','character_class':'렌','character_level':294}]}]})
    return route.fulfill(json={'date':time.strftime('%Y-%m-%d'),'character_level':294,'daily_contents':[],'weekly_contents':[],'boss_contents':[]})
ST={'version':5,'theme':'dark','activeId':'c0','characters':[{'id':'c0','name':'림강혼망','level':294,'job':'렌','world':'스카니아','ocid':'o1','accId':'a1','isMain':True,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}],
    'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':KA}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate('openAdd()'); pg.wait_for_selector('.bkrow'); pg.wait_for_timeout(500)
    check('계정 줄 아래 예비 키 줄 (이름 칸 + 키 칸 + 등록)', pg.locator('#bkLb-a1').count()==1 and pg.locator('#bkIn-a1').count()==1 and '본계정 예비' in pg.get_attribute('#bkLb-a1','placeholder'))
    q=pg.inner_text('.accrow .quota'); check('기본 키 남은 호출 표시', q.startswith('남은 호출 약 ') and q.endswith('/1000') and int(q.split('약 ')[1].split('/')[0])<1000, q)
    pg.fill('#bkIn-a1',KX); pg.click('[data-bkadd=a1]'); pg.wait_for_selector('.bkerr')
    e=pg.inner_text('.bkerr'); col=pg.evaluate("getComputedStyle(document.querySelector('.bkerr')).color")
    check('다른 넥슨 계정 키 → 빨간 거절 메시지, 저장 안 됨', '같은 넥슨 계정의 키가 아닙니다' in e and col=='rgb(255, 90, 90)' and not pg.evaluate("accById('a1').bk"), (e,col))
    pg.fill('#bkLb-a1','본계정 예비'); pg.fill('#bkIn-a1',BKA); pg.click('[data-bkadd=a1]'); pg.wait_for_selector('.bkrow .regok')
    check('같은 계정 키 → ✔ 등록 완료 + 이름', pg.evaluate("accById('a1').bk")==BKA and pg.input_value('[data-bklabel=a1]')=='본계정 예비' and '등록 완료' in pg.inner_text('.bkrow'))
    RATE['on']=True; n0=len(CALLS)
    r=pg.evaluate("nx('/maplestory/v1/scheduler/character-state',{ocid:'o1'},accById('a1').key).then(d=>!!d.date)")
    used=[k for _,k in CALLS[n0:]]
    check('기본 키 429 → 같은 요청을 예비 키로 다시 (성공)', r and used==[KA,BKA], used)
    n1=len(CALLS); pg.evaluate("nx('/maplestory/v1/scheduler/character-state',{ocid:'o1'},accById('a1').key)")
    check('그 뒤로는 오늘(KST) 예비 키만', [k for _,k in CALLS[n1:]]==[BKA], CALLS[n1:])
    pg.evaluate("renderAccList()"); q=pg.locator('.accrow .quota')
    check('한도 걸린 키: 빨간 표시 + 예비 키 사용 중', '예비 키 사용 중' in q.inner_text() and pg.evaluate("getComputedStyle(document.querySelector('.accrow .quota')).color")=='rgb(255, 90, 90)', q.inner_text())
    bq=pg.inner_text('.bkrow .quota'); check('예비 키 남은 호출 표시', '남은 호출 약' in bq, bq)
    ls=pg.evaluate("JSON.stringify(localStorage)"); dump=pg.evaluate("localStorage.getItem('mapleBossTracker.callCount')")
    check('호출 수는 키 해시로만 저장 (키 값 없음)', KA not in dump and BKA not in dump, dump)
    check('예비 키는 계정 설정에 있고 서버/드라이브용 데이터(backupData false)에는 없음', BKA not in pg.evaluate("JSON.stringify(backupData(false))") and '본계정 예비' in pg.evaluate("JSON.stringify(backupData(false))"))
    pg.evaluate("localStorage.setItem('mapleBossTracker.bkDay',JSON.stringify({a1:'2000-01-01'}))"); RATE['on']=False; n2=len(CALLS)
    pg.evaluate("nx('/maplestory/v1/scheduler/character-state',{ocid:'o1'},accById('a1').key)"); check('다음 날엔 기본 키로 돌아감', [k for _,k in CALLS[n2:]]==[KA])
    pg.evaluate("localStorage.setItem('mapleBossTracker.bkDay',JSON.stringify({a1:dayId()}));renderAccList()")
    pg.locator('#importModal .modal').screenshot(path='/workspace/shots/b48_backup.png')
    pg.click('[data-bkdel=a1]'); check('예비 키 삭제', not pg.evaluate("accById('a1').bk") and pg.locator('#bkIn-a1').count()==1)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
