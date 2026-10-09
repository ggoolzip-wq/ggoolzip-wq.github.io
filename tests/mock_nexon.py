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
# 일퀘/길드 (실제 응답 이름 그대로, 2026-10-09 실측): (quest_state, now, max) — 지역 순서 세르니움…기어드락
DQ_NAMES=['[일일 퀘스트] 세르니움 조사','[일일 퀘스트] 호텔 아르크스 주변 청소','[일일 퀘스트] 오디움 일대 탐사','[일일 퀘스트] 도원경 오염 정화',
  '[일일 퀘스트] 아르테리아 잔당 처치','[일일 퀘스트] 카르시온 복구 지원','[일일 퀘스트] 탈라하트 고대신의 힘 조사','[일일 퀘스트] 기어드락 크로노스의 잔재 수집']
OLD_DQ=['[일일 퀘스트] 소멸의 여로 조사','[일일 퀘스트] 츄츄 아일랜드 최고의 요리','[일일 퀘스트] 리멘 조사']
DQ={'ocid-main':(['2','2','2','1','2','1','0','0'],(7,14),(5,5,'2'),(23513,10000,10)),
    'ocid-alt1':(['2','1','0','0','0','0','0','0'],(3,14),(2,5,'1'),(0,0,0)),
    'ocid-b1':(['2','2','0','0','0','0','0','0'],(0,14),(0,5,'1'),(1200,0,4)),
    'ocid-b2':(['1','0','0','0','0','0','0','0'],(0,14),None,None)}
def sched_extra(o):
    if o not in DQ: return [],[]
    qs,mp,xmp,gd=DQ[o]
    daily=[{'content_name':'몬스터파크','type':'contents','registration_flag':'true','now_count':mp[0],'max_count':mp[1],'quest_state':None}]
    daily+=[{'content_name':n,'type':'quest','registration_flag':'false','now_count':0,'max_count':0,'quest_state':'0'} for n in OLD_DQ]
    daily+=[{'content_name':n,'type':'quest','registration_flag':'true','now_count':0,'max_count':100 if q=='1' else 0,'quest_state':q} for n,q in zip(DQ_NAMES,qs)]
    weekly=[{'content_name':'에픽 던전 : 악몽선경','type':'contents','registration_flag':'true','now_count':5,'max_count':0,'quest_state':None}]
    if xmp: weekly.append({'content_name':'[몬스터파크] 익스트림 몬스터파커에 도전해보겠나?','type':'quest','registration_flag':'true','now_count':xmp[0],'max_count':xmp[1],'quest_state':xmp[2]})
    if gd: weekly+=[{'content_name':'[길드] 주간 미션 포인트','type':'contents','registration_flag':'false','now_count':gd[2],'max_count':10,'quest_state':None},
                    {'content_name':'[길드] 지하 수로','type':'contents','registration_flag':'false','now_count':gd[0],'max_count':0,'quest_state':None},
                    {'content_name':'[길드] 플래그 레이스','type':'contents','registration_flag':'false','now_count':gd[1],'max_count':0,'quest_state':None}]
    return daily,weekly
GUILD_EMPTY=set()   # 이 날짜(YYYY-MM-DD)는 랭킹이 아직 비어 있음 → 앱이 어제로 대체하는지 확인
CALLS=[]            # (path, query) 호출 기록
GUILD_ROWS={1:(4000,523),2:(137591,532)}
import datetime as _dt
def _today_kst():  # 스케줄러 응답 날짜 = 오늘(KST) — 고정 날짜면 다음 날부터 앱이 '지난 자료'로 봄
    return (_dt.datetime.now(_dt.timezone.utc)+_dt.timedelta(hours=9)).strftime('%Y-%m-%d')

def handle(route):
    u=urllib.parse.urlparse(route.request.url); q=dict(urllib.parse.parse_qsl(u.query)); p=u.path
    if '/static/maplestory/character/look/' in p:
        col={'main':'#f28c28','alt1':'#7b5cd6','alt2':'#2fa36b','b1':'#d94a7a','b2':'#3a8fd9'}.get(p.rsplit('-',1)[-1],'#4a90d9')
        return route.fulfill(status=200,content_type='image/svg+xml',body=AV.format(c=col))
    CALLS.append((p,q))
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
    if p.endswith('/ranking/guild'):
        if not q.get('date'): return route.fulfill(status=400,json={'error':{'name':'OPENAPI00004','message':'date required'}})
        if q['date'] in GUILD_EMPTY or q.get('guild_name')!='봉사활동': return route.fulfill(json={'ranking':[]})
        pt,rk=GUILD_ROWS[int(q['ranking_type'])]
        return route.fulfill(json={'ranking':[{'date':q['date'],'world_name':'스카니아','guild_name':'봉사활동','guild_level':30,'guild_mark':'','guild_point':pt,'ranking':rk,'guild_master_name':'터래플'}]})
    if p.endswith('/scheduler/character-state'):
        if q['ocid'] not in own or q['ocid'] not in SCHED: return route.fulfill(status=400,json={'error':{'name':'OPENAPI00003','message':'Please input valid id'}})
        c=ALL[q['ocid']]; bs,cl=SCHED[q['ocid']]
        return route.fulfill(json={'date':_today_kst()+'T00:00+09:00','character_name':c[1],'world_name':c[2],'character_level':c[4],'character_class':c[3],'daily_contents':sched_extra(q['ocid'])[0],'weekly_contents':sched_extra(q['ocid'])[1],
          'boss_contents':[{'content_name':n,'difficulty':d,'cycle':'bossMonthly' if n=='검은 마법사' else 'bossWeekly','list_order_no':i,'registration_flag':'true','complete_flag':'true' if f else 'false'} for i,(n,d,f) in enumerate(bs)],
          'weekly_boss_clear_count':cl,'weekly_boss_clear_limit_count':12})
    return route.fulfill(status=400,json={'error':{'name':'OPENAPI00006','message':'invalid path'}})

def st(pg): return json.loads(pg.evaluate("localStorage.getItem('mapleBossTracker.v1')"))
def names(pg): return pg.evaluate("orderedChars().map(c=>c.name)")  # 월드 탭(2026-10-10)으로 사이드바엔 한 월드만 보이므로 전체 순서는 상태에서
def worlds(pg): return pg.eval_on_selector_all('#worldTabs .wtab', "els=>els.map(e=>e.dataset.world)")
