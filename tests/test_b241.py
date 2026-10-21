# test_b241: 주간 보스 12개를 다 잡은 뒤 스케줄러(게임)에서 보스를 바꾸면 → 이번 주는 그대로(최대 12), 바뀐 등록은 목 리셋 때 적용 (c.bossNext)
# MBT_SHOTDIR=폴더 → 재현 화면 사진 · MBT_ROOT=다른 빌드(변경 전 사진만)
import os, sys, subprocess, time, urllib.request, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK=not os.environ.get('MBT_ROOT'); SD=os.environ.get('MBT_SHOTDIR'); PFX='after' if CHECK else 'before'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_tutil.free_port()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
# 12개 클리어 + 1개(새로 등록, 안 잡음) — 실제 보스 id 는 페이지에서 고름
SETUP="""()=>{ const W=BOSSES.filter(b=>b.type==='weekly'&&b.diffs.length).slice(-13); const lim=S.settings.weeklyLimit;
  const c={id:'c1',name:'다잡은캐',level:285,job:'히어로',world:'스카니아',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}};
  W.slice(0,12).forEach(b=>{ c.bosses[b.id]={enabled:true,diff:b.diffs[b.diffs.length-1],party:1}; c.weekly[b.id]=true; c.auto[b.id]=true; });
  S.characters=[c]; S.activeId='c1'; save();
  const rows=W.slice(0,12).map(b=>({content_name:b.name,difficulty:b.diffs[b.diffs.length-1],cycle:'bossWeekly',registration_flag:'true',complete_flag:'true'}))
    .concat([{content_name:W[12].name,difficulty:W[12].diffs[0],cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]);
  window.__new=W[12].id; window.__rows=rows; sessionStorage.setItem('t241rows',JSON.stringify(rows)); return [lim,W[12].id,W[12].name]; }"""
