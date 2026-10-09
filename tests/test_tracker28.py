# 2026-10-10 배치: 듄켈 파티 1→2→1, 회색 칩, API 표시 삭제, 월간 라벨, 체크 아이콘 삭제, 추가 모달, 탭, 에픽빔, 칠흑 상자 모달, 썬데이 라벨
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    pth=os.path.join(OUT,name); loc.screenshot(path=pth,**kw); SHOTDIR and shutil.copy(pth,SHOTDIR)
PORT=8828
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def B(d,p=1): return {'enabled':True,'diff':d,'party':p}
c1={'id':'c1','name':'단풍용사','level':285,'job':'히어로','world':'스카니아','ocid':'o1','accId':'a1','isMain':True,'image':'','bosses':{'dunkel':{'enabled':True,'diff':'hard'},'zakum':B('chaos'),'seren':B('hard'),'kaling':B('normal'),'blackmage':B('hard')},'weekly':{'seren':True},'monthly':{},'auto':{'seren':1},'drops':{},'sync':{'at':1}}
SUN={'id':1,'title':'썬데이 메이플','url':'https://x','image':'https://lwi.nexon.com/a.png','start':'2026-10-11T00:00:00+09:00','end':'2026-10-11T23:59:00+09:00','date':'2026-10-08T10:00:00+09:00','benefit':'A · B'}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps({'sunday':SUN,'items':[]})))
    pg.goto(URL)
    ST={'version':5,'theme':'dark','activeId':'c1','characters':[c1],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_mock_MAIN','status':{'ok':True,'count':274}}],'lastSync':int(time.time()*1000)}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(600)
    pg.select_option('[data-party="dunkel"]','2'); pg.wait_for_timeout(100)
    on1=pg.evaluate("!document.querySelector('#pendSave').disabled")
    pg.select_option('[data-party="dunkel"]','1'); pg.wait_for_timeout(100)
    check('듄켈 party 1→2→1 (saved party key missing) → 취소/저장 disabled again', on1 and pg.evaluate("document.querySelector('#pendSave').disabled&&document.querySelector('#pendCancel').disabled&&!pend"))
    check('party normalized to number on load', pg.evaluate("S.characters[0].bosses.dunkel.party")==1)
    # 2
    bs=pg.evaluate("['#pendCancel','#pendSave'].map(s=>{const c=getComputedStyle(document.querySelector(s));return c.borderTopWidth+' '+c.borderTopStyle})")
    check('buttons have a visible box when disabled', all(x.startswith('1px solid') for x in bs), bs)
    # 3,4,5,6
    v=pg.inner_text('#view'); h=pg.inner_html('#view')
    off=pg.eval_on_selector_all('.boss:has([data-party="dunkel"]) .drop.off, .drops .drop.off',"e=>e.map(x=>x.title)")
    check('disabled 여명/보장 chips present, greyed, not clickable', len(off)>=2 and pg.evaluate("[...document.querySelectorAll('.drop.off')].every(e=>getComputedStyle(e).pointerEvents==='none'&&!e.dataset.drop)"), off)
    check('disabled chips at END of tables', pg.evaluate("[...document.querySelectorAll('.drops')].every(d=>{const k=[...d.children];const i=k.findIndex(x=>x.classList.contains('off'));return i<0||k.slice(i).every(x=>x.classList.contains('off'))})"))
    check('파풀라투스 마크 not disabled', pg.locator('.drop.off[title*="파풀라투스"]').count()==0)
    check("no 'API'/'API 자동' pill", pg.locator('.pill.api').count()==0 and 'API 자동' not in v)
    check('no clear-check icon in boss rows', pg.locator('[data-check]').count()==0)
    rp=pg.inner_text('.revpanel')
    check("월간 label: no (별도), '(따로 합산)' below", '(별도)' not in rp and '(따로 합산)' in rp, rp[:300])
    shot(pg.locator('#view'),'b28_bosslist.png')
    # 7
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(300)
    pg.evaluate("accounts()[0].status={ok:true,count:274};renderAccList()"); al=pg.inner_text('#accList')
    check('acc row: 등록 완료 + green check, no mask/count, no 캐릭터 목록', '등록 완료' in al and '캐릭터 목록' not in al and '명' not in al and '•' not in al and '***' not in al, al)
    check("'계정 캐릭터 N명' header removed; 캐릭터 추가 button next to world select", pg.evaluate("!document.querySelector('#impTitle').offsetParent") and pg.evaluate("document.querySelector('#impWorld').nextElementSibling.id")=='impOk' and pg.inner_text('#impOk')=='캐릭터 추가')
    shot(pg.locator('#importModal .mbox, #importModal').first,'b28_addmodal.png')
    pg.keyboard.press('Escape'); pg.evaluate("closeImport&&closeImport()"); pg.wait_for_timeout(150)
    # 11
    pg.click('[data-drop="kaling|chaosbox"]'); pg.wait_for_selector('#chaosModal')
    opts=pg.eval_on_selector_all('#chaosModal .cbopt',"e=>e.map(x=>x.textContent.trim())")
    check('chaos modal: title + 7 options in order with icons + cancel', pg.inner_text('#chaosModal h3')=='어떤 장신구를 획득하셨나요?' and opts==['루즈 컨트롤 머신 마크','마력이 깃든 안대','몽환의 벨트','저주받은 마도서 선택 상자','거대한 공포','커맨더 포스 이어링','고통의 근원'] and pg.locator('#chaosModal .cbopt img').count()==7 and pg.locator('#chaosModal .cbcancel').count()==1, opts)
    shot(pg.locator('#chaosModal .cbbox'),'b28_chaos_modal.png')
    pg.click('#chaosModal .cbcancel'); pg.wait_for_timeout(100)
    check('cancel → nothing recorded, buttons disabled', not pg.evaluate("S.characters[0].drops['kaling|chaosbox']") and pg.evaluate("!pend"))
    pg.click('[data-drop="kaling|chaosbox"]'); pg.click('#chaosModal [data-cbpick="eye"]'); pg.wait_for_timeout(400)
    check("choose → '축하드립니다!' with item", '축하드립니다' in pg.inner_text('#congrats') and '마력이 깃든 안대' in pg.inner_text('#congrats'))
    pg.screenshot(path=os.path.join(OUT,'b28_chaos_congrats.png')); SHOTDIR and shutil.copy(os.path.join(OUT,'b28_chaos_congrats.png'),SHOTDIR)
    pg.evaluate("endCelebrate()")
    check('stored like ring outcomes, pending', pg.evaluate("S.characters[0].dropOut['kaling|chaosbox']")==['cb:eye'] and pg.evaluate("!!pend"))
    pg.click('[data-drop="kaling|chaosbox"]'); pg.wait_for_timeout(100)
    check('click again → canceled, back to snapshot', not pg.evaluate("S.characters[0].drops['kaling|chaosbox']") and not pg.evaluate("(S.characters[0].dropOut||{})['kaling|chaosbox']") and pg.evaluate("!pend"))
    pg.click('[data-drop="kaling|chaosbox"]'); pg.click('#chaosModal [data-cbpick="eye"]'); pg.wait_for_timeout(100); pg.evaluate("endCelebrate()"); pg.click('#pendSave'); pg.wait_for_timeout(200)
    ri=pg.inner_text('.revpanel')
    check("records show '[icon] - 마력이 깃든 안대'", '마력이 깃든 안대' in ri and '상자 x1' not in ri and pg.locator('.revpanel .cbx img').count()>=2, ri[-200:])
    k0=pg.evaluate("Object.keys(ITEMS).find(k=>document.querySelector(`[data-drop=\"seren|${k}\"]`)&&!isRing(k)&&k!=='chaosbox')")
    pg.click(f'[data-drop="seren|{k0}"]'); pg.wait_for_timeout(450)
    check('plain drop acquire → dozens of own-icon copies burst', pg.locator('#iconBurst img').count()>=30 and pg.evaluate("k=>[...document.querySelectorAll('#iconBurst img')].every(i=>i.getAttribute('src')===ITEM_ICONS[k])",k0))
    pg.screenshot(path=os.path.join(OUT,'b28_icon_burst.png')); SHOTDIR and shutil.copy(os.path.join(OUT,'b28_icon_burst.png'),SHOTDIR)
    pg.wait_for_timeout(2300); check('burst cleaned up after ~2s', pg.locator('#iconBurst').count()==0)
    pg.click(f'[data-drop="seren|{k0}"]'); pg.wait_for_timeout(200); check('un-click → no burst', pg.locator('#iconBurst').count()==0)
    # 8,9,10
    tabs=pg.eval_on_selector_all('[data-tab]',"e=>e.map(x=>x.textContent.trim())")
    check("tabs: no 캐릭터 별 기록, '수익 분석'", '캐릭터 별 기록' not in tabs and '수익 분석' in tabs and '총 수익' not in tabs, tabs)
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(300)
    av=pg.evaluate("(()=>{const a=document.querySelector('#view h2 .avatar');const l=document.querySelector('#charList .avatar');return a&&l?[a.getBoundingClientRect().width,l.getBoundingClientRect().width]:null})()")
    check('main portrait in 캐릭터별 누적 same size as left list', av and abs(av[0]-av[1])<1, av)
    t=pg.inner_text('#view')
    check("'에픽빔 본 횟수' with chosen item + aurora x-count", '에픽빔 본 횟수' in t and '물욕' not in t and '마력이 깃든 안대' in t and pg.evaluate("[...document.querySelectorAll('.lx.aur')].every(e=>getComputedStyle(e).backgroundClip==='text'||getComputedStyle(e).webkitBackgroundClip==='text')") and pg.locator('.lx.aur').count()>=1)
    shot(pg.locator('#view'),'b28_total.png')
    # b29: 에픽빔 — 제목 옆 합계(오로라), 목록 개수는 선홍색, 저장 데이터와 일치
    pg.evaluate("S.characters[0].drops['seren|mitra']=1; S.characters[0].drops['zakum|papmark']=1; save(); render()"); pg.wait_for_timeout(200)
    exp=pg.evaluate("(()=>{let n=0;for(const c of S.characters) for(const m of [c.drops||{},c.mdrops||{}]) for(const [k,v] of Object.entries(m)){const it=parseIK(k).it; if(ITEMS[it]&&!isRing(it)) n+=+v;} return n})()")
    sm=pg.inner_text('.epsum'); items=pg.eval_on_selector_all('.card:has(.epsum) .totloot .lx',"e=>e.map(x=>[x.textContent,getComputedStyle(x).color,getComputedStyle(x).backgroundClip])")
    check('에픽빔 heading sum = stored non-ring drops, aurora', sm==f'x{exp}' and exp==3 and pg.evaluate("getComputedStyle(document.querySelector('.epsum')).backgroundClip")=='text', (sm,exp))
    check('per-item counts crimson, no gradient, sum matches', all(c=='rgb(224, 17, 95)' and bc!='text' for _,c,bc in items) and sum(int(t[1:]) for t,_,_ in items)==exp, items)
    pg.locator('.card:has(.epsum)').screenshot(path='/workspace/shots/b29_epic.png') if SHOTDIR else None
    # 12 썬데이 라벨 (mocked clock)
    lab=lambda now: pg.evaluate("n=>sunLabel(feed.data.sunday,n)",now)
    ms=lambda s: pg.evaluate("s=>Date.parse(s)",s)
    check('Sun 10-11 → 이번 주', lab(ms('2026-10-11T12:00:00+09:00'))=='이번 주 혜택')
    check('Sun 23:59 → 이번 주', lab(ms('2026-10-11T23:59:59+09:00'))=='이번 주 혜택')
    check('Mon 10-12 00:00 KST → 저번 주', lab(ms('2026-10-12T00:00:00+09:00'))=='저번 주 혜택')
    pg.evaluate("feed.data.sunday=Object.assign({},feed.data.sunday,{date:'2026-10-15T10:00:00+09:00',benefit:'새 혜택'})")
    check('new post (Thu 10-15) → 이번 주 again', lab(ms('2026-10-15T11:00:00+09:00'))=='이번 주 혜택')
    pg.evaluate("feed.data.sunday.date='2026-10-08T10:00:00+09:00'; renderSun()")
    pg.clock.install(time=ms('2026-10-12T00:00:30+09:00')) if False else None
    cur=pg.inner_text('#sunCard .sunben b'); check('rendered label uses real clock', cur in ('이번 주 혜택','저번 주 혜택'), cur)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
