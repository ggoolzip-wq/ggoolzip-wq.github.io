import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, datetime
URL='file://'+ROOT+'/index.html'; errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR',accept_downloads=True)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(200)
    wk=pg.evaluate('weekId()'); per={'week':wk,'day':pg.evaluate('dayId()'),'month':pg.evaluate('monthId()')}
    B=lambda **kw:{k:{'enabled':True,'diff':v[0],'party':v[1]} for k,v in kw.items()}
    def ch(i,name,lvl,job,world,main=False,bosses=None,weekly=None,monthly=None):
        return {'id':'c'+str(i),'name':name,'level':lvl,'job':job,'world':world,'isMain':main,'ocid':'','bosses':bosses or {},'weekly':weekly or {},'monthly':monthly or {},'auto':{},'sync':{}}
    chars=[ch(1,'단풍용사',287,'히어로','스카니아',True,B(lotus=('hard',1),damien=('hard',1),lucid=('hard',1),will=('hard',1),jinhilla=('hard',1),seren=('hard',1),kalos=('normal',1),blackmage=('hard',1)),{'lotus':True,'damien':True,'lucid':True,'will':True,'jinhilla':True,'seren':True},{'blackmage':wk}),
           ch(2,'불독메이지',272,'아크메이지(불,독)','스카니아',False,B(lotus=('hard',1),damien=('normal',1),slime=('chaos',2)),{'lotus':True,'slime':True}),
           ch(3,'루나아델',261,'아델','루나',False,B(lotus=('normal',1)),{})]
    d0=datetime.date.fromisoformat(wk)
    hist=[]
    for i in range(30,0,-1):
        w=(d0-datetime.timedelta(days=7*i)).isoformat(); t1=(900+i*13%250)*1_000_000; t2=(300+i*7%90)*1_000_000
        pc=[{'id':'c1','name':'단풍용사','meso':t1,'count':6,'bosses':[]},{'id':'c2','name':'불독메이지' if i>5 else '불독메이지','meso':t2,'count':3,'bosses':[]}]
        if i%4==0: pc[0]['items']={'seren|daybreak':1}
        if i%7==0: pc[1]['items']={'lotus|r_red':1,'slime|r_black':1}
        if i==20: pc.append({'name':'삭제된캐릭','meso':50_000_000,'count':1,'bosses':[]})
        hist.append({'week':w,'weeklyOnly':True,'total':sum(x['meso'] for x in pc),'cleared':9,'crystals':9,'perChar':pc})
    mh=[{'month':'2026-08','total':465000000,'cleared':1,'perChar':[{'id':'c1','name':'단풍용사','meso':465000000,'bosses':['검은 마법사(하드)'],'items':{'blackmage|genesis':1}}]},
        {'month':'2026-09','total':465000000,'cleared':1,'perChar':[{'id':'c1','name':'단풍용사','meso':465000000,'bosses':['검은 마법사(하드)']}]}]
    st={'version':5,'activeId':'c1','characters':chars,'history':hist,'monthHistory':mh,'worldOrder':[],'settings':{'weeklyLimit':12,'monthlyLimit':1,'prices':{},'accounts':[],'apiMode':'direct','autoSync':False,'autoEnable':True,'lastSync':0},'period':per}
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); pg.reload(); pg.wait_for_timeout(400)
    s0=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    print('D0 startWeek persisted:', s0['startWeek'], '== earliest', hist[0]['week'], s0['startWeek']==hist[0]['week'])
    total_before=pg.evaluate("allRevenue().total")
    # drop clicks
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|daybreak"]'); pg.wait_for_timeout(80)
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|daybreak"]'); pg.wait_for_timeout(80)
    pg.click('.boss:has-text("스우") [data-drop="lotus|r_red"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(80)
    print('D1 counts after clicks:', pg.evaluate("activeChar().drops"), '| chip text:', pg.inner_text('[data-drop="seren|daybreak"]'), '| got class:', pg.get_attribute('[data-drop="seren|daybreak"]','class'))
    pg.click('[data-dropdec="seren|daybreak"]'); pg.wait_for_timeout(80)
    pg.click('[data-drop="lotus|r_red"]', button='right'); pg.wait_for_timeout(80)
    print('D2 after −1 and right-click:', pg.evaluate("activeChar().drops"), '| revenue unchanged:', pg.evaluate("allRevenue().total")==total_before)
    # +N expand → hidden chip clickable
    more=pg.locator('.boss:has-text("선택받은 세렌") [data-dropmore]')
    print('D3 seren chips before expand:', pg.eval_on_selector_all('.boss:has-text("선택받은 세렌") .drop .dn','e=>e.map(x=>x.textContent)'))
    if more.count(): more.first.click(); pg.wait_for_timeout(80)
    print('D3b after expand:', pg.eval_on_selector_all('.boss:has-text("선택받은 세렌") .drop .dn','e=>e.map(x=>x.textContent)'))
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|r_white"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(80)
    # monthly boss drop
    pg.click('[data-filter="monthly"]'); pg.wait_for_timeout(80); pg.click('[data-drop="blackmage|genesis"]'); pg.wait_for_timeout(80)
    print('D4 monthly drop stored in mdrops:', pg.evaluate("activeChar().mdrops"), '| weekly drops:', pg.evaluate("activeChar().drops"))
    pg.click('[data-filter="weekly"]'); pg.wait_for_timeout(80)
    # second char drop
    pg.click('.char[data-id="c2"]'); pg.wait_for_timeout(80); pg.click('[data-drop="slime|r_black"]'); pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(80)
    print('D5 right panel items:', pg.eval_on_selector_all('.revpanel .rp-char','e=>e.map(x=>[x.querySelector(".rp-nm").textContent.trim(), [...x.querySelectorAll(".iti")].map(i=>i.title)])'), '|', pg.inner_text('.revpanel').split('\n')[-1])
    pg.click('.char[data-id="c1"]'); pg.wait_for_timeout(80)
    pg.screenshot(path=OUT+'/shot7_boss.png',full_page=True)
    # history tab
    pg.click('[data-tab="history"]'); pg.wait_for_timeout(100)
    print('H1 history rows:', pg.locator('.htable tbody tr').count(), '| chart bars:', pg.locator('.chart rect').count(), '| this week items:', pg.inner_text('.htable tbody tr:first-child').replace('\n',' | ')[:220])
    pg.screenshot(path=OUT+'/shot7_history.png',full_page=True)
    # total tab
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(150)
    T=pg.evaluate("(()=>{const T=totalData();return {weeks:T.weeks.length,w:T.wTotal,m:T.mTotal,g:T.grand,chars:T.chars.map(c=>[c.name,c.week,c.month,c.items]),items:T.items.map(([k,I])=>[k,I.n,I.by])}})()")
    exp_w=sum(h['total'] for h in hist)+pg.evaluate("allRevenue().total"); exp_m=930000000+pg.evaluate("allRevenue().monthTotal")
    print('T1 totals ok:', T['weeks']==31, T['w']==exp_w, T['m']==exp_m, T['g']==exp_w+exp_m, '| chars:', T['chars'])
    print('T2 items:', T['items'])
    print('T3 UI:', pg.eval_on_selector_all('#view .stat','e=>e.map(x=>x.innerText.replace(/\\n/g," / "))'), '| bars', pg.locator('.chart rect').count(), 'line pts', pg.locator('.chart circle').count(), '| week rows', pg.locator('#view .card:last-child tbody tr').count())
    print('T4 tab order:', pg.eval_on_selector_all('#tabs button','e=>e.map(x=>x.textContent)'))
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(100)
    pg.screenshot(path=''+OUT+'/total.png',full_page=True)
    # export includes startWeek/history/monthHistory/drops
    ex=pg.evaluate('gdPayload().data')
    print('B1 backup has startWeek/history/monthHistory/drops:', ex.get('startWeek'), len(ex['history']), len(ex['monthHistory']), ex['characters'][0].get('drops'), ex['characters'][0].get('mdrops'))
    # week rollover archive + month rollover
    pg.evaluate("S.period.week='"+(d0-datetime.timedelta(days=0)).isoformat()+"'; S.period.week=weekId(); S.period.week=(()=>{const d=new Date(weekId()+'T00:00:00Z');d.setUTCDate(d.getUTCDate()-0);return weekId();})();")
    prev=(d0+datetime.timedelta(days=0)).isoformat()
    pg.evaluate("(()=>{ S.period.month='2026-09'; S.period.week=S.period.week; const cw=S.period.week; S.period.week='2026-01-01'; const sum=weekSummary(cw); S.period.week=cw; })()")
    # simulate: pretend current period is last week by setting period.week to a fake older id then checkResets
    pg.evaluate("S.history=S.history.filter(h=>h.week!=='2026-10-01'); S.period.week='2026-10-01'; checkResets(); render();")
    s=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    a=[h for h in s['history'] if h['week']=='2026-10-01'][0]
    print('R1 archived week items:', a.get('items'), [ (p['name'],p.get('items')) for p in a['perChar'] if p.get('items')], '| drops cleared:', [c['drops'] for c in s['characters']])
    print('R2 month archived:', [ (m['month'], m.get('perChar')) for m in s['monthHistory'] if m['month']=='2026-09'], '| mdrops cleared:', [c['mdrops'] for c in s['characters']])
    print('R3 history never trimmed:', len(s['history']), '| startWeek kept:', s['startWeek'])
    # mobile
    data=s
    m=ctx.new_page(); m.set_viewport_size({'width':390,'height':844}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)", json.dumps(st)); m.reload(); m.wait_for_timeout(300)
    m.click('[data-tab="total"]') if m.is_visible('[data-tab="total"]') else m.evaluate("tab='total';syncTabs();render()")
    m.wait_for_timeout(200)
    print('M1 mobile total overflow (page):', m.evaluate('document.documentElement.scrollWidth>innerWidth'), '| chart scrolls inside:', m.evaluate("(()=>{const c=document.querySelector('.chart');return c.scrollWidth>c.clientWidth})()"))
    m.screenshot(path=OUT+'/shot7_total_mobile.png',full_page=True)
    m.evaluate("tab='boss';syncTabs();render()"); m.wait_for_timeout(150)
    print('M2 mobile boss overflow:', m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    m.screenshot(path=OUT+'/shot7_boss_mobile.png',full_page=False)
    b.close()
print('ERRORS:',errs)
