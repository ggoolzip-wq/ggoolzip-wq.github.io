import sys; print('SKIP: b294 길드 현황 탭 삭제 (화면 없음)'); sys.exit(0)
import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8881=_tutil.free_port()
# b85: 길드 현황 — 고정 '봉사활동' 삭제, '+ 길드 추가'(보이는 캐릭터의 월드+길드, 다중), 길드별 수로·플래그 정보, ✕ 제거, settings.guilds 저장. (원래 b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8881
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
import json, urllib.parse as up
def ch(id,name,acc,guild=None,world='스카니아'):
    c={'id':id,'name':name,'level':280,'job':'히어로','world':world,'image':'','accId':acc,'ocid':'o'+id,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
    if guild is not None: c['guild']=guild; c['guildAt']=1
    return c
ST={'version':5,'theme':'dark','activeId':'c1','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch('c1','에이','a1','A길드'),ch('c2','비이','a1','B길드'),ch('c5','에이둘','a1','A길드'),ch('c3','씨이','a1',None,'루나'),ch('c4','숨는캐','a2','H길드')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}],'suroChars':[]}}
calls=[]
def nexon(route):
    u=up.urlparse(route.request.url); q=dict(up.parse_qsl(u.query)); calls.append(u.path)
    if u.path.endswith('/character/basic'):
        G={'oc1':('스카니아','A길드'),'oc5':('스카니아','A길드'),'oc2':('스카니아','B길드'),'oc3':('루나','C길드'),'oc4':('스카니아','H길드')}[q.get('ocid')]
        return route.fulfill(status=200,content_type='application/json',body=json.dumps({'world_name':G[0],'character_guild_name':G[1],'character_level':280,'character_class':'히어로'}))
    if u.path.endswith('/ranking/guild'):
        pt=1000 if q.get('ranking_type')=='2' else 50
        return route.fulfill(status=200,content_type='application/json',body=json.dumps({'ranking':[{'guild_name':q.get('guild_name'),'world_name':q.get('world_name'),'guild_level':25,'guild_master_name':'마스터','guild_point':pt,'ranking':7}]}))
    return route.fulfill(status=200,content_type='application/json',body='{}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',nexon)
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='guild'; render()"); pg.wait_for_timeout(400)
    txt=pg.inner_text('#view')
    check("no hardcoded '봉사활동'", '봉사활동' not in txt, txt[:200])
    check("'+ 길드 추가' next to title", pg.evaluate("!!document.querySelector('#guildCard h2 #guildAdd')"))
    pg.click('#guildAdd'); pg.wait_for_function("document.querySelectorAll('#guildCard .surocand').length===3",timeout=20000)
    cands=pg.evaluate("[...document.querySelectorAll('#guildCard .surocand')].map(e=>e.innerText.replace(/\\s+/g,' ').trim())")
    check('candidates: distinct world+guild of visible chars (C길드 via basic API, hidden H길드 excluded)', len(cands)==3 and any('A길드' in c and '에이, 에이둘' in c for c in cands) and any('C길드' in c and '루나' in c for c in cands) and not any('H길드' in c for c in cands), cands)
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12w_b85_test_guild_picker.png')
    pg.check('#guildCard .surocand input[value="스카니아|A길드"]'); pg.check('#guildCard .surocand input[value="루나|C길드"]'); pg.click('#guildOk'); pg.wait_for_function("[...document.querySelectorAll('#guildCard .gblk')].filter(e=>e.innerText.includes('1,000')).length===2",timeout=20000)
    blks=pg.evaluate("[...document.querySelectorAll('#guildCard .gblk')].map(e=>e.innerText.replace(/\\s+/g,' '))")
    check('two guild blocks with 수로·플래그 info', len(blks)==2 and all('1,000' in x and '50' in x and '7' in x and '마스터' in x for x in blks), blks)
    pg.screenshot(path='/workspace/maple-boss-tracker/oct12w_b85_test_guild_added.png')
    pg.click('[data-gdel="스카니아|A길드"]'); pg.wait_for_timeout(300)
    saved=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).settings.guilds")
    check('remove + persisted', saved==[{'world':'루나','name':'C길드'}], saved)
    pg.reload(); pg.wait_for_timeout(800); pg.evaluate("tab='guild'; render()"); pg.wait_for_timeout(500)
    r=pg.evaluate("[...document.querySelectorAll('#guildCard .gblk-h b')].map(e=>e.innerText)"); check('survives reload', r==['C길드'], r)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
