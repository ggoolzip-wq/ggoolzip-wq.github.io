# b229: 홍옥 반지 상자로 리4/컨4 — 보스 드롭 줄 끝 버튼 → 창(리4/컨4 고르기·판매금·저장/취소) → drops 'hong_c4' + 판매금 = '이번주 획득 아이템' 금액·xN 1, 홍옥 상자 수·결정석 그대로, 득템 분석 표들에 홍옥 아이콘+반지 아이콘 xN · 다시 누르면 취소 · 실제 + 예시
import os, sys, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8992'
SHOT=os.environ.get('MBT_SHOTDIR')
fails=[]; errs=[]
REV="""()=>{ const T=totalData(), id=S.characters[0].id, ch=T.chars.find(c=>c.id===id)||{}, bk=(bossKills(T)||[]).find(o=>o.b.id==='lotus')||{}; const num=t=>+String(t||'').replace(/[^0-9]/g,'')||0;
  const a=allRevenue(vchars()), sale=vchars().reduce((t,c)=>t+pItemSale(c),0);
  return {panel:a.total+sale, panelTxt:document.querySelector('.rp-total')?.innerText||'', item:sale, grand:T.grand, wTotal:T.wTotal, ch:(ch.week||0)+(ch.month||0), sales:Object.values(T.sales).reduce((t,o)=>t+o.m,0), bossSale:bk.sale||0,
    wk:(T.weeks.find(w=>w.week===S.period.week)||{}).total||0}; }"""
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
TXT='홍옥 반지 상자로 리4/컨4를 먹었을 경우 클릭'
LINE="""lb=>{const r=[...document.querySelectorAll('.revpanel > .rp-line')].find(x=>x.querySelector('.rplb')?.textContent===lb); return r?{x:r.querySelector('.rpx')?.textContent||'',t:r.innerText.replace(/\\s+/g,' ')}:null}"""
BTN="""()=>[...document.querySelectorAll('[data-rred]')].filter(b=>b.getClientRects().length).map(b=>{const r=b.getBoundingClientRect(), p=b.parentElement.getBoundingClientRect(), last=b===b.parentElement.lastElementChild&&(b.closest('.rredrow')?b.closest('.boss').lastElementChild===b.closest('.rredrow'):true);
  return {id:b.dataset.rred,row:!!b.closest('.rredrow'),t:b.textContent,one:b.getClientRects().length===1&&r.height<34,fit:b.scrollWidth<=b.clientWidth+0.5,inside:r.right<=p.right+0.5&&r.left>=p.left-0.5,last}})"""
