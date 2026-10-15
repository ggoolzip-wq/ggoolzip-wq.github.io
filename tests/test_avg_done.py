# b176: 평균 = 끝난 주(월)만, 진행 중인 주 제외. 끝난 주 없으면 '집계 중'
import os, sys, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8931'; fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://**',lambda r:r.abort()); pg.route('**/feed.json*',lambda r:r.fulfill(status=200,body='{"version":1,"sources":{},"items":{}}'))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    R=pg.evaluate("""()=>{ const cw=S.period.week, prev=(k,n)=>{ const d=new Date(weekStartMs()-n*7*864e5+9*3600e3); return weekId(new Date(weekStartMs()-n*7*864e5+3600e3)); };
      S.characters=[{id:'x',name:'가',level:1,job:'',world:'스카니아',bosses:{},weekly:{},monthly:{},auto:{},sync:{},drops:{}}]; save(); const H=(w,m)=>({week:w,total:m,perChar:[{id:'x',name:'가',meso:m,items:{}}]}); const out={};
      S.history=[]; S.monthHistory=[]; out.none=doneAvgs(totalData()).grand; out.txt=avgTxt('주',out.none);
      const w1=weekId(weekStartMs()-13*864e5), w2=weekId(weekStartMs()-6*864e5); out.wk=[w1,w2,cw];
      S.history=[H(w1,700e8)]; out.one=doneAvgs(totalData()).grand;
      S.history=[H(w1,700e8),H(w2,600e8)]; out.two=doneAvgs(totalData()).wTotal; out.mon=doneAvgs(totalData()).mTotal;
      return out; }""")
    check('끝난 주 없음 → null, 집계 중', R['none'] is None and R['txt']=='주 평균 집계 중', R)
    check('1주 끝 → 700억 (진행 중인 주 제외)', R['wk'][0]!=R['wk'][1]!=R['wk'][2] and R['one']==700e8, R)
    check('2주 끝 → 650억', R['two']==650e8, R)
    check('끝난 달 없음 → 월 평균 null', R['mon'] is None, R)
    check('no page errors', not errs, errs[:3])
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails else 0)
