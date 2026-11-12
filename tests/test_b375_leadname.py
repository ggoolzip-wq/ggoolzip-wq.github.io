# test_b375 (t407u): 이름 앞 숫자 닉네임 '2터래플' — 라이브에서 '터래플'로 잡히던 것. 앞 기호 유무로 구분 (b284 설계)
import os, sys, tempfile, shutil, subprocess, json, base64
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
shutil.copy(os.path.join(ROOT,'tests','fixtures','b375','live_2terraple.png'),os.path.join(site,'u.png'))
shutil.copy(os.path.join(ROOT,'tests','fixtures','b284','s10.jpg'),os.path.join(site,'t.jpg'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SET="""(N)=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1}; S.characters=N.map((n,i)=>({id:'c'+i,name:n,level:285,job:'',world:'',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}})); S.activeId='c0'; save();
  const A=window.AR; A.det={cid:'',boss:'',diff:'',src:''}; A.nHist=[]; A.nLead=[]; A.nLock=null; A.nSw=null; A.nOther=[]; A.nameOk=false; A.nOcrPrev=null; A.nprev=null; }"""
RUN="""async ([f,n])=>{ const im=new Image(); im.src=f; await im.decode(); const A=window.AR; const seq=[]; for(let i=0;i<n;i++){ A.nameOk=false; A.nOcrPrev=null; const p=arNameWatch(im); if(p&&p.then) await p; await new Promise(r=>setTimeout(r,120)); const c=S.characters.find(x=>x.id===A.det.cid); seq.push(c?c.name:'-'); } return {seq,src:A.nameSrc,raw:A.nameText}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':900},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SET,['터래플','2터래플','제트루'])
    dc=pg.evaluate("()=>['Lv.285 2터래플','\\\\0.285 2터래플   -','7.200 <ㅇ더대들','Lv.289 터래플','.289 터래플','.2852터래플','.285터래플'].map(t=>{ const c=S.characters.find(x=>x.id===arDetectChar(t)); return c?c.name:''; })")
    check('arDetectChar: 앞 기호 있으면 2터래플, 없으면 터래플 (레벨 붙은 .285터래플 = 터래플)',dc==['2터래플','2터래플','','터래플','터래플','2터래플','터래플'],dc)
    v=pg.evaluate("""()=>{ const A=window.AR, r={}, nm=id=>(S.characters.find(x=>x.id===id)||{}).name||'';
      A.nHist=['터래플','터래플','터래플','터래플']; A.nLead=[true,true,true,false]; r.lead=nm(arNameVote2().cid);
      A.nHist=['터래플','터래플','터래플','터래플']; A.nLead=[false,false,false,false]; r.plain=nm(arNameVote2().cid);
      A.nHist=['터래플','터래플','터래플','터래플']; A.nLead=[true,false,true,false]; r.mix=nm(arNameVote2().cid);
      A.nHist=['터래플','터래플','터래플']; A.nLead=[]; r.unk=nm(arNameVote2().cid);
      S.characters=S.characters.filter(c=>c.name!=='터래플'); A.nHist=['터래플','터래플','터래플','터래플']; A.nLead=[false,false,false,false]; r.only2plain=nm(arNameVote2().cid); A.nLead=[true,true,true,true]; r.only2lead=nm(arNameVote2().cid);
      return r; }""")
    check('투표: 앞 기호 읽힘 다수 → 2터래플 · 없음 → 터래플 · 반반 → 2터래플(≥절반) · 모름(옛 기록) → 터래플',v['lead']=='2터래플' and v['plain']=='터래플' and v['mix']=='2터래플' and v['unk']=='터래플',v)
    check('2터래플만 등록: 앞 기호 없는 화면(터래플)은 안 잡고, 앞 기호 화면은 2터래플',v['only2plain']=='' and v['only2lead']=='2터래플',v)
    pg.evaluate(SET,['터래플','2터래플','제트루']); pg.evaluate("arOcrLoad()"); pg.wait_for_function("window.AR.ocr||window.AR.ocrErr",timeout=60000)
    r=pg.evaluate(RUN,['u.png',12]); print('user',r)
    check('실화면(사용자 스샷 Lv.285 2터래플) → 2터래플, 터래플로 한 번도 안 잡힘',r['seq'][-1]=='2터래플' and '터래플' not in r['seq'],r)
    pg.evaluate(SET,['2터래플','제트루']); r=pg.evaluate(RUN,['u.png',12]); print('only2',r)
    check('2터래플만 등록해도 실화면 → 2터래플 (예전엔 숫자 이름이 투표에서 빠져 영원히 -)',r['seq'][-1]=='2터래플',r)
    pg.evaluate(SET,['터래플','2터래플','제트루']); r=pg.evaluate(RUN,['t.jpg',12]); print('plain',r)
    # b415: s10.jpg 화면은 'Lv.289 더래플'(픽셀 그대로). 예전에는 칸이 글자 위를 잘라 '러래플'로 읽고 음절 경로가 터래플로 오인함. 더래플 목록 확정은 test_b415.
    check('회귀: s10(실제 더래플)을 목록의 터래플/2터래플로 오인하지 않음', '터래플' not in r['seq'] and '2터래플' not in r['seq'], r)
    pg.evaluate("()=>{ const A=window.AR; A.nOther=[]; A.nameOk=false; }"); r=pg.evaluate(RUN,['u.png',30]); print('switch',r)
    check('같은 세션에서 터래플(음절·이미지 학습 뒤) → 2터래플 화면으로 바꾸면 2터래플',r['seq'][-1]=='2터래플',r)
    m=pg.evaluate("""()=>{ localStorage.setItem('arNTpl',JSON.stringify({'터래플':{w:4,h:4,d:btoa('\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\x09\\x0a\\x0b\\x0c\\x0d\\x0e\\x0f\\x10')},'제트루':{w:4,h:4,d:btoa('\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\x09\\x0a\\x0b\\x0c\\x0d\\x0e\\x0f\\x10')}})); localStorage.removeItem('arNTplV'); window.AR.ntpl=null; const L=arNtLoad(); return Object.keys(L).sort(); }""")
    check('옛 잘못 배운 틀: 한글이 같은 이름 짝(터래플/2터래플)의 틀만 한 번 지움, 다른 이름 틀은 유지',m==['제트루'],m)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
