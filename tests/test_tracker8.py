import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json
URL='file://'+ROOT+'/index.html'; errs=[]
OUT=ROOT+'/'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR',accept_downloads=True)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(200)
    wk=pg.evaluate('weekId()'); per={'week':wk,'day':pg.evaluate('dayId()'),'month':pg.evaluate('monthId()')}
    B=lambda **kw:{k:{'enabled':True,'diff':v[0],'party':v[1]} for k,v in kw.items()}
    def ch(i,name,bosses,weekly,monthly=None,drops=None):
        return {'id':'c'+str(i),'name':name,'level':280,'job':'히어로','world':'스카니아','isMain':i==1,'ocid':'','bosses':bosses,'weekly':weekly,'monthly':monthly or {},'auto':{},'sync':{},'drops':drops or {}}
    # legacy: c1 already has 2 white boxes from seren without outcomes (pre-feature)
    chars=[ch(1,'단풍용사',B(lotus=('hard',1),seren=('hard',1),blackmage=('hard',1),kalos=('chaos',1)),{'lotus':True,'seren':True,'kalos':True},{'blackmage':wk},{'seren|r_white':2}),
           ch(2,'불독메이지',B(slime=('chaos',1)),{'slime':True})]
    hist=[{'week':'2026-09-24','weeklyOnly':True,'total':1e9,'cleared':3,'crystals':3,'perChar':[{'id':'c1','name':'단풍용사','meso':1e9,'items':{'lotus|r_red':3},'outcomes':{'lotus|r_red':['x','r4']}}]}]
    st={'version':5,'activeId':'c1','characters':chars,'history':hist,'monthHistory':[],'worldOrder':[],'settings':{'weeklyLimit':12,'monthlyLimit':1,'prices':{},'accounts':[],'apiMode':'direct','autoSync':False,'autoEnable':True,'lastSync':0},'period':per}
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); pg.reload(); pg.wait_for_timeout(400)
    st_=lambda: pg.evaluate("activeChar()")
    print('P0 legacy shows 미기록 (not 꽝):', pg.inner_text('.boss:has-text("선택받은 세렌") .ringouts'))
    rev0=pg.evaluate("allRevenue().total")
    # cancel paths
    for how in ['x','esc','backdrop']:
        pg.click('.boss:has-text("스우") [data-drop="lotus|r_red"]'); pg.wait_for_selector('#ringModal.show')
        if how=='x': pg.click('#ringClose')
        elif how=='esc': pg.keyboard.press('Escape')
        else: pg.mouse.click(10,500)
        pg.wait_for_timeout(100); print('C cancel via',how,'→ modal open:', pg.is_visible('#ringModal.show'), '| drops:', st_()['drops'], '| outs:', st_().get('dropOut'))
    # modal screenshot
    pg.click('.boss:has-text("스우") [data-drop="lotus|r_red"]'); pg.wait_for_selector('#ringModal.show'); pg.wait_for_timeout(200)
    print('M modal:', pg.inner_text('#ringModal .modal').replace('\n',' | '), '| ring icons:', pg.evaluate("[...document.querySelectorAll('#ringModal .ringico img')].map(i=>i.naturalWidth)"))
    pg.screenshot(path=OUT+'ringbox_modal.png')
    # choice r4 → celebrate
    pg.click('#ringModal [data-ring="r4"]'); pg.wait_for_timeout(650)
    print('R4 congrats visible:', pg.is_visible('#congrats.show'), pg.inner_text('#congrats').replace('\n',' | '), '| canvas drawn:', pg.evaluate("(()=>{const c=document.querySelector('#fx');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=40)if(d[i])n++;return n})()")>50)
    pg.screenshot(path=OUT+'ringbox_congrats.png')
    pg.wait_for_timeout(2400); print('R4b auto-ended:', not pg.is_visible('#congrats.show'), not pg.evaluate("celebrate.running"))
    print('R4c stored:', st_()['drops'], st_()['dropOut'])
    # c4 on seren white (legacy 2) and x on kalos life; dismiss congrats by click
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|r_white"]'); pg.click('#ringModal [data-ring="c4"]'); pg.wait_for_timeout(300); pg.click('#congrats'); pg.wait_for_timeout(100)
    print('C4 clicked-dismiss:', not pg.is_visible('#congrats.show'))
    pg.click('.boss:has-text("감시자 칼로스") [data-drop="kalos|r_life"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(150)
    print('X no congrats:', not pg.is_visible('#congrats.show'), '| toast:', pg.inner_text('#toast'))
    pg.click('.boss:has-text("감시자 칼로스") [data-drop="kalos|r_life"]'); pg.click('#ringModal [data-ring="r4"]'); pg.wait_for_timeout(100); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    print('Esc ends congrats:', not pg.is_visible('#congrats.show'))
    c=st_(); print('S stored drops:', c['drops'], '| outs:', c['dropOut'], '| revenue unchanged:', pg.evaluate("allRevenue().total")==rev0)
    print('S row texts:', pg.eval_on_selector_all('.ringouts','e=>e.map(x=>x.innerText.replace(/\\n/g," "))'))
    # undo latest: kalos had [x, r4] → − removes r4
    pg.click('[data-dropdec="kalos|r_life"]'); pg.wait_for_timeout(80)
    print('U undo:', st_()['drops'].get('kalos|r_life'), st_()['dropOut'].get('kalos|r_life'))
    # seren: legacy 2 + c4 → undo removes c4 → then 2 legacy remain, outs deleted
    pg.click('[data-dropdec="seren|r_white"]'); pg.wait_for_timeout(80)
    print('U2 undo seren:', st_()['drops'].get('seren|r_white'), st_()['dropOut'].get('seren|r_white'), '|', pg.inner_text('.boss:has-text("선택받은 세렌") .ringouts'))
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|r_white"]'); pg.click('#ringModal [data-ring="c4"]'); pg.wait_for_timeout(100); pg.evaluate("endCelebrate()")
    # monthly boss ring box
    pg.click('[data-filter="monthly"]'); pg.click('[data-drop="blackmage|r_white"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(100)
    print('MO monthly stored:', st_()['mdrops'], st_()['mdropOut']); pg.click('[data-filter="weekly"]'); pg.wait_for_timeout(80)
    # second char
    pg.click('.char[data-id="c2"]'); pg.click('[data-drop="slime|r_black"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(80); pg.click('.char[data-id="c1"]'); pg.wait_for_timeout(80)
    print('RP right panel:', pg.eval_on_selector_all('.revpanel .rp-items','e=>e.map(x=>x.innerText.replace(/\\n/g," "))'))
    pg.evaluate("document.querySelector('#toast').classList.remove('show')")
    pg.screenshot(path=OUT+'screenshot.png',full_page=True)
    # history
    pg.click('[data-tab="history"]'); pg.wait_for_timeout(100)
    print('H history:', pg.eval_on_selector_all('.htable .hitems','e=>e.map(x=>x.innerText.replace(/\\n/g," "))'))
    print('H monthly:', pg.eval_on_selector_all('#view .card:last-child .hitems','e=>e.map(x=>x.innerText.replace(/\\n/g," "))'))
    # totals
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(100)
    print('T ring summary:', pg.inner_text('.ringsum'))
    print('T ring tally:', pg.evaluate("totalData().ring"))
    print('T per item:', pg.eval_on_selector_all('#view table tbody tr','e=>e.map(x=>x.innerText.replace(/\\s+/g," ")).filter(t=>t.includes("반지"))'))
    pg.screenshot(path=OUT+'/shot8_total.png',full_page=True)
    # export
    ex=pg.evaluate('gdPayload().data'); print('B backup outs:', ex['characters'][0].get('dropOut'), ex['characters'][0].get('mdropOut'))
    # reset archive
    pg.evaluate("S.history=S.history.filter(h=>h.week!=='2026-10-01'); S.period.week='2026-10-01'; S.period.month='2026-09'; checkResets(); render();")
    s=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    a=[h for h in s['history'] if h['week']=='2026-10-01'][0]
    print('A week archived outcomes:', [(p['name'],p.get('items'),p.get('outcomes')) for p in a['perChar'] if p.get('items')])
    print('A month archived:', [(m['month'],[(p['name'],p.get('items'),p.get('outcomes')) for p in m['perChar']]) for m in s['monthHistory']])
    print('A cleared:', [(c['drops'],c['dropOut'],c['mdrops'],c['mdropOut']) for c in s['characters']])
    pg.evaluate("tab='total';syncTabs();render()"); print('A totals after archive:', pg.evaluate("totalData().ring"))
    # mobile
    m=ctx.new_page(); m.set_viewport_size({'width':390,'height':844}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)", json.dumps(st)); m.reload(); m.wait_for_timeout(300)
    m.click('.boss:has-text("스우") [data-drop="lotus|r_red"]'); m.wait_for_selector('#ringModal.show'); m.wait_for_timeout(150)
    print('MB modal fits:', m.evaluate("(()=>{const r=document.querySelector('#ringModal .modal').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight})()"))
    m.screenshot(path=OUT+'/shot8_modal_mobile.png')
    m.click('#ringModal [data-ring="c4"]'); m.wait_for_timeout(600); m.screenshot(path=OUT+'/shot8_congrats_mobile.png')
    print('MB congrats:', m.is_visible('#congrats.show'), '| overflow:', m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    m.wait_for_timeout(2400); m.evaluate("tab='total';syncTabs();render()"); m.wait_for_timeout(100)
    print('MB total overflow:', m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    b.close()
print('ERRORS:',errs)
