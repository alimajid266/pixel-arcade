from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select
import time
URL='http://127.0.0.1:8770/road-hop/'
o=Options();o.add_argument('-headless');o.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=o,service=Service('/snap/bin/firefox.geckodriver'))
try:
 d.set_window_size(1280,800);d.get(URL)
 for _ in range(50):
  if d.execute_script('return __game&&__game.ready'):break
  time.sleep(.1)
 assert d.find_element('id','biome-select').is_displayed()
 d.execute_script("localStorage.removeItem('roadHop.save.v2')");d.refresh()
 for _ in range(50):
  if d.execute_script('return __game&&__game.ready'):break
  time.sleep(.1)
 Select(d.find_element('id','biome-select')).select_by_value('wetlands')
 d.find_element('id','start').click()
 economy=d.execute_script("""__game.debug.clearBlockers(1);__game.move('forward');__game.debug.advance(.25);__game.move('back');__game.debug.advance(.25);__game.move('forward');__game.debug.advance(.25);return [__game.save.coins,__game.player.row,__game.biome,__game.lanes.some(l=>l.type==='water')];""")
 assert economy[0:3]==[1,1,'wetlands'],economy
 d.execute_script("__game.setState('MENU')")
 d.find_element('id','shop-open').click();assert d.find_element('id','shop').is_displayed()
 bought=d.execute_script("__game.debug.setCoins(75);return __game.buyCharacter('BOUNCE')&&__game.selectCharacter('BOUNCE')")
 assert bought and d.execute_script("return [__game.save.coins,__game.character]")==[0,'BOUNCE']
 d.refresh()
 for _ in range(50):
  if d.execute_script('return __game&&__game.ready'):break
  time.sleep(.1)
 assert d.execute_script("return [__game.save.coins,__game.character,__game.biome,__errors.slice()]")==[0,'BOUNCE','wetlands',[]]
 daily=d.execute_script("return [__game.dailySeed(),__game.dailySeed()]");assert daily[0]==daily[1]
 d.find_element('id','daily-toggle').click();assert d.execute_script("return __game.dailyMode") is True
 d.find_element('id','start').click();daily_run=d.execute_script("""for(let row=1;row<=3;row++){__game.debug.clearBlockers(row);for(const v of __game.vehicles){v.speed=0;v.x=99;v.mesh.position.x=99}__game.move('forward');__game.debug.advance(.25)}return [__game.score,__game.save.records.daily[new Date().toISOString().slice(0,10)]];""");assert daily_run==[3,3],daily_run
 assert d.execute_script("return __errors.slice()")==[]
 print('ROAD HOP EXPANSION RUNTIME PASS',economy,daily_run)
finally:d.quit()
