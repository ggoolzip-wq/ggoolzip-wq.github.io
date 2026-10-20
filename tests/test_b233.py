# b233: 이번 주 수익 총합 — 캐릭터 이름 앞 초상화 = 주별 득템 표 이름 앞 초상화와 같은 크기·자르기(.avatar.av24 24px), 사진 없으면 같은 크기 글자 칸, 줄바꿈·잘림 없음, 금액 오른쪽 끝 같음
import os, sys, time, subprocess, urllib.request, json, io
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8977'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:500] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
from PIL import Image, ImageDraw
im=Image.new('RGBA',(96,96),(40,120,200,255)); ImageDraw.Draw(im).ellipse((30,30,66,66),fill=(250,200,60,255)); buf=io.BytesIO(); im.save(buf,'PNG'); PNG=buf.getvalue()
IMG='https://open.api.nexon.com/static/maplestory/character/look/TESTFIXTURE'
def nx(r):
    if r.request.url.startswith('https://open.api.nexon.com/static/'): return r.fulfill(status=200,content_type='image/png',body=PNG)
    return r.abort()
A="""(sel)=>[...document.querySelectorAll(sel)].filter(a=>a.getClientRects().length).map(a=>{const s=getComputedStyle(a), i=a.querySelector('img'), si=i&&getComputedStyle(i), r=a.getBoundingClientRect(), ir=i&&i.getBoundingClientRect();
  return {w:r.width,h:r.height,rad:s.borderRadius,fs:s.fontSize,txt:a.textContent, img:i?[si.width,si.height,si.objectFit,si.objectPosition, Math.round(ir.width), i.complete&&i.naturalWidth>0]:null}})"""
ROWS="""()=>[...document.querySelectorAll('.revpanel .rp-char .rp-top')].map(t=>{const a=t.querySelector('.avatar'), n=t.querySelector('.rp-nm'), b=t.querySelector(':scope>b'), r=t.getBoundingClientRect();
  return {av:!!a, avFirst:a&&a.compareDocumentPosition(n)&Node.DOCUMENT_POSITION_FOLLOWING, nm:n.textContent, fit:n.scrollWidth<=n.clientWidth+1, h:Math.round(r.height), br:Math.round(b.getBoundingClientRect().right), pr:Math.round(document.querySelector('.revpanel').getBoundingClientRect().right), avR:a&&a.getBoundingClientRect().right, nL:n.getBoundingClientRect().left}})"""
try:
  with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1600,390):
        ctx=br.new_context(viewport={'width':w,'height':1000},locale='ko-KR'); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',nx)
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        E=lambda d:{'enabled':True,'diff':d,'party':1}
        ch=[{'id':f'c{i}','name':n,'level':285,'job':'히어로','world':'스카니아','image':img,'bosses':{'lotus':E('hard')},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,n,img in [(1,'원모본캐',IMG),(2,'아주긴닉네임열두글자임',IMG),(3,'사진없는캐릭','')]]
        ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':ch,'settings':{'accounts':[]},'startWeek':'2026-10-08'}
        pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
        pg.evaluate("""()=>{ const P=(id,name,items)=>({id,name,meso:1e9,count:1,bosses:['스우(하드)'],bvals:[1e9],items,outcomes:{}});
          S.history=[{week:'2026-10-08',weeklyOnly:true,total:2e9,cleared:2,perChar:[P('c1','원모본캐',{'lotus|eye':1}),P('c3','사진없는캐릭',{'lotus|eye':1})]}];
          for(const c of S.characters){ c.weekly={lotus:true}; } S.characters[0].drops={'lotus|eye':1}; save(); render(); }""")
        pg.wait_for_timeout(800)
        P=pg.evaluate(A,'.revpanel .rp-top .avatar'); R=pg.evaluate(ROWS)
        check(f'{w}: 수익 총합 캐릭터마다 이름 앞 초상화', len(R)==3 and all(r['av'] and r['avFirst'] and r['avR']<=r['nL'] for r in R), R)
        check(f'{w}: 이름 안 잘림·한 줄·금액 오른쪽 끝 같음·패널 안', all(r['fit'] and r['h']<=30 for r in R) and len({r['br'] for r in R})==1 and all(r['br']<=r['pr'] for r in R), R)
        pg.click('[data-tab=loot]'); pg.wait_for_timeout(900)
        Wl=pg.evaluate(A,'#weekLoot .wlpage.on .wlb .avatar')
        ref_img=[x for x in Wl if x['img']]; ref_ph=[x for x in Wl if not x['img']]; p_img=[x for x in P if x['img']]; p_ph=[x for x in P if not x['img']]
        k=lambda x:(x['w'],x['h'],x['rad'],x['fs'],tuple(x['img'] or []))
        check(f'{w}: 초상화 = 주별 득템 표와 같은 크기·모서리·자르기(사진 있는 캐릭터)', ref_img and p_img and k(p_img[0])==k(ref_img[0]) and p_img[0]['w']==24 and p_img[0]['img'][5], (p_img[:1],ref_img[:1]))
        check(f'{w}: 사진 없음 = 같은 크기 글자 칸', p_ph and ref_img and (p_ph[0]['w'],p_ph[0]['h'],p_ph[0]['rad'],p_ph[0]['fs'])==(ref_img[0]['w'],ref_img[0]['h'],ref_img[0]['rad'],ref_img[0]['fs']) and p_ph[0]['txt']=='사', (p_ph,ref_img[:1]))
        ctx.close()
    # 예시
    for w in (1600,390):
        ctx=br.new_context(viewport={'width':w,'height':1000},locale='ko-KR'); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        R=pg.evaluate(ROWS); P=pg.evaluate(A,'.revpanel .rp-top .avatar')
        check(f'예시 {w}: 캐릭터 4명 이름 앞 24px 초상화(글자 칸)·한 줄·금액 끝 같음', len(R)==4 and all(r['av'] and r['fit'] and r['h']<=30 for r in R) and len({r['br'] for r in R})==1 and all(x['w']==24 and x['h']==24 for x in P), (R,P))
        ctx.close()
    br.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(repr(e))
finally:
    srv.kill()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
