# test_b301 (t523): 해상도 프로필 자동 감지 — 사용자 기준 스크린샷 20장(왼쪽 아래 Lv 바 부분만 fixture) → 5개 프로필
#   · 같은 해상도(1920·2560)에서 기본/최적 비율을 UI 크기로 구분 · 모르는 해상도는 가까운 프로필 배율 + '(추정)'
#   · 프로필 고정 영역(인벤·창고·창고 옆 인벤 메소) · '영역 숨기기' 옆 라벨 · 네온 버튼 스타일(다크/라이트)
import os, sys, json, base64, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','t523')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
meta=json.load(open(os.path.join(FX,'meta.json')))
du=lambda f:'data:image/png;base64,'+base64.b64encode(open(os.path.join(FX,f),'rb').read()).decode()
cases=[(n,meta[str(n)][0],meta[str(n)][1],du('bl%02d.png'%n)) for n in range(1,21)]
EXP=['1366']*4+['1920o']*4+['1920b']*4+['2560b']*4+['2560o']*4
DET="""async ([w,h,u])=>{ const A=window.AR; const im=new Image(); await new Promise(r=>{im.onload=r; im.src=u;});
  const cv=document.createElement('canvas'); cv.width=w; cv.height=h; const g=cv.getContext('2d'); g.fillStyle='#000'; g.fillRect(0,0,w,h); g.drawImage(im,0,h-im.height);
  A.bbox=null; A.bbKey=''; A.prof=null; A.geo=null; const P=await arProfDetect(cv); const R=k=>{ const r=arR(k,cv); return [Math.round(r.x*w),Math.round(r.y*h),Math.round(r.w*w),Math.round(r.h*h)]; };
  return P?{id:P.id,s:P.s,lab:P.lab,est:P.est,sc:P.score,inv:R('inv'),sto:R('sto'),stoInv:R('stoInv'),name:R('name'),log:R('log')}:null; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    got={}
    for (n,w,h,u),e in zip(cases,EXP):
      r=pg.evaluate(DET,[w,h,u]); got[n]=r
      check(f'{n:02d}번 {w}x{h} → {e}',bool(r) and r['id']==e and not r['est'],r)
    LAB={'1366':'1366 x 768','1920o':'1920 x 1080(최적 비율)','1920b':'1920 x 1080(기본 비율)','2560b':'2560 x 1440(기본 비율)','2560o':'2560 x 1440(최적 비율)'}
    check('라벨 형식 "1920 x 1080(최적 비율)"',all(got[n] and got[n]['lab']==LAB[EXP[n-1]] for n in got),[got[n]['lab'] for n in (1,5,9,13,17)])
    # 고정 영역 (스크린샷 실측 px)
    M={1:([550,538,272,26],[635,582,200,30]),5:([728,674,272,26],[830,728,200,30]),9:([773,757,382,37],[776,804,281,42]),13:([1031,1009,510,49],[1037,1073,375,56]),17:([100,1012,544,52],[1020,1096,400,60])}
    for n,(inv,sto) in M.items(): check(f'{n:02d}번 프로필 인벤/창고 메소 고정 영역',got[n]['inv']==inv and got[n]['sto']==sto,(got[n]['inv'],got[n]['sto']))
    check('기본 비율 UI 영역 = 1366 배치 × 배율 (닉네임 높이 28×1.40625)',got[9]['name'][3]==int(28*1.40625+.5) and got[13]['name'][3]==int(28*1.875+.5),(got[9]['name'],got[13]['name']))
    # 모르는 해상도
    rb=pg.evaluate(DET,[1600,900,du('u1600b.png')]); ro=pg.evaluate(DET,[1600,900,du('u1600o.png')])
    check('1600x900 기본 비율(1366 화면 확대) → 기본 비율 추정',bool(rb) and rb['est'] and abs(rb['s']-900/768)<.01 and rb['lab']=='1600 x 900(기본 비율)(추정)',rb)
    check('1600x900 최적 비율(UI 1배) → 최적 비율 추정',bool(ro) and ro['est'] and ro['s']==1 and ro['lab']=='1600 x 900(최적 비율)(추정)',ro)
    check('추정 영역은 가까운 프로필 기준 화면 가운데 + UI px × 배율 (창고 메소 dx -130·dy 188 UI px)',ro and abs(ro['sto'][0]-(800-130))<=2 and abs(ro['sto'][1]-(450+188))<=2,ro and ro['sto'])
    # UI: 라벨 + 네온 버튼
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'")
      pg.click('#tabs [data-tab="auto"]'); pg.wait_for_timeout(400)
      okb=pg.evaluate("""()=>{ const b=document.querySelector('#arGuide [data-arg="ok"]'); if(!b) return null; const cs=getComputedStyle(b); return {bg:cs.backgroundImage,sh:cs.boxShadow,r:cs.borderRadius}; }""")
      check(f'{th}: 안내창 확인 버튼 네온(그라디언트 테두리·빛)',bool(okb) and 'gradient' in okb['bg'] and okb['sh']!='none' and okb['r'].startswith('999'),okb)
      pg.evaluate("document.querySelector('#arGuide').hidden=true; const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; window.AR.testSrc=cv; window.AR.stream={getTracks:()=>[]}; window.AR.prof={id:'1920o',lab:'1920 x 1080(최적 비율)',s:1,gw:1920,gh:1080}; arPanel(true); arPanelPaint();")
      r=pg.evaluate("""()=>{ const b=document.querySelector('#arPanel .ar-roib'), l=document.querySelector('#arPanel .ar-prof'), a=document.querySelector('#addCharBtn');
        return {lab:l&&l.textContent, next:!!(b&&b.nextElementSibling===l), roiBg:b&&getComputedStyle(b).backgroundImage, addBg:a&&getComputedStyle(a).backgroundImage}; }""")
      check(f'{th}: 영역 숨기기 옆 라벨',r['lab']=='1920 x 1080(최적 비율)' and r['next'],r)
      check(f'{th}: 영역 버튼·캐릭터 추가 버튼 네온',r['roiBg'] and 'gradient' in r['roiBg'] and r['addBg'] and 'gradient' in r['addBg'],r)
      pg.evaluate("window.AR.stream=null; window.AR.testSrc=null; window.AR.prof=null")
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs)
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails else 0)
