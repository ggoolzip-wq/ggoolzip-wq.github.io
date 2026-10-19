import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8871=_tutil.free_port()
# b161: 캐릭터·로그인 없이도 LIVE 배지(로드 직후) + 라이브 탭 유튜브 플레이어(클릭 시 iframe, autoplay 없음), 모바일 탭 줄 자동 노출
import os, sys, json, subprocess, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = _P8871
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
LIVE = {"at": int(time.time()*1000), "yt": {"live": True, "vid": "IkEDT0Wy8zY", "url": "https://www.youtube.com/watch?v=IkEDT0Wy8zY", "title": "테스트 라이브", "checked_at": int(time.time()*1000)}, "nx": {"live": False}, "list": []}
srv = _tutil.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for w in (1280, 390):
            pg = b.new_page(viewport={"width": w, "height": 800}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("**/api/live*", lambda r: r.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(LIVE)))
            pg.route("https://open.api.nexon.com/**", lambda r: r.abort())
            pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
            check(f"{w}: 로드 직후 LIVE 배지 표시", pg.evaluate("!document.getElementById('liveBadge').hidden"))
            pg.wait_for_timeout(2500)
            vis = pg.evaluate("(()=>{const t=document.querySelector('[data-tab=live]').getBoundingClientRect(),n=document.querySelector('.tabs').getBoundingClientRect();return t.left>=n.left-1&&t.right<=n.right+1})()")
            check(f"{w}: 라이브 탭 버튼이 화면 안", vis, pg.evaluate("[document.querySelector('.tabs').scrollLeft,document.querySelector('.tabs').scrollWidth,document.querySelector('.tabs').clientWidth]"))
            pg.click("[data-tab=live]"); pg.wait_for_timeout(500)
            check(f"{w}: 캐릭터 없어도 라이브 화면", pg.evaluate("!!document.querySelector('#view .lvgrid')&&!document.querySelector('#view .card.empty')"))
            lay = pg.evaluate("(()=>{const c=[...document.querySelectorAll('#view .lvcol')],v=document.querySelector('#view .lvgrid').getBoundingClientRect(),r=c[0].getBoundingClientRect(),ls=[...document.querySelectorAll('#view .lvlink')].map(a=>a.href);return [c.length,Math.abs((r.left+r.right)/2-(v.left+v.right)/2)<3,ls,document.querySelector('#view .lvlist h2').innerText]})()")
            check(f"{w}: 넥슨 칸 없음·유튜브 중앙·유튜브 링크 아래 넥슨 링크·'라이브 저장소'", lay[0]==1 and lay[1] and len(lay[2])==2 and 'youtube' in lay[2][0] and lay[2][1]=='https://live.nexon.com/channels/23' and lay[3]=='라이브 저장소', lay)
            check(f"{w}: b168 '1분마다 서버가 확인해요·마지막 확인' 문구 없음(요소 삭제)", pg.evaluate("!/1분마다 서버|마지막 확인/.test(document.querySelector('#view').innerText) && (()=>{const c=document.querySelector('#view .lvlist');const l=c.lastElementChild;return !(l&&l.matches('p.tiny'))})()"))
            check(f"{w}: 클릭 전에는 iframe 없음(자동재생 안 함)", pg.evaluate("!document.querySelector('#view iframe')"))
            pg.click("#view .lvplay[data-embed*='IkEDT0Wy8zY']"); pg.wait_for_timeout(300)
            src = pg.evaluate("(document.querySelector('#view iframe')||{}).src||''")
            check(f"{w}: 클릭 → 유튜브 임베드", "IkEDT0Wy8zY" in src, src)
            check(f"{w}: JS 오류 없음", not errs, errs); pg.close()
        # 라이브 없음(가짜 데이터): 배지 숨김 + 핑크빈 + '라이브 일정이 없습니다.'
        OFF = {"at": LIVE["at"], "yt": {"live": False, "thumb": "https://i.ytimg.com/x.jpg", "checked_at": LIVE["at"]}, "nx": {"live": False}, "list": []}
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.route("**/api/live*", lambda r: r.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps(OFF)))
        pg.route("https://open.api.nexon.com/**", lambda r: r.abort()); pg.route("https://i.ytimg.com/**", lambda r: r.abort())
        pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        pg.click("[data-tab=live]"); pg.wait_for_timeout(500)
        r = pg.evaluate("(()=>{const n=document.querySelector('#view .lvnone'),i=n&&n.querySelector('img.pinkbean');return [document.getElementById('liveBadge').hidden,!!n&&n.innerText.trim(),!!i&&i.naturalWidth>50&&i.src.startsWith('data:image/png'),!document.querySelector('#view .lvplay[data-embed]'),i&&n.querySelector('span')&&i.getBoundingClientRect().bottom<=n.querySelector('span').getBoundingClientRect().top]})()")
        check("라이브 없음: 배지 숨김·문구·핑크빈(내장, 문구 위)·재생 버튼 없음", r[0] and r[1]=="라이브 일정이 없습니다." and r[2] and r[3] and r[4], r)
        pc = pg.evaluate("(()=>{const i=document.querySelector('.pinkbean').getBoundingClientRect(),t=document.querySelector('.lvnone span').getBoundingClientRect();return [i.left+i.width*39/109,(t.left+t.right)/2]})()")
        check("핑크빈 몸통 중심 = 문구 가운데(±2px)", abs(pc[0]-pc[1]) <= 2, pc)
        pg.screenshot(path="/workspace/maple-boss-tracker/b161_after_livetab_off.png"); pg.close()
        b.close()
finally:
    srv.terminate()
print("FAILS:", fails); sys.exit(1 if fails else 0)
