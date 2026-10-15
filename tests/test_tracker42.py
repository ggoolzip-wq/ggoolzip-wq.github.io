# b53: 반짝이 가루, 아이템 순위(1.5/2), 녹옥 비활성, 못 가진 아이템 다중 보스, 1~3위 글자색, (난이도) 굵게·전 화면 표기, 시드링 글자, 블빵 구분선 1개, 누적 라인 차트
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8842/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8842','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
ch={'id':'c0','name':'캐릭00','level':280,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'',
    'bosses':{'kaling':{'enabled':True,'diff':'hard','party':1},'limbo':{'enabled':True,'diff':'normal','party':1}},'weekly':{},'monthly':{},'auto':{},'sync':{},
    'drops':{'kaling|g_faith':1,'limbo|se3':1},'dropOut':{}}
per=[{'id':'c0','name':'캐릭00','meso':100000000,'count':2,'bosses':['카링(하드)','림보(노말)'],'bvals':[1,1],
      'items':{'kaling|g_faith':1,'kaling|se1':1,'kaling|se1#2':1,'limbo|whisper':1,'kaling|g_life':1,'kaling|r_black':1,'kaling|chaosbox':1,'blackmage|h_belt':1,'kaling|h_ear':1},
      'outcomes':{'kaling|r_black':['r4'],'kaling|chaosbox':['cb:cfe']}}]
