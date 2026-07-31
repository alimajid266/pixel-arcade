from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

URL = 'http://127.0.0.1:8770/road-hop/'
FIREFOX = '/snap/firefox/current/usr/lib/firefox/firefox'
DRIVER = '/snap/bin/firefox.geckodriver'


def browser(storage=True):
    options = Options()
    options.add_argument('-headless')
    options.binary_location = FIREFOX
    if not storage:
        options.set_preference('dom.storage.enabled', False)
    return webdriver.Firefox(options=options, service=Service(DRIVER))


def wait_ready(driver):
    for _ in range(60):
        try:
            if driver.execute_script('return !!(window.__game && window.__game.ready)'):
                return
        except Exception:
            pass
        time.sleep(.1)
    raise AssertionError(driver.execute_script('return window.__errors || []'))


# Storage denial must not prevent startup.
denied = browser(storage=False)
try:
    denied.get(URL)
    wait_ready(denied)
    assert denied.execute_script('return __errors.slice()') == []
finally:
    denied.quit()


driver = browser()
try:
    driver.set_window_size(1280, 800)
    driver.get(URL)
    wait_ready(driver)

    assert driver.execute_script("return typeof __game.debug.normalizeSave") == 'function'
    normalized = driver.execute_script("""
      return __game.debug.normalizeSave({
        coins:'bad',best:99999999,owned:['PIP','PIP','NOPE'],character:'NOPE',
        postcards:['meadow','meadow','NOPE','wetlands','autumn','haunted','meadow'],
        visited:['haunted','haunted','NOPE','meadow','wetlands','autumn'],
        records:{rallyBest:99,daily:{'2026-02-31':8,'2026-07-30':9,'bad-key':99,'2026-07-31':99999999}},
        missions:{day:'1900-01-01',progress:[99999,-5,'bad'],claimed:[1,0,'yes'],biomes:['meadow','meadow','NOPE']}
      });
    """)
    assert normalized['coins'] == 0 and normalized['best'] == 999999
    assert normalized['owned'] == ['PIP'] and normalized['character'] == 'PIP'
    assert normalized['postcards'] == ['meadow','wetlands','autumn','haunted']
    assert normalized['visited'] == ['haunted','meadow','wetlands','autumn']
    assert normalized['records'] == {'rallyBest': 4, 'daily': {'2026-07-30': 9, '2026-07-31': 999999}}

    assert driver.execute_script("return typeof __game.debug.changeCoins") == 'function'
    coin_bounds = driver.execute_script("""
      __game.debug.setCoins(999999);__game.debug.changeCoins(1);const capped=__game.save.coins;
      __game.debug.changeCoins(-1000000);const floored=__game.save.coins;
      __game.debug.setCoins(999999);__game.setMode('endless');__game.start();
      __game.debug.clearBlockers(1);for(const v of __game.vehicles){v.x=99;v.mesh.position.x=99}
      __game.move('forward');__game.debug.advance(.25);const rowReward=__game.save.coins;
      __game.start();__game.debug.finishRace([1,0,2,3]);const rallyReward=__game.save.coins;
      return [capped,floored,rowReward,rallyReward];
    """)
    assert coin_bounds == [999999,0,999999,999999], coin_bounds

    rollover = driver.execute_script("""
      __game.save.missions.day='1900-01-01';
      __game.save.missions.progress=[20,20,20];
      __game.save.missions.claimed=[true,true,true];
      __game.save.missions.biomes=['meadow','wetlands'];
      __game.debug.ensureMissionDay();
      return __game.save.missions;
    """)
    assert rollover['progress'] == [0,0,0] and rollover['claimed'] == [False,False,False]
    assert rollover['biomes'] == []

    biome_mission = driver.execute_script("""
      __game.save.visited=['meadow','wetlands','autumn','haunted'];
      __game.save.missions.biomes=['meadow'];
      __game.setBiome('wetlands');
      __game.start();
      return __game.save.missions.biomes.slice();
    """)
    assert biome_mission == ['meadow','wetlands'], biome_mission

    postcard = driver.execute_script("""
      __game.setMode('endless');__game.setBiome('autumn');__game.start();
      for(let row=1;row<=10;row++){
        __game.debug.clearBlockers(row);
        const lane=__game.lanes.find(l=>l.row===row);
        if(lane&&lane.type==='water')lane.bridges.add(0);
        for(const v of __game.vehicles){v.speed=0;v.x=99;v.mesh.position.x=99}
        __game.move('forward');__game.debug.advance(.25);
      }
      return [__game.score,__game.save.postcards.includes('autumn')];
    """)
    assert postcard == [10, True], postcard

    driver.execute_script("__game.debug.setDaily(true);__game.setMode('rally')")
    daily_rally = driver.execute_script("return [__game.dailyMode,document.getElementById('daily-toggle').textContent]")
    assert daily_rally == [False, 'PLAY DAILY CHALLENGE'], daily_rally

    assert driver.execute_script("return typeof __game.debug.stepSequence") == 'function'
    deterministic = driver.execute_script("""
      function snap(){return {
        rivals:__game.rivals.map(r=>[r.row,r.x,r.checkpoint,r.crashes,Number(r.wait.toFixed(6)),r.finished]),
        order:__game.race.order.slice(),
        vehicles:__game.vehicles.map(v=>Number(v.x.toFixed(5)))
      }}
      __game.setMode('rally');__game.start();__game.debug.stepSequence([.1,.1,.1,.06]);const a=snap();
      __game.start();__game.debug.stepSequence([.09,.09,.09,.09]);const b=snap();
      __game.debug.stepSequence([.1]);__game.start();__game.debug.stepSequence([.1]);const retry=snap();
      __game.start();__game.debug.stepSequence([.1]);const clean=snap();
      return [a,b,retry,clean];
    """)
    assert deterministic[0] == deterministic[1], deterministic[:2]
    assert deterministic[2] == deterministic[3], deterministic[2:]

    props = driver.execute_script("""
      const found={};
      for(const biome of ['autumn','haunted']){
        __game.setBiome(biome);__game.start();
        found[biome]=[];
        __game.world.traverse(o=>{if(o.name)found[biome].push(o.name)});
      }
      return found;
    """)
    assert 'autumn-leaf-pile' in props['autumn'], props
    assert 'haunted-lamp' in props['haunted'], props
    assert driver.execute_script('return __errors.slice()') == []
    print('ROAD HOP REVIEW REGRESSIONS PASS', normalized, rollover, biome_mission, postcard, daily_rally)
finally:
    driver.quit()
