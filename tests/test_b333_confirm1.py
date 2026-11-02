# test_b333 (t638): 아이템 아이콘 1번만 보여도 확정(confirm 1), 같은 자리 다시 보이면 중복 기록 안 함, 저장된 confirm:2 → 1
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
T="""()=>{ const A=window.AR, P=[]; const o=window.arPick; window.arPick=(h,via)=>P.push(h.k+'/'+via); A.cfg.on=true; A.tracks=[]; const t=1e6;
 A.mapSt={boss:'seren',kind:'brw',diff:'hard'}; A.mapText='왕궁 메인홀 <하드>';
 arTrack([{k:'mitra',x:900,y:500,score:.9,air:true}],1080,t); const a=P.length;
 arTrack([{k:'mitra',x:930,y:520,score:.9,air:true}],1080,t+100); arTrack([{k:'mitra',x:950,y:510,score:.9,air:true}],1080,t+1500); const b=P.length;
 arTrack([{k:'r_white',x:300,y:900,score:.9}],1080,t+1600); const c=P.length;
 A.mapText=''; arTrack([{k:'eye',x:500,y:500,score:.74,air:true}],1080,t+2000); const d=P.length; arTrack([{k:'eye',x:510,y:500,score:.74,air:true}],1080,t+2100); const e=P.length;
 window.arPick=o; return {conf:A.cfg.confirm,a,b,c,d,e,P}; }"""
try:
  with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=br.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    r=pg.evaluate(T)
    check('기본 confirm 1',r['conf']==1,r)
    check('1번 보이면 바로 기록',r['a']==1,r)
    check('같은 자리 다시 보여도 중복 기록 없음',r['b']==1,r)
    check('다른 아이템은 따로 1번 기록',r['c']==2,r)
    check('맵 이름 빈 칸(이동 중)이면 1번으론 안 기록, 2번이면 기록',r['d']==2 and r['e']==3,r)
    k=pg.evaluate("AR_KEY"); pg.evaluate("k=>localStorage.setItem(k,JSON.stringify({confirm:2}))",k); pg.reload(); pg.wait_for_timeout(800)
    check('저장된 confirm:2 → 1 로 바뀜',pg.evaluate("window.AR.cfg.confirm")==1)
    pg.evaluate("k=>{ const c=JSON.parse(localStorage.getItem(k)||'{}'); c.v333=1; c.confirm=3; localStorage.setItem(k,JSON.stringify(c)); }",k); pg.reload(); pg.wait_for_timeout(800)
    check('바뀐 뒤 사용자가 다시 정한 값은 유지',pg.evaluate("window.AR.cfg.confirm")==3)
    br.close()
finally: srv.kill()
check('페이지 오류 없음',not errs,errs)
print('FAILS',fails); sys.exit(1 if fails else 0)
