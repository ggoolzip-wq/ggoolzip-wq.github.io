# test_b328_box (t625): 보상맵 영상 9개 득템 기록 점검에서 나온 수정
#  1) 듄켈 보상맵 '끝에'→':메' 오독 → 맵 이름 실패 → 상자 검사 안 함 : <난이도> 꼬리표 + 고유한 끝 4글자면 .8로 인정
#  2) 진힐라·듄켈 상자가 캐릭터/이펙트에 가려 전체 NCC .53~.72 : 가려지지 않은 절반 점수(-.1)로 인정
#  3) 세렌 '세르니움 왕궁 메인홀'이 '황궁 메민홀'로 읽혀 래치가 풀림 → 맵 인식으로 같은 보스 보상맵이면 유지
#  4) 대적자: 전투→보상맵 바뀜을 2번째 읽기까지 기다려 13.6~14.5초에만 보인 상자를 놓침 → 같은 보스 정확 일치면 바로
#  5) 잡템(큐브·결정 AR_REWX)은 기본 기록 후보에서 제외
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b328')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n+'.jpg'),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']:
    if os.path.isdir(os.path.join(ROOT,d)): shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SC="""async ([src,k,part])=>{ const im=new Image(); im.src=src; await im.decode(); ARX.cfg.boxPart=part; const s=await arBoxScore(im,k); ARX.cfg.boxPart=undefined; return [s,AR_BOX[k].thr]; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    D=lambda s: pg.evaluate("t=>{const d=arDetectBMap(t); return d?[d.boss,d.diff,d.kind]:null}",s)
    r=D('ㅜ ]멘 :메 가까운 곳 <하드>'); check('듄켈 오독(:메) + <하드> → dunkel hard 보상',r and r[0]=='dunkel' and r[1]=='hard' and 'r' in r[2],r)
    r=D('ㅜ ]멘 :메 가까운 곳'); check('꼬리표 없으면 인정 안 함',r is None,r)
    r=D('리멘 끝에 가까운 곳 앞'); check('듄켈 대기맵은 그대로 대기',r and 'w' in r[2],r)
    a=pg.evaluate(SC,[u('v3_jinhilla'),'jinhilla',False]); c=pg.evaluate(SC,[u('v3_jinhilla'),'jinhilla',None])
    check(f'진힐라 가려진 상자: 전체만 {a[0]:.3f} < 문턱',a[0]<a[1],a); check(f'진힐라 절반 점수 포함 {c[0]:.3f} ≥ 문턱',c[0]>=c[1],c)
    c=pg.evaluate(SC,[u('v5_dunkel'),'dunkel',None]); check(f'듄켈 상자(맵 인식되면 검사됨) {c[0]:.3f} ≥ 문턱',c[0]>=c[1],c)
    c=pg.evaluate(SC,[u('v4_adversary'),'adversary',None]); check(f'대적자 상자(14.2초) {c[0]:.3f} ≥ 문턱',c[0]>=c[1],c)
    for k in ['jinhilla','dunkel','seren','will','adversary']:
        c=pg.evaluate(SC,[u('v4_fight'),k,None]); check(f'전투 화면(상자 없음) {k} {c[0]:.3f} < 문턱',c[0]<c[1],c)
    r=pg.evaluate("""()=>{ ARX.rwl={boss:'seren',names:['왕궁 메인홀']}; const a=arRwlSim(']르니움 황궁 메민홀 <하드>'), z=arRwlSim('리멘 끝에 가까운 곳 <하드>'); ARX.rwl=null; return [a,z]; }""")
    check('세렌 래치: 황궁/메민홀 오독도 유지(1), 다른 보스 맵은 낮음',r[0]==1 and r[1]<.3,r)
    r=pg.evaluate("""()=>{ ARX.mapSt=null; ARX.mapPend=null; ARX.rew=null; ARX.rwl=null; arMapState('명의 전장 : 전설로 거듭나는 운명 <미지>',1000); arMapState('명의 전장 : 전설로 거듭나는 운명 <미지>',1100);
      const a=ARX.mapSt&&ARX.mapSt.kind; arMapState('명의 전장 : 의지가 증명된 자리 <미지>',1200); const b=ARX.mapSt&&ARX.mapSt.kind;
      arMapState('리멘 끝에 가까운 곳 앞',1300); const c=ARX.mapSt&&ARX.mapSt.boss; ARX.mapSt=null; return [a,b,c]; }""")
    check('같은 보스 전투→보상맵(정확 일치)은 한 번 읽기로 바로 보상맵, 다른 보스는 2번',r[0]=='b' and r[1]=='r' and r[2]=='adversary',r)
    r=pg.evaluate("()=>{ ARX.cfg.rewx=undefined; return [AR_REWX.length, /ARX\\.cfg\\.rewx===true/.test(arCandidates.toString())]; }")
    check('잡템(AR_REWX) 기본 제외',r[1],r)
    r=pg.evaluate("()=>{ const miss=[]; for(const b of BOSSES) for(const d of b.diffs) for(const k of dropsFor(b,d)) if(!ITEM_ICONS[k]&&!miss.includes(k)) miss.push(k); return miss; }")
    check('드랍 테이블 아이템 아이콘 모두 있음',not r,r)
    r=pg.evaluate("()=>['r_green','r_red','r_black','r_white','r_life'].filter(k=>!ITEM_ICONS[k])"); check('반지 상자 아이콘',not r,r)
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs[:3])
print('\nRESULT', 'FAIL' if fails else 'PASS', fails); sys.exit(1 if fails else 0)
