# test_b376 (t409u): PIP 레벨·월드 없앰 + [최소화] → 2줄(닉네임+[최소화 해제] / 보상 맵), 득템 시 선홍 '·득템 기록 확인'. MBT_SHOTDIR 에 b376_full.png·b376_min.png·b376_min_new.png
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

B="""()=>{ const d=document.getElementById('fakePip').contentDocument, q=s=>d.querySelector(s), R=e=>e?e.getBoundingClientRect():null, vis=s=>{ const e=q(s); return !!e&&getComputedStyle(e).display!=='none'&&R(e).height>0; }; const pc=q('.ar-pipchar'), mb=q('.ar-pipchar .ar-pipminb'), nw=q('.ar-pmnew'), cb=q('.ar-cboss');
 return {pc:pc.textContent, btn:mb?mb.textContent:null, btnCls:mb?mb.className:'', btnR:mb?R(mb).right:0, iw:d.defaultView.innerWidth, ih:d.defaultView.innerHeight, sh:d.documentElement.scrollHeight, min:d.body.classList.contains('pip-min'), meso:vis('.ar-pipmeso'), rec:vis('.ar-piprec'), sale:vis('.ar-pipsale'), h2:vis('.ar-cboss h2'), row:q('.ar-pminrow')?q('.ar-pminrow').textContent:null, nw:nw?nw.textContent:null, nwc:nw?getComputedStyle(nw).color:null, nwAnim:nw?getComputedStyle(nw).animationName:null, cbb:R(cb).bottom, minH:window.AR.pip.minH}; }"""
CLICK="""()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipminb').click()"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark',device_scale_factor=int(os.environ.get('B376_DSF','1'))); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ arStart(document.createElement('video')); }"); pg.evaluate(REW,'lucid'); pg.evaluate(STUB)
    pg.evaluate(FAKE); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(500)
    pg.evaluate("()=>{ ARX.det.cid='c0'; }"); pg.wait_for_timeout(500)
    for k in ['eye','belt']: pg.evaluate(REC,['lucid',k])
    pg.wait_for_timeout(300); r=pg.evaluate(B); print(r)
    check('전체 PIP: 닉네임 있음, Lv·월드 없음','트딕이' in r['pc'] and 'Lv.' not in r['pc'] and '스카니아' not in r['pc'],r)
    check('전체 PIP: [최소화] 네온 버튼 오른쪽 끝',r['btn']=='최소화' and 'neonBtn' in r['btnCls'] and r['btnR']<=r['iw'] and r['btnR']>r['iw']-40,r)
    check('전체 PIP: 메소·득템 목록·제목 보임',r['meso'] and r['rec'] and r['h2'] and not r['min'],r)
    shot(pg,os.path.join(OUT,'b376_full.png'))
    pg.evaluate(CLICK); pg.wait_for_timeout(400); r=pg.evaluate(B); print(r)
    check('최소화: body.pip-min + [최소화 해제]',r['min'] and r['btn']=='최소화 해제',r)
    check('최소화: 메소·득템 목록·수익 칸·제목 숨김',not r['meso'] and not r['rec'] and not r['sale'] and not r['h2'],r)
    check('최소화: 2줄 = 보상 맵 + 루시드',r['row'] and '보상 맵' in r['row'] and '루시드' in r['row'] and r['nw'] is None,r)
    check('최소화: 창 높이 줄어듦(최소 크기 갱신) + 스크롤 없음',r['minH']<=90 and r['ih']<=r['minH']+1 and r['sh']<=r['ih']+1 and r['cbb']<=r['ih']+1,r)
    check('최소화 상태 localStorage 저장',pg.evaluate("localStorage.getItem('arPipMin')")=='1')
    shot(pg,os.path.join(OUT,'b376_min.png'))
    pg.evaluate(REC,['lucid','h_pocket']); pg.wait_for_timeout(400); r=pg.evaluate(B); print(r)
    check("득템 → 보스 옆 선홍 '·득템 기록 확인'",r['nw']=='·득템 기록 확인' and r['nwc']=='rgb(255, 255, 255)' and r['nwAnim']=='mwFade' and pg.evaluate("()=>getComputedStyle(document.getElementById('fakePip').contentDocument.querySelector('.ar-pmnew'),'::after').animationName")=='mwShine',r)  # b377: 훈장 경고 애니
    check('득템 후에도 2줄 유지(스크롤 없음)',r['sh']<=r['ih']+1 and not r['rec'],r)
    shot(pg,os.path.join(OUT,'b376_min_new.png'))
    for i,t in enumerate([0,250,1200,700]):  # b377: 애니 프레임
        pg.wait_for_timeout(t); shot(pg,os.path.join(OUT,f'b377_anim_{i}.png'))
    pg.evaluate("()=>{ window.__bs=window.arBossState; window.arBossState=()=>''; ARX.det.boss=''; ARX.rew=null; arLivePaint(); }"); pg.wait_for_timeout(400); r=pg.evaluate(B); print(r)
    lg=pg.evaluate("()=>{ const d=document.getElementById('fakePip').contentDocument; return [!!d.querySelector('.ar-pml.rew'),!!d.querySelector('.ar-pmlast')]; }")
    check('보상 맵을 벗어나도 마지막 득템 보스 이름 + 표시 유지 (초록 점 꺼짐)',r['row'] and '루시드' in r['row'] and r['nw']=='·득템 기록 확인' and lg==[False,True],(r,lg))
    shot(pg,os.path.join(OUT,'b376_min_left.png')); pg.evaluate("()=>{ window.arBossState=window.__bs; }"); pg.evaluate(REW,'lucid')
    pg.evaluate(CLICK); pg.wait_for_timeout(400); r=pg.evaluate(B); print(r)
    check('최소화 해제: 전체 PIP 복귀(368) + 목록 3개',not r['min'] and r['btn']=='최소화' and r['meso'] and r['rec'] and r['minH']==368 and r['ih']>=367,r)
    check('해제 저장',pg.evaluate("localStorage.getItem('arPipMin')")=='0')
    pg.evaluate(CLICK); pg.wait_for_timeout(300); r=pg.evaluate(B)
    check('다시 최소화하면 확인한 득템은 표시 안 함',r['min'] and r['nw'] is None,r)
    # 닫고 다시 열면 최소화 유지
    pg.evaluate("()=>arPipClose()"); pg.wait_for_timeout(300); pg.evaluate(REW,'lucid'); pg.locator('#arPanel .ar-cboss .ar-pipb').click(); pg.wait_for_timeout(500); r=pg.evaluate(B); print(r)
    check('PIP 다시 열어도 최소화 유지(작은 창)',r['min'] and r['btn']=='최소화 해제' and r['ih']<140,r)
    # 최소화 중 2인 수익 칸 대기 → 표시, 해제하면 수익 칸 보임
    pg.evaluate("()=>{ S.characters[0].bosses[findBoss('will').id].party=2; save(); }"); pg.evaluate(REW,'will'); pg.evaluate(STUB)
    pg.evaluate("()=>{ window.__k='belt'; arRecord('belt',.9,'t'); }"); pg.wait_for_timeout(400); r=pg.evaluate(B); print(r)
    check('최소화 중 수익 기록 대기 → ·득템 기록 확인, 수익 칸 숨김',r['nw']=='·득템 기록 확인' and not r['sale'] and r['sh']<=r['ih']+1,r)
    pg.evaluate(CLICK); pg.wait_for_timeout(400); r=pg.evaluate(B)
    check('해제하면 수익 기록 칸 보임',r['sale'] and not r['min'],r)
    pg.evaluate("()=>arDisconnect()"); b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
