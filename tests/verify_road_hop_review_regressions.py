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

    assert driver.execute_script("return document.fonts.check(\"16px 'Road Hop Arcade'\")")
    assert 'Road Hop Arcade' in driver.execute_script("return getComputedStyle(document.body).fontFamily")
    assert driver.execute_script("return __game.renderer.getContext().getContextAttributes().antialias") is True

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
        if(biome==='haunted')found.hauntedPositions=[];
        __game.world.traverse(o=>{
          if(o.name)found[biome].push(o.name);
          if(biome==='haunted'&&(o.name==='haunted-grave-cluster'||o.name==='haunted-lamp')){
            const p=o.getWorldPosition(o.position.clone());
            found.hauntedPositions.push(`${p.x.toFixed(2)}:${p.z.toFixed(2)}`);
          }
        });
        if(biome==='haunted'){
          if(__game.camera.getObjectByName('haunted-moon'))found[biome].push('haunted-moon');
          if(__game.ambience.getObjectByName('haunted-ghost'))found[biome].push('haunted-ghost');
        }
      }
      return found;
    """)
    assert 'autumn-leaf-pile' in props['autumn'], props
    assert 'haunted-lamp' in props['haunted'], props
    assert 'haunted-grave-cluster' in props['haunted'], props
    assert 'haunted-moon' in props['haunted'], props
    assert 'haunted-ghost' in props['haunted'], props
    for detail in ('haunted-jack-o-lantern', 'haunted-path-lantern', 'haunted-candle-cluster', 'haunted-bat'):
        assert detail in props['haunted'], (detail, props['haunted'])
    assert len(props['hauntedPositions']) == len(set(props['hauntedPositions'])), props['hauntedPositions']

    # Wetlands crossings must meander instead of repeating the same center route.
    wetland_routes = driver.execute_script("""
      __game.setBiome('wetlands');__game.start();
      return __game.lanes.filter(l=>l.type==='water').map(l=>[l.row,[...l.bridges].sort((a,b)=>a-b).join(',')]);
    """)
    assert len(wetland_routes) >= 4, wetland_routes
    assert len({route for _, route in wetland_routes}) >= 3, wetland_routes
    for previous, current in zip(wetland_routes, wetland_routes[1:]):
        assert previous[1] != current[1], wetland_routes
        if current[0] == previous[0] + 1:
            previous_center = int(previous[1].split(',')[1])
            current_center = int(current[1].split(',')[1])
            assert abs(current_center - previous_center) == 1, wetland_routes

    regenerated_routes = driver.execute_script("""
      const exercise=daily=>{
        if(__game.dailyMode!==daily)document.getElementById('daily-toggle').click();__game.setMode('endless');__game.setBiome('wetlands');__game.start();
        const snap=()=>Object.fromEntries(__game.lanes.filter(l=>l.type==='water').map(l=>[l.row,l.bridgeCenter]));
        const initial=snap();__game.aiDecision(100,0,'balanced');for(let row=99;row>=0;row--)__game.aiDecision(row,0,'balanced');const regenerated=snap();
        __game.start();const fresh=snap();
        const changed=Object.keys(fresh).filter(row=>regenerated[row]!==fresh[row]).map(Number);
        const sorted=Object.entries(regenerated).map(([row,center])=>[Number(row),center]).sort((a,b)=>a[0]-b[0]),broken=[];
        for(let i=1;i<sorted.length;i++)if(sorted[i][0]===sorted[i-1][0]+1&&Math.abs(sorted[i][1]-sorted[i-1][1])!==1)broken.push([sorted[i-1],sorted[i]]);
        return {initial,regenerated,fresh,changed,broken};
      };
      const result={standard:exercise(false),daily:exercise(true)};if(__game.dailyMode)document.getElementById('daily-toggle').click();return result;
    """)
    for route_mode in ('standard','daily'):
        assert regenerated_routes[route_mode]['changed'] == [], regenerated_routes
        assert regenerated_routes[route_mode]['broken'] == [], regenerated_routes

    long_route = driver.execute_script("""
      const exercise=daily=>{
        if(__game.dailyMode!==daily)document.getElementById('daily-toggle').click();__game.setMode('endless');__game.setBiome('wetlands');__game.start();const failures=[];let reachable=new Set(Array.from({length:15},(_,i)=>i-7));
        for(let row=2;row<=500;row++){
          __game.aiDecision(row,0,'balanced');const previous=__game.lanes.find(l=>l.row===row-1),current=__game.lanes.find(l=>l.row===row);
          if(previous?.type==='water'&&current?.type==='grass'&&![...previous.bridges].some(cell=>!current.blockers.has(cell)))failures.push(['water-grass',row,[...previous.bridges],[...current.blockers]]);
          if(previous?.type==='grass'&&current?.type==='water'&&![...current.bridges].some(cell=>!previous.blockers.has(cell)))failures.push(['grass-water',row,[...previous.blockers],[...current.bridges]]);
          const open=cell=>cell>=-7&&cell<=7&&!current.blockers.has(cell)&&(current.type!=='water'||current.bridges.has(cell));let next=new Set([...reachable].filter(open)),changed=true;
          while(changed){changed=false;for(const cell of [...next])for(const adjacent of[cell-1,cell+1])if(open(adjacent)&&!next.has(adjacent)){next.add(adjacent);changed=true}}
          if(!next.size){failures.push(['no-route',row,[...reachable],current.type,[...current.blockers],[...current.bridges]]);break}reachable=next;
        }
        return failures;
      };
      const result={standard:exercise(false),daily:exercise(true)};if(__game.dailyMode)document.getElementById('daily-toggle').click();return result;
    """)
    assert long_route == {'standard': [], 'daily': []}, long_route

    # Bound ultrawide gameplay and keep both traffic wrap endpoints outside its camera frustum.
    driver.set_window_rect(width=2560, height=1100)
    time.sleep(0.25)
    traffic_entry = driver.execute_script("""
      __game.setBiome('meadow');__game.start();__game.camera.updateMatrixWorld();
      const canvasRect=document.getElementById('game').getBoundingClientRect(),projected=[];
      for(const row of [...new Set(__game.vehicles.map(vehicle=>vehicle.row))])for(const x of [-20,20]){
        const point=__game.vehicles[0].mesh.position.clone().set(x,.5,-row).project(__game.camera);
        projected.push([row,x,point.x,point.y,Math.abs(point.x)>1.02||Math.abs(point.y)>1.02]);
      }
      const v=__game.vehicles[0];v.direction=1;v.x=100;v.mesh.position.x=100;
      __game.debug.advance(.05);
      return {x:v.x,inner:[innerWidth,innerHeight],canvas:[canvasRect.x,canvasRect.y,canvasRect.width,canvasRect.height],projected};
    """)
    assert traffic_entry['x'] <= -18, traffic_entry
    assert traffic_entry['inner'][0] / traffic_entry['inner'][1] > 2.3, traffic_entry
    assert traffic_entry['canvas'][2] <= traffic_entry['canvas'][3] * 2 + 1, traffic_entry
    assert abs(traffic_entry['canvas'][0] - (traffic_entry['inner'][0] - traffic_entry['canvas'][2]) / 2) <= 1, traffic_entry
    assert all(point[4] for point in traffic_entry['projected']), traffic_entry

    hud_writes = driver.execute_async_script("""
      const done=arguments[0],before=__game.debug.uiWriteCount();
      __game.setMode('endless');__game.start();__game.debug.clearBlockers(1);
      for(const v of __game.vehicles){v.x=99;v.mesh.position.x=99}
      __game.move('forward');__game.debug.advance(.25);
      requestAnimationFrame(()=>done(__game.debug.uiWriteCount()-before));
    """)
    assert 0 <= hud_writes <= 1, hud_writes
    assert driver.execute_script('return __errors.slice()') == []
    print('ROAD HOP REVIEW REGRESSIONS PASS', normalized, rollover, biome_mission, postcard, daily_rally)
finally:
    driver.quit()
