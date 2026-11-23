# test_b435 (t585u): PIP [화면 공유 종료] — 최소화/최소화 해제 왼쪽, 공유 중일 때만, 누르면 기존 arDisconnect 경로(트랙 stop·인식 정지). MBT_SHOTDIR 에 b435_pip_*.png
# (원본 test_b376 틀 재사용) test_b376 (t409u·t414u/b378): PIP 최소화 + 득템 시 선홍 '·득템 기록 확인'(정적) + 보스 칸(.ar-pminrow.ar-pmwarn) 훈장경고 애니. MBT_SHOTDIR 에 b376_*.png·b378_anim_*.png
# 원본 test_b349 (t655): PIP 맨 위 현재 캐릭터 한 줄(아바타·이름·Lv/직업·월드 / 인식 중·미인식), 실시간 갱신, 스크롤 없음. 원본 b347 틀
# (b347 t651): PIP 위치 안내 없앰 + 창 높이 최소화 (상태 칸·득템 목록·수익 칸·반지 고르기 유지). MBT_SHOTDIR 에 pip_idle.png, pip_sale.png
#  headless 에 documentPictureInPicture 없음 → iframe 창 흉내(resizeTo = iframe 크기 바꿈)
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
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
REW="""b=>{ const A=window.AR; A.det.boss=b; A.det.diff='hard'; A.rew={boss:b,diff:'hard',hash:null}; arLivePaint(); }"""
FAKE="""()=>{ Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:0;outline:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; Object.defineProperty(w,'outerWidth',{get:()=>w.innerWidth}); Object.defineProperty(w,'outerHeight',{get:()=>w.innerHeight}); w.resizeTo=(x,y)=>{ window.__rz=(window.__rz||0)+1; f.style.width=x+'px'; f.style.height=y+'px'; }; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}}); }"""
STUB="""()=>{ window.arBoxOk=()=>true; window.arTarget=()=>({c:S.characters[0]}); window.arToast=()=>{}; window.arCandidates=()=>[{k:window.__k,b:findBoss(window.AR.det.boss)}]; }"""
REC="""([b,k])=>arSessAdd(k,findBoss(b).name,S.characters[0].name)"""
def shot(pg,n):
    f=pg.locator('#fakePip').bounding_box(); pg.screenshot(path=n,clip={'x':f['x']-10,'y':f['y']-10,'width':f['width']+20,'height':f['height']+20})
# PIP 안 내용이 창 안에 다 보이는지 (스크롤 없이, 목록만 자체 스크롤)
FIT="""()=>{ const d=document.getElementById('fakePip').contentDocument, w=d.defaultView; return {sh:d.documentElement.scrollHeight, ih:w.innerHeight, iw:w.innerWidth, sw:d.documentElement.scrollWidth}; }"""
VIS="""s=>{ const d=document.getElementById('fakePip').contentDocument, e=d.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return {h:r.height,b:r.bottom,ih:d.defaultView.innerHeight,show:getComputedStyle(e).display!=='none'&&r.height>0}; }"""

B="""()=>{ const d=document.getElementById('fakePip').contentDocument, q=s=>d.querySelector(s), R=e=>e?e.getBoundingClientRect():null, vis=s=>{ const e=q(s); return !!e&&getComputedStyle(e).display!=='none'&&R(e).height>0; }; const pc=q('.ar-pipchar'), mb=q('.ar-pipchar .ar-pipminb'), nw=q('.ar-pmnew'), row=q('.ar-pminrow'), cb=q('.ar-cboss');
 return {pc:pc.textContent, btn:mb?mb.textContent:null, btnCls:mb?mb.className:'', btnR:mb?R(mb).right:0, iw:d.defaultView.innerWidth, ih:d.defaultView.innerHeight, sh:d.documentElement.scrollHeight, min:d.body.classList.contains('pip-min'), meso:vis('.ar-pipmeso'), rec:vis('.ar-piprec'), sale:vis('.ar-pipsale'), h2:vis('.ar-cboss h2'), row:row?row.textContent:null, rowCls:row?row.className:'', rowAnim:row?getComputedStyle(row).animationName:null, rowShine:row?getComputedStyle(row,'::after').animationName:null, nw:nw?nw.textContent:null, nwc:nw?getComputedStyle(nw).color:null, nwAnim:nw?getComputedStyle(nw).animationName:null, cbb:R(cb).bottom, minH:window.AR.pip.minH}; }"""
