from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

root = Path(__file__).resolve().parents[1]
home = (root / 'index.html').read_text()
flappy = (root / 'flappy/index.html').read_text()
zombie = (root / 'zombie-defense/index.html').read_text()

assert 'Music and sound-effect preferences are controlled independently inside each game.' not in home
assert 'transform:translate(-50%,-50%)' in home.replace(' ', '')
for source in (flappy, zombie):
    compact = source.replace(' ', '')
    assert 'right:-8px;top:-4px' in compact
    assert '.game-tilesmall{display:block;margin-top:5px;font-size:9px}' in compact

options = Options()
options.add_argument('-headless')
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'
driver = webdriver.Firefox(options=options, service=Service('/snap/bin/firefox.geckodriver'))
try:
    driver.get('http://127.0.0.1:8770/zombie-defense/')
    time.sleep(.4)
    result = driver.execute_script("""
      const I = window.__internals;
      const Zombie = I.Zombie, Projectile = I.Projectile, WEAPONS = I.WEAPONS;
      const MANUAL_TYPES = I.MANUAL_TYPES, MANUAL_TEXT = I.MANUAL_TEXT;
      const MENU_LAYOUT = I.MENU_LAYOUT, totalRoute = I.routeLength();
      const earlyBurrowers = I.WAVE_LIST.slice(0, 6).flat().filter(t => t === 'burrower').length;
      const lateBurrowers = I.WAVE_LIST.slice(6).flat().filter(t => t === 'burrower').length;
      const wave1 = new Zombie('walker', 1);
      const wave2 = new Zombie('walker', 2);
      const wave8 = new Zombie('walker', 8);
      const wave12 = new Zombie('walker', 12);

      const toxic = new Zombie('toxic', 5);
      toxic.hp = toxic.maxHp - 50;
      const toxicBefore = toxic.hp;
      toxic.update(1);

      const burrower = new Zombie('burrower', 7);
      const burrowStart = [burrower.underground, burrower.surfaceAt / totalRoute];
      let guard = 0;
      while (burrower.underground && guard++ < 1000) burrower.update(.1);

      const direct = new Zombie('walker', 1);
      const nearby = new Zombie('walker', 1);
      direct.maxHp = direct.hp = 1000;
      nearby.maxHp = nearby.hp = 1000;
      direct.x = direct.drawX = 300; direct.y = direct.drawY = 300;
      nearby.x = nearby.drawX = 340; nearby.y = nearby.drawY = 300;
      const game = {enemies:[direct, nearby], effects:[], scorches:[]};
      const projectile = new Projectile(293, 300, direct, WEAPONS[2]);
      projectile.update(.1, game);

      const a = MENU_LAYOUT.arsenal, m = MENU_LAYOUT.map;
      const layoutsOverlap = a.x < m.x + m.w && a.x + a.w > m.x && a.y < m.y + m.h && a.y + a.h > m.y;
      const start = MENU_LAYOUT.start || {y:515, h:24};
      const instructions = MENU_LAYOUT.instructions || {y:531, h:38};
      const menuSpacing = m.y + m.h < start.y &&
        start.y + start.h < instructions.y;
      return {
        speeds:[wave1.speed,wave2.speed,wave8.speed,wave12.speed],
        toxicHealing:toxic.hp-toxicBefore,
        toxicManual:MANUAL_TEXT[MANUAL_TYPES.indexOf('toxic')],
        burrowStart,
        burrowEnded:!burrower.underground,
        burrowManual:MANUAL_TYPES.includes('burrower'),
        earlyBurrowers,
        lateBurrowers,
        directLoss:1000-direct.hp,
        nearbyLoss:1000-nearby.hp,
        layoutsOverlap,
        menuSpacing,
        errors:window.__errors.slice()
      };
    """)
    assert result['speeds'][0] == 58 and result['speeds'][1] == 58, result
    assert 58 < result['speeds'][2] <= 65 and 58 < result['speeds'][3] <= 70, result
    assert 12 <= result['toxicHealing'] <= 16 and 'FOCUS FIRE' in result['toxicManual'], result
    assert result['burrowStart'][0] and .25 <= result['burrowStart'][1] <= .45, result
    assert result['burrowEnded'] and result['burrowManual'], result
    assert result['earlyBurrowers'] == 0 and result['lateBurrowers'] >= 6, result
    assert abs(result['directLoss'] - 52) < 1e-6, result
    assert 0 < result['nearbyLoss'] <= 8, result
    assert not result['layoutsOverlap'] and result['errors'] == [], result
    assert result['menuSpacing'], result
    print('GAMEPLAY FEEDBACK PASS:', result)
finally:
    driver.quit()
