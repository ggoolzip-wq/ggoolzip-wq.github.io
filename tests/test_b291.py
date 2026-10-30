# test_b291 (사용자 규칙): 보스 보상 맵 18개만 읽음. 보상 맵 이름(+<난이도>)일 때만 보스를 정하고 아이템 기록.
#   입구·전투 맵·마을·지역 이름만·소울 조각 로그 → 보스 안 바뀜, 보스가 없으면 기록 안 함.
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b290')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/png;base64,'+base64.b64encode(open(os.path.join(FX,n+'.png'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save&&save(); render();
 window._T=1e7; const D0=Date.now; Date.now=()=>window._T; window.arItemScan=async()=>[]; window.arFindIcons=async()=>[]; ARX.stream=null; ARX.det={cid:'',boss:'',diff:'',src:''};
 window._img=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); g.fillStyle='#223'; g.fillRect(0,0,1920,1080); g.drawImage(im,0,0); return cv; };
 window._step=async(u,dt)=>{ window._T+=dt; await arFrame2(await _img(u),true); return [ARX.det.boss,ARX.det.diff]; };
 return 1; }"""
REWARD=[('블랙헤븐 고요해진 함선 <하드>','lotus','hard'),('타락한 세계수 세계수 정상 <하드>','damien','hard'),('라무라무 계곡 고요한 제단 <카오스>','slime','chaos'),
 ('레헬른 악몽의 시계탑 <하드>','lucid','hard'),('에스페라 바스러지는 빛 <하드>','will','hard'),('문브릿지 공허의 눈 <카오스>','dusk','chaos'),
 ('고통의 미궁 욕망의 제단 <하드>','jinhilla','hard'),('리멘 끝에 가까운 곳 <하드>','dunkel','hard'),('리멘 존재하지 않는 공간 <하드>','blackmage','hard'),
 ('세르니움 왕궁 메인홀 <하드>','seren','hard'),('카로테 카로테 마천루 <미지>','kalos','easy'),('증명의 전장 의지가 증명된 자리 <노멀>','adversary','normal'),
 ('도원경 빛을 되찾은 사계 <이지>','kaling','easy'),('검은 바다 잠든 환상 <하드>','star','hard'),('솔라톰 골짜기 솔라톰의 유산 <미지>','bellona','easy'),
 ('카르시온 해방된 나무 정상 <노멀>','limbo','normal'),('탈라하트 폭풍이 사그라든 여명 <노멀>','baldrix','normal'),('기어드락 적막한 용광로 <노멀>','jupiter','normal')]
OTHER=['고통의 미궁\n욕망의 제단 입구','~ | 공허의 눈 앞','개! 격전의 마천루 <노멀>','개울. 라무라무 신전 :카오스>','사계가 머무는 누각','의지가 시작되는 곳','거울에 비친 빛의 신좌',
 '도원경','리멘','레헬른','에스페라 회절의 회랑 <하드>','증명의 전장 물러서지 않는 용기 <노멀>','카로테 격전의 마천루 <노멀>','루타비스 여왕의 성 <카오스>','헤네시스']
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    D=lambda t: pg.evaluate("t=>arDetectBoss(t)",t)
    check('보상 맵 18개',pg.evaluate("AR_REWARD.length")==18 and pg.evaluate("typeof AR_MAPS")=='undefined')
    for t,bo,di in REWARD:
      r=D(t); check(f'보상 맵 {t!r} → {bo} {di}',r and r['boss']==bo and r['diff']==di,r)
    for t in OTHER:
      r=D(t); check(f'다른 맵 무시 {t!r}',r is None,r)
    # 보스 없음 + 다른 맵 → 기록 안 함
    s=pg.evaluate("""async()=>{ ARX.det={cid:'',boss:'',diff:'',src:''}; const o=arOcr; window.arOcr=async()=>'카로테 격전의 마천루 <노멀>'; await arFrame2(document.createElement('canvas'),true);
      const c=document.createElement('canvas'); c.width=1920; c.height=1080; window._T+=500; await arFrame2(c,true); const b0=ARX.det.boss; const n0=ARX.log.length; arRecord('r_white',.9,'공중'); const rec0=ARX.log.length>n0;
      window.arOcr=async()=>'카로테 카로테 마천루 <노멀>'; window._T+=500; await arFrame2(c,true); const b1=[ARX.det.boss,ARX.det.diff];
      window.arOcr=async()=>'카로테 격전의 마천루 <카오스>'; window._T+=500; await arFrame2(c,true); const b2=[ARX.det.boss,ARX.det.diff]; window.arOcr=o; return {b0,rec0,b1,b2}; }""")
    check('전투 맵만 → 보스 없음, 기록 안 함',s['b0']=='' and not s['rec0'],s)
    check('보상 맵 → 칼로스 노멀, 다시 전투 맵(카오스) 읽혀도 안 바뀜',s['b1']==['kalos','normal'] and s['b2']==['kalos','normal'],s)
    pg.evaluate("()=>{ ARX.det={cid:'',boss:'',diff:'',src:''}; arSoulHint('소비 아이템을 얻었습니다 (벨로나의 소울 조각)'); }")
    check('소울 조각 로그로 보스 안 정함',pg.evaluate("ARX.det.boss")=='')
    pg.evaluate("()=>{ ARX.det={cid:'',boss:'',diff:'',src:''}; }")
    r1=pg.evaluate("u=>_step(u,500)",u('v11_0421')); check('v11 #421 실제 OCR → 카링 이지',r1==['kaling','easy'],r1)
    r2=pg.evaluate("u=>_step(u,500)",u('v11_0691')); check('v11 #691 진 힐라 입구 → 무시 (카링 이지 유지)',r2==['kaling','easy'],r2)
    r3=pg.evaluate("u=>_step(u,500)",u('v02_0181')); check('v02 진 힐라 보상 맵 실제 OCR → 진 힐라 하드',r3==['jinhilla','hard'],r3)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