CLICK="""()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipminb').click()"""
Q="""()=>{ const f=document.getElementById('fakePip'); if(!f) return null; const d=f.contentDocument, R=e=>e?e.getBoundingClientRect():null, s=d.querySelector('.ar-pipchar .ar-pipstopb'), m=d.querySelector('.ar-pipchar .ar-pipminb');
 return {stop:s?s.textContent:null, cls:s?s.className:'', sR:s?R(s).right:0, sL:s?R(s).left:0, sT:s?R(s).top:0, mL:m?R(m).left:0, mR:m?R(m).right:0, mT:m?R(m).top:0, min:m?m.textContent:null, iw:d.defaultView.innerWidth, sw:d.documentElement.scrollWidth, pcw:d.querySelector('.ar-pipchar').scrollWidth, pccw:d.querySelector('.ar-pipchar').clientWidth}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate(FAKE); pg.evaluate('arPipOpen(arPipCard())'); pg.wait_for_timeout(500)
    r=pg.evaluate(Q); check('공유 없으면 [화면 공유 종료] 없음', r and r['stop'] is None and r['min']=='최소화', r)
    # 실제 MediaStream(캔버스) 을 공유 화면처럼 연결 + 브라우저 '공유 중지'와 같은 ended 연결
    pg.evaluate("()=>{ const c=document.createElement('canvas'); c.width=64; c.height=36; c.getContext('2d').fillRect(0,0,64,36); const st=c.captureStream(5); ARX.stream=st; window.__trk=st.getVideoTracks()[0]; ARX.det.cid='c0'; window.__dc=0; const o=window.arDisconnect; window.arDisconnect=function(){ window.__dc++; return o.apply(this,arguments); }; }")
    pg.wait_for_timeout(600); r=pg.evaluate(Q); print(r)
    check('공유 중: [화면 공유 종료] 네온 crimson 작은 버튼', r['stop']=='화면 공유 종료' and 'neonBtn' in r['cls'] and 'nb-crimson' in r['cls'] and 'nb-sm' in r['cls'], r)
    check('[화면 공유 종료] 는 [최소화] 바로 왼쪽·같은 줄, 창 안', r['sR']<=r['mL'] and r['mL']-r['sR']<=12 and abs(r['sT']-r['mT'])<=3 and r['mR']<=r['iw'] and r['sL']>=0, r)
    check('PIP 가로 넘침 없음', r['sw']<=r['iw']+1, r)
    shot(pg,os.path.join(OUT,'b435_pip_full.png'))
    # 캐릭터 미인식(이 캐릭터예요 고르기)이 같은 줄에 있어도 버튼 둘 다 창 안에 다 보임
    pg.evaluate("()=>{ ARX.det.cid=''; }"); pg.wait_for_timeout(600); r=pg.evaluate(Q); t=pg.evaluate("()=>{ const d=document.getElementById('fakePip').contentDocument, R=s=>{ const e=d.querySelector(s); return e?e.getBoundingClientRect():null; }; const a=R('.ar-pipchar .ar-teach'), b=R('.ar-pipchar .ar-tbtn'), pc=R('.ar-pipchar'); return {teach:!!a, tbR:b?b.right:0, tbL:b?b.left:0, tbB:b?b.bottom:0, tbT:b?b.top:0, pcR:pc.right, pcB:pc.bottom, pcT:pc.top}; }"); print(r,t)
    check('미인식 고르기 + [화면 공유 종료] + [최소화] 모두 줄 안에 보임(겹침·잘림 없음)', t['teach'] and r['stop']=='화면 공유 종료' and t['tbR']<=r['sL']+1 and r['sR']<=r['mL'] and r['mR']<=t['pcR'] and r['pcw']<=r['pccw']+1 and t['tbT']>=t['pcT']-1 and t['tbB']<=t['pcB']+1, (r,t))
    shot(pg,os.path.join(OUT,'b435_pip_teach.png')); pg.evaluate("()=>{ ARX.det.cid='c0'; }"); pg.wait_for_timeout(500)
    pg.evaluate(CLICK); pg.wait_for_timeout(400); r=pg.evaluate(Q); print(r)
    check('최소화 중에도 [화면 공유 종료] 가 [최소화 해제] 왼쪽', r['stop']=='화면 공유 종료' and r['min']=='최소화 해제' and r['sR']<=r['mL'] and abs(r['sT']-r['mT'])<=3 and r['mR']<=r['iw'] and r['sw']<=r['iw']+1, r)
    shot(pg,os.path.join(OUT,'b435_pip_min.png'))
    pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipstopb').click()"); pg.wait_for_timeout(500)
    st=pg.evaluate("()=>({dc:window.__dc, stream:!!ARX.stream, ended:window.__trk.readyState, timer:ARX.timer, nTimer:ARX.nTimer, live:!!document.querySelector('#tabs [data-tab=auto].arlive')})"); print(st)
    check('누르면 기존 arDisconnect 1번(트랙 ended·인식 타이머 0·공유 표시 꺼짐)', st['dc']==1 and not st['stream'] and st['ended']=='ended' and not st['timer'] and not st['nTimer'] and not st['live'], st)
    pc=pg.evaluate("()=>({frame:!!document.getElementById('fakePip'), pip:!!ARX.pip, back:!!document.querySelector('#arPanel .ar-cboss:not(.ar-inpip)'), ph:!!document.querySelector('.ar-pipph')})"); print(pc)
    check('t588u: 누르면 PIP 창도 닫힘(카드는 페이지로 돌아옴)', not pc['frame'] and not pc['pip'] and not pc['ph'], pc)
    # 메인 화면 [메이플 연결 해제] 와 같은 함수인지 (코드 경로)
    same=pg.evaluate(r"()=>/arDisconnect\(\)/.test(arPipMinClick.toString()) && /a==='stop'\) arDisconnect\(\)/.test(document.documentElement.innerHTML)")
    check('PIP 버튼과 [메이플 연결 해제] 가 같은 arDisconnect 경로', same, same)
    b.close()
    # 모바일(390px) — PIP 없음, 화면 오류 없음
    b=p.chromium.launch(args=['--no-sandbox']); pg=b.new_page(viewport={'width':390,'height':844}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(800)
    check('모바일: PIP 종료 버튼 페이지에 없음', pg.evaluate("()=>!document.querySelector('.ar-pipstopb')"))
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
