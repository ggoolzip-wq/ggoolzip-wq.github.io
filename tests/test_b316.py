# b316(t571) 상단 탭 네온 박스 + b317(t572) 자동 기록 안내창 크게
import os
from playwright.sync_api import sync_playwright
URL='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','index.html'))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME','/usr/bin/google-chrome'),args=['--no-sandbox'])
  for w,h in [(1600,900),(390,800),(1600,520)]:
    pg=b.new_page(viewport={'width':w,'height':h}); pg.goto(URL); pg.wait_for_timeout(800)
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.wait_for_timeout(100)
      t=pg.evaluate("""(()=>{const n=document.querySelector('#tabs'),bs=[...n.querySelectorAll('button')],c=e=>getComputedStyle(e);
        const on=bs.find(x=>x.classList.contains('on')),off=bs.find(x=>!x.classList.contains('on'));
        return {over:n.scrollWidth>n.clientWidth+1||document.documentElement.scrollWidth>innerWidth,rad:bs.map(x=>parseFloat(c(x).borderTopLeftRadius)),bw:bs.map(x=>parseFloat(c(x).borderTopWidth)),
        sep:n.querySelectorAll('.tabsep').length,sepv:[...n.querySelectorAll('.tabsep')].every(s=>s.getBoundingClientRect().width>0),onS:c(on).boxShadow.length,offS:c(off).boxShadow,onS2:c(on).boxShadow,
        noOverlap:bs.every((a,i)=>bs.every((q,j)=>i>=j||(r=>(s=>r.right<=s.left+.5||s.right<=r.left+.5||r.bottom<=s.top+.5||s.bottom<=r.top+.5)(q.getBoundingClientRect()))(a.getBoundingClientRect())))}})()""")
      assert not t['over'],(w,th,t); assert all(r>=6 for r in t['rad']) and all(x>=1 for x in t['bw']),t
      assert t['sep']==2 and t['sepv'] and t['noOverlap'],t; assert t['onS2']!=t['offS'],t
      if w>500:
        off=pg.query_selector('#tabs button:not(.on)'); s0=off.evaluate("e=>getComputedStyle(e).boxShadow"); off.hover(); pg.wait_for_timeout(350)
        assert off.evaluate("e=>getComputedStyle(e).boxShadow")!=s0,'hover'; pg.mouse.move(800,h-5)
      pg.evaluate("arGuide()"); pg.wait_for_timeout(600)
      g=pg.evaluate("(()=>{const m=document.querySelector('#arGuide'),r=m.getBoundingClientRect(),i=m.querySelector('img').getBoundingClientRect();return {l:r.left,r:r.right,b:r.bottom,iw:i.width,sc:m.scrollHeight>m.clientHeight,oy:getComputedStyle(m).overflowY}})()")
      assert g['l']>=0 and g['r']<=w and g['b']<=h+.5,(w,h,g); assert g['oy']=='auto'
      assert g['iw']>=(500 if w>1000 else 300),g
      if h==520: assert g['sc'],g
      pg.keyboard.press('Escape')
    pg.close()
  b.close(); print('OK b316')