hist=[{'week':'2026-10-01','weeklyOnly':True,'total':100000000,'cleared':2,'perChar':per},{'week':'2026-10-08','weeklyOnly':True,'total':200000000,'cleared':2,'perChar':[]}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':[ch],'history':hist,'monthHistory':[],'worldOrder':[],'startWeek':'2026-10-01','settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.tab','total')}",ST); pg.reload(); pg.wait_for_timeout(900); pg.evaluate("(()=>{const v=document.querySelector('#view');const o=render;window.render=function(){renderLoot();const l=v.innerHTML;o.apply(this,arguments);v.insertAdjacentHTML('beforeend',l)};render()})()")
    pri=pg.evaluate("Object.fromEntries(['whisper','h_face','h_ear','genesis','lcm','cfe','eye','chaosbox','g_faith','g_life'].map(k=>[k,itemPri(k)]))")
    check('순위: 광휘 1 · 해머·창세 1.5 · 루컨마·커포 = 다른 칠흑과 같은 2', pri['whisper']==1 and pri['h_face']==1.5 and pri['h_ear']==1.5 and pri['genesis']==1.5 and pri['lcm']==2 and pri['cfe']==2 and pri['eye']==2 and pri['chaosbox']==2 and pri['g_faith']==3.05 and pri['g_life']==3.1, pri)
    j=pg.evaluate("[dropsFor(findBoss('lotus'),'normal').includes('r_green'), dropsOff(findBoss('lotus'),'normal').includes('r_green'), missingItems(totalData()).some(o=>o.k==='r_green'), dropsFor(findBoss('lotus'),'normal').includes('r_red')]")
    check('녹옥 반지 상자: 회색 칩(비활성) + 못 가진 목록에서 제외', j[0]==False and j[1]==True and j[2]==False, j)
    # 못 가진 아이템: 같은 아이템 모든 보스
    ml=pg.evaluate("(()=>{const o=missingItems(totalData()).find(x=>x.k==='se4'); return o?o.list.map(x=>x.b.id+'|'+x.d):[]})()")
    check('못 가진 아이템: 4단계 소울 에테르 = 유피테르 노말·하드 모두', ml==['jupiter|normal','jupiter|hard'], ml)
    g=pg.evaluate("(()=>{const o=missingItems(totalData()).find(x=>x.k==='se2'); return o?o.list.map(x=>x.b.id+'|'+x.d):[]})()")
    check('못 가진 아이템: 2단계 에테르 = 여러 보스(별·벨로나)', len(g)==4 and {x.split('|')[0] for x in g}=={'star','bellona'}, g)
    rows=pg.evaluate("[...document.querySelectorAll('#missItems tbody tr:not(.rkpad)')].map(r=>({h:r.getBoundingClientRect().height,n:r.querySelectorAll('.missbn').length,t:r.innerText.replace(/\\s+/g,' ')}))")
    check('못 가진 목록 행 = 한 줄(48px), 여러 보스 줄 존재', rows and all(r['h']<=49 for r in rows) and any(r['t'].count('(')>=2 for r in rows), rows[:4])
    # 글자색 (1~3위만)
    col=pg.evaluate("""(()=>{const out={};document.querySelectorAll('#epicCard tbody tr[class*=rk]').forEach(t=>{const s=t.querySelector('.rkname > span:last-child');if(s) out[t.querySelector('.rkno').innerText.trim()+':'+s.innerText]=[s.className,getComputedStyle(s).color];});return out})()""")
    print(col)
    check('1~3위 아이템에만 색 클래스', all((('ic-' in v[0]) or not ('md-' in v[0])) for v in col.values()) and any('ic-pink' in v[0] for v in col.values()) or any('ic-sky' in v[0] for v in col.values()) or any('ic-purple' in v[0] for v in col.values()), col)
    cc=pg.evaluate("[itemCol('whisper'),itemCol('h_ear'),itemCol('eye'),itemCol('chaosbox'),itemCol('genesis'),itemCol('g_faith'),itemCol('se2'),itemCol('r_red'),itemCol('cb:cfe')]")
    check('색 매핑: 광휘·해머 핑크, 칠흑·상자 보라, 연마석·에테르 하늘', cc==['ic-pink','ic-pink','ic-purple','ic-purple','ic-purple','ic-sky','ic-sky','','ic-purple'], cc)
    cs=pg.evaluate("(()=>{const e=document.querySelector('#epicCard tr.rk1 .ic-pink,#epicCard tr.rk1 .ic-purple,#epicCard tr.rk1 .ic-sky');return e?getComputedStyle(e).color:''})()")
    check('1위 아이템 글자색 적용', cs in ('rgb(255, 79, 163)','rgb(179, 107, 255)','rgb(95, 208, 255)'), cs)
    # b54: 별 반짝이(currentColor, 약함), 극익스트림 주홍, 득템왕 색, 에픽빔 스포트라이트
    st=pg.evaluate("(()=>{const e=document.querySelector('#epicCard tr.rk1 .spk');const a=getComputedStyle(e,'::before');return [a.backgroundColor===getComputedStyle(e).color,a.maskImage!=='none'||a.webkitMaskImage!=='none',a.animationName]})()")
    check('반짝이: 글자색과 같은 색 작은 별 마스크', st[0] and st[1] and st[2]=='spkd1', st)
    ex=pg.evaluate("(()=>{const e=document.createElement('span');e.className='dlv dlv-extreme';document.body.appendChild(e);return getComputedStyle(e).color})()")
    check('익스트림 = 주홍 #ff4500', ex=='rgb(255, 69, 0)', ex)
    lk=pg.evaluate("[...document.querySelectorAll('#lootKing tr.rk1 .ln')].map(e=>e.className+'|'+getComputedStyle(e).color)")
    check('득템왕 1위 아이템 이름: 규칙대로 색+반짝이', any('ic-sky' in x for x in lk) and all('spk' in x for x in lk if 'ic-' in x), lk)
    eg=pg.evaluate("(()=>{const e=document.querySelector('.epgold');if(!e) return null;const c=getComputedStyle(e);return [c.animationName,c.backgroundImage.split('gradient').length-1]})()")
    check('에픽빔 숫자 스포트라이트(2겹 배경 애니메이션)', eg and eg[0]=='epgs' and eg[1]>=2, eg)
    # b55: 스포트라이트
    sl=pg.evaluate("""(()=>{const g=(sel)=>{const e=document.querySelector(sel);if(!e)return null;const c=getComputedStyle(e);return [c.animationName,c.animationDuration,c.getPropertyValue('--spa2').trim(),c.webkitTextFillColor,c.color,c.backgroundClip||c.webkitBackgroundClip]};
      const ex=document.createElement('span');ex.className='dlv dlv-extreme';ex.textContent='(익스트림)';document.body.appendChild(ex);const c=getComputedStyle(ex);
      return {r1:g('#epicCard tr.rk1 .spk'),r2:g('#epicCard tr.rk2 .spk'),r3:g('#epicCard tr.rk3 .spk'),ex:[c.animationName,c.animationDuration,c.getPropertyValue('--spa2').trim(),c.color]}})()""")
    check('스포트라이트: 1위 2.2s 강(.9) / 2위 3.2s .7 / 3위 3.2s .5 / 익스트림 spx 2.8s 주홍 유지', sl['r1'][:3]==['spl','2.2s','.9'] and sl['r2'][:3]==['spl','3.2s','.7'] and sl['r3'][:3]==['spl','3.2s','.5'] and sl['ex'][:2]==['spx','2.8s'] and sl['ex'][3]=='rgb(255, 69, 0)' and sl['r1'][3]=='rgba(0, 0, 0, 0)', sl)
    # b56: 행 전체 스포트라이트, 익스트림 굵게·검은 빛
    rw=pg.evaluate("""(()=>{const out={};for(const sel of ['#mesoKing','#lootKing','#bossKing','#epicCard','#chaosCard']){const tr=document.querySelector(sel+' tr.rk1');if(!tr){out[sel]='none';continue}
      const leaves=[...tr.querySelectorAll('td,span,b')].filter(e=>!e.children.length&&e.innerText.trim()&&!e.classList.contains('crown'));out[sel]=[leaves.length,leaves.filter(e=>getComputedStyle(e).animationName==='spl').length]}return out})()""")
    check('1위 행 모든 글자 스포트라이트', all(v=='none' or v[0]==v[1] for v in rw.values()) and rw['#epicCard'][0]>=3, rw)
    xe=pg.evaluate("(()=>{const e=document.createElement('span');e.className='dlv dlv-extreme';e.textContent='(익스트림)';document.body.appendChild(e);const c=getComputedStyle(e);return [c.fontWeight,c.color,c.backgroundImage.includes('rgba(0, 0, 0'),c.animationName]})()")
    check('익스트림: 900 굵기, 주홍, 검은 빛', xe[0]=='900' and xe[1]=='rgb(255, 69, 0)' and xe[2] and xe[3]=='spx', xe)
    # 난이도 굵게
    bw=pg.evaluate("[...document.querySelectorAll('.dlv')].map(e=>getComputedStyle(e).fontWeight)")
    check('(난이도) 전부 굵게', bw and all(int(x)>=700 for x in bw), bw[:5])
    # 라인 차트
    lc=pg.evaluate("(()=>{const c=document.querySelector('.linechart');return c?[c.querySelectorAll('polyline').length,c.querySelectorAll('rect:not(.lpt rect)').length,c.querySelectorAll('circle').length]:null})()")
    check('주별 누적 = 라인 차트(막대 없음, 점 3개(이번 주 포함))', lc==[1,0,3], lc)
    # 시드링
    rs=pg.evaluate("(()=>{const s=document.querySelector('.ringsum'),l=s.querySelector('.rslab'),x=s.querySelector('.ringexp');return [getComputedStyle(s).fontSize,getComputedStyle(l).color,getComputedStyle(l).fontWeight,getComputedStyle(x).fontSize,getComputedStyle(x).color==getComputedStyle(s).color,s.scrollWidth<=s.clientWidth+1,s.getBoundingClientRect().height]})()")
    check('시드링: 글자 크고 굵게, 라벨 초록, 기댓값 작고 무색, 한 줄', float(rs[0][:-2])>=16 and rs[1]=='rgb(63, 208, 122)' and int(rs[2])>=700 and float(rs[3][:-2])<12 and rs[4] and rs[5] and rs[6]<60, rs)
    # 블빵 구분선
    pg.evaluate("s=>{const x=JSON.parse(JSON.stringify(s));x.history[0].perChar[0].items['kaling|g_faith#2w']=1;localStorage.setItem('mapleBossTracker.v1',JSON.stringify(x))}",ST); pg.reload(); pg.wait_for_timeout(700); pg.evaluate("(()=>{const v=document.querySelector('#view');const o=render;window.render=function(){renderLoot();const l=v.innerHTML;o.apply(this,arguments);v.insertAdjacentHTML('beforeend',l)};render()})()")
    bb=pg.evaluate("""(()=>{const t=document.querySelector('#bbRate tr:last-child td'),w=document.querySelector('#bbWon');const cs=getComputedStyle(w);return [t?getComputedStyle(t).borderBottomWidth:'-',cs.borderTopWidth,cs.paddingTop,cs.marginTop]})()""")
    check('블빵: 승률 표 마지막 줄선 없음 + 구분선 1개, 위아래 여백', bb[0] in ('0px','-') and bb[1]=='1px' and float(bb[2][:-2])>=14 and float(bb[3][:-2])>=14, bb)
    # 이번 주 수익 / 가격 카드 / 보스 별 누적
    pg.evaluate("s=>{localStorage.setItem('mapleBossTracker.tab','boss')}"); pg.reload(); pg.wait_for_timeout(900)
    rp=pg.evaluate("[...document.querySelectorAll('.revpanel .dlb')].map(e=>e.innerText.trim())")
    check('이번 주 수익: 보스 + (난이도)', '카링 (하드)' in rp and '림보 (노말)' in rp, rp)
    pr=pg.evaluate("[document.querySelectorAll('.pricecard .pc-nm .dlv').length,[...document.querySelectorAll('.pricecard .pc-row:not(.has-up)')].every(r=>r.getBoundingClientRect().height<30),[...document.querySelectorAll('.pricecard .pc-nm')].every(n=>n.scrollWidth<=n.clientWidth+1)]")
    hu=pg.evaluate("[...document.querySelectorAll('.pricecard .pc-row.has-up')].every(r=>r.getBoundingClientRect().height<46&&r.querySelector('.pc-up').scrollWidth<=r.querySelector('.pc-up').clientWidth+1)")
    check('결정석 가격: 색 (난이도), 한 줄, 잘림 없음 (테섭 예정 행은 2줄 허용)', pr[0]>10 and pr[1] and pr[2] and hu, [pr,hu])
    pg.set_viewport_size({'width':1280,'height':800}); pg.wait_for_timeout(500)
    pr=pg.evaluate("[[...document.querySelectorAll('.pricecard .pc-row:not(.has-up)')].every(r=>r.getBoundingClientRect().height<30),[...document.querySelectorAll('.pricecard .pc-nm')].every(n=>n.scrollWidth<=n.clientWidth+1)]")
    check('1280px 결정석 가격 한 줄·잘림 없음', all(pr), pr)
    # b127: 보스 드랍 테이블은 스케줄러 난이도 그림 (글자는 .sr)
    bp=pg.evaluate("(e=>e&&[e.querySelector('.sr').innerText,!!e.querySelector('img')])(document.querySelector('.boss-list .bn .dimg'))")
    check('보스 드랍 테이블: 난이도 그림 + 숨은 글자', bp and bp[0] in ('하드','노말') and bp[1], bp)
    # 녹옥 칩 (스우 노말)
    pg.evaluate("s=>{const x=JSON.parse(localStorage.getItem('mapleBossTracker.v1'));x.characters[0].bosses.lotus={enabled:true,diff:'normal',party:1};x.activeId='c0';localStorage.setItem('mapleBossTracker.v1',JSON.stringify(x))}"); pg.reload(); pg.wait_for_timeout(700)
    jc=pg.evaluate("(()=>{const l=[...document.querySelectorAll('.drop.off')].filter(e=>/녹옥/.test(e.innerText||e.title));return [l.length,l[0]&&l[0].getAttribute('aria-disabled'),document.querySelectorAll('.drop[data-drop*=r_green]').length]})()")
    check('녹옥 반지 상자 칩: 회색 비활성', jc[0]>=1 and jc[1]=='true' and jc[2]==0, jc)
    check('JS 오류 없음', not errs, errs)
finally:
    srv.terminate()
print('FAILS:',fails,'ERRORS:',errs)
sys.exit(1 if fails else 0)
