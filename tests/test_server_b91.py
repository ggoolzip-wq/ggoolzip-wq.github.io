# b91: /api/admin/users — 본계정 regAt, 부계정 목록(alts: label·대표 캐릭터·regAt), acct_role.created_at 유지 (wrangler dev 로컬 D1)
import os, sys, json, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
NP, WP = 8891, 8890
def req(m,path,body=None,tok=None):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(f'http://127.0.0.1:{WP}{path}',data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=15) as res: return res.status, json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')
# b104: 가짜 maple.ai.kr 페이지 (Next.js 페이지 안의 escaped JSON 일별 기록 두 개)
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
MAI_HITS=[]; MAI_INM=[]
MAI_HTML=('<html><script>self.__next_f.push([1,"x:{\\"data\\":[{\\"date\\":\\"2026-10-11\\",\\"items\\":{\\"마깃안\\":{\\"challenger\\":40,\\"main\\":28}}},'
          '{\\"date\\":\\"2026-10-12\\",\\"items\\":{\\"마깃안\\":{\\"challenger\\":41,\\"main\\":29.28},\\"에스텔라\\":{\\"challenger\\":4.4},\\"리4\\":{\\"main\\":39}}}]}"])</script></html>')
class MH(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        MAI_HITS.append(self.headers.get('User-Agent','')); MAI_INM.append(self.headers.get('If-None-Match',''))
        if self.headers.get('If-None-Match')=='"e1"': self.send_response(304); self.end_headers(); return
        b=MAI_HTML.encode(); self.send_response(200); self.send_header('ETag','"e1"'); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
MS=ThreadingHTTPServer(('127.0.0.1',8892),MH); threading.Thread(target=MS.serve_forever,daemon=True).start()
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP,extra={'MAI_URL':'http://127.0.0.1:8892/blog/item-price-tracker-2026'})
try:
    KA,KF,KB='live_KEY_A_0123456789abcdef','live_KEY_F_0123456789abcdef','live_KEY_B_0123456789abcdef'
    s,a=req('POST','/api/login',{'key':KA}); TA=a['token']; UA=dev.sql('SELECT id FROM users')[0]['id']
    dev.sql(f"INSERT INTO meta (k,v) VALUES ('admin_user','{UA}')")
    s,b=req('POST','/api/login',{'key':KB}); TB=b['token']
    s,r=req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KF,'label':'부계정F'}]},tok=TA); AH=r['subs'][0]['ah']; check('subkeys stored', s==200 and AH, r)
    ch=lambda i,n,acc,lv: {'id':i,'name':n,'level':lv,'world':'스카니아','accId':acc,'isMain':i=='c1'}
    st={'version':5,'characters':[ch('c1','본캐A','a1',285),ch('c2','부캐F','a2',270)],'settings':{'accounts':[{'id':'a1','label':'본계정','main':True,'ah':a['accounts'][0]},{'id':'a2','label':'부계정F','ah':AH},{'id':'a3','label':'키없음'}]}}
    s,_=req('PUT','/api/state',{'baseRev':0,'updatedAt':1,'data':st},tok=TA); check('state saved', s==200, s)
    s,u=req('GET','/api/admin/users',tok=TA); U={x['id']:x for x in u['users']}; A=U[UA]
    check('main regAt set', A['regAt']>0, A)
    check('alts = 부계정F only (rep char 부캐F, regAt); b102: 키 없는 칸 키없음 은 안 보임', [x['label'] for x in A['alts']]==['부계정F'] and A['alts'][0]['name']=='부캐F' and A['alts'][0]['regAt']>0, A['alts'])
    s,u2=req('GET','/api/admin/users?prices=1',tok=TA); check('b102: ?prices=1 → users + prices in one response', s==200 and 'prices' in u2 and len(u2['users'])==len(u['users']), list(u2))
    check('no key/hash leaked', KF not in json.dumps(u) and AH not in json.dumps(u))
    check('user B no alts', all(x['alts']==[] for x in u['users'] if x['id']!=UA), u['users'])
    t0=A['alts'][0]['regAt']; time.sleep(1.2)
    req('PUT','/api/subkeys',{'main':KA,'subs':[{'key':KF,'label':'부계정F'}]},tok=TA)
    s,u=req('GET','/api/admin/users',tok=TA); A=[x for x in u['users'] if x['id']==UA][0]
    check('re-saving subkeys keeps original regAt', A['alts'][0]['regAt']==t0, (t0,A['alts']))
    # b93: /api/admin/prices (관리자만)
    s,r=req('GET','/api/admin/prices',tok=TB); check('b93: non-admin prices → 403', s==403, (s,r))
    s,r=req('PUT','/api/admin/prices',{'prices':{'eye':{'p':2928000000,'t':1000},'BAD KEY':{'p':1,'t':1},'x':{'p':-5,'t':1}}},tok=TA); check('b93: admin PUT keeps valid only', s==200 and r['prices']=={'eye':{'p':2928000000,'t':1000}}, r)
    req('PUT','/api/admin/prices',{'prices':{'eye':{'p':1,'t':500},'belt':{'p':3900000000,'t':2000}}},tok=TA)
    s,r=req('GET','/api/admin/prices',tok=TA); check('b93: older time ignored, merge', r['prices']=={'eye':{'p':2928000000,'t':1000},'belt':{'p':3900000000,'t':2000}}, r)
    s,_=req('POST','/api/unlink',{'ah':AH},tok=TA); s,u3=req('GET','/api/admin/users',tok=TA); A3=[x for x in u3['users'] if x['id']==UA][0]
    check('b102: after /api/unlink of the alt → admin shows 0 alts (even though state still has the slot)', A3['alts']==[], A3['alts'])
    s,r=req('GET','/api/admin/maple-prices',tok=TB); check('b104: non-admin maple-prices → 403', s==403, (s,r))
    s,r=req('GET','/api/admin/maple-prices',tok=TA); check('b104: latest date only, 본섭(main) only', s==200 and r['date']=='2026-10-12' and r['items']=={'마깃안':{'main':29.28},'리4':{'main':39}} and r['fetchedAt']>0, r)
    check('b207: one outside request with descriptive UA', len(MAI_HITS)==1 and 'bossmaple' in MAI_HITS[0], MAI_HITS)
    s,r2=req('GET','/api/admin/maple-prices',tok=TA); check('b207: again → conditional GET(If-None-Match) → 304 → cached same data (no same-day lock)', s==200 and r2.get('cached') and len(MAI_HITS)==2 and MAI_INM[1]=='"e1"' and r2['date']=='2026-10-12' and r2['fetchedAt']==r['fetchedAt'], (MAI_INM,r2))
    s,r3=req('GET','/api/prices'); check('b207: server wrote admin_prices from maple.ai.kr (eye=29.28억, ring_r4=39억, t=first seen)', r3['prices'].get('eye')=={'p':2928000000,'t':r['fetchedAt']} and r3['prices'].get('ring_r4',{}).get('p')==3900000000 and r3['prices'].get('belt')=={'p':3900000000,'t':2000}, r3)
finally:
    dev.stop(); ms.shutdown()
print('FAILS:',fails); sys.exit(1 if fails else 0)
