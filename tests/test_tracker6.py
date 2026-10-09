import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json
URL='file://'+ROOT+'/index.html'; errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',lambda r:r.fulfill(status=400,json={'error':{'name':'OPENAPI00005','message':'x'}}))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(200)
    wk=pg.evaluate('weekId()'); per={'week':wk,'day':pg.evaluate('dayId()'),'month':pg.evaluate('monthId()')}
    def ch(i,name,lvl,job,world,acc=None,main=False,ocid=None,bosses=None,weekly=None,monthly=None):
        return {'id':'c'+str(i),'name':name,'level':lvl,'job':job,'world':world,'accId':acc,'isMain':main,'ocid':ocid or '', 'bosses':bosses or {},'weekly':weekly or {},'monthly':monthly or {},'auto':{},'sync':{},
                'exp':{'rate':55.5,'exp':1,'level':lvl,'date':'','at':0}}
    B=lambda **kw:{k:{'enabled':True,'diff':v[0],'party':v[1]} for k,v in kw.items()}
    chars=[ch(1,'가나다라마바사아자차카',287,'아크메이지(불,독)','스카니아','A',True,'o1',B(lotus=('normal',1),seren=('extreme',1),blackmage=('hard',1),kaling=('easy',1)),{'lotus':True,'seren':True},{'blackmage':wk}),
           ch(2,'WWWWWWWWWWWW',262,'듀얼블레이드','스카니아','B',False,'o2',B(will=('hard',2),blackmage=('extreme',3)),{'will':True},{}),
           ch(3,'짧은이름',100,'와일드헌터','루나',None,False,'o3'),
           ch(4,'긴이름의캐릭터입니다',9,'블래스터','루나','A')]
    hist=[{'week':'2026-09-24','total':5000000000+4500000000,'cleared':3,'crystals':3,'perChar':[{'name':'가나다라마바사아자차카','meso':9500000000,'count':3,'bosses':['스우(노멀)','검은 마법사(하드)','윌(하드)/2인']}]}]
    st={'version':4,'activeId':'c1','characters':chars,'history':hist,'worldOrder':[],'settings':{'weeklyLimit':12,'monthlyLimit':1,'worldLimit':90,'prices':{},'accounts':[{'id':'A','label':'본계정','key':'live_x'},{'id':'B','label':'부계정1','key':'live_y'}],'apiMode':'direct','autoSync':False,'autoEnable':True,'lastSync':0},'period':per}
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); pg.reload(); pg.wait_for_timeout(400)
    s=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    bm=pg.evaluate("price(findBoss('blackmage'),'hard')")
    print('M0 v5 migration:', s['version'], 'worldLimit gone:', 'worldLimit' not in s['settings'], '| hist total', s['history'][0]['total'], 'expected', 9500000000-bm, '| bosses', s['history'][0]['perChar'][0]['bosses'], 'cleared', s['history'][0]['cleared'])
    r=pg.evaluate("(()=>{const a=allRevenue();return {total:a.total,month:a.monthTotal,mc:a.monthCount,count:a.count,c1:charRevenue(S.characters[0]).meso,c1m:charRevenue(S.characters[0]).monthMeso}})()")
    exp_w=pg.evaluate("price(findBoss('lotus'),'normal')+price(findBoss('seren'),'extreme')+Math.floor(price(findBoss('will'),'hard')/2)")
    exp_m=bm
    print('M1 weekly excludes monthly:', r['total']==exp_w, r, '| expected month', exp_m, r['month']==exp_m)
    print('M2 sidebar rev c1 = weekly only:', pg.inner_text('.char[data-id="c1"] .rev'), '| expected', pg.evaluate(f"meso({r['c1']})"))
    print('M3 revpanel:', pg.inner_text('.revpanel .rp-total'), '|', pg.inner_text('.revpanel .rp-month') if pg.locator('.rp-month').count() else None, '| world section gone:', pg.locator('.rp-world').count()==0 and 'rp-sec' in pg.inner_html('.revpanel') and '월드별' not in pg.inner_text('.revpanel'))
    print('M4 boss stats:', pg.eval_on_selector_all('#view .stat .k','e=>e.map(x=>x.textContent)'), pg.inner_text('#view .stat:nth-child(3) .v'))
    pg.click('[data-tab="total"]'); pg.wait_for_timeout(100)
    print('M5 summary stats:', pg.eval_on_selector_all('#view .stat','e=>e.map(x=>x.innerText.replace(/\\n/g," / "))'), '| 90 anywhere:', '/ 90' in pg.inner_text('#view'))
    pg.screenshot(path=OUT+'/shot6_summary.png',full_page=True)
    # week rollover → history weekly only; month rollover → monthHistory
    pg.evaluate("S.period.week='2026-10-01'; S.period.month='2026-09'; checkResets(); render();")
    s=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    h=[x for x in s['history'] if x['week']=='2026-10-01'][0]
    print('M6 rollover week total == weekly only:', h['total']==exp_w, h['total'], [p['bosses'] for p in h['perChar'] if p['bosses']], '| monthHistory:', s.get('monthHistory'))
    pg.evaluate("document.querySelector('#view').innerHTML='<h2>(주간 기록 탭 삭제됨)</h2>'"); pg.wait_for_timeout(100); print('M7 history cards:', pg.eval_on_selector_all('#view h2','e=>e.map(x=>x.textContent)'))
    pg.screenshot(path=OUT+'/shot6_history.png',full_page=True)
    # restore & ring drops
    pg.reload(); pg.wait_for_timeout(300)
    print('R1 dropsFor:', pg.evaluate("Object.fromEntries([['lotus','normal'],['lotus','extreme'],['seren','normal'],['seren','extreme'],['kalos','chaos'],['jinhilla','normal'],['bellona','hard'],['jupiter','normal'],['blackmage','hard'],['zakum','chaos']].map(([b,d])=>[b+':'+d,dropsFor(findBoss(b),d)]))"))
    print('R2 RING_DROPS diffs valid:', pg.evaluate("Object.entries(RING_DROPS).flatMap(([k,m])=>Object.entries(m).flatMap(([b,ds])=>ds.filter(d=>!findBoss(b)||!findBoss(b).diffs.includes(d)).map(d=>k+':'+b+':'+d)))"), '| icons:', pg.evaluate("['r_green','r_red','r_black','r_white','r_life'].every(k=>ITEM_ICONS[k])"))
    pg.click('[data-tab="boss"]'); pg.wait_for_timeout(100)
    rows=pg.evaluate("[...document.querySelectorAll('.boss')].map(e=>{const d=e.querySelector('.drops');return [e.querySelector('.bn').textContent.trim().split(/\\s+/)[0], d?[...d.querySelectorAll('.drop:not(.erda)')].map(x=>x.querySelector('.dn').textContent):[], d?Math.round(d.getBoundingClientRect().height):0, d?d.scrollWidth<=d.clientWidth+1:true]})")
    print('R3 boss rows chips (name, chips, height, fits):', rows)
    pg.screenshot(path=OUT+'/shot6_boss.png',full_page=True)
    def lvcheck(page,tag):
        res=page.evaluate("""[...document.querySelectorAll('#charList .char')].map(c=>{const lv=c.querySelector('.lv'),g=c.querySelector('.grow');const a=lv.getBoundingClientRect(),gr=g.getBoundingClientRect();
          return [c.querySelector('.nm').textContent.trim().slice(0,6), lv.textContent, lv.scrollWidth<=lv.clientWidth+0.5 && a.right<=gr.right+0.5 && a.width>0, Math.round(c.getBoundingClientRect().height)]})""")
        print(tag, 'level fully visible:', all(x[2] for x in res), res, '| accb in cards/header:', page.locator('#charList .accb').count(), page.locator('#view .card .accb').count())
    lvcheck(pg,'L1 1280')
    for w in (1000,760,390,340):
        pg.set_viewport_size({'width':w,'height':900}); pg.wait_for_timeout(150); lvcheck(pg,f'L {w}')
        if w==390: pg.screenshot(path=OUT+'/shot6_mobile.png',full_page=False)
    pg.set_viewport_size({'width':1280,'height':1000}); pg.wait_for_timeout(100)
    pg.locator('#charList').screenshot(path=OUT+'/shot6_sidebar.png')
    b.close()
print('ERRORS:',errs)
