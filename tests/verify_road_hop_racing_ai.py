from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
URL='http://127.0.0.1:8770/road-hop/'
o=Options();o.add_argument('-headless');o.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=o,service=Service('/snap/bin/firefox.geckodriver'))
try:
 d.get(URL)
 for _ in range(50):
  if d.execute_script('return __game&&__game.ready'):break
  time.sleep(.1)
 contract=d.execute_script("return [__game.RACE_LENGTH,__game.rivals.length,__game.aiDecision(12,0,'careful'),__game.aiDecision(12,0,'careful')]")
 assert contract[0:2]==[50,3] and contract[2]==contract[3],contract
 d.execute_script("__game.setMode('rally');__game.start()")
 profiles=d.execute_script("return __game.rivals.map(r=>r.profile)")
 assert profiles==['careful','balanced','aggressive'],profiles
 respawn=d.execute_script("__game.debug.setRacer(0,27,2);__game.debug.crashRival(0);return [__game.rivals[0].row,__game.rivals[0].checkpoint,__game.rivals[0].crashes]")
 assert respawn==[20,20,1],respawn
 d.execute_script("__game.save.missions.claimed=[true,true,true];__game.debug.setCoins(0);__game.debug.finishRace([1,0,2,3])");finish=d.execute_script("return [__game.state,__game.race.finished,__game.race.reward,__game.save.coins,__game.race.order.length]")
 assert finish[0]=='RACE_COMPLETE' and finish[1:] == [True,40,40,4],finish
 bounded=d.execute_script("""let disposed=0;const seen=new Set();for(const r of __game.rivals)r.mesh.traverse(o=>{if(o.geometry&&!seen.has(o.geometry)){seen.add(o.geometry);o.geometry.addEventListener('dispose',()=>disposed++)}});const expected=seen.size,before=__game.renderer.info.memory.geometries;__game.start();const firstDisposed=disposed;for(let i=0;i<5;i++){__game.start();__game.debug.advance(.1)}const rows=__game.lanes.map(l=>l.row);return [Math.min(...rows),Math.max(...rows),rows.length,before,__game.renderer.info.memory.geometries,__errors.slice(),firstDisposed,expected];""")
 assert bounded[0]>=-5 and bounded[1]<=24 and bounded[2]<=30 and bounded[4]<=bounded[3]+30 and bounded[5]==[],bounded
 assert bounded[6]==bounded[7] and bounded[7]>0,bounded
 rendering=d.execute_script("""const base=__game.lanes[0].group.children[0];return [__game.renderer.getPixelRatio(),__game.renderer.shadowMap.enabled,__game.pip.scale.x,base.geometry.parameters.width,__game.camera.right-__game.camera.left,!!__game.scene.getObjectByName('world-underlay')];""")
 assert rendering[0:3]==[1,False,.72] and rendering[3]>=rendering[4] and rendering[5] is True,rendering
 print('ROAD HOP RACING AI PASS',contract,profiles,respawn,finish,bounded,rendering)
finally:d.quit()
