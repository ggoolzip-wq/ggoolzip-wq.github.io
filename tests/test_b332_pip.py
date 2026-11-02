# test_b332 (t636): '보상 맵 인식' 칸 PIP 버튼 — Document Picture-in-Picture 로 칸을 작은 창으로 옮김, 실시간 갱신, 닫으면 되돌림, 미지원 안내
#  headless 에 documentPictureInPicture 없음 → iframe 창으로 requestWindow 흉내. MBT_SHOTDIR 에 button.png / pip.png
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
FAKE="""()=>{ Object.defineProperty(window,"documentPictureInPicture",{configurable:true,value:{requestWindow:async o=>{ const f=document.createElement('iframe'); f.id='fakePip'; f.style.cssText=`position:fixed;right:20px;top:20px;width:${o.width}px;height:${o.height}px;z-index:99999;border:1px solid #39ff7a;background:#000`; f.srcdoc='<!doctype html><html><head></head><body></body></html>'; const ld=new Promise(r=>f.onload=r); document.documentElement.append(f); await ld; const w=f.contentWindow; w.close=()=>{ w.dispatchEvent(new Event('pagehide')); f.remove(); }; return w; }}}); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR',color_scheme='dark'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800); pg.evaluate(SETUP); pg.wait_for_timeout(300)
    pg.evaluate(REW,'adversary'); pg.wait_for_timeout(300)
    btn=pg.locator('#arPanel .ar-cboss .ar-pipb'); check('보상 맵 인식 칸 안에 PIP 버튼',btn.count()==1 and btn.inner_text()=='PIP')
    pg.locator('#arPanel .ar-cboss').screenshot(path=os.path.join(OUT,'button.png'))
    pg.evaluate("()=>{ window.__dpip=Object.getOwnPropertyDescriptor(window,'documentPictureInPicture'); Object.defineProperty(window,'documentPictureInPicture',{configurable:true,value:undefined}); }")
    if True:
      btn.click(); pg.wait_for_timeout(200); m=pg.locator('#arPanel .ar-pipmsg')
      check('미지원 → 크롬/엣지 최신 버전 안내',m.is_visible() and '크롬/엣지 최신 버전' in m.inner_text(),m.inner_text())
    pg.evaluate(FAKE); btn.click(); pg.wait_for_timeout(400)
    st=pg.evaluate("""()=>{ const f=document.getElementById('fakePip'); const d=f&&f.contentDocument; const c=d&&d.querySelector('.ar-cboss'); return {inPip:!!c, ph:!!document.querySelector('#arPanel .ar-pipph'), onPage:!!document.querySelector('#arPanel .ar-cboss'), css:d?d.querySelectorAll('style,link').length:0, txt:c?c.innerText:'', theme:d?d.documentElement.getAttribute('data-theme'):null, pageTheme:document.documentElement.getAttribute('data-theme'), font:c?getComputedStyle(c).fontFamily:'', dot:c&&c.querySelector('.ar-dot')?d.defaultView.getComputedStyle(c.querySelector('.ar-dot')).backgroundColor:''}; }""")
    check('PIP 창으로 칸 이동(페이지엔 자리표)',('최신 버전' not in st['txt']) and st['inPip'] and st['ph'] and not st['onPage'],st)
    check('스타일 복사·테마 유지·초록 점',st['css']>0 and st['theme']==st['pageTheme'] and 'Pretendard' in st['font'] and st['dot']=='rgb(61, 255, 127)',st)
    check('PIP 에 보상 인식 중 + 보스',('보상 인식 중' in st['txt']) and pg.evaluate("findBoss('adversary').name") in st['txt'],st['txt'])
    pg.evaluate(REW,'lucid'); pg.wait_for_timeout(500)
    t2=pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-cboss').innerText")
    check('인식 결과 바뀌면 PIP 실시간 갱신',pg.evaluate("findBoss('lucid').name") in t2,t2)
    pg.screenshot(path=os.path.join(OUT,'pip.png'))
    pg.evaluate("()=>document.getElementById('fakePip').contentDocument.querySelector('.ar-pipb').click()"); pg.wait_for_timeout(400)
    st=pg.evaluate("()=>({back:!!document.querySelector('#arPanel .ar-g .ar-cboss .ar-b'), ph:!!document.querySelector('#arPanel .ar-pipph'), win:!!document.getElementById('fakePip'), b:document.querySelector('#arPanel .ar-pipb').textContent, pip:!!AR.pip})")
    check('PIP 닫으면 칸이 페이지로 돌아옴',st['back'] and not st['ph'] and not st['win'] and st['b']=='PIP' and not st['pip'],st)
    pg.evaluate(REW,'seren'); pg.wait_for_timeout(400)
    check('돌아온 뒤에도 페이지 칸 실시간',pg.evaluate("findBoss('seren').name") in pg.locator('#arPanel .ar-cboss .ar-b').inner_text())
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
