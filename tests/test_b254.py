# test_b254: 로이드·소울 조각 삭제 · 칼로스/대적자/카링 에테르넬 방어구 상자 + 앱솔랩스/아케인셰이드 상자 = 기록 안 하는 정보 칩(에리온 칩 뒤) · 아이템 아이콘 전부 64px 고화질
import os, sys, json, base64, io, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from PIL import Image
IC=json.load(open(os.path.join(ROOT,'src','itemicons.json')))
def sz(k): return Image.open(io.BytesIO(base64.b64decode(IC[k].split(',')[1]))).size
NEW=['erion','b_kalos','b_adv','b_kaling','b_star','b_limbo','b_baldrix','b_bellona','b_jupiter','h_pocket','h_pendant','ab_w','ab_a','ar_w','ar_a']
check('새 아이콘 15종 존재 + 64px', all(k in IC and sz(k)==(64,64) for k in NEW), [(k,k in IC and sz(k)) for k in NEW])
items=[k for k in IC if not k.startswith(('emo_','dif_','mc_')) and k not in ('guildbless','pcmedal')]
check('아이템 아이콘 전부 64×64 (이모지·난이도 배지·모멘텀 제외)', all(sz(k)==(64,64) for k in items), [(k,sz(k)) for k in items if sz(k)!=(64,64)])
check('투명 배경(모서리 알파 0)', all(Image.open(io.BytesIO(base64.b64decode(IC[k].split(',')[1]))).convert('RGBA').getpixel((0,0))[3]==0 for k in NEW))
check('수동 키 보존(blink·emo·dif·mc·guildbless·pcmedal)', all(k in IC for k in ['blink','emo_1f389','dif_hard','dif_clear','mc_b','guildbless','pcmedal']))
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
BS={'kalos':'extreme','adversary':'hard','kaling':'extreme','lucid':'hard','lotus':'hard','jinhilla':'normal','limbo':'extreme','blackmage':'extreme'}
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>{const f=id=>BOSSES.find(b=>b.id===id);
      const allD=BOSSES.flatMap(b=>b.diffs.map(d=>dropsFor(b,d))).flat();
      return {as:Object.keys(ITEMS).filter(k=>/^[as]_/.test(k)), asD:allD.filter(k=>/^[as]_/.test(k)),
        noRec:['b_kalos','b_adv','b_kaling'].filter(k=>allD.includes(k)), rec:['b_star','b_limbo','b_baldrix','b_bellona','b_jupiter'].filter(k=>allD.includes(k)),
        ib:Object.fromEntries(BOSSES.flatMap(b=>b.diffs.map(d=>[b.id+'|'+d,infoBoxFor(b,d)])).filter(x=>x[1].length)),
        noIcon:Object.keys(ITEMS).filter(k=>!ITEM_ICONS[k]&&!/^hong_/.test(k)), sl:[...SET_LABEL?Object.keys(SET_LABEL):[]]}}""")
    check('로이드·소울 조각 ITEMS·DROPS 에서 삭제', not r['as'] and not r['asD'], r['as']+r['asD'])
    check('칼로스·대적자·카링 방어구 상자 = DROPS 에 없음(기록 안 함)', not r['noRec'], r['noRec'])
    check('흉성·림보·발드릭스·벨로나·유피테르 상자 = 기록 가능 유지', len(r['rec'])==5, r['rec'])
    AB=['ab_w','ab_a']; AR=['ar_w','ar_a']
    exp={'kalos|chaos':['b_kalos'],'kalos|extreme':['b_kalos'],'adversary|hard':['b_adv'],'adversary|extreme':['b_adv'],'kaling|hard':['b_kaling'],'kaling|extreme':['b_kaling'],
      'lotus|hard':AB,'lotus|extreme':AB,'damien|hard':AB,'lucid|hard':AR,'will|hard':AR,'dusk|chaos':AR,'jinhilla|normal':AR,'jinhilla|hard':AR,'dunkel|hard':AR,'blackmage|hard':AR,'blackmage|extreme':AR}
    check('정보 칩 보스·난이도 표 (앱솔: 하드 스우·데미안 / 아케인: 하드 루시드·윌·듄켈, 카오스 더스크, 진힐라, 검마)', r['ib']==exp, r['ib'])
    check('모든 ITEMS 에 이미지 아이콘(글자 아이콘 없음)', not r['noIcon'], r['noIcon'])
    check('SET_LABEL 에 로이드·소울 없음', '로이드' not in r['sl'] and '소울' not in r['sl'], r['sl'])
    pg.evaluate("()=>render()"); pg.wait_for_timeout(500)
    q=pg.evaluate("""()=>[...document.querySelectorAll('.drops')].map(d=>{const ch=[...d.children];return {
      ib:ch.filter(x=>x.classList.contains('ibox')).map(x=>({al:x.getAttribute('aria-label'),tip:x.hasAttribute('data-tip'),drop:x.hasAttribute('data-drop'),role:x.getAttribute('role'),tab:x.getAttribute('tabindex'),img:!!x.querySelector('img'),w:x.querySelector('img')?.getBoundingClientRect().width})),
      ord:ch.map(x=>x.classList.contains('erion')?'E':x.classList.contains('ibox')?'I':x.classList.contains('eter')?'T':x.classList.contains('erda')?'e':'d').join(''),
      ifb:d.querySelectorAll('.ifb').length}})""")
    ibs=[x for d in q for x in d['ib']]
    check('정보 칩: aria-label(…기록하지 않음), data-tip(b258: 이름)·data-drop·role·tabindex 없음, 이미지', ibs and all(x['al'].endswith('(기록하지 않음)') and x['tip'] and not x['drop'] and not x['role'] and not x['tab'] and x['img'] for x in ibs), ibs[:4])
    check('정보 칩 아이콘 크기 = 다른 칩과 같은 26px', all(abs(x['w']-26)<0.6 for x in ibs), [x['w'] for x in ibs])
    names={x['al'] for x in ibs}
    check('화면: 의지·고대·흉수 + 앱솔·아케인 상자 칩', all(any(n in a for a in names) for n in ['의지의 에테르넬','고대의 에테르넬','흉수의 에테르넬','앱솔랩스 무기 상자','앱솔랩스 방어구 상자','아케인셰이드 무기 상자','아케인셰이드 방어구 상자']), names)
    check('순서: 정보 칩은 에리온 칩 바로 뒤(에리온 없으면 같은 자리)', all(('EI' in d['ord']) if 'E' in d['ord'] and 'I' in d['ord'] else True for d in q) and all(d['ord'].rfind('I')<(d['ord'].find('d') if 'd' in d['ord'] else 99) for d in q if 'I' in d['ord']), [d['ord'] for d in q])
    check('드롭 칩 영역에 글자 아이콘(.ifb) 없음', all(d['ifb']==0 for d in q), [d['ifb'] for d in q])
    n0=pg.evaluate("Object.keys(S.characters[0].drops||{}).length"); pg.click('.drop.ibox'); pg.wait_for_timeout(300)
    check('정보 칩 클릭 = 기록 안 됨', pg.evaluate("Object.keys(S.characters[0].drops||{}).length")==n0)
    b.close()
finally: srv.terminate()
dist=open(os.path.join(ROOT,'tools','pages_dist.sh')).read()
check('아이콘 = index.html 인라인(별도 파일 없음 → pages_dist 누락 위험 없음), epicbeam 스프라이트 배포 유지', 'epicbeam_sprite.webp' in dist and 'data:image/webp' in open(os.path.join(ROOT,'index.html')).read())
check('페이지 오류 없음', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
