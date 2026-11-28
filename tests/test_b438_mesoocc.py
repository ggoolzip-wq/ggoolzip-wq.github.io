# test_b438 (t677u '메소 칸 일부를 마우스 커서가 가리면 가린 자리를 빼고 기록'): 151억 7721만 4644 에서 억/만/일 자리에 커서를 올리면 7721만 4644 / 151억 4644 / 151억 7721만 로 읽어 저장하던 문제.
# 수정 후: ① arMesoOccl(칸 안 글자 띠 밖의 어두운 화소 = 글자가 아닌 것이 덮음 → 보류) ② arMesoDamaged(직전 저장값에서 글자가 빠진 모양 → 같은 값 8번 연속 읽혀야 받아들임).
# 시험: 합성 프레임(실제 칸 프레임 + 원모님 값 글자 합성) + 실제 프레임 3장(v09·x06·y17)에 윈도우 화살표를 여러 자리·크기·높이로 올림. 틀린 값 저장 0 · 치우면 정답 복귀 · 진짜 변화는 막히지 않음.
import os, sys, tempfile, shutil, subprocess, base64, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures'); OUT=os.environ.get('B438_OUT')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def u(n): return 'data:image/jpeg;base64,'+base64.b64encode(open(os.path.join(FX,n),'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
shutil.copy(os.environ.get('LIVE_INDEX') or os.path.join(ROOT,'index.html'),os.path.join(site,'index.html')); shutil.copy(os.path.join(ROOT,'prices.json'),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:280,job:'',world:'',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}); S.characters=[mk('c1','테스트')]; S.meso={}; save(); }"""
# 한 장면 시험: seq = [{src, cur:[{x,y,k}], n}] 순서대로 arMesoNow n번. 커서 = 윈도우 화살표(흰 속·검은 테두리)
RUN="""async A=>{ const imgs={}; for(const s of A.seq){ if(!imgs[s.src]){ const im=new Image(); im.src=s.src; await im.decode(); imgs[s.src]=im; } }
 const first=imgs[A.seq[0].src]; ARX.bbox=arBBox(first); ARX.bbKey=''; ARX.geo=null; ARX.prof=null; await arProfDetect(first); ARX.mesoLoc=null; ARX.mesoLocT=0; ARX.mesoAllKey=null; ARX.mesoS=null; ARX.mesoSus=null; ARX.mesoLast=null; ARX.mesoSaveT=0; ARX.mesoPend=null; ARX.mesoGood=null; ARX.mesoDmg=null; ARX.cfg.mesoFindMs=1; ARX.cfg.mesoSaveMs=1; await arMesoTpl();
 ARX.det.cid='c1'; ARX.nameSrc='직접'; ARX.nOkCid='c1'; ARX.nameOk=true; ARX.cidT=Date.now();
 const saved=[], sv=window.saveMeso; window.saveMeso=(c,i,s)=>{saved.push(i); return true;}; const steps=[];
 const mk=(im,cur)=>{ const c=document.createElement('canvas'); c.width=im.width; c.height=im.height; const g=c.getContext('2d'); g.drawImage(im,0,0);
   for(const q of cur){ const P=[[0,0],[0,16],[4,12],[7,19],[9,18],[6,11],[11,11]]; g.beginPath(); P.forEach(([a,b],i)=>{ const X=q.x+a*q.k, Y=q.y+b*q.k; i?g.lineTo(X,Y):g.moveTo(X,Y); }); g.closePath(); g.fillStyle='#fff'; g.fill(); g.lineWidth=Math.max(1,q.k*.9); g.strokeStyle='#000'; g.stroke(); } return c; };
 let span=null;
 for(const s of A.seq){ const cv=mk(imgs[s.src],s.cur||[]); for(let i=0;i<(s.n||1);i++){ await new Promise(r=>setTimeout(r,3)); const o=await arMesoNow(cv); steps.push(o&&(o.why||'ok')); if(!span&&ARX.mesoLoc&&ARX.mesoLoc.inv&&(!s.cur||!s.cur.length)){ const sp=arMesoSpan(cv,'inv'), L=ARX.mesoLoc.inv; span={x:Math.round(sp.x*cv.width), w:Math.round(sp.w*cv.width), y:Math.round(L.y*cv.height), h:Math.round(L.h*cv.height)}; } } }
 window.saveMeso=sv; return {saved, steps, span}; }"""
DMG="""()=>{ const t=(a,b)=>arMesoDamaged(a,b); const O=15177214644; return {
  hideEok:t(77214644,O), hideMan:t(15100004644,O), hideIl:t(15177210000,O), lowDigit:t(1e8+77214644,O), man_il:t(15100000000,O),
  same:t(O,O), hunt:t(O+3500,O), hunt2:t(15177224000,O), spend:t(O-5e8,O), down:t(7721,O), big:t(O+2e12,O), none:t(null,O), up:t(1e12,O) }; }"""
CASES=[('원모님 값 151억 7721만 4644(합성)','b438/user_151.jpg',15177214644),('실제 v09 520억 2129만 8608','b437/v09.jpg',52021298608),('실제 x06 581억 6443만 3608','b437/x06.jpg',58164433608),('실제 y17 659억 6392만 4492','b437/y17.jpg',65963924492)]
res={}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP)
    pg.evaluate("()=>{ arOcrLoad(); }"); pg.wait_for_function("()=>!!window.AR.ocr",timeout=60000)
    check('빌드 b438 이상',int(pg.evaluate("document.documentElement.dataset.build").lstrip('b'))>=438)
    # 2층 단위: 글자가 빠진 모양만 참
    d=pg.evaluate(DMG); res['dmg']=d
    check('2층: 억 자리 가림(7721만 4644) = 손상',d['hideEok'],d); check('2층: 만 자리 가림(151억 4644) = 손상',d['hideMan']); check('2층: 일 자리 가림(151억 7721만) = 손상',d['hideIl'])
    check('2층: 한 글자 가림(51억 → 1억) = 손상',d['lowDigit'] ); check('2층: 만·일 모두 가림(151억) = 손상',d['man_il'])
    check('2층: 같은 값·사냥 증가·작은 변화는 손상 아님',(not d['same']) and (not d['hunt']) and (not d['hunt2']) and (not d['none']) and (not d['up']) and (not d['big']),d)
    for lab,fn,want in CASES:
      # A 정상 → 커서 여러 자리 → 정상 복귀
      r0=pg.evaluate(RUN,{'seq':[{'src':u(fn),'cur':[],'n':3}]}); sp=r0['span']; res[lab+'/clean']=r0
      check(f'{lab}: 커서 없음 → 정답 저장',want in r0['saved'] and all(v==want for v in r0['saved']),r0['saved'])
      ks=(1.0,1.8) if 'v09' not in lab and '합성' in lab else (1.8,)
      cfgs=[(k,dy) for k in ks for dy in (0.15,0.55)]
      xs=list(range(sp['x']+2,sp['x']+sp['w']+8,10 if '합성' in lab else 14))
      wrong=[]; heldAll=0; tot=0; recov=0
      for k,dy in cfgs:
        for x in xs:
          y=round(sp['y']+sp['h']*dy)
          r=pg.evaluate(RUN,{'seq':[{'src':u(fn),'cur':[],'n':2},{'src':u(fn),'cur':[{'x':x,'y':y,'k':k}],'n':2},{'src':u(fn),'cur':[],'n':2}]})
          tot+=1; bad=[v for v in r['saved'] if v!=want]
          if bad: wrong.append((k,dy,x,bad[:2]))
          if r['saved'] and r['saved'][-1]==want and r['steps'][-1]=='ok': recov+=1
      res[lab+'/sweep']={'total':tot,'wrong':wrong,'recov':recov}
      print('  ',lab,'커서 시험',tot,'개 중 틀린 저장',len(wrong),'치운 뒤 정답 복귀',recov)
      check(f'{lab}: 커서를 억·만·일 자리에 올려도 틀린 값 저장 0 ({tot}개)',not wrong,wrong[:4])
      check(f'{lab}: 커서를 치우면 정답으로 바로 복귀 ({tot}개)',recov==tot,(recov,tot))
    # 진짜 변화(150억 씀 = 1억 7721만 4644)는 막히지 않음: 손상처럼 보여도 같은 값 8번 연속이면 저장
    r=pg.evaluate(RUN,{'seq':[{'src':u('b438/user_151.jpg'),'cur':[],'n':3},{'src':u('b438/user_1.jpg'),'cur':[],'n':12}]}); res['realchange']=r
    check('진짜 변화(151억→1억 7721만 4644)는 처음엔 보류, 계속 같으면 저장',100000000+77214644 in r['saved'] and 'damaged' in r['steps'],(r['saved'],r['steps']))
    check('진짜 변화: 보류는 7번 이하',r['steps'].count('damaged')<=8,r['steps'])
    b.close()
  check('페이지 오류 없음',not errs,errs)
finally:
  srv.terminate(); shutil.rmtree(site,ignore_errors=True)
  if OUT: json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
print('RESULT',('FAIL '+str(len(fails))) if fails else 'PASS'); sys.exit(1 if fails else 0)
