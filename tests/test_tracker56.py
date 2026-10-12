# b75: 보스 목록 저장 → 초록 '저장이 완료되었습니다.'(취소 왼쪽, 하단 알림 없음) / 저장 안 한 변경 + 탭·캐릭터 이동 → 사진+질문 예/아니오 / 수익 기록 창 바깥 클릭 무시, 빈 금액 '금액을 입력해주세요.' / 빈 칸 경고 = 빨간 테두리
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8861
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','bosses':{'lucid':{'enabled':True,'diff':'hard','party':1}},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch('c1','본캐용사'),ch('c2','부캐에프')],'settings':{'accounts':[]}}
MK="pendStart(); activeChar().bosses.lucid.party=(activeChar().bosses.lucid.party||1)+1; save(); render();"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    toast=lambda: pg.evaluate("document.querySelector('#toast').classList.contains('show')")
    pg.evaluate(MK); pg.wait_for_timeout(200); pg.click('#pendSave'); pg.wait_for_timeout(400)
    pos=pg.evaluate("(()=>{const d=document.querySelector('.pdone'),c=document.querySelector('#pendCancel'); return d&&c?[d.textContent,getComputedStyle(d).color,d.getBoundingClientRect().right<=c.getBoundingClientRect().left]:null})()")
    check("save → green '저장이 완료되었습니다.' left of 취소, no toast", pos and pos[0]=='저장이 완료되었습니다.' and pos[1]=='rgb(60, 207, 110)' and pos[2] and not toast(), (pos,toast()))
    pg.wait_for_timeout(3200); check('save text disappears after ~3s', pg.locator('.pdone').count()==0)
    # 캐릭터 이동 가드
    pg.evaluate(MK); pg.click('#charList [data-id=c2]'); pg.wait_for_timeout(300)
    check('pending + other character → centered ask with portrait + text', pg.locator('#svAsk .pgav .avatar').count()==1 and '지금까지의 변경사항을 저장하시겠습니까?' in pg.inner_text('#svAsk') and pg.evaluate("S.activeId")=='c1')
    pg.mouse.click(5,5); pg.wait_for_timeout(200)
    check('backdrop → stays (no move, still pending)', pg.evaluate("[S.activeId,!!pend]")==['c1',True])
    pg.click('#charList [data-id=c2]'); pg.wait_for_timeout(300); pg.click('#svAsk [data-k=no]'); pg.wait_for_timeout(300)
    check('아니오 → discarded, moved to target', pg.evaluate("[S.activeId,!!pend,S.characters[0].bosses.lucid.party]")==['c2',False,2], pg.evaluate("[S.activeId,!!pend,S.characters[0].bosses.lucid.party]"))
    pg.evaluate(MK); pg.click('[data-tab=loot]') if pg.locator('[data-tab=loot]').count() else pg.click('#tabs button:nth-child(3)'); pg.wait_for_timeout(300)
    pg.click('#svAsk [data-k=yes]'); pg.wait_for_timeout(500)
    check('예 on tab switch → saved then moved', pg.evaluate("[!!pend,S.characters[1].bosses.lucid.party,tab!=='boss']")==[False,2,True], pg.evaluate("[!!pend,S.characters[1].bosses.lucid.party,tab]"))
    # 수익 기록 창
    pg.evaluate("askRev(activeChar(),findBoss('lucid'),'lucid|x','pitched_box',null)"); pg.wait_for_timeout(200)
    pg.mouse.click(5,5); pg.wait_for_timeout(200); check('rev modal: backdrop click does nothing', pg.locator('#revModal').count()==1)
    pg.click('[data-rv=ok]'); pg.wait_for_timeout(200)
    check("rev empty → '금액을 입력해주세요.' + red border", pg.inner_text('#rvErr')=='금액을 입력해주세요.' and 'inerr' in pg.get_attribute('#rvAmt','class'))
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12m_b75_test_rev.png')
    pg.type('#rvAmt','3'); check('typing clears red border', 'inerr' not in (pg.get_attribute('#rvAmt','class') or ''))
    pg.click('[data-rv=no]')
    # 계정 추가 줄: 빈 이름·키 → 빨간 테두리
    pg.evaluate("openImport()"); pg.wait_for_timeout(300); pg.evaluate("accAddShow(true)"); pg.fill('#newAccLabel',''); pg.click('#newAccBtn'); pg.wait_for_timeout(200)
    check('first key with empty name allowed as 본계정, empty key → red border on key', 'inerr' in pg.get_attribute('#newAccKey','class') and 'inerr' not in (pg.get_attribute('#newAccLabel','class') or ''))
    pg.type('#newAccKey','x'); check('typing key clears border', 'inerr' not in pg.get_attribute('#newAccKey','class'))
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
