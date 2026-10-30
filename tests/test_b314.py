# b314: 사이트 전체 글씨체 통일(Pretendard 스택, 자간 보통) — 탭마다 같아야 함, 디지털 글씨(MrjUnitKo)는 유지
import os
from playwright.sync_api import sync_playwright
URL='file://'+os.path.abspath(os.path.join(os.path.dirname(__file__),'..','index.html'))
def main():
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME','/usr/bin/google-chrome'),args=['--no-sandbox']); pg=b.new_page(viewport={'width':1500,'height':950})
    pg.goto(URL); pg.wait_for_timeout(800)
    pg.evaluate("""()=>{const all={};for(const b of BOSSES)all[b.id]={enabled:true,party:1,diff:b.diffs[0]};S.characters=[{id:'c0',name:'테스트',level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}}];S.activeId='c0';save();render();}""")
    seen={}
    for t in ['boss','total','loot','auto','live']:
      pg.click(f'#tabs [data-tab="{t}"]'); pg.wait_for_timeout(500)
      r=pg.evaluate("""()=>{const o={};const q=(k,s)=>{const e=document.querySelector(s);if(e){const c=getComputedStyle(e);o[k]=[c.fontFamily,c.letterSpacing]}};q('body','body');q('nm','#charList .nm');q('btn','#tabs [data-tab]');
        const bad=[...document.querySelectorAll('body *')].filter(e=>e.offsetParent&&/Orbit/.test(getComputedStyle(e).fontFamily)).length;o.orbit=bad;
        const d=document.querySelector('.tir-k,.tsk,.hdot');o.dig=d?getComputedStyle(d).fontFamily:null;return o}""")
      assert r['orbit']==0,(t,r)
      for k in ['body','nm','btn']:
        if k in r:
          assert r[k][0].startswith('Pretendard'),(t,k,r[k]); assert r[k][1]=='normal',(t,k,r[k])
          seen.setdefault(k,set()).add(tuple(r[k]))
      if r['dig']: assert 'MrjUnitKo' in r['dig'],(t,r['dig'])
    for k,v in seen.items(): assert len(v)==1,(k,v)
    assert not pg.evaluate("!!document.getElementById('orbitCss')")
    b.close(); print('OK b314')
main()
