# test_b285: 실제 1인 보스 보상 상자 영상 10개(트딕이) — 미니맵 제목 → 보스·난이도 (보스 이름 없는 맵), 펼친 미니맵 배치,
#            v07 벨로나 이지 보상 로그 연속 프레임 → 백옥의 보스 반지 상자(r_white) 1번 기록 · 벨로나에 귀속, 번쩍이는 프레임에서 인식 유지
import os, sys, tempfile, shutil, subprocess, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PROBE=os.environ.get('PROBE')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
shutil.copytree(os.path.join(ROOT,'tests','fixtures','b285'),os.path.join(site,'fx'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  const C=(id,name,lv)=>({id,name,level:lv,job:'',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[C('c0','트딕이',285),C('c1','팬더데이',285),C('c2','터래플',289)]; S.activeId='c1'; save&&save(); render(); }"""
STEP="""async ([f,force,on])=>{ const im=new Image(); im.src='fx/'+f; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0);
  const A=window.AR; A.cfg.on=on; await arFrame(cv,force); const lg=await arLogFrame(cv)||[]; return {map:A.mapText,name:A.nameText,det:{...A.det},log:A.logText,new:lg.map(x=>x.k+'x'+x.n)}; }"""
RESET="()=>{const A=window.AR; A.logPrev=[]; A.recent={}; A.hits={}; A.counted=[]; A.infoSeen=[]; A.log=[]; A.det={cid:'',boss:'',diff:'',src:''}; A.detT=0; A.cidT=0;}"
TRUTH={'v01':('adversary','normal'),'v02':('jinhilla','hard'),'v03':('dunkel','hard'),'v04':('kalos','normal'),'v05':('dusk','chaos'),
       'v06':('slime','chaos'),'v07':('bellona','easy'),'v08':('seren','hard'),'v09':('kaling','easy'),'v10':('will','hard')}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("ARX.cfg.boxGate=false")  # t522: 이 테스트는 아이템 인식만 봄 — 보상 상자 게이트는 test_b300
    pg.evaluate(SETUP); pg.evaluate("arOcrLoad()"); pg.wait_for_function("window.AR.ocr||window.AR.ocrErr",timeout=60000)
    bad=[]; badc=[]
    for v,t in sorted(TRUTH.items()):
        pg.evaluate(RESET); r=pg.evaluate(STEP,['map_%s.jpg'%v,True,False])
        if PROBE: print(v,json.dumps(r,ensure_ascii=False)[:300])
        if (r['det']['boss'],r['det']['diff'])!=t: bad.append((v,r['det']['boss'],r['det']['diff'],r['map']))
    check('미니맵 제목 → 보스·난이도 10개 영상 모두 (보스 이름 없는 맵 · 펼친 미니맵 · <미지> 같은 OCR 변형)', not bad, bad)
    # v07 연속 프레임 (4fps): 보상 로그가 한꺼번에 쌓이고 화면이 보라색으로 번쩍임
    pg.evaluate(SETUP); pg.evaluate(RESET); seq=[]
    for i,f in enumerate(sorted(os.path.basename(x) for x in glob.glob(os.path.join(ROOT,'tests','fixtures','b285','v07_*.jpg')))):
        r=pg.evaluate(STEP,[f,i%4==0,True]); seq.append((f,r['det']['boss'],r['det']['diff'],r['new']))
        if PROBE: print(f,json.dumps(r,ensure_ascii=False)[:500])
    fin=pg.evaluate("({act:S.activeId, cnt:window.AR.counted.map(x=>x.k), log:window.AR.log, cid:window.AR.det.cid})")
    print('SEQ',seq); print('FIN',json.dumps(fin,ensure_ascii=False)[:600])
    check('v07: 모든 프레임에서 벨로나 이지 유지 (번쩍이는 프레임 포함)', all(s[1]=='bellona' and s[2]=='easy' for s in seq), seq)
    check('v07: 백옥의 보스 반지 상자 로그 줄 정확히 1번 셈', fin['cnt'].count('r_white')==1, fin['cnt'])
    rec=[l for l in fin['log'] if '자동 기록' in l]
    check('v07: 트딕이로 전환 · 벨로나 백옥 반지 상자 자동 기록 (반지 결과 고르기 창)', fin['act']=='c0' and fin['cid']=='c0' and len(rec)==1 and '백옥의 보스 반지 상자 · 벨로나' in rec[0], fin)
    # 로그 줄 OCR 변형 (실제 영상에서 나온 글자)
    q=pg.evaluate("""()=>{ window.AR.det={cid:'c0',boss:'bellona',diff:'easy',src:'t'};
      return ['백옥의 보즈 반.. 마미템을 | 개 얻었습니다. 「 소비 )','백옥의 보스 반.. 아이템플 1 개 얼있슬니다. ( 소비 )','백옥의 보스 반.. 아이템을 1 개 펀켰습니다. ( 소비 )','주문의 흔적 아이템을 240 개 얻었습니다. ( 기타 )'].map(l=>(arLogItem(l)||{}).k||''); }""")
    check('로그 OCR 변형: 백옥 줄 3개 인식 · 관계없는 줄 무시', q==['r_white','r_white','r_white',''], q)
    # 소울 조각 줄 → 맵을 못 읽었을 때 보스 힌트
    h=pg.evaluate("()=>{ const A=window.AR; A.det={cid:'c0',boss:'',diff:'',src:''}; arSoulHint('소비 아이템을 얻었습니다 (벨로나의 소울 조각)'); const a=A.det.boss; A.det.boss=''; arSoulHint('소비 아이템을 얻었습니다 (최초의 대적자의 소..)'); return [a,A.det.boss]; }")
    check('b291: 소울 조각 줄로 보스 안 정함 (보상 맵 이름으로만)', h==['',''], h)
    nm=pg.evaluate("()=>['07.209 드틱니      “ 뇨','17.208 드닉니','Lv.289 터래플'].map(arDetectChar)")
    check('상태바 이름: 뒤 잡티 한 글자 무시 · 흐린 OCR(드틱니/드닉니) → 트딕이', nm==['c0','c0','c2'], nm)
    b.close()
finally: srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else 'FAILED: '+', '.join(fails)); sys.exit(1 if fails else 0)
