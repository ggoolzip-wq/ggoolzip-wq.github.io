# 보스 목록 [취소]/[저장] (대기 중인 변경), 드롭 기간당 1회, 드롭 표 정리, '캐릭터 별 기록' 탭, '주간 기록' 탭 삭제 (2026-10-10)
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
PORT=8800
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def B(d,p=1): return {'enabled':True,'diff':d,'party':p}
def ch(id,name,bosses,weekly,drops,dropOut={}):
    return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':'o-'+id,'accId':'a1','isMain':id=='c1','image':'','bosses':bosses,'weekly':weekly,'monthly':{},'auto':{},'drops':drops,'dropOut':dropOut,'sync':{}}
c1=ch('c1','단풍용사',{'papulatus':B('chaos'),'magnus':B('hard'),'seren':B('hard',2),'kaling':B('normal',2)},{'seren':True,'kaling':True},
      {'seren|mitra':2,'kaling|chaosbox':3,'kaling|r_white':2},{'kaling|r_white':['x','r4']})
c2=ch('c2','불독메이지',{'lucid':B('hard'),'blackmage':B('hard')},{'lucid':True},{'lucid|belt':1})
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m: print('console:',m.text) if 'dropClamp' in m.text else None)
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    pg.goto(URL); wk=pg.evaluate("weekId()")
    H=[{'week':'2026-10-01','weeklyOnly':True,'total':999,'perChar':[{'id':'c1','name':'단풍용사','meso':999,'items':{'seren|mitra':1}}]},
       {'week':'2026-10-08','weeklyOnly':True,'total':5,'perChar':[{'id':'c1','name':'단풍용사','meso':0,'items':{}}]}] if wk>'2026-10-08' else []
    ST={'version':5,'theme':'dark','activeId':'c1','characters':[c1,c2],'history':H,'monthHistory':[],'worldOrder':[],'settings':{'accounts':[{'id':'a1','label':'본계정','key':''}],'lastSync':int(time.time()*1000)}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(500)
    d=pg.evaluate("S.characters[0].drops"); o=pg.evaluate("S.characters[0].dropOut")
    check('B migration: counts >1 clamped to 1 (3 entries), ring outcome keeps latest', d=={'seren|mitra':1,'kaling|chaosbox':1,'kaling|r_white':1} and o['kaling|r_white']==['r4'] and pg.evaluate("dropClampN")==3, (d,o))
    # E/D tabs
    tabs=pg.eval_on_selector_all('#tabs [data-tab], nav [data-tab]',"e=>e.map(x=>x.textContent.trim())")
    check("tabs: 보스 현황 / 수익 분석, no 주간 기록·캐릭터 별 기록", '보스 현황' in tabs and '수익 분석' in tabs and '캐릭터 별 기록' not in tabs and '주간 기록' not in tabs and '수익 요약' not in tabs, tabs)
    # C drop tables
    def drops_of(slot): return pg.eval_on_selector_all(f'[data-drop^="{slot}|"]',"e=>e.map(x=>x.dataset.drop.split('|')[1])")
    check('papulatus chaos: only 파풀라투스 마크', drops_of('papulatus')==['papmark'], drops_of('papulatus'))
    check('magnus hard: no accessory drops', drops_of('magnus')==[], drops_of('magnus'))
    check('seren hard: no 여명 (daybreak)', 'daybreak' not in drops_of('seren') and 'mitra' in drops_of('seren'), drops_of('seren'))
    for slot,name in [('papulatus','drops_papulatus_chaos.png'),('magnus','drops_magnus_hard.png'),('seren','drops_seren_hard.png')]:
        shot(pg.locator('.boss',has=pg.locator(f'[data-party="{slot}"]')),name)
    rp=pg.inner_html('.revpanel'); rt=pg.inner_text('.revpanel')
    check('income panel: meso icon heading, 검은 마법사 icon (no 🌙), items line between 월간 and 캐릭터별 with chaos-box icon, no +1 hint',
          pg.locator('.revpanel h2 img').count()==1 and '🌙' not in rt and '🎁' not in rt and '+1' not in rt and pg.locator('.rp-items-n img').count()==1
          and rp.index('rp-items-n')<rp.index('캐릭터별') and (rp.find('rp-month')<0 or rp.index('rp-month')<rp.index('rp-items-n')), rt[:200])
    shot(pg.locator('.revpanel'),'income_panel.png')
    # A buttons
    check('취소/저장 disabled by default', pg.is_disabled('#pendCancel') and pg.is_disabled('#pendSave'))
    shot(pg.locator('.bosslay .grid>.card').nth(1).locator('.toolbar'),'pend_buttons_off.png')
    rev0=pg.inner_text('.char[data-id="c1"] .rev'); r0=pg.evaluate("charRevenue(S.characters[0]).meso")
    pg.select_option('[data-party="seren"]','1'); pg.wait_for_timeout(150)
    check('party change → buttons active', pg.is_enabled('#pendCancel') and pg.is_enabled('#pendSave') and 'on' in pg.get_attribute('#pendSave','class'))
    shot(pg.locator('.bosslay .grid>.card').nth(1).locator('.toolbar'),'pend_buttons_on.png')
    check('pending party change not in income (char list) nor storage', pg.inner_text('.char[data-id="c1"] .rev')==rev0 and json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))['characters'][0]['bosses']['seren']['party']==2, (rev0,pg.inner_text('.char[data-id="c1"] .rev')))
    pg.select_option('[data-party="seren"]','2'); pg.wait_for_timeout(150)
    check('party changed back to original → state equals snapshot → buttons disabled', pg.is_disabled('#pendSave') and pg.is_disabled('#pendCancel') and not pg.evaluate('!!pend'))
    pg.click('[data-drop="papulatus|papmark"]'); pg.wait_for_timeout(100); en=pg.is_enabled('#pendSave')
    pg.click('[data-drop="papulatus|papmark"]'); pg.wait_for_timeout(100)
    check('drop toggled on then off → buttons disabled again', en and pg.is_disabled('#pendSave') and not pg.evaluate('!!pend'))
    pg.select_option('[data-party="seren"]','1'); pg.wait_for_timeout(150)
    # B: click obtained → cancel, click again → obtained (pending)
    pg.click('[data-drop="seren|mitra"]'); pg.wait_for_timeout(100)
    check('click obtained item → cancelled (0)', pg.evaluate("S.characters[0].drops['seren|mitra']") is None)
    pg.click('[data-drop="seren|mitra"]'); pg.wait_for_timeout(100)
    check('click again → obtained once (1, never 2)', pg.evaluate("S.characters[0].drops['seren|mitra']")==1)
    pg.click('[data-drop="kaling|chaosbox"]'); pg.wait_for_timeout(100)
    # 취소 → 모달 → 아니오
    pg.click('#pendCancel'); pg.wait_for_selector('#svAsk')
    check("cancel modal: '변경사항을 취소하시겠습니까?' 예/아니오", '변경사항을 취소하시겠습니까?' in pg.inner_text('#svAsk') and pg.inner_text('#svAsk [data-k=yes]')=='예' and pg.inner_text('#svAsk [data-k=no]')=='아니오')
    shot(pg.locator('#svAsk .svaskbox'),'pend_cancel_modal.png')
    pg.click('#svAsk [data-k=no]'); pg.wait_for_timeout(100)
    check('아니오 → only closes (still pending)', pg.locator('#svAsk').count()==0 and pg.evaluate("!!pend") and pg.evaluate("S.characters[0].bosses.seren.party")==1)
    pg.click('#pendCancel'); pg.click('#svAsk [data-k=yes]'); pg.wait_for_timeout(150)
    check('예 → reverted to snapshot (party 2, drops back), buttons disabled', pg.evaluate("S.characters[0].bosses.seren.party")==2 and pg.evaluate("S.characters[0].drops['kaling|chaosbox']")==1 and pg.is_disabled('#pendSave'))
    # 저장
    pg.select_option('[data-party="seren"]','1'); pg.click('[data-drop="papulatus|papmark"]'); pg.wait_for_timeout(100); pg.click('#pendSave'); pg.wait_for_timeout(200)
    stg=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))['characters'][0]
    check('저장 → committed to storage + income updated, buttons disabled', stg['bosses']['seren']['party']==1 and stg['drops'].get('papulatus|papmark')==1 and pg.evaluate("charRevenue(S.characters[0]).meso")>r0 and pg.inner_text('.char[data-id="c1"] .rev')!=rev0 and pg.is_disabled('#pendSave'), (stg['bosses']['seren'],r0))
    check('캐릭터 별 기록 tab deleted', pg.locator('[data-tab="summary"]').count()==0)
    # 개수 표기: '리4 x1' (붙어서 '리41개'로 읽히지 않게), 0개는 숨김
    pg.evaluate("S.characters[0].drops['kaling|r_white']=1; S.characters[0].dropOut={'kaling|r_white':['r4']}; save(); tab='total'; render()"); pg.wait_for_timeout(200)
    rs=' | '.join(pg.eval_on_selector_all('.ringsum','e=>e.map(x=>x.textContent)'))
    check("ring summary uses '리4 x1', hides 컨4 x0, no '개'", '리4 x1' in rs and '컨4' not in rs and '리41' not in rs, rs)
    t=pg.inner_text('#view')
    check("item counts use 'xN' (no ×, no N개 glued)", '×' not in t and ' x1' in t, t[:300])
    h2=pg.eval_on_selector_all('#view h2','e=>e.map(x=>[x.textContent.trim(),!!x.querySelector("img")])')
    check("total tab: '시드링 획득' + '에픽빔 본 횟수' sections with icons, no 아이템별/캐릭터별 column", ['시드링 획득',True] in h2 and ['에픽빔 본 횟수',True] in h2 and not any('아이템별' in x[0] for x in h2) and '캐릭터별</th>' not in pg.inner_html('#view'), h2)
    sr=pg.inner_text('.totloot'); check('seed-ring section lists box with outcome (x-count)', '백옥의 보스 반지 상자' in sr and 'x1' in sr and pg.locator('.totloot .routs').count()>=1, sr)
    check('에픽빔 section lists non-ring drops', '파풀라투스 마크 x1' in pg.inner_text('#view'))
    k=pg.eval_on_selector_all('#view .stat .k','e=>e.map(x=>[x.textContent.trim(),!!x.querySelector("img")])')
    check('total stats labels: 총 수익 / 주간 보스 누적 / 월간 보스 누적 / 획득 아이템 누적, each with icon', [x[0] for x in k]==['총 수익','주간 보스 누적','월간 보스 누적','획득 아이템 누적'] and all(x[1] for x in k), k)
    check('총 수익 title icon + 캐릭터별 누적 main-char avatar (fallback ok)', pg.locator('#view h2:has-text("총 수익") img').count()==1 and pg.locator('#view h2:has-text("캐릭터별 누적") .hav, #view h2:has-text("캐릭터별 누적") .avatar').count()==1)
    pth=os.path.join(OUT,'total_counts.png'); pg.locator('#view').screenshot(path=pth); SHOTDIR and shutil.copy(pth,SHOTDIR)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails)
