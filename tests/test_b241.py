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
        check('b242: 대기 중(12개 처치 후 스케줄러 수정)에도 빨간 안내', pg.evaluate("!!document.querySelector('#view .bover')"))
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,f'{PFX}_b242_pending_red_note.png'))
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
        TXT='*스케줄러에 등록된 보스가 12마리를 초과했거나, 보스 클리어 후 스케줄러를 수정하여\n 일부 보스가 미출력됩니다.'
        ov=pg.evaluate("(document.querySelector('#view .bover')||{}).innerText||''")
        check('b242: 빨간 안내 문구 정확히 두 줄', ov.replace('\r','')==TXT or ov.split('\n')==TXT.split('\n') or [x.strip() for x in ov.split('\n')]==[x.strip() for x in TXT.split('\n')], repr(ov))
        check('b242: 두 줄로 보임(높이)', pg.evaluate("(()=>{const o=document.querySelector('#view .bover'); return o.getClientRects().length>=2||o.getBoundingClientRect().height>parseFloat(getComputedStyle(o).lineHeight)*1.5})()"))
        pos=pg.evaluate("()=>{ const s=document.querySelector('#view .seg'), o=document.querySelector('#view .bover'), b=document.querySelector('#revAllBtn'); return !!(s&&o&&b)&&(s.compareDocumentPosition(o)&4)&&(o.compareDocumentPosition(b)&4)&&getComputedStyle(o).color; }")
        check('위치 = 월간 보스 버튼과 수익 기록 전체 수정 사이, 빨간색', bool(pos) and 'rgb(255, 77, 79)' == pos, pos)
        check('예상 수익도 12개 기준', pg.evaluate("expectedAll(S.characters[0]).length<=12"))
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,f'{PFX}_over12_red_note.png'))
        pg.evaluate("()=>{ const c=S.characters[0]; for(const b of BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).slice(0,1)) c.bosses[b.id].enabled=false; render(); }")
        check('12개 이하 → 안내 없음', pg.evaluate("!document.querySelector('#view .bover')"))
        # b242: 12개 등록·8개 처치, 안 잡은 보스를 스케줄러에서 다른 보스로 교체 → 바로 적용, 정상 표시(12개·새 보스 보임·옛 보스 없음·빨간 안내·대기 없음)
        sw=pg.evaluate("""()=>{ const W=BOSSES.filter(b=>b.type==='weekly'&&b.diffs.length).slice(-13);
          const c={id:'c1',name:'교체캐',level:285,job:'히어로',world:'스카니아',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}};
          W.slice(0,12).forEach((b,i)=>{ c.bosses[b.id]={enabled:true,diff:b.diffs[b.diffs.length-1],party:1}; if(i<8){ c.weekly[b.id]=true; c.auto[b.id]=true; } });
          S.characters=[c]; S.activeId='c1'; bossFilter='weekly'; save(); render(); return [W[11].id,W[12].id,W[12].name,W[11].name]; }""")
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,'swap_before.png'))
        pg.evaluate("""()=>{ const W=BOSSES.filter(b=>b.type==='weekly'&&b.diffs.length).slice(-13); const c=S.characters[0];
          const rows=W.slice(0,11).map((b,i)=>({content_name:b.name,difficulty:b.diffs[b.diffs.length-1],cycle:'bossWeekly',registration_flag:'true',complete_flag:i<8?'true':'false'}))
            .concat([{content_name:W[11].name,difficulty:W[11].diffs[W[11].diffs.length-1],cycle:'bossWeekly',registration_flag:'false',complete_flag:'false'},
                     {content_name:W[12].name,difficulty:W[12].diffs[0],cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]);
          applyScheduler(c,{date:S.period.week+'T00:00+09:00',boss_contents:rows}); save(); render(); }"""); pg.wait_for_timeout(300)
        r=pg.evaluate(f"""()=>{{ const c=S.characters[0]; const ids=[...document.querySelectorAll('#view .boss [data-drop]')].map(e=>e.dataset.drop.split('|')[0]);
          return {{rows:document.querySelectorAll('#view .boss').length, seg:document.querySelector('#view [data-filter=weekly]').textContent, newOn:bossOn(c,findBoss('{sw[1]}')), oldOn:bossOn(c,findBoss('{sw[0]}')), txt:document.querySelector('#view').innerText, red:!!document.querySelector('#view .bover'), pend:Object.keys(c.bossNext||{{}}).length}}; }}""")
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,'swap_after.png'))
        check('b242 교체: 바로 적용 — 새 보스 보임·옛 보스 없음', r['newOn'] and not r['oldOn'] and sw[2] in r['txt'], {k:r[k] for k in ('newOn','oldOn','rows','seg')})
        check('b242 교체: 12개·8/12·빨간 안내·대기 없음', r['rows']==12 and '8/12' in r['seg'] and not r['red'] and r['pend']==0, {k:r[k] for k in ('rows','seg','red','pend')})
        # b242: 10개 처치 상태에서 '잡은 보스'를 다른 보스로 교체 → 잡은 보스는 이번 주 그대로(클리어), 새 보스는 대기, 빨간 안내. 섞인 교체 = 안 잡은 쪽은 바로
        CS="""(mixed)=>{ const W=BOSSES.filter(b=>b.type==='weekly'&&b.diffs.length).slice(-14);
          const c={id:'c1',name:'잡은보스교체',level:285,job:'히어로',world:'스카니아',image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}};
          W.slice(0,12).forEach((b,i)=>{ c.bosses[b.id]={enabled:true,diff:b.diffs[b.diffs.length-1],party:1}; if(i<10){ c.weekly[b.id]=true; c.auto[b.id]=true; } });
          S.characters=[c]; S.activeId='c1'; bossFilter='weekly'; save(); render(); return W.map(b=>[b.id,b.name]); }"""
        CA="""(mixed)=>{ const W=BOSSES.filter(b=>b.type==='weekly'&&b.diffs.length).slice(-14); const c=S.characters[0]; const L=b=>b.diffs[b.diffs.length-1];
          const rows=W.slice(0,12).map((b,i)=>({content_name:b.name,difficulty:L(b),cycle:'bossWeekly',registration_flag:(i===0||(mixed&&i===11))?'false':'true',complete_flag:i<10?'true':'false'}))
            .concat([{content_name:W[12].name,difficulty:W[12].diffs[0],cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}])
            .concat(mixed?[{content_name:W[13].name,difficulty:W[13].diffs[0],cycle:'bossWeekly',registration_flag:'true',complete_flag:'false'}]:[]);
          applyScheduler(c,{date:S.period.week+'T00:00+09:00',boss_contents:rows}); save(); render(); }"""
        W=pg.evaluate(CS,False)
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,'cleared_swap_before.png'))
        pg.evaluate(CA,False); pg.wait_for_timeout(300)
        r=pg.evaluate(f"""()=>{{ const c=S.characters[0]; return {{rows:document.querySelectorAll('#view .boss').length, seg:document.querySelector('#view [data-filter=weekly]').textContent,
          xOn:bossOn(c,findBoss('{W[0][0]}')), xClr:!!c.weekly['{W[0][0]}'], yOn:bossOn(c,findBoss('{W[12][0]}')), next:c.bossNext||{{}}, red:!!document.querySelector('#view .bover')}}; }}""")
        if SD: pg.locator('#view').screenshot(path=os.path.join(SD,'cleared_swap_after.png'))
        check('b242 잡은 보스 교체: 잡은 보스 이번 주 그대로(클리어 표시), 새 보스 대기, 12개·10/12', r['xOn'] and r['xClr'] and not r['yOn'] and r['rows']==12 and '10/12' in r['seg'], r)
        check('b242 잡은 보스 교체: 대기 = 새 보스 켜기 + 잡은 보스 빼기, 빨간 안내', r['next'].get(W[12][0],{}).get('enabled')==True and r['next'].get(W[0][0],{}).get('enabled')==False and r['red'], r['next'])
        pg.reload(); pg.wait_for_timeout(800); pg.evaluate("render()")
        check('b242 대기 유지(새로고침)·빨간 안내', pg.evaluate("Object.keys(S.characters[0].bossNext||{}).length==2&&!!document.querySelector('#view .bover')"))
        pg.evaluate("()=>{ S.period.week='2000-01-06'; checkResets(); render(); }")
        st=pg.evaluate(f"()=>{{const c=S.characters[0]; return [c.bosses['{W[0][0]}']?.enabled, c.bosses['{W[12][0]}']?.enabled, !c.bossNext, BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).length]}}")
        check('b242 목 리셋: 잡은 보스 빠지고 새 보스 켜짐(12개)', st==[False,True,True,12], st)
        # 섞인 교체: 잡은 X 빼고 + 안 잡은 Z(11번) 빼고, 새 Y·V 등록 → 빈 칸 1개 = 가격 높은 새 보스 바로, 나머지 대기
        W=pg.evaluate(CS,True); pg.evaluate(CA,True); pg.wait_for_timeout(200)
        m=pg.evaluate(f"""()=>{{ const c=S.characters[0]; const on=id=>bossOn(c,findBoss(id)); return {{z:on('{W[11][0]}'), y:on('{W[12][0]}'), v:on('{W[13][0]}'), x:on('{W[0][0]}'), next:Object.keys(c.bossNext||{{}}), rows:document.querySelectorAll('#view .boss').length, red:!!document.querySelector('#view .bover')}}; }}""")
        check('b242 섞인 교체: 안 잡은 보스는 바로 빠짐, 새 보스 1개 바로·1개 대기, 잡은 보스 그대로, 12개·빨간 안내', (not m['z']) and m['x'] and (m['y']!=m['v']) and len(m['next'])==2 and m['rows']==12 and m['red'], m)
        check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
