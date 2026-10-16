# b135: 주 평균 글씨(누적 수익·판매·총 득템) + 주간 메소 그래프 = 이번 주만(목 0시 0부터)
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8965'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:350] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f"{os.environ.get('MBT_PFX','b190')}_{TAG}_{name}.png"))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)

def it(name,slot='모자',**o): return {'item_equipment_slot':slot,'item_equipment_part':slot,'item_name':name,'item_total_option':{k:str(v) for k,v in o.items()}}
PC=lambda: it('프리미엄 PC방 훈장','훈장'); GOOD=lambda: it('칠요의 몬스터파커','훈장')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1400,'height':1200},locale='ko-KR')
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(500)
    M=lambda e: pg.evaluate("e=>medalFrom(e)",e)
    strong=[it('모자',boss_damage=30,attack_power=100,dex=200)]; weak=[it('모자',attack_power=10,dex=20)]
    r=M({'preset_no':1,'item_equipment_preset_1':weak+[GOOD()],'item_equipment_preset_2':strong+[PC()],'item_equipment_preset_3':[]})
    check('1 보스 프리셋(점수 최고=2)에 PC방 훈장 → 경고', r['bad'] and r['preset']==2 and not r['empty'], r)
    r=M({'preset_no':2,'item_equipment_preset_1':strong+[GOOD()],'item_equipment_preset_2':weak+[PC()]})
    check('2 사냥 프리셋에만 PC방 훈장 → 경고 없음', not r['bad'] and r['preset']==1, r)
    r=M({'preset_no':1,'item_equipment_preset_1':weak+[GOOD()],'item_equipment_preset_2':strong})
    check('3 보스 프리셋 훈장 칸 비어 있음 → 경고(empty)', r['bad'] and r['empty'] and r['preset']==2, r)
    r=M({'preset_no':3,'item_equipment_preset_1':weak+[GOOD()],'item_equipment_preset_3':weak+[PC()]})
    check('4 점수 같으면 현재 preset_no(3)', r['bad'] and r['preset']==3, r)
    r=M({'preset_no':1,'item_equipment_preset_1':[],'item_equipment_preset_2':None})
    check('5 프리셋 전부 비면 경고 없음', not r['bad'], r)
    C={'id':'c1','name':'캐릭A','level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{},'medal':{'v':2,'bad':True,'empty':True,'preset':2,'where':['보스 프리셋 2 (훈장 없음)'],'at':1}}
    ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'period':pg.evaluate("({...S.period})"),'settings':{}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(1000)
    t=pg.evaluate("[document.querySelector('.medalwarn')?.innerText||'',document.querySelector('.medalrow .mdtxt')?.innerText||'']")
    check('UI: 기존 경고 띠 + 문구(훈장 없음)', '훈장 잘못 착용중' in t[0] and '훈장이 없는' in t[1], t)
    if pg.locator('.medalrow').count(): shot(pg.locator('.medalrow').locator('xpath=ancestor::div[contains(@class,"card")][1]'),'medal')
    b.close()
finally: srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
