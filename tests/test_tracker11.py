import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, re
URL='file://'+ROOT+'/index.html'; errs=[]; fails=[]
def check(name,cond,detail=''):
    print(('PASS ' if cond else 'FAIL ')+name+(' — '+str(detail) if detail else '')); 
    if not cond: fails.append(name)
JS_VIEWS=r"""()=>{
 const T=e=>e.innerText.replace(/\s+/g,' ').trim(); const out={boss:[],panel:[],hist:[],month:[]};
 // 보스 행: 모든 캐릭터 × 주간/월간 (render 를 직접 바꿔 가며 수집)
 const keep=[S.activeId, typeof bossFilter!=='undefined'?bossFilter:null];
 for(const c of S.characters){ S.activeId=c.id;
   for(const f of ['weekly','monthly']){ document.querySelector(`[data-filter="${f}"]`)?.click();
     document.querySelectorAll('#view .boss').forEach(row=>{ const d=row.querySelector('[data-drop]'); if(!d) return; const b=findBoss(d.dataset.drop.split('|')[0]);
       row.querySelectorAll('.ringouts .dlt').forEach(l=>out.boss.push([c.name,b.name,T(l)])); }); } }
 S.activeId=keep[0]; render();
 document.querySelectorAll('.rp-items').forEach(box=>{ const nm=T(box.parentElement.querySelector('.rp-nm')).replace('★','').trim();
   box.querySelectorAll('.dl').forEach(l=>out.panel.push([nm,T(l.querySelector('.dlb')),T(l.querySelector('.dlt'))])); });
 tab='history'; syncTabs(); render();
 const tbs=document.querySelectorAll('#view table');
 const rows=(tr,arr)=>tr&&tr.querySelectorAll('.hitems').forEach(h=>{ const nm=T(h.querySelector('b')); h.querySelectorAll('.dl').forEach(l=>arr.push([nm,T(l.querySelector('.dlb')),T(l.querySelector('.dlt'))])); });
 rows(tbs[0].querySelector('tbody tr'),out.hist); rows(tbs[1].querySelector('tbody tr'),out.month);
 tab='total'; syncTabs(); render();
 const cards=[...document.querySelectorAll('#view .card')];
 const charCard=cards.find(x=>x.innerText.includes('캐릭터별 누적')), itemCard=cards.find(x=>x.innerText.includes('아이템별 누적'));
 out.totChar=[...charCard.querySelectorAll('tbody tr')].flatMap(tr=>[...tr.querySelectorAll('.dlt')].map(l=>[T(tr.querySelector('td b')),T(l)]));
 out.totItem=[...itemCard.querySelectorAll('tbody tr')].map(tr=>T(tr.querySelector('.dlt')));
 tab='boss'; syncTabs(); render(); document.querySelector('[data-filter="weekly"]')?.click(); return out; }"""
def views(pg): return pg.evaluate(JS_VIEWS)
def agg(lines):
    """[(char,boss,'name ×n outs')] → per char+name(with party) totals of count and outcome tallies, for totals comparison"""
    d={}
    for ch,_,t in lines:
        m=re.match(r'(.*?) ×(\d+)(.*)',t); name,n,o=m.group(1),int(m.group(2)),m.group(3)
        e=d.setdefault((ch,name),[0,{}]); e[0]+=n
        for part in [x.strip() for x in o.split('·') if x.strip()]:
            mm=re.match(r'(리4|컨4|꽝|미기록)(?:×(\d+))?',part); e[1][mm.group(1)]=e[1].get(mm.group(1),0)+int(mm.group(2) or 1)
    return d
