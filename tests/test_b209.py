# b209: 로그인 전 첫 화면 '+ 캐릭터 추가' 버튼 테두리 네온(느린 숨쉬기·줄이기 설정이면 고정) + 캐릭터 추가 창 'API 발급 : 링크' 아래 발급 순서 안내
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8993'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b209_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
EXP=['①링크 클릭 후 넥슨 로그인','②이용약관 스크롤 끝까지 내린 후 약관 동의','③어떤 게임으로 애플리케이션을 만드실 건가요?','☞ 메이플스토리','④아직 개발 단계인가요? 아니면 서비스 출시 단계인가요?','☞ 개발 단계','⑤출시할 서비스명을 설정해주세요','☞ 메보기',"⑥마이페이지 - 애플리케이션 목록 - 서비스명 '메보기' 클릭",'⑦첫번째 API key 옆 복사버튼 누른 후 API키 입력란에 Ctrl+V']
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for th in ('dark','light'):
      for rm in ('no-preference','reduce'):
        ctx=b.new_context(viewport={'width':1400,'height':1000},locale='ko-KR',reduced_motion=rm); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        ctx.route('http://127.0.0.1:9996/**',lambda r:r.fulfill(status=401,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},content_type='application/json',body='{"error":"no_session"}'))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate(f"localStorage.setItem('mapleBossTracker.theme','{th}');localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9996')"); pg.reload(); pg.wait_for_timeout(1200)
        r=pg.evaluate("(()=>{const b=document.getElementById('importAccBtn'),c=getComputedStyle(b),a=getComputedStyle(b,'::after');return {bs:c.boxShadow,an:a.animationName,dur:a.animationDuration,bw:c.borderTopWidth,h:b.getBoundingClientRect().height,one:b.scrollWidth<=b.clientWidth+1}})()")
        if rm=='no-preference':
            check(f'{th}: 테두리 네온(겹 그림자) + 아주 느린 숨쉬기(5초)', r['bs'].count('rgba')>=3 and r['an']=='neonBreath' and r['dur']=='5s' and r['h']<40, r)
            pg.mouse.move(0,0); pg.wait_for_timeout(2500); shot(pg.locator('#view .dmkey'),f'button_{th}')
        else:
            check(f'{th}: 움직임 줄이기 → 고정 네온(애니메이션 없음)', r['an']=='none' and r['bs'].count('rgba')>=3, r)
        if th=='dark' and rm=='no-preference':
            pg.click('#importAccBtn'); pg.wait_for_timeout(500)
            g=pg.evaluate("""(()=>{const s=document.getElementById('svMainSec');if(!s) return null;const api=s.querySelector('.svmapi'),ol=s.querySelector('.apiguide');
              const lines=ol?[...ol.querySelectorAll('li')].flatMap(li=>{const a=li.querySelector('.aga');const main=li.querySelector('.agn').textContent+li.querySelector('.agt').textContent;return a?[main,a.textContent]:[main]}):[];
              const fit=ol?[...ol.querySelectorAll('li,.aga')].every(e=>e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().right<=ol.getBoundingClientRect().right+0.5):false;
              const ind=ol?[...ol.querySelectorAll('.aga')].every(a=>a.getBoundingClientRect().left>a.closest('li').getBoundingClientRect().left+8):false;
              const oneLine=ol?[...ol.querySelectorAll('.agt,.aga')].every(e=>e.getBoundingClientRect().height<24):false;
              return {apiTxt:api&&api.textContent.trim(),apiFirst:api&&ol&&(api.compareDocumentPosition(ol)&4)>0,lines,fit,ind,oneLine,fam:ol&&getComputedStyle(ol).fontFamily.split(',')[0],bodyFam:getComputedStyle(document.body).fontFamily.split(',')[0]}})()""")
            check("'API 발급 : 링크' 그대로 + 바로 아래 안내", g and g['apiTxt'].startswith('API 발급 : https://openapi.nexon.com/') and g['apiFirst'], g)
            check('안내 문구 = 사용자 문구 그대로(①~⑦, ☞ 줄)', g and g['lines']==EXP, g and g['lines'])
            check('☞ 줄 들여쓰기·한 줄·안 잘림·일반 글꼴', g and g['ind'] and g['fit'] and g['oneLine'] and g['fam']==g['bodyFam'], g and {k:g[k] for k in ('fit','ind','oneLine','fam','bodyFam')})
            shot(pg.locator('#importModal .modal'),'window_dark')
            pg.evaluate("localStorage.setItem('mapleBossTracker.theme','light');applyTheme()"); pg.wait_for_timeout(200); shot(pg.locator('#importModal .modal'),'window_light')
            pg.set_viewport_size({'width':390,'height':900}); pg.wait_for_timeout(300)
            g=pg.evaluate("(()=>{const ol=document.querySelector('#svMainSec .apiguide');return {fit:[...ol.querySelectorAll('li,.aga')].every(e=>e.scrollWidth<=e.clientWidth+1),over:ol.scrollWidth>ol.clientWidth+1}})()")
            check('390px(휴대폰)도 안 잘림·가로 넘침 없음', g['fit'] and not g['over'], g)
            shot(pg.locator('#importModal .modal'),'window_mobile')
        ctx.close()
    b.close()
finally: srv.terminate()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
