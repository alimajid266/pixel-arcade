from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from pathlib import Path
import time

URL='http://127.0.0.1:8770/zombie-defense/'
root=Path(__file__).resolve().parents[1]
zombie_source=(root/'zombie-defense/index.html').read_text()
flappy_source=(root/'flappy/index.html').read_text()
assert 'drawMapPreview(ctx)' in zombie_source
assert "t.level<2?'UP $'+t.upgradeCost():'MAX LVL'" in zombie_source and "fillText('SELL'" in zombie_source
assert 'ONLY HITS' in zombie_source and "p.t==='deadTree'" in zombie_source and "p.t==='bones'" in zombie_source
assert 'let valid=this.money>=w.cost&&' in zombie_source
assert 'HORIZONTAL 2x1' in zombie_source and "'UP $'+t.upgradeCost()" in zombie_source
for source in (zombie_source,flappy_source):
    assert 'right:-26px' in source.replace(' ','')
options=Options();options.add_argument('-headless');options.binary_location='/snap/firefox/current/usr/lib/firefox/firefox'
d=webdriver.Firefox(options=options,service=Service('/snap/bin/firefox.geckodriver'))
try:
    d.get(URL);time.sleep(.4)
    result=d.execute_script("""
      __debug.start();
      const initial=__game.selected;
      __game.selectWeapon(initial);
      const deselected=__game.selected;
      const money=__game.money, count=__game.towers.length;
      const placed=__game.placeTower(0,0);
      __game.selectWeapon(2); const selected=__game.selected;
      __game.selectWeapon(2); const toggled=__game.selected;
      const wave1=__game.wave.start();
      __game.wave.spawned=__game.wave.queue.length;
      __game.enemies.push(new __internals.Zombie('walker',1));
      const perWave=!!__game.wave.records;
      if(perWave){__game.wave.records[1].escaped=2;__game.wave.records[1].livesLost=3;}
      else{__game.wave.escaped=2;__game.wave.livesLost=3;}
      const earlyAvailable=typeof __game.wave.canStart==='function'&&__game.wave.canStart();
      const wave2=__game.wave.start();
      const accounting=perWave?[__game.wave.records[1].escaped,__game.wave.records[1].livesLost,__game.wave.records[2].escaped,__game.wave.records[2].livesLost]:[__game.wave.escaped,__game.wave.livesLost];
      return {initial,deselected,placed,moneyUnchanged:__game.money===money,towersUnchanged:__game.towers.length===count,selected,toggled,wave1,earlyAvailable,wave2,currentWave:__game.wave.wave,enemies:__game.enemies.length,perWave,accounting,errors:__errors.slice()};
    """)
    assert result=={'initial':0,'deselected':-1,'placed':False,'moneyUnchanged':True,'towersUnchanged':True,'selected':2,'toggled':-1,'wave1':True,'earlyAvailable':True,'wave2':True,'currentWave':2,'enemies':1,'perWave':True,'accounting':[2,3,0,0],'errors':[]},result
    settlement=d.execute_script("""
      __game.startGame();__game.money=100;__game.best=0;
      __game.wave.start();__game.wave.spawned=__game.wave.queue.length;
      __game.wave.start();
      const r1=__game.wave.records[1],r2=__game.wave.records[2];
      while(r1.remaining>0)__game.wave.resolveEnemy({wave:1,type:'walker',lifeDamage:1},false);
      const afterWave1={money:__game.money,best:__game.best,r1:r1.settled,r2:r2.settled};
      __game.wave.resolveEnemy({wave:2,type:'walker',lifeDamage:1},true);
      while(r2.remaining>0)__game.wave.resolveEnemy({wave:2,type:'walker',lifeDamage:1},false);
      const afterWave2={money:__game.money,best:__game.best,failed:__game.failedWaves,r2:r2.settled};
      __game.startGame();__game.wave.wave=12;__game.wave.active=true;
      const old={wave:11,escaped:0,livesLost:0,settled:false},final={wave:12,escaped:0,livesLost:0,settled:false};
      __game.wave.records={11:old,12:final};
      __game.wave.settle(final);const delayed=__game.state.current==='PLAYING';
      __game.wave.settle(old);const victory=__game.state.current==='VICTORY';
      __game.startGame();__game.money=190;__game.lives=1;__game.wave.start();
      const lethalRecord=__game.wave.records[1];
      const hasAbort=typeof __game.wave.abortOnGameOver==='function';
      const lethalZombie=new __internals.Zombie('walker',1);lethalZombie.segment=999;
      __game.enemies.push(lethalZombie);__game.updatePlaying(.01);
      const lethal={hasAbort,money:__game.money,failed:__game.failedWaves,settled:lethalRecord.settled,state:__game.state.current};
      __game.startGame();__game.wave.wave=11;__game.wave.queue=null;__game.wave.start();
      const bossRecord=__game.wave.records[12];bossRecord.regularRemaining=1;bossRecord.remaining=2;
      __game.wave.resolveEnemy({wave:12,type:'walker',lifeDamage:1},false);
      const bosses=__game.enemies.filter(e=>e.type==='boss');
      if(bosses[0])__game.wave.resolveEnemy(bosses[0],false);
      const bossFlow={spawned:bosses.length,type:bosses[0]&&bosses[0].type,state:__game.state.current,settled:bossRecord.settled};
      __game.startGame();__game.money=100;__game.wave.wave=12;__game.wave.active=true;
      const failedOld={wave:11,remaining:1,regularRemaining:1,escaped:2,livesLost:2,bossSpawned:false,settled:false};
      const failedFinal={wave:12,remaining:0,regularRemaining:0,escaped:1,livesLost:1,bossSpawned:true,settled:false};
      __game.wave.records={11:failedOld,12:failedFinal};__game.wave.settle(failedFinal);
      const finalFailure={money:__game.money,failed:__game.failedWaves,oldSettled:failedOld.settled,finalSettled:failedFinal.settled,state:__game.state.current};
      __game.startGame();__game.money=0;__game.wave.wave=1;__game.wave.active=true;
      const bountyRecord={wave:1,remaining:1,regularRemaining:1,escaped:1,livesLost:1,bossSpawned:false,settled:false};
      __game.wave.records={1:bountyRecord};const bountyWalker=new __internals.Zombie('walker',1);bountyWalker.dead=true;__game.enemies=[bountyWalker];__game.updatePlaying(0);
      const bountyFine={money:__game.money,failed:__game.failedWaves,settled:bountyRecord.settled,state:__game.state.current};
      __game.startGame();__game.money=0;__game.wave.wave=12;__game.wave.active=true;
      const bountyOld={wave:11,remaining:1,regularRemaining:1,escaped:2,livesLost:2,bossSpawned:false,settled:false};
      const bountyFinal={wave:12,remaining:1,regularRemaining:0,escaped:1,livesLost:1,bossSpawned:true,settled:false};
      __game.wave.records={11:bountyOld,12:bountyFinal};const bountyBoss=new __internals.Zombie('boss',12);bountyBoss.dead=true;__game.enemies=[bountyBoss];__game.updatePlaying(0);
      const finalBountyFine={money:__game.money,reward:bountyBoss.reward,failed:__game.failedWaves,oldSettled:bountyOld.settled,finalSettled:bountyFinal.settled,state:__game.state.current};
      __game.startGame();__game.money=0;__game.lives=8;__game.wave.wave=12;__game.wave.active=true;
      const sameFrameOld={wave:11,remaining:1,regularRemaining:1,escaped:0,livesLost:0,bossSpawned:false,settled:false};
      const sameFrameFinal={wave:12,remaining:1,regularRemaining:0,escaped:0,livesLost:0,bossSpawned:true,settled:false};
      __game.wave.records={11:sameFrameOld,12:sameFrameFinal};const laterDead=new __internals.Zombie('walker',11);laterDead.dead=true;const escapingBoss=new __internals.Zombie('boss',12);escapingBoss.segment=999;__game.enemies=[laterDead,escapingBoss];__game.updatePlaying(0);
      const terminalLoop={money:__game.money,state:__game.state.current,enemies:__game.enemies.length,oldSettled:sameFrameOld.settled,finalSettled:sameFrameFinal.settled};
      __game.startGame();__game.money=0;__game.lives=3;__game.wave.wave=12;__game.wave.active=true;
      const lethalBossRecord={wave:12,remaining:1,regularRemaining:0,escaped:0,livesLost:0,bossSpawned:true,settled:false};
      __game.wave.records={12:lethalBossRecord};const lethalBoss=new __internals.Zombie('boss',12);lethalBoss.segment=999;__game.enemies=[lethalBoss];__game.updatePlaying(0);
      const lethalBossEscape={lives:__game.lives,money:__game.money,state:__game.state.current,enemies:__game.enemies.length,settled:lethalBossRecord.settled};
      return {afterWave1,afterWave2,finalGate:{delayed,victory},lethal,bossFlow,finalFailure,bountyFine,finalBountyFine,terminalLoop,lethalBossEscape,errors:__errors.slice()};
    """)
    assert settlement=={'afterWave1':{'money':117,'best':1,'r1':True,'r2':False},
      'afterWave2':{'money':107,'best':2,'failed':1,'r2':True},
      'finalGate':{'delayed':True,'victory':True},
      'lethal':{'hasAbort':True,'money':180,'failed':1,'settled':True,'state':'GAME_OVER'},
      'bossFlow':{'spawned':1,'type':'boss','state':'VICTORY','settled':True},
      'finalFailure':{'money':70,'failed':2,'oldSettled':True,'finalSettled':True,'state':'GAME_OVER'},
      'bountyFine':{'money':0,'failed':1,'settled':True,'state':'PLAYING'},
      'finalBountyFine':{'money':146,'reward':176,'failed':2,'oldSettled':True,'finalSettled':True,'state':'GAME_OVER'},
      'terminalLoop':{'money':0,'state':'GAME_OVER','enemies':0,'oldSettled':True,'finalSettled':True},
      'lethalBossEscape':{'lives':0,'money':0,'state':'GAME_OVER','enemies':0,'settled':True},'errors':[]},settlement
    strategy=d.execute_script("""
      const I=__internals;
      if(!I.Tower||!I.MAPS||!I.weaponCanTarget)return {featureContract:false,errors:__errors.slice()};
      __game.startGame();__game.money=1000;
      const bombPlaced=__game.placeTower(0,0,2),bomb=__game.towers[0];
      const footprint=bomb.cells.map(c=>[c.col,c.row]);
      const overlapBlocked=!__game.placeTower(1,0,0);
      const edgeBlocked=!__game.placeTower(19,0,3);
      __game.selectTower(bomb);
      const beforeUpgrade=__game.money,upgradeCost=bomb.upgradeCost();
      const upgraded=__game.upgradeSelectedTower(),afterUpgrade=__game.money;
      const level=bomb.level,damage=bomb.damage,sellValue=bomb.sellValue();
      const beforeSell=__game.money,sold=__game.sellSelectedTower(),afterSell=__game.money;
      const walker=new __internals.Zombie('walker',1),armored=new __internals.Zombie('armored',4);
      const walkerHp=walker.hp,armoredHp=armored.hp;
      walker.damage(20,'sniper');armored.damage(20,'rifle');
      const immune=[walker.hp===walkerHp,armored.hp===armoredHp];
      armored.damage(20,'bomb');
      const compatibility=I.WEAPONS.map(w=>I.MANUAL_TYPES.filter(t=>I.weaponCanTarget(w,t)));
      const speeds=[new __internals.Zombie('walker',1).speed,new __internals.Zombie('walker',12).speed];
      const scary=I.MAPS.every(m=>m.mood&&m.props.some(p=>['grave','bones','skull','deadTree','puddle'].includes(p.t)));
      const L=I.MENU_LAYOUT;
      return {featureContract:true,bombPlaced,footprint,center:[bomb.x,bomb.y],overlapBlocked,edgeBlocked,upgradeCost,upgraded,costPaid:beforeUpgrade-afterUpgrade,level,damage,sellValue,sold,salePaid:afterSell-beforeSell,immune,bombDamagedArmored:armored.hp<armoredHp,compatibility,speeds,scary,preview:!!L.preview,previewGap:L.preview.y+L.preview.h+18<=L.map.y,utilitiesTopRight:L.instructions.y<=70&&L.instructions.x>=580&&L.sound.y<=70&&L.sound.x>L.instructions.x,selectedCleared:__game.selectedTower===null,errors:__errors.slice()};
    """)
    assert strategy['featureContract'],strategy
    assert strategy['bombPlaced'] and strategy['footprint']==[[0,0],[1,0]] and strategy['center']==[40,20],strategy
    assert strategy['overlapBlocked'] and strategy['edgeBlocked'],strategy
    assert strategy['upgradeCost']==72 and strategy['upgraded'] and strategy['costPaid']==72 and strategy['level']==2 and abs(strategy['damage']-83.2)<1e-6,strategy
    assert 0<strategy['sellValue']<192 and strategy['sold'] and strategy['salePaid']==strategy['sellValue'] and strategy['selectedCleared'],strategy
    assert strategy['immune']==[True,True] and strategy['bombDamagedArmored'],strategy
    assert all(strategy['compatibility']) and len({tuple(x) for x in strategy['compatibility']})==4,strategy
    assert 60<=strategy['speeds'][0]<=64 and 72<=strategy['speeds'][1]<=82,strategy
    assert strategy['scary'] and strategy['preview'] and strategy['previewGap'] and strategy['utilitiesTopRight'] and strategy['errors']==[],strategy
    print('ZOMBIE STRATEGY CORE PASS:',result)
    print('ZOMBIE WAVE ACCOUNTING PASS:',settlement)
    print('ZOMBIE STRATEGY SYSTEMS PASS:',strategy)
    clicks=d.execute_script("""
      __game.startGame(); __game.money=1000;
      __game.selected=0;
      __game.handleClick(67,590);
      const deselectedByShopClick=__game.selected===-1;
      let placed=false;
      for(let r=0;r<12&&!placed;r++)for(let c=0;c<20&&!placed;c++)placed=__game.placeTower(c,r,0);
      const tower=__game.towers[0];
      __game.selectedTower=null; __game.selected=-1;
      __game.handleClick(tower.x,tower.y);
      const selectedByCanvasClick=__game.selectedTower===tower;
      const beforeUpgrade=__game.money;
      __game.handleClick(495,620);
      const upgradedByButton=tower.level===2&&__game.money===beforeUpgrade-tower.weapon.cost*.6;
      const expectedSale=tower.sellValue(),beforeSale=__game.money;
      __game.handleClick(569,620);
      return {deselectedByShopClick,selectedByCanvasClick,upgradedByButton,
        soldByButton:__game.towers.length===0&&__game.money===beforeSale+expectedSale,
        errors:__errors.slice()};
    """)
    assert clicks=={'deselectedByShopClick':True,'selectedByCanvasClick':True,
      'upgradedByButton':True,'soldByButton':True,'errors':[]},clicks
    print('ZOMBIE STRATEGY INPUT PASS:',clicks)
    d.set_window_size(700,500)
    mobile=[]
    for path in ('/zombie-defense/','/flappy/'):
        d.get('http://127.0.0.1:8770'+path);time.sleep(.25)
        mobile.append(d.execute_script("""
          const canvasEl=document.querySelector('canvas'),canvas=canvasEl.getBoundingClientRect();
          return [...document.querySelectorAll('.game-entry')].map(e=>{
            const tile=e.querySelector('.game-tile').getBoundingClientRect(),tab=e.querySelector('.open-tab').getBoundingClientRect();
            const intersects=(a,b)=>!(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom);
            return {tileOverlap:intersects(tab,tile),canvasOverlap:intersects(tab,canvas),scaleDiff:Math.abs(canvas.width/canvasEl.width-canvas.height/canvasEl.height)};
          });
        """))
    assert all(not item['tileOverlap'] and not item['canvasOverlap'] and item['scaleDiff']<.02 for page in mobile for item in page),mobile
    print('MOBILE SIDEBAR GEOMETRY PASS:',mobile)
    portraits=[]
    for path in ('/zombie-defense/','/flappy/'):
      d.set_window_size(390,844);d.get('http://127.0.0.1:8770'+path);time.sleep(.4)
      portraits.append(d.execute_script("""
        const n=document.querySelector('.rotate-notice'),s=document.getElementById('shell')||document.querySelector('body>canvas');
        const before=window.__game&&window.__game.snapshot?window.__game.snapshot().state:null;
        window.dispatchEvent(new KeyboardEvent('keydown',{key:' ',code:'Space',bubbles:true}));
        const after=window.__game&&window.__game.snapshot?window.__game.snapshot().state:null;
        return {exists:!!n,shown:!!n&&getComputedStyle(n).display!=='none',font:n?parseFloat(getComputedStyle(n).fontSize):0,shellHidden:getComputedStyle(s).display==='none',keyboardBlocked:before===after,errors:window.__errors?window.__errors.slice():[]};
      """))
    assert all(p=={'exists':True,'shown':True,'font':16,'shellHidden':True,'keyboardBlocked':True,'errors':[]} for p in portraits),portraits
    print('PORTRAIT ORIENTATION GATE PASS:',portraits)
finally:
    d.quit()
