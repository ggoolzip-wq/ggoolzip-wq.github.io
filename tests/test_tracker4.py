import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, urllib.parse
import sys
SHOT=sys.argv[1] if len(sys.argv)>1 else ''+OUT+'/screenshot.png'
URL='file://'+ROOT+'/index.html'
KM,KA='live_mock_MAIN','live_mock_ALT'
errs=[]
AV='<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><circle cx="48" cy="40" r="16" fill="#ffd9b3"/><rect x="34" y="56" width="28" height="26" rx="6" fill="{c}"/><path d="M32 36q16-22 32 0" fill="#7a4a2a"/></svg>'
ACC={KM:[('ocid-main','단풍용사','스카니아','히어로',287),('ocid-alt1','불독메이지','스카니아','아크메이지(불,독)',272),('ocid-alt2','신궁짱','스카니아','신궁',265),('ocid-luna','루나부캐','루나','아델',261)],
     KA:[('ocid-b1','부계정비숍','스카니아','비숍',268),('ocid-b2','부계정카인','베라','카인',262)]}
ALL={c[0]:c for v in ACC.values() for c in v}
SCHED={'ocid-main':([('스우','hard',1),('데미안','hard',1),('루시드','hard',1),('윌','hard',1),('진 힐라','hard',1),('선택받은 세렌','hard',1),('감시자 칼로스','normal',0),('최초의 대적자','easy',0),('카링','easy',0),('검은 마법사','hard',1)],6),
       'ocid-alt1':([('스우','하드',1),('데미안','노멀',1),('루시드','노말',0),('힐라','하드',1),('핑크빈','카오스',1)],2),
       'ocid-b1':([('가디언 엔젤 슬라임','normal',1),('더스크','normal',1),('듄켈','normal',0)],2),
       'ocid-b2':([('스우','normal',1)],1)}
def handle(route):
    u=urllib.parse.urlparse(route.request.url); q=dict(urllib.parse.parse_qsl(u.query)); p=u.path
    if '/static/maplestory/character/look/' in p:
        col={'main':'#f28c28','alt1':'#7b5cd6','alt2':'#2fa36b','b1':'#d94a7a','b2':'#3a8fd9'}.get(p.rsplit('-',1)[-1],'#4a90d9')
        return route.fulfill(status=200,content_type='image/svg+xml',body=AV.format(c=col))
    k=route.request.headers.get('x-nxopen-api-key')
    if k not in ACC: return route.fulfill(status=400,json={'error':{'name':'OPENAPI00005','message':'The apikey is not valid.'}})
    own={c[0] for c in ACC[k]}
    if p.endswith('/character/list'):
        return route.fulfill(json={'account_list':[{'account_id':'acc-'+k[-3:],'character_list':[{'ocid':o,'character_name':n,'world_name':w,'character_class':j,'character_level':l} for o,n,w,j,l in ACC[k]]}]})
    if p.endswith('/maplestory/v1/id'):
        m=[c for c in ALL.values() if c[1]==q.get('character_name')]
        return route.fulfill(json={'ocid':m[0][0]}) if m else route.fulfill(status=400,json={'error':{'name':'OPENAPI00004','message':'invalid'}})
    if p.endswith('/character/basic'):
        c=ALL[q['ocid']]
        body={'date':'2026-10-08T00:00+09:00','character_name':c[1],'world_name':c[2],'character_class':c[3],'character_level':c[4],'character_image':f'https://open.api.nexon.com/static/maplestory/character/look/mock-{c[0].split("-")[1]}'}
        EXP={'ocid-main':('73.512',123456789012),'ocid-alt1':('8.004',5550000000),'ocid-alt2':('99.990',1),'ocid-luna':('41.5',1),'ocid-b1':('0.123',1)}
        if q['ocid'] in EXP: body['character_exp_rate'],body['character_exp']=EXP[q['ocid']]
        return route.fulfill(json=body)
    if p.endswith('/scheduler/character-state'):
        if q['ocid'] not in own or q['ocid'] not in SCHED: return route.fulfill(status=400,json={'error':{'name':'OPENAPI00003','message':'Please input valid id'}})
        c=ALL[q['ocid']]; bs,cl=SCHED[q['ocid']]
        return route.fulfill(json={'date':'2026-10-09T00:00+09:00','character_name':c[1],'world_name':c[2],'character_level':c[4],'character_class':c[3],'daily_contents':[],'weekly_contents':[],
          'boss_contents':[{'content_name':n,'difficulty':d,'cycle':'bossMonthly' if n=='검은 마법사' else 'bossWeekly','list_order_no':i,'registration_flag':'true','complete_flag':'true' if f else 'false'} for i,(n,d,f) in enumerate(bs)],
          'weekly_boss_clear_count':cl,'weekly_boss_clear_limit_count':12})
    return route.fulfill(status=400,json={'error':{'name':'OPENAPI00006','message':'invalid path'}})

