"""b410 (t693): 브레이빗아웃 받침 ㅜ→ㅗ 읽기·배너 순간 감시 안대 .8·UI 배율 못 찾으면 0.5초 재확인."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.goto(f'http://127.0.0.1:{port}');r=pg.evaluate("""async ()=>{const check=(v,s)=>{if(!v)throw Error(s)};
  const C=(id,name)=>({id,name,bosses:{},weekly:{},monthly:{},drops:{}});
  // p16 실제 읽기 순서 (화면 = 브레이빗아웃)
  const H=['브레미빗미못','브레미빗마못','브레미빗미웃'];
  S.characters=[C('a','브레이빗아웃'),C('b','콜더쇼츠')];ARX.nHist=H.slice();ARX.nLead=H.map(()=>false);check(arNameVote2().cid==='a','ㅜ read as ㅗ with same batchim accepted');
  check(arSylM('못','웃',1)===2&&arSylM('옷','웃',1)===2,'batchim ㅗ/ㅜ strong');check(arSylM('못','웃')!==2,'default unchanged');check(arSylM('모','우',1)!==2,'no batchim not strong');
  check(arSylM('웃','못',1)!==2,'screen ㅗ read ㅜ not widened');check(arSylM('몬','웃',1)!==2,'different batchim not widened');
  S.characters=[C('a','브레이빗아웃'),C('c','브레이빗아옷')];ARX.nHist=H.slice();ARX.nLead=H.map(()=>false);const pv=arNameVote2().cid; check(pv!=='a','pair (아옷) in list -> 아웃 not chosen from ㅗ reads');
  // 배너 순간 감시: 안대 .716 (데미안 붉은 불씨) 기록 안 함, 다른 아이템 .72 는 그대로
  check(AR_BANNER_KTHR.eye===.8,'banner eye .8');
  const M=arMatchRun, P=arPick, CA=arCandidates; let picked=[];
  try{ arCandidates=()=>[{k:'eye'},{k:'r_white'}]; arPick=(h)=>picked.push(h.k); ARX.cfg.on=true;
   arMatchRun=async()=>({hits:[{k:'eye',score:.716}],scores:[]}); ARX.bq=[{img:new ImageData(8,8),px:56}]; await arBannerPump(); check(!picked.length,'eye .716 not picked');
   arMatchRun=async()=>({hits:[{k:'eye',score:.83}],scores:[]}); ARX.bq=[{img:new ImageData(8,8),px:56}]; await arBannerPump(); check(picked.join()==='eye','eye .83 picked');
   arMatchRun=async()=>({hits:[{k:'r_white',score:.72}],scores:[]}); ARX.bq=[{img:new ImageData(8,8),px:56}]; await arBannerPump(); check(picked.join()==='eye,r_white','other items keep .7');
  } finally { arMatchRun=M; arPick=P; arCandidates=CA; }
  const K=arMapTplLoad().filter(t=>t.extra&&t.text==='빛을 되찾은 사계 <이지>'); check(K.length===1&&K[0].w===186,'b410 collapsed-minimap kaling template');
  return true;}""");assert r
  src=Path(__file__).parent.parent.joinpath('src','autorec.js').read_text()
  assert '(ARX.profN||0)<20?500:3000' in src, 'profile retry 0.5s when unknown (first 20)'
  b.close();print('PASS b410: ㅜ→ㅗ batchim name read; banner eye .8; profile retry 0.5s')
finally:srv.terminate()
