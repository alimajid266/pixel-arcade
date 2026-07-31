from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

URL = "http://127.0.0.1:8770/road-hop/"
options = Options(); options.add_argument("-headless")
options.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
driver = webdriver.Firefox(options=options, service=Service("/snap/bin/firefox.geckodriver"))
try:
    driver.set_window_size(1280, 800)
    driver.get(URL)
    for _ in range(30):
        if driver.execute_script("return window.__game && window.__game.ready"):
            break
        time.sleep(.1)

    driver.find_element('id','start').click()
    start = driver.execute_script("""
      return [__game.state,__game.player.row,__game.player.x,__game.score,__game.lanes.length];
    """)
    assert start[0:4] == ["PLAYING", 0, 0, 0] and start[4] >= 25, start

    moved = driver.execute_script("""
      const accepted=__game.move('forward');
      __game.debug.advance(.25);
      return [accepted,__game.player.row,__game.player.x,__game.score,__game.pip.position.z];
    """)
    assert moved == [True, 1, 0, 1, -1], moved

    back = driver.execute_script("""
      __game.move('back');__game.debug.advance(.25);
      return [__game.player.row,__game.score];
    """)
    assert back == [0, 1], back

    blocked = driver.execute_script("""
      __game.debug.blockCell(1,0);
      const accepted=__game.move('forward');
      __game.debug.advance(.25);
      return [accepted,__game.player.row,__game.score];
    """)
    assert blocked == [False, 0, 1], blocked

    keyboard = driver.execute_script("""
      __game.debug.clearBlockers(1);
      dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowUp'}));
      __game.debug.advance(.25);
      dispatchEvent(new KeyboardEvent('keydown',{key:'p'}));
      const paused=__game.state;
      dispatchEvent(new KeyboardEvent('keydown',{key:'p'}));
      return [__game.player.row,__game.score,paused,__game.state];
    """)
    assert keyboard == [1, 1, "PAUSED", "PLAYING"], keyboard

    crash = driver.execute_script("""
      __game.debug.forceCrash();
      __game.debug.advance(.02);
      return [__game.state,__game.best,localStorage.getItem('roadHop.best'),document.getElementById('gameover').classList.contains('hidden')];
    """)
    assert crash == ["GAME_OVER", 1, "1", False], crash

    driver.find_element('id','retry').click()
    retry = driver.execute_script("""
      return [__game.state,__game.player.row,__game.player.x,__game.score,__game.best];
    """)
    assert retry == ["PLAYING", 0, 0, 0, 1], retry

    real_collision = driver.execute_script("""
      const car=__game.vehicles[0];
      __game.player.row=car.row;__game.player.x=car.x;
      __game.pip.position.set(car.x,0,-car.row);
      __game.debug.advance(.02);
      return [__game.state,car.row,__game.best];
    """)
    assert real_collision[0] == "GAME_OVER" and real_collision[1] > 0 and real_collision[2] == 1, real_collision

    bounds = driver.execute_script("""
      __game.start();
      __game.player.row=99;__game.pip.position.z=-99;
      __game.move('forward');__game.debug.advance(.25);
      __game.player.row=0;__game.player.x=0;__game.player.moving=null;__game.pip.position.set(0,0,0);
      __game.move('forward');__game.debug.advance(.25);
      const rows=__game.lanes.map(l=>l.row);
      return [Math.min(...rows),Math.max(...rows),rows.length];
    """)
    assert bounds[0] >= -5 and bounds[1] <= 31 and bounds[2] <= 38, bounds
    assert driver.execute_script("return __errors.slice()") == []
    print("ROAD HOP GAMEPLAY PASS", start, moved, blocked, keyboard, crash, retry, real_collision, bounds)
finally:
    driver.quit()
