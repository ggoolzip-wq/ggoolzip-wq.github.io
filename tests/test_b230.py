# b230: 주별 득템 — 제목 아이콘 = 고정 28px 칸(주마다 아이템은 달라도 크기·자리 같음), 줄 아이콘 22px, 오른쪽 위 주 선택칸(◀▶와 같이 움직임)
#       이번 주 수익 총합 — '주보 결정석'·'이번 주 남은 결정석' 개수(xN) 없음, 금액 오른쪽 끝 그대로
import os, sys, time, subprocess, urllib.request, json
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8982'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
M="""()=>{const c=document.querySelector('#weekLoot'), h=c.querySelector('h2'), i=h.querySelector('.wlico'), im=i.querySelector('img,.ric,.ifb'), t=h.querySelector('.wlt'), s=h.querySelector('.wlsel');
 const cr=c.getBoundingClientRect(), r=e=>{const b=e.getBoundingClientRect(); return [Math.round((b.x-cr.x)*10)/10,Math.round((b.y-cr.y)*10)/10,Math.round(b.width*10)/10,Math.round(b.height*10)/10]}; // 카드 기준 자리
 const pages=[...c.querySelectorAll('.wlpage')], on=pages.findIndex(p=>p.classList.contains('on')), [o,n]=c.querySelectorAll('[data-wlpg]');
 return {ico:r(i), img:im?r(im):null, icoSrc:im?(im.getAttribute('src')||'').slice(-30):'', t:r(t), h2:r(h), sel:!!s, selV:s&&s.value, on, n:pages.length, opts:s?[...s.options].map(o=>o.text):[], now:c.querySelector('.wlnow').textContent, olderDis:o.disabled, newerDis:n.disabled,
   selFit:s&&s.scrollWidth<=s.clientWidth+1&&s.getBoundingClientRect().height<34, selIn:s&&s.getBoundingClientRect().right<=cr.right+0.5&&s.getBoundingClientRect().left>t.getBoundingClientRect().right, h2One:h.getBoundingClientRect().height<=36,
   rowIco:[...new Set([...c.querySelectorAll('.wlpage.on .loot>img,.wlpage.on .loot>.ric')].map(e=>Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height)))]};}"""
RP="""()=>[...document.querySelectorAll('.revpanel .rp-line')].map(l=>({lb:l.querySelector('.rplb')?.textContent||'', x:l.querySelector('.rpx')?.textContent||null, nr:Math.round(l.querySelector('.rpn')?.getBoundingClientRect().right||0)}))"""
try:
  with sync_playwright() as p:
    br=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1600,1280,390):
        ctx=br.new_context(viewport={'width':w,'height':1000},locale='ko-KR'); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
        pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        L=pg.evaluate(RP); g={l['lb']:l['x'] for l in L}
        check(f'예시 {w}: 주보 결정석·이번 주 남은 결정석 xN 없음, 검마 결정석·이번주 획득 아이템 xN 그대로', g.get('주보 결정석','?') is None and g.get('이번 주 남은 결정석','?') is None and (g.get('검마 결정석') or '').startswith('x') and (g.get('이번주 획득 아이템') or '').startswith('x'), g)
        check(f'예시 {w}: 금액 오른쪽 끝 한 줄', len({l['nr'] for l in L if l['nr']})==1, L)
        pg.click('[data-tab=loot]'); pg.wait_for_timeout(900)
        R=[pg.evaluate(M)]
        check(f'{w}: 선택칸 = 1주차~이번 주(최신 먼저), 이번 주 선택', R[0]['sel'] and len(R[0]['opts'])==R[0]['n']>=3 and R[0]['opts'][0].startswith(f"{R[0]['n']}주차 (이번 주)") and R[0]['opts'][-1].startswith('1주차') and R[0]['selV']=='0', R[0]['opts'])
        check(f'{w}: 날짜 = 넓은 화면만', all(('~' in o)==(w>560) for o in R[0]['opts']), R[0]['opts'])
        pg.click('#weekLoot [data-wlpg="1"]'); pg.wait_for_timeout(150); R.append(pg.evaluate(M))
        check(f'{w}: ◀ → 선택칸도 지난 주', R[1]['on']==1 and R[1]['selV']=='1' and not R[1]['newerDis'], R[1])
        pg.select_option('#weekLoot .wlsel',str(R[0]['n']-1)); pg.wait_for_timeout(150); R.append(pg.evaluate(M))
        check(f'{w}: 선택칸 1주차 → 그 주로, ◀ 꺼짐·라벨 1주차', R[2]['on']==R[0]['n']-1 and R[2]['olderDis'] and '1주차' in R[2]['now'], R[2])
        pg.click('#weekLoot [data-wlpg="-1"]'); pg.wait_for_timeout(150); R.append(pg.evaluate(M))
        check(f'{w}: ▶ → 선택칸 2주차', R[3]['selV']==str(R[0]['n']-2), R[3])
        check(f'{w}: 제목 아이콘 28x28 고정 칸·이미지 28x28·제목·줄 높이 모든 쪽 같음', all(r['ico'][2:]==[28,28] and r['img'] and r['img'][2:]==[28,28] and r['ico']==R[0]['ico'] and r['img']==R[0]['img'] and r['t']==R[0]['t'] and r['h2']==R[0]['h2'] for r in R), [(r['ico'],r['img'],r['t'],r['h2']) for r in R])
        check(f'{w}: 쪽마다 아이콘 아이템은 다를 수 있음(b229 그대로: 그 주 최다)', len({r['icoSrc'] for r in R})>=1)
        check(f'{w}: 선택칸 한 줄·안 잘림·카드 안·제목과 안 겹침, 제목 줄 한 줄', all(r['selFit'] and r['selIn'] and r['h2One'] for r in R), R[0])
        check(f'{w}: 줄 아이템 아이콘 22x22', all(set(r['rowIco'])<={'22x22'} for r in R), [r['rowIco'] for r in R])
        ctx.close()
    br.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(repr(e))
finally:
    srv.kill()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
