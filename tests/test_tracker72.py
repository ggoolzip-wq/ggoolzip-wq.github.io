# b98: 동기화 충돌 — 넥슨 API 자동 값(medal·guildAt·guild)은 '어느 데이터를 쓸까요?'에 나오지 않고 자동 병합 (훈장은 최근 확인, guildAt 은 큰 값)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=8897
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
def ch(**k): return {'id':'c1','name':'랑트킹','level':280,'job':'히어로','world':'스카니아','ocid':'o1','accId':'a1','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{},**k}
def st(c): return {'version':5,'characters':[c],'settings':{'accounts':[{'id':'a1','label':'본'}]},'history':[],'monthHistory':[]}
B=st(ch(medal={'bad':False,'where':[],'at':1},guildAt=1,guild='A'))
L=st(ch(medal={'bad':True,'where':['프리셋 2'],'at':300},guildAt=500,guild='A'))
R=st(ch(medal={'bad':False,'where':[],'at':200},guildAt=900,guild='B'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.wait_for_timeout(500)
    for base in (True,False):
      r=pg.evaluate("([b,l,r,base])=>{ const ctx={base,prefer:'l',conf:[]}; const m=gdMerge(base?b:null,l,r,ctx); return {conf:ctx.conf.length, c:m.characters[0]}; }",[B,L,R,base])
      check(f'base={base}: no conflict for medal/guildAt/guild', r['conf']==0, r)
      check(f'base={base}: medal = newer check (at 300), guildAt = max 900', r['c']['medal']['at']==300 and r['c']['guildAt']==900, r['c'])
    check('auto fields not in compare signature', pg.evaluate("([l,r])=>gdSig(l)===gdSig(r)",[st(ch(medal={'bad':True,'at':5},guildAt=3)),st(ch(medal={'bad':False,'at':9},guildAt=7))]))
    r=pg.evaluate("([b,l,r])=>{ const ctx={base:true,prefer:'l',conf:[]}; gdMerge(b,l,r,ctx); return ctx.conf.length; }",[st(ch(name='a')),st(ch(name='b')),st(ch(name='c'))])
    r2=pg.evaluate("([b,l,r])=>{ const ctx={base:true,prefer:'l',conf:[]}; const m=gdMerge(b,l,r,ctx); return [ctx.conf.length,m.characters[0].level]; }",[st(ch(level=200)),st(ch(level=200)),st(ch(level=210))])
    check('manual level edit still merges normally (other side edit kept)', r2==[0,210], r2)
    check('real user field (name) conflict still asked', r>0, r)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
