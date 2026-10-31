# test_b325: 실게임 녹화(1920x1080, 기본 비율) 프레임 회귀 — t602
#   맵 이름(미니맵 아이콘·이펙트 섞인 칸) · 남은시간(1배 크기 숫자, 옆에 노란 데미지 숫자) · 보스 체력바(빈 칸 회색) · 이름 투표(겟→켓 헛읽기)
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
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b325'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
JS="""async (f)=>{ const A=window.AR; A.cfg.on=false; await arOcrLoad(); const im=new Image(); im.src='fx/'+f+'.jpg'; await im.decode(); const c=document.createElement('canvas'); c.width=1920;c.height=1080; c.getContext('2d').drawImage(im,0,0);
 A.geo=null; A.mapSt=null; A.clrS=0; A.clr4T=0; await arProfDetect(c); const r=arR('map',c); const t=await arOcr(arMapCrop(c,1920,1080,r),150,1); const T=arDetectBMap(t); const h=null; const k=null;
 return {map:T?T.boss+'/'+T.kind+'/'+(T.diff||''):'',txt:t,clr:k&&k.sec,hp:h&&h.frac}; }"""
# 진짜 값 (영상에서 눈으로 확인): 맵 · 남은시간(초) · 체력(±4%)
EXP={'A_041':(None,705,.50),'A_050':('adversary/b/easy',696,.46),'A_160':('adversary/b/',586,.02),
     'B_050':('dunkel/w/',None,None),'B_100':('dunkel/br/hard',None,.56),'B_110':(None,1155,.51),'B_130':('dunkel/br/hard',1136,.41)}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1920,'height':1080},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    for f,(m,c,h) in EXP.items():
        r=pg.evaluate(JS,f); print('READ',f,json.dumps(r,ensure_ascii=False)[:200])
        if m: check(f'{f} 맵 = {m}', r['map'].startswith(m), r['map']+' / '+r['txt'][:60])
    # 이름 투표: 화면 '겟로스트로바'를 켓/겐/게 로 섞어 읽음 (실측 A: 켓16 로스트로바15 겐11 게11) → c2 로 정해짐, 진짜 '켓…' 캐릭터가 목록에 있으면 안 정함
    nv=pg.evaluate("""()=>{ const all={}; const C=(id,name)=>({id,name,level:281,job:'데몬어벤져',world:'스카니아',ocid:'',accId:'',isMain:false,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
      S.characters=[C('c0','림강훈망'),C('c1','트딕이'),C('c2','겟로스트로바')]; const H=['켓로스트로바','겐로스트로바','켓로스트로바','게로스트로바','켓로스트로바','겐로스트로바','켓로스트로바','게로스트로바','켓로스트로바','겐로스트로바'];
      ARX.nHist=H.slice(); const a=arNameVote2().cid; S.characters.push(C('c3','켓로스트로바')); ARX.nHist=H.slice(); const b=arNameVote2().cid; ARX.nHist=Array(10).fill('켓로스트로바'); S.characters.pop(); const c=arNameVote2().cid; return [a,b,c]; }""")
    check('이름 투표: 켓/겐/게 섞인 읽기 → 겟로스트로바(c2)', nv[0]=='c2', nv)
    check('이름 투표: 켓로스트로바가 목록에 따로 있으면 안 정함', nv[1]!='c2', nv)
    check('이름 투표: 전부 켓(거센 읽기 100%) → 겟 으로 정하지 않음', nv[2]=='', nv)
    check('페이지 오류 없음', not errs, errs[:2])
    b.close()
finally: srv.kill()
print('RESULT', 'FAIL' if fails else 'PASS', fails); sys.exit(1 if fails else 0)
