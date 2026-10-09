import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')  # 지정하면 tab_daily.png / tab_daily_hover.png / tab_guild.png 를 그 폴더에도 저장
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 일퀘 현황 · 길드 현황 탭 (스케줄러 / 길드 랭킹 모의 응답)
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil
sys.argv=[sys.argv[0]]
import mock_nexon
from mock_nexon import handle, KM, KA, CALLS, GUILD_EMPTY
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(loc_or_pg,name,**kw):
    path=os.path.join(OUT,name); loc_or_pg.screenshot(path=path,**kw)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen('http://127.0.0.1:8787/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL='http://localhost:8787/index.html'
IMG='https://open.api.nexon.com/static/maplestory/character/look/mock-'
def ch(id,name,lv,job,ocid,acc,main=False,img=''):
    return {'id':id,'name':name,'level':lv,'job':job,'world':'스카니아','ocid':ocid,'accId':acc,'isMain':main,'image':(IMG+img) if img else '',
            'bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],
  'characters':[ch('c1','단풍용사',287,'히어로','ocid-main','a1',True,'main'),ch('c2','불독메이지',272,'아크메이지(불,독)','ocid-alt1','a1',False,'alt1'),
                ch('c3','신궁짱',265,'신궁','ocid-alt2','a1',False,'alt2'),ch('c4','부계정비숍',268,'비숍','ocid-b1','a2',False,'b1'),
                ch('c5','수동캐릭',250,'아델','','',False)],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM},{'id':'a2','label':'부계정','key':KA}],'autoSync':True,'autoEnable':True,'lastSync':int(time.time()*1000)}}
