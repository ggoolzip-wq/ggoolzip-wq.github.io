# b171: 가격 카드 '마지막 확인' = checkedAt·테섭 예정 반영(detectedAt) 중 늦은 것 + 테섭 반영 시각 표시 + prices.json 5분 단위 재요청(내용 바뀌면 다시 그림)
import os, sys, json, subprocess, time, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen(['python3','-m','http.server','8879','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8879/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
base=json.load(open(ROOT+'/prices.json',encoding='utf-8'))
cur={'pj':dict(base,checkedAt='2026-10-14T09:00:00+09:00',changedAt='2026-09-17',upcoming={'source':{'url':'https://x/Testworld/News/Update/1','title':'테섭 공지','date':'2026-10-15'},'rows':[{'boss':'선택받은 세렌 (하드)','new':1234567}],'detectedAt':'2026-10-15T16:27:00+09:00'})}
urls=[]
CH="{id:'c1',name:'단풍용사',level:287,job:'히어로',world:'스카니아',isMain:true,ocid:'',bosses:{seren:{enabled:true,diff:'hard',party:1}},weekly:{},monthly:{},auto:{},sync:{},drops:{}}"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1400,390):
        pg=b.new_page(viewport={'width':w,'height':900}); pg.on('pageerror',lambda e:errs.append(str(e)))
        def h(route):
            urls.append(route.request.url); route.fulfill(status=200,content_type='application/json',body=json.dumps(cur['pj'],ensure_ascii=False))
        pg.route('**/prices.json*',h)
        pg.goto('http://127.0.0.1:8879/index.html'); pg.wait_for_timeout(500)
        pg.evaluate("(()=>{const st=JSON.parse(JSON.stringify(S));st.characters=[%s];st.activeId='c1';S=normState(st);render();})()"%CH)
        pg.wait_for_function("!!document.querySelector('.pricecard .pc-foot')&&officialInfo&&officialInfo.upAt",timeout=8000); pg.evaluate('render()')
        f=pg.inner_text('.pricecard .pc-foot')
        check(f'{w}: 테섭 반영이 더 늦으면 마지막 확인 = 테섭 반영 시각', '마지막 확인 10.15 16:27' in f, f)
        check(f'{w}: 테섭 예정 줄에 반영 시각', '테섭 공지 (반영 10.15 16:27)' in f, f)
        check(f'{w}: 하루 단위 ?d= 대신 5분 단위 ?t=', urls and '?t=' in urls[-1] and '?d=' not in urls[-1], urls[-1:])
        cur['pj']=dict(cur['pj'],checkedAt='2026-10-15T20:30:00+09:00')
        pg.evaluate("fetchOfficialPrices()"); pg.wait_for_timeout(700)
        f=pg.inner_text('.pricecard .pc-foot')
        check(f'{w}: 다시 받은 prices.json 의 새 checkedAt 이 바로 표시', '마지막 확인 10.15 20:30' in f, f)
        n=len(urls); pg.evaluate("fetchOfficialPrices()"); pg.wait_for_timeout(500)
        check(f'{w}: 같은 내용이면 다시 그리지 않음(요청은 함)', len(urls)==n+1 and '10.15 20:30' in pg.inner_text('.pricecard .pc-foot'))
        cur['pj']=dict(cur['pj'],checkedAt='2026-10-14T09:00:00+09:00')
        pg.close()
    check('JS 오류 없음', not errs, errs)
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs); sys.exit(1 if fails or errs else 0)
