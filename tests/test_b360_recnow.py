# test_b360 (t672): 보스 득템 자동 기록의 [저장/기록] = 캐릭터 정보창 [저장]과 같은 즉시 확정 (저장 대기 pend 안 남김)
#   (1) 메인(PIP 없음) 자동 기록 → 바로 localStorage·서버 저장 호출, pend 없음  (2) PIP 수익 기록 [기록하기] → 수익까지 확정
#   (3) PIP 반지 고르기 / 칠흑 고르기 → 확정  (4) 손으로 누른 보스 목록 칩은 예전처럼 저장 대기(회귀)
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save();
 window.__push=0; const o=svPushBg; svPushBg=function(){ __push++; }; }"""
LS="()=>{ const d=JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEY)); return d.characters[0]; }"
def keyof(pg,item):
    return pg.evaluate("""(it)=>{ for(const b of BOSSES){ for(const d of Object.keys(b.drops||{})){ if((b.drops[d]||[]).includes(it)) return b.id+'|'+it; } } const b=BOSSES.find(b=>JSON.stringify(b).includes('"'+it+'"')); return b?b.id+'|'+it:null; }""",item)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(200)
    # 보상 키 고르기: 아무 보스의 일반 아이템·반지·칠흑 상자
    K={'n':'kaling|se1','ring':'kaling|r_white','cb':'kaling|chaosbox'}
    check('테스트용 키 찾음',K.get('n') and K.get('ring') and K.get('cb'),K)
    # (1) 메인 자동 기록
    r=pg.evaluate("""(key)=>{ recAuto(()=>changeDrop(key,+1)); const bb=document.querySelector('[data-bb="w"]'); if(bb) bb.click(); return {pend:!!pend,push:__push}; }""",K['n'])
    pg.wait_for_timeout(300)
    c=pg.evaluate(LS)
    check('메인 자동 기록 → 저장 대기 없이 바로 확정', (not r['pend']) and (c.get('drops',{}).get(K['n'])==1 or json.dumps(c).count(K['n'])>0) and r['push']>=1, (r,K['n']))
    pg.evaluate("()=>document.querySelectorAll('.modal.show,.rvmodal,.cbmodal').forEach(e=>e.remove())")
    # (4) 회귀: 손으로 누른 칩 = 저장 대기
    r=pg.evaluate("""(key)=>{ const c=activeChar(); c.drops={}; pend=null; save(); changeDrop(key,+1); document.querySelector('[data-bb="w"]')?.click(); const st=!!pend; pendCancel(true); return st; }""",K['n'])
    check('손으로 누른 보스 목록 칩은 예전처럼 저장 대기',r)
    pg.evaluate("()=>document.querySelectorAll('.rvmodal,[class*=rv]').forEach(e=>{ if(e.classList.contains('modal')||e.id) {} })")
    # PIP 흉내
    pg.evaluate("""async()=>{ const f=document.createElement('iframe'); f.id='fakePip'; document.body.append(f); await new Promise(r=>setTimeout(r,50)); const card=f.contentDocument.createElement('div'); f.contentDocument.body.append(card); ARX.pip={win:f.contentWindow,card}; const c=activeChar(); c.drops={}; c.drev={}; pend=null; save(); __push=0; }""")
    pg.wait_for_timeout(100)
    r=pg.evaluate("""(key)=>{ const c=activeChar(), b=findBoss(key.split('|')[0]); const ok=arSaleTake(c,b,key,key.split('|')[1]); const p1=!!pend; const d=ARX.pip.win.document, el=d.querySelector('.ar-pipsale'); el.querySelector('.ar-psamt').value='3'; arSaleDo(el,'ok'); return {ok,p1,p2:!!pend,push:__push}; }""",K['n'])
    c=pg.evaluate(LS)
    check('(2) PIP 수익 [기록하기] → 득템·수익 바로 확정',r['ok'] and not r['p1'] and not r['p2'] and r['push']>=1 and K['n'] in json.dumps(c.get('drev',{})),(r,c.get('drev')))
    r=pg.evaluate("""(key)=>{ const c=activeChar(), b=findBoss(key.split('|')[0]); arSaleTake(c,b,key,key.split('|')[1]); const q=ARX.saleQ[0]; arSalePick(q,'r4'); return {p:!!pend,push:__push}; }""",K['ring'])
    c=pg.evaluate(LS)
    check('(3) PIP 반지 고르기 → 바로 확정',not r['p'] and K['ring'] in json.dumps(c),(r))
    pg.evaluate("()=>{ ARX.saleQ=[]; arPipSale(); }")
    r=pg.evaluate("""(key)=>{ const c=activeChar(), b=findBoss(key.split('|')[0]); arSaleTake(c,b,key,key.split('|')[1]); const q=ARX.saleQ[0]; arSalePick(q,CHAOS_PICK[0]); return {p:!!pend}; }""",K['cb'])
    c=pg.evaluate(LS)
    check('(3) PIP 칠흑 고르기 → 바로 확정',not r['p'] and K['cb'] in json.dumps(c),(r))
    # 고르기 전 [기록하지 않기] = 아무것도 안 남김
    r=pg.evaluate("""()=>{ const c=activeChar(); c.drops={}; c.dropOut={}; c.chaosOut={}; pend=null; save(); const key=%s; const b=findBoss(key.split('|')[0]); arSaleTake(c,b,key,key.split('|')[1]); const el=ARX.pip.win.document.querySelector('.ar-pipsale'); arSaleDo(el,'skip'); return !!pend; }"""%json.dumps(K['ring']))
    check('고르기 전 [기록하지 않기] → 저장 대기 안 남음',not r)
    b.close()
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
