# test_b436 (t589u): 메소 저장은 지금 화면에서 확정된 닉네임 캐릭터에만 — A(1억 저장) → 캐릭터 전환(검은 화면) → B 인벤(100억)은 B 닉 확정 전엔 보류(A 저장 0), B 확정 뒤 B 에만 저장. 맵 이동도 확정 리셋.
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
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RUN="""async()=>{ const A=window.AR; const mk=(id,n)=>({id,name:n,level:285,job:'나이트로드',world:'스카니아',ocid:'',accId:'',isMain:id==='c0',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});
  S.characters=[mk('c0','에이캐릭'),mk('c1','비캐릭')]; S.activeId='c0'; S.meso={}; A.nameOf=null; A.det.cid=''; A.nLock=null; A.nSw=null; A.nameOk=false; A.nOkCid=''; A.cidT=0; A.nResetT=0; A.mesoSaveT=0; A.mesoPend=null; A.mesoSus=null;
  let t=1e12; const on=Date.now; Date.now=()=>t; let R={v:0,hi:true}; const saved=[]; const sm=window.saveMeso; window.saveMeso=(c,i,s)=>{ saved.push([c,i]); return sm(c,i,s); };
  window.arMesoPanel=(s,k)=>k==='inv'; window.arMesoRead=async()=>({t:'',v:R.v,hi:R.hi}); window.arMesoLocate=()=>{}; A.mtpl=A.mtpl||{};
  const conf=cid=>{ A.nameOk=true; A.cidT=t; arCidPut(cid,t,'이미지'); }; /* = 닉네임 칸 이미지 대조/OCR 이 이 캐릭터로 읽음 (arNameTplTick·arNameRes 와 같은 순서) */
  const cv=document.createElement('canvas'); cv.width=1920; cv.height=1080; const g=cv.getContext('2d'); g.fillStyle='#6a8'; g.fillRect(0,0,1920,1080);
  const o={};
  // ① A 닉 확정 + 메소 1억 → A 저장
  conf('c0'); R={v:100000000,hi:true}; o.r1=await arMesoNow(cv); A.mesoSaveT=0; arMesoFlush(t,true); o.s1=saved.slice();
  // ② 캐릭터 변경: 검은 화면(arBlackTick 실제 함수) → B 접속, 닉 칸 그림 바뀜(nameOk=false), B 닉은 아직 못 읽음. det.cid 는 A 로 고정 유지(nLock)
  const bk=document.createElement('canvas'); bk.width=1920; bk.height=1080; bk.getContext('2d').fillRect(0,0,1920,1080); t+=500; arBlackTick(bk,t); t+=2000; arBlackTick(bk,t); t+=300; arBlackTick(cv,t);
  o.detAfterBlack=A.det.cid; o.freshA=arNameFresh('c0'); o.resetWhy=A.nResetWhy;
  t+=1000; R={v:10000000000,hi:true}; A.mesoSaveT=0; o.r2=await arMesoNow(cv); t+=1000; o.r2b=await arMesoNow(cv); arMesoFlush(t,true); o.s2=saved.slice();
  // ③ B 닉이 읽히기 시작 — 전환 확인 중(arCidPut 3번·2초 전엔 det.cid=A) 에도 A 로 저장 안 함
  t+=200; conf('c1'); o.detSwitching=A.det.cid; A.mesoSaveT=0; o.r3=await arMesoNow(cv); arMesoFlush(t,true); o.s3=saved.slice();
  t+=1000; conf('c1'); t+=1200; conf('c1'); o.detB=A.det.cid; A.mesoSaveT=0; o.r4=await arMesoNow(cv); arMesoFlush(t,true); o.s4=saved.slice();
  // ④ 맵 이동(맵 이름 칸 그림 바뀜, 실제 arMapWatch) → B 다시 확정 전엔 보류, 확정되면 저장
  const m1=document.createElement('canvas'); m1.width=1920; m1.height=1080; const mg=m1.getContext('2d'); mg.fillStyle='#6a8'; mg.fillRect(0,0,1920,1080); mg.fillStyle='#fff'; mg.font='bold 40px sans-serif'; mg.fillText('새 맵 이름 칸',10,50);
  A.mapBusy=true; t+=1000; arMapWatch(cv); t+=200; arMapWatch(m1); o.freshB_afterMap=arNameFresh('c1'); R={v:10500000000,hi:true}; A.mesoSaveT=0; o.r5=await arMesoNow(m1); arMesoFlush(t,true); o.s5=saved.slice();
  t+=200; conf('c1'); A.mesoSaveT=0; o.r6=await arMesoNow(m1); arMesoFlush(t,true); o.s6=saved.slice(); A.mapBusy=false;
  o.meso=JSON.parse(JSON.stringify(S.meso));
  Date.now=on; window.saveMeso=sm; return JSON.parse(JSON.stringify(o)); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    o=pg.evaluate(RUN); print(json.dumps(o,ensure_ascii=False))
    check('① A 닉 확정 → A 에 1억 저장', o['s1']==[['c0',100000000]], o['s1'])
    check('② 검은 화면 = 전환 신호 → A 확정 풀림 (det.cid 는 A 로 남아 있어도)', o['detAfterBlack']=='c0' and o['freshA'] is False and o['resetWhy']=='검은 화면', o)
    check('② B 닉 미확정 상태 B 인벤 100억 → 보류(nameWait), A 저장 0', o['r2'].get('why')=='nameWait' and o['r2b'].get('why')=='nameWait' and o['s2']==[['c0',100000000]], (o['r2'],o['s2']))
    check('③ B 닉 읽힘·전환 확인 중(det.cid=A) → A 로 저장 안 함', o['detSwitching']=='c0' and o['r3'].get('why')=='nameWait' and o['s3']==[['c0',100000000]], (o['r3'],o['s3']))
    check('③ B 확정(det.cid=B) → B 에만 100억 저장', o['detB']=='c1' and o['s4']==[['c0',100000000],['c1',10000000000]], o['s4'])
    check('④ 맵 이동 → 확정 풀림, 다시 확정 전 보류', o['freshB_afterMap'] is False and o['r5'].get('why')=='nameWait' and o['s5']==o['s4'], (o['r5'],o['s5']))
    check('④ B 다시 확정 → B 에 저장', o['s6'][-1]==['c1',10500000000] and len(o['s6'])==3, o['s6'])
    mv={v['by']:v['inv'] for v in o['meso'].values()}
    check('최종: A=1억 그대로, B=105억 (A 오염 0)', mv.get('c0')==100000000 and mv.get('c1')==10500000000, o['meso'])
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
