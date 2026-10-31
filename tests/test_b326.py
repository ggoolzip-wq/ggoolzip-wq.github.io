# test_b326 (t603): 보상 맵 인식 래치 — 처음 보상 상자로 '보상 인식 중'이 되면 보상 맵 이름이 '다른 맵 이름'으로 연속 2번 읽힐 때까지 유지. 검은 화면·잘림·오독(자리→파리)은 유지. 카드 = 초록 '보상 인식 중'+보스 / 아니면 '-'
# from b309 (t551/t552): 목록에 없는 닉네임 → 캐릭터 '-' · 기록 대상 없음 / 검은 화면·못 읽음 → 직전 유지 / 상태바 안내 문구 제거
# (was b307): '현재 보스' 상태 — 대기 맵=노란 '대기 중', 전투 맵=빨간 '진행 중', 보상 맵+상자=초록 '보상 인식 중'. 대기/진행 중에도 보스·난이도 표시, 기록은 보상 인식 중만
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; save(); S.tab='auto'; renderAuto(); }"""
ST="""(t)=>{ const A=window.AR; if(t!==null) arRwlCheck(t); const s=arBossState(); arLivePaint(); const e=document.querySelector('#arPanel .ar-cboss .ar-b'); return {st:s, boss:A.det.boss, ok:arBoxOk(), html:e?e.innerText.trim():null, h2:(document.querySelector('#arPanel .ar-cboss h2')||{}).textContent}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    a=pg.evaluate(ST,None); check("카드 제목 '보상 맵 인식' · 평소 '-'", a['h2']=='보상 맵 인식' and a['html']=='-' and a['st']!='rew', a)
    pg.evaluate("()=>{ const A=window.AR; A.det.boss='adversary'; A.det.diff=''; A.rew={boss:'adversary',diff:'',hash:null}; }")
    a=pg.evaluate(ST,None); check('보상 상자 → 보상 인식 중 + 보스 이름', a['st']=='rew' and '보상 인식 중' in a['html'] and pg.evaluate("findBoss('adversary').name") in a['html'], a)
    pg.evaluate("()=>{ const A=window.AR; A.rew=null; A.lock=null; A.box=null; A.det.boss=''; }")
    for t in ['','  ','ㅠㅜ','증명의 전장 의지가 증명된 파리 <011>','의지가 증명된','헤네시스','의지가 증명된 자리']:
      a=pg.evaluate(ST,t); check(f'읽기 {t!r} → 유지 (락·상자 꺼져도)', a['st']=='rew' and a['boss']=='adversary' and a['ok'], a)
    a=pg.evaluate(ST,'헤네시스 시장'); check('다른 맵 이름 1번 → 아직 유지', a['st']=='rew', a)
    a=pg.evaluate(ST,''); check('사이 검은 화면 → 유지', a['st']=='rew', a)
    a=pg.evaluate(ST,'헤네시스 시장'); check("다른 맵 이름 연속 2번 → '-'", a['st']!='rew' and a['boss']=='' and a['html']=='-', a)
    pg.screenshot(path=os.path.join(OUT,'b326_end.png'))
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
