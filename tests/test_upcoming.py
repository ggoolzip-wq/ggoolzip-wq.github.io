# 테섭 예정 결정석 가격: 테섭 새 글 본문 → prices.json upcoming, 본섭 가격이 같아지면 삭제
import os, sys, json, tempfile, copy
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'scripts'))
import update_feed, upcoming, nexon_prices
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
html=open(os.path.join(ROOT,'tests','fixtures','update_813.html'),encoding='utf-8').read()  # 테섭 공지도 같은 본문 형식 (가격표 있는 실제 공지)
info=nexon_prices.parse_post(html)
check('parser finds crystal table in post body', len(info['rows'])>=20, len(info['rows']))
live=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8'))
tmp=tempfile.mkdtemp(); P=os.path.join(tmp,'prices.json')
# 1) 실서버와 같은 표 → 예정 없음
json.dump(live,open(P,'w'),ensure_ascii=False); update_feed.PRICES=P
ch=update_feed.test_prices([{'id':'test:900','title':'테섭 공지','url':'https://x/Testworld/News/Update/900','date':'2026-10-10T00:00:00+09:00'}],fetch=lambda u: html)
check('same as live → no upcoming', not ch and 'upcoming' not in json.load(open(P)))
# 2) 10% 내린 표 → 예정 가격, 실서버 rows 그대로
low=html
for r in info['rows']:
    low=low.replace(f"{r['new']:,}",f"{int(r['new']*0.9):,}")
ch=update_feed.test_prices([{'id':'test:901','title':'테섭 공지2','url':'https://x/Testworld/News/Update/901','date':'2026-10-11T00:00:00+09:00'}],fetch=lambda u: low)
pj=json.load(open(P))
check('lower prices → upcoming stored, live rows untouched', ch and len(pj['upcoming']['rows'])>=20 and pj['rows']==live['rows'] and pj['upcoming']['source']['url'].endswith('/901'), (ch,len(pj.get('upcoming',{}).get('rows',[]))))
# 3) 새 글이 없으면 아무것도 안 함
check('no new test posts → no fetch', update_feed.test_prices([],fetch=lambda u: 1/0)==False)
# 4) 본섭이 일부 적용 → 그 줄만 삭제, 모두 적용 → upcoming 삭제
pj2=copy.deepcopy(pj); up={upcoming.bkey(r['boss']):r['new'] for r in pj2['upcoming']['rows']}
first=pj2['rows'][0]; first['new']=up[upcoming.bkey(first['boss'])]
check('main patch applies one → that row cleared', upcoming.reconcile(pj2) and len(pj2['upcoming']['rows'])==len(pj['upcoming']['rows'])-1)
for r in pj2['rows']:
    k=upcoming.bkey(r['boss'])
    if k in up: r['new']=up[k]
check('main patch applies all → upcoming removed', upcoming.reconcile(pj2) and 'upcoming' not in pj2)
# 5) update_prices.write 가 기존 upcoming 을 유지하고 정리
import update_prices
update_prices.OUT=P; update_prices._OLD_UP=pj['upcoming']
new=copy.deepcopy(live); update_prices.write(new); w=json.load(open(P))
check('update_prices keeps upcoming when prices unchanged', 'upcoming' in w and len(w['upcoming']['rows'])==len(pj['upcoming']['rows']))
# 6) 테섭 새 글에 결정석 변경 없음 → 가격 그대로, '마지막 확인'만 오늘로
json.dump(dict(live,checkedAt='2026-01-01'),open(P,'w'),ensure_ascii=False)
ch=update_feed.test_prices([{'id':'test:902','title':'테섭 일반','url':'https://x/Testworld/News/Update/902','date':''}],fetch=lambda u: '<html><title>x</title><body>버그 수정</body></html>')
w=json.load(open(P)); check('no crystal change → only checkedAt updated', ch and w['checkedAt']==update_feed.today_kst() and w['rows']==live['rows'] and 'upcoming' not in w)
# 7) 본섭 패치: 예정 없으면 본문 안 받음 / 예정 있으면 그 공지 가격으로 실서버 갱신 + 예정 삭제
new_patch=[{'id':'update:999','title':'본섭 업데이트','url':'https://maplestory.nexon.com/News/Update/999','date':'2026-10-16T10:00:00+09:00'}]
check('patch without pending upcoming → no fetch', update_feed.patch_prices(new_patch,fetch=lambda u: 1/0)==False)
json.dump(pj,open(P,'w'),ensure_ascii=False)
check('patch with no table → unchanged', update_feed.patch_prices(new_patch,fetch=lambda u:'<html><body>점검</body></html>')==False and 'upcoming' in json.load(open(P)))
ch=update_feed.patch_prices(new_patch,fetch=lambda u: low); w=json.load(open(P))
lowmap={upcoming.bkey(r['boss']):r['new'] for r in pj['upcoming']['rows']}
check('patch applies → live = 테섭 prices, upcoming cleared, source=patch', ch and 'upcoming' not in w and w['source']['url'].endswith('/999') and all(lowmap.get(upcoming.bkey(r['boss']),r['new'])==r['new'] for r in w['rows']))
print('FAILS:',fails); sys.exit(1 if fails else 0)
