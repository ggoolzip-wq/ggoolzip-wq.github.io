"""b441 (t705u 진힐라 '고근' 오기록): 공중 기록 = 확실한 맞춤 arNeed번 + 다른 시각 2번 이상 + 움직임(1080 기준 airMovePx 20px).
약한 맞춤은 움직임 근거로만. 제자리 이펙트(같은 자리 반복·조금 출렁임)는 기록 안 함. 바닥은 그대로(제자리 정상).
+ 실제 진힐라 보상 맵 프레임(fixtures/b441): 연두색 빛 자리에서 고근이 .73 이상으로 맞는 것 확인(원인 재현)."""
import sys,subprocess,json,base64
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
T="""()=>{ const A=ARX, P=[]; const o=window.arPick; window.arPick=(h,via)=>P.push(h.k+'/'+via); A.cfg.on=true; const t0=1e6;
 A.mapSt={boss:'jinhilla',kind:'brw',diff:'hard'}; A.mapText='고통의 미궁 - 폭망의 제단 <하드>';
 const S=(x,y,sad,air=true)=>({k:'sos',x,y,w:78,h:78,score:.75,sad,air,ok:sad<=A.cfg.airSad,soft:sad>A.cfg.airSad&&sad<=A.cfg.airSad2});
 const run=(seq,sh=776)=>{ A.tracks=[]; P.length=0; for(const [h,t] of seq) arTrack([h],sh,t); return P.length; };
 const r={
  staticStrong: run([[S(625,271,38),t0],[S(626,271,38),t0+70],[S(625,275,38),t0+140],[S(627,272,38),t0+900]]),  // 제자리 빛(확실한 맞춤이라도)
  driftSoft:    run([[S(671,287,45),t0],[S(685,287,45),t0+67]]),     // 실제 n2(밝기+0.06) 약한 맞춤 14px 출렁임 → b440은 기록
  softFar:      run([[S(600,300,44),t0],[S(700,200,44),t0+170]]),    // 약한 맞춤만, 크게 움직여도
  strongSingle: run([[S(600,300,35),t0]]),                           // 한 번만
  strongMove:   run([[S(600,300,35),t0],[S(610,240,36),t0+67]]),      // 실제 공중 아이템: 위로 튀어 오름
  strongSoft:   run([[S(600,300,35),t0],[S(615,250,44),t0+67]]),      // 확실 1 + 약한 1 움직임
  ground:       run([[S(600,500,30,false),t0]]),                     // 바닥은 한 번에 그대로
 };
 A.cfg.airMove=false; r.legacySoft=run([[S(671,287,45),t0],[S(685,287,45),t0+67]]); r.legacySingle=run([[S(600,300,35),t0]]); delete A.cfg.airMove;
 window.arPick=o; return r; }"""
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}');pg.wait_for_timeout(800)
  r=pg.evaluate(T)
  check('제자리 빛(확실한 맞춤 4번, 움직임 4px) → 0건',r['staticStrong']==0,r)
  check('약한 맞춤 14px 출렁임(실제 n2 밝기+0.06) → 0건 (b440은 1건)',r['driftSoft']==0,r)
  check('약한 맞춤만이면 크게 움직여도 0건',r['softFar']==0,r)
  check('확실한 맞춤 한 번만 → 아직 0건',r['strongSingle']==0,r)
  check('확실한 맞춤 + 위로 튀어 오름 → 1건',r['strongMove']==1,r)
  check('확실한 맞춤 1 + 약한 맞춤 움직임 → 1건',r['strongSoft']==1,r)
  check('바닥은 한 번에 기록(그대로)',r['ground']==1,r)
  check('cfg.airMove=false → 예전 규칙(약한 맞춤 2번+움직임 1건, 한 번 1건)',r['legacySoft']==1 and r['legacySingle']==1,r)
  F=Path(__file__).parent/'fixtures'/'b441'
  if (F/'jinhilla_glow.png').exists():
    im=base64.b64encode((F/'jinhilla_glow.png').read_bytes()).decode(); meta=json.loads((F/'jinhilla_glow.json').read_text())
    s=pg.evaluate("""async ([img,m])=>{ const im=new Image(); im.src='data:image/png;base64,'+img; await im.decode(); const cv=document.createElement('canvas'); cv.width=im.width; cv.height=im.height; const g=cv.getContext('2d',{willReadFrequently:true}); g.drawImage(im,0,0);
      const c=ARX.cfg, px=m.px, KO={multi:true,tiles:true,sad:999,thr:.5,f:Math.max(2,Math.round(px/9)),angles:arAirAngles(c.airKoStep),aref:c.airKoRef,vmax:c.airKoVmax||8,sq:[1],drop:true};
      const r=await arMatchRun({img:g.getImageData(0,0,cv.width,cv.height)},['sos'],[px],KO); const h=(r.hits||[]).sort((a,b)=>b.score-a.score)[0]; return h?[+h.score.toFixed(3),h.sad]:null; }""",[im,meta])
    check('실제 진힐라 보상 맵 연두색 빛: 고근 점수 .73 이상(원인 재현, 색 차이 40~50)',s and s[0]>=.73 and 40<s[1]<=50,s)
  check('페이지 오류 없음',not errs,errs)
  b.close()
finally: srv.terminate()
print('FAILS',bad); sys.exit(1 if bad else 0)
