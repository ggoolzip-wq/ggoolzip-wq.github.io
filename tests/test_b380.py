# test_b380 (t416·t418): 벨로나 하드 보상 맵에서 신념의 연마석·광기의 방어구 상자 기록 안 됨.
#   원인: 벨로나 이지 판에서 저장된 맵 이름 그림 템플릿 '솔라툼의 유산 <이지>'가 하드 화면에도 .9 로 맞아 난이도가 이지로 정해짐
#   → 후보가 이지 드롭(백옥 반지 상자)만 → 하드 드롭 전부 안 찾음. 수정: 템플릿은 맵 이름만, 난이도는 전투 맵 OCR(runDiff) / 없으면 OCR.
#   화면: v07(벨로나 이지 실제 프레임)에서 '<이지>'를 v10 실제 프레임의 '<하드>' 글자로 바꾼 합성(b380_bellona_hard_syn.png).
#   + 생명/신념의 연마석 색 묶음(AR_VAR): 생명 연마석 아이콘이 신념 연마석 모양 .81 로 맞아 하드에서 신념으로 잘못 기록되던 것 → 색으로 생명.
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures','b300')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:500] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return ('data:image/png' if n.endswith('png') else 'data:image/jpeg')+';base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""async([e,h])=>{ window._img=async(u)=>{ const im=new Image(); im.src=u; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; cv.getContext('2d').drawImage(im,0,0); return cv; };
 const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.id==='bellona'?'easy':(b.diffs.includes('hard')?'hard':b.diffs[0])};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; render();
 window._T=1e7; Date.now=()=>window._T; ARX.cfg.on=true; window.E=await _img(e); window.H=await _img(h);
 ARX.rwl={boss:'bellona'}; const I=arMapTplImg(E), B=arMapTplBands(I), t='솔라툼 골짜기 : 솔라툼의 유산 <이지>'; arMapTplLearn(I,B,t,1000); arMapTplLearn(I,B,t,2000); ARX.rwl=null;
 return JSON.parse(localStorage.getItem('arMapTpl')||'[]').map(x=>x.text); }"""
WATCH="""(src)=>{ ARX.mapOk=false; ARX.mChgT=Date.now(); ARX.mOcrT=0; ARX.mapBusy=false; ARX.mprev=null; const oo=ARX.ocr; ARX.ocr={}; window._ocrN=0; const o=window.arOcr; window.arOcr=async()=>{ _ocrN++; return ''; }; arMapWatch(window[src]); window.arOcr=o; ARX.ocr=oo;
  return {hit:ARX.mapTplHit&&ARX.mapTplHit.text, det:ARX.mapDet&&{boss:ARX.mapDet.boss,diff:ARX.mapDet.diff}, run:ARX.runDiff}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    sv=pg.evaluate(SETUP,[u('v07_0120.jpg'),u('b380_bellona_hard_syn.png')])
    check('솔라툼의 유산 <이지> 그림이 기본 템플릿으로 들어 있음',pg.evaluate("()=>arMapTplLoad().some(t=>t.text==='솔라툼의 유산 <이지>'&&t.boss==='bellona')"))
    check('이미 있으면 같은 이름 템플릿을 다시 저장하지 않음',sv==[],sv)
    sc=pg.evaluate("()=>{ const r=arMapTplMatch(H); return r&&[r.text,+r.sc.toFixed(3)]; }")
    check('하드 화면도 이지 템플릿에 맞음 (원인 확인)',sc and sc[0]=='솔라툼의 유산 <이지>' and sc[1]>=.8,sc)
    # 전투 맵 OCR '테네아 신전 <하드>' → 보상 맵 템플릿 → 난이도 하드 유지
    r=pg.evaluate("()=>{ ARX.runDiff=null; ARX.mapDet=null; arDetectBMap('솔라툼 골짜기 : 테네아 신전 <하드>'); return 1; }")
    r=pg.evaluate(WATCH,'H')
    check('하드 판: 템플릿으로 맵(벨로나 보상 맵) 확정 + 난이도는 전투 맵에서 읽은 하드',r['hit']=='솔라툼의 유산 <이지>' and r['det']=={'boss':'bellona','diff':'hard'} and r['run']['diff']=='hard',r)
    r=pg.evaluate("""async()=>{ ARX.box=null; ARX.det={cid:'c0',boss:'',diff:'',src:''}; ARX.boxScanT=0; await arBoxStep(H,true); const t=arTarget(); const C=arCandidates(true).map(c=>c.k);
      const d0=k=>+(dropMap(S.characters[0],'weekly')['bellona|'+k]||0); arRecord('g_faith',.95,'공중'); arRecord('b_bellona',.95,'공중'); return {det:{...ARX.det},diff:t&&t.diff,C,g:d0('g_faith'),bb:d0('b_bellona')}; }""")
    check('보상 상자 → 벨로나 하드 (캐릭터 설정은 이지여도)',r['det']['boss']=='bellona' and r['diff']=='hard',r)
    check('하드 드롭 후보: 신념의 연마석·광기의 방어구 상자·혼돈의 칠흑 상자·생명 반지 상자',all(k in r['C'] for k in ['g_faith','b_bellona','chaosbox','r_life']),r['C'])
    check('신념의 연마석·광기의 방어구 상자 자동 기록',r['g']==1 and r['bb']==1,r)
    # 같은 판 전투 맵 난이도가 없으면 템플릿 난이도 안 씀 → OCR 한 번 더
    r=pg.evaluate("()=>{ ARX.runDiff=null; ARX.mapDet=null; return 1; }"); r=pg.evaluate(WATCH,'H'); n=pg.evaluate("_ocrN")
    check('전투 맵 난이도 없음 → 템플릿 난이도(이지) 안 씀 + OCR 로 난이도 읽으러 감',r['det'] and r['det']['boss']=='bellona' and r['det']['diff']=='' and n==1,[r,n])
    r=pg.evaluate("()=>{ ARX.runDiff=null; return arDetectBMap('솔라툼 골짜기 : 솔라툼의 유산 <하드>'); }")
    check('OCR 줄의 <하드> 는 그대로 읽음',r and r['diff']=='hard',r)
    r=pg.evaluate("()=>AR_VAR.some(g=>g.includes('g_life')&&g.includes('g_faith'))")
    check('생명/신념의 연마석 색 묶음',r)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.kill(); shutil.rmtree(site,ignore_errors=True)
print('FAILS',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
