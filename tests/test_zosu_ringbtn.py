import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P9463=_tutil.free_port()
# zosu-hong: 홍옥 반지 상자 버튼 = 아이콘 + '홍옥 반지 상자', 옆 아이콘만 칩 없음 · 다크/라이트 · 1600/390 · 예시 화면 · 클릭 → #rredModal
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT=str(_P9463)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=_tutil.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
Q="""()=>[...document.querySelectorAll('[data-rred]')].filter(b=>b.getClientRects().length).map(b=>{const r=b.getBoundingClientRect(), i=b.querySelector('.rrbico img, .rrbico .ric'), ir=i&&i.getBoundingClientRect(), boss=b.closest('.boss'), cs=getComputedStyle(b);
 return {t:b.textContent.trim(), ico:!!i&&ir.width>=16&&ir.width<=22&&ir.top>=r.top-1&&ir.bottom<=r.bottom+1, one:r.height<34&&b.scrollWidth<=b.clientWidth+0.5,
  inside:r.right<=boss.getBoundingClientRect().right+0.5, offchip:!!boss.querySelector('.drop.off img[src], .drop.off .ric')&&[...boss.querySelectorAll('.drop.off')].some(x=>/홍옥/.test(x.dataset.tip||'')), col:cs.color, bg:document.body.style.background||getComputedStyle(document.body).backgroundColor}})"""
QS="""()=>[...document.querySelectorAll('[data-rred]')].filter(b=>b.getClientRects().length).map(b=>{const t=document.createElement('span'); t.className='drop'+(b.classList.contains('got')?' got':''); t.innerHTML='<span class="ifb">?</span><span class="dn">x</span>'; b.parentNode.insertBefore(t,b);
 const f=e=>{const c=getComputedStyle(e);return {bw:c.borderTopWidth,bs:c.borderTopStyle,bc:c.borderTopColor,br:c.borderTopLeftRadius,h:Math.round(e.getBoundingClientRect().height),bg:c.backgroundColor,pad:c.paddingTop+' '+c.paddingBottom,fs:c.fontSize}};
 const r=[f(b),f(t)]; t.remove(); return r;})"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1600,390):
      pg=b.new_page(viewport={'width':w,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.wait_for_timeout(1500)
      for th in ('dark','light'):
        if th=='light': pg.click('#themeBtn'); pg.wait_for_timeout(300)
        check(f'{w} {th}: 테마', pg.evaluate("document.documentElement.dataset.theme||'dark'")==th)
        B=pg.evaluate(Q)
        check(f'{w} {th}: 버튼 있음·글자 홍옥 반지 상자·아이콘 안·한 줄·칸 안', B and all(x['t']=='홍옥 반지 상자' and x['ico'] and x['one'] and x['inside'] for x in B), B)
        S=pg.evaluate(QS)
        check(f'{w} {th}: 테두리 두께·모양·색·둥글기·높이·배경·위아래 여백·글자 크기 = 옆 아이템 칩(.drop, 기록됨이면 .drop.got)과 같음 (zosu-b234)', S and all(x==y for x,y in S), S)
        check(f'{w} {th}: 옆 홍옥 아이콘만 칩 없음', B and not any(x['offchip'] for x in B), B)
      pg.locator('[data-rred]:visible').first.click(); pg.wait_for_timeout(300)
      check(f'{w}: 예시 화면 클릭 = 예전과 같음(캐릭터 없음 → 창 안 열림; 실제 캐릭터 창은 test_b229_rred)', pg.locator('#rredModal').count()==0 and not errs, errs)
      pg.close()
finally: srv.terminate()
check('JS 오류 없음', not errs, errs)
sys.exit(1 if fails else 0)