sched_calls=lambda: [q.get('ocid') for p,q in CALLS if p.endswith('/scheduler/character-state')]
guild_calls=lambda: [(q.get('date'),q.get('ranking_type')) for p,q in CALLS if p.endswith('/ranking/guild')]
def wait_idle(pg): pg.wait_for_function("!dqBusy && !guildBusy && !syncing",timeout=20000); pg.wait_for_timeout(200)
CELLS="(id)=>[...document.querySelectorAll(`.dqc[data-dqchar=${id}] .dqi`)].map(e=>[e.dataset.dqi,[...e.classList].find(c=>c.startsWith('s-')),e.querySelector('.dqs').textContent.trim(),!!e.querySelector('.dqov')])"
OVFD="[document.documentElement.scrollWidth,...[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&!e.closest('header')).slice(0,5).map(e=>e.tagName+'.'+e.className+':'+Math.round(e.getBoundingClientRect().right))]"
NOOVF="[...document.querySelectorAll('main *')].every(e=>{const r=e.getBoundingClientRect();return r.left>=-1&&r.right<=innerWidth+1})"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1366,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'Failed to load resource' not in m.text and 'gsi' not in m.text else None)
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload(); pg.wait_for_timeout(500)
    today=pg.evaluate('dayId()'); yday=pg.evaluate('dayId(Date.now()-864e5)')
    # 1) 탭 바: 총 수익 → ㅡ 구분선 → 일퀘 현황 → 길드 현황
    tabs=pg.eval_on_selector_all('#tabs > *',"e=>e.map(x=>x.tagName==='SPAN'?'|'+x.className:x.textContent.trim())")
    check('tab order with divider', tabs==['보스 체크','수익 요약','주간 기록','총 수익','|tabsep','일퀘 현황','길드 현황'], tabs)
    sep=pg.evaluate("(()=>{const r=document.querySelector('#tabs .tabsep').getBoundingClientRect(),t=document.querySelector('[data-tab=total]').getBoundingClientRect();return {w:r.width,h:r.height,mid:Math.abs((r.top+r.bottom)/2-(t.top+t.bottom)/2)}})()")
    check('divider is a short horizontal line, vertically centered', 8<=sep['w']<=20 and 1<=sep['h']<=3 and sep['mid']<6, sep)
    check('no API calls before opening tabs', not sched_calls() and not guild_calls(), CALLS)
    # 2) 일퀘 현황
    pg.click('[data-tab=daily]'); pg.wait_for_selector('.dqc'); wait_idle(pg)
    sc=sched_calls(); check('daily tab fetched scheduler once per keyed character', sorted(sc)==['ocid-alt1','ocid-alt2','ocid-b1','ocid-main'], sc)
    cards=pg.eval_on_selector_all('.dqc','e=>e.map(x=>x.dataset.dqchar)'); check('cards in sidebar order, no-key char excluded', cards==['c1','c2','c3','c4'], cards)
    check('footer mentions no-key char', 'API 키가 연결되지 않은 캐릭터 1명' in pg.inner_text('.dqfoot'))
    m=pg.evaluate(CELLS,'c1'); print('c1',m)
    check('c1 items (Lv.287: 세르니움~카르시온 + 몬파 + 익몬)', [x[0] for x in m]==['cer','arcs','odium','dow','art','car','mp','xmp'], m)
    st={x[0]:x for x in m}
    check('states', st['cer'][1]=='s-done' and st['dow'][1]=='s-prog' and st['car'][1]=='s-prog' and st['mp'][1]=='s-done' and st['xmp'][1]=='s-done', m)
    check('counts shown (진행 0/100, 몬파 7/7회, 익몬 5/5)', st['car'][2]=='진행 0/100' and st['mp'][2]=='완료 7/7회' and st['xmp'][2]=='완료 5/5', m)
    check('done cells have overlay, others not', all(x[3]==(x[1]=='s-done') for x in m))
    check('locked line for Lv.290/295', '탈라하트 Lv.290' in pg.inner_text('.dqc[data-dqchar=c1] .dqlock') and '기어드락 Lv.295' in pg.inner_text('.dqc[data-dqchar=c1] .dqlock'))
    check('done count 6/8', pg.inner_text('.dqc[data-dqchar=c1] .dqcnt')=='6/8', pg.inner_text('.dqc[data-dqchar=c1] .dqcnt'))
    m2=pg.evaluate(CELLS,'c2'); check('c2 Lv.272: 세르니움·아르크스·오디움 + 몬파·익몬 only', [x[0] for x in m2]==['cer','arcs','odium','mp','xmp'] and [x[1] for x in m2]==['s-done','s-prog','s-idle','s-prog','s-prog'], m2)
    check('c2 texts (진행 0/100, 미수락, 몬파 3/7회, 익몬 주간 2/5)', [x[2] for x in m2[1:]]==['진행 0/100','미수락','3/7회','주간 2/5'], m2)
    check('c3 scheduler error shown', '조회 실패' in pg.inner_text('.dqc[data-dqchar=c3]'), pg.inner_text('.dqc[data-dqchar=c3]'))
    ov=pg.evaluate("(()=>{const o=document.querySelector('.dqc[data-dqchar=c1] .dqi[data-dqi=cer] .dqov'),cs=getComputedStyle(o),r=o.getBoundingClientRect(),c=o.parentElement.getBoundingClientRect();return {bg:cs.backgroundColor,pe:cs.pointerEvents,op:cs.opacity,cover:Math.abs(r.width-c.width)<2.5&&Math.abs(r.height-c.height)<2.5,t:o.textContent}})()")
    check('overlay = rgba(0,0,0,.55), covers cell, click-through, shows name + ✓ 완료', ov['bg']=='rgba(0, 0, 0, 0.55)' and ov['pe']=='none' and ov['op']=='1' and ov['cover'] and ov['t']=='세르니움✓ 완료', ov)
    check('underlying text hidden under overlay', pg.evaluate("getComputedStyle(document.querySelector('.dqc[data-dqchar=c1] .dqi[data-dqi=cer] .dqn')).opacity")=='0')
    check('same scheduler call auto-checked weekly bosses', pg.evaluate("Object.keys(S.characters[0].weekly).length")>=5, pg.evaluate("S.characters[0].weekly"))
    CLIP="[...document.querySelectorAll('.dqi')].filter(e=>{const r=e.getBoundingClientRect();return [...e.querySelectorAll('.dqn,.dqs')].some(n=>n.getBoundingClientRect().right>r.right+0.5)}).map(e=>e.innerText)"
    check('desktop: no clipped cell text', pg.evaluate(CLIP)==[], pg.evaluate(CLIP))
    pg.mouse.move(5,5); pg.wait_for_timeout(250); shot(pg,'tab_daily.png')
    pg.hover('.dqc[data-dqchar=c1] .dqi[data-dqi=cer]'); pg.wait_for_timeout(300)
    check('hover removes overlay (only hovered cell), original cell visible', pg.evaluate("getComputedStyle(document.querySelector('.dqc[data-dqchar=c1] .dqi[data-dqi=cer] .dqov')).opacity")=='0' and pg.evaluate("getComputedStyle(document.querySelector('.dqc[data-dqchar=c1] .dqi[data-dqi=cer] .dqn')).opacity")=='1' and pg.evaluate("getComputedStyle(document.querySelector('.dqc[data-dqchar=c1] .dqi[data-dqi=arcs] .dqov')).opacity")=='1')
    shot(pg,'tab_daily_hover.png'); pg.mouse.move(5,5)
    # 3) 편집 (설정 탭 없이 탭 안에서)
    check('no edit chips in normal mode', pg.query_selector('.dqchip') is None and pg.inner_text('#dqEditBtn')=='편집')
    pg.click('#dqEditBtn'); check('edit shows 10 item chips', pg.locator('.dqchip.on').count()==10 and pg.inner_text('#dqEditBtn')=='완료')
    pg.click('.dqchip[data-dqg=mp]'); check('global off: 몬스터파크 removed from every card', pg.locator('.dqi[data-dqi=mp]').count()==0 and pg.evaluate('S.dq.off.mp')==1)
    pg.click('.dqc[data-dqchar=c1] .dqi[data-dqi=cer]'); check('per-character off (edit shows it struck through)', pg.evaluate("S.dq.charOff.c1&&S.dq.charOff.c1.cer")==1 and pg.locator('.dqc[data-dqchar=c1] .dqi[data-dqi=cer].off').count()==1)
    pg.click('.dqc[data-dqchar=c4] [data-dqhide]'); check('hide character card', pg.evaluate("S.dq.hide.c4")==1 and 'hid' in pg.get_attribute('.dqc[data-dqchar=c4]','class'))
    pg.click('#dqEditBtn')
    check('after edit: c1 without 세르니움, c2 keeps it', pg.locator('.dqc[data-dqchar=c1] .dqi[data-dqi=cer]').count()==0 and pg.locator('.dqc[data-dqchar=c2] .dqi[data-dqi=cer]').count()==1)
    check('hidden card gone + footer note', pg.locator('.dqc[data-dqchar=c4]').count()==0 and '숨긴 캐릭터 1명' in pg.inner_text('.dqfoot'))
    check('count excludes hidden items (c1 4/6)', pg.inner_text('.dqc[data-dqchar=c1] .dqcnt')=='4/6', pg.inner_text('.dqc[data-dqchar=c1] .dqcnt'))
    # 4) 캐시·자동 갱신: 새로고침 후 10분 안이면 재호출 없음, 오래되면 그 캐릭터만
    n0=len(sched_calls()); pg.reload(); pg.wait_for_timeout(400); pg.click('[data-tab=daily]'); wait_idle(pg)
    check('settings persisted after reload', pg.evaluate("S.dq.off.mp===1&&S.dq.hide.c4===1&&S.dq.charOff.c1.cer===1"))
    check('cached (no new scheduler calls within 10 min)', len(sched_calls())==n0 and pg.locator('.dqc').count()==3, sched_calls()[n0:])
    pg.evaluate("schedC.c2.at-=11*60e3; tabTick()"); wait_idle(pg)
    check('auto refresh only stale char', sched_calls()[n0:]==['ocid-alt1'], sched_calls()[n0:])
    pg.evaluate("schedC.c4.at-=11*60e3; tabTick()"); wait_idle(pg)
    check('hidden char not refreshed', sched_calls()[n0:]==['ocid-alt1'], sched_calls()[n0:])
    # 5) 길드 현황
    pg.click('[data-tab=guild]'); pg.wait_for_selector('.gtile'); wait_idle(pg)
    gc=guild_calls(); print('guild calls',gc)
    ready=pg.evaluate("(()=>{const k=kst();return k.getUTCHours()*60+k.getUTCMinutes()>=570})()"); exp=today if ready else yday
    check('guild ranking called for type 2 and 1 with date', sorted(gc)==sorted([(exp,'2'),(exp,'1')]), gc)
    tiles=pg.eval_on_selector_all('.gtile','e=>e.map(x=>x.innerText.replace(/\\s+/g," ").trim())'); print(tiles)
    check('지하 수로 tile', '지하 수로' in tiles[0] and '137,591' in tiles[0] and '532위' in tiles[0], tiles)
    check('플래그 레이스 tile', '플래그 레이스' in tiles[1] and '4,000' in tiles[1] and '523위' in tiles[1], tiles)
    gt=pg.inner_text('.gcard'); check('guild level/master/date shown', 'Lv.30' in gt and '터래플' in gt and f'기준 {exp}' in gt and '봉사활동' in gt and '스카니아' in gt, gt)
    rows=pg.eval_on_selector_all('.grow-r','e=>e.map(x=>x.innerText.replace(/\\s+/g," ").trim())'); print(rows)
    check('main characters only, with 지하 수로 score from scheduler', len(rows)==1 and '단풍용사' in rows[0] and '23,513' in rows[0] and '10,000' in rows[0] and '10/10' in rows[0], rows)
    check('guild tab: no extra scheduler call for main (cached)', sched_calls()[n0:]==['ocid-alt1'], sched_calls()[n0:])
    pg.mouse.move(5,5); shot(pg,'tab_guild.png')
    # 랭킹 미준비 → 어제로 대체
    GUILD_EMPTY.add(today); g0=len(guild_calls())
    pg.evaluate("guildC=null; refreshGuild(true)"); wait_idle(pg)
    gt=pg.inner_text('.gcard'); check('fallback to yesterday when today empty', f'기준 {yday}' in gt and '어제' in gt and '137,591' in gt, (gt,guild_calls()[g0:]))
    GUILD_EMPTY.add(yday); pg.evaluate("refreshGuild(true)"); wait_idle(pg)
    gt=pg.inner_text('.gcard'); check('both empty → message, keeps last data', '찾지 못했습니다' in gt and '137,591' in gt, gt)
    GUILD_EMPTY.clear()
    # 본캐가 여러 명이어도 모두 표시 (현재 UI는 1명) / 없으면 안내
    pg.evaluate("S.characters.forEach(c=>c.isMain=false); renderGuild()"); check('no main → hint', '본캐로 지정된 캐릭터가 없습니다' in pg.inner_text('#view'))
    pg.evaluate("S.characters[0].isMain=true; save(); renderGuild()")
    # 6) 사이드바 캐릭터 클릭 → 보스 체크로 이동, 기존 탭 정상
    pg.click('#charList .char[data-id=c2]'); pg.wait_for_timeout(150); check('sidebar click → boss tab', pg.evaluate('tab')=='boss' and pg.evaluate('S.activeId')=='c2')
    for t in ['summary','history','total','boss']: pg.click(f'[data-tab={t}]'); pg.wait_for_timeout(80)
    check('existing tabs still render', pg.query_selector('#view .card') is not None)
    # 7) 모바일 375 / 320
    for w in (375,320):
        pg.set_viewport_size({'width':w,'height':800}); pg.click('[data-tab=daily]'); wait_idle(pg); pg.wait_for_timeout(150)
        check(f'{w}px daily: no horizontal overflow', pg.evaluate(NOOVF), pg.evaluate(OVFD))
        cols=pg.evaluate("(()=>{const xs=[...document.querySelectorAll('.dqc[data-dqchar=c1] .dqi')].map(e=>Math.round(e.getBoundingClientRect().top));return xs.filter(x=>x===xs[0]).length})()")
        check(f'{w}px daily: 3 cells per row', cols==3, cols)
        fit=pg.evaluate("[...document.querySelectorAll('.dqi')].every(e=>{const n=e.querySelector('.dqn'),r=e.getBoundingClientRect(),q=n.getBoundingClientRect();const d=e.querySelector('.dqs').getBoundingClientRect();return n.scrollWidth<=n.clientWidth+1&&q.right<=r.right+0.5&&d.right<=r.right+0.5&&e.scrollHeight<=e.clientHeight+1})")
        check(f'{w}px daily: item names/status not clipped', fit, pg.evaluate("[...document.querySelectorAll('.dqi')].filter(e=>{const n=e.querySelector('.dqn'),r=e.getBoundingClientRect(),q=n.getBoundingClientRect();return !(n.scrollWidth<=n.clientWidth+1&&q.right<=r.right+0.5&&e.scrollHeight<=e.clientHeight+1)}).map(e=>e.innerText)"))
        tabsOK=pg.evaluate("(()=>{const n=document.querySelector('#tabs');return getComputedStyle(n).overflowX==='auto'})()"); check(f'{w}px tabs scrollable', tabsOK)
        if w==375: shot(pg,'tab_daily_mobile.png',full_page=True)
        pg.click('[data-tab=guild]'); wait_idle(pg); pg.wait_for_timeout(150)
        check(f'{w}px guild: no horizontal overflow', pg.evaluate(NOOVF), pg.evaluate(OVFD))
        if w==375: shot(pg,'tab_guild_mobile.png',full_page=True)
    # 8) 라이트 테마도 깨지지 않음
    pg.set_viewport_size({'width':1366,'height':900}); pg.click('#themeBtn'); pg.click('[data-tab=daily]'); wait_idle(pg)
    check('light theme renders', pg.evaluate("document.documentElement.dataset.theme")=='light' and pg.locator('.dqc').count()==3)
    shot(pg,'tab_daily_light.png')
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
