"""b428 (t564u·t565u·t566u): 일반 판별 — ① 맵 이름 = 표의 모든 이름과 자모 유사도 1등·(다른 보스) 2등 차이 ② 난이도 = 줄 끝 조각을 그 보스 난이도들과 비교 ③ 닉 = 음절마다 강한 읽기. 오인 방지 그대로."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import _tutil
from playwright.sync_api import sync_playwright
port=_tutil.free_port();srv=_tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
bad=[]
def check(n,c,v):
  print(('PASS ' if c else 'FAIL ')+n,'—',v)
  if not c: bad.append(n)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);pg=b.new_page();pg.route('https://**/*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}')
  D=lambda s: pg.evaluate("t=>{ARX.runDiff=null;ARX.mapSt=null;const d=arDetectBMap(t); return d?[d.boss,d.diff,d.kind]:null}",s)
  # 실제 OCR 기록(1,421줄)에서 예전엔 못 읽던 줄
  for t,e,n in [('아기 계식    ”\n가디언    、\n디연 엔켈 글라임의 께단',['slime','','w'],'슬라임 대기 (엔켈·글라임·께단)'),
                ('：           (20 ㅜ\n운 명의 전진\n어티가 |팍되는 족',['adversary','','w'],'대적자 대기 (어티가 팍되는 족)'),
                ('르그홈 황궁 메민홈   비호',['seren','','brw'],'세렌 왕궁 메인홀'),
                ('+\n솜을 두른 나계<미디-',['kaling','easy','b'],'카링 죽음을 두른 사계 + 이지'),
                ('라무라무 계곡 고요한 깨단 ㆍ카모스>',['slime','chaos','r'],'난이도 카모스 → 카오스'),
                ('아고라 바즈러피는 빛 하프',['will','hard','br'],'난이도 하프 → 하드'),
                ('카로데 카로테 마천루 -노딸>',['kalos','normal','br'],'난이도 노딸 → 노멀'),
                ('콩떠의 눈 일',None,'꼬리 없는 전투·보상맵 비슷한 줄(대기 공허의 눈 앞 오독)은 정하지 않음'),
                ('공허의 눈 <카오스>',['dusk','chaos','br'],'정확한 이름 그대로'),
                ('어둠의 신전 <하드>',['blackmage','hard','b'],'검은 마법사 그대로'),
                ('도원경 빛을 되찾은 사계 01            ,',['kaling','','r'],'여는 기호 없는 01은 난이도 안 정함(b427 그대로)')]:
    r=D(t); check(n,r==e,r)
  nv=pg.evaluate("""()=>{ const run=(chars,H,lead)=>{ S.characters=chars.map((n,i)=>({id:'c'+i,name:n})); ARX.nHist=H.slice(); ARX.nLead=H.map(()=>!!lead); const v=arNameVote2(); return v.cid?S.characters.find(c=>c.id===v.cid).name:''; };
    const x03=['람르킴','람르킴','람르킹','랑르킴','람르킴','랑르킴'];
    return { lang:run(['랑트킹','린벨자','2터래플','터래플'],x03), langOnlyWeak:run(['랑트킹'],['람르킴','람르킴','람르킴','람르킴']),
      two:run(['2터래플','터래플','랑트킹'],['러래플','러래플','러래플','러래플'],true), plain:run(['2터래플','터래플'],['러래플','러래플','러래플','러래플'],false),
      lilk:run(['2터래플','릴캉혼망'],['림강몬망','림강몬망','림강몬망','림강몬망']) }; }""")
  check('x03 실제 읽기(람르킴·랑르킴·람르킹) → 랑트킹 (음절마다 강한 읽기 있음)',nv['lang']=='랑트킹',nv)
  check('받침이 한 번도 맞게 안 나오면(람르킴만) 안 정함',nv['langOnlyWeak']=='',nv)
  check('2터래플·터래플 둘 다 등록 + 앞 기호 읽힘 → 2터래플 (ㅌ을 ㄹ로만 읽어도)',nv['two']=='2터래플',nv)
  check('앞 기호 없는 읽기 → 터래플',nv['plain']=='터래플',nv)
  check('림강몬망 읽기로 릴캉혼망은 안 정함(릴 음절 안 나옴)',nv['lilk']=='',nv)
  b.close()
finally: srv.terminate()
print('PASS b428' if not bad else 'FAIL '+str(bad)); sys.exit(1 if bad else 0)