def st(pg): return json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
def names(pg): return pg.evaluate("orderedChars().map(c=>c.name)")  # 월드 탭(2026-10-10)으로 사이드바엔 한 월드만 보이므로 전체 순서는 상태에서
def worlds(pg): return pg.eval_on_selector_all('#worldTabs .wtab', "els=>els.map(e=>e.dataset.world)")
def wait_sync(pg): pg.wait_for_function("!syncing", timeout=20000); pg.wait_for_timeout(250)

with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    pg=ctx.new_page()
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)))
    pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' and 'status of 400' not in m.text else None)
    pg.goto(URL); pg.wait_for_timeout(200)
    wk=pg.evaluate('weekId()'); period={'week':wk,'day':pg.evaluate('dayId()'),'month':pg.evaluate('monthId()')}
    # ---- A. bug scenario: v2 data, single key overwritten with ALT key, main chars imported earlier
    mk=lambda o,lvl,main=False:{'id':'c-'+o,'name':ALL[o][1],'job':ALL[o][3],'level':lvl,'world':ALL[o][2],'ocid':o,'isMain':main,'bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{'ok':False,'msg':'old failure'}}
    chs=[mk('ocid-alt1',272),mk('ocid-main',287,True),mk('ocid-b1',268)]
    chs[0]['bosses']={'hilla':{'enabled':True,'diff':'hard','party':1},'cygnus':{'enabled':True,'diff':'easy','party':1},'lotus':{'enabled':True,'diff':'hard','party':1}}; chs[0]['weekly']={'hilla':True,'cygnus':True}
    v2={'version':2,'activeId':'c-ocid-main','characters':chs,'history':[],
        'settings':{'weeklyLimit':12,'monthlyLimit':1,'worldLimit':90,'prices':{'kaling_normal':576000000,'star_normal':593000000,'hilla_hard':2880000,'lotus_hard':50000000},'apiKey':KA,'apiMode':'direct','autoSync':True,'autoEnable':True,'lastSync':0},'period':period}
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(v2)); pg.reload(); wait_sync(pg)
    s=st(pg)
    print('A1 migrated accounts:', [(a['label'],a['key']) for a in s['settings']['accounts']], 'apiKey left:', 'apiKey' in s['settings'], 'version', s['version'])
    print('A2 order kept (main first):', names(pg))
    a1=[c for c in s['characters'] if c['name']=='불독메이지'][0]
    print('G1 v4 migration: version',s['version'],'| alt1 bosses',sorted(a1['bosses']),'weekly',sorted(a1['weekly']),'| prices',s['settings']['prices'])
    print('G1b alt1 jinhilla NOT auto-checked from 힐라:', 'jinhilla' not in a1['weekly'], '| unmatched:', a1['sync'].get('unmatched'))
    print('G1c BOSSES ids has hilla/pinkbean/cygnus:', pg.evaluate("BOSSES.filter(b=>['hilla','pinkbean','cygnus'].includes(b.id)).length"))
    print('A3 assignment after auto-sync:', {c['name']:(c.get('accId') and [a['label'] for a in s['settings']['accounts'] if a['id']==c['accId']][0], c['sync'].get('ok')) for c in s['characters']})
    print('A4 sidebar warn badges:', pg.locator('#charList .accb.warn').count(), '| no API side card:', pg.locator('#apiSide').count()==0, '| no settings tab:', pg.locator('[data-tab="settings"]').count()==0)
    # add main account key via the unified '+ 추가' modal
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(600)
    pg.fill(f'#importModal [data-acclabel="{s["settings"]["accounts"][0]["id"]}"]','부계정'); pg.press(f'#importModal [data-acclabel="{s["settings"]["accounts"][0]["id"]}"]','Tab'); pg.wait_for_timeout(100)
    pg.fill('#newAccLabel','본계정'); pg.fill('#newAccKey',KM); pg.click('#newAccBtn'); pg.wait_for_timeout(900)
    print('A5 key add auto-listed chars:', pg.inner_text('#impMsg'), '| items', pg.locator('#impList .imp-item').count(), '| accounts in modal:', pg.locator('#accList .accrow').count(), '| masked:', pg.eval_on_selector_all('#accList .kmask','e=>e.map(x=>x.textContent)'))
    pg.click('#impClose')
    pg.click('#syncBtn'); wait_sync(pg); s=st(pg)
    lab={a['id']:a['label'] for a in s['settings']['accounts']}
    print('A6 after sync:', {c['name']:(lab.get(c.get('accId')), c['sync'].get('ok'), sorted(c['weekly'])) for c in s['characters']})
    print('A7 toast:', pg.inner_text('#toast'))
    # wrong key on an account -> only that account's chars fail
    # ---- B. import from each account
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(500)
    print('B1 account rows:', pg.eval_on_selector_all('#accList .acclbl','e=>e.map(x=>x.value)'))
    pg.click('#accList .accrow:has(.acclbl[value="본계정"]) [data-acctest]'); pg.wait_for_timeout(500)
    print('B2 main list:', pg.eval_on_selector_all('#impList .imp-item b','e=>e.map(x=>x.textContent)'))
    pg.click('#impAll'); pg.click('#impOk'); wait_sync(pg)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(300); pg.click('#accList .accrow:has(.acclbl[value="부계정"]) [data-acctest]'); pg.wait_for_timeout(500)
    pg.click('#impAll'); pg.click('#impOk'); wait_sync(pg); s=st(pg); lab={a['id']:a['label'] for a in s['settings']['accounts']}
    print('B3 all chars:', [(c['name'],lab.get(c.get('accId')),c['world'],c['sync'].get('ok')) for c in s['characters']])
    print('B4 sidebar worlds/order:', worlds(pg), names(pg))
    print('G2 exp lines:', pg.eval_on_selector_all('#charList .char', "els=>els.map(e=>[e.querySelector('.nm').childNodes[0].textContent.trim(), e.querySelector('.exppct')?.textContent||null, e.querySelector('.expbar>i')?.style.width||null])"))
    print('G2b stored exp main:', [c.get('exp') for c in s['characters'] if c['name']=='단풍용사'])
    hs0=pg.evaluate("(()=>{document.body.classList.add('noexp');const s=document.createElement('style');s.id='nx';s.textContent='.noexp .expl{display:none}';document.head.append(s);const r=[...document.querySelectorAll('#charList .char')].map(e=>Math.round(e.getBoundingClientRect().height));s.remove();document.body.classList.remove('noexp');return r})()")
    print('G2c card heights without exp line:', hs0)
    hs=pg.evaluate("[...document.querySelectorAll('#charList .char')].map(e=>Math.round(e.getBoundingClientRect().height))")
    print('G2c card heights:', hs)
    # ---- C. reorder
    before=names(pg)
    pg.drag_and_drop('.char[data-id="c-ocid-b1"]', '.char[data-id="c-ocid-main"]', target_position={'x':40,'y':4}); pg.wait_for_timeout(200)
    print('C1 HTML5 drag 부계정비숍 above 단풍용사:', names(pg))
    print('C2 only selected world shown:', pg.evaluate("[...new Set([...document.querySelectorAll('#charList .char')].map(e=>e.dataset.world))]"))
    pg.click('[data-move="c-ocid-main|-1"]'); pg.wait_for_timeout(100)
    print('C3 ▲ on 단풍용사:', names(pg))
    # touch drag via pointer events on handle: move 불독메이지 to bottom of 스카니아
    pg.evaluate("""()=>{
      const src=document.querySelector('.char[data-id="c-ocid-alt1"] .drag-h');
      const rows=[...document.querySelectorAll('.char[data-world="스카니아"]')]; const last=rows.at(-1).getBoundingClientRect();
      const s=src.getBoundingClientRect(); const o={bubbles:true,cancelable:true,pointerId:7,pointerType:'touch',isPrimary:true};
      src.dispatchEvent(new PointerEvent('pointerdown',{...o,clientX:s.x+4,clientY:s.y+4}));
      document.dispatchEvent(new PointerEvent('pointermove',{...o,clientX:last.x+60,clientY:last.bottom-5}));
      document.dispatchEvent(new PointerEvent('pointerup',{...o,clientX:last.x+60,clientY:last.bottom-5}));
    }"""); pg.wait_for_timeout(150)
    print('C4 touch drag 불독메이지 to bottom:', names(pg))
    print('C5 worlds before:', worlds(pg))
    pg.drag_and_drop('.wtab[data-world="루나"]', '.wtab[data-world="스카니아"]', target_position={'x':2,'y':5}); pg.wait_for_timeout(150)
    print('C6 drag tab 루나 before 스카니아:', worlds(pg))
    pg.drag_and_drop('.wtab[data-world="베라"]', '.wtab[data-world="루나"]', target_position={'x':2,'y':5}); pg.wait_for_timeout(150)
    print('C7 HTML5 drag world 베라 above 루나:', worlds(pg))
    order=names(pg); wo=worlds(pg)
    # set main on another char & sync -> order unchanged
    pg.click('.char:has-text("신궁짱") [data-edit]'); pg.check('#fMain'); pg.click('#fSave'); pg.wait_for_timeout(100)
    pg.click('#syncBtn'); wait_sync(pg); pg.reload(); pg.wait_for_timeout(400); wait_sync(pg)
    print('C8 order persists after set-main+sync+reload:', names(pg)==order and worlds(pg)==wo, names(pg))
    # add manual char -> appended at end of its world
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.evaluate('closeImport();openCharModal()'); pg.fill('#fName','수동캐'); pg.fill('#fWorld','스카니아'); pg.select_option('#fAcc',''); pg.click('#fSave'); pg.wait_for_timeout(100)
    print('C9 manual add appended:', names(pg))
    print('G2d manual char exp hidden:', pg.locator('.char:has-text("수동캐") .expl').count()==0)
    # ---- D. icons
    pg.click('.char[data-id="c-ocid-main"]'); pg.click('[data-tab="boss"]'); pg.evaluate('editMode=true;render()'); pg.wait_for_timeout(100)
    print('D1 weekly edit icons img/fallback:', pg.locator('.boss img.bicon').count(), pg.locator('.boss span.bicon.fb').count(), pg.eval_on_selector_all('.boss span.bicon.fb','e=>e.map(x=>x.textContent)'))
    nat=pg.evaluate("Promise.all([...document.querySelectorAll('img.bicon')].map(i=>i.decode().then(()=>i.naturalWidth).catch(()=>0)))")
    print('D2 all icons decode:', all(n==64 for n in nat), len(nat))
    pg.evaluate("editMode=false;bossFilter='weekly';render()"); pg.wait_for_timeout(100)
    print('G3 drops on main boss rows:', pg.eval_on_selector_all('.boss', "els=>els.map(e=>[e.querySelector('.bn').textContent.trim().split(' ')[0], [...e.querySelectorAll('.drop .dn')].map(x=>x.textContent)]).filter(x=>x[1].length)"))
    nat=pg.evaluate("Promise.all([...document.querySelectorAll('.drop img')].map(i=>i.decode().then(()=>i.naturalWidth).catch(()=>0)))")
    print('G3b drop icons decode 32px:', all(n==32 for n in nat), len(nat), '| fallback:', pg.locator('.drop .ifb').count())
    print('G3c ITEM_ICONS keys missing:', pg.evaluate("Object.keys(ITEMS).filter(k=>!ITEM_ICONS[k])"), '| DROPS keys invalid:', pg.evaluate("Object.values(DROPS).flat().filter(([k,ds])=>!ITEMS[k]).length"), pg.evaluate("Object.entries(DROPS).flatMap(([b,l])=>l.flatMap(([k,ds])=>ds.filter(d=>!findBoss(b).diffs.includes(d)).map(d=>b+':'+k+':'+d)))"))
    rp=pg.evaluate("(()=>{const r=document.querySelector('.revpanel');if(!r)return null;const b=r.getBoundingClientRect(),m=document.querySelector('.bosslay>.grid').getBoundingClientRect();return {x:Math.round(b.x),w:Math.round(b.width),mainRight:Math.round(m.right),total:r.querySelector('.rp-total').textContent,chars:r.querySelectorAll('.rp-char').length,worlds:r.querySelectorAll('.rp-world').length,app:meso(allRevenue().total)}})()")
    print('G4 revpanel desktop:', rp)
    pg.click('.revpanel .rp-char:nth-child(2)'); pg.wait_for_timeout(100); print('G4b click panel char selects:', pg.evaluate('activeChar().name'))
    pg.evaluate("setWorldTab('스카니아')"); pg.click('.char[data-id="c-ocid-main"]'); pg.wait_for_timeout(100)  # 다른 월드 캐릭터를 고른 뒤라 스카니아 탭으로
    # ---- E. export excludes keys
    print('G5 UI markers gone (src tags / 공식 / 커뮤니티 text in UI):', pg.locator('.src').count(), pg.evaluate("document.body.innerText.includes('커뮤니티')||document.body.innerText.includes('공식 20')"), '| one price per row:', pg.evaluate("[...document.querySelectorAll('table tr:has(input[data-price])')].every(r=>r.querySelectorAll('input[data-price]').length===1)"), pg.locator('input[data-price]').count())
    print('G5b prices kaling/star/will/damien:', pg.evaluate("[PRICE_CONFIG.kaling_normal,PRICE_CONFIG.star_normal,PRICE_CONFIG.will_easy,PRICE_CONFIG.damien_normal]"))
    exp={'data':pg.evaluate('backupData(false)')}
    print('E1 no JSON export/import UI:', pg.query_selector('#exportBtn') is None and pg.query_selector('#importFile') is None, '| compare-serialization accounts:', exp['data']['settings']['accounts'], '| key in it:', KM in json.dumps(exp) or KA in json.dumps(exp))
    # 키 없는 데이터 적용 → 계정 id 기준으로 키 다시 연결
    pg.evaluate('applyData(backupData(false))'); pg.wait_for_timeout(500); s=st(pg)
    print('E2 keys after re-import:', [(a['label'],bool(a.get('key'))) for a in s['settings']['accounts']])
    # ---- F. screenshot
    pg.evaluate("""S.history=[['2026-08-20',1520],['2026-08-27',1610],['2026-09-03',1480],['2026-09-10',1750],['2026-09-17',1210],['2026-09-24',1330],['2026-10-01',1390]].map(([w,t])=>({week:w,total:t*1e6,cleared:18,crystals:18,perChar:[]}));
       S.characters=S.characters.filter(c=>c.name!=='수동캐'); S.activeId='c-ocid-main'; tab='boss'; syncTabs(); save(); render();""")
    if pg.locator('[data-party="seren"]').count(): pg.select_option('[data-party="seren"]','2')
    else: print('note: seren row not visible, view=', pg.evaluate('tab'), pg.evaluate('activeChar()&&activeChar().name'))
    pg.evaluate("window.scrollTo(0,0);document.querySelector('#toast').classList.remove('show')"); pg.wait_for_timeout(500)
    pg.screenshot(path=SHOT,full_page=True)
    for t in ['summary']:
        pg.click(f'[data-tab="{t}"]'); pg.evaluate("window.scrollTo(0,0);document.querySelector('#toast').classList.remove('show')"); pg.wait_for_timeout(300)
        pg.screenshot(path=OUT+f'/shot4_{t}.png',full_page=True)
    data=st(pg)
    m=ctx.new_page(); m.set_viewport_size({'width':390,'height':844}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)", json.dumps({**data,'theme':'dark'})); m.reload(); m.wait_for_timeout(600)
    m.screenshot(path=OUT+'/shot4_mobile_dark.png', full_page=True)
    print('G6b overflowing els:', m.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(e=>e.tagName+'.'+e.className+' '+Math.round(e.getBoundingClientRect().right))"))
    print('G6 mobile revpanel below main:', m.evaluate("(()=>{const r=document.querySelector('.revpanel').getBoundingClientRect(),g=document.querySelector('.bosslay>.grid').getBoundingClientRect();return r.top>=g.bottom-1 && Math.abs(r.x-g.x)<2})()"), '| horiz overflow:', m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    b.close()
print('ERRORS:',errs)
