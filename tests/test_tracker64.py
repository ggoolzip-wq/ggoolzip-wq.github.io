# b86: '프리미엄 PC방' 훈장(현재+프리셋 1~3 어디든) 캐릭터 카드에 '훈장 잘못 착용중' 띠. (원래 b83: 득템 분석 '보스 득템왕' — 득템왕과 에픽빔왕 사이, 보스(난이도)별 득템 횟수 순위, 1위 보스 아이콘, 1~3위 지역 색, 한 줄·가로 스크롤 없음, 숨은 캐릭터 제외
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8882
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
import json, urllib.parse as up
def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'ocid':'o'+id,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c2','history':[],'monthHistory':[],'worldOrder':[],'characters':[ch('c1','프리셋범','a1'),ch('c2','정상캐','a1'),ch('c3','현재범','a1'),ch('c4','숨는캐','a2')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}]}}
M=lambda n:[{'item_equipment_part':'훈장','item_equipment_slot':'훈장','item_name':n}]
EQ={'oc1':{'preset_no':3,'item_equipment':M('THE RED'),'item_equipment_preset_1':M('THE RED'),'item_equipment_preset_2':M('THE RED'),'item_equipment_preset_3':M('프리미엄 PC방')},
    'oc2':{'item_equipment':M('THE RED'),'item_equipment_preset_1':M('THE RED'),'item_equipment_preset_2':[],'item_equipment_preset_3':M('카오스 벨룸 킬러')},
    'oc3':{'item_equipment':M('프리미엄 PC방'),'item_equipment_preset_1':M('프리미엄 PC방')},'oc4':{'item_equipment':M('프리미엄 PC방')}}
def nexon(route):
    u=up.urlparse(route.request.url); q=dict(up.parse_qsl(u.query))
    if u.path.endswith('/character/item-equipment'): return route.fulfill(status=200,content_type='application/json',body=json.dumps(EQ[q['ocid']]))
    return route.fulfill(status=200,content_type='application/json',body='{}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1280,390):
        pg=b.new_page(viewport={'width':w,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
        pg.route('https://open.api.nexon.com/**',nexon)
        pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
        pg.evaluate("syncAll({silent:true})"); pg.wait_for_timeout(2500)
        flagged=pg.evaluate("[...document.querySelectorAll('.char[data-id]')].filter(e=>e.querySelector('.medalwarn')).map(e=>e.dataset.id)")
        check(f'{w}: flagged = preset-only c1 + current c3 (hidden c4 not shown, clean c2 not)', sorted(flagged)==['c1','c3'], flagged)
        if w==1280:
            check('text', pg.inner_text('.char[data-id=c1] .medalwarn').strip()=='훈장 잘못 착용중')
            check('title names the preset', '프리셋 3' in pg.get_attribute('.char[data-id=c1] .medalwarn','title'))
            st=pg.evaluate("(()=>{const e=document.querySelector('.char[data-id=c1] .medalwarn'), cs=getComputedStyle(e), a=getComputedStyle(e,'::after'); return [cs.pointerEvents,cs.position,cs.animationName,a.animationName,a.animationDuration]})()")
            check('overlay: click-through, absolute, fade + fast shine loop', st[0]=='none' and st[1]=='absolute' and st[2]=='mwFade' and st[3]=='mwShine' and float(st[4][:-1])<=1, st)
            h0=pg.evaluate("document.querySelector('.char[data-id=c2]').getBoundingClientRect().height"); h1=pg.evaluate("document.querySelector('.char[data-id=c1]').getBoundingClientRect().height")
            check('layout unchanged (same card height)', abs(h0-h1)<1, (h0,h1))
            pg.click('.char[data-id=c1] .nm'); pg.wait_for_timeout(300)
            check('card still clickable', pg.evaluate("S.activeId")=='c1')
            pg.wait_for_timeout(300); pg.locator('aside').first.screenshot(path='/workspace/maple-boss-tracker/oct12x_b86_test_sidebar.png')
            pg.wait_for_timeout(1500); pg.locator('aside').first.screenshot(path='/workspace/maple-boss-tracker/oct12x_b86_test_sidebar_faded.png')
            saved=pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters.find(c=>c.id==='c2').medal")
            check('clean char stored bad=false', saved and saved['bad']==False, saved)
        else:
            pg.screenshot(path='/workspace/maple-boss-tracker/oct12x_b86_test_mobile.png')
        pg.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
