# b162: 디지털 숫자 1.4배 + 카운팅 애니메이션 (0→최종, 같은 값 재렌더 시 반복 안 함, 폭 고정, reduced-motion, 최종값 일치, 잘림 없음)
import os, sys, subprocess, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 8873
src = open(os.path.join(ROOT, "tests", "test_tracker81.py")).read(); NS = {}; exec(src[src.index("B=lambda"):src.index("\ntry:")], NS)
fails = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + (" — " + str(d) if d != "" else ""))
    if not c: fails.append(n)
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
VIS = "(sel=>{const t=document.querySelector(sel);return [...t.querySelectorAll('.tir-g path.tl')].length})"
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for w, rm in ((1400, "no-preference"), (390, "no-preference"), (1400, "reduce")):
            pg = b.new_page(viewport={"width": w, "height": 900}, reduced_motion=rm); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.route("https://open.api.nexon.com/**", lambda r: r.abort())
            pg.goto(f"http://127.0.0.1:{PORT}/index.html"); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}", NS["ST"]); pg.reload()
            pg.wait_for_timeout(300); pg.evaluate("(()=>{const t=localStorage.getItem('mapleBossTracker.tab');if(TABS.includes(t)&&t!==tab){tab=t;syncTabs();render();}})()")
            pg.evaluate(NS["SETUP"]); pg.wait_for_timeout(150)
            st = pg.evaluate("[...document.querySelectorAll('.stats .tir[data-tv]')].map(e=>[e.dataset.tk,e.dataset.tanim||'',e.getBoundingClientRect().width,e.style.minWidth])")
            if rm == "reduce":
                check(f"{w}/reduce: 애니메이션 없음", all(x[1] == "" for x in st), st)
            else:
                check(f"{w}: 화면 안 숫자 카운팅 시작 + 폭 고정", any(x[1] == "run" and x[3] for x in st), st)
            pg.wait_for_timeout(1600)
            fin = pg.evaluate("[...document.querySelectorAll('#view .tir[data-tv]')].filter(e=>e.dataset.tanim).map(e=>{const t=document.createElement('span');t.innerHTML=tir(({eok:fmtEok,meso})[e.dataset.tf](+e.dataset.tv)+(e.dataset.ts||''));return [e.dataset.tk,e.innerHTML===t.firstChild.innerHTML,e.dataset.tanim,e.style.minWidth]})")
            check(f"{w}/{rm}: 끝나면 최종값 그대로(포맷 동일)·폭 고정 해제", all(x[1] and x[2] == "done" and not x[3] for x in fin), fin)
            sm2 = pg.evaluate("[...document.querySelectorAll('.stats .tsm')].map(t=>[t.parentElement.id||t.parentElement.className,t.innerText.trim(),getComputedStyle(t.querySelector('.tl')).fill===getComputedStyle(t.parentElement).color])")
            check(f"{w}: 수익 분석 보조 문구 작은 디지털·원래 색", len(sm2) == 3 and all(x[2] for x in sm2) and sm2[0][1].startswith('주 평균'), sm2)
            pg.evaluate("render()"); pg.wait_for_timeout(200)
            again = pg.evaluate("[...document.querySelectorAll('.stats .tir[data-tv]')].map(e=>e.dataset.tanim||'')")
            check(f"{w}/{rm}: 같은 값 재렌더 → 반복 안 함", all(a == "" for a in again), again)
            sz = pg.evaluate("(()=>{const g=document.querySelector('.stats .tir .tir-g'),v=g.closest('.v');return [g.getBoundingClientRect().height,parseFloat(getComputedStyle(v).fontSize)]})()")
            check(f"{w}: 숫자 크기 1.4배 (숫자 높이 ≈ 1.27×글자크기)", abs(sz[0] / sz[1] - 1.4 * 0.905) < .05, sz)
            clip = pg.evaluate("[...document.querySelectorAll('#view .tir, #charList .tir')].filter(t=>{const gs=[...t.querySelectorAll('.tir-g')].map(x=>x.getBoundingClientRect().top);if(gs.length>1&&Math.abs(gs[0]-gs[gs.length-1])>2)return true;const r=t.getBoundingClientRect(),c=t.closest('.stat,.sl,.rp-total,.card');if(!c)return false;const q=c.getBoundingClientRect();return r.right>q.right+1}).map(t=>t.innerText)")
            check(f"{w}: 디지털 글씨 줄바꿈·넘침 없음(수익 분석)", not clip, clip)
            pg.evaluate("tab='boss';syncTabs();render()"); pg.wait_for_timeout(600)
            rp = pg.evaluate("[...document.querySelectorAll('.revpanel .rp-cry,.revpanel .rp-sale')].map(l=>[l.querySelectorAll('.tsm').length,l.querySelectorAll('.ric,img,svg.mi,.mi').length>0,l.querySelector('.rpl').scrollWidth<=l.querySelector('.rpl').clientWidth+1,l.getBoundingClientRect().height<52,[...l.querySelectorAll('.tsm .tl')].every(x=>getComputedStyle(x).fill===getComputedStyle(l).color)])")
            check(f"{w}: 이번 주 수익 두 줄 작은 디지털·아이콘 유지·잘림/줄바꿈 없음·원래 색", len(rp) == 2 and rp[0][0] >= 3 and rp[1][0] >= 2 and all(x[1] and x[2] and x[3] and x[4] for x in rp), rp)
            pg.evaluate("tab='loot';syncTabs();render()"); pg.wait_for_timeout(1700)
            lt = pg.evaluate("(()=>{const c=document.querySelector('#lootTop');return [c.querySelectorAll('.tir').length,[...c.querySelectorAll('.tir[data-tv]')].every(e=>e.dataset.tdone==='1'),c.querySelector('#ltTotal .v').innerText.trim(),/^상위 /.test(c.querySelector('#ltRing .v').innerText.trim())||c.querySelector('#ltRing .v').innerText.trim()=='-',c.querySelector('.kt').innerText,[...c.querySelectorAll('.tir')].every(t=>!t.querySelector('.tir-k'))]})()")
            check(f"{w}: 누적 득템 숫자+단위 디지털(개/회/%/인/승/패 픽셀), 이름 그대로, 카운팅 끝", lt[0] >= 4 and lt[1] and lt[2].endswith('개') and lt[3] and lt[4] == '총 득템' and lt[5], lt)
            sm = pg.evaluate("(()=>{const r=[];document.querySelectorAll('#view .tsm').forEach(t=>{const m=t.parentElement,g=t.querySelector('.tir-g'),l=t.querySelector('.tl');r.push([m.id||m.className,parseFloat(getComputedStyle(t).fontSize)/parseFloat(getComputedStyle(m).fontSize)>1.28,getComputedStyle(g).filter==='none',getComputedStyle(l).fill===getComputedStyle(m).color,!t.dataset.tv,!t.querySelector('.tir-k')])});return r})()")
            check(f"{w}: 누적 득템 작은 문구 = 작은 디지털(같은 크기·원래 색·글로우/카운팅 없음·전부 픽셀 글리프)", len(sm) >= 2 and all(all(x[1:]) for x in sm), sm)
            mv = pg.evaluate("[...document.querySelectorAll('#lootTop .stat .v .tir')].map(t=>[t.innerText.trim(),getComputedStyle(t.querySelector('.tir-g')).filter!=='none'])")
            check(f"{w}: 누적 득템 메인 값만 큰 디지털(글로우)", len(mv) == 3 and all(x[1] for x in mv), mv)
            check(f"{w}: JS 오류 없음", not errs, errs); pg.close()
        b.close()
finally:
    srv.terminate()
print("FAILS:", fails); sys.exit(1 if fails else 0)
