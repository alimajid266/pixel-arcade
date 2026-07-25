from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time

BASE='https://pixel-arcade-pied.vercel.app'
options=Options();options.add_argument('-headless');options.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=options,service=Service('/snap/bin/firefox.geckodriver'))
try:
    d.set_window_size(1280,900)
    d.get(BASE+'/');time.sleep(.7)
    home=[d.title,d.current_url,d.execute_script('return window.__errors')]
    assert home==['Pixel Arcade',BASE+'/',[]],home
    assert d.find_element(By.ID,'play-flappy').get_attribute('href')==BASE+'/flappy/'
    assert d.find_element(By.ID,'play-zombie').get_attribute('href')==BASE+'/zombie-defense/'

    d.find_element(By.ID,'play-flappy').click();time.sleep(.7)
    flappy=d.execute_script("return [document.title,__game.machine.name,__errors.slice(),__game.sound.context===null,location.pathname]")
    assert flappy==['Flappy Canvas','MENU',[],True,'/flappy/'],flappy
    d.find_element(By.ID,'music-toggle').click()
    assert d.execute_script('return [__game.sound.musicMuted,__game.sound.sfxMuted]')==[True,False]

    d.find_element(By.ID,'zombie-game-link').click();time.sleep(.7)
    zombie=d.execute_script("return [document.title,__game.state.current,__errors.slice(),__game.maps.length,__game.audio.ctx===null,location.pathname]")
    assert zombie==['Zombie Defense: Last Outpost','MENU',[],3,True,'/zombie-defense/'],zombie
    d.find_element(By.ID,'sfx-toggle').click()
    assert d.execute_script('return [__game.audio.musicMuted,__game.audio.sfxMuted]')==[False,True]

    d.find_element(By.CSS_SELECTOR,'.rail-brand').click();time.sleep(.5)
    assert d.current_url==BASE+'/' and d.title=='Pixel Arcade',(d.current_url,d.title)
    d.save_screenshot('/tmp/pixel-arcade-production.png')
    print('PIXEL ARCADE PRODUCTION PASS:',home,flappy,zombie)
finally:
    d.quit()
