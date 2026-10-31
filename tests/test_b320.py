# test_b320 (t583): 목록 전 캐릭터 이름 쌍 교차 오인식 0건 — 화면 이름 A, 목록에 A 없음·B 있음 → 어떤 읽기 순서에서도 B 가 뜨면 안 됨.
# ① 이름 쌍 전부: A 를 그대로/헷갈리는 짝(B)으로 섞어 읽은 OCR 결과 ② 실게임(v01~v20) 프레임 실제 OCR 결과 순서 그대로 (트딕이 화면을 '드딕이'로 자주 읽음)
import os, sys, tempfile, shutil, subprocess, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
NAMES=['트딕이','드딕이','트딕','트닉이','팬더데이','펜더데이','터래플','붐하우스','Drcancel','Dreancel','Drcance']
READS=json.load(open(os.path.join(ROOT,'tests','fixtures','b320_reads.json')))
RUN="""([names,seqs])=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1};
  S.characters=names.map((n,i)=>({id:'c'+i,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:!i,image:'',bosses:JSON.parse(JSON.stringify(all)),weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  const A=window.AR, seen=new Set(); for(const sq of seqs){ A.det.cid=''; A.nHist=[]; A.nOther=[]; A.nameOk=false; for(const t of sq){ arNameRes(t); if(A.det.cid) seen.add(A.det.cid); } }
  return [...seen].map(id=>S.characters.find(c=>c.id===id).name); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(600)
    bad=[]
    for a in NAMES:
      others=[n for n in NAMES if n!=a]
      for bn in others:
        seqs=[[f'Lv.285 {a}']*8,[f'Lv.285 {x}' for x in [a,bn,a,bn,bn,a,bn,bn]],[f'Lv.285 {bn}',f'Lv.285 {a}']*4]
        if any(len(set(x))>1 for x in [a]) and bn in others:
          got=pg.evaluate(RUN,[others,seqs[:1]])  # A 만 읽힘 → 목록에 없으니 아무것도 안 떠야
          if got: bad.append((a,'only',got))
        # 섞여 읽힘: B 가 정확히 읽혀도 A(헷갈리는 짝)가 섞이면 안 뜸 — 단 A·B 가 서로 헷갈리는 짝일 때만 요구
        got=pg.evaluate(RUN,[others,seqs[1:]]); conf=pg.evaluate("([a,b])=>{ const H=[a,b].map(x=>x.replace(/[^가-힣]/g,'')); if(H[0].length<2||H[0].length!==H[1].length) return false; const dl=arLev(arLoose(H[0]),arLoose(H[1])); return dl<=1&&arLev(arJamo(H[0]),arJamo(H[1]))>dl; }",[a,bn])
        if conf and bn in got: bad.append((a,bn,got))
    check(f'이름 쌍 {len(NAMES)*(len(NAMES)-1)}개 교차 오인식 0건',not bad,bad[:6])
    lst=['드딕이','트딕','트닉이','팬더데이','붐하우스','Drcance','Dreancel','DrcanceI2']
    got=pg.evaluate(RUN,[lst,[READS[v] for v in sorted(READS)]]); check('실게임 OCR 읽기 순서(목록에 실제 이름 없음) → 어떤 캐릭터도 안 뜸',not got,got)
    got=pg.evaluate(RUN,[['트딕이','팬더데이','터래플','Drcancel'],[READS[v] for v in sorted(READS)]]); check('실게임 OCR (실제 이름 있음) → 다른 캐릭터 안 뜸',set(got)<={'트딕이','Drcancel'},got)
    b.close()
finally: srv.terminate()
check('페이지 오류 없음',not errs,errs)
print('RESULT', 'FAIL' if fails else 'PASS'); sys.exit(1 if fails else 0)