def agg_tot(lines):
    d={}
    for ch,t in lines:
        m=re.match(r'(.*?) ×(\d+)(.*)',t); o={}
        for part in [x.strip() for x in m.group(3).split('·') if x.strip()]:
            mm=re.match(r'(리4|컨4|꽝|미기록)(?:×(\d+))?',part); o[mm.group(1)]=int(mm.group(2) or 1)
        d[(ch,m.group(1))]=[int(m.group(2)),o]
    return d
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':1000},locale='ko-KR',accept_downloads=True)
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:errs.append('console:'+m.text) if m.type=='error' else None)
    pg.goto(URL); pg.wait_for_timeout(200)
    wk=pg.evaluate('weekId()'); per={'week':wk,'day':pg.evaluate('dayId()'),'month':pg.evaluate('monthId()')}
    B=lambda **kw:{k:{'enabled':True,'diff':v[0],'party':v[1]} for k,v in kw.items()}
    lcm=pg.evaluate("dropsFor(findBoss('lotus'),'hard').filter(k=>!isRing(k))[0]")
    solo=pg.evaluate("(()=>{for(const b of ['dusk','will','lucid','dunkel','jinhilla',...BOSSES.map(x=>x.id)].map(findBoss)){ if(!b||b.type!=='weekly'||['lotus','seren','kalos'].includes(b.id)) continue; for(const d of b.diffs){ const k=dropsFor(b,d).filter(x=>!isRing(x)); if(k.length) return [b.id,d,k[0],b.name]; } } })()")
    print('solo boss:',solo); sb,sd,kal,sname=solo
    # 기존 데이터(이전 버전 형식, dropParty 포함) → 현재 파티 인원을 따르도록 마이그레이션
    c1={'id':'c1','name':'단풍용사','level':287,'job':'히어로','world':'스카니아','isMain':True,'ocid':'','bosses':B(lotus=('hard',3),seren=('hard',3),kalos=('chaos',1),blackmage=('hard',2),**{sb:(sd,1)}),
        'weekly':{'lotus':True,'seren':True,'kalos':True,sb:True},'monthly':{'blackmage':wk},'auto':{},'sync':{},
        'drops':{'seren|r_white':3, f'lotus|{lcm}':1, 'lotus|r_red':1, f'{sb}|{kal}':1,'kalos|r_life':2},'dropOut':{'seren|r_white':['x','r4'],'lotus|r_red':['c4'],'kalos|r_life':['x','r4']},
        'dropParty':{'seren|r_white':[1,2]},'mdrops':{'blackmage|r_white':1},'mdropOut':{'blackmage|r_white':['c4']}}
    c2={'id':'c2','name':'불독메이지','level':262,'job':'아크메이지(불,독)','world':'스카니아','isMain':False,'ocid':'','bosses':B(slime=('chaos',1)),'weekly':{'slime':True},'monthly':{},'auto':{},'sync':{},
        'drops':{'slime|r_black':1},'dropOut':{'slime|r_black':['x']}}
    st={'version':5,'activeId':'c1','characters':[c1,c2],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'weeklyLimit':12,'monthlyLimit':1,'prices':{},'accounts':[],'apiMode':'direct','autoSync':False,'autoEnable':True,'lastSync':0},'period':per}
    pg.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); pg.reload(); pg.wait_for_timeout(400)
    check('migration drops dropParty', pg.evaluate("S.characters[0].dropParty===undefined"))
    # UI 로 추가 획득: 세렌 백옥 1개(꽝), 스우 마크 1개
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|r_white"]'); pg.wait_for_selector('#ringModal.show')
    check('ring modal shows party', '3인 분배' in pg.inner_text('#ringSub'), pg.inner_text('#ringSub'))
    pg.click('#ringModal [data-ring="x"]'); pg.wait_for_timeout(150)
    pg.click(f'.boss:has-text("스우") [data-drop="lotus|{lcm}"]'); pg.wait_for_timeout(150)
    def consistency(tag, expect_party_text):
        v=views(pg)
        bs=sorted(map(tuple,v['boss'])); pn=sorted(map(tuple,v['panel'])); hm=sorted(map(tuple,v['hist']+v['month']))
        check(f'{tag}: boss rows == right panel', bs==pn, (bs,pn) if bs!=pn else len(bs))
        check(f'{tag}: boss rows == 주간 기록+월간', bs==hm, (bs,hm) if bs!=hm else '')
        check(f'{tag}: every line has ×count', all(re.search(r' ×\d+',t) for *_,t in bs))
        tc=agg_tot(v['totChar']); ex=agg(bs)
        check(f'{tag}: 총 수익 per-character == sum of boss rows', tc==ex, (tc,ex) if tc!=ex else '')
        ti={}
        for (ch,name),(n,o) in ex.items():
            e=ti.setdefault(name,[0,{}]); e[0]+=n
            for k,x in o.items(): e[1][k]=e[1].get(k,0)+x
        it=agg_tot([('',t) for t in v['totItem']]); it={k[1]:val for k,val in it.items()}
        check(f'{tag}: 총 수익 per-item == sum', it==ti, (it,ti) if it!=ti else '')
        for txt in expect_party_text: check(f'{tag}: shows "{txt}"', any(txt in t for *_,t in bs) and any(txt in t for *_,t in pn) and any(txt in t for *_,t in hm))
        return v
    v=consistency('A (세렌 3인, 스우 3인, 칼로스 솔로)',['백옥의 보스 반지 상자 (3인 분배) ×4','루즈 컨트롤 머신 마크 (3인 분배) ×2','홍옥의 보스 반지 상자 (3인 분배) ×1','백옥의 보스 반지 상자 (2인 분배) ×1'])
    print('  boss rows:',v['boss'])
    check('A: no stale (2인 분배) on 세렌', not any(b=='선택받은 세렌' and '(2인' in t for _,b,t in v['boss']))
    check('A: solo line has ×count', any(b==sname and re.search(r'^[^()]+ ×1$',t) for _,b,t in v['boss']) and any(b=='감시자 칼로스' and t=='생명의 보스 반지 상자 ×2 리4 · 꽝' for _,b,t in v['boss']), [x for x in v['boss'] if x[1] in (sname,'감시자 칼로스')])
    check('A: 세렌 outcomes', any(b=='선택받은 세렌' and t.endswith('리4 · 꽝×2 · 미기록') for _,b,t in v['boss']), [x for x in v['boss'] if x[1]=='선택받은 세렌'])
    pg.evaluate("$('#toast').classList.remove('show')"); pg.wait_for_timeout(400); pg.screenshot(path=''+OUT+'/party_drops.png')
    # 파티 인원 변경 → 이번 주 기록 표시가 따라감
    pg.select_option('.boss:has-text("선택받은 세렌") select[data-party="seren"]','2'); pg.wait_for_timeout(150)
    v=consistency('B (세렌 → 2인)',['백옥의 보스 반지 상자 (2인 분배) ×4'])
    check('B: no (3인) left on 세렌', not any(b=='선택받은 세렌' and '(3인' in t for _,b,t in v['boss']))
    check('B: totals merge 세렌+검마 백옥 2인', any(t.startswith('백옥의 보스 반지 상자 (2인 분배) ×5') for t in v['totItem']), v['totItem'])
    pg.select_option('.boss:has-text("스우") select[data-party="lotus"]','1'); pg.wait_for_timeout(150)
    v=consistency('C (스우 → 1인)',['루즈 컨트롤 머신 마크 ×2'])
    check('C: 스우 lines solo', all('인 분배' not in t for _,b,t in v['boss'] if b=='스우'))
    pg.select_option('.boss:has-text("스우") select[data-party="lotus"]','3'); pg.select_option('.boss:has-text("선택받은 세렌") select[data-party="seren"]','3'); pg.wait_for_timeout(150)
    # undo
    pg.click('.boss:has-text("선택받은 세렌") [data-drop="seren|r_white"]'); pg.wait_for_timeout(150)
    v=consistency('D (undo latest 세렌 백옥)',['백옥의 보스 반지 상자 (3인 분배) ×3'])
    check('D: undo removed latest 꽝', any(b=='선택받은 세렌' and t.endswith('리4 · 꽝 · 미기록') for _,b,t in v['boss']), [x for x in v['boss'] if x[1]=='선택받은 세렌'])
    # backup
    ex=pg.evaluate('gdPayload().data')
    check('backup has drops (party from bosses)', ex['characters'][0]['drops'].get('seren|r_white')==3 and ex['characters'][0]['bosses']['seren']['party']==3)
    # archive freeze
    pg.evaluate("S.period.week='2026-10-01'; S.period.month='2026-09'; checkResets(); tab='boss'; syncTabs(); render();")
    s=json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
    a=[h for h in s['history'] if h['week']=='2026-10-01'][0]['perChar'][0]
    check('archive keys frozen with party', a['items'].get('seren|r_white#3')==3 and a['items'].get(f'lotus|{lcm}#3')==2 and a['items'].get(f'{sb}|{kal}')==1 and a['items'].get('kalos|r_life')==2, a['items'])
    mh=s['monthHistory'][-1]['perChar'][0]
    check('month archive frozen', mh['items'].get('blackmage|r_white#2')==1, mh['items'])
    before=pg.evaluate("tab='total';syncTabs();render(); [...document.querySelectorAll('#view .card')].find(x=>x.innerText.includes('아이템별 누적')).innerText")
    pg.evaluate("tab='boss';syncTabs();render()")
    pg.select_option('.boss:has-text("선택받은 세렌") select[data-party="seren"]','5'); pg.select_option('.boss:has-text("스우") select[data-party="lotus"]','1'); pg.wait_for_timeout(150)
    after=pg.evaluate("tab='total';syncTabs();render(); [...document.querySelectorAll('#view .card')].find(x=>x.innerText.includes('아이템별 누적')).innerText")
    check('archived totals unchanged after party change', before==after)
    hist=pg.evaluate("tab='history';syncTabs();render(); [...document.querySelectorAll('.hitems')].map(x=>x.innerText.replace(/\\s+/g,' '))")
    check('archived history keeps (3인 분배)', any('백옥의 보스 반지 상자 (3인 분배) ×3' in h for h in hist) and not any('(5인' in h for h in hist), hist)
    # mobile
    m=ctx.new_page(); m.set_viewport_size({'width':375,'height':812}); m.on('pageerror',lambda e:errs.append('m:'+str(e)))
    m.goto(URL); m.evaluate("s=>localStorage.setItem('mapleBossTracker.v1',s)",json.dumps(st)); m.reload(); m.wait_for_timeout(300)
    for t in ['boss','history','total']:
        m.evaluate(f"tab='{t}';syncTabs();render()"); check(f'mobile {t} no overflow', not m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    m.evaluate("tab='boss';syncTabs();render()"); m.screenshot(path=OUT+'/shot11_mobile.png',full_page=True)
    b.close()
print('FAILS:',fails); print('ERRORS:',errs)
