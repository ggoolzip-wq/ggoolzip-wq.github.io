# test_b323 (t586): 클리어 시간 — 14:30~15:30 사이 클리어(남은시간 ≈5:00 에서 5:00 리셋 → 점프가 작거나 없음)에도 끝을 ±3초 안으로 잡음,
# 점프를 못 본 경우는 '추정' 표시, 타이머로 끝을 하나도 못 잡으면(상자만) '추정', 일간 보스는 기록 안 함
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SIM="""([boss,tc,boxD,stopAfter])=>{ const A=window.AR; A.clr=null; A.clrHold=false; A.clrT=0; A.det={cid:'x',boss,diff:'hard',src:''}; A.cfg.clrOff=false; A.ocr=null;
  S.characters=[{id:'x',name:'x',bosses:{}}]; const t0=1e9; let rd=null; window.arClrRead=()=>rd; arClrMap({boss,diff:'hard'},t0);
  for(let e=5;e<=tc+boxD;e++){ const rem=e<tc?1200-e:300-(e-tc); if(stopAfter!=null&&e>stopAfter){ rd=null; continue; } rd={sec:rem,m:Math.floor(rem/60),s:rem%60}; arClrTick({},t0+e*1000+37); }
  const c=arClrFinish(boss,'hard',t0+(tc+boxD)*1000+37); return c&&{sec:c.sec,end:c.end,est:c.est}; }"""
HPSIM="""([boss,maps,hp,tc,boxD,stopAfter,rw])=>{ const A=window.AR; A.clr=null; A.clrHold=false; A.clrT=0; A.det={cid:'x',boss,diff:'hard',src:''}; A.cfg.clrOff=false; A.ocr=null;
  S.characters=[{id:'x',name:'x',bosses:{}}]; const t0=1e9; let rd=null, h=null; window.arClrRead=()=>rd; window.arBossHpMock=()=>h; arClrMap({boss,diff:'hard'},t0);
  const mp=e=>{ let m=maps[0][1]; for(const [s,n] of maps) if(e>=s) m=n; return m; };
  for(let e=5;e<=tc+boxD;e++){ const nm=mp(e); A.mapSt={boss,kind:'b',name:arNorm(nm),t:0}; h=null; for(const [a,b,f] of hp) if(e>=a&&e<b) h={frac:f};
    const rem=e<tc?1200-e:300-(e-tc); rd=(stopAfter!=null&&e>stopAfter)?null:{sec:rem,m:Math.floor(rem/60),s:rem%60}; arClrTick({},t0+e*1000+37); }
  if(rw) A.clr&&(A.clr.rwT=t0+rw*1000+37); window.arBossHpMock=null; const c=arClrFinish(boss,'hard',t0+(tc+boxD)*1000+37); return c&&{sec:c.sec,end:c.end,est:c.est}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    bad=[]
    for tc in range(870,931,3):
      r=pg.evaluate(SIM,['lotus',tc,8,None])
      if not r or abs(r['sec']-tc)>3: bad.append((tc,r))
      elif abs(tc-900)<=3 and not r['est']: bad.append((tc,'추정 아님',r))
    check('14:30~15:30 클리어(21가지) → 끝 오차 ≤3초, 점프 안 보이는 5:00±3초는 추정 표시',not bad,bad)
    r=pg.evaluate(SIM,['lotus',600,8,None]); check('10분 클리어(큰 점프) → 타이머 리셋, 추정 아님',r and abs(r['sec']-600)<=1 and r['end'] in('타이머 리셋','5:00 카운트다운') and not r['est'],r)
    r=pg.evaluate(SIM,['lotus',600,30,400]); check('타이머 400초 뒤 안 보임 → 끝=상자 → 추정',r and r['end']=='상자' and r['est'],r)
    dl='daily_zakum'  # 일간 보스는 BOSSES 에 없음
    r=pg.evaluate(SIM,[dl,300,8,None]) if dl else 'none'; check(f'일간 보스({dl}) 는 클리어 시간 기록 안 함',r is None,r)
    L=[[0,'경계하는 코어'],[200,'해방된 코어'],[500,'폭주하는 함선']]
    bad=[]
    for tc in range(885,916,3):
      r=pg.evaluate(HPSIM,['lotus',L,[[6,199,.9],[199,210,0],[210,500,.8],[500,tc,.7],[tc,tc+20,0]],tc,10,None,0])
      if not r or abs(r['sec']-tc)>1 or r['est'] or not r['end'].startswith('체력 0'): bad.append((tc,r))
    check('15분 근처 클리어 + 마지막 페이즈 체력 0 → 끝 오차 ≤1초, 추정 아님 (앞 페이즈 체력 0 은 무시)',not bad,bad)
    D=[[0,'세계수 정상']]
    r=pg.evaluate(HPSIM,['damien',D,[[6,400,.9],[400,405,0],[405,880,.8],[880,900,0]],880,10,None,0])
    check('같은 맵 다페이즈(데미안): 1페이즈 체력 0 → 재등장으로 취소, 끝=2페이즈 체력 0',r and abs(r['sec']-880)<=1 and r['end'].startswith('체력 0'),r)
    r=pg.evaluate(HPSIM,['damien',D,[[6,400,.9],[400,405,0],[405,880,.8]],880,10,None,0])
    check('체력 0 후 재등장만 (마지막 아님) → 체력 0 으로 기록 안 함',r and not r['end'].startswith('체력 0'),r)
    r=pg.evaluate(HPSIM,['lotus',L,[[6,500,.9],[500,700,.6],[700,720,0]],700,25,699,712])
    check('체력 0 후 타이머 안 보임 → 보상(맵)으로 확정, 끝=체력 0',r and abs(r['sec']-700)<=1 and r['end']=='체력 0+보상',r)
    r=pg.evaluate(HPSIM,['lotus',L,[[6,500,.9]],700,25,None,0])
    check('체력바 없이 큰 점프 → 5:00 카운트다운 역산',r and abs(r['sec']-700)<=1 and r['end'] in('5:00 카운트다운','타이머 리셋'),r)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
