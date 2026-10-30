# test_b303 (t529~t531): 보스 클리어 시간 — '남은시간' 7세그먼트 판독(1920 실제 화면 + 1.33/1.875 배율), 입장 = 지금−(제한−남은) 중앙값,
#   늘어남(5:00 리셋)=클리어 신호, 상자=끝, 타이머 못 읽으면 맵 이름 시각 (추정), PRACTICE MODE·상자 없이 나감 = 기록 안 함, 보스 칸 오른쪽 위 네온 표시(다크/라이트)
import os, sys, json, base64, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures'); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
du=lambda f:'data:image/jpeg;base64,'+base64.b64encode(open(f,'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
GT={'b284/s01.jpg':'4:08','b284/s02.jpg':'3:54','b284/s03.jpg':'4:44','b284/s05.jpg':'4:41','b284/s06.jpg':'4:47','b284/s07.jpg':'4:26','b284/s08.jpg':'4:24',
    'b284/s09.jpg':'4:23','b284/s10.jpg':'4:39','b284/s12.jpg':None,'b286/v01_0130.jpg':'4:36','b284/s04.jpg':None,'b284/s11.jpg':None}
READ="""async ([u,k])=>{ const im=await new Promise(r=>{ const i=new Image(); i.onload=()=>r(i); i.src=u; }); const cv=document.createElement('canvas'); cv.width=Math.round(1920*k); cv.height=Math.round(1080*k);
  cv.getContext('2d').drawImage(im,0,0,cv.width,cv.height); const A=window.AR; A.bbox=null; A.bbKey=''; A.geo={sw:cv.width,sh:cv.height,bb:'',x:0,y:0,w:cv.width,h:cv.height,gx:0,gy:0,gw:cv.width,gh:cv.height,s:k};
  const r=arClrRead(cv); return r?r.m+':'+String(r.s).padStart(2,'0'):null; }"""
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]};
 S.characters=[{id:'c0',name:'트딕이',level:285,job:'',world:'스카니아',ocid:'o-1',accId:'',isMain:true,image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}]; S.activeId='c0'; S.clears={}; save(); render(); return BOSSES.filter(b=>b.type==='weekly').slice(0,3).map(b=>b.id); }"""
# 가짜 시계 + 읽기 순서로 세션 흉내: ev = [[t초, 'r', 남은초|null] | [t,'map',boss] | [t,'box',boss] | [t,'leave'] | [t,'prac']]
SIM="""([boss,ev])=>{ const A=window.AR, on=Date.now, rd=window.arClrRead; let T=0, cur=null; Date.now=()=>T; window.arClrRead=()=>cur;
  A.clr=null; A.clrHold=false; A.clrSeen=0; A.clrT=0; A.clrPT=1e15; S.clears={}; const B=0;
  try{ for(const e of ev){ T=1e12+e[0]*1000;
    if(e[1]==='r'){ cur=e[2]==null?null:{m:Math.floor(e[2]/60),s:e[2]%60,sec:e[2]}; A.clrT=0; arClrTick({},T); }
    else if(e[1]==='map') arClrMap({boss:e[2],diff:'hard'},T);
    else if(e[1]==='leave') arClrLeave(T);
    else if(e[1]==='prac'){ if(A.clr) A.clr.practice=true; }
    else if(e[1]==='box') arClrFinish(e[2],'hard',T); } }
  finally{ Date.now=on; window.arClrRead=rd; } return JSON.parse(JSON.stringify(S.clears)); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    ids=pg.evaluate(SETUP); bid=ids[0]
    for k in [1,4/3,1.875]:
      got={f:pg.evaluate(READ,[du(os.path.join(FX,f)),k]) for f in GT}
      bad={f:(got[f],GT[f]) for f in GT if got[f]!=GT[f]}
      check(f'남은시간 판독 13장 (UI 배율 {k:.3g}) — 창·글자에 가려진 3장은 못 읽음(null)',not bad,bad or got)
    # 30분 보스: 입장 60초 뒤 처음 읽음(29:00), 이후 1초마다, 중간 잘못 읽은 값 2개, 클리어 시 5:00 리셋, 상자 = 입장 후 612초
    ev=[[0,'map',bid]]+[[60+i,'r',1740-i] for i in range(0,400)]; ev[100]=[159,'r',600]; ev[200]=[259,'r',1777]
    ev+= [[460,'r',300],[461,'r',299],[462,'r',298]]+[[600+i,'r',None] for i in range(10)]+[[612,'box',bid]]
    r=pg.evaluate(SIM,[bid,ev]); v=r.get(bid+'|hard')
    check('입장 = 지금−(30:00−남은) 중앙값, 잘못 읽은 값 무시, 5:00 리셋 뒤 무시 → 10분 12초',v and v['sec']==612 and not v['est'],r)
    # 제한 시간 첫 값 올림: 첫 읽기 29:59 → 30:00
    r=pg.evaluate(SIM,[bid,[[0,'r',1799],[1,'r',1798],[2,'r',1797],[95,'box',bid]]]); v=r.get(bid+'|hard')
    check('첫 읽은 값 29:59 → 제한 30분 올림 → 1분 36초',v and v['sec']==96,r)
    r=pg.evaluate(SIM,[bid,[[0,'map',bid],[5,'r',None],[300,'box',bid]]]); v=r.get(bid+'|hard')
    check('타이머 한 번도 못 읽음 → 맵 이름 시각 기준 5분 0초 (추정)',v and v['sec']==300 and v['est'],r)
    r=pg.evaluate(SIM,[bid,[[0,'r',1799],[1,'r',1798],[2,'prac'],[60,'box',bid]]])
    check('PRACTICE MODE → 기록 안 함',r=={},r)
    r=pg.evaluate(SIM,[bid,[[0,'map',bid],[1,'r',1799],[2,'r',1798],[10,'leave'],[100,'box',bid]]])
    check('상자 없이 맵 나감 → 버림',r=={},r)
    r=pg.evaluate(SIM,[bid,[[0,'r',1799],[1,'r',1798],[2,'leave'],[50,'box',bid]]]); v=r.get(bid+'|hard')
    check('타이머가 보이는 동안 맵 이름 못 읽은 건 나간 게 아님',v and v['sec']==51,r)
    # 표시
    ids=pg.evaluate("[...document.querySelectorAll('.boss select[data-party]')].map(e=>e.dataset.party)"); print('shown',ids[:4])
    pg.evaluate("([a,b2])=>{ S.clears={[a+'|hard']:{sec:292,at:Date.now(),est:false},[b2+'|hard']:{sec:75,at:Date.now(),est:true}}; save(); render(); }",[ids[0],ids[1]])
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'; render()"); pg.wait_for_timeout(300)
      q=pg.evaluate("""()=>[...document.querySelectorAll('.boss')].map(e=>{ const t=e.querySelector('.clrtime'); if(!t) return null; const a=t.getBoundingClientRect(), c=e.getBoundingClientRect();
        return {t:t.textContent, dr:Math.round(c.right-a.right), dt:Math.round(a.top-c.top), fs:parseFloat(getComputedStyle(t).fontSize), sh:getComputedStyle(t).textShadow!=='none'}; })""")
      hit=[x for x in q if x]
      check(f'[{th}] 기록 있는 보스 2칸만 "m분 s초" 오른쪽 위 작게·네온',len(hit)==2 and {h['t'] for h in hit}=={'4분 52초','1분 15초 (추정)'} and all(h['dr']<=12 and h['dt']<=6 and h['fs']<=12 and h['sh'] for h in hit),q[:6])
      el=pg.query_selector('.boss-list'); el.screenshot(path=os.path.join(OUT,f'b303_clear_{th}.png'))
    check('새로고침 뒤 유지',(pg.reload(), pg.wait_for_timeout(800), pg.evaluate("Object.keys(S.clears||{}).length"))[2]==2)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally: srv.kill()
print('RESULT', 'FAIL' if fails else 'OK', len(fails)); sys.exit(1 if fails else 0)
