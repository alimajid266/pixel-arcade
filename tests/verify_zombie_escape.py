from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import json
import time

URL = 'http://127.0.0.1:8770/zombie-defense/'
options = Options()
options.add_argument('-headless')
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'
driver = webdriver.Firefox(
    options=options,
    service=Service('/snap/bin/firefox.geckodriver'),
)

try:
    driver.get(URL)
    time.sleep(.4)
    result = driver.execute_script("""
      const I=__internals;
      const endpoints=I.MAPS.map(map=>{
        const p=map.path[map.path.length-1];
        return {map:map.name,col:p.col,row:p.row,x:p.col*40+20,y:p.row*40+20};
      });

      __game.startGame();
      const route=I.routeLength();
      const boundaryZombie=new I.Zombie('walker',1);
      boundaryZombie.update((route-1)/boundaryZombie.speed);
      const before={x:boundaryZombie.x,y:boundaryZombie.y,reached:boundaryZombie.reached,segment:boundaryZombie.segment};
      boundaryZombie.update(2/boundaryZombie.speed);
      const after={x:boundaryZombie.x,y:boundaryZombie.y,reached:boundaryZombie.reached,segment:boundaryZombie.segment};

      function startIsolatedWave(){
        if(!__game.wave.start())throw new Error('wave '+(__game.wave.wave+1)+' did not start');
        const record=__game.wave.records[__game.wave.wave];
        __game.wave.spawned=__game.wave.queue.length;
        return record;
      }
      function killRealRegularWave(){
        const record=startIsolatedWave();
        record.remaining=record.wave===12?2:1;
        record.regularRemaining=1;
        const enemy=new I.Zombie('walker',record.wave);
        enemy.damage(enemy.hp+1);
        __game.enemies.push(enemy);
        __game.updatePlaying(0);
        if(record.wave===12){
          const boss=__game.enemies.find(enemy=>enemy.type==='boss');
          if(!boss)throw new Error('final boss was not spawned');
          boss.damage(boss.hp+1);
          __game.updatePlaying(0);
        }
        return record;
      }
      function escapeRealRegular(record){
        const enemy=new I.Zombie('walker',record.wave);
        enemy.update((I.routeLength()+1)/enemy.speed);
        __game.enemies.push(enemy);
        const beforeLives=__game.lives,beforeMoney=__game.money,beforeCount=__game.enemies.length;
        __game.updatePlaying(0);
        return {
          reached:enemy.reached,
          end:[enemy.x,enemy.y],
          beforeLives,
          afterLives:__game.lives,
          beforeMoney,
          afterMoney:__game.money,
          beforeCount,
          afterCount:__game.enemies.length,
          totalEscaped:__game.totalEscaped,
          recordEscaped:record.escaped,
          recordLivesLost:record.livesLost,
          settled:record.settled,
          state:__game.state.current,
        };
      }

      // One real Wave 1 enemy escapes; Waves 2-12 are resolved by killing real enemies.
      __game.startGame();
      const earlyRecord=startIsolatedWave();
      earlyRecord.remaining=1;earlyRecord.regularRemaining=1;
      const earlyEscape=escapeRealRegular(earlyRecord);
      for(let wave=2;wave<=12;wave++)killRealRegularWave();
      const earlyEscapeCampaign={
        state:__game.state.current,
        lives:__game.lives,
        totalEscaped:__game.totalEscaped,
        failedWaves:__game.failedWaves,
        wave:__game.wave.wave,
        finalEscaped:__game.wave.records[12].escaped,
        allSettled:Object.values(__game.wave.records).every(record=>record.settled),
      };

      // A real regular enemy escapes on Wave 12, then the real boss is killed.
      __game.startGame();__game.wave.wave=11;
      const finalRecord=startIsolatedWave();
      finalRecord.remaining=2;finalRecord.regularRemaining=1;
      const finalEscape=escapeRealRegular(finalRecord);
      const boss=__game.enemies.find(enemy=>enemy.type==='boss');
      if(!boss)throw new Error('boss missing after final regular escape');
      boss.damage(boss.hp+1);
      __game.updatePlaying(0);
      const finalEscapeCampaign={
        state:__game.state.current,
        lives:__game.lives,
        totalEscaped:__game.totalEscaped,
        failedWaves:__game.failedWaves,
        wave:__game.wave.wave,
        finalEscaped:finalRecord.escaped,
        finalSettled:finalRecord.settled,
      };

      return {
        grid:{columns:20,visible:[0,19],canvasRight:800,lastVisibleCenter:780},
        endpoints,boundary:{route,before,after},earlyEscape,earlyEscapeCampaign,
        finalEscape,finalEscapeCampaign,errors:__errors.slice()
      };
    """)
finally:
    driver.quit()

assert result['grid'] == {'columns':20,'visible':[0,19],'canvasRight':800,'lastVisibleCenter':780}, result
assert all(endpoint['col'] == 20 and endpoint['x'] == 820 for endpoint in result['endpoints']), result
assert result['boundary']['before']['reached'] is False and 800 < result['boundary']['before']['x'] < 820, result
assert result['boundary']['after']['reached'] is True and result['boundary']['after']['x'] == 820, result
assert result['earlyEscape'] == {
    'reached':True,'end':[820,180],'beforeLives':8,'afterLives':7,
    'beforeMoney':190,'afterMoney':180,'beforeCount':1,'afterCount':0,
    'totalEscaped':1,'recordEscaped':1,'recordLivesLost':1,
    'settled':True,'state':'PLAYING',
}, result
assert result['earlyEscapeCampaign'] == {
    'state':'VICTORY','lives':7,'totalEscaped':1,'failedWaves':1,
    'wave':12,'finalEscaped':0,'allSettled':True,
}, result
assert result['finalEscape']['reached'] is True and result['finalEscape']['afterLives'] == 7, result
assert result['finalEscapeCampaign'] == {
    'state':'VICTORY','lives':7,'totalEscaped':1,'failedWaves':1,
    'wave':12,'finalEscaped':1,'finalSettled':True,
}, result
assert result['errors'] == [], result
print('ZOMBIE ESCAPE ROUTE PASS:', json.dumps(result, sort_keys=True))
