from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

URL = "http://127.0.0.1:8770/road-hop/"
options = Options()
options.add_argument("-headless")
options.binary_location = "/snap/firefox/current/usr/lib/firefox/firefox"
driver = webdriver.Firefox(options=options, service=Service("/snap/bin/firefox.geckodriver"))
try:
    driver.set_window_size(1280, 800)
    driver.get(URL)
    for _ in range(30):
        if driver.execute_script("return window.__game && window.__game.ready"):
            break
        time.sleep(.1)
    shell = driver.execute_script("""
        const canvas=document.getElementById('game');
        return {
          title:document.title,
          state:__game.state,
          errors:__errors.slice(),
          revision:__game.THREE_REVISION,
          rendered:canvas.width>0 && canvas.height>0 && !!canvas.getContext('webgl2'),
          sceneChildren:__game.scene.children.length,
          camera:__game.camera.type,
          renderer:__game.renderer.isWebGLRenderer
        };
    """)
    assert shell["title"] == "Road Hop", shell
    assert shell["state"] == "MENU" and shell["errors"] == [], shell
    assert shell["rendered"] and shell["sceneChildren"] >= 4, shell
    assert shell["revision"] == "170", shell
    assert shell["camera"] == "OrthographicCamera", shell
    assert shell["renderer"] is True, shell
    fps = driver.execute_async_script("""
      const done=arguments[0],start=performance.now();let frames=0;
      function tick(now){frames++;if(now-start>=1200)done(frames*1000/(now-start));else requestAnimationFrame(tick)}
      requestAnimationFrame(tick);
    """)
    assert fps >= 40, fps
    lane_types = driver.execute_script("return Array.from(new Set(__game.lanes.map(l=>l.type))).sort()")
    assert lane_types == ['grass','road'], lane_types
    memory = driver.execute_async_script("""
      const done=arguments[0],samples=[];
      function cycle(left){
        __game.start();
        requestAnimationFrame(()=>requestAnimationFrame(()=>{
          samples.push(__game.renderer.info.memory.geometries);
          if(left>1)cycle(left-1);else done(samples);
        }));
      }
      cycle(5);
    """)
    assert max(memory)-min(memory) <= 2, memory
    driver.save_screenshot("/tmp/road-hop-shell.png")
    driver.execute_script("__game.start();__game.move('forward');__game.debug.advance(.25)")
    driver.save_screenshot("/tmp/road-hop-gameplay.png")
    print("ROAD HOP SHELL PASS", shell, "FPS", round(fps,1), lane_types, "GEOMETRIES", memory)
finally:
    driver.quit()
