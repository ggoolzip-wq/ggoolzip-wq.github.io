# b217: 시작 렌더 오류(admPrices TDZ)로 스크립트가 멈춰 body.html 뼈대('☁ 구글 로그인'·빈 화면)만 남던 문제
#  A) 예전 방식 본계정 키 삭제(세션 남음·키 없음) + 관리자 → 새로고침 = 예시 화면, 오류 없음, 서버 기록 유지 → 다시 등록하면 복원
#  B) 관리자 로그인 + 캐릭터 0명 → 새로고침해도 오류 없음, 헤더 로그아웃, 캐릭터 추가 화면
#  C) 정적 뼈대에 '구글' 문구 없음
import os, sys, json, subprocess, time, urllib.request, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
SHOT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out')
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
html=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
body=re.sub(r'<script[\s\S]*?</script>','',html[html.index('<body'):])
check('C: 정적 뼈대(스크립트 제외)에 구글 문구 없음, 헤더 버튼은 처음엔 숨김', '구글' not in body and re.search(r'id="gBtn"[^>]*hidden',body) is not None)
T=open(os.path.join(ROOT,'tests','test_b216.py'),encoding='utf-8').read(); exec(T[T.index("KA,KF="):T.index("if not cf_dev")])
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS:',fails); sys.exit(1 if fails else 0)
PORT, WP, NP = 8951, 8952, 8953
API=f'http://127.0.0.1:{WP}'; URL=f'http://localhost:{PORT}/index.html'
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # A
    c1,p1=mkctx(b); fresh(p1); login(p1,KA); wait_on(p1)
    p1.evaluate("S.characters.push({id:'c1',name:'본캐A',level:280,job:'히어로',world:'스카니아',ocid:'o-acc-A',accId:accounts()[0].id,isMain:true,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}});save();render();svSaveNow()"); wait_on(p1)
    p1.evaluate("accounts().forEach(a=>{a.key='';}); save(); render(); localStorage.setItem('mapleBossTracker.svAdmin','1')"); p1.wait_for_timeout(2500)
    n0=len(errs); p1.reload(); p1.wait_for_timeout(3000)
    check('A: 새로고침 → 예시 화면, 헤더 구글 없음, 스크립트 오류 없음', p1.locator('#view>.demotop').count()==1 and '구글' not in p1.inner_text('header') and len(errs)==n0 and not p1.evaluate("svTok()"), (p1.inner_text('header')[:60],errs[n0:]))
    p1.screenshot(path=SHOT+'/A_stale_keyless_admin_reload.png')
    check('A: 서버 기록 그대로', srvchars()==['c1'], srvchars())
    login(p1,KA); wait_on(p1); p1.wait_for_timeout(500)
    check('A: 같은 본계정 키 다시 등록 → 캐릭터 복원', [c['id'] for c in st(p1)['characters']]==['c1'] and p1.evaluate("S.characters.filter(charShown).length")==1)
    # B
    c2,p2=mkctx(b); fresh(p2); login(p2,'live_KEY_B_0123456789abcdef'); wait_on(p2)
    p2.evaluate("localStorage.setItem('mapleBossTracker.svAdmin','1')"); n0=len(errs); p2.reload(); p2.wait_for_timeout(3000)
    check('B: 관리자·캐릭터 0명 새로고침 → 오류 없음, 헤더 로그아웃, 추가 안내 화면', len(errs)==n0 and p2.evaluate("document.getElementById('gBtn').textContent")=='로그아웃' and p2.locator('#view .empty').count()==1, (errs[n0:],p2.evaluate("document.getElementById('gBtn').textContent")))
    p2.screenshot(path=SHOT+'/B_admin_zero_chars_reload.png')
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