def shots(pg,name):
    if SHOT: pg.screenshot(path=os.path.join(SHOT,name))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for w in (1600,390):
        ctx=b.new_context(viewport={'width':w,'height':1000},locale='ko-KR',device_scale_factor=2); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        E=lambda d:{'enabled':True,'diff':d,'party':1}
        ch=[{'id':'c1','name':'원모본캐','level':285,'job':'히어로','world':'스카니아','image':'','bosses':{'lotus':E('hard'),'will':E('hard'),'seren':E('hard'),'jinhilla':E('normal'),'damien':E('normal')},'weekly':{'lotus':True},'monthly':{},'auto':{},'drops':{},'sync':{}}]
        ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':ch,'settings':{'accounts':[]}}
        pg.evaluate("([s])=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",[ST]); pg.reload(); pg.wait_for_timeout(1200)
        B=pg.evaluate(BTN)
        check(f'{w}: 홍옥 상자 보스(스우 하드·윌 하드·진힐라 노말)에만 버튼, 데미안 노말·세렌 없음', sorted(x['id'] for x in B)==['jinhilla','lotus','will'], [x['id'] for x in B])
        check(f'{w}: 글자 그대로·줄 끝·한 줄·안 잘림·칸 안', all(x['t']==TXT and x['last'] and x['one'] and x['fit'] and x['inside'] for x in B), B)
        if SHOT: pg.locator('[data-rred=lotus]:visible').evaluate("e=>e.closest('.boss, .card, tr')?.scrollIntoView({block:'center'})"); pg.wait_for_timeout(200); shots(pg,f'b229_rred_btn_{w}.png')
        before=pg.evaluate(f"({LINE})('이번주 획득 아이템')"); cry=pg.evaluate("allRevenue(vchars()).total")
        pg.locator('[data-rred=lotus]:visible').click(); pg.wait_for_selector('#rredModal')
        m=pg.evaluate("""()=>{const h=document.querySelector('#rrTitle'), n=document.querySelector('.rrnote'), box=document.querySelector('#rredModal .modal').getBoundingClientRect();
          return {h:h.textContent.trim(), icons:h.querySelectorAll('.rrico img, .rrico .ric').length, note:n.textContent, hOne:h.getClientRects().length===1&&h.scrollWidth<=h.clientWidth+0.5&&h.getBoundingClientRect().height<40,
            nOne:n.scrollWidth<=n.clientWidth+0.5&&n.getBoundingClientRect().height<22, btns:[...document.querySelectorAll('#rredModal [data-rr]')].map(b=>b.textContent), picks:[...document.querySelectorAll('#rredModal [data-rrpick]')].map(b=>b.dataset.rrpick+(b.classList.contains('on')?'*':'')), pickAbove:document.querySelector('.rrpicks').getBoundingClientRect().bottom<=document.querySelector('#rrAmt').getBoundingClientRect().top, cx:Math.abs((box.left+box.right)/2-innerWidth/2)<2, gap:Math.round(document.querySelector('.rrpicks').getBoundingClientRect().top-n.getBoundingClientRect().bottom)}}""")
        check(f'{w}: 창 제목·아이콘 2개·작은 안내·두 줄 띄움·저장/취소·가운데', m['h']=='홍옥 반지 상자로 리4/컨4를 먹었을 경우' and m['icons']==2 and m['note']=='(홍옥 반지 상자는 카운팅X, 리4/컨4 판매금은 아이템 메소에 편입됩니다)' and m['btns']==['저장','취소'] and m['picks']==['r4*','c4'] and m['pickAbove'] and m['cx'] and m['gap']>=20, m)
        check(f'{w}: 창 글자 한 줄·안 잘림', m['hOne'] and m['nOne'], m)
        shots(pg,f'b229_rred_modal_{w}.png')
        pg.click('#rredModal [data-rr=ok]'); pg.wait_for_timeout(150)
        check(f'{w}: 빈 칸 저장 = 경고(빨간 테두리)', pg.locator('#rredModal').count()==1 and pg.locator('#rrAmt.inerr').count()==1)
        r0=pg.evaluate(REV)
        pg.click('#rredModal [data-rrpick=c4]'); pg.fill('#rrAmt','15'); pg.click('#rredModal [data-rr=ok]'); pg.wait_for_timeout(200)
        pd=pg.evaluate('!!pend'); pg.evaluate('pendSave()'); pg.wait_for_timeout(300)
        after=pg.evaluate(f"({LINE})('이번주 획득 아이템')"); ring=pg.evaluate(f"({LINE})('반지 상자')")
        st=pg.evaluate("({drops:S.characters[0].drops, rev:S.characters[0].drev, cry:allRevenue(vchars()).total, pend:!!pend})")
        check(f'{w}: 저장 → 이번주 획득 아이템 x0→x1, +1,500,000,000', before and before['x']=='x0' and after['x']=='x1' and '+1,500,000,000' in after['t'], (before,after))
        check(f'{w}: 홍옥 상자 기록 없음·반지 상자 줄 없음·결정석 그대로·저장 대기', st['drops']=={'lotus|hong_c4':1} and not ring and st['cry']==cry and st['rev']=={'lotus|hong_c4':{'m':1500000000,'a':15,'p':1,'i':'hong_c4'}} and pd, (st,ring,pd))
        r1=pg.evaluate(REV); D={k:r1[k]-r0[k] for k in r0 if k!='panelTxt'}
        check(f'{w}: 판매금 15억이 모든 수익 합계에 들어감(이번주 획득 아이템·이번 주 수익 총합·누적/주간 총합·캐릭터 누적·판매 누적·보스 메소왕 아이템 판매값)', all(D[k]==1500000000 for k in D), (D,r0['panelTxt'],r1['panelTxt']))
        check(f'{w}: 이번 주 수익 총합 표시 숫자도 바뀜', r0['panelTxt']!=r1['panelTxt'], (r0['panelTxt'],r1['panelTxt']))
        check(f'{w}: 버튼 = 기록됨 표시(글자 그대로)', pg.evaluate("[...document.querySelectorAll('[data-rred=lotus]')].filter(b=>b.getClientRects().length).map(b=>b.classList.contains('got')&&b.textContent)")==[TXT])
        if w==1600:
            sm=pg.evaluate("weekSummary(S.period.week).perChar[0].revs"); check('주간 기록(revs)에 판매금 남음', sm.get('lotus|hong_c4',{}).get('m')==1500000000, sm)
            pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
            H=pg.evaluate("""()=>{const q=s=>document.querySelector(s); const ic=s=>[...document.querySelectorAll(s+' .hongico')].filter(e=>e.getClientRects().length).filter(e=>e.closest('.sl,.loot,.blkchip,.tl,.ringsum')).map(e=>e.closest('.sl,.loot,.blkchip,.tl,.ringsum').innerText.replace(/\\s+/g,' ').trim()); 
              return {sales:ic('#salesCard'), salesTxt:q('#salesCard').textContent, king:ic('#lootKing'), bking:ic('#bossLootKing'), bloot:ic('.bossloot'), week:ic('#weekLoot .wlpage.on'), ring:q('.hongsum')?.innerText.replace(/\\s+/g,' ').trim()||'', ringHasX:/꽝/.test(q('.hongsum')?.innerText||''),
                exp:q('.ringexp')?.innerText||'', tot:q('.itemtot')?.innerText||''}}""")
            check('판매 누적 수익: 홍옥 아이콘+컨4 아이콘 x1 (일반 반지 줄과 따로)', len(H['sales'])==1 and 'x1' in H['sales'][0] and '컨티뉴어스 링 4레벨 (홍옥 반지 상자)' in H['salesTxt'], H['sales'])
            check('득템왕·보스 득템왕·보스 별 누적·주별 득템: 홍옥 아이콘 + x1', all(len(H[k])==1 and H[k][0].endswith('x1') for k in ('king','bking','bloot','week')), {k:H[k] for k in ('king','bking','bloot','week')})
            for tb in ('loot','boss','total'):
                pg.evaluate(f"tab='{tb}'; render()"); pg.wait_for_timeout(300)
                lk=pg.evaluate("[...document.querySelectorAll('body *')].filter(e=>e.getClientRects().length&&!e.closest('.vh,.modal-bg')&&[...e.childNodes].some(n=>n.nodeType===3&&/\\(홍옥 반지 상자\\)|홍옥 [리컨]4/.test(n.textContent))).map(e=>e.className)")
                check(f'{tb} 탭: 홍옥 리4/컨4 이름 글자 안 보임(아이콘 + xN)', lk==[], lk)
            pg.evaluate("tab='loot'; render()"); pg.wait_for_timeout(300)
            check('시드링 획득 타율: 홍옥 줄(라벨·컨4 x1·꽝 없음·기댓값 없음)', H['ring'].startswith('홍옥 반지 상자로 얻은 리4/컨4') and '컨4 x1' in H['ring'] and not H['ringHasX'] and '기댓값' not in H['ring'], H['ring'])
            if SHOT: pg.locator('.ringcard').screenshot(path=os.path.join(SHOT,'b229_hong_ringcard_real.png'))
            pg.evaluate("tab='boss'; render()"); pg.wait_for_timeout(300)
        pg.locator('[data-rred=lotus]:visible').click(); pg.wait_for_timeout(200); pg.evaluate('pendSave()'); pg.wait_for_timeout(300)
        a2=pg.evaluate(f"({LINE})('이번주 획득 아이템')")
        check(f'{w}: 다시 누르면 취소 → x0, 기록 없음', a2['x']=='x0' and pg.evaluate("!S.characters[0].drev"), a2)
        pg.locator('[data-rred=will]:visible').click(); pg.wait_for_selector('#rredModal'); pg.click('#rredModal [data-rr=cancel]'); pg.wait_for_timeout(200)
        check(f'{w}: 창 취소 = 기록 없음·저장 대기 없음', pg.locator('#rredModal').count()==0 and pg.evaluate("!S.characters[0].drev && !pend"))
        ctx.close()
        ctx=b.new_context(viewport={'width':w,'height':1000},locale='ko-KR',device_scale_factor=2); pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**',lambda r:r.abort()); pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        B=pg.evaluate(BTN)
        check(f'예시 {w}: 버튼 보임·한 줄·안 잘림', len(B)>=1 and all(x['t']==TXT and x['one'] and x['fit'] and x['inside'] for x in B), B)
        if SHOT: pg.locator('[data-rred]:visible').first.evaluate("e=>e.scrollIntoView({block:'center'})"); pg.wait_for_timeout(200); shots(pg,f'b229_rred_demo_{w}.png')
        ctx.close()
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); fails.append('exception')
finally:
    srv.kill()
print('FAILS:',fails,'ERRORS:',errs); sys.exit(1 if fails or errs else 0)
