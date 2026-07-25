from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

source=(Path(__file__).resolve().parents[1]/'flappy/index.html').read_text()
assert 'TOP PLAYERS' in source and 'TOP PILOTS' not in source

options=Options();options.add_argument('-headless');options.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=options,service=Service('/snap/bin/firefox.geckodriver'))
try:
    d.get('http://127.0.0.1:8770/flappy/');time.sleep(.4)
    empty=d.execute_script("""
      __game.leaderboard=[];
      const c=__game.ctx,old=c.fillText.bind(c),calls=[];
      c.fillText=function(text,x,y){if(text==='NO SCORES YET')calls.push([x,y,this.textAlign]);return old(text,x,y);};
      __game.menu.draw(c);c.fillText=old;return calls;
    """)
    assert empty==[[280,344,'center']],empty
    ghost=d.execute_script("""
      const c=__game.ctx,old=c.rotate.bind(c),rotations=[];
      c.rotate=function(a){rotations.push(a);return old(a);};
      __game.bird.wingAngle=0;__game.bird.drawGhost(c,210,.42);c.rotate=old;
      __game.previousGhost[0]=200;__game.previousGhost[1]=212;__game.previousGhostCount=2;__game.ghostPlaybackTime=1/30;
      return [rotations,__game.getGhostTilt(),__errors.slice()];
    """)
    assert any(abs(v-.42)<1e-6 for v in ghost[0]),ghost
    assert ghost[1]>0 and ghost[2]==[],ghost
    print('FLAPPY FEEDBACK PASS:',empty,ghost)
finally:
    d.quit()
