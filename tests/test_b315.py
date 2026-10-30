# b315(t570): 클리어 시간 'N분 N초' + 글씨 = 같은 칸 .price × 1.3 (다크/라이트)
import os
from playwright.sync_api import sync_playwright
URL='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','index.html'))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('CHROME','/usr/bin/google-chrome'),args=['--no-sandbox']); pg=b.new_page(viewport={'width':1500,'height':950})
  pg.goto(URL); pg.wait_for_timeout(800)
  pg.evaluate("""()=>{const all={};for(const b of BOSSES)all[b.id]={enabled:true,party:1,diff:b.diffs[0]};S.characters=[{id:'c0',name:'테스트',level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}];S.activeId='c0';S.clears={};BOSSES.forEach((b,i)=>b.diffs.forEach(d=>S.clears[b.id+'|'+d]={sec:[205,25,600][i%3]}));save();render();}""")
  pg.click('#tabs [data-tab="boss"]'); pg.wait_for_timeout(500)
  for th in ['dark','light']:
    pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); pg.wait_for_timeout(200)
    r=pg.evaluate("()=>[...document.querySelectorAll('.boss .clrtime')].slice(0,3).map(c=>[c.textContent,parseFloat(getComputedStyle(c).fontSize),parseFloat(getComputedStyle(c.closest('.boss').querySelector('.price')).fontSize)])")
    assert [x[0] for x in r]==['3분 25초','0분 25초','10분 0초'],r
    for t,a,pz in r: assert abs(a-pz*1.3)<.05,(th,a,pz)
  b.close(); print('OK b315')
