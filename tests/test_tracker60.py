import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8864=_tutil.free_port()
# b82: 모든 합계·표·차트 = 보이는(키 등록된) 캐릭터만 (기록은 유지, 키 다시 넣으면 합계 복귀)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8864
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(id,name): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}

def ch(id,name,acc): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','image':'','accId':acc,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
def pc(id,name,meso,item): return {'id':id,'name':name,'meso':meso,'count':1,'bosses':['루시드(하드)'],'bvals':[meso],'items':{f'lucid|{item}':1},'revs':{f'lucid|{item}':{'m':meso//10,'a':1,'p':1,'i':item}}}
H=[{'week':'2026-09-28','total':15000000000,'cleared':2,'crystals':2,'items':2,'perChar':[pc('c1','보이는캐',10000000000,'belt'),pc('c2','숨는캐',5000000000,'eye')]}]
ST={'version':5,'theme':'dark','activeId':'c1','startWeek':'2026-09-28','history':H,'monthHistory':[],'worldOrder':[],'characters':[ch('c1','보이는캐','a1'),ch('c2','숨는캐','a2')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True},{'id':'a2','label':'부','key':''}]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
    T=lambda: pg.evaluate("(()=>{const T=totalData(); return [T.wTotal-T.weeks[T.weeks.length-1].total, T.chars.map(c=>c.name), Object.keys(T.sales).sort(), T.items.map(x=>x[0]).sort()]})()")
    t=T(); check('hidden char excluded from totals/rank/sales/items', t[0]==11000000000 and t[1]==['보이는캐'] and t[2]==['belt#1'] and 'eye' not in ' '.join(t[3]), t)
    for tb in ('total','loot'):
        pg.evaluate(f"tab='{tb}'; render()"); pg.wait_for_timeout(200)
        txt=pg.inner_text('#view'); i=txt.find('마력이 깃든 안대'); print('CTX',tb,repr(txt[max(0,i-300):i+40]) if i>=0 else '', '숨는캐' in txt); check(f'{tb} tab: no hidden char name / item', '숨는캐' not in txt)
    pg.evaluate("tab='total'; render()"); pg.screenshot(path='/workspace/maple-boss-tracker/oct12t_b82_test_total.png')
    check('history data kept', pg.evaluate("S.history[0].perChar.length")==2)
    pg.evaluate("accounts()[1].key='live_K2_0123456789abcdefgh'; save(); render()")
    t=T(); check('key back → sums back', t[0]==16500000000 and sorted(t[1])==['보이는캐','숨는캐'] and t[2]==['belt#1','eye#1'], t)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