APPLY="()=>{ const c=S.characters[0]; applyScheduler(c,{date:S.period.week+'T00:00+09:00',boss_contents:(window.__rows||JSON.parse(sessionStorage.getItem('t241rows'))),weekly_boss_clear_count:12,weekly_boss_clear_limit_count:12}); save(); render(); }"
CNT="()=>{ const c=S.characters[0]; return [BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).length, weeklyCount(c), document.querySelectorAll('#view .boss').length]; }"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1500},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("()=>{localStorage.clear();localStorage.setItem('mapleBossTracker.tab','boss')}"); pg.reload(); pg.wait_for_timeout(900)
    info=pg.evaluate(SETUP); pg.evaluate("render()"); pg.wait_for_timeout(200)
    pg.evaluate(APPLY); pg.wait_for_timeout(300)
    n=pg.evaluate(CNT); print('counts (enabled weekly, cleared, rows):',n)
    if SD: pg.locator('#view').screenshot(path=os.path.join(SD,f'{PFX}_full12_sched_edit.png'))
    if SD and not CHECK:
        pg.evaluate(SETUP); pg.evaluate("()=>{ const c=S.characters[0]; Object.keys(c.weekly).forEach(k=>{delete c.weekly[k];}); window.__rows.forEach(r=>r.complete_flag='false'); }"); pg.evaluate(APPLY); pg.wait_for_timeout(300)
        pg.locator('#view').screenshot(path=os.path.join(SD,f'{PFX}_over12_red_note.png'))
    if CHECK:
        nid=info[1]
        check('12개 다 잡은 뒤 스케줄러 변경 → 이번 주 주간 보스 12개 그대로', n[0]==12 and n[1]==12, n)
        check('새 등록은 대기(c.bossNext) — 이번 주엔 꺼져 있음', pg.evaluate(f"!S.characters[0].bosses['{nid}']?.enabled && !!S.characters[0].bossNext?.['{nid}']"), pg.evaluate("S.characters[0].bossNext"))
        check('안내 문구(목요일 초기화 때 적용)', '목요일' in pg.inner_text('#view') and info[2] in pg.inner_text('#view .bnext'), pg.evaluate("(document.querySelector('#view .bnext')||{}).textContent"))
        pg.reload(); pg.wait_for_timeout(800)
        check('새로고침해도 대기 유지(저장)', pg.evaluate(f"!!S.characters[0].bossNext?.['{nid}'] && JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0].bossNext['{nid}'].enabled===true"))
        pg.evaluate(APPLY); check('같은 응답 다시 와도 12개 그대로', pg.evaluate(CNT)[0]==12)
        # 목 리셋: 지난 주로 돌려 checkResets
        pg.evaluate("()=>{ S.period.week='2000-01-06'; checkResets(); render(); }")
        st=pg.evaluate(f"()=>{{const c=S.characters[0]; return [c.bosses['{nid}']?.enabled, c.bosses['{nid}']?.diff, !c.bossNext||!Object.keys(c.bossNext).length, weeklyCount(c)]}}")
        check('목 리셋 때 대기 적용(켜짐·난이도)·대기 비움·처치 초기화', st[0]==True and st[2] and st[3]==0, st)
        # 12개 안 잡았으면 바로 적용
        pg.evaluate(SETUP); pg.evaluate("()=>{ const c=S.characters[0]; delete c.weekly[Object.keys(c.weekly)[0]]; window.__rows[0].complete_flag='false'; }"); pg.evaluate(APPLY)
        check('11개만 잡았으면 바로 적용(13개 등록)', pg.evaluate(f"S.characters[0].bosses['{nid}']?.enabled===true && !S.characters[0].bossNext?.['{nid}']") and pg.evaluate(CNT)[0]==13, pg.evaluate(CNT))
        # 대기 중 처치 체크를 풀어 12개 미만 → 다음 동기화 때 바로 적용
        pg.evaluate(SETUP); pg.evaluate(APPLY); pg.evaluate("()=>{ const c=S.characters[0]; delete c.weekly[Object.keys(c.weekly)[0]]; window.__rows[0].complete_flag='false'; }"); pg.evaluate(APPLY)
        check('대기 중 12개 미만이 되면 다음 적용 때 바로 켬', pg.evaluate(f"S.characters[0].bosses['{nid}']?.enabled===true && !S.characters[0].bossNext?.['{nid}']"))
        # rollPeriod (다른 기기 데이터) 도 적용
        x=pg.evaluate(f"()=>{{ const x=JSON.parse(JSON.stringify(S)); x.period.week='2000-01-06'; const c=x.characters[0]; c.bossNext={{'{nid}':{{enabled:true,diff:BOSSES.find(b=>b.id==='{nid}').diffs[0]}}}}; delete c.bosses['{nid}']; rollPeriod(x); return [x.characters[0].bosses['{nid}']?.enabled, !!x.characters[0].bossNext]; }}")
        check('다른 기기 상태(rollPeriod)도 리셋 때 적용', x[0]==True and not x[1], x)
        # 등록 13개(12개 초과) → 어디서나 12개, 처치한 보스는 항상 포함, 나머지 = 가격 높은 순, 빨간 안내
        pg.evaluate(SETUP); pg.evaluate("()=>{ const c=S.characters[0]; Object.keys(c.weekly).forEach(k=>{delete c.weekly[k]; delete c.auto[k];}); window.__rows.forEach(r=>r.complete_flag='false'); }"); pg.evaluate(APPLY)
        ids=pg.evaluate("()=>{ const c=S.characters[0]; const l=BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).map(b=>[b.id,Math.floor(price(b,c.bosses[b.id].diff)/1)]); l.sort((a,b)=>a[1]-b[1]); return l; }")
        cheap=ids[0][0]
        pg.evaluate(f"()=>{{ const c=S.characters[0]; c.weekly['{cheap}']=true; save(); bossFilter='weekly'; render(); }}")
        v=pg.evaluate("()=>{ const c=S.characters[0]; return {rows:document.querySelectorAll('#view .boss').length, seg:document.querySelector('#view [data-filter=weekly]').textContent, over:(document.querySelector('#view .bover')||{}).textContent||'', shown:[...weeklyShown(c)]}; }")
        check('등록 13개 → 카드 12개·카운트 /12', len(ids)==13 and v['rows']==12 and '/12' in v['seg'], (len(ids),v))
        check('처치한 보스(가장 싼 것)는 12개 안에 남음', cheap in v['shown'], (cheap,v['shown']))
        check('안 잡은 것 중 가장 싼 보스가 빠짐', ids[1][0] not in v['shown'], ids[:2])
        check('빨간 안내 문구 정확히', v['over']=='*스케줄러에 등록된 보스가 12마리를 초과하여 일부 보스가 미출력됩니다.', v['over'])
        pos=pg.evaluate("()=>{ const s=document.querySelector('#view .seg'), o=document.querySelector('#view .bover'), b=document.querySelector('#revAllBtn'); return !!(s&&o&&b)&&(s.compareDocumentPosition(o)&4)&&(o.compareDocumentPosition(b)&4)&&getComputedStyle(o).color; }")
        check('위치 = 월간 보스 버튼과 수익 기록 전체 수정 사이, 빨간색', bool(pos) and 'rgb(255, 77, 79)' == pos, pos)
        check('예상 수익도 12개 기준', pg.evaluate("expectedAll(S.characters[0]).length<=12"))
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,f'{PFX}_over12_red_note.png'))
        pg.evaluate("()=>{ const c=S.characters[0]; for(const b of BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).slice(0,1)) c.bosses[b.id].enabled=false; render(); }")
        check('12개 이하 → 안내 없음', pg.evaluate("!document.querySelector('#view .bover')"))
        check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
