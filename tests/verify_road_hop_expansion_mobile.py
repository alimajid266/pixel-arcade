from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select
import time
URL='http://127.0.0.1:8770/road-hop/'
o=Options();o.add_argument('-headless');o.binary_location='/snap/firefox/current/usr/lib/firefox/firefox';o.enable_bidi=True
d=webdriver.Firefox(options=o,service=Service('/snap/bin/firefox.geckodriver'))
try:
 d.get(URL);d.browsing_context.set_viewport(context=d.current_window_handle,viewport={'width':390,'height':844})
 for _ in range(50):
  if d.execute_script('return __game&&__game.ready'):break
  time.sleep(.1)
 geometry=d.execute_script("""const ids=['start','shop-open','gallery-open','biome-select','mode-select','daily-toggle'];return [innerWidth,document.documentElement.scrollWidth,...ids.map(id=>{const r=document.getElementById(id).getBoundingClientRect();return [r.left,r.right,r.width,r.height]})];""")
 assert geometry[1]<=geometry[0],geometry
 for left,right,w,h in geometry[2:]:assert left>=0 and right<=390 and w>=44 and h>=44,(left,right,w,h)
 d.find_element('id','shop-open').click();assert d.find_element('id','shop').is_displayed()
 d.find_element('id','shop-close').click();d.find_element('id','gallery-open').click();assert d.find_element('id','gallery').is_displayed()
 d.find_element('id','gallery-close').click();Select(d.find_element('id','mode-select')).select_by_value('rally');d.find_element('id','start').click()
 swipe=d.execute_script("""const c=document.getElementById('game');c.dispatchEvent(new PointerEvent('pointerdown',{pointerId:44,clientX:195,clientY:600,bubbles:true}));c.dispatchEvent(new PointerEvent('pointerup',{pointerId:44,clientX:195,clientY:480,bubbles:true}));__game.debug.advance(.25);return [__game.mode,__game.player.row,__game.state,__errors.slice()];""")
 assert swipe==['rally',1,'PLAYING',[]],swipe
 d.save_screenshot('/tmp/road-hop-expansion-mobile.png')
 print('ROAD HOP EXPANSION MOBILE PASS',geometry,swipe)
finally:d.quit()
