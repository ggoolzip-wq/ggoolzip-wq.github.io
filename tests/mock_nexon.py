import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import json, urllib.parse
import sys
SHOT=None
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
def names(pg): return pg.eval_on_selector_all('#charList .char .nm', "els=>els.map(e=>e.childNodes[0].textContent.trim())")
def worlds(pg): return pg.eval_on_selector_all('#charList .world-h', "els=>els.map(e=>e.dataset.world)")
