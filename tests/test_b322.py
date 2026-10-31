# test_b322 (t584): 모든 보스 맵 — (1) 대기→각 페이즈 맵 2번 읽으면 그 상태, 사이에 다른 맵 1번 잘못 읽어도 상태 안 바뀜(스우 진행 중↔대기 중 왕복 방지)
# (2) 보상 인식 중(래치)이면 전투/대기/잡음 읽기가 섞여도 '보상 인식 중' 유지, 맵 그림 바뀌어 래치 풀리면 정상 전환
# (3) 클리어 시간: 20분 제한(주간), 끝 = 타이머 리셋 순간, 맵 흔들림에 측정 안 버림, 다페이즈는 첫 페이즈부터
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
BM=json.load(open(os.path.join(ROOT,'tests','fixtures','boss_maps.json')))
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
RESET="const A=window.AR; A.lock=null; A.box=null; A.det={cid:'',boss:'',diff:'',src:''}; A.mapSt=null; A.mapPend=null; A.rew=null; A.clr=null; A.clrHold=false; A.mOffN=0; A.mOther=0;"
SEQ="""([seq,latch])=>{ """+RESET+""" let t=Date.now(); const out=[]; for(const x of seq){ if(x==='@LATCH'){ A.det.boss=A.mapSt&&A.mapSt.boss||''; A.rew={hash:null,t,n:0,boss:A.det.boss}; continue; } if(x==='@UNLATCH'){ A.rew=null; A.box=null; A.det.boss=''; continue; }
  t+=1000; arMapState(x,t); out.push(arBossState()); } return out; }"""
ONE="""([x])=>{ """+RESET+""" const t=Date.now(); arMapState(x,t); arMapState(x,t+1000); return {st:arBossState(),kind:A.mapSt&&A.mapSt.kind,boss:A.mapSt&&A.mapSt.boss}; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    n=0
    for bo in BM:
      for d in bo['difficulties']:
        W=(bo.get('waiting') or {}).get(d,[None])[0] or bo.get('waiting_base')
        PH=[ph['maps'][d][0] for ph in bo.get('phases',[]) if d in ph.get('maps',{})]
        R=(bo.get('reward') or {}).get(d); R=R[0] if isinstance(R,list) else None  # '미확인' 은 건너뜀
        if not PH or not W: continue
        sW=pg.evaluate(ONE,[W]); sP=[pg.evaluate(ONE,[m]) for m in PH]; sR=pg.evaluate(ONE,[R]) if R else None
        # (1) 전투 맵 2번 → 상태, 사이에 대기맵 1번 잘못 읽힘 → 유지
        for m,s in zip(PH,sP):
          if s['st']==sW['st']: continue
          o=pg.evaluate(SEQ,[[W,W,m,m,m,W,m,m],False]); n+=1
          check(f"{bo['boss']} {d} 전투 '{m}' 중 대기맵 1번 잘못 읽음 → 상태 유지", o[3:]==[s['st']]*5, o)
          o=pg.evaluate(SEQ,[[m,m,W,W,W],False]); n+=1
          check(f"{bo['boss']} {d} 전투→대기 2번 연속이면 대기로", o[-1]==sW['st'], o)
        # (1b) t585 대기맵 OCR 오독(끝 잘림·태그 없음·':' 빠짐·공백 없음) 섞여도 대기 유지, 태그 붙은 전투맵 2번이면 전환
        import re as _re
        rg,nm=_re.split('[:：]',W,1) if _re.search('[:：]',W) else ('',W); base=_re.sub(r'<[^>]*>','',nm).strip(); tg=(_re.search(r'<[^>]*>',nm) or [''])[0]
        V=[rg+'：'+base[:-i] for i in (1,2,3) if len(base)-i>=3]+[rg+'：'+base, rg+base+' '+tg, W.replace(' ','')]
        o=pg.evaluate(SEQ,[[W,W]+V+V,False]); n+=1
        check(f"{bo['boss']} {d} 대기 중 대기맵 오독 {len(V)}종 → 대기 유지", all(x==sW['st'] for x in o), list(zip(V+V,o[2:])))
        if sP and sP[0]['st']!=sW['st']:
          o=pg.evaluate(SEQ,[[W,W,V[0],PH[0],PH[0],PH[0]],False]); n+=1
          check(f"{bo['boss']} {d} 대기→전투 '{PH[0]}' 2번이면 전환", o[-1]==sP[0]['st'] and o[2]==sW['st'], o)
        # (2) 보상 래치 유지
        if R:
          seq=[R,R,'@LATCH']+[PH[-1],R,W,'ㅁㄴ리 0',PH[0],R,PH[-1]]; o=pg.evaluate(SEQ,[seq,True]); n+=1
          check(f"{bo['boss']} {d} 보상 인식 중 → 전투/대기/잡음 섞여도 유지", all(x=='rew' for x in o[2:]), o)
          o=pg.evaluate(SEQ,[[R,R,'@LATCH',PH[-1],'@UNLATCH',W,W],True]); n+=1
          check(f"{bo['boss']} {d} 맵 그림 바뀌어 래치 풀리면 대기로", o[-1]==sW['st'], o)
    check(f'보스 맵 시퀀스 {n}개 확인', n>=60, n)
    # (3) 클리어 시간
    r=pg.evaluate("""()=>{ """+RESET+""" const t0=Date.now()-600000; A.det.cid='x';
      S.characters=[{id:'x',name:'x',bosses:{}}]; arClrMap({boss:'lotus',diff:'hard'},t0);
      const C=A.clr; const sh=[]; for(let i=0;i<300;i+=3) C.reads.push({t:t0+5000+i*1000,rem:1200-5-i}); // 입장 0초에 20:00 시작
      // 맵 흔들림(대기맵 1번)·타이머 2초 전 보임 → 버리지 않음
      A.clrSeen=t0+300000; arClrLeave(t0+301000); const kept=!!A.clr;
      const la=C.reads[C.reads.length-1]; C.jump=la.t+3000; C.upT=la.t+2000; // 클리어 = la.t+1초 근처 리셋
      const c=arClrFinish('lotus','hard',la.t+12000); return {kept, sec:c&&c.sec, want:Math.round((la.t+1000-t0)/1000), lim:arClrLimFor('lotus','hard'), end:c&&c.end, limEst:c&&c.limEst}; }""")
    check('주간 보스 제한시간 20분(1200초)', r['lim']==1200, r)
    check('타이머 2초 전에 보였으면 맵 흔들림에 클리어 측정 안 버림', r['kept'], r)
    check('끝 = 타이머 리셋 순간 (상자 감지 10초 늦어도 오차 ≤1초)', r['sec'] is not None and abs(r['sec']-r['want'])<=1 and r['end']=='타이머 리셋' and r['limEst'] is False, r)
    b.close()
finally:
  srv.terminate()
check('페이지 오류 없음', not errs, errs)
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
