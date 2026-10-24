# test_b261: 드롭표 = 보스별 장신망 상자 원래 이름·아이콘·기록 키(b_bellona·b_limbo·b_baldrix·b_jupiter), 시세만 b_sjm 공용.
# 기록 = 상자 자기 키·이름으로 저장, 자동 채움 = b_sjm 시세. 아이템 시세 목록 = b_sjm 1줄. b260 때 b_sjm 으로 저장된 기록 → 보스별 상자로 이전.
import os, sys, tempfile, shutil, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
BS={'limbo':'extreme','baldrix':'hard','bellona':'hard','jupiter':'hard'}
C={'id':'c0','name':'zetking','level':295,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{k:{'enabled':True,'diff':v,'party':1} for k,v in BS.items()},'weekly':{},'monthly':{},'auto':{},
   'drops':{'bellona|b_sjm':1,'whisper|x':0},'drev':{'bellona|b_sjm':{'m':1500000000,'a':15,'p':1,'i':'b_sjm'}},'sync':{}}
H=[{'week':'2026-10-15','total':1,'perChar':[{'id':'c0','name':'zetking','meso':0,'bosses':[],'items':{'jupiter|b_sjm':1,'mystery|b_sjm':1},'revs':{'jupiter|b_sjm':{'m':1600000000,'a':16,'p':1,'i':'b_sjm'},'baldrix|b_sjm#2':{'m':800000000,'a':16,'p':2,'i':'b_sjm'}}}]}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':H,'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
T=1761300000000
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("([s,t])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.itemPrices',JSON.stringify({b_sjm:{p:1871000000,t}}))}",[ST,T]); pg.reload(); pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>{const f=id=>BOSSES.find(b=>b.id===id), D2=(id,d)=>dropsFor(f(id),d), all=BOSSES.flatMap(b=>b.diffs.flatMap(d=>dropsFor(b,d)));
      return {lh:D2('limbo','hard'),le:D2('limbo','extreme'),bh:D2('baldrix','hard'),be:D2('baldrix','extreme'),eh:D2('bellona','hard'),jh:D2('jupiter','hard'),sjm:all.includes('b_sjm'),
        rev:revItems().filter(k=>k==='b_sjm').length, revBox:revItems().filter(k=>/^b_(limbo|baldrix|bellona|jupiter)$/.test(k)),
        ap:['b_limbo','b_baldrix','b_bellona','b_jupiter'].map(admPriceOf), pid:priceId('b_limbo'), names:['b_limbo','b_baldrix','b_bellona','b_jupiter'].map(k=>ITEMS[k].n)}}""")
    check('드롭표 = 보스별 원래 상자', 'b_limbo' in r['lh'] and 'b_limbo' in r['le'] and 'b_baldrix' in r['bh'] and 'b_baldrix' in r['be'] and 'b_bellona' in r['eh'] and 'b_jupiter' in r['jh'], r)
    check('b_sjm 은 드롭표에 없음', not r['sjm'])
    check('아이템 시세 목록: b_sjm 1줄, 상자 4종 없음', r['rev']==1 and not r['revBox'], r)
    check('상자 4종 시세 = b_sjm 시세', [x and x.get('p') for x in r['ap']]==[1871000000]*4 and r['pid']=='b_sjm', (r['ap'],r['pid']))
    chips=pg.evaluate("()=>[...document.querySelectorAll('.drop[data-drop=\"limbo|b_limbo\"]')].map(e=>({t:(e.getAttribute('title')||'')+' '+e.textContent,img:(e.querySelector('img')||{}).src||''}))")
    check('림보 익스트림 칩 = 욕망 상자 이름', chips and any('욕망' in c['t'] for c in chips) and all('장신망' not in c['t'] for c in chips), chips)
    # 기록: 상자 자기 키로 저장, 금액 = b_sjm 시세
    pg.evaluate("askRev(S.characters[0],findBoss('limbo'),'limbo|b_limbo','b_limbo',()=>{})"); pg.wait_for_timeout(300)
    v=pg.evaluate("()=>document.getElementById('rvAmt').value"); check('기록 창 자동 채움 18.71', v=='18.71', v)
    pg.click('#revModal [data-rv="ok"]'); pg.wait_for_timeout(300)
    s=pg.evaluate("()=>JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
    c=s['characters'][0]; dr=c.get('drev',{})
    check('기록 = limbo|b_limbo, i=b_limbo', dr.get('limbo|b_limbo',{}).get('i')=='b_limbo' and dr['limbo|b_limbo']['m']==1871000000, dr)
    check('b_sjm 기록 → 벨로나 상자로 이전(drops·drev)', c['drops'].get('bellona|b_bellona')==1 and 'bellona|b_sjm' not in c['drops'] and dr.get('bellona|b_bellona',{}).get('i')=='b_bellona' and 'bellona|b_sjm' not in dr, (c['drops'],dr))
    pc=s['history'][0]['perChar'][0]
    check('지난 기록 b_sjm → 보스별 상자(파티 #2 포함), 보스 모르면 그대로', pc['revs'].get('jupiter|b_jupiter',{}).get('i')=='b_jupiter' and pc['revs'].get('baldrix|b_baldrix#2',{}).get('i')=='b_baldrix' and pc['items'].get('jupiter|b_jupiter')==1 and pc['items'].get('mystery|b_sjm')==1, pc)
    h=pg.evaluate("()=>{const p=S.history[0].perChar[0];return itemsInline(p.items,{revs:p.revs,byBoss:true})}")
    check('수익 기록(지난 주)에 갈망 상자 이름', r['names'][3] in h or 'b_jupiter' in h, h[:300])
    pg.evaluate("()=>{S.characters[0].drops['limbo|b_limbo']=1;openRevAll()}"); pg.wait_for_timeout(300)
    ra=pg.evaluate("()=>{const m=document.getElementById('revAllModal');return m?m.innerHTML:''}")
    check('전체 수정 창: 욕망·광기 상자 이름/아이콘', (r['names'][0] in ra or 'b_limbo' in ra) and (r['names'][2] in ra or 'b_bellona' in ra) and '장신망 상자' not in ra, [x for x in ['욕망','광기','장신망'] if x in ra])
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
    srv.terminate()
print('FAILED:',fails) if fails else print('ALL PASS'); sys.exit(1 if fails else 0)
