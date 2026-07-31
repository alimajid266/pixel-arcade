from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time

URL='http://127.0.0.1:8770'
options=Options();options.add_argument('-headless');options.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=options,service=Service('/snap/bin/firefox.geckodriver'))
try:
    d.set_window_size(1280,900)
    d.get(URL+'/');time.sleep(.3)
    assert d.title=='Pixel Arcade',d.title
    assert d.find_element(By.ID,'play-flappy').get_attribute('href')==URL+'/flappy/'
    assert d.find_element(By.ID,'play-zombie').get_attribute('href')==URL+'/zombie-defense/'
    assert d.find_element(By.ID,'play-road-hop').get_attribute('href')==URL+'/road-hop/'
    assert d.execute_script('return window.__errors')==[]
    d.save_screenshot('/tmp/pixel-arcade-home.png')

    d.get(URL+'/flappy/');time.sleep(.4)
    flappy=d.execute_script("""return [
      document.title,__game.machine.name,__errors.slice(),
      document.getElementById('flappy-game-link').getAttribute('href'),
      document.getElementById('zombie-game-link').getAttribute('href'),
      document.getElementById('road-hop-game-link').getAttribute('href'),
      document.querySelector('.rail-brand').getAttribute('href'),
      __game.sound.context===null
    ]""")
    assert flappy==['Flappy Canvas','MENU',[],'/flappy/','/zombie-defense/','/road-hop/','/',True],flappy
    d.find_element(By.ID,'music-toggle').click()
    assert d.execute_script('return [__game.sound.musicMuted,__game.sound.sfxMuted]')==[True,False]
    d.save_screenshot('/tmp/pixel-arcade-flappy.png')

    d.find_element(By.ID,'zombie-game-link').click();time.sleep(.4)
    zombie=d.execute_script("""return [
      document.title,__game.state.current,__errors.slice(),__game.maps.length,
      document.getElementById('flappy-game-link').getAttribute('href'),
      document.getElementById('zombie-game-link').getAttribute('href'),
      document.getElementById('road-hop-game-link').getAttribute('href'),
      document.querySelector('.rail-brand').getAttribute('href'),
      __game.audio.ctx===null
    ]""")
    assert zombie==['Zombie Defense: Last Outpost','MENU',[],3,'/flappy/','/zombie-defense/','/road-hop/','/',True],zombie
    d.find_element(By.ID,'sfx-toggle').click()
    assert d.execute_script('return [__game.audio.musicMuted,__game.audio.sfxMuted,__game.state.current]')==[False,True,'MENU']
    d.save_screenshot('/tmp/pixel-arcade-zombie.png')

    d.find_element(By.CSS_SELECTOR,'.rail-brand').click();time.sleep(.25)
    assert d.current_url==URL+'/' and d.title=='Pixel Arcade',(d.current_url,d.title)
    d.set_window_size(390,844);d.get(URL+'/');time.sleep(.25)
    mobile=d.execute_script("return [document.documentElement.scrollWidth,window.innerWidth,document.querySelectorAll('.game-card').length,window.__errors.slice()]")
    assert mobile[0]<=mobile[1] and mobile[2:]==[3,[]],mobile
    d.save_screenshot('/tmp/pixel-arcade-home-mobile.png')
    print('COMBINED PIXEL ARCADE PASS:',flappy,zombie,mobile)
finally:
    d.quit()
